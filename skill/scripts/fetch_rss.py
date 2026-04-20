#!/usr/bin/env python3
"""
Generic RSS/Atom feed fetcher. Outputs a JSON array of items to stdout.

Usage:
    python fetch_rss.py --url https://example.com/feed.xml
    python fetch_rss.py --url https://arxiv.org/rss/cs.AI --time-window-hours 48 --item-limit 30

Supports RSS 2.0 (<item>) and Atom (<entry>), including arXiv namespaced feeds.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

USER_AGENT = "ai-newsletter-builder/1.0 (+https://github.com/vissong/ai-newsletter-builder)"

ATOM_NS = "http://www.w3.org/2005/Atom"
DC_NS = "http://purl.org/dc/elements/1.1/"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RSS1_NS = "http://purl.org/rss/1.0/"

STRIP_HTML_RE = re.compile(r"<[^>]+>")
COLLAPSE_WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = STRIP_HTML_RE.sub(" ", text)
    return COLLAPSE_WS_RE.sub(" ", text).strip()


def parse_datetime(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    date_str = date_str.strip()

    # RFC-822 (RSS 2.0 pubDate)
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        pass

    # ISO-8601 / Atom
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def text_of(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return (el.text or "").strip()


def fetch_xml(url: str) -> ET.Element:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return ET.fromstring(data)


def parse_rss2(root: ET.Element) -> list[dict]:
    items = []
    for item in root.iter("item"):
        title = strip_html(text_of(item.find("title")))
        link = text_of(item.find("link"))
        if not link:
            guid_el = item.find("guid")
            if guid_el is not None and (guid_el.get("isPermaLink", "true") == "true"):
                link = text_of(guid_el)

        pub_date = text_of(item.find("pubDate"))
        desc = text_of(item.find("description"))
        content_encoded = text_of(item.find(f"{{{CONTENT_NS}}}encoded"))
        dc_date = text_of(item.find(f"{{{DC_NS}}}date"))

        summary = strip_html(content_encoded or desc)
        published_at = parse_datetime(pub_date or dc_date)

        if title and link:
            items.append({
                "title": title,
                "url": link,
                "published_at": published_at.isoformat() if published_at else None,
                "summary": summary,
            })
    return items


def parse_atom(root: ET.Element) -> list[dict]:
    ns = {"a": ATOM_NS}
    entries = root.findall("a:entry", ns) or root.findall(f"{{{ATOM_NS}}}entry")
    if not entries:
        entries = root.findall("entry")

    items = []
    for entry in entries:
        title_el = entry.find(f"{{{ATOM_NS}}}title") or entry.find("title")
        title = strip_html(text_of(title_el))

        link = ""
        for link_el in entry.findall(f"{{{ATOM_NS}}}link") + entry.findall("link"):
            rel = link_el.get("rel", "alternate")
            if rel == "alternate":
                link = link_el.get("href", "")
                break
        if not link:
            all_links = entry.findall(f"{{{ATOM_NS}}}link") + entry.findall("link")
            if all_links:
                link = all_links[0].get("href", "")

        pub_el = (
            entry.find(f"{{{ATOM_NS}}}published")
            or entry.find("published")
            or entry.find(f"{{{ATOM_NS}}}updated")
            or entry.find("updated")
        )
        published_at = parse_datetime(text_of(pub_el))

        summary_el = (
            entry.find(f"{{{ATOM_NS}}}summary")
            or entry.find("summary")
            or entry.find(f"{{{ATOM_NS}}}content")
            or entry.find("content")
        )
        summary = strip_html(text_of(summary_el))

        if title and link:
            items.append({
                "title": title,
                "url": link,
                "published_at": published_at.isoformat() if published_at else None,
                "summary": summary,
            })
    return items


def parse_rdf(root: ET.Element) -> list[dict]:
    """RSS 1.0 / RDF format (used by some arXiv feeds)."""
    items = []
    for item in root.findall(f"{{{RSS1_NS}}}item"):
        title = strip_html(text_of(item.find(f"{{{RSS1_NS}}}title")))
        link = text_of(item.find(f"{{{RSS1_NS}}}link"))
        desc = text_of(item.find(f"{{{RSS1_NS}}}description"))
        dc_date = text_of(item.find(f"{{{DC_NS}}}date"))
        published_at = parse_datetime(dc_date)
        summary = strip_html(desc)

        if title and link:
            items.append({
                "title": title,
                "url": link,
                "published_at": published_at.isoformat() if published_at else None,
                "summary": summary,
            })
    return items


def detect_and_parse(root: ET.Element) -> list[dict]:
    tag = root.tag.lower()

    # Atom
    if "feed" in tag and ATOM_NS in tag:
        return parse_atom(root)
    if root.tag == "feed":
        return parse_atom(root)

    # RDF / RSS 1.0
    if "RDF" in root.tag or RDF_NS in root.tag:
        return parse_rdf(root)

    # RSS 2.0
    if root.tag == "rss" or root.find("channel") is not None:
        return parse_rss2(root)

    # Fallback: try Atom then RSS 2.0
    items = parse_atom(root)
    if items:
        return items
    return parse_rss2(root)


def filter_items(
    items: list[dict],
    time_window_hours: float,
    item_limit: int,
) -> list[dict]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=time_window_hours)

    filtered = []
    for item in items:
        if item["published_at"]:
            pub = parse_datetime(item["published_at"])
            if pub and pub < cutoff:
                continue
        filtered.append(item)

    filtered.sort(
        key=lambda x: parse_datetime(x["published_at"] or "") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return filtered[:item_limit]


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch RSS/Atom feed and output JSON items")
    ap.add_argument("--url", required=True, help="RSS/Atom feed URL")
    ap.add_argument("--time-window-hours", type=float, default=48, help="Drop items older than this (default: 48)")
    ap.add_argument("--item-limit", type=int, default=30, help="Max items to return (default: 30)")
    ap.add_argument("--language", default=None, help="Language hint (en/zh), added to each item if set")
    args = ap.parse_args()

    print(f"Fetching: {args.url}", file=sys.stderr)
    try:
        root = fetch_xml(args.url)
    except Exception as e:
        print(f"error: failed to fetch {args.url}: {e}", file=sys.stderr)
        return 1

    items = detect_and_parse(root)
    print(f"Parsed {len(items)} raw items", file=sys.stderr)

    items = filter_items(items, args.time_window_hours, args.item_limit)
    print(f"After filtering: {len(items)} items (window={args.time_window_hours}h, limit={args.item_limit})", file=sys.stderr)

    if args.language:
        for item in items:
            item["language"] = args.language

    # Clean up None published_at
    for item in items:
        if item["published_at"] is None:
            del item["published_at"]

    json.dump(items, sys.stdout, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
