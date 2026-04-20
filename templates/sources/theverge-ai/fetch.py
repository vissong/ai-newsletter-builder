#!/usr/bin/env python3
"""Fetch The Verge AI articles using Playwright headless Chromium.

Outputs JSON array to stdout.
"""

import json
import sys
from datetime import datetime, timezone, timedelta

from playwright.sync_api import sync_playwright


URL = "https://www.theverge.com/ai-artificial-intelligence"
ITEM_LIMIT = 15
TIME_WINDOW_HOURS = 48
RECENT_HOURS = 24

JS_LIST = r"""
(() => {
    const links = Array.from(document.querySelectorAll('a[href]'));
    const seen = new Set();
    const results = [];
    for (const a of links) {
        const href = a.href;
        if (!href || seen.has(href) || href.includes('#')) continue;
        if (!/\/\d{5,}\//.test(href)) continue;
        if (!href.includes('theverge.com')) continue;
        const text = a.textContent.trim().replace(/CommentsComment Icon Bubble\d+/g, '').trim();
        if (text.length < 15) continue;
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

    const timeEl = document.querySelector('time[datetime]');
    const published = timeEl ? timeEl.getAttribute('datetime') : '';

    const ps = document.querySelectorAll('article p, main p, [class*="article"] p, [class*="body"] p, p');
    let summary = '';
    for (const p of ps) {
        const t = p.textContent.trim();
        if (t.length > 60 && !t.includes('daily email digest') && !t.includes('homepage feed')) {
            summary = t.slice(0, 300); break;
        }
    }
    return { title, published, summary };
})()
"""


def parse_dt(raw):
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M%z",
                "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(raw, fmt).astimezone(timezone.utc)
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
                detail_page = browser.new_page()
                try:
                    detail_page.goto(item["url"], wait_until="domcontentloaded", timeout=15000)
                    detail_page.wait_for_timeout(1500)
                    detail = detail_page.evaluate(JS_DETAIL)
                except Exception:
                    detail = {"title": item["title"], "published": "", "summary": ""}
                finally:
                    detail_page.close()

                title = detail.get("title") or item["title"]
                pub_raw = detail.get("published", "")
                pub = parse_dt(pub_raw)

                if pub and pub < cutoff:
                    continue

                entry = {
                    "title": title,
                    "url": item["url"],
                    "published_at": pub_raw,
                    "summary": detail.get("summary", ""),
                    "language": "en",
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
    print(f"Fetched {len(results)} items from The Verge AI (window: {TIME_WINDOW_HOURS}h)", file=sys.stderr)


if __name__ == "__main__":
    main()
