"""
Integration tests for the Flask API endpoints.

Uses unittest.mock to patch GitHub service calls so tests
run offline without consuming real API rate limits.

Run with: pytest -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from backend.app import create_app


# ═══════════════════════════════════════════════════════════════
#  SHARED FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _recent_iso(days_ago: int = 1) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _fake_meta(slug="facebook/react") -> dict:
    owner, repo = slug.split("/")
    return {
        "full_name":        slug,
        "description":      "A test repository",
        "language":         "JavaScript",
        "stargazers_count": 5000,
        "forks_count":      500,
        "open_issues_count": 30,
        "watchers_count":   5000,
        "created_at":       "2020-01-01T00:00:00Z",
        "updated_at":       _recent_iso(1),
        "html_url":         f"https://github.com/{slug}",
        "archived":         False,
        "license":          {"spdx_id": "MIT"},
        "default_branch":   "main",
        "topics":           ["javascript", "ui"],
    }


def _fake_commits(n=20):
    return [
        {"commit": {"author": {"date": _recent_iso(i)}}}
        for i in range(n)
    ]


def _fake_contributors(n=5):
    return [
        {"login": f"user{i}", "contributions": 100 - i * 10,
         "avatar_url": "https://avatars.githubusercontent.com/u/1",
         "html_url": f"https://github.com/user{i}"}
        for i in range(n)
    ]


def _fake_pulls(merged=8, rejected=2):
    return (
        [{"merged_at": _recent_iso(i), "state": "closed"} for i in range(merged)] +
        [{"merged_at": None, "state": "closed"}            for _ in range(rejected)]
    )


def _fake_releases(n=3):
    return [{"published_at": _recent_iso(i * 30)} for i in range(n)]


# Helper: patch all github_service calls at once
def _patch_github(meta_slug="facebook/react"):
    patches = {
        "services.github_service.fetch_repo_meta":     (_fake_meta(meta_slug), False),
        "services.github_service.fetch_commits":        (_fake_commits(), False),
        "services.github_service.fetch_contributors":   (_fake_contributors(), False),
        "services.github_service.fetch_pull_requests":  (_fake_pulls(), False),
        "services.github_service.fetch_releases":       (_fake_releases(), False),
    }
    return {k: patch(k, return_value=v) for k, v in patches.items()}


# ═══════════════════════════════════════════════════════════════
#  GET /api/repos/<owner>/<repo>
# ═══════════════════════════════════════════════════════════════

class TestGetRepo:
    def test_success_200(self, client):
        patcher = _patch_github()
        with patcher["services.github_service.fetch_repo_meta"], \
             patcher["services.github_service.fetch_commits"], \
             patcher["services.github_service.fetch_contributors"], \
             patcher["services.github_service.fetch_pull_requests"], \
             patcher["services.github_service.fetch_releases"]:

            resp = client.get("/api/repos/facebook/react")
            assert resp.status_code == 200

    def test_response_envelope(self, client):
        patcher = _patch_github()
        with patcher["services.github_service.fetch_repo_meta"], \
             patcher["services.github_service.fetch_commits"], \
             patcher["services.github_service.fetch_contributors"], \
             patcher["services.github_service.fetch_pull_requests"], \
             patcher["services.github_service.fetch_releases"]:

            data = client.get("/api/repos/facebook/react").get_json()
            assert data["success"] is True
            assert "data" in data
            assert "meta" in data

    def test_response_data_keys(self, client):
        patcher = _patch_github()
        with patcher["services.github_service.fetch_repo_meta"], \
             patcher["services.github_service.fetch_commits"], \
             patcher["services.github_service.fetch_contributors"], \
             patcher["services.github_service.fetch_pull_requests"], \
             patcher["services.github_service.fetch_releases"]:

            payload = client.get("/api/repos/facebook/react").get_json()["data"]
            for key in ("repo", "health", "contributors", "warnings", "recommendation"):
                assert key in payload, f"Missing key: {key}"

    def test_health_metrics_present(self, client):
        patcher = _patch_github()
        with patcher["services.github_service.fetch_repo_meta"], \
             patcher["services.github_service.fetch_commits"], \
             patcher["services.github_service.fetch_contributors"], \
             patcher["services.github_service.fetch_pull_requests"], \
             patcher["services.github_service.fetch_releases"]:

            health = client.get("/api/repos/facebook/react").get_json()["data"]["health"]
            assert "health_score" in health
            assert "metrics" in health
            assert set(health["metrics"].keys()) == {"activity", "community", "maintenance"}

    def test_404_for_nonexistent_repo(self, client):
        with patch(
            "services.github_service.fetch_repo_meta",
            side_effect=ValueError("Repository not found.")
        ):
            resp = client.get("/api/repos/nobody/doesnotexist999")
            assert resp.status_code == 404
            data = resp.get_json()
            assert data["success"] is False
            assert data["error"]["code"] == "REPO_NOT_FOUND"

    def test_429_for_rate_limit(self, client):
        with patch(
            "services.github_service.fetch_repo_meta",
            side_effect=PermissionError("Rate limit exceeded.")
        ):
            resp = client.get("/api/repos/facebook/react")
            assert resp.status_code == 429
            assert resp.get_json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_warnings_is_list(self, client):
        patcher = _patch_github()
        with patcher["services.github_service.fetch_repo_meta"], \
             patcher["services.github_service.fetch_commits"], \
             patcher["services.github_service.fetch_contributors"], \
             patcher["services.github_service.fetch_pull_requests"], \
             patcher["services.github_service.fetch_releases"]:

            warnings = client.get("/api/repos/facebook/react").get_json()["data"]["warnings"]
            assert isinstance(warnings, list)


# ═══════════════════════════════════════════════════════════════
#  GET /api/repos/compare
# ═══════════════════════════════════════════════════════════════

class TestCompare:
    def _do_compare(self, client):
        patcher = _patch_github()
        with patcher["services.github_service.fetch_repo_meta"], \
             patcher["services.github_service.fetch_commits"], \
             patcher["services.github_service.fetch_contributors"], \
             patcher["services.github_service.fetch_pull_requests"], \
             patcher["services.github_service.fetch_releases"]:
            return client.get("/api/repos/compare?repo1=facebook/react&repo2=vuejs/vue")

    def test_success_200(self, client):
        assert self._do_compare(client).status_code == 200

    def test_response_has_both_repos(self, client):
        data = self._do_compare(client).get_json()["data"]
        assert "repo_1" in data
        assert "repo_2" in data
        assert "comparison" in data

    def test_comparison_has_winners(self, client):
        comparison = self._do_compare(client).get_json()["data"]["comparison"]
        assert "winners" in comparison
        assert "summary" in comparison

    def test_missing_repo1_returns_400(self, client):
        resp = client.get("/api/repos/compare?repo2=vuejs/vue")
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_invalid_slug_returns_400(self, client):
        resp = client.get("/api/repos/compare?repo1=notaslug&repo2=vuejs/vue")
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════
#  POST /api/repos/batch
# ═══════════════════════════════════════════════════════════════

class TestBatch:
    def _do_batch(self, client, repos):
        patcher = _patch_github()
        with patcher["services.github_service.fetch_repo_meta"], \
             patcher["services.github_service.fetch_commits"], \
             patcher["services.github_service.fetch_contributors"], \
             patcher["services.github_service.fetch_pull_requests"], \
             patcher["services.github_service.fetch_releases"]:
            return client.post(
                "/api/repos/batch",
                json={"repos": repos},
                content_type="application/json",
            )

    def test_success_200(self, client):
        resp = self._do_batch(client, ["facebook/react", "vuejs/vue"])
        assert resp.status_code == 200

    def test_results_are_ranked(self, client):
        data = self._do_batch(client, ["facebook/react", "vuejs/vue"]).get_json()["data"]
        scores = [r["health_score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_results_have_rank_field(self, client):
        data = self._do_batch(client, ["facebook/react"]).get_json()["data"]
        assert data["results"][0]["rank"] == 1

    def test_missing_body_returns_400(self, client):
        resp = client.post("/api/repos/batch", content_type="application/json")
        assert resp.status_code == 400

    def test_empty_list_returns_400(self, client):
        resp = client.post("/api/repos/batch", json={"repos": []})
        assert resp.status_code == 400

    def test_exceeding_limit_returns_400(self, client):
        resp = client.post("/api/repos/batch", json={"repos": [f"a/b{i}" for i in range(11)]})
        assert resp.status_code == 400

    def test_invalid_slugs_go_to_failed(self, client):
        patcher = _patch_github()
        with patcher["services.github_service.fetch_repo_meta"], \
             patcher["services.github_service.fetch_commits"], \
             patcher["services.github_service.fetch_contributors"], \
             patcher["services.github_service.fetch_pull_requests"], \
             patcher["services.github_service.fetch_releases"]:
            data = client.post(
                "/api/repos/batch",
                json={"repos": ["facebook/react", "notavalidslug"]},
            ).get_json()["data"]
            assert any(f["slug"] == "notavalidslug" for f in data["failed"])


# ═══════════════════════════════════════════════════════════════
#  DELETE /api/cache
# ═══════════════════════════════════════════════════════════════

class TestCache:
    def test_clear_all_cache(self, client):
        with patch("services.github_service.clear_cache") as mock_clear:
            resp = client.delete("/api/cache", json={})
            assert resp.status_code == 200
            mock_clear.assert_called_once_with()

    def test_clear_specific_repo_cache(self, client):
        with patch("services.github_service.clear_cache") as mock_clear:
            resp = client.delete("/api/cache", json={"repo": "facebook/react"})
            assert resp.status_code == 200
            mock_clear.assert_called_once_with("facebook", "react")
