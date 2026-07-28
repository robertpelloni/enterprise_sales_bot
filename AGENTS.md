# AI DevKit Rules

## Project Context

This project uses ai-devkit for structured AI-assisted development. Phase documentation is located in `docs/ai/`.

## Documentation Structure

- `docs/ai/requirements/` - Problem understanding and requirements
- `docs/ai/design/` - System architecture and design decisions
- `docs/ai/planning/` - Task breakdown and project planning
- `docs/ai/implementation/` - Implementation guides and notes
- `docs/ai/testing/` - Testing strategy and test cases
- `docs/ai/deployment/` - Deployment and infrastructure docs

## Code Style & Standards

- Follow Go conventions and `gofmt` formatting
- Use `slog` for structured logging
- PostgreSQL for all persistent data
- Error handling with `fmt.Errorf("context: %w", err)`

## Development Workflow

1. Review phase documentation before implementing features
2. Keep requirements and design docs updated
3. Write tests alongside implementation
4. Update CHANGELOG.md for significant changes

## Key Commands

```bash
# Build
go build -o bin/marketing_agent ./cmd/marketing_agent/

# Test
go test ./...

# Run locally
./bin/marketing_agent

# Deploy to production
scp bin/marketing_agent root@5.161.250.43:/opt/marketing_agent/bin/
ssh root@5.161.250.43 "systemctl restart marketing-agent"
```

## Project Structure

```
marketing_agent/
├── cmd/marketing_agent/    # Main entrypoint
├── internal/               # Core business logic
│   ├── billing/           # Stripe integration
│   ├── communication/     # Outreach & reply handling
│   ├── enrichment/        # Contact enrichment
│   ├── db/                # PostgreSQL data layer
│   ├── llm/               # LLM provider abstraction
│   ├── scraper/           # Lead discovery
│   ├── web/               # HTTP API & dashboard
│   └── ...
├── pkg/agents/             # Background workers
├── hypernexus_site/        # HyperNexus marketing site
├── tormentnexus_site/      # TormentNexus developer site
├── scripts/                # Utility scripts
└── docs/                   # Documentation
```

## Key Files

| File | Purpose |
|------|---------|
| `cmd/marketing_agent/main.go` | Application entrypoint |
| `internal/db/repository.go` | Database queries |
| `internal/communication/cadence.go` | Outreach cadence logic |
| `internal/billing/billing.go` | Stripe billing integration |
| `internal/web/server.go` | HTTP API handlers |
| `.env.example` | Configuration template |

## Production Environment

- **Server:** 5.161.250.43 (Ubuntu 24.04)
- **Database:** PostgreSQL (sales_bot)
- **Service:** systemd (marketing-agent.service)
- **Websites:** Nginx with SSL (Let's Encrypt)

## TormentNexus Integration

The marketing agent integrates with TormentNexus (local AI control plane) for:

- L2 vector memory (semantic search)
- MCP tool routing
- Session management

Access at <http://localhost:7778>

## Marketing Bot (scripts/marketing_bot/)

The marketing bot is an autonomous multi-platform social media engagement system that posts comments, replies, and articles across Reddit, Twitter/X, LinkedIn, Bluesky, and Hacker News.

### Quick Start

```bash
# Run all platforms
python scripts/marketing_bot/run.py

# Run specific platform
python scripts/marketing_bot/run.py --platform reddit
python scripts/marketing_bot/run.py --platform twitter
python scripts/marketing_bot/run.py --platform linkedin

# Run in article mode
python scripts/marketing_bot/run.py --mode articles
```

### Architecture

```
scripts/marketing_bot/
├── README.md                  # Detailed documentation
├── AGENTS.md                  # Agent protocol documentation
├── __init__.py                # Package init
├── config.py                  # Centralized configuration
├── llm.py                     # MiMo v2.5 LLM integration
├── cdp_utils.py               # Chrome DevTools Protocol utilities
├── platforms/
│   ├── __init__.py
│   ├── reddit.py              # Reddit posting & commenting
│   ├── twitter.py             # Twitter/X posting & commenting
│   ├── linkedin.py            # LinkedIn posting & commenting
│   ├── bluesky.py             # Bluesky posting (API-based)
│   ├── hackernews.py          # Hacker News posting
│   └── devto.py               # dev.to article publishing
├── content/
│   ├── __init__.py
│   ├── generator.py           # Content generation with LLM
│   ├── templates.py           # Fallback templates
│   └── articles.py            # Article content for cross-posting
├── orchestrator.py            # Main orchestrator (runs all platforms)
└── run.py                     # CLI entry point
```

### Key Features

| Feature | Description |
|---------|-------------|
| **MiMo v2.5 LLM** | Generates contextual replies and articles |
| **Multi-platform** | Reddit, Twitter, LinkedIn, Bluesky, HN, dev.to |
| **Anti-spam** | Rate limiting, random delays, content variation |
| **Karma building** | Comments before promotional posts |
| **Fallback templates** | Works even when LLM is unavailable |

### Configuration

All settings in `scripts/marketing_bot/config.py`. Key environment variables:

| Variable | Description |
|----------|-------------|
| `HERMES_API_URL` | MiMo v2.5 API endpoint |
| `HERMES_API_KEY` | API key |
| `REDDIT_USERNAME` | Reddit account |
| `REDDIT_PASSWORD` | Reddit password |
| `BLUESKY_TN_PASSWORD` | Bluesky TormentNexus password |
| `BLUESKY_HN_PASSWORD` | Bluesky HyperNexus password |
| `DEVTO_API_KEY` | dev.to API key |

### Anti-Spam Measures

1. **Rate Limiting**: Max 4 posts/hour per platform
2. **Random Delays**: 15-45 min between posts
3. **Content Variation**: LLM-generated unique content
4. **Karma Building**: Comments before promotional posts
5. **Smaller Subreddits**: Targets less moderated communities

### Documentation

- `scripts/marketing_bot/README.md` - Full documentation
- `scripts/marketing_bot/AGENTS.md` - Agent protocol details
