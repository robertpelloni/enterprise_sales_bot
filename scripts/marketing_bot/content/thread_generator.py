"""
Thread Generator Module

Converts blog posts into Twitter/LinkedIn threads.
Takes a blog post URL and creates a 5-7 tweet thread.
Falls back to templates when LLM is unavailable.
"""

import json
import re
from typing import List, Optional

from .. import config
from ..llm import call_mimo


class ThreadGenerator:
    """Generates social media threads from blog posts."""

    PLATFORMS = ["twitter", "linkedin"]

    def __init__(self):
        self.generated_threads: List[dict] = []

    def _parse_json_array(self, text: str, expected_count: int) -> Optional[List[str]]:
        """Parse JSON array from LLM response."""
        # Try direct JSON parse
        try:
            result = json.loads(text.strip())
            if isinstance(result, list) and len(result) > 0:
                return result[:expected_count]
        except Exception:
            pass

        # Try to extract JSON array from text
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                if isinstance(result, list) and len(result) > 0:
                    return result[:expected_count]
            except Exception:
                pass

        return None

    def _get_fallback_thread(self, topic: str, num_tweets: int) -> List[str]:
        """Get fallback thread when LLM fails."""
        url = config.URL_COMMERCIAL
        topic_lower = topic.lower()

        if "token" in topic_lower or "routing" in topic_lower:
            tweets = [
                "1/ Most AI agents waste 60% of their token budget loading tool definitions they'll never use.",
                "2/ Progressive tool routing solves this: semantic search matches your prompt to the top 3 most relevant tools. No more context bloat.",
                "3/ The result? 60% fewer tokens. Faster responses. Better accuracy. Your agent focuses on what matters.",
                "4/ Combined with LLM Waterfall failover, you get zero downtime. When one provider rate limits, the next picks up.",
                f"5/ HyperNexus does all this automatically. Self-host for free or use the cloud version. {url}",
            ]
        elif "memory" in topic_lower:
            tweets = [
                "1/ Every AI agent forgets everything between sessions. Ask it to remember a decision? Blank stare.",
                "2/ We built dual-tier memory: L1 for session scratchpad (ephemeral, fast), L2 for permanent semantic storage (SQLite + vector search).",
                "3/ Your agent remembers decisions across sessions. Searches by meaning, not keywords.",
                "4/ This is how you build an AI agent that actually learns and improves over time.",
                f"5/ Open source and self-hostable. {url}",
            ]
        elif "waterfall" in topic_lower or "failover" in topic_lower:
            tweets = [
                "1/ It's 2 AM. Your AI agent hits a 429 rate limit. Workflow stops. Productivity: zero.",
                "2/ The LLM Waterfall Pattern solves this: Primary API -> Secondary API -> Local models -> Queue.",
                "3/ When one provider fails, the next picks up automatically. Zero downtime. Zero interruptions.",
                "4/ Rate limits are inevitable. Downtime is not.",
                f"5/ Built into HyperNexus. Works with Claude, GPT, Gemini, and local models. {url}",
            ]
        else:
            tweets = [
                "1/ AI development is evolving fast. Here's what's changing and why it matters.",
                "2/ Progressive tool routing cuts token usage by 60%. Your agents get faster and cheaper.",
                "3/ Persistent memory means your AI remembers context across sessions. No more starting over.",
                "4/ LLM Waterfall ensures zero downtime. Rate limits can't stop your workflow.",
                f"5/ The future of AI infrastructure is local-first and open source. {url}",
            ]

        return tweets[:num_tweets]

    def generate_thread_from_blog(
        self,
        blog_title: str,
        blog_content: str,
        platform: str = "twitter",
        num_tweets: int = 6,
    ) -> Optional[List[str]]:
        """Generate a thread from blog content."""
        max_chars = 280 if platform == "twitter" else 1000

        prompt = f"""Convert this blog post into a {num_tweets}-tweet thread for {platform}.

Blog Title: {blog_title}
Blog Content (first 1000 chars): {blog_content[:1000]}

Rules:
- First tweet: Hook that grabs attention, include title
- Middle tweets: Key points, one per tweet
- Last tweet: Call to action with link (use {{url}} placeholder)
- Each tweet max {max_chars} chars
- Use emojis sparingly
- Make it conversational, not corporate
- Number each tweet (1/, 2/, etc.)

Return ONLY a JSON array of strings. Example: ["tweet1", "tweet2", "tweet3"]"""

        system_prompt = """You are a social media expert who creates engaging technical threads.
Return ONLY valid JSON array format. No markdown, no explanation, just the JSON array."""

        result = call_mimo(
            prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.8,
        )

        if result:
            tweets = self._parse_json_array(result, num_tweets)
            if tweets:
                url = (
                    config.URL_COMMERCIAL
                    if platform == "twitter"
                    else config.URL_OPENSOURCE
                )
                if "{url}" in tweets[-1]:
                    tweets[-1] = tweets[-1].replace("{url}", url)
                return tweets

        # Fallback to templates
        return self._get_fallback_thread(blog_title, num_tweets)

    def generate_thread_from_topic(
        self,
        topic: str,
        platform: str = "twitter",
        num_tweets: int = 6,
    ) -> Optional[List[str]]:
        """Generate a thread about a topic."""
        max_chars = 280 if platform == "twitter" else 1000

        prompt = f"""Create a {num_tweets}-tweet thread about: {topic}

Rules:
- First tweet: Hook that grabs attention
- Middle tweets: Key insights, one per tweet
- Last tweet: Call to action with link (use {{url}} placeholder)
- Each tweet max {max_chars} chars
- Use emojis sparingly
- Make it conversational, not corporate
- Number each tweet (1/, 2/, etc.)
- Include specific numbers and examples

Return ONLY a JSON array of strings. Example: ["tweet1", "tweet2", "tweet3"]"""

        system_prompt = """You are a social media expert who creates engaging technical threads.
Return ONLY valid JSON array format. No markdown, no explanation, just the JSON array."""

        result = call_mimo(
            prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.8,
        )

        if result:
            tweets = self._parse_json_array(result, num_tweets)
            if tweets:
                url = config.URL_COMMERCIAL
                if "{url}" in tweets[-1]:
                    tweets[-1] = tweets[-1].replace("{url}", url)
                return tweets

        # Fallback to templates
        return self._get_fallback_thread(topic, num_tweets)

    def format_thread(self, tweets: List[str], platform: str = "twitter") -> str:
        """Format a thread for display."""
        separator = "\n\n" if platform == "twitter" else "\n\n---\n\n"
        return separator.join(tweets)
