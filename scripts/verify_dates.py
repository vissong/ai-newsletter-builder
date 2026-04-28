#!/usr/bin/env python3
"""
词元长街 — 日期验证脚本
Phase 4.3: 对 published_at == fetched_at 的可见条目，读取网页提取真实发布日期，
           如过期(>48h)则标记 trimmed。

用法:
  python3 scripts/verify_dates.py site/data/raw/2026-04-28/merged.json

依赖: requests (stdlib: re, json, sys, datetime)
"""

import json
import re
import sys
import os
import subprocess
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# ─── 配置 ───
MAX_AGE_HOURS = 48
MAX_WORKERS = 6
FETCH_TIMEOUT = 15  # seconds per URL

# ─── 不需要验证的 URL 模式（社交媒体/视频，页面上日期不可靠或无意义）───
SKIP_DOMAINS = {
    "x.com", "twitter.com",       # 推文：follow-builders 已有过滤
}

# YouTube 视频和 Reddit 帖子：标题中经常含日期线索，直接从标题判断
TITLE_DATE_SOURCES = {"youtube.com", "reddit.com", "www.youtube.com", "www.reddit.com"}

# ─── 日期提取模式 ───

# ISO 格式: 2026-04-28T10:00:00Z, 2026-04-28
ISO_DATE_RE = re.compile(
    r'(?:published|datePublished|date_published|article:published_time|pubdate|'
    r'publish_date|post_date|created_at|dateCreated|uploadDate|datePosted|time|datetime)'
    r'["\s:=>{]*(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?(?:[Z+\-][\d:]*)?)?)',
    re.IGNORECASE,
)

# HTML time tag: <time datetime="2026-04-28">
TIME_TAG_RE = re.compile(
    r'<time[^>]*datetime=["\'](\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?(?:[Z+\-][\d:]*)?)?)["\']',
    re.IGNORECASE,
)

# meta tags: <meta property="article:published_time" content="2026-04-28T...">
META_DATE_RE = re.compile(
    r'<meta[^>]*(?:property|name)=["\'](?:article:published_time|date|pubdate|'
    r'og:article:published_time|sailthru\.date|dc\.date|DC\.date\.issued|dcterms\.date|parsely-pub-date)'
    r'["\'][^>]*content=["\'](\d{4}-\d{2}-\d{2}(?:T[^"\']*)?)["\']',
    re.IGNORECASE,
)

# JSON-LD datePublished
JSONLD_DATE_RE = re.compile(
    r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2}(?:T[^"]*)?)"',
    re.IGNORECASE,
)

# 中文日期: 2026年4月28日
ZH_DATE_RE = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')

# 英文日期: April 28, 2026 / 28 April 2026 / Apr 28, 2026
EN_MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
EN_DATE_RE = re.compile(
    r'(?:' +
    '|'.join(EN_MONTH_MAP.keys()) +
    r')[\s.]+(\d{1,2})[\s,]+(\d{4})',
    re.IGNORECASE,
)
EN_DATE_RE2 = re.compile(
    r'(\d{1,2})[\s]+(?:' +
    '|'.join(EN_MONTH_MAP.keys()) +
    r')[\s,]+(\d{4})',
    re.IGNORECASE,
)

# 标题中的日期线索
TITLE_DATE_RE = re.compile(
    r'(\d{4})年(\d{1,2})月(\d{1,2})日|'  # 2026年4月10日
    r'(\d{4})年(\d{1,2})月第?\d+周|'       # 2026年4月第3周
    r'(\d{1,2})月(\d{1,2})日|'             # 4月10日 (assume current year)
    r'(?:' + '|'.join(EN_MONTH_MAP.keys()) + r')\s+(\d{1,2}),?\s+(\d{4})',  # April 10, 2026
    re.IGNORECASE,
)


def parse_date(date_str: str):
    """Try to parse various date formats into a datetime."""
    if not date_str:
        return None
    date_str = date_str.strip().rstrip("Z")
    
    # Try ISO formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
    ]:
        try:
            return datetime.strptime(date_str[:len(fmt.replace('%', 'X'))], fmt).replace(tzinfo=timezone.utc)
        except (ValueError, IndexError):
            continue
    
    # Try with timezone offset
    try:
        # Handle +08:00 style offsets
        clean = re.sub(r'([+-]\d{2}):(\d{2})$', r'\1\2', date_str)
        return datetime.strptime(clean, "%Y-%m-%dT%H:%M:%S%z")
    except (ValueError, IndexError):
        pass
    
    return None


def extract_date_from_html(html: str):
    """Extract the most likely publish date from HTML content."""
    candidates = []
    
    # Priority 1: JSON-LD datePublished (most reliable)
    for m in JSONLD_DATE_RE.finditer(html[:50000]):
        d = parse_date(m.group(1))
        if d:
            candidates.append(("jsonld", d))
    
    # Priority 2: meta tags
    for m in META_DATE_RE.finditer(html[:20000]):
        d = parse_date(m.group(1))
        if d:
            candidates.append(("meta", d))
    
    # Priority 3: <time> tags
    for m in TIME_TAG_RE.finditer(html[:50000]):
        d = parse_date(m.group(1))
        if d:
            candidates.append(("time_tag", d))
    
    # Priority 4: structured data attributes
    for m in ISO_DATE_RE.finditer(html[:50000]):
        d = parse_date(m.group(1))
        if d:
            candidates.append(("structured", d))
    
    # Priority 5: Chinese dates in text
    for m in ZH_DATE_RE.finditer(html[:30000]):
        try:
            d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
            candidates.append(("zh_date", d))
        except ValueError:
            pass
    
    # Priority 6: English dates in text
    for m in EN_DATE_RE.finditer(html[:30000]):
        month_str = m.group(0).split()[0].lower().rstrip('.')
        month_num = EN_MONTH_MAP.get(month_str)
        if month_num:
            try:
                d = datetime(int(m.group(2)), month_num, int(m.group(1)), tzinfo=timezone.utc)
                candidates.append(("en_date", d))
            except ValueError:
                pass
    
    if not candidates:
        return None
    
    # Pick earliest plausible date (filter out future dates and very old dates)
    now = datetime.now(timezone.utc)
    year_ago = now - timedelta(days=365)
    
    valid = [(src, d) for src, d in candidates if year_ago <= d <= now + timedelta(days=1)]
    if not valid:
        return None
    
    # Prefer higher priority sources; among same priority, pick the earliest
    priority = {"jsonld": 0, "meta": 1, "time_tag": 2, "structured": 3, "zh_date": 4, "en_date": 5}
    valid.sort(key=lambda x: (priority.get(x[0], 99), x[1]))
    
    return valid[0][1]


def extract_date_from_title(title: str, run_date: datetime):
    """Extract date hints from the item title."""
    # 2026年4月10日
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', title)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
        except ValueError:
            pass
    
    # 4月10日 (no year -> assume run_date year)
    m = re.search(r'(\d{1,2})月(\d{1,2})日', title)
    if m:
        try:
            return datetime(run_date.year, int(m.group(1)), int(m.group(2)), tzinfo=timezone.utc)
        except ValueError:
            pass
    
    # 4月第3周 -> estimate mid-week date
    m = re.search(r'(\d{1,2})月第(\d)周', title)
    if m:
        month, week = int(m.group(1)), int(m.group(2))
        try:
            # Estimate: week N of month -> day = (N-1)*7 + 4 (mid-week)
            day = min((week - 1) * 7 + 4, 28)
            return datetime(run_date.year, month, day, tzinfo=timezone.utc)
        except ValueError:
            pass
    
    # English: April 28, 2026 / Apr 10, 2026
    for m in EN_DATE_RE.finditer(title):
        month_str = m.group(0).split()[0].lower().rstrip('.')
        month_num = EN_MONTH_MAP.get(month_str)
        if month_num:
            try:
                return datetime(int(m.group(2)), month_num, int(m.group(1)), tzinfo=timezone.utc)
            except ValueError:
                pass
    
    return None


def fetch_page(url: str):
    """Fetch a URL and return the raw HTML (first 80KB)."""
    try:
        result = subprocess.run(
            ["curl", "-sL", "-m", str(FETCH_TIMEOUT), "-A",
             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
             "--max-filesize", "500000",
             url],
            capture_output=True, text=True, timeout=FETCH_TIMEOUT + 5,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout[:80000]
    except (subprocess.TimeoutExpired, Exception):
        pass
    return None


def check_item(item: dict, cutoff: datetime, run_date: datetime):
    """
    Check a single item. Returns a dict with verification result or None if skipped.
    """
    url = item.get("url", "")
    title = item.get("title", "") or item.get("title_original", "")
    item_id = item.get("id", "?")
    domain = urlparse(url).netloc.lower()
    
    result = {"id": item_id, "url": url, "title": title[:60]}
    
    # 1. Check title for date hints first (cheap, no network needed)
    title_date = extract_date_from_title(title, run_date)
    if title_date and title_date < cutoff:
        result["method"] = "title_date"
        result["date"] = title_date.strftime("%Y-%m-%d")
        result["stale"] = True
        return result
    
    # 2. Skip social media that we can't reliably extract dates from
    if domain in SKIP_DOMAINS:
        result["method"] = "skip_domain"
        result["stale"] = False
        return result
    
    # 3. YouTube/Reddit: rely on title date only (already checked above)
    base_domain = domain.replace("www.", "")
    if base_domain in TITLE_DATE_SOURCES:
        # If title had no date, we can't verify — leave as is
        if title_date:
            result["method"] = "title_date"
            result["date"] = title_date.strftime("%Y-%m-%d")
            result["stale"] = title_date < cutoff
        else:
            result["method"] = "title_no_date"
            result["stale"] = False
        return result
    
    # 4. Fetch the page and extract date
    html = fetch_page(url)
    if not html or len(html) < 200:
        result["method"] = "fetch_failed"
        result["stale"] = False
        return result
    
    page_date = extract_date_from_html(html)
    if page_date:
        result["method"] = "page_date"
        result["date"] = page_date.strftime("%Y-%m-%d")
        result["stale"] = page_date < cutoff
        return result
    
    # 5. Couldn't determine date from page either
    result["method"] = "no_date_found"
    result["stale"] = False
    return result


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/verify_dates.py <merged.json>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r") as f:
        items = json.load(f)

    # Infer run date
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', path)
    run_date_str = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
    run_date = datetime.strptime(run_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    cutoff = run_date - timedelta(hours=MAX_AGE_HOURS)

    print(f"📅 Run date: {run_date_str}, cutoff: {cutoff.strftime('%Y-%m-%d %H:%M')}")
    print(f"📦 Total items: {len(items)}")

    # Find items needing verification: visible + (pub==fetch or no pub)
    needs_check = []
    for item in items:
        if item.get("trimmed"):
            continue
        pub = item.get("published_at", "")
        fetch = item.get("fetched_at", "")
        if (pub and fetch and pub == fetch) or not pub:
            needs_check.append(item)

    print(f"🔍 Items needing date verification: {len(needs_check)}")
    print()

    if not needs_check:
        print("✅ No items need verification.")
        return

    # Check items in parallel
    results = []
    item_map = {item.get("id"): item for item in items}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(check_item, item, cutoff, run_date): item
            for item in needs_check
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                item = futures[future]
                print(f"  ❌ Error checking {item.get('id', '?')}: {e}")

    # Apply results
    stale_count = 0
    verified_count = 0
    for result in sorted(results, key=lambda r: r.get("stale", False), reverse=True):
        item_id = result["id"]
        is_stale = result.get("stale", False)
        method = result.get("method", "?")
        date_str = result.get("date", "?")
        title = result.get("title", "?")

        if is_stale:
            stale_count += 1
            # Mark as trimmed in the original data
            if item_id in item_map:
                item_map[item_id]["trimmed"] = True
                item_map[item_id]["trimmed_reason"] = f"stale: {date_str} (via {method})"
            print(f"  🗑️ STALE [{method}] {date_str} | {title}")
        else:
            verified_count += 1
            if method == "page_date":
                # Update published_at with the real date
                if item_id in item_map:
                    item_map[item_id]["published_at"] = result["date"] + "T00:00:00+00:00"
                print(f"  ✅ OK [{method}] {date_str} | {title}")
            elif method in ("title_no_date", "fetch_failed", "no_date_found", "skip_domain"):
                print(f"  ⚠️ UNKNOWN [{method}] | {title}")
            else:
                print(f"  ✅ OK [{method}] {date_str} | {title}")

    print(f"\n📊 Results: {stale_count} stale (trimmed), {verified_count} verified/unknown")
    
    # Recalculate visible count
    visible = [i for i in items if not i.get("trimmed")]
    print(f"📦 Visible after verification: {len(visible)}")

    # Write back
    with open(path, "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"\n已写回 {path}")


if __name__ == "__main__":
    main()
