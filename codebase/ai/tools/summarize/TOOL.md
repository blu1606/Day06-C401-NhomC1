---
name: summarize
track: core
kind: local_knowledge
provider: local
requires_env: []
inputs: [content, detail_level, retrieval, query, mode, workshop_no, max_sources]
outputs: [summary, key_points, keywords, citation, citations, confidence]
side_effect: false
---
# summarize

Summarizes learning content for quick review.

Use this tool when the student asks to summarize a lesson concept, workshop
section, or slide topic. The tool only uses published sources and returns
citations when confidence is high enough.

Contract-compatible inputs:
- `content`: direct text to summarize. If provided without `query`, the tool
  summarizes this content directly, unless `retrieval` is provided.
- `detail_level`: `brief` or `detailed`.
- `retrieval`: optional callable that receives the query/content and returns
  `{data, citation}`. When present, summarize uses this source first and falls
  back to local published mock data if retrieval has no match.

For longer slide records, the tool can use raw text fields such as `content`,
`full_text`, `raw_text`, `slide_text`, or `notes`. It chunks long text locally,
ranks chunks against the query, and uses the most relevant chunks for summary,
key points, and citation excerpts.

Modes:
- `concept`: summarize the best matching source.
- `workshop`: summarize multiple published sources from one workshop.
- `auto`: infer workshop mode from queries like "Tom tat workshop 8".
