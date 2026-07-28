#!/usr/bin/env python3
"""
Reddit Agent - Autonomous Reddit engagement
Extracted from autonomous_marketing.py
"""
import json
import time
import random

# HyperNexus branding
BRANDING = {
    "product": "HyperNexus",
    "url": "https://hypernexus.site",
    "github": "https://github.com/HyperNexusSoft/HyperNexus",
    "key_features": [
        "Progressive tool routing (60% token reduction)",
        "Three-tier LLM waterfall (zero downtime)",
        "Dual-tier memory (L1 session + L2 permanent)",
        "MCP server management",
        "Multi-agent orchestration",
    ],
}

# Search terms for finding relevant posts
SEARCH_TERMS = [
    "MCP server",
    "AI agent framework",
    "Claude Code",
    "AI tool routing",
    "LLM rate limit",
    "AI memory management",
    "developer AI tools",
    "open source AI",
]

# Subreddits to monitor
SUBREDDITS = [
    "mcp",
    "ClaudeAI",
    "LocalLLaMA",
    "MachineLearning",
    "SaaS",
    "startups",
    "SideProject",
    "webdev",
    "artificial",
    "ChatGPT",
]


def is_opensource_context(title):
    """Determine if post is more open-source focused"""
    title_lower = title.lower()
    oss_keywords = ["open source", "opensource", "free", "self-host", "github", "foss", "community"]
    commercial_keywords = ["enterprise", "business", "company", "team", "production", "saas", "paid"]
    oss_score = sum(1 for kw in oss_keywords if kw in title_lower)
    commercial_score = sum(1 for kw in commercial_keywords if kw in title_lower)
    return oss_score >= commercial_score


def categorize_post(title):
    """Categorize a post by its topic"""
    title_lower = title.lower()
    
    if any(term in title_lower for term in ["mcp", "model context protocol", "tool routing"]):
        return "mcp"
    elif any(term in title_lower for term in ["rate limit", "429", "quota", "api limit"]):
        return "rate_limit"
    elif any(term in title_lower for term in ["memory", "forget", "context", "remember"]):
        return "memory"
    elif any(term in title_lower for term in ["agent", "framework", "orchestration"]):
        return "agent"
    else:
        return "generic"


def generate_reply(post_title, post_content=""):
    """Generate an intelligent reply based on post content"""
    category = categorize_post(post_title)
    is_oss = is_opensource_context(post_title)
    
    url = BRANDING["github"] if is_oss else BRANDING["url"]
    
    replies = {
        "mcp": [
            f"Great question! Progressive tool routing can help here. Instead of loading all 50+ MCP server definitions into context, semantic vector search matches your prompt to the top 3 most relevant tools. This reduces token usage by ~60%. HyperNexus does this automatically. {url}",
            f"This is exactly the problem we solved with HyperNexus. The key insight is that you don't need all tools available all the time. Progressive routing dynamically selects the most relevant tools based on your current task. {url}",
            f"For MCP server management, I recommend checking out HyperNexus. It handles tool routing automatically - you define your tools once, and it intelligently selects which ones to inject based on semantic similarity to your prompt. {url}",
        ],
        "rate_limit": [
            f"The LLM Waterfall Pattern solves this! Set up a cascade: primary API -> secondary API -> local models -> queue. When one provider rate limits you, it automatically fails over to the next. Zero downtime from rate limits. {url}",
            f"I've been using a three-tier waterfall approach: cloud APIs as primary, a secondary provider as backup, and local Ollama models as fallback. No more 2AM rate limit interruptions. {url}",
            f"Rate limits are inevitable with AI APIs. The solution is transparent failover. HyperNexus handles this automatically with its waterfall architecture. {url}",
        ],
        "memory": [
            f"Dual-tier memory architecture is the answer. L1 for session scratchpad (ephemeral, fast), L2 for permanent semantic storage with vector search. Your agent remembers decisions across sessions. {url}",
            f"We solved this with a two-layer memory system: session memory for current work, and permanent memory with semantic search for cross-session knowledge. Game changer for agent reliability. {url}",
            f"Memory management is crucial for AI agents. HyperNexus uses SQLite + sqlite-vec for permanent semantic memory. Your agent can search past decisions by meaning, not just keywords. {url}",
        ],
        "agent": [
            f"For multi-agent workflows, consider a swarm architecture with role rotation: Planner -> Implementer -> Tester -> Critic. Each agent has a specific responsibility, and a consensus engine resolves conflicts. {url}",
            f"The key to reliable AI agents is progressive tool routing and persistent memory. Most frameworks dump everything into context, but selective tool injection and cross-session memory make agents much more capable. {url}",
            f"AI agent frameworks are evolving fast. The best ones now combine MCP tool routing, persistent memory, and multi-model failover. That's what makes HyperNexus different. {url}",
        ],
        "generic": [
            f"Interesting discussion! One thing that's helped me is progressive tool routing - instead of loading all tool definitions, you semantically match the current task to the most relevant tools. Saves tokens and improves accuracy. {url}",
            f"Great point! For anyone dealing with this, consider using a universal control plane that handles tool routing, memory, and failover automatically. It's been a game changer for my workflow. {url}",
            f"This resonates with what we're building at HyperNexus. The key insight is that AI infrastructure should be as well-engineered as the applications it powers. {url}",
        ],
    }
    
    return random.choice(replies.get(category, replies["generic"]))


def search_subreddit(cdp, subreddit, term):
    """Search a subreddit for relevant posts"""
    url = f"https://old.reddit.com/r/{subreddit}/search?q={term}&restrict_sr=on&sort=new&t=week"
    cdp.navigate(url)
    time.sleep(5)

    result = cdp.evaluate("""
        (function() {
            var posts = [];
            var links = document.querySelectorAll('.search-result .search-title a');
            for (var i = 0; i < Math.min(links.length, 10); i++) {
                var link = links[i];
                posts.push({
                    title: link.textContent.trim(),
                    url: link.href,
                    id: link.href.split('/').pop()
                });
            }
            return JSON.stringify(posts);
        })()
    """)

    if result and result.get("result", {}).get("value"):
        try:
            return json.loads(result["result"]["value"])
        except:
            pass
    return []


def post_reply(cdp, post_url, reply_text):
    """Post a reply to a Reddit post"""
    cdp.navigate(post_url)
    time.sleep(5)

    # Find and click reply button
    cdp.evaluate("""
        (function() {
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                if (links[i].textContent.trim() === 'reply') {
                    links[i].click();
                    return 'reply link clicked';
                }
            }
            return 'reply button not found';
        })()
    """)

    time.sleep(2)

    # Find textarea and type reply
    cdp.evaluate("""
        (function() {
            var textarea = document.querySelector('textarea, [contenteditable="true"]');
            if (textarea) {
                textarea.focus();
                return 'textarea focused';
            }
            return 'textarea not found';
        })()
    """)

    time.sleep(1)
    cdp.type_text(reply_text)
    time.sleep(2)

    # Click submit
    result = cdp.evaluate("""
        (function() {
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent.trim().toLowerCase();
                if (text === 'save' || text === 'submit' || text === 'reply') {
                    buttons[i].click();
                    return 'submitted';
                }
            }
            return 'submit button not found';
        })()
    """)

    time.sleep(3)
    return result


def run_reddit_loop(cdp, stats, running):
    """Main Reddit engagement loop"""
    print("Starting Reddit engagement loop...")
    replied_posts = set()

    while running():
        try:
            subreddit = random.choice(SUBREDDITS)
            term = random.choice(SEARCH_TERMS)

            print(f"[Reddit] Searching r/{subreddit} for '{term}'...")
            posts = search_subreddit(cdp, subreddit, term)

            if posts:
                new_posts = [p for p in posts if p["id"] not in replied_posts]

                if new_posts:
                    post = random.choice(new_posts)
                    print(f"[Reddit] Found post: {post['title'][:50]}...")

                    reply = generate_reply(post["title"])
                    print(f"[Reddit] Generated reply: {reply[:50]}...")

                    result = post_reply(cdp, post["url"], reply)

                    if result and "submitted" in str(result).lower():
                        replied_posts.add(post["id"])
                        stats["reddit_replies"] = stats.get("reddit_replies", 0) + 1
                        print(f"[Reddit] Reply posted! Total: {stats['reddit_replies']}")
                    else:
                        print(f"[Reddit] Failed to post reply: {result}")
                else:
                    print("[Reddit] No new posts found")
            else:
                print("[Reddit] No posts found")

            delay = random.randint(15 * 60, 45 * 60)
            print(f"[Reddit] Waiting {delay // 60} minutes...")
            time.sleep(delay)

        except Exception as e:
            print(f"[Reddit] Error: {e}")
            time.sleep(60)
