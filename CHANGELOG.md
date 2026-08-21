
## [0.7.2] - 2026-08-20

### Repository Sync

- **Comprehensive sync**: Scanned and analyzed 90+ repositories for feature branches
- **Branch analysis**: All feature branches were either empty, stale, or upstream-only
- **HyperNexus sync**: Updated submodules, committed formatting changes
- **Server sync**: All services verified active, database at 1,786 contacts
- **Download links**: Updated to point to HyperNexusLLC/HyperNexus releases
- **Documentation**: Updated HANDOFF.md, VERSION.md, CHANGELOG.md

## [0.7.1] - 2026-07-13

### Fixed

- **Email template variables**: Added `stripTemplateVars()` regex filter that removes any bracketed
  placeholders (`[Your Name]`, `[Company Name]`, etc.) from LLM-generated email content.
  Even when the system prompt says "never include these", LLMs sometimes slip them in.
  This post-processing filter catches them all.
- **HN scraper broken**: HN's Algolia search API started returning HTML instead of JSON
  (rate-limiting). Rewrote to use Firebase user endpoint (`/user/whoishiring.json`).
  Added Algolia fallback with Content-Type check to avoid JSON parse errors.

### Added

- **Scraper constructors**: `NewLinkedInSource()` and `NewRedditSource()` restore build
  after partial merge. Reddit stubs search across r/LocalLLaMA, r/MachineLearning, etc.

### Changed

- **Blog engine rewritten**: 28 diverse topics (was 8), each with 3 angle variations.
  JSON state persistence prevents duplicates. Max tokens 3000.
- **Dashboard**: Pipeline funnel bar replaces text summary.
- **Systray**: Added Open Blog, Open Site, Restart Service menu items.
- **Project**: Scripts archived to `scripts/archive/`.

## [0.7.0] - 2026-07-13

### Fixed

- Template variable placeholder stripping in LLM emails
- Scraper constructors restored after branch merge
- TormentNexus TTY crash via script wrapper
- Orphaned `GetLastProvisionedCompany` call in server

### Added

- CDP poster for Twitter/Reddit silent posting
- Blog cross-post publisher (dev.to, hashnode)
- GitHub Discussions engager
- Launch materials (Product Hunt, Show HN)
- Stripe checkout with seat quantities

## [0.6.1] - 2026-07-07

### Added

- Secrets encryption at rest (`pkg/crypto` + secrets DB migration)
- GraphRAG memory vault integration tests
- Telemetry WebSocket integration tests
- Web dashboard handler tests
- GDPR endpoint unit tests
- Feedback loop integration tests
- Negative DB tests with nil checking

### Changed

- Dead `.gitmodules` entry removed (tormentnexus submodule never committed)
- `build.bat` and `start.bat` updated (submodule graceful handling, .exe extension)

## [0.6.0] - 2026-07-06

### Added

- Stripe subscription billing system with full subscription lifecycle
- Grandfathered rate support — auto-freezes old rates on price increases
- Stripe webhook handler (checkout, invoice, subscription events)
- Billing API endpoints (checkout, subscription, cancel, portal)
- HyperNexus $5 sale pricing with slashed $100 + pulsing SALE ENDING... SOON!
- HyperNexus Stripe checkout integration on pricing buttons
- Dashboard: real-time telemetry WebSocket, audit log stream, Hermes latency gauge
- Dashboard: self-service deploy (sync repo, trigger build) buttons
- GraphRAG memory vault schema and access layer
- Webhook IP allowlisting
- Database migration: subscriptions, price history, billing events tables

### Changed

- Robotic scream and heartbeat audio removed from TormentNexus canvas
- SpookySkull nose cavity moved between eyes and mouth, made angular and on top layer
- Both sites: copy updated with real technical specs (384-dim embeddings, BM25, L1/L2/L3 capacities)
- Version bumped to 0.6.0

## [0.5.3] - 2026-06-25

### Changed

- HyperNexus site: light theme, neon gradients, frosted glass cards, animated splashes
- TormentNexus site: skull jaw/nose adjustments, smaller nasal cavity
- Pricing: removed $0 tier, added self-host redirect to TormentNexus.site
- Video: NotebookLM video downloads and embedded players

### Fixed

- HyperNexus: removed body::before grid overlay causing frosted glass effect
- HyperNexus: fixed body overflow/scroll issues, cleaned CSS
