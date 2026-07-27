#!/usr/bin/env python3
"""
Post tweets using Twitter API v2 with OAuth 1.0a
"""
import requests
import time
from requests_oauthlib import OAuth1

# Twitter API credentials
API_KEY = "HXaYr19KFaQnpCKtQ7vTX1PPz"
API_SECRET = "PSIqZEkQc7yJ5bq2zjsQzW2Uj7pnCLBOoahgqnJBnqAMr3rxRT"
ACCESS_TOKEN = "2079245743085223936-pQHfVkcpy6TgrgN7pQAUMbrXaeW9SQ"
ACCESS_SECRET = "NDEJUqR7Fsnaix8gjNFWhb4s6PWZqMgkat9y5T7Z3ew2Q"

# OAuth 1.0a authentication
auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)

# Tweets to post
TWEETS = [
    {
        "text": "Your AI agent is drowning in 50,000 tokens of tool definitions.\n\nHyperNexus uses Progressive MCP Tool Routing to inject only the 3 most relevant tools per request.\n\nResult: 95% reduction in context usage.\n\nhttps://hypernexus.site/blog/progressive-tool-routing.html\n\n#AI #MCP #DevTools",
        "url": "https://hypernexus.site/blog/progressive-tool-routing.html"
    },
    {
        "text": "Your AI agent forgets everything between sessions.\n\nHyperNexus implements a dual-tier memory architecture with 14,726+ persistent memories that survive restarts.\n\nYour team's knowledge accumulates, not evaporates.\n\nhttps://hypernexus.site/blog/ai-agent-memory.html\n\n#AI #Memory #LLM",
        "url": "https://hypernexus.site/blog/ai-agent-memory.html"
    },
    {
        "text": "When OpenAI rate-limits you at 2 AM, your team stops working.\n\nHyperNexus implements automatic LLM failover:\n1. Primary APIs\n2. OpenRouter\n3. Local Ollama\n\nZero downtime inference.\n\nhttps://hypernexus.site/blog/llm-waterfall.html\n\n#AI #LLM #Infrastructure",
        "url": "https://hypernexus.site/blog/llm-waterfall.html"
    },
    {
        "text": "Your code shouldn't leave your network.\n\nHyperNexus is local-first:\n- Privacy: Prompts stay on your machines\n- Speed: 10x faster than cloud APIs\n- Reliability: Works offline\n- Cost: No per-query pricing\n\nhttps://hypernexus.site/blog/local-first.html\n\n#AI #LocalFirst #Privacy",
        "url": "https://hypernexus.site/blog/local-first.html"
    },
    {
        "text": "One config. Six AI harnesses. Zero vendor lock-in.\n\nHyperNexus maintains byte-for-byte tool parity across Claude Code, Cursor, Codex, Gemini CLI, Copilot, and Kiro.\n\n27 golden fixtures. 6 platforms.\n\nhttps://hypernexus.site/blog/cross-harness-parity.html\n\n#AI #MCP #DevTools",
        "url": "https://hypernexus.site/blog/cross-harness-parity.html"
    },
    {
        "text": "Security checklist for self-hosted AI:\n\n1. TLS everywhere\n2. Network isolation\n3. Auth on every endpoint\n4. Audit logging\n\nHyperNexus ships with all four by default.\n\nhttps://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html\n\n#AI #Security #SelfHosted",
        "url": "https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html"
    }
]

def post_tweet(text):
    """Post a tweet using Twitter API v2"""
    url = "https://api.twitter.com/2/tweets"
    
    payload = {"text": text}
    
    try:
        response = requests.post(url, json=payload, auth=auth, timeout=30)
        
        if response.status_code == 201:
            result = response.json()
            tweet_id = result["data"]["id"]
            print(f"  Posted: https://x.com/HyperNexusLLC/status/{tweet_id}")
            return True
        elif response.status_code == 429:
            print("  Rate limited - waiting...")
            time.sleep(60)
            # Retry
            response = requests.post(url, json=payload, auth=auth, timeout=30)
            if response.status_code == 201:
                result = response.json()
                tweet_id = result["data"]["id"]
                print(f"  Posted (retry): https://x.com/HyperNexusLLC/status/{tweet_id}")
                return True
            else:
                print(f"  Error (retry): {response.status_code} - {response.text[:100]}")
                return False
        else:
            print(f"  Error: {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def main():
    print("=" * 60)
    print("POSTING TO TWITTER/X")
    print("=" * 60)
    print()
    
    print("Account: @HyperNexusLLC")
    print(f"Tweets to post: {len(TWEETS)}")
    print()
    
    success = 0
    for i, tweet in enumerate(TWEETS, 1):
        print(f"[{i}/{len(TWEETS)}] {tweet['text'][:60]}...")
        
        if post_tweet(tweet["text"]):
            success += 1
        
        # Wait between tweets to avoid rate limiting
        if i < len(TWEETS):
            print("  Waiting 5 seconds...")
            time.sleep(5)
    
    print()
    print(f"Results: {success}/{len(TWEETS)} tweets posted")
    print("=" * 60)

if __name__ == "__main__":
    main()
