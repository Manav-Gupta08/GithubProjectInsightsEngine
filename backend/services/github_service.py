"""
All GitHub REST API communication lives here.

Changes from v1:
  - All public functions now return (data, from_cache) tuples
    so callers can include cache status in API responses.
  - Added fetch_pull_requests() for PR merge rate signal.
  - Added fetch_releases() for release frequency signal.
  - Improved error messages with actionable guidance.
"""

import os
import time
import requests
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN", "")
CACHE_TTL       = int(os.getenv("CACHE_TTL", 300))  # seconds

# Simple in-memory cache: key → { "ts": float, "data": any }
# Phase 2 will replace this with Redis; the interface stays identical.
_CACHE: dict = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _headers() -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def _cache_get(key: str):
    entry = _CACHE.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"], True
    return None, False


def _cache_set(key: str, data):
    _CACHE[key] = {"ts": time.time(), "data": data}


def _get(url: str, params: dict = None):
    """
    Single GET request with structured error raising.

    Raises:
        ValueError      — 404 (repo not found)
        PermissionError — 403 / 429 (rate limit)
        RuntimeError    — any other failure
    """
    resp = requests.get(url, headers=_headers(), params=params, timeout=10)

    if resp.status_code == 404:
        raise ValueError(
            "Repository not found. Verify the owner/repo slug is correct and the repo is public."
        )
    if resp.status_code in (403, 429):
        reset_ts  = resp.headers.get("X-RateLimit-Reset", "unknown")
        remaining = resp.headers.get("X-RateLimit-Remaining", "0")
        raise PermissionError(
            f"GitHub API rate limit exceeded (remaining: {remaining}). "
            f"Limit resets at Unix timestamp {reset_ts}. "
            "Set GITHUB_TOKEN in your .env to raise the limit from 60 to 5,000 req/hr."
        )
    if not resp.ok:
        raise RuntimeError(
            f"GitHub API returned {resp.status_code}: {resp.text[:300]}"
        )

    return resp.json()


def _paginate(url: str, params: dict = None, max_pages: int = 3) -> list:
    """Collect paginated results up to max_pages pages."""
    params = dict(params or {})
    params.setdefault("per_page", 100)
    results = []

    for page in range(1, max_pages + 1):
        params["page"] = page
        data = _get(url, params)
        if not data:
            break
        results.extend(data)
        if len(data) < params["per_page"]:
            break  # last page

    return results


# ---------------------------------------------------------------------------
# Public API — each returns (data, from_cache: bool)
# ---------------------------------------------------------------------------

def fetch_repo_meta(owner: str, repo: str) -> tuple[dict, bool]:
    """Fetch repository metadata (stars, forks, issues, description, …)."""
    key = f"{owner}/{repo}/meta"
    cached, hit = _cache_get(key)
    if hit:
        return cached, True

    data = _get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
    _cache_set(key, data)
    return data, False


def fetch_commits(owner: str, repo: str, days: int = 30) -> tuple[list, bool]:
    """Fetch commits from the last `days` days (up to 300)."""
    key = f"{owner}/{repo}/commits/{days}"
    cached, hit = _cache_get(key)
    if hit:
        return cached, True

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    data  = _paginate(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
        params={"since": since},
        max_pages=3,
    )
    _cache_set(key, data)
    return data, False


def fetch_contributors(owner: str, repo: str, top_n: int = 10) -> tuple[list, bool]:
    """Fetch top N contributors sorted by commit count."""
    key = f"{owner}/{repo}/contributors"
    cached, hit = _cache_get(key)
    if hit:
        return cached[:top_n], True

    data = _paginate(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors",
        params={"anon": "false"},
        max_pages=1,
    )
    _cache_set(key, data)
    return data[:top_n], False


def fetch_pull_requests(owner: str, repo: str) -> tuple[list, bool]:
    """
    Fetch recent closed pull requests (last 100) to compute merge rate.

    We fetch 'closed' state — GitHub includes both merged and rejected PRs.
    The analysis layer distinguishes them via pr["merged_at"] != None.
    """
    key = f"{owner}/{repo}/pulls"
    cached, hit = _cache_get(key)
    if hit:
        return cached, True

    data = _paginate(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
        params={"state": "closed", "sort": "updated", "direction": "desc"},
        max_pages=1,   # 100 PRs is a representative sample
    )
    _cache_set(key, data)
    return data, False


def fetch_releases(owner: str, repo: str) -> tuple[list, bool]:
    """
    Fetch the last 30 releases to compute release frequency.
    Repos with no releases return an empty list (not an error).
    """
    key = f"{owner}/{repo}/releases"
    cached, hit = _cache_get(key)
    if hit:
        return cached, True

    try:
        data = _paginate(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases",
            params={},
            max_pages=1,
        )
    except ValueError:
        # Some repos disable releases — treat as empty list
        data = []

    _cache_set(key, data)
    return data, False


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

def clear_cache(owner: str = None, repo: str = None):
    """Clear all cache or just one repo's entries."""
    if owner and repo:
        prefix = f"{owner}/{repo}/"
        for k in [k for k in _CACHE if k.startswith(prefix)]:
            del _CACHE[k]
    else:
        _CACHE.clear()


def cache_stats() -> dict:
    """Return basic cache statistics (useful for health checks)."""
    now = time.time()
    live = sum(1 for v in _CACHE.values() if (now - v["ts"]) < CACHE_TTL)
    return {
        "total_entries": len(_CACHE),
        "live_entries":  live,
        "ttl_seconds":   CACHE_TTL,
    }
