"""
Unit tests for the scoring engine and red-flag detector.
Run with: pytest -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.services import analysis_service as analysis


# ═══════════════════════════════════════════════════════════════
#  FIXTURES — minimal fake data
# ═══════════════════════════════════════════════════════════════

def _make_meta(**overrides) -> dict:
    base = {
        "full_name":        "test/repo",
        "description":      "A test repo",
        "language":         "Python",
        "stargazers_count": 500,
        "forks_count":      50,
        "open_issues_count": 20,
        "archived":         False,
        "license":          {"spdx_id": "MIT"},
    }
    return {**base, **overrides}


def _make_commit(days_ago: int = 1) -> dict:
    from datetime import datetime, timedelta, timezone
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {"commit": {"author": {"date": dt.isoformat()}}}


def _make_pr(merged: bool = True) -> dict:
    from datetime import datetime, timezone
    merged_at = datetime.now(timezone.utc).isoformat() if merged else None
    return {"merged_at": merged_at, "state": "closed"}


def _make_release(days_ago: int = 10) -> dict:
    from datetime import datetime, timedelta, timezone
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {"published_at": dt.isoformat()}


# ═══════════════════════════════════════════════════════════════
#  compute_score — basic shape
# ═══════════════════════════════════════════════════════════════

class TestComputeScore:
    def _run(self, meta=None, commits=None, contributors=None, pulls=None, releases=None):
        return analysis.compute_score(
            meta         or _make_meta(),
            commits      or [_make_commit(i) for i in range(1, 21)],
            contributors or [{"login": f"u{i}", "contributions": 100-i} for i in range(5)],
            pulls        or [_make_pr(True)] * 8 + [_make_pr(False)] * 2,
            releases     or [_make_release(30)],
        )

    def test_returns_required_keys(self):
        result = self._run()
        for key in ("health_score", "label", "metrics", "signal_scores",
                    "commit_trend", "pr_merge_rate"):
            assert key in result, f"Missing key: {key}"

    def test_metrics_has_three_dimensions(self):
        result = self._run()
        assert set(result["metrics"].keys()) == {"activity", "community", "maintenance"}

    def test_score_in_range(self):
        result = self._run()
        assert 0 <= result["health_score"] <= 100

    def test_active_label_for_healthy_repo(self):
        """A well-maintained repo should score Active."""
        commits = [_make_commit(i) for i in range(1, 61)]   # 60 recent commits
        meta    = _make_meta(stargazers_count=5000, open_issues_count=10)
        contribs = [{"login": f"u{i}", "contributions": 200} for i in range(15)]
        pulls    = [_make_pr(True)] * 20
        releases = [_make_release(20), _make_release(50)]
        result   = analysis.compute_score(meta, commits, contribs, pulls, releases)
        assert result["label"] == "Active"
        assert result["health_score"] >= 70

    def test_inactive_label_for_dead_repo(self):
        """A repo with no commits and no stars should score Inactive."""
        result = analysis.compute_score(
            _make_meta(stargazers_count=0, open_issues_count=0),
            commits=[],
            contributors=[],
            pulls=[],
            releases=[],
        )
        assert result["label"] == "Inactive"
        assert result["health_score"] < 40

    def test_pr_merge_rate_computed(self):
        """PR merge rate should reflect ratio of merged to closed PRs."""
        pulls  = [_make_pr(True)] * 7 + [_make_pr(False)] * 3
        result = self._run(pulls=pulls)
        assert abs(result["pr_merge_rate"] - 0.7) < 0.01

    def test_no_pulls_gives_neutral_pr_rate(self):
        """No PR data should not crash and should return None."""
        result = self._run(pulls=[])
        assert result["pr_merge_rate"] is None

    def test_commit_trend_has_30_days(self):
        result = self._run()
        assert len(result["commit_trend"]["labels"]) == 30
        assert len(result["commit_trend"]["counts"]) == 30


# ═══════════════════════════════════════════════════════════════
#  detect_red_flags
# ═══════════════════════════════════════════════════════════════

class TestDetectRedFlags:
    def _analytics(self, **overrides) -> dict:
        base = {
            "health_score":      60,
            "label":             "Moderate",
            "days_since_last":   5,
            "commit_count_30d":  20,
            "open_issues":       15,
            "pr_merge_rate":     0.8,
            "contributor_count": 5,
            "star_count":        500,
            "signal_scores":     {"release_cadence": 0.6},
        }
        return {**base, **overrides}

    def test_no_flags_for_healthy_repo(self):
        flags = analysis.detect_red_flags(self._analytics(), _make_meta())
        assert flags == []

    def test_archived_flag(self):
        flags = analysis.detect_red_flags(self._analytics(), _make_meta(archived=True))
        codes = [f["code"] for f in flags]
        assert "ARCHIVED" in codes

    def test_archived_returns_only_one_flag(self):
        """Archived check short-circuits further analysis."""
        flags = analysis.detect_red_flags(
            self._analytics(days_since_last=400, contributor_count=1),
            _make_meta(archived=True),
        )
        assert len(flags) == 1

    def test_no_recent_commits_flag(self):
        analytics = self._analytics(days_since_last=200, commit_count_30d=0)
        flags = analysis.detect_red_flags(analytics, _make_meta())
        codes = [f["code"] for f in flags]
        assert "NO_RECENT_COMMITS" in codes

    def test_single_contributor_flag(self):
        analytics = self._analytics(contributor_count=1)
        flags = analysis.detect_red_flags(analytics, _make_meta())
        codes = [f["code"] for f in flags]
        assert "SINGLE_CONTRIBUTOR" in codes

    def test_issue_backlog_flag(self):
        analytics = self._analytics(open_issues=600, commit_count_30d=2)
        flags = analysis.detect_red_flags(analytics, _make_meta())
        codes = [f["code"] for f in flags]
        assert "ISSUE_BACKLOG" in codes

    def test_low_pr_merge_rate_flag(self):
        analytics = self._analytics(pr_merge_rate=0.15)
        flags = analysis.detect_red_flags(analytics, _make_meta())
        codes = [f["code"] for f in flags]
        assert "LOW_PR_MERGE_RATE" in codes

    def test_flag_has_required_fields(self):
        analytics = self._analytics(contributor_count=1)
        flags = analysis.detect_red_flags(analytics, _make_meta())
        for flag in flags:
            assert "code"     in flag
            assert "severity" in flag
            assert "message"  in flag
            assert flag["severity"] in ("high", "medium", "low")


# ═══════════════════════════════════════════════════════════════
#  compare_repos
# ═══════════════════════════════════════════════════════════════

class TestCompareRepos:
    def _make_analytics(self, score, commits, contribs, stars):
        return {
            "health_score":      score,
            "commit_count_30d":  commits,
            "contributor_count": contribs,
            "star_count":        stars,
        }

    def test_returns_winners_and_summary(self):
        a = self._make_analytics(80, 50, 10, 1000)
        b = self._make_analytics(60, 30,  5,  500)
        result = analysis.compare_repos(a, b)
        assert "winners" in result
        assert "summary" in result

    def test_repo1_wins_all_metrics(self):
        a = self._make_analytics(90, 100, 20, 5000)
        b = self._make_analytics(30,  10,  2,  100)
        result = analysis.compare_repos(a, b)
        for metric, winner in result["winners"].items():
            assert winner == "repo_1", f"Expected repo_1 to win {metric}"

    def test_summary_mentions_winner(self):
        a = self._make_analytics(90, 100, 20, 5000)
        b = self._make_analytics(30,  10,  2,  100)
        result = analysis.compare_repos(a, b)
        assert "Repo 1" in result["summary"]


# ═══════════════════════════════════════════════════════════════
#  compute_commit_trend
# ═══════════════════════════════════════════════════════════════

class TestCommitTrend:
    def test_returns_30_labels(self):
        trend = analysis.compute_commit_trend([])
        assert len(trend["labels"]) == 30
        assert len(trend["counts"]) == 30

    def test_counts_commits_correctly(self):
        from datetime import datetime, timedelta, timezone
        today_commit = {
            "commit": {
                "author": {
                    "date": datetime.now(timezone.utc).isoformat()
                }
            }
        }
        trend = analysis.compute_commit_trend([today_commit, today_commit])
        assert trend["counts"][-1] == 2   # last element = today

    def test_empty_commits_all_zeros(self):
        trend = analysis.compute_commit_trend([])
        assert all(c == 0 for c in trend["counts"])
