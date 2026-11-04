---
name: upgrade
description: Refresh an existing My CC workspace's compatibility engine while preserving local data and Skills
disable-model-invocation: true
---

Request: $ARGUMENTS

1. Use the installed plugin's bundled engine for this upgrade, even if the workspace's `.cc/cc` is old. Read applicable workspace instructions before proceeding.
2. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" upgrade --dry-run` from the existing command-center folder, then run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" upgrade`. Invoking /cc:upgrade authorizes this refresh; do not initialize again. If the user requested only a preview, stop after the dry run.
3. Default upgrade refreshes only the recognized My CC compatibility engine and its management metadata. All existing local Skills stay untouched. Add `--refresh-skills` to both commands only if the user explicitly requests updating generated standalone `/cc-*` Skills too. Unrelated Skills are never targeted; customized My CC files are preserved, with current templates staged for manual comparison.
4. Report refreshed files, preserved conflicts, candidate paths, and backup location from actual output. A preserved engine conflict means the local engine is still the user's copy; do not claim it was updated. Do not overwrite a conflict or infer permission to merge it.
5. Never modify `workspace.json`, tickets, state, repository registrations, context, CLAUDE.md, MEMORY.md, AGENTS.md, integration configuration, or credentials as part of this upgrade. Do not fetch or install plugins, create a release, or change the plugin version. Plugin installation/update and workspace refresh are separate operations.
6. Explain that namespaced `/cc:*` commands always use this plugin's bundled engine; this refresh is for terminal `.cc/cc` compatibility. After an installed plugin update, use `/reload-plugins` on supported Claude versions or restart Claude Code. If standalone Skills were refreshed, use `/reload-skills` or restart to load them. Do not restart or close the developer's session automatically.

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
