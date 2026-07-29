"""
Hacker News Platform Module

Handles posting "Show HN" submissions and comments using CDP automation.
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
    disable_beforeunload,
)
from ..llm import generate_reply, get_url_for_context


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
            # Disable beforeunload dialogs
            self._disable_beforeunload()
            return True
        return False

    def _disable_beforeunload(self):
        """Disable beforeunload event to prevent 'Leave site?' dialogs."""
        if self.ws:
            disable_beforeunload(self.ws)

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
        """Comment on a Hacker News post."""
        if post.get("url", "") in self.replied_urls:
            return None

        # Generate comment
        comment = generate_reply(
            post["title"],
            platform="hackernews",
            max_chars=config.MAX_REPLY_LENGTH["hackernews"],
        )

        if not comment:
            url = get_url_for_context(post["title"])
            comment = f"Progressive tool routing changes the game for AI dev efficiency. {url}"

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

    def submit_show_hn(self, title: str, url: str) -> bool:
        """Submit a 'Show HN' post."""
        return self._submit_post(f"Show HN: {title}", url=url)

    def run_cycle(self) -> Optional[dict]:
        """Run one engagement cycle."""
        posts = self._extract_posts()
        if not posts:
            return None

        # Filter for suitable posts
        candidates = [
            p
            for p in posts
            if 2 <= p.get("comments", 0) <= 100
            and p.get("url", "") not in self.replied_urls
        ]

        if not candidates:
            return None

        post = random.choice(candidates)
        return self.engage_with_post(post)
