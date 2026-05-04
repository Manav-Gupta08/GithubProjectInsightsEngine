"""
AI insight generator using Google Gemini API.
Feature flag: set AI_INSIGHTS_ENABLED=true and GEMINI_API_KEY in .env.
"""

import os
import json
import requests

_AI_ENABLED = os.getenv("AI_INSIGHTS_ENABLED", "false").lower() == "true"
_API_KEY    = os.getenv("GEMINI_API_KEY", "")
_MODEL      = "gemini-2.5-flash"   # fast + free tier available
_API_URL    = f"https://generativelanguage.googleapis.com/v1/models/{_MODEL}:generateContent"


def is_enabled() -> bool:
    """Return True when AI insights are configured and enabled."""
    return _AI_ENABLED and bool(_API_KEY)


def generate_insight(meta: dict, analytics: dict, warnings: list[dict]) -> str:
    """
    Generate a concise plain-English insight about the repository using Gemini.

    Returns:
        A 2-3 sentence string for display in the UI.

    Raises:
        RuntimeError if the API call fails.
    """
    if not is_enabled():
        raise RuntimeError("AI insights are not enabled.")

    # Build a compact summary to send to Gemini
    summary = {
        "repo":            meta.get("full_name", "unknown"),
        "description":     (meta.get("description") or "")[:200],
        "language":        meta.get("language", "unknown"),
        "health_score":    analytics["health_score"],
        "label":           analytics["label"],
        "metrics":         analytics["metrics"],
        "commits_30d":     analytics["commit_count_30d"],
        "contributors":    analytics["contributor_count"],
        "stars":           analytics["star_count"],
        "open_issues":     analytics["open_issues"],
        "pr_merge_rate":   analytics.get("pr_merge_rate"),
        "days_since_last": analytics["days_since_last"],
        "warnings":        [w["message"] for w in warnings],
    }

    prompt = (
        "You are a senior open-source engineer with 15 years of experience "
        "evaluating libraries for production use.\n\n"
        "A developer is deciding whether to use this GitHub repository as a dependency. "
        "They can already see the raw metrics (score, commits, stars, contributors, warnings). "
        "Do NOT repeat those numbers.\n\n"
        "Instead, give them something the metrics cannot — your expert judgment:\n"
        "- What kind of project is this likely to be? (solo experiment, corporate-backed, community-driven?)\n"
        "- What is the REAL risk of adopting it? (not just 'low activity' — what could actually go wrong?)\n"
        "- Is there a smarter alternative approach? (fork it, find a replacement, vendor it, avoid entirely?)\n\n"
        "Write 3 punchy sentences. Be opinionated. Be specific to THIS repo. "
        "Sound like a staff engineer giving a code review comment, not a report. "
        "No bullet points. No headers. No metric repetition.\n\n"
        f"Repository: {summary['repo']}\n"
        f"Description: {summary['description']}\n"
        f"Language: {summary['language']}\n"
        f"Health label: {summary['label']}\n"
        f"Days since last commit: {summary['days_since_last']}\n"
        f"Warnings: {summary['warnings']}\n"
        f"Stars: {summary['stars']} | Contributors: {summary['contributors']} | "
        f"PR merge rate: {summary['pr_merge_rate']}"
    )

    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 1000,
            "temperature": 0.3,
        }
    }

    resp = requests.post(
        f"{_API_URL}?key={_API_KEY}",
        headers=headers,
        json=payload,
        timeout=20,
    )

    if not resp.ok:
        raise RuntimeError(
            f"Gemini API error {resp.status_code}: {resp.text[:200]}"
        )

    data = resp.json()

    # Extract text from Gemini response structure
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response format: {e}")