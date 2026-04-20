# Newsletter Layouts

Multiple canonical page skeletons for the daily issue. Pick ONE per site based on the active DESIGN.md's atmosphere (§1) and voice — don't mix. The homepage uses the same layout family as the issues for consistency.

This guide is orthogonal to `design_md_guide.md`: DESIGN.md tells you **what the visual language is** (colors, fonts, components); this file tells you **how the page is organized**.

## How to pick

Read DESIGN.md §1 (Visual Theme & Atmosphere) and §7 (Do's and Don'ts), then match:

| If DESIGN.md reads as… | Use layout… |
|------------------------|-------------|
| Editorial, magazine, gallery, brand showcase, strong typographic voice — **or when unsure** | `editorial-longscroll` |
| Clean dashboard, product UI, airy minimalism, neutral | `card-grid` |
| Dev tool, mono, terminal, technical, changelog-y | `terminal-log` |
| Email-like, cozy, personal briefing, small audience | `digest-compact` |

When in doubt, default to `editorial-longscroll` — it's the most versatile and works with any DESIGN.md that has a hero treatment (gradient, dark band, photo, plain-text statement — all fine) and a typographic hierarchy.

You can always ask the user which they prefer if the DESIGN.md is ambiguous.

---

## Layout A: `editorial-longscroll`

Long scrolling page with a full-bleed hero, an inverted highlights block, mono-label category dividers, and border-only news items flowing down. The **structure** is fixed; the **visual character** comes entirely from the active DESIGN.md — this layout is design-system-agnostic and works with any design that has defined a hero treatment.

**Use when** you want a strong editorial opening and a clear continuous reading flow. Works with any DESIGN.md — minimal, editorial, warm, figma, cohere, or custom. If unsure, this is the safe default.

### Structure

```
<body>
  <!-- Hero: full-bleed, visually dominant.
       Background, colors, and typography all come from DESIGN.md §2 + §3.
       Layout only requires: full-width, first element, reader's eye lands here. -->
  <header class="hero">
    <h1>AI DAILY<br>NEWSLETTER</h1>
    <p class="date">YYYY年MM月DD日 · POWERED BY ...</p>
    <p class="hero-sub">源A · 源B · 源C</p>
  </header>

  <div class="container">

    <!-- Highlights: inverted-surface block, ~5 bullets.
         "Inverted" = foreground/background swap vs. page canvas.
         Exact colors: use DESIGN.md's dark/accent surface token.
         If DESIGN.md has no inverted surface, use primary accent at full opacity. -->
    <div class="highlights">
      <h2>TODAY'S HIGHLIGHTS · 今日要闻</h2>
      <ul>
        <li>top story 1 (one sentence)</li>
        <li>top story 2</li>
        ... 5 total, source_count desc
      </ul>
    </div>

    <!-- One section per category, in fixed slug order.
         .section-label appearance (font, border) comes from DESIGN.md §3/§4. -->
    <div class="section-label">重大发布 · Major Releases</div>

    <div class="news-item">
      <div class="news-tags">
        <span class="badge badge-hot">Hot</span>   ← source_count≥3 OR recent+source_count≥2
        <span class="badge">OpenAI</span>           ← brand entity from sources[]
        <span class="badge">大模型</span>            ← 1 theme tag, max 3 badges total
      </div>
      <h3>中文标题</h3>
      <div class="news-meta">
        <span>📅 YYYY-MM-DD</span>
        <span>📰 source-a · source-b</span>
      </div>
      <div class="news-content">
        摘要。<strong>关键数字/模型名</strong>加粗，
        必要时 <ul><li>...</li></ul> 结构化子要点。
      </div>
      <a class="news-link" href="url">→ 原文链接</a>
    </div>

    <div class="section-label">行业动态 · Industry &amp; Business</div>
    ...

  </div>

  <footer class="footer">
    <p><strong>AI 日报</strong> · 每日更新</p>
    <p>由 ai-newsletter-builder 生成 · <a href="../">← 返回首页</a></p>
  </footer>
</body>
```

### Structural rules (design-agnostic)

- **Hero** is always full-bleed and the page opening. Its visual treatment — gradient, dark band, photo, plain-text statement, or white with oversized type — is **fully determined by DESIGN.md §1 + §2**. Never hard-code a color or shape here.
- **Highlights block** uses the "inverted" surface (whatever contrast reversal the design defines). The layout requires it look visually different from the page canvas; the specific colors are DESIGN.md's job.
- **`.section-label`** marks each category. It must be visually distinct from body text; how (uppercase, mono, border, background band) is up to DESIGN.md.
- **`.news-item` has no card chrome** — only a bottom separator. Rhythm: `padding: 32px 0 / border-bottom: 1px`. Card decoration belongs in `card-grid`, not here.
- **`.badge` / `.badge-hot`** shape and color come from DESIGN.md §4 (component stylings). Badge-hot semantics: reserved for `source_count >= 3` OR `recent + source_count >= 2`. Don't over-use.
- **Footer** treatment follows DESIGN.md (dark bar, light strip, same-as-page, etc.). Not prescribed here.
- **Category order is fixed**: major-release → industry-business → research-frontier → tools-release → policy-regulation.
- **One mandatory visual constraint from the layout**: hero and highlights must not look identical. One must provide stronger contrast than the other. How — DESIGN.md decides.

### CSS mapping (for whoever writes style.css)

| Class | Layout contract | DESIGN.md source |
|---|---|---|
| `.hero` | full-width, visually dominant opener | §2 hero/accent colors + §1 atmosphere |
| `.hero h1` | largest text on page | §3 Display/Hero row |
| `.date`, `.hero-sub` | secondary header text | §3 Mono Label or Caption row |
| `.highlights` | inverted surface, high contrast | §2 dark/accent surface + §3 heading |
| `.section-label` | uppercase category divider | §3 Uppercase Label + §4 horizontal rule |
| `.news-item` | padding + bottom separator only | §5 spacing scale + §2 divider color |
| `.badge`, `.badge-hot` | small label/chip | §4 Component Stylings |
| `.news-content strong` | emphasis | §3 body weight scale |
| `.news-link` | styled link | §4 link treatment |
| `.footer` | page closing | §2 footer colors |

### Homepage for this layout

Same hero and container. Body is one `.news-item` per issue. `.badge` shows "DAILY" / date; `h3` is the issue title; `.news-content` is the summary; `.news-link` points into the daily page.

---

## Layout B: `card-grid`

Compact card grid inside a quiet column. Each item is a bordered card; categories are H2 headings; homepage shows issue teasers as card rows.

**Use when** DESIGN.md feels minimal, product-UI-like, dashboard-y. Pairs with `minimal`. Good when you expect LOTS of items and want dense scanning over narrative flow.

### Structure

```
<body>
  <header class="site-header">
    <a href="./">AI 日报</a>
    <p class="subtitle">...</p>
  </header>

  <main>
    <section class="intro">
      <h1>AI 日报 · 2026-04-18</h1>
      <p class="lead">2-3 句导读</p>
      <div class="stats">共 N 条 · M 个源 · 生成于 ...</div>
    </section>

    <section class="category" data-slug="major-release">
      <h2>重大发布 <span class="count">· 9</span></h2>
      <article class="item">
        <h3><a href="...">标题</a>
          <span class="category-tag" data-slug="major-release">重大发布</span>
        </h3>
        <p class="summary">摘要</p>
        <div class="meta">来源：a · b · 发布于 YYYY-MM-DD</div>
      </article>
      ...
    </section>

    <footer class="site-footer">...</footer>
  </main>
</body>
```

### Rules

- Single column, ~760px wide, generous line-height.
- No hero image; `<h1>` + lead paragraph is the top.
- Each item is a plain `<article>` with bottom border separation (not a box-shadow card).
- Category headings are `<h2>` with a small count suffix.
- `category-tag` is the key color marker (one per item, inline with title).

### Homepage for this layout

Exactly the existing `templates/index.html` + `build_index.py` output: `<ul class="issue-list">` of teaser blocks with top-3 items per issue.

---

## Layout C: `terminal-log`

No hero. Starts at the top with a system-prompt-style header and lists items like log entries. Dense, mono, left-aligned.

**Use when** DESIGN.md has `terminal` vibe, dev-tool audience, changelog aesthetic.

### Structure

```
<body>
  <pre class="prompt">$ ai-newsletter --date 2026-04-18 --items 35</pre>

  <section class="meta-block">
    <span class="k">items</span> 35
    <span class="k">sources</span> 18
    <span class="k">recent</span> 26
    <span class="k">trimmed</span> 10
  </section>

  <section class="category">
    <h2>[major-release] 重大发布 · 9</h2>
    <div class="log-entry">
      <span class="time">06:12Z</span>
      <span class="src">[openai-blog+2]</span>
      <a href="...">OpenAI 发布 ...</a>
      <span class="tag recent">recent</span>
      <p class="body">摘要，单段，无 bullet list。</p>
    </div>
    ...
  </section>
  ...

  <footer>— EOF —</footer>
</body>
```

### Rules

- Entire page is `font-family: mono` (per DESIGN.md §3 mono stack).
- No images, no shadows, minimal color (accent color only for links and one tag type).
- Time prefix on each entry (use `published_at` extracted time, else `--:--Z`).
- `[src+N]` shows source_count compactly.
- Keep summary to one paragraph; no structured lists.

### Homepage for this layout

Just a `ls` of issues. Pipe-separated. Clickable dates.

---

## Layout D: `digest-compact`

Email-style compact briefing. Works on narrow width (600px). Just text, minimal chrome. Feels like an actual newsletter drop.

**Use when** DESIGN.md is `warm` or any cozy / personal vibe, OR the user explicitly wants something that reads like an email.

### Structure

```
<body>
  <div class="email-wrap">
    <header>
      <h1>AI 日报</h1>
      <p class="from">你的每日 AI 简报 · 2026年4月18日</p>
    </header>

    <section class="lead">
      <p>2-3 句导读</p>
    </section>

    <section class="digest-section">
      <h2>▍ 重大发布</h2>
      <article>
        <h3>标题</h3>
        <p>摘要（一两句）。<a href="...">阅读原文 →</a></p>
        <small>来源：a · b · YYYY-MM-DD</small>
      </article>
      ...
    </section>

    <footer>
      <p>— 由 ai-newsletter-builder 生成</p>
      <p><a href="../">← 全部期号</a></p>
    </footer>
  </div>
</body>
```

### Rules

- 600px max-width.
- No hero, no colored blocks (except maybe a single warm accent on the leading bar ▍ before each category heading).
- Each item summary is ONE short sentence max. No `<ul>`, no `<strong>`. Length discipline is the whole point.
- Feels like it'd survive being pasted into a real email.

### Homepage for this layout

Same wrap, list of issues as short blocks with date + one-line summary + "read" link.

---

## Cross-layout conventions

No matter which layout you pick, keep these invariants so the content stays portable:

1. **5 category slugs are fixed**: `major-release`, `industry-business`, `research-frontier`, `tools-release`, `policy-regulation`. Layouts may change how they display them but not which exist.
2. **Category order is fixed** in the layouts above. Don't reorder even if DESIGN.md suggests otherwise.
3. **`trimmed: true` items never render**. They stay in `merged.json` for audit only.
4. **`recent: true` always gets surface treatment** — a badge, a position nudge to the top of its category, or color differentiation. How exactly depends on the layout (`.badge-hot` in A, `.recent` tag in C, etc.).
5. **`source_count > 1` is surfaced** somewhere in the item (badge, prefix, or count suffix). Multi-source = higher signal.
6. **`alt_urls` surface** where the layout allows: `<details>` in A, linked brackets in C, omit in D.

## Writing this file into a live site

When rendering a daily issue, include the chosen layout as a comment at the top of the HTML:

```html
<!-- layout: editorial-longscroll -->
```

This makes future rerenders consistent — if the model picks `editorial-longscroll` for issue 1 and someone regenerates issue 2 with a different model (or session), reading the comment tells them which skeleton to match.

Also note the chosen layout once in `site/config/site.yaml`:

```yaml
layout: editorial-longscroll
```

Load this at render time; don't re-pick every run.

## Adding a new layout

If none of A–D fits (rare — they cover the common shapes), propose a new one to the user rather than silently picking something else. A new layout should:

1. Define the hero (or the reason there isn't one).
2. Define the category presentation (headings, blocks, grouping).
3. Define the per-item unit (card / border-separated / log line / email entry).
4. Define the homepage counterpart.
5. List which DESIGN.md atmospheres it's best for.

Then either add it here, or save it inline in the site's `config/layout.md`.
