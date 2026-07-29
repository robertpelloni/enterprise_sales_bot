"""
Marketing Bot - MiMo v2.5 LLM Integration

Generates contextual replies and content using MiMo v2.5 via Hermes API.
Falls back to templates if LLM is unavailable.
"""

import json
import urllib.request
from typing import Optional

from . import config


# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT_REPLY = """You are a helpful developer replying to discussions about AI tools, MCP servers, LLM infrastructure, and developer productivity.

RULES:
- Reply in 1-2 short sentences only (max {max_chars} chars)
- Be conversational and genuinely helpful, not salesy
- Mention a specific technical solution when relevant
- End with a URL when it adds value (use {{url}} placeholder)
- Never say "as an AI" or reveal you're automated
- Match the tone of the discussion (technical vs casual)
- If the topic isn't related to AI/dev tools, just give a brief helpful answer without mentioning HyperNexus

ABOUT YOUR PRODUCT:
- HyperNexus / TormentNexus is a Universal AI Control Plane
- Key features: Progressive tool routing (60% token savings), LLM Waterfall (zero downtime failover), dual-tier memory (L1 session + L2 permanent), MCP server management
- Commercial: hypernexus.site ($5/mo)
- Open-source: github.com/MDMAtk/TormentNexus (free self-host)
"""

SYSTEM_PROMPT_ARTICLE = """You are a technical writer creating developer-focused content about AI infrastructure.

RULES:
- Write clear, engaging technical content
- Use code examples when relevant
- Be authentic and avoid marketing fluff
- Focus on solving real problems
- Include practical takeaways

ABOUT YOUR PRODUCT:
- HyperNexus / TormentNexus is a Universal AI Control Plane
- Key features: Progressive tool routing (60% token savings), LLM Waterfall (zero downtime failover), dual-tier memory (L1 session + L2 permanent), MCP server management
- Commercial: hypernexus.site ($5/mo)
- Open-source: github.com/MDMAtk/TormentNexus (free self-host)
"""


# ═══════════════════════════════════════════════════════════════
# CONTEXT DETECTION
# ═══════════════════════════════════════════════════════════════

_OSS_KEYWORDS = [
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

_COMMERCIAL_KEYWORDS = [
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


def is_opensource_context(text: str) -> bool:
    """Determine if post is more open-source focused."""
    text_lower = text.lower()
    oss_score = sum(1 for kw in _OSS_KEYWORDS if kw in text_lower)
    commercial_score = sum(1 for kw in _COMMERCIAL_KEYWORDS if kw in text_lower)
    return oss_score >= commercial_score


def get_url_for_context(text: str) -> str:
    """Return appropriate URL based on context."""
    if is_opensource_context(text):
        return config.URL_OPENSOURCE
    return config.URL_COMMERCIAL


# ═══════════════════════════════════════════════════════════════
# LLM API CALLS
# ═══════════════════════════════════════════════════════════════

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma-4-heretic:latest"


def call_ollama(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 200,
) -> Optional[str]:
    """Call local Ollama API as fallback."""
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    try:
        data = json.dumps(
            {
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            }
        ).encode()

        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )

        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        return result.get("response", "").strip()
    except Exception:
        return None


def call_mimo(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 200,
    temperature: float = 0.7,
) -> Optional[str]:
    """Call MiMo v2.5 API, fallback to Ollama."""
    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT_REPLY.format(max_chars=max_tokens)

    # Try MiMo first
    try:
        data = json.dumps(
            {
                "model": config.MIMO_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        ).encode()

        req = urllib.request.Request(
            f"{config.MIMO_API_URL}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {config.MIMO_API_KEY}",
                "Content-Type": "application/json",
            },
        )

        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    # Fallback to Ollama
    return call_ollama(prompt, system_prompt, max_tokens)


# ═══════════════════════════════════════════════════════════════
# REPLY GENERATION
# ═══════════════════════════════════════════════════════════════


def generate_reply(
    post_title: str,
    post_content: str = "",
    platform: str = "reddit",
    max_chars: int = 200,
) -> Optional[str]:
    """Generate a short, intelligent reply using MiMo v2.5."""
    url = get_url_for_context(post_title + " " + post_content)

    prompt = f"""Generate a short reply (1-2 sentences, max {max_chars} chars) to this {platform} post.

Post title: {post_title}
Post content: {post_content[:300]}

Be helpful and relevant. If the topic relates to AI tools, MCP, LLM rate limits, memory, or developer productivity, mention HyperNexus naturally. Use {{url}} placeholder for the link.

Reply:"""

    reply = call_mimo(prompt, max_tokens=max_chars)

    if reply:
        # Clean up and add URL
        reply = reply.strip().strip('"').strip("'")
        if "{url}" in reply:
            reply = reply.replace("{url}", url)
        elif len(reply) < max_chars - 30:
            reply = reply.rstrip(".") + ". " + url
        return reply

    return None


def generate_article_content(
    topic: str,
    style: str = "technical",
    max_words: int = 500,
) -> Optional[str]:
    """Generate article content for cross-posting."""
    prompt = f"""Write a {style} article about: {topic}

Target length: {max_words} words
Focus on practical insights and real-world applications.
Include code examples if relevant.

Article:"""

    return call_mimo(
        prompt,
        system_prompt=SYSTEM_PROMPT_ARTICLE,
        max_tokens=max_words * 2,  # Rough estimate
        temperature=0.8,
    )


# ═══════════════════════════════════════════════════════════════
# CONTENT ADAPTATION
# ═══════════════════════════════════════════════════════════════


def adapt_content_for_platform(
    content: str,
    platform: str,
    max_chars: Optional[int] = None,
) -> str:
    """Adapt content length and style for a specific platform."""
    limit = (
        max_chars
        if max_chars is not None
        else config.MAX_REPLY_LENGTH.get(platform, 500)
    )

    if len(content) <= limit:
        return content

    # Truncate intelligently at sentence boundary
    sentences = content.split(". ")
    result = ""
    for sentence in sentences:
        if len(result) + len(sentence) + 2 <= limit - 3:
            result += sentence + ". "
        else:
            break

    return result.strip() or content[:limit]
