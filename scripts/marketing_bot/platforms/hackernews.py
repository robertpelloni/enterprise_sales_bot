"""
Hacker News Platform Module

Handles posting "Show HN" submissions and comments using CDP automation.
"""

import json
import random
import time
from typing import List, Optional

import websocket

from ..cdp_utils import (
    create_tab,
    fill_input,
    click_element,
    navigate,
    send_and_recv,
    wait_for_element,
)


class HackerNewsPlatform:
    """Hacker News engagement platform using CDP automation."""

    PLATFORM = "hackernews"

    def __init__(self, browser_ws: str):
        self.browser_ws = browser_ws
        self.ws: Optional[websocket.WebSocket] = None
        self.replied_urls: set = set()
        self.post_count: int = 0
        self.comment_count: int = 0

    def connect(self) -> bool:
        """Create a new browser tab for Hacker News."""
        tab_ws = create_tab(self.browser_ws, "https://news.ycombinator.com/")
        if tab_ws:
            self.ws = websocket.create_connection(tab_ws, timeout=30)
            self._inject_dialog_blocker()
            return True
        return False

    def _inject_dialog_blocker(self):
        """Inject JS to block beforeunload/alert/confirm/prompt on ALL page loads."""
        if not self.ws:
            return
        try:
            send_and_recv(
                self.ws,
                500,
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                    (function() {
                        window.addEventListener('beforeunload', function(e) {
                            e.preventDefault();
                            delete e.returnValue;
                            return '';
                        }, true);
                        Object.defineProperty(window, 'onbeforeunload', {
                            set: function() {},
                            get: function() { return null; }
                        });
                        window.alert = function() {};
                        window.confirm = function() { return true; };
                        window.prompt = function() { return ''; };
                        return 'dialogs blocked';
                    })()
                    """,
                },
            )
        except Exception:
            pass

    def reconnect(self) -> bool:
        """Reconnect to a fresh browser tab."""
        self.disconnect()
        return self.connect()

    def is_alive(self) -> bool:
        """Check if the WebSocket connection is still alive."""
        if not self.ws:
            return False
        try:
            self.ws.ping()
            return True
        except Exception:
            return False

    def disconnect(self):
        """Close the WebSocket connection."""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

    def _extract_posts(self) -> List[dict]:
        """Extract posts from Hacker News front page."""
        if not self.ws:
            return []

        result = send_and_recv(
            self.ws,
            1,
            "Runtime.evaluate",
            {
                "expression": """
                (function() {
                    var posts = [];
                    var rows = document.querySelectorAll('.athing');
                    for (var i = 0; i < Math.min(rows.length, 15); i++) {
                        var el = rows[i];
                        var titleEl = el.querySelector('.titleline > a');
                        var linkEl = el.querySelector('.titleline > a[href]');
                        var subtext = el.nextElementSibling;
                        var commentsEl = subtext ? subtext.querySelector('a[href*="item?id="]') : null;
                        if (titleEl) {
                            posts.push({
                                title: titleEl.textContent.trim(),
                                url: linkEl ? linkEl.href : '',
                                comments: commentsEl ? parseInt(commentsEl.textContent) || 0 : 0,
                                id: el.id
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
            except json.JSONDecodeError:
                pass
        return []

    def _is_relevant_post(self, title: str) -> bool:
        """Check if a post is relevant to HyperNexus/TormentNexus features."""
        title_lower = title.lower()

        # Keywords that indicate relevance to our product
        relevant_keywords = [
            "mcp",
            "model context protocol",
            "tool routing",
            "tool schema",
            "claude code",
            "cursor",
            "copilot",
            "gemini cli",
            "ai agent",
            "llm",
            "rate limit",
            "429",
            "context window",
            "token",
            "memory",
            "persistent",
            "vector",
            "sqlite",
            "embedding",
            "failover",
            "waterfall",
            "cascade",
            "ollama",
            "local llm",
            "developer tools",
            "productivity",
            "automation",
            "workflow",
            "ai infrastructure",
            "agent framework",
            "multi-agent",
            "self-hosted",
            "open source",
            "go",
            "golang",
            "typescript",
        ]

        for keyword in relevant_keywords:
            if keyword in title_lower:
                return True

        return False

    def _post_comment(self, item_id: str, comment_text: str) -> bool:
        """Post a comment on a Hacker News item."""
        if not self.ws:
            return False

        navigate(self.ws, f"https://news.ycombinator.com/item?id={item_id}", wait=5)

        # Find comment box
        comment_box = 'textarea[name="text"]'
        if not wait_for_element(self.ws, comment_box, timeout=10):
            return False

        # Fill comment
        if not fill_input(self.ws, comment_box, comment_text, msg_id=10):
            return False

        time.sleep(1)

        # Submit
        if not click_element(self.ws, 'input[type="submit"]', msg_id=11):
            return False

        time.sleep(3)
        return True

    def _submit_post(self, title: str, url: str = "", text: str = "") -> bool:
        """Submit a new post to Hacker News."""
        if not self.ws:
            return False

        navigate(self.ws, "https://news.ycombinator.com/submit", wait=5)

        # Fill title
        if not fill_input(self.ws, 'input[name="title"]', title, msg_id=20):
            return False

        # Fill URL or text
        if url:
            if not fill_input(self.ws, 'input[name="url"]', url, msg_id=21):
                return False
        elif text:
            if not fill_input(self.ws, 'textarea[name="text"]', text, msg_id=22):
                return False

        time.sleep(1)

        # Submit
        if not click_element(self.ws, 'input[type="submit"]', msg_id=23):
            return False

        time.sleep(3)
        self.post_count += 1
        return True

    def engage_with_post(self, post: dict) -> Optional[dict]:
        """Comment on a Hacker News post (no links, just discussion)."""
        if post.get("url", "") in self.replied_urls:
            return None

        # Generate comment without links
        comment = self._generate_no_link_comment(post["title"])

        # Post comment
        success = self._post_comment(post["id"], comment)

        if success:
            self.replied_urls.add(post["url"])
            self.comment_count += 1
            return {
                "platform": self.PLATFORM,
                "action": "comment",
                "post_title": post["title"][:80],
                "comment": comment[:100],
                "success": True,
            }

        return None

    def _generate_no_link_comment(self, post_title: str) -> str:
        """Generate a helpful comment without any links."""
        post_lower = post_title.lower()

        # Template comments based on topic (no links)
        templates = {
            "mcp": [
                "Progressive tool routing is the key insight here - semantic search matches prompts to only the most relevant tools instead of loading everything into context. Cuts token usage dramatically.",
                "The MCP ecosystem benefits a lot from progressive routing. Only loading the tools you need per task keeps context windows manageable.",
                "Interesting. I've found that managing MCP servers gets much easier with health monitoring and automatic failover built in.",
            ],
            "rate_limit": [
                "The waterfall pattern is underrated for rate limits: Primary -> Secondary -> Local models -> Queue. When one provider fails, the next picks up automatically.",
                "Transparent failover between providers solves the rate limit problem well. Your agents shouldn't even notice when one API is down.",
            ],
            "memory": [
                "Dual-tier memory is the way to go: L1 for session scratchpad (fast, ephemeral), L2 for permanent semantic storage with vector search.",
                "Persistent memory across sessions changes everything. Vector search by meaning rather than keywords makes it genuinely useful.",
            ],
            "agent": [
                "The combo that makes agents reliable: progressive tool routing, persistent memory, and multi-model failover.",
                "Agents become production-ready when you solve tool selection, memory persistence, and provider failover together.",
            ],
            "generic": [
                "This is an interesting problem. A similar approach that worked for us was to only load the tools the agent actually needs for each task.",
                "The biggest win for AI dev efficiency is cutting down what gets loaded into context. Semantically matching tasks to the top tools helps a lot.",
            ],
        }

        # Select category
        if "mcp" in post_lower or "tool" in post_lower:
            category = "mcp"
        elif "rate limit" in post_lower or "429" in post_lower:
            category = "rate_limit"
        elif "memory" in post_lower or "remember" in post_lower:
            category = "memory"
        elif "agent" in post_lower:
            category = "agent"
        else:
            category = "generic"

        return random.choice(templates[category])

    def submit_show_hn(self, title: str, url: str) -> bool:
        """Submit a 'Show HN' post."""
        return self._submit_post(f"Show HN: {title}", url=url)

    def run_cycle(self) -> Optional[dict]:
        """Run one engagement cycle."""
        posts = self._extract_posts()
        if not posts:
            return None

        # Filter for suitable posts AND relevance to our product
        candidates = [
            p
            for p in posts
            if 2 <= p.get("comments", 0) <= 100
            and p.get("url", "") not in self.replied_urls
            and self._is_relevant_post(p.get("title", ""))
        ]

        if not candidates:
            return None

        post = random.choice(candidates)
        return self.engage_with_post(post)
