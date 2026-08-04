"""
Marketing Bot Orchestrator

Main orchestrator that runs all platform agents in parallel.
Handles connection drops and auto-reconnection.
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
    """Orchestrates all platform agents with auto-reconnection."""

    def __init__(self, mode: str = "comments"):
        self.mode = mode
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

    def _run_platform_loop(self, platform, platform_name: str, connect_func):
        """Generic platform loop with auto-reconnection."""
        if not connect_func():
            self.log(platform_name, "Failed to connect")
            return

        self.log(platform_name, "Agent started")
        action_count = 0
        consecutive_failures = 0

        # Warmup
        time.sleep(5)

        while not self.stop_event.is_set():
            try:
                result = platform.run_cycle()
                consecutive_failures = 0  # Reset on success

                if result:
                    self.record_result(result)
                    comment = (
                        result.get("post_title")
                        or result.get("tweet_text")
                        or result.get("post_text")
                        or ""
                    )
                    self.log(
                        platform_name, f"Action #{action_count + 1}: {comment[:60]}..."
                    )
                    action_count += 1
                    delay = random.randint(
                        config.DELAY_MIN_SECONDS, config.DELAY_MAX_SECONDS
                    )
                else:
                    delay = random.randint(120, 240)

                self.log(platform_name, f"Waiting {delay // 60} minutes...")

                if self.stop_event.wait(timeout=delay):
                    break

            except Exception as e:
                consecutive_failures += 1
                self.log(platform_name, f"Error ({consecutive_failures}): {e}")

                # Try to reconnect with fresh browser connection
                if consecutive_failures <= 5:
                    self.log(
                        platform_name,
                        f"Reconnecting (attempt {consecutive_failures})...",
                    )
                    try:
                        # Re-discover browser WebSocket URL
                        new_ws = get_browser_ws()
                        if new_ws:
                            platform.browser_ws = new_ws

                        if platform.reconnect():
                            self.log(platform_name, "Reconnected successfully!")
                            time.sleep(5)  # Let page load
                            continue
                        else:
                            self.log(platform_name, "Reconnect failed")
                    except Exception as re:
                        self.log(platform_name, f"Reconnect error: {re}")

                # Back off on repeated failures
                backoff = min(60 * consecutive_failures, 300)
                self.log(platform_name, f"Waiting {backoff}s before retry...")
                if self.stop_event.wait(timeout=backoff):
                    break

        platform.disconnect()
        self.log(platform_name, f"Agent stopped. Total actions: {action_count}")

    def run_reddit_agent(self):
        """Run Reddit engagement agent."""
        if not self.browser_ws:
            return
        platform = RedditPlatform(self.browser_ws)
        self._run_platform_loop(platform, "Reddit", platform.connect)

    def run_twitter_agent(self):
        """Run Twitter engagement agent."""
        if not self.browser_ws:
            return
        platform = TwitterPlatform(self.browser_ws)
        self._run_platform_loop(platform, "Twitter", platform.connect)

    def run_linkedin_agent(self):
        """Run LinkedIn engagement agent."""
        if not self.browser_ws:
            return
        platform = LinkedInPlatform(self.browser_ws)
        self._run_platform_loop(platform, "LinkedIn", platform.connect)

    def run_hackernews_agent(self):
        """Run Hacker News engagement agent."""
        if not self.browser_ws:
            return
        platform = HackerNewsPlatform(self.browser_ws)
        self._run_platform_loop(platform, "HackerNews", platform.connect)

    def run_bluesky_agent(self):
        """Run Bluesky posting agent."""
        platform = BlueskyPlatform()
        self.log("Bluesky", "Agent started")
        post_count = 0

        while not self.stop_event.is_set():
            try:
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

                delay = random.randint(3600, 7200)
                self.log("Bluesky", f"Waiting {delay // 60} minutes...")

                if self.stop_event.wait(timeout=delay):
                    break

            except Exception as e:
                self.log("Bluesky", f"Error: {e}")
                if self.stop_event.wait(timeout=60):
                    break

        self.log("Bluesky", f"Agent stopped. Total posts: {post_count}")

    def run_all(self):
        """Run all platform agents in parallel."""
        if not self.connect_browser():
            return

        self.log("System", "=" * 60)
        self.log("System", "  HyperNexus Marketing Bot v2.0")
        self.log("System", "=" * 60)
        self.log("System", f"  Mode: {self.mode}")
        self.log("System", "  Platforms: Reddit, Twitter, LinkedIn, Bluesky, HN")
        self.log("System", "  Auto-reconnect: enabled")
        self.log("System", "  Press Ctrl+C to stop all agents")
        self.log("System", "=" * 60)

        threads = []

        if self.mode == "comments":
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
            agents = [("Bluesky", self.run_bluesky_agent)]

        for name, target in agents:
            t = threading.Thread(target=target, name=name, daemon=True)
            threads.append(t)
            t.start()
            time.sleep(3)

        try:
            while True:
                time.sleep(10)
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
        platform_counts: Dict[str, int] = {}
        for r in self.results:
            p = r.get("platform", "unknown")
            platform_counts[p] = platform_counts.get(p, 0) + 1
        for platform, count in platform_counts.items():
            self.log("System", f"  {platform}: {count} actions")
        self.log("System", f"  Total: {len(self.results)} actions")
        self.log("System", "=" * 60 + "\n")
