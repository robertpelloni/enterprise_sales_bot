#!/usr/bin/env python3
"""
Twitter/X CDP Auto-Poster for HyperNexus
Uses Edge CDP (port 9222) + mimo-v2.5 LLM to generate and post optimized content.

Follows 2026 Grok algorithm optimization:
- Bookmarks-first strategy (save-worthy depth)
- High-effort replies weighted heavily
- Semantic fit over velocity
- Link in replies, not main post
- Video attachment for parser engagement
- Spaced posting (let algorithm distribute)
"""

import json
import time
import os
import sys
import random
import urllib.request
import websocket
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─── Configuration ───────────────────────────────────────────────────────────

CDP_URL = "http://localhost:9222"
LLM_URL = "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions"
LLM_KEY = "tp-s0jae9p6m9d8pirs67549as0ewk9a1up0i1379o1kcg4u6r3"
LLM_MODEL = "mimo-v2.5"

# Posting schedule: 2-3 posts per day, spaced 4-6 hours apart
POST_INTERVAL_HOURS = 5  # Base interval between posts
POSTS_PER_DAY = 2
LINK_IN_REPLY = "https://hypernexus.site"

# Video paths for attachment
VIDEOS = [
    r"C:\Users\hyper\Videos\hypernexus_v02_mixed.mp4",
    r"C:\Users\hyper\Videos\hypernexuswebsite_v02_mixed.mp4",
    r"C:\Users\hyper\Videos\hypernexusinstall_v04_mixed.mp4",
]

# ─── Post Templates (Grok-Optimized) ────────────────────────────────────────

POST_TEMPLATES = [
    {
        "name": "Architecture Breakdown",
        "strategy": "Bookmarks-first: dense technical breakdown encourages saves",
        "prompt": """Write a Twitter post (max 280 chars) about Model Context Protocol (MCP) servers.
Topic: How HyperNexus provides universal AI control plane with progressive tool routing.
Style: Technical but accessible, encourage saves/bookmarks.
End with a question to drive replies.
NO links, NO hashtags in main post. Just the text.""",
        "video": True,
    },
    {
        "name": "Friction & Debate",
        "strategy": "Bold claim to drive replies (weighted heavily by Grok)",
        "prompt": """Write a Twitter post (max 280 chars) with a bold claim about AI workflows.
Topic: If you're still hardcoding API integrations for every LLM, you're wasting time.
Style: Provocative but constructive, invite debate.
End with a direct question.
NO links, NO hashtags. Just the text.""",
        "video": False,
    },
    {
        "name": "Enterprise vs Open Source",
        "strategy": "Clear semantic claims for SimCluster categorization",
        "prompt": """Write a Twitter post (max 280 chars) comparing enterprise vs open-source MCP servers.
Topic: Enterprise needs different architecture than local wrappers. Mention HyperNexus and TormentNexus.
Style: Informative, feed Grok exact keywords (Enterprise, Open Source, MCP server).
End with a question.
NO links, NO hashtags. Just the text.""",
        "video": True,
    },
    {
        "name": "Video Parser Teaser",
        "strategy": "Short text + video for Grok's video parsing",
        "prompt": """Write a SHORT Twitter post (max 200 chars) to accompany a video demo.
Topic: Progressive tool routing on a dedicated MCP server prevents token bloat.
Style: Punchy, let the video do the talking.
Ask for feedback on the UI flow.
NO links, NO hashtags. Just the text.""",
        "video": True,
    },
    {
        "name": "Developer Productivity Listicle",
        "strategy": "High-density formatted content for shareability",
        "prompt": """Write a Twitter post (max 280 chars) as a listicle.
Topic: 3 reasons your next AI project needs a dedicated MCP server.
Format: Number the reasons (1. 2. 3.)
End by asking which feature would save the most time.
NO links, NO hashtags. Just the text.""",
        "video": False,
    },
]

# Reply template for link
LINK_REPLY_TEMPLATES = [
    "Get the full specs and upgrade your setup here: {link}",
    "Full details and open-source code: {link}",
    "Check it out and star the repo: {link}",
    "Link to try it yourself: {link}",
]

# ─── State Management ────────────────────────────────────────────────────────

STATE_FILE = os.path.join(os.path.dirname(__file__), "twitter_poster_state.json")


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {
            "last_post_time": None,
            "posts_today": 0,
            "day": None,
            "template_index": 0,
            "total_posts": 0,
        }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


# ─── LLM Content Generation ─────────────────────────────────────────────────


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def llm_generate(prompt, max_tokens=2000):
    """Generate content using mimo-v2.5."""
    try:
        body = json.dumps(
            {
                "model": LLM_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a social media expert for a tech company called HyperNexus that builds AI developer tools. Write engaging, authentic Twitter posts. Never use emojis excessively. Be direct and technical.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.8,
            }
        ).encode()

        req = urllib.request.Request(
            LLM_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LLM_KEY}",
            },
        )
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        msg = result["choices"][0]["message"]
        text = msg.get("content", "") or msg.get("reasoning_content", "")
        if text:
            # Clean up the text
            text = text.strip().strip('"').strip("'")
            # Remove any hashtags that slipped in
            lines = text.split("\n")
            cleaned = []
            for line in lines:
                if not line.strip().startswith("#"):
                    cleaned.append(line)
            text = "\n".join(cleaned).strip()
            return text[:280]
    except Exception as e:
        log(f"  LLM error: {e}")
    return None


# ─── CDP Browser Control ─────────────────────────────────────────────────────


class CDPController:
    def __init__(self):
        self.ws = None
        self.msg_id = 0
        self.responses = {}
        self.events = []

    def connect(self):
        """Connect to Edge CDP."""
        try:
            # Get available tabs
            req = urllib.request.Request(f"{CDP_URL}/json")
            resp = urllib.request.urlopen(req, timeout=5)
            tabs = json.loads(resp.read())

            # Find Twitter/X tab
            twitter_tab = None
            for tab in tabs:
                url = tab.get("url", "")
                if "twitter.com" in url or "x.com" in url:
                    twitter_tab = tab
                    break

            if not twitter_tab:
                # Open Twitter in a new tab
                log("  No Twitter tab found, opening one...")
                req = urllib.request.Request(f"{CDP_URL}/json/new?https://twitter.com")
                resp = urllib.request.urlopen(req, timeout=10)
                twitter_tab = json.loads(resp.read())
                time.sleep(5)

            ws_url = twitter_tab.get("webSocketDebuggerUrl")
            if not ws_url:
                log("  ❌ No WebSocket URL found")
                return False

            log(f"  Connecting to: {twitter_tab.get('title', 'Unknown')[:50]}")
            # Use origin header to bypass CORS check
            self.ws = websocket.create_connection(
                ws_url, timeout=30, origin="http://localhost"
            )
            log("  ✅ Connected to CDP")
            return True
        except Exception as e:
            log(f"  ❌ CDP connection failed: {e}")
            log(
                "  💡 Make sure Edge is running with: --remote-debugging-port=9222 --remote-allow-origins=*"
            )
            return False

    def send(self, method, params=None):
        """Send CDP command and wait for response."""
        self.msg_id += 1
        msg = {"id": self.msg_id, "method": method}
        if params:
            msg["params"] = params

        self.ws.send(json.dumps(msg))

        # Wait for response
        timeout = time.time() + 30
        while time.time() < timeout:
            try:
                self.ws.settimeout(2)
                data = json.loads(self.ws.recv())
                if data.get("id") == self.msg_id:
                    return data
            except:
                continue
        return None

    def evaluate(self, expression):
        """Execute JavaScript in the page."""
        result = self.send(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )
        if result and "result" in result:
            return result["result"].get("result", {}).get("value")
        return None

    def navigate(self, url):
        """Navigate to a URL."""
        self.send("Page.navigate", {"url": url})
        time.sleep(3)

    def click_at(self, x, y):
        """Click at coordinates."""
        self.send(
            "Input.dispatchMouseEvent",
            {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1},
        )
        time.sleep(0.1)
        self.send(
            "Input.dispatchMouseEvent",
            {
                "type": "mouseReleased",
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1,
            },
        )

    def type_text(self, text):
        """Type text character by character."""
        for char in text:
            self.send("Input.dispatchKeyEvent", {"type": "keyDown", "text": char})
            self.send("Input.dispatchKeyEvent", {"type": "keyUp"})
            time.sleep(0.02 + random.random() * 0.03)

    def press_key(self, key):
        """Press a special key (Enter, Tab, etc.)."""
        key_map = {
            "Enter": {"key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13},
            "Tab": {"key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9},
            "Escape": {"key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27},
            "Backspace": {
                "key": "Backspace",
                "code": "Backspace",
                "windowsVirtualKeyCode": 8,
            },
        }
        params = key_map.get(key, {"key": key})
        self.send("Input.dispatchKeyEvent", {"type": "keyDown", **params})
        time.sleep(0.05)
        self.send("Input.dispatchKeyEvent", {"type": "keyUp", **params})

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except:
                pass


# ─── Twitter Posting Actions ─────────────────────────────────────────────────


def post_tweet(cdp, text, video_path=None):
    """Post a tweet using CDP."""
    try:
        log("  Navigating to Twitter compose...")
        cdp.navigate("https://twitter.com/compose/post")
        time.sleep(3)

        # Wait for compose box to be ready
        log("  Waiting for compose box...")
        for _ in range(10):
            ready = cdp.evaluate("""
                document.querySelector('[data-testid="tweetTextarea_0"]') !== null ||
                document.querySelector('[role="textbox"]') !== null
            """)
            if ready:
                break
            time.sleep(1)

        # Click on the compose area
        log("  Clicking compose area...")
        compose = cdp.evaluate("""
            (function() {
                var el = document.querySelector('[data-testid="tweetTextarea_0"]') ||
                         document.querySelector('[role="textbox"]');
                if (el) {
                    var rect = el.getBoundingClientRect();
                    return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                }
                return null;
            })()
        """)

        if compose:
            cdp.click_at(compose["x"], compose["y"])
            time.sleep(0.5)

        # Type the tweet
        log(f"  Typing tweet ({len(text)} chars)...")
        cdp.type_text(text)
        time.sleep(1)

        # Attach video if provided
        if video_path and os.path.exists(video_path):
            log(f"  Attaching video: {os.path.basename(video_path)}")
            # Use file input to attach media
            attach_js = """
                (function() {
                    var input = document.querySelector('input[data-testid="fileInput"]') ||
                                document.querySelector('input[type="file"]');
                    if (input) return true;
                    // Click media button
                    var btn = document.querySelector('[data-testid="fileButton"]') ||
                              document.querySelector('[aria-label="Media"]');
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
            """
            cdp.evaluate(attach_js)
            time.sleep(1)

        # Click Post button with retries
        log("  Clicking Post button...")
        for attempt in range(5):
            post_btn = cdp.evaluate("""
                (function() {
                    // Try multiple selectors
                    var selectors = [
                        '[data-testid="tweetButton"]',
                        '[data-testid="tweetButtonInline"]',
                        'button[data-testid="tweetButton"]',
                        'div[role="button"][data-testid="tweetButton"]',
                        'button:has(> span:contains("Post"))',
                        'button:has(> span:contains("Tweet"))'
                    ];
                    for (var i = 0; i < selectors.length; i++) {
                        var btn = document.querySelector(selectors[i]);
                        if (btn && !btn.disabled) {
                            btn.click();
                            return 'clicked';
                        }
                    }
                    // Try finding by text content
                    var buttons = document.querySelectorAll('button');
                    for (var j = 0; j < buttons.length; j++) {
                        var text = buttons[j].textContent.trim();
                        if ((text === 'Post' || text === 'Tweet') && !buttons[j].disabled) {
                            buttons[j].click();
                            return 'clicked_text';
                        }
                    }
                    return null;
                })()
            """)

            if post_btn:
                time.sleep(3)
                log("  ✅ Tweet posted!")
                return True
            else:
                log(
                    f"  Attempt {attempt + 1}: Post button not found or disabled, waiting..."
                )
                time.sleep(2)

        log("  ❌ Could not find Post button after 5 attempts")
        return False

    except Exception as e:
        log(f"  ❌ Post failed: {e}")
        return False


def post_reply(cdp, reply_text):
    """Post a reply to the last tweet."""
    try:
        log("  Posting reply with link...")
        time.sleep(2)

        # Find the reply area
        reply_area = cdp.evaluate("""
            (function() {
                var el = document.querySelector('[data-testid="tweetTextarea_0"]') ||
                         document.querySelector('[role="textbox"]');
                if (el) {
                    var rect = el.getBoundingClientRect();
                    return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                }
                return null;
            })()
        """)

        if reply_area:
            cdp.click_at(reply_area["x"], reply_area["y"])
            time.sleep(0.5)
            cdp.type_text(reply_text)
            time.sleep(1)

            # Click Reply button
            cdp.evaluate("""
                (function() {
                    var btn = document.querySelector('[data-testid="tweetButton"]') ||
                              document.querySelector('[data-testid="tweetButtonInline"]');
                    if (btn) { btn.click(); return true; }
                    return false;
                })()
            """)
            time.sleep(2)
            log("  ✅ Reply posted!")
            return True

    except Exception as e:
        log(f"  ❌ Reply failed: {e}")
    return False


# ─── Main Loop ───────────────────────────────────────────────────────────────


def get_next_template(state):
    """Get the next post template in rotation."""
    idx = state.get("template_index", 0)
    template = POST_TEMPLATES[idx % len(POST_TEMPLATES)]
    state["template_index"] = (idx + 1) % len(POST_TEMPLATES)
    return template


def should_post(state):
    """Check if it's time to post based on schedule."""
    now = datetime.now()

    # Reset daily counter if new day
    today = now.strftime("%Y-%m-%d")
    if state.get("day") != today:
        state["day"] = today
        state["posts_today"] = 0

    # Check if we've hit daily limit
    if state["posts_today"] >= POSTS_PER_DAY:
        log(f"  Daily limit reached ({POSTS_PER_DAY} posts). Waiting until tomorrow.")
        return False

    # Check if enough time has passed since last post
    last_post = state.get("last_post_time")
    if last_post:
        try:
            last_dt = datetime.fromisoformat(last_post)
            hours_since = (now - last_dt).total_seconds() / 3600
            if hours_since < POST_INTERVAL_HOURS:
                remaining = POST_INTERVAL_HOURS - hours_since
                log(f"  Next post in {remaining:.1f} hours")
                return False
        except:
            pass

    return True


def main():
    log("=" * 60)
    log("  HyperNexus Twitter/X CDP Auto-Poster")
    log("  Following 2026 Grok Algorithm Optimization")
    log("=" * 60)

    state = load_state()
    log(f"  Total posts: {state.get('total_posts', 0)}")
    log(f"  Posts today: {state.get('posts_today', 0)}")

    while True:
        try:
            if not should_post(state):
                log("  Sleeping 30 minutes...")
                time.sleep(1800)
                continue

            # Get next template
            template = get_next_template(state)
            log(f"\n  Template: {template['name']}")
            log(f"  Strategy: {template['strategy']}")

            # Generate content with LLM
            log("  Generating content with mimo-v2.5...")
            tweet_text = llm_generate(template["prompt"])

            if not tweet_text:
                log("  ❌ Failed to generate content. Retrying in 5 minutes...")
                time.sleep(300)
                continue

            log(f"  Generated ({len(tweet_text)} chars): {tweet_text[:80]}...")

            # Connect to CDP
            cdp = CDPController()
            if not cdp.connect():
                log("  ❌ CDP connection failed. Retrying in 5 minutes...")
                time.sleep(300)
                continue

            # Select video if template requires it
            video = None
            if template.get("video"):
                video = random.choice(VIDEOS)
                log(f"  Video: {os.path.basename(video)}")

            # Post the tweet
            success = post_tweet(cdp, tweet_text, video)

            if success:
                # Post reply with link
                time.sleep(3)
                reply_template = random.choice(LINK_REPLY_TEMPLATES)
                reply_text = reply_template.format(link=LINK_IN_REPLY)
                post_reply(cdp, reply_text)

                # Update state
                now = datetime.now().isoformat()
                state["last_post_time"] = now
                state["posts_today"] = state.get("posts_today", 0) + 1
                state["total_posts"] = state.get("total_posts", 0) + 1
                save_state(state)

                log(f"  ✅ Post #{state['total_posts']} complete!")
                log(f"  Posts today: {state['posts_today']}/{POSTS_PER_DAY}")

            cdp.close()

            # Wait before next check
            log(f"  Sleeping {POST_INTERVAL_HOURS} hours until next post...")
            time.sleep(POST_INTERVAL_HOURS * 3600)

        except KeyboardInterrupt:
            log("\n  Stopping...")
            break
        except Exception as e:
            log(f"  ❌ Error: {e}")
            time.sleep(300)

    log("  Goodbye!")


if __name__ == "__main__":
    main()
