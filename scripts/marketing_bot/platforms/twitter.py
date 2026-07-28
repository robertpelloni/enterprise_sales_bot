"""
Twitter/X Platform Module

Handles posting replies to Twitter/X using CDP automation.
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


class TwitterPlatform:
    """Twitter/X engagement platform using CDP automation."""

    PLATFORM = "twitter"

    def __init__(self, browser_ws: str):
        self.browser_ws = browser_ws
        self.ws: Optional[websocket.WebSocket] = None
        self.replied_urls: set = set()
        self.reply_count: int = 0

    def connect(self) -> bool:
        """Create a new browser tab for Twitter."""
        tab_ws = create_tab(self.browser_ws, "https://x.com/explore")
        if tab_ws:
            self.ws = websocket.create_connection(tab_ws, timeout=30)
            return True
        return False

    def disconnect(self):
        """Close the WebSocket connection."""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

    def _search_tweets(self, query: str) -> List[dict]:
        """Search for tweets matching a query."""
        if not self.ws:
            return []

        search_url = f"https://x.com/search?q={query}&src=typed_query&f=live"
        navigate(self.ws, search_url, wait=6)

        # Extract tweet data
        result = send_and_recv(
            self.ws,
            1,
            "Runtime.evaluate",
            {
                "expression": """
                (function() {
                    var tweets = [];
                    var articles = document.querySelectorAll('article[data-testid="tweet"]');
                    for (var i = 0; i < Math.min(articles.length, 15); i++) {
                        var el = articles[i];
                        var textEl = el.querySelector('[data-testid="tweetText"]');
                        var linkEl = el.querySelector('a[href*="/status/"]');
                        if (textEl && linkEl) {
                            tweets.push({
                                text: textEl.textContent.trim().substring(0, 300),
                                url: linkEl.href,
                                author: el.querySelector('[data-testid="User-Name"]')?.textContent?.trim() || 'unknown'
                            });
                        }
                    }
                    return JSON.stringify(tweets);
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

    def _post_reply(self, tweet_url: str, reply_text: str) -> bool:
        """Post a reply to a tweet."""
        if not self.ws:
            return False

        navigate(self.ws, tweet_url, wait=5)

        # Find reply box
        reply_box = '[data-testid="tweetTextarea_0"]'
        if not wait_for_element(self.ws, reply_box, timeout=10):
            return False

        # Click to focus
        click_element(self.ws, reply_box, msg_id=10)
        time.sleep(1)

        # Type reply
        if not type_text(self.ws, reply_text, msg_id=11):
            return False

        time.sleep(1)

        # Submit reply
        if not click_element(self.ws, '[data-testid="tweetButton"]', msg_id=12):
            return False

        time.sleep(3)
        return True

    def engage_with_search(self, query: str) -> Optional[dict]:
        """Find and reply to a relevant tweet."""
        tweets = self._search_tweets(query)
        if not tweets:
            return None

        # Filter for suitable tweets
        candidates = [
            t
            for t in tweets
            if len(t.get("text", "")) > 30
            and t.get("url", "") not in self.replied_urls
        ]

        if not candidates:
            return None

        tweet = random.choice(candidates)

        # Generate reply
        reply = generate_reply(
            tweet["text"],
            platform="twitter",
            max_chars=config.MAX_REPLY_LENGTH["twitter"],
        )

        if not reply:
            url = get_url_for_context(tweet["text"])
            reply = f"Progressive tool routing + persistent memory = reliable AI agents. {url}"

        # Post reply
        success = self._post_reply(tweet["url"], reply)

        if success:
            self.replied_urls.add(tweet["url"])
            self.reply_count += 1
            return {
                "platform": self.PLATFORM,
                "action": "reply",
                "query": query,
                "tweet_text": tweet["text"][:80],
                "reply": reply[:100],
                "success": True,
            }

        return None

    def post_tweet(self, text: str) -> bool:
        """Post a new tweet."""
        if not self.ws:
            return False

        navigate(self.ws, "https://x.com/compose/post", wait=5)

        # Focus textarea
        click_element(self.ws, '[data-testid="tweetTextarea_0"]', msg_id=20)
        time.sleep(1)

        # Type tweet
        if not type_text(self.ws, text[:280], msg_id=21):
            return False

        time.sleep(1)

        # Submit
        if not click_element(self.ws, '[data-testid="tweetButton"]', msg_id=22):
            return False

        time.sleep(3)
        return True

    def run_cycle(self) -> Optional[dict]:
        """Run one engagement cycle."""
        query = random.choice(config.TWITTER_SEARCH_TERMS)
        return self.engage_with_search(query)
