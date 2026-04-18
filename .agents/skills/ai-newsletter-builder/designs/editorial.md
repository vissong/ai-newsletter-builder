# Editorial

> 杂志风排版，强烈的标题层次，衬线体 + 高对比。适合像一份真的 newsletter 那样投递。

## Tokens
- background: #F7F3EC
- surface: #FFFDF8
- ink: #1B1B1A
- ink-muted: #5C5850
- accent: #A3330B
- accent-soft: #F2D9C9
- divider: #DCD3C2
- radius: 2
- font-body: "Source Serif Pro", "Noto Serif SC", Georgia, serif
- font-display: "Playfair Display", "Noto Serif SC", Georgia, serif
- font-mono: "IBM Plex Mono", ui-monospace, monospace
- max-width: 720

## Category colors
- major-release: #A3330B
- industry-business: #1C6B42
- research-frontier: #3A2F7A
- tools-release: #8A6B1F
- policy-regulation: #7A2233

## Typography scale
- h1: 56px / 1.05 / 700
- h2: 32px / 1.2 / 700
- h3: 20px / 1.35 / 700
- body: 17px / 1.75 / 400
- small: 13px / 1.5 / 400

## Voice
像一份周末刊物——有观点、有节奏、不怕用一句俏皮话开头。依然忠于事实，但在"这件事为什么值得一看"上多花一个句子。避免企业公关稿式的形容词；用动词驱动，让人读得下去。

## Hero
<section class="hero">
  <p class="hero__kicker">AI NEWSLETTER · DAILY ISSUE</p>
  <h1 class="hero__title">{{ title }}</h1>
  <p class="hero__lead">{{ lead_summary }}</p>
</section>

## Custom CSS
.hero { padding: 48px 0 24px; border-bottom: 1px solid var(--divider); margin-bottom: 32px; }
.hero__kicker { font-family: var(--font-mono); letter-spacing: 0.2em; font-size: 12px; color: var(--accent); margin: 0 0 12px; }
.hero__title { font-family: var(--font-display); font-size: 56px; line-height: 1.05; margin: 0 0 16px; }
.hero__lead { font-size: 19px; line-height: 1.6; color: var(--ink-muted); max-width: 640px; margin: 0; }
article h2 { font-family: var(--font-display); }
