---
name: dashboard
description: Open a local read-only dashboard for this command-center workspace
disable-model-invocation: true
---

Request: $ARGUMENTS

For a stop request, run the stop command below instead of launching.

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" dashboard --background` from the current command-center workspace. This uses the updated bundled engine even if `.cc/cc` is older.
Report the returned URL and startup result. The command opens the browser and reuses an existing dashboard for this workspace.
To stop, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" dashboard --stop` from that workspace.
Use `--no-browser` when requested; do not expose the server on the network or modify ticket state.

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
