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
