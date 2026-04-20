#!/usr/bin/env python3
"""
Fetch content from zarazhangrui/follow-builders and emit a JSON array to stdout.

This source tracks three feed files (feed-x.json, feed-blogs.json, feed-podcasts.json)
in a GitHub repo. Each file is updated daily with content from AI KOC/KOL builders.

Change detection: SHA-256 hashes of each file are stored in
  <cache-dir>/.hashes.json
Only files whose hash changed since the last run are processed. On a clean run
(no hash file), all files are processed.

Usage:
    python fetch.py --cache-dir site/data/sources/follow-builders \
                    [--recent-hours 24] [--force]

Output: JSON array to stdout matching the source extension contract.
Diagnostics go to stderr.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_URL = "https://github.com/zarazhangrui/follow-builders.git"
FEED_FILES = ["feed-x.json", "feed-blogs.json", "feed-podcasts.json"]
HASH_FILE = ".hashes.json"


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git_clone(repo_url: str, dest: Path) -> None:
    subprocess.run(["git", "clone", "--depth=1", repo_url, str(dest)], check=True)


def git_pull(repo_dir: Path) -> None:
    subprocess.run(["git", "-C", str(repo_dir), "pull", "--ff-only"], check=True)


def ensure_repo(cache_dir: Path) -> None:
    if (cache_dir / ".git").exists():
        git_pull(cache_dir)
    else:
        cache_dir.mkdir(parents=True, exist_ok=True)
        git_clone(REPO_URL, cache_dir)


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------

def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_hashes(cache_dir: Path) -> dict[str, str]:
    p = cache_dir / HASH_FILE
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


def save_hashes(cache_dir: Path, hashes: dict[str, str]) -> None:
    (cache_dir / HASH_FILE).write_text(json.dumps(hashes, indent=2))


def changed_files(cache_dir: Path) -> list[str]:
    old = load_hashes(cache_dir)
    changed = []
    for fname in FEED_FILES:
        path = cache_dir / fname
        if not path.exists():
            continue
        h = file_sha256(path)
        if old.get(fname) != h:
            changed.append(fname)
    return changed


def commit_hashes(cache_dir: Path) -> None:
    new = {}
    for fname in FEED_FILES:
        p = cache_dir / fname
        if p.exists():
            new[fname] = file_sha256(p)
    save_hashes(cache_dir, new)


# ---------------------------------------------------------------------------
# Parsers — one per feed type, each returns list[dict]
# ---------------------------------------------------------------------------

def _is_recent(ts: str, recent_hours: int) -> bool:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - dt <= timedelta(hours=recent_hours)
    except Exception:
        return False


def _ts(value: str | None, fallback: str) -> str:
    return value if value else fallback


def parse_x(data: dict, fetched_at: str, recent_hours: int) -> list[dict]:
    items = []
    for builder in data.get("x", data.get("builders", data if isinstance(data, list) else [])):
        handle = builder.get("handle", "unknown")
        name = builder.get("name", handle)
        for tweet in builder.get("tweets", []):
            text: str = tweet.get("text", "").strip()
            if not text:
                continue
            url = tweet.get("url", f"https://x.com/{handle}")
            created_at = tweet.get("createdAt", fetched_at)
            title = text[:80] + ("…" if len(text) > 80 else "")
            likes = tweet.get("likes", 0)
            rts = tweet.get("retweets", 0)
            summary = f"[{name} @{handle} · likes:{likes} rt:{rts}] {text}"
            items.append({
                "title": title,
                "url": url,
                "published_at": created_at,
                "summary": summary,
                "language": "en",
            })
    return items


def parse_blogs(data: dict, fetched_at: str, recent_hours: int) -> list[dict]:
    items = []
    for item in data.get("blogs", []):
        title = item.get("title", "").strip()
        url = item.get("url", "")
        if not title or not url:
            continue
        published_at = item.get("publishedAt") or fetched_at
        author = item.get("author") or item.get("name", "")
        description = item.get("description", "").strip()
        content = item.get("content", "").strip()
        summary = description or content[:400] or title
        if author:
            summary = f"[{author}] {summary}"
        items.append({
            "title": title,
            "url": url,
            "published_at": published_at,
            "summary": summary,
            "language": "en",
        })
    return items


def parse_podcasts(data: dict, fetched_at: str, recent_hours: int) -> list[dict]:
    items = []
    for item in data.get("podcasts", []):
        title = item.get("title", "").strip()
        url = item.get("url", "")
        if not title or not url:
            continue
        published_at = item.get("publishedAt") or fetched_at
        name = item.get("name", "")
        transcript = item.get("transcript", "").strip()
        summary = transcript[:400] if transcript else title
        if name:
            summary = f"[{name}] {summary}"
        items.append({
            "title": title,
            "url": url,
            "published_at": published_at,
            "summary": summary,
            "language": "en",
        })
    return items


PARSERS = {
    "feed-x.json": parse_x,
    "feed-blogs.json": parse_blogs,
    "feed-podcasts.json": parse_podcasts,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", required=True,
                    help="Local directory to clone/pull the repo into")
    ap.add_argument("--recent-hours", type=int, default=24)
    ap.add_argument("--force", action="store_true",
                    help="Process all files regardless of change detection")
    args = ap.parse_args()

    cache_dir = Path(args.cache_dir)

    print(f"Syncing {REPO_URL} → {cache_dir}", file=sys.stderr)
    try:
        ensure_repo(cache_dir)
    except subprocess.CalledProcessError as e:
        print(f"error: git operation failed: {e}", file=sys.stderr)
        return 2

    if args.force:
        to_process = [f for f in FEED_FILES if (cache_dir / f).exists()]
        print("--force: processing all files", file=sys.stderr)
    else:
        to_process = changed_files(cache_dir)
        if not to_process:
            print("No feed files changed since last run — skipping.", file=sys.stderr)
            json.dump([], sys.stdout)
            return 0
        print(f"Changed files: {to_process}", file=sys.stderr)

    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    all_items: list[dict] = []

    for fname in to_process:
        path = cache_dir / fname
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"warning: could not parse {fname}: {e}", file=sys.stderr)
            continue
        parser = PARSERS.get(fname)
        if parser is None:
            print(f"warning: no parser for {fname}", file=sys.stderr)
            continue
        items = parser(data, fetched_at, args.recent_hours)
        print(f"  {fname}: {len(items)} items", file=sys.stderr)
        all_items.extend(items)

    json.dump(all_items, sys.stdout, ensure_ascii=False, indent=2)
    print(f"\nfollow-builders: {len(all_items)} items total", file=sys.stderr)

    commit_hashes(cache_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
