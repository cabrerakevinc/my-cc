---
name: save
description: Checkpoint ticket facts, decisions, and next action
---

Ticket: $ARGUMENTS
1. Resolve the ticket with `python3 .cc/cc show <TICKET>`.
2. Distill verified findings and decisions; preserve rejected alternatives and reasons with `python3 .cc/cc decision`.
3. Keep `brief.md`, `plan.md`, and `decisions.md` factual, concise, and current. Do not copy whole transcripts or raw logs.
4. Run `python3 .cc/cc checkpoint <TICKET> --summary '...' --next '...'` and verify it succeeds.
5. Report the exact phase, pause state, and next action. Never claim success unless the command succeeds.
