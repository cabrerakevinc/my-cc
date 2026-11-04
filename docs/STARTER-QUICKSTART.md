# Your first Command Center

## Install on the Mac that has Claude Code

1. Download and unzip `command-center-starter.zip`.
2. In Terminal, go into the unzipped `command-center-starter` folder.
3. Run `./install.sh` (review the script first). If `cc` is not found in later Terminal sessions, add `~/.local/bin` to your `PATH`.
4. Run:

```bash
cc init ~/work/bbc/command-center --name "BBC Engineering" --profile engineering
cd ~/work/bbc/command-center
cc doctor
claude
```

You can use the globally installed `/cc-init` Skill inside an *empty* command-center directory when creating the next workspace. The `cc init` CLI is also available directly.

## First simulated ticket — without TWG

Open another terminal while still in the BBC command-center directory:

```bash
cc pickup PAY-104 --title "Sample duplicate-payment fix" --sprint DEMO --summary "This is sample data, not Jira data"
cc phase PAY-104 planning
cc checkpoint PAY-104 --summary "Planning scheduled" --next "Create and review a plan" --pause
cc status --state paused
cc resume PAY-104
```

You can now close Claude entirely and later reopen your command center and run `/cc-resume PAY-104` or `cc resume PAY-104`. The checkpoint is stored as actual files.

## Before real coding

- On the company Mac, inspect the approved TWG and AWS MCP CLI commands. Configure only permitted operations; the starter does not yet implement them.
- Plan and explicitly approve the ticket (`cc plan ...`, `cc approve ... --plan`, `cc approve ... --implementation`).
- Register one real repo (`cc repo add payment-service PATH`).
- Launch `cc work PAY-104 --repo payment-service`: this creates/reuses its worktree and starts Claude there, with the approved work order.
- Confirm repo instructions with Claude Code `/context all`; if both `AGENTS.md` and `CLAUDE.md` exist, configure loading both. Singular `AGENT.md` is explicitly called out in the work order.
- Use Claude Code's ordinary `/plan` and `/code-review` as needed. Nothing in this starter replaces them.

**What's saved:** Ticket summary, plan, decisions, handoff, approvals, Git worktree location/branch/HEAD, and optional reported test evidence. What isn't automatically saved: every thought, every tool output, or all chat transcripts. Write important decisions before switching tasks.
