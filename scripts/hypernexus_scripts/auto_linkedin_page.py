"""
LinkedIn HyperNexus Page Agent
Posts content and comments as the HyperNexus company page using CDP
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
from llm_reply import get_url_for_context, URL_OPENSOURCE, URL_COMMERCIAL


COMPANY_PAGE_URL = "https://www.linkedin.com/company/135697123/admin/"
COMPANY_ID = "135697123"

# Fallback templates if LLM fails
FALLBACK_TEMPLATES = {
    "mcp": "Progressive tool routing is key for MCP management - semantic search matches prompts to top 3 relevant tools. {url}",
    "rate_limit": "The LLM Waterfall Pattern: Primary -> Secondary -> Local -> Queue. Zero downtime from rate limits. {url}",
    "agent": "Progressive tool routing + persistent memory + multi-model failover is the reliable AI agent stack. {url}",
    "generic": "Progressive tool routing changes the game for AI development efficiency. {url}",
}

URL_COMMERCIAL = "https://hypernexus.site"
URL_OPENSOURCE = "https://github.com/MDMAtk/TormentNexus"
URL_OPENSOURCE_SITE = "https://tormentnexus.site"

# Posts to publish as the HyperNexus page
PAGE_POSTS = [
    """Every AI agent has the same problem: it drowns in 50,000 tokens of tool definitions before doing any actual work.

We solved this with Progressive Tool Routing.

Instead of loading ALL tool definitions into context, semantic vector search matches your prompt to the top 3 most relevant tools.

The result? 60% reduction in token usage. Faster responses. Better accuracy.

Your agent doesn't need 50 tools at once. It needs the RIGHT 3 tools.

That's what HyperNexus does automatically.

https://hypernexus.site

#AI #DeveloperTools #MCP #OpenSource""",
    """It's 2 AM. Your AI agent is in the middle of a critical task. OpenAI returns a 429 - rate limited.

Your workflow stops. You wait. You retry. Productivity: zero.

This doesn't happen with the LLM Waterfall Pattern.

Primary API -> Secondary API -> Local models -> Queue.

When one provider fails, the next picks up automatically. Zero downtime. Zero interruptions.

Rate limits are inevitable. Downtime is not.

#AI #LLM #DeveloperTools #Infrastructure""",
    """Every AI agent forgets everything between sessions.

Ask it to remember a decision from yesterday? Blank stare. Tell it your coding preferences? You'll tell it again tomorrow.

We built a dual-tier memory architecture:

L1: Session scratchpad (ephemeral, fast)
L2: Permanent semantic storage (SQLite + sqlite-vec)

Your agent remembers decisions across sessions. Searches by meaning, not keywords.

That's how you build an AI agent that never forgets.

#AI #MachineLearning #DeveloperTools #Memory""",
    """MCP servers are powerful. But managing 50+ of them? That's a nightmare.

Tool definitions bloat your context window. Servers go down silently. Configs drift across teams.

We built HyperNexus to solve this:

- Progressive routing: Only load relevant tools
- Health monitoring: Know when servers fail
- GitOps configs: Version-controlled, PR-reviewed
- Team sync: One push updates everyone

MCP shouldn't be painful. It should just work.

#MCP #AI #DeveloperTools #DevOps""",
    """Solo AI coding is fast. Multi-agent swarms are faster.

We measured it: teams using Planner -> Implementer -> Tester -> Critic role rotation complete tasks 3x faster than solo Copilot workflows.

The key ingredients:
- Role specialization (each agent has one job)
- Consensus engine (resolves conflicts automatically)
- Shared memory (agents learn from each other)
- Progressive tool routing (right tools, right time)

The future of AI development is swarms, not solos.

#AI #SoftwareEngineering #DeveloperTools #Productivity""",
    """We just open-sourced HyperNexus - a Universal AI Control Plane.

What it does:
- Routes tools progressively (60% token savings)
- Manages MCP servers automatically
- Provides persistent memory across sessions
- Handles LLM failover with zero downtime
- Supports Claude Code, Cursor, Copilot, and more

$5/mo for the hosted version. Free if you self-host.

Because AI infrastructure should be accessible to every developer.

https://hypernexus.site | https://github.com/MDMAtk/TormentNexus

#OpenSource #AI #DeveloperTools #MCP""",
    """Why does HyperNexus use Go for the kernel and TypeScript for the dashboard?

Go:
- 446 HTTP handlers with goroutines
- Native concurrency for multi-agent orchestration
- Single binary deployment
- Sub-millisecond routing decisions

TypeScript:
- React dashboard with real-time updates
- Type-safe API contracts with tRPC
- Rich ecosystem for UI components

The result: A modular monolith that's fast, reliable, and developer-friendly.

Sometimes the best architecture is two languages, not one.

#Go #TypeScript #SoftwareArchitecture #AI""",
]

# Reply templates for commenting on relevant LinkedIn posts
REPLY_TEMPLATES = {
    "mcp": [
        "Progressive tool routing is key for MCP management. Instead of loading all definitions, semantic search matches prompts to the top 3 most relevant tools. 60% token reduction. {url}",
        "The biggest challenge with MCP servers is context bloat. Progressive routing dynamically selects only the tools you need per task. Game changer for efficiency. {url}",
        "MCP servers are powerful but need smart management. HyperNexus handles tool routing, health monitoring, and failover automatically. {url}",
    ],
    "rate_limit": [
        "The LLM Waterfall Pattern solves rate limits: Primary API -> Secondary API -> Local models -> Queue. Zero downtime from 429s. {url}",
        "Transparent failover is the answer. When one provider rate limits, the next picks up automatically. Your agent shouldn't even notice. {url}",
        "Three-tier LLM cascade: cloud primary, secondary backup, local fallback. No more rate limit interruptions. {url}",
    ],
    "agent": [
        "The key to reliable AI agents: progressive tool routing + persistent memory + multi-model failover. Infrastructure matters more than prompts. {url}",
        "AI agents need infrastructure, not just clever prompts. Tool routing, memory management, and failover should be automatic. {url}",
        "Multi-agent swarms with role rotation (Planner -> Implementer -> Tester -> Critic) outperform solo workflows by 3x. {url}",
    ],
    "generic": [
        "Great insight! Progressive tool routing changes the game for AI development efficiency. {url}",
        "This resonates. AI infrastructure should be as well-engineered as the applications it powers. {url}",
        "The key is making AI tools work together seamlessly. That's what a universal control plane solves. {url}",
    ],
}


def is_opensource_context(text):
    """Determine if post is more open-source focused"""
    text_lower = text.lower()
    oss_keywords = [
        "open source",
        "opensource",
        "free",
        "self-host",
        "github",
        "foss",
        "community",
        "hobbyist",
        "indie",
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
    ]
    oss_score = sum(1 for kw in oss_keywords if kw in text_lower)
    commercial_score = sum(1 for kw in commercial_keywords if kw in text_lower)
    return oss_score >= commercial_score


def get_url_for_context(text):
    """Return appropriate URL based on context"""
    if is_opensource_context(text):
        return URL_OPENSOURCE
    return URL_COMMERCIAL


def get_browser_ws():
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json/version", timeout=5)
        return json.loads(resp.read()).get("webSocketDebuggerUrl")
    except Exception:
        return None


def create_tab(browser_ws, url="about:blank"):
    ws = websocket.create_connection(browser_ws, timeout=15)
    ws.send(
        json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": url}})
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
        except Exception:
            continue
    ws.close()
    if target_id:
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        for t in tabs:
            if t.get("id") == target_id:
                return t.get("webSocketDebuggerUrl")
    return None


def send_and_recv(ws, msg_id, method, params=None, timeout=8):
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    time.sleep(1)
    result = None
    for _ in range(15):
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


def navigate(ws, url, wait=7):
    ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}}))
    time.sleep(wait)
    for _ in range(10):
        try:
            ws.settimeout(0.5)
            ws.recv()
        except Exception:
            break


def log(msg):
    ts = time.strftime("%H:%M:%S")
    sys.stdout.buffer.write(f"[{ts}] [LinkedIn] {msg}\n".encode("utf-8"))
    sys.stdout.flush()


def open_post_editor(ws):
    """Navigate to company page and open the post creation dialog"""
    navigate(ws, COMPANY_PAGE_URL)

    # Click "Create" button
    result = send_and_recv(
        ws,
        10,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === 'Create') {
                    buttons[i].click();
                    return 'clicked Create';
                }
            }
            return 'Create not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "clicked" not in str(result):
        log(f"Create button: {result}")
        return False

    time.sleep(2)

    # Click "Start a post"
    result = send_and_recv(
        ws,
        11,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var links = document.querySelectorAll('a, button, [role="button"]');
            for (var i = 0; i < links.length; i++) {
                var text = links[i].textContent.trim();
                if (text.startsWith('Start a post')) {
                    links[i].click();
                    return 'clicked Start a post';
                }
            }
            return 'Start a post not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "clicked" not in str(result):
        log(f"Start a post: {result}")
        return False

    time.sleep(3)
    return True


def type_post_content(ws, content):
    """Type content into the post editor"""
    # Focus the post editor textbox
    result = send_and_recv(
        ws,
        12,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var editables = document.querySelectorAll('[contenteditable="true"][role="textbox"]');
            for (var i = 0; i < editables.length; i++) {
                var ph = editables[i].getAttribute('data-placeholder') || '';
                if (ph.includes('What do you want to talk about')) {
                    editables[i].click();
                    editables[i].focus();
                    return 'focused';
                }
            }
            return 'editor not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "focused" not in str(result):
        log(f"Editor focus: {result}")
        return False

    time.sleep(1)

    # Type content
    ws.send(
        json.dumps(
            {"id": 13, "method": "Input.insertText", "params": {"text": content}}
        )
    )
    time.sleep(3)
    for _ in range(5):
        try:
            ws.settimeout(1)
            ws.recv()
        except Exception:
            break

    return True


def click_post_button(ws):
    """Click the Post button to publish"""
    result = send_and_recv(
        ws,
        14,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === 'Post' && !buttons[i].disabled) {
                    buttons[i].click();
                    return 'posted';
                }
            }
            return 'Post button not found or disabled';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(5)

    if result and "posted" in str(result):
        return True

    log(f"Post button: {result}")
    return False


def publish_post(ws, content):
    """Full workflow: open editor, type content, post"""
    log("Opening post editor...")
    if not open_post_editor(ws):
        return False

    log("Typing content...")
    if not type_post_content(ws, content):
        return False

    log("Clicking Post...")
    if not click_post_button(ws):
        return False

    log("Post published!")
    return True


def comment_on_post(ws, post_url, comment_text):
    """Navigate to a post and leave a comment as HyperNexus"""
    navigate(ws, post_url)

    # Find and click the comment textbox
    result = send_and_recv(
        ws,
        20,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var editables = document.querySelectorAll('[contenteditable="true"][role="textbox"]');
            for (var i = 0; i < editables.length; i++) {
                var ph = editables[i].getAttribute('data-placeholder') || '';
                if (ph.includes('Comment as HyperNexus')) {
                    editables[i].click();
                    editables[i].focus();
                    return 'focused comment box';
                }
            }
            return 'comment box not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "focused" not in str(result):
        log(f"Comment box: {result}")
        return False

    time.sleep(1)

    # Type comment
    ws.send(
        json.dumps(
            {"id": 21, "method": "Input.insertText", "params": {"text": comment_text}}
        )
    )
    time.sleep(2)
    for _ in range(5):
        try:
            ws.settimeout(1)
            ws.recv()
        except Exception:
            break

    # Click Comment button
    result = send_and_recv(
        ws,
        22,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === 'Comment' && !buttons[i].disabled) {
                    buttons[i].click();
                    return 'commented';
                }
            }
            return 'Comment button not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(3)

    if result and "commented" in str(result):
        return True

    log(f"Comment button: {result}")
    return False


def search_linkedin_feed(ws, term):
    """Search LinkedIn for relevant posts"""
    url = f"https://www.linkedin.com/search/results/content/?keywords={term}&origin=SWITCH_SEARCH_VERTICAL&timePostedInterval=%5B%22past-week%22%5D"
    navigate(ws, url)

    result = send_and_recv(
        ws,
        30,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var posts = [];
            var items = document.querySelectorAll('.feed-shared-update-v2, .update-components-actor');
            var postContainers = document.querySelectorAll('[data-urn*="urn:li:activity"]');
            
            for (var i = 0; i < Math.min(postContainers.length, 10); i++) {
                var container = postContainers[i];
                var textEl = container.querySelector('.feed-shared-text, .update-components-text');
                var authorEl = container.querySelector('.update-components-actor__name, .feed-shared-actor__name');
                var linkEl = container.querySelector('a[href*="/posts/"], a[href*="/pulse/"]');
                
                if (textEl) {
                    posts.push({
                        text: textEl.textContent.trim().substring(0, 300),
                        author: authorEl ? authorEl.textContent.trim().substring(0, 50) : 'Unknown',
                        url: linkEl ? linkEl.href : ''
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


def categorize_linkedin_post(text):
    t = text.lower()
    if any(
        w in t for w in ["mcp", "model context protocol", "tool routing", "tool server"]
    ):
        return "mcp"
    if any(w in t for w in ["rate limit", "429", "quota", "api limit"]):
        return "rate_limit"
    if any(w in t for w in ["agent", "framework", "orchestration", "workflow"]):
        return "agent"
    return "generic"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn HyperNexus Page Agent")
    parser.add_argument("--post", action="store_true", help="Publish all page posts")
    parser.add_argument(
        "--comment", action="store_true", help="Comment on relevant posts"
    )
    parser.add_argument(
        "--post-index", type=int, default=-1, help="Post a specific post by index (0-6)"
    )
    args = parser.parse_args()

    browser_ws = get_browser_ws()
    if not browser_ws:
        print("Could not connect to browser")
        return

    # Create a dedicated tab for LinkedIn
    tab_ws_url = create_tab(browser_ws, "https://www.linkedin.com/feed/")
    if not tab_ws_url:
        print("Failed to create LinkedIn tab")
        return

    log(f"Tab: {tab_ws_url}")
    ws = websocket.create_connection(tab_ws_url, timeout=15)
    time.sleep(5)

    # Verify we're on the HyperNexus page
    result = send_and_recv(
        ws,
        1,
        "Runtime.evaluate",
        {
            "expression": "document.title + ' | ' + window.location.href",
            "returnByValue": True,
        },
    )
    log(f"Page: {result}")

    if args.post or args.post_index >= 0:
        # Publish all posts
        posts_to_publish = PAGE_POSTS
        if args.post_index >= 0:
            posts_to_publish = [PAGE_POSTS[args.post_index]]

        for i, content in enumerate(posts_to_publish):
            log(f"Publishing post {i + 1}/{len(posts_to_publish)}...")
            success = publish_post(ws, content)
            if success:
                log(f"Post {i + 1} published!")
            else:
                log(f"Post {i + 1} failed")

            if i < len(posts_to_publish) - 1:
                delay = random.randint(30, 60)
                log(f"Waiting {delay} seconds before next post...")
                time.sleep(delay)

    elif args.comment:
        # Search and comment on relevant posts
        search_terms = ["MCP server", "AI agent", "Claude Code", "developer tools AI"]
        commented_urls = set()
        count = 0

        log("Starting comment agent...")

        while True:
            try:
                term = random.choice(search_terms)
                log(f"Searching LinkedIn for '{term}'...")

                posts = search_linkedin_feed(ws, term)
                log(f"Found {len(posts)} posts")

                candidates = [
                    p
                    for p in posts
                    if len(p.get("text", "")) > 50
                    and p.get("url", "") not in commented_urls
                    and p.get("url", "") != ""
                ]

                if candidates:
                    post = random.choice(candidates)

                    log(f"Commenting on: {post['text'][:60]}...")

                    # Generate intelligent comment with MiMo v2.5
                    log("[LLM] Generating comment with MiMo v2.5...")
                    comment = generate_reply(post["text"], platform="linkedin")

                    if not comment:
                        # Fallback if LLM fails
                        url = get_url_for_context(post["text"])
                        category = categorize_linkedin_post(post["text"])
                        comment = FALLBACK_TEMPLATES.get(
                            category, FALLBACK_TEMPLATES["generic"]
                        ).format(url=url)
                        log(f"[Fallback] {comment[:60]}...")
                    else:
                        log(f"[Comment] {comment[:60]}...")

                    success = comment_on_post(ws, post["url"], comment)

                    if success:
                        commented_urls.add(post["url"])
                        count += 1
                        log(f"Comment #{count} posted!")
                    else:
                        log("Failed to post comment")
                else:
                    log("No suitable posts found")

                delay = random.randint(20, 45) * 60
                log(f"Waiting {delay // 60} minutes...")
                time.sleep(delay)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                log(f"Error: {e}")
                time.sleep(60)

    else:
        print("\nUsage:")
        print("  python auto_linkedin_page.py --post          # Publish all 7 posts")
        print("  python auto_linkedin_page.py --post-index 0  # Publish post #1 only")
        print(
            "  python auto_linkedin_page.py --comment       # Auto-comment on relevant posts"
        )

    ws.close()


if __name__ == "__main__":
    main()
