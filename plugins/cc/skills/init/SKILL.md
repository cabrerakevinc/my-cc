---
name: init
description: Initialize a reusable My CC workspace in the current empty directory
disable-model-invocation: true
---

Create an independent Claude Code command center in the current directory, using the bundled engine. Do not overwrite any files or existing workspace.

1. Ask for a name and profile (`engineering`, `business`, `academic`, or `general`) only if not provided in $ARGUMENTS. Engineering is the suggested default.
2. State the absolute directory that would be initialized; confirm it is empty and get approval before filesystem changes.
3. Preview with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" init . --name 'WORKSPACE NAME' --profile engineering --dry-run`.
4. Once approved, initialize with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" init . --name 'WORKSPACE NAME' --profile engineering` using the actual chosen profile/name.
5. Verify using `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" doctor`; explain workspace-local durable ticket state and context profiles. Namespaced `/cc:*` commands always use the installed plugin engine. `python3 .cc/cc` and standalone `/cc-*` Skills are compatibility snapshots; use /cc:upgrade to refresh the engine later. Existing local Skills are untouched unless refreshing generated My CC Skills is explicitly requested.
6. Do not install or modify TWG, AWS, Context7, or credentials. Those remain existing company-approved integrations.

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
