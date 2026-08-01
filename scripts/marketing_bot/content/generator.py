"""
Content Generator

Generates platform-specific content using MiMo v2.5 LLM.
"""

import random
from typing import Optional

from ..llm import (
    generate_reply,
    generate_article_content,
    adapt_content_for_platform,
    get_url_for_context,
)
from .templates import FALLBACK_TEMPLATES


class ContentGenerator:
    """Generates content for multiple platforms."""

    def __init__(self):
        self.used_templates: dict = {}

    def get_reply(
        self,
        post_text: str,
        platform: str,
        max_chars: int = 200,
        use_fallback: bool = True,
    ) -> Optional[str]:
        """Generate a reply for a post."""
        # Try LLM first
        reply = generate_reply(post_text, platform=platform, max_chars=max_chars)

        if reply:
            return adapt_content_for_platform(reply, platform, max_chars)

        # Fall back to templates
        if use_fallback:
            return self._get_fallback(post_text, platform)

        return None

    def get_article(self, topic: str, style: str = "technical") -> Optional[str]:
        """Generate article content."""
        return generate_article_content(topic, style=style)

    def _get_fallback(self, post_text: str, platform: str) -> str:
        """Get a fallback template for the platform."""
        templates = FALLBACK_TEMPLATES.get(platform, FALLBACK_TEMPLATES["reddit"])

        # Try to match context
        post_lower = post_text.lower()
        if "rate limit" in post_lower or "429" in post_lower:
            category = "rate_limit"
        elif "memory" in post_lower or "remember" in post_lower:
            category = "memory"
        elif "mcp" in post_lower or "tool" in post_lower:
            category = "mcp"
        else:
            category = "generic"

        # Get unused template or random one
        key = f"{platform}_{category}"
        if key not in self.used_templates:
            self.used_templates[key] = []

        available = [t for t in templates if t not in self.used_templates[key]]
        if not available:
            self.used_templates[key] = []
            available = templates

        template = random.choice(available)
        self.used_templates[key].append(template)

        # Substitute URL placeholder (the templates use {url})
        url = get_url_for_context(post_text)
        return template.replace("{url}", url)
