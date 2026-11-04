---
name: draft
description: Draft communication using workspace voice and task context
---

Request: $ARGUMENTS
Read `context/communication/principles.md` then the relevant `slack.md`, `email.md`, or `stakeholder-updates.md`. If a ticket is named, use `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cc" resume <TICKET>` for verified facts. Always use this bundled engine, including in older workspaces. Check workspace people/business reference files only when relevant. Produce a draft; do not send messages automatically.
