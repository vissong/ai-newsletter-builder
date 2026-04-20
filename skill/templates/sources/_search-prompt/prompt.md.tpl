# {{name}}

## Fetch

Search query: {{query}}

Template variables available: `{{today}}` and `{{yesterday}}` are resolved to
ISO dates at collection time.

Preferred search provider: {{provider_hint}}
If unavailable, fall back to: tavily-search → web-search → built-in WebSearch.

## Extract

From search results, extract each result as an item:
- title: the result title/headline
- url: the result URL
- published_at: from the result's date metadata if available
- summary: from the result snippet; if `follow_articles` is enabled, fetch the
  full page and produce a 2-4 sentence summary instead

## Edge Cases

- Blocked domains: {{blocked_domains}}
- Skip results that are aggregator pages (e.g., Google News compilations)
- Skip results older than time_window_hours
{{additional_edge_cases}}
