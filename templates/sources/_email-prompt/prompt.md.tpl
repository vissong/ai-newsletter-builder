# {{name}}

## Fetch

Provider: {{provider}}
CLI: {{cli}} (must be installed and authenticated)
Query: {{query}}

Run the CLI to search for matching emails:
```
{{cli}} {{search_command}} --query "{{query}}" --limit {{max_messages}} --json
```

For each matching message, fetch the full body:
```
{{cli}} {{get_command}} <message-id> --format markdown
```

## Extract

Each email may contain one or more distinct news items. Split multi-story
newsletter emails into separate items.

For each item:
- title: the story headline (from email subject or inline heading)
- url: the linked article URL (extract from email body)
- published_at: the email's received date
- summary: 2-4 sentence summary of the story

## Edge Cases

- Strip quoted reply chains (lines starting with >)
- Skip promotional/ad sections in newsletter emails
- If an email has no extractable links, skip it
- Some newsletters embed tracking URLs — extract the final destination URL
{{additional_edge_cases}}
