#!/usr/bin/env python3
"""
Post articles to Hashnode using new API key
"""
import requests
import json
import time

HASHNODE_API_KEY = "f022d11a-e4a7-4428-b51c-d7a2e98b815a"
HASHNODE_PUBLICATION_ID = "6a53bf6ef03768644714afbe"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": HASHNODE_API_KEY
}

# All articles to post
ARTICLES = [
    {
        "title": "Harden Your Self-Hosted AI: A Practical Checklist for TLS, Auth, and Network Isolation",
        "url": "https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html",
        "tags": ["ai", "security", "selfhosted", "devops"],
        "description": "A comprehensive security checklist for self-hosted AI deployments covering TLS configuration, authentication, and network isolation best practices."
    },
    {
        "title": "The CISO's Uncompromising Checklist for Agentic AI Governance",
        "url": "https://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html",
        "tags": ["ai", "security", "governance", "enterprise"],
        "description": "SSO, RBAC, and immutable audits - what every CISO should demand before deploying agentic AI systems in production."
    },
    {
        "title": "Zero Trust AI Architecture: Authenticating Every Tool Call, Memory Access, and Model Request",
        "url": "https://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html",
        "tags": ["ai", "security", "zerotrust", "architecture"],
        "description": "How to implement zero trust principles in AI systems - every request authenticated, every access logged, every action verified."
    },
    {
        "title": "Securing Self-Hosted AI: Localhost Isolation with TLS and Nginx",
        "url": "https://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html",
        "tags": ["ai", "security", "nginx", "selfhosted"],
        "description": "Practical guide to securing self-hosted AI infrastructure using localhost isolation, TLS termination, and Nginx reverse proxy."
    },
    {
        "title": "Hardening Self-Hosted AI: The 4-Point TLS and Zero Trust Checklist",
        "url": "https://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html",
        "tags": ["ai", "security", "zerotrust", "checklist"],
        "description": "Four essential security controls for hardening self-hosted AI deployments against common attack vectors."
    },
    {
        "title": "What Your CISO Should Demand Before Deploying Agentic AI",
        "url": "https://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html",
        "tags": ["ai", "governance", "enterprise", "ciso"],
        "description": "A practical governance checklist for enterprise AI deployments - compliance, security, and operational requirements."
    }
]

def create_post(article):
    """Create a post on Hashnode"""
    query = """
    mutation CreatePublicationPost($input: CreatePublicationPostInput!) {
        createPublicationPost(input: $input) {
            post {
                id
                slug
                url
            }
        }
    }
    """
    
    variables = {
        "input": {
            "title": article["title"],
            "contentMarkdown": f"""# {article['title']}

{article['description']}

Read the full article on [hypernexus.site]({article['url']})

*Originally published on [hypernexus.site](https://hypernexus.site)*
""",
            "tags": [{"name": t, "slug": t} for t in article["tags"][:5]],
            "publicationId": HASHNODE_PUBLICATION_ID,
            "originalArticleURL": article["url"],
            "metaTags": {
                "title": article["title"],
                "description": article["description"]
            }
        }
    }
    
    try:
        response = requests.post(
            "https://api.hashnode.com",
            headers=HEADERS,
            json={"query": query, "variables": variables},
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"errors": [{"message": str(e)}]}

def main():
    print(f"Posting {len(ARTICLES)} articles to Hashnode...")
    print(f"Publication ID: {HASHNODE_PUBLICATION_ID}")
    print()
    
    success = 0
    for i, article in enumerate(ARTICLES, 1):
        print(f"[{i}/{len(ARTICLES)}] {article['title'][:60]}...")
        
        result = create_post(article)
        
        if "data" in result and "createPublicationPost" in result["data"]:
            post = result["data"]["createPublicationPost"]["post"]
            print(f"  Published: {post['url']}")
            success += 1
        elif "errors" in result:
            print(f"  Error: {result['errors'][0]['message'][:100]}")
        else:
            print(f"  Unknown: {json.dumps(result)[:100]}")
        
        time.sleep(2)
    
    print()
    print(f"Results: {success}/{len(ARTICLES)} posted")
    print("=" * 60)

if __name__ == "__main__":
    main()
