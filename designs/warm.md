# Warm

> 米色底、柔和强调色、像午后咖啡的温暖配色——适合生活化的订阅感。

## Tokens
- background: #FBF5EB
- surface: #FFFBF2
- ink: #2B2118
- ink-muted: #7A6B5A
- accent: #C85A3F
- accent-soft: #F6DBCE
- divider: #EADFC9
- radius: 14
- font-body: "Source Sans 3", "Noto Sans SC", system-ui, -apple-system, sans-serif
- font-display: "Fraunces", "Noto Serif SC", Georgia, serif
- font-mono: "IBM Plex Mono", ui-monospace, monospace
- max-width: 740

## Category colors
- major-release: #C85A3F
- industry-business: #4A7A48
- research-frontier: #6D5BA1
- tools-release: #C48A2E
- policy-regulation: #9E3C3C

## Typography scale
- h1: 44px / 1.15 / 650
- h2: 26px / 1.3 / 650
- h3: 19px / 1.4 / 600
- body: 17px / 1.75 / 400
- small: 14px / 1.55 / 400

## Voice
像在朋友圈里分享给懂行朋友的简报——专业但不冷淡，会在两条之间停下来说一句"这个值得点开看看"。避免科技媒体的标题党，也不故作克制；偶尔用一句俏皮话过渡。核心还是事实清楚 + 句子通顺。

## Hero
<section class="hero">
  <p class="hero__kicker">{{ date }} · AI Newsletter</p>
  <h1 class="hero__title">{{ title }}</h1>
  <p class="hero__lead">{{ lead_summary }}</p>
</section>

## Custom CSS
.hero { padding: 40px 28px; background: var(--surface); border-radius: calc(var(--radius) * 1.5); border: 1px solid var(--divider); margin-bottom: 36px; }
.hero__kicker { color: var(--accent); font-size: 13px; letter-spacing: 0.1em; margin: 0 0 10px; text-transform: uppercase; }
.hero__title { font-family: var(--font-display); font-size: 44px; line-height: 1.15; margin: 0 0 16px; color: var(--ink); }
.hero__lead { font-size: 18px; line-height: 1.7; color: var(--ink-muted); margin: 0; }
article h2 { font-family: var(--font-display); }
.category-tag { border-radius: 999px; padding: 2px 10px; }
