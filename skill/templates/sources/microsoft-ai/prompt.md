# microsoft-ai

## Fetch

URL: https://news.microsoft.com/source/topics/ai/

Note: the original URL `https://blogs.microsoft.com/ai/` returns a 301 redirect to this address. Always use the redirected URL directly.

Use WebFetch. The page is server-rendered HTML.

## Extract

From the page content, extract each news article:
- title: the article headline
- url: the article link (absolute URL starting with `https://news.microsoft.com/`)
- published_at: the publication date if shown (may be absent — omit the field if not found)
- summary: the excerpt or description; if too short, follow the article URL for a 2-4 sentence summary

**Time filter**: only keep items published within the last **168 hours** (7 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 168h. If `published_at` is missing, include the item (cannot filter).

## Edge Cases

- The page mixes AI-specific posts with general Microsoft news tagged "AI" — include all
- published_at is often missing from the listing page; omit the field rather than guessing
- Many posts are Copilot case studies; include them (they categorize as `industry-business` or `tools-release`)
- Publishing frequency is moderate (2-4 per week)
