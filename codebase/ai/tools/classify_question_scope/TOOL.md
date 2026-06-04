---
name: classify_question_scope
track: core
kind: policy
provider: local
requires_env: []
inputs: [question, retrievedMatches]
outputs: [scope, reason, confidence]
side_effect: false
---
# classify_question_scope

Classifies whether a student question is in scope, low confidence, or out of
scope based on retrieved official source matches.
