package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"gitlab.com/robertpelloni/marketing_agent/internal/autodev"
	"gitlab.com/robertpelloni/marketing_agent/internal/billing"
	"gitlab.com/robertpelloni/marketing_agent/internal/communication"
	"gitlab.com/robertpelloni/marketing_agent/internal/config"
	"gitlab.com/robertpelloni/marketing_agent/internal/crm"
	"gitlab.com/robertpelloni/marketing_agent/internal/db"
	"gitlab.com/robertpelloni/marketing_agent/internal/deploy"
	"gitlab.com/robertpelloni/marketing_agent/internal/enrichment"
	"gitlab.com/robertpelloni/marketing_agent/internal/gitcheck"
	"gitlab.com/robertpelloni/marketing_agent/internal/gitres"
	"gitlab.com/robertpelloni/marketing_agent/internal/llm"
	"gitlab.com/robertpelloni/marketing_agent/internal/researcher"
	"gitlab.com/robertpelloni/marketing_agent/internal/sales"
	"gitlab.com/robertpelloni/marketing_agent/internal/scraper"
	"gitlab.com/robertpelloni/marketing_agent/internal/web"
	"gitlab.com/robertpelloni/marketing_agent/pkg/agents"

	_ "github.com/lib/pq" // PostgreSQL driver
)

func main() {
	reconcile := flag.Bool("reconcile", false, "Run branch reconciliation and exit")
	inventory := flag.Bool("inventory", false, "Generate submodule inventory and exit")
	flag.Parse()

	if *inventory {
		slog.Info("Generating submodule inventory")
		table, err := gitcheck.GenerateSubmoduleInventory()
		if err != nil {
			slog.Error("Failed to generate inventory", "error", err)
			os.Exit(1)
		}
		fmt.Println(table)
		return
	}

	if *reconcile {
		slog.Info("Running intelligent merge engine")
		if err := gitres.ReconcileBranches(); err != nil {
			slog.Error("Reconciliation failed", "error", err)
			os.Exit(1)
		}
		slog.Info("Reconciliation complete")
		return
	}

	slog.Info("Starting TormentNexus Autonomous Sales Bot")

	// 0. Load Configuration
	cfg := config.Load()

	// 1. Initialize Database
	database, err := db.NewDB(cfg.DatabaseURL)
	if err != nil {
		slog.Error(fmt.Sprintf("Could not connect to database: %v", err))
		os.Exit(1)
	}
	if cfg.SecretKey != "" {
		database.SetSecretKey(cfg.SecretKey)
	}
	defer func() { _ = database.Close() }()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 2. Setup Scraper — HN "Who is Hiring" + LinkedIn + GitHub Issues + Reddit
	linkedInSource := scraper.NewLinkedInSource()
	if os.Getenv("LINKEDIN_USERNAME") != "" && os.Getenv("LINKEDIN_PASSWORD") != "" {
		linkedInSource.SetCredentials(os.Getenv("LINKEDIN_USERNAME"), os.Getenv("LINKEDIN_PASSWORD"))
		slog.Info("Scraper: LinkedIn credentials configured.")
	} else {
		slog.Info("Scraper: No LinkedIn credentials found, running in simulation mode.")
	}

	redditSource := scraper.NewRedditSource()

	sources := []scraper.LeadSource{
		&scraper.HNWhoIsHiringSource{Client: http.DefaultClient},
		linkedInSource,
		&scraper.GitHubIssueSource{Client: http.DefaultClient, Token: cfg.GitHubToken},
		redditSource,
	}

	s := scraper.NewScraper(database, sources)

	keywords := []string{"AI Engineer", "LLM Orchestration", "Agentic Workflows", "AI Platform", "ML Infrastructure"}
	go s.Run(ctx, 2*time.Hour, keywords)

	// 2a. Setup CRM Integration
	var crmClient crm.CRMClient
	if cfg.CRMBaseURL != "" && cfg.CRMAPIKey != "" {
		slog.Info(fmt.Sprintf("CRM: Initializing production REST CRM client at %s", cfg.CRMBaseURL))
		crmClient = crm.NewRestCRMClient(cfg.CRMBaseURL, cfg.CRMAPIKey)
	} else {
		slog.Info("CRM: Initializing mock CRM client (missing configuration).")
		crmClient = crm.NewMockCRMClient()
	}

	// 2b. Setup Enricher — Hunter.io + Apollo.io + GitHub fallback with FallbackSource
	var enrichmentSources []enrichment.EnrichmentSource
	var sourceNames []string

	if cfg.HunterAPIKey != "" {
		slog.Info("Enrichment: Initializing Hunter.io source.")
		enrichmentSources = append(enrichmentSources, enrichment.NewHunterSource(cfg.HunterAPIKey))
		sourceNames = append(sourceNames, "Hunter.io")
	} else {
		slog.Info("Enrichment: No HUNTER_API_KEY set - skipping Hunter.io.")
	}

	if cfg.ApolloAPIKey != "" {
		slog.Info("Enrichment: Initializing Apollo.io source.")
		enrichmentSources = append(enrichmentSources, enrichment.NewApolloSource(cfg.ApolloAPIKey))
		sourceNames = append(sourceNames, "Apollo.io")
	} else {
		slog.Info("Enrichment: No APOLLO_API_KEY set - skipping Apollo.io.")
	}

	// GitHub commit email fallback — works even when Hunter/Apollo fail
	if cfg.GitHubToken != "" {
		slog.Info("Enrichment: Initializing GitHub commit email source (last-resort fallback).")
		enrichmentSources = append(enrichmentSources, enrichment.NewGitHubEnrichSource(cfg.GitHubToken))
		sourceNames = append(sourceNames, "GitHub Commits")
	} else {
		slog.Info("Enrichment: No GITHUB_TOKEN set - skipping GitHub commit email fallback.")
	}

	if len(enrichmentSources) == 0 {
		slog.Info("Enrichment: No real sources configured.")
	}

	// Wrap sources in fallback chain for ordered retry with clear logging
	fallbackSource := enrichment.NewFallbackSource(enrichmentSources, sourceNames)
	slog.Info(fmt.Sprintf("Enrichment: Fallback chain configured — %s", fallbackSource.Status()))

	e := enrichment.NewEnricher(database, []enrichment.EnrichmentSource{fallbackSource}, crmClient)
	go e.Run(ctx, 1*time.Hour)

	// 2c. Setup Researcher — GitHub, Tech Blogs, and RSS Feeds
	rssFeeds := []string{
		"https://hnrss.org/frontpage?points=10",
		"https://blog.rust-lang.org/feed.xml",
		"https://go.dev/blog/feed.atom",
		"https://engineering.fb.com/feed/",
		"https://netflixtechblog.com/feed/",
		"https://github.blog/category/engineering/feed/",
	}
	crawlers := []researcher.Crawler{
		&researcher.GitHubCrawler{Client: http.DefaultClient},
		&researcher.BlogCrawler{Client: http.DefaultClient},
		&researcher.RSSFeedCrawler{
			Feeds:  rssFeeds,
			Client: http.DefaultClient,
		},
	}
	processor := &researcher.DefaultDossierProcessor{}
	r := researcher.NewResearcher(database, crawlers, processor, crmClient)
	go r.Run(ctx, 1*time.Hour)

	crmWorker := crm.NewWorker(database, crmClient)
	go crmWorker.Run(ctx, 30*time.Minute)

	// 2f. Setup LLM Provider — DeepSeek > Hermes > Mock
	var llmProvider llm.LLMProvider
	if cfg.DeepSeekAPIKey != "" {
		slog.Info(fmt.Sprintf("LLM: Initializing DeepSeek provider (model: %s)", cfg.DeepSeekModel))
		llmProvider = llm.NewDeepSeekLLMProvider(llm.DeepSeekConfig{
			APIKey:  cfg.DeepSeekAPIKey,
			Model:   cfg.DeepSeekModel,
			BaseURL: cfg.DeepSeekBaseURL,
		})

		if err := llmProvider.(*llm.DeepSeekLLMProvider).HealthCheck(ctx); err != nil {
			slog.Info(fmt.Sprintf("LLM: WARNING — DeepSeek health check failed: %v", err))
		} else {
			slog.Info("LLM: DeepSeek health check passed ✓")
		}
	} else if cfg.HermesAPIURL != "" && cfg.HermesAPIKey != "" {
		slog.Info(fmt.Sprintf("LLM: Initializing Hermes provider at %s (model: %s)", cfg.HermesAPIURL, cfg.HermesModel))
		llmProvider = llm.NewHermesLLMProvider(llm.HermesConfig{
			BaseURL: cfg.HermesAPIURL,
			APIKey:  cfg.HermesAPIKey,
			Model:   cfg.HermesModel,
		})

		if err := llmProvider.(*llm.HermesLLMProvider).HealthCheck(ctx); err != nil {
			slog.Info(fmt.Sprintf("LLM: WARNING — Hermes health check failed: %v", err))
		} else {
			slog.Info("LLM: Hermes health check passed ✓")
		}
	} else {
		slog.Info("LLM: Initializing Mock LLM Provider (set DEEPSEEK_API_KEY or HERMES_API_URL + HERMES_API_KEY for real LLM).")
		llmProvider = &llm.MockLLMProvider{}
	}

	// 2d. Setup Target Discovery
	outreachWorker := agents.NewTargetDiscoveryWorker(database, llmProvider)
	go outreachWorker.Run(ctx, 30*time.Minute)

	// 2e. Setup Deployer
	var ciTracker deploy.CITracker
	var dispatcher deploy.WorkflowDispatcher

	if cfg.GitHubRepository != "" {
		parts := strings.Split(cfg.GitHubRepository, "/")
		if len(parts) == 2 {
			slog.Info(fmt.Sprintf("CI: Initializing GitHub CI Tracker and Dispatcher for %s", cfg.GitHubRepository))
			ciTracker = deploy.NewGitHubCITracker(parts[0], parts[1])
			dispatcher = deploy.NewGitHubDispatcher(parts[0], parts[1])
		}
	}

	if ciTracker == nil {
		slog.Info("CI: Initializing Mock CI Tracker (missing GITHUB_REPOSITORY).")
		ciTracker = &deploy.MockCITracker{}
	}

	deployer := deploy.NewDeployer(ciTracker, dispatcher)
	go deployer.Run(ctx, cfg.DeploySyncInterval)
	go deployer.MonitorDeployment(ctx, cfg.DeploySyncInterval)

	// 2k. Setup Social Media Poster Agent
	socialPoster := agents.NewSocialPosterWorker(database, llmProvider)
	go socialPoster.Run(ctx, 4*time.Hour)

	// 2l. Setup Auto-Blog Engine (SEO content for tormentnexus.site & hypernexus.site)
	blogEngine := agents.NewBlogEngine(llmProvider, "/opt/marketing_agent/blog_output")
	go blogEngine.Run(ctx, 4*time.Hour)

	// 2m. Setup GitHub Discussions Engager (reply to MCP/AI discussions)
	githubDiscussions := agents.NewGitHubDiscussionsEngager(cfg.GitHubToken)
	go githubDiscussions.Run(ctx, 6*time.Hour)

	// 2g. Setup Intent Classifier
	var classifier communication.IntentClassifier
	if cfg.HermesAPIURL != "" && cfg.HermesAPIKey != "" {
		slog.Info("Communication: Initializing LLM-backed Intent Classifier via Hermes.")
		classifier = communication.NewLLMIntentClassifier(llmProvider)
	} else {
		slog.Info("Communication: Initializing Mock Intent Classifier.")
		classifier = &communication.MockIntentClassifier{}
	}

	responder := communication.NewRAGResponseGenerator(database, llmProvider)
	strategy := communication.NewLearningSalesEngine(database, crmClient, llmProvider)

	// 2h. Setup Email Sender — Gmail OAuth2, SMTP, Draft
	var emailSender communication.EmailSender
	if os.Getenv("GOOGLE_CLIENT_ID") != "" && os.Getenv("GOOGLE_CLIENT_SECRET") != "" && os.Getenv("GOOGLE_REFRESH_TOKEN") != "" && !cfg.DryRun {
		slog.Info("Email: Initializing Gmail OAuth2 sender")
		oauth2Sender := communication.NewGmailOAuth2Sender()
		if err := oauth2Sender.HealthCheck(context.Background()); err != nil {
			slog.Warn("Email: Gmail OAuth2 health check failed, falling back to SMTP", "error", err)
		} else {
			emailSender = oauth2Sender
			slog.Info("Email: Gmail OAuth2 sender configured successfully")
		}
	}
	if emailSender == nil && cfg.SMTPHost != "" && cfg.SMTPUsername != "" && cfg.SMTPPassword != "" && !cfg.DryRun {
		slog.Info(fmt.Sprintf("Email: Initializing SMTP sender via %s:%d as %s", cfg.SMTPHost, cfg.SMTPPort, cfg.SMTPUsername))
		emailSender = communication.NewSMTPSender(communication.SMTPConfig{
			Host:     cfg.SMTPHost,
			Port:     cfg.SMTPPort,
			Username: cfg.SMTPUsername,
			Password: cfg.SMTPPassword,
			From:     cfg.SMTPFrom,
			FromName: cfg.SMTPFromName,
		})
	}
	if emailSender == nil && cfg.DryRun && cfg.IMAPHost != "" && cfg.IMAPUsername != "" && cfg.IMAPPassword != "" {
		slog.Info(fmt.Sprintf("Email: DRY RUN mode — saving drafts to %s via IMAP.", cfg.IMAPFolder))
		emailSender = communication.NewDraftSender(cfg.IMAPHost, cfg.IMAPPort, cfg.IMAPUsername, cfg.IMAPPassword)
	}
	if emailSender == nil {
		if cfg.DryRun {
			slog.Info("Email: DRY RUN mode — no IMAP configured, emails will be logged only.")
		} else {
			slog.Info("Email: No email sender configured — outbound emails will be logged but not sent.")
		}
		emailSender = &communication.NoopEmailSender{}
	}

	var billingClient billing.BillingClient
	if cfg.StripeAPIKey != "" {
		slog.Info("Billing: Initializing Stripe Billing Client.")
		priceIDs := map[billing.Tier]string{
			billing.TierCommunity:     cfg.StripePriceCommunity,
			billing.TierProfessional:  cfg.StripePriceProfessional,
			billing.TierEnterprise:    cfg.StripePriceEnterprise,
			billing.TierHyperNexusPro: cfg.StripePriceHyperNexusPro,
		}
		billingStore := &billing.DBAdapter{DB: database.Conn}
		billingClient = billing.NewStripeBillingClient(cfg.StripeAPIKey, cfg.StripeWebhookSecret, priceIDs, billingStore)
	} else {
		slog.Info("Billing: No STRIPE_API_KEY set. Initializing Mock Billing Client.")
		billingStore := &billing.DBAdapter{DB: database.Conn}
		billingClient = billing.NewMockBillingClient(billingStore)
	}

	orderProcessor := sales.NewOrderProcessor(database, billingClient, crmClient)

	commManager := communication.NewManager(database, classifier, responder, strategy, orderProcessor, emailSender)

	// Initialize Objection Library and attach to manager
	objectionLib := communication.NewObjectionLibrary()
	commManager.SetObjectionLibrary(objectionLib)
	go commManager.Run(ctx, 30*time.Minute)

	// 2j. Setup Cadence-aware outreach scheduling
	cadenceManager := communication.NewCadenceAwareManager(commManager, database)
	go cadenceManager.RunCadence(ctx, 15*time.Minute) // checks every 15min for next touch

	// 2i. Setup IMAP Email Receiver
	if cfg.IMAPHost != "" && cfg.IMAPUsername != "" && cfg.IMAPPassword != "" {
		slog.Info(fmt.Sprintf("Email: Initializing IMAP receiver from %s:%d (polling every %v)", cfg.IMAPHost, cfg.IMAPPort, cfg.IMAPPollInterval))
		imapReceiver := communication.NewEmailReceiver(communication.IMAPConfig{
			Host:     cfg.IMAPHost,
			Port:     cfg.IMAPPort,
			Username: cfg.IMAPUsername,
			Password: cfg.IMAPPassword,
			Folder:   cfg.IMAPFolder,
		}, commManager)
		go imapReceiver.Run(ctx, cfg.IMAPPollInterval)
	} else {
		slog.Info("Email: No IMAP configured — inbound emails will not be received.")
	}

	// 3. Initialize Autonomous Development
	taskManager := autodev.NewTaskManager("TODO.md")
	agent := autodev.NewLocalAgent(llmProvider)

	var prManager gitcheck.PRManager
	if cfg.GitHubRepository != "" {
		parts := strings.Split(cfg.GitHubRepository, "/")
		if len(parts) == 2 {
			slog.Info(fmt.Sprintf("Autodev: Initializing GitHub PR Manager for %s", cfg.GitHubRepository))
			prManager = gitcheck.NewGitHubPRManager(parts[0], parts[1])
		}
	}
	if prManager == nil {
		slog.Info("Autodev: Initializing Mock PR Manager (missing GITHUB_REPOSITORY).")
		prManager = &gitcheck.MockPRManager{}
	}

	orchestrator := autodev.NewOrchestrator(database, taskManager, agent, prManager, ciTracker)
	go orchestrator.Run(ctx, 1*time.Hour)

	// 4. Start Web Server
	webServer := web.NewServer(database, deployer, ciTracker, taskManager, llmProvider, billingClient, blogEngine)

	srv := &http.Server{
		Addr:    ":" + cfg.Port,
		Handler: webServer,
	}

	go func() {
		slog.Info(fmt.Sprintf("Web Dashboard: Listening on :%s", cfg.Port))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Info(fmt.Sprintf("Web server error: %v", err))
		}
	}()

	// 5. Graceful Shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		slog.Info("Shutting down: Signal received, initiating graceful drain...")
		cancel()
		shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer shutdownCancel()
		if err := srv.Shutdown(shutdownCtx); err != nil {
			slog.Info(fmt.Sprintf("Web server shutdown error: %v", err))
		}
		slog.Info("Shutting down: Done.")
		os.Exit(0)
	}()

	setupSystray(cancel, cfg.Port)
}
