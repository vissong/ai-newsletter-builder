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
    const cards = document.querySelectorAll('.duet--content-cards--content-card');
    const seen = new Set();
    const results = [];

    for (const card of cards) {
        const links = card.querySelectorAll('a[href]');
        let articleUrl = '';
        let linkText = '';

        for (const a of links) {
            const href = a.href;
            if (!href || !href.includes('theverge.com/')) continue;
            if (!/\/\d{5,}\//.test(href)) continue;
            if (href.includes('#comments')) continue;
            if (seen.has(href)) break;
            articleUrl = href;
            linkText = a.textContent.trim().replace(/\s+/g, ' ');
            break;
        }

        if (!articleUrl || seen.has(articleUrl)) continue;
        seen.add(articleUrl);

        // Headline: prefer link text, fall back to card text
        let title = linkText;
        if (!title || title.length < 15) {
            const raw = card.textContent.replace(/\s+/g, ' ').trim();
            // Strip author/date/comment noise
            title = raw
                .replace(/CommentsComment Icon Bubble\d*/g, '')
                .replace(/\d{1,2}:\d{2}\s*(AM|PM)\s*GMT[+-]\d+/gi, '')
                .replace(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}/gi, '')
                .trim();
            // Strip leading author name pattern: "FirstnameLastname" or "Firstname O'Lastname"
            title = title.replace(/^[A-Z][a-z]+(?:\s+(?:O')?[A-Z][a-z]+)+(?=\s*[A-Z])/, '').trim();
        }
        title = title.replace(/CommentsComment Icon Bubble\d*/g, '').trim();
        if (!title || title.length < 10) continue;

        const timeEl = card.querySelector('time[datetime]');
        const datetime = timeEl ? timeEl.getAttribute('datetime') : '';

        results.push({title: title.slice(0, 200), url: articleUrl, published_at: datetime});
        if (results.length >= LIMIT) break;
    }
    return results;
})()
""".replace("LIMIT", str(ITEM_LIMIT))

JS_DETAIL = """
(() => {
    const ps = document.querySelectorAll('article p, main p, [class*="article"] p, [class*="body"] p, p');
    let summary = '';
    for (const p of ps) {
        const t = p.textContent.trim();
        if (t.length > 60 && !t.includes('daily email digest') && !t.includes('homepage feed')) {
            summary = t.slice(0, 300); break;
        }
    }
    return summary;
})()
"""


def parse_dt(raw):
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M%z",
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
                pub_raw = item.get("published_at", "")
                pub = parse_dt(pub_raw)

                if pub and pub < cutoff:
                    continue

                detail_page = browser.new_page()
                try:
                    detail_page.goto(item["url"], wait_until="domcontentloaded", timeout=15000)
                    detail_page.wait_for_timeout(1500)
                    summary = detail_page.evaluate(JS_DETAIL)
                except Exception:
                    summary = ""
                finally:
                    detail_page.close()

                entry = {
                    "title": item["title"],
                    "url": item["url"],
                    "published_at": pub_raw,
                    "summary": summary,
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
