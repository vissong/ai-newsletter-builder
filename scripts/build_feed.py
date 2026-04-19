#!/usr/bin/env python3
"""
Generate site/feed.xml (RSS 2.0) from site/data/issues.json.

Usage:
    python build_feed.py --site ./site [--base-url https://example.com]

Each issue in issues.json becomes one <item>.  Items link to their daily
HTML page.  The feed is always rebuilt from scratch — idempotent like
build_index.py.

The --base-url flag is required if any issue path or the feed's <link>
needs to be an absolute URL.  If omitted, relative URLs are used in
<link> and a warning is printed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape as xmlescape

SKILL_DIR = Path(__file__).resolve().parent.parent

CATEGORY_LABELS = {
    "major-release": "重大发布",
    "industry-business": "行业动态及商业价值",
    "research-frontier": "研究前沿",
    "tools-release": "工具发布",
    "policy-regulation": "政策监管",
}


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
    """Convert ISO-8601 string to RFC-822 date used in RSS."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        dt = datetime.now(timezone.utc)
    return format_datetime(dt)


def build_item_description(issue: dict) -> str:
    """Produce a short HTML description for the RSS <description> field."""
    parts: list[str] = []
    summary = issue.get("summary", "")
    if summary:
        parts.append(f"<p>{xmlescape(summary)}</p>")

    top_items = issue.get("top_items") or []
    if top_items:
        parts.append("<ul>")
        for t in top_items:
            label = CATEGORY_LABELS.get(t.get("category", ""), t.get("category", ""))
            title = xmlescape(t.get("title", ""))
            url = xmlescape(t.get("url", "#"))
            sc = int(t.get("source_count", 1))
            badge = f" ({sc} sources)" if sc > 1 else ""
            parts.append(f'<li><a href="{url}">{title}</a> [{xmlescape(label)}]{badge}</li>')
        parts.append("</ul>")

    cat_counts = issue.get("category_counts") or {}
    if cat_counts:
        tags = ", ".join(
            f"{CATEGORY_LABELS.get(s, s)} {n}"
            for s, n in cat_counts.items() if n
        )
        parts.append(f"<p><small>{xmlescape(tags)}</small></p>")

    return "".join(parts)


def render_feed(site_cfg: dict, issues: list[dict], base_url: str) -> str:
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
        description = build_item_description(issue)
        guid = link  # stable per-issue URL as GUID

        items_xml.append(f"""\
    <item>
      <title>{xmlescape(item_title)}</title>
      <link>{xmlescape(link)}</link>
      <guid isPermaLink="true">{xmlescape(guid)}</guid>
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

    if not args.base_url:
        print("warning: --base-url not set; feed will use relative URLs (fine for local preview, broken for feed readers)", file=sys.stderr)

    site_cfg = load_site_yaml(site)
    xml_out = render_feed(site_cfg, issues, args.base_url)
    feed_path = site / "feed.xml"
    feed_path.write_text(xml_out, encoding="utf-8")

    print(f"✓ wrote feed.xml with {len(issues)} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
