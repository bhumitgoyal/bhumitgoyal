#!/usr/bin/env python3
"""Scrape the public GitHub contribution calendar (no token, no GraphQL).

GitHub serves the same calendar fragment the profile page uses at
    https://github.com/users/<username>/contributions
as plain public HTML. We parse the day cells with BeautifulSoup and write
data/contributions.json with the raw days plus a few derived stats.

Usage:
    python scripts/fetch_contributions.py            # uses USERNAME below / env
    GH_USERNAME=octocat python scripts/fetch_contributions.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "bhumitgoyal")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

URL = f"https://github.com/users/{USERNAME}/contributions"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (profile-art contribution fetcher)",
    "X-Requested-With": "XMLHttpRequest",
}

# "12 contributions on July 13th." / "No contributions on July 13th."
_COUNT_RE = re.compile(r"^\s*(No|[\d,]+)\s+contribution", re.IGNORECASE)
# id="contribution-day-component-{dow}-{week}"
_ID_RE = re.compile(r"contribution-day-component-(\d+)-(\d+)")


def fetch_html() -> str:
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # id -> count, from the sr-only tool-tip elements
    counts: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if not target:
            continue
        m = _COUNT_RE.match(tip.get_text(strip=True))
        if not m:
            continue
        token = m.group(1)
        counts[target] = 0 if token.lower() == "no" else int(token.replace(",", ""))

    days: list[dict] = []
    for cell in soup.select("td.ContributionCalendar-day"):
        iso = cell.get("data-date")
        if not iso:
            continue
        cid = cell.get("id", "")
        m = _ID_RE.search(cid)
        dow, week = (int(m.group(1)), int(m.group(2))) if m else (None, None)
        days.append(
            {
                "date": iso,
                "count": counts.get(cid, 0),
                "level": int(cell.get("data-level", 0)),
                "dow": dow,
                "week": week,
            }
        )

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    # streaks over the ordered day list
    longest = current = run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    # current streak = trailing consecutive active days
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break

    best = max(days, key=lambda d: d["count"]) if days else {"date": None, "count": 0}

    # monthly totals (YYYY-MM -> count)
    monthly: dict[str, int] = {}
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]

    active_days = sum(1 for d in days if d["count"] > 0)
    span = len(days)

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": active_days,
        "busiest_avg": round(total / active_days, 1) if active_days else 0,
        "monthly": monthly,
        "day_span": span,
    }


def main() -> int:
    html = fetch_html()
    days = parse(html)
    if not days:
        print("ERROR: no contribution cells parsed — markup may have changed", file=sys.stderr)
        return 1

    stats = compute_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z",
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "stats": stats,
        "days": days,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(
        f"Wrote {OUT.relative_to(ROOT)} — {len(days)} days, "
        f"{stats['total']} contributions, "
        f"current streak {stats['current_streak']}, longest {stats['longest_streak']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
