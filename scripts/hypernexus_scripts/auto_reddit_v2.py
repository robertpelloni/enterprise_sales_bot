"""
Autonomous Reddit Reply Agent v2
Posts intelligent replies to relevant discussions using CDP
Uses MiMo v2.5 LLM for generating contextual replies
"""

import websocket
import json
import time
import random
import urllib.request
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_reply import get_url_for_context

# Fallback templates if LLM fails
FALLBACK_TEMPLATES = {
    "mcp": "Progressive tool routing is key - semantic search matches your prompt to the top 3 most relevant tools instead of loading all definitions. {url}",
    "rate_limit": "The LLM Waterfall Pattern solves this: Primary API -> Secondary API -> Local models -> Queue. Zero downtime from rate limits. {url}",
    "memory": "Dual-tier memory architecture: L1 for session scratchpad, L2 for permanent semantic storage with vector search. {url}",
    "agent": "Progressive tool routing + persistent memory + multi-model failover is the combo that makes AI agents reliable. {url}",
    "generic": "Progressive tool routing changes the game - semantically match tasks to the top 3 tools instead of dumping everything in context. {url}",
}


def is_opensource_context(title):
    """Determine if a post is more open-source focused vs commercial"""
    title_lower = title.lower()
    oss_keywords = [
        "open source",
        "opensource",
        "free",
        "self-host",
        "selfhost",
        "github",
        "foss",
        "community",
        "hobbyist",
        "indie",
        "student",
        "budget",
        "personal project",
        "side project",
    ]
    commercial_keywords = [
        "enterprise",
        "business",
        "company",
        "team",
        "production",
        "saas",
        "paid",
        "pricing",
        "professional",
        "startup",
        "scale",
    ]
    oss_score = sum(1 for kw in oss_keywords if kw in title_lower)
    commercial_score = sum(1 for kw in commercial_keywords if kw in title_lower)
    return oss_score >= commercial_score


def get_cdp_url():
    """Get CDP WebSocket URL from browser"""
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        for tab in tabs:
            if "edge://newtab" in tab.get("url", ""):
                return tab.get("webSocketDebuggerUrl")
        if tabs:
            return tabs[0].get("webSocketDebuggerUrl")
    except Exception:
        pass
    return None


def send_and_recv(ws, msg_id, method, params=None, timeout=5):
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
        except websocket.WebSocketTimeoutException:
            break
        except Exception:
            break
    return result


def navigate(ws, url, wait=6):
    """Navigate to URL and wait"""
    ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}}))
    time.sleep(wait)
    # Clear buffer
    for _ in range(10):
        try:
            ws.settimeout(0.5)
            ws.recv()
        except Exception:
            break


def extract_posts(ws, subreddit):
    """Extract posts from a subreddit"""
    navigate(ws, f"https://old.reddit.com/r/{subreddit}/new/")

    result = send_and_recv(
        ws,
        2,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var posts = [];
            var items = document.querySelectorAll('.link');
            for (var i = 0; i < Math.min(items.length, 15); i++) {
                var titleLink = items[i].querySelector('a.title');
                var commentsLink = items[i].querySelector('a.comments');
                if (titleLink) {
                    var commentText = commentsLink ? commentsLink.textContent.trim() : '0 comments';
                    var commentCount = parseInt(commentText) || 0;
                    posts.push({
                        title: titleLink.textContent.trim(),
                        url: commentsLink ? commentsLink.href : titleLink.href,
                        comments: commentCount
                    });
                }
            }
            return JSON.stringify(posts);
        })()
        """,
            "returnByValue": True,
        },
    )

    if result:
        try:
            return json.loads(result)
        except Exception:
            pass
    return []


def categorize_post(title):
    """Categorize a post by topic"""
    t = title.lower()
    if any(
        w in t for w in ["mcp", "model context protocol", "tool routing", "tool server"]
    ):
        return "mcp"
    if any(w in t for w in ["rate limit", "429", "quota", "api limit"]):
        return "rate_limit"
    if any(w in t for w in ["memory", "forget", "context", "remember"]):
        return "memory"
    if any(w in t for w in ["agent", "framework", "orchestration", "workflow"]):
        return "agent"
    return "generic"


def post_reply(ws, post_url, reply_text):
    """Navigate to post, click reply, type and submit"""
    navigate(ws, post_url)

    # Click the first reply button on the post
    result = send_and_recv(
        ws,
        3,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var btns = document.querySelectorAll('.reply-button a');
            if (btns.length > 0) {
                btns[0].click();
                return 'clicked';
            }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "clicked" not in str(result):
        print(f"  [!] Could not click reply: {result}")
        return False

    time.sleep(2)

    # Focus the visible textarea
    result = send_and_recv(
        ws,
        4,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var tas = document.querySelectorAll('textarea[name="text"]');
            for (var i = 0; i < tas.length; i++) {
                if (tas[i].offsetParent !== null) {
                    tas[i].focus();
                    return 'focused';
                }
            }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "focused" not in str(result):
        print(f"  [!] Could not focus textarea: {result}")
        return False

    time.sleep(1)

    # Type the reply
    ws.send(
        json.dumps(
            {"id": 5, "method": "Input.insertText", "params": {"text": reply_text}}
        )
    )
    time.sleep(2)
    for _ in range(5):
        try:
            ws.settimeout(1)
            ws.recv()
        except Exception:
            break

    # Click save button
    result = send_and_recv(
        ws,
        6,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var btns = document.querySelectorAll('button[type="submit"]');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].offsetParent !== null && btns[i].textContent.trim().toLowerCase() === 'save') {
                    btns[i].click();
                    return 'saved';
                }
            }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(3)

    if result and "saved" in str(result):
        return True

    print(f"  [!] Could not click save: {result}")
    return False


def main():
    ws_url = get_cdp_url()
    if not ws_url:
        print(
            "Could not connect to browser. Is Edge running with --remote-debugging-port=9222?"
        )
        return

    print(f"Connecting to: {ws_url}")
    ws = websocket.create_connection(ws_url, timeout=15)
    print("Connected!")

    subreddits = [
        "mcp",
        "ClaudeAI",
        "LocalLLaMA",
        "MachineLearning",
        "SaaS",
        "startups",
        "SideProject",
        "webdev",
    ]
    replied_urls = set()
    reply_count = 0

    print("\n" + "=" * 60)
    print("  Autonomous Reddit Reply Agent v2")
    print("=" * 60)
    print(f"  Subreddits: {', '.join(subreddits)}")
    print("  Delay: 15-45 minutes between replies")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    try:
        while True:
            try:
                subreddit = random.choice(subreddits)
                print(f"\n[Scan] r/{subreddit}...")

                posts = extract_posts(ws, subreddit)
                print(f"[Found] {len(posts)} posts")

                # Filter: 2-50 comments (active but not saturated), not already replied
                candidates = [
                    p
                    for p in posts
                    if 2 <= p.get("comments", 0) <= 50 and p["url"] not in replied_urls
                ]

                if candidates:
                    post = random.choice(candidates)

                    print(f"[Target] {post['title'][:70]}...")
                    print(f"[Comments] {post.get('comments', '?')}")

                    # Generate intelligent reply with MiMo v2.5
                    print("[LLM] Generating reply with MiMo v2.5...")
                    reply = generate_reply(post["title"], platform="reddit")

                    if not reply:
                        # Fallback if LLM fails
                        url = get_url_for_context(post["title"])
                        category = categorize_post(post["title"])
                        reply = FALLBACK_TEMPLATES.get(
                            category, FALLBACK_TEMPLATES["generic"]
                        ).format(url=url)
                        print(f"[Fallback] {reply[:70]}...")
                    else:
                        print(f"[Reply] {reply[:70]}...")

                    success = post_reply(ws, post["url"], reply)

                    if success:
                        replied_urls.add(post["url"])
                        reply_count += 1
                        print(f"[OK] Reply #{reply_count} posted!")
                    else:
                        print("[FAIL] Could not post reply")
                else:
                    print("[Skip] No suitable posts (need 2-50 comments)")

                # Random delay
                delay_min = random.randint(15, 45)
                print(f"[Wait] {delay_min} minutes...")

                for remaining in range(delay_min, 0, -1):
                    time.sleep(60)
                    if remaining % 10 == 0 and remaining > 0:
                        print(f"  ...{remaining} min remaining")

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"[Error] {e}")
                time.sleep(60)

    except KeyboardInterrupt:
        print(f"\n\nStopped. Total replies: {reply_count}")

    ws.close()


if __name__ == "__main__":
    main()
