# Design Systems

A `design.md` file describes a visual style for the newsletter. The skill ships four built-ins under `designs/`, and users can supply their own.

Applying a design means:
1. Copy (or link) the chosen `design.md` to `site/config/design.md`.
2. Generate `site/assets/style.css` from its tokens.
3. Inject the HTML shell snippet (if the design defines one) into the templates.

This file explains the `design.md` contract so you can validate user-supplied designs and translate any of them consistently.

## Required sections in `design.md`

Every `design.md` must declare the following headings. If a user's file is missing one, ask them to fill it in — don't silently invent values.

```
# <Design name>

> <one-line tagline>

## Tokens
- background: #hex
- surface: #hex
- ink: #hex                 (primary text)
- ink-muted: #hex           (secondary text)
- accent: #hex              (primary accent, used on links and category badges)
- accent-soft: #hex         (tint of accent, for hover backgrounds)
- divider: #hex
- radius: 0 | 6 | 12 | ...  (base border radius in px)
- font-body: <CSS font stack>
- font-display: <CSS font stack>
- font-mono: <CSS font stack>
- max-width: 720 | 840 | 960  (main column width in px)

## Category colors
- major-release: #hex
- industry-business: #hex
- research-frontier: #hex
- tools-release: #hex
- policy-regulation: #hex

## Typography scale
- h1: size/line-height/weight
- h2: ...
- h3: ...
- body: ...
- small: ...

## Voice
<2–4 sentences describing the tone of voice the renderer should match when
writing summaries and the editorial lead.>

## Optional

### Hero
<optional HTML snippet inserted above the list on both index and issue pages>

### Custom CSS
<optional verbatim CSS appended after the token-derived CSS>
```

The Tokens, Category colors, Typography scale, and Voice sections are required. Hero and Custom CSS are optional.

## Translating tokens to CSS

```css
:root {
  --bg: <background>;
  --surface: <surface>;
  --ink: <ink>;
  --ink-muted: <ink-muted>;
  --accent: <accent>;
  --accent-soft: <accent-soft>;
  --divider: <divider>;
  --radius: <radius>px;
  --max-w: <max-width>px;
  --font-body: <font-body>;
  --font-display: <font-display>;
  --font-mono: <font-mono>;

  --cat-major-release: <...>;
  --cat-industry-business: <...>;
  --cat-research-frontier: <...>;
  --cat-tools-release: <...>;
  --cat-policy-regulation: <...>;
}
```

Every template is token-driven — changing a single color in `design.md` and re-running the build should ripple through every page. Never hard-code colors in templates.

## Voice section

The Voice section is the only free-prose part. Read it before rewriting item summaries and before writing the editorial lead. The model should match the voice — a `terminal.md` voice will say "shipped" where `editorial.md` would say "unveiled."

## Validating a user-supplied design.md

When the user points at an external `design.md`:

1. Parse it. Check all required sections exist.
2. Check tokens are valid (hex colors, numeric sizes).
3. Check category colors cover all 5 slugs.
4. Render a quick preview — a single issue page with sample data — so the user can see the result before overwriting the existing style. Save preview to `site/preview.html`.
5. On confirm, copy the file to `site/config/design.md` and regenerate `assets/style.css`.

If validation fails, show the exact missing/invalid field. Do NOT try to fix it silently.

## Built-in designs

| file            | vibe                                             |
| --------------- | ------------------------------------------------ |
| `minimal.md`    | 极简白底、大段留白、sans + 灰调；适合长期阅读     |
| `editorial.md`  | 杂志风、强排版层次、大标题 + 衬线；适合拿来投递   |
| `terminal.md`   | 深色、等宽、赛博终端感；适合开发者口味            |
| `warm.md`       | 米色底、柔和强调色、温暖配色；适合生活化订阅感    |

Each one is complete — copy-paste into `site/config/design.md` and the build works immediately.

## Switching designs

When the user wants to switch styles:

1. Ask whether to re-render past issues or only apply to new ones. Past issues load the current `assets/style.css`, so a style change applies to all of them automatically once the CSS is regenerated; the question is really about whether any per-page HTML structure also needs to change (e.g. the Hero block was structurally different in the old design).
2. Copy the new `design.md` into `site/config/design.md`.
3. Regenerate `site/assets/style.css`.
4. Rebuild the homepage via `scripts/build_index.py`. Re-render daily pages only if the HTML shell changed.
