#!/usr/bin/env python3
"""
Ensure site/ has the SPA shell templates in place.

Usage:
    python build_index.py --site ./site

The homepage and issue page are client-side rendered SPAs that read JSON data
at runtime. This script simply ensures the template HTML files are copied into
the correct locations. It does NOT inject any content — that's done by the
browser at view time.

Templates are copied only if missing, so re-running is safe and idempotent.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"


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


def copy_template(src: Path, dest: Path, title: str, subtitle: str) -> bool:
    if dest.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = src.read_text(encoding="utf-8")
    content = content.replace("{{ title }}", title).replace("{{ subtitle }}", subtitle)
    dest.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="Path to site/ directory")
    args = ap.parse_args()

    site = Path(args.site).resolve()
    if not site.is_dir():
        print(f"error: {site} is not a directory", file=sys.stderr)
        return 2

    cfg = load_site_yaml(site)
    title = cfg.get("title", "AI Newsletter")
    subtitle = cfg.get("subtitle", "")

    copied = []
    if copy_template(TEMPLATES / "index.html", site / "index.html", title, subtitle):
        copied.append("index.html")
    if copy_template(TEMPLATES / "issue.html", site / "issues" / "index.html", title, subtitle):
        copied.append("issues/index.html")

    if copied:
        print(f"✓ copied templates: {', '.join(copied)}")
    else:
        print("✓ templates already in place")
    return 0


if __name__ == "__main__":
    sys.exit(main())
