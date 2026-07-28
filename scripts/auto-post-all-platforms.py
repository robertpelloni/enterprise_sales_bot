#!/usr/bin/env python3
"""
Automated Multi-Platform Poster with MiMo v2.5
Posts to Hacker News, Reddit, and Twitter using CDP
"""
import websocket
import json
import urllib.request
import time
import os
import requests

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

HERMES_API_URL = os.environ.get("HERMES_API_URL", "https://token-plan-sgp.xiaomimimo.com/v1")
HERMES_API_KEY = os.environ.get("HERMES_API_KEY", "tp-s0jae9p6m9d8pirs67549as0ewk9a1up0i1379o1kcg4u6r3")
HERMES_MODEL = os.environ.get("HERMES_MODEL", "mimo-v2.5")

# Less prominent subreddits (smaller, more engaged communities)
REDDIT_SUBREDDITS = [
    "MCP_Servers",
    "AI_Agents",
    "AgentFrameworks",
    "LLMDevs",
    "PromptEngineering",
    "AItools",
    "devtools",
    "opensourceai"
]

# ═══════════════════════════════════════════════════════════════
# LLM CONTENT GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_content(platform, subreddit=None):
    """Generate platform-specific content using MiMo v2.5"""
    
    prompts = {
        "hackernews_title": """Generate a Hacker News 'Show HN' title for TormentNexus.

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

Return ONLY the title, nothing else.""",

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
Return ONLY the post body.""",

        "reddit": f"""Write a Reddit post for r/{subreddit or 'MCP_Servers'} about TormentNexus.

Context about the subreddit:
- MCP_Servers: People interested in Model Context Protocol servers
- AI_Agents: People building AI agents
- AgentFrameworks: People looking for agent frameworks
- LLMDevs: LLM developers
- PromptEngineering: Prompt engineers
- AItools: People looking for AI tools
- devtools: Developer tool enthusiasts
- opensourceai: Open source AI community

Key features to mention:
- Progressive MCP tool routing (60% token reduction)
- Persistent memory across sessions (14K+ memories)
- LLM waterfall failover (zero downtime)
- Works with Claude Code, Cursor, Copilot, Gemini CLI

Links to include:
- Open source: https://github.com/MDMAtk/TormentNexus
- Website: https://tormentnexus.site

Requirements:
- Write a title on the first line
- Write the body after a blank line
- Be authentic and helpful, not salesy
- Focus on the problem being solved
- Under 300 words total
- Match the subreddit's tone

Format:
TITLE: [your title]

[body text]""",

        "twitter": """Generate a single tweet about TormentNexus.

Key features:
- Progressive MCP tool routing (60% token reduction)
- Persistent memory across sessions (14K+ memories)
- LLM waterfall failover (zero downtime)
- Works with Claude Code, Cursor, Copilot, Gemini CLI

Links:
- https://github.com/MDMAtk/TormentNexus
- https://tormentnexus.site

Requirements:
- Under 280 characters
- Include one link
- Use 1-2 hashtags max
- Be authentic, not salesy

Return ONLY the tweet text."""
    }
    
    prompt_key = platform
    if platform == "reddit":
        prompt_key = "reddit"
    
    prompt = prompts.get(prompt_key, prompts["twitter"])
    
    try:
        response = requests.post(
            f"{HERMES_API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {HERMES_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": HERMES_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an expert technical writer. Write concise, authentic content for developer audiences. No fluff, no marketing speak."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.8
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"  LLM error: {response.status_code}")
            return None
    except Exception as e:
        print(f"  LLM error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# CDP HELPERS
# ═══════════════════════════════════════════════════════════════

def get_browser_ws():
    """Get browser WebSocket URL"""
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json/version", timeout=5)
        return json.loads(resp.read()).get("webSocketDebuggerUrl")
    except:
        return None

def create_tab(browser_ws, url):
    """Create a new tab and return its WebSocket URL"""
    ws = websocket.create_connection(browser_ws, timeout=15)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": url}}))
    time.sleep(5)
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
    return None

def send_and_recv(ws, msg_id, method, params=None, timeout=8):
    """Send CDP command and get response"""
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

# ═══════════════════════════════════════════════════════════════
# POSTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def post_to_hackernews(browser_ws):
    """Post to Hacker News"""
    print("\n" + "=" * 60)
    print("HACKER NEWS")
    print("=" * 60)
    
    # Generate content
    print("Generating title...")
    title = generate_content("hackernews_title")
    if not title:
        print("Failed to generate title")
        return False
    print(f"Title: {title}")
    
    print("Generating body...")
    body = generate_content("hackernews_body")
    if not body:
        print("Failed to generate body")
        return False
    print(f"Body: {body[:100]}...")
    
    # Create tab and navigate
    print("Creating tab...")
    tab_ws = create_tab(browser_ws, "https://news.ycombinator.com/submit")
    if not tab_ws:
        print("Failed to create tab")
        return False
    
    ws = websocket.create_connection(tab_ws, timeout=30)
    print("Connected to HN submit page")
    
    # Fill title
    print("Filling title...")
    result = send_and_recv(ws, 2, "Runtime.evaluate", {
        "expression": f"""
        (function() {{
            var el = document.querySelector('input[name="title"]');
            if (el) {{
                el.value = {json.dumps(title)};
                return 'filled';
            }}
            return 'not found';
        }})()
        """,
        "returnByValue": True
    })
    print(f"  Title: {result}")
    
    # Fill body
    print("Filling body...")
    result = send_and_recv(ws, 3, "Runtime.evaluate", {
        "expression": f"""
        (function() {{
            var el = document.querySelector('textarea[name="text"]');
            if (el) {{
                el.value = {json.dumps(body)};
                return 'filled';
            }}
            return 'not found';
        }})()
        """,
        "returnByValue": True
    })
    print(f"  Body: {result}")
    
    # Submit
    print("Submitting...")
    result = send_and_recv(ws, 4, "Runtime.evaluate", {
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
        "returnByValue": True
    })
    print(f"  Result: {result}")
    
    time.sleep(3)
    
    # Check final URL
    final_url = send_and_recv(ws, 5, "Runtime.evaluate", {
        "expression": "window.location.href",
        "returnByValue": True
    })
    print(f"  Final URL: {final_url}")
    
    ws.close()
    return "newest" in str(final_url)

def post_to_reddit(browser_ws, subreddit):
    """Post to a single subreddit"""
    print(f"\n--- r/{subreddit} ---")
    
    # Generate content
    print("Generating content...")
    content = generate_content("reddit", subreddit)
    if not content:
        print("Failed to generate content")
        return False
    
    # Parse title and body
    lines = content.strip().split("\n")
    title = lines[0].replace("TITLE:", "").strip() if lines[0].startswith("TITLE:") else lines[0]
    body = "\n".join(lines[2:]).strip() if len(lines) > 2 else content
    
    print(f"Title: {title[:80]}...")
    print(f"Body: {body[:100]}...")
    
    # Create tab
    print("Creating tab...")
    tab_ws = create_tab(browser_ws, f"https://old.reddit.com/r/{subreddit}/submit")
    if not tab_ws:
        print("Failed to create tab")
        return False
    
    ws = websocket.create_connection(tab_ws, timeout=30)
    print(f"Connected to r/{subreddit}")
    
    # Wait for page to load
    time.sleep(3)
    
    # Fill title
    print("Filling title...")
    result = send_and_recv(ws, 2, "Runtime.evaluate", {
        "expression": f"""
        (function() {{
            var el = document.querySelector('#title');
            if (el) {{
                el.value = {json.dumps(title)};
                return 'filled';
            }}
            return 'not found';
        }})()
        """,
        "returnByValue": True
    })
    print(f"  Title: {result}")
    
    # Fill body
    print("Filling body...")
    result = send_and_recv(ws, 3, "Runtime.evaluate", {
        "expression": f"""
        (function() {{
            var el = document.querySelector('#text');
            if (el) {{
                el.value = {json.dumps(body)};
                return 'filled';
            }}
            return 'not found';
        }})()
        """,
        "returnByValue": True
    })
    print(f"  Body: {result}")
    
    # Submit
    print("Submitting...")
    result = send_and_recv(ws, 4, "Runtime.evaluate", {
        "expression": """
        (function() {
            var btn = document.querySelector('button[type="submit"], input[type="submit"]');
            if (btn) {
                btn.click();
                return 'submitted';
            }
            return 'not found';
        })()
        """,
        "returnByValue": True
    })
    print(f"  Result: {result}")
    
    time.sleep(3)
    
    # Check URL
    final_url = send_and_recv(ws, 5, "Runtime.evaluate", {
        "expression": "window.location.href",
        "returnByValue": True
    })
    print(f"  Final URL: {final_url}")
    
    ws.close()
    return subreddit in str(final_url)

def post_to_twitter(browser_ws):
    """Post to Twitter"""
    print("\n" + "=" * 60)
    print("TWITTER")
    print("=" * 60)
    
    # Generate content
    print("Generating tweet...")
    tweet = generate_content("twitter")
    if not tweet:
        print("Failed to generate tweet")
        return False
    print(f"Tweet: {tweet}")
    
    # Create tab
    print("Creating tab...")
    tab_ws = create_tab(browser_ws, "https://x.com/compose/post")
    if not tab_ws:
        print("Failed to create tab")
        return False
    
    ws = websocket.create_connection(tab_ws, timeout=30)
    print("Connected to Twitter compose")
    
    # Wait for composer
    time.sleep(3)
    
    # Focus textarea
    print("Focusing textarea...")
    result = send_and_recv(ws, 2, "Runtime.evaluate", {
        "expression": """
        (function() {
            var el = document.querySelector('[data-testid="tweetTextarea_0"]');
            if (el) {
                el.focus();
                return 'focused';
            }
            return 'not found';
        })()
        """,
        "returnByValue": True
    })
    print(f"  Focus: {result}")
    
    # Type content
    print("Typing tweet...")
    ws.send(json.dumps({"id": 3, "method": "Input.insertText", "params": {"text": tweet[:280]}}))
    time.sleep(2)
    
    # Submit
    print("Submitting...")
    result = send_and_recv(ws, 4, "Runtime.evaluate", {
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
        "returnByValue": True
    })
    print(f"  Result: {result}")
    
    ws.close()
    return "tweeted" in str(result)

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("AUTOMATED MULTI-PLATFORM POSTER")
    print("Using MiMo v2.5 for content generation")
    print("=" * 60)
    
    # Get browser connection
    browser_ws = get_browser_ws()
    if not browser_ws:
        print("ERROR: No browser connection. Start Edge with --remote-debugging-port=9222")
        return
    
    print(f"Connected to browser: {browser_ws[:50]}...")
    
    results = {"hackernews": False, "reddit": [], "twitter": False}
    
    # 1. Hacker News
    results["hackernews"] = post_to_hackernews(browser_ws)
    time.sleep(5)
    
    # 2. Reddit (2 subreddits to avoid spam)
    print("\n" + "=" * 60)
    print("REDDIT")
    print("=" * 60)
    
    for subreddit in REDDIT_SUBREDDITS[:2]:
        result = post_to_reddit(browser_ws, subreddit)
        results["reddit"].append({"subreddit": subreddit, "success": result})
        time.sleep(10)
    
    # 3. Twitter
    results["twitter"] = post_to_twitter(browser_ws)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Hacker News: {'POSTED' if results['hackernews'] else 'FAILED'}")
    print(f"Reddit: {len([r for r in results['reddit'] if r.get('success')])}/{len(results['reddit'])} posted")
    print(f"Twitter: {'POSTED' if results['twitter'] else 'FAILED'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
