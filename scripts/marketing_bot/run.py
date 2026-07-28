#!/usr/bin/env python3
"""
Marketing Bot CLI Entry Point

Usage:
    python run.py                     # Run all platforms in comment mode
    python run.py --mode comments     # Run all platforms in comment mode
    python run.py --mode articles     # Run all platforms in article mode
    python run.py --platform reddit   # Run only Reddit
    python run.py --platform twitter  # Run only Twitter
    python run.py --platform linkedin # Run only LinkedIn
"""

import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from marketing_bot.orchestrator import MarketingOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="HyperNexus Marketing Bot - Multi-platform social media engagement"
    )
    parser.add_argument(
        "--mode",
        choices=["comments", "articles"],
        default="comments",
        help="Operation mode: comments (engage with discussions) or articles (cross-post content)",
    )
    parser.add_argument(
        "--platform",
        choices=["reddit", "twitter", "linkedin", "bluesky", "hackernews", "all"],
        default="all",
        help="Run specific platform or all",
    )

    args = parser.parse_args()

    orchestrator = MarketingOrchestrator(mode=args.mode)

    if not orchestrator.connect_browser():
        print("ERROR: Could not connect to browser.")
        print("Make sure Edge is running with --remote-debugging-port=9222")
        sys.exit(1)

    print("=" * 60)
    print("  HyperNexus Marketing Bot v2.0")
    print("=" * 60)
    print(f"  Mode: {args.mode}")
    print(f"  Platform: {args.platform}")
    print("=" * 60)

    if args.platform == "all":
        orchestrator.run_all()
    elif args.platform == "reddit":
        orchestrator.run_reddit_agent()
    elif args.platform == "twitter":
        orchestrator.run_twitter_agent()
    elif args.platform == "linkedin":
        orchestrator.run_linkedin_agent()
    elif args.platform == "bluesky":
        orchestrator.run_bluesky_agent()
    elif args.platform == "hackernews":
        orchestrator.run_hackernews_agent()


if __name__ == "__main__":
    main()
