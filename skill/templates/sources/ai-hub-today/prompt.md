# ai-hub-today

## Fetch

Prefer the date-pinned URL over the root:
- Primary: `https://ai.hubtoday.app/{{year-month}}/{{date}}` (e.g. `https://ai.hubtoday.app/2026-04/2026-04-20`)
- Fallback: `https://ai.hubtoday.app/`

The `{{year-month}}` and `{{date}}` template variables are resolved at collection time.

Use WebFetch directly — the page is server-rendered and returns clean content. The daily digest page is pre-curated (10-20 items).

## Extract

From the page content, extract each AI news item:
- title: the headline (usually in Chinese, one-line summary format)
- url: the linked article URL if provided; if only a relative path, prepend `https://ai.hubtoday.app`
- published_at: use the date from the URL path as the publication date (e.g. `2026-04-20`)
- summary: the brief description shown for each item

**Time filter**: only keep items published within the last **48 hours** (2 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 48h.

## Edge Cases

- The root URL shows whatever the current front page is; the date URL is the actual daily digest
- If the date URL returns a 404 (no digest for that day), fall back to the root URL
- Items are pre-curated aggregations — they may overlap with other sources (techcrunch, openai blog, etc.); this is fine, Phase 3 dedup handles it
- Content is in Chinese (zh)
