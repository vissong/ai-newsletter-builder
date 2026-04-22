#!/usr/bin/env python3
"""
Fetch Hacker News /beststories — full item details as a JSON array to stdout.

Pulls the beststories ID list, then fetches each item in parallel. Outputs
every story that has a score >= --min-score, keeping title, url, score,
comments count, author, and published_at. Filtering for topical relevance
(AI vs non-AI) is done afterwards by prompt.md, not here.

Usage:
    python fetch.py [--limit 80] [--min-score 50]

Output: JSON array on stdout. Diagnostics on stderr.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
import urllib.request
from datetime import datetime, timezone

API = "https://hacker-news.firebaseio.com/v0"
USER_AGENT = "ai-newsletter-builder/1.0 (+https://github.com/vissong/ai-newsletter-builder)"


def _get(path: str, timeout: int = 15):
    req = urllib.request.Request(f"{API}/{path}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def fetch_item(item_id: int) -> dict | None:
    try:
        return _get(f"item/{item_id}.json")
    except Exception as e:
        print(f"  warn: item {item_id} failed: {e}", file=sys.stderr)
        return None


def to_iso(ts: int | None) -> str | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=80,
                    help="Max number of beststories IDs to inspect (max 500).")
    ap.add_argument("--min-score", type=int, default=50,
                    help="Drop items with score below this.")
    args = ap.parse_args()

    print(f"Fetching /beststories.json (limit={args.limit})", file=sys.stderr)
    ids = _get("beststories.json")[: args.limit]

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        raw = list(ex.map(fetch_item, ids))

    items: list[dict] = []
    for it in raw:
        if not it or it.get("type") != "story":
            continue
        score = it.get("score", 0)
        if score < args.min_score:
            continue
        title = (it.get("title") or "").strip()
        if not title:
            continue
        hn_url = f"https://news.ycombinator.com/item?id={it['id']}"
        url = it.get("url") or hn_url
        summary_bits = [
            f"HN score: {score}",
            f"comments: {it.get('descendants', 0)}",
            f"by: {it.get('by', '?')}",
        ]
        items.append({
            "title": title,
            "url": url,
            "published_at": to_iso(it.get("time")),
            "summary": " · ".join(summary_bits),
            "language": "en",
            "hn_id": it["id"],
            "hn_url": hn_url,
            "hn_score": score,
            "hn_comments": it.get("descendants", 0),
        })

    items.sort(key=lambda x: x["hn_score"], reverse=True)
    json.dump(items, sys.stdout, ensure_ascii=False, indent=2)
    print(f"\nhn-best: {len(items)} stories (score >= {args.min_score})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
