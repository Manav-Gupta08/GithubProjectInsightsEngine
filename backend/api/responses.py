"""
Centralised response builders.

Every endpoint should call one of these helpers so all responses share
a consistent envelope:

Success:
    {
      "success": true,
      "data": { ... },
      "meta": { "cached": bool, "generated_at": "ISO8601" }
    }

Error:
    {
      "success": false,
      "error": {
        "code": "REPO_NOT_FOUND",
        "message": "Human-readable description",
        "details": { ... }   # optional extra context
      }
    }
"""

from datetime import datetime, timezone
from flask import jsonify


# ── Error code constants ───────────────────────────────────────────────────

class ErrorCode:
    VALIDATION_ERROR  = "VALIDATION_ERROR"
    REPO_NOT_FOUND    = "REPO_NOT_FOUND"
    RATE_LIMIT        = "RATE_LIMIT_EXCEEDED"
    GITHUB_ERROR      = "GITHUB_API_ERROR"
    SERVER_ERROR      = "INTERNAL_SERVER_ERROR"
    NOT_FOUND         = "NOT_FOUND"


# ── Success builder ────────────────────────────────────────────────────────

def success(data: dict | list, status: int = 200, cached: bool = False):
    """
    Return a standardised success response.

    Args:
        data:   The payload to return under the "data" key.
        status: HTTP status code (default 200).
        cached: Whether this response came from the cache.
    """
    body = {
        "success": True,
        "data": data,
        "meta": {
            "cached": cached,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    return jsonify(body), status


# ── Error builder ──────────────────────────────────────────────────────────

def error(
    code: str,
    message: str,
    status: int = 400,
    details: dict = None,
):
    """
    Return a standardised error response.

    Args:
        code:    Machine-readable error code (use ErrorCode constants).
        message: Human-readable explanation.
        status:  HTTP status code.
        details: Optional dict with extra context (e.g. rate limit reset time).
    """
    body: dict = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details:
        body["error"]["details"] = details

    return jsonify(body), status
