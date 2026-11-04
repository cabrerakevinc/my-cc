---
name: status
description: Summarize sprint tickets without loading all ticket histories
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" status` with the filters requested in $ARGUMENTS. Use the SQLite status index, not the contents of every ticket folder. Summarize blockers, pending decisions, and the next actions. Keep Jira and local phase distinct. Always use this bundled engine, including in older workspaces.
