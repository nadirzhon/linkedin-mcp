"""
Local post store — scheduled queue and published history.

A simple JSON file under ~/.linkedin-mcp/posts.json. Enough for a personal
tool; no database needed.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from . import config


def _load() -> dict[str, Any]:
    data = config.load_json(config.STORE_FILE)
    data.setdefault("scheduled", [])
    data.setdefault("published", [])
    return data


def _save(data: dict[str, Any]) -> None:
    config.save_json(config.STORE_FILE, data)


def _new_id(text: str) -> str:
    raw = f"{text}|{time.time()}"
    return "p_" + hashlib.sha1(raw.encode()).hexdigest()[:10]


def add_scheduled(text: str, when_ts: float, visibility: str) -> dict[str, Any]:
    data = _load()
    item = {
        "id": _new_id(text),
        "text": text,
        "visibility": visibility,
        "when_ts": when_ts,
        "created_ts": time.time(),
    }
    data["scheduled"].append(item)
    data["scheduled"].sort(key=lambda x: x["when_ts"])
    _save(data)
    return item


def cancel_scheduled(post_id: str) -> bool:
    data = _load()
    before = len(data["scheduled"])
    data["scheduled"] = [p for p in data["scheduled"] if p["id"] != post_id]
    _save(data)
    return len(data["scheduled"]) < before


def due(now_ts: float | None = None) -> list[dict[str, Any]]:
    now_ts = now_ts if now_ts is not None else time.time()
    return [p for p in _load()["scheduled"] if p["when_ts"] <= now_ts]


def mark_published(post_id: str, result: dict[str, Any]) -> None:
    data = _load()
    item = next((p for p in data["scheduled"] if p["id"] == post_id), None)
    if item:
        data["scheduled"] = [p for p in data["scheduled"] if p["id"] != post_id]
    else:
        item = {"id": post_id}
    item = {**item, "published_ts": time.time(), "linkedin_id": result.get("id", ""),
            "url": result.get("url", "")}
    data["published"].insert(0, item)
    _save(data)


def record_published(text: str, visibility: str, result: dict[str, Any]) -> None:
    data = _load()
    data["published"].insert(0, {
        "id": _new_id(text), "text": text, "visibility": visibility,
        "published_ts": time.time(), "linkedin_id": result.get("id", ""),
        "url": result.get("url", ""),
    })
    _save(data)


def lists(kind: str = "all") -> dict[str, Any]:
    data = _load()
    if kind == "scheduled":
        return {"scheduled": data["scheduled"]}
    if kind == "published":
        return {"published": data["published"][:50]}
    return {"scheduled": data["scheduled"], "published": data["published"][:50]}
