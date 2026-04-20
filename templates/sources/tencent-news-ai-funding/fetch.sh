#!/usr/bin/env bash
set -euo pipefail

QUERY="人工智能 融资"
LIMIT=15

echo "Running: tencent-news-cli search \"$QUERY\" --limit $LIMIT" >&2
RAW=$(tencent-news-cli search "$QUERY" --limit $LIMIT --caller ai-newsletter-builder 2>&1) || {
  echo "error: tencent-news-cli search failed" >&2
  exit 1
}

python3 -c "
import sys, re, json

text = sys.stdin.read().strip()
items = []

for m in re.finditer(
    r'\d+\.\s*标题[：:]\s*(.*?)\n\s*摘要[：:]\s*(.*?)\n\s*来源[：:]\s*(.*?)\n\s*发布时间[：:]\s*(.*?)\n\s*链接[：:]\s*(https?://\S+)',
    text, re.DOTALL
):
    title = m.group(1).strip()
    summary = m.group(2).strip()[:300]
    url = m.group(5).strip()
    if title and url:
        items.append({'title': title, 'url': url, 'summary': summary, 'language': 'zh'})

json.dump(items, sys.stdout, ensure_ascii=False, indent=2)
" <<< "$RAW"
