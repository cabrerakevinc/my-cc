# Native planning and durable ticket handoffs

My CC keeps native `/plan`. Plan acceptance for future work, permission to launch
a repository session, and native approval to start editing are separate actions.
Saving never grants implementation permission.

## Assessment and supported boundaries

The previous implementation already stored one `ticket.json`, `brief.md`,
`plan.md`, `decisions.md`, and `handoff.md` per ticket. Pickup created a local
record; its Skill performed Jira lookup and repository discovery through approved
tools. The Python CLI itself did not fetch Jira. Save distilled documents and
called `checkpoint`, but did not require importing the native plan. Resume printed
only the first 6,500 plan characters, and work included only the first 12,000.
Plan import reset approval even for identical content. Approval used booleans
without identifying a revision, so direct plan edits could retain approval.

Existing documentation distinguished local plan approval from implementation
authorization; it did **not** explicitly equate native approval with future
approval. However, it omitted how to leave native planning without execution,
and its “write a plan, approve, save” examples left that distinction unclear.

Verified locally on 2026-11-04: `claude --version` reports **2.1.318**;
`claude --help` supports `--permission-mode plan`. An interactive safe-mode check
confirmed that Shift+Tab leaves Plan Mode, cycling through Auto and then Manual
in this environment, without sending a model request. This CLI is not logged in,
so the completed-plan approval dialog could not be reproduced locally.

[Anthropic's permission-mode documentation](https://code.claude.com/docs/en/permission-modes#review-and-approve-a-plan)
states that native Yes options exit planning and begin execution; it also
documents Shift+Tab to leave planning without approval.
[Interactive controls](https://code.claude.com/docs/en/interactive-mode#general-controls)
document Esc to dismiss a dialog or decline a permission prompt. These are the
supported basis for the sequence below; the completed-plan dialog dismissal
still needs a live check in your authenticated terminal. Custom bindings and
organization settings can change the UI. Check `/help` or `?` and the visible
mode indicator, rather than relying on an assumed number of key presses.

Native plans are Markdown files. The documented
[`plansDirectory` setting](https://code.claude.com/docs/en/settings-reference#plansdirectory)
changes their location relative to the project root; the default is
`~/.claude/plans`. A known file can be imported reliably. A directory alone does
not establish which plan belongs to which ticket. No current-session plan export
or ticket mapping was found in the installed CLI help or reviewed public CLI
reference. This is a verification boundary, not a promise about private internals.
My CC does not parse session JSONL, guess filenames, or choose the newest plan.
It asks for the exact path or complete content when the conversation cannot
identify the file.

Rechecked public documentation on 2026-11-04:
[ExitPlanMode hook inputs](https://code.claude.com/docs/en/hooks#exitplanmode)
can expose `plan` and `planFilePath` before the approval prompt; PostToolUse can
expose the approved plan. This is a supported integration point, but it does not
give the current hook-free My CC CLI automatic knowledge that a plan was finalized
for a ticket. No hook or session watcher is installed by this feature. Skills use
conversation context to query `next-steps TICKET --plan-finalized` when appropriate;
otherwise the guidance includes a manual `/cc:save TICKET` fallback after `/plan`.
The hint never records acceptance or permission to implement. See
[next-step guidance](NEXT-STEPS.md).

## Day 1: investigate, plan, accept for later, save

In the command-center Claude session:

```text
/cc:pickup MSC-1873
/plan
Use the pickup findings to prepare a minimal implementation and test plan.
Read applicable repository instructions. Identify affected repositories and
files, constraints, decisions, rejected alternatives, and open questions.
Do not implement. Show the exact plan file path so we can save it for later.
```

Review and revise the plan. At the native execution prompt, do not choose either
Yes option when you intend to stop. Dismiss with Esc, then cycle out of Plan Mode
with Shift+Tab until the mode indicator shows Manual. Confirm no implementation
was authorized. Do not send an implementation instruction while cycling modes.
If this sequence differs in your installed UI, use its displayed help and leave
the execution request unapproved; do not guess a shortcut.

Then explicitly accept the revision for future work:

```text
I approve this finalized plan for future implementation only. Do not implement.
/cc:save MSC-1873
```

Save imports the **complete** native plan, preserves findings and repository
references in the brief, records decisions and rejected alternatives, records
explicit future-plan approval, and writes a concise handoff. If no approval was
given, it saves a draft or asks for the missing approval choice. If the full plan
cannot be located, it requests its exact path or complete content before claiming
a plan checkpoint. Dismissing the native dialog is not plan acceptance.

Equivalent terminal commands from the workspace:

```bash
python3 .cc/cc plan MSC-1873 --file /exact/path/to/native-plan.md
# Only after explicit acceptance of this exact revision for future work:
python3 .cc/cc approve MSC-1873 --plan
python3 .cc/cc checkpoint MSC-1873 --summary 'Plan reviewed for future implementation' \
  --next 'Revalidate Jira and repository state; authorize repository session' --pause
python3 .cc/cc show MSC-1873
```

For an unapproved import and checkpoint in one command, use
`checkpoint MSC-1873 --plan-file /exact/path/to/native-plan.md --summary 'Draft plan saved'`.
This flag never records approval. Investigation-only checkpoints remain supported
without a plan file. Keep important decisions in `decisions.md`; do not paste raw
transcripts into the handoff.

## Day 7: resume, revalidate, launch, approve editing

Start a fresh Claude session in the same command center:

```text
/cc:resume MSC-1873
/cc:work MSC-1873
```

Resume restores the full brief, plan, decisions, and handoff. It remains read-only.
Recheck Jira acceptance criteria, relevant repository branches/HEADs, PRs and
contracts. If those changes require revising the plan, import the full revision
and obtain fresh approvals. Otherwise retain the reviewed plan.

The work Skill requests explicit launch/implementation authorization if absent,
then provides the launcher command. In a **separate terminal**, after authorizing:

```bash
python3 .cc/cc approve MSC-1873 --implementation
# Register the actual repository first if necessary:
python3 .cc/cc repo add payment-service /actual/path/to/payment-service
python3 .cc/cc work MSC-1873 --repo payment-service --dry-run
python3 .cc/cc work MSC-1873 --repo payment-service
```

Both local approvals are required before launch. The separate repository session
starts with `--permission-mode plan`, the complete work package for this ticket,
and instructions to read applicable repository guidance from outermost to
innermost directories. It verifies requirements and repository state, then asks
for approval **in that session before source edits**. Native approval is
appropriate here because implementation is now intended. The saved plan need
not be reconstructed. Repository instructions govern implementation; conflicts
require clarification. No permission bypass is added. Native Plan Mode supplies
the initial editing boundary; My CC does not implement a separate permission
engine or override organization policies.

## State, repeat saves, and existing workspaces

`ticket.json` retains the existing approval booleans and adds:

| Field | Meaning |
| --- | --- |
| `plan_sha256` | Hash of current full plan bytes |
| `plan_source` | Last explicitly imported path; provenance only, never followed automatically |
| `approved_plan_sha256`, `approved_plan_at` | Exact revision accepted for future work and UTC time |
| `implementation_plan_sha256`, `implementation_approved_at` | Revision authorized for repository launch and UTC time |

Identical imports keep approvals and their timestamps. Changed content invalidates
both approvals. Show, resume, work and dashboard details check effective approval
against current plan bytes, including direct edits or missing plans. A mutation
persists invalidation; read-only commands do not rewrite records. Historic text in
a handoff is a checkpoint snapshot; current effective metadata governs launching.
The SQLite index remains a disposable summary and is not an authorization source.

Legacy tickets and custom fields remain intact. Old approvals without hashes are
shown as unverified/unapproved and cannot authorize launch until explicitly
reapproved against the current saved plan. No saved plan is deleted or rewritten
by resume. Full plans and decisions are no longer silently truncated in resume
or work orders. Very large work packages still have to fit Claude's context;
reduce the scope deliberately rather than silently dropping plan steps.

All namespaced plugin Skills use the bundled engine even for existing workspaces whose
`.cc/cc` snapshot is older. For terminal commands in such a workspace, substitute
`python3 /path/to/updated/my-cc/cc` for `python3 .cc/cc`, or update the local engine
snapshot with `/cc:upgrade`. Existing local Skills are untouched by default.
Existing standalone `/cc-*` Skills require an explicit `--refresh-skills` request
to refresh unchanged generated templates; customized and unrelated Skills remain
intact. Prefer `/cc:*` commands so local compatibility snapshots do not become a
second update requirement. See the [upgrade guide](UPGRADING.md). Reinitialization
is unnecessary and refuses to overwrite an existing workspace.

For an unreleased checkout, exit Claude Code and start it from the existing
command-center directory with
`claude --continue --plugin-dir /absolute/path/to/my-cc/plugins/cc`.
Use `--resume <session-id>` to select a particular conversation instead.
This loads the local plugin for that session; it does not install or publish it.
Invoke the namespaced `/cc:*` Skills to use its bundled engine. A marketplace
installation will not acquire unpublished checkout changes. Once an updated
plugin is installed, supported versions can apply pending plugin changes with
[`/reload-plugins`](https://code.claude.com/docs/en/commands), or restart Claude
Code. `/reload-skills` refreshes standalone Skills after those files are updated;
neither reload command replaces the workspace's `.cc/cc` engine snapshot.

This solution adds no `/cc:plan` Skill, agents, background services, hooks, or
automatic checkpointing. The existing CLI `plan --file` only imports a file;
native Claude Code remains responsible for planning. These capabilities are
included in v0.2.0; see the [release notes](releases/v0.2.0.md).
