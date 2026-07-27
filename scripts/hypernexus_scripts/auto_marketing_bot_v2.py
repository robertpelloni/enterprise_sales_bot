"""
HyperNexus Autonomous Marketing Bot v2
Creates separate browser tabs for each agent
"""

import websocket
import json
import time
import random
import threading
import urllib.request
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_reddit_v2 import (
    extract_posts,
    post_reply as reddit_post_reply,
)
from auto_twitter_v2 import (
    search_twitter,
    post_reply as twitter_post_reply,
)
from auto_linkedin_page import (
    publish_post,
    comment_on_post,
    search_linkedin_feed,
    PAGE_POSTS as LINKEDIN_POSTS,
)
from llm_reply import generate_reply, get_url_for_context


def get_browser_ws():
    """Get browser-level WebSocket URL for creating tabs"""
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json/version", timeout=5)
        info = json.loads(resp.read())
        return info.get("webSocketDebuggerUrl")
    except Exception:
        return None


def create_tab(browser_ws, url="about:blank"):
    """Create a new browser tab and return its WebSocket URL"""
    ws = websocket.create_connection(browser_ws, timeout=15)
    ws.send(
        json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": url}})
    )
    time.sleep(2)

    target_id = None
    for _ in range(5):
        try:
            ws.settimeout(3)
            d = json.loads(ws.recv())
            if d.get("id") == 1:
                target_id = d.get("result", {}).get("targetId")
                break
        except Exception:
            continue

    ws.close()

    if target_id:
        # Get the tab's WebSocket URL
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        for tab in tabs:
            if tab.get("id") == target_id:
                return tab.get("webSocketDebuggerUrl")

    return None


def log(prefix, msg):
    ts = time.strftime("%H:%M:%S")
    sys.stdout.buffer.write(f"[{ts}] [{prefix}] {msg}\n".encode("utf-8"))
    sys.stdout.flush()


def reddit_agent(ws_url, stop_event):
    """Reddit reply agent with its own tab"""
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

                log("Reddit", f"Replying to: {post['title'][:60]}...")

                # Generate intelligent reply with MiMo v2.5
                log("Reddit", "[LLM] Generating reply...")
                reply = generate_reply(post["title"], platform="reddit")

                if not reply:
                    url = get_url_for_context(post["title"])
                    reply = f"Progressive tool routing changes the game for AI dev efficiency. {url}"
                    log("Reddit", f"[Fallback] {reply[:60]}...")
                else:
                    log("Reddit", f"[Reply] {reply[:60]}...")

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
    """Twitter reply agent with its own tab"""
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

                log("Twitter", f"Replying to: {tweet['text'][:60]}...")

                # Generate intelligent reply with MiMo v2.5
                log("Twitter", "[LLM] Generating reply...")
                reply = generate_reply(tweet["text"], platform="twitter")

                if not reply:
                    url = get_url_for_context(tweet["text"])
                    reply = f"Progressive tool routing + persistent memory = reliable AI agents. {url}"
                    log("Twitter", f"[Fallback] {reply[:60]}...")
                else:
                    log("Twitter", f"[Reply] {reply[:60]}...")

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


def linkedin_agent(ws_url, stop_event):
    """LinkedIn page agent: posts content and comments as HyperNexus"""
    try:
        ws = websocket.create_connection(ws_url, timeout=15)
    except Exception as e:
        log("LinkedIn", f"Connection failed: {e}")
        return

    # Track published posts to avoid duplicates
    published_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "linkedin_published.json"
    )
    try:
        with open(published_file, "r") as f:
            published_indices = json.load(f)
    except Exception:
        published_indices = []

    # First, publish the 7 page posts (only unpublished ones)
    log(
        "LinkedIn",
        f"Checking for unpublished posts... ({len(published_indices)} already published)",
    )
    for i, content in enumerate(LINKEDIN_POSTS):
        if stop_event.is_set():
            break
        if i in published_indices:
            log("LinkedIn", f"Post {i + 1} already published, skipping")
            continue
        log("LinkedIn", f"Publishing post {i + 1}/{len(LINKEDIN_POSTS)}...")
        success = publish_post(ws, content)
        if success:
            published_indices.append(i)
            with open(published_file, "w") as f:
                json.dump(published_indices, f)
            log("LinkedIn", f"Post {i + 1} published!")
        else:
            log("LinkedIn", f"Post {i + 1} failed")
        if i < len(LINKEDIN_POSTS) - 1:
            delay = random.randint(30, 60)
            log("LinkedIn", f"Waiting {delay}s before next post...")
            if stop_event.wait(timeout=delay):
                break

    log("LinkedIn", "All page posts published. Starting comment agent...")

    # Then start commenting on relevant posts
    search_terms = ["MCP server", "AI agent", "Claude Code", "developer tools AI"]
    commented_urls = set()
    count = 0

    log("LinkedIn", "Starting comment agent...")

    while not stop_event.is_set():
        try:
            term = random.choice(search_terms)
            log("LinkedIn", f"Searching for '{term}'...")

            posts = search_linkedin_feed(ws, term)
            log("LinkedIn", f"Found {len(posts)} posts")

            candidates = [
                p
                for p in posts
                if len(p.get("text", "")) > 50
                and p.get("url", "") not in commented_urls
                and p.get("url", "") != ""
            ]

            if candidates:
                post = random.choice(candidates)

                log("LinkedIn", f"Commenting on: {post['text'][:60]}...")

                # Generate intelligent comment with MiMo v2.5
                log("LinkedIn", "[LLM] Generating comment...")
                comment = generate_reply(post["text"], platform="linkedin")

                if not comment:
                    url = get_url_for_context(post["text"])
                    comment = f"Progressive tool routing changes the game for AI dev efficiency. {url}"
                    log("LinkedIn", f"[Fallback] {comment[:60]}...")
                else:
                    log("LinkedIn", f"[Comment] {comment[:60]}...")

                success = comment_on_post(ws, post["url"], comment)

                if success:
                    commented_urls.add(post["url"])
                    count += 1
                    log("LinkedIn", f"Comment #{count} posted!")
                else:
                    log("LinkedIn", "Failed to post comment")
            else:
                log("LinkedIn", "No suitable posts found")

            delay = random.randint(20, 45) * 60
            log("LinkedIn", f"Waiting {delay // 60} minutes...")

            if stop_event.wait(timeout=delay):
                break

        except Exception as e:
            log("LinkedIn", f"Error: {e}")
            if stop_event.wait(timeout=60):
                break

    ws.close()
    log("LinkedIn", f"Agent stopped. Total comments: {count}")


def main():
    browser_ws = get_browser_ws()
    if not browser_ws:
        print(
            "Could not connect to browser. Is Edge running with --remote-debugging-port=9222?"
        )
        return

    print(f"Browser WS: {browser_ws}")

    # Create separate tabs for each agent
    print("Creating browser tabs...")
    reddit_ws_url = create_tab(browser_ws, "https://old.reddit.com/r/mcp/new/")
    time.sleep(2)
    twitter_ws_url = create_tab(
        browser_ws, "https://x.com/search?q=MCP%20server&src=typed_query&f=live"
    )
    time.sleep(2)
    linkedin_ws_url = create_tab(
        browser_ws, "https://www.linkedin.com/company/135697123/admin/"
    )

    if not reddit_ws_url or not twitter_ws_url or not linkedin_ws_url:
        print("Failed to create browser tabs")
        return

    print(f"Reddit tab: {reddit_ws_url}")
    print(f"Twitter tab: {twitter_ws_url}")
    print(f"LinkedIn tab: {linkedin_ws_url}")

    print("\n" + "=" * 60)
    print("  HyperNexus Autonomous Marketing Bot v3")
    print("=" * 60)
    print("  Reddit: r/mcp, r/ClaudeAI, r/LocalLLaMA, etc.")
    print("  Twitter: MCP, AI agent, Claude Code searches")
    print("  LinkedIn: HyperNexus Page posts + comments")
    print("  Each agent has its own browser tab")
    print("  Press Ctrl+C to stop all agents")
    print("=" * 60)

    stop_event = threading.Event()

    reddit_thread = threading.Thread(
        target=reddit_agent, args=(reddit_ws_url, stop_event), daemon=True
    )
    twitter_thread = threading.Thread(
        target=twitter_agent, args=(twitter_ws_url, stop_event), daemon=True
    )
    linkedin_thread = threading.Thread(
        target=linkedin_agent, args=(linkedin_ws_url, stop_event), daemon=True
    )

    reddit_thread.start()
    time.sleep(3)
    twitter_thread.start()
    time.sleep(3)
    linkedin_thread.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\nStopping all agents...")
        stop_event.set()
        reddit_thread.join(timeout=30)
        twitter_thread.join(timeout=30)
        linkedin_thread.join(timeout=30)
        print("All agents stopped.")


if __name__ == "__main__":
    main()
