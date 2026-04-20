name: {{name}}
type: prompt
enabled: true
language: {{language}}
priority: 2
time_window_hours: 24
recent_hours: 24
timeout_seconds: 60

fetch_method: email

extract:
  item_limit: 30
  exclude_keywords: ["广告", "sponsored", "unsubscribe"]
