"""
Scheduler — publishes queued posts whose time has come.

Run it periodically (cron / launchd) so scheduled posts actually go out even
when you're not in a chat:

    */15 * * * *  /usr/bin/python3 -m linkedin_mcp.scheduler >> ~/.linkedin-mcp/scheduler.log 2>&1

Each run publishes every due post and moves it from the queue to history. Safe
to run often — if nothing is due, it does nothing.
"""

from __future__ import annotations

import sys
import time

from . import client, store


def run_once() -> int:
    due = store.due()
    if not due:
        print(f"[{time.strftime('%Y-%m-%d %H:%M')}] nothing due")
        return 0
    published = 0
    for item in due:
        try:
            result = client.publish(item["text"], visibility=item.get("visibility", "PUBLIC"))
            store.mark_published(item["id"], result)
            print(f"[{time.strftime('%H:%M')}] published {item['id']} -> {result.get('url','')}")
            published += 1
        except client.LinkedInError as e:
            # Leave it in the queue to retry next run; report the error.
            print(f"[{time.strftime('%H:%M')}] FAILED {item['id']}: {e}", file=sys.stderr)
    return published


if __name__ == "__main__":
    run_once()
