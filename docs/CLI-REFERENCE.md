# Command Center Starter (v0.1)

## Configurable next-step guidance

`cc next-steps PAY-104` reads authoritative ticket state and effective approvals,
then displays the phase and up to two actions by default. It does not write state
or execute suggestions. `--surface standalone` uses `/cc-*` names instead of
plugin `/cc:*` names. Without a ticket it provides workspace-level guidance.

`cc next-steps PAY-104 --plan-finalized` is a manual hint that a native plan in the
current conversation is finalized but not imported; it recommends saving the
exact plan. It does not grant approval or persist the hint. Blockers, completed
and paused states still take priority.

Ticket commands also append guidance automatically. Skills query this command
at completion and show the configured result once. Set `workflow.next_steps.enabled`
to `false` in `workspace.yaml` or `workspace.json` to omit it. Explicit JSON values
override YAML per setting. See [configuration and rules](NEXT-STEPS.md).

A **local-first, dependency-free** starter for a reusable Claude Code command center. It keeps your original engineering use case at the center: Jira ticket → scope/plan → approved repo-specific implementation → tests/review → PR/merge/deployment through existing company tooling → verified Jira closure.

The CLI and workspace templates are functional. **TWG and AWS integration commands are deliberately not guessed or automatically connected**; configure their approved operations later on the company machine. Context7 remains your existing Claude Code MCP server. This starter does *not* fetch real Jira tickets, open real PRs, send Slack messages, merge, or deploy.

## Install on your Mac

Prerequisites: Python 3.10+, Git, and Claude Code installed on your work machine. `cc` uses only Python's standard library. Review the shell script before running it.

```bash
unzip command-center-starter.zip
cd command-center-starter
./install.sh
# If needed, add ~/.local/bin to your PATH in ~/.zshrc.
cc --version
```

`install.sh` copies the Python CLI to `~/.local/share/command-center-starter/`, symlinks `~/.local/bin/cc`, and installs the global `/cc-init` Skill under `~/.claude/skills/cc-init/`. It **does not** modify Claude's settings, connect MCP services, or change credentials. If you already have a `/cc-init` skill, it stops rather than overwriting it.

You may also use `python3 ./cc` directly without installation, although `/cc-init` will not exist until installed.

## Create isolated workspaces

The CLI initializes independent workspaces directly:

```bash
cc init ~/work/bbc/command-center --name "BBC Engineering" --profile engineering
cc init ~/work/bevz/command-center --name "BEVZ" --profile business
cc init ~/school/mba/command-center --name "MBA" --profile academic
```

Or, after installing the global skill, create an empty folder, start Claude Code there, and invoke `/cc-init`. Do not confuse it with Claude Code's built-in `/init`.

Inside one workspace:

```bash
cd ~/work/bbc/command-center
cc doctor
claude
# Within Claude Code: /cc-status
```

Each workspace contains:

```text
command-center/
  CLAUDE.md                        # Short, always-on coordinator instructions
  workspace.json                   # Workspace identity/model/profile
  config/integrations.json         # Tool inventory; not wired until configured
  .claude/skills/cc-*/SKILL.md    # Commands for the coordinator
  context/identity.md
  context/communication/{principles,slack,email,stakeholder-updates}.md
  context/people/directory.md
  context/business/{overview,glossary,systems}.md
  context/references/index.md
  state/index.sqlite              # Rebuildable query index
  state/repos.json                # Local repository lookup
  state/tickets/PAY/PAY-104/       # Durable per-ticket records
      ticket.json
      brief.md
      plan.md
      decisions.md
      handoff.md
      work-orders/...
      work-results/...
```

The default `.gitignore` excludes `state/` and `context/` because work and business information may be confidential. These directories remain local. Review any backup/sync approach against company policy. **Do not put credentials or sensitive AWS output in notes.**

## Your daily engineering workflow

### 1. Pick up a ticket in the command-center session

```bash
cc pickup PAY-104 --title "Fix duplicate charges" --sprint S24 \
  --summary "Investigate retries that may create duplicate processing"
cc phase PAY-104 investigating
cc show PAY-104
```

When TWG is configured, the `/cc-pickup` Skill can query Jira and prepare the factual `brief.md` instead of using manual ticket arguments. Until then, this is a local record—not a claim that Jira was accessed.

### 2. Plan in Claude Code and persist decisions

Keep using native `/plan` in the same command-center session as pickup. Review
and finalize the plan, then leave the native execution prompt unapproved and return
to Manual mode when saving for later. The native Yes options start execution.
Use the exact native plan file path (or obtain complete content if unavailable), then:

```bash
cc plan PAY-104 --file /path/to/reviewed-plan.md
cc decision PAY-104 --text "Use existing idempotency records" \
  --reason "Avoid introducing a new persistence dependency"
cc approve PAY-104 --plan                    # Only after you approved the plan
cc checkpoint PAY-104 --summary "Plan approved" \
  --next "Implement next Monday" --pause
```

`plan --file` imports the complete file; it does not generate plans. Alternatively,
`checkpoint TICKET --plan-file /exact/path.md --summary 'Draft saved'` imports and
checkpoints without granting approval. Empty, missing, unreadable or placeholder
imports fail before checkpointing. No file is selected automatically.

`approve --plan` records explicit acceptance of that revision for future work;
`approve --implementation` separately authorizes repository launch. Neither a save
request nor native execution approval is treated as future-plan acceptance.
Approvals have UTC timestamps and bind to SHA-256 plan hashes. Identical saves
retain approvals; changed content resets both. Direct edits are checked before
approval, resume and launch. Legacy flags without hashes require reapproval while
all saved documents remain intact. See the [workflow and assessment](PLANNING-WORKFLOW.md)
for metadata, supported plan locations, UI verification limits, and existing-workspace
engine compatibility.

### 3. Resume next week, with a fresh context

```bash
cc status --state paused
cc resume PAY-104
cc checkpoint PAY-104 --unpause --next "Verify Jira and repo state"
```

`cc resume` is intentionally read-only. It prints the full saved brief, handoff, decisions, and plan without replaying the Claude session or truncating plan steps. Use `/cc-resume PAY-104` inside the coordinator to have Claude check for stale assumptions.

### 4. Launch a **repo-specific** coding session

Register a local repo, or its clone destination and remote (not all 100 repos):

```bash
cc repo add payment-service ~/work/bbc/repositories/payment-service
# Not cloned yet? Register the remote explicitly:
# cc repo add payment-service ~/work/bbc/repositories/payment-service --remote <approved-git-url>
cc repo list
```

After you separately approve implementation:

```bash
cc approve PAY-104 --implementation
cc work PAY-104 --repo payment-service --dry-run
cc work PAY-104 --repo payment-service
# If needed, select a verified base branch explicitly: --base origin/main
# Add --clone if the registered repository is not cloned yet.
```

`cc work` makes a Git worktree at `~/work/bbc/.cc-worktrees/payment-service/PAY-104` (unless you explicitly set `--no-worktree`), starts a **separate Claude Code interactive session** from that path, and supplies the complete approved ticket work package with `--permission-mode plan`. The worker revalidates scope and requests implementation approval in that session before source edits. The work order instructs Claude to read the applicable repo `AGENT.md` (singular) explicitly and check `AGENTS.md`/`CLAUDE.md`. It does not write or replace the repo's instruction files. For projects with both `CLAUDE.md` and `AGENTS.md`, select **Project instructions → claude-md-and-agents-md** in Claude Code's `/config` on a supported version. Verify loading with `/context all`.

You can still use native `/plan` and `/code-review` in the repo session. The launcher does not run tests, commit, push, merge, or deploy automatically. After the coding session exits normally, it captures a **Git-state-only checkpoint**; test results and rationale still need explicit recording. It stops before launch without both current, content-bound local approvals. Native Plan Mode provides the initial source-editing gate after launch.

When you finish coding, inside that worker session or back in the coordinator:

```bash
cc sync PAY-104 --repo payment-service --summary "Minimal fix implemented" --tests "pytest targeted suite: passed"
cc checkpoint PAY-104 --summary "Implementation ready for review" --next "Run code-review and prepare PR" --pause
```

`cc sync` captures branch, HEAD commit, local Git status, diff summary (against the original worktree base), and user-supplied test evidence in the ticket workspace. It does not mark a test as passed on its own. `CC_WORKSPACE` is provided to workers, so they can call `cc` without navigating back to the command center.

### 5. Continue normal delivery workflow

Use company-approved TWG commands for PR creation and Jira updates once the interface is documented. Use your AWS MCP CLI only with the access your company permits. Record PR links and deployment evidence in the ticket workspace. Final Jira transitions remain deliberate, after verification. These integrations are **not yet implemented**.

## Multiple workspaces and writing voice

BBC, BEVZ, and MBA each have independent `context/` and `state/`. Edit `context/communication/principles.md`, `slack.md`, and `email.md` with your own voice. `context/people/directory.md` can store *professional* roles and audience preferences, and `context/business/` houses your verified business specs and service maps.

In your coordinator session, `/cc-draft` loads only the relevant writing preferences. Communication personas do **not** get injected into repo coding workers, where the repository instructions take precedence for implementation details.

## What's deliberately deferred

- TWG Jira/Bitbucket/Rovo syntax adapter, until `twg --help` can be safely examined on your work machine
- AWS MCP CLI diagnostics integration and permission enforcement
- Automatic PR/CI/deployment status polling and Jira transitions
- Full multi-repository dependency orchestration
- Repo metadata search across uncloned repositories (first version uses manual repo registry)
- Automatic transcript capture: checkpoints are **explicit**, and `/cc-save` helps you capture decisions
- Automatic enforcement of company authorization at the shell layer; your CLI and Claude Code permission policies need to be applied in the company environment

## Smoke tests

```bash
python3 -m unittest discover -s tests -v
```

To clean up: remove a workspace folder only after reviewing its state and backing up whatever your company permits. Remove the global skill at `~/.claude/skills/cc-init/` and the installed `cc` binary/symlink if desired. The installer does not install a background daemon.

Marketplace plugin commands use `/cc:init`, `/cc:upgrade`, `/cc:pickup`, `/cc:save`, `/cc:resume`, `/cc:status`, `/cc:work`, and `/cc:draft` after installing `cc@my-cc-marketplace`. All namespaced commands use the plugin's bundled engine. The `/cc-*` examples above remain valid for standalone workspace skills.

`upgrade --dry-run` previews a compatibility-engine refresh from the engine you
are invoking; `upgrade` applies it, backing up recognized generated files first.
All existing local Skills stay untouched unless you explicitly add
`--refresh-skills`. Even then, only unchanged generated My CC Skills are refreshed;
custom and unrelated Skills are preserved. Data, `workspace.json`, context and
instructions never change during upgrade. Use `/cc:upgrade` with the updated
plugin so an older `.cc/cc` snapshot need not understand this command. See the
[upgrade guide](UPGRADING.md) for conflicts, backups and plugin reloads.

## Local dashboard (v0.1.2+)

Run `python3 .cc/cc dashboard --background` in a workspace initialized with the current engine. It opens the browser and returns a private loopback URL. `--no-browser` suppresses opening, `--port N` selects a port (default 8765, 0 chooses a free port), and `--stop` shuts down this workspace's server. Foreground mode stops with Ctrl+C. Closing a tab leaves the server running.

`/cc:dashboard` uses the updated plugin engine, so it also works in older workspaces without changing their `.cc/cc` snapshot. The skill can launch or stop that server. Each workspace has a separate dashboard; use different ports or `--port 0` to run several.

The overview reads SQLite in read-only mode. Details read the authoritative ticket documents, work orders, and work results as escaped text. Refresh to pick up changes. Browsing does not alter ticket state; the launcher writes only its private runtime metadata at `state/dashboard.json`, which is removed on normal shutdown. The dashboard has no chat, ticket editing, or repository execution.
