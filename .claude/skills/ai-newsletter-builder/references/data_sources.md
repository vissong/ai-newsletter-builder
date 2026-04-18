# Data Sources

Complete catalog of built-in data sources and fetch instructions per type. Source definitions live in `site/config/sources.yaml`. The schema and add-source flow are in `add_source_flow.md`.

## sources.yaml schema

```yaml
# Top-level site config can be in site.yaml; sources.yaml is just the list.
sources:
  - name: techcrunch-ai           # required, lowercase-dashed, used as filename key
    type: web                      # email | web | search | cli
    enabled: true                  # default true
    language: en                   # hint for summarization, not strict
    priority: 1                    # 1 (primary) .. 3 (niche). Used to pick highlights.
    # type-specific fields below...
    url: https://techcrunch.com/category/artificial-intelligence/
    extract:
      list_selector: article        # optional, CSS selector hint for the reader
      item_limit: 15
      time_window_hours: 48         # keep items within last N hours; default 48
      recent_hours: 24              # mark items in last N hours as `recent: true`; default 24
      timeout_seconds: 30           # per-source fetch timeout; default 30, max 120
      exclude_selectors: [".ad", ".sponsored", ".advert"]   # CSS selectors stripped before parsing
      exclude_keywords: ["广告", "推广", "sponsored", "promoted", "赞助"]  # drop items whose title/summary contains any
```

### Freshness defaults

- **`time_window_hours`**: 48 by default. Items older than this are dropped. Override per source for slow-moving feeds (company blogs → 168h is fine) or speed up for breaking-news sources (techcrunch → 24h).
- **`recent_hours`**: 24 by default. Items published within this window are tagged `recent: true` in the normalized output; rendering prioritizes them to the top of each category. Never set `recent_hours > time_window_hours` — that makes no sense.
- **`timeout_seconds`**: 30 by default, max 120. The collector enforces this as a hard deadline on the fetch attempt (including any redirects and follow_articles passes). Timed-out sources get recorded in `collect.log` with `timed_out: true` and skipped — they do not block the rest of the run and are not retried in the same collection phase. Bump this only for known-slow sources (arxiv index, huge company blog pages); don't raise it as a fix for "sometimes fails."

### Ad / promotion filtering

Aggregator sites (`ai-bot.cn`, `36kr`, some industry trackers) sprinkle paid placements among organic entries. Two layers of defense:

- **`exclude_selectors`** (structural): CSS selectors the reader should strip out BEFORE extracting items. Common targets: `.ad`, `.sponsored`, `.advert`, `[data-ad]`, `.promo-card`, anything labeled "推广位"/"广告位". When using `WebFetch`, pass the exclusion list via the prompt: *"ignore any element matching `.ad, .sponsored, ...`; also skip items whose container has the word 广告/推广/sponsored."*
- **`exclude_keywords`** (post-filter): keyword list. After extraction, drop any item whose title, summary, or surrounding label text contains one of these (case-insensitive, substring match). Defaults worth baking in: `["广告", "推广", "赞助", "sponsored", "promoted", "AD"]`. Add site-specific ones per source.

Record dropped ads in `collect.log` as `<source>: N items fetched, M dropped as ads`. This prevents silent over-filtering — if a source's ad-filter suddenly removes everything, you want to notice.

Keep `name` stable — it's the filename key under `data/raw/<date>/<name>.md` and the key inside each item's `sources` array. Renaming breaks the dedup history.

## Type: `web`

Fetch a page (index or article) and extract a list of items. Prefer the best available reader in this priority order:

1. `web-access` skill (if listed in available skills) — invoke via the Skill tool. Best at login walls and JS-rendered pages.
2. `browser-use` skill — use when the page needs real browser interaction.
3. `mcp__web_reader__webReader` — lightweight, good enough for most article indexes.
4. Built-in `WebFetch` — fallback.

Per-source fields:

```yaml
type: web
url: https://example.com/ai
extract:
  item_limit: 15                  # stop after N items
  time_window_hours: 48           # drop items older than this
  list_selector: null             # optional CSS/xpath hint; many readers will infer
  follow_articles: true           # if true, also fetch each item's URL for summary
```

If `follow_articles: true`, a second pass pulls the full article so the summary is grounded (not just the headline). Cap to top 10 followed articles per source per day to keep cost sane.

## Type: `search`

Run a web search query. Prefer in this order:

1. `tavily-search` skill — LLM-optimized results, best snippets.
2. `web-search` skill — ranked results with freshness filter.
3. Built-in `WebSearch`.

```yaml
type: search
query: "AI model release after:{{yesterday}}"
extract:
  provider_hint: tavily           # optional, force a provider
  result_limit: 20
  follow_articles: true           # fetch each result page for summary
  blocked_domains: [reddit.com]
```

`{{yesterday}}` and `{{today}}` are resolved at collection time (ISO date, local tz). Add one search per topic you care about — don't combine multiple intents into one query or the model can't tell what to keep.

## Type: `email`

Email sources depend on an external CLI. Before running, verify the CLI is installed (`which <cmd>`). If missing, halt this source with a clear message like: *"Gmail source `my-gmail` requires the `gog` CLI. Install from https://gogcli.sh/ and run `gog auth login`, then re-run the collection."* — do NOT silently skip.

### Built-in: Gmail via `gog`

```yaml
type: email
provider: gmail
cli: gog                           # must resolve in PATH
auth_hint: "run `gog auth login` once"
query: 'newer_than:2d label:ai-newsletter'   # Gmail search syntax
extract:
  max_messages: 30
  include_body: true
  strip_quoted: true               # drop > quoted replies
```

Collection pattern (pseudocode):

```
gog gmail search --query "<query>" --limit <max_messages> --json
  → list of message IDs
for id in ids:
  gog gmail get <id> --format markdown
  → write item block to data/raw/<date>/<name>.md
```

Email items usually already contain curated links. Treat each email as one or more items — if a newsletter email contains several distinct stories, split them into separate items so merge/dedup across newsletters works.

### Other email providers

Add new providers by dropping in a different `cli`. Each one should expose "search" + "get" subcommands. Pattern:

- Outlook: no first-class CLI yet — recommend `himalaya` or IMAP fallback.
- Apple Mail / IMAP: use `himalaya` with an account configured.

Document the install step in the source's `auth_hint` so the add-source flow can surface it.

## Type: `cli`

Arbitrary command whose stdout is the content. Use this for anything that isn't email/web/search — RSS tools, paper-scraping scripts, custom aggregators, feed readers.

```yaml
type: cli
command: "rsstail -u https://arxiv.org/rss/cs.AI -n 20 -p"
parser: rsstail                    # informational; see parsers below
check:
  binary: rsstail
  install_hint: "brew install rsstail"
extract:
  item_limit: 20
```

Before running `command`, verify `check.binary` is available. If not, halt and show `install_hint`.

Built-in parsers (just hints to the model — each one tells you how to split stdout into items):

- `rsstail` — blank lines between items, fields prefixed with `Title:`, `Link:`, `Pub.date:`, `Description:`.
- `jsonl` — one item per line, JSON object with `title`/`url`/`summary`/`published_at`.
- `raw` — split stdout on `extract.separator` (default `\n---\n`).
- `tencent-news-cli` — numbered list output from `tencent-news-cli`. Items start with `<N>.` on a new line. Fields per item: `标题:`, `摘要:`, `来源:` (optional), `发布时间:` (optional), `链接:`. Block ends at next `<N+1>.` or EOF.

If no parser matches, tell the user and ask them to pick one or provide a regex.

## Built-in source catalog (seed)

Imported from the repo's existing `daily-ai-news` skill. During `scripts/init_site.py`, offer these as a checklist. Not everything has to be enabled — default to the starred ones.

### Web sources (news)

| name                         | url                                                     | priority | ★ |
| ---------------------------- | ------------------------------------------------------- | -------- | - |
| venturebeat-ai               | https://venturebeat.com/category/ai/                     | 1        | ★ |
| techcrunch-ai                | https://techcrunch.com/category/artificial-intelligence/ | 1        | ★ |
| theverge-ai                  | https://www.theverge.com/ai-artificial-intelligence     | 1        |   |
| mit-tech-review-ai           | https://www.technologyreview.com/topic/artificial-intelligence/ | 1 |   |
| 36kr-ai                      | https://36kr.com/search/articles/AI                      | 1        | ★ |
| ai-bot-daily-news            | https://ai-bot.cn/daily-ai-news/                         | 1        | ★ |
| ai-bot-tools                 | https://ai-bot.cn/ai-tools/                              | 2        | ★ |
| artificial-intelligence-news | https://artificialintelligence-news.com/                | 2        |   |
| ai-hub-today                 | https://ai.hubtoday.app/                                | 2        | ★ |
| synced-review                | https://syncedreview.com/                               | 2        |   |

**Note on `36kr-ai`**: Chinese startup/tech portal. The "AI 频道" is at `/motif/327685989388`; the AI search endpoint (`/search/articles/AI`) returns most recent matches and is the easier target. Content is Chinese; entries are sorted by recency, which pairs well with `time_window_hours: 48`.

**Note on `ai-hub-today`**: prefer the date-pinned URL `https://ai.hubtoday.app/YYYY-MM/YYYY-MM-DD` (e.g. `https://ai.hubtoday.app/2026-04/2026-04-18`) over the root. The root shows whatever the site's front page is; the date URL is the actual daily digest, already pre-curated 10–20 items. When configuring, use a template string: `url: "https://ai.hubtoday.app/{{year-month}}/{{date}}"` — the collector substitutes at fetch time.

**Note on `ai-bot.cn`**: aggregator site with both organic entries and promoted/ad placements. Always configure `exclude_selectors` + `exclude_keywords` (see §Ad / promotion filtering above). Recommended YAML for this pair:

```yaml
- name: ai-bot-daily-news
  type: web
  enabled: true
  language: zh
  priority: 1
  url: https://ai-bot.cn/daily-ai-news/
  extract:
    item_limit: 20
    time_window_hours: 48
    exclude_selectors: [".ad", ".sponsored", ".advert", "[class*=promo]", "[class*=推广]"]
    exclude_keywords: ["广告", "推广", "赞助", "sponsored", "AD"]

- name: ai-bot-tools
  type: web
  enabled: true
  language: zh
  priority: 2
  url: https://ai-bot.cn/ai-tools/
  extract:
    item_limit: 15
    time_window_hours: 168   # tools directory; entries are mostly static, widen window
    exclude_selectors: [".ad", ".sponsored", ".advert", "[class*=promo]", "[class*=推广]"]
    exclude_keywords: ["广告", "推广", "赞助", "sponsored", "AD"]
```

`ai-bot-daily-news` maps naturally to news items; `ai-bot-tools` almost always categorizes as `tools-release` — these entries are product/tool listings, not time-sensitive news. When merging, treat `tools-release` items from this source as lower-priority (let dedup collapse them against actual launches from primary sources like company blogs).

### Web sources (company blogs)

| name            | url                                      | priority | ★ |
| --------------- | ---------------------------------------- | -------- | - |
| openai-blog     | https://openai.com/blog                  | 1        | ★ |
| anthropic-news  | https://www.anthropic.com/news           | 1        | ★ |
| google-ai-blog  | https://blog.google/technology/ai/       | 1        |   |
| deepmind-blog   | https://deepmind.google/discover/blog/   | 1        |   |
| microsoft-ai    | https://blogs.microsoft.com/ai/          | 2        |   |
| meta-ai-blog    | https://ai.meta.com/blog/                | 2        |   |

### Research sources

| name             | url                                     | priority |
| ---------------- | --------------------------------------- | -------- |
| arxiv-cs-ai      | https://arxiv.org/list/cs.AI/recent     | 2        |
| arxiv-cs-lg      | https://arxiv.org/list/cs.LG/recent     | 2        |
| arxiv-cs-cl      | https://arxiv.org/list/cs.CL/recent     | 2        |
| huggingface-blog | https://huggingface.co/blog             | 2        |
| papers-with-code | https://paperswithcode.com/             | 3        |

arXiv has three separate recent-listings relevant to AI: `cs.AI` (general AI), `cs.LG` (machine learning), `cs.CL` (computation & language — LLMs/NLP). The three overlap significantly in content but each surfaces items the others miss. Enable all three when you want broad research coverage; the `research-frontier` cap of 10 will keep it manageable. If budget-conscious, `cs.AI` alone is usually enough.

### Chinese social / content platforms (login- or JS-heavy, opt-in)

| name              | url                                                               | priority | requires capability |
| ----------------- | ----------------------------------------------------------------- | -------- | ------------------- |
| weixin-sogou      | https://weixin.sogou.com/weixin?type=2&query=AI                   | 2        | —                   |
| weibo-ai-hot      | https://s.weibo.com/weibo?q=AI&sort=hot&timescope=custom:24h      | 3        | `real_browser`      |
| douyin-ai-hot     | https://www.douyin.com/search/AI?sort_type=1                      | 3        | `real_browser`      |

These sources are **opt-in** because they require heavier tooling than a simple `WebFetch`:

- **`weixin-sogou`** — WeChat public-account search via Sogou. Returns article titles, snippets, account names, and publication dates. Works with plain `WebFetch` if the HTML is parseable, though Sogou occasionally serves a captcha page under heavy polling (expect ~70-80% success rate). Target accounts listed via `preferred_accounts`: 机器之心, 新智元, 量子位, 智东西, 雷锋网, 36氪. Use `exclude_keywords: ["推广", "广告"]` to filter ad placements that occasionally mix into search results.

- **`weibo-ai-hot`** — Weibo hot-topic search. Unauthenticated requests hit a login gate; full results need a logged-in session. Declare `requires_capability: real_browser`. Output value is moderate — good for trending-topic awareness, weak for factual depth. Cap item_limit to 5–8.

- **`douyin-ai-hot`** — Douyin (TikTok China) search. Fully JS-rendered, effectively useless without a real browser. Declare `requires_capability: real_browser`. Video content; the text you can extract is just title + description. Signal is low. Enable only when covering consumer/社会 AI topics; skip for B2B / research newsletters.

#### Capabilities and the tools that satisfy them

Sources declare what they need via `requires_capability` (a capability token). The collector then picks ANY locally-available tool that advertises that capability. This keeps source definitions portable across environments — don't hard-code a specific skill name.

| Capability       | What it means                                                                 | Tools that satisfy it (any one is enough)                                            |
| ---------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `real_browser`   | CDP-capable real browser: executes JS, holds cookies, can follow login flows. | `browser-use` skill; `web-access` skill; Playwright/Puppeteer via MCP; any CDP-bridge tool. |
| `authenticated`  | Must carry user-specific auth (cookies, tokens) to return meaningful content. | All `real_browser` tools that the user has logged in once; or a cookie-injection MCP.|
| `search_api`     | Structured search API with ranking + snippets.                                | `tavily-search` skill; `web-search` skill; built-in `WebSearch`.                     |

When the collector starts, detect which of these are available in the current session:

1. List the environment's available skills (from the system prompt / skill registry).
2. Build a map `capability → [tool_name, ...]` using the table above.
3. When iterating over enabled sources, for each source with `requires_capability`, look up the map and pick the highest-priority tool in the list order (left to right).
4. If the capability has **zero satisfying tools**, mark that source as failed in `collect.log` with reason `capability 'real_browser' not available in this environment — install browser-use or web-access` and skip. Don't silently downgrade to `WebFetch` — it will return empty pages and pollute dedup.

`weixin-sogou` has no `requires_capability` because plain `WebFetch` usually suffices. If Sogou starts rejecting all fetches at scale, a user can add `requires_capability: real_browser` and the collector will re-route.

Recommended YAML for the three:

```yaml
- name: weixin-sogou
  type: web
  enabled: true              # WebFetch works well enough in practice
  language: zh
  priority: 2
  url: https://weixin.sogou.com/weixin?type=2&query=AI
  extract:
    item_limit: 15
    time_window_hours: 48
    exclude_keywords: ["广告", "推广", "赞助"]
    preferred_accounts:      # informational only; renderer can highlight these
      - 机器之心
      - 新智元
      - 量子位
      - 智东西
      - 雷锋网
      - 36氪

- name: weibo-ai-hot
  type: web
  enabled: false             # opt-in; signal:noise is moderate at best
  language: zh
  priority: 3
  url: https://s.weibo.com/weibo?q=AI&sort=hot&timescope=custom:24h
  requires_capability: real_browser
  extract:
    item_limit: 8
    time_window_hours: 24
    exclude_keywords: ["广告", "推广", "转发抽奖", "福利"]

- name: douyin-ai-hot
  type: web
  enabled: false             # opt-in; low signal for most newsletters
  language: zh
  priority: 3
  url: https://www.douyin.com/search/AI?sort_type=1
  requires_capability: real_browser
  extract:
    item_limit: 6
    time_window_hours: 24
    exclude_keywords: ["广告", "推广", "赞助"]
```

### Search sources (generated)

Default queries (users can add/remove freely):

| name                  | query                                                                 |
| --------------------- | --------------------------------------------------------------------- |
| search-major-release  | `"AI model release" OR "launches" OR "announces" after:{{yesterday}}` |
| search-funding        | `"AI startup" (funding OR Series OR raises) after:{{yesterday}}`      |
| search-research       | `"AI paper" OR "machine learning breakthrough" after:{{yesterday}}`   |
| search-policy         | `AI (regulation OR policy OR bill OR law) after:{{yesterday}}`        |
| search-36kr-ai        | `site:36kr.com AI after:{{yesterday}}` (中文，辅助 36kr-ai 页面抓取)   |
| search-weixin-ai      | `site:mp.weixin.qq.com AI after:{{yesterday}}` (备用，直达公众号文章) |

### Email example (opt-in)

**Privacy note.** The built-in catalog does NOT preset any Gmail source — it's off by default and never auto-enabled. Users who want it must explicitly add their own entry per the add-source flow. No email address ever lands in `sources.yaml`: authentication lives in the external CLI (`gog`'s own config), not in the project. The `query` field uses labels or sender-name filters, so the project config stays publishable. If you publish the site to GitHub Pages, also add `site/data/raw/**/gmail-*.md` to `.gitignore` — the raw bodies can contain tracking tokens and unsubscribe links unique to the user.

```yaml
- name: gmail-ai-newsletter
  type: email
  provider: gmail
  cli: gog
  query: "newer_than:1d label:ai-newsletter"
  # — label-based queries are safest; they don't embed the user's address.
  # — if you want to filter by sender, prefer placeholder form
  #   (e.g. `from:<sender-display-name>`) over pasting a real address.
  extract:
    max_messages: 30
    include_body: true
    strip_quoted: true
    timeout_seconds: 60
    exclude_keywords: ["广告", "sponsored", "unsubscribe to stop"]
```

### CLI example (opt-in)

```yaml
- name: arxiv-rss
  type: cli
  command: "rsstail -u https://arxiv.org/rss/cs.AI -n 15 -p"
  parser: rsstail
  check:
    binary: rsstail
    install_hint: "brew install rsstail"
```

### Tencent News CLI (built-in ★)

`tencent-news-cli` is a purpose-built CLI for querying Tencent News. It supports hot-trend rankings, keyword search, and daily briefings, with structured text output using the `tencent-news-cli` parser.

**Installation**: `https://news.qq.com/exchange?scene=appkey` — requires an API key set via `tencent-news-cli apikey-set <key>`.

| name                    | command                                                                          | priority | ★ |
| ----------------------- | -------------------------------------------------------------------------------- | -------- | - |
| tencent-news-ai-search  | `tencent-news-cli search "AI 大模型" --limit 20`                                  | 1        | ★ |
| tencent-news-ai-agent   | `tencent-news-cli search "AI 智能体 Agent" --limit 15`                            | 1        | ★ |
| tencent-news-ai-funding | `tencent-news-cli search "人工智能 融资" --limit 15`                               | 2        | ★ |
| tencent-news-ai-policy  | `tencent-news-cli search "AI 政策 法规" --limit 15` *(time_window_hours: 72)*     | 2        | ★ |
| tencent-news-hot        | `tencent-news-cli hot --limit 20` *(通用热榜，噪音高，需 include_keywords 后处理)* | 3        |   |

All four ★ sources use the `search` sub-command with distinct topic coverage:

| Source | 覆盖的 newsletter 类别 | 典型命中 |
|---|---|---|
| `ai-search` ("AI 大模型") | major-release / research-frontier | 大模型发布、基准测试突破 |
| `ai-agent` ("AI 智能体 Agent") | tools-release / major-release | Agent 框架发布、agentic 产品 |
| `ai-funding` ("人工智能 融资") | industry-business | 融资轮次、并购、估值 |
| `ai-policy` ("AI 政策 法规") | policy-regulation | 国家/地方 AI 政策、新规、发改委 |

The four queries have intentional topic overlap at the margins (e.g. a large fundraise for an AI company may appear in both `ai-search` and `ai-funding`). This is fine — Phase 3 dedup collapses cross-source duplicates by title similarity and absorbs them into one item with `source_count: 2`.

**Why skip "AI 芯片 算力"?** Chip/compute news on Tencent News tends to skew older than 48h and frequently hits financial product promotions (ETF launches, stock analysis). The `ai-search` and `ai-agent` queries pick up the most important compute stories (NVIDIA announcements, domestic chip news) through their broader coverage anyway. Add a dedicated chip source if you specifically need it.

**Why "AI 政策 法规" with `time_window_hours: 72`?** Policy documents and regulatory announcements don't publish every day; a tighter 48h window would miss many of them. 72h keeps a reasonable window without pulling in old content.

Recommended YAML for the search source:

```yaml
- name: tencent-news-ai-search
  type: cli
  enabled: true
  language: zh
  priority: 1
  command: "tencent-news-cli search \"AI 大模型\" --limit 20 --caller ai-newsletter-builder"
  parser: tencent-news-cli
  check:
    binary: tencent-news-cli
    install_hint: "install from https://news.qq.com/exchange?scene=appkey then: tencent-news-cli apikey-set <your-key>"
  extract:
    item_limit: 20
    time_window_hours: 48
    exclude_keywords: ["ETF", "涨停", "跌停", "涨超", "跌超", "股票", "基金", "大盘", "行情"]
```

The `exclude_keywords` list filters out stock-market and financial-product entries that frequently appear in AI-tagged news but have no newsletter value. Extend it per taste.

The `--caller` flag is recommended (identifies the client to Tencent News analytics); use your site name.

## Language hint

Set `language: zh` or `language: en` per source. Used only as a hint when summarizing — the site's output language is configured separately in `site.yaml` (`output_language: zh` or `en`). It's fine to have zh sources in an en-output site and vice versa; the model translates during the summarization step.

## What to write to the raw file

Each source's collector writes `data/raw/<date>/<name>.md`. Use this exact structure — the merge step relies on the field order:

```markdown
# Source: <name>
Collected at: 2026-04-18T08:02:33Z
Tool: tavily-search / web-access / webReader / gog / ...
Item count: 12

---

## <Item 1 title>
- url: https://...
- source: <name>
- published_at: 2026-04-18T04:15:00Z
- fetched_at: 2026-04-18T08:02:33Z
- language: en

<2–4 sentence factual summary in the source's language. No editorial framing.>

---

## <Item 2 title>
...
```

Keep summaries factual and short at this stage — editorial voice is applied during rendering, not collection. Keeping them short also makes dedup/merge cheaper.
