# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Claude Code skill that builds static AI newsletter sites. It collects content from multiple sources (web, email, search, CLI), deduplicates and categorizes items, renders daily issue pages + an auto-indexed homepage, and publishes to GitHub Pages or Cloudflare Pages.

Distributed as an installable skill: `npx skills install vissong/ai-newsletter-builder`

## Common Commands

```bash
# Scaffold a new site (one-time)
python scripts/init_site.py --dir site --design minimal --title "AI Daily" --lang zh

# Rebuild homepage from issues.json manifest (cheap, idempotent)
python scripts/build_index.py --site site

# Generate RSS feed
python scripts/build_feed.py --site site --base-url https://example.com
```

No npm/pip dependencies — all Python scripts use stdlib only (Python 3.7+).

### Optional: browser-use (Playwright)

Some sources (`venturebeat-ai`, and future `theverge-ai` / `36kr-ai`) require a headless browser because the target site blocks automated HTTP requests. These sources declare `requires_capability: real_browser` in their `source.yaml`.

Install once:
```bash
uv venv ~/.browser-use-env --python 3.13
uv pip install --python ~/.browser-use-env/bin/python3 browser-use playwright
~/.browser-use-env/bin/python3 -m playwright install chromium
```

The collector resolves `real_browser` at runtime: if `~/.browser-use-env/bin/python3` exists, script sources that need Playwright will use it; otherwise the source is skipped with a clear error in `collect.log`.

### Optional: Tavily Search CLI (tvly)

Search-type sources (`search-major-release`, `search-funding`, etc.) use the Tavily CLI instead of the built-in `WebSearch` API, which requires a Claude official subscription. Install once:
```bash
curl -fsSL https://cli.tavily.com/install.sh | bash && tvly login
```

Sources that depend on `tvly` declare `requires_cli: tvly` in their `source.yaml`. The collector checks this before running the fetch script.

## Architecture

**Entry point:** `SKILL.md` — the full skill specification (triggers, phases, rules). This is what Claude Code loads when the skill activates.

**Pipeline (7 phases):**

```
Phase 0: Init       → scaffold site/, pick design, seed sources (scripts/init_site.py)
Phase 1: Sources    → manage site/config/sources/<name>/ folders
Phase 2: Collect    → concurrent fetch, write site/data/raw/<date>/<source>.json
Phase 3: Merge      → dedupe + cross-source fusion → merged.json
Phase 4: Categorize → assign to 5 fixed category slugs
Phase 5: Render     → fill templates/issue.html → site/issues/<date>.html
Phase 6: Index+RSS  → scripts/build_index.py + scripts/build_feed.py
Phase 7: Publish    → GitHub Pages or Cloudflare Pages (user confirmation required)
```

Each phase can be invoked independently — don't force the full pipeline if the user only wants one step.

**Key directories:**

- `scripts/` — Python build scripts (init, index, feed)
- `templates/` — HTML templates for homepage (`index.html`), daily issue (`issue.html`), and source templates (`sources/`)
- `designs/` — Built-in design systems: legacy single-file (`*.md` with tokens) and DESIGN.md directories (9-section prose spec)
- `references/` — Detailed guides for data sources, source extension, page generation, layouts, design translation, publishing
- `site/` — Generated output (created on first run, `data/raw/` is gitignored)

**Config (all in `site/config/`):**

- `site.yaml` — title, subtitle, language, timezone, design, layout, base_url
- `sources/<name>/` — folder-based data sources (type: script or prompt), auto-discovered
- `design.md` or `design/<name>/DESIGN.md` — active design system

## Data Source Types

Two extension approaches, each as a folder under `site/config/sources/<name>/`:

1. **Script** (`type: script`): Stable data format → fixed Python/shell script outputs JSON to stdout. Example: `follow-builders/fetch.py`
2. **Prompt** (`type: prompt`): Unstable data format → `prompt.md` describes fetch + extraction for LLM execution. Fetch methods: web, search, email, CLI

Tiered web fetch fallback for prompt sources: real browser → plain fetch → Jina Reader → WebSearch.
RSS-first strategy: always check for RSS feed before scraping a web source.

See `references/source_extension_guide.md` for the full schema and extension guide.

## Content Categories (fixed slugs, never rename)

| Slug | Name |
|---|---|
| `major-release` | 重大发布 |
| `industry-business` | 行业动态及商业价值 |
| `research-frontier` | 研究前沿 (capped at 10 items/day) |
| `tools-release` | 工具发布 |
| `policy-regulation` | 政策监管 |

## Dedup Rules

Applied globally before categorization:
1. Same URL (tracking params stripped)
2. Near-identical title (Levenshtein ≤ 3, same first entity)
3. Same entity + same event + 48h window

Items fused across sources get `source_count > 1` and rank higher within their category.

## Design Systems

Two formats coexist:
- **Legacy** (`designs/*.md`): token list → `init_site.py` generates templated CSS automatically
- **DESIGN.md** (`designs/<name>/DESIGN.md`): 9-section prose spec → Claude reads and writes custom CSS

Special case: `designs/ciyuan-jie/` has a pre-built `style.css` (never regenerate) and `standalone.html` (client-side JS renderer).

## Page Layouts

Four canonical skeletons set via `site/config/site.yaml → layout`:
- `editorial-longscroll` (default) — full-bleed hero, section labels, border-only items
- `card-grid` — bordered cards, H2 category headings
- `terminal-log` — prompt-line style, `[CATEGORY]` headings
- `digest-compact` — 600px email-width, one-sentence summaries
