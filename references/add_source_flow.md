# Add Source Flow

Guided interview for adding a new data source to `site/config/sources.yaml`. Run this whenever the user asks to add/attach/integrate a new source. **Do not** skip the trial fetch — the whole point is to verify the source actually works before saving.

## Interview sequence

Run the questions in order. You can ask multiple in one message if the user seems engaged and the types are closely related, but don't front-load everything.

### 1. Type

> 新数据源的类型是？
> - `email` — 邮箱（需要对应邮箱 CLI，比如 Gmail 用 `gog`）
> - `web` — 网页或博客（用网页抓取工具读取）
> - `search` — 搜索查询（用搜索工具执行）
> - `cli` — 其他命令行工具（比如 RSS、自建聚合器）

### 2. Name

> 给这个源起个短名字（用作文件 key，例如 `openai-blog`、`my-gmail`）。要求小写、用 dash 分隔、不重复。

Validate:
- Matches `^[a-z][a-z0-9-]{1,39}$`
- Not already in `sources.yaml`

### 3. Type-specific questions

#### If type == `web`

1. URL of the index or feed page.
2. Is it a list page (many articles) or a single-article page? If list, ask for `item_limit` (default 15) and `time_window_hours` (default 48).
3. Does it need login / cookies / JS rendering? If yes, recommend `web-access` or `browser-use` skill. If no, `webReader` or `WebFetch` is fine.
4. Should we follow each article for its full text? (default yes for list pages, no for single-article feeds).

#### If type == `search`

1. The search query. Explain that `{{today}}` and `{{yesterday}}` will be substituted at collection time.
2. Preferred search provider (tavily / built-in) — or leave unset to auto-pick.
3. `result_limit` (default 20), `follow_articles` (default true), blocked domains if any.

#### If type == `email`

1. Provider (gmail / outlook / imap / ...).
2. CLI binary to use (default per provider: gmail → `gog`).
3. Query — for Gmail use its native search syntax; for IMAP, a search expression.
4. `max_messages` (default 30), include full body (default yes), strip quoted reply chains (default yes).
5. Verify the CLI is installed:
   ```bash
   which <cli> || echo "not installed"
   ```
   If missing, provide the install hint and stop. Do not save the source until the CLI is available.

#### If type == `cli`

1. The full command to run. Explain that stdout will be captured.
2. Parser — `rsstail` / `jsonl` / `raw` + separator. Ask what stdout looks like; pick one.
3. `check.binary` — the executable the command depends on.
4. `check.install_hint` — one-line install command for missing binary.
5. Verify the binary is installed; on miss, show the hint and stop.

### 4. Optional metadata

- `language` — `en` / `zh` / other (default: infer from URL or ask).
- `priority` — 1 (primary, always collect) / 2 (secondary) / 3 (niche, collect only when asked). Default 2.
- `enabled` — default true.

## Trial fetch

As soon as the user answers the type-specific questions, run a trial fetch against a temporary YAML fragment — don't persist to `sources.yaml` yet. The trial should:

1. Execute the exact fetch that phase 2 would run, but with `item_limit` capped at 3.
2. Parse the result into the normalized item format.
3. Show the user all 3 items (title + url + 1-sentence summary) inline.
4. Tell them how long it took, how many items came back, and any parse warnings.

Typical outcomes:

- **Success (3 items, sensible fields):** ask "save this source?" → append to `sources.yaml`.
- **Partial (items but titles are missing / summaries are HTML noise):** suggest an `extract.list_selector` tweak, or switch reader tool, and re-try.
- **Empty (0 items):** probably selector / query / auth issue. Ask the user whether to debug together (check the raw response) or skip.
- **Error (tool failed, CLI not found):** surface the exact error; offer install instructions or a different tool.

Do not save a source that couldn't fetch anything in the trial. A broken source in `sources.yaml` silently corrupts future runs and is hard to notice.

## Save

On success, append the new source to `site/config/sources.yaml` *preserving existing comments and order* (insert at the end of its type's group if one exists). Show the diff to the user and confirm.

Also echo back a one-line summary:

> Added `openai-blog` (web, priority 1, follow_articles=true). Trial fetched 3 items in 4.2s. Enabled by default.

## Editing / removing a source

Same flow, inverted:

- **Edit**: load the source block, show current values, ask what to change, run the trial fetch again after the edit, save if the trial still works.
- **Remove**: show the block, ask for confirmation, delete. Leave historical `data/raw/<date>/<name>.md` files alone — they still contribute to past issues.
- **Disable**: flip `enabled: false` without deleting. Useful for sources that are intermittent or rate-limited.
