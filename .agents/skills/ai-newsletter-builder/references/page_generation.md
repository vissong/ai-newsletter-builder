# Page Generation

Details of merge → categorize → render. The high-level flow is in SKILL.md; this file has the concrete rules and examples.

## Inputs and outputs

**Input:** all `site/data/raw/<date>/<source>.md` files for the target date.

**Outputs:**
- `site/data/raw/<date>/merged.json` — canonical, deduplicated, categorized item list for that date.
- `site/issues/<date>.html` — the fully rendered daily page.
- An entry in `site/data/issues.json` — the manifest teaser used by the homepage.

## Step 1: Load and normalize

Parse every `data/raw/<date>/<source>.md` into a flat list. Each parsed item must have:

```
title, summary, url, published_at, fetched_at, language, source
```

Drop items where:
- URL is missing (can't cite)
- Summary is empty (model produced nothing)
- Published_at is older than **48 hours** (default freshness window; extend only if the user explicitly asks for a wider window such as a weekly digest).

Mark items published within the last **24 hours** with `recent: true` (the collectors should already do this; if the flag is missing, infer from `published_at`). `recent: true` items get priority in sort and display.

Don't drop items just because they're in a different language than the output — translation happens during render.

## Step 2: Dedup + merge

## Step 2: Dedup + merge

**Dedup runs globally, across ALL sources and categories at once, before anything gets a category assigned.** Classification happens in Step 3 — so when the same story appears in a news outlet (heading toward `industry-business`) AND a company blog (heading toward `major-release`), both copies must be fused into one item here, in Step 2, before either category exists. Per-category dedup after the fact misses these cross-category duplicates and is the single most common reason the same story shows up twice in an issue.

Walk the flat list and fuse duplicates into groups. Order matters — apply the rules in this order so the cheap checks catch common cases first.

### Rule A — URL match

Normalize URLs by stripping:
- Tracking params (`utm_*`, `ref`, `fbclid`, `gclid`, `mc_cid`, `mc_eid`, `source=`)
- Trailing slash, hash fragment
- `www.` prefix
- Lower-cased host

Two items with the same normalized URL → same story.

### Rule B — Title similarity

For remaining items, normalize titles (lowercase, strip punctuation, drop leading "BREAKING:" / "Update:" / publication prefixes). Compute Levenshtein distance on the normalized form.

- Distance ≤ 3 and same first entity (first proper noun or quoted phrase) → same story.
- Distance > 3 → keep separate (even if topics overlap).

This is cheap and catches most dup headlines across outlets without over-merging.

### Rule C — Event fingerprint (optional)

If the user asks for aggressive dedup or you see 3+ items obviously covering the same announcement, fall back to an "event fingerprint": normalized entity + action verb + object. E.g. `openai|release|gpt-5.1`. If two items share the fingerprint AND their `published_at` is within 48 hours, merge.

Use this sparingly — it's the rule most likely to collapse distinct-but-related stories. When unsure, don't merge.

### Merging two items

```python
merged = {
  "title": best_title(a, b),              # longer, less clickbait-y one
  "summary": best_summary(a, b),          # prefer the one citing the primary source
  "url": authoritative_url(a, b),         # see below
  "alt_urls": [the_other_url],
  "sources": sorted(set(a.sources + b.sources)),
  "source_count": len(sources),
  "published_at": min(a.published_at, b.published_at),
  "language": a.language,                 # keep earliest; render will translate
  "fetched_at": max(a.fetched_at, b.fetched_at),
}
```

**Authoritative URL ranking** (lower index wins):
1. First-party (company blog, official docs, paper PDF)
2. Reputable outlet (Tier-1 sources from `data_sources.md`)
3. Aggregator (HN, Reddit, AI Hub Today)
4. Anything else

When in doubt, prefer the URL whose domain matches a name in `sources` (the blog that announced it).

### What `source_count` means downstream

`source_count` is the strongest signal for "this is today's big story." Items with `source_count >= 3` should be hoisted to the top of their category in the rendered page and noted in the homepage teaser. Don't hide the count — the page should say something like "Reported by 4 sources" so readers can gauge weight.

## Step 3: Categorize

Assign each merged item to exactly one of five categories. Slugs (not names) are what templates key off of.

| slug                | 名称               | keep in / examples                                                          |
| ------------------- | ------------------ | --------------------------------------------------------------------------- |
| `major-release`     | 重大发布           | 新模型上线、旗舰产品首发、里程碑级功能、GA / public launch                   |
| `industry-business` | 行业动态及商业价值 | 融资、并购、收入、partnerships、大客户签约、市场份额、B 端落地案例          |
| `research-frontier` | 研究前沿           | 论文、新架构、新方法、benchmark 突破、可复现代码 + 结果                    |
| `tools-release`     | 工具发布           | 开源项目、SDK、CLI、plugin、API、agent 框架、低代码工具、dev tooling       |
| `policy-regulation` | 政策监管           | 法律、法规、政策草案、监管行动、合规要求、AI 安全事件、政府 AI 战略         |

### Decision rule when ambiguous

An item has one **primary hook**. Ask: what's the headline really about?
- "OpenAI releases GPT-5.1 and raises $10B" → `major-release` (the release is the hook; the raise is secondary).
- "OpenAI raises $10B to build GPT-5.1" → `industry-business` (the funding is the hook).
- "Anthropic paper shows new interp technique; ships tool" → `research-frontier` (paper is primary; tool is a demo).

If two hooks are genuinely equal weight, default to `industry-business` — it's the catch-all. Do NOT invent a sixth category.

### Sort within each category

After categorization, within each category:
1. `recent: true` items first (last 24h), then 24–48h items
2. `source_count` descending within each recency band (multi-source stories on top)
3. `published_at` descending
4. Alphabetical on title (stable fallback)

### Cap on `research-frontier` — keep top 10 by importance

Research sources (arxiv, papers-with-code, HuggingFace research posts, MIT Tech Review analysis, etc.) routinely generate 20–40 items per day — enough to bury the other four categories. After the sort above, trim `research-frontier` to the top 10 by importance. Other categories are left uncapped.

Importance ranking (applied in order, each tie-breaker kicks in only when the previous one didn't resolve):

1. `source_count` desc — if a paper shows up in multiple places (including outside research sources), it's escaping pure research.
2. Cross-referenced by an item in another category (e.g. a product launch cites the paper) — the paper is load-bearing for the rest of the issue.
3. Flagship lab or top-tier institution on a frontier topic — DeepMind / OpenAI / Anthropic / FAIR / Microsoft Research / top universities on scaling, reasoning, alignment, robotics, multimodal, agentic systems.
4. Benchmark result clearly beating a well-known prior SOTA (explicit numbers in the summary).
5. `recent: true` beats 24–48h.
6. Alphabetical on title (final stable tie-breaker).

For the bottom (trimmed) items, **don't delete** — keep them in `merged.json` with `"trimmed": true` and a one-line `trim_reason` (e.g. `"trim_reason": "single-source preprint, no SOTA claim"`). This way the user can see what was dropped and you can explain decisions. Only items without `trimmed` render to HTML.

Override: if the user asks for "all research" or a weekly research digest, disable or raise the cap for that run.

## Step 4: Render the daily page

`templates/issue.html` is a Jinja2-style template with these top-level variables:

```
date: "2026-04-18"
title: "<site title> · 2026-04-18"
lead_summary: str    # 2–3 sentence editorial lead written by the model
categories: [
  {
    slug: "major-release",
    name: "重大发布",
    items: [ merged_item_dict, ... ],
  },
  ...  # empty categories are omitted from the page
]
stats: {
  total_items: 23,
  total_sources: 18,
  categories_with_content: 4,
}
generated_at: ISO timestamp
prev_date, next_date: optional navigation (can be null if ends)
```

Write the `lead_summary` yourself as the skill — 2–3 sentences surfacing the day's top 2 stories by `source_count`, plus any policy/regulation if it exists (people always want to hear about that).

When rendering item descriptions, rewrite the raw summary into the **output language** set in `site/config/site.yaml`. Keep it factual, cite key numbers verbatim, and drop marketing adjectives. The goal is "skimmable brief," not "PR rewrite."

Each item block in the template should include: title (linked), 1–2 sentence summary, category tag, source count badge (only if > 1, formatted as "N sources"), primary URL, and collapsible alt_urls if > 0.

## Step 5: Update `issues.json`

After writing the daily HTML, update the manifest:

```python
issues = json.load(open("site/data/issues.json")) if exists else {"issues": []}
# Remove existing entry for this date if re-running
issues["issues"] = [i for i in issues["issues"] if i["date"] != date]
issues["issues"].append({
  "date": date,
  "title": f"{site_title} · {date}",
  "path": f"issues/{date}.html",
  "item_count": total_items,
  "top_items": top_3_to_5_items_as_teaser,
  "summary": lead_summary,
  "generated_at": now_iso(),
  "category_counts": {slug: n for slug, n in counts_by_category.items()},
})
issues["issues"].sort(key=lambda i: i["date"], reverse=True)
json.dump(issues, ...)
```

`top_items` are teasers only — 3–5 items, each with `{title, category, source_count, url}`. The homepage reads just this; it never reaches into per-day HTML.

## Step 6: Rebuild the homepage

Run `scripts/build_index.py`. It's a pure data → HTML transform; no network calls. Cheap and idempotent.

## Examples

### Merge example

Raw input (two sources):
```
Source: techcrunch-ai
## OpenAI launches GPT-5.1 with multi-modal reasoning
url: https://techcrunch.com/2026/04/18/openai-gpt-51/
...

Source: openai-blog
## Introducing GPT-5.1
url: https://openai.com/blog/gpt-5-1
...
```

Rule B applies (titles are topically identical; first entity `OpenAI` matches). Merged:

```json
{
  "title": "OpenAI launches GPT-5.1 with multi-modal reasoning",
  "url": "https://openai.com/blog/gpt-5-1",
  "alt_urls": ["https://techcrunch.com/2026/04/18/openai-gpt-51/"],
  "sources": ["openai-blog", "techcrunch-ai"],
  "source_count": 2,
  "category": "major-release"
}
```

### Don't-merge example

```
## Meta open-sources Llama 4 weights
## Meta announces Llama 4 API partnership with AWS
```

Same company, but different news hooks (weights release vs AWS partnership). Keep separate. Llama-4 weights → `tools-release` (or `major-release` if it's the flagship). Llama-4 AWS deal → `industry-business`.
