---
name: pickup
description: Start or investigate a ticket with local, persisted context
---

Ticket: $ARGUMENTS
1. Check `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" show <TICKET>`; if missing, retrieve Jira details using the approved TWG CLI after inspecting available `twg --help` commands. Do not invent flags or use unapproved MCP connectors.
2. Create the local ticket with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" pickup <TICKET> --title '...'` and save an accurate `brief.md`. Never fabricate Jira facts.
3. Identify candidate repositories from the ticket, known repo registry, and targeted metadata searches. Avoid scanning all repositories. Record repository paths, branches/HEADs, relevant files, and source references in `brief.md`.
4. Investigate only the necessary code, reading applicable repository instructions from outermost to innermost directories.
5. Explain findings and proposed scope. Do not edit code, create PRs, or transition Jira at pickup.
6. Continue in the same session with native `/plan` for the minimal implementation and testing plan. Do not create a competing /cc:plan command. Keep findings in the conversation until a manual /cc:save.

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
