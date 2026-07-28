"""
dev.to Platform Module

Handles cross-posting articles to dev.to using the API.
"""

import json
import urllib.request
from typing import Optional

from .. import config


class DevToPlatform:
    """dev.to publishing platform using API."""

    PLATFORM = "devto"

    def __init__(self):
        self.api_key: str = config.DEVTO_API_KEY

    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def publish_article(
        self,
        title: str,
        body_markdown: str,
        tags: Optional[list] = None,
        series: str = "",
        canonical_url: str = "",
    ) -> Optional[dict]:
        """Publish an article to dev.to."""
        if not self.api_key:
            print("[DevTo] No API key configured")
            return None

        if tags is None:
            tags = ["ai", "developer-tools", "mcp", "open-source"]

        article = {
            "title": title,
            "body_markdown": body_markdown,
            "tags": tags[:4],  # dev.to allows max 4 tags
            "published": True,
        }

        if series:
            article["series"] = series
        if canonical_url:
            article["canonical_url"] = canonical_url

        try:
            data = json.dumps({"article": article}).encode()
            req = urllib.request.Request(
                "https://dev.to/api/articles",
                data=data,
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())
            return {
                "id": result.get("id"),
                "url": result.get("url"),
                "title": result.get("title"),
            }
        except Exception as e:
            print(f"[DevTo] Publish error: {e}")
            return None

    def get_articles(self, page: int = 1, per_page: int = 10) -> list:
        """Get published articles."""
        if not self.api_key:
            return []

        try:
            req = urllib.request.Request(
                f"https://dev.to/api/articles/me?page={page}&per_page={per_page}",
                headers={"api-key": self.api_key},
            )
            resp = urllib.request.urlopen(req, timeout=15)
            return json.loads(resp.read())
        except Exception as e:
            print(f"[DevTo] Get articles error: {e}")
            return []

    def run_cycle(self, content: Optional[dict] = None) -> Optional[dict]:
        """Publish an article if content is provided."""
        if content is None:
            return None

        result = self.publish_article(
            title=content.get("title", ""),
            body_markdown=content.get("body", ""),
            tags=content.get("tags"),
            series=content.get("series", ""),
            canonical_url=content.get("canonical_url", ""),
        )

        if result:
            return {
                "platform": self.PLATFORM,
                "action": "publish",
                "title": result["title"],
                "url": result["url"],
                "success": True,
            }

        return None
