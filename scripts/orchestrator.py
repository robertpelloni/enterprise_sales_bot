#!/usr/bin/env python3
"""
Marketing Orchestrator - Main orchestrator for all marketing agents
Replaces autonomous_marketing.py with modular architecture
"""

import threading
import time
import argparse
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modular agents
from cdp_utils import CDPSession, get_browser_ws
from reddit_agent import run_reddit_loop
from twitter_agent import run_twitter_loop


class MarketingOrchestrator:
    """Main orchestrator for autonomous marketing"""

    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.cdp = None
        self.running = False
        self.stats = {
            "reddit_replies": 0,
            "twitter_replies": 0,
            "tweets": 0,
        }

    def connect(self):
        """Connect to browser via CDP"""
        self.cdp = CDPSession(self.ws_url)
        if not self.cdp.connect():
            print("Failed to connect to browser")
            return False
        print("Connected to browser via CDP")
        return True

    def start(self, enable_reddit=True, enable_twitter=True):
        """Start all marketing loops"""
        if not self.connect():
            return False

        self.running = True

        # Start loops in separate threads
        threads = []

        if enable_reddit:
            reddit_thread = threading.Thread(
                target=run_reddit_loop,
                args=(self.cdp, self.stats, lambda: self.running),
                daemon=True,
            )
            reddit_thread.start()
            threads.append(reddit_thread)

        if enable_twitter:
            twitter_thread = threading.Thread(
                target=run_twitter_loop,
                args=(self.cdp, self.stats, lambda: self.running),
                daemon=True,
            )
            twitter_thread.start()
            threads.append(twitter_thread)

        print("\n" + "=" * 60)
        print("Marketing Orchestrator Started!")
        print("=" * 60)
        print(f"Reddit: {'Enabled' if enable_reddit else 'Disabled'}")
        print(f"Twitter: {'Enabled' if enable_twitter else 'Disabled'}")
        print("=" * 60)
        print("Press Ctrl+C to stop")
        print("=" * 60)

        # Keep main thread alive and print stats
        try:
            while self.running:
                time.sleep(10)
                self._print_stats()
        except KeyboardInterrupt:
            print("\nStopping...")
            self.running = False

        return True

    def _print_stats(self):
        """Print current statistics"""
        print(
            f"\r[Stats] Reddit: {self.stats['reddit_replies']} | Twitter: {self.stats['twitter_replies']} | Tweets: {self.stats['tweets']}",
            end="",
            flush=True,
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Marketing Orchestrator")
    parser.add_argument("--ws-url", help="WebSocket URL for CDP connection")
    parser.add_argument(
        "--reddit-only", action="store_true", help="Only run Reddit agent"
    )
    parser.add_argument(
        "--twitter-only", action="store_true", help="Only run Twitter agent"
    )

    args = parser.parse_args()

    # Get WebSocket URL
    ws_url = args.ws_url
    if not ws_url:
        print("No --ws-url provided, trying to detect browser...")
        ws_url = get_browser_ws()
        if not ws_url:
            print(
                "ERROR: Could not detect browser. Start Edge with --remote-debugging-port=9222"
            )
            sys.exit(1)
        print(f"Detected browser: {ws_url[:50]}...")

    # Determine which agents to enable
    enable_reddit = not args.twitter_only
    enable_twitter = not args.reddit_only

    # Start orchestrator
    orchestrator = MarketingOrchestrator(ws_url)
    orchestrator.start(enable_reddit=enable_reddit, enable_twitter=enable_twitter)


if __name__ == "__main__":
    main()
