---
name: resume
description: Restore the latest checkpoint for one ticket only
---

Ticket: $ARGUMENTS
1. Execute `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" resume <TICKET>` and read the complete saved plan, brief, decisions, and handoff for this ticket only. Resume is read-only; it neither approves implementation nor clears pause state. Content-bound approval is checked against the current plan; legacy unbound approval requires explicit reapproval.
2. Recheck relevant Jira requirements and repository branch/HEAD, PR and contract changes through approved tools before implementation, especially after days or weeks. Explain what changed; do not reconstruct the entire conversation.
3. Do not silently change an approved plan. If changes are needed, import the revised full plan and request fresh plan and implementation approvals.
4. For implementation, use /cc:work to prepare a separate repository session. Request explicit authorization before recording `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" approve <TICKET> --implementation`; saving or approving a plan alone never grants it. The worker starts in native Plan Mode and requests approval before editing.

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
