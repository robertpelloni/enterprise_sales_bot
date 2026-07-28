"""
Thread Generator Module

Converts blog posts into Twitter/LinkedIn threads.
Takes a blog post URL and creates a 5-7 tweet thread.
"""

import json
from typing import List, Optional

from .. import config
from ..llm import call_mimo


class ThreadGenerator:
    """Generates social media threads from blog posts."""

    PLATFORMS = ["twitter", "linkedin"]

    def __init__(self):
        self.generated_threads: List[dict] = []

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

Return as JSON array of strings: ["tweet1", "tweet2", ...]"""

        system_prompt = """You are a social media expert who creates engaging technical threads.
Your threads get high engagement because they:
- Start with a compelling hook
- Break complex ideas into digestible pieces
- Use concrete numbers and examples
- End with a clear call to action

Always return valid JSON array format."""

        result = call_mimo(
            prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.8,
        )

        if result:
            try:
                # Clean up the response to extract JSON
                result = result.strip()
                if result.startswith("```"):
                    result = result.split("\n", 1)[1] if "\n" in result else result[3:]
                if result.endswith("```"):
                    result = result[:-3]
                result = result.strip()

                tweets = json.loads(result)
                if isinstance(tweets, list) and len(tweets) > 0:
                    # Add URL to last tweet
                    url = (
                        config.URL_COMMERCIAL
                        if platform == "twitter"
                        else config.URL_OPENSOURCE
                    )
                    if "{url}" in tweets[-1]:
                        tweets[-1] = tweets[-1].replace("{url}", url)
                    return tweets
            except json.JSONDecodeError:
                # Try to extract tweets manually
                lines = result.split("\n")
                tweets = [
                    line.strip()
                    for line in lines
                    if line.strip() and len(line.strip()) > 10
                ]
                if tweets:
                    return tweets[:num_tweets]

        return None

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

Return as JSON array of strings: ["tweet1", "tweet2", ...]"""

        system_prompt = """You are a social media expert who creates engaging technical threads about AI and developer tools.
Your threads get high engagement because they:
- Start with a compelling hook
- Use concrete numbers (e.g., "60% token reduction")
- Break complex ideas into digestible pieces
- End with a clear call to action

Always return valid JSON array format."""

        result = call_mimo(
            prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.8,
        )

        if result:
            try:
                result = result.strip()
                if result.startswith("```"):
                    result = result.split("\n", 1)[1] if "\n" in result else result[3:]
                if result.endswith("```"):
                    result = result[:-3]
                result = result.strip()

                tweets = json.loads(result)
                if isinstance(tweets, list) and len(tweets) > 0:
                    url = config.URL_COMMERCIAL
                    if "{url}" in tweets[-1]:
                        tweets[-1] = tweets[-1].replace("{url}", url)
                    return tweets
            except json.JSONDecodeError:
                lines = result.split("\n")
                tweets = [
                    line.strip()
                    for line in lines
                    if line.strip() and len(line.strip()) > 10
                ]
                if tweets:
                    return tweets[:num_tweets]

        return None

    def format_thread(self, tweets: List[str], platform: str = "twitter") -> str:
        """Format a thread for display."""
        separator = "\n\n" if platform == "twitter" else "\n\n---\n\n"
        return separator.join(tweets)
