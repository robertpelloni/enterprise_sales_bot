# TormentNexus — Autonomous B2B Sales Pipeline

> ⚠️ **Alpha Software** — Expect breaking changes. Not ready for production use.

An autonomous B2B sales pipeline written in Go that discovers enterprise customers, enriches contacts, sends hyper-personalized outreach, and closes deals — all without human intervention.

## What It Does

1. **Discovers leads** from GitHub repos, job boards, and HN hiring threads
2. **Enriches contacts** via Apollo.io, Hunter.io, and GitHub commit analysis
3. **Sends personalized outreach** with a multi-touch cadence system
4. **Handles replies autonomously** via LLM-powered response generation
5. **Closes deals** with Stripe billing integration
6. **Publishes content** — auto-generates blog posts and cross-posts to dev.to/Hashnode

## Quick Start

```bash
# Clone and configure
git clone https://github.com/robertpelloni/marketing_agent.git
cp .env.example .env  # Edit with your API keys

# Build and run
go build -o bin/marketing_agent ./cmd/marketing_agent/
./bin/marketing_agent
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          main.go                                     │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ Scraper  │  │ Enricher │  │Researcher│  │   Communication    │  │
│  │ (30m)    │  │ (1h)     │  │ (1h)     │  │     Manager        │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬───────────┘  │
│       │              │              │                 │              │
│  ┌────▼──────────────▼──────────────▼─────────────────▼──────────┐  │
│  │                      PostgreSQL                                │  │
│  │  companies → contacts → interactions → deals                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ CRM Sync │  │ AutoDev  │  │  Billing │  │   Web Dashboard    │  │
│  │  (30m)   │  │ (1h)     │  │ (Stripe) │  │   :8084            │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Go 1.24 |
| Database | PostgreSQL 13+ |
| LLM | DeepSeek (MiMo v2.5) via API |
| Email | Gmail SMTP/IMAP |
| Billing | Stripe |
| Analytics | Plausible (self-hosted) |
| Websites | Static HTML + Nginx |

## Module Architecture

| Package | Purpose |
|---------|---------|
| `internal/scraper` | Lead discovery from job boards & GitHub |
| `internal/enrichment` | Contact enrichment (Apollo, Hunter, GitHub) |
| `internal/researcher` | Technical dossier building |
| `internal/communication` | Cadence-aware outreach & reply handling |
| `internal/crm` | Bidirectional CRM sync |
| `internal/billing` | Stripe checkout & subscription management |
| `internal/llm` | LLM provider abstraction |
| `internal/autodev` | Autonomous code development |
| `internal/web` | HTTP API & dashboard |
| `internal/db` | PostgreSQL data layer |
| `pkg/agents` | Target discovery & blog engine |

## 7-State Lead Lifecycle

```
Discovered → Researched → Outreach_Sent → Engaged → Negotiating → Closed_Won
                                                                     ↘ Closed_Lost
```

## Configuration

All configuration via environment variables. See `.env.example` for the full list.

**Required:**

- `DATABASE_URL` — PostgreSQL connection string
- `GITHUB_TOKEN` — For repo scanning
- `SMTP_USER` / `SMTP_PASSWORD` — For sending emails
- `APOLLO_API_KEY` — For contact enrichment

**Optional:**

- `STRIPE_SECRET_KEY` — For billing
- `HUNTER_API_KEY` — Additional enrichment source
- `DEEPSEEK_API_KEY` — For LLM features

## Testing

```bash
# Unit tests
go test ./...

# Integration tests (requires DATABASE_URL)
go test ./internal/... -tags=integration

# E2E tests
go test ./tests/e2e/...
```

## Deployment

The marketing agent runs as a systemd service on the production server:

```bash
# SSH to server
ssh root@5.161.250.43

# Build and restart
cd /opt/marketing_agent
go build -o bin/marketing_agent ./cmd/marketing_agent/
systemctl restart marketing-agent

# Check status
systemctl status marketing-agent
journalctl -u marketing-agent -f
```

## Websites

| Site | URL | Purpose |
|------|-----|---------|
| HyperNexus | <https://hypernexus.site> | Corporate landing page |
| Cloud Dashboard | <https://cloud.hypernexus.site> | Login & account management |
| TormentNexus | <https://tormentnexus.site> | Open source / developer site |
| Blog | <https://hypernexus.site/blog/> | Technical content |

## Related Repositories

- **TormentNexus Core:** <https://github.com/MDMAtk/TormentNexus>
- **HyperNexus Docs:** <https://github.com/HyperNexusSoft/HyperNexus>

## License

BSL 1.1 / AGPLv3 — See [LICENSE](LICENSE) for details.

## Links

- **Website:** <https://hypernexus.site>
- **Discord:** <https://discord.gg/w7zpZ7qBt>
- **Twitter:** <https://x.com/tormentnexus>
- **Bluesky:** <https://bsky.app/profile/tormentnexus.bsky.social>
