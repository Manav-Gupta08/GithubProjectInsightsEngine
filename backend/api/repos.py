"""
RESTful endpoints for repository analysis.

Routes:
    GET /api/repos/<owner>/<repo>
        → Full analysis of a single repository

    GET /api/repos/compare?repo1=owner/repo&repo2=owner/repo
        → Side-by-side comparison of two repositories

    GET /api/repos/<owner>/<repo>/ai-insights
        → LLM-generated summary (feature-flagged, requires ANTHROPIC_API_KEY)

    DELETE /api/cache
        → Clear in-memory cache (admin / dev use)
"""

import os
from flask import Blueprint, request
from backend.api.responses import success, error, ErrorCode
from backend.services import github_service as gh
from backend.services import analysis_service as analysis
from backend.services import ai_service

repos_bp = Blueprint("repos", __name__)


# ── Input helpers ──────────────────────────────────────────────────────────

def _validate_slug(slug: str, param_name: str = "repo"):
    """
    Validate that `slug` is in 'owner/repo' format.
    Returns (owner, repo) tuple or raises ValueError with a message.
    """
    if not slug:
        raise ValueError(f"Missing required parameter: {param_name}")
    parts = slug.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError(
            f"'{param_name}' must be in 'owner/repo' format, e.g. 'facebook/react'"
        )
    return parts[0], parts[1]


def _build_repo_payload(owner: str, repo: str) -> tuple[dict, bool]:
    """
    Fetch GitHub data, run analysis, and return a structured payload dict.
    Second return value indicates whether data came from cache.

    Raises ValueError / PermissionError / RuntimeError on fetch failures.
    """
    meta, from_cache         = gh.fetch_repo_meta(owner, repo)
    commits, _               = gh.fetch_commits(owner, repo, days=30)
    contributors, _          = gh.fetch_contributors(owner, repo, top_n=10)
    pulls, _                 = gh.fetch_pull_requests(owner, repo)
    releases, _              = gh.fetch_releases(owner, repo)

    analytics    = analysis.compute_score(meta, commits, contributors, pulls, releases)
    warnings     = analysis.detect_red_flags(analytics, meta)
    recommendation = analysis.build_recommendation(analytics, meta)

    shaped_meta = {
        "full_name":      meta.get("full_name", ""),
        "description":    meta.get("description", ""),
        "language":       meta.get("language", ""),
        "stars":          meta.get("stargazers_count", 0),
        "forks":          meta.get("forks_count", 0),
        "open_issues":    meta.get("open_issues_count", 0),
        "watchers":       meta.get("watchers_count", 0),
        "created_at":     meta.get("created_at", ""),
        "updated_at":     meta.get("updated_at", ""),
        "html_url":       meta.get("html_url", ""),
        "archived":       meta.get("archived", False),
        "license":        (meta.get("license") or {}).get("spdx_id", "None"),
        "default_branch": meta.get("default_branch", "main"),
        "topics":         meta.get("topics", []),
    }

    shaped_contributors = [
        {
            "login":         c.get("login", "anonymous"),
            "contributions": c.get("contributions", 0),
            "avatar_url":    c.get("avatar_url", ""),
            "html_url":      c.get("html_url", ""),
        }
        for c in contributors
    ]

    return {
        "repo":           shaped_meta,
        "health":         analytics,
        "contributors":   shaped_contributors,
        "warnings":       warnings,
        "recommendation": recommendation,
    }, from_cache


# ══════════════════════════════════════════════════════════════
#  GET /api/repos/<owner>/<repo>
# ══════════════════════════════════════════════════════════════

@repos_bp.route("/repos/<owner>/<repo>", methods=["GET"])
def get_repo(owner: str, repo: str):
    """
    Analyse a single GitHub repository.

    Path params:
        owner  — GitHub username or organisation
        repo   — Repository name

    Query params:
        days   — Commit lookback window (1–90, default 30)

    Response 200:
        { "success": true, "data": { repo, health, contributors, warnings, recommendation } }
    """
    try:
        days = int(request.args.get("days", 30))
        days = max(1, min(days, 90))
    except ValueError:
        days = 30

    try:
        payload, cached = _build_repo_payload(owner, repo)
        return success(payload, cached=cached)
    except ValueError as exc:
        return error(ErrorCode.REPO_NOT_FOUND, str(exc), status=404)
    except PermissionError as exc:
        return error(ErrorCode.RATE_LIMIT, str(exc), status=429)
    except Exception as exc:
        return error(ErrorCode.SERVER_ERROR, f"Unexpected error: {exc}", status=500)


# ══════════════════════════════════════════════════════════════
#  GET /api/repos/compare
# ══════════════════════════════════════════════════════════════

@repos_bp.route("/repos/compare", methods=["GET"])
def compare_repos():
    """
    Compare two GitHub repositories side-by-side.

    Query params:
        repo1  — First  repo slug (owner/repo)
        repo2  — Second repo slug (owner/repo)

    Response 200:
        {
          "success": true,
          "data": {
            "repo_1": { repo, health, contributors, warnings, recommendation },
            "repo_2": { repo, health, contributors, warnings, recommendation },
            "comparison": { winners, summary }
          }
        }
    """
    slug1 = request.args.get("repo1", "").strip()
    slug2 = request.args.get("repo2", "").strip()

    # Validate both slugs
    validation_errors = []
    for name, slug in [("repo1", slug1), ("repo2", slug2)]:
        try:
            _validate_slug(slug, name)
        except ValueError as exc:
            validation_errors.append(str(exc))

    if validation_errors:
        return error(
            ErrorCode.VALIDATION_ERROR,
            "Invalid query parameters",
            details={"errors": validation_errors},
        )

    results = {}
    for key, slug in [("repo_1", slug1), ("repo_2", slug2)]:
        owner, repo = slug.split("/", 1)
        try:
            payload, _ = _build_repo_payload(owner, repo)
            results[key] = payload
        except ValueError as exc:
            return error(ErrorCode.REPO_NOT_FOUND, f"{slug}: {exc}", status=404)
        except PermissionError as exc:
            return error(ErrorCode.RATE_LIMIT, str(exc), status=429)
        except Exception as exc:
            return error(ErrorCode.SERVER_ERROR, f"{slug}: {exc}", status=500)

    comparison = analysis.compare_repos(
        results["repo_1"]["health"],
        results["repo_2"]["health"],
    )

    return success({**results, "comparison": comparison})


# ══════════════════════════════════════════════════════════════
#  GET /api/repos/<owner>/<repo>/ai-insights
# ══════════════════════════════════════════════════════════════

@repos_bp.route("/repos/<owner>/<repo>/ai-insights", methods=["GET"])
def ai_insights(owner: str, repo: str):
    """
    Generate an LLM-powered summary for a repository.

    Feature-flagged: requires AI_INSIGHTS_ENABLED=true and GEMINI_API_KEY
    to be set in the environment.

    Response 200:
        { "success": true, "data": { "insight": "..." } }
    Response 503:
        AI insights disabled or API key not configured.
    """
    if not ai_service.is_enabled():
        return error(
            "AI_INSIGHTS_DISABLED",
            "AI insights are not enabled. Set AI_INSIGHTS_ENABLED=true and GEMINI_API_KEY in .env.",
            status=503,
        )

    try:
        meta, _        = gh.fetch_repo_meta(owner, repo)
        commits, _     = gh.fetch_commits(owner, repo, days=30)
        contributors,_ = gh.fetch_contributors(owner, repo, top_n=10)
        pulls, _       = gh.fetch_pull_requests(owner, repo)
        releases, _    = gh.fetch_releases(owner, repo)

        analytics = analysis.compute_score(meta, commits, contributors, pulls, releases)
        warnings  = analysis.detect_red_flags(analytics, meta)

        insight = ai_service.generate_insight(meta, analytics, warnings)
        return success({"insight": insight})

    except ValueError as exc:
        return error(ErrorCode.REPO_NOT_FOUND, str(exc), status=404)
    except PermissionError as exc:
        return error(ErrorCode.RATE_LIMIT, str(exc), status=429)
    except Exception as exc:
        return error(ErrorCode.SERVER_ERROR, str(exc), status=500)


# ══════════════════════════════════════════════════════════════
#  DELETE /api/cache
# ══════════════════════════════════════════════════════════════

@repos_bp.route("/cache", methods=["DELETE"])
def clear_cache():
    """
    Clear in-memory cache.
    Body (optional JSON): { "repo": "owner/repo" }
    """
    body      = request.get_json(silent=True) or {}
    repo_slug = body.get("repo", "")

    if repo_slug and repo_slug.count("/") == 1:
        owner, repo = repo_slug.split("/", 1)
        gh.clear_cache(owner, repo)
        return success({"cleared": repo_slug})
    else:
        gh.clear_cache()
        return success({"cleared": "all"})
