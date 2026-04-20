#!/usr/bin/env bash
set -euo pipefail

echo "Running: tencent-news-cli hot --limit 20" >&2
RAW=$(tencent-news-cli hot --limit 20 --caller ai-newsletter-builder 2>&1) || {
  echo "error: tencent-news-cli hot failed" >&2
  exit 1
}

python3 -c "
import sys, re, json

text = sys.stdin.read().strip()
items = []
AI_KEYWORDS = ['AI', '人工智能', '大模型', 'GPT', 'LLM', '机器学习', '深度学习']

for m in re.finditer(
    r'\d+\.\s*标题[：:]\s*(.*?)\n\s*摘要[：:]\s*(.*?)\n\s*来源[：:]\s*(.*?)\n\s*发布时间[：:]\s*(.*?)\n\s*链接[：:]\s*(https?://\S+)',
    text, re.DOTALL
):
    title = m.group(1).strip()
    summary = m.group(2).strip()[:300]
    published_at = m.group(4).strip()
    url = m.group(5).strip()
    if title and url:
        combined = title + summary
        if any(kw in combined for kw in AI_KEYWORDS):
            items.append({'title': title, 'url': url, 'published_at': published_at, 'summary': summary, 'language': 'zh'})

json.dump(items, sys.stdout, ensure_ascii=False, indent=2)
" <<< "$RAW"
