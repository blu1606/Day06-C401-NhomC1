---
name: explain
track: learning_tutor
kind: generation
provider: local
requires_env: [OPENROUTER_API_KEY]
inputs: [content, retrieval]
outputs: [explanation, citation]
side_effect: false
---
# explain

Generates a grounded explanation for a student query based on retrieved source slides.
The output contains three parts: detailed explanation, simplified version, and a real-life analogy/example.
