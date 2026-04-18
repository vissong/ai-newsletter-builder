# DESIGN.md Guide (Google Stitch / getdesign.md format)

Richer design systems in this skill use a **directory** under `designs/<name>/` containing a `DESIGN.md` file. This format comes from Google Stitch and is also what [getdesign.md](https://getdesign.md/) publishes. It's a prose-heavy, 9-section spec that you interpret into CSS and HTML — it is NOT a simple token list like the legacy `.md` designs (minimal/editorial/terminal/warm).

## File layout

```
designs/
├── figma/
│   └── DESIGN.md          # Google Stitch format, 9 sections
├── cohere/
│   └── DESIGN.md
└── minimal.md             # legacy single-file, tokens-only
```

Users can add their own by:
1. Downloading a DESIGN.md from [getdesign.md](https://getdesign.md/) and dropping it into `designs/<name>/DESIGN.md`.
2. Writing their own following the 9-section schema below.
3. Pointing `--design <path>` at an external directory.

## The 9-section schema

Every Stitch-style DESIGN.md has these sections in order. If a user's file is missing a section, warn but don't fail — use sensible defaults.

| # | Section | What to extract |
|---|---------|-----------------|
| 1 | **Visual Theme & Atmosphere** | The mood. Read it to calibrate voice + the overall feel of the page. Informs how aggressive/calm/playful the markup is. |
| 2 | **Color Palette & Roles** | Hex values, roles (primary, surface, accent, gradient, etc.). Turn into CSS custom properties. |
| 3 | **Typography Rules** | Font stacks, weights, size scale, line heights, letter-spacing. Turn into CSS vars + utility classes. |
| 4 | **Component Stylings** | Per-component rules — buttons (pill/solid/glass variants), cards, navigation, distinctive components. Emit real CSS classes matching these names so the issue template can opt into them. |
| 5 | **Layout Principles** | Spacing scale, max-width, grid, border-radius scale. Turn into CSS vars. |
| 6 | **Depth & Elevation** | Shadow scale. |
| 7 | **Do's and Don'ts** | Read this! It prevents you from doing things that violate the spirit of the system (e.g. "don't use drop shadows on the hero"). |
| 8 | **Responsive Behavior** | Breakpoints + collapsing strategy. |
| 9 | **Agent Prompt Guide** | Optional — the designer's own notes for agents. If present, follow it; it's the most direct spec. |

## Translating DESIGN.md into `site/assets/style.css`

You (the model) own this step. There is no script that parses the prose. Read the whole DESIGN.md, then write a complete `style.css` that:

### 1. Declares CSS variables from §2, §3, §5, §6

```css
:root {
  /* §2 colors */
  --color-ink: #000000;
  --color-bg: #ffffff;
  --color-accent: ...;
  --gradient-hero: linear-gradient(...);

  /* §3 typography */
  --font-display: "figmaSans", "SF Pro Display", system-ui, sans-serif;
  --font-mono: "figmaMono", "SF Mono", monospace;
  --weight-thin: 320;
  --weight-regular: 400;
  --weight-bold: 700;

  /* §5 spacing + radius */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --radius-subtle: 6px;
  --radius-card: 8px;
  --radius-pill: 50px;

  /* §6 shadows */
  --shadow-1: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-2: 0 4px 12px rgba(0,0,0,0.08);
}
```

### 2. Writes component classes from §4 by exact name

If the spec mentions "Black Solid (Pill) button" and "Glass Dark button," emit `.btn-solid-pill` and `.btn-glass-dark`. The class names don't have to match verbatim — what matters is that they exist and are documented in a comment at the top of the CSS so the render step knows which classes to attach to which elements.

### 3. Writes base styles using the tokens

`body`, `h1–h3`, `a`, `p` — styled from §3 typography rules. Don't leave defaults showing through.

### 4. Implements the `.category-tag` system using design-appropriate shapes

The category tag is mandatory in our HTML (5 category slugs). Map each slug to a color from §2 that fits the system:

- `major-release` — the most visually loud color in the palette (accent)
- `industry-business` — a secondary / neutral hue
- `research-frontier` — another secondary
- `tools-release` — another secondary
- `policy-regulation` — a warning/attention hue (red/orange family if present)

Shape follows §4/§5. If the system uses pill buttons (figma), use pill category tags. If it uses sharp corners (editorial), use square. Don't force inconsistency.

### 5. Honors §7 Do's and Don'ts

This is where most mistakes happen. Re-read §7 before finalizing the CSS. If it says "don't use drop shadows on the hero," don't. If it says "always enable `font-feature-settings: 'kern' 1`," do.

### 6. Includes a header comment block

```css
/* Generated from designs/<name>/DESIGN.md — do not edit by hand.
 * Regenerate by asking the skill to re-render CSS.
 *
 * Component classes available:
 * - .btn-solid-pill, .btn-glass-dark, .btn-white-pill
 * - .card, .card-elevated
 * - .hero, .hero-gradient
 * - .tab-bar, .tab
 * - .category-tag, .recent-badge
 */
```

This helps the render step (Phase 5) know which classes it can reach for.

## Translating DESIGN.md into the issue HTML

The issue template (`templates/issue.html`) is intentionally lean — it's a structural skeleton. When DESIGN.md is active, the render step should:

1. Read DESIGN.md §1 to set voice (stays consistent with the Chinese summary writing).
2. Read §4 to know what components exist. Attach appropriate classes to template regions:
   - Hero: use `.hero` / `.hero-gradient` if the system has one (figma does; minimal doesn't).
   - Category headings: use `.tab` or `.section-heading` styling.
   - Items: wrap in `.card` or `.card-elevated` if §4 defines cards; otherwise use the plain item layout.
   - Source-count badge: use `.mono-label` if §3 defines a mono uppercase style.
3. Read §7 once more before finalizing. Do not add visual flourishes that violate the "Don't" list.

Don't invent components that aren't in the system. If DESIGN.md doesn't mention gradients, don't add gradients just because they'd look nice.

## Translating into the homepage

Same philosophy: the homepage is a list of issue teasers. Attach design-appropriate component classes:
- `.card` or `.card-elevated` for each issue entry
- `.mono-label` for the date kicker
- `.category-tag` for the category counts (styled once in CSS, reusable everywhere)

Don't duplicate work — the homepage and issue pages share `style.css`. Both benefit from the same component definitions.

## When a section is missing

Graceful fallbacks, in priority order:

- Missing §2 — refuse to proceed, ask the user for colors. Can't fake this.
- Missing §3 — use system-ui 400 for body, 700 for headings. Emit a TODO comment in CSS.
- Missing §4 — emit only the category-tag + base classes; no buttons / cards / hero.
- Missing §5 — use 8px base with common multiples; radius 8px for cards.
- Missing §6 — flat design, no shadows.
- Missing §7 — tread more carefully; less guidance means more room for error. Stick to the most literal reading of §1–§5.
- Missing §8 — center the main column at 720–840px max width, stack on small screens.
- Missing §9 — fine, most files don't have this.

## Fetching from getdesign.md

When the user asks to use a DESIGN.md from getdesign.md:

1. Ask them for the brand slug (e.g. `linear`, `stripe`, `vercel`).
2. Use the best available web tool (see SKILL.md's Phase 1 tool priority) to fetch `https://getdesign.md/<slug>` — the markdown is the page body, typically a download link or inline content.
3. Save to `designs/<slug>/DESIGN.md` in the skill OR to `site/config/design/<slug>/DESIGN.md` in the active site if this is a one-off. Ask the user where to save.
4. Validate it has the 9 sections; if missing, show what's missing and ask whether to proceed with fallbacks.

## Distinguishing DESIGN.md from legacy design.md

| Feature | Legacy `.md` (minimal.md etc) | `DESIGN.md` (Stitch / getdesign.md) |
|---------|-------------------------------|-------------------------------------|
| Location | `designs/<name>.md` (single file) | `designs/<name>/DESIGN.md` (directory) |
| Parser | `scripts/init_site.py` regex | Model reads prose |
| CSS generation | Python templated | Model-written, rich |
| Schema | Tokens + category colors + voice | 9 numbered prose sections |
| Use when | Quick custom style, prototyping | Polished brand match, production sites |

Both are supported. The skill picks up whichever exists. If both exist under the same name (you shouldn't), directory wins.

## See also

`references/newsletter_layouts.md` is the companion file to this one. DESIGN.md defines the **visual language** (colors, type, components). newsletter_layouts.md defines the **page skeleton** (hero shape, category presentation, item unit). You need both to render a page — first pick a layout that matches DESIGN.md §1 atmosphere, then style its required classes with DESIGN.md §2–§6.
