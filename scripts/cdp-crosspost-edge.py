#!/usr/bin/env python3
"""
Cross-post to LinkedIn and Twitter using CDP with Edge browser.
Same approach as HyperNexus/scripts/auto_linkedin_page.py
"""

import websocket
import json
import time
import urllib.request
import sys

# LinkedIn company page
LINKEDIN_COMPANY_URL = "https://www.linkedin.com/company/135697123/admin/"

# Articles to post
ARTICLES = [
    {
        "title": "Harden Your Self-Hosted AI",
        "linkedin": """Your self-hosted AI is probably not as secure as you think.

Here's a practical checklist we use at HyperNexus:

1. TLS everywhere - even on localhost
2. Network isolation - separate VLANs for AI services
3. Auth on every endpoint - no anonymous access
4. Audit logging - every action tracked

Full checklist with implementation details:
https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html

#AI #Security #SelfHosted #DevOps""",
        "twitter": """Your self-hosted AI is probably not as secure as you think.

Practical checklist:
1. TLS everywhere
2. Network isolation
3. Auth on every endpoint
4. Audit logging

HyperNexus ships with all four by default.

https://hypernexus.site/blog/harden-your-self-hosted-ai-a-practical-checklist-for-tls-auth-and-network-isolation.html

#AI #Security""",
    },
    {
        "title": "CISO's Checklist for Agentic AI",
        "linkedin": """What should your CISO demand before deploying agentic AI?

The non-negotiables:
- SSO integration (no local passwords)
- RBAC with least-privilege defaults
- Immutable audit logs (append-only)
- Data residency controls
- Kill switch for autonomous actions

HyperNexus checks every box.

Full governance checklist:
https://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html

#AI #Governance #Enterprise #CISO""",
        "twitter": """What should your CISO demand before deploying agentic AI?

Non-negotiables:
- SSO integration
- RBAC with least-privilege
- Immutable audit logs
- Kill switch for autonomous actions

HyperNexus checks every box.

https://hypernexus.site/blog/the-cisos-uncompromising-checklist-for-agentic-ai-governance-sso-rbac-and-immutable-audits.html

#AI #Enterprise""",
    },
    {
        "title": "Zero Trust AI Architecture",
        "linkedin": """Zero trust isn't just for networks anymore.

In agentic AI, you need to authenticate:
- Every tool call
- Every memory access
- Every model request
- Every context injection

One unauthenticated path = complete compromise.

How HyperNexus implements zero trust for AI:
https://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html

#AI #ZeroTrust #Security #Architecture""",
        "twitter": """Zero trust for AI means authenticating:
- Every tool call
- Every memory access
- Every model request
- Every context injection

One unauthenticated path = complete compromise.

https://hypernexus.site/blog/zero-trust-ai-architecture-authenticating-every-tool-call-memory-access-and-model-request.html

#AI #ZeroTrust""",
    },
    {
        "title": "Securing Self-Hosted AI with Nginx",
        "linkedin": """The simplest security improvement for self-hosted AI:

Bind to localhost + Nginx reverse proxy with TLS.

Why it works:
- AI services never exposed to network
- TLS terminates at Nginx
- Single point for auth/rate limiting
- Easy to add WAF rules

Step-by-step guide:
https://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html

#AI #Nginx #Security #SelfHosted""",
        "twitter": """Simplest security improvement for self-hosted AI:

Bind to localhost + Nginx reverse proxy with TLS.

- AI services never exposed to network
- TLS terminates at Nginx
- Single point for auth/rate limiting

https://hypernexus.site/blog/securing-self-hosted-ai-localhost-isolation-with-tls-and-nginx.html

#AI #Security""",
    },
    {
        "title": "4-Point TLS & Zero Trust Checklist",
        "linkedin": """4 security controls that block 90% of attacks on self-hosted AI:

1. TLS 1.3 everywhere (no exceptions)
2. mTLS for service-to-service
3. Token-based auth (no API keys in URLs)
4. Network segmentation (AI on isolated VLAN)

Implement all four in under an hour:
https://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html

#AI #Security #Checklist""",
        "twitter": """4 security controls that block 90% of attacks on self-hosted AI:

1. TLS 1.3 everywhere
2. mTLS for service-to-service
3. Token-based auth
4. Network segmentation

https://hypernexus.site/blog/hardening-self-hosted-ai-the-4-point-tls-amp-zero-trust-checklist.html

#AI #Security""",
    },
    {
        "title": "What CISOs Should Demand",
        "linkedin": """Before your org deploys agentic AI, your CISO should demand:

1. Data flow mapping (where does training data go?)
2. Access controls (who can invoke what?)
3. Incident response (how to revoke AI access?)
4. Compliance evidence (SOC2, HIPAA, GDPR)
5. Vendor security review (supply chain)

Full checklist with templates:
https://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html

#AI #CISO #Enterprise #Governance""",
        "twitter": """Before deploying agentic AI, your CISO should demand:

1. Data flow mapping
2. Access controls
3. Incident response plan
4. Compliance evidence
5. Vendor security review

Full checklist:
https://hypernexus.site/blog/what-your-ciso-should-demand-before-deploying-agentic-ai-a-practical-governance-checklist.html

#AI #Enterprise""",
    },
]


def get_browser_ws():
    """Get browser WebSocket URL from CDP"""
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json/version", timeout=5)
        return json.loads(resp.read()).get("webSocketDebuggerUrl")
    except Exception:
        return None


def create_tab(browser_ws, url="about:blank"):
    """Create a new tab and return its WebSocket URL"""
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
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        for t in tabs:
            if t.get("id") == target_id:
                return t.get("webSocketDebuggerUrl")
    return None


def send_and_recv(ws, msg_id, method, params=None, timeout=8):
    """Send CDP command and receive response"""
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    time.sleep(1)
    result = None
    for _ in range(15):
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
    """Navigate to URL"""
    ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}}))
    time.sleep(wait)
    for _ in range(10):
        try:
            ws.settimeout(0.5)
            ws.recv()
        except Exception:
            break


def log(msg):
    """Log with timestamp"""
    ts = time.strftime("%H:%M:%S")
    sys.stdout.buffer.write(f"[{ts}] {msg}\n".encode("utf-8"))
    sys.stdout.flush()


def open_linkedin_post_editor(ws):
    """Navigate to company page and open the post creation dialog"""
    navigate(ws, LINKEDIN_COMPANY_URL)

    # Click "Create" button
    result = send_and_recv(
        ws,
        10,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === 'Create') {
                    buttons[i].click();
                    return 'clicked Create';
                }
            }
            return 'Create not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "clicked" not in str(result):
        log(f"Create button: {result}")
        return False

    time.sleep(2)

    # Click "Start a post"
    result = send_and_recv(
        ws,
        11,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var links = document.querySelectorAll('a, button, [role="button"]');
            for (var i = 0; i < links.length; i++) {
                var text = links[i].textContent.trim();
                if (text.startsWith('Start a post')) {
                    links[i].click();
                    return 'clicked Start a post';
                }
            }
            return 'Start a post not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "clicked" not in str(result):
        log(f"Start a post: {result}")
        return False

    time.sleep(3)
    return True


def type_linkedin_content(ws, content):
    """Type content into the LinkedIn post editor"""
    # Focus the post editor textbox
    result = send_and_recv(
        ws,
        12,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var editables = document.querySelectorAll('[contenteditable="true"][role="textbox"]');
            for (var i = 0; i < editables.length; i++) {
                var ph = editables[i].getAttribute('data-placeholder') || '';
                if (ph.includes('What do you want to talk about')) {
                    editables[i].click();
                    editables[i].focus();
                    return 'focused';
                }
            }
            return 'editor not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    if not result or "focused" not in str(result):
        log(f"Editor focus: {result}")
        return False

    time.sleep(1)

    # Type content
    ws.send(
        json.dumps(
            {"id": 13, "method": "Input.insertText", "params": {"text": content}}
        )
    )
    time.sleep(3)
    for _ in range(5):
        try:
            ws.settimeout(1)
            ws.recv()
        except Exception:
            break

    return True


def click_linkedin_post_button(ws):
    """Click the Post button to publish on LinkedIn"""
    result = send_and_recv(
        ws,
        14,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === 'Post' && !buttons[i].disabled) {
                    buttons[i].click();
                    return 'posted';
                }
            }
            return 'Post button not found or disabled';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(5)

    if result and "posted" in str(result):
        return True

    log(f"Post button: {result}")
    return False


def post_to_linkedin(ws, content):
    """Full workflow: open editor, type content, post"""
    log("Opening LinkedIn post editor...")
    if not open_linkedin_post_editor(ws):
        return False

    log("Typing content...")
    if not type_linkedin_content(ws, content):
        return False

    log("Clicking Post...")
    if not click_linkedin_post_button(ws):
        return False

    log("LinkedIn post published!")
    return True


def post_to_twitter(ws, content):
    """Post to Twitter/X using CDP"""
    log("Navigating to Twitter...")
    navigate(ws, "https://x.com/compose/post", wait=10)

    # Check if logged in
    result = send_and_recv(
        ws,
        20,
        "Runtime.evaluate",
        {
            "expression": "document.querySelector('[data-testid=\"tweetTextarea_0\"]') ? 'ready' : 'not_ready'",
            "returnByValue": True,
        },
    )

    if result != "ready":
        log("Twitter: Not logged in or composer not found")
        return False

    # Focus and type
    send_and_recv(
        ws,
        21,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var el = document.querySelector('[data-testid="tweetTextarea_0"]');
            if (el) {
                el.focus();
                return 'focused';
            }
            return 'not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(1)
    ws.send(
        json.dumps(
            {"id": 22, "method": "Input.insertText", "params": {"text": content[:280]}}
        )
    )
    time.sleep(2)

    # Click tweet button
    result = send_and_recv(
        ws,
        23,
        "Runtime.evaluate",
        {
            "expression": """
        (function() {
            var btn = document.querySelector('[data-testid="tweetButton"]');
            if (btn) {
                btn.click();
                return 'tweeted';
            }
            return 'button not found';
        })()
        """,
            "returnByValue": True,
        },
    )

    time.sleep(3)

    if result and "tweeted" in str(result):
        log("Twitter post published!")
        return True

    log(f"Twitter: {result}")
    return False


def main():
    print("=" * 60)
    print("CROSS-POSTING TO LINKEDIN & TWITTER (CDP/Edge)")
    print("=" * 60)
    print()

    # Connect to browser
    browser_ws = get_browser_ws()
    if not browser_ws:
        print("ERROR: Edge browser not running with --remote-debugging-port=9222")
        print()
        print("Please start Edge with:")
        print(
            '  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222'
        )
        print()
        return

    print(f"Connected to browser: {browser_ws[:50]}...")
    print()

    # Create tabs
    linkedin_tab_ws = create_tab(browser_ws, "about:blank")
    twitter_tab_ws = create_tab(browser_ws, "about:blank")

    if not linkedin_tab_ws or not twitter_tab_ws:
        print("ERROR: Could not create browser tabs")
        return

    # Connect to tabs
    linkedin_ws = websocket.create_connection(linkedin_tab_ws, timeout=30)
    twitter_ws = websocket.create_connection(twitter_tab_ws, timeout=30)

    # Post to LinkedIn
    print("=" * 60)
    print("LINKEDIN (HyperNexus Company Page)")
    print("=" * 60)

    linkedin_success = 0
    for i, article in enumerate(ARTICLES, 1):
        print(f"\n[{i}/{len(ARTICLES)}] {article['title']}")
        if post_to_linkedin(linkedin_ws, article["linkedin"]):
            linkedin_success += 1
        time.sleep(5)

    print(f"\nLinkedIn: {linkedin_success}/{len(ARTICLES)} posted")

    # Post to Twitter
    print("\n" + "=" * 60)
    print("TWITTER/X (@HyperNexusLLC)")
    print("=" * 60)

    twitter_success = 0
    for i, article in enumerate(ARTICLES, 1):
        print(f"\n[{i}/{len(ARTICLES)}] {article['title']}")
        if post_to_twitter(twitter_ws, article["twitter"]):
            twitter_success += 1
        time.sleep(5)

    print(f"\nTwitter: {twitter_success}/{len(ARTICLES)} posted")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"LinkedIn: {linkedin_success}/{len(ARTICLES)} posts")
    print(f"Twitter: {twitter_success}/{len(ARTICLES)} posts")
    print("=" * 60)


if __name__ == "__main__":
    main()
