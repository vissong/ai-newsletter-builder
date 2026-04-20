#!/usr/bin/env python3
"""Fetch VentureBeat AI articles using Playwright headless Chromium.

Outputs JSON array to stdout.
"""

import json
import sys
from datetime import datetime, timezone, timedelta

from playwright.sync_api import sync_playwright


URL = "https://venturebeat.com/category/ai/"
ITEM_LIMIT = 15
TIME_WINDOW_HOURS = 96
RECENT_HOURS = 24
EXCLUDE_KEYWORDS = ["Partner Content", "Sponsored"]


def parse_published_at(raw):
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(raw, fmt).astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def fetch(browser):
    page = browser.new_page()
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        items = page.evaluate("""
        (() => {
            const articles = document.querySelectorAll('article');
            const els = articles.length > 0
                ? Array.from(articles)
                : Array.from(document.querySelectorAll('h2 a, h3 a'));

            return els.slice(0, """ + str(ITEM_LIMIT) + """).map(el => {
                const isLink = el.tagName === 'A';
                if (isLink) {
                    return { title: el.textContent.trim(), url: el.href, published_at: '' };
                }
                const a = el.querySelector('a[href]');
                const h = el.querySelector('h2, h3, h1');
                const time = el.querySelector('time');
                return {
                    title: (h || a)?.textContent?.trim() || '',
                    url: a?.href || '',
                    published_at: time?.getAttribute('datetime') || ''
                };
            }).filter(i => i.title && i.url);
        })()
        """)
    finally:
        page.close()
    return items


def fetch_summary(browser, url):
    page = browser.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1000)
        summary = page.evaluate("""
        (() => {
            const selectors = [
                'article p',
                '.article-content p',
                '[class*="ArticleBody"] p',
                'main p'
            ];
            for (const sel of selectors) {
                const ps = document.querySelectorAll(sel);
                for (const p of ps) {
                    const text = p.textContent.trim();
                    if (text.length > 50 && !text.startsWith('Credit:') && !text.startsWith('Image credit:')) {
                        return text.slice(0, 300);
                    }
                }
            }
            return '';
        })()
        """)
        return summary
    except Exception:
        return ""
    finally:
        page.close()


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=TIME_WINDOW_HOURS)
    recent_cutoff = now - timedelta(hours=RECENT_HOURS)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            raw_items = fetch(browser)

            results = []
            for item in raw_items:
                title = item["title"]
                if any(kw in title for kw in EXCLUDE_KEYWORDS):
                    continue

                pub = parse_published_at(item.get("published_at", ""))
                if pub and pub < cutoff:
                    continue

                summary = fetch_summary(browser, item["url"])
                if any(kw in summary for kw in EXCLUDE_KEYWORDS):
                    continue

                entry = {
                    "title": title,
                    "url": item["url"],
                    "published_at": item.get("published_at", ""),
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
    print(f"Fetched {len(results)} items from VentureBeat AI (window: {TIME_WINDOW_HOURS}h)", file=sys.stderr)


if __name__ == "__main__":
    main()
