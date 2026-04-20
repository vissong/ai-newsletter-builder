# venturebeat-ai

## Fetch

URL: https://venturebeat.com/category/ai/

**Requires real browser (CDP)** — VentureBeat blocks automated HTTP requests (429/403). Standard WebFetch and Jina Reader both fail. Must use browser-based access (Tier 1).

Fetch steps:
1. Open the URL in a browser tab via CDP
2. Wait for page load
3. Extract article data from DOM using `article` elements or `h2 a` / `h3 a` heading links

If CDP is not available, the source should be skipped — do not attempt WebFetch or Jina, they will fail.

## Extract

From the AI category page, extract each article:
- title: the article headline (from `h2` or `h3` within each `article` element)
- url: the article permalink (absolute URL starting with `https://venturebeat.com/`)
- published_at: the `datetime` attribute from `<time>` elements — already in ISO-8601
- summary: the excerpt paragraph; if only image credits are shown, omit the summary

**Time filter**: only keep items published within the last **96 hours** (4 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 96h. VentureBeat does not publish on weekends, so a 48h window would miss Friday articles on Monday.

## Edge Cases

- **Rate limiting**: VentureBeat returns 429 for automated requests; only real browser access works
- **Sponsored content**: skip items where summary contains "Partner Content" or "Sponsored"
- **Image credits as summary**: many article cards show image credit text instead of a real excerpt — treat these as missing summaries
- Content is in English (en)
