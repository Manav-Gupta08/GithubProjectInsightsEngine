# GitHub Insights Engine

> A production-grade repository health analysis tool. Enter any GitHub repository and get a detailed breakdown of its activity, contributor diversity, maintenance quality, and an overall health score.

---

## Why This Project Matters

When evaluating an open-source library to use in production, most developers just look at star count. That misses critical signals — is it still actively maintained? How many contributors does it have? What percentage of PRs get merged? Are there hundreds of unresolved issues?

This tool answers all of those questions in seconds, with a transparent, explainable scoring algorithm.

---

## Features

| Feature | Details |
|---|---|
| **Health Score (0–100)** | Composite score across Activity, Community, and Maintenance dimensions |
| **Red Flag Detection** | Automatic warnings: abandoned repos, bus-factor risk, issue backlogs, low PR acceptance |
| **Commit Trend Chart** | 30-day daily commit activity visualised with Chart.js |
| **Top Contributors** | Ranked list with contribution bars |
| **PR Merge Rate** | What % of closed PRs were actually merged |
| **Compare Mode** | Side-by-side head-to-head analysis of two repos |
| **Batch Ranking** | Input up to 10 repos, get them ranked by health score |
| **AI Insights** | Optional LLM-generated plain-English summary (requires Anthropic API key) |
| **In-memory Cache** | 5-minute TTL cache to minimise GitHub API calls |
| **RESTful API** | Clean JSON API with consistent response envelopes |
| **Full Test Suite** | Unit tests for scoring logic + integration tests for all API endpoints |
| **Docker Ready** | Multi-stage Dockerfile + docker-compose for one-command deployment |

---

## Tech Stack

| Layer | Technology                                    |
|---|-----------------------------------------------|
| Backend | Python 3.11, Flask 3, flask-cors              |
| Frontend | React 18, Vite, CSS Modules                   |
| Charts | Chart.js 4, react-chartjs-2                   |
| Data | GitHub REST API v3                            |
| AI (optional) | Google Gemini API                             |
| Testing | pytest, unittest.mock                         |
| Deployment | Docker, Gunicorn, Render / Railway compatible |

---

## Project Structure

```
github-insights/
│
├── .env.example              # Environment variable template
├── .gitignore
├── Dockerfile                # Multi-stage build (React → Flask)
├── docker-compose.yml
├── README.md
│
├── backend/
│   ├── app.py                # Flask application factory
│   ├── requirements.txt
│   ├── pytest.ini
│   │
│   ├── api/                  # Route blueprints (HTTP layer only)
│   │   ├── repos.py          # GET /api/repos/<owner>/<repo>
│   │   │                     # GET /api/repos/compare
│   │   │                     # GET /api/repos/<owner>/<repo>/ai-insights
│   │   │                     # DELETE /api/cache
│   │   ├── batch.py          # POST /api/repos/batch
│   │   └── responses.py      # Shared JSON envelope builders
│   │
│   ├── services/             # Business logic (no Flask dependency)
│   │   ├── github_service.py   # GitHub REST API calls + in-memory cache
│   │   ├── analysis_service.py # Scoring engine + red flag detector
│   │   └── ai_service.py       # Optional LLM insight generator
│   │
│   └── tests/
│       ├── test_analysis_service.py   # Unit tests (25+ cases)
│       └── test_api.py                # API integration tests (20+ cases)
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js        # Dev proxy: /api/* → localhost:5000
    │
    └── src/
        ├── main.jsx
        ├── App.jsx            # Root component + tab routing
        │
        ├── styles/
        │   └── global.css     # Design tokens + reset + shared classes
        │
        ├── utils/
        │   ├── api.js         # All fetch() calls in one place
        │   └── format.js      # Number/date/label formatting helpers
        │
        ├── hooks/
        │   └── useRepo.js     # Fetch lifecycle hook for single repo
        │
        ├── pages/             # Top-level page components (one per tab)
        │   ├── AnalysePage.jsx
        │   ├── ComparePage.jsx
        │   ├── BatchPage.jsx
        │   └── Page.module.css   # Shared hero/page layout styles
        │
        └── components/
            ├── layout/
            │   ├── Header.jsx + .module.css
            │   └── Footer.jsx + .module.css
            │
            ├── common/          # Reusable UI primitives
            │   ├── SearchBar.jsx + .module.css
            │   └── Feedback.jsx + .module.css   (ErrorMessage, LoadingSpinner)
            │
            ├── dashboard/       # Single-repo analysis panels
            │   ├── Dashboard.jsx           # Grid layout orchestrator
            │   ├── RepoMetaBar.jsx         # Title + KPI strip
            │   ├── ScoreCard.jsx           # Animated ring + breakdown bars
            │   ├── CommitChart.jsx         # Chart.js line chart
            │   ├── ContributorList.jsx     # Ranked contributors
            │   ├── WarningList.jsx         # Red flag cards
            │   └── RecommendationCard.jsx  # "Should I use this?" + AI insight
            │
            ├── compare/
            │   └── CompareCard.jsx         # One side of a comparison
            │
            └── batch/
                └── BatchResultsTable.jsx   # Ranked results table
```

---

## Scoring Algorithm

The 0–100 health score is computed from **three weighted dimensions**, each built from individual signals:

```
Health Score = Activity(40%) + Community(30%) + Maintenance(30%)

Activity:
  commit_frequency  50%  — commits in last 30 days (log scale, ceiling 60)
  commit_recency    35%  — days since last commit (linear decay over 30 days)
  release_cadence   15%  — how recently and often releases ship

Community:
  stars             40%  — log₁₀ scale, 10k stars = full marks
  contributor_count 40%  — log scale, 20+ contributors = full marks
  forks             20%  — log₁₀ scale, 1k forks = full marks

Maintenance:
  pr_merge_rate     40%  — % of closed PRs that were merged
  issue_resolution  35%  — commit activity relative to open issues
  stale_issues      25%  — penalty for large unmanaged issue backlog
```

**Labels:**
- ≥ 70 → **Active**
- 40–69 → **Moderate**
- < 40 → **Inactive**

All weights live in `SCORE_CONFIG` in `analysis_service.py` — change them without touching signal logic.

---

## Red Flag Detection

| Flag | Condition | Severity |
|---|---|---|
| `ARCHIVED` | Repo is archived | High |
| `NO_RECENT_COMMITS` | No commits in 6+ months | High |
| `SINGLE_CONTRIBUTOR` | Only 1 contributor | High |
| `ISSUE_BACKLOG` | 500+ open issues, <5 commits/month | High |
| `LOW_CONTRIBUTOR_COUNT` | ≤2 contributors | Medium |
| `GROWING_ISSUE_BACKLOG` | 200+ issues, <10 commits/month | Medium |
| `LOW_PR_MERGE_RATE` | <30% of PRs merged | Medium |
| `NO_RELEASES` | No versioned releases, but active code | Low |

---

## API Reference

### `GET /api/repos/<owner>/<repo>`

```json
{
  "success": true,
  "data": {
    "repo":   { "full_name", "description", "language", "stars", "forks", ... },
    "health": {
      "health_score": 84,
      "label": "Active",
      "metrics": { "activity": 88, "community": 79, "maintenance": 82 },
      "signal_scores": { "commit_frequency": 0.92, ... },
      "commit_trend": { "labels": [...], "counts": [...] },
      "pr_merge_rate": 0.87
    },
    "contributors": [ { "login", "contributions", "avatar_url" } ],
    "warnings":     [ { "code", "severity", "message" } ],
    "recommendation": "✅ Production-ready. Actively maintained..."
  },
  "meta": { "cached": false, "generated_at": "2024-05-20T10:00:00Z" }
}
```

### `GET /api/repos/compare?repo1=owner/repo&repo2=owner/repo`

Returns `{ repo_1: {...}, repo_2: {...}, comparison: { winners, summary } }`

### `POST /api/repos/batch`

```json
// Request
{ "repos": ["facebook/react", "vuejs/vue", "sveltejs/svelte"] }

// Response data
{
  "results": [ { "rank": 1, "slug": "facebook/react", "health_score": 84, ... } ],
  "failed":  []
}
```

### `GET /api/repos/<owner>/<repo>/ai-insights`

Returns `{ "insight": "Plain English 2-3 sentence summary..." }`.
Requires `AI_INSIGHTS_ENABLED=true` and `ANTHROPIC_API_KEY` in `.env`.

### `DELETE /api/cache`

```json
// Body (optional): { "repo": "owner/repo" }
// Clears one repo or all cached entries.
```

---

## Quick Start

### Option A — Local development (recommended)

**1. Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env     # fill in GITHUB_TOKEN
python app.py                  # → http://localhost:5000
```

**2. Frontend** (separate terminal)
```bash
cd frontend
npm install
npm run dev                    # → http://localhost:5173
```

The Vite dev server proxies all `/api/*` requests to Flask on `:5000`.

### Option B — Docker (one command)

```bash
cp .env.example .env           # fill in GITHUB_TOKEN
docker compose up --build      # → http://localhost:8000
```

### Run tests

```bash
cd backend
pytest                         # all tests
pytest tests/test_analysis_service.py -v   # unit tests only
pytest tests/test_api.py -v               # API tests only
```

---

## Environment Variables

| Variable              | Required | Default | Description                       |
|-----------------------|---|---|-----------------------------------|
| `GITHUB_TOKEN`        | Recommended | — | Raises rate limit 60→5,000 req/hr |
| `CACHE_TTL`           | No | `300` | Cache expiry in seconds           |
| `AI_INSIGHTS_ENABLED` | No | `false` | Enable LLM summaries              |
| `GEMINI_API_KEY`      | If AI enabled | — | GEMINI API key                    |
| `PORT`                | No | `5000` | Flask port                        |
| `FLASK_DEBUG`         | No | `1` | Set to `0` in production          |

---

## Deployment

### Render / Railway (backend only)

1. Set root directory to `backend/`
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"`
4. Add environment variables in the dashboard

### Future additions (designed for, not yet implemented)

- **Phase 2:** Replace in-memory cache with Redis; add PostgreSQL to persist analysis history
- **Phase 3:** JWT authentication; save favourite repositories; view past comparisons

These are explicitly designed as separate git commits so the project history stays clean and readable.
