"""
linkedin-mcp — an MCP server that lets an AI assistant publish and schedule
posts on YOUR LinkedIn profile, and plan a content calendar.

Tools:
  auth_status          — is the tool authorized, and as whom
  publish_now          — post immediately to your profile
  schedule_post        — queue a post for a future time (published by the scheduler)
  list_posts           — scheduled queue and published history
  cancel_scheduled     — remove a queued post
  post_brief           — a structured brief + rules to write a strong post
  content_calendar     — a safe weekly cadence and best-practice rules

Scope is intentionally narrow: it posts as you and nothing else. No auto-connect,
auto-like, auto-comment, messaging, scraping or engagement automation — those
break LinkedIn's User Agreement and risk a permanent ban.
"""

from __future__ import annotations

import datetime as _dt

from mcp.server import MCPServer

from . import client, content, store

mcp = MCPServer("linkedin-mcp", version="1.0.0")


def _parse_when(when: str) -> float:
    """Accept ISO 8601 ('2026-08-20T09:00') or '+2h' / '+30m' / '+1d'."""
    when = when.strip()
    if when.startswith("+"):
        num = int("".join(c for c in when[1:] if c.isdigit()) or "0")
        unit = when.rstrip()[-1].lower()
        secs = {"m": 60, "h": 3600, "d": 86400}.get(unit)
        if not secs:
            raise ValueError("relative time must end in m/h/d, e.g. +2h")
        return _dt.datetime.now().timestamp() + num * secs
    dt = _dt.datetime.fromisoformat(when)
    return dt.timestamp()


@mcp.tool()
def auth_status() -> dict:
    """Check whether the tool is authorized to post, and as which member."""
    try:
        who = client.userinfo()
        return {"authorized": True, "name": who.get("name", ""),
                "member_id": who.get("sub", "")}
    except client.LinkedInError as e:
        return {"authorized": False, "error": str(e),
                "hint": "Run: python -m linkedin_mcp.auth"}


@mcp.tool()
def publish_now(text: str, visibility: str = "PUBLIC") -> dict:
    """Publish a text post to your LinkedIn profile immediately.

    text: the full post body.
    visibility: PUBLIC (default) or CONNECTIONS.
    """
    result = client.publish(text, visibility=visibility)
    store.record_published(text, visibility, result)
    return {"ok": True, **result}


@mcp.tool()
def schedule_post(text: str, when: str, visibility: str = "PUBLIC") -> dict:
    """Queue a post for later. It is published by the scheduler process.

    when: ISO time ('2026-08-20T09:00') or relative ('+2h', '+1d').
    Run the scheduler (cron or `python -m linkedin_mcp.scheduler`) so queued
    posts actually go out.
    """
    when_ts = _parse_when(when)
    item = store.add_scheduled(text, when_ts, visibility)
    return {"ok": True, "id": item["id"],
            "when": _dt.datetime.fromtimestamp(when_ts).isoformat(timespec="minutes")}


@mcp.tool()
def list_posts(kind: str = "all") -> dict:
    """List posts. kind: 'scheduled', 'published', or 'all'."""
    return store.lists(kind)


@mcp.tool()
def cancel_scheduled(post_id: str) -> dict:
    """Remove a queued post by its id."""
    return {"ok": store.cancel_scheduled(post_id)}


@mcp.tool()
def post_brief(topic: str, archetype: str = "build_in_public") -> dict:
    """Get a structured brief + rules to write a strong post on a topic.

    archetype: build_in_public | lesson | teardown | opinion | result.
    Use the returned structure and rules to write the actual post, then
    publish_now or schedule_post it.
    """
    return content.brief(topic, archetype)


@mcp.tool()
def content_calendar() -> dict:
    """A safe weekly posting cadence and best-practice rules for steady growth."""
    return content.calendar()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
