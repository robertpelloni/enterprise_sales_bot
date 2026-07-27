"""
Autonomous Reddit Reply Agent
Posts intelligent replies to relevant discussions using CDP
"""

import websocket
import json
import time
import random


# HyperNexus context for generating relevant replies
REPLY_TEMPLATES = {
    "mcp": [
        "Progressive tool routing is key here. Instead of loading all MCP definitions into context, semantic search matches your prompt to the top 3 most relevant tools. Reduces token usage by ~60%. HyperNexus does this automatically.",
        "The biggest issue with MCP servers is managing 50+ tool definitions. Progressive routing dynamically selects the most relevant tools based on your current task. Game changer for token efficiency.",
        "For MCP management, I recommend looking at progressive tool routing. You define tools once, and the system intelligently selects which ones to inject based on semantic similarity to your prompt.",
    ],
    "rate_limit": [
        "The LLM Waterfall Pattern solves this: Primary API -> Secondary API -> Local models -> Queue. When one provider rate limits you, it automatically fails over to the next. Zero downtime.",
        "Set up a three-tier cascade: cloud APIs as primary, secondary provider as backup, local Ollama models as fallback. No more rate limit interruptions.",
        "Rate limits are inevitable with AI APIs. The solution is transparent failover. Your agent shouldn't even notice when one provider hits limits.",
    ],
    "memory": [
        "Dual-tier memory architecture is the answer. L1 for session scratchpad (ephemeral, fast), L2 for permanent semantic storage with vector search. Your agent remembers decisions across sessions.",
        "We solved this with a two-layer memory system: session memory for current work, and permanent memory with semantic search for cross-session knowledge.",
        "Memory management is crucial for AI agents. Use SQLite + sqlite-vec for permanent semantic memory. Search past decisions by meaning, not just keywords.",
    ],
    "agent": [
        "For reliable AI agents, combine progressive tool routing + persistent memory + multi-model failover. Most frameworks dump everything into context, but selective tool injection makes agents much more capable.",
        "The key to reliable AI agents is infrastructure, not just prompts. Tool routing, memory management, and failover should be automatic.",
        "AI agent frameworks are evolving fast. The best ones now combine MCP tool routing, persistent memory, and multi-model failover.",
    ],
    "generic": [
        "Great insight! Progressive tool routing changes the game. Instead of dumping 50K tokens of tool definitions, you semantically match the task to the top 3 tools.",
        "This resonates! AI infrastructure should be as well-engineered as the apps it powers.",
        "The key is making AI tools work together seamlessly. Universal control plane is the answer.",
    ],
}


def get_cdp_url():
    """Get CDP WebSocket URL from browser"""
    import urllib.request

    try:
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        for tab in tabs:
            if "edge://newtab" in tab.get("url", ""):
                return tab.get("webSocketDebuggerUrl")
        if tabs:
            return tabs[0].get("webSocketDebuggerUrl")
    except:
        pass
    return None


def navigate_and_wait(ws, url, wait=5):
    """Navigate to URL and wait for page load"""
    ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}}))
    time.sleep(wait)

    # Clear response buffer
    for _ in range(10):
        try:
            ws.settimeout(1)
            ws.recv()
        except:
            break


def extract_posts(ws, subreddit):
    """Extract posts from a subreddit"""
    url = f"https://old.reddit.com/r/{subreddit}/new/"
    navigate_and_wait(ws, url, 6)

    ws.send(
        json.dumps(
            {
                "id": 2,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
            (function() {
                var posts = [];
                var links = document.querySelectorAll('.link .title a.title');
                for (var i = 0; i < Math.min(links.length, 15); i++) {
                    posts.push({
                        title: links[i].textContent.trim(),
                        url: links[i].href
                    });
                }
                return JSON.stringify(posts);
            })()
            """,
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(2)

    for _ in range(5):
        try:
            ws.settimeout(2)
            data = json.loads(ws.recv())
            if data.get("id") == 2:
                result = data.get("result", {}).get("result", {}).get("value", "[]")
                return json.loads(result)
        except:
            continue
    return []


def categorize_post(title):
    """Categorize a post to determine reply type"""
    title_lower = title.lower()

    if any(
        term in title_lower
        for term in ["mcp", "model context protocol", "tool routing", "tool server"]
    ):
        return "mcp"
    elif any(
        term in title_lower for term in ["rate limit", "429", "quota", "api limit"]
    ):
        return "rate_limit"
    elif any(
        term in title_lower for term in ["memory", "forget", "context", "remember"]
    ):
        return "memory"
    elif any(
        term in title_lower
        for term in ["agent", "framework", "orchestration", "workflow"]
    ):
        return "agent"
    else:
        return "generic"


def generate_reply(category):
    """Generate a reply based on category"""
    templates = REPLY_TEMPLATES.get(category, REPLY_TEMPLATES["generic"])
    return random.choice(templates)


def post_reply(ws, post_url, reply_text):
    """Post a reply to a Reddit post"""
    navigate_and_wait(ws, post_url, 6)

    # Find and click reply button
    ws.send(
        json.dumps(
            {
                "id": 3,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
            (function() {
                var links = document.querySelectorAll('a');
                for (var i = 0; i < links.length; i++) {
                    if (links[i].textContent.trim() === 'reply') {
                        links[i].click();
                        return 'reply clicked';
                    }
                }
                return 'reply not found';
            })()
            """,
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(2)

    for _ in range(5):
        try:
            ws.settimeout(2)
            ws.recv()
        except:
            break

    # Find textarea
    ws.send(
        json.dumps(
            {
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
            (function() {
                var textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.focus();
                    return 'textarea focused';
                }
                return 'textarea not found';
            })()
            """,
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(1)

    for _ in range(5):
        try:
            ws.settimeout(2)
            ws.recv()
        except:
            break

    # Type reply
    ws.send(
        json.dumps(
            {"id": 5, "method": "Input.insertText", "params": {"text": reply_text}}
        )
    )
    time.sleep(2)

    for _ in range(5):
        try:
            ws.settimeout(2)
            ws.recv()
        except:
            break

    # Click save button
    ws.send(
        json.dumps(
            {
                "id": 6,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
            (function() {
                var buttons = document.querySelectorAll('button, input[type="submit"]');
                for (var i = 0; i < buttons.length; i++) {
                    var text = buttons[i].textContent.trim().toLowerCase();
                    if (text === 'save' || text === 'submit') {
                        buttons[i].click();
                        return 'save clicked';
                    }
                }
                return 'save not found';
            })()
            """,
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(3)

    for _ in range(5):
        try:
            ws.settimeout(2)
            ws.recv()
        except:
            break

    return True


def main():
    """Main function"""
    ws_url = get_cdp_url()
    if not ws_url:
        print("Could not connect to browser")
        return

    print(f"Connecting to: {ws_url}")

    try:
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
        ]
        replied_posts = set()
        reply_count = 0

        print("\n" + "=" * 60)
        print("Autonomous Reddit Reply Agent Started")
        print("=" * 60)
        print(f"Monitoring subreddits: {', '.join(subreddits)}")
        print("Press Ctrl+C to stop")
        print("=" * 60)

        while True:
            try:
                # Select random subreddit
                subreddit = random.choice(subreddits)
                print(f"\n[Scanning] r/{subreddit}...")

                # Extract posts
                posts = extract_posts(ws, subreddit)
                print(f"[Found] {len(posts)} posts")

                if posts:
                    # Filter out already replied posts
                    new_posts = [p for p in posts if p["url"] not in replied_posts]

                    if new_posts:
                        # Select a random post
                        post = random.choice(new_posts)
                        category = categorize_post(post["title"])
                        reply = generate_reply(category)

                        print(f"[Target] {post['title'][:60]}...")
                        print(f"[Category] {category}")
                        print(f"[Reply] {reply[:60]}...")

                        # Post reply
                        success = post_reply(ws, post["url"], reply)

                        if success:
                            replied_posts.add(post["url"])
                            reply_count += 1
                            print(f"[Success] Reply #{reply_count} posted!")
                        else:
                            print("[Failed] Could not post reply")
                    else:
                        print("[Skip] No new posts found")

                # Random delay between 15-45 minutes
                delay = random.randint(15 * 60, 45 * 60)
                print(f"[Waiting] {delay // 60} minutes until next reply...")

                # Show progress every minute
                for i in range(delay // 60):
                    time.sleep(60)
                    remaining = (delay // 60) - i - 1
                    if remaining > 0 and remaining % 5 == 0:
                        print(f"[Timer] {remaining} minutes remaining...")

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"[Error] {e}")
                time.sleep(60)

    except KeyboardInterrupt:
        print(f"\n\nStopped! Total replies posted: {reply_count}")
    except Exception as e:
        print(f"Connection error: {e}")


if __name__ == "__main__":
    main()
