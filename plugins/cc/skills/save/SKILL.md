---
name: save
description: Checkpoint ticket facts, decisions, and next action
---

Ticket: $ARGUMENTS
1. Resolve the ticket with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" show <TICKET>`. This is a manual checkpoint, never permission to implement.
2. If native planning occurred, locate the exact finalized Markdown plan using the path known in this conversation or supplied by the developer. Native plans default to `~/.claude/plans/`; `plansDirectory` can change that. Never select by newest timestamp, infer ticket ownership from a filename, or inspect private session JSONL/internal mappings. If the exact plan is unavailable or ambiguous, ask for its path or complete content and stop the plan checkpoint until supplied. Do not silently save a summary as the full plan. If content is supplied, write it in full to a ticket-scoped file before importing.
3. Import the complete plan with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" plan <TICKET> --file '<EXACT-PATH>'`. This is a file importer, not a planner. Preserve every implementation/testing step, constraint, and alternative; keep only the handoff concise. For a progress save with no new planning, retain the existing plan; an investigation-only checkpoint may remain unapproved.
4. Preserve verified findings, repository references and observed branches/HEADs in `brief.md`; preserve technical decisions and rejected alternatives with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" decision <TICKET> --text '...' --reason '...'`. Review existing entries first to avoid duplicates.
5. Record `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" approve <TICKET> --plan` only when the developer explicitly accepts this exact revision for future implementation. If approval is unclear, ask whether to save it as a draft or approve it for future work. Native execution approval, dismissing a dialog, and requesting a save do not imply this approval. Never run `approve --implementation` as part of saving. Identical imports retain existing approval; changed content resets both approvals.
6. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" checkpoint <TICKET> --summary '...' --next '...'` (add `--pause` when stopping). Then run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" show <TICKET>` and read the persisted `plan.md` to verify full content, hash, and effective approval status. Report the exact saved path, phase, approval status, pause state and next action. Never claim success before verification.

Use the bundled engine above even when this workspace has an older `.cc/cc` snapshot.

At completion, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" next-steps <TICKET>`
for the ticket involved, or omit <TICKET> when no ticket is selected. Display the
returned Workflow/Next/Optional lines once, preserving command labels and
configuration. If output is empty, omit guidance. Never invent or execute a
suggested command. When presenting terminal commands, preserve the resolved
absolute engine and workspace paths returned by the CLI.
After native /plan is finalized in this conversation but not imported, add
--plan-finalized to this read-only query. Do not infer native planning completion
from files, timestamps or approval dialogs; otherwise show the returned manual
save fallback. Do not add your own next-step commands outside this output.
