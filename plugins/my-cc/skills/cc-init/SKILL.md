---
name: cc-init
description: Initialize a reusable My CC workspace in the current empty directory
disable-model-invocation: true
---

Create an independent Claude Code command center in the current directory, using the bundled engine. Do not overwrite any files or existing workspace.

1. Ask for a name and profile (`engineering`, `business`, `academic`, or `general`) only if not provided in $ARGUMENTS. Engineering is the suggested default.
2. State the absolute directory that would be initialized; confirm it is empty and get approval before filesystem changes.
3. Preview with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" init . --name 'WORKSPACE NAME' --profile engineering --dry-run`.
4. Once approved, initialize with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" init . --name 'WORKSPACE NAME' --profile engineering` using the actual chosen profile/name.
5. Verify using `python3 .cc/cc doctor`; explain workspace-local durable ticket state, context profiles, and `python3 .cc/cc` command usage.
6. Do not install or modify TWG, AWS, Context7, or credentials. Those remain existing company-approved integrations.
