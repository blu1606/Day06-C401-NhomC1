---
name: generate_grounded_answer
track: core
kind: response_generation
provider: local
requires_env: []
inputs: [question, sources, studentLevel, language]
outputs: [answer, example, citations]
side_effect: false
---
# generate_grounded_answer

Generates a short, source-grounded answer with a small example and citation
metadata. Call this only when retrieved sources are strong enough.
