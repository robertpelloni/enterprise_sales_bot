"""
Comment Responder Module

Monitors and responds to comments on our posts across platforms.
Tracks which comments we've replied to and generates contextual responses.
"""

import json
import os
from typing import Dict, Optional

from .. import config
from ..llm import call_mimo


class CommentResponder:
    """Monitors and responds to comments on our posts."""

    def __init__(self):
        self.responded_comments: Dict[str, set] = {
            "reddit": set(),
            "twitter": set(),
            "linkedin": set(),
        }
        self.response_count: int = 0
        self.state_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "comment_state.json",
        )
        self._load_state()

    def _load_state(self):
        """Load responded comments from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    for platform in self.responded_comments:
                        if platform in state:
                            self.responded_comments[platform] = set(state[platform])
        except Exception:
            pass

    def _save_state(self):
        """Save responded comments to file."""
        try:
            state = {
                platform: list(comments)
                for platform, comments in self.responded_comments.items()
            }
            with open(self.state_file, "w") as f:
                json.dump(state, f)
        except Exception:
            pass

    def should_respond(self, comment_id: str, platform: str) -> bool:
        """Check if we should respond to a comment."""
        if platform not in self.responded_comments:
            return False
        return comment_id not in self.responded_comments[platform]

    def generate_response(
        self,
        comment_text: str,
        original_post_text: str,
        platform: str,
    ) -> Optional[str]:
        """Generate a response to a comment."""
        prompt = f"""Someone commented on our post about AI tools. Generate a helpful, engaging reply.

Original Post: {original_post_text[:200]}
Comment: {comment_text[:300]}

Rules:
- Be helpful and genuine, not defensive
- If they have a question, answer it
- If they're skeptical, provide evidence
- If they're supportive, thank them and add value
- Keep it short (1-2 sentences)
- Include a link if relevant (use {{url}} placeholder)

Reply:"""

        system_prompt = """You are a community manager for HyperNexus, an AI control plane.
You respond to comments in a helpful, genuine way that builds trust.
Never be defensive or salesy. Focus on providing value.

Key features to mention if relevant:
- Progressive tool routing (60% token savings)
- LLM Waterfall (zero downtime failover)
- Persistent memory (L1 session + L2 permanent)
- Open source: github.com/MDMAtk/TormentNexus
- Commercial: hypernexus.site ($5/mo)"""

        response = call_mimo(
            prompt,
            system_prompt=system_prompt,
            max_tokens=150,
            temperature=0.7,
        )

        if response:
            response = response.strip().strip('"').strip("'")
            if "{url}" in response:
                url = (
                    config.URL_OPENSOURCE
                    if "open source" in comment_text.lower()
                    else config.URL_COMMERCIAL
                )
                response = response.replace("{url}", url)
            return response

        return None

    def mark_responded(self, comment_id: str, platform: str):
        """Mark a comment as responded to."""
        if platform in self.responded_comments:
            self.responded_comments[platform].add(comment_id)
            self.response_count += 1
            self._save_state()

    def get_stats(self) -> Dict:
        """Get response statistics."""
        return {
            "total_responses": self.response_count,
            "by_platform": {
                platform: len(comments)
                for platform, comments in self.responded_comments.items()
            },
        }
