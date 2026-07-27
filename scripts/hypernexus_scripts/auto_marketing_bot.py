"""
HyperNexus Autonomous Marketing Bot
Runs Reddit + Twitter reply agents in parallel with random delays
"""

import websocket
import json
import time
import random
import threading
import urllib.request
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_reddit_v2 import (
    extract_posts,
    categorize_post,
    REPLY_TEMPLATES as REDDIT_TEMPLATES,
    post_reply as reddit_post_reply,
)
from auto_twitter_v2 import (
    search_twitter,
    categorize_tweet,
    REPLY_TEMPLATES as TWITTER_TEMPLATES,
    post_reply as twitter_post_reply,
)


def get_cdp_url():
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        for tab in tabs:
            if "edge://newtab" in tab.get("url", ""):
                return tab.get("webSocketDebuggerUrl")
        if tabs:
            return tabs[0].get("webSocketDebuggerUrl")
    except Exception:
        pass
    return None


def log(prefix, msg):
    ts = time.strftime("%H:%M:%S")
    sys.stdout.buffer.write(f"[{ts}] [{prefix}] {msg}\n".encode("utf-8"))
    sys.stdout.flush()


def reddit_agent(ws_url, stop_event):
    """Reddit reply agent thread"""
    try:
        ws = websocket.create_connection(ws_url, timeout=15)
    except Exception as e:
        log("Reddit", f"Connection failed: {e}")
        return

    subreddits = [
        "mcp",
        "ClaudeAI",
        "LocalLLaMA",
        "MachineLearning",
        "SaaS",
        "startups",
        "SideProject",
        "webdev",
    ]
    replied_urls = set()
    count = 0

    log("Reddit", "Agent started")

    while not stop_event.is_set():
        try:
            subreddit = random.choice(subreddits)
            log("Reddit", f"Scanning r/{subreddit}...")

            posts = extract_posts(ws, subreddit)
            log("Reddit", f"Found {len(posts)} posts")

            candidates = [
                p
                for p in posts
                if 2 <= p.get("comments", 0) <= 50 and p["url"] not in replied_urls
            ]

            if candidates:
                post = random.choice(candidates)
                category = categorize_post(post["title"])
                reply = random.choice(REDDIT_TEMPLATES[category])

                log("Reddit", f"Replying to: {post['title'][:60]}...")

                success = reddit_post_reply(ws, post["url"], reply)

                if success:
                    replied_urls.add(post["url"])
                    count += 1
                    log("Reddit", f"Reply #{count} posted!")
                else:
                    log("Reddit", "Failed to post reply")
            else:
                log("Reddit", "No suitable posts")

            delay = random.randint(15, 45) * 60
            log("Reddit", f"Waiting {delay // 60} minutes...")

            if stop_event.wait(timeout=delay):
                break

        except Exception as e:
            log("Reddit", f"Error: {e}")
            if stop_event.wait(timeout=60):
                break

    ws.close()
    log("Reddit", f"Agent stopped. Total replies: {count}")


def twitter_agent(ws_url, stop_event):
    """Twitter reply agent thread"""
    try:
        ws = websocket.create_connection(ws_url, timeout=15)
    except Exception as e:
        log("Twitter", f"Connection failed: {e}")
        return

    search_terms = [
        "MCP server",
        "AI agent framework",
        "Claude Code",
        "AI tool routing",
        "LLM rate limit",
    ]
    replied_urls = set()
    count = 0

    log("Twitter", "Agent started")

    while not stop_event.is_set():
        try:
            term = random.choice(search_terms)
            log("Twitter", f"Searching: '{term}'...")

            tweets = search_twitter(ws, term)
            log("Twitter", f"Found {len(tweets)} tweets")

            candidates = [
                t
                for t in tweets
                if len(t.get("text", "")) > 30 and t.get("url", "") not in replied_urls
            ]

            if candidates:
                tweet = random.choice(candidates)
                category = categorize_tweet(tweet["text"])
                reply = random.choice(TWITTER_TEMPLATES[category])

                log("Twitter", f"Replying to: {tweet['text'][:60]}...")

                success = twitter_post_reply(ws, tweet["url"], reply)

                if success:
                    replied_urls.add(tweet["url"])
                    count += 1
                    log("Twitter", f"Reply #{count} posted!")
                else:
                    log("Twitter", "Failed to post reply")
            else:
                log("Twitter", "No suitable tweets")

            delay = random.randint(10, 30) * 60
            log("Twitter", f"Waiting {delay // 60} minutes...")

            if stop_event.wait(timeout=delay):
                break

        except Exception as e:
            log("Twitter", f"Error: {e}")
            if stop_event.wait(timeout=60):
                break

    ws.close()
    log("Twitter", f"Agent stopped. Total replies: {count}")


def main():
    ws_url = get_cdp_url()
    if not ws_url:
        print(
            "Could not connect to browser. Is Edge running with --remote-debugging-port=9222?"
        )
        return

    print(f"Connecting to: {ws_url}")

    print("\n" + "=" * 60)
    print("  HyperNexus Autonomous Marketing Bot")
    print("=" * 60)
    print("  Reddit: r/mcp, r/ClaudeAI, r/LocalLLaMA, etc.")
    print("  Twitter: MCP, AI agent, Claude Code searches")
    print("  Press Ctrl+C to stop all agents")
    print("=" * 60)

    stop_event = threading.Event()

    reddit_thread = threading.Thread(
        target=reddit_agent, args=(ws_url, stop_event), daemon=True
    )
    twitter_thread = threading.Thread(
        target=twitter_agent, args=(ws_url, stop_event), daemon=True
    )

    reddit_thread.start()
    time.sleep(5)  # Stagger starts
    twitter_thread.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\nStopping all agents...")
        stop_event.set()
        reddit_thread.join(timeout=30)
        twitter_thread.join(timeout=30)
        print("All agents stopped.")


if __name__ == "__main__":
    main()
