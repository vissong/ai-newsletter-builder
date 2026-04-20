#!/usr/bin/env python3
"""Fetch AI newsletter emails from Gmail via gog CLI.

Outputs JSON array to stdout. Each email becomes one item with subject as title
and body text as summary. Requires: gog CLI authenticated.
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser


GMAIL_QUERY = "newer_than:2d label:AI-Newsletter"
MAX_RESULTS = 30
TIME_WINDOW_HOURS = 48
RECENT_HOURS = 24

SKIP_URL_PATTERNS = [
    "cdn-cgi/image/", "beehiiv.com/cdn-cgi/", "/unsubscribe", "/pixel",
    "list-manage.com/track/", "mailchimp.com/track/", "email.mg.",
    "open.substack.com/api/", "fonts.googleapis.com",
    ".png", ".jpg", ".gif", ".svg", ".ico",
]

ARTICLE_URL_PATTERNS = [
    "substack.com/p/", "every.to/p/", "every.to/c/", "latent.space/p/",
    "langchain.com/", "github.com/", "arxiv.org/",
    "openai.com/", "anthropic.com/", "deepmind.google/",
    "huggingface.co/", "techcrunch.com/", "theverge.com/",
    "turingpost.com/p/", "theaibreak.com/",
]


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = False
        self._links = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head"):
            self._skip = True
        if tag == "a" and not self._skip:
            for name, val in attrs:
                if name == "href" and val and not val.startswith("#") and not val.startswith("mailto:"):
                    self._links.append(val)
        if tag in ("br", "p", "div", "h1", "h2", "h3", "h4", "li", "tr", "blockquote"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head"):
            self._skip = False
        if tag in ("p", "div", "h1", "h2", "h3", "h4", "li", "blockquote"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)

    def get_text(self):
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def get_links(self):
        return self._links


def strip_html(html):
    stripper = HTMLStripper()
    stripper.feed(html)
    return stripper.get_text(), stripper.get_links()


def run_gog(*args):
    result = subprocess.run(
        ["gog"] + list(args),
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"gog failed: {result.stderr.strip()}")
    return result.stdout


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except Exception:
        pass
    return None


def is_skip_url(url):
    return any(pat in url for pat in SKIP_URL_PATTERNS)


def pick_best_url(urls, subject):
    cleaned = []
    for u in urls:
        u = re.sub(r'[)\]_]+$', '', u)
        u = u.split('?utm_')[0]
        cleaned.append(u)

    for u in cleaned:
        if any(pat in u for pat in ARTICLE_URL_PATTERNS):
            return u
    for u in cleaned:
        if u.startswith("https://") and len(u) > 30:
            return u
    return cleaned[0] if cleaned else ""


def extract_summary(text):
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f\ufeff]', '', text)
    text = re.sub(r'‌', '', text)
    skip_starts = (
        "View this", "Unsubscribe", "Update your", "Manage your",
        "Was this email", "Sign up", "Click here", "If you",
        "Copyright", "All rights", "---", "===",
        "forwarded to you", "Add your", "Share this",
    )
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for para in paragraphs:
        if len(para) < 60:
            continue
        if any(para.startswith(s) for s in skip_starts):
            continue
        clean = re.sub(r"\[https?://[^\]]+\]", "", para).strip()
        if len(clean) < 40:
            continue
        return clean[:400]
    return ""


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=TIME_WINDOW_HOURS)
    recent_cutoff = now - timedelta(hours=RECENT_HOURS)

    try:
        raw = run_gog("gmail", "search", GMAIL_QUERY, "--max", str(MAX_RESULTS), "--json")
        search_data = json.loads(raw)
    except Exception as e:
        print(f"error searching gmail: {e}", file=sys.stderr)
        sys.exit(1)

    threads = search_data.get("threads", [])
    if not threads:
        json.dump([], sys.stdout)
        print("\nNo emails found", file=sys.stderr)
        return

    results = []
    for thread in threads:
        msg_id = thread["id"]
        try:
            msg_raw = run_gog("gmail", "get", msg_id, "--format", "full", "--json")
            msg = json.loads(msg_raw)
        except Exception as e:
            print(f"warning: failed to get message {msg_id}: {e}", file=sys.stderr)
            continue

        headers = msg.get("headers", {})
        subject = headers.get("Subject", headers.get("subject", ""))
        from_addr = headers.get("From", headers.get("from", ""))
        date_str = headers.get("Date", headers.get("date", ""))
        body = msg.get("body", "")

        pub = parse_date(date_str)
        if pub and pub < cutoff:
            continue

        is_html = body.strip()[:10].startswith("<!") or body.strip()[:10].lower().startswith("<html")
        if is_html:
            body_text, html_links = strip_html(body)
            all_urls = [u for u in html_links if not is_skip_url(u)]
        else:
            body_text = body
            all_urls = [u for u in re.findall(r"https?://[^\s\]\"'>]+", body_text) if not is_skip_url(u)]

        main_url = pick_best_url(all_urls, subject) if all_urls else ""
        summary = extract_summary(body_text)

        entry = {
            "title": subject,
            "url": main_url,
            "published_at": pub.isoformat() if pub else date_str,
            "summary": summary,
            "source_detail": from_addr,
            "language": "en",
            "fetched_at": now.isoformat(),
        }
        if pub and pub >= recent_cutoff:
            entry["recent"] = True
        results.append(entry)

    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    print(file=sys.stderr)
    print(f"Fetched {len(results)} items from Gmail AI Newsletter", file=sys.stderr)


if __name__ == "__main__":
    main()
