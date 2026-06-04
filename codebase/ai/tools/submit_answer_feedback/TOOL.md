---
name: submit_answer_feedback
track: core
kind: feedback
provider: local
requires_env: []
inputs: [question, answerId, sourceIds, feedbackType, note, userRole]
outputs: [saved, feedbackId, nextAction]
side_effect: true
---
# submit_answer_feedback

Saves feedback about answer quality or citation correctness as a correction
signal for mentor review or golden-test follow-up.
