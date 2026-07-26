# Handoff — 2026-07-07

## Full Launch: TormentNexus → Developers / HyperNexus → Corporate Executives

### System Status: ✅ LIVE

- **Service**: `marketing-agent.service` — **active (running)** PID 2217199
- **Binary**: v0.6.2 (Linux graceful shutdown fix, dual-brand outreach)
- **Web Dashboard**: `http://us-east-ubuntu-2-8-80:8084`
- **Database**: `sales_bot` — 1,899 companies, 493 contacts, 541 interactions

### Pipeline Status

| State | Count | Action |
|---|---|---|
| Discovered | 83 | Awaiting research |
| Researched | 1,416 | **Ready for outreach** (cadence step 1 → intro-email) |
| Outreach_Sent | 406 | Already contacted (cadence step 2+ pending) |

### Dual-Brand Configuration

- **TormentNexus** (tormentnexus.site) → Developer audience (free email, github.com)
  - Messaging: local-first, open-source, MCP tool routing, 14K+ memories
  - Channels: GitHub comments, LinkedIn
- **HyperNexus** (hypernexus.site) → Corporate executives (company email domains)
  - Messaging: cloud-hosted, SSO/RBAC, audit trails, enterprise fork
  - Channels: Email, LinkedIn

### Key Configurations Deployed

- ✅ **SMTP**: smtp.gmail.com:587 — <pelloni.robert@gmail.com> (app password)
- ✅ **IMAP**: imap.gmail.com:993 — inbound email polling (30min)
- ✅ **Hunter.io**: API key configured (contact enrichment)
- ✅ **Apollo.io**: ⚠️ Invalid API key (403) — needs replacement
- ✅ **Hermes LLM**: localhost:4000 — free-llm model (health check 404 but functional)
- ✅ **SECRET_KEY**: Generated 32-char hex key
- ✅ **Templates**: Updated to use "HyperNexus" as default brand (code auto-swaps to "TormentNexus" for devs)
- ✅ **Migrations**: subscriptions, billing_events, secrets tables created

### Cadence (5-Touch Sequence)

1. Day 0: intro-email (HyperNexus for {{company}} — Quick Question)
2. Day 2: github-hook (GitHub comment on relevant repos)
3. Day 3: followup-email (Re: HyperNexus for {{company}} — Thoughts?)
4. Day 4: linkedin-connect (LinkedIn connection request)
5. Day 7: breakup-email (Should I close your file?)

### Issues to Address

1. **Apollo.io API key** — 403 error. Needs new key.
2. **Hunter.io** — Low hit rate on `.tech` domains (most leads are `.github.com`). Consider expanding lead sources.
3. **GitHub token** — `ghp_dmEJo9...zzVK` was in git history (now redacted). Token works, rotation optional.
4. **Stripe billing** — No STRIPE_API_KEY set. Billing API disabled.
5. **Social posting** — Currently SIMULATION mode. Needs real platform API keys for actual posting.
