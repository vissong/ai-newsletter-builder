#!/usr/bin/env python3
"""Fetch 36Kr AI articles using Playwright headless Chromium.

Outputs JSON array to stdout.
"""

import json
import sys
from datetime import datetime, timezone, timedelta

from playwright.sync_api import sync_playwright


URL = "https://36kr.com/search/articles/AI"
ITEM_LIMIT = 15
TIME_WINDOW_HOURS = 48
RECENT_HOURS = 24
EXCLUDE_KEYWORDS = ["广告", "推广", "赞助"]

JS_LIST = r"""
(() => {
    const links = Array.from(document.querySelectorAll('a[href]'));
    const seen = new Set();
    const results = [];
    for (const a of links) {
        const href = a.href;
        if (!href || seen.has(href) || href.includes('#')) continue;
        if (!/\/p\/\d+/.test(href) && !/\/newsflashes\/\d+/.test(href)) continue;
        const text = a.textContent.trim();
        if (text.length < 10 || text.length > 200) continue;
        seen.add(href);
        results.push({ title: text.slice(0, 150), url: href });
        if (results.length >= LIMIT) break;
    }
    return results;
})()
""".replace("LIMIT", str(ITEM_LIMIT))

JS_DETAIL = """
(() => {
    const og = document.querySelector('meta[property="og:title"]');
    const h1 = document.querySelector('h1');
    const title = (og && og.content) || (h1 && h1.textContent.trim()) || '';

    const timeMeta = document.querySelector('meta[property="article:published_time"]');
    const timeEl = document.querySelector('time[datetime]');
    const published = (timeMeta && timeMeta.content) || (timeEl && timeEl.getAttribute('datetime')) || '';

    const ps = document.querySelectorAll('article p, .article-content p, .common-width p');
    let summary = '';
    for (const p of ps) {
        const t = p.textContent.trim();
        if (t.length > 30) { summary = t.slice(0, 300); break; }
    }
    return { title, published, summary };
})()
"""


def parse_dt(raw):
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M%z",
                "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=TIME_WINDOW_HOURS)
    recent_cutoff = now - timedelta(hours=RECENT_HOURS)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            page = browser.new_page()
            page.goto(URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            raw_items = page.evaluate(JS_LIST)
            page.close()

            results = []
            for item in raw_items:
                title = item["title"]
                if any(kw in title for kw in EXCLUDE_KEYWORDS):
                    continue

                detail_page = browser.new_page()
                try:
                    detail_page.goto(item["url"], wait_until="domcontentloaded", timeout=15000)
                    detail_page.wait_for_timeout(1500)
                    detail = detail_page.evaluate(JS_DETAIL)
                except Exception:
                    detail = {"title": title, "published": "", "summary": ""}
                finally:
                    detail_page.close()

                full_title = detail.get("title") or title
                if any(kw in full_title for kw in EXCLUDE_KEYWORDS):
                    continue

                pub_raw = detail.get("published", "")
                pub = parse_dt(pub_raw)

                if pub and pub < cutoff:
                    continue

                summary = detail.get("summary", "")
                if any(kw in summary for kw in EXCLUDE_KEYWORDS):
                    continue

                entry = {
                    "title": full_title,
                    "url": item["url"],
                    "published_at": pub_raw,
                    "summary": summary,
                    "language": "zh",
                    "fetched_at": now.isoformat(),
                }
                if pub and pub >= recent_cutoff:
                    entry["recent"] = True
                results.append(entry)

            browser.close()
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    print(file=sys.stderr)
    print(f"Fetched {len(results)} items from 36Kr AI (window: {TIME_WINDOW_HOURS}h)", file=sys.stderr)


if __name__ == "__main__":
    main()
