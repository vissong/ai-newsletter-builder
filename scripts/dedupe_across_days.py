#!/usr/bin/env python3
"""
Cross-day dedupe: remove items from a target date's merged.json that already
appeared in one of the previous N days' issues.

Rules (applied in order, first match wins):
  1. Same canonical URL (tracking params stripped) — also checks alt_urls on both sides.
  2. Normalized title equality, or Levenshtein distance ≤ 4 on either zh or original title.

Items that match a prior-day entry are REMOVED from the target merged.json
(not merely flagged), because the goal is "don't show yesterday's news again."

Usage:
    python3 scripts/dedupe_across_days.py --site site --date 2026-04-21 [--lookback 3]

After running, you should also rebuild the issue manifest (issues.json) so counts
reflect the trimmed list.
"""
import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path


def norm_text(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_url(u: str) -> str:
    u = (u or "").split("?")[0].rstrip("/")
    return u.lower()


def levenshtein(a: str, b: str, max_d: int = 4) -> int:
    if abs(len(a) - len(b)) > max_d:
        return max_d + 1
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb))
        if min(cur) > max_d:
            return max_d + 1
        prev = cur
    return prev[-1]


def load_prior_index(site_dir: Path, target_date: str, lookback: int):
    """Return (url_set, titles_list) aggregated across the previous `lookback` days."""
    target = date.fromisoformat(target_date)
    urls: set[str] = set()
    titles: list[str] = []
    for delta in range(1, lookback + 1):
        prior = (target - timedelta(days=delta)).isoformat()
        merged_path = site_dir / "data" / "raw" / prior / "merged.json"
        if not merged_path.exists():
            continue
        with merged_path.open("r", encoding="utf-8") as f:
            prior_items = json.load(f)
        for m in prior_items:
            u = norm_url(m.get("url", ""))
            if u:
                urls.add(u)
            for au in m.get("alt_urls", []) or []:
                urls.add(norm_url(au))
            for key in ("title", "title_original"):
                t = norm_text(m.get(key, ""))
                if t and len(t) >= 8:
                    titles.append(t)
    return urls, titles


def is_duplicate(item, prior_urls, prior_titles):
    u = norm_url(item.get("url", ""))
    if u and u in prior_urls:
        return True, f"url:{u}"
    for au in item.get("alt_urls", []) or []:
        au_n = norm_url(au)
        if au_n and au_n in prior_urls:
            return True, f"alt_url:{au_n}"
    for key in ("title", "title_original"):
        t = norm_text(item.get(key, ""))
        if not t or len(t) < 8:
            continue
        for pt in prior_titles:
            if t == pt or levenshtein(t, pt, 4) <= 4:
                return True, f"title:{t[:60]}"
    return False, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="site", help="site directory")
    ap.add_argument("--date", required=True, help="target date YYYY-MM-DD")
    ap.add_argument("--lookback", type=int, default=3, help="how many prior days to check")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    site_dir = Path(args.site)
    target_merged = site_dir / "data" / "raw" / args.date / "merged.json"
    if not target_merged.exists():
        print(f"error: {target_merged} does not exist", file=sys.stderr)
        return 1

    prior_urls, prior_titles = load_prior_index(site_dir, args.date, args.lookback)
    with target_merged.open("r", encoding="utf-8") as f:
        items = json.load(f)

    kept, removed = [], []
    for m in items:
        dup, why = is_duplicate(m, prior_urls, prior_titles)
        if dup:
            removed.append((m.get("id"), m.get("title"), why))
        else:
            kept.append(m)

    # Renumber ids sequentially for stable output
    for i, m in enumerate(kept):
        m["id"] = f"item-{i}"

    print(f"loaded {len(items)} items from {args.date}")
    print(f"prior index: {len(prior_urls)} urls, {len(prior_titles)} titles "
          f"(lookback={args.lookback}d)")
    print(f"removed {len(removed)} duplicates:")
    for mid, title, why in removed:
        print(f"  - [{mid}] {title}  ({why})")
    print(f"kept {len(kept)} items")

    if args.dry_run:
        print("(dry run — file not written)")
        return 0

    with target_merged.open("w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)
    print(f"wrote {target_merged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
