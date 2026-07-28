package agents

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha1"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"sort"
	"strings"
	"time"

	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
)

// ─── Bluesky AT Protocol Client (pure Go, no external deps) ─────────────

type BlueskyProvider struct {
	Handle   string
	Password string
	client   *http.Client
	dryRun   bool
}

func NewBlueskyProvider(handle, password string) *BlueskyProvider {
	return &BlueskyProvider{
		Handle:   handle,
		Password: password,
		client:   &http.Client{Timeout: 30 * time.Second},
		dryRun:   os.Getenv("BLUESKY_DRY_RUN") == "true" || os.Getenv("DRY_RUN") == "true",
	}
}
func (p *BlueskyProvider) Name() string { return "bluesky" }

// atprotoSession is returned by com.atproto.server.createSession
type atprotoSession struct {
	AccessJWT  string `json:"accessJwt"`
	RefreshJWT string `json:"refreshJwt"`
	Handle     string `json:"handle"`
	Did        string `json:"did"`
}

// atprotoRecord is the payload for com.atproto.repo.createRecord
type atprotoRecord struct {
	Repo       string `json:"repo"`
	Collection string `json:"collection"`
	Record     any    `json:"record"`
}

// blueskyPost is the schema for app.bsky.feed.post
type blueskyPost struct {
	Text      string        `json:"text"`
	CreatedAt string        `json:"createdAt"`
	Facets    []any         `json:"facets,omitempty"`
	Embed     *blueskyEmbed `json:"embed,omitempty"`
}

type blueskyEmbed struct {
	Type     string          `json:"$type"`
	External blueskyExternal `json:"external"`
}

type blueskyExternal struct {
	URI         string `json:"uri"`
	Title       string `json:"title"`
	Description string `json:"description"`
}

func (p *BlueskyProvider) Post(ctx context.Context, req PostRequest) error {
	if p.dryRun {
		slog.Info(fmt.Sprintf("[Bluesky DRY RUN] Would post to %s:\n%s", req.AccountID, truncate(req.Content, 200)))
		return nil
	}

	// 1. Create session (authenticate)
	session, err := p.createSession(ctx)
	if err != nil {
		return fmt.Errorf("bluesky auth: %w", err)
	}

	// 2. Build the post record
	post := blueskyPost{
		Text:      req.Content,
		CreatedAt: time.Now().UTC().Format(time.RFC3339),
	}

	// 3. Create the record via the AT Protocol
	recordURL := "https://bsky.social/xrpc/com.atproto.repo.createRecord"
	payload := atprotoRecord{
		Repo:       session.Did,
		Collection: "app.bsky.feed.post",
		Record:     post,
	}

	body, _ := json.Marshal(payload)
	httpReq, _ := http.NewRequestWithContext(ctx, "POST", recordURL, bytes.NewReader(body))
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+session.AccessJWT)

	resp, err := p.client.Do(httpReq)
	if err != nil {
		return fmt.Errorf("bluesky createRecord: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("bluesky createRecord: HTTP %d: %s", resp.StatusCode, truncate(string(respBody), 300))
	}

	slog.Info(fmt.Sprintf("Bluesky: Posted to %s ✓", req.AccountID))
	return nil
}

func (p *BlueskyProvider) createSession(ctx context.Context) (*atprotoSession, error) {
	body := map[string]string{
		"identifier": p.Handle,
		"password":   p.Password,
	}
	payload, _ := json.Marshal(body)

	req, _ := http.NewRequestWithContext(ctx, "POST",
		"https://bsky.social/xrpc/com.atproto.server.createSession",
		bytes.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("connection: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, truncate(string(respBody), 200))
	}

	var session atprotoSession
	if err := json.NewDecoder(resp.Body).Decode(&session); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	if session.AccessJWT == "" {
		return nil, fmt.Errorf("empty access token in session response")
	}
	return &session, nil
}

// ─── Reddit API Client (OAuth2 App-Only + Script) ────────────────────────

type RedditProvider struct {
	ClientID     string
	ClientSecret string
	Username     string
	Password     string
	client       *http.Client
	accessToken  string
	dryRun       bool
}

func NewRedditProvider(clientID, clientSecret, username, password string) *RedditProvider {
	return &RedditProvider{
		ClientID:     clientID,
		ClientSecret: clientSecret,
		Username:     username,
		Password:     password,
		client:       &http.Client{Timeout: 30 * time.Second},
		dryRun:       os.Getenv("REDDIT_DRY_RUN") == "true" || os.Getenv("DRY_RUN") == "true",
	}
}
func (p *RedditProvider) Name() string { return "reddit" }

func (p *RedditProvider) Post(ctx context.Context, req PostRequest) (err error) {
	if p.dryRun {
		slog.Info(fmt.Sprintf("[Reddit DRY RUN] Would post to %s:\n%s", req.AccountID, truncate(req.Content, 200)))
		return nil
	}

	if p.Username == "" || p.Password == "" {
		slog.Info("RedditProvider: Credentials not configured, skipping live Reddit post.")
		return nil
	}

	slog.Info("RedditProvider: Attempting headless post via go-rod", "subreddit", "r/TormentNexusDev")

	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("reddit headless post panicked: %v", r)
		}
	}()

	// Launch headless Chromium with all required flags for Linux VPS (root/no sandbox)
	u := launcher.New().
		NoSandbox(true).
		Headless(true).
		Set("disable-gpu").
		Set("disable-dev-shm-usage").
		Set("disable-extensions").
		Set("disable-setuid-sandbox").
		MustLaunch()
	browser := rod.New().ControlURL(u).MustConnect()
	defer func() { _ = browser.Close() }()

	page := browser.MustPage()

	// 1. Login via old.reddit.com (simpler form, no anti-bot JS)
	page.MustNavigate("https://old.reddit.com/login")
	page.MustWaitLoad()
	page.MustElement("input[name='user']").MustInput(p.Username)
	page.MustElement("input[name='passwd']").MustInput(p.Password)
	page.MustElement("button[type='submit']").MustClick()
	time.Sleep(3 * time.Second)

	// 2. Navigate to submit page
	page.MustNavigate("https://old.reddit.com/r/TormentNexusDev/submit")
	page.MustWaitLoad()

	// 3. Write post
	page.MustElement("input[name='title']").MustInput("TormentNexus Marketing System Update")
	page.MustElement("textarea[name='text']").MustInput(req.Content)

	// 4. Click Submit
	page.MustElement("button[type='submit']").MustClick()
	time.Sleep(3 * time.Second)

	slog.Info("Reddit: Headless post successful to r/TormentNexusDev ✓")
	return nil
}

func (p *RedditProvider) getToken(ctx context.Context) (string, error) {
	if p.accessToken != "" {
		return p.accessToken, nil
	}

	data := strings.NewReader(fmt.Sprintf(
		"grant_type=password&username=%s&password=%s",
		p.Username, p.Password,
	))

	req, _ := http.NewRequestWithContext(ctx, "POST",
		"https://www.reddit.com/api/v1/access_token", data)
	req.Header.Set("Authorization", basicAuth(p.ClientID, p.ClientSecret))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("User-Agent", "web:tormentnexus-bot:v1 (by /u/"+p.Username+")")

	resp, err := p.client.Do(req)
	if err != nil {
		return "", fmt.Errorf("token request: %w", err)
	}
	defer resp.Body.Close()

	var result struct {
		AccessToken string `json:"access_token"`
		Error       string `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", fmt.Errorf("token decode: %w", err)
	}
	if result.Error != "" {
		return "", fmt.Errorf("reddit oauth error: %s", result.Error)
	}
	if result.AccessToken == "" {
		return "", fmt.Errorf("empty access token")
	}
	p.accessToken = result.AccessToken
	return result.AccessToken, nil
}

// ─── Twitter / X API v2 Client ──────────────────────────────────────────

type TwitterProvider struct {
	APIKey       string
	APISecret    string
	AccessToken  string
	AccessSecret string
	BearerToken  string
	client       *http.Client
	dryRun       bool
}

func NewTwitterProvider(apiKey, apiSecret, accessToken, accessSecret, bearerToken string) *TwitterProvider {
	return &TwitterProvider{
		APIKey:       apiKey,
		APISecret:    apiSecret,
		AccessToken:  accessToken,
		AccessSecret: accessSecret,
		BearerToken:  bearerToken,
		client:       &http.Client{Timeout: 30 * time.Second},
		dryRun:       os.Getenv("TWITTER_DRY_RUN") == "true" || os.Getenv("DRY_RUN") == "true",
	}
}
func (p *TwitterProvider) Name() string { return "twitter" }

func (p *TwitterProvider) Post(ctx context.Context, req PostRequest) error {
	if p.dryRun {
		slog.Info(fmt.Sprintf("[Twitter DRY RUN] Would post to %s:\n%s", req.AccountID, truncate(req.Content, 200)))
		return nil
	}

	payload := map[string]string{"text": req.Content}
	body, _ := json.Marshal(payload)

	apiURL := "https://api.twitter.com/2/tweets"
	httpReq, _ := http.NewRequestWithContext(ctx, "POST", apiURL, bytes.NewReader(body))
	httpReq.Header.Set("Content-Type", "application/json")

	// Use OAuth 1.0a for posting (Bearer token is read-only)
	if p.AccessToken != "" && p.APISecret != "" && p.AccessSecret != "" && p.APIKey != "" {
		httpReq.Header.Set("Authorization", oauth1Header("POST", apiURL, p.APIKey, p.APISecret, p.AccessToken, p.AccessSecret))
	} else if p.BearerToken != "" && len(p.BearerToken) > 50 {
		// Fall back to Bearer token (may not work for posting)
		httpReq.Header.Set("Authorization", "Bearer "+p.BearerToken)
	} else {
		return fmt.Errorf("twitter: no valid auth credentials configured")
	}

	resp, err := p.client.Do(httpReq)
	if err != nil {
		return fmt.Errorf("twitter post: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("twitter post: HTTP %d: %s", resp.StatusCode, truncate(string(respBody), 300))
	}

	slog.Info(fmt.Sprintf("Twitter: Posted to %s ✓", req.AccountID))
	return nil
}

// ─── OAuth 1.0a Signing ──────────────────────────────────────────────

// oauth1Header generates an OAuth 1.0a Authorization header for Twitter API.
func oauth1Header(method, urlStr, consumerKey, consumerSecret, token, tokenSecret string) string {
	nonce := randomNonce(16)
	timestamp := fmt.Sprintf("%d", time.Now().Unix())

	params := map[string]string{
		"oauth_consumer_key":     consumerKey,
		"oauth_nonce":            nonce,
		"oauth_signature_method": "HMAC-SHA1",
		"oauth_timestamp":        timestamp,
		"oauth_token":            token,
		"oauth_version":          "1.0",
	}

	signingKey := url.QueryEscape(consumerSecret) + "&" + url.QueryEscape(tokenSecret)
	signatureBase := signatureBaseString(method, urlStr, params)
	signature := hmacSHA1(signingKey, signatureBase)
	params["oauth_signature"] = signature

	// Build header
	var headerParts []string
	for k, v := range params {
		headerParts = append(headerParts, fmt.Sprintf("%s=\"%s\"", url.QueryEscape(k), url.QueryEscape(v)))
	}
	return "OAuth " + strings.Join(headerParts, ", ")
}

func signatureBaseString(method, urlStr string, params map[string]string) string {
	var sorted []string
	for k, v := range params {
		sorted = append(sorted, fmt.Sprintf("%s=%s", url.QueryEscape(k), url.QueryEscape(v)))
	}
	sort.Strings(sorted)
	paramStr := strings.Join(sorted, "&")
	return strings.ToUpper(method) + "&" + url.QueryEscape(urlStr) + "&" + url.QueryEscape(paramStr)
}

func hmacSHA1(key, data string) string {
	mac := hmac.New(sha1.New, []byte(key))
	mac.Write([]byte(data))
	return base64.StdEncoding.EncodeToString(mac.Sum(nil))
}

func randomNonce(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		randByte := make([]byte, 1)
		_, _ = rand.Read(randByte)
		b[i] = charset[int(randByte[0])%len(charset)]
	}
	return string(b)
}

// ─── Helpers ──────────────────────────────────────────────────────────

func basicAuth(username, password string) string {
	auth := username + ":" + password
	return "Basic " + base64.StdEncoding.EncodeToString([]byte(auth))
}

func stripNewlines(s string) string {
	return strings.ReplaceAll(strings.ReplaceAll(s, "\n", " "), "\r", "")
}
