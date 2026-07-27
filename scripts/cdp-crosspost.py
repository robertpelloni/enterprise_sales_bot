#!/usr/bin/env python3
"""
Cross-post articles to LinkedIn, Twitter, Hashnode, and Medium using Playwright CDP.
Same approach as the marketing agent's go-rod implementation.
"""
import asyncio
from playwright.async_api import async_playwright

# Credentials
LINKEDIN_USERNAME = "pelloni.robert@gmail.com"
LINKEDIN_PASSWORD = "Temppass.0"
LINKEDIN_COMPANY_URL = "https://www.linkedin.com/company/hypernexusllc/admin/page-posts/"

# Articles to post
ARTICLES = [
    {
        "title": "Harden Your Self-Hosted AI: A Practical Checklist for TLS, Auth, and Network Isolation",
        "url": "https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html",
        "linkedin": "Your self-hosted AI is probably not as secure as you think.\n\nHere's a practical checklist we use at HyperNexus:\n\n1. TLS everywhere - even on localhost\n2. Network isolation - separate VLANs for AI services\n3. Auth on every endpoint - no anonymous access\n4. Audit logging - every action tracked\n\nFull checklist with implementation details:\nhttps://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html",
        "twitter": "Your self-hosted AI is probably not as secure as you think.\n\nPractical checklist:\n1. TLS everywhere\n2. Network isolation\n3. Auth on every endpoint\n4. Audit logging\n\nHyperNexus ships with all four by default.\n\nhttps://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html"
    },
    {
        "title": "The CISO's Uncompromising Checklist for Agentic AI Governance",
        "url": "https://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html",
        "linkedin": "What should your CISO demand before deploying agentic AI?\n\nThe non-negotiables:\n- SSO integration (no local passwords)\n- RBAC with least-privilege defaults\n- Immutable audit logs (append-only)\n- Data residency controls\n- Kill switch for autonomous actions\n\nHyperNexus checks every box.\n\nFull governance checklist:\nhttps://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html",
        "twitter": "What should your CISO demand before deploying agentic AI?\n\nNon-negotiables:\n- SSO integration\n- RBAC with least-privilege\n- Immutable audit logs\n- Kill switch for autonomous actions\n\nHyperNexus checks every box.\n\nhttps://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html"
    },
    {
        "title": "Zero Trust AI Architecture: Authenticating Every Tool Call, Memory Access, and Model Request",
        "url": "https://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html",
        "linkedin": "Zero trust isn't just for networks anymore.\n\nIn agentic AI, you need to authenticate:\n- Every tool call\n- Every memory access\n- Every model request\n- Every context injection\n\nOne unauthenticated path = complete compromise.\n\nHow HyperNexus implements zero trust for AI:\nhttps://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html",
        "twitter": "Zero trust for AI means authenticating:\n- Every tool call\n- Every memory access\n- Every model request\n- Every context injection\n\nOne unauthenticated path = complete compromise.\n\nhttps://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html"
    },
    {
        "title": "Securing Self-Hosted AI: Localhost Isolation with TLS and Nginx",
        "url": "https://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html",
        "linkedin": "The simplest security improvement for self-hosted AI:\n\nBind to localhost + Nginx reverse proxy with TLS.\n\nWhy it works:\n- AI services never exposed to network\n- TLS terminates at Nginx\n- Single point for auth/rate limiting\n- Easy to add WAF rules\n\nStep-by-step guide:\nhttps://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html",
        "twitter": "Simplest security improvement for self-hosted AI:\n\nBind to localhost + Nginx reverse proxy with TLS.\n\n- AI services never exposed to network\n- TLS terminates at Nginx\n- Single point for auth/rate limiting\n\nhttps://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html"
    },
    {
        "title": "Hardening Self-Hosted AI: The 4-Point TLS & Zero Trust Checklist",
        "url": "https://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html",
        "linkedin": "4 security controls that block 90% of attacks on self-hosted AI:\n\n1. TLS 1.3 everywhere (no exceptions)\n2. mTLS for service-to-service\n3. Token-based auth (no API keys in URLs)\n4. Network segmentation (AI on isolated VLAN)\n\nImplement all four in under an hour:\nhttps://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html",
        "twitter": "4 security controls that block 90% of attacks on self-hosted AI:\n\n1. TLS 1.3 everywhere\n2. mTLS for service-to-service\n3. Token-based auth\n4. Network segmentation\n\nhttps://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html"
    },
    {
        "title": "What Your CISO Should Demand Before Deploying Agentic AI",
        "url": "https://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html",
        "linkedin": "Before your org deploys agentic AI, your CISO should demand:\n\n1. Data flow mapping (where does training data go?)\n2. Access controls (who can invoke what?)\n3. Incident response (how to revoke AI access?)\n4. Compliance evidence (SOC2, HIPAA, GDPR)\n5. Vendor security review (supply chain)\n\nFull checklist with templates:\nhttps://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html",
        "twitter": "Before deploying agentic AI, your CISO should demand:\n\n1. Data flow mapping\n2. Access controls\n3. Incident response plan\n4. Compliance evidence\n5. Vendor security review\n\nFull checklist:\nhttps://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html"
    }
]

async def post_to_linkedin(page, content):
    """Post to LinkedIn company page using go-rod style automation"""
    try:
        print("  Navigating to LinkedIn company page...")
        await page.goto(LINKEDIN_COMPANY_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        
        # Check if we need to login
        if "login" in page.url:
            print("  Logging in to LinkedIn...")
            await page.fill('#username', LINKEDIN_USERNAME)
            await page.fill('#password', LINKEDIN_PASSWORD)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(3)
            
            # Navigate to company page again
            await page.goto(LINKEDIN_COMPANY_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
        
        # Look for "Start a post" button
        print("  Looking for post button...")
        start_post = await page.query_selector('button:has-text("Start a post"), button:has-text("Create a post")')
        if start_post:
            await start_post.click()
            await asyncio.sleep(2)
            
            # Wait for the post modal
            print("  Writing post content...")
            editor = await page.query_selector('.share-box-feed-entry__contenteditable, .ql-editor, [contenteditable="true"]')
            if editor:
                await editor.click()
                await page.keyboard.type(content[:1000], delay=10)
                await asyncio.sleep(1)
                
                # Click Post button
                post_btn = await page.query_selector('button:has-text("Post"):not(:has-text("Cancel"))')
                if post_btn:
                    await post_btn.click()
                    await asyncio.sleep(3)
                    print("  Posted to LinkedIn!")
                    return True
        
        print("  Could not find post button")
        return False
    except Exception as e:
        print(f"  LinkedIn error: {e}")
        return False

async def post_to_twitter(page, content):
    """Post to Twitter/X using go-rod style automation"""
    try:
        print("  Navigating to Twitter...")
        await page.goto("https://x.com/compose/post", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        
        # Check if we need to login
        if "login" in page.url or "i/flow" in page.url:
            print("  Login required - skipping (needs manual login)")
            return False
        
        # Look for tweet composer
        print("  Looking for tweet composer...")
        editor = await page.query_selector('[data-testid="tweetTextarea_0"], [contenteditable="true"]')
        if editor:
            await editor.click()
            await page.keyboard.type(content[:280], delay=10)
            await asyncio.sleep(1)
            
            # Click Tweet button
            tweet_btn = await page.query_selector('[data-testid="tweetButton"], button:has-text("Post")')
            if tweet_btn:
                await tweet_btn.click()
                await asyncio.sleep(3)
                print("  Posted to Twitter!")
                return True
        
        print("  Could not find tweet composer")
        return False
    except Exception as e:
        print(f"  Twitter error: {e}")
        return False

async def post_to_hashnode(page, title, content):
    """Post to Hashnode using go-rod style automation"""
    try:
        print("  Navigating to Hashnode...")
        await page.goto("https://hashnode.com", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        
        # Check if logged in
        sign_in = await page.query_selector('a:has-text("Sign in")')
        if sign_in:
            print("  Login required - skipping (needs manual login)")
            return False
        
        # Click Write
        write_btn = await page.query_selector('a:has-text("Write")')
        if write_btn:
            await write_btn.click()
            await asyncio.sleep(3)
            
            # Fill title
            title_input = await page.query_selector('input[placeholder*="title"], textarea[placeholder*="title"]')
            if title_input:
                await title_input.fill(title)
                await asyncio.sleep(1)
            
            # Fill content
            editor = await page.query_selector('.ProseMirror, [contenteditable="true"]')
            if editor:
                await editor.click()
                await page.keyboard.type(content[:2000], delay=5)
                await asyncio.sleep(1)
                
                # Click Publish
                publish_btn = await page.query_selector('button:has-text("Publish")')
                if publish_btn:
                    await publish_btn.click()
                    await asyncio.sleep(3)
                    print("  Posted to Hashnode!")
                    return True
        
        print("  Could not find editor")
        return False
    except Exception as e:
        print(f"  Hashnode error: {e}")
        return False

async def main():
    print("=" * 60)
    print("CROSS-POSTING TO ALL PLATFORMS (CDP)")
    print("=" * 60)
    print()
    
    async with async_playwright() as p:
        # Launch browser (headless=True for server, headless=False for debugging)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # Create pages for each platform
        linkedin_page = await context.new_page()
        twitter_page = await context.new_page()
        hashnode_page = await context.new_page()
        
        # Post to LinkedIn
        print("=" * 60)
        print("LINKEDIN (HyperNexus Company Page)")
        print("=" * 60)
        
        linkedin_success = 0
        for i, article in enumerate(ARTICLES[:3], 1):  # Start with 3 articles
            print(f"\n[{i}/3] {article['title'][:50]}...")
            if await post_to_linkedin(linkedin_page, article["linkedin"]):
                linkedin_success += 1
            await asyncio.sleep(5)
        
        print(f"\nLinkedIn: {linkedin_success}/3 posted")
        
        # Post to Twitter
        print("\n" + "=" * 60)
        print("TWITTER/X (@HyperNexusLLC)")
        print("=" * 60)
        
        twitter_success = 0
        for i, article in enumerate(ARTICLES[:3], 1):  # Start with 3 articles
            print(f"\n[{i}/3] {article['title'][:50]}...")
            if await post_to_twitter(twitter_page, article["twitter"]):
                twitter_success += 1
            await asyncio.sleep(5)
        
        print(f"\nTwitter: {twitter_success}/3 posted")
        
        # Post to Hashnode
        print("\n" + "=" * 60)
        print("HASHNODE")
        print("=" * 60)
        
        hashnode_success = 0
        for i, article in enumerate(ARTICLES[:3], 1):  # Start with 3 articles
            print(f"\n[{i}/3] {article['title'][:50]}...")
            if await post_to_hashnode(hashnode_page, article["title"], article["linkedin"]):
                hashnode_success += 1
            await asyncio.sleep(5)
        
        print(f"\nHashnode: {hashnode_success}/3 posted")
        
        # Keep browser open for debugging
        print("\n" + "=" * 60)
        print("Browser will stay open for 60 seconds for debugging...")
        print("=" * 60)
        await asyncio.sleep(60)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
