#!/usr/bin/env python3
"""
Post new HyperNexus articles to dev.to
"""
import requests

DEVTO_API_KEY = "acWJBPGAFfSb4VeMAmgp5SWr"
headers = {"api-key": DEVTO_API_KEY, "Content-Type": "application/json"}

NEW_ARTICLES = [
    {
        "title": "Harden Your Self-Hosted AI: A Practical Checklist for TLS, Auth, and Network Isolation",
        "url": "https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html",
        "tags": ["ai", "security", "selfhosted", "hypernexus"],
        "description": "A comprehensive security checklist for self-hosted AI deployments covering TLS configuration, authentication, and network isolation best practices."
    },
    {
        "title": "The CISO's Uncompromising Checklist for Agentic AI Governance",
        "url": "https://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html",
        "tags": ["ai", "security", "governance", "hypernexus"],
        "description": "SSO, RBAC, and immutable audits - what every CISO should demand before deploying agentic AI systems in production."
    },
    {
        "title": "Zero Trust AI Architecture: Authenticating Every Tool Call, Memory Access, and Model Request",
        "url": "https://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html",
        "tags": ["ai", "security", "zerotrust", "hypernexus"],
        "description": "How to implement zero trust principles in AI systems - every request authenticated, every access logged, every action verified."
    },
    {
        "title": "Securing Self-Hosted AI: Localhost Isolation with TLS and Nginx",
        "url": "https://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html",
        "tags": ["ai", "security", "nginx", "hypernexus"],
        "description": "Practical guide to securing self-hosted AI infrastructure using localhost isolation, TLS termination, and Nginx reverse proxy."
    },
    {
        "title": "Hardening Self-Hosted AI: The 4-Point TLS and Zero Trust Checklist",
        "url": "https://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html",
        "tags": ["ai", "security", "zerotrust", "hypernexus"],
        "description": "Four essential security controls for hardening self-hosted AI deployments against common attack vectors."
    },
    {
        "title": "What Your CISO Should Demand Before Deploying Agentic AI",
        "url": "https://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html",
        "tags": ["ai", "governance", "enterprise", "hypernexus"],
        "description": "A practical governance checklist for enterprise AI deployments - compliance, security, and operational requirements."
    }
]

print(f"Posting {len(NEW_ARTICLES)} articles to dev.to...")
print()

for i, article in enumerate(NEW_ARTICLES, 1):
    payload = {
        "article": {
            "title": article["title"],
            "published": True,
            "tags": article["tags"],
            "canonical_url": article["url"],
            "description": article["description"],
            "body_markdown": f"""---
title: {article['title']}
published: true
tags: {', '.join(article['tags'])}
canonical_url: {article['url']}
---

# {article['title']}

{article['description']}

Read the full article on [hypernexus.site]({article['url']})

*Originally published on [hypernexus.site](https://hypernexus.site)*
"""
        }
    }
    
    try:
        response = requests.post("https://dev.to/api/articles", headers=headers, json=payload, timeout=30)
        if response.status_code == 201:
            result = response.json()
            print(f"[{i}/{len(NEW_ARTICLES)}] Published: {result['url']}")
        elif response.status_code == 429:
            print(f"[{i}/{len(NEW_ARTICLES)}] Rate limited - waiting...")
            import time
            time.sleep(10)
            # Retry
            response = requests.post("https://dev.to/api/articles", headers=headers, json=payload, timeout=30)
            if response.status_code == 201:
                result = response.json()
                print(f"[{i}/{len(NEW_ARTICLES)}] Published (retry): {result['url']}")
            else:
                print(f"[{i}/{len(NEW_ARTICLES)}] Error {response.status_code}: {response.text[:100]}")
        else:
            print(f"[{i}/{len(NEW_ARTICLES)}] Error {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"[{i}/{len(NEW_ARTICLES)}] Exception: {e}")
    
    # Small delay between posts
    import time
    time.sleep(2)

print()
print("Done!")
