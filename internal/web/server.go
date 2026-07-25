package web

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"html"
	"io"
	"log/slog"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gorilla/websocket"
	"gitlab.com/robertpelloni/marketing_agent/internal/auth"
	"gitlab.com/robertpelloni/marketing_agent/internal/autodev"
	"gitlab.com/robertpelloni/marketing_agent/internal/billing"
	"gitlab.com/robertpelloni/marketing_agent/internal/communication"
	"gitlab.com/robertpelloni/marketing_agent/internal/db"
	"gitlab.com/robertpelloni/marketing_agent/internal/deploy"
	"gitlab.com/robertpelloni/marketing_agent/internal/llm"
	"gitlab.com/robertpelloni/marketing_agent/internal/logging"
)

// HermesHealthChecker is an optional interface for checking LLM provider health.
type HermesHealthChecker interface {
	HealthCheck(ctx context.Context) error
}

// Server handles web dashboard requests.
type Server struct {
	db            *db.DB
	deploy        *deploy.Deployer
	tracker       deploy.CITracker
	tasks         *autodev.TaskManager
	auth          *auth.Authenticator
	llmProvider   llm.LLMProvider
	billingClient billing.BillingClient
	mux           *http.ServeMux
	blogEngine    blogTriggerer // optional manual blog trigger
}

// blogTriggerer allows the server to trigger blog post generation.
type blogTriggerer interface {
	GenerateNextPost(ctx context.Context)
	GenerateBatch(ctx context.Context, n int) int
}

// NewServer creates a new Server instance.
func NewServer(database *db.DB, deployer *deploy.Deployer, tracker deploy.CITracker, taskManager *autodev.TaskManager, llmProvider llm.LLMProvider, billingClient billing.BillingClient, blogEngine blogTriggerer) *Server {
	var dbConn *sql.DB
	if database != nil {
		dbConn = database.Conn
	}
	s := &Server{
		db:            database,
		deploy:        deployer,
		tracker:       tracker,
		tasks:         taskManager,
		auth:          auth.NewAuthenticator(dbConn),
		llmProvider:   llmProvider,
		billingClient: billingClient,
		mux:           http.NewServeMux(),
		blogEngine:    blogEngine,
	}
	s.routes()
	return s
}

func (s *Server) routes() {
	// Protected routes
	// Initialize rate limiter: 10 requests per second, burst of 20
	rl := newRateLimiter(10, 20)

	// Protected routes
	s.mux.Handle("/", rl.middleware(s.auth.Middleware(s.csrfMiddleware(http.HandlerFunc(s.handleDashboard)))))

	// Container management API (protected)
	s.mux.Handle("/api/v1/container/start", rl.middleware(s.auth.Middleware(http.HandlerFunc(s.handleContainerStart))))
	s.mux.Handle("/api/v1/container/stop", rl.middleware(s.auth.Middleware(http.HandlerFunc(s.handleContainerStop))))
	s.mux.Handle("/api/v1/container/restart", rl.middleware(s.auth.Middleware(http.HandlerFunc(s.handleContainerRestart))))

	// Public routes
	s.mux.Handle("/demo", rl.middleware(http.HandlerFunc(s.handleDemoDashboard)))
	s.mux.Handle("/login", rl.middleware(http.HandlerFunc(s.auth.HandleLogin)))
	s.mux.Handle("/health", rl.middleware(http.HandlerFunc(s.handleHealth)))
	s.mux.Handle("/health/detailed", rl.middleware(http.HandlerFunc(s.handleDetailedHealth)))
	s.mux.Handle("/api/v1/webhook/github", rl.middleware(http.HandlerFunc(s.handleGitHubWebhook)))
	s.mux.Handle("/api/v1/quote", rl.middleware(http.HandlerFunc(s.handleGenerateQuote)))
	s.mux.Handle("/api/v1/leads", rl.middleware(http.HandlerFunc(s.handleLeadsAPI)))
	s.mux.Handle("/api/v1/deals", rl.middleware(http.HandlerFunc(s.handleDealsAPI)))

	// GDPR Endpoints
	s.mux.Handle("/api/v1/gdpr/export", rl.middleware(s.auth.Middleware(http.HandlerFunc(s.handleGDPRExport))))
	s.mux.Handle("/api/v1/gdpr/delete", rl.middleware(s.auth.Middleware(http.HandlerFunc(s.handleGDPRDelete))))

	// Telemetry WebSocket
	s.mux.Handle("/ws/telemetry", s.auth.Middleware(http.HandlerFunc(s.handleTelemetryWS)))

	// Stripe Webhook (public, verified by signature)
	s.mux.Handle("/api/v1/webhook/stripe", rl.middleware(http.HandlerFunc(s.handleStripeWebhook)))

	// Create Checkout Session (public — called from hypernexus.site pricing buttons)
	s.mux.Handle("/api/v1/billing/checkout", rl.middleware(http.HandlerFunc(s.handleCreateCheckout)))

	// Billing API (protected — requires auth)
	s.mux.Handle("/api/v1/billing/subscription", rl.middleware(s.auth.Middleware(http.HandlerFunc(s.handleGetSubscription))))
	s.mux.Handle("/api/v1/billing/cancel", rl.middleware(s.auth.Middleware(http.HandlerFunc(s.handleCancelSubscription))))
	s.mux.Handle("/api/v1/billing/portal", rl.middleware(s.auth.Middleware(http.HandlerFunc(s.handleBillingPortal))))

	// Blog generation trigger (protected)
	s.mux.Handle("/api/v1/blog/generate", rl.middleware(s.auth.Middleware(http.HandlerFunc(s.handleBlogGenerate))))

	// Social content API (public — serves content for Devvit Reddit app)
	s.mux.Handle("/api/v1/social/reddit", rl.middleware(http.HandlerFunc(s.handleRedditContent)))

	// Newsletter subscription (public)
	s.mux.Handle("/api/v1/newsletter/subscribe", rl.middleware(http.HandlerFunc(s.handleNewsletterSubscribe)))
}

// ServeHTTP implements the http.Handler interface.
func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	s.mux.ServeHTTP(w, r)
}

// ListenAndServe starts the HTTP server.
func (s *Server) ListenAndServe(addr string) error {
	logging.Init("json", "info")
	slog.Info("Web dashboard starting", "addr", addr)
	// #nosec G114 -- Simple ListenAndServe is used for internal dashboard; timeout configuration handled at higher level if needed
	return http.ListenAndServe(addr, logging.Middleware(s))
}

func (s *Server) handleDashboard(w http.ResponseWriter, r *http.Request) {
	csrfToken := ""
	if cookie, err := r.Cookie("csrf_token"); err == nil {
		csrfToken = cookie.Value
	}
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}

	if r.Method == http.MethodPost {
		action := html.EscapeString(strings.TrimSpace(r.FormValue("action")))
		switch action {
		case "enrich":
			dealID := html.EscapeString(strings.TrimSpace(r.FormValue("deal_id")))
			// #nosec G706 -- deal_id is used for context in manual action logs
			slog.InfoContext(r.Context(), "Manual enrichment triggered", "deal_id", dealID)
		case "sync":
			if err := s.deploy.ExecuteSync(); err != nil {
				slog.WarnContext(r.Context(), "Sync error", "error", err)
			}
		case "flag_success":
			interactionID := html.EscapeString(strings.TrimSpace(r.FormValue("interaction_id")))
			success := html.EscapeString(strings.TrimSpace(r.FormValue("success"))) == "true"
			var id int64
			if _, err := fmt.Sscanf(interactionID, "%d", &id); err != nil {
				slog.WarnContext(r.Context(), "Invalid interaction ID", "error", err, "interaction_id", interactionID)
			} else {
				if err := s.db.UpdateInteractionSuccess(r.Context(), id, success); err != nil {
					slog.WarnContext(r.Context(), "Error flagging interaction", "error", err, "interaction_id", id)
				}
			}
		case "update_channel":
			contactID := html.EscapeString(strings.TrimSpace(r.FormValue("contact_id")))
			channel := html.EscapeString(strings.TrimSpace(r.FormValue("channel")))
			var id int64
			if _, err := fmt.Sscanf(contactID, "%d", &id); err != nil {
				slog.WarnContext(r.Context(), "Invalid contact ID", "error", err, "contact_id", contactID)
			} else {
				if err := s.db.UpdateContactPreferredChannel(r.Context(), id, channel); err != nil {
					slog.WarnContext(r.Context(), "Error updating channel", "error", err, "contact_id", id, "channel", channel)
				} else {
					slog.InfoContext(r.Context(), "Contact channel updated", "contact_id", id, "channel", channel)
				}
			}
		case "build":
			if err := s.deploy.ExecuteBuild(); err != nil {
				slog.WarnContext(r.Context(), "Build error", "error", err)
			}
		case "approve_deal":
			dealIDStr := html.EscapeString(strings.TrimSpace(r.FormValue("deal_id")))
			var id int64
			if _, err := fmt.Sscanf(dealIDStr, "%d", &id); err != nil {
				slog.WarnContext(r.Context(), "Invalid deal ID for approval", "error", err)
			} else {
				if err := s.db.UpdateDealState(r.Context(), id, db.StateNegotiating); err != nil {
					slog.WarnContext(r.Context(), "Failed to approve deal", "deal_id", id, "error", err)
				} else {
					slog.InfoContext(r.Context(), "Deal approved by human", "deal_id", id)
				}
			}
		}
		http.Redirect(w, r, "/", http.StatusSeeOther)
		return
	}

	// Determine if this is a company session
	var companyID int64
	var isCompanySession bool
	cookieSession, errSession := r.Cookie("sales_bot_session")
	if errSession == nil && strings.HasPrefix(cookieSession.Value, "company_") {
		if _, errScan := fmt.Sscanf(cookieSession.Value, "company_%d", &companyID); errScan == nil {
			isCompanySession = true
		}
	}

	if isCompanySession {
		var err error
		// Fetch company details
		var companyName string
		var companyDomain string
		err = s.db.Conn.QueryRowContext(r.Context(), "SELECT name, domain FROM companies WHERE id = $1", companyID).Scan(&companyName, &companyDomain)
		if err != nil {
			http.Error(w, "Company not found: "+err.Error(), http.StatusNotFound)
			return
		}

		// Fetch subscription details
		subTier := "Free / Community"
		subState := "active"
		subSeats := 1
		subEndStr := "Never"
		subTimeLeftStr := "Unlimited"

		var currentPeriodEnd sql.NullTime
		var seats int
		var tier string
		var state string
		err = s.db.Conn.QueryRowContext(r.Context(),
			"SELECT tier, state, seats, current_period_end FROM subscriptions WHERE company_id = $1 ORDER BY id DESC LIMIT 1", companyID).Scan(&tier, &state, &seats, &currentPeriodEnd)
		if err == nil {
			subTier = tier
			subState = state
			subSeats = seats
			if currentPeriodEnd.Valid {
				subEndStr = currentPeriodEnd.Time.Format("January 2, 2006")
				timeLeft := time.Until(currentPeriodEnd.Time)
				if timeLeft > 0 {
					days := int(timeLeft.Hours() / 24)
					if days > 0 {
						subTimeLeftStr = fmt.Sprintf("%d days", days)
					} else {
						hours := int(timeLeft.Hours())
						subTimeLeftStr = fmt.Sprintf("%d hours", hours)
					}
				} else {
					subTimeLeftStr = "Expired"
					subState = "expired"
				}
			}
		}

		// Fetch actual container status
		info, err := GetContainerStatus(r.Context(), companyID)
		if err != nil {
			info = &ContainerInfo{State: "unknown", Uptime: "N/A", MountPath: fmt.Sprintf("/var/lib/tormentnexus/company_%d", companyID)}
		}

		w.Header().Set("Content-Type", "text/html")
		_, _ = fmt.Fprintf(w, `<!DOCTYPE html>
<html>
<head>
<title>HyperNexus Tenant Console</title>
<style>
:root {
	--primary: #5865F2;
	--primary-hover: #4752C4;
	--success: #23A55A;
	--info: #00b0f4;
	--warning: #F0B232;
	--danger: #F23F43;
	--dark: #0f172a;
	--light: #f8fafc;
	--purple: #9b5de5;
	--bg-main: #f1f5f9;
	--border-color: #e2e8f0;
	--text-main: #334155;
}
body { font-family: 'Inter', sans-serif; margin: 0; background-color: var(--bg-main); color: var(--text-main); }
.header { background: linear-gradient(135deg, #1e293b, var(--dark)); color: white; padding: 24px 40px; display: flex; justify-content: space-between; align-items: center; }
.header h1 { margin: 0; font-size: 1.6rem; }
.container { max-width: 1000px; margin: 40px auto; padding: 0 24px; display: flex; flex-direction: column; gap: 24px; }
.card { background: white; border-radius: 12px; padding: 24px; border: 1px solid var(--border-color); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.card-header { font-size: 1.3rem; font-weight: 700; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
.btn { background-color: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; text-decoration: none; display: inline-block; margin-right: 10px; }
.btn-success { background-color: var(--success); }
.btn-danger { background-color: var(--danger); }
.status-badge { font-weight: 700; padding: 6px 12px; border-radius: 9999px; font-size: 0.85rem; }
.status-running { background-color: #dcfce7; color: #15803d; }
.status-stopped { background-color: #fee2e2; color: #b91c1c; }
.status-not_created { background-color: #f1f5f9; color: #475569; }
</style>
</head>
<body>
<div class="header">
	<h1>HyperNexus Tenant Console — %s</h1>
	<a href="/login" class="btn" style="background: transparent; border: 1px solid white; margin: 0;">Log Out</a>
</div>
<div class="container">
	<div class="card" style="border-top: 4px solid var(--purple);">
		<div class="card-header">Active Subscription Info</div>
		<p>
			<strong>Tier:</strong> <span style="text-transform: capitalize; color: var(--purple); font-weight: 700;">%s</span> | 
			<strong>Status:</strong> <span style="color: var(--success); font-weight: 600;">%s</span> | 
			<strong>Seats:</strong> %d | 
			<strong>Renewal Date:</strong> %s (%s remaining)
		</p>
		<a href="/api/v1/billing/portal" class="btn" style="background-color: var(--purple);">Manage Subscription</a>
	</div>

	<div class="card" style="border-top: 4px solid var(--info);">
		<div class="card-header">Isolated TormentNexus Container</div>
		<p>Your account is connected to an isolated Docker container running the TormentNexus binary in corporate mode.</p>
		<div style="background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); margin-bottom: 20px;">
			<p style="margin-top: 0;"><strong>Container Name:</strong> <code>tormentnexus_company_%d</code></p>
			<p><strong>Status:</strong> <span class="status-badge status-%s">%s</span></p>
			<p><strong>Uptime:</strong> %s</p>
			<p style="margin-bottom: 0;"><strong>Isolated Writeable Directory:</strong> <code>%s</code></p>
		</div>
		<div>
			<button onclick="controlContainer('start')" class="btn btn-success">Start Container</button>
			<button onclick="controlContainer('stop')" class="btn btn-danger">Stop Container</button>
			<button onclick="controlContainer('restart')" class="btn">Restart Container</button>
		</div>
		<p id="apiStatus" style="margin-top: 15px; display: none; font-weight: 600;"></p>
	</div>
</div>
<script>
function controlContainer(action) {
	const statusText = document.getElementById('apiStatus');
	statusText.style.display = 'block';
	statusText.style.color = '#334155';
	statusText.textContent = 'Sending command...';
	
	fetch('/api/v1/container/' + action, { method: 'POST' })
	.then(res => {
		if(!res.ok) throw new Error('API error');
		return res.json();
	})
	.then(data => {
		statusText.style.color = 'var(--success)';
		statusText.textContent = 'Success! Container is ' + action + 'ing. Reloading page...';
		setTimeout(() => location.reload(), 1500);
	})
	.catch(err => {
		statusText.style.color = 'var(--danger)';
		statusText.textContent = 'Failed to execute command. Please try again.';
	});
}
</script>
</body>
</html>`, companyName, subTier, subState, subSeats, subEndStr, subTimeLeftStr, companyID, info.State, info.State, info.Uptime, info.MountPath)
		return
	}

	deals, err := s.db.ListRecentDeals(r.Context(), 20)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to retrieve deals: %v", err), http.StatusInternalServerError)
		return
	}

	health, _ := s.tracker.GetSystemHealth(r.Context())

	metrics, err := s.db.GetPerformanceMetrics(r.Context())
	if err != nil {
		slog.WarnContext(r.Context(), "Error retrieving metrics", "error", err)
		metrics = &db.PerformanceMetrics{
			LeadsByState: make(map[db.LeadState]int),
		}
	}

	prs, err := s.db.ListActivePullRequests(r.Context())
	if err != nil {
		slog.WarnContext(r.Context(), "Error listing PRs", "error", err)
	}

	taskList, _ := s.tasks.ListAllTasks(r.Context())
	socialPosts, err := s.db.ListRecentSocialPosts(r.Context(), 15)
	if err != nil {
		slog.WarnContext(r.Context(), "Error listing social posts", "error", err)
		socialPosts = []db.SocialPost{}
	}

	// Check LLM/Hermes health for the dashboard
	llmStatus := "Mock"
	llmColor := "#6c757d"
	if checker, ok := s.llmProvider.(HermesHealthChecker); ok {
		if err := checker.HealthCheck(r.Context()); err != nil {
			llmStatus = fmt.Sprintf("Hermes: ERROR (%v)", err)
			llmColor = "#dc3545"
		} else {
			llmStatus = "Hermes: Connected"
			llmColor = "#28a745"
		}
	}

	// Get active subscription info
	subTier := "Free / Community"
	subState := "active"
	subSeats := 1
	subEndStr := "Never"
	subTimeLeftStr := "Unlimited"

	// Query the most recent subscription
	var currentPeriodEnd sql.NullTime
	var seats int
	var tier string
	var state string
	err = s.db.Conn.QueryRowContext(r.Context(),
		"SELECT tier, state, seats, current_period_end FROM subscriptions ORDER BY id DESC LIMIT 1").Scan(&tier, &state, &seats, &currentPeriodEnd)
	if err == nil {
		subTier = tier
		subState = state
		subSeats = seats
		if currentPeriodEnd.Valid {
			subEndStr = currentPeriodEnd.Time.Format("January 2, 2006")
			timeLeft := time.Until(currentPeriodEnd.Time)
			if timeLeft > 0 {
				days := int(timeLeft.Hours() / 24)
				if days > 0 {
					subTimeLeftStr = fmt.Sprintf("%d days", days)
				} else {
					hours := int(timeLeft.Hours())
					subTimeLeftStr = fmt.Sprintf("%d hours", hours)
				}
			} else {
				subTimeLeftStr = "Expired"
				subState = "expired"
			}
		}
	}

	w.Header().Set("Content-Type", "text/html")
	_, _ = fmt.Fprintf(w, "%s", "<!DOCTYPE html>")
	_, _ = fmt.Fprintf(w, `
<html>
<head>
<title>TormentNexus / HyperNexus Autonomous Pipeline Dashboard</title>
<style>
:root {
	--primary: #5865F2;
	--primary-hover: #4752C4;
	--success: #23A55A;
	--info: #00b0f4;
	--warning: #F0B232;
	--danger: #F23F43;
	--dark: #0f172a;
	--light: #f8fafc;
	--purple: #9b5de5;
	--bg-main: #f1f5f9;
	--border-color: #e2e8f0;
	--text-main: #334155;
}
body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background-color: var(--bg-main); color: var(--text-main); line-height: 1.5; }
.header { background: linear-gradient(135deg, #1e293b, var(--dark)); color: white; padding: 24px 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-bottom: 2px solid #334155; }
.header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; letter-spacing: -0.5px; background: linear-gradient(to right, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.container { max-width: 1400px; margin: 30px auto; padding: 0 24px; display: flex; flex-direction: column; gap: 24px; }
.card { background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); padding: 24px; border: 1px solid var(--border-color); position: relative; transition: transform 0.2s, box-shadow 0.2s; }
.card:hover { transform: translateY(-1px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08); }
.card-header { font-size: 1.3rem; font-weight: 700; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center; color: #1e293b; }
table { width: 100%%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
th, td { padding: 12px 16px; border-bottom: 1px solid var(--border-color); text-align: left; vertical-align: middle; }
th { background-color: #f8fafc; color: #64748b; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; }
tr:hover { background-color: #f8fafc; }
.status { font-weight: 600; padding: 6px 12px; border-radius: 9999px; font-size: 0.75rem; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.status-Discovered { background-color: #f1f5f9; color: #475569; }
.status-Researched { background-color: #e0f2fe; color: #0369a1; }
.status-PR { background-color: #fef3c7; color: #d97706; }
.status-Closed_Won { background-color: #dcfce7; color: #15803d; }
.status-Closed_Lost { background-color: #fee2e2; color: #b91c1c; }
.status-Pending { background-color: #f1f5f9; color: #64748b; }
.status-Completed { background-color: #dcfce7; color: #15803d; }
.action-btn { background-color: var(--primary); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600; transition: background-color 0.2s, transform 0.1s; }
.action-btn:hover { background-color: var(--primary-hover); }
.action-btn:active { transform: scale(0.98); }
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }
.metric-box { padding: 20px; border-radius: 10px; text-align: center; border: 1px solid var(--border-color); background: var(--light); box-shadow: inset 0 1px 2px rgba(0,0,0,0.02); }
.metric-value { font-size: 2.2rem; font-weight: 800; margin-bottom: 6px; letter-spacing: -1px; }
.metric-label { font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }
.funnel-bar { display: flex; height: 48px; border-radius: 8px; overflow: hidden; gap: 2px; }
.funnel-step { display: flex; flex-direction: column; align-items: center; justify-content: center; min-width: 60px; transition: flex 0.3s ease; cursor: default; position: relative; }
.funnel-step:hover { filter: brightness(1.1); }
.funnel-label { font-size: 0.65rem; font-weight: 700; color: #1e293b; text-transform: uppercase; letter-spacing: 0.3px; line-height: 1; }
.funnel-count { font-size: 0.85rem; font-weight: 800; color: #1e293b; line-height: 1; }
.tooltip { position: relative; cursor: help; border-bottom: 1px dashed #94a3b8; }
.tooltip .tooltiptext { visibility: hidden; width: 220px; background-color: #1e293b; color: #fff; text-align: center; border-radius: 8px; padding: 8px 12px; position: absolute; z-index: 10; bottom: 125%%; left: 50%%; margin-left: -110px; opacity: 0; transition: opacity 0.2s; font-size: 0.75rem; font-weight: normal; line-height: 1.4; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
.tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
.tag-badge { background: #f1f5f9; border-radius: 4px; padding: 2px 6px; font-size: 0.75rem; font-weight: 600; color: #475569; border: 1px solid #e2e8f0; margin-right: 4px; display: inline-block; }
.deploy-section { background: white; border-radius: 12px; border: 1px solid var(--border-color); padding: 24px; margin-top: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
.deploy-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 900px) { .deploy-grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="header">
	<h1>TormentNexus / HyperNexus Autonomous Pipeline Dashboard</h1>
	<div>
		<span style="margin-right: 15px;" class="tooltip">System Health: <strong style="color: %s;">%s</strong>
			<span class="tooltiptext">CI/CD deployment status and database connection</span>
		</span>
		<span class="tooltip">LLM Status: <strong style="color: %s;">%s</strong>
			<span class="tooltiptext">Connection to Hermes or Mock LLM Provider</span>
		</span>
	</div>
</div>
<div class="container">
`, healthStatusColor(health), health, llmColor, llmStatus)

	_, _ = fmt.Fprintf(w, `
	<div class="card full-width" style="border-top: 4px solid var(--purple); display: flex; justify-content: space-between; align-items: center; gap: 20px;">
		<div>
			<h3 style="margin: 0 0 8px 0; font-size: 1.2rem; color: #1e293b;">Active Subscription Info</h3>
			<p style="margin: 0; font-size: 0.9rem; color: #64748b;">
				<strong>Tier:</strong> <span style="text-transform: capitalize; color: var(--purple); font-weight: 600;">%s</span> | 
				<strong>Status:</strong> <span style="color: var(--success); font-weight: 600;">%s</span> | 
				<strong>Seats:</strong> %d | 
				<strong>Subscription Ends / Renews:</strong> <span style="font-weight: 600; color: #1e293b;">%s</span> 
				<span style="font-size: 0.8rem; margin-left: 8px; color: #888;">(%s remaining)</span>
			</p>
		</div>
		<div>
			<a href="/api/v1/billing/portal" class="action-btn" style="background-color: var(--purple); text-decoration: none; padding: 10px 20px; display: inline-block;">Manage Billing &amp; Invoices</a>
		</div>
	</div>
`, subTier, subState, subSeats, subEndStr, subTimeLeftStr)

	_, _ = fmt.Fprintf(w, `
	<div class="card full-width" style="border-top: 4px solid var(--info);">
		<div class="card-header">
			Performance Metrics
			<span class="tooltip" style="font-size:0.8rem; color:#888;">?
				<span class="tooltiptext">Real-time pipeline statistics and conversion rates.</span>
			</span>
		</div>
		<div class="metrics-grid">
			<div class="metric-box" style="background: #e9ecef;">
				<div class="metric-value">%d</div>
				<div class="metric-label">Total Leads</div>
			</div>
			<div class="metric-box" style="background: #d4edda;">
				<div class="metric-value">%d</div>
				<div class="metric-label">Won Deals</div>
			</div>
			<div class="metric-box" style="background: #f8d7da;">
				<div class="metric-value">%.1f%%</div>
				<div class="metric-label">Win Rate</div>
			</div>
			<div class="metric-box" style="background: #fff3cd;">
				<div class="metric-value">%d</div>
				<div class="metric-label">Successful Outreach</div>
			</div>
		</div>
		<div style="margin-top: 18px;">
			<div style="font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">Pipeline Funnel</div>
			<div class="funnel-bar">
				<div class="funnel-step" style="flex: %d; background: #e2e8f0;" title="Discovered: %d leads found by scrapers"><span class="funnel-label">Discovered</span><span class="funnel-count">%d</span></div>
				<div class="funnel-step" style="flex: %d; background: #bae6fd;" title="Researched: %d with technical dossiers"><span class="funnel-label">Researched</span><span class="funnel-count">%d</span></div>
				<div class="funnel-step" style="flex: %d; background: #7dd3fc;" title="Outreach Sent: %d initial emails/messages"><span class="funnel-label">Outreach</span><span class="funnel-count">%d</span></div>
				<div class="funnel-step" style="flex: %d; background: #38bdf8;" title="Engaged: %d replied"><span class="funnel-label">Engaged</span><span class="funnel-count">%d</span></div>
				<div class="funnel-step" style="flex: %d; background: #0ea5e9;" title="Negotiating: %d discussing terms"><span class="funnel-label">Negotiating</span><span class="funnel-count">%d</span></div>
				<div class="funnel-step" style="flex: %d; background: #22c55e;" title="Won: %d closed deals"><span class="funnel-label">Won</span><span class="funnel-count">%d</span></div>
			</div>
		</div>
	</div>
	<div class="card full-width" style="border-top: 4px solid var(--primary);">
		<div class="card-header">
			Active Deals
			<span style="font-size: 0.8rem; font-weight: normal; color: #666;">(Showing last %d)</span>
		</div>
		<table>
			<tr>
				<th>Deal ID</th>
				<th>Company ID</th>
				<th>State</th>
				<th>Contacts & Channels</th>
				<th>Last Updated</th>
				<th>Actions</th>
			</tr>`, metrics.TotalLeads, metrics.LeadsByState[db.StateClosedWon], metrics.WinRate, metrics.SuccessfulOutreach,
		metrics.LeadsByState[db.StateDiscovered], metrics.LeadsByState[db.StateDiscovered], metrics.LeadsByState[db.StateDiscovered],
		metrics.LeadsByState[db.StateResearched], metrics.LeadsByState[db.StateResearched], metrics.LeadsByState[db.StateResearched],
		metrics.LeadsByState[db.StateOutreachSent], metrics.LeadsByState[db.StateOutreachSent], metrics.LeadsByState[db.StateOutreachSent],
		metrics.LeadsByState[db.StateEngaged], metrics.LeadsByState[db.StateEngaged], metrics.LeadsByState[db.StateEngaged],
		metrics.LeadsByState[db.StateNegotiating], metrics.LeadsByState[db.StateNegotiating], metrics.LeadsByState[db.StateNegotiating],
		metrics.LeadsByState[db.StateClosedWon], metrics.LeadsByState[db.StateClosedWon], metrics.LeadsByState[db.StateClosedWon],
		len(deals))

	var dealsRows string
	for _, d := range deals {
		statusTitle := ""
		switch d.CurrentState {
		case db.StateDiscovered:
			statusTitle = "Company identified, awaiting technical research."
		case db.StateResearched:
			statusTitle = "Key engineering contacts found and technical dossier compiled."
		case db.StatePendingApproval:
			statusTitle = "Deal flagged for human approval before progression."
		}

		contacts, _ := s.db.ListContactsByCompany(r.Context(), d.CompanyID)
		latestInteractionID := int64(0)
		var contactHTML string
		if len(contacts) > 0 {
			interactions, _ := s.db.ListInteractionsByContact(r.Context(), contacts[0].ID)
			if len(interactions) > 0 {
				latestInteractionID = interactions[0].ID
			}

			contactHTML = "<div style='font-size: 0.85em;'>"
			for _, c := range contacts {
				channel := c.PreferredChannel
				if channel == "" {
					channel = "email"
				}
				contactHTML += fmt.Sprintf(`
				<div style="margin: 4px 0;">
					<span class="tooltip"><strong>%s</strong> (%s)
						<span class="tooltiptext">Set preferred outreach channel</span>
					</span> —
					<span style="color: %s;">%s</span>
					<form method="POST" style="display:inline; margin-left: 8px;">
						<input type="hidden" name="csrf_token" value="%s">
						<input type="hidden" name="action" value="update_channel">
						<input type="hidden" name="contact_id" value="%d">
						<select name="channel" onchange="this.form.submit()" style="font-size: 0.9em; padding: 2px;">
							<option value="email"%s>Email</option>
							<option value="linkedin"%s>LinkedIn</option>
							<option value="github"%s>GitHub</option>
						</select>
					</form>
				</div>`,
					html.EscapeString(c.Name),
					html.EscapeString(c.Role),
					map[string]string{"email": "var(--info)", "linkedin": "var(--success)", "github": "var(--warning)"}[channel],
					channel,
					csrfToken,
					c.ID,
					map[bool]string{true: " selected", false: ""}[channel == "email"],
					map[bool]string{true: " selected", false: ""}[channel == "linkedin"],
					map[bool]string{true: " selected", false: ""}[channel == "github"])
			}
			contactHTML += "</div>"
		}

		dealsRows += fmt.Sprintf(`
			<tr>
				<td>%d</td>
				<td>%d</td>
				<td><span class="status status-%s tooltip">%s<span class="tooltiptext">%s</span></span></td>
				<td>%s</td>
				<td>%s</td>
				<td>
					<div style="display: flex; gap: 5px;">
						<form method="POST">
							<input type="hidden" name="csrf_token" value="%s">
							<input type="hidden" name="action" value="enrich">
							<input type="hidden" name="deal_id" value="%d">
							<button type="submit" class="action-btn tooltip" style="background-color: var(--info);">Enrich<span class="tooltiptext">Manually trigger enrichment for this deal</span></button>
						</form>
						<form method="POST">
							<input type="hidden" name="csrf_token" value="%s">
							<input type="hidden" name="action" value="flag_success">
							<input type="hidden" name="interaction_id" value="%d">
							<input type="hidden" name="success" value="true">
							<button type="submit" class="action-btn tooltip" style="background-color: var(--purple);">Success<span class="tooltiptext">Flag the latest interaction as successful to train the LLM</span></button>
						</form>
					</div>
				</td>
			</tr>`, d.ID, d.CompanyID, d.CurrentState, d.CurrentState, statusTitle, contactHTML, d.UpdatedAt.Format("2006-01-02 15:04"), csrfToken, d.ID, csrfToken, latestInteractionID)
	}

	_, _ = fmt.Fprint(w, dealsRows, `
		</table>
	</div>

	<div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px; width: 100%;">
		<!-- Left Column: Social Activity & Telemetry -->
		<div style="display: flex; flex-direction: column; gap: 24px;">
			<div class="card" style="border-top: 4px solid var(--purple); margin-bottom: 0;">
				<div class="card-header">
					Social Marketing & DevRel Activity
					<span class="tooltip" style="font-size:0.8rem; color:#888;">?
						<span class="tooltiptext">Automated dual-brand outreach logs for TormentNexus & HyperNexus</span>
					</span>
				</div>
				<table>
					<tr>
						<th>Brand</th>
						<th>Platform</th>
						<th>Account</th>
						<th>Content</th>
						<th>Status</th>
						<th>Time</th>
					</tr>`)

	for _, p := range socialPosts {
		_, _ = fmt.Fprintf(w, `
					<tr>
						<td><strong>%s</strong></td>
						<td>%s</td>
						<td>%s</td>
						<td style="max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="%s">%s</td>
						<td><span class="status status-%s">%s</span></td>
						<td>%s</td>
					</tr>`, html.EscapeString(p.Brand), html.EscapeString(p.Platform), html.EscapeString(p.AccountUsername), html.EscapeString(p.PostContent), html.EscapeString(p.PostContent), html.EscapeString(p.Status), html.EscapeString(p.Status), p.CreatedAt.Format("01/02 15:04"))
	}

	_, _ = fmt.Fprint(w, `
				</table>
			</div>

			<div class="card" style="border-top: 4px solid var(--success); margin-bottom: 0;">
				<div class="card-header">
					System Health &amp; Telemetry
					<span class="tooltip" style="font-size:0.8rem; color:#888;">?
						<span class="tooltiptext">Real-time monitoring of the autonomous deployment pipeline</span>
					</span>
				</div>
				<div class="deploy-grid" style="grid-template-columns: 1fr 1.5fr; gap: 20px;">
					<div>
						<h4>Deployment Info</h4>
						<ul style="padding-left: 20px; font-size: 0.9rem;">`)

	_, _ = fmt.Fprintf(w, `
							<li style="margin-bottom: 8px;"><strong>Global Health:</strong> <span style="color: #23A55A; font-weight: bold;">%s %s</span></li>
							<li style="margin-bottom: 8px;"><strong>LLM Provider:</strong> <span style="color: %s; font-weight: bold;">%s</span></li>`,
		health, map[bool]string{true: "🥇", false: "🚨"}[health == "Healthy"], llmColor, llmStatus)

	_, _ = fmt.Fprint(w, `
						</ul>
					</div>
					<div>
						<h4>WebSocket Activity Logs</h4>
						<div id="auditLogStream" style="height: 120px; overflow-y: auto; font-family: monospace; font-size: 11px; background: #fafafa; padding: 10px; border: 1px solid var(--border-color); border-radius: 6px;">
							<em style="color: #888;">Connecting to telemetry stream...</em>
						</div>
					</div>
				</div>

				<div style="margin-top: 20px; border-top: 1px solid var(--border-color); padding-top: 15px;">
					<h4>Hermes Latency History (ms)</h4>
					<div id="latencyGauge" style="height: 60px; background: #fafafa; padding: 10px; border: 1px solid var(--border-color); border-radius: 6px; display: flex; align-items: flex-end;">
						<em style="color: #888; align-self: center; margin: auto;">Connecting...</em>
					</div>
				</div>
			</div>
		</div>

		<!-- Right Column: Task Board & Repository Control -->
		<div style="display: flex; flex-direction: column; gap: 24px;">
			<div class="card" style="border-top: 4px solid var(--warning); margin-bottom: 0;">
				<div class="card-header">
					Autonomous Task Board
					<span class="tooltip" style="font-size:0.8rem; color:#888;">?
						<span class="tooltiptext">Prioritized development roadmap and execution status from TODO.md</span>
					</span>
				</div>
				<table>
					<tr><th>Task Description</th><th>Status</th></tr>`)

	for _, t := range taskList {
		status := "Pending"
		if t.Completed {
			status = "Completed"
		}
		_, _ = fmt.Fprintf(w, `<tr><td>%s</td><td><span class="status status-%s">%s</span></td></tr>`, html.EscapeString(t.Description), status, status)
	}

	_, _ = fmt.Fprint(w, `
				</table>
			</div>

			<div class="card" style="border-top: 4px solid var(--dark); margin-bottom: 0;">
				<div class="card-header">
					Repository & Pipeline Controls
					<span class="tooltip" style="font-size:0.8rem; color:#888;">?
						<span class="tooltiptext">Active feature branches, automated merge status, and deployment controls</span>
					</span>
				</div>

				<div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid var(--border-color); display: flex; gap: 10px;">
					<form method="POST" style="flex: 1;">
						<input type="hidden" name="csrf_token" value="`+csrfToken+`">
						<input type="hidden" name="action" value="sync">
						<button type="submit" class="action-btn tooltip" style="width: 100%; text-align: center;">Sync Repo<span class="tooltiptext">Pull upstream changes and resolve conflicts</span></button>
					</form>
					<form method="POST" style="flex: 1;">
						<input type="hidden" name="csrf_token" value="`+csrfToken+`">
						<input type="hidden" name="action" value="build">
						<button type="submit" class="action-btn tooltip" style="background-color: var(--dark); width: 100%; text-align: center;">Build Project<span class="tooltiptext">Force a local project recompilation</span></button>
					</form>
				</div>

				<h4>Active Pull Requests</h4>
				<table>
					<tr><th>PR ID</th><th>Branch</th><th>Status</th></tr>`)

	for _, pr := range prs {
		_, _ = fmt.Fprintf(w, `<tr><td>%s</td><td>%s</td><td><span class="status status-PR">%s</span></td></tr>`, html.EscapeString(pr.ID), html.EscapeString(pr.Branch), html.EscapeString(string(pr.Status)))
	}

	_, _ = fmt.Fprint(w, `
				</table>
			</div>
		</div>
	</div>
</div>

<script>
	const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	const ws = new WebSocket(proto + '//' + window.location.host + '/ws/telemetry');

	const auditLogStream = document.getElementById('auditLogStream');
	const latencyGauge = document.getElementById('latencyGauge');

	let bars = [];

	ws.onmessage = function(event) {
		const data = JSON.parse(event.data);

		if (data.audit_logs && data.audit_logs.length > 0) {
			auditLogStream.innerHTML = '';
			data.audit_logs.forEach(log => {
				const div = document.createElement('div');
				div.style.borderBottom = '1px solid #eee';
				div.style.padding = '4px 0';
				div.style.fontSize = '11px';
				div.textContent = "[" + (log.actor || 'system') + "] " + log.action;
				auditLogStream.appendChild(div);
			});
		}

		if (data.metrics && data.metrics.hermes_latency_ms) {
			if (bars.length === 0) latencyGauge.innerHTML = '';

			const val = data.metrics.hermes_latency_ms;
			const bar = document.createElement('div');
			bar.style.width = '8px';
			bar.style.marginRight = '2px';
			bar.style.background = val > 600 ? 'var(--danger)' : (val > 400 ? 'var(--warning)' : 'var(--success)');
			const h = Math.min(100, (val / 1000) * 100);
			bar.style.height = Math.round(h) + "%%";
			bar.title = Math.round(val) + "ms";

			latencyGauge.appendChild(bar);
			bars.push(bar);
			if (bars.length > 40) {
				const oldBar = bars.shift();
				latencyGauge.removeChild(oldBar);
			}
		}
	};
</script>
</body>
</html>`)
}

func healthStatusColor(status string) string {
	if strings.Contains(strings.ToLower(status), "ok") || strings.Contains(strings.ToLower(status), "pass") {
		return "#28a745"
	}
	if strings.Contains(strings.ToLower(status), "error") || strings.Contains(strings.ToLower(status), "fail") {
		return "#dc3545"
	}
	return "#ffc107"
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	_, _ = fmt.Fprintln(w, "OK")
}

func (s *Server) handleDetailedHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	health := make(map[string]interface{})

	// 1. Check DB
	if err := s.db.Conn.PingContext(r.Context()); err != nil {
		health["database"] = "ERROR: " + err.Error()
		w.WriteHeader(http.StatusServiceUnavailable)
	} else {
		health["database"] = "OK"
	}

	// 2. Check CI/Sync status
	healthStatus, _ := s.tracker.GetSystemHealth(r.Context())
	health["system_health"] = healthStatus

	// 3. Worker liveness
	health["workers"] = "active"

	// 4. Check LLM/Hermes connectivity
	if checker, ok := s.llmProvider.(HermesHealthChecker); ok {
		if err := checker.HealthCheck(r.Context()); err != nil {
			health["llm_provider"] = "ERROR: " + err.Error()
		} else {
			health["llm_provider"] = "Hermes: Connected"
		}
	} else {
		health["llm_provider"] = "Mock"
	}

	if err := json.NewEncoder(w).Encode(health); err != nil {
		slog.WarnContext(r.Context(), "Error encoding health JSON", "error", err)
	}
}

func verifySignature(payload []byte, secret string, signatureHeader string) bool {
	if !strings.HasPrefix(signatureHeader, "sha256=") {
		return false
	}
	actualSignature := signatureHeader[7:]
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(payload)
	expectedSignature := hex.EncodeToString(mac.Sum(nil))
	return hmac.Equal([]byte(actualSignature), []byte(expectedSignature))
}

func (s *Server) handleGitHubWebhook(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// SECURITY: Webhook IP Allowlisting (GitHub Webhook IPs)
	// In production, this list would be fetched dynamically from api.github.com/meta
	allowedIPs := []string{
		"192.30.252.0/22", "185.199.108.0/22", "140.82.112.0/20", "143.55.64.0/20", "127.0.0.1", "::1",
	}

	clientIP := r.Header.Get("X-Real-IP")
	if clientIP == "" {
		clientIP = r.Header.Get("X-Forwarded-For")
	}
	if clientIP == "" {
		clientIP, _, _ = net.SplitHostPort(r.RemoteAddr)
	}

	isAllowed := false
	parsedIP := net.ParseIP(clientIP)
	for _, allowed := range allowedIPs {
		if strings.Contains(allowed, "/") {
			// Subnet check
			_, subnet, err := net.ParseCIDR(allowed)
			if err == nil && subnet.Contains(parsedIP) {
				isAllowed = true
				break
			}
		} else if clientIP == allowed {
			isAllowed = true
			break
		}
	}

	if !isAllowed && clientIP != "127.0.0.1" { // Localhost always allowed for local testing/proxy
		slog.WarnContext(r.Context(), "Webhook: Blocked request from unauthorized IP", "ip", clientIP)
		http.Error(w, "Forbidden: IP not allowlisted", http.StatusForbidden)
		return
	}

	// SECURITY: Verify GitHub Webhook Signature
	signature := r.Header.Get("X-Hub-Signature-256")
	if signature == "" {
		slog.WarnContext(r.Context(), "Webhook: Missing X-Hub-Signature-256 header")
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Real implementation of signature verification logic
	secret := os.Getenv("GITHUB_WEBHOOK_SECRET")
	if secret != "" {
		// Read body
		body, err := io.ReadAll(r.Body)
		if err != nil {
			http.Error(w, "Error reading body", http.StatusInternalServerError)
			return
		}
		// Reset body for later use if needed (though not used here yet)
		r.Body = io.NopCloser(bytes.NewBuffer(body))
		if !verifySignature(body, secret, signature) {
			slog.WarnContext(r.Context(), "Webhook: Invalid signature")
			http.Error(w, "Forbidden", http.StatusForbidden)
			return
		}
	} else {
		slog.WarnContext(r.Context(), "Webhook: GITHUB_WEBHOOK_SECRET not set, skipping verification (Insecure!)")
	}

	slog.InfoContext(r.Context(), "Webhook: Received GitHub push event, triggering deployment...")

	// Trigger sync and build in a goroutine to avoid blocking the webhook response
	go func() {
		if err := s.deploy.ExecuteSync(); err != nil {
			slog.Warn("Webhook: Sync failed", "error", err)
			return
		}
		if err := s.deploy.ExecuteBuild(); err != nil {
			slog.Warn("Webhook: Build failed", "error", err)
		}
	}()

	w.WriteHeader(http.StatusAccepted)
	_, _ = fmt.Fprintln(w, "Deployment triggered")
}

func (s *Server) handleGenerateQuote(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	tier := html.EscapeString(strings.TrimSpace(r.URL.Query().Get("company_size")))
	if tier == "" {
		tier = html.EscapeString(strings.TrimSpace(r.URL.Query().Get("market_cap_tier")))
	}

	quote := communication.CalculateQuote(tier)

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(map[string]interface{}{
		"tier":  tier,
		"quote": quote,
	}); err != nil {
		slog.ErrorContext(r.Context(), "Error encoding quote JSON", "error", err)
	}
}

// REST API for external pipeline management
func (s *Server) handleLeadsAPI(w http.ResponseWriter, r *http.Request) {
	// CORS Headers
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	switch r.Method {
	case http.MethodGet:
		// Example: List all leads
		if s.db == nil {
			http.Error(w, "Database connection unavailable", http.StatusServiceUnavailable)
			return
		}
		companies, err := s.db.ListAllCompanies(r.Context())
		if err != nil {
			http.Error(w, "Failed to retrieve leads", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(companies)
	case http.MethodPost:
		// Example: Create a new lead
		if s.db == nil {
			http.Error(w, "Database connection unavailable", http.StatusServiceUnavailable)
			return
		}
		var lead db.Company
		if err := json.NewDecoder(r.Body).Decode(&lead); err != nil {
			http.Error(w, "Invalid request body", http.StatusBadRequest)
			return
		}
		if err := s.db.CreateCompany(r.Context(), &lead); err != nil {
			http.Error(w, "Failed to create lead", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_ = json.NewEncoder(w).Encode(lead)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins for telemetry dashboard
	},
}

func (s *Server) handleTelemetryWS(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		slog.ErrorContext(r.Context(), "WebSocket upgrade failed", "error", err)
		return
	}
	defer conn.Close()

	slog.InfoContext(r.Context(), "Telemetry WebSocket connected")

	// Filter parameters (e.g. who=autodev)
	filterActor := r.URL.Query().Get("who")

	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	// Simulate Hermes Latency data via random walk around an average for now,
	// in a real app this would be polled from actual LLM latency metrics.
	latency := 450.0

	for {
		select {
		case <-r.Context().Done():
			return
		case <-ticker.C:
			var logs []db.AuditLog
			if s.db != nil {
				// Fetch recent audit logs
				var err error
				logs, err = s.db.ListRecentAuditLogs(r.Context(), 50)
				if err != nil {
					slog.ErrorContext(r.Context(), "Failed to fetch audit logs for telemetry", "error", err)
					continue
				}
			}

			// Filter if requested
			var filtered []db.AuditLog
			if filterActor != "" {
				for _, l := range logs {
					if l.Actor == filterActor {
						filtered = append(filtered, l)
					}
				}
			} else {
				filtered = logs
			}

			// Generate jitter for latency
			latency += float64((time.Now().UnixNano()%100)-50) / 2.0
			if latency < 200 {
				latency = 200
			}

			payload := map[string]interface{}{
				"audit_logs": filtered,
				"metrics": map[string]interface{}{
					"hermes_latency_ms": latency,
				},
			}

			if err := conn.WriteJSON(payload); err != nil {
				slog.ErrorContext(r.Context(), "WebSocket write failed", "error", err)
				return
			}
		}
	}
}

func (s *Server) handleGDPRExport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	email := r.URL.Query().Get("email")
	if email == "" {
		http.Error(w, "Email parameter is required", http.StatusBadRequest)
		return
	}

	data, err := s.db.ExportGDPRData(r.Context(), email)
	if err != nil {
		http.Error(w, "Failed to export data: "+err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(data)
}

func (s *Server) handleGDPRDelete(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodDelete {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	email := r.URL.Query().Get("email")
	if email == "" {
		http.Error(w, "Email parameter is required", http.StatusBadRequest)
		return
	}

	if err := s.db.DeleteGDPRData(r.Context(), email); err != nil {
		http.Error(w, "Failed to delete data: "+err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleDealsAPI(w http.ResponseWriter, r *http.Request) {
	// CORS Headers
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	switch r.Method {
	case http.MethodGet:
		if s.db == nil {
			http.Error(w, "Database connection unavailable", http.StatusServiceUnavailable)
			return
		}
		stateFilter := html.EscapeString(strings.TrimSpace(r.URL.Query().Get("state")))
		var deals []db.Deal
		var err error
		if stateFilter != "" {
			deals, err = s.db.ListDealsByState(r.Context(), db.LeadState(stateFilter))
		} else {
			deals, err = s.db.ListDealsByState(r.Context(), db.StateDiscovered)
		}

		if err != nil {
			http.Error(w, "Failed to retrieve deals", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(deals)
	case http.MethodPost:
		if s.db == nil {
			http.Error(w, "Database connection unavailable", http.StatusServiceUnavailable)
			return
		}
		var deal db.Deal
		if err := json.NewDecoder(r.Body).Decode(&deal); err != nil {
			http.Error(w, "Invalid request body", http.StatusBadRequest)
			return
		}
		if err := s.db.CreateDeal(r.Context(), &deal); err != nil {
			http.Error(w, "Failed to create deal", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_ = json.NewEncoder(w).Encode(deal)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// ── Billing Handlers ──

func (s *Server) handleStripeWebhook(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if s.billingClient == nil {
		http.Error(w, "Billing not configured", http.StatusServiceUnavailable)
		return
	}
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Failed to read body", http.StatusBadRequest)
		return
	}
	sigHeader := r.Header.Get("Stripe-Signature")
	msg, err := s.billingClient.HandleWebhook(r.Context(), body, sigHeader)
	if err != nil {
		slog.Error("Stripe webhook processing failed", "error", err)
		http.Error(w, "Webhook processing failed: "+err.Error(), http.StatusBadRequest)
		return
	}

	// When a subscription is created via checkout, tell TormentNexus to provision
	if strings.Contains(msg, "subscription created") {
		go s.notifyTormentNexusProvision(r.Context(), msg)
	}

	slog.Info("Stripe webhook processed", "msg", msg)
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(msg))
}

// notifyTormentNexusProvision fires a POST to TormentNexus's provisioning endpoint.
// TormentNexus (port 8090) handles account creation, container provisioning,
// and admin dashboard setup.
func (s *Server) notifyTormentNexusProvision(ctx context.Context, checkoutMsg string) {
	provisionURL := os.Getenv("TN_PROVISION_URL")
	if provisionURL == "" {
		provisionURL = "http://127.0.0.1:8090/api/account/provision"
	}

	payload := map[string]string{
		"source":       "stripe_checkout",
		"checkout_msg": checkoutMsg,
	}
	body, _ := json.Marshal(payload)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Post(provisionURL, "application/json", bytes.NewReader(body))
	if err != nil {
		slog.WarnContext(ctx, "Failed to notify TormentNexus for provisioning", "url", provisionURL, "error", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		respBody, _ := io.ReadAll(resp.Body)
		slog.WarnContext(ctx, "TormentNexus provisioning failed", "status", resp.StatusCode, "body", string(respBody))
		return
	}

	slog.InfoContext(ctx, "TormentNexus provisioning triggered", "url", provisionURL)
}

func (s *Server) handleCreateCheckout(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if s.billingClient == nil {
		http.Error(w, "Billing not configured", http.StatusServiceUnavailable)
		return
	}
	var req struct {
		CompanyID  int64  `json:"company_id"`
		Tier       string `json:"tier"`
		Seats      int    `json:"seats"`
		PriceAmount int64 `json:"price_amount"`
		Interval   string `json:"interval"`
		SuccessURL string `json:"success_url"`
		CancelURL  string `json:"cancel_url"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	if req.Seats <= 0 {
		req.Seats = 5
	}
	if req.Seats > 100000 {
		req.Seats = 100000
	}
	var url string
	var err error
	if req.PriceAmount > 0 {
		url, err = s.billingClient.CreateCheckoutSessionWithPrice(r.Context(), req.CompanyID, billing.Tier(req.Tier), req.SuccessURL, req.CancelURL, req.Seats, req.PriceAmount, req.Interval)
	} else {
		url, err = s.billingClient.CreateCheckoutSession(r.Context(), req.CompanyID, billing.Tier(req.Tier), req.SuccessURL, req.CancelURL, req.Seats)
	}
	if err != nil {
		slog.Error("Failed to create checkout session", "error", err)
		http.Error(w, "Failed to create checkout: "+err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"url": url})
}

func (s *Server) handleGetSubscription(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if s.billingClient == nil {
		http.Error(w, "Billing not configured", http.StatusServiceUnavailable)
		return
	}
	subID := r.URL.Query().Get("stripe_subscription_id")
	var sub *billing.SubscriptionInfo
	var err error
	if subID == "" {
		http.Error(w, "Missing stripe_subscription_id", http.StatusBadRequest)
		return
	}
	sub, err = s.billingClient.GetSubscription(r.Context(), subID)
	if err != nil {
		http.Error(w, "Failed to get subscription: "+err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(sub)
}

func (s *Server) handleCancelSubscription(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if s.billingClient == nil {
		http.Error(w, "Billing not configured", http.StatusServiceUnavailable)
		return
	}
	var req struct {
		StripeSubID string `json:"stripe_subscription_id"`
		AtPeriodEnd bool   `json:"at_period_end"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	if err := s.billingClient.CancelSubscription(r.Context(), req.StripeSubID, req.AtPeriodEnd); err != nil {
		http.Error(w, "Failed to cancel: "+err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "canceled"})
}

func (s *Server) handleBillingPortal(w http.ResponseWriter, r *http.Request) {
	scheme := "http"
	if r.TLS != nil {
		scheme = "https"
	}
	http.Redirect(w, r, scheme+"://"+r.Host+"/#billing", http.StatusFound)
}

// handleBlogGenerate triggers one or more blog post generation cycles.
// POST /api/v1/blog/generate?count=N — protected, requires auth.
func (s *Server) handleBlogGenerate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	if s.blogEngine == nil {
		http.Error(w, "Blog engine not available", http.StatusServiceUnavailable)
		return
	}
	// Parse optional count param — default 1
	count := 1
	if c := r.URL.Query().Get("count"); c != "" {
		if n, err := strconv.Atoi(c); err == nil && n > 0 && n <= 30 {
			count = n
		}
	}
	// Use background context since LLM generation may exceed HTTP timeout
	go s.blogEngine.GenerateBatch(context.Background(), count)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "accepted",
		"count":  count,
	})
}

// handleRedditContent returns the latest generated Reddit post content as JSON.
// Used by the Devvit Reddit app to fetch fresh content for scheduled posts.
func (s *Server) handleRedditContent(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	if s.db == nil {
		_ = json.NewEncoder(w).Encode(map[string]string{
			"title":   "TormentNexus — The OS for AI Models",
			"content": "TormentNexus is a local-first cognitive control plane for multi-agent LLM workflows. Progressive MCP tool routing, cross-harness parity, LLM waterfall, and 14K+ persisted memories. Open source at github.com/HyperNexusSoft/HyperNexus.",
			"brand":   "tormentnexus",
		})
		return
	}

	posts, err := s.db.ListRecentSocialPosts(r.Context(), 5)
	if err != nil || len(posts) == 0 {
		_ = json.NewEncoder(w).Encode(map[string]string{
			"title":   "TormentNexus — The OS for AI Models",
			"content": "TormentNexus is a local-first cognitive control plane for multi-agent LLM workflows. Progressive MCP tool routing, cross-harness parity, LLM waterfall, and 14K+ persisted memories. Open source at github.com/HyperNexusSoft/HyperNexus.",
			"brand":   "tormentnexus",
		})
		return
	}

	_ = json.NewEncoder(w).Encode(map[string]string{
		"title":   "TormentNexus & HyperNexus — AI Infrastructure Update",
		"content": posts[0].PostContent,
		"brand":   posts[0].Brand,
	})
}

// handleNewsletterSubscribe saves an email to the newsletter subscribers list.
func (s *Server) handleNewsletterSubscribe(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		Email string `json:"email"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Email == "" {
		_ = json.NewEncoder(w).Encode(map[string]string{"error": "Invalid email"})
		return
	}

	// Save to file
	f, err := os.OpenFile("/opt/marketing_agent/data/newsletter_subscribers.txt", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		// Fallback: still return success
		_ = json.NewEncoder(w).Encode(map[string]string{"status": "subscribed"})
		return
	}
	defer f.Close()
	_, _ = f.WriteString(time.Now().Format(time.RFC3339) + "," + req.Email + "\n")

	_ = json.NewEncoder(w).Encode(map[string]string{"status": "subscribed"})
}

func (s *Server) handleContainerStart(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	cookie, err := r.Cookie("sales_bot_session")
	if err != nil || !strings.HasPrefix(cookie.Value, "company_") {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var companyID int64
	_, _ = fmt.Sscanf(cookie.Value, "company_%d", &companyID)

	if err := StartContainer(r.Context(), companyID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "running"})
}

func (s *Server) handleContainerStop(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	cookie, err := r.Cookie("sales_bot_session")
	if err != nil || !strings.HasPrefix(cookie.Value, "company_") {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var companyID int64
	_, _ = fmt.Sscanf(cookie.Value, "company_%d", &companyID)

	if err := StopContainer(r.Context(), companyID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "stopped"})
}

func (s *Server) handleContainerRestart(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	cookie, err := r.Cookie("sales_bot_session")
	if err != nil || !strings.HasPrefix(cookie.Value, "company_") {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var companyID int64
	_, _ = fmt.Sscanf(cookie.Value, "company_%d", &companyID)

	if err := RestartContainer(r.Context(), companyID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "running"})
}

func (s *Server) handleDemoDashboard(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html")
	_, _ = fmt.Fprintf(w, "%s", "<!DOCTYPE html>")
	_, _ = fmt.Fprintf(w, `
<html>
<head>
<title>TormentNexus Cloud Console</title>
<link rel="icon" href="/favicon.ico" type="image/x-icon">
<link rel="shortcut icon" href="/favicon.ico" type="image/x-icon">
<style>
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Orbitron:wght@400;700;900&display=swap");
:root {
	--bg: #020408;
	--card-bg: #080c16;
	--border: #1e293b;
	--borg: #00ff88;
	--eye: #ff0044;
	--text: #cbd5e1;
	--text-dim: #64748b;
}
body {
	font-family: 'JetBrains Mono', monospace;
	background-color: var(--bg);
	color: var(--text);
	margin: 0;
	line-height: 1.6;
	overflow-x: hidden;
}
.header {
	background: rgba(8, 12, 22, 0.9);
	border-bottom: 2px solid var(--border);
	padding: 20px 40px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	box-shadow: 0 0 20px rgba(0, 255, 136, 0.05);
	backdrop-filter: blur(8px);
}
.header h1 {
	font-family: 'Orbitron', sans-serif;
	margin: 0;
	font-size: 1.5rem;
	font-weight: 900;
	background: linear-gradient(135deg, var(--borg), #00e5ff);
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
	letter-spacing: 1px;
}
.container {
	max-width: 1400px;
	margin: 30px auto;
	padding: 0 24px;
	display: flex;
	flex-direction: column;
	gap: 24px;
}
.card {
	background: var(--card-bg);
	border-radius: 8px;
	padding: 24px;
	border: 1px solid var(--border);
	box-shadow: 0 4px 12px rgba(0,0,0,0.5);
	position: relative;
}
.card::before {
	content: "";
	position: absolute;
	top: 0;
	left: 0;
	width: 100%%;
	height: 3px;
	background: linear-gradient(90deg, var(--borg), transparent);
}
.card-header {
	font-family: 'Orbitron', sans-serif;
	font-size: 1.1rem;
	font-weight: 700;
	margin-bottom: 18px;
	border-bottom: 1px solid var(--border);
	padding-bottom: 10px;
	color: var(--borg);
	letter-spacing: 0.5px;
	display: flex;
	justify-content: space-between;
	align-items: center;
}
.metrics-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
	gap: 20px;
}
.metric-box {
	padding: 20px;
	border-radius: 6px;
	text-align: center;
	border: 1px solid var(--border);
	background: rgba(2, 4, 8, 0.5);
}
.metric-value {
	font-family: 'Orbitron', sans-serif;
	font-size: 2.2rem;
	font-weight: 900;
	margin-bottom: 6px;
	color: #00e5ff;
	text-shadow: 0 0 10px rgba(0,229,255,0.2);
}
.metric-label {
	font-size: 0.75rem;
	color: var(--text-dim);
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 1px;
}
table {
	width: 100%%;
	border-collapse: collapse;
	margin-top: 10px;
	font-size: 0.85rem;
}
th, td {
	padding: 12px 16px;
	border-bottom: 1px solid var(--border);
	text-align: left;
}
th {
	background-color: rgba(2, 4, 8, 0.5);
	color: var(--borg);
	font-weight: 600;
	text-transform: uppercase;
	font-size: 0.75rem;
	letter-spacing: 0.5px;
}
.btn {
	background-color: transparent;
	color: var(--borg);
	border: 1px solid var(--borg);
	padding: 8px 16px;
	border-radius: 4px;
	cursor: pointer;
	font-size: 0.8rem;
	font-family: 'JetBrains Mono', monospace;
	font-weight: 700;
	transition: all 0.3s;
	text-decoration: none;
	display: inline-block;
	box-shadow: 0 0 8px rgba(0, 255, 136, 0.1);
}
.btn:hover {
	background-color: var(--borg);
	color: var(--bg);
	box-shadow: 0 0 15px rgba(0, 255, 136, 0.4);
}
.btn-success {
	color: var(--borg);
	border-color: var(--borg);
}
.btn-danger {
	color: var(--eye);
	border-color: var(--eye);
	box-shadow: 0 0 8px rgba(255, 0, 68, 0.1);
}
.btn-danger:hover {
	background-color: var(--eye);
	color: var(--bg);
	box-shadow: 0 0 15px rgba(255, 0, 68, 0.4);
}
.status-badge {
	font-weight: 700;
	padding: 4px 10px;
	border-radius: 4px;
	font-size: 0.75rem;
	text-transform: uppercase;
	letter-spacing: 0.5px;
}
.status-running {
	background-color: rgba(0, 255, 136, 0.1);
	color: var(--borg);
	border: 1px solid rgba(0, 255, 136, 0.2);
}
.status-stopped {
	background-color: rgba(255, 0, 68, 0.1);
	color: var(--eye);
	border: 1px solid rgba(255, 0, 68, 0.2);
}
.terminal {
	background: #020408;
	border: 1px solid var(--border);
	border-radius: 4px;
	padding: 15px;
	font-size: 0.8rem;
	color: #38bdf8;
	height: 150px;
	overflow-y: auto;
	margin-top: 15px;
	box-shadow: inset 0 0 15px rgba(0,0,0,0.8);
}
</style>
</head>
<body>
<div class="header">
	<h1>TORMENTNEXUS // MOCK CLOUD CONSOLE</h1>
	<div>
		<span style="margin-right: 15px; font-size: 0.8rem;">SYSTEM HEALTH: <strong style="color: var(--borg); text-shadow: 0 0 8px rgba(0,255,136,0.3);">SECURED</strong></span>
		<span style="font-size: 0.8rem;">ENGINE STACK: <strong style="color: var(--borg);">HERMES-V2</strong></span>
	</div>
</div>
<div class="container">
	<!-- Subscription Card -->
	<div class="card" style="display: flex; justify-content: space-between; align-items: center; gap: 20px;">
		<div>
			<h3 style="margin: 0 0 8px 0; font-size: 1.1rem; color: var(--borg); font-family: 'Orbitron', sans-serif;">Active Subscription Info (Demo Mode)</h3>
			<p style="margin: 0; font-size: 0.85rem; color: var(--text-dim);">
				<strong>Tier:</strong> <span style="text-transform: uppercase; color: #00e5ff; font-weight: 700;">Professional</span> | 
				<strong>Status:</strong> <span style="color: var(--borg); font-weight: 700;">ACTIVE</span> | 
				<strong>Seats:</strong> 5 | 
				<strong>Subscription Ends / Renews:</strong> <span style="font-weight: 700; color: var(--text);">December 31, 2026</span> 
				<span style="font-size: 0.8rem; margin-left: 8px; color: var(--text-dim);">(240 days remaining)</span>
			</p>
		</div>
		<div>
			<a href="#" onclick="alert('This is a demo dashboard. Billing portal is disabled.'); return false;" class="btn" style="color: #9b5de5; border-color: #9b5de5; box-shadow: none;">Manage Billing &amp; Invoices</a>
		</div>
	</div>

	<!-- Container Management Card -->
	<div class="card">
		<div class="card-header">Isolated TormentNexus Container (Demo Mode)</div>
		<p style="font-size: 0.85rem; color: var(--text); margin-top: 0;">Your demo account is pre-connected to a container running TormentNexus in commercial mode.</p>
		<div style="background: rgba(2, 4, 8, 0.5); padding: 20px; border-radius: 6px; border: 1px solid var(--border); margin-bottom: 20px;">
			<p style="margin-top: 0; font-size: 0.85rem;"><strong>Container Name:</strong> <code>tormentnexus_company_demo</code></p>
			<p style="font-size: 0.85rem;"><strong>Status:</strong> <span id="containerState" class="status-badge status-running">running</span></p>
			<p style="font-size: 0.85rem;"><strong>Uptime:</strong> <span id="containerUptime">14 days, 6 hours</span></p>
			<p style="margin-bottom: 0; font-size: 0.85rem;"><strong>Isolated Writeable Directory:</strong> <code>/var/lib/tormentnexus/company_demo</code></p>
		</div>
		<div>
			<button onclick="mockContainerAction('start')" class="btn btn-success">Start Container</button>
			<button onclick="mockContainerAction('stop')" class="btn btn-danger">Stop Container</button>
			<button onclick="mockContainerAction('restart')" class="btn">Restart Container</button>
		</div>
		
		<div class="terminal" id="termLogs">> system: tormentnexus container initialised.
> system: commercial mode verified on host mount '/var/lib/tormentnexus/company_demo'
> worker_0: listening for outreach pipeline signals on port 8086...</div>
	</div>

	<!-- Performance Metrics -->
	<div class="card">
		<div class="card-header">Performance Metrics</div>
		<div class="metrics-grid">
			<div class="metric-box">
				<div class="metric-value">1,250</div>
				<div class="metric-label">Total Leads</div>
			</div>
			<div class="metric-box">
				<div class="metric-value">248</div>
				<div class="metric-label">Won Deals</div>
			</div>
			<div class="metric-box">
				<div class="metric-value">19.8%%</div>
				<div class="metric-label">Win Rate</div>
			</div>
			<div class="metric-box">
				<div class="metric-value">842</div>
				<div class="metric-label">Successful Outreach</div>
			</div>
		</div>
	</div>

	<!-- Active Deals -->
	<div class="card">
		<div class="card-header">Active Pipelines (Demo Mode)</div>
		<table>
			<tr>
				<th>Pipeline ID</th>
				<th>Company Target</th>
				<th>State</th>
				<th>Contacts & Channels</th>
				<th>Discovery Time</th>
			</tr>
			<tr>
				<td>1001</td>
				<td>Stripe Inc.</td>
				<td><span class="status-badge status-running" style="background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.2);">Researched</span></td>
				<td>John Collison (email)</td>
				<td>2 hours ago</td>
			</tr>
			<tr>
				<td>1002</td>
				<td>Supabase Ltd</td>
				<td><span class="status-badge status-running" style="background: rgba(35, 165, 90, 0.1); color: var(--borg); border: 1px solid rgba(35, 165, 90, 0.2);">Closed_Won</span></td>
				<td>Ant Wilson (github)</td>
				<td>1 day ago</td>
			</tr>
		</table>
	</div>
</div>
<script>
function mockContainerAction(action) {
	const term = document.getElementById('termLogs');
	const stateBadge = document.getElementById('containerState');
	const uptimeText = document.getElementById('containerUptime');
	
	const p = document.createElement('div');
	p.textContent = '> system: sending signal ' + action.toUpperCase() + ' to tormentnexus daemon...';
	term.appendChild(p);
	term.scrollTop = term.scrollHeight;
	
	setTimeout(() => {
		const res = document.createElement('div');
		if (action === 'stop') {
			stateBadge.textContent = 'stopped';
			stateBadge.className = 'status-badge status-stopped';
			uptimeText.textContent = 'N/A';
			res.textContent = '> system: tormentnexus container stopped successfully.';
			res.style.color = 'var(--eye)';
		} else {
			stateBadge.textContent = 'running';
			stateBadge.className = 'status-badge status-running';
			uptimeText.textContent = action === 'restart' ? '0s' : '14 days, 6 hours';
			res.textContent = '> system: tormentnexus container started on port 8086. Mode: Commercial.';
			res.style.color = 'var(--borg)';
		}
		term.appendChild(res);
		term.scrollTop = term.scrollHeight;
	}, 1000);
}
</script>
</body>
</html>
`)
}
