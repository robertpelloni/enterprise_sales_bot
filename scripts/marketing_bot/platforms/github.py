"""
GitHub Engagement Module

Engages with relevant GitHub repositories through:
- Starring repos
- Commenting on issues
- Opening helpful issues
- Contributing to discussions
"""

import json
import os
import urllib.request
from typing import Dict, List, Optional

from ..llm import call_mimo


class GitHubEngagement:
    """Engages with GitHub repositories."""

    # Search queries for finding relevant repos
    SEARCH_QUERIES = [
        "topic:model-context-protocol",
        "topic:mcp-server",
        "topic:ai-agent",
        "topic:llm-infrastructure",
        "MCP server language:typescript",
        "AI agent framework language:go",
    ]

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        self.engaged_repos: List[str] = []

    def _make_request(
        self, url: str, method: str = "GET", data: Optional[dict] = None
    ) -> Optional[dict]:
        """Make a GitHub API request."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HyperNexus-Bot",
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            if data:
                req.data = json.dumps(data).encode()
                headers["Content-Type"] = "application/json"

            resp = urllib.request.urlopen(req, timeout=15)
            return json.loads(resp.read())
        except Exception as e:
            print(f"[GitHub] Request error: {e}")
            return None

    def search_repos(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for repositories."""
        url = f"https://api.github.com/search/repositories?q={query}&sort=updated&per_page={limit}"
        result = self._make_request(url)
        if result:
            return result.get("items", [])
        return []

    def star_repo(self, owner: str, repo: str) -> bool:
        """Star a repository."""
        if not self.github_token:
            print("[GitHub] No token configured for starring")
            return False

        url = f"https://api.github.com/user/starred/{owner}/{repo}"
        result = self._make_request(url, method="PUT")
        return result is not None

    def get_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """Get issues for a repository."""
        url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}&per_page=10"
        result = self._make_request(url)
        if result:
            return [i for i in result if "pull_request" not in i]
        return []

    def generate_issue_comment(
        self, issue_title: str, issue_body: str
    ) -> Optional[str]:
        """Generate a helpful comment for an issue."""
        prompt = f"""Generate a helpful GitHub issue comment.

Issue Title: {issue_title}
Issue Body (first 500 chars): {issue_body[:500]}

Rules:
- Be helpful and constructive
- If it's a question, provide a clear answer
- If it's a bug, suggest debugging steps
- If it's a feature request, discuss trade-offs
- Mention HyperNexus only if directly relevant
- Keep it technical and professional
- Include code examples if helpful

Comment:"""

        system_prompt = """You are a developer who contributes helpful comments to GitHub issues.
You're knowledgeable about AI infrastructure, MCP servers, and developer tools.
You only mention HyperNexus when it directly solves the issue being discussed.
Your comments are technical, helpful, and never promotional."""

        return call_mimo(
            prompt,
            system_prompt=system_prompt,
            max_tokens=300,
            temperature=0.7,
        )

    def find_and_engage(self, max_repos: int = 5) -> List[Dict]:
        """Find relevant repos and engage with them."""
        results = []

        for query in self.SEARCH_QUERIES[:2]:  # Limit queries
            repos = self.search_repos(query, limit=max_repos)

            for repo in repos:
                full_name = repo.get("full_name", "")
                if full_name in self.engaged_repos:
                    continue

                # Star the repo
                owner, name = full_name.split("/") if "/" in full_name else ("", "")
                if owner and name:
                    starred = self.star_repo(owner, name)
                    results.append(
                        {
                            "action": "star",
                            "repo": full_name,
                            "success": starred,
                        }
                    )

                    self.engaged_repos.append(full_name)

        return results

    def get_trending_repos(self) -> List[Dict]:
        """Get trending repositories in AI/ML space."""
        repos = []
        for query in ["topic:ai", "topic:machine-learning", "topic:llm"]:
            results = self.search_repos(query, limit=5)
            repos.extend(results)
        return repos
