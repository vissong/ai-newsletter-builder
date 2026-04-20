name: {{name}}
type: prompt
enabled: true
language: {{language}}
priority: 2
time_window_hours: 24
recent_hours: 24
timeout_seconds: 30

fetch_method: web

extract:
  item_limit: 15
  follow_articles: true
  follow_limit: 10
  exclude_selectors: [".ad", ".sponsored"]
  exclude_keywords: ["广告", "推广", "sponsored"]
