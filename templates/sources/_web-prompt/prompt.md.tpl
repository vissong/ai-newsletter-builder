# {{name}}

## Fetch

URL: {{url}}
{{#rss}}
This URL serves an RSS/Atom feed. Use WebFetch directly on the feed URL.
No JS rendering needed.
{{/rss}}
{{#web}}
This is a standard web page. Use the tiered fallback chain:
1. WebFetch (plain HTTP)
2. Jina Reader (https://r.jina.ai/{{url}}) if WebFetch returns empty/blocked
3. WebSearch with site:{{domain}} as last resort
{{/web}}

## Extract

From the page content, extract each news item:
- title: the article headline
- url: the article link (absolute URL)
- published_at: the publication date/time (convert to ISO-8601)
- summary: 2-4 sentence factual summary

{{additional_extraction_notes}}

## Edge Cases

- Skip items that are ads or promotions (check for "sponsored", "推广", "广告")
- Skip items unrelated to AI/ML if the source covers broader topics
- If published_at is missing, omit the field (the collector uses fetched_at as fallback)
{{additional_edge_cases}}
