# meta-ai-blog

## Fetch

URL: https://ai.meta.com/blog/

No RSS feed available. Use WebFetch directly — the page returns readable HTML with article listings.

## Extract

From the page content, extract each blog post:
- title: the article headline
- url: the article link (absolute URL starting with `https://ai.meta.com/blog/`)
- published_at: the publication date (convert to ISO-8601)
- summary: the excerpt shown on the listing page; if too short, follow the article URL for a 2-4 sentence summary

**Time filter**: only keep items published within the last **168 hours** (7 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 168h.

## Edge Cases

- Meta AI blog covers research, products, and infrastructure — include all AI-related posts
- Some posts are case studies or partner spotlights; include them but they typically categorize as `industry-business`
- Publishing frequency is low (1-3 per week); empty results within 48h are normal
