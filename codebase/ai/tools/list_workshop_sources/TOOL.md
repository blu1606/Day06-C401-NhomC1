---
name: list_workshop_sources
track: core
kind: admin
provider: local
requires_env: []
inputs: [cohort, workshopNo, status]
outputs: [sources]
side_effect: false
---
# list_workshop_sources

Lists local slide/document sources available to the AI tutor, with optional
filters for cohort, workshop/day number, and publication status.
