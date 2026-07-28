#!/usr/bin/env python3
"""
Twitter Agent - Autonomous Twitter/X engagement
Extracted from autonomous_marketing.py
"""
import json
import time
import random

# Search terms for finding relevant tweets
SEARCH_TERMS = [
    "MCP server",
    "AI agent",
    "Claude Code",
    "AI tool routing",
    "LLM rate limit",
    "AI memory",
    "developer tools AI",
]


def categorize_tweet(text):
    """Categorize a tweet by its topic"""
    text_lower = text.lower()
    
    if any(term in text_lower for term in ["mcp", "model context protocol"]):
        return "mcp"
    elif any(term in text_lower for term in ["rate limit", "429", "quota"]):
        return "rate_limit"
    elif any(term in text_lower for term in ["agent", "ai tool", "developer"]):
        return "agent"
    else:
        return "generic"


def generate_reply(tweet_text):
    """Generate an intelligent reply to a tweet"""
    category = categorize_tweet(tweet_text)
    
    replies = {
        "mcp": [
            "Progressive tool routing is the key! Instead of loading all MCP definitions, semantic search matches your prompt to the top 3 most relevant tools. 60% token reduction. HyperNexus does this automatically.",
            "This is exactly why we built HyperNexus. MCP servers are powerful, but managing 50+ tools manually is painful. Progressive routing + automatic failover = zero friction.",
            "The future of MCP is intelligent tool selection. Not all tools need to be in context all the time.",
        ],
        "rate_limit": [
            "The Waterfall Pattern solves this: Primary API -> Secondary API -> Local models -> Queue. Zero downtime from rate limits. HyperNexus handles this automatically.",
            "Rate limits killed my workflow until I set up a three-tier failover cascade. Now when OpenAI hits 429, it seamlessly switches to Claude, then to local Ollama. No interruptions.",
            "Transparent LLM failover is the answer. Your agent shouldn't even notice rate limits.",
        ],
        "agent": [
            "Progressive tool routing changes the game. Instead of dumping 50K tokens of tool definitions, you semantically match the task to the top 3 tools. HyperNexus does this automatically.",
            "The key to reliable AI agents: 1) Progressive tool routing 2) Persistent memory 3) Multi-model failover. That's what makes HyperNexus different.",
            "AI agents need infrastructure, not just prompts. Tool routing, memory management, and failover should be automatic.",
        ],
        "generic": [
            "Great insight! Progressive tool routing + persistent memory = reliable AI agents. That's what we're building at HyperNexus.",
            "This resonates! AI infrastructure should be as well-engineered as the apps it powers.",
            "The key is making AI tools work together seamlessly. Universal control plane is the answer.",
        ],
    }
    
    return random.choice(replies.get(category, replies["generic"]))


def search_twitter(cdp, term):
    """Search Twitter for relevant tweets"""
    url = f"https://x.com/search?q={term}&src=typed_query&f=live"
    cdp.navigate(url)
    time.sleep(6)

    result = cdp.evaluate("""
        (function() {
            var tweets = [];
            var tweetElements = document.querySelectorAll('article[data-testid="tweet"]');
            for (var i = 0; i < Math.min(tweetElements.length, 10); i++) {
                var tweet = tweetElements[i];
                var text = tweet.querySelector('[data-testid="tweetText"]');
                var user = tweet.querySelector('[data-testid="User-Name"]');
                var replyCount = tweet.querySelector('[data-testid="reply"]');
                
                if (text) {
                    tweets.push({
                        text: text.textContent.trim().substring(0, 300),
                        user: user ? user.textContent.trim().substring(0, 50) : 'Unknown',
                        replies: replyCount ? replyCount.textContent.trim() : '0',
                        id: tweet.getAttribute('data-tweet-id') || i.toString()
                    });
                }
            }
            return JSON.stringify(tweets);
        })()
    """)

    if result and result.get("result", {}).get("value"):
        try:
            return json.loads(result["result"]["value"])
        except:
            pass
    return []


def post_reply(cdp, tweet_id, reply_text):
    """Post a reply to a tweet"""
    # Find and click reply button
    cdp.evaluate("""
        (function() {
            var tweet = document.querySelector('article[data-testid="tweet"]');
            if (!tweet) return 'tweet not found';
            
            var replyBtn = tweet.querySelector('[data-testid="reply"]');
            if (replyBtn) {
                replyBtn.click();
                return 'reply clicked';
            }
            return 'reply button not found';
        })()
    """)

    time.sleep(2)

    # Type reply in the modal
    cdp.evaluate("""
        (function() {
            var textbox = document.querySelector('[data-testid="tweetTextarea_0"]');
            if (textbox) {
                textbox.focus();
                return 'textbox focused';
            }
            return 'textbox not found';
        })()
    """)

    time.sleep(1)
    cdp.type_text(reply_text)
    time.sleep(2)

    # Click tweet button
    result = cdp.evaluate("""
        (function() {
            var tweetBtn = document.querySelector('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]');
            if (tweetBtn) {
                tweetBtn.click();
                return 'tweeted';
            }
            return 'tweet button not found';
        })()
    """)

    time.sleep(3)
    return result


def post_tweet(cdp, text):
    """Post a new tweet"""
    cdp.navigate("https://x.com/compose/post")
    time.sleep(5)

    # Focus textarea
    cdp.evaluate("""
        (function() {
            var textbox = document.querySelector('[data-testid="tweetTextarea_0"]');
            if (textbox) {
                textbox.focus();
                return 'focused';
            }
            return 'not found';
        })()
    """)

    time.sleep(1)
    cdp.type_text(text[:280])
    time.sleep(2)

    # Click tweet button
    result = cdp.evaluate("""
        (function() {
            var tweetBtn = document.querySelector('[data-testid="tweetButton"]');
            if (tweetBtn) {
                tweetBtn.click();
                return 'tweeted';
            }
            return 'not found';
        })()
    """)

    time.sleep(3)
    return result


def run_twitter_loop(cdp, stats, running):
    """Main Twitter engagement loop"""
    print("Starting Twitter engagement loop...")
    replied_tweets = set()

    while running():
        try:
            term = random.choice(SEARCH_TERMS)
            print(f"[Twitter] Searching for '{term}'...")

            tweets = search_twitter(cdp, term)

            if tweets:
                relevant_tweets = [
                    t for t in tweets
                    if t["id"] not in replied_tweets
                ]

                if relevant_tweets:
                    tweet = random.choice(relevant_tweets)
                    print(f"[Twitter] Found tweet: {tweet['text'][:50]}...")

                    reply = generate_reply(tweet["text"])
                    print(f"[Twitter] Generated reply: {reply[:50]}...")

                    result = post_reply(cdp, tweet["id"], reply)

                    if result and "tweeted" in str(result).lower():
                        replied_tweets.add(tweet["id"])
                        stats["twitter_replies"] = stats.get("twitter_replies", 0) + 1
                        print(f"[Twitter] Reply posted! Total: {stats['twitter_replies']}")
                    else:
                        print(f"[Twitter] Failed to post reply: {result}")
                else:
                    print("[Twitter] No relevant tweets found")
            else:
                print("[Twitter] No tweets found")

            delay = random.randint(10 * 60, 30 * 60)
            print(f"[Twitter] Waiting {delay // 60} minutes...")
            time.sleep(delay)

        except Exception as e:
            print(f"[Twitter] Error: {e}")
            time.sleep(60)
