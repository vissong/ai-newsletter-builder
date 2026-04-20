# ai-bot-tools

## Fetch

URL: https://ai-bot.cn/ai-tools/

Use WebFetch directly — the page is server-rendered.
If WebFetch returns empty/blocked, fall back to Jina Reader: `https://r.jina.ai/https://ai-bot.cn/ai-tools/`

## Extract

From the page content, extract each AI tool entry:
- title: the tool name/headline
- url: the tool page link (absolute URL starting with `https://ai-bot.cn/`)
- published_at: relative date if shown — convert to ISO-8601; omit if not available
- summary: the tool description (usually 1-2 sentences about what the tool does)

**Time filter**: only keep items published within the last **168 hours** (7 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 168h. If no date is shown, include the item (cannot filter).

## Edge Cases

- **Ad filtering**: same rules as ai-bot-daily-news — skip "广告", "推广", "赞助", "VipCheap", "会员充值"
- This is a tools directory, not time-sensitive news — entries are mostly static product/tool listings
- Almost all items categorize as `tools-release`; when merging, these should be lower priority than actual launch announcements from company blogs
- time_window is set to 168h because new tools are added infrequently
- Content is in Chinese (zh)
