#!/usr/bin/env python3
"""
bigmodel-releases: Fetch new model releases from docs.bigmodel.cn/cn/update/new-releases

Parses the changelog page directly via curl (SSR page).
Each div.update has: id="YYYY-MM-DD", model name in <strong>, bullets in <li>, doc link.
Only outputs items published within --recent-hours (default 48).
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone


def parse_entries_from_html(html: str):
    """Parse changelog entries from the new-releases page HTML."""
    entries = []
    
    # Find all update container divs with date IDs
    pattern = re.compile(
        r'class="update[^"]*"\s+id="(\d{4}-\d{2}-\d{2})(?:-\d+)?"'
    )
    matches = list(pattern.finditer(html))
    
    for i, m in enumerate(matches):
        date_str = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else min(start + 5000, len(html))
        chunk = html[start:end]
        
        # Extract model name from <strong> tags
        strong_matches = re.findall(r'<strong[^>]*>([^<]+)</strong>', chunk)
        model_name = strong_matches[0].strip() if strong_matches else ''
        
        # Extract title from stripped text
        text = re.sub(r'<[^>]+>', ' ', chunk)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Pattern: "... YYYY-MM-DD Title Text emoji ModelName bullet1..."
        title_match = re.search(
            r'\d{4}-\d{2}-\d{2}\s+(.+?)(?:\s+' + re.escape(model_name) + r'\s)' if model_name 
            else r'\d{4}-\d{2}-\d{2}\s+(.{10,80})',
            text
        )
        
        title_text = ''
        if title_match:
            title_text = title_match.group(1).strip()
            # Remove trailing emoji
            title_text = re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]+\s*$', '', title_text).strip()
        
        if not title_text:
            title_text = f"{model_name} 发布" if model_name else f"智谱更新 {date_str}"
        
        # Extract doc link
        doc_link = ''
        link_match = re.search(r'href="(/cn/guide/[^"]+)"', chunk)
        if link_match:
            doc_link = f"https://docs.bigmodel.cn{link_match.group(1)}"
        
        # Extract bullet points for summary
        bullets = re.findall(r'<li[^>]*>(.*?)</li>', chunk, re.DOTALL)
        summary_parts = []
        for b in bullets[:4]:
            clean = re.sub(r'<[^>]+>', '', b).strip()
            if clean:
                summary_parts.append(clean)
        summary = '；'.join(summary_parts)
        if len(summary) > 300:
            summary = summary[:297] + '...'
        
        url = doc_link or f"https://docs.bigmodel.cn/cn/update/new-releases#{date_str}"
        page_url = f"https://docs.bigmodel.cn/cn/update/new-releases#{date_str}"
        
        entries.append({
            'date': date_str,
            'title': title_text,
            'model': model_name,
            'url': url,
            'summary': summary,
            'page_url': page_url,
        })
    
    return entries


def main():
    parser = argparse.ArgumentParser(description='Fetch bigmodel releases')
    parser.add_argument('--recent-hours', type=int, default=48,
                        help='Only include items from the last N hours (default: 48)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file path (default: stdout)')
    args = parser.parse_args()

    import subprocess
    
    url = 'https://docs.bigmodel.cn/cn/update/new-releases'
    try:
        result = subprocess.run(
            ['curl', '-sL', '--max-time', '15',
             '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
             url],
            capture_output=True, text=True, timeout=20
        )
        html = result.stdout
    except Exception:
        html = ''
    
    if not html or len(html) < 500:
        json.dump([], sys.stdout)
        return
    
    entries = parse_entries_from_html(html)
    
    if not entries:
        json.dump([], sys.stdout)
        return
    
    # Time filter
    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.recent_hours)
    now = datetime.now(timezone.utc)
    
    items = []
    for entry in entries:
        try:
            # Parse date as UTC+8 (China time)
            dt = datetime.strptime(entry['date'], '%Y-%m-%d')
            dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
            
            if dt.date() < cutoff.date():
                continue
                
            alt_urls = []
            if entry['page_url'] != entry['url']:
                alt_urls.append(entry['page_url'])
            
            items.append({
                'title': entry['title'],
                'url': entry['url'],
                'summary': entry['summary'],
                'published_at': dt.isoformat(),
                'fetched_at': now.isoformat(),
                'source': 'bigmodel-releases',
                'alt_urls': alt_urls,
            })
        except (ValueError, TypeError):
            continue
    
    output = json.dumps(items, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)


if __name__ == '__main__':
    main()
