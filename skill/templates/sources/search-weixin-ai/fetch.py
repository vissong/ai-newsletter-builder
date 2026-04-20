#!/usr/bin/env python3
"""Search WeChat articles (mp.weixin.qq.com) for AI news via Tavily CLI."""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

QUERY = 'AI 人工智能 大模型'
TOPIC = "news"
TIME_RANGE = "week"
MAX_RESULTS = 15
LANGUAGE = "zh"
TIME_WINDOW_HOURS = 48
RECENT_HOURS = 24
INCLUDE_DOMAINS = ["mp.weixin.qq.com"]
EXCLUDE_DOMAINS = []
EXCLUDE_KEYWORDS = ["广告", "推广", "赞助"]


def parse_pub_date(s):
    if not s:
        return None
    try:
        return parsedate_to_datetime(s).astimezone(timezone.utc)
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=TIME_WINDOW_HOURS)
    recent_cutoff = now - timedelta(hours=RECENT_HOURS)

    cmd = ["tvly", "search", QUERY, "--json", "--max-results", str(MAX_RESULTS)]
    if TOPIC:
        cmd += ["--topic", TOPIC]
    if TIME_RANGE:
        cmd += ["--time-range", TIME_RANGE]
    if INCLUDE_DOMAINS:
        cmd += ["--include-domains", ",".join(INCLUDE_DOMAINS)]
    if EXCLUDE_DOMAINS:
        cmd += ["--exclude-domains", ",".join(EXCLUDE_DOMAINS)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"tvly failed: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        data = json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print("tvly search timed out", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    items = []
    for r in data.get("results", []):
        title = r.get("title", "").strip()
        url = r.get("url", "")
        if not title or not url:
            continue

        if any(kw in title for kw in EXCLUDE_KEYWORDS):
            continue

        pub = parse_pub_date(r.get("published_date", ""))
        if pub and pub < cutoff:
            continue

        content = r.get("content", "")
        if any(kw in content[:200] for kw in EXCLUDE_KEYWORDS):
            continue

        summary = content[:400] if content else title

        entry = {
            "title": title,
            "url": url,
            "published_at": pub.isoformat() if pub else r.get("published_date", ""),
            "summary": summary,
            "language": LANGUAGE,
            "fetched_at": now.isoformat(),
        }
        if pub and pub >= recent_cutoff:
            entry["recent"] = True
        items.append(entry)

    json.dump(items, sys.stdout, ensure_ascii=False, indent=2)
    print(f"\n{len(items)} items from Tavily search: {QUERY}", file=sys.stderr)


if __name__ == "__main__":
    main()
