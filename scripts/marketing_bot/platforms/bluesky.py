"""
Bluesky Platform Module

Handles posting to Bluesky using the AT Protocol API.
No CDP automation needed - uses direct API calls.
"""

import json
import urllib.request
from typing import Optional

from .. import config
from ..llm import generate_reply


class BlueskyPlatform:
    """Bluesky posting platform using AT Protocol API."""

    PLATFORM = "bluesky"

    def __init__(self):
        self.access_jwt: Optional[str] = None
        self.did: Optional[str] = None
        self.handle: Optional[str] = None

    def authenticate(self, handle: str, password: str) -> bool:
        """Authenticate with Bluesky and get access token."""
        try:
            data = json.dumps({"identifier": handle, "password": password}).encode()
            req = urllib.request.Request(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read())
            self.access_jwt = result.get("accessJwt")
            self.did = result.get("did")
            self.handle = handle
            return True
        except Exception as e:
            print(f"[Bluesky] Auth error: {e}")
            return False

    def post(self, text: str) -> bool:
        """Post a message to Bluesky."""
        if not self.access_jwt or not self.did:
            return False

        try:
            data = json.dumps(
                {
                    "repo": self.did,
                    "collection": "app.bsky.feed.post",
                    "record": {
                        "$type": "app.bsky.feed.post",
                        "text": text[:300],
                        "createdAt": self._get_timestamp(),
                    },
                }
            ).encode()

            req = urllib.request.Request(
                "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                data=data,
                headers={
                    "Authorization": f"Bearer {self.access_jwt}",
                    "Content-Type": "application/json",
                },
            )
            urllib.request.urlopen(req, timeout=15)
            return True
        except Exception as e:
            print(f"[Bluesky] Post error: {e}")
            return False

    def post_to_all_accounts(self, text: str) -> dict:
        """Post to all configured Bluesky accounts."""
        results = {}
        for account in config.BLUESKY_ACCOUNTS:
            handle = account["handle"]
            password = account["password"]
            if not password:
                results[handle] = {"success": False, "error": "No password"}
                continue

            if self.authenticate(handle, password):
                success = self.post(text)
                results[handle] = {"success": success}
            else:
                results[handle] = {"success": False, "error": "Auth failed"}

        return results

    @staticmethod
    def _get_timestamp() -> str:
        """Get ISO timestamp for Bluesky posts."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def run_cycle(self, content: Optional[str] = None) -> Optional[dict]:
        """Post content to all Bluesky accounts."""
        if content is None:
            content = generate_reply(
                "AI developer tools and MCP server management",
                platform="bluesky",
                max_chars=config.MAX_REPLY_LENGTH["bluesky"],
            )

        if not content:
            return None

        results = self.post_to_all_accounts(content)
        success_count = sum(1 for r in results.values() if r.get("success"))

        return {
            "platform": self.PLATFORM,
            "action": "post",
            "content": content[:100],
            "accounts_posted": success_count,
            "total_accounts": len(results),
            "success": success_count > 0,
        }
