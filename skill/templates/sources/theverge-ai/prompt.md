# theverge-ai

## Fetch

URL: https://www.theverge.com/ai-artificial-intelligence

**This source requires a real browser** — The Verge aggressively blocks non-browser requests. All automated fetch tiers fail:
- WebFetch: returns 403 Forbidden
- Jina Reader: ECONNREFUSED
- WebSearch fallback: limited to search snippets only

When `browser-use` or equivalent CDP-capable skill becomes available, use it to load the page and extract content from the rendered DOM.

## Extract

From the AI section page, extract each article:
- title: the article headline
- url: the article permalink (absolute URL starting with `https://www.theverge.com/`)
- published_at: the article timestamp — convert to ISO-8601
- summary: the article deck/subtitle or first paragraph

**Time filter**: only keep items published within the last **48 hours** (2 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 48h.

## Edge Cases

- **Anti-scraping**: The Verge uses aggressive bot detection; standard HTTP fetches return 403 or empty content
- **Dynamic content**: Page uses client-side rendering for article listings; static HTML fetch misses most content
- Content is in English (en)
