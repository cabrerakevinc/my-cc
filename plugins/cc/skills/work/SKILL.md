---
name: work
description: Launch repo-specific Claude Code implementation worker
disable-model-invocation: true
---

Ticket / repository: $ARGUMENTS
1. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" show <TICKET>` and read the complete saved plan, brief and decisions. Confirm content-bound plan approval and revalidate relevant Jira and repository changes. If the plan changed, import it and obtain fresh approval first.
2. Request explicit implementation/launch authorization before recording `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" approve <TICKET> --implementation`. Prior plan approval or a saved checkpoint does not grant this authorization. If launch authorization is already recorded for the unchanged plan, do not ask to record it again.
3. Discover/confirm the target repository. Register it first with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" repo add` if necessary. Explain the precise `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" work <TICKET> --repo <REPO>` command for a separate terminal; do not run interactive Claude as a nested Bash process.
4. The launcher starts a separate Claude Code session in the registered clone by default (or an opt-in worktree configured with `"worktrees": true` in `workspace.json`, overridden by `--worktree` / `--no-worktree`), with the complete saved work package and `--permission-mode plan`. The worker must read applicable repository instructions, revalidate scope, and request implementation approval before source edits. Use native approval there when ready to implement.
5. Never implement code in the command-center checkout. Repository instructions, including AGENT.md, AGENTS.md, CLAUDE.md and applicable MEMORY.md, retain authority. Check outermost-to-innermost instructions and repeat when entering subfolders.
6. Do not perform merge, push, deploy, or Jira Done transitions without separate authorization.

When presenting the separate-terminal launcher, resolve `${CLAUDE_PLUGIN_ROOT}` to the actual absolute plugin directory and quote the resulting engine path. Do not assume this variable exists in the developer's separate terminal, and do not substitute the workspace's older `.cc/cc` snapshot. The worker receives `CC_ENGINE` pointing to the same bundled engine for result synchronization.

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
