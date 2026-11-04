---
name: cc-resume
description: Restore the latest checkpoint for one ticket only
---

Ticket: $ARGUMENTS
1. Execute `python3 .cc/cc resume <TICKET>` and read only the listed ticket documents as needed.
2. If the ticket was paused for days, recheck relevant Jira requirements and Git branch/contract changes through approved tools.
3. Explain new information, decisions, risks, and next action. Do not silently change an approved plan.
4. If ready to implement, request explicit approval. Coding must occur in a repository-specific session via `python3 .cc/cc work`.
