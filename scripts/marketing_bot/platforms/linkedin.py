"""
LinkedIn Platform Module

Handles posting content and comments to LinkedIn using CDP automation.
Posts as the HyperNexus company page.
"""

import json
import random
import time
from typing import List, Optional

import websocket

from .. import config
from ..cdp_utils import (
    create_tab,
    click_element,
    navigate,
    send_and_recv,
    type_text,
    wait_for_element,
)
from ..llm import generate_reply, get_url_for_context


class LinkedInPlatform:
    """LinkedIn engagement platform using CDP automation."""

    PLATFORM = "linkedin"

    def __init__(self, browser_ws: str):
        self.browser_ws = browser_ws
        self.ws: Optional[websocket.WebSocket] = None
        self.commented_urls: set = set()
        self.post_count: int = 0
        self.comment_count: int = 0

    def connect(self) -> bool:
        """Create a new browser tab for LinkedIn."""
        tab_ws = create_tab(self.browser_ws, config.LINKEDIN_COMPANY_URL)
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

    def _search_feed(self, query: str) -> List[dict]:
        """Search LinkedIn feed for relevant posts."""
        if not self.ws:
            return []

        search_url = (
            f"https://www.linkedin.com/search/results/content/?keywords={query}"
        )
        navigate(self.ws, search_url, wait=6)

        # Extract post data
        result = send_and_recv(
            self.ws,
            1,
            "Runtime.evaluate",
            {
                "expression": """
                (function() {
                    var posts = [];
                    var cards = document.querySelectorAll('.feed-shared-update-v2, .occludable-update');
                    for (var i = 0; i < Math.min(cards.length, 10); i++) {
                        var el = cards[i];
                        var textEl = el.querySelector('.feed-shared-update-v2__description, .update-components-text');
                        var linkEl = el.querySelector('a[href*="/posts/"], a[href*="/activity/"]');
                        if (textEl) {
                            posts.push({
                                text: textEl.textContent.trim().substring(0, 500),
                                url: linkEl ? linkEl.href : '',
                                author: el.querySelector('.feed-shared-actor__name, .update-components-actor__name')?.textContent?.trim() || 'unknown'
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

    def _post_comment(self, post_url: str, comment_text: str) -> bool:
        """Post a comment on a LinkedIn post."""
        if not self.ws:
            return False

        navigate(self.ws, post_url, wait=5)

        # Find comment box
        comment_box = '.comments-comment-texteditor, [contenteditable="true"]'
        if not wait_for_element(self.ws, comment_box, timeout=10):
            return False

        # Click to focus
        click_element(self.ws, comment_box, msg_id=10)
        time.sleep(1)

        # Type comment
        if not type_text(self.ws, comment_text, msg_id=11):
            return False

        time.sleep(1)

        # Submit
        if not click_element(
            self.ws,
            '.comments-comment-box__submit-button, button[type="submit"]',
            msg_id=12,
        ):
            return False

        time.sleep(3)
        return True

    def _publish_post(self, content: str) -> bool:
        """Publish a post as the company page."""
        if not self.ws:
            return False

        navigate(self.ws, config.LINKEDIN_COMPANY_URL, wait=5)

        # Find "Start a post" button
        if not click_element(
            self.ws,
            'button.share-box-feed-entry__trigger, [data-test-id="main-feed-tab-highlight__share-actions"]',
            msg_id=20,
        ):
            return False

        time.sleep(2)

        # Type content
        editor = '.ql-editor, [contenteditable="true"]'
        if not wait_for_element(self.ws, editor, timeout=10):
            return False

        if not type_text(self.ws, content, msg_id=21):
            return False

        time.sleep(1)

        # Submit
        if not click_element(
            self.ws,
            'button.share-actions__primary-action, button[data-test-id="share-actions__primary-action"]',
            msg_id=22,
        ):
            return False

        time.sleep(3)
        self.post_count += 1
        return True

    def engage_with_search(self, query: str) -> Optional[dict]:
        """Find and comment on a relevant post."""
        posts = self._search_feed(query)
        if not posts:
            return None

        # Filter for suitable posts
        candidates = [
            p
            for p in posts
            if len(p.get("text", "")) > 50
            and p.get("url", "") not in self.commented_urls
            and p.get("url", "") != ""
        ]

        if not candidates:
            return None

        post = random.choice(candidates)

        # Generate comment
        comment = generate_reply(
            post["text"],
            platform="linkedin",
            max_chars=config.MAX_REPLY_LENGTH["linkedin"],
        )

        if not comment:
            url = get_url_for_context(post["text"])
            comment = f"Progressive tool routing changes the game for AI dev efficiency. {url}"

        # Post comment
        success = self._post_comment(post["url"], comment)

        if success:
            self.commented_urls.add(post["url"])
            self.comment_count += 1
            return {
                "platform": self.PLATFORM,
                "action": "comment",
                "query": query,
                "post_text": post["text"][:80],
                "comment": comment[:100],
                "success": True,
            }

        return None

    def publish_article(self, content: str) -> bool:
        """Publish an article post."""
        return self._publish_post(content)

    def run_cycle(self) -> Optional[dict]:
        """Run one engagement cycle."""
        query = random.choice(config.LINKEDIN_SEARCH_TERMS)
        return self.engage_with_search(query)
