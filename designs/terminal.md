# Terminal

> 深色背景、等宽字体、ANSI 风格的强调色——给工程师读的 newsletter。

## Tokens
- background: #0B0F14
- surface: #11161D
- ink: #D8DEE9
- ink-muted: #7C8796
- accent: #7DF9A2
- accent-soft: #1B2B22
- divider: #1E2630
- radius: 4
- font-body: "JetBrains Mono", "IBM Plex Mono", ui-monospace, "SF Mono", monospace
- font-display: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace
- font-mono: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace
- max-width: 820

## Category colors
- major-release: #7DF9A2
- industry-business: #F5C66C
- research-frontier: #A1A1FF
- tools-release: #5DE1E6
- policy-regulation: #FF8D7A

## Typography scale
- h1: 28px / 1.3 / 700
- h2: 20px / 1.4 / 700
- h3: 16px / 1.5 / 700
- body: 14px / 1.7 / 400
- small: 12px / 1.4 / 400

## Voice
像 changelog 条目——动词开头、事实紧凑、能用数字就上数字。省略冠词和客套；用 `$`、`→`、`—` 等符号作为视觉锚点。不吹不黑，像在终端里读发布说明。

## Hero
<section class="hero">
  <div class="hero__prompt">$ ai-newsletter --date {{ date }}</div>
  <h1 class="hero__title">{{ title }}</h1>
  <p class="hero__lead">{{ lead_summary }}</p>
  <div class="hero__meta">items: {{ stats.total_items }} · sources: {{ stats.total_sources }}</div>
</section>

## Custom CSS
body { font-feature-settings: "liga" 0; }
.hero { border: 1px solid var(--divider); padding: 20px; margin: 24px 0 32px; background: var(--surface); }
.hero__prompt { color: var(--accent); font-size: 12px; margin-bottom: 12px; }
.hero__title { font-size: 28px; margin: 0 0 8px; }
.hero__lead { color: var(--ink-muted); margin: 0 0 12px; }
.hero__meta { color: var(--ink-muted); font-size: 12px; border-top: 1px dashed var(--divider); padding-top: 8px; }
.category-tag::before { content: "["; }
.category-tag::after { content: "]"; }
