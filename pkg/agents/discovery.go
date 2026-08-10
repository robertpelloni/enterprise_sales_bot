package agents

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"strings"
	"time"

	"github.com/google/go-github/v60/github"
	"gitlab.com/robertpelloni/marketing_agent/internal/db"
	"gitlab.com/robertpelloni/marketing_agent/internal/llm"
)

// TargetDiscoveryWorker scans for new opportunities (e.g., GitHub, MCP servers).
type TargetDiscoveryWorker struct {
	db  *db.DB
	llm llm.LLMProvider
}

// NewTargetDiscoveryWorker creates a new discovery worker.
func NewTargetDiscoveryWorker(database *db.DB, llmProvider llm.LLMProvider) *TargetDiscoveryWorker {
	return &TargetDiscoveryWorker{db: database, llm: llmProvider}
}

// Run starts the target discovery background loop.
func (w *TargetDiscoveryWorker) Run(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	slog.Info(fmt.Sprintf("TormentNexus Outreach: Target discovery worker started (interval: %v)...", interval))

	// Run first discovery cycle immediately
	w.discover(ctx)

	for {
		select {
		case <-ctx.Done():
			slog.Info("TormentNexus Outreach: Target discovery worker stopping...")
			return
		case <-ticker.C:
			w.discover(ctx)
		}
	}
}

func (w *TargetDiscoveryWorker) discover(ctx context.Context) {
	slog.Info("TormentNexus Outreach: Scanning for new MCP server repositories on GitHub...")

	client := github.NewClient(nil)
	token := os.Getenv("GITHUB_TOKEN")
	if token != "" {
		client = github.NewClient(nil).WithAuthToken(token)
	}

	query := "model-context-protocol OR mcp-server language:Go language:TypeScript"
	if w.llm != nil {
		suggested, err := w.llm.Generate(ctx, llm.Prompt{
			System: "You are a lead generation strategist for an AI tool router. Suggest a GitHub code/repository search query (maximum 8 words, using OR/AND, tags, or languages) to find developer projects using model context protocol, agent frameworks, or LLM routing. Output ONLY the query string, no other text or quotes. Do not include prefix tags or explanations. IMPORTANT: The query must contain at least one text search term (not just qualifiers like topic: or language:).",
			User: "Provide a single query string.",
		})
		if err == nil && strings.TrimSpace(suggested) != "" {
			cleanQuery := strings.TrimSpace(suggested)
			cleanQuery = strings.Trim(cleanQuery, "\"`'")
			// Validate that query has at least one text search term (not just qualifiers)
			if cleanQuery != "" && !strings.HasPrefix(cleanQuery, "topic:") && !strings.HasPrefix(cleanQuery, "language:") {
				query = cleanQuery
				slog.Info(fmt.Sprintf("TargetDiscoveryWorker: LLM suggested dynamic search query: %q", query))
			} else {
				slog.Info(fmt.Sprintf("TargetDiscoveryWorker: LLM query rejected (only qualifiers): %q, using default", cleanQuery))
			}
		}
	}

	opts := &github.SearchOptions{
		Sort:	"updated",
		Order:	"desc",
		ListOptions: github.ListOptions{
			PerPage: 10,
		},
	}

	result, _, err := client.Search.Repositories(ctx, query, opts)
	if err != nil {
		slog.Info(fmt.Sprintf("TormentNexus Outreach Error: GitHub search failed: %v", err))
		return
	}

	for _, repo := range result.Repositories {
		domain := fmt.Sprintf("github.com/%s", repo.GetFullName())
		// #nosec G706 -- Domain name is used for context in informational logs
		slog.Info(fmt.Sprintf("TormentNexus Outreach: Evaluating repository: %s", domain))

		// Check if company already exists
		existing, _ := w.db.GetCompanyByDomain(ctx, domain)
		if existing != nil {
			continue
		}

		// Create new lead
		company := &db.Company{
			Name:		repo.GetName(),
			Domain:		domain,
			TechStack:	[]string{repo.GetLanguage()},
			HiringSignals:	[]string{"Active Open Source contributor"},
			MarketCapTier:	"SMB",	// Default for discovered repos
		}

		if err := w.db.CreateCompany(ctx, company); err != nil {
			// #nosec G706 -- Domain name is used for context in error logs
			slog.Info(fmt.Sprintf("TormentNexus Outreach Warning: Failed to create company %s: %v", domain, err))
			continue
		}

		deal := &db.Deal{
			CompanyID:	company.ID,
			CurrentState:	db.StateDiscovered,
		}

		if err := w.db.CreateDeal(ctx, deal); err != nil {
			// #nosec G706 -- Domain name is used for context in error logs
			slog.Info(fmt.Sprintf("TormentNexus Outreach Warning: Failed to create deal for %s: %v", domain, err))
		} else {
			// #nosec G706 -- Domain name is used for context in success logs
			slog.Info(fmt.Sprintf("TormentNexus Outreach Success: New lead discovered: %s", domain))
		}
	}
}
