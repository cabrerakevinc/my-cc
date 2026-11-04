# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## [0.3.0] — 2026-11-04

- **Breaking:** `cc work` now uses the registered clone/current checkout by default, including for existing workspaces with no `worktrees` key. `cc upgrade` preserves `workspace.json` and existing worktree records; it does not infer or migrate the setting. Set `"worktrees": true` in `workspace.json` before upgrading to retain worktree launches and reuse existing ticket worktrees, or pass `--worktree` for one run. `--no-worktree` forces the clone. Existing worktrees are left on disk.
- Record the actual branch in both launch modes, show it with `cc show`, and print the working path and a ready-to-run `git log` command. Checkout mode preserves the current branch and uncommitted changes; `--base` remains limited to new worktree branches and does not fetch.

## [0.2.0] — 2026-11-04

- Add deterministic, read-only `next-steps` guidance after ticket commands and Skills.
- Configure guidance in `workspace.yaml` or `workspace.json`: enabled, preferred command formats, and maximum suggestions; explicit JSON values override YAML per setting.
- Preserve native `/plan`, manual save fallback, approval gates, and paused/blocked states.
- Add guidance tests and configuration documentation.
- Preserve complete native plans with content-bound approvals and safe workspace compatibility upgrades.

## [0.1.2] — 2026-11-04

- Add `/cc:dashboard`, workspace `/cc-dashboard`, and the `dashboard` CLI command.
- Browse active and paused tickets, filter phases, search, inspect saved documents and reported test evidence, and copy resume commands.
- Add loopback-only serving, private URL tokens, background launch/reuse, and explicit shutdown.
- Keep ticket browsing read-only and support older workspaces through the bundled plugin engine.
- Add dashboard integration tests and launch/stop documentation.

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
