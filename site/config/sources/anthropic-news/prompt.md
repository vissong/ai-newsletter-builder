# anthropic-news

## Fetch

URL: https://www.anthropic.com/news

No RSS feed available. Use WebFetch directly — the page is server-rendered and returns clean HTML.
No JS rendering or login needed.

## Extract

From the page content, extract each news/blog entry:
- title: the article headline
- url: the article link — relative paths start with `/news/` or `/research/`, prepend `https://www.anthropic.com`
- published_at: the publication date (convert to ISO-8601)
- summary: the excerpt shown on the listing page; if too short, follow the article URL for a 2-4 sentence summary

**Time filter**: only keep items published within the last **24 hours**. Mark them as `recent: true`. Discard anything older than 24h. Anthropic publishes 1-3 posts per week, so most days this source returns 0 items — that's expected.

## Edge Cases

- Some entries link to external sites (e.g. `/glasswing`) — include them, use the full URL as shown
- The page lists both product announcements and research posts; include all of them
- Anthropic publishes infrequently (1-3 posts per week); empty results within 48h are normal
