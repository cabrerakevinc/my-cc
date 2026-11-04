---
name: cc-work
description: Launch repo-specific Claude Code implementation worker
disable-model-invocation: true
---

Ticket / repository: $ARGUMENTS
1. Run `python3 .cc/cc show <TICKET>` and verify the approved plan and implementation approval.
2. Discover/confirm the target repository. Register it first with `python3 .cc/cc repo add` if necessary.
3. Explain that `python3 .cc/cc work <TICKET> --repo <REPO>` starts a *separate* Claude Code coding session from that repo's isolated worktree.
4. Never implement code in the command-center checkout. Repository instructions, including AGENT.md and AGENTS.md, govern implementation details.
5. Do not perform merge, push, deploy, or Jira Done transitions without separate authorization.

**Important:** Run the actual `python3 .cc/cc work ...` command in a *separate terminal*, not via a Bash call from an active Claude Code session. Nested Claude sessions are not the intended execution model.
