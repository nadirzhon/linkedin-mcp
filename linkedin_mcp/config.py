"""
Configuration and local storage paths.

Secrets (LinkedIn client id/secret and the OAuth token) live in a local config
file under ~/.linkedin-mcp — never in the repo. Client id/secret can also come
from environment variables so nothing sensitive is ever written to disk if you
prefer.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(os.environ.get("LINKEDIN_MCP_HOME", Path.home() / ".linkedin-mcp"))
TOKEN_FILE = CONFIG_DIR / "token.json"
STORE_FILE = CONFIG_DIR / "posts.json"

# LinkedIn OAuth endpoints
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/rest/posts"
# LinkedIn versions its REST API by month (YYYYMM). Bump when needed.
LINKEDIN_VERSION = os.environ.get("LINKEDIN_API_VERSION", "202401")

# Scopes needed to post on your own profile and read your identity.
SCOPES = "openid profile w_member_social"
DEFAULT_REDIRECT = "http://localhost:8710/callback"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(CONFIG_DIR, 0o700)
    except OSError:
        pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_json(path: Path, data: dict[str, Any]) -> None:
    _ensure_dir()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def client_credentials() -> tuple[str, str, str]:
    """Return (client_id, client_secret, redirect_uri) from env or config."""
    cfg = load_json(TOKEN_FILE)
    cid = os.environ.get("LINKEDIN_CLIENT_ID") or cfg.get("client_id", "")
    secret = os.environ.get("LINKEDIN_CLIENT_SECRET") or cfg.get("client_secret", "")
    redirect = os.environ.get("LINKEDIN_REDIRECT_URI") or cfg.get("redirect_uri", DEFAULT_REDIRECT)
    return cid, secret, redirect
