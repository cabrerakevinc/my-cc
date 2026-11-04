---
name: pickup
description: Start or investigate a ticket with local, persisted context
---

Ticket: $ARGUMENTS
1. Check `python3 .cc/cc show <TICKET>`; if missing, retrieve Jira details using the approved TWG CLI after inspecting available `twg --help` commands. Do not invent flags or use unapproved MCP connectors.
2. Create the local ticket with `python3 .cc/cc pickup <TICKET> --title '...'` and save an accurate `brief.md`. Never fabricate Jira facts.
3. Identify candidate repositories from the ticket, known repo registry, and targeted metadata searches. Avoid scanning all repositories.
4. Investigate only the necessary code, preserving existing repo instructions.
5. Explain findings and proposed scope. Do not edit code, create PRs, or transition Jira at pickup.
