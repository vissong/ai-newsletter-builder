# gmail-ai-newsletter

## Fetch

Uses `gog` CLI to search Gmail for emails labeled `AI-Newsletter` within the time window.

```
gog gmail search "newer_than:2d label:AI-Newsletter" --max 30 --json
```

For each thread, fetch the message body:
```
gog gmail get <messageId> --format full --json
```

The body may be plain text (Substack newsletters) or HTML (marketing emails). The fetch script handles both formats — HTML is stripped to text before extraction.

## Extract

Each email may contain one or more distinct AI news items. Extract:
- title: the subject line, or individual story headlines within the email
- url: links to original articles mentioned in the email body
- published_at: the email Date header, converted to ISO-8601
- summary: the key paragraph or story summary from the email

When a newsletter email contains multiple stories (common for digest-format newsletters like AINews), split them into separate items so cross-source dedup works correctly.

**Time filter**: only keep emails received within the last **48 hours** (2 days). Mark items from the last **24 hours** as `recent: true`. Discard anything older than 48h.

## Edge Cases

- **Auth required**: `gog` must be authenticated (`gog auth login`). If auth fails, the source should report an error, not silently return empty.
- **HTML emails**: strip HTML tags before extracting content; preserve link URLs
- **Digest newsletters**: AINews, Turing Post etc. pack 5-15 stories per email — split into individual items
- **Single-story newsletters**: Every, LangChain etc. are usually one topic per email — treat as one item
- Content is primarily in English (en), but some newsletters may be bilingual
