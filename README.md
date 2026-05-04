#  GitHub Insights Engine

> **Production-grade GitHub repository analysis tool**  
Analyze any repository and instantly understand its **activity, maintainability, community strength, and overall health score**.

---

##  Overview

Choosing an open-source library based only on ⭐ stars is misleading.

This tool helps you answer critical questions:

- Is the project actively maintained?
- How strong is the contributor base?
- Are pull requests getting merged?
- Is there an unresolved issue backlog?

👉 Get **data-driven insights + a transparent scoring system** in seconds.

---

##  Key Features

### Core Analysis
- **Health Score (0–100)** — Based on Activity, Community, Maintenance
- **Red Flag Detection** — Identify risky repositories instantly
- **PR Merge Rate** — Understand contribution acceptance
- **Issue Backlog Analysis** — Detect maintenance problems

###  Visualization
- **Commit Trend Chart (30 days)** — Built with Chart.js
- **Top Contributors Ranking** — With contribution weight

### Advanced Capabilities
- **Compare Mode** — Side-by-side repo comparison
- **Batch Ranking** — Rank up to 10 repositories
- **AI Insights (optional)** — Natural language summary
- **Caching Layer** — 5-minute TTL to reduce API calls
- **REST API** — Clean and consistent JSON responses

###  Engineering Quality
- Full unit + integration tests
- Docker-ready deployment
- Modular architecture (MVC-inspired)

---

##  Tech Stack

| Layer        | Technology |
|-------------|----------|
| Backend     | Python 3.11, Flask 3 |
| Frontend    | React 18, Vite |
| Charts      | Chart.js |
| Data Source | GitHub REST API |
| AI (optional) | Google Gemini API |
| Testing     | pytest |
| Deployment  | Docker, Gunicorn |

---

##  Project Structure

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

##  Scoring Algorithm

```
Health Score = Activity (40%) + Community (30%) + Maintenance (30%)
```

---

##  Red Flag Detection

| Flag | Meaning |
|------|--------|
| ARCHIVED | Project is no longer maintained |
| NO_RECENT_COMMITS | Inactive for 6+ months |
| SINGLE_CONTRIBUTOR | High bus-factor risk |
| ISSUE_BACKLOG | Too many unresolved issues |
| LOW_PR_MERGE_RATE | Contributions ignored |

---

##  API Endpoints

- GET /api/repos/<owner>/<repo>
- GET /api/repos/compare
- POST /api/repos/batch
- GET /api/repos/<repo>/ai-insights
- DELETE /api/cache

---

##  Quick Start

### Backend
```
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Frontend
```
cd frontend
npm install
npm run dev
```

---

##  Docker Setup

```
docker compose up --build
```

---

##  Testing

```
pytest
```

---

## Future additions

- **Phase 2:** Replace in-memory cache with Redis; add PostgreSQL to persist analysis history
- **Phase 3:** JWT authentication; save favourite repositories; view past comparisons

---

## Author

**Manav Gupta**

Computer Science Student | Backend Developer

GitHub: https://github.com/Manav-Gupta08

---

## License

MIT License
