# Design System: NIO (蔚来)

## 1. Visual Theme & Atmosphere

NIO's website is cinematic minimalism in service of intelligent electric luxury — a design system that communicates technological precision, premium craftsmanship, and the quiet confidence of a brand redefining what a car company looks like. Every section is a full-screen "frame," with automotive photography or video occupying the background while ultra-light typography floats above it. The result feels less like a website and more like a directed film about the future of mobility.

The typography is anchored by `BlueSkyStandard` — NIO's proprietary typeface, used at extreme light weights (300, even 100 for hero numerals) to create an airy, high-altitude elegance. A 64px headline at weight 300 whispers rather than shouts, conveying technological sophistication rather than raw power. The contrast with the rare weight-700 label creates a focused hierarchy without aggression.

The color story is built on duality. White (`#ffffff`) and warm off-white (`#f2f3ed`) anchor informational sections, while deep charcoal (`#151515`) and pure black (`#000000`) power the immersive product hero moments. The brand's signature Teal (`#00b3be`) appears as a precise, surgical accent — never on backgrounds, always reserved for brand marks and interactive highlights. On premium model pages like ET9, a warm Copper Gold (`#c49476`) elevates spec data into sculptural detail, while Deep Navy (`#335176`) grounds primary action buttons with authority.

What defines NIO's system uniquely is its commitment to angular geometry: zero border-radius everywhere. Not a single rounded corner appears on any button, card, or container. This industrial sharpness, combined with the 160px section padding that creates enormous breathing room, produces a tension between the vast and the precise — exactly the tension at the heart of NIO's brand.

**Key Characteristics:**
- `BlueSkyStandard` proprietary typeface, ultra-light (300/100) for display — precision whispered, not shouted
- Zero border-radius, zero exceptions — angular industrial geometry throughout
- Full-screen cinematic sections: video/photography backgrounds, floating white text
- Transparent-to-frosted-glass Header: `rgba(255,255,255,0)` → `rgba(255,255,255,0.65)` + backdrop blur on scroll
- Brand Teal (`#00b3be`) as surgical accent — never decorative, never background
- Copper Gold (`#c49476`) on ET9 and premium contexts — warmth as premium signal
- 160px section top padding — monumental whitespace as a design element
- Dual theme: white/warm-white for information, near-black (`#151515`) for immersion

## 2. Color Palette & Roles

### Brand Colors
- **NIO Teal** (`#00b3be`): Primary brand accent. Logos, brand marks, hover highlights. Never on large surfaces.
- **Teal Light** (`#21c9cc`): Hover/active state for Teal elements
- **Teal Pale** (`#e5f9f9`): Teal tint for backgrounds in light brand contexts

### Backgrounds
- **Pure White** (`#ffffff`): Default page background, cards, navigation dropdown
- **Warm Off-White** (`#f2f3ed`): Alternate section backgrounds — warmer, organic, non-sterile
- **Deep Charcoal** (`#151515`): Premium model hero backgrounds (ET9, flagship vehicles)
- **Pure Black** (`#000000`): Full-immersion hero carousels, video sections

### Interactive
- **Deep Navy** (`#335176`): Primary CTA button fill — authority, trustworthiness
- **Star Gray** (`#5577a1`): Secondary interactive elements in dark contexts

### Accent / Premium
- **Copper Gold** (`#c49476`): ET9 and premium tier — spec numbers, luxury detail highlights. Warmth as elevation signal.

### Text
- **Black** (`#000000`): Primary text on light backgrounds
- **Charcoal** (`#111111`): Header and navigation text
- **Secondary** (`#9c9c9c`): Captions, metadata, secondary labels
- **Spec Label** (`#979797`): Technical specification labels
- **Footer Links** (`#5a5a5a`): Footer secondary navigation
- **White** (`#ffffff`): All text on dark/charcoal backgrounds

### Neutral Scale (CSS Variables: `--nio-web-*`)
| Token | Hex | Use |
|-------|-----|-----|
| gray-1 | `#ffffff` | Surfaces |
| gray-2 | `#f6f7fa` | Subtle backgrounds |
| gray-3 | `#e6e7ec` | Dividers |
| gray-4 | `#ced0d8` | Disabled states |
| gray-6 | `#9c9fac` | Placeholder text |
| gray-8 | `#595e72` | Secondary body |
| gray-9 | `#040b29` | Near-black text |

### Header States
- **Transparent** (`rgba(255,255,255,0)`): Default over hero imagery
- **Frosted** (`rgba(255,255,255,0.65)` + `backdrop-filter: blur`): On scroll or nav open

## 3. Typography Rules

### Font Family
- **Primary**: `BlueSkyStandard` (NIO proprietary), fallbacks: `"Helvetica Neue", Helvetica, Arial, "PingFang SC", "Hiragino Sans GB", "Heiti SC", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif`
- NIO's custom typeface is Latin-first with comprehensive CJK fallbacks for Chinese content.

### Hierarchy

| Role | Size | Weight | Line Height | Notes |
|------|------|--------|-------------|-------|
| Super Display (ET9 Hero) | 64px | 300 (Light) | 90px | Flagship model titles — maximum airy elegance |
| Display Hero | 40px | 300 (Light) | 56px | Main section hero headlines |
| Sub-Hero | 28px | 400 (Regular) | 44.8px | Hero descriptors, section sub-headlines |
| Section Title | 20px | 400 (Regular) | 28px | H3 section headings |
| Card Title | 18px | 700 (Bold) | 28.8px | Product card names, feature titles |
| Small Card Title | 14px | 700 (Bold) | 16.8px | Compact card labels |
| Category Tag | 12px | 700 (Bold) | — | Navigation labels, filter tags |
| Navigation Link | 12px | 400 (Regular) | — | Header and sub-nav links |
| Body (Large) | 16px | 400 (Regular) | — | Standard reading text |
| Body | 14px | 400 (Regular) | 22.4px | Default body copy |
| Button (Medium) | 14px | 400 (Regular) | — | Standard button text |
| Button (Small) | 12px | 400 (Regular) | 30px | Compact button text |
| Spec Numeral | 48px | 100 (Thin) | — | ET9 technical specifications — extreme precision |
| Footer | 12–14px | 400 (Regular) | — | Footer links and legal |

### Principles
- **Ultra-light as luxury signal**: Hero headlines at weight 300 (and spec numerals at weight 100) create a refined, high-altitude elegance. Heavy weight appears only in compact labels (700). The system deliberately avoids the 500–600 medium range.
- **Scale contrast over weight contrast**: NIO relies on dramatic size differences (64px vs 12px) rather than bold/regular contrast to create hierarchy. The type palette is intentionally weight-restrained.
- **Generous line-heights**: Unlike BMW's compressed system, NIO's line-heights are proportionally open — 90px for 64px type (1.40), 56px for 40px (1.40) — creating an airy, spacious reading rhythm.
- **Latin typeface for a Chinese brand**: BlueSkyStandard is a Latin-designed custom typeface with CJK fallbacks. The brand positions itself as global-first.

## 4. Component Stylings

### Buttons

**Ghost Button (Primary UI — most common)**
- Background: `transparent`
- Border: `1px solid currentColor` (adapts to context: white on dark, black on light)
- Text (dark context): `#ffffff`, Font: BlueSkyStandard 12px weight 400
- Text (light context): `#000f16`, Font: BlueSkyStandard 12px/14px weight 400
- Padding: `0 14px` (small), `0 15px` (medium)
- Height: 30–32px (small), 40px (medium), Width: ~88px
- Border-radius: **`0px`** — sharp rectangle, no exceptions
- Hover: `transition: 0.2s ease-in`, border/text color intensifies

**Primary Button (CTA — Deep Navy)**
- Background: `#335176` (Deep Navy)
- Text: `#ffffff`
- Height: 32px, Width: ~72px, Padding: `9.6px 12px`
- Border-radius: **`0px`**
- Font: 12px weight 400
- Use: Purchase flow, primary vehicle CTAs

**HyperButton (ET9 Hero CTA)**
- Background: `transparent`
- Border: `1px solid #ffffff`
- Height: 40px, Width: 88–144px, Padding: `0 15px`
- Border-radius: **`0px`**
- Font: 14px weight 400, white text
- Use: Flagship model hero CTAs only

**"预约试驾" (Test Drive) Header Button**
- Background: `transparent`
- Dimensions: `74×30px`, Padding: `0 14px`
- Border: `1px solid #ffffff` (on dark hero) / `1px solid #000000` (on scroll)
- Border-radius: **`0px`**
- Font: 12px, smooth `transition: 0.2s ease-in`

### Navigation (Header)

- Height: `64px`, `position: fixed`, `z-index: 100`
- Default background: `rgba(255,255,255,0)` — fully transparent, sits over hero imagery
- Scroll/hover background: `rgba(255,255,255,0.65)` + `backdrop-filter: blur()`
- Dropdown: `#ffffff` solid, `padding: 32px 90px 24–59px`
- Nav links: 12px BlueSkyStandard weight 400, color `#111111`
- Bottom border on dropdown: `1px solid #efefef`
- Logo: Minimal, `~20×18.8px` — almost invisible, brand confidence through restraint
- Right CTA: "预约试驾" ghost button

### In-Page Anchor Navigation (Elevator — Sticky Sub-Nav)

- Height: `44px`
- Background: `#ffffff` with `1px solid #efefef` bottom border
- Font: 12px, neutral gray
- Becomes sticky as user scrolls through vehicle detail page
- Contains section jumps (Performance, Interior, Technology, etc.) + "立即购买" primary button

### Cards & Containers

- Background: transparent — inherits parent section background
- Border-radius: **`0px`** — sharp corners, no exceptions
- No box-shadow on cards (depth through background contrast, not elevation)
- No borders on cards (whitespace separates, not lines)
- Section padding: `160px 80px 0` — enormous top breathing room
- Grid gap: `40px` horizontal

### Hero Sections

**Homepage Hero (NewHero)**
- Full viewport width, height `628px`
- Video or full-bleed photography as background
- Text color: `#ffffff` (always white, never black on hero)
- Headline description: 28px weight 400, white
- Button group: bottom-aligned, ghost buttons

**ET9/Flagship Hero (TopHero)**
- Full viewport width, height `713px`
- Background: `#151515` near-black
- Model name as display headline, ultra-light weight
- Button group: 40px height, horizontal flex layout

### Image Treatment

- Full-bleed vehicle photography — no cropping, no decorative frames
- Vehicle on solid or gradient background — object isolated from environment
- Photography carries emotional weight; UI components are intentionally invisible
- ET9: Mirror-finish photography, extreme close-ups of material details

## 5. Layout Principles

### Spacing System
- Base unit: 8px
- Scale: 8px, 12px, 14px, 15px, 16px, 20px, 24px, 32px, 40px, 64px, 75px, 80px, 90px, 110px, 160px

### Grid & Container
- Max-width: `1920px` (full ultra-wide support)
- Content grid: 12 columns (`niogrid`), with 10-column active content area on large screens (`grid-col-lg-10`)
- Horizontal padding: `80px` left/right (replaces gutter-based constraints)
- Grid gap: `40px` horizontal
- No fixed max-content-width container — layout is fluid and full-width

### Whitespace Philosophy
- **Monumental breathing room**: 160px top padding on sections is not whitespace — it's a statement. Each section is given the gravity of physical space in a showroom.
- **Full-screen cinema**: Each section is a "scene." The transition between scenes (between vehicle models, between brand stories) is managed by full-screen background color changes, never by cards or borders.
- **Angular compression**: Despite the massive outer spacing, internal elements (buttons, type, labels) are tightly set. The contrast between vast outer space and precise inner density creates the NIO aesthetic tension.

### Border Radius Scale
- **None.** Zero border-radius throughout the entire system. Every container, button, card, image treatment, and UI element is a sharp-cornered rectangle. This is non-negotiable and defines NIO's industrial-luxury identity.

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Photography (Level 0) | Full-bleed vehicle imagery / video | Hero section backgrounds |
| Flat White (Level 1) | `#ffffff` solid surface, no shadow | Content section backgrounds |
| Flat Off-White (Level 1b) | `#f2f3ed` warm surface, no shadow | Alternate informational sections |
| Deep Black (Level 0) | `#151515` / `#000000` solid | Premium/immersive hero sections |
| Frosted Header | `rgba(255,255,255,0.65)` + `backdrop-filter: blur` | Sticky nav on scroll |
| Sticky Sub-Nav | `#ffffff` + `1px solid #efefef` bottom | In-page section navigation |

**Shadow Philosophy**: NIO uses zero shadows. Elevation is communicated entirely through background color contrast — the shift from `#151515` (premium hero) to `#ffffff` (informational content) to `#f2f3ed` (warm feature section) creates a depth map without any synthetic shadow. This is consistent with the zero-decoration philosophy: photography and color blocks do the depth work.

## 7. Do's and Don'ts

### Do
- Use `BlueSkyStandard` weight 300 for all large display text — light weight IS the NIO aesthetic
- Keep ALL corners at 0px — angular geometry is absolute and non-negotiable
- Apply the transparent→frosted-glass header transition — it is core to the immersive scrolling experience
- Use 160px top section padding to create monumental breathing room
- Use NIO Teal (`#00b3be`) only for brand marks and precise interactive accents — never as backgrounds
- Use Copper Gold (`#c49476`) for premium/ET9 contexts — it signals luxury tier
- Let vehicle photography be the primary visual element — every UI component should retreat
- Use Deep Navy (`#335176`) for primary purchase/action buttons — it conveys authority
- Maintain dual theme awareness: white for information, `#151515` for immersion

### Don't
- Don't add border-radius to anything — even 2px rounds are a violation of the design language
- Don't use weight 500 or 600 — the scale skips from 400 (Regular) to 700 (Bold), nothing in between
- Don't use Teal as a background fill or large surface color — it is an accent only
- Don't add shadows or borders to cards — depth comes from background contrast, not elevation
- Don't use right-aligned or centered body text — NIO body copy reads left to right
- Don't reduce section padding below 80px horizontal — the white space is structural
- Don't introduce additional accent colors beyond Teal and Copper Gold
- Don't let any UI element compete visually with vehicle photography
- Don't use opaque header by default — the transparent/frosted state on scroll is the expected behavior
- Don't use weight 100 (Thin) outside of technical specification numerals

## 8. Responsive Behavior

### Breakpoints
| Name | Width | Key Changes |
|------|-------|-------------|
| Mobile | <375px | Single column, minimum supported |
| Mobile | 375–480px | Full-width sections, stacked layout |
| Mobile Large | 480–640px | Larger imagery, adjusted type scale |
| Tablet Small | 640–768px | 2-column content begins |
| Tablet | 768–1024px | Sub-navigation visible |
| Desktop Small | 1024–1280px | 10-column grid activates |
| Desktop | 1280–1440px | Full layout, standard experience |
| Large Desktop | 1440–1920px | Max-width 1920px, expanded margins |

### Collapsing Strategy
- **Hero sections**: Full-bleed maintained at all sizes; headline scales from 64px → 40px → 28px
- **Navigation**: Full horizontal header → hamburger menu on mobile
- **In-page anchor nav**: Scrollable horizontal tabs on mobile, full horizontal bar on desktop
- **Section padding**: `160px 80px` → `80px 24px` on mobile — breathing room scales with screen
- **Grid**: 10-column → 2-column → 1-column, gap reduces proportionally
- **Buttons**: Maintain sharp corners and consistent padding at all breakpoints
- **Photography**: Full-bleed maintained; aspect ratio preserved, never cropped on desktop

### Touch Targets
- All buttons maintain minimum `44px` touch height in mobile contexts
- Ghost button height 40px (medium) is the mobile standard
- Header navigation collapses, ensuring tap targets are adequately spaced

## 9. Agent Prompt Guide

### Quick Color Reference
- **Background (default)**: `#ffffff`
- **Background (warm section)**: `#f2f3ed`
- **Background (premium/dark)**: `#151515`
- **Background (full black)**: `#000000`
- **Text (on light)**: `#000000` / `#111111`
- **Text (on dark)**: `#ffffff`
- **Secondary text**: `#9c9c9c`
- **Brand accent (Teal)**: `#00b3be`
- **Primary button (Navy)**: `#335176`
- **Premium accent (Copper)**: `#c49476`
- **Header frosted**: `rgba(255,255,255,0.65)` + blur

### Example Component Prompts
- "Create a NIO hero section: full-viewport-height, background `#151515`. Headline at 64px BlueSkyStandard weight 300, line-height 90px, color `#ffffff`. Sub-headline at 28px weight 400, line-height 44.8px, white. Two ghost buttons side by side: 88×40px, `border: 1px solid #ffffff`, `border-radius: 0`, 14px white text."
- "Design a NIO navigation header: height 64px, `position: fixed`, default `background: rgba(255,255,255,0)`. On scroll: `background: rgba(255,255,255,0.65)` + `backdrop-filter: blur(10px)`. Nav links: 12px BlueSkyStandard weight 400, color `#111111`. Right: '预约试驾' button `74×30px`, `border: 1px solid #000000`, `border-radius: 0`, 12px."
- "Build a NIO vehicle card: no border-radius, no shadow, no border. Full-bleed vehicle photograph top. Model name: 18px BlueSkyStandard weight 700, color `#000000`. Category label: 12px weight 700, color `#9c9c9c`. Ghost CTA button: `88×32px`, `border: 1px solid #000000`, `border-radius: 0`, 12px."
- "Create an ET9 spec section: background `#151515`. Spec number: 48px BlueSkyStandard weight 100, color `#c49476` (Copper Gold). Spec label: 12px weight 400, color `#979797`. Section title: 20px weight 400, white. Sharp corners everywhere."
- "Design a NIO content section with warm background: `background: #f2f3ed`. Section top padding: 160px. Content left/right padding: 80px. Heading: 40px BlueSkyStandard weight 300, line-height 56px, color `#000000`. Body: 14px weight 400, line-height 22.4px. No shadows, no borders, no border-radius."

### Iteration Guide
1. **Zero border-radius** — this is absolute. No exceptions across any component or scale
2. **Weight extremes only**: 100 (spec numerals), 300 (display), 400 (body/nav), 700 (labels) — skip 500–600
3. **Teal sparingly**: `#00b3be` is a surgical accent, not a palette color
4. **Dual background awareness**: every component needs both a light (`#ffffff`) and dark (`#151515`) variant
5. **Photography dominance**: UI elements should be invisible against the vehicle. If you can see the UI too clearly, it's too prominent
6. **160px top padding**: this is structural — it creates the monumental NIO scale
7. **Transparent header first**: the frosted-glass state is a scroll-triggered enhancement, not the default
8. **Copper Gold for premium tier**: use `#c49476` to signal ET9/flagship context, never for standard models
