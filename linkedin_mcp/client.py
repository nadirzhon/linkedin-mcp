"""
LinkedIn API client — publishes posts on your own profile via the official API.

Uses OAuth 2.0 with the `w_member_social` scope (the "Share on LinkedIn"
product). Publishing is done through the Posts API. Pure standard library
(urllib) — no third-party HTTP dependency.

This only ever posts as the authenticated member (you). It does NOT connect,
like, comment, message, scrape, or automate engagement — those violate
LinkedIn's User Agreement and risk a permanent ban.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Any

from . import config


class LinkedInError(RuntimeError):
    pass


def _request(method: str, url: str, *, headers: dict[str, str],
             data: bytes | None = None) -> tuple[int, dict[str, Any], dict[str, str]]:
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            resp_headers = {k: v for k, v in r.headers.items()}
            return r.status, (json.loads(body) if body.strip() else {}), resp_headers
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return e.code, parsed, {k: v for k, v in (e.headers or {}).items()}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise LinkedInError(f"network error: {e}") from e


# ---------------------------------------------------------------------------
# OAuth token exchange / refresh
# ---------------------------------------------------------------------------
def exchange_code(code: str) -> dict[str, Any]:
    cid, secret, redirect = config.client_credentials()
    payload = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect,
        "client_id": cid,
        "client_secret": secret,
    }).encode()
    status, data, _ = _request(
        "POST", config.TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, data=payload)
    if status != 200 or "access_token" not in data:
        raise LinkedInError(f"token exchange failed ({status}): {data}")
    _persist_token(data)
    return data


def refresh_token() -> dict[str, Any]:
    tok = config.load_json(config.TOKEN_FILE)
    rt = tok.get("refresh_token")
    if not rt:
        raise LinkedInError("no refresh_token stored; run the auth flow again")
    cid, secret, _ = config.client_credentials()
    payload = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": rt,
        "client_id": cid,
        "client_secret": secret,
    }).encode()
    status, data, _ = _request(
        "POST", config.TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, data=payload)
    if status != 200 or "access_token" not in data:
        raise LinkedInError(f"token refresh failed ({status}): {data}")
    _persist_token(data)
    return data


def _persist_token(data: dict[str, Any]) -> None:
    tok = config.load_json(config.TOKEN_FILE)
    tok["access_token"] = data["access_token"]
    if "refresh_token" in data:
        tok["refresh_token"] = data["refresh_token"]
    if "expires_in" in data:
        tok["expires_at"] = int(time.time()) + int(data["expires_in"]) - 60
    config.save_json(config.TOKEN_FILE, tok)


def _valid_access_token() -> str:
    tok = config.load_json(config.TOKEN_FILE)
    at = tok.get("access_token")
    if not at:
        raise LinkedInError("not authenticated — run: python -m linkedin_mcp.auth")
    # Auto-refresh if we know it's expired and a refresh token exists.
    if tok.get("expires_at") and time.time() > tok["expires_at"] and tok.get("refresh_token"):
        at = refresh_token()["access_token"]
    return at


def _auth_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {_valid_access_token()}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": config.LINKEDIN_VERSION,
    }
    if extra:
        h.update(extra)
    return h


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------
def userinfo() -> dict[str, Any]:
    """Return the authenticated member's OpenID profile (name, sub=member id)."""
    status, data, _ = _request("GET", config.USERINFO_URL, headers=_auth_headers())
    if status != 200:
        raise LinkedInError(f"userinfo failed ({status}): {data}")
    return data


def author_urn() -> str:
    sub = userinfo().get("sub")
    if not sub:
        raise LinkedInError("could not determine member id from userinfo")
    return f"urn:li:person:{sub}"


# ---------------------------------------------------------------------------
# Publishing
# ---------------------------------------------------------------------------
def publish(text: str, *, visibility: str = "PUBLIC") -> dict[str, Any]:
    """Publish a text post to the authenticated member's profile.

    visibility: PUBLIC | CONNECTIONS
    Returns {id, url} on success.
    """
    if not text or not text.strip():
        raise LinkedInError("post text is empty")
    if visibility not in ("PUBLIC", "CONNECTIONS"):
        raise LinkedInError("visibility must be PUBLIC or CONNECTIONS")

    body = json.dumps({
        "author": author_urn(),
        "commentary": text,
        "visibility": visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }).encode("utf-8")

    status, data, headers = _request(
        "POST", config.POSTS_URL,
        headers=_auth_headers({"Content-Type": "application/json"}), data=body)
    if status not in (200, 201):
        raise LinkedInError(f"publish failed ({status}): {data}")
    post_id = headers.get("x-restli-id") or headers.get("X-RestLi-Id") or data.get("id", "")
    return {"id": post_id, "url": f"https://www.linkedin.com/feed/update/{post_id}" if post_id else ""}
