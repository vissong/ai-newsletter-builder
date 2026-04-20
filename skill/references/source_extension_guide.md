# Source Extension Guide

How to create, configure, and test data sources for the newsletter pipeline. Each data source is a **folder** under `site/config/sources/<name>/`. The pipeline auto-discovers all folders containing a `source.yaml`.

## Choosing script vs prompt

```
Is the data format stable and machine-parseable?
  ├─ YES: structured API, CLI with fixed output, git-tracked JSON feed
  │       → type: script — write a fetch script that outputs JSON to stdout
  │
  └─ NO: web page that changes layout, search results, email newsletters
         → type: prompt — write a prompt.md describing how to fetch and extract
```

**Rule of thumb:** if you could write a parser that works for 6+ months without changes, use `script`. If you'd need to tweak selectors or parsing logic every few weeks, use `prompt` and let the LLM adapt.

## Folder structure

```
site/config/sources/<name>/
├── source.yaml              # required: metadata + config
├── fetch.py or fetch.sh     # script type: the fetch script
└── prompt.md                # prompt type: fetch + extraction instructions
```

A source folder must contain `source.yaml` and exactly one of `fetch.py`/`fetch.sh` (script type) or `prompt.md` (prompt type).

## source.yaml schema

### Common fields (both types)

```yaml
name: techcrunch-ai              # MUST match the folder name; lowercase-dashed
                                 # regex: ^[a-z][a-z0-9-]{1,39}$
type: script                     # "script" | "prompt"
enabled: true                    # default true; set false to skip without deleting
language: en                     # en | zh | other; hint for summarization
priority: 1                      # 1 (primary) .. 3 (niche); used to pick highlights
time_window_hours: 48            # drop items older than this; default 48
recent_hours: 24                 # mark items within this window as recent; default 24
timeout_seconds: 30              # hard deadline per fetch; default 30, max 120
```

### Script type additional fields

```yaml
type: script

script: fetch.py                 # entry point, relative to source folder
                                 # default: fetch.py (or fetch.sh if no .py exists)
                                 # can also reference a shared script in scripts/ (e.g. fetch_rss.py)
runtime: python3                 # python3 | bash | node; inferred from extension if omitted

check:                           # optional but recommended dependency check
  binary: git                    # executable that must be in PATH
  install_hint: "git must be installed and available in PATH"

args:                            # key-value pairs passed to the script
  cache_dir: site/data/sources/follow-builders
  recent_hours: "{{recent_hours}}"   # template var resolved at collection time
```

**Available template variables in `args`:**

| Variable | Resolved to |
|---|---|
| `{{date}}` | Collection date, ISO format (e.g. `2026-04-20`) |
| `{{recent_hours}}` | Value of `recent_hours` from this source.yaml |
| `{{time_window_hours}}` | Value of `time_window_hours` from this source.yaml |

### Shared scripts

The `script` field can reference a script in the skill's `scripts/` directory. This avoids duplicating the same logic across many sources — source folders contain only `source.yaml` config, and the collector resolves the script from the skill path.

Built-in shared script: **`scripts/fetch_rss.py`** — generic RSS/Atom feed fetcher. Supports RSS 2.0, Atom, and RDF/RSS 1.0. Accepts `--url`, `--time-window-hours`, `--item-limit`, `--language` via args. All 12 built-in RSS sources share this single script.

Example source.yaml using the shared RSS script:

```yaml
name: techcrunch-ai
type: script
script: fetch_rss.py
runtime: python3
args:
  url: "https://techcrunch.com/category/artificial-intelligence/feed/"
  time_window_hours: "{{time_window_hours}}"
  item_limit: "15"
```

The collector looks for the script in two places: first in the source folder itself, then in the skill's `scripts/` directory. Custom shared scripts follow the same pattern — place them in `scripts/` and reference by filename.

### Prompt type additional fields

```yaml
type: prompt

fetch_method: web                # web | search | email | cli
                                 # informational hint for the LLM about which tools to use

extract:                         # extraction config read by the LLM alongside prompt.md
  item_limit: 15
  follow_articles: true
  follow_limit: 10
  exclude_selectors: [".ad", ".sponsored"]
  exclude_keywords: ["广告", "推广"]

requires_capability: real_browser  # optional; see data_sources.md §Capabilities
```

## JSON output contract

All sources — both script and prompt — produce a **JSON array**. Scripts write it to stdout; prompt-based sources format it as the extraction result.

```json
[
  {
    "title": "OpenAI launches GPT-5.1",
    "url": "https://openai.com/blog/gpt-5-1",
    "published_at": "2026-04-18T06:00:00Z",
    "summary": "OpenAI announced GPT-5.1, a multi-modal model that scores 92% on MMLU-Pro. Available via API today.",
    "language": "en"
  }
]
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | yes | Items without a title are dropped |
| `url` | string | yes | Items without a URL are dropped |
| `published_at` | ISO-8601 | no | Falls back to `fetched_at` if missing |
| `summary` | string | yes | 2-4 sentences, factual, in source language |
| `language` | string | no | Inherited from `source.yaml` if missing |

**Fields injected by the collector** (do NOT include in script/prompt output):
- `source` — folder name
- `fetched_at` — collection timestamp
- `recent` — true if within `recent_hours`

## Script type: detailed contract

### Input

The collector invokes the script as:

```
<runtime> <source-folder>/<script> [--key value ...]
```

Arguments come from the `args:` map in source.yaml, with template variables resolved. Example:

```bash
python3 site/config/sources/follow-builders/fetch.py \
  --cache-dir site/data/sources/follow-builders \
  --recent-hours 24
```

### Output

- **stdout**: a JSON array matching the output contract above. Nothing else on stdout.
- **stderr**: diagnostics, progress messages, warnings — free-form, not parsed.
- **exit code**: 0 = success (even if 0 items); non-zero = failure.

### Environment variables

The collector sets these before invoking the script:

| Variable | Value |
|---|---|
| `SOURCE_NAME` | Folder name (e.g. `follow-builders`) |
| `SOURCE_DATE` | Collection date, ISO (e.g. `2026-04-20`) |
| `SOURCE_DIR` | Absolute path to the source folder |

### Error handling

- If `check.binary` is specified, the collector runs `which <binary>` first. If missing, the source is marked failed in `collect.log` with the `install_hint` message — the script is never invoked.
- If the script exits non-zero, the source is marked failed. stderr is captured into `collect.log`.
- If stdout is not valid JSON or not an array, the source is marked failed with a parse error.

### Example: follow-builders/fetch.py

See `templates/sources/follow-builders/fetch.py` for a complete working example.

Key patterns:
- Git clone/pull with change detection (SHA-256 hashes)
- Multiple sub-feeds parsed into a unified item list
- `json.dump(items, sys.stdout, ensure_ascii=False)` at the end

## Prompt type: writing prompt.md

A `prompt.md` file is the LLM's complete instruction set for fetching and extracting content from a source. Structure it in three sections:

### Section 1: Fetch

Describe HOW to get the raw content:
- The URL or command to execute
- Which tool tier to prefer (e.g. "use WebFetch on the RSS URL directly")
- Authentication requirements, if any
- Whether the page needs JS rendering

### Section 2: Extract

Describe WHAT to pull out:
- Which elements on the page represent items (CSS selectors, XML tags, JSON paths)
- How to map page elements to the JSON contract fields (title, url, published_at, summary)
- Whether to follow article links for full text
- Date format conversion rules

### Section 3: Edge Cases

Describe what can go wrong and how to handle it:
- Ad/promotion filtering rules
- Non-AI content that might appear
- Date parsing quirks
- Pagination behavior
- Known failure modes (CAPTCHA, rate limiting)

### Example: techcrunch-ai/prompt.md

```markdown
# techcrunch-ai

## Fetch

URL: https://techcrunch.com/category/artificial-intelligence/feed/
This is an RSS feed returning XML with ~23 items, updated hourly.
Use WebFetch directly — the feed URL returns 200 without anti-bot friction.
No JS rendering or login needed.

## Extract

From the RSS XML, extract each <item>:
- title: from <title>
- url: from <link>
- published_at: from <pubDate> (RFC-822 format → convert to ISO-8601)
- summary: from <description> — short excerpts (~25-30 words)

Descriptions are too short for good summaries. Follow each article URL
(up to follow_limit) to fetch full text and produce a 2-4 sentence summary.

## Edge Cases

- Ignore items with <category> containing "Sponsored" or "Partner"
- The feed occasionally includes non-AI articles from other TC categories;
  skip items whose title and description contain no AI/ML/LLM-related terms
- <pubDate> is always present and accurate
```

### How extract config interacts with prompt.md

The `extract:` block in source.yaml provides **parameters** that the LLM reads alongside `prompt.md`:
- `item_limit` caps how many items to extract
- `follow_articles` / `follow_limit` control whether to fetch full article text
- `exclude_selectors` / `exclude_keywords` provide filtering rules
- `time_window_hours` is applied by the collector after extraction

The prompt.md should reference these parameters by name (e.g. "follow each article URL up to `follow_limit`") so the LLM knows to respect them.

## Testing a source

### Trial fetch (manual)

**Script type:**
```bash
cd site/config/sources/<name>
python3 fetch.py --cache-dir /tmp/test-cache | python3 -m json.tool | head -50
```
Verify: valid JSON array, items have title + url + summary.

**Prompt type:**
During the add-source guided flow, the skill runs a trial fetch with `item_limit` capped at 3. You can also test by asking the skill: "试一下 techcrunch-ai 这个源" — it reads the prompt.md and runs the extraction.

### Checklist

- [ ] `source.yaml` passes schema validation (name matches folder, type is script/prompt)
- [ ] Script exits 0 and outputs valid JSON array to stdout
- [ ] Or prompt.md has all three sections (Fetch / Extract / Edge Cases)
- [ ] At least 1 item extracted in trial fetch
- [ ] Items have title, url, and summary fields
- [ ] `published_at` is ISO-8601 when present

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Script exits non-zero | Missing dependency or bad args | Check `check.binary`; run script manually with stderr visible |
| stdout is not JSON | Script prints diagnostics to stdout | Move all non-JSON output to stderr |
| 0 items extracted | Wrong URL, stale feed, or selector mismatch | Run trial fetch; check if page structure changed |
| Timeout | Source is slow or hung | Increase `timeout_seconds` or switch to a faster tier |
| Prompt extracts wrong fields | prompt.md is vague | Add explicit CSS selectors or XPath in the Extract section |
| Duplicate items across runs | No change detection | For script type, implement hash-based change detection (see follow-builders example) |
