# 36kr-ai

## Fetch

URL: https://36kr.com/search/articles/AI

**This source requires a real browser** — 36Kr uses heavy JavaScript rendering. All automated fetch tiers fail:
- WebFetch: returns empty/minimal HTML shell with no article content
- Jina Reader: ECONNREFUSED
- WebSearch fallback: limited to search snippets only

When `browser-use` or equivalent CDP-capable skill becomes available, use it to load the page, wait for JS rendering to complete, and extract content from the rendered DOM.

## Extract

From the search results page, extract each article:
- title: the article headline
- url: the article link — use absolute URL (prepend `https://36kr.com` if relative)
- published_at: the article timestamp — convert to ISO-8601
- summary: the article excerpt/snippet shown in search results

**Time filter**: only keep items published within the last **48 hours** (2 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 48h.

## Edge Cases

- **JS rendering required**: The page HTML is a skeleton; all content is loaded via JavaScript after initial page load
- **Ad filtering**: skip items containing "广告", "推广", "赞助" in the title or snippet
- Content is in Chinese (zh)
