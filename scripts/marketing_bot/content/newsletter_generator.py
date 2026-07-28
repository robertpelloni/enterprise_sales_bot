"""
Newsletter Generator Module

Generates weekly newsletter content from blog posts and social media activity.
Can be used with Substack, Mailchimp, or any email platform.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

from .. import config
from ..llm import call_mimo


class NewsletterGenerator:
    """Generates newsletter content from recent activity."""

    def __init__(self):
        self.generated_newsletters: List[dict] = []

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

Create a newsletter with:
1. Subject line (compelling, not clickbait)
2. Opening paragraph (2-3 sentences)
3. "This Week's Top Insights" section (3-5 bullet points)
4. "Featured Article" section (highlight one blog post)
5. "Community Spotlight" section (mention social engagement)
6. Closing paragraph with call to action

Format as JSON:
{{
  "subject": "...",
  "opening": "...",
  "insights": ["...", "..."],
  "featured": {{"title": "...", "summary": "...", "url": "..."}},
  "community": "...",
  "closing": "..."
}}"""

        system_prompt = """You are a newsletter writer for HyperNexus, an AI control plane for developers.
Your newsletters are:
- Concise and value-packed
- Technical but accessible
- Focused on actionable insights
- Not salesy or promotional

Key messages:
- Progressive tool routing saves 60% tokens
- LLM Waterfall ensures zero downtime
- Open source and self-hostable
- Works with Claude Code, Cursor, Copilot"""

        result = call_mimo(
            prompt,
            system_prompt=system_prompt,
            max_tokens=1500,
            temperature=0.7,
        )

        if result:
            try:
                result = result.strip()
                if result.startswith("```"):
                    result = result.split("\n", 1)[1] if "\n" in result else result[3:]
                if result.endswith("```"):
                    result = result[:-3]
                result = result.strip()

                newsletter = json.loads(result)
                newsletter["week_ending"] = week_ending
                newsletter["generated_at"] = datetime.now().isoformat()
                self.generated_newsletters.append(newsletter)
                return newsletter
            except json.JSONDecodeError:
                pass

        return None

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
        <a href="{featured.get("url", config.URL_COMMERCIAL)}" class="cta">Read More →</a>
    </div>

    <h2>🌟 Community Spotlight</h2>
    <p>{newsletter.get("community", "")}</p>

    <p>{newsletter.get("closing", "")}</p>

    <div class="footer">
        <p>You're receiving this because you subscribed to HyperNexus updates.</p>
        <p><a href="{config.URL_COMMERCIAL}">Website</a> · <a href="{config.URL_OPENSOURCE}">GitHub</a> · <a href="https://twitter.com/hypernexus">Twitter</a></p>
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

## 📊 This Week's Top Insights

{insights_md}

## 📝 Featured Article

### {featured.get("title", "")}

{featured.get("summary", "")}

[Read More →]({featured.get("url", config.URL_COMMERCIAL)})

## 🌟 Community Spotlight

{newsletter.get("community", "")}

{newsletter.get("closing", "")}

---

**Links:**
- [Website]({config.URL_COMMERCIAL})
- [GitHub]({config.URL_OPENSOURCE})
- [Twitter](https://twitter.com/hypernexus)
"""
