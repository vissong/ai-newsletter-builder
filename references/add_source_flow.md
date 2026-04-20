# Add Source Flow

Guided interview for adding a new data source. Each source lives in its own folder under `site/config/sources/<name>/`. Run this whenever the user asks to add/attach/integrate a new source. **Do not** skip the trial fetch — the whole point is to verify the source actually works before saving.

## Source Types

Two types:

| Type | Folder contents | When to use |
|------|----------------|-------------|
| `script` | `source.yaml` + `fetch.py` or `fetch.sh` | 有现成 CLI、稳定 API、或可解析的固定格式输出 |
| `prompt` | `source.yaml` + `prompt.md` | 网页结构不固定、需要 LLM 理解并提取内容 |

## Interview sequence

Run the questions in order. You can ask multiple in one message if the user seems engaged and the types are closely related, but don't front-load everything.

### 1. Type

> 新数据源的类型是？
> - `script` — 有可执行脚本获取数据（有现成 CLI 或稳定 API → 选这个）
> - `prompt` — 用 LLM 提取数据（网页结构不固定、需要智能解析 → 选这个）
>
> 简单判断：有现成 CLI 或稳定 API → script；网页结构不固定 → prompt

### 2. Name

> 给这个源起个短名字（将作为文件夹名，例如 `openai-blog`、`hacker-news`）。要求小写、用 dash 分隔、不重复。

Validate:
- Matches `^[a-z][a-z0-9-]{1,39}$`
- Folder `site/config/sources/<name>/` does not already exist

### 3. Type-specific questions

#### If type == `script`

1. **Runtime**: `python3` / `bash` / `node`? Default `python3`.
2. **Dependencies**: Does the script depend on external binaries or packages?
   - For each dependency, record `binary` (the executable name) and `install_hint` (one-line install command).
   - Verify each binary is installed:
     ```bash
     which <binary> || echo "not installed"
     ```
     If missing, show the install hint and stop. Do not proceed until all dependencies are available.
3. **Arguments**: Does the script need any arguments at runtime? Common ones:
   - `--date {{today}}` — date placeholder substituted at collection time
   - `--limit <n>` — item count cap
   - `--output <path>` — output file path (default: stdout)
   Record these in `source.yaml` under `args`.
4. **Co-write the fetch script**: Based on the user's description, write `fetch.py` / `fetch.sh` / `fetch.js` together. The script must:
   - Output a JSON array to stdout (each item: `{title, url, summary, date?, source?}`)
   - Exit 0 on success, non-zero on failure
   - Print errors to stderr, never to stdout
   - Use only stdlib imports unless a dependency was declared in step 2

#### If type == `prompt`

1. **Fetch method**: How to get the raw content before LLM extraction?
   - `web` — fetch a URL (tiered fallback: browser → plain fetch → Jina Reader → WebSearch)
   - `search` — run a search query (`{{today}}` / `{{yesterday}}` substitution available)
   - `email` — read email via CLI (e.g. `gog` for Gmail)
   - `cli` — run a shell command, capture stdout
2. **Method-specific params**:
   - **web**: URL of the page/feed; is it a list page or single article? Need login/JS?
   - **search**: query template (explain `{{today}}`/`{{yesterday}}`); `result_limit` (default 20); blocked domains?
   - **email**: provider + CLI binary; query expression; `max_messages` (default 30)
   - **cli**: the full command; what stdout looks like (HTML/JSON/plain text)
3. **Extraction hints**: What should the LLM look for? Category preferences? Language of the content? Typical number of items per fetch?
4. **Co-write the prompt.md**: Build the file with three sections:

   ```markdown
   ## Fetch
   [How to obtain raw content — method, URL/query/command, parameters]

   ## Extract
   [What to extract — field mapping, item format, quality filters]

   ## Edge Cases
   [Empty results, rate limits, format changes, fallback strategies]
   ```

   The prompt.md is what Claude reads at collection time to know how to fetch and parse this source. Be specific and actionable.

### 4. Optional metadata

- `language` — `en` / `zh` / other (default: infer from URL/content or ask).
- `priority` — 1 (primary, always collect) / 2 (secondary) / 3 (niche, collect only when asked). Default 2.
- `enabled` — default true.

Record these in `source.yaml`.

## Trial fetch

As soon as the user answers the type-specific questions, run a trial fetch — don't persist anything yet.

### For `script` type:

1. Run the fetch script with `item_limit` capped at 3 (or equivalent argument).
2. Validate that stdout is a valid JSON array.
3. Check each item has at least `title` and `url`.
4. Show the user all items (title + url + 1-sentence summary) inline.
5. Report: execution time, item count, any stderr warnings.

### For `prompt` type:

1. Execute the prompt.md instructions: fetch raw content using the declared method.
2. Apply the Extract section with `item_limit=3`.
3. Format extracted items as JSON array.
4. Show the user all items (title + url + 1-sentence summary) inline.
5. Report: execution time, item count, any extraction issues.

### Typical outcomes:

- **Success (items returned, sensible fields):** ask "保存这个源？" → create folder.
- **Partial (items but titles missing / summaries are noise):** for `script`, fix the parsing logic; for `prompt`, refine the Extract section. Re-try.
- **Empty (0 items):** probably URL/query/auth issue. Ask the user whether to debug together (check the raw response) or skip.
- **Error (script failed, binary not found, fetch timeout):** surface the exact error; offer install instructions or a different approach.

Do not save a source that couldn't fetch anything in the trial. A broken source silently corrupts future runs and is hard to notice.

## Save

On success, create the source folder:

```
site/config/sources/<name>/
├── source.yaml
└── fetch.py / fetch.sh / fetch.js   (script type)
    OR
    prompt.md                          (prompt type)
```

### source.yaml format

For `script` type:
```yaml
name: <name>
type: script
runtime: python3  # or bash, node
args:
  - "--date"
  - "{{today}}"
dependencies:
  - binary: rsstail
    install_hint: "brew install rsstail"
language: en
priority: 2
enabled: true
```

For `prompt` type:
```yaml
name: <name>
type: prompt
fetch_method: web  # or search, email, cli
params:
  url: "https://example.com/blog"
  # or query: "AI news {{today}}"
  # or command: "gog search ..."
language: en
priority: 2
enabled: true
```

Show created files to the user and echo a one-line summary:

> 已添加 `openai-blog` (script, python3, priority 1). 试运行获取 3 条数据，耗时 4.2s. 默认启用。

## Editing / removing / disabling a source

All operations target the folder `site/config/sources/<name>/`.

- **Edit**: Load `source.yaml` + script/prompt, show current config, ask what to change, run the trial fetch again after the edit, save if the trial still works.
- **Remove**: Show the folder contents, ask for confirmation (`确认删除 <name> 源？`), delete the entire folder. Leave historical `data/raw/<date>/<name>.md` files alone — they still contribute to past issues.
- **Disable**: Set `enabled: false` in `source.yaml` without deleting the folder. Useful for sources that are intermittent or rate-limited.
- **Enable**: Set `enabled: true` in `source.yaml`. Optionally re-run the trial fetch to verify it still works.
