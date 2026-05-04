"""
Repository health scoring engine.

═══════════════════════════════════════════════════════════════
SCORING ARCHITECTURE
═══════════════════════════════════════════════════════════════

The 0–100 health score is composed of three dimension scores,
each independently computed from a set of signals:

  Dimension       Weight   Signals
  ─────────────   ──────   ──────────────────────────────────────
  Activity          40%    commit frequency, recency, release cadence
  Community         30%    stars, contributor count, bus-factor
  Maintenance       30%    PR merge rate, issue resolution, stale issues

Each signal returns a normalised 0.0–1.0 value; dimension scores
are weighted averages of their signals; the final score is the
weighted average of dimension scores × 100.

This modular design means:
  - Each signal is independently testable.
  - Weights live in SCORE_CONFIG and can be changed without
    touching the signal functions.
  - New signals can be added by inserting an entry in SCORE_CONFIG.

Labels:
  ≥ 70  → Active
  40–69 → Moderate
  <  40 → Inactive

═══════════════════════════════════════════════════════════════
RED FLAG THRESHOLDS
═══════════════════════════════════════════════════════════════
  - No commits in last 6 months        → "Potentially abandoned"
  - Single contributor > 80% commits   → "Bus-factor risk"
  - Open issues > 500 with low activity → "Issue backlog"
  - PR merge rate < 30%                → "Low PR acceptance"
  - No releases in 1 year + active code → "Unreleased changes"
═══════════════════════════════════════════════════════════════
"""

import math
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone


# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION — change weights here, not in signal functions
# ═══════════════════════════════════════════════════════════════

SCORE_CONFIG = {
    # dimension_name: { weight: float, signals: { name: weight } }
    "activity": {
        "weight": 0.40,
        "signals": {
            "commit_frequency":  0.50,   # commits in last 30 days (log scale)
            "commit_recency":    0.35,   # days since last commit
            "release_cadence":   0.15,   # how often new versions ship
        },
    },
    "community": {
        "weight": 0.30,
        "signals": {
            "stars":             0.40,   # community adoption proxy
            "contributor_count": 0.40,   # bus-factor / diversity
            "forks":             0.20,   # derivative work indicator
        },
    },
    "maintenance": {
        "weight": 0.30,
        "signals": {
            "pr_merge_rate":     0.40,   # % of closed PRs that were merged
            "issue_resolution":  0.35,   # activity relative to open issues
            "stale_issues":      0.25,   # penalty for high stale-issue ratio
        },
    },
}

# Label thresholds
LABEL_ACTIVE   = 70
LABEL_MODERATE = 40

# Red flag thresholds
RF_ABANDONED_DAYS     = 180   # no commits → potentially abandoned
RF_BUS_FACTOR_PCT     = 0.80  # top contributor owns > 80% of commits
RF_ISSUE_BACKLOG      = 500   # open issues with very low commit activity
RF_LOW_PR_MERGE_RATE  = 0.30  # < 30% PRs merged
RF_NO_RELEASE_DAYS    = 365   # no release in a year


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _days_since(iso_str: str) -> float:
    """Days elapsed since an ISO 8601 datetime string (UTC)."""
    if not iso_str:
        return 9_999
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86_400


def _log_scale(value: float, ceiling: float) -> float:
    """
    Map value onto 0–1 using log₁₀, where `ceiling` maps to ≈1.0.
    Used for quantities with diminishing returns (stars, commits).
    """
    if value <= 0:
        return 0.0
    return _clamp(math.log10(value + 1) / math.log10(ceiling + 1))


# ═══════════════════════════════════════════════════════════════
#  SIGNAL FUNCTIONS  (each returns 0.0 – 1.0)
# ═══════════════════════════════════════════════════════════════

# ── Activity signals ───────────────────────────────────────────

def _sig_commit_frequency(commit_count: int) -> float:
    """
    Log scale: 0 commits=0, 10=~0.5, 60+=1.0.
    Ceiling of 60 reflects 2 commits/day as "very active".
    """
    return _log_scale(commit_count, ceiling=60)


def _sig_commit_recency(days_since_last: float) -> float:
    """
    Linear decay over 30 days.
    0 days → 1.0, 15 days → 0.5, 30+ days → 0.0.
    """
    return _clamp(1.0 - days_since_last / 30)


def _sig_release_cadence(releases: list[dict]) -> float:
    """
    Score based on how recently and how often the project ships releases.

    No releases → 0.25 (penalised but not zero; many libs don't tag)
    1 release in last year → 0.5
    Monthly+ releases → 1.0
    """
    if not releases:
        return 0.25  # absence of releases is a soft penalty, not disqualifying

    dates = []
    for r in releases[:12]:  # look at last 12 releases max
        published = r.get("published_at", "")
        if published:
            dates.append(_days_since(published))

    if not dates:
        return 0.25

    # Days since most recent release
    recency_score = _clamp(1.0 - (min(dates) / 365))

    # Frequency: average gap between releases (in days)
    if len(dates) > 1:
        dates_sorted = sorted(dates)
        gaps = [dates_sorted[i+1] - dates_sorted[i] for i in range(len(dates_sorted)-1)]
        avg_gap = sum(gaps) / len(gaps)
        # ≤ 30 days avg gap → 1.0, 365 days → 0.0
        freq_score = _clamp(1.0 - avg_gap / 365)
    else:
        freq_score = 0.4  # only one release; can't measure cadence

    return (recency_score * 0.6 + freq_score * 0.4)


# ── Community signals ──────────────────────────────────────────

def _sig_stars(star_count: int) -> float:
    """Log₁₀ scale: 0→0, 100→~0.5, 10k+→1.0."""
    return _log_scale(star_count, ceiling=10_000)


def _sig_contributor_count(count: int) -> float:
    """Log scale: 1→~0.15, 5→~0.45, 20+→1.0."""
    return _log_scale(count, ceiling=20)


def _sig_forks(fork_count: int) -> float:
    """Log₁₀ scale: 0→0, 50→~0.5, 1000+→1.0."""
    return _log_scale(fork_count, ceiling=1_000)


# ── Maintenance signals ────────────────────────────────────────

def _sig_pr_merge_rate(pulls: list[dict]) -> float:
    """
    Fraction of closed PRs that were actually merged.

    GitHub returns both merged and rejected PRs in the 'closed' state.
    A merged PR has pr["merged_at"] != None.

    No PRs → neutral score of 0.5 (absence of data ≠ bad maintenance).
    """
    if not pulls:
        return 0.5  # no PR data — neutral

    closed  = len(pulls)
    merged  = sum(1 for pr in pulls if pr.get("merged_at"))
    rate    = merged / closed
    return _clamp(rate)


def _sig_issue_resolution(open_issues: int, commit_count: int, star_count: int = 0) -> float:
    """
    Measure how well a repo manages its issue load relative to its size.

    Normalise open_issues against star_count so that a large
    issue count is only penalised if it is disproportionate to community size,
    AND factor in whether commits are happening at all.

    Examples:
      30 commits, 5000 issues, 130k stars -> issues/stars = 0.038 -> healthy
      2  commits, 5000 issues, 200 stars  -> issues/stars = 25.0  -> neglected
    """
    if open_issues == 0:
        return 1.0

    if star_count > 100:
        # Popular repo: normalise issues against community size
        # issues per 1000 stars — below 50 is healthy, above 200 is concerning
        issues_per_k_stars = (open_issues / star_count) * 1000
        size_score = _clamp(1.0 - math.log10(max(issues_per_k_stars, 1)) / math.log10(200))
    else:
        # Small repo: use simple commit/issue ratio
        ratio = commit_count / (open_issues + 1)
        size_score = _clamp(ratio / 0.5)

    # Bonus: recent commits means maintainer is still active
    activity_bonus = min(commit_count / 20, 1.0) * 0.2

    return _clamp(size_score + activity_bonus)


def _sig_stale_issues(open_issues: int, commit_count: int, star_count: int = 0) -> float:
    """
    Penalty for repos where issues pile up with zero maintainer activity.

    Only heavily penalise when BOTH are true:
      1. Issue count is high relative to repo size
      2. Recent commit activity is very low (maintainer absent)
    """
    if open_issues == 0:
        return 1.0

    maintainer_active = commit_count >= 5

    if maintainer_active:
        if star_count > 0:
            issues_per_k_stars = (open_issues / star_count) * 1000
            # Only penalise if ratio is truly extreme (>500 per 1k stars)
            return _clamp(1.0 - math.log10(max(issues_per_k_stars, 1)) / math.log10(500))
        return 0.8  # active but no star context — give benefit of the doubt
    else:
        # Inactive maintainer — raw issue volume matters
        pressure = open_issues / max(commit_count + 1, 1)
        return _clamp(1.0 - math.log10(max(pressure, 1)) / math.log10(50))


# ═══════════════════════════════════════════════════════════════
#  DIMENSION SCORERS
# ═══════════════════════════════════════════════════════════════

def _score_dimension(signals: dict, weights: dict) -> float:
    """
    Compute a weighted average of signal scores.
    signals: { name: float (0–1) }
    weights: { name: float } (do not need to sum to 1; normalised internally)
    """
    total_weight = sum(weights[k] for k in signals)
    if total_weight == 0:
        return 0.0
    return sum(signals[k] * weights[k] for k in signals) / total_weight


# ═══════════════════════════════════════════════════════════════
#  PUBLIC: compute_score
# ═══════════════════════════════════════════════════════════════

def compute_score(
        meta:         dict,
        commits:      list[dict],
        contributors: list[dict],
        pulls:        list[dict],
        releases:     list[dict],
) -> dict:
    """
    Compute the composite health score.

    Returns:
    {
      "health_score":  int (0–100),
      "label":         "Active" | "Moderate" | "Inactive",
      "metrics": {
        "activity":    int (0–100),
        "community":   int (0–100),
        "maintenance": int (0–100),
      },
      "signal_scores": { signal_name: float (0–1) },
      "commit_count_30d": int,
      "last_commit_date": str,
      "days_since_last":  float,
      "contributor_count": int,
      "star_count":        int,
      "open_issues":       int,
      "pr_merge_rate":     float,
      "weekly_avg_commits": float,
      "commit_trend":      { labels, counts },
    }
    """
    # ── Raw stats ──────────────────────────────────────────────
    commit_count    = len(commits)
    contrib_count   = len(contributors)
    star_count      = meta.get("stargazers_count", 0)
    fork_count      = meta.get("forks_count", 0)
    open_issues     = meta.get("open_issues_count", 0)

    last_commit_date = ""
    if commits:
        # Most recent commit is first in the list
        last_commit_date = commits[0].get("commit", {}).get("author", {}).get("date", "")

    # BUGFIX: if no commits in the last 30 days, fall back to meta["pushed_at"]
    # which GitHub always provides. Without this, _days_since("") returns 9999
    # making the repo look like it hasn't been touched since 1997.
    if not last_commit_date:
        last_commit_date = meta.get("pushed_at", "")

    days_since_last = _days_since(last_commit_date)

    # PR merge rate (raw float for red-flag use)
    closed_prs  = len(pulls)
    merged_prs  = sum(1 for pr in pulls if pr.get("merged_at"))
    pr_rate_raw = (merged_prs / closed_prs) if closed_prs else None

    # ── Signal scores ──────────────────────────────────────────
    activity_signals = {
        "commit_frequency": _sig_commit_frequency(commit_count),
        "commit_recency":   _sig_commit_recency(days_since_last),
        "release_cadence":  _sig_release_cadence(releases),
    }
    community_signals = {
        "stars":             _sig_stars(star_count),
        "contributor_count": _sig_contributor_count(contrib_count),
        "forks":             _sig_forks(fork_count),
    }
    maintenance_signals = {
        "pr_merge_rate":    _sig_pr_merge_rate(pulls),
        "issue_resolution": _sig_issue_resolution(open_issues, commit_count, star_count),
        "stale_issues":     _sig_stale_issues(open_issues, commit_count, star_count),
    }

    # ── Dimension scores (0–1) ─────────────────────────────────
    dim_scores = {
        "activity":    _score_dimension(activity_signals,    SCORE_CONFIG["activity"]["signals"]),
        "community":   _score_dimension(community_signals,   SCORE_CONFIG["community"]["signals"]),
        "maintenance": _score_dimension(maintenance_signals, SCORE_CONFIG["maintenance"]["signals"]),
    }

    # ── Composite (weighted average → 0–100) ───────────────────
    total_dim_weight = sum(SCORE_CONFIG[d]["weight"] for d in dim_scores)
    composite = sum(
        dim_scores[d] * SCORE_CONFIG[d]["weight"]
        for d in dim_scores
    ) / total_dim_weight

    health_score = int(round(composite * 100))

    # Label
    if health_score >= LABEL_ACTIVE:
        label = "Active"
    elif health_score >= LABEL_MODERATE:
        label = "Moderate"
    else:
        label = "Inactive"

    # Commit trend
    trend = compute_commit_trend(commits)
    weekly_avg = round(sum(trend["counts"]) / 4, 1)

    return {
        "health_score":       health_score,
        "label":              label,
        "metrics": {
            "activity":    int(round(dim_scores["activity"]    * 100)),
            "community":   int(round(dim_scores["community"]   * 100)),
            "maintenance": int(round(dim_scores["maintenance"] * 100)),
        },
        "signal_scores":      {
            **activity_signals, **community_signals, **maintenance_signals
        },
        "commit_count_30d":   commit_count,
        "last_commit_date":   last_commit_date,
        "days_since_last":    round(days_since_last, 1),
        "contributor_count":  contrib_count,
        "star_count":         star_count,
        "fork_count":         fork_count,
        "open_issues":        open_issues,
        "pr_merge_rate":      round(pr_rate_raw, 3) if pr_rate_raw is not None else None,
        "weekly_avg_commits": weekly_avg,
        "commit_trend":       trend,
    }


# ═══════════════════════════════════════════════════════════════
#  PUBLIC: compute_commit_trend
# ═══════════════════════════════════════════════════════════════

def compute_commit_trend(commits: list[dict]) -> dict:
    """
    Bucket commits by calendar date for the last 30 days.
    Returns { "labels": [...], "counts": [...] }.
    """
    daily: dict[str, int] = defaultdict(int)
    for c in commits:
        date_str = c.get("commit", {}).get("author", {}).get("date", "")
        if date_str:
            daily[date_str[:10]] += 1

    today  = date.today()
    labels = [(today - timedelta(days=29 - i)).isoformat() for i in range(30)]
    counts = [daily.get(lbl, 0) for lbl in labels]
    return {"labels": labels, "counts": counts}


# ═══════════════════════════════════════════════════════════════
#  PUBLIC: detect_red_flags
# ═══════════════════════════════════════════════════════════════

def detect_red_flags(analytics: dict, meta: dict) -> list[dict]:
    """
    Scan analytics for known warning patterns and return a list of
    structured warning objects.

    Each warning:
    {
      "code":     "BUS_FACTOR_RISK",
      "severity": "high" | "medium" | "low",
      "message":  "Human-readable warning",
    }
    """
    warnings = []
    days         = analytics["days_since_last"]
    commits_30d  = analytics["commit_count_30d"]
    open_issues  = analytics["open_issues"]
    pr_rate      = analytics.get("pr_merge_rate")
    contrib_count = analytics["contributor_count"]

    # ── Archived ────────────────────────────────────────────────
    if meta.get("archived"):
        warnings.append({
            "code":     "ARCHIVED",
            "severity": "high",
            "message":  "This repository is archived and will receive no further updates.",
        })
        return warnings  # no point running further checks

    # ── Potentially abandoned ────────────────────────────────────
    if days > RF_ABANDONED_DAYS:
        months = int(days // 30)
        warnings.append({
            "code":     "NO_RECENT_COMMITS",
            "severity": "high",
            "message":  f"No commits in the last {months} month(s). Repository may be abandoned.",
        })

    # ── Bus-factor risk ──────────────────────────────────────────
    # BUGFIX: Don't flag personal/new repos as bus-factor risk.
    # If the repo has very few total commits it's likely a new project,
    # not an abandoned one-person show. Only warn when there's meaningful
    # history (>20 commits) and still only one contributor.
    if contrib_count == 1 and commits_30d > 20:
        warnings.append({
            "code":     "SINGLE_CONTRIBUTOR",
            "severity": "high",
            "message":  "Only one contributor detected. High bus-factor risk if the maintainer stops.",
        })
    elif contrib_count <= 2 and commits_30d > 20:
        warnings.append({
            "code":     "LOW_CONTRIBUTOR_COUNT",
            "severity": "medium",
            "message":  f"Only {contrib_count} contributors. Consider the risk of contributor attrition.",
        })

    # ── Issue backlog ────────────────────────────────────────────
    if open_issues > RF_ISSUE_BACKLOG and commits_30d < 5:
        warnings.append({
            "code":     "ISSUE_BACKLOG",
            "severity": "high",
            "message":  f"{open_issues:,} open issues with very low recent commit activity. Backlog may be unmanaged.",
        })
    elif open_issues > 200 and commits_30d < 10:
        warnings.append({
            "code":     "GROWING_ISSUE_BACKLOG",
            "severity": "medium",
            "message":  f"{open_issues:,} open issues relative to low commit activity. Monitor for backlog growth.",
        })

    # ── Low PR merge rate ────────────────────────────────────────
    if pr_rate is not None and pr_rate < RF_LOW_PR_MERGE_RATE:
        warnings.append({
            "code":     "LOW_PR_MERGE_RATE",
            "severity": "medium",
            "message":  f"Only {pr_rate:.0%} of closed PRs were merged. Contributions may be discouraged or the project is selective.",
        })

    # ── No releases (but active code) ───────────────────────────
    release_score = analytics["signal_scores"].get("release_cadence", 1.0)
    if release_score <= 0.25 and commits_30d > 5:
        warnings.append({
            "code":     "NO_RELEASES",
            "severity": "low",
            "message":  "No versioned releases detected. Dependency management may be difficult for consumers.",
        })

    return warnings


# ═══════════════════════════════════════════════════════════════
#  PUBLIC: build_recommendation
# ═══════════════════════════════════════════════════════════════

def build_recommendation(analytics: dict, meta: dict) -> str:
    score = analytics["health_score"]
    label = analytics["label"]
    days  = analytics["days_since_last"]
    stars = analytics["star_count"]

    if meta.get("archived"):
        return (
            "⚠️ Archived — will not receive further updates. "
            "Do not use in new projects without forking and maintaining it yourself."
        )
    if label == "Active":
        return (
            f"✅ Production-ready. Actively maintained (score {score}/100) "
            f"with {stars:,} stars and a last commit {int(days)} day(s) ago."
        )
    if label == "Moderate":
        return (
            f"⚠️ Evaluate carefully. Moderate activity (score {score}/100). "
            f"Last commit {int(days)} day(s) ago. Check open issues and whether "
            "the project's roadmap aligns with your needs before adopting."
        )
    return (
        f"❌ Not recommended for new projects. Low activity (score {score}/100). "
        f"Last commit {int(days)} day(s) ago. Seek an actively maintained alternative."
    )


# ═══════════════════════════════════════════════════════════════
#  PUBLIC: compare_repos
# ═══════════════════════════════════════════════════════════════

def compare_repos(a: dict, b: dict) -> dict:
    """Return per-metric winners and an overall summary."""
    metrics = ["health_score", "commit_count_30d", "contributor_count", "star_count"]
    winners = {m: ("repo_1" if a.get(m, 0) >= b.get(m, 0) else "repo_2") for m in metrics}

    r1_wins = sum(1 for v in winners.values() if v == "repo_1")
    r2_wins = len(metrics) - r1_wins

    if r1_wins > r2_wins:
        summary = f"Repo 1 leads in {r1_wins}/{len(metrics)} key metrics."
    elif r2_wins > r1_wins:
        summary = f"Repo 2 leads in {r2_wins}/{len(metrics)} key metrics."
    else:
        summary = "Both repositories are evenly matched across key metrics."

    return {
        "winners": winners,
        "summary": summary,
        "metric_labels": {
            "health_score":       "Health Score",
            "commit_count_30d":   "Commits (30d)",
            "contributor_count":  "Contributors",
            "star_count":         "Stars",
        },
    }