---
name: handle_low_confidence_answer
track: core
kind: safety
provider: local
requires_env: []
inputs: [question, reason, closestSources]
outputs: [message, suggestedQuestions]
side_effect: false
---
# handle_low_confidence_answer

Returns a safe fallback message when sources are missing, weak, or outside the
official workshop scope.
