# My CC

**Engineering-first, local-first command centers for Claude Code.** Save Jira ticket plans and decisions, pause for days or weeks, resume from durable checkpoints, and launch coding sessions inside the correct repository/worktree so repository-specific instructions remain relevant.

**Version:** `0.1.1` (starter). **Maintainer:** [Kevin Cabrera](https://github.com/cabrerakevinc).

> This project is an independent Claude Code plugin and local Python utility. It is not affiliated with Anthropic, Atlassian, or AWS.

## Install via Claude Code marketplace (recommended)

In Claude Code, run:

```text
/plugin marketplace add cabrerakevinc/my-cc
/plugin install cc@my-cc-marketplace
```

The marketplace commands work **after** this repository has been pushed to GitHub. For local development before pushing:

```bash
cd /Users/kevincabrera/Code/my-cc
claude plugin validate ./plugins/cc
claude plugin validate .
claude plugin marketplace add /Users/kevincabrera/Code/my-cc
claude plugin install cc@my-cc-marketplace
```

Then create and enter a fresh, empty workspace:

```bash
mkdir -p ~/work/bbc/command-center
cd ~/work/bbc/command-center
claude
```

Inside Claude Code invoke **`/cc:init`**. Plugin skills are namespaced, so the plugin's initializer is `/cc:init`, not the built-in `/init` and not the global `/cc-init` from the optional legacy installer. It initializes a workspace with a local, self-contained CLI at `.cc/cc`.

Outside Claude Code, use the generated CLI:

```bash
cd ~/work/bbc/command-center
python3 .cc/cc doctor
python3 .cc/cc pickup PAY-104 --title 'Sample task' --sprint DEMO
python3 .cc/cc checkpoint PAY-104 --summary 'Investigated' --next 'Plan and review' --pause
python3 .cc/cc resume PAY-104
```

Plugin commands are `/cc:init`, `/cc:pickup`, `/cc:save`, `/cc:resume`, `/cc:status`, `/cc:work`, and `/cc:draft`.

To migrate an existing plugin installation, uninstall `my-cc@my-cc-marketplace`, update the marketplace, install `cc@my-cc-marketplace`, and restart Claude Code. Existing workspace files and ticket state remain usable.

The independent workspace also has non-namespaced local `/cc-*` skills, plus the plugin's `/cc:*` skills. You can continue using native Claude Code `/plan` and `/code-review` unchanged.

## Work in a repository, not in the command center

Plan tickets and preserve decisions from the command center. After approving a plan and implementation, run the *actual coding launcher in a separate terminal*:

```bash
cd ~/work/bbc/command-center
python3 .cc/cc repo add payment-service ~/work/bbc/repositories/payment-service
python3 .cc/cc work PAY-104 --repo payment-service --dry-run
python3 .cc/cc work PAY-104 --repo payment-service
```

The launcher creates/reuses an isolated worktree and starts a separate Claude Code conversation from that repository. It calls out applicable `AGENT.md` (singular), `AGENTS.md`, and `CLAUDE.md` instructions; do not assume the singular name is automatically loaded. **Repository engineering conventions govern implementation.** The approved ticket plan governs requirements; if they conflict, Claude must stop and ask.

## Reusable workspaces and persistent context

Use the same plugin to create `~/work/bbc/command-center`, `~/work/bevz/command-center`, or `~/school/mba/command-center`. Each stores its own per-ticket state, SQLite index, `handoff.md`/`decisions.md`/`plan.md`, and business/communication profiles. Workspace `state/` and `context/` are gitignored; verify company policy before syncing work material.

## Integrations and limitations

- **TWG CLI**: intended Atlassian (Jira/Bitbucket/Rovo) integration, but commands are not wired until inspected on the company machine.
- **AWS MCP CLI**: intentionally not automatically configured; follow company authorization and use read-only diagnostics as appropriate.
- **Context7**: reuse the user's existing MCP setup, no auto-install.
- **Release v0.1.0**: local persistence, workspace initialization, repository launching, and skills. **No automatic Jira fetch, PR creation, merge, deploy, or Jira state transitions yet.**
- Python 3.10+ and Git required. Claude Code required for interactive coding; Python CLI uses standard library only.
- Plugin installation does not modify user shell configuration. Optional `./install.sh` installs a global `cc` CLI and unprefixed global `/cc-init`, but is **not necessary** for the marketplace plugin.

Full CLI walkthrough: [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md). Quick start: [QUICKSTART.md](QUICKSTART.md). Release notes: [v0.1.1](docs/releases/v0.1.1.md).

## Development and validation

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
claude plugin validate ./plugins/cc  # requires Claude Code CLI
claude plugin validate .                 # requires Claude Code CLI
```

## Publishing

Follow [docs/RELEASING.md](docs/RELEASING.md) to push to `git@github.com:cabrerakevinc/my-cc.git`, tag the next unpublished version, and create a GitHub Release. A local tag or ZIP is **not** evidence of a published GitHub Release.

## License

No open-source license is granted by default. The maintainer can add an explicit license before encouraging external redistribution or contributions.
