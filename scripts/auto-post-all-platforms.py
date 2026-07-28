#!/usr/bin/env python3
"""
Automated Multi-Platform Poster
Posts to Hacker News, Reddit, and Twitter using MiMo v2.5 for content generation
"""

import requests
import json
import time
import websocket
import urllib.request
import os

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

HERMES_API_URL = os.environ.get(
    "HERMES_API_URL", "https://token-plan-sgp.xiaomimimo.com/v1"
)
HERMES_API_KEY = os.environ.get(
    "HERMES_API_KEY", "tp-s0jae9p6m9d8pirs67549as0ewk9a1up0i1379o1kcg4u6r3"
)
HERMES_MODEL = os.environ.get("HERMES_MODEL", "mimo-v2.5")

# Platform configs
PLATFORMS = {
    "hackernews": {
        "url": "https://news.ycombinator.com/submit",
        "title_prefix": "Show HN:",
    },
    "reddit": {
        "subreddits": [
            "selfhosted",
            "MachineLearning",
            "LocalLLaMA",
            "programming",
            "artificial",
        ]
    },
    "twitter": {"search_terms": ["MCP server", "AI agent framework", "Claude Code"]},
}

# ═══════════════════════════════════════════════════════════════
# LLM CONTENT GENERATION
# ═══════════════════════════════════════════════════════════════


def generate_content(platform, topic="AI infrastructure"):
    """Generate platform-specific content using MiMo v2.5"""

    prompts = {
        "hackernews_title": """Generate a compelling Hacker News 'Show HN' title for TormentNexus, an open-source local-first AI control plane.

Key features:
- Progressive MCP tool routing (60% token reduction)
- Persistent memory across sessions (14K+ memories)
- LLM waterfall failover (zero downtime)
- Works with Claude Code, Cursor, Copilot, Gemini CLI

Requirements:
- Start with "Show HN:"
- Under 80 characters
- Technical but accessible
- Mention "local-first" or "open source"

Example: "Show HN: Local-first AI Control Plane with Progressive Tool Routing"
""",
        "hackernews_body": """Write a Hacker News 'Show HN' post body for TormentNexus.

Include:
1. What it does (2-3 sentences)
2. Why local-first matters (2-3 bullet points)
3. Technical stack (Go + TypeScript + SQLite)
4. Links:
   - Open source: https://github.com/MDMAtk/TormentNexus
   - Website: https://tormentnexus.site
   - Cloud version: https://hypernexus.site

Keep it under 300 words. Be technical but accessible. End with "Happy to answer questions!"
""",
        "reddit_title": """Generate a Reddit post title for r/{subreddit} about TormentNexus.

Subreddit context:
- r/selfhosted: Focus on local-first, self-hosting, privacy
- r/MachineLearning: Focus on architecture, performance, research
- r/LocalLLaMA: Focus on Ollama integration, local models
- r/programming: Focus on Go + TypeScript architecture
- r/artificial: Focus on AI agents, tool routing

Key features:
- Progressive MCP tool routing (60% token reduction)
- Persistent memory across sessions
- LLM waterfall failover
- Works with Claude Code, Cursor, Copilot, Gemini CLI

Requirements:
- Under 300 characters
- Mention the subreddit context
- Include "open source" or "local-first"
""",
        "reddit_body": """Write a Reddit post body for r/{subreddit} about TormentNexus.

Include:
1. What it does (2-3 sentences)
2. Why it matters for this subreddit (2-3 bullet points)
3. Technical details relevant to the subreddit
4. Links:
   - Open source: https://github.com/MDMAtk/TormentNexus
   - Website: https://tormentnexus.site
   - Cloud version: https://hypernexus.site

Keep it under 500 words. Match the subreddit's tone and interests.
""",
        "twitter_thread": """Generate a 6-tweet thread about TormentNexus for Twitter.

Tweet 1: Hook - What problem does it solve?
Tweet 2: Key feature 1 - Progressive MCP tool routing
Tweet 3: Key feature 2 - Persistent memory
Tweet 4: Key feature 3 - LLM waterfall failover
Tweet 5: Why local-first matters
Tweet 6: CTA with links

Requirements:
- Each tweet under 280 characters
- Use emojis sparingly
- Include hashtags: #AI #MCP #OpenSource
- Links in tweet 6:
  - Open source: https://github.com/MDMAtk/TormentNexus
  - Website: https://tormentnexus.site
""",
    }

    prompt_key = f"{platform}_title" if "title" in topic else f"{platform}_body"
    if platform == "twitter":
        prompt_key = "twitter_thread"

    prompt = prompts.get(prompt_key, prompts["hackernews_body"])

    try:
        response = requests.post(
            f"{HERMES_API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {HERMES_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": HERMES_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert technical writer and marketer. Write compelling, accurate content for developer audiences.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1000,
                "temperature": 0.7,
            },
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"LLM error: {response.status_code}")
            return None
    except Exception as e:
        print(f"LLM error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# CDP BROWSER AUTOMATION
# ═══════════════════════════════════════════════════════════════


def get_cdp_url():
    """Get a usable browser tab URL"""
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        # Prefer about:blank tabs
        for tab in tabs:
            if tab.get("url", "") == "about:blank":
                return tab.get("webSocketDebuggerUrl")
        # Fallback to generic tabs
        for tab in tabs:
            url = tab.get("url", "")
            if (
                url.startswith("https://")
                and "x.com" not in url
                and "linkedin" not in url
            ):
                return tab.get("webSocketDebuggerUrl")
        # Create new tab
        browser_resp = urllib.request.urlopen(
            "http://localhost:9222/json/version", timeout=5
        )
        browser_ws = json.loads(browser_resp.read()).get("webSocketDebuggerUrl")
        if browser_ws:
            ws = websocket.create_connection(browser_ws, timeout=15)
            ws.send(
                json.dumps(
                    {
                        "id": 1,
                        "method": "Target.createTarget",
                        "params": {"url": "about:blank"},
                    }
                )
            )
            time.sleep(2)
            target_id = None
            for _ in range(5):
                try:
                    ws.settimeout(3)
                    d = json.loads(ws.recv())
                    if d.get("id") == 1:
                        target_id = d.get("result", {}).get("targetId")
                        break
                except:
                    continue
            ws.close()
            if target_id:
                resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
                for t in json.loads(resp.read()):
                    if t.get("id") == target_id:
                        return t.get("webSocketDebuggerUrl")
    except:
        pass
    return None


def send_and_recv(ws, msg_id, method, params=None, timeout=8):
    """Send CDP command and wait for response"""
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    time.sleep(1)
    result = None
    for _ in range(10):
        try:
            ws.settimeout(timeout)
            data = json.loads(ws.recv())
            if data.get("id") == msg_id:
                result = data.get("result", {}).get("result", {}).get("value")
                break
        except:
            break
    return result


def navigate(ws, url, wait=7):
    """Navigate to URL"""
    ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}}))
    time.sleep(wait)
    for _ in range(10):
        try:
            ws.settimeout(0.5)
            ws.recv()
        except:
            break


# ═══════════════════════════════════════════════════════════════
# PLATFORM POSTERS
# ═══════════════════════════════════════════════════════════════


def post_to_hackernews(ws, title, body):
    """Post to Hacker News"""
    print("[HN] Navigating to submit page...")
    navigate(ws, "https://news.ycombinator.com/submit")
    time.sleep(3)

    # Fill title
    print("[HN] Filling title...")
    send_and_recv(
        ws,
        2,
        "Runtime.evaluate",
        {
            "expression": f"""
        (function() {{
            var title = document.querySelector('input[name="title"]');
            if (title) {{
                title.value = {json.dumps(title)};
                return 'filled';
            }}
            return 'not found';
        }})()
        """,
            "returnByValue": True,
        },
    )
    time.sleep(1)

    # Fill body
    print("[HN] Filling body...")
    send_and_recv(
        ws,
        3,
        "Runtime.evaluate",
        {
            "expression": f"""
        (function() {{
            var text = document.querySelector('textarea[name="text"]');
            if (text) {{
                text.value = {json.dumps(body)};
                return 'filled';
            }}
            return 'not found';
        }})()
        """,
            "returnByValue": True,
        },
    )
    time.sleep(1)

    # Submit
    print("[HN] Submitting...")
    result = send_and_recv(
        ws,
        4,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var btn = document.querySelector('input[type="submit"]');
            if (btn) {
                btn.click();
                return 'submitted';
            }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(3)
    return "submitted" in str(result)


def post_to_reddit(ws, subreddit, title, body):
    """Post to Reddit"""
    print(f"[Reddit] Navigating to r/{subreddit}...")
    navigate(ws, f"https://old.reddit.com/r/{subreddit}/submit")
    time.sleep(3)

    # Fill title
    print("[Reddit] Filling title...")
    send_and_recv(
        ws,
        2,
        "Runtime.evaluate",
        {
            "expression": f"""
        (function() {{
            var title = document.querySelector('#title');
            if (title) {{
                title.value = {json.dumps(title)};
                return 'filled';
            }}
            return 'not found';
        }})()
        """,
            "returnByValue": True,
        },
    )
    time.sleep(1)

    # Fill body
    print("[Reddit] Filling body...")
    send_and_recv(
        ws,
        3,
        "Runtime.evaluate",
        {
            "expression": f"""
        (function() {{
            var text = document.querySelector('#text');
            if (text) {{
                text.value = {json.dumps(body)};
                return 'filled';
            }}
            return 'not found';
        }})()
        """,
            "returnByValue": True,
        },
    )
    time.sleep(1)

    # Submit
    print("[Reddit] Submitting...")
    result = send_and_recv(
        ws,
        4,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var btn = document.querySelector('button[type="submit"]');
            if (btn) {
                btn.click();
                return 'submitted';
            }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(3)
    return "submitted" in str(result)


def post_to_twitter(ws, text):
    """Post to Twitter"""
    print("[Twitter] Navigating to compose...")
    navigate(ws, "https://x.com/compose/post")
    time.sleep(3)

    # Focus textarea
    print("[Twitter] Focusing textarea...")
    send_and_recv(
        ws,
        2,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var box = document.querySelector('[data-testid="tweetTextarea_0"]');
            if (box) {
                box.focus();
                return 'focused';
            }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )
    time.sleep(1)

    # Type content
    print("[Twitter] Typing content...")
    ws.send(
        json.dumps(
            {"id": 3, "method": "Input.insertText", "params": {"text": text[:280]}}
        )
    )
    time.sleep(2)

    # Submit
    print("[Twitter] Submitting...")
    result = send_and_recv(
        ws,
        4,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var btn = document.querySelector('[data-testid="tweetButton"]');
            if (btn) {
                btn.click();
                return 'tweeted';
            }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(3)
    return "tweeted" in str(result)


# ═══════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════


def main():
    print("=" * 60)
    print("AUTOMATED MULTI-PLATFORM POSTER")
    print("=" * 60)
    print()

    # Check browser connection
    ws_url = get_cdp_url()
    if not ws_url:
        print(
            "ERROR: No browser connection. Start Edge with --remote-debugging-port=9222"
        )
        return

    print(f"Connected to browser: {ws_url[:50]}...")
    ws = websocket.create_connection(ws_url, timeout=30)

    results = {"hackernews": False, "reddit": [], "twitter": False}

    # ═══════════════════════════════════════════════════════════
    # 1. HACKER NEWS
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("HACKER NEWS")
    print("=" * 60)

    hn_title = generate_content("hackernews", "title")
    hn_body = generate_content("hackernews", "body")

    if hn_title and hn_body:
        print(f"Title: {hn_title}")
        print(f"Body: {hn_body[:100]}...")
        results["hackernews"] = post_to_hackernews(ws, hn_title, hn_body)
    else:
        print("Failed to generate HN content")

    time.sleep(5)

    # ═══════════════════════════════════════════════════════════
    # 2. REDDIT
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("REDDIT")
    print("=" * 60)

    for subreddit in PLATFORMS["reddit"]["subreddits"][:2]:  # Limit to 2 subreddits
        print(f"\n--- r/{subreddit} ---")

        reddit_title = generate_content("reddit", f"title for r/{subreddit}")
        reddit_body = generate_content("reddit", f"body for r/{subreddit}")

        if reddit_title and reddit_body:
            print(f"Title: {reddit_title}")
            print(f"Body: {reddit_body[:100]}...")
            result = post_to_reddit(ws, subreddit, reddit_title, reddit_body)
            results["reddit"].append({"subreddit": subreddit, "success": result})
        else:
            print(f"Failed to generate content for r/{subreddit}")

        time.sleep(10)

    # ═══════════════════════════════════════════════════════════
    # 3. TWITTER
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TWITTER")
    print("=" * 60)

    twitter_thread = generate_content("twitter", "thread")

    if twitter_thread:
        # Extract first tweet from thread
        tweets = twitter_thread.split("\n\n")
        first_tweet = tweets[0] if tweets else twitter_thread[:280]
        print(f"Tweet: {first_tweet[:100]}...")
        results["twitter"] = post_to_twitter(ws, first_tweet)
    else:
        print("Failed to generate Twitter content")

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Hacker News: {'POSTED' if results['hackernews'] else 'FAILED'}")
    print(
        f"Reddit: {len([r for r in results['reddit'] if r.get('success')])}/{len(results['reddit'])} posted"
    )
    print(f"Twitter: {'POSTED' if results['twitter'] else 'FAILED'}")
    print("=" * 60)

    ws.close()


if __name__ == "__main__":
    main()
