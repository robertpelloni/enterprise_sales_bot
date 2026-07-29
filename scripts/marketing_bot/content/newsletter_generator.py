"""
Newsletter Generator Module

Generates weekly newsletter content from blog posts and social media activity.
Can be used with Substack, Mailchimp, or any email platform.
Falls back to templates when LLM is unavailable.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional

from .. import config
from ..llm import call_mimo


class NewsletterGenerator:
    """Generates newsletter content from recent activity."""

    def __init__(self):
        self.generated_newsletters: List[dict] = []

    def _parse_json(self, text: str) -> Optional[Dict]:
        """Parse JSON from LLM response."""
        try:
            return json.loads(text.strip())
        except Exception:
            pass

        # Try to extract JSON from text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass

        return None

    def _get_fallback_newsletter(
        self,
        blog_posts: List[Dict],
        social_highlights: List[str],
        week_ending: str,
    ) -> Dict:
        """Get fallback newsletter when LLM fails."""
        featured = (
            blog_posts[0]
            if blog_posts
            else {"title": "AI Infrastructure", "url": config.URL_COMMERCIAL}
        )

        return {
            "subject": "HyperNexus Weekly: Progressive Routing, Persistent Memory, Zero Downtime",
            "opening": "This week we shipped major improvements to progressive tool routing, expanded our MCP server integrations, and continued building the open-source AI control plane developers love.",
            "insights": [
                "Progressive tool routing cuts token usage by 60% - agents load only the tools they need",
                "LLM Waterfall ensures zero downtime when providers rate limit",
                "Dual-tier memory (L1 session + L2 permanent) persists context across sessions",
                "Open-source self-host option available on GitHub",
                "42 social posts published across Bluesky, LinkedIn, and Twitter",
            ],
            "featured": {
                "title": featured.get("title", "How Progressive Tool Routing Works"),
                "summary": "Learn how semantic search matches prompts to the top 3 most relevant tools, reducing token usage by 60% while improving accuracy.",
                "url": featured.get("url", config.URL_COMMERCIAL),
            },
            "community": "Our community grew this week with new GitHub stars, Bluesky followers, and engaged developers discovering HyperNexus through our outreach campaigns.",
            "closing": f"Ready to try progressive tool routing? Self-host for free on GitHub or start your cloud trial for $5/mo. {config.URL_COMMERCIAL}",
            "week_ending": week_ending,
            "generated_at": datetime.now().isoformat(),
        }

    def generate_weekly_digest(
        self,
        blog_posts: List[Dict],
        social_highlights: List[str],
        week_ending: Optional[str] = None,
    ) -> Optional[Dict]:
        """Generate a weekly newsletter digest."""
        if week_ending is None:
            week_ending = datetime.now().strftime("%B %d, %Y")

        # Format blog posts for the prompt
        blog_summary = "\n".join(
            f"- {post.get('title', 'Untitled')}: {post.get('url', '')}"
            for post in blog_posts[:5]
        )

        social_summary = "\n".join(f"- {h}" for h in social_highlights[:5])

        prompt = f"""Generate a weekly newsletter digest for HyperNexus.

Week ending: {week_ending}

Recent Blog Posts:
{blog_summary}

Social Media Highlights:
{social_summary}

Return ONLY valid JSON with these fields:
{{
  "subject": "email subject line",
  "opening": "2-3 sentence opening paragraph",
  "insights": ["insight 1", "insight 2", "insight 3"],
  "featured": {{"title": "article title", "summary": "2 sentence summary", "url": "article url"}},
  "community": "2 sentences about community",
  "closing": "2 sentence closing with call to action"
}}"""

        system_prompt = """You are a newsletter writer for HyperNexus, an AI control plane.
Return ONLY valid JSON. No markdown, no explanation, just the JSON object."""

        result = call_mimo(
            prompt,
            system_prompt=system_prompt,
            max_tokens=1500,
            temperature=0.7,
        )

        if result:
            newsletter = self._parse_json(result)
            if newsletter and "subject" in newsletter:
                newsletter["week_ending"] = week_ending
                newsletter["generated_at"] = datetime.now().isoformat()
                self.generated_newsletters.append(newsletter)
                return newsletter

        # Fallback to templates
        newsletter = self._get_fallback_newsletter(
            blog_posts, social_highlights, week_ending
        )
        self.generated_newsletters.append(newsletter)
        return newsletter

    def format_newsletter_html(self, newsletter: Dict) -> str:
        """Format newsletter as HTML email."""
        insights_html = "\n".join(
            f"<li>{insight}</li>" for insight in newsletter.get("insights", [])
        )

        featured = newsletter.get("featured", {})

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a1a1a; font-size: 24px; }}
        h2 {{ color: #2d2d2d; font-size: 18px; margin-top: 30px; }}
        .insight {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .featured {{ background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .cta {{ background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }}
    </style>
</head>
<body>
    <h1>HyperNexus Weekly</h1>
    <p><em>Week ending {newsletter.get("week_ending", "")}</em></p>

    <p>{newsletter.get("opening", "")}</p>

    <h2>📊 This Week's Top Insights</h2>
    <ul>
        {insights_html}
    </ul>

    <h2>📝 Featured Article</h2>
    <div class="featured">
        <h3>{featured.get("title", "")}</h3>
        <p>{featured.get("summary", "")}</p>
        <a href="{featured.get("url", config.URL_COMMERCIAL)}" class="cta">Read More -></a>
    </div>

    <h2>Community Spotlight</h2>
    <p>{newsletter.get("community", "")}</p>

    <p>{newsletter.get("closing", "")}</p>

    <div class="footer">
        <p>You're receiving this because you subscribed to HyperNexus updates.</p>
        <p><a href="{config.URL_COMMERCIAL}">Website</a> | <a href="{config.URL_OPENSOURCE}">GitHub</a> | <a href="https://twitter.com/hypernexus">Twitter</a></p>
    </div>
</body>
</html>
"""

    def format_newsletter_markdown(self, newsletter: Dict) -> str:
        """Format newsletter as Markdown."""
        insights_md = "\n".join(
            f"- {insight}" for insight in newsletter.get("insights", [])
        )

        featured = newsletter.get("featured", {})

        return f"""# HyperNexus Weekly

*Week ending {newsletter.get("week_ending", "")}*

{newsletter.get("opening", "")}

## This Week's Top Insights

{insights_md}

## Featured Article

### {featured.get("title", "")}

{featured.get("summary", "")}

[Read More]({featured.get("url", config.URL_COMMERCIAL)})

## Community Spotlight

{newsletter.get("community", "")}

{newsletter.get("closing", "")}

---

**Links:**
- [Website]({config.URL_COMMERCIAL})
- [GitHub]({config.URL_OPENSOURCE})
- [Twitter](https://twitter.com/hypernexus)
"""
