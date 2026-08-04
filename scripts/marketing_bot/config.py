"""
Marketing Bot - Centralized Configuration

All settings for the autonomous marketing bot.
Environment variables override defaults.
"""

import os
from typing import List


def _get_int(env_key: str, default: int) -> int:
    """Safely get integer from environment variable."""
    try:
        return int(os.environ.get(env_key, str(default)))
    except (ValueError, TypeError):
        return default


def _get_float(env_key: str, default: float) -> float:
    """Safely get float from environment variable."""
    try:
        return float(os.environ.get(env_key, str(default)))
    except (ValueError, TypeError):
        return default


# ═══════════════════════════════════════════════════════════════
# LLM CONFIGURATION (MiMo v2.5 via Hermes API)
# ═══════════════════════════════════════════════════════════════

MIMO_API_URL: str = os.environ.get(
    "HERMES_API_URL",
    "https://token-plan-sgp.xiaomimimo.com/v1",
)
MIMO_API_KEY: str = os.environ.get(
    "HERMES_API_KEY",
    "tp-s0jae9p6m9d8pirs67549as0ewk9a1up0i1379o1kcg4u6r3",
)
MIMO_MODEL: str = os.environ.get("HERMES_MODEL", "mimo-v2.5")

# ═══════════════════════════════════════════════════════════════
# PRODUCT URLS
# ═══════════════════════════════════════════════════════════════

URL_COMMERCIAL: str = "https://hypernexus.site"
URL_OPENSOURCE: str = "https://github.com/MDMAtk/TormentNexus"
URL_OPENSOURCE_SITE: str = "https://tormentnexus.site"

# ═══════════════════════════════════════════════════════════════
# PLATFORM ENABLE/DISABLE FLAGS
# ═══════════════════════════════════════════════════════════════

# Set to False to disable a platform (code stays ready to re-enable)
REDDIT_ENABLED: bool = True  # Re-enabled - no links in replies to avoid removal
TWITTER_ENABLED: bool = True
LINKEDIN_ENABLED: bool = True
BLUESKY_ENABLED: bool = True
HACKERNEWS_ENABLED: bool = True

# ═══════════════════════════════════════════════════════════════
# REDDIT CONFIGURATION
# ═══════════════════════════════════════════════════════════════

REDDIT_CLIENT_ID: str = os.environ.get("REDDIT_CLIENT_ID", "0lX58KJiiwuHIY9uHEgZZw")
REDDIT_CLIENT_SECRET: str = os.environ.get(
    "REDDIT_CLIENT_SECRET", "E07dDaqBlpFdn5vVL2UZPn9YxtQNcg"
)
REDDIT_USERNAME: str = os.environ.get("REDDIT_USERNAME", "HyperNexusLLC")
REDDIT_PASSWORD: str = os.environ.get("REDDIT_PASSWORD", "Temppass0!")

# Smaller, less moderated subreddits (less likely to get removed)
# Focused on AI tools, MCP, and developer productivity
REDDIT_SUBREDDITS: List[str] = [
    "MCP_Servers",
    "ClaudeAI",
    "LocalLLaMA",
    "MachineLearning",
    "artificial",
    "singularity",
    "PromptEngineering",
    "selfhosted",
]

# Larger subreddits (build karma first, post later)
REDDIT_KARMA_SUBREDDITS: List[str] = [
    "MachineLearning",
    "LocalLLaMA",
    "ClaudeAI",
    "artificial",
    "singularity",
]

# ═══════════════════════════════════════════════════════════════
# TWITTER/X CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Search terms that match HyperNexus/TormentNexus features
TWITTER_SEARCH_TERMS: List[str] = [
    "MCP server management",
    "AI agent context window",
    "Claude Code memory",
    "AI tool routing token",
    "LLM rate limit 429",
    "AI agent persistent memory",
    "MCP tool schema bloat",
    "developer productivity AI tools",
    "local-first AI infrastructure",
    "AI agent failover",
]

# ═══════════════════════════════════════════════════════════════
# LINKEDIN CONFIGURATION
# ═══════════════════════════════════════════════════════════════

LINKEDIN_COMPANY_ID: str = "135697123"
LINKEDIN_COMPANY_URL: str = (
    f"https://www.linkedin.com/company/{LINKEDIN_COMPANY_ID}/admin/"
)

# Search terms that match HyperNexus/TormentNexus features
LINKEDIN_SEARCH_TERMS: List[str] = [
    "MCP server management",
    "AI agent infrastructure",
    "Claude Code tools",
    "developer productivity AI",
    "AI agent memory",
    "LLM rate limiting",
]

# ═══════════════════════════════════════════════════════════════
# BLUESKY CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BLUESKY_ACCOUNTS: List[dict] = [
    {
        "handle": "tormentnexus.bsky.social",
        "password": os.environ.get("BLUESKY_TN_PASSWORD", ""),
    },
    {
        "handle": "hypernexus.bsky.social",
        "password": os.environ.get("BLUESKY_HN_PASSWORD", ""),
    },
]

# ═══════════════════════════════════════════════════════════════
# HACKER NEWS CONFIGURATION
# ═══════════════════════════════════════════════════════════════

HN_USERNAME: str = os.environ.get("HN_USERNAME", "")
HN_PASSWORD: str = os.environ.get("HN_PASSWORD", "")

# ═══════════════════════════════════════════════════════════════
# DEV.TO CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DEVTO_API_KEY: str = os.environ.get("DEVTO_API_KEY", "")

# ═══════════════════════════════════════════════════════════════
# RATE LIMITING
# ═══════════════════════════════════════════════════════════════

# Minimum delay between posts (seconds)
DELAY_MIN_SECONDS: int = _get_int("DELAY_MIN_SECONDS", 900)  # 15 min
DELAY_MAX_SECONDS: int = _get_int("DELAY_MAX_SECONDS", 2700)  # 45 min

# Maximum posts per hour per platform
MAX_POSTS_PER_HOUR: int = _get_int("MAX_POSTS_PER_HOUR", 4)

# Maximum posts per day per platform
MAX_POSTS_PER_DAY: int = _get_int("MAX_POSTS_PER_DAY", 20)

# ═══════════════════════════════════════════════════════════════
# BROWSER CONFIGURATION
# ═══════════════════════════════════════════════════════════════

CDP_PORT: int = _get_int("CDP_PORT", 9222)
CDP_HOST: str = os.environ.get("CDP_HOST", "localhost")

# ═══════════════════════════════════════════════════════════════
# CONTENT SETTINGS
# ═══════════════════════════════════════════════════════════════

# Maximum reply length by platform
MAX_REPLY_LENGTH: dict = {
    "reddit": 500,
    "twitter": 280,
    "linkedin": 1000,
    "bluesky": 300,
    "hackernews": 2000,
}

# LLM temperature (0.0-1.0, higher = more creative)
LLM_TEMPERATURE: float = _get_float("LLM_TEMPERATURE", 0.7)

# Maximum tokens for LLM response
LLM_MAX_TOKENS: int = _get_int("LLM_MAX_TOKENS", 200)

# ═══════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "[{timestamp}] [{platform}] {message}"
