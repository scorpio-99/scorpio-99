"""Fetch user stats from the GitHub GraphQL API."""

import json
import os
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_API_TIMEOUT = 30  # seconds


class GitHubAPIError(Exception):
    """Raised when a GitHub GraphQL request fails."""


@dataclass
class GitHubStats:
    repos: int = 0
    stars: int = 0
    total_contributions: int = 0
    member_since: int = 0
    top_languages: list[str] = field(default_factory=list)


QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection { contributionYears }

    allRepos: repositories(ownerAffiliations: OWNER, isFork: false) {
      totalCount
    }

    publicRepos: repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes { stargazerCount }
    }

    allReposWithLang: repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

YEARLY_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { totalContributions }
    }
  }
}
"""


def _get_nested(data: dict[str, Any], *keys: str) -> Any:
    """Safely traverse nested dicts; raise on missing keys."""
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            path = " -> ".join(keys)
            raise GitHubAPIError(
                f"Unexpected API response structure: missing key '{key}' in path [{path}]"
            )
        current = current[key]
    return current


def _graphql(token: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Execute a GraphQL query against the GitHub API."""
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(req, timeout=_API_TIMEOUT) as resp:
            body: dict[str, Any] = json.loads(resp.read().decode())
    except HTTPError as exc:
        raise GitHubAPIError(
            f"GitHub API returned HTTP {exc.code}: {exc.reason}"
        ) from None
    except URLError as exc:
        raise GitHubAPIError(
            f"Failed to reach GitHub API: {exc.reason}"
        ) from None
    except TimeoutError:
        raise GitHubAPIError(
            "GitHub API request timed out"
        ) from None

    if "errors" in body:
        messages = [e.get("message", str(e)) for e in body["errors"]]
        raise GitHubAPIError(
            f"GraphQL errors: {'; '.join(messages)}"
        )

    if "data" not in body:
        raise GitHubAPIError("GitHub API response missing 'data' key")

    return body


def _fetch_total_contributions(token: str, username: str, years: list[int]) -> int:
    """Sum contributions across all years."""
    total = 0
    for year in years:
        data = _graphql(token, YEARLY_QUERY, {
            "login": username,
            "from": f"{year}-01-01T00:00:00Z",
            "to": f"{year}-12-31T23:59:59Z",
        })
        total += _get_nested(
            data, "data", "user", "contributionsCollection",
            "contributionCalendar", "totalContributions",
        )
    return total


def fetch_stats(username: str) -> GitHubStats:
    """Fetch GitHub user statistics via GraphQL API."""
    token = os.environ.get("METRICS_TOKEN", "")
    if not token:
        raise RuntimeError("METRICS_TOKEN environment variable not set")

    data = _graphql(token, QUERY, {"login": username})
    user = _get_nested(data, "data", "user")
    contribs = _get_nested(user, "contributionsCollection")

    public_nodes: list[dict[str, Any]] = _get_nested(user, "publicRepos", "nodes")
    stars = sum(n.get("stargazerCount", 0) for n in public_nodes)

    years: list[int] = contribs["contributionYears"]
    total_contributions = _fetch_total_contributions(token, username, years)

    # Top languages from ALL repos by bytes (public + private)
    lang_bytes: dict[str, int] = {}
    for node in _get_nested(user, "allReposWithLang", "nodes"):
        for edge in node.get("languages", {}).get("edges", []):
            name = edge["node"]["name"]
            lang_bytes[name] = lang_bytes.get(name, 0) + edge["size"]
    top_languages = sorted(lang_bytes, key=lang_bytes.get, reverse=True)[:3]

    created = user.get("createdAt", "")
    member_since = int(created[:4]) if created else 0

    return GitHubStats(
        repos=_get_nested(user, "allRepos", "totalCount"),
        stars=stars,
        total_contributions=total_contributions,
        member_since=member_since,
        top_languages=top_languages,
    )
