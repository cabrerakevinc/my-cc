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
