# Video Demo Script: Stop Re-Explaining Your Codebase to Every AI Tool

**Target Duration:** 90–120 Seconds
**Format:** Screen Recording + Voiceover + On-screen Terminal Text
**Platforms:** YouTube Shorts, X/Twitter, TikTok, Landing Page Hero

---

## Pre-Recording Checklist

- [ ] Terminal theme: Catppuccin Macchiato or Tokyo Night (large bold font)
- [ ] Font size: 18-20pt minimum for mobile readability
- [ ] Screen resolution: 1920x1080 (scale to 4K if possible)
- [ ] Close all unnecessary tabs/apps
- [ ] Pre-stage demo environment (clean terminal, no history pollution)
- [ ] TormentNexus daemon pre-installed and tested
- [ ] Ollama running with `qwen2.5-coder` model loaded
- [ ] Record at 1.5x speed for terminal typing (slow down in post if needed)

---

## [0:00 - 0:15] SECTION 1: The Pain Point (Hook)

### Visual

Fast-paced cut switching between terminal windows:

- Open `claude` → type a question → watch it forget context
- Open `codex` → same question → same amnesia
- Open Antigravity IDE → same thing
- Red text overlays: `Context Bloat: 48,500 Tokens` / `Memory: LOST`

### Voiceover
>
> "Every time you open a new AI coding tool—Claude Code, Codex CLI, Google Antigravity—you face the same problem.
>
> It completely forgets what you built 10 minutes ago in another tool.
>
> And it burns through 50,000 tokens just loading duplicate tool schemas.
>
> Here's how you fix it in 30 seconds."

### On-Screen Text Overlay

```
❌ Context Bloat: 48,500 Tokens
❌ Memory: LOST between tools
❌ Cost: $0.15 per query wasted
```

---

## [0:15 - 0:45] SECTION 2: One-Command Installation

### Visual

Clean terminal window. Single command typed with crisp keystrokes.

### Terminal Commands (record each separately, cut between)

**Step 1: Start the daemon**

```bash
tormentnexus daemon start
```

*Screen highlights appear after command:*

```
[✓] SQLite-vec memory vault mounted
[✓] Progressive MCP gateway running on :8080
[✓] LLM waterfall cascade ready
[✓] All systems GO
```

**Step 2: Claude Code**

```bash
claude mcp add hypernexus --transport http http://localhost:8080/mcp
```

*On-screen checkmark:* `✓ Connected to Claude Code`

**Step 3: Codex CLI**

```bash
codex mcp add hypernexus http://localhost:8080/mcp
```

*On-screen checkmark:* `✓ Shared config linked`

**Step 4: Google Antigravity**
*Screen recording of:*

- Open Antigravity Agent Manager
- Navigate to MCP Integration settings
- Paste `http://localhost:8080/mcp`
- Click "Connect"
*On-screen checkmark:* `✓ Active in Antigravity`

### Voiceover
>
> "Start the local Go control plane. One command. It boots your sqlite-vec memory vault and mounts a progressive MCP gateway.
>
> Now hook it into your stack. One line for Claude Code. One line for Codex. Point Antigravity's Agent Manager to the local gateway.
>
> That's it. One unified config across every harness."

### On-Screen Text

```
┌─────────────────────────────────────────────┐
│  TormentNexus Control Plane                 │
│  ├── SQLite-vec Memory Vault    [✓ READY]   │
│  ├── Progressive MCP Gateway    [✓ :8080]   │
│  ├── LLM Waterfall Cascade     [✓ ARMED]    │
│  └── Connected Harnesses:       3 tools     │
└─────────────────────────────────────────────┘
```

---

## [0:45 - 1:20] SECTION 3: The Magic (What It Actually Does)

### Visual

Open Claude Code in terminal. Ask a cross-tool question.

### Terminal Input

```bash
claude "What database migration did we choose in Antigravity yesterday? Run the schema test."
```

### Visual Focus - Split Screen Comparison

**Left side (WITHOUT HyperNexus):**

```
Token Usage: 52,000 tokens
Tools Injected: 47 MCP schemas
Context: BLOATED
Memory: NONE
Response: "I don't have context about previous sessions..."
```

**Right side (WITH HyperNexus):**

```
Token Usage: 3,200 tokens
Tools Injected: 3 relevant schemas
Context: OPTIMIZED
Memory: L1-L3 VECTOR VAULT
Response: "Yesterday in Antigravity we chose PostgreSQL 
           with uuid-ossp extension. Running schema test..."
```

### Visual - Token Telemetry Dashboard

```
┌─────────────────────────────────────────────────┐
│  Progressive Tool Routing                       │
│                                                 │
│  Without HyperNexus:  ████████████████ 52,000   │
│  With HyperNexus:     ███              3,200    │
│                                                 │
│  Token Savings: 93.8%                           │
│  Tools Selected: 3 of 47                        │
│  Selection Method: Semantic vector search       │
└─────────────────────────────────────────────────┘
```

### Voiceover
>
> "Watch this. Instead of shoving 47 tool schemas into Claude's prompt, HyperNexus uses progressive routing. It inspects the prompt and injects only the top three relevant tools.
>
> Token waste: slashed by 90 percent.
>
> And because memory persists in the local vector vault, Claude instantly remembers decisions made inside Antigravity or Codex. Zero re-explaining."

---

## [1:20 - 1:40] SECTION 4: Zero-Downtime Cascade

### Visual

Simulate an OpenAI 429 rate limit error during a background task.

### Terminal Log (appears line by line)

```
[14:32:01] Agent processing task: refactor auth module
[14:32:02] [WARN] Primary LLM (OpenAI) returned HTTP 429
[14:32:02] [CASCADE] Attempting fallback: OpenRouter
[14:32:03] [WARN] OpenRouter rate limited
[14:32:03] [CASCADE] Falling back to local Ollama (qwen2.5-coder)
[14:32:04] [SUCCESS] Internal context processing complete (120ms)
[14:32:04] [INFO] Task completed. Zero downtime.
```

### Visual - Waterfall Diagram

```
┌─────────────────────────────────────────────┐
│  LLM Waterfall Cascade                      │
│                                             │
│  1. OpenAI GPT-4o      → 429 Rate Limited  │
│  2. OpenRouter          → 429 Rate Limited  │
│  3. Local Ollama        → ✓ SUCCESS         │
│                                             │
│  Result: Zero downtime. Zero state loss.    │
└─────────────────────────────────────────────┘
```

### Voiceover
>
> "When primary APIs hit rate limits or go down, the internal waterfall automatically cascades to local models via Ollama.
>
> Your agents never stall. Never lose state. Never crash.
>
> Rate limits are inevitable. Downtime is not."

---

## [1:40 - 2:00] SECTION 5: Call to Action

### Visual

Full-screen comparison table with animated reveal

### Comparison Table

```
┌─────────────────┬──────────────┬─────────────────┬─────────────────┐
│                 │ HyperNexus   │ Cursor          │ GitHub Copilot  │
├─────────────────┼──────────────┼─────────────────┼─────────────────┤
│ Price           │ $50/yr       │ $240/yr         │ $120/yr         │
│ Persistent Mem  │ ✓ Included   │ ✗               │ ✗               │
│ Cross-Harness   │ ✓ 6 tools    │ ✗               │ ✗               │
│ Token Savings   │ ✓ 90%+       │ ✗               │ ✗               │
│ LLM Failover    │ ✓ Auto       │ ✗               │ ✗               │
│ Self-Hosted     │ ✓ Included   │ ✗               │ ✗               │
│ Open Source      │ ✓ Full       │ ✗               │ ✗               │
└─────────────────┴──────────────┴─────────────────┴─────────────────┘
```

### Final Screen

```
┌─────────────────────────────────────────────────┐
│                                                 │
│   Stop wasting tokens. Own your memory.         │
│                                                 │
│   🆓 Open Source:  tormentnexus.site            │
│   ☁️  Cloud Pro:    hypernexus.site             │
│                                                 │
│   $50/year. Everything included.                │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Voiceover
>
> "Get persistent memory, 90% context reduction, and universal tool parity across every AI client.
>
> Try the open-source Go daemon free at TormentNexus dot site.
>
> Or grab the 50-dollar yearly license at HyperNexus dot site.
>
> Stop wasting tokens. Own your memory."

---

## Post-Production Notes

### Audio

- Voiceover: Clean, energetic male/female voice (or professional TTS)
- Background: Dark synthwave or psytrance at 15-20% volume
- Sound effects: Subtle "ding" on checkmarks, "whoosh" on transitions

### Editing

- Terminal typing: 1.5x speed (slow down in post if needed)
- Transitions: Quick cuts (0.3s) between tools
- Overlays: Animated progress bars, floating checkmarks
- Color scheme: Dark terminal with green/cyan highlights

### Export Settings

- Resolution: 1920x1080 (landscape) or 1080x1920 (vertical for Shorts/TikTok)
- Frame rate: 60fps for smooth terminal rendering
- Format: MP4 (H.264)

### Distribution

- YouTube: Full 2-minute version
- YouTube Shorts: 60-second cut (Sections 1, 2, 5)
- TikTok: 60-second cut with captions
- X/Twitter: 90-second cut with thread link
- Landing Page: Embedded full version

---

## Key Messaging Summary

| Problem | Solution | Proof |
|---------|----------|-------|
| Context bloat (50K tokens) | Progressive tool routing | 93.8% token reduction |
| Memory loss between tools | SQLite-vec vector vault | Cross-tool context persists |
| API rate limits crash agents | LLM waterfall cascade | Zero downtime guarantee |
| Vendor lock-in | Universal harness parity | 6 tools, one config |
| High cost ($120-240/yr) | $50/year lifetime license | 60-80% cheaper |

---

## Call-to-Action Links

- **Open Source:** <https://tormentnexus.site>
- **Cloud Pro:** <https://hypernexus.site>
- **GitHub:** <https://github.com/MDMAtk/TormentNexus>
- **Pricing:** <https://hypernexus.site/pricing.html>
