"""
Marketing Bot Orchestrator

Main orchestrator that runs all platform agents in parallel.
"""

import random
import sys
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

from . import config
from .cdp_utils import get_browser_ws
from .content.generator import ContentGenerator
from .platforms.bluesky import BlueskyPlatform
from .platforms.hackernews import HackerNewsPlatform
from .platforms.linkedin import LinkedInPlatform
from .platforms.reddit import RedditPlatform
from .platforms.twitter import TwitterPlatform


class MarketingOrchestrator:
    """Orchestrates all platform agents."""

    def __init__(self, mode: str = "comments"):
        self.mode = mode  # "comments" or "articles"
        self.browser_ws: Optional[str] = None
        self.stop_event = threading.Event()
        self.content_generator = ContentGenerator()
        self.results: List[Dict] = []
        self.results_lock = threading.Lock()

    def log(self, platform: str, message: str):
        """Log a message with timestamp."""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{platform}] {message}"
        sys.stdout.buffer.write(line.encode("utf-8") + b"\n")
        sys.stdout.flush()

    def connect_browser(self) -> bool:
        """Connect to the browser."""
        self.browser_ws = get_browser_ws()
        if not self.browser_ws:
            self.log(
                "System",
                "ERROR: No browser connection. Start Edge with --remote-debugging-port=9222",
            )
            return False
        self.log("System", f"Connected to browser: {self.browser_ws[:50]}...")
        return True

    def record_result(self, result: Optional[Dict]):
        """Thread-safe result recording."""
        if result:
            with self.results_lock:
                self.results.append(result)

    def run_reddit_agent(self):
        """Run Reddit engagement agent."""
        if not self.browser_ws:
            return
        platform = RedditPlatform(self.browser_ws)
        if not platform.connect():
            self.log("Reddit", "Failed to connect")
            return

        self.log("Reddit", "Agent started")
        post_count = 0

        # Warmup - let the page load before first cycle
        time.sleep(5)

        while not self.stop_event.is_set():
            try:
                result = platform.run_cycle()
                if result:
                    self.record_result(result)
                    self.log(
                        "Reddit",
                        f"Comment #{platform.comment_count}: {result.get('post_title', '')[:60]}...",
                    )
                    post_count += 1
                    # Longer wait after a successful post (rate limiting)
                    delay = random.randint(
                        config.DELAY_MIN_SECONDS, config.DELAY_MAX_SECONDS
                    )
                else:
                    # No post found/failed - retry sooner (2-4 min)
                    delay = random.randint(120, 240)

                self.log("Reddit", f"Waiting {delay // 60} minutes...")

                if self.stop_event.wait(timeout=delay):
                    break

            except Exception as e:
                self.log("Reddit", f"Error: {e}")
                if self.stop_event.wait(timeout=60):
                    break

        platform.disconnect()
        self.log("Reddit", f"Agent stopped. Total comments: {post_count}")

    def run_twitter_agent(self):
        """Run Twitter engagement agent."""
        if not self.browser_ws:
            return
        platform = TwitterPlatform(self.browser_ws)
        if not platform.connect():
            self.log("Twitter", "Failed to connect")
            return

        self.log("Twitter", "Agent started")
        reply_count = 0

        # Warmup - let the page load before first cycle
        time.sleep(5)

        while not self.stop_event.is_set():
            try:
                result = platform.run_cycle()
                if result:
                    self.record_result(result)
                    self.log(
                        "Twitter",
                        f"Reply #{platform.reply_count}: {result.get('tweet_text', '')[:60]}...",
                    )
                    reply_count += 1
                    # Longer wait after a successful post (rate limiting)
                    delay = random.randint(
                        config.DELAY_MIN_SECONDS, config.DELAY_MAX_SECONDS
                    )
                else:
                    # No reply found/failed - retry sooner (2-4 min)
                    delay = random.randint(120, 240)

                self.log("Twitter", f"Waiting {delay // 60} minutes...")

                if self.stop_event.wait(timeout=delay):
                    break

            except Exception as e:
                self.log("Twitter", f"Error: {e}")
                if self.stop_event.wait(timeout=60):
                    break

        platform.disconnect()
        self.log("Twitter", f"Agent stopped. Total replies: {reply_count}")

    def run_linkedin_agent(self):
        """Run LinkedIn engagement agent."""
        if not self.browser_ws:
            return
        platform = LinkedInPlatform(self.browser_ws)
        if not platform.connect():
            self.log("LinkedIn", "Failed to connect")
            return

        self.log("LinkedIn", "Agent started")
        comment_count = 0

        # Warmup - let the page load before first cycle
        time.sleep(5)

        while not self.stop_event.is_set():
            try:
                result = platform.run_cycle()
                if result:
                    self.record_result(result)
                    self.log(
                        "LinkedIn",
                        f"Comment #{platform.comment_count}: {result.get('post_text', '')[:60]}...",
                    )
                    comment_count += 1
                    # Longer wait after a successful post (rate limiting)
                    delay = random.randint(
                        config.DELAY_MIN_SECONDS, config.DELAY_MAX_SECONDS
                    )
                else:
                    # No comment found/failed - retry sooner (2-4 min)
                    delay = random.randint(120, 240)

                self.log("LinkedIn", f"Waiting {delay // 60} minutes...")

                if self.stop_event.wait(timeout=delay):
                    break

            except Exception as e:
                self.log("LinkedIn", f"Error: {e}")
                if self.stop_event.wait(timeout=60):
                    break

        platform.disconnect()
        self.log("LinkedIn", f"Agent stopped. Total comments: {comment_count}")

    def run_bluesky_agent(self):
        """Run Bluesky posting agent."""
        platform = BlueskyPlatform()
        self.log("Bluesky", "Agent started")
        post_count = 0

        while not self.stop_event.is_set():
            try:
                # Generate content
                content = self.content_generator.get_reply(
                    "AI developer tools and MCP server management",
                    platform="bluesky",
                    max_chars=config.MAX_REPLY_LENGTH["bluesky"],
                )

                if content:
                    result = platform.run_cycle(content)
                    if result:
                        self.record_result(result)
                        self.log(
                            "Bluesky", f"Post #{post_count + 1}: {content[:60]}..."
                        )
                        post_count += 1

                # Rate limiting (longer for Bluesky)
                delay = random.randint(3600, 7200)  # 1-2 hours
                self.log("Bluesky", f"Waiting {delay // 60} minutes...")

                if self.stop_event.wait(timeout=delay):
                    break

            except Exception as e:
                self.log("Bluesky", f"Error: {e}")
                if self.stop_event.wait(timeout=60):
                    break

        self.log("Bluesky", f"Agent stopped. Total posts: {post_count}")

    def run_hackernews_agent(self):
        """Run Hacker News engagement agent."""
        if not self.browser_ws:
            return
        platform = HackerNewsPlatform(self.browser_ws)
        if not platform.connect():
            self.log("HackerNews", "Failed to connect")
            return

        self.log("HackerNews", "Agent started")
        comment_count = 0

        # Warmup - let the page load before first cycle
        time.sleep(5)

        while not self.stop_event.is_set():
            try:
                result = platform.run_cycle()
                if result:
                    self.record_result(result)
                    self.log(
                        "HackerNews",
                        f"Comment #{platform.comment_count}: {result.get('post_title', '')[:60]}...",
                    )
                    comment_count += 1
                    # Longer wait after a successful post (rate limiting)
                    delay = random.randint(
                        config.DELAY_MIN_SECONDS, config.DELAY_MAX_SECONDS
                    )
                else:
                    # No comment found/failed - retry sooner (2-4 min)
                    delay = random.randint(120, 240)

                self.log("HackerNews", f"Waiting {delay // 60} minutes...")

                if self.stop_event.wait(timeout=delay):
                    break

            except Exception as e:
                self.log("HackerNews", f"Error: {e}")
                if self.stop_event.wait(timeout=60):
                    break

        platform.disconnect()
        self.log("HackerNews", f"Agent stopped. Total comments: {comment_count}")

    def run_all(self):
        """Run all platform agents in parallel."""
        if not self.connect_browser():
            return

        self.log("System", "=" * 60)
        self.log("System", "  HyperNexus Marketing Bot v2.0")
        self.log("System", "=" * 60)
        self.log("System", f"  Mode: {self.mode}")
        self.log("System", "  Platforms: Reddit, Twitter, LinkedIn, Bluesky, HN")
        self.log("System", "  Press Ctrl+C to stop all agents")
        self.log("System", "=" * 60)

        # Create threads for each platform
        threads = []

        if self.mode == "comments":
            # Comment/engagement mode - check enabled flags
            agents = []
            if getattr(config, "REDDIT_ENABLED", True):
                agents.append(("Reddit", self.run_reddit_agent))
            if getattr(config, "TWITTER_ENABLED", True):
                agents.append(("Twitter", self.run_twitter_agent))
            if getattr(config, "LINKEDIN_ENABLED", True):
                agents.append(("LinkedIn", self.run_linkedin_agent))
            if getattr(config, "BLUESKY_ENABLED", True):
                agents.append(("Bluesky", self.run_bluesky_agent))
            if getattr(config, "HACKERNEWS_ENABLED", True):
                agents.append(("HackerNews", self.run_hackernews_agent))
        else:
            # Article mode (future)
            agents = [
                ("Bluesky", self.run_bluesky_agent),
            ]

        for name, target in agents:
            t = threading.Thread(target=target, name=name, daemon=True)
            threads.append(t)
            t.start()
            time.sleep(3)  # Stagger starts

        # Main loop
        try:
            while True:
                time.sleep(10)
                # Print summary every 5 minutes
                if len(self.results) > 0 and len(self.results) % 5 == 0:
                    self._print_summary()
        except KeyboardInterrupt:
            self.log("System", "\nStopping all agents...")
            self.stop_event.set()

            for t in threads:
                t.join(timeout=30)

            self.log("System", "All agents stopped.")
            self._print_summary()

    def _print_summary(self):
        """Print results summary."""
        if not self.results:
            return

        self.log("System", "\n" + "=" * 60)
        self.log("System", "RESULTS SUMMARY")
        self.log("System", "=" * 60)

        # Count by platform
        platform_counts: Dict[str, int] = {}
        for r in self.results:
            p = r.get("platform", "unknown")
            platform_counts[p] = platform_counts.get(p, 0) + 1

        for platform, count in platform_counts.items():
            self.log("System", f"  {platform}: {count} actions")

        self.log("System", f"  Total: {len(self.results)} actions")
        self.log("System", "=" * 60 + "\n")
