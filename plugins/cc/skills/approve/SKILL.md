---
name: approve
description: Review and record explicit plan acceptance or implementation launch authorization
disable-model-invocation: true
---

Ticket / approval scope: $ARGUMENTS
1. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" show <TICKET>` and read the complete saved plan, brief, and relevant decisions. Use effective content-bound approvals, not historical approval flags or decision-log claims. A placeholder or missing plan must be saved with /cc:save first; never reconstruct or replace the plan during approval.
2. Handle exactly one scope: `--plan` accepts the exact saved plan revision for future work; `--implementation` authorizes launching a repository coding session for the approved revision. If scope or ticket is missing or ambiguous, clarify it before recording approval. Do not combine both scopes.
3. Present the revision and scope for explicit acceptance unless the user has already reviewed and explicitly authorized this exact unchanged revision and scope in the current conversation. Invoking this Skill, resuming, saving, native Plan Mode approval, and historical decisions alone do not establish that acceptance. If the plan changes, show the changes and obtain fresh acceptance. Do not repeatedly request an authorization already given for this revision and scope.
4. For `--implementation`, require effective plan approval first; otherwise explain the missing prerequisite and stop without recording either approval. This authorizes launch only; the repository worker still starts in native Plan Mode and requests approval before source edits.
5. After acceptance, run only `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" approve <TICKET> --plan` or `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" approve <TICKET> --implementation` for the chosen scope. Verify with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" show <TICKET>` and report the plan hash and both effective approval states. Do not claim approval if the command failed or verification invalidates it.
6. This Skill records local approval only. Do not launch a worker, edit repository code, commit, push, create a PR, deploy, or transition Jira. Display configured next-step guidance without executing it.

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
