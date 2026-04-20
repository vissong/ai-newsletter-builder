#!/usr/bin/env python3
"""
Generate site/feed.xml (RSS 2.0) from site/data/issues.json.

Usage:
    python build_feed.py --site ./site [--base-url https://example.com]

Each issue becomes one <item> with a rich categorized description.
Data source priority:
  1. site/data/raw/<date>/merged.json  — full structured items
  2. site/issues/<date>.html           — parsed from rendered HTML
  3. issues.json top_items             — fallback summary only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape as xmlescape

SKILL_DIR = Path(__file__).resolve().parent.parent

CATEGORY_LABELS = {
    "major-release":     ("重大发布",         "Major Releases"),
    "industry-business": ("行业动态及商业价值", "Industry & Business"),
    "research-frontier": ("研究前沿",          "Research Frontier"),
    "tools-release":     ("工具发布",          "Tools & Developer Releases"),
    "policy-regulation": ("政策监管",          "Policy & Regulation"),
}

# Ordered display sequence
CATEGORY_ORDER = [
    "major-release",
    "industry-business",
    "tools-release",
    "research-frontier",
    "policy-regulation",
]


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_items_from_merged_json(site: Path, date: str) -> dict[str, list[dict]]:
    """
    Load full categorized items from merged.json.
    Returns {category_slug: [item, ...]} or {} if file not found.
    """
    path = site / "data" / "raw" / date / "merged.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    items: list[dict] = raw if isinstance(raw, list) else raw.get("items", [])
    by_cat: dict[str, list[dict]] = {}
    for item in items:
        if item.get("trimmed"):
            continue
        cat = item.get("category") or "industry-business"
        by_cat.setdefault(cat, []).append(item)
    return by_cat


class _IssueHTMLParser(HTMLParser):
    """State-machine parser that extracts category sections and articles from issue HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.categories: list[dict] = []
        self._cur_cat: dict | None = None
        self._cur_item: dict | None = None
        self._in_cat_name = False
        self._in_h3 = False
        self._in_h3_a = False
        self._in_art_dek = False
        self._h3_url = ""
        self._buf = ""

    def handle_starttag(self, tag: str, attrs: list) -> None:
        a = dict(attrs)
        cls = a.get("class", "")

        if tag == "section" and "category-section" in cls:
            self._cur_cat = {"name": "", "items": []}
            self.categories.append(self._cur_cat)
            self._cur_item = None
            return

        if tag == "span" and "cat-name" in cls:
            self._in_cat_name = True
            self._buf = ""
            return

        if tag == "li" and "article" in cls and self._cur_cat is not None:
            self._cur_item = {"title": "", "url": "", "summary": ""}
            self._cur_cat["items"].append(self._cur_item)
            return

        if tag == "h3" and self._cur_item is not None:
            self._in_h3 = True
            return

        if tag == "a" and self._in_h3 and self._cur_item is not None:
            self._in_h3_a = True
            self._h3_url = a.get("href", "")
            self._buf = ""
            return

        if tag == "p" and "art-dek" in cls and self._cur_item is not None:
            self._in_art_dek = True
            self._buf = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self._in_cat_name:
            self._in_cat_name = False
            if self._cur_cat is not None:
                self._cur_cat["name"] = self._buf.strip()
            return

        if tag == "a" and self._in_h3_a:
            self._in_h3_a = False
            if self._cur_item is not None:
                self._cur_item["title"] = self._buf.strip()
                self._cur_item["url"] = self._h3_url
            return

        if tag == "h3" and self._in_h3:
            self._in_h3 = False
            return

        if tag == "p" and self._in_art_dek:
            self._in_art_dek = False
            if self._cur_item is not None:
                self._cur_item["summary"] = self._buf.strip()
            return

        if tag == "section":
            self._cur_cat = None
            self._cur_item = None

    def handle_data(self, data: str) -> None:
        if self._in_cat_name or self._in_h3_a or self._in_art_dek:
            self._buf += data


def load_items_from_html(site: Path, date: str) -> dict[str, list[dict]]:
    """
    Parse issue HTML to extract categorized items.
    Returns {category_name_zh: [item, ...]} or {} if file not found.
    """
    html_path = site / "issues" / f"{date}.html"
    if not html_path.exists():
        return {}
    parser = _IssueHTMLParser()
    parser.feed(html_path.read_text(encoding="utf-8", errors="replace"))
    return {cat["name"]: cat["items"] for cat in parser.categories if cat["items"]}


# ---------------------------------------------------------------------------
# Description builder
# ---------------------------------------------------------------------------

def _render_category_block(cat_zh: str, cat_en: str, items: list[dict], base_url: str) -> str:
    """Render one category's items as HTML for RSS description."""
    parts = [f"<h3>{xmlescape(cat_zh)} · {xmlescape(cat_en)} ({len(items)})</h3><ul>"]
    for item in items:
        title = xmlescape(item.get("title", ""))
        url = item.get("url") or item.get("canonical_url") or ""
        if url and base_url and not url.startswith(("http://", "https://")):
            url = base_url.rstrip("/") + "/" + url.lstrip("/")
        url_attr = xmlescape(url) if url else "#"
        summary = xmlescape(item.get("summary", ""))
        sc = int(item.get("source_count", 1))
        badge = f" <em>({sc} 个来源)</em>" if sc > 1 else ""
        summary_part = f"<br><small>{summary}</small>" if summary else ""
        parts.append(f'<li><a href="{url_attr}">{title}</a>{badge}{summary_part}</li>')
    parts.append("</ul>")
    return "".join(parts)


def build_item_description(issue: dict, site: Path, base_url: str) -> str:
    """
    Produce a rich HTML description for the RSS <description> field.
    Tries merged.json → HTML parse → fallback summary.
    """
    date = issue.get("date", "")
    parts: list[str] = []

    # Summary header
    summary = issue.get("summary", "")
    if summary:
        parts.append(f"<p>{xmlescape(summary)}</p>")

    # --- Strategy 1: merged.json (full structured data) ---
    by_cat = load_items_from_merged_json(site, date)
    if by_cat:
        for slug in CATEGORY_ORDER:
            items = by_cat.get(slug, [])
            if not items:
                continue
            zh, en = CATEGORY_LABELS.get(slug, (slug, slug))
            parts.append(_render_category_block(zh, en, items, base_url))
        # Any category not in the canonical order
        for slug, items in by_cat.items():
            if slug not in CATEGORY_ORDER and items:
                zh, en = CATEGORY_LABELS.get(slug, (slug, slug))
                parts.append(_render_category_block(zh, en, items, base_url))
        return "".join(parts)

    # --- Strategy 2: parse issue HTML ---
    by_cat_html = load_items_from_html(site, date)
    if by_cat_html:
        # Map zh names to canonical order
        zh_to_slug = {v[0]: k for k, v in CATEGORY_LABELS.items()}
        ordered: list[tuple[str, str, list]] = []
        seen: set[str] = set()
        for slug in CATEGORY_ORDER:
            zh = CATEGORY_LABELS[slug][0]
            en = CATEGORY_LABELS[slug][1]
            if zh in by_cat_html:
                ordered.append((zh, en, by_cat_html[zh]))
                seen.add(zh)
        for zh, items in by_cat_html.items():
            if zh not in seen:
                slug = zh_to_slug.get(zh, "")
                en = CATEGORY_LABELS.get(slug, (zh, zh))[1]
                ordered.append((zh, en, items))
        for zh, en, items in ordered:
            parts.append(_render_category_block(zh, en, items, base_url))
        return "".join(parts)

    # --- Strategy 3: fallback to top_items from issues.json ---
    top_items = issue.get("top_items") or []
    if top_items:
        parts.append("<ul>")
        for t in top_items:
            slug = t.get("category", "")
            label = CATEGORY_LABELS.get(slug, (slug, ""))[0]
            title = xmlescape(t.get("title", ""))
            url = xmlescape(t.get("url", "#"))
            sc = int(t.get("source_count", 1))
            badge = f" ({sc} sources)" if sc > 1 else ""
            parts.append(f'<li><a href="{url}">{title}</a> [{xmlescape(label)}]{badge}</li>')
        parts.append("</ul>")

    cat_counts = issue.get("category_counts") or issue.get("categories") or {}
    if cat_counts:
        tags = ", ".join(
            f"{CATEGORY_LABELS.get(s, (s,))[0]} {n}"
            for s, n in cat_counts.items() if n
        )
        parts.append(f"<p><small>{xmlescape(tags)}</small></p>")

    return "".join(parts)


# ---------------------------------------------------------------------------
# Feed renderer
# ---------------------------------------------------------------------------

def load_site_yaml(site: Path) -> dict:
    path = site / "config" / "site.yaml"
    cfg: dict[str, str] = {}
    if not path.exists():
        return cfg
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.split("#", 1)[0].rstrip()
        m = re.match(r'^([A-Za-z_][\w-]*):\s*"?(.*?)"?\s*$', ln)
        if m:
            cfg[m.group(1)] = m.group(2)
    return cfg


def iso_to_rfc822(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        dt = datetime.now(timezone.utc)
    return format_datetime(dt)


def render_feed(site_cfg: dict, issues: list[dict], base_url: str, site: Path) -> str:
    title = site_cfg.get("title", "AI Newsletter")
    subtitle = site_cfg.get("subtitle", "Daily AI digest")
    site_link = base_url.rstrip("/") if base_url else ""
    feed_url = f"{site_link}/feed.xml" if site_link else "feed.xml"
    build_date = format_datetime(datetime.now(timezone.utc))

    items_xml: list[str] = []
    for issue in issues:
        date = issue.get("date", "")
        path = issue.get("path", f"issues/{date}.html")
        link = f"{site_link}/{path}" if site_link else path
        item_title = issue.get("title") or f"AI Newsletter · {date}"
        pub_date = iso_to_rfc822(issue.get("generated_at") or f"{date}T00:00:00Z")
        description = build_item_description(issue, site, site_link)

        items_xml.append(f"""\
    <item>
      <title>{xmlescape(item_title)}</title>
      <link>{xmlescape(link)}</link>
      <guid isPermaLink="true">{xmlescape(link)}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{description}]]></description>
    </item>""")

    items_block = "\n".join(items_xml)
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{xmlescape(title)}</title>
    <link>{xmlescape(site_link or ".")}</link>
    <description>{xmlescape(subtitle)}</description>
    <language>zh-CN</language>
    <lastBuildDate>{build_date}</lastBuildDate>
    <atom:link href="{xmlescape(feed_url)}" rel="self" type="application/rss+xml"/>
{items_block}
  </channel>
</rss>
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="Path to site/ directory")
    ap.add_argument("--base-url", default="", help="Public base URL, e.g. https://example.com")
    args = ap.parse_args()

    site = Path(args.site).resolve()
    if not site.is_dir():
        print(f"error: {site} is not a directory", file=sys.stderr)
        return 2

    manifest_path = site / "data" / "issues.json"
    if not manifest_path.exists():
        print(f"error: {manifest_path} missing — has any issue been generated yet?", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    issues = manifest.get("issues", [])
    issues.sort(key=lambda i: i.get("date", ""), reverse=True)
    issues = issues[:20]

    if not args.base_url:
        print("warning: --base-url not set; feed will use relative URLs", file=sys.stderr)

    site_cfg = load_site_yaml(site)
    xml_out = render_feed(site_cfg, issues, args.base_url, site)
    feed_path = site / "feed.xml"
    feed_path.write_text(xml_out, encoding="utf-8")

    print(f"✓ wrote feed.xml with {len(issues)} item(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
