"""
Autonomous Twitter/X Reply Agent
Posts intelligent replies to relevant threads using CDP
Uses MiMo v2.5 LLM for generating contextual replies
"""

import websocket
import json
import time
import random
import urllib.request
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_reply import generate_reply, get_url_for_context

# Fallback templates if LLM fails
FALLBACK_TEMPLATES = {
    "mcp": "Progressive tool routing matches prompts to top 3 most relevant tools via semantic search. ~60% token reduction. {url}",
    "rate_limit": "The Waterfall Pattern: Primary API -> Secondary API -> Local models -> Queue. Zero downtime from rate limits. {url}",
    "agent": "Progressive tool routing + persistent memory + multi-model failover is the reliable AI agent stack. {url}",
    "generic": "Progressive tool routing + persistent memory = reliable AI agents. {url}",
}


def get_cdp_url():
    """Get a usable browser tab URL.

    Strategy: Use the first available about:blank or generic tab.
    The caller will navigate to Twitter/search as needed.
    """
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        # Priority 1: about:blank tabs (fresh, no interference)
        for tab in tabs:
            if tab.get("url", "") == "about:blank":
                return tab.get("webSocketDebuggerUrl")
        # Priority 2: generic non-app tabs
        for tab in tabs:
            url = tab.get("url", "")
            if (
                url.startswith("https://")
                and "x.com" not in url
                and "twitter" not in url
                and "linkedin" not in url
                and "reddit" not in url
            ):
                return tab.get("webSocketDebuggerUrl")
        # Last resort: create a new tab via browser-level WS
        browser_resp = urllib.request.urlopen(
            "http://localhost:9222/json/version", timeout=5
        )
        browser_ws = json.loads(browser_resp.read()).get("webSocketDebuggerUrl")
        if browser_ws:
            ws = websocket.create_connection(browser_ws, timeout=15)
            ws.send(
                json.dumps(
                    {
                        "id": 1,
                        "method": "Target.createTarget",
                        "params": {"url": "about:blank"},
                    }
                )
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
                resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
                for t in json.loads(resp.read()):
                    if t.get("id") == target_id:
                        return t.get("webSocketDebuggerUrl")
    except Exception:
        pass
    return None


def send_and_recv(ws, msg_id, method, params=None, timeout=8):
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    time.sleep(1)
    result = None
    for _ in range(10):
        try:
            ws.settimeout(timeout)
            data = json.loads(ws.recv())
            if data.get("id") == msg_id:
                result = data.get("result", {}).get("result", {}).get("value")
                break
        except websocket.WebSocketTimeoutException:
            break
        except Exception:
            break
    return result


def navigate(ws, url, wait=7):
    ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}}))
    time.sleep(wait)
    for _ in range(10):
        try:
            ws.settimeout(0.5)
            ws.recv()
        except Exception:
            break


def search_twitter(ws, term):
    """Search Twitter for recent tweets with a term"""
    url = f"https://x.com/search?q={term}&src=typed_query&f=live"
    navigate(ws, url)

    result = send_and_recv(
        ws,
        2,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var tweets = [];
            var articles = document.querySelectorAll('article[data-testid="tweet"]');
            for (var i = 0; i < Math.min(articles.length, 10); i++) {
                var el = articles[i];
                var textEl = el.querySelector('[data-testid="tweetText"]');
                var replyBtn = el.querySelector('[data-testid="reply"]');
                var timeEl = el.querySelector('time');

                if (textEl) {
                    var replyCount = 0;
                    if (replyBtn) {
                        var ariaLabel = replyBtn.getAttribute('aria-label') || '';
                        var match = ariaLabel.match(/(\\d+)/);
                        if (match) replyCount = parseInt(match[1]);
                    }

                    var links = el.querySelectorAll('a[href*="/status/"]');
                    var tweetUrl = links.length > 0 ? links[links.length-1].href : '';

                    tweets.push({
                        text: textEl.textContent.trim().substring(0, 300),
                        url: tweetUrl,
                        replies: replyCount,
                        time: timeEl ? timeEl.getAttribute('datetime') : ''
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
        except Exception:
            pass
    return []


def categorize_tweet(text):
    t = text.lower()
    if any(w in t for w in ["mcp", "model context protocol", "tool routing"]):
        return "mcp"
    if any(w in t for w in ["rate limit", "429", "quota"]):
        return "rate_limit"
    if any(w in t for w in ["agent", "framework", "orchestration"]):
        return "agent"
    return "generic"


def post_reply(ws, tweet_url, reply_text):
    """Navigate to tweet and post a reply"""
    navigate(ws, tweet_url)

    # Click reply button
    result = send_and_recv(
        ws,
        3,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var btn = document.querySelector('[data-testid="reply"]');
            if (btn) { btn.click(); return 'clicked'; }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "clicked" not in str(result):
        print(f"  [!] Reply button: {result}")
        return False

    time.sleep(2)

    # Focus the tweet textbox
    result = send_and_recv(
        ws,
        4,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var box = document.querySelector('[data-testid="tweetTextarea_0"]');
            if (box) { box.focus(); return 'focused'; }
            var divs = document.querySelectorAll('div[contenteditable="true"]');
            for (var i = 0; i < divs.length; i++) {
                if (divs[i].getAttribute('role') === 'textbox') {
                    divs[i].focus(); return 'focused div';
                }
            }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "focused" not in str(result):
        print(f"  [!] Textbox: {result}")
        return False

    time.sleep(1)

    # Type reply
    ws.send(
        json.dumps(
            {"id": 5, "method": "Input.insertText", "params": {"text": reply_text}}
        )
    )
    time.sleep(2)
    for _ in range(5):
        try:
            ws.settimeout(1)
            ws.recv()
        except Exception:
            break

    # Click tweet/reply button
    result = send_and_recv(
        ws,
        6,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var btn = document.querySelector('[data-testid="tweetButton"]');
            if (btn) { btn.click(); return 'tweeted'; }
            var btn2 = document.querySelector('[data-testid="tweetButtonInline"]');
            if (btn2) { btn2.click(); return 'tweeted inline'; }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(3)

    if result and "tweeted" in str(result):
        return True

    print(f"  [!] Tweet button: {result}")
    return False


def main():
    ws_url = get_cdp_url()
    if not ws_url:
        print("Could not connect to browser")
        return

    print(f"Connecting to: {ws_url}")
    ws = websocket.create_connection(ws_url, timeout=15)
    print("Connected!")

    search_terms = [
        "MCP server",
        "AI agent framework",
        "Claude Code",
        "AI tool routing",
        "LLM rate limit",
    ]
    replied_urls = set()
    reply_count = 0

    print("\n" + "=" * 60)
    print("  Autonomous Twitter Reply Agent (MiMo v2.5)")
    print("=" * 60)
    print(f"  Search terms: {', '.join(search_terms)}")
    print("  Delay: 10-30 minutes between replies")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    try:
        while True:
            try:
                term = random.choice(search_terms)
                print(f"\n[Search] '{term}'...")

                tweets = search_twitter(ws, term)
                print(f"[Found] {len(tweets)} tweets")

                candidates = [
                    t
                    for t in tweets
                    if len(t.get("text", "")) > 30
                    and t.get("url", "") not in replied_urls
                ]

                if candidates:
                    tweet = random.choice(candidates)

                    print(f"[Target] {tweet['text'][:70]}...")

                    # Generate intelligent reply with MiMo v2.5
                    print("[LLM] Generating reply with MiMo v2.5...")
                    reply = generate_reply(tweet["text"], platform="twitter")

                    if not reply:
                        # Fallback if LLM fails
                        url = get_url_for_context(tweet["text"])
                        category = categorize_tweet(tweet["text"])
                        reply = FALLBACK_TEMPLATES.get(
                            category, FALLBACK_TEMPLATES["generic"]
                        ).format(url=url)
                        print(f"[Fallback] {reply[:70]}...")
                    else:
                        print(f"[Reply] {reply[:70]}...")

                    success = post_reply(ws, tweet["url"], reply)

                    if success:
                        replied_urls.add(tweet["url"])
                        reply_count += 1
                        print(f"[OK] Reply #{reply_count} posted!")
                    else:
                        print("[FAIL] Could not post reply")
                else:
                    print("[Skip] No suitable tweets found")

                # Random delay 10-30 min
                delay_min = random.randint(10, 30)
                print(f"[Wait] {delay_min} minutes...")

                for remaining in range(delay_min, 0, -1):
                    time.sleep(60)
                    if remaining % 5 == 0 and remaining > 0:
                        print(f"  ...{remaining} min remaining")

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"[Error] {e}")
                time.sleep(60)

    except KeyboardInterrupt:
        print(f"\n\nStopped. Total replies: {reply_count}")

    ws.close()


if __name__ == "__main__":
    main()
