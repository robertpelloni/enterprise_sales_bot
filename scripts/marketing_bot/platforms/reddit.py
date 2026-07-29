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
from ..llm import generate_reply, get_url_for_context


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
            # Disable beforeunload dialogs
            self._disable_beforeunload()
            return True
        return False

    def _disable_beforeunload(self):
        """Disable beforeunload event to prevent 'Leave site?' dialogs."""
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
                        window.addEventListener('beforeunload', function(e) {
                            e.preventDefault();
                            delete e.returnValue;
                        }, true);
                        window.onbeforeunload = null;
                        return 'disabled';
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

        # Submit the comment
        submit_btn = 'button[type="submit"], input[type="submit"]'
        if not click_element(self.ws, submit_btn, msg_id=11):
            # Try alternative: save button
            if not click_element(self.ws, ".save-button", msg_id=12):
                return False

        time.sleep(3)
        return True

    def engage_with_subreddit(self, subreddit: str) -> Optional[dict]:
        """Find and reply to a relevant post in a subreddit."""
        posts = self._extract_posts(subreddit)
        if not posts:
            return None

        # Filter for suitable posts (active but not too crowded)
        candidates = [
            p
            for p in posts
            if 2 <= p.get("comments", 0) <= 50
            and p.get("url", "") not in self.replied_urls
            and p.get("score", 0) >= 1
        ]

        if not candidates:
            return None

        post = random.choice(candidates)

        # Generate reply
        reply = generate_reply(
            post["title"],
            platform="reddit",
            max_chars=config.MAX_REPLY_LENGTH["reddit"],
        )

        if not reply:
            # Fallback to template
            url = get_url_for_context(post["title"])
            reply = f"Progressive tool routing changes the game for AI dev efficiency. {url}"

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
