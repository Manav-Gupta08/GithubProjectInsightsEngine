"""
Batch analysis endpoint — analyse multiple repos at once
and return them ranked by health score.

Route:
    POST /api/repos/batch
    Body: { "repos": ["owner/repo", "owner/repo", ...] }   (max 10)
"""

from flask import Blueprint, request
from backend.api.responses import success, error, ErrorCode
from backend.services import github_service as gh
from backend.services import analysis_service as analysis

batch_bp = Blueprint("batch", __name__)

MAX_BATCH_SIZE = 10


@batch_bp.route("/repos/batch", methods=["POST"])
def batch_analyse():
    """
    Analyse a list of repositories and return ranked results.

    Request body:
        {
          "repos": ["facebook/react", "vuejs/vue", "sveltejs/svelte"]
        }

    Response 200:
        {
          "success": true,
          "data": {
            "results": [
              { "slug": "facebook/react", "health_score": 84, "label": "Active", ... },
              ...
            ],
            "ranked_by": "health_score",
            "total": 3,
            "failed": []
          }
        }

    Repos that fail (invalid slug, not found, rate-limited) are collected
    in the "failed" list rather than aborting the whole batch.
    """
    body = request.get_json(silent=True)
    if not body or "repos" not in body:
        return error(
            ErrorCode.VALIDATION_ERROR,
            "Request body must be JSON with a 'repos' key: { \"repos\": [\"owner/repo\", ...] }",
        )

    repo_list = body["repos"]

    if not isinstance(repo_list, list) or len(repo_list) == 0:
        return error(ErrorCode.VALIDATION_ERROR, "'repos' must be a non-empty list.")

    if len(repo_list) > MAX_BATCH_SIZE:
        return error(
            ErrorCode.VALIDATION_ERROR,
            f"Batch size exceeds maximum of {MAX_BATCH_SIZE}. Got {len(repo_list)}.",
        )

    # Deduplicate while preserving order
    seen = set()
    unique_repos = []
    for slug in repo_list:
        slug = str(slug).strip()
        if slug not in seen:
            seen.add(slug)
            unique_repos.append(slug)

    results = []
    failed  = []

    for slug in unique_repos:
        # Validate slug format
        parts = slug.split("/")
        if len(parts) != 2 or not all(parts):
            failed.append({"slug": slug, "reason": "Invalid format — expected 'owner/repo'"})
            continue

        owner, repo = parts

        try:
            meta, _         = gh.fetch_repo_meta(owner, repo)
            commits, _      = gh.fetch_commits(owner, repo, days=30)
            contributors, _ = gh.fetch_contributors(owner, repo, top_n=5)
            pulls, _        = gh.fetch_pull_requests(owner, repo)
            releases, _     = gh.fetch_releases(owner, repo)

            analytics  = analysis.compute_score(meta, commits, contributors, pulls, releases)
            warnings   = analysis.detect_red_flags(analytics, meta)

            results.append({
                "slug":         slug,
                "full_name":    meta.get("full_name", slug),
                "description":  meta.get("description", ""),
                "language":     meta.get("language", ""),
                "stars":        meta.get("stargazers_count", 0),
                "html_url":     meta.get("html_url", ""),
                "health_score": analytics["health_score"],
                "label":        analytics["label"],
                "metrics":      analytics["metrics"],
                "warning_count": len(warnings),
                "warnings":     warnings,
            })

        except ValueError as exc:
            failed.append({"slug": slug, "reason": str(exc)})
        except PermissionError as exc:
            # Rate limit hit — stop processing remaining repos
            return error(ErrorCode.RATE_LIMIT, str(exc), status=429)
        except Exception as exc:
            failed.append({"slug": slug, "reason": f"Unexpected error: {exc}"})

    # Sort results by health score descending
    results.sort(key=lambda r: r["health_score"], reverse=True)

    # Add rank position
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return success({
        "results":    results,
        "ranked_by":  "health_score",
        "total":      len(results),
        "failed":     failed,
    })
