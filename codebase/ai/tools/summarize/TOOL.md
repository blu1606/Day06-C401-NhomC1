---
name: summarize
track: core
kind: local_knowledge
provider: local
requires_env: []
inputs: [query, mode, workshop_no, max_sources]
outputs: [summary, key_points, citations, confidence]
side_effect: false
---
# summarize

Summarizes official workshop slide sources from local mock data.

Use this tool when the student asks to summarize a lesson concept, workshop
section, or slide topic. The tool only uses published sources and returns
citations when confidence is high enough.

For longer slide records, the tool can use raw text fields such as `content`,
`full_text`, `raw_text`, `slide_text`, or `notes`. It chunks long text locally,
ranks chunks against the query, and uses the most relevant chunks for summary,
key points, and citation excerpts.

Modes:
- `concept`: summarize the best matching source.
- `workshop`: summarize multiple published sources from one workshop.
- `auto`: infer workshop mode from queries like "Tom tat workshop 8".
