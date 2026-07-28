"""
Fallback Templates

Used when LLM is unavailable or fails to generate content.
"""

from typing import Dict, List

# Platform-specific fallback templates
FALLBACK_TEMPLATES: Dict[str, List[str]] = {
    "reddit": [
        "Progressive tool routing is key - semantic search matches your prompt to the top 3 most relevant tools instead of loading all definitions. {url}",
        "The LLM Waterfall Pattern solves this: Primary API -> Secondary API -> Local models -> Queue. Zero downtime from rate limits. {url}",
        "Dual-tier memory architecture: L1 for session scratchpad, L2 for permanent semantic storage with vector search. {url}",
        "Progressive tool routing + persistent memory + multi-model failover is the combo that makes AI agents reliable. {url}",
    ],
    "twitter": [
        "Progressive tool routing matches prompts to top 3 most relevant tools via semantic search. ~60% token reduction. {url}",
        "The Waterfall Pattern: Primary API -> Secondary API -> Local models -> Queue. Zero downtime from rate limits. {url}",
        "Progressive tool routing + persistent memory + multi-model failover is the reliable AI agent stack. {url}",
    ],
    "linkedin": [
        "Progressive tool routing is key for MCP management - semantic search matches prompts to top 3 relevant tools. {url}",
        "The LLM Waterfall Pattern: Primary -> Secondary -> Local -> Queue. Zero downtime from rate limits. {url}",
        "Progressive tool routing + persistent memory + multi-model failover is the reliable AI agent stack. {url}",
    ],
    "hackernews": [
        "Progressive tool routing changes the game for AI dev efficiency. {url}",
        "The LLM Waterfall Pattern solves this: Primary API -> Secondary API -> Local models -> Queue. {url}",
        "Dual-tier memory architecture: L1 for session scratchpad, L2 for permanent semantic storage. {url}",
    ],
    "bluesky": [
        "Progressive tool routing + persistent memory = reliable AI agents. {url}",
        "60% token reduction with progressive tool routing. {url}",
    ],
}
