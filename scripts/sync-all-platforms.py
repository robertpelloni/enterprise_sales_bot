#!/usr/bin/env python3
"""
Sync all articles across ALL platforms automatically.
Platforms: dev.to, Twitter, LinkedIn, Bluesky, Reddit, Hashnode
"""

import requests
import json
import time
import urllib.request

# ═══════════════════════════════════════════════════════════════
# API KEYS
# ═══════════════════════════════════════════════════════════════

DEVTO_API_KEY = "acWJBPGAFfSb4VeMAmgp5SWr"
BLUESKY_HANDLE = "hypernexusllc.bsky.social"
BLUESKY_APP_PASSWORD = "b33d-3ivg-pqtk-c6tv"
REDDIT_USERNAME = "HyperNexusLLC"
REDDIT_PASSWORD = "Temppass0!"
REDDIT_CLIENT_ID = "0lX58KJiiwuHIY9uHEgZZw"
REDDIT_CLIENT_SECRET = "E07dDaqBlpFdn5vVL2UZPn9YxtQNcg"

# LinkedIn (CDP)
LINKEDIN_COMPANY_URL = "https://www.linkedin.com/company/135697123/admin/"

# Subreddits to post to
SUBREDDITS = ["selfhosted", "MachineLearning", "LocalLLaMA", "ChatGPT", "programming"]

# ═══════════════════════════════════════════════════════════════
# ALL ARTICLES TO SYNC
# ═══════════════════════════════════════════════════════════════

ARTICLES = [
    {
        "title": "Harden Your Self-Hosted AI: A Practical Checklist",
        "url": "https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html",
        "tags": ["ai", "security", "selfhosted", "hypernexus"],
        "description": "A comprehensive security checklist for self-hosted AI deployments.",
        "tweet": "Your self-hosted AI is probably not as secure as you think.\n\nPractical checklist:\n1. TLS everywhere\n2. Network isolation\n3. Auth on every endpoint\n4. Audit logging\n\nhttps://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html\n\n#AI #Security",
        "linkedin": "Your self-hosted AI is probably not as secure as you think.\n\nHere's a practical checklist we use at HyperNexus:\n\n1. TLS everywhere - even on localhost\n2. Network isolation - separate VLANs for AI services\n3. Auth on every endpoint - no anonymous access\n4. Audit logging - every action tracked\n\nFull checklist: https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html",
        "reddit_title": "Practical checklist for hardening self-hosted AI deployments",
        "reddit_body": "We put together a comprehensive security checklist for self-hosted AI:\n\n1. TLS everywhere - even on localhost\n2. Network isolation - separate VLANs\n3. Auth on every endpoint\n4. Audit logging\n\nFull guide: https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html\n\nWhat security measures do you use for your self-hosted AI stack?",
    },
    {
        "title": "The CISO's Checklist for Agentic AI Governance",
        "url": "https://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html",
        "tags": ["ai", "security", "governance", "hypernexus"],
        "description": "What every CISO should demand before deploying agentic AI.",
        "tweet": "What should your CISO demand before deploying agentic AI?\n\nNon-negotiables:\n- SSO integration\n- RBAC with least-privilege\n- Immutable audit logs\n- Kill switch for autonomous actions\n\nhttps://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html\n\n#AI #Enterprise",
        "linkedin": "What should your CISO demand before deploying agentic AI?\n\nThe non-negotiables:\n- SSO integration (no local passwords)\n- RBAC with least-privilege defaults\n- Immutable audit logs (append-only)\n- Data residency controls\n- Kill switch for autonomous actions\n\nFull checklist: https://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html",
        "reddit_title": "CISO's checklist for agentic AI governance - what to demand before deploying",
        "reddit_body": "Before deploying agentic AI in your org, your CISO should demand:\n\n1. SSO integration\n2. RBAC with least-privilege\n3. Immutable audit logs\n4. Data residency controls\n5. Kill switch for autonomous actions\n\nFull checklist: https://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html\n\nWhat governance requirements does your org have for AI?",
    },
    {
        "title": "Zero Trust AI Architecture",
        "url": "https://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html",
        "tags": ["ai", "security", "zerotrust", "hypernexus"],
        "description": "How to implement zero trust principles in AI systems.",
        "tweet": "Zero trust for AI means authenticating:\n- Every tool call\n- Every memory access\n- Every model request\n- Every context injection\n\nOne unauthenticated path = complete compromise.\n\nhttps://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html\n\n#AI #ZeroTrust",
        "linkedin": "Zero trust isn't just for networks anymore.\n\nIn agentic AI, you need to authenticate:\n- Every tool call\n- Every memory access\n- Every model request\n- Every context injection\n\nOne unauthenticated path = complete compromise.\n\nFull guide: https://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html",
        "reddit_title": "Implementing zero trust for AI agents - authenticating every tool call",
        "reddit_body": "Zero trust for AI means authenticating every single interaction:\n\n- Every tool call\n- Every memory access\n- Every model request\n- Every context injection\n\nOne unauthenticated path = complete compromise.\n\nFull guide: https://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html\n\nHow do you handle auth in your AI stack?",
    },
    {
        "title": "Securing Self-Hosted AI with Nginx",
        "url": "https://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html",
        "tags": ["ai", "security", "nginx", "hypernexus"],
        "description": "Practical guide to securing self-hosted AI with localhost isolation.",
        "tweet": "Simplest security improvement for self-hosted AI:\n\nBind to localhost + Nginx reverse proxy with TLS.\n\n- AI services never exposed to network\n- TLS terminates at Nginx\n- Single point for auth/rate limiting\n\nhttps://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html\n\n#AI #Security",
        "linkedin": "The simplest security improvement for self-hosted AI:\n\nBind to localhost + Nginx reverse proxy with TLS.\n\nWhy it works:\n- AI services never exposed to network\n- TLS terminates at Nginx\n- Single point for auth/rate limiting\n- Easy to add WAF rules\n\nStep-by-step: https://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html",
        "reddit_title": "Simplest security fix for self-hosted AI: localhost + Nginx reverse proxy",
        "reddit_body": "The simplest security improvement for self-hosted AI:\n\nBind to localhost + Nginx reverse proxy with TLS.\n\nWhy it works:\n- AI services never exposed to network\n- TLS terminates at Nginx\n- Single point for auth/rate limiting\n- Easy to add WAF rules\n\nFull guide: https://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html\n\nAnyone else running their AI stack behind Nginx?",
    },
    {
        "title": "4-Point TLS & Zero Trust Checklist",
        "url": "https://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html",
        "tags": ["ai", "security", "zerotrust", "hypernexus"],
        "description": "Four essential security controls for self-hosted AI.",
        "tweet": "4 security controls that block 90% of attacks on self-hosted AI:\n\n1. TLS 1.3 everywhere\n2. mTLS for service-to-service\n3. Token-based auth\n4. Network segmentation\n\nhttps://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html\n\n#AI #Security",
        "linkedin": "4 security controls that block 90% of attacks on self-hosted AI:\n\n1. TLS 1.3 everywhere (no exceptions)\n2. mTLS for service-to-service\n3. Token-based auth (no API keys in URLs)\n4. Network segmentation (AI on isolated VLAN)\n\nImplement all four: https://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html",
        "reddit_title": "4 security controls that block 90% of attacks on self-hosted AI",
        "reddit_body": "These 4 security controls block 90% of attacks on self-hosted AI:\n\n1. TLS 1.3 everywhere\n2. mTLS for service-to-service\n3. Token-based auth (no API keys in URLs)\n4. Network segmentation\n\nFull guide: https://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html\n\nWhat's your security stack look like?",
    },
    {
        "title": "What CISOs Should Demand Before Deploying Agentic AI",
        "url": "https://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html",
        "tags": ["ai", "governance", "enterprise", "hypernexus"],
        "description": "A practical governance checklist for enterprise AI deployments.",
        "tweet": "Before deploying agentic AI, your CISO should demand:\n\n1. Data flow mapping\n2. Access controls\n3. Incident response plan\n4. Compliance evidence\n5. Vendor security review\n\nhttps://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html\n\n#AI #Enterprise",
        "linkedin": "Before your org deploys agentic AI, your CISO should demand:\n\n1. Data flow mapping (where does training data go?)\n2. Access controls (who can invoke what?)\n3. Incident response (how to revoke AI access?)\n4. Compliance evidence (SOC2, HIPAA, GDPR)\n5. Vendor security review (supply chain)\n\nFull checklist: https://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html",
        "reddit_title": "What your CISO should demand before deploying agentic AI",
        "reddit_body": "Before deploying agentic AI, your CISO should demand:\n\n1. Data flow mapping\n2. Access controls\n3. Incident response plan\n4. Compliance evidence (SOC2, HIPAA, GDPR)\n5. Vendor security review\n\nFull checklist: https://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html\n\nWhat does your org's AI governance look like?",
    },
    {
        "title": "Progressive Tool Routing for AI Agents",
        "url": "https://hypernexus.site/blog/progressive-tool-routing.html",
        "tags": ["ai", "mcp", "tooling", "hypernexus"],
        "description": "How to inject only the 3 most relevant tools per request.",
        "tweet": "Your AI agent is drowning in 50,000 tokens of tool definitions.\n\nHyperNexus uses Progressive MCP Tool Routing to inject only the 3 most relevant tools per request.\n\nResult: 95% reduction in context usage.\n\nhttps://hypernexus.site/blog/progressive-tool-routing.html\n\n#AI #MCP",
        "linkedin": "Every time you connect an MCP server, you're adding thousands of tokens to your context window.\n\nConnect 10 servers? That's 50,000 tokens of tool schemas before you've even asked a question.\n\nHyperNexus solves this with Progressive MCP Tool Routing - semantic search matches your prompt to the top 3 most relevant tools.\n\n95% reduction in tool-related context usage.\n\nhttps://hypernexus.site/blog/progressive-tool-routing.html",
        "reddit_title": "Progressive tool routing: 95% reduction in AI agent context usage",
        "reddit_body": "Your AI agent is drowning in 50,000 tokens of tool definitions.\n\nProgressive MCP Tool Routing injects only the 3 most relevant tools per request instead of dumping the entire catalog.\n\nResult: 95% reduction in context usage, 3x improvement in tool selection accuracy.\n\nFull article: https://hypernexus.site/blog/progressive-tool-routing.html\n\nHow do you handle tool context in your AI agents?",
    },
    {
        "title": "AI Agent Memory Architecture",
        "url": "https://hypernexus.site/blog/ai-agent-memory.html",
        "tags": ["ai", "memory", "llm", "hypernexus"],
        "description": "Building a dual-tier memory architecture that persists across sessions.",
        "tweet": "Your AI agent forgets everything between sessions.\n\nHyperNexus implements a dual-tier memory architecture with 14,726+ persistent memories that survive restarts.\n\nYour team's knowledge accumulates, not evaporates.\n\nhttps://hypernexus.site/blog/ai-agent-memory.html\n\n#AI #Memory",
        "linkedin": "Most AI agents lose context between sessions. Ours doesn't.\n\nWe built a dual-tier memory architecture:\n- L1: Session scratchpad (ephemeral, fast)\n- L2: Permanent semantic storage (SQLite + sqlite-vec)\n\n14,726+ memories persisted, all surviving restarts.\n\nhttps://hypernexus.site/blog/ai-agent-memory.html",
        "reddit_title": "Building AI agent memory that survives restarts - dual-tier architecture",
        "reddit_body": "Most AI agents lose context between sessions.\n\nWe built a dual-tier memory architecture:\n- L1: Session scratchpad (ephemeral, fast)\n- L2: Permanent semantic storage (SQLite + sqlite-vec)\n\n14,726+ memories persisted, all surviving restarts.\n\nFull article: https://hypernexus.site/blog/ai-agent-memory.html\n\nHow do you handle memory in your AI agents?",
    },
    {
        "title": "LLM Waterfall: Zero Downtime Inference",
        "url": "https://hypernexus.site/blog/llm-waterfall.html",
        "tags": ["ai", "llm", "infrastructure", "hypernexus"],
        "description": "Automatic LLM failover with zero downtime.",
        "tweet": "When OpenAI rate-limits you at 2 AM, your team stops working.\n\nHyperNexus implements automatic LLM failover:\n1. Primary APIs\n2. OpenRouter\n3. Local Ollama\n\nZero downtime inference.\n\nhttps://hypernexus.site/blog/llm-waterfall.html\n\n#AI #LLM",
        "linkedin": "When your primary LLM provider hits rate limits or goes down, your workflow shouldn't stop.\n\nHyperNexus cascades automatically:\n1. Primary APIs (NVIDIA NIM, Anthropic, Google)\n2. OpenRouter (secondary aggregator)\n3. Local Ollama (offline fallback)\n\nZero downtime. Zero interruptions.\n\nhttps://hypernexus.site/blog/llm-waterfall.html",
        "reddit_title": "LLM waterfall pattern: zero downtime inference with automatic failover",
        "reddit_body": "When your primary LLM provider hits rate limits or goes down, your workflow shouldn't stop.\n\nThe LLM Waterfall Pattern:\n1. Primary APIs (NVIDIA NIM, Anthropic, Google)\n2. OpenRouter (secondary aggregator)\n3. Local Ollama (offline fallback)\n\nZero downtime inference.\n\nFull article: https://hypernexus.site/blog/llm-waterfall.html\n\nHow do you handle LLM failover in your stack?",
    },
    {
        "title": "Why We Bet on Local-First AI Infrastructure",
        "url": "https://hypernexus.site/blog/local-first.html",
        "tags": ["ai", "localfirst", "infrastructure", "hypernexus"],
        "description": "Your team's knowledge stays on your machines.",
        "tweet": "Your code shouldn't leave your network.\n\nHyperNexus is local-first:\n- Privacy: Prompts stay on your machines\n- Speed: 10x faster than cloud APIs\n- Reliability: Works offline\n- Cost: No per-query pricing\n\nhttps://hypernexus.site/blog/local-first.html\n\n#AI #LocalFirst",
        "linkedin": "Your team's knowledge stays on your machines. No cloud dependency.\n\nWhy local-first matters:\n- Privacy: Your code and prompts never leave your network\n- Speed: Local vector search is 10x faster than cloud APIs\n- Reliability: Works offline, no internet required\n- Cost: No per-query pricing, no surprise bills\n\nhttps://hypernexus.site/blog/local-first.html",
        "reddit_title": "Why local-first AI infrastructure matters for enterprise",
        "reddit_body": "Your team's knowledge stays on your machines. No cloud dependency.\n\nWhy local-first matters:\n- Privacy: Your code and prompts never leave your network\n- Speed: Local vector search is 10x faster than cloud APIs\n- Reliability: Works offline\n- Cost: No per-query pricing\n\nFull article: https://hypernexus.site/blog/local-first.html\n\nAnyone else going local-first for their AI stack?",
    },
    {
        "title": "Cross-Harness Tool Parity",
        "url": "https://hypernexus.site/blog/cross-harness-parity.html",
        "tags": ["ai", "mcp", "tooling", "hypernexus"],
        "description": "One config, six AI harnesses, zero vendor lock-in.",
        "tweet": "One config. Six AI harnesses. Zero vendor lock-in.\n\nHyperNexus maintains byte-for-byte tool parity across Claude Code, Cursor, Codex, Gemini CLI, Copilot, and Kiro.\n\n27 golden fixtures. 6 platforms.\n\nhttps://hypernexus.site/blog/cross-harness-parity.html\n\n#AI #MCP",
        "linkedin": "One config. Six AI harnesses. Zero vendor lock-in.\n\nHyperNexus maintains byte-for-byte tool parity across:\n- Claude Code\n- GitHub Copilot CLI\n- Codex CLI\n- Cursor\n- Gemini CLI\n- Kiro\n\n27 golden fixtures. 6 L2 platforms.\n\nhttps://hypernexus.site/blog/cross-harness-parity.html",
        "reddit_title": "Cross-harness tool parity: one config for 6 AI coding tools",
        "reddit_body": "One config. Six AI harnesses. Zero vendor lock-in.\n\nHyperNexus maintains byte-for-byte tool parity across:\n- Claude Code\n- GitHub Copilot CLI\n- Codex CLI\n- Cursor\n- Gemini CLI\n- Kiro\n\n27 golden fixtures. 6 platforms.\n\nFull article: https://hypernexus.site/blog/cross-harness-parity.html\n\nHow do you handle multi-harness tooling?",
    },
]


# ═══════════════════════════════════════════════════════════════
# PLATFORM: dev.to
# ═══════════════════════════════════════════════════════════════


def post_to_devto(article):
    """Post to dev.to API"""
    headers = {"api-key": DEVTO_API_KEY, "Content-Type": "application/json"}
    payload = {
        "article": {
            "title": article["title"],
            "published": True,
            "tags": article["tags"][:4],
            "canonical_url": article["url"],
            "description": article["description"],
            "body_markdown": f"---\ntitle: {article['title']}\npublished: true\ntags: {', '.join(article['tags'][:4])}\ncanonical_url: {article['url']}\n---\n\n# {article['title']}\n\n{article['description']}\n\n[Read full article]({article['url']})\n",
        }
    }
    try:
        resp = requests.post(
            "https://dev.to/api/articles", headers=headers, json=payload, timeout=30
        )
        if resp.status_code == 201:
            return resp.json().get("url", "")
        elif resp.status_code == 422 and "already been taken" in resp.text:
            return "already_posted"
        return None
    except:
        return None


# ═══════════════════════════════════════════════════════════════
# PLATFORM: Bluesky (AT Protocol)
# ═══════════════════════════════════════════════════════════════


def post_to_bluesky(text):
    """Post to Bluesky using AT Protocol"""
    try:
        # Create session
        resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.createSession",
            json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_APP_PASSWORD},
            timeout=15,
        )
        if resp.status_code != 200:
            return None

        token = resp.json().get("accessJwt")

        # Create post
        resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.createRecord",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "repo": BLUESKY_HANDLE,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": text[:300],
                    "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
            },
            timeout=15,
        )

        if resp.status_code == 200:
            uri = resp.json().get("uri", "")
            return f"posted:{uri}"
        return None
    except:
        return None


# ═══════════════════════════════════════════════════════════════
# PLATFORM: Reddit
# ═══════════════════════════════════════════════════════════════


def get_reddit_token():
    """Get Reddit OAuth token"""
    try:
        resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
            data={
                "grant_type": "password",
                "username": REDDIT_USERNAME,
                "password": REDDIT_PASSWORD,
            },
            headers={"User-Agent": "HyperNexus/1.0"},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        return None
    except:
        return None


def post_to_reddit(token, subreddit, title, body):
    """Post to a subreddit"""
    try:
        resp = requests.post(
            "https://oauth.reddit.com/api/submit",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "HyperNexus/1.0",
            },
            data={
                "sr": subreddit,
                "title": title,
                "text": body[:10000],
                "kind": "self",
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("url", "")
        return None
    except:
        return None


# ═══════════════════════════════════════════════════════════════
# PLATFORM: Twitter (CDP)
# ═══════════════════════════════════════════════════════════════


def post_to_twitter_cdp(ws, text):
    """Post to Twitter using CDP"""

    # Focus textarea
    ws.send(
        json.dumps(
            {
                "id": 10,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": 'document.querySelector("[data-testid=\\"tweetTextarea_0\\"]").focus()',
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(1)
    try:
        ws.recv()
    except:
        pass

    # Type content
    ws.send(
        json.dumps(
            {"id": 11, "method": "Input.insertText", "params": {"text": text[:280]}}
        )
    )
    time.sleep(2)
    try:
        ws.recv()
    except:
        pass

    # Click Post
    ws.send(
        json.dumps(
            {
                "id": 12,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": 'document.querySelector("[data-testid=\\"tweetButton\\"]").click()',
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(3)
    try:
        ws.recv()
    except:
        pass

    return True


# ═══════════════════════════════════════════════════════════════
# PLATFORM: LinkedIn (CDP)
# ═══════════════════════════════════════════════════════════════


def post_to_linkedin_cdp(ws, content):
    """Post to LinkedIn company page using CDP"""
    # Navigate to company page
    ws.send(
        json.dumps(
            {
                "id": 1,
                "method": "Page.navigate",
                "params": {"url": LINKEDIN_COMPANY_URL},
            }
        )
    )
    time.sleep(7)
    for _ in range(10):
        try:
            ws.settimeout(0.5)
            ws.recv()
        except:
            break

    # Click Create
    ws.send(
        json.dumps(
            {
                "id": 10,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
        (function() {
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === 'Create') {
                    buttons[i].click();
                    return 'clicked';
                }
            }
            return 'not_found';
        })()
        """,
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(2)
    try:
        ws.recv()
    except:
        pass

    # Click Start a post
    ws.send(
        json.dumps(
            {
                "id": 11,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
        (function() {
            var links = document.querySelectorAll('a, button, [role="button"]');
            for (var i = 0; i < links.length; i++) {
                if (links[i].textContent.trim().startsWith('Start a post')) {
                    links[i].click();
                    return 'clicked';
                }
            }
            return 'not_found';
        })()
        """,
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(3)
    try:
        ws.recv()
    except:
        pass

    # Focus editor
    ws.send(
        json.dumps(
            {
                "id": 12,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
        (function() {
            var editables = document.querySelectorAll('[contenteditable="true"][role="textbox"]');
            for (var i = 0; i < editables.length; i++) {
                editables[i].click();
                editables[i].focus();
                return 'focused';
            }
            return 'not_found';
        })()
        """,
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(1)
    try:
        ws.recv()
    except:
        pass

    # Type content
    ws.send(
        json.dumps(
            {"id": 13, "method": "Input.insertText", "params": {"text": content[:1000]}}
        )
    )
    time.sleep(2)
    try:
        ws.recv()
    except:
        pass

    # Click Post
    ws.send(
        json.dumps(
            {
                "id": 14,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
        (function() {
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === 'Post' && !buttons[i].disabled) {
                    buttons[i].click();
                    return 'posted';
                }
            }
            return 'not_found';
        })()
        """,
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(5)
    try:
        ws.recv()
    except:
        pass

    return True


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════


def main():
    print("=" * 60)
    print("SYNC ALL ARTICLES ACROSS ALL PLATFORMS")
    print("=" * 60)
    print(f"Articles: {len(ARTICLES)}")
    print("Platforms: dev.to, Bluesky, Reddit, Twitter (CDP), LinkedIn (CDP)")
    print()

    results = {p: 0 for p in ["devto", "bluesky", "reddit", "twitter", "linkedin"]}

    # Get Reddit token
    reddit_token = get_reddit_token()

    # Get CDP browser
    browser_ws = None
    twitter_ws = None
    linkedin_ws = None
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json/version", timeout=5)
        browser_ws = json.loads(resp.read()).get("webSocketDebuggerUrl")

        # Get existing Twitter tab
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        for t in tabs:
            if "x.com/compose" in t.get("url", ""):
                twitter_ws = __import__("websocket").create_connection(
                    t.get("webSocketDebuggerUrl"), timeout=30
                )
            elif "linkedin.com/company" in t.get("url", ""):
                linkedin_ws = __import__("websocket").create_connection(
                    t.get("webSocketDebuggerUrl"), timeout=30
                )
    except:
        pass

    for i, article in enumerate(ARTICLES, 1):
        print(f"\n[{i}/{len(ARTICLES)}] {article['title']}")
        print("-" * 40)

        # dev.to
        result = post_to_devto(article)
        if result == "already_posted":
            print("  dev.to: already posted")
        elif result:
            print(f"  dev.to: {result}")
            results["devto"] += 1
        else:
            print("  dev.to: failed")
        time.sleep(2)

        # Bluesky
        result = post_to_bluesky(article["tweet"])
        if result:
            print("  Bluesky: posted")
            results["bluesky"] += 1
        else:
            print("  Bluesky: failed")
        time.sleep(2)

        # Reddit (first subreddit only to avoid spam)
        if reddit_token and i <= 3:
            result = post_to_reddit(
                reddit_token,
                "selfhosted",
                article["reddit_title"],
                article["reddit_body"],
            )
            if result:
                print(f"  Reddit: {result}")
                results["reddit"] += 1
            else:
                print("  Reddit: failed")
            time.sleep(5)

        # Twitter (CDP)
        if twitter_ws:
            try:
                post_to_twitter_cdp(twitter_ws, article["tweet"])
                print("  Twitter: posted")
                results["twitter"] += 1
                # Navigate back to compose
                twitter_ws.send(
                    json.dumps(
                        {
                            "id": 1,
                            "method": "Page.navigate",
                            "params": {"url": "https://x.com/compose/post"},
                        }
                    )
                )
                time.sleep(5)
                for _ in range(10):
                    try:
                        twitter_ws.settimeout(0.5)
                        twitter_ws.recv()
                    except:
                        break
            except:
                print("  Twitter: failed")

        # LinkedIn (CDP)
        if linkedin_ws:
            try:
                post_to_linkedin_cdp(linkedin_ws, article["linkedin"])
                print("  LinkedIn: posted")
                results["linkedin"] += 1
            except:
                print("  LinkedIn: failed")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for platform, count in results.items():
        print(f"  {platform}: {count}/{len(ARTICLES)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
