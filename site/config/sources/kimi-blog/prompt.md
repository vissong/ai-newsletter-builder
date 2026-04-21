# kimi-blog

## Fetch

URL: https://www.kimi.com/blog/

No RSS feed available. Use WebFetch directly — the page is server-rendered and returns clean HTML listings.
No JS rendering or login needed.

## Extract

From the page content, extract each blog post:
- title: the post headline (as shown on the listing)
- url: the post link
  - relative paths starting with `/blog/` → prepend `https://www.kimi.com`
  - external links (github.com, huggingface.co, moonshotai.github.io, kvcache-ai) → keep as-is
- published_at: the date shown next to each entry (format YYYY/MM/DD → convert to ISO-8601)
- summary: the excerpt if shown; otherwise follow the article URL and write a 2-4 sentence summary covering the model/paper/product announced

**Time filter**: only keep items published within the last **24 hours**. Mark them as `recent: true`. Discard anything older than 24h. Moonshot/Kimi publishes 1-2 posts per month, so most days this source returns 0 items — that's expected.

## Edge Cases

- Many older entries point to external hosts (GitHub / Hugging Face / moonshotai.github.io). Keep the external URL as the canonical `url` and use it verbatim — don't rewrite to kimi.com.
- Posts often introduce flagship models (Kimi K2, K2.5, K2.6, Kimi K1.5, Kimi-Researcher) — these typically categorize as `major-release` during merge.
- Research posts like "MoBA: Mixture of Block Attention" or "Muon is Scalable for LLM Training" categorize as `research-frontier`.
- Content is in English; titles are model/paper names and kept verbatim in `title_original`. Translate to Chinese during Phase 3.5.
