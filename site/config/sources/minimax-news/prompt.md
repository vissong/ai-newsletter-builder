# minimax-news

## Fetch

URL: https://www.minimax.io/news

Next.js / client-rendered page. WebFetch usually returns the hydrated HTML with the full list, but if it comes back empty fall back to Jina Reader: `https://r.jina.ai/https://www.minimax.io/news`.

## Extract

From the listing page, capture every news/blog entry:
- title: the entry headline (e.g. "MiniMax M2.7", "MiniMax Speech 2.8")
- url: absolute URL. Relative paths starting with `/news/` or `/models/` → prepend `https://www.minimax.io`
- "NEW" badge: note which entries are flagged `NEW` in the UI — these are the source's own signal of recency

**The listing page does NOT show dates.** To recover `published_at`, follow each candidate article URL (up to `follow_limit`) and extract the publish date from the article header. Format as ISO-8601.

Build the `summary` from the article intro (2-4 sentences: what model/product, key capabilities, what changed vs. the previous version).

**Time filter**: only keep items whose resolved `published_at` is within the last **24 hours**. Mark them as `recent: true`. Discard anything older than 24h or whose date cannot be resolved from the article page. MiniMax publishes 1-3 posts per month, so most days this source returns 0 items — that's expected.

## Edge Cases

- Product line names (M / Speech / Hailuo / Music) each have their own versioning. Don't collapse "Music 2.5+" and "Music 2.5" into one item — they are distinct releases.
- Flagship model posts (M2, M2.1, M2.7) categorize as `major-release`.
- Speech / Hailuo / Music posts also categorize as `major-release` when they are version bumps; as `tools-release` when they're API / developer-tooling posts.
- Content is in English; keep `title_original` verbatim. Translate title + summary to Chinese during Phase 3.5.
- **"NEW" badges on the listing are NOT reliable recency signals** — they persist long after the release date (e.g. a post flagged NEW may be 3+ months old). Always verify via the article page's date.
- Some product pages (e.g. `/models/text/m27`) do NOT carry a visible date. If an article is flagged NEW but the page has no date AND it does not appear on any reliable external feed, skip it rather than guessing — a prematurely-posted pre-announcement would end up wrong.
- If WebFetch returns an empty or JS-bootstrap-only response, use Jina Reader (`https://r.jina.ai/<url>`) as Tier 3 fallback.
