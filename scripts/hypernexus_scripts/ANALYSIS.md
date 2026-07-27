# Marketing Scripts Analysis

# Moved from ../HyperNexus/scripts to marketing_agent

## Overview

17 scripts copied, totaling ~8,000 lines of Python code for automated marketing across multiple platforms.

## Script Categories

### 1. LINKEDIN AUTOMATION

| Script | Lines | Purpose | Status |
|--------|-------|---------|--------|
| `auto_linkedin_page.py` | 707 | Posts to HyperNexus company page via CDP | ✅ Working (used today) |
| `post_linkedin_article.py` | 121 | Posts long-form LinkedIn articles | ✅ Working |

**How it works:**

- Connects to Edge browser via CDP (localhost:9222)
- Navigates to company page admin
- Clicks "Create" → "Start a post"
- Types content using `Input.insertText`
- Clicks "Post" button

**Key functions:**

- `open_post_editor()` - Opens the post creation dialog
- `type_post_content()` - Types content into editor
- `click_post_button()` - Publishes the post
- `publish_post()` - Full workflow

---

### 2. TWITTER/X AUTOMATION

| Script | Lines | Purpose | Status |
|--------|-------|---------|--------|
| `auto_twitter_v2.py` | 330 | Posts tweets via CDP | ✅ Working |
| `twitter_cdp_poster.py` | 612 | Advanced Twitter posting with threads | ✅ Working |

**How it works:**

- Connects to Edge browser via CDP
- Navigates to x.com/compose/post
- Finds tweet textarea via `data-testid="tweetTextarea_0"`
- Types content using `Input.insertText`
- Clicks tweet button via `data-testid="tweetButton"`

**Key functions:**

- `post_tweet()` - Posts a single tweet
- `post_thread()` - Posts a thread (multiple tweets)

---

### 3. REDDIT AUTOMATION

| Script | Lines | Purpose | Status |
|--------|-------|---------|--------|
| `auto_post_reddit.py` | 360 | Posts to Reddit via CDP | ✅ Working |
| `auto_reddit_v2.py` | 376 | Enhanced Reddit posting | ✅ Working |
| `reddit-agent.py` | 354 | Reddit engagement agent | ✅ Working |
| `reddit-agent-v2.py` | 537 | Enhanced Reddit agent | ✅ Working |
| `reddit-scanner.py` | 415 | Scans Reddit for relevant threads | ❌ Blocked (403) |
| `find-relevant-threads.py` | 169 | Finds relevant Reddit threads | ⚠️ Needs API key |

**How it works:**

- Connects to Edge browser via CDP
- Navigates to subreddit
- Clicks "Create Post"
- Fills in title and body
- Clicks "Post"

**Key features:**

- Monitors subreddits for relevant threads
- Generates AI-powered replies
- Avoids spam detection with delays
- Tracks posted content in SQLite

---

### 4. MULTI-PLATFORM ORCHESTRATION

| Script | Lines | Purpose | Status |
|--------|-------|---------|--------|
| `autonomous_marketing.py` | 1237 | Full autonomous marketing system | ✅ Working |
| `auto_marketing_bot.py` | 232 | Basic marketing bot | ✅ Working |
| `auto_marketing_bot_v2.py` | 419 | Enhanced marketing bot | ✅ Working |
| `swarm_v7.py` | 1994 | Multi-agent swarm system | ✅ Working |

**How it works:**

- Runs as a continuous background process
- Monitors multiple platforms simultaneously
- Generates content using LLM
- Posts to LinkedIn, Twitter, Reddit, Bluesky
- Tracks engagement and adjusts strategy

**Key features:**

- Thread-safe with locks
- Rate limiting to avoid bans
- Content deduplication
- Engagement tracking

---

### 5. CONTENT GENERATION

| Script | Lines | Purpose | Status |
|--------|-------|---------|--------|
| `gen-blog.py` | 52 | Generates blog post HTML | ✅ Working |
| `llm_reply.py` | 135 | Generates LLM-powered replies | ✅ Working |

**How it works:**

- Uses TormentNexus/HyperNexus LLM API
- Generates contextual content
- Formats for each platform

---

### 6. MONITORING & MAINTENANCE

| Script | Lines | Purpose | Status |
|--------|-------|---------|--------|
| `watchdog.py` | 311 | Monitors all services | ✅ Working |

**How it works:**

- Checks service health every 5 minutes
- Restarts failed services
- Sends alerts on failures

---

## CDP Connection Pattern

All scripts use the same pattern to connect to Edge browser:

```python
def get_browser_ws():
    """Get browser WebSocket URL from CDP"""
    resp = urllib.request.urlopen("http://localhost:9222/json/version", timeout=5)
    return json.loads(resp.read()).get("webSocketDebuggerUrl")

def create_tab(browser_ws, url="about:blank"):
    """Create a new tab and return its WebSocket URL"""
    ws = websocket.create_connection(browser_ws, timeout=15)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": url}}))
    # ... get target ID and return WebSocket URL
```

## Environment Variables Required

```bash
# LinkedIn
LINKEDIN_USERNAME=pelloni.robert@gmail.com
LINKEDIN_PASSWORD=Temppass.0

# Twitter (CDP - no API keys needed, uses browser session)

# Reddit
REDDIT_USERNAME=HyperNexusLLC
REDDIT_PASSWORD=Temppass0!
REDDIT_CLIENT_ID=0lX58KJiiwuHIY9uHEgZZw
REDDIT_CLIENT_SECRET=E07dDaqBlpFdn5vVL2UZPn9YxtQNcg

# Bluesky
BLUESKY_HANDLE=hypernexusllc.bsky.social
BLUESKY_APP_PASSWORD=b33d-3ivg-pqtk-c6tv
```

## Recommended Consolidation

The scripts can be consolidated into a single unified cross-posting system:

1. **`unified_crosspost.py`** - Single entry point for all platforms
2. **`platform_linkedin.py`** - LinkedIn-specific logic
3. **`platform_twitter.py`** - Twitter-specific logic
4. **`platform_reddit.py`** - Reddit-specific logic
5. **`platform_bluesky.py`** - Bluesky-specific logic
6. **`content_generator.py`** - LLM-powered content generation
7. **`scheduler.py`** - Rate limiting and scheduling

## Usage

To use these scripts:

1. Start Edge with CDP:

   ```
   "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222
   ```

2. Login to platforms manually (first time)

3. Run scripts:

   ```bash
   python scripts/hypernexus_scripts/auto_linkedin_page.py
   python scripts/hypernexus_scripts/auto_twitter_v2.py
   python scripts/hypernexus_scripts/auto_reddit_v2.py
   ```
