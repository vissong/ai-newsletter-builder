# Data Sources

Complete catalog of built-in data sources and fetch instructions per type. Each source is a folder under `site/config/sources/<name>/` containing a `source.yaml` config and either a `fetch.py` script or a `prompt.md` extraction prompt. The full schema and extension guide are in `source_extension_guide.md`.

## Folder-based source system

Sources are auto-discovered by scanning `site/config/sources/`. Each subfolder is one source:

```
site/config/sources/
  techcrunch-ai/
    source.yaml      # metadata, type, priority, language, extract options
    prompt.md        # (type: prompt) LLM extraction instructions
  follow-builders/
    source.yaml
    fetch.py         # (type: script) executable that outputs JSON to stdout
```

**Two source types:**

| Type | Mechanism | Output |
|------|-----------|--------|
| `script` | Runs `fetch.py` which prints a JSON array to stdout | Structured JSON items |
| `prompt` | LLM reads the URL/content and follows `prompt.md` instructions to extract items | Structured JSON items |

- **Auto-discovery**: the pipeline scans `site/config/sources/` at collection time. Any folder with a valid `source.yaml` is included (unless `enabled: false`).
- **Naming**: folder name = source name (lowercase-dashed). Keep it stable — it's the key in dedup history and output filenames.
- See `templates/sources/` for ready-to-copy source folder templates.

### Shared RSS script

All RSS-feed sources use a single shared script: `scripts/fetch_rss.py`. Each RSS source folder contains only a `source.yaml` that references this script via `script: fetch_rss.py` and passes the feed URL through `args.url`. The script supports RSS 2.0 and Atom formats, filters by `time_window_hours`, and caps output at `item_limit`. No external dependencies — stdlib only.

For RSS sources where the feed description is too short for a good summary (< 50 words), set `follow_articles: true` in `source.yaml` so the collector does a follow-up LLM pass to fetch full articles.

### Freshness defaults

- **`time_window_hours`**: 48 by default. Items older than this are dropped. Override per source for slow-moving feeds (company blogs → 168h is fine) or speed up for breaking-news sources (techcrunch → 24h).
- **`recent_hours`**: 24 by default. Items published within this window are tagged `recent: true` in the normalized output; rendering prioritizes them to the top of each category. Never set `recent_hours > time_window_hours` — that makes no sense.
- **`timeout_seconds`**: 30 by default, max 120. The collector enforces this as a hard deadline on the fetch attempt (including any redirects and follow_articles passes). Timed-out sources get recorded in `collect.log` with `timed_out: true` and skipped — they do not block the rest of the run and are not retried in the same collection phase. Bump this only for known-slow sources (arxiv index, huge company blog pages); don't raise it as a fix for "sometimes fails."

### Ad / promotion filtering

Aggregator sites (`ai-bot.cn`, `36kr`, some industry trackers) sprinkle paid placements among organic entries. Two layers of defense:

- **`exclude_selectors`** (structural): CSS selectors the reader should strip out BEFORE extracting items. Common targets: `.ad`, `.sponsored`, `.advert`, `[data-ad]`, `.promo-card`, anything labeled "推广位"/"广告位". When using `WebFetch`, pass the exclusion list via the prompt: *"ignore any element matching `.ad, .sponsored, ...`; also skip items whose container has the word 广告/推广/sponsored."*
- **`exclude_keywords`** (post-filter): keyword list. After extraction, drop any item whose title, summary, or surrounding label text contains one of these (case-insensitive, substring match). Defaults worth baking in: `["广告", "推广", "赞助", "sponsored", "promoted", "AD"]`. Add site-specific ones per source.

Record dropped ads in `collect.log` as `<source>: N items fetched, M dropped as ads`. This prevents silent over-filtering — if a source's ad-filter suddenly removes everything, you want to notice.

## Fetch strategy: RSS-first, web scraping as fallback

For every `prompt`-type web source, **prefer RSS if one exists**. RSS is more reliable, cheaper to parse, and returns structured metadata (pubDate, author, categories). Only fall back to web scraping when:

1. The source has no RSS feed (marked in the catalog table), OR
2. The RSS feed is stale — latest item is older than `time_window_hours * 2` (e.g. synced-review's feed was last updated in 2025-08), OR
3. The RSS feed returns empty content for 2+ consecutive runs on weekdays (not weekends — arXiv is empty on weekends by design)

When degrading to web scraping, log the reason in `collect.log`:
```
techcrunch-ai: rss→ok (23 items)
synced-review: rss→stale (last item 2025-08-14), degraded to web scrape
anthropic-news: no rss, web scrape (tier-2)
```

This log makes it easy to spot sources that need attention without silently producing empty results.

## Type: `prompt`

Prompt-based sources use an LLM to fetch a page and extract structured items. The `prompt.md` file in the source folder contains extraction instructions. Use the **tiered fallback chain** — try each tier in order, escalate only when the current tier returns empty content, a 403/429, or unreadable HTML:

| Tier | Tool | When to use |
|---|---|---|
| 1 | `web-access` / `browser-use` skill (CDP real browser) | JS-rendered pages, login walls, anti-bot pages |
| 2 | `mcp__web_reader__webReader` or built-in `WebFetch` | Standard server-rendered pages |
| 3 | **Jina Reader** — `https://r.jina.ai/<url>` | Tiers 1-2 fail or return blocked/empty content |
| 4 | `WebSearch` with `site:<domain> after:{{yesterday}}` | All above fail; headlines-only, low fidelity |

**Jina Reader** (Tier 3) is a plain WebFetch call — no special tool needed. Prepend `https://r.jina.ai/` to any URL:
```
WebFetch → https://r.jina.ai/https://venturebeat.com/category/ai/
```
Jina converts the page to clean Markdown, bypasses most anti-scraping measures, and works with standard HTTP. Use it whenever direct fetching returns empty, blocked, or unparseable content.

If `follow_articles: true` in `source.yaml`, a second pass pulls the full article so the summary is grounded (not just the headline). Cap to top 10 followed articles per source per day to keep cost sane.

## Type: `script`

Script-based sources run `fetch.py` which outputs a JSON array to stdout. Use this for anything that needs custom logic — CLI tools, API clients, git-tracked feeds, custom aggregators.

Before running `fetch.py`, verify any required binaries are available (declared in `source.yaml` under `check.binary`). If missing, halt and show `check.install_hint`.

## Type: `email`

Email sources depend on an external CLI. Before running, verify the CLI is installed (`which <cmd>`). If missing, halt this source with a clear message like: *"Gmail source `my-gmail` requires the `gog` CLI. Install from https://gogcli.sh/ and run `gog auth login`, then re-run the collection."* — do NOT silently skip.

### Built-in: Gmail via `gog`

Collection pattern (pseudocode):

```
gog gmail search --query "<query>" --limit <max_messages> --json
  → list of message IDs
for id in ids:
  gog gmail get <id> --format markdown
  → extract items and output as JSON
```

Email items usually already contain curated links. Treat each email as one or more items — if a newsletter email contains several distinct stories, split them into separate items so merge/dedup across newsletters works.

### Other email providers

Add new providers by dropping in a different `cli`. Each one should expose "search" + "get" subcommands. Pattern:

- Outlook: no first-class CLI yet — recommend `himalaya` or IMAP fallback.
- Apple Mail / IMAP: use `himalaya` with an account configured.

Document the install step in the source's `check.install_hint` so the add-source flow can surface it.

## Type: `git-json` — follow-builders (AI KOC/KOL content)

A special built-in source backed by the GitHub repo `zarazhangrui/follow-builders`. The repo contains three feed files updated daily with content produced by famous AI builders:

| File | Content | Source tag |
|---|---|---|
| `feed-x.json` | X/Twitter posts (tweets, engagement metrics) | `follow-builders-x` |
| `feed-blogs.json` | Blog posts (title, description, full content) | `follow-builders-blogs` |
| `feed-podcasts.json` | Podcast episodes with transcripts | `follow-builders-podcasts` |

**Change detection**: `scripts/fetch_follow_builders.py` stores SHA-256 hashes of each file in `site/data/sources/follow-builders/.hashes.json`. On each run it `git pull`s then compares hashes — only changed files are processed. If nothing changed, the script exits cleanly with 0 items (not an error).

**JSON schemas** (for reference):

`feed-x.json`:
```json
{
  "generatedAt": "ISO-8601",
  "builders": [
    {
      "source": "x", "name": "Swyx", "handle": "swyx", "bio": "...",
      "tweets": [
        { "id": "...", "text": "...", "createdAt": "ISO-8601",
          "url": "...", "likes": 42, "retweets": 7, "replies": 3,
          "isQuote": false, "quotedTweetId": null }
      ]
    }
  ]
}
```

`feed-blogs.json`:
```json
{
  "generatedAt": "ISO-8601", "lookbackHours": 48,
  "blogs": [
    { "source": "blog", "name": "...", "title": "...", "url": "...",
      "publishedAt": "ISO-8601|null", "author": "...",
      "description": "...", "content": "full text" }
  ]
}
```

`feed-podcasts.json`:
```json
{
  "generatedAt": "ISO-8601", "lookbackHours": 48,
  "podcasts": [
    { "source": "podcast", "name": "...", "title": "...", "guid": "...",
      "url": "...", "publishedAt": "ISO-8601", "transcript": "timestamped text" }
  ]
}
```

**Notes:**
- Tweets without `text` are silently skipped; blogs without `title+url` are skipped.
- `publishedAt: null` in blogs is common — falls back to `fetched_at`.
- Transcripts can be long; the script caps summaries at 400 chars; set `follow_articles: false` (not applicable here — content is inline).
- Use `--force` flag to reprocess all files regardless of hash (useful after schema changes).

## Built-in source catalog (seed)

During `scripts/init_site.py`, offer these as a checklist. Not everything has to be enabled — default to the starred ones.

See `templates/sources/` for ready-to-copy source folder templates.

### Git-tracked JSON feed (default)

| name | repo | priority | 推荐类型 | ★ |
|------|------|----------|----------|---|
| follow-builders | github.com/zarazhangrui/follow-builders | 1 | `script` | ★★ |

This source is **enabled by default** — always include it during `init`. It requires `git` in PATH. See the `Type: git-json` section above for full details.

### Web sources (news)

| name | url | rss? | priority | 推荐类型 | ★ |
|------|-----|------|----------|----------|---|
| venturebeat-ai | https://venturebeat.com/category/ai/feed | ✅ | 1 | `script` | ★ |
| techcrunch-ai | https://techcrunch.com/category/artificial-intelligence/feed/ | ✅ | 1 | `script` | ★ |
| theverge-ai | https://www.theverge.com/ai-artificial-intelligence | ❌ | 1 | `prompt` | |
| mit-tech-review-ai | https://www.technologyreview.com/topic/artificial-intelligence/feed/ | ✅ | 1 | `script` | |
| 36kr-ai | https://36kr.com/search/articles/AI | ❌ | 1 | `prompt` | ★ |
| ai-bot-daily-news | https://ai-bot.cn/daily-ai-news/ | ❌ | 1 | `prompt` | ★ |
| ai-bot-tools | https://ai-bot.cn/ai-tools/ | ❌ | 2 | `prompt` | ★ |
| artificial-intelligence-news | https://artificialintelligence-news.com/feed/ | ✅ | 2 | `script` | |
| ai-hub-today | https://ai.hubtoday.app/ | ❌ | 2 | `prompt` | ★ |
| synced-review | https://syncedreview.com/feed/ | ✅ | 2 | `script` | |

**Note on `venturebeat-ai`**: RSS feed at `/category/ai/feed` returns 80–120 word paragraph excerpts with author and category metadata — good enough to summarize without `follow_articles`. pubDate is accurate. Set `item_limit: 10` and `time_window_hours: 24`.

**Note on `techcrunch-ai`**: Use the RSS feed URL (`/feed/`) — it returns 200 directly without anti-bot friction that often forces Tier 3 (Jina). The feed contains 23 items updated hourly, with `dc:creator`, `category` tags, and `pubDate`. Description fields are short excerpts (~25-30 words); always set `follow_articles: true` to fetch full text for summaries.

**Note on `mit-tech-review-ai`**: RSS feed at `/topic/artificial-intelligence/feed/` returns 50–70 word excerpts with author and category. **Sponsored content appears in the feed** — add `exclude_keywords: ["Sponsored"]` to filter it. pubDate accurate.

**Note on `artificial-intelligence-news`**: RSS at `/feed/` returns only 35–40 word excerpts; not enough for good summaries. Set `follow_articles: true, follow_limit: 8`.

**Note on `synced-review`**: RSS at `/feed/` works (60-word excerpts, good structure) but the feed is **very slow to update** — latest item observed was from 2025-08, months stale. Consider disabling or setting `time_window_hours: 720` (30 days) and `priority: 3` to avoid empty runs.

**Note on `36kr-ai`**: Chinese startup/tech portal. The "AI 频道" is at `/motif/327685989388`; the AI search endpoint (`/search/articles/AI`) returns most recent matches and is the easier target. Content is Chinese; entries are sorted by recency, which pairs well with `time_window_hours: 48`.

**Note on `ai-hub-today`**: prefer the date-pinned URL `https://ai.hubtoday.app/YYYY-MM/YYYY-MM-DD` (e.g. `https://ai.hubtoday.app/2026-04/2026-04-18`) over the root. The root shows whatever the site's front page is; the date URL is the actual daily digest, already pre-curated 10–20 items. When configuring, use a template string: `url: "https://ai.hubtoday.app/{{year-month}}/{{date}}"` — the collector substitutes at fetch time.

**Note on `ai-bot.cn`**: aggregator site with both organic entries and promoted/ad placements. Always configure `exclude_selectors` + `exclude_keywords` (see Ad / promotion filtering above). `ai-bot-daily-news` maps naturally to news items; `ai-bot-tools` almost always categorizes as `tools-release` — these entries are product/tool listings, not time-sensitive news. When merging, treat `tools-release` items from this source as lower-priority (let dedup collapse them against actual launches from primary sources like company blogs).

### Web sources (company blogs)

| name | url | rss? | priority | 推荐类型 | ★ |
|------|-----|------|----------|----------|---|
| openai-blog | https://openai.com/blog/rss.xml | ✅ | 1 | `script` | ★ |
| anthropic-news | https://www.anthropic.com/news | ❌ | 1 | `prompt` | ★ |
| google-ai-blog | https://blog.google/technology/ai/rss/ | ✅ | 1 | `script` | |
| deepmind-blog | https://deepmind.google/discover/blog/feed/ | ✅ | 1 | `script` | |
| microsoft-ai | https://blogs.microsoft.com/ai/ | ❌ | 2 | `prompt` | |
| meta-ai-blog | https://ai.meta.com/blog/ | ❌ | 2 | `prompt` | |

**Note on `openai-blog`**: RSS at `/blog/rss.xml` returns ~130-character short excerpts with category tags (Product/Research). Must use `follow_articles: true` to get full content. 940 items total; use `item_limit: 10` and `time_window_hours: 168` (company blogs publish infrequently).

**Note on `google-ai-blog`**: RSS at `/technology/ai/rss/` returns 60–95 character headline-only excerpts with author and media assets. Must use `follow_articles: true`. 20 items, good pubDate accuracy. Set `time_window_hours: 168`.

**Note on `deepmind-blog`**: RSS at `/discover/blog/feed/` returns 95–120 character excerpts, no author or category fields. Must use `follow_articles: true`. 100 items. Set `time_window_hours: 168`.

**Note on `anthropic-news` / `microsoft-ai` / `meta-ai-blog`**: No RSS feed found — use web scraping (Tier 1/2) or Jina (Tier 3). These publish rarely; set `time_window_hours: 168`.

### Research sources

| name | url | rss? | priority | 推荐类型 |
|------|-----|------|----------|----------|
| arxiv-cs-ai | https://arxiv.org/rss/cs.AI | ✅ | 2 | `script` |
| arxiv-cs-lg | https://arxiv.org/rss/cs.LG | ✅ | 2 | `script` |
| arxiv-cs-cl | https://arxiv.org/rss/cs.CL | ✅ | 2 | `script` |
| huggingface-blog | https://huggingface.co/blog/feed.xml | ✅ | 2 | `script` |
| papers-with-code | https://paperswithcode.com/ | ❌ | 3 | `prompt` |

arXiv has three separate recent-listings relevant to AI: `cs.AI` (general AI), `cs.LG` (machine learning), `cs.CL` (computation & language — LLMs/NLP). The three overlap significantly in content but each surfaces items the others miss. Enable all three when you want broad research coverage; the `research-frontier` cap of 10 will keep it manageable. If budget-conscious, `cs.AI` alone is usually enough.

**Note on arXiv RSS**: Use the RSS URLs (`https://arxiv.org/rss/cs.AI` etc.) directly — they return well-structured XML with title, abstract, authors, and arXiv ID. The feed is only populated on weekdays when new submissions are announced (Mon–Fri, ~midnight ET); on weekends and holidays the feed returns a valid but empty document — this is normal, not a failure. Set `time_window_hours: 48` so Friday submissions survive the weekend gap.

**Note on `huggingface-blog`**: Use the RSS feed at `https://huggingface.co/blog/feed.xml` (200, 766+ items). **Critical: the feed contains NO description field — only title, link, pubDate, and guid.** Always set `follow_articles: true` to fetch full post content. Posts are deep technical writeups (model cards, research, integrations) — almost always `research-frontier` or `tools-release`. Set `item_limit: 10` and `time_window_hours: 72`.

**Note on `papers-with-code`**: No RSS feed found — the site now redirects to `huggingface.co/papers/trending`. Skip this source and rely on arXiv RSS + HuggingFace blog instead; between the two you get both the raw papers and the curated commentary.

### Chinese social / content platforms (login- or JS-heavy, opt-in)

| name | url | priority | 推荐类型 | requires capability |
|------|-----|----------|----------|---------------------|
| weixin-sogou | https://weixin.sogou.com/weixin?type=2&query=AI | 2 | `prompt` | — |
| weibo-ai-hot | https://s.weibo.com/weibo?q=AI&sort=hot&timescope=custom:24h | 3 | `prompt` | `real_browser` |
| douyin-ai-hot | https://www.douyin.com/search/AI?sort_type=1 | 3 | `prompt` | `real_browser` |

These sources are **opt-in** because they require heavier tooling than a simple `WebFetch`:

- **`weixin-sogou`** — WeChat public-account search via Sogou. Returns article titles, snippets, account names, and publication dates. Works with plain `WebFetch` if the HTML is parseable, though Sogou occasionally serves a captcha page under heavy polling (expect ~70-80% success rate). Target accounts listed via `preferred_accounts`: 机器之心, 新智元, 量子位, 智东西, 雷锋网, 36氪. Use `exclude_keywords: ["推广", "广告"]` to filter ad placements that occasionally mix into search results.

- **`weibo-ai-hot`** — Weibo hot-topic search. Unauthenticated requests hit a login gate; full results need a logged-in session. Declare `requires_capability: real_browser`. Output value is moderate — good for trending-topic awareness, weak for factual depth. Cap item_limit to 5–8.

- **`douyin-ai-hot`** — Douyin (TikTok China) search. Fully JS-rendered, effectively useless without a real browser. Declare `requires_capability: real_browser`. Video content; the text you can extract is just title + description. Signal is low. Enable only when covering consumer/社会 AI topics; skip for B2B / research newsletters.

#### Capabilities and the tools that satisfy them

Sources declare what they need via `requires_capability` (a capability token). The collector then picks ANY locally-available tool that advertises that capability. This keeps source definitions portable across environments — don't hard-code a specific skill name.

| Capability | What it means | Tools that satisfy it (any one is enough) |
|------------|---------------|-------------------------------------------|
| `real_browser` | CDP-capable real browser: executes JS, holds cookies, can follow login flows. | `browser-use` skill; `web-access` skill; Playwright/Puppeteer via MCP; any CDP-bridge tool. |
| `authenticated` | Must carry user-specific auth (cookies, tokens) to return meaningful content. | All `real_browser` tools that the user has logged in once; or a cookie-injection MCP. |
| `search_api` | Structured search API with ranking + snippets. | `tavily-search` skill; `web-search` skill; built-in `WebSearch`. |

When the collector starts, detect which of these are available in the current session:

1. List the environment's available skills (from the system prompt / skill registry).
2. Build a map `capability → [tool_name, ...]` using the table above.
3. When iterating over enabled sources, for each source with `requires_capability`, look up the map and pick the highest-priority tool in the list order (left to right).
4. If the capability has **zero satisfying tools**, mark that source as failed in `collect.log` with reason `capability 'real_browser' not available in this environment — install browser-use or web-access` and skip. Don't silently downgrade to `WebFetch` — it will return empty pages and pollute dedup.

`weixin-sogou` has no `requires_capability` because plain `WebFetch` usually suffices. If Sogou starts rejecting all fetches at scale, a user can add `requires_capability: real_browser` and the collector will re-route.

### Search sources (Tavily CLI)

All 6 search sources use `tvly` CLI (Tavily Search) instead of the built-in `WebSearch` API, which requires a Claude official subscription. Each source is a `script` type with a standalone `fetch.py` that calls `tvly search` and outputs JSON to stdout.

**Dependency:** `tvly` CLI must be installed and authenticated. Install: `curl -fsSL https://cli.tavily.com/install.sh | bash && tvly login`

| name | query | type | time_window | ★ |
|------|-------|------|-------------|---|
| search-major-release | `"AI model release" OR "AI launches" OR "AI announces"` | `script` | 48h | ★ |
| search-funding | `"AI startup" funding OR "Series" OR raises` | `script` | 96h | ★ |
| search-research | `"AI paper" OR "machine learning breakthrough" OR "AI research"` | `script` | 96h | ★ |
| search-policy | `AI regulation OR policy OR bill OR law` | `script` | 48h | ★ |
| search-36kr-ai | `AI 大模型 人工智能` (domain: 36kr.com) | `script` | 48h | ★ |
| search-weixin-ai | `AI 人工智能 大模型` (domain: mp.weixin.qq.com) | `script` | 48h | ★ |

`search-funding` and `search-research` use 96h windows because funding/research news publishes primarily on weekdays; a 48h window misses Friday articles on Sunday collection runs. The Chinese sources (`search-36kr-ai`, `search-weixin-ai`) use `--include-domains` to restrict results to their target platforms, with `exclude_keywords` filtering out ads and financial promotions.

Each `fetch.py` uses `--time-range day` (or `week`) and `--topic news` for recency, then applies `time_window_hours` filtering locally on `published_date`. Add one search per topic you care about — don't combine multiple intents into one query or the model can't tell what to keep.

### Email example (opt-in)

**Privacy note.** The built-in catalog does NOT preset any Gmail source — it's off by default and never auto-enabled. Users who want it must explicitly add their own entry per the add-source flow. No email address ever lands in source config: authentication lives in the external CLI (`gog`'s own config), not in the project. The `query` field uses labels or sender-name filters, so the project config stays publishable. If you publish the site to GitHub Pages, also add `site/data/raw/**/gmail-*.md` to `.gitignore` — the raw bodies can contain tracking tokens and unsubscribe links unique to the user.

| name | type | 推荐类型 |
|------|------|----------|
| gmail-ai-newsletter | email | `prompt` |

### CLI sources (opt-in)

| name | command example | 推荐类型 |
|------|----------------|----------|
| arxiv-rss | `rsstail -u https://arxiv.org/rss/cs.AI -n 15 -p` | `script` |

Built-in parsers (just hints to the model — each one tells you how to split stdout into items):

- `rsstail` — blank lines between items, fields prefixed with `Title:`, `Link:`, `Pub.date:`, `Description:`.
- `jsonl` — one item per line, JSON object with `title`/`url`/`summary`/`published_at`.
- `raw` — split stdout on `extract.separator` (default `\n---\n`).
- `tencent-news-cli` — numbered list output from `tencent-news-cli`. Items start with `<N>.` on a new line. Fields per item: `标题:`, `摘要:`, `来源:` (optional), `发布时间:` (optional), `链接:`. Block ends at next `<N+1>.` or EOF.

If no parser matches, tell the user and ask them to pick one or provide a regex.

### Tencent News CLI (built-in)

`tencent-news-cli` is a purpose-built CLI for querying Tencent News. It supports hot-trend rankings, keyword search, and daily briefings, with structured text output using the `tencent-news-cli` parser.

**Installation**: `https://news.qq.com/exchange?scene=appkey` — requires an API key set via `tencent-news-cli apikey-set <key>`.

| name | command | priority | 推荐类型 | ★ |
|------|---------|----------|----------|---|
| tencent-news-ai-search | `tencent-news-cli search "AI 大模型" --limit 20` | 1 | `script` | ★ |
| tencent-news-ai-agent | `tencent-news-cli search "AI 智能体 Agent" --limit 15` | 1 | `script` | ★ |
| tencent-news-ai-funding | `tencent-news-cli search "人工智能 融资" --limit 15` | 2 | `script` | ★ |
| tencent-news-ai-policy | `tencent-news-cli search "AI 政策 法规" --limit 15` *(time_window_hours: 72)* | 2 | `script` | ★ |
| tencent-news-hot | `tencent-news-cli hot --limit 20` *(通用热榜，噪音高，需 include_keywords 后处理)* | 3 | `script` | |

All four starred sources use the `search` sub-command with distinct topic coverage:

| Source | 覆盖的 newsletter 类别 | 典型命中 |
|--------|----------------------|----------|
| `ai-search` ("AI 大模型") | major-release / research-frontier | 大模型发布、基准测试突破 |
| `ai-agent` ("AI 智能体 Agent") | tools-release / major-release | Agent 框架发布、agentic 产品 |
| `ai-funding` ("人工智能 融资") | industry-business | 融资轮次、并购、估值 |
| `ai-policy` ("AI 政策 法规") | policy-regulation | 国家/地方 AI 政策、新规、发改委 |

The four queries have intentional topic overlap at the margins (e.g. a large fundraise for an AI company may appear in both `ai-search` and `ai-funding`). This is fine — Phase 3 dedup collapses cross-source duplicates by title similarity and absorbs them into one item with `source_count: 2`.

**Why skip "AI 芯片 算力"?** Chip/compute news on Tencent News tends to skew older than 48h and frequently hits financial product promotions (ETF launches, stock analysis). The `ai-search` and `ai-agent` queries pick up the most important compute stories (NVIDIA announcements, domestic chip news) through their broader coverage anyway. Add a dedicated chip source if you specifically need it.

**Why "AI 政策 法规" with `time_window_hours: 72`?** Policy documents and regulatory announcements don't publish every day; a tighter 48h window would miss many of them. 72h keeps a reasonable window without pulling in old content.

The `exclude_keywords` list filters out stock-market and financial-product entries that frequently appear in AI-tagged news but have no newsletter value: `["ETF", "涨停", "跌停", "涨超", "跌超", "股票", "基金", "大盘", "行情"]`. Extend it per taste.

The `--caller` flag is recommended (identifies the client to Tencent News analytics); use your site name.

## Language hint

Set `language: zh` or `language: en` per source in `source.yaml`. Used only as a hint when summarizing — the site's output language is configured separately in `site.yaml` (`output_language: zh` or `en`). It's fine to have zh sources in an en-output site and vice versa; the model translates during the summarization step.
