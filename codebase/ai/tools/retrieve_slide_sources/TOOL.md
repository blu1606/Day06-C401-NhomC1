---
name: retrieve_slide_sources
track: core
kind: local_knowledge
provider: local
requires_env: []
inputs: [question, cohort, workshopNo, topK]
outputs: [matches]
side_effect: false
---
# retrieve_slide_sources

Finds the most relevant published slide/document sources for a student
question. It searches local mock source JSON by summary, excerpt, skill tags,
section title, learning objective, and example student questions.
