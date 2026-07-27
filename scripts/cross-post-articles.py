#!/usr/bin/env python3
"""
Cross-post HyperNexus articles to multiple platforms using CDP
"""

import os

# New articles to cross-post (not yet on dev.to)
NEW_ARTICLES = [
    {
        "title": "Harden Your Self-Hosted AI: A Practical Checklist for TLS, Auth, and Network Isolation",
        "url": "https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html",
        "tags": ["ai", "security", "selfhosted", "hypernexus"],
        "description": "A comprehensive security checklist for self-hosted AI deployments covering TLS configuration, authentication, and network isolation best practices.",
    },
    {
        "title": "The CISO's Uncompromising Checklist for Agentic AI Governance",
        "url": "https://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html",
        "tags": ["ai", "security", "governance", "hypernexus"],
        "description": "SSO, RBAC, and immutable audits — what every CISO should demand before deploying agentic AI systems in production.",
    },
    {
        "title": "Zero Trust AI Architecture: Authenticating Every Tool Call, Memory Access, and Model Request",
        "url": "https://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html",
        "tags": ["ai", "security", "zerotrust", "hypernexus"],
        "description": "How to implement zero trust principles in AI systems — every request authenticated, every access logged, every action verified.",
    },
    {
        "title": "Securing Self-Hosted AI: Localhost Isolation with TLS and Nginx",
        "url": "https://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html",
        "tags": ["ai", "security", "nginx", "hypernexus"],
        "description": "Practical guide to securing self-hosted AI infrastructure using localhost isolation, TLS termination, and Nginx reverse proxy.",
    },
    {
        "title": "Hardening Self-Hosted AI: The 4-Point TLS & Zero Trust Checklist",
        "url": "https://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html",
        "tags": ["ai", "security", "zerotrust", "hypernexus"],
        "description": "Four essential security controls for hardening self-hosted AI deployments against common attack vectors.",
    },
    {
        "title": "What Your CISO Should Demand Before Deploying Agentic AI",
        "url": "https://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html",
        "tags": ["ai", "governance", "enterprise", "hypernexus"],
        "description": "A practical governance checklist for enterprise AI deployments — compliance, security, and operational requirements.",
    },
]

# Platform configs
PLATFORMS = {
    "devto": {
        "name": "dev.to",
        "api_url": "https://dev.to/api/articles",
        "api_key_env": "DEVTO_API_KEY",
        "max_tags": 4,
    },
    "hashnode": {
        "name": "Hashnode",
        "api_url": "https://api.hashnode.com",
        "api_key_env": "HASHNODE_API_KEY",
        "publication_id_env": "HASHNODE_PUBLICATION_ID",
    },
    "medium": {
        "name": "Medium",
        "api_url": "https://api.medium.com/v1",
        "api_key_env": "MEDIUM_API_KEY",
        "author_id_env": "MEDIUM_AUTHOR_ID",
    },
}


def generate_devto_article(article):
    """Generate dev.to article payload"""
    return {
        "article": {
            "title": article["title"],
            "published": True,
            "tags": article["tags"][:4],  # dev.to max 4 tags
            "canonical_url": article["url"],
            "description": article["description"],
            "body_markdown": f"""---
title: {article["title"]}
published: true
tags: {", ".join(article["tags"][:4])}
canonical_url: {article["url"]}
---

# {article["title"]}

{article["description"]}

Read the full article on [hypernexus.site]({article["url"]})

*Originally published on [hypernexus.site](https://hypernexus.site)*
""",
        }
    }


def generate_hashnode_article(article, publication_id):
    """Generate Hashnode article payload"""
    return {
        "query": """
        mutation CreatePublicationPost($input: CreatePublicationPostInput!) {
            createPublicationPost(input: $input) {
                post {
                    id
                    slug
                    url
                }
            }
        }
        """,
        "variables": {
            "input": {
                "title": article["title"],
                "contentMarkdown": f"""# {article["title"]}

{article["description"]}

Read the full article on [hypernexus.site]({article["url"]})

*Originally published on [hypernexus.site](https://hypernexus.site)*
""",
                "tags": [{"name": t, "slug": t} for t in article["tags"][:5]],
                "publicationId": publication_id,
                "originalArticleURL": article["url"],
                "metaTags": {
                    "title": article["title"],
                    "description": article["description"],
                },
            }
        },
    }


def generate_medium_article(article, author_id):
    """Generate Medium article payload"""
    return {
        "title": article["title"],
        "contentFormat": "markdown",
        "content": f"""# {article["title"]}

{article["description"]}

Read the full article on [hypernexus.site]({article["url"]})

*Originally published on [hypernexus.site](https://hypernexus.site)*
""",
        "tags": article["tags"][:5],
        "canonicalUrl": article["url"],
        "publishStatus": "public",
    }


def main():
    print("=" * 60)
    print("CROSS-POST ARTICLES TO ALL PLATFORMS")
    print("=" * 60)
    print()

    # Check for API keys
    devto_key = os.environ.get("DEVTO_API_KEY", "")
    hashnode_key = os.environ.get("HASHNODE_API_KEY", "")
    hashnode_pub = os.environ.get("HASHNODE_PUBLICATION_ID", "")
    medium_key = os.environ.get("MEDIUM_API_KEY", "")
    medium_author = os.environ.get("MEDIUM_AUTHOR_ID", "")

    print("Platform Status:")
    print(f"  dev.to: {'[OK] API key found' if devto_key else '[FAIL] No API key'}")
    print(f"  Hashnode: {'[OK] API key found' if hashnode_key else '[FAIL] No API key'}")
    print(f"  Medium: {'[OK] API key found' if medium_key else '[FAIL] No API key'}")
    print()

    print(f"Articles to cross-post: {len(NEW_ARTICLES)}")
    for i, article in enumerate(NEW_ARTICLES, 1):
        print(f"  {i}. {article['title']}")
    print()

    # Generate payloads for each platform
    print("Generated Payloads:")
    print()

    if devto_key:
        print("=== dev.to Articles ===")
        for article in NEW_ARTICLES:
            payload = generate_devto_article(article)
            print(f"  - {article['title']}")
            print(f"    Tags: {', '.join(payload['article']['tags'])}")
            print(f"    URL: {article['url']}")
        print()

    if hashnode_key and hashnode_pub:
        print("=== Hashnode Articles ===")
        for article in NEW_ARTICLES:
            payload = generate_hashnode_article(article, hashnode_pub)
            print(f"  - {article['title']}")
            print(f"    Tags: {', '.join(article['tags'][:5])}")
        print()

    if medium_key:
        print("=== Medium Articles ===")
        for article in NEW_ARTICLES:
            payload = generate_medium_article(article, medium_author)
            print(f"  - {article['title']}")
            print(f"    Tags: {', '.join(payload['tags'])}")
        print()

    print("=" * 60)
    print("To post, set the API keys and run with --post flag")
    print("=" * 60)


if __name__ == "__main__":
    main()
