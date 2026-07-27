"""
Shared MiMo v2.5 LLM module for generating intelligent marketing replies
"""

import json
import urllib.request

MIMO_URL = "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions"
MIMO_KEY = "tp-s0jae9p6m9d8pirs67549as0ewk9a1up0i1379o1kcg4u6r3"
MIMO_MODEL = "mimo-v2.5"

# URLs for different contexts
URL_COMMERCIAL = "https://hypernexus.site"
URL_OPENSOURCE = "https://github.com/MDMAtk/TormentNexus"

SYSTEM_PROMPT = """You are a helpful developer replying to discussions about AI tools, MCP servers, LLM infrastructure, and developer productivity.

RULES:
- Reply in 1-2 short sentences only (max 200 chars)
- Be conversational and genuinely helpful, not salesy
- Mention a specific technical solution when relevant
- End with a URL when it adds value (use {url} placeholder)
- Never say "as an AI" or reveal you're automated
- Match the tone of the discussion (technical vs casual)
- If the topic isn't related to AI/dev tools, just give a brief helpful answer without mentioning HyperNexus

ABOUT YOUR PRODUCT:
- HyperNexus / TormentNexus is a Universal AI Control Plane
- Key features: Progressive tool routing (60% token savings), LLM Waterfall (zero downtime failover), dual-tier memory (L1 session + L2 permanent), MCP server management
- Commercial: hypernexus.site ($5/mo)
- Open-source: github.com/MDMAtk/TormentNexus (free self-host)
"""


def call_mimo(prompt, max_tokens=150):
    """Call MiMo v2.5 API"""
    try:
        data = json.dumps(
            {
                "model": MIMO_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }
        ).encode()

        req = urllib.request.Request(
            MIMO_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {MIMO_KEY}",
                "Content-Type": "application/json",
            },
        )

        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def is_opensource_context(text):
    """Determine if post is more open-source focused"""
    text_lower = text.lower()
    oss_keywords = [
        "open source",
        "opensource",
        "free",
        "self-host",
        "selfhost",
        "github",
        "foss",
        "community",
        "hobbyist",
        "indie",
        "student",
        "budget",
        "personal project",
        "side project",
    ]
    commercial_keywords = [
        "enterprise",
        "business",
        "company",
        "team",
        "production",
        "saas",
        "paid",
        "pricing",
        "professional",
        "startup",
        "scale",
    ]
    oss_score = sum(1 for kw in oss_keywords if kw in text_lower)
    commercial_score = sum(1 for kw in commercial_keywords if kw in text_lower)
    return oss_score >= commercial_score


def get_url_for_context(text):
    """Return appropriate URL based on context"""
    if is_opensource_context(text):
        return URL_OPENSOURCE
    return URL_COMMERCIAL


def generate_reply(post_title, post_content="", platform="reddit"):
    """Generate a short, intelligent reply using MiMo v2.5"""
    url = get_url_for_context(post_title + " " + post_content)

    prompt = f"""Generate a short reply (1-2 sentences, max 200 chars) to this {platform} post.

Post title: {post_title}
Post content: {post_content[:300]}

Be helpful and relevant. If the topic relates to AI tools, MCP, LLM rate limits, memory, or developer productivity, mention HyperNexus naturally. Use {{url}} placeholder for the link.

Reply:"""

    reply = call_mimo(prompt)

    if reply:
        # Clean up and add URL
        reply = reply.strip().strip('"').strip("'")
        if "{url}" in reply:
            reply = reply.replace("{url}", url)
        elif len(reply) < 180:
            reply = reply.rstrip(".") + ". " + url
        return reply

    # Fallback to template if LLM fails
    return None
