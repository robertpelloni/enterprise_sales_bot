#!/usr/bin/env python3
"""
Post articles to Twitter/X using API v2
"""
import os

# Twitter API credentials from .env
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_HYPERNEXUS_BEARER_TOKEN", "")
TWITTER_API_KEY = os.environ.get("TWITTER_HYPERNEXUS_API_KEY", "")
TWITTER_API_SECRET = os.environ.get("TWITTER_HYPERNEXUS_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_HYPERNEXUS_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_HYPERNEXUS_ACCESS_SECRET", "")

# Articles to tweet
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

def create_oauth_signature(method, url, params, consumer_secret, token_secret):
    """Create OAuth 1.0a signature"""
    import hmac
    import hashlib
    import base64
    from urllib.parse import quote
    
    # Sort parameters
    sorted_params = sorted(params.items())
    param_string = '&'.join([f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in sorted_params])
    
    # Create signature base string
    base_string = f"{method}&{quote(url, safe='')}&{quote(param_string, safe='')}"
    
    # Create signing key
    signing_key = f"{quote(consumer_secret, safe='')}&{quote(token_secret, safe='')}"
    
    # Create signature
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    
    return signature

def post_tweet(tweet_text):
    """Post a tweet using Twitter API v2"""
    url = "https://api.twitter.com/2/tweets"
    
    # For now, just print the tweet (API v2 requires OAuth 2.0 PKCE)
    print(f"Tweet: {tweet_text[:100]}...")
    print(f"Length: {len(tweet_text)} chars")
    print()
    
    # Note: Twitter API v2 requires OAuth 2.0 with PKCE flow
    # which cannot be done with simple API calls
    return {"text": tweet_text, "status": "ready_to_post"}

def main():
    print("=" * 60)
    print("TWITTER/X CROSS-POSTING")
    print("=" * 60)
    print()
    
    print(f"API Key: {'Found' if TWITTER_API_KEY else 'Not found'}")
    print(f"Access Token: {'Found' if TWITTER_ACCESS_TOKEN else 'Not found'}")
    print()
    
    print(f"Tweets to post: {len(TWEETS)}")
    print()
    
    for i, tweet in enumerate(TWEETS, 1):
        print(f"[{i}/{len(TWEETS)}] {tweet['text'][:80]}...")
        print(f"  URL: {tweet['url']}")
        print()
    
    print("=" * 60)
    print("Note: Twitter API v2 requires OAuth 2.0 PKCE flow")
    print("Use the browser automation or post manually")
    print("=" * 60)

if __name__ == "__main__":
    main()
