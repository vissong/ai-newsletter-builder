# ai-newsletter-builder

> A Claude Code skill that turns multiple data sources into a daily AI newsletter site — with dedup, categorization, custom design systems, and one-command publish.

## Install

```bash
npx skills install vissong/ai-newsletter-builder
```

Then in any Claude Code session, the skill activates automatically when you ask to build a newsletter, set up data sources, or pick a design style.

---

## What it does

Tell Claude:

> "帮我创建一个 AI 日报站点"  
> "生成今天的 AI newsletter"  
> "给我的 AI 日报加一个腾讯新闻数据源"  
> "换成 figma 风格重新生成"

The skill handles the full pipeline:

```
数据源收集（并发）
  → 去重 & 跨源归并（source_count 追踪）
  → 分类（5 类固定 slug）
  → 渲染（日报页 + 首页索引）
  → 发布到 GitHub Pages / Cloudflare Pages
```

All output lands in `site/` under your project directory.

---

## Quick start

```
你：帮我在当前目录创建一个 AI 日报站点
```

Claude will walk you through:
1. **Output dir** — default `./site`
2. **Design system** — pick from built-ins or supply your own `DESIGN.md`
3. **Data sources** — enable from the catalog or add custom ones
4. **First issue** — collect → merge → render → open in browser

---

## Data sources

Four source types are supported. The skill manages a `site/config/sources.yaml` file with all configuration.

### Web (pages & blogs)

```yaml
- name: techcrunch-ai
  type: web
  enabled: true
  language: en
  priority: 1
  url: https://techcrunch.com/category/artificial-intelligence/
  extract:
    item_limit: 15
    time_window_hours: 48       # drop items older than 48h
    recent_hours: 24             # mark last-24h items as recent: true
    timeout_seconds: 30
    exclude_selectors: [".ad", ".sponsored"]
    exclude_keywords: ["广告", "推广"]
```

Built-in catalog includes: VentureBeat AI, TechCrunch AI, The Verge AI, MIT Tech Review, 36Kr, ai-bot.cn daily news & tools catalog, OpenAI/Anthropic/Google/DeepMind blogs, arXiv cs.AI/LG/CL, HuggingFace Blog, Papers with Code, and more.

### Search queries

```yaml
- name: search-major-release
  type: search
  query: '"AI model release" OR "launches" after:{{yesterday}}'
  extract:
    result_limit: 20
    follow_articles: true
```

### CLI tools

```yaml
# Tencent News CLI (tencent-news-cli)
- name: tencent-news-ai-search
  type: cli
  command: 'tencent-news-cli search "AI 大模型" --limit 20 --caller ai-newsletter-builder'
  parser: tencent-news-cli
  check:
    binary: tencent-news-cli
    install_hint: "https://news.qq.com/exchange?scene=appkey"
  extract:
    time_window_hours: 48
    exclude_keywords: ["ETF", "涨停", "跌停", "股票", "基金"]
```

Any CLI that writes structured text to stdout works. Built-in parsers: `rsstail`, `jsonl`, `tencent-news-cli`, `raw`.

### Email (Gmail via `gog`)

```yaml
- name: gmail-ai-newsletter
  type: email
  provider: gmail
  cli: gog                                    # gog.sh — Google Workspace CLI
  query: "newer_than:1d label:ai-newsletter"  # Gmail search syntax, no email address needed
  extract:
    max_messages: 30
    include_body: true
    strip_quoted: true
```

Requires `gog` CLI: [`https://gogcli.sh`](https://gogcli.sh). Run `gog auth login` once. No email address is stored in the config — authentication lives in gog's local keychain.

### Social platforms (opt-in, needs real browser)

```yaml
- name: weixin-sogou            # WeChat articles via Sogou search
  type: web
  enabled: true                 # works with plain WebFetch
  url: https://weixin.sogou.com/weixin?type=2&query=AI

- name: weibo-ai-hot            # Weibo hot search — needs browser-use / web-access skill
  type: web
  enabled: false
  requires_capability: real_browser
  url: https://s.weibo.com/weibo?q=AI&sort=hot&timescope=custom:24h
```

---

## Design systems

Two formats are supported.

### Legacy single-file (quick)

Four built-ins under `designs/*.md` — token-heavy, Python-parsed, no LLM step needed:

| Name | Vibe |
|---|---|
| `minimal` | Clean white, generous whitespace, sans |
| `editorial` | Magazine, strong typographic contrast, serif |
| `terminal` | Dark, mono, cyber/technical |
| `warm` | Cream, soft accents, cozy reading feel |

Switch with: *"换成 editorial 风格"*

### DESIGN.md — Google Stitch / getdesign.md format (rich)

Directory-based, 9-section prose spec. Claude reads it and writes a fully custom `style.css`. Works with any brand identity — all three built-ins are included:

```
designs/
├── figma/
│   └── DESIGN.md   ← figmaSans variable font (weight 320–700), pill/circle buttons, neon hero gradient
├── cohere/
│   └── DESIGN.md   ← 22px rounded cards, CohereText serif + Unica77 sans, deep purple hero band
└── nio/
    └── DESIGN.md   ← BlueSkyStandard ultra-light (weight 100–300), zero border-radius, cinematic full-screen sections
```

**NIO highlights**: Angular geometry (0px radius everywhere), brand Teal `#00b3be` as surgical accent only, 160px section padding, transparent-to-frosted header on scroll. Produces a cinematic minimalist aesthetic suited to high-stakes editorial content.

Fetch more from [getdesign.md](https://getdesign.md) and drop them in `designs/<name>/DESIGN.md`.

---

## Page layouts

Four canonical skeletons. Set in `site/config/site.yaml`:

```yaml
layout: editorial-longscroll   # change this line
```

| Layout | Structure | Best with |
|---|---|---|
| `editorial-longscroll` | Full-bleed hero · Highlights block · Section labels · Border-only item flow | Any design — default |
| `card-grid` | Quiet header · H2 category headings · Bordered cards | minimal, cohere, dashboard-y |
| `terminal-log` | No hero · Prompt line · `[CATEGORY]` headings · Log entries | terminal design |
| `digest-compact` | 600px email-width · `▍` section marks · One-sentence summaries | warm, personal briefing |

---

## Content pipeline

### Categorization (5 fixed buckets)

| Slug | 名称 | What goes in |
|---|---|---|
| `major-release` | 重大发布 | Flagship model launches, milestone product releases |
| `industry-business` | 行业动态及商业价值 | Funding, M&A, revenue, enterprise deals |
| `research-frontier` | 研究前沿 | Papers, benchmarks, new architectures |
| `tools-release` | 工具发布 | Open source, SDKs, agent frameworks, CLIs |
| `policy-regulation` | 政策监管 | Laws, regulations, compliance, safety incidents |

### Dedup rules

- Same URL (tracking params stripped) → merge
- Near-identical title (Levenshtein ≤ 3, same first entity) → merge  
- Same entity + same event + 48h window → merge

Cross-source dedup runs *before* categorization — the same story appearing in an English news outlet and a Chinese blog gets fused into one item with `source_count: 2`. Multi-source stories surface to the top of their category.

### Research cap

`research-frontier` is trimmed to **top 10** items by importance (source_count → flagship lab → SOTA numbers → recency). Trimmed items stay in `merged.json` with `trimmed: true + trim_reason` for inspection.

---

## Publishing

```
你：发布到 GitHub Pages
```

Or Cloudflare Pages. See `references/publish.md` for the exact setup steps, including a ready-to-paste GitHub Actions workflow.

---

## Files in this repo

```
SKILL.md              ← skill entrypoint (name, description, full workflow)
designs/              ← built-in design systems
  minimal.md          ← legacy token format
  editorial.md
  terminal.md
  warm.md
  figma/DESIGN.md     ← Google Stitch format
  cohere/DESIGN.md
references/
  data_sources.md     ← source catalog + fetch instructions per type
  add_source_flow.md  ← guided interview for adding a source
  page_generation.md  ← merge/dedup/categorize/render rules
  newsletter_layouts.md ← 4 canonical page skeletons
  design_md_guide.md  ← how to translate a DESIGN.md into CSS + HTML
  design_systems.md   ← legacy design.md schema
  publish.md          ← GitHub Pages / Cloudflare Pages deployment
scripts/
  init_site.py        ← scaffold site/ and generate style.css from design
  build_index.py      ← rebuild homepage from issues.json manifest
templates/
  index.html          ← homepage template (used by build_index.py)
  issue.html          ← daily issue template skeleton
```
