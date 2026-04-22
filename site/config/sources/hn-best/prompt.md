# hn-best

## Fetch

Run the local helper script to pull the raw beststories payload — no web scraping, no fallback chain needed:

```bash
python3 site/config/sources/hn-best/fetch.py --limit 80 --min-score 50
```

The script queries the HN Firebase API (`/beststories.json` + `/item/<id>.json` in parallel) and prints a JSON array of story objects with fields: `title`, `url`, `published_at`, `summary`, `language`, `hn_id`, `hn_url`, `hn_score`, `hn_comments`.

If the script exits non-zero or returns an empty array, fall back to calling the API directly via `curl` — do NOT try web scraping news.ycombinator.com.

## Filter (AI only)

The raw output mixes AI stories with general tech / science / politics / hobby content. Keep **only items that are clearly about AI / ML / LLMs / agents / AI policy / AI industry**. Drop everything else.

### Keep if the title or URL clearly involves any of:

- AI models or labs: OpenAI, Anthropic, Google DeepMind, Meta AI, Mistral, xAI, Cohere, Kimi, Qwen, DeepSeek, etc.
- Named model families: GPT, Claude, Gemini, Llama, Mistral, Kimi, Qwen, Mixtral, Phi, etc.
- AI-native products & concepts: LLM, chatbot, agent, copilot, RAG, fine-tune, embedding, vector DB, MCP, vibe coding, prompt engineering
- AI developer tooling: Cursor, Windsurf, Claude Code, Copilot, Cody, Continue, Aider, LangChain, LlamaIndex, vLLM, Ollama
- AI infra & hardware in the AI context: NVIDIA / AMD GPUs explicitly tied to training/inference, TPU, inference engines
- AI research topics: transformers, diffusion, reinforcement learning on language models, alignment, interpretability, benchmarks (MMLU, GSM8K, SWE-bench…)
- AI policy & regulation: EU AI Act, export controls on AI chips, AI safety legislation, AI-related lawsuits
- AI business: AI company funding rounds, AI product launches, AI acquisitions, AI layoffs driven by automation

### Drop (do NOT keep) if the item is:

- Generic programming, OS, browser, networking, security stories with no AI angle
- General science / space / biology / hardware reviews with no AI angle
- Retro computing, history pieces, vintage tech, game design
- Personal essays, career rants, hiring threads, Ask HN / Show HN for non-AI projects
- Politics, economics, geopolitics without a primary AI framing
- Open source projects that are not AI-specific (e.g. a new JS bundler, Linux tool)

When in doubt, **lean towards dropping** — this feed is meant to be a high-signal AI slice of HN.

### Cross-check by visiting the URL

If the title is ambiguous (e.g. `"A printing press for biological data"`, `"Rspack 2.0"`, `"Laws of Software Engineering"`), skim the linked page via WebFetch / Jina Reader to decide. If the AI angle is secondary or forced, drop it.

## Output

Return a JSON array where each item is the original story object **unchanged** (same fields the script produced) plus:

- Preserve `language: "en"` — translation to Chinese happens later in Phase 3.5
- Preserve `published_at` as-is (ISO-8601 from the script)
- Preserve `hn_id`, `hn_url`, `hn_score`, `hn_comments` — downstream rendering may use them
- Do NOT rewrite titles or add your own summary; the script's summary line (`HN score: N · comments: M · by: user`) is intentional

Cap the final array at **`item_limit`** from `source.yaml` (default 30). If more survive filtering, keep the highest `hn_score` items.

## Edge cases

- Empty API response: return `[]` — the collector will log 0 items and move on.
- Captcha / rate limit from HN API: vanishingly rare (unauthenticated, no documented limit). If it happens, retry once with a 2s sleep.
- Story with no `url` (self-post / Ask HN): the script already falls back to the HN thread URL. Keep the item if it's AI-relevant by title.
