# weixin-sogou

## Fetch

URL: https://weixin.sogou.com/weixin?type=2&query=AI

Use WebFetch directly — the page usually returns parseable HTML, though Sogou occasionally serves a captcha (~70-80% success rate).

If WebFetch returns a captcha page or empty content:
1. Try Jina Reader: `https://r.jina.ai/https://weixin.sogou.com/weixin?type=2&query=AI`
2. If still blocked, fall back to WebSearch: `site:mp.weixin.qq.com AI`

## Extract

From the search results page, extract each WeChat article:
- title: the article headline
- url: the article link — **Sogou wraps URLs in encrypted redirects**; extract the final `mp.weixin.qq.com` URL if possible, otherwise use the Sogou redirect URL as-is
- published_at: shown as relative time ("X天前", "X小时前") — convert to ISO-8601; omit if not parseable
- summary: the snippet text shown under each result

**Time filter**: only keep items published within the last **48 hours** (2 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 48h. Relative times like "3天前" (3 days ago) exceed 48h — discard them.

Note the `preferred_accounts` list in source.yaml (机器之心, 新智元, 量子位, etc.) — items from these accounts can be highlighted by the renderer, but do not skip items from other accounts.

## Edge Cases

- **Captcha**: Sogou may serve a verification page under heavy polling. If the response contains "请输入验证码" or similar, the fetch has failed — do not extract items from the captcha page
- **Encrypted URLs**: Sogou redirect links (long base64-like paths) are opaque; they work for clicking but not for dedup. If possible, resolve the redirect to get the real `mp.weixin.qq.com` URL
- **Ad filtering**: skip items containing "广告", "推广", "赞助" in the title or snippet
- Content is in Chinese (zh)
