# ai-bot-daily-news

## Fetch

URL: https://ai-bot.cn/daily-ai-news/

Use WebFetch directly — the page is server-rendered with article listings.
If WebFetch returns empty/blocked, fall back to Jina Reader: `https://r.jina.ai/https://ai-bot.cn/daily-ai-news/`

## Extract

From the page content, extract each AI news item:
- title: the article/tool headline
- url: the article link (absolute URL starting with `https://ai-bot.cn/`)
- published_at: relative date ("1 day ago", "3 days ago") — convert to ISO-8601 based on today's date
- summary: the description shown on the listing page (usually 1-2 sentences)

**Time filter**: only keep items published within the last **48 hours** (2 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 48h.

## Edge Cases

- **Ad filtering is critical**: this site mixes organic entries with paid promotions. Skip any item containing: "广告", "推广", "赞助", "VipCheap", "会员充值", "sponsored", "AD"
- Items about "充值" (recharge/subscription services) are ads, not news — skip them
- URLs are internal links to ai-bot.cn tool/news pages
- The page lists 100+ items; respect `item_limit` (20) and take the most recent ones
- Content is in Chinese (zh)
