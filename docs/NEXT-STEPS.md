# Configurable next-step guidance

My CC reports the current workflow phase and one primary action, with an optional
alternative. Suggestions are instructions for the user to choose; My CC never
executes them automatically.

Add or edit `workspace.yaml` at the command-center root:

```yaml
workflow:
  next_steps:
    enabled: true
    display: both
    max_suggestions: 2
```

You can also add the same settings to the existing `workspace.json`, alongside
its other fields:

```json
{
  "workflow": {
    "next_steps": {
      "enabled": true,
      "display": "both",
      "max_suggestions": 2
    }
  }
}
```

This is a fragment to merge into the file; keep existing workspace fields.
Settings resolve per key: built-in defaults, then YAML, then explicit JSON
values. JSON takes precedence when both files define the same setting, so a
generated YAML default cannot mask a JSON change. Both guidance blocks must
contain valid settings. JSON uses boolean and integer types, not strings.

New workspaces include both the existing `workspace.json` metadata and the YAML
guidance defaults. JSON-only workspaces need no YAML file. Existing workspaces get the same defaults when
the file or keys are absent; an upgrade preserves workspace configuration. Set
`enabled: false` to omit guidance, or `max_suggestions: 1` for only the primary
action. The limit must be a positive integer.

`display: slash` prefers Claude Code commands, `cli` prefers Python terminal
commands, and `both` shows both forms when available. If only one supported form
exists, that form is shown regardless of preference. Labels distinguish
**Claude Code** from **Terminal**. Terminal examples use the invoking engine's
absolute path and an explicit workspace, including when the plugin operates on
an older workspace snapshot.

The dependency-free configuration reader supports this block-mapping syntax,
scalar values (optionally quoted), and comments. General YAML features such as
anchors, tags, flow mappings and multiline values are unsupported in this block.
Unrelated workspace sections are ignored. Invalid guidance values produce a
clear error from `next-steps`; automatic guidance reports its failure without
failing an otherwise successful ticket operation. Existing settings remain in
`workspace.json`, which can also hold guidance preferences; no configuration or
ticket migration is needed.

## Recommendations

| Ticket state | Primary action |
| --- | --- |
| Blocked phase or recorded `blockers` | Review the handoff and resolve blockers before continuing |
| Completed | Review the saved outcome if needed |
| Paused | Review the saved handoff before deciding to continue; resume stays read-only |
| No saved plan | Native `/plan` for this ticket in the same session; optional manual save when finalized |
| Native plan finalized but not saved | `/cc:save TICKET`, using the exact path or full content |
| Saved plan lacks effective approval | Review it and, after explicit acceptance, `approve TICKET --plan` |
| Approved plan lacks implementation authorization | Request authorization and record `approve TICKET --implementation` only when granted |
| Both approvals valid; early workflow phase | `/cc:work TICKET` to confirm the repository and prepare the separate-terminal worker |
| Implementing, testing, review, deployment, verification | Review the handoff with phase-specific instructions; follow existing repository delivery rules |

Blockers, completion, and pause take priority over planning hints. Effective
approvals use existing content hashes, so edited, missing or legacy unbound plans
cannot retain implementation permission in the recommendations. Arbitrary
`next_action` text is never interpreted as an executable command. The handoff
retains the recorded next action, blockers and repository-specific details.

Approval guidance supports `/cc:approve TICKET --plan` and
`/cc:approve TICKET --implementation` as well as their terminal equivalents.
`display: slash` shows the Skill, `cli` shows the Python command, and `both`
shows both for the same action. The standalone forms are `/cc-approve`.
The approval Skill reviews the saved revision and records only the explicitly
accepted scope; selecting the Skill alone does not approve anything. Plan
acceptance, launch authorization, and the worker's native editing approval remain
separate. A changed or legacy plan requires content-bound reapproval.

There is no `/cc:plan`. Native planning and the save Skill display only Claude Code forms.
The `plan` CLI command imports an exact file and is not a native planning or full
save Skill equivalent. A `work` terminal example is included only when the ticket
already records exactly one repository; otherwise the work Skill handles selection
without a guessed repository or a non-executable placeholder. Native approval
before worker edits remains required.

## Native planning and manual fallback

After `/cc:pickup PAY-104`, a typical result is:

```text
Workflow: PAY-104 · discovered
Next: Plan PAY-104 in this same Claude Code session. Claude Code: `/plan Prepare the implementation and test plan for PAY-104`
Optional: When the native plan for PAY-104 is finalized, save its exact path or full content manually. Claude Code: `/cc:save PAY-104`
```

My CC installs no hook or watcher to detect native planning completion. The Skill
may use known conversation context to run:

```bash
python3 .cc/cc next-steps PAY-104 --plan-finalized
```

This read-only hint recommends `/cc:save PAY-104` without modifying state or
inferring approval. Without the hint, the conditional save suggestion remains
the manual fallback. If only one suggestion is configured, invoke `/cc:save PAY-104`
manually when planning is finalized, or query with `--plan-finalized`. Use the
exact known plan path or full content; never select the newest native plan file.
See the [planning workflow](PLANNING-WORKFLOW.md) for supported native controls
and the separate plan, launch, and worker approval gates.

## Skills and compatibility

All plugin and newly generated standalone Skills query `next-steps` at completion,
display its output once, and omit guidance when disabled. With no ticket selected
(for example, initialization or a workspace overview), they query without a ticket
and report that no ticket is selected rather than guessing one or loading every
ticket history. Standalone Skills use `--surface standalone` for `/cc-*` names.

The Python ticket commands also append recommendations. To refresh existing
standalone Skills, explicitly use `/cc:upgrade --refresh-skills` or the updated
engine's `upgrade --refresh-skills`; a default upgrade leaves local Skills intact.
Customized Skills are preserved under the existing upgrade rules. This feature
adds no new agent, background process, or MCP integration.
