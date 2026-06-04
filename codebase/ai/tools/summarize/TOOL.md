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

Modes:
- `concept`: summarize the best matching source.
- `workshop`: summarize multiple published sources from one workshop.
- `auto`: infer workshop mode from queries like "Tom tat workshop 8".
