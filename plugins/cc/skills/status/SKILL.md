---
name: status
description: Summarize sprint tickets without loading all ticket histories
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" status` with the filters requested in $ARGUMENTS. Use the SQLite status index, not the contents of every ticket folder. Summarize blockers, pending decisions, and the next actions. Keep Jira and local phase distinct. Always use this bundled engine, including in older workspaces.

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
