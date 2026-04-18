#!/usr/bin/env python3
"""
Rebuild site/index.html from site/data/issues.json.

Usage:
    python build_index.py --site ./site

This is the homepage-only build: per-day issue HTML files are never touched.
The homepage reads the lightweight issues.json manifest, sorts by date desc,
and renders the index template. Cheap and idempotent.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"

CATEGORY_LABELS = {
    "major-release": "重大发布",
    "industry-business": "行业动态及商业价值",
    "research-frontier": "研究前沿",
    "tools-release": "工具发布",
    "policy-regulation": "政策监管",
}


def load_site_yaml(site: Path) -> dict:
    """Tiny YAML parser for site.yaml — only handles `key: value` lines with optional quoted strings.
    Good enough for this config; avoids a PyYAML dep.
    """
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


def render_index(site_cfg: dict, issues: list[dict]) -> str:
    tmpl_path = TEMPLATES / "index.html"
    tmpl = tmpl_path.read_text(encoding="utf-8")

    title = site_cfg.get("title", "AI Newsletter")
    subtitle = site_cfg.get("subtitle", "")

    issue_items_html: list[str] = []
    for issue in issues:
        date = issue.get("date", "")
        href = html.escape(issue.get("path", "#"))
        issue_title = html.escape(issue.get("title", f"Issue {date}"))
        summary = html.escape(issue.get("summary", ""))
        item_count = issue.get("item_count", 0)
        cat_counts = issue.get("category_counts", {}) or {}
        top_items = issue.get("top_items", []) or []

        tags_html = "".join(
            f'<span class="category-tag" data-slug="{html.escape(slug)}">'
            f'{html.escape(CATEGORY_LABELS.get(slug, slug))} · {n}</span>'
            for slug, n in cat_counts.items() if n
        )
        tops_html = "".join(
            f'<li><a href="{html.escape(t.get("url", "#"))}">{html.escape(t.get("title", ""))}</a>'
            f' <span class="category-tag" data-slug="{html.escape(t.get("category", ""))}">'
            f'{html.escape(CATEGORY_LABELS.get(t.get("category", ""), t.get("category", "")))}</span>'
            + (f' <span class="source-badge">{int(t.get("source_count", 1))} sources</span>' if int(t.get("source_count", 1)) > 1 else "")
            + "</li>"
            for t in top_items
        )

        issue_items_html.append(
            f"""
            <li>
              <time datetime="{html.escape(date)}">{html.escape(date)} · {item_count} items</time>
              <h3><a href="{href}">{issue_title}</a></h3>
              <p class="teaser">{summary}</p>
              <div class="category-tags">{tags_html}</div>
              {f'<ul class="top-item-list">{tops_html}</ul>' if tops_html else ''}
            </li>
            """
        )

    body = (
        tmpl.replace("{{ title }}", html.escape(title))
        .replace("{{ subtitle }}", html.escape(subtitle))
        .replace("{{ issue_count }}", str(len(issues)))
        .replace("{{ issue_list }}", "\n".join(issue_items_html) or "<li><em>还没有任何期号。生成第一期试试？</em></li>")
        .replace("{{ generated_at }}", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    )
    return body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="Path to site/ directory")
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

    site_cfg = load_site_yaml(site)
    html_out = render_index(site_cfg, issues)
    (site / "index.html").write_text(html_out, encoding="utf-8")

    # Stamp the manifest so we can tell when the homepage was last rebuilt.
    manifest["index_built_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ rebuilt index.html with {len(issues)} issues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
