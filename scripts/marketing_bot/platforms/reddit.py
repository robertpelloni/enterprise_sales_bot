"""
Reddit Platform Module

Handles posting comments and content to Reddit using CDP automation.
Targets smaller, less moderated subreddits to avoid removal.
"""

import json
import random
import time
from typing import List, Optional

import websocket

from .. import config
from ..cdp_utils import (
    create_tab,
    fill_input,
    click_element,
    navigate,
    send_and_recv,
    wait_for_element,
)


class RedditPlatform:
    """Reddit engagement platform using CDP automation."""

    PLATFORM = "reddit"

    def __init__(self, browser_ws: str):
        self.browser_ws = browser_ws
        self.ws: Optional[websocket.WebSocket] = None
        self.replied_urls: set = set()
        self.post_count: int = 0
        self.comment_count: int = 0

    def connect(self) -> bool:
        """Create a new browser tab for Reddit."""
        tab_ws = create_tab(self.browser_ws, "https://old.reddit.com/")
        if tab_ws:
            self.ws = websocket.create_connection(tab_ws, timeout=30)
            # Disable beforeunload dialogs via JS injection (no watcher thread -
            # a separate thread reading the same WebSocket steals responses)
            self._inject_dialog_blocker()
            return True
        return False

    def _inject_dialog_blocker(self):
        """Inject JavaScript to block all beforeunload/alert/confirm/prompt dialogs."""
        if not self.ws:
            return
        try:
            send_and_recv(
                self.ws,
                500,
                "Runtime.evaluate",
                {
                    "expression": """
                    (function() {
                        // Override beforeunload to prevent dialogs
                        window.addEventListener('beforeunload', function(e) {
                            e.preventDefault();
                            delete e.returnValue;
                            return '';
                        }, true);
                        // Override onbeforeunload
                        Object.defineProperty(window, 'onbeforeunload', {
                            set: function() {},
                            get: function() { return null; }
                        });
                        // Override alert/confirm/prompt
                        window.alert = function() {};
                        window.confirm = function() { return true; };
                        window.prompt = function() { return ''; };
                        return 'dialogs blocked';
                    })()
                    """,
                    "returnByValue": True,
                },
            )
        except Exception:
            pass

    def disconnect(self):
        """Close the WebSocket connection."""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

    def _extract_posts(self, subreddit: str) -> List[dict]:
        """Extract posts from a subreddit page."""
        if not self.ws:
            return []

        navigate(self.ws, f"https://old.reddit.com/r/{subreddit}/new/", wait=5)

        # Extract post data using JavaScript
        result = send_and_recv(
            self.ws,
            1,
            "Runtime.evaluate",
            {
                "expression": """
                (function() {
                    var posts = [];
                    var elements = document.querySelectorAll('.thing.link');
                    for (var i = 0; i < Math.min(elements.length, 25); i++) {
                        var el = elements[i];
                        var titleEl = el.querySelector('a.title');
                        var commentsEl = el.querySelector('a.comments');
                        if (titleEl && commentsEl) {
                            posts.push({
                                title: titleEl.textContent.trim(),
                                url: commentsEl.href,
                                comments: parseInt(commentsEl.textContent) || 0,
                                score: parseInt(el.querySelector('.score.unvoted')?.textContent) || 0
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

    def _post_reply(self, post_url: str, reply_text: str) -> bool:
        """Post a reply to a Reddit thread."""
        if not self.ws:
            return False

        navigate(self.ws, post_url, wait=5)

        # Find and fill the comment box
        comment_box = 'textarea[name="text"]'
        if not wait_for_element(self.ws, comment_box, timeout=10):
            # Try alternative selector
            comment_box = "#commentreply textarea"
            if not wait_for_element(self.ws, comment_box, timeout=5):
                return False

        # Fill the comment
        if not fill_input(self.ws, comment_box, reply_text, msg_id=10):
            return False

        time.sleep(1)

        # Submit the comment - use the SPECIFIC save button (not generic submit selector,
        # which can match header buttons like "GET NEW REDDIT")
        submit_btn = ".commentarea button.save"
        if not click_element(self.ws, submit_btn, msg_id=11):
            # Try alternative: generic save button
            if not click_element(self.ws, "button.save", msg_id=12):
                # Last resort: form submit via JS
                if not self._submit_form_via_js():
                    return False

        time.sleep(3)
        return True

    def _submit_form_via_js(self) -> bool:
        """Submit the comment form via JavaScript as last resort."""
        if not self.ws:
            return False
        try:
            result = send_and_recv(
                self.ws,
                13,
                "Runtime.evaluate",
                {
                    "expression": """
                    (function() {
                        var form = document.querySelector('.commentarea form');
                        if (!form) return 'no form';
                        // Trigger the form's onsubmit handler directly
                        var result = form.onsubmit ? form.onsubmit.call(form) : true;
                        if (result === false) return 'onsubmit returned false';
                        // Fallback: submit the form
                        form.submit();
                        return 'submitted';
                    })()
                    """,
                    "returnByValue": True,
                },
            )
            return result == "submitted" or result == "onsubmit returned false"
        except Exception:
            return False

    def engage_with_subreddit(self, subreddit: str) -> Optional[dict]:
        """Find and reply to a relevant post in a subreddit."""
        posts = self._extract_posts(subreddit)
        if not posts:
            return None

        # Filter for suitable posts (allow posts with any comment count)
        candidates = [
            p
            for p in posts
            if p.get("url", "") not in self.replied_urls and p.get("score", 0) >= 1
        ]

        if not candidates:
            return None

        post = random.choice(candidates)

        # Generate reply (no links to avoid removal)
        reply = self._generate_no_link_reply(post["title"])

        # Post reply
        success = self._post_reply(post["url"], reply)

        if success:
            self.replied_urls.add(post["url"])
            self.comment_count += 1
            return {
                "platform": self.PLATFORM,
                "action": "comment",
                "subreddit": subreddit,
                "post_title": post["title"][:80],
                "reply": reply[:100],
                "success": True,
            }

        return None

    def _generate_no_link_reply(self, post_title: str) -> str:
        """Generate a helpful reply without any links."""
        post_lower = post_title.lower()

        # Template replies based on topic (no links)
        templates = {
            "mcp": [
                "Progressive tool routing is key for MCP management - semantic search matches your prompt to the top 3 most relevant tools instead of loading all definitions. Cuts token usage significantly.",
                "The biggest challenge with MCP servers is context bloat. Progressive routing dynamically selects only the tools you need per task. Game changer for efficiency.",
                "MCP servers are powerful but need smart management. Progressive routing, health monitoring, and failover handling make them production-ready.",
            ],
            "rate_limit": [
                "The Waterfall Pattern solves rate limits: Primary API -> Secondary API -> Local models -> Queue. When one provider fails, the next picks up automatically.",
                "Transparent failover is the answer. When one provider rate limits, the next picks up automatically. Your agent shouldn't even notice.",
            ],
            "memory": [
                "Dual-tier memory architecture works well: L1 for session scratchpad (ephemeral, fast), L2 for permanent semantic storage with vector search.",
                "Persistent memory across sessions is crucial. Vector search by meaning, not keywords, makes it actually useful.",
            ],
            "agent": [
                "Progressive tool routing + persistent memory + multi-model failover is the combo that makes AI agents reliable.",
                "The key ingredients for reliable agents: right tools at the right time, memory that persists, and failover when providers go down.",
            ],
            "generic": [
                "Progressive tool routing changes the game - semantically match tasks to the top 3 tools instead of dumping everything in context.",
                "The biggest win for AI dev efficiency is only loading the tools your agent actually needs for each task.",
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

    def post_content(self, subreddit: str, title: str, body: str) -> bool:
        """Create a new post in a subreddit."""
        if not self.ws:
            return False

        navigate(self.ws, f"https://old.reddit.com/r/{subreddit}/submit", wait=5)

        # Fill title
        if not fill_input(self.ws, 'input[name="title"]', title, msg_id=20):
            return False

        # Fill body
        if not fill_input(self.ws, 'textarea[name="text"]', body, msg_id=21):
            return False

        time.sleep(1)

        # Submit
        if not click_element(self.ws, 'button[type="submit"]', msg_id=22):
            return False

        time.sleep(3)
        self.post_count += 1
        return True

    def run_cycle(self) -> Optional[dict]:
        """Run one engagement cycle."""
        subreddit = random.choice(config.REDDIT_SUBREDDITS)
        return self.engage_with_subreddit(subreddit)
