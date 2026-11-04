# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## [0.1.1] — 2026-11-04

- Rename the marketplace plugin to `cc` and its skills to expose `/cc:init`, `/cc:pickup`, `/cc:save`, `/cc:resume`, `/cc:status`, `/cc:work`, and `/cc:draft`.
- Preserve standalone workspace commands, durable tickets, initialization, and repository launching.
- Update packaging checks and installation instructions.
- Document the ticket lifecycle with a README diagram and an end-to-end example.

## [0.1.0] — 2026-11-04

- Initial My CC engine and Claude Code marketplace plugin.
- Ticket checkpointing, plan approval, decision logs, status index, workspace profile scaffolding.
- Worktree launcher with repository-instruction awareness and bounded work orders.
- Local-first design with TWG/AWS integrations explicitly deferred.
