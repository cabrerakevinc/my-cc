# Updating My CC without recreating a workspace

My CC separates the installed commands from local workspace data. Use namespaced
`/cc:*` commands for the normal workflow: every command uses the installed
plugin's bundled Python engine, regardless of the workspace's `.cc/cc` version.

## Normal plugin update

After an updated version is published, run in Claude Code:

```text
/plugin marketplace update my-cc-marketplace
/plugin update cc@my-cc-marketplace
/reload-plugins
```

If the installed Claude version asks for a restart, restart and resume the same
command-center conversation. Current versions document
[`/reload-plugins`](https://code.claude.com/docs/en/commands) for applying pending
plugin changes without restarting. Plugin update/reload changes executable
commands and their Skills; it does not recreate or migrate ticket data.

No workspace upgrade is required to use the updated `/cc:pickup`, `/cc:save`,
`/cc:resume`, `/cc:work`, `/cc:status`, `/cc:draft`, or `/cc:dashboard` commands.

## What stays local

| Workspace content | Plugin update or `/cc:upgrade` behavior |
| --- | --- |
| `workspace.json` | Untouched |
| `state/`, tickets, plans, approvals, decisions, handoffs, repository registrations and SQLite index | Untouched by upgrading; ordinary ticket commands still read/write their intended state |
| `context/`, integration settings and credentials | Untouched |
| `CLAUDE.md`, `MEMORY.md`, `AGENTS.md` and other owner instructions | Untouched |
| Existing local Skills under `.claude/skills/` | Untouched by default |
| `.cc/cc` terminal compatibility snapshot | Refreshed only by explicit workspace upgrade, if recognized as generated |
| `.cc/managed-files.json`, `.cc/backups/`, `.cc/upgrade-candidates/` | Local upgrade tracking, backups and conflict templates |

Data continues to live in the original workspace. An upgrade never uploads it.
Normal Jira or repository operations still follow the configured approved tools.
Existing ticket approval compatibility is covered in the
[planning guide](PLANNING-WORKFLOW.md#state-repeat-saves-and-existing-workspaces).

## Optional: refresh terminal compatibility

Workspaces retain a self-contained `.cc/cc` engine for standalone terminal use.
To refresh it from the **updated installed plugin**, run:

```text
/cc:upgrade
```

This previews the change, then refreshes the recognized generated engine with an
atomic file replacement and backups. **All existing local Skills stay untouched.**
Ticket state, `workspace.json`, context, instruction files and user configuration
are not modified. Repeating an unchanged upgrade is safe and creates no new
backups. Preview alone is available by asking `/cc:upgrade` for a dry run.

From a terminal, use the updated engine's absolute path, not an old workspace
snapshot that may not know the `upgrade` command:

```bash
python3 /path/to/updated/my-cc/cc --workspace /path/to/command-center upgrade --dry-run
python3 /path/to/updated/my-cc/cc --workspace /path/to/command-center upgrade
```

The workspace retains standalone `/cc-*` Skills for compatibility. If you
explicitly want to refresh unchanged generated My CC Skills too, request that
with `/cc:upgrade`, or add `--refresh-skills` to the terminal command. The upgrade
only targets known My CC filenames; unrelated Skills are never touched.
After refreshing standalone Skills, use `/reload-skills` on supported versions
or restart Claude Code to load them. Prefer `/cc:*` for routine use so these
optional snapshots do not become a second update requirement.

## Custom files and older workspaces

New workspaces track hashes of generated files. Older workspaces can be recognized
using the bundled exact hashes of known generated snapshots. A filename alone
never establishes ownership: a customized or unrecognized engine/Skill is
preserved, with a current template under `.cc/upgrade-candidates/` for manual
comparison. The output reports every conflict. A preserved engine conflict means
the terminal snapshot still needs a deliberate manual merge; namespaced plugin
commands already use the updated engine.

Existing files are backed up under `.cc/backups/<unique-upgrade-id>/` before
replacement, including the prior management manifest when it changes. For a
manual rollback, inspect that backup and restore the corresponding files and
manifest together. Customizations are never overwritten merely because backups
exist. Symlinks in managed upgrade paths are refused before writes.

Do not rerun `/cc:init` in an existing workspace. Do not replace `workspace.json`
or restore unrelated user data as an upgrade shortcut. No agent, background
updater, automatic checkpoint hook, or state migration is involved.

## Trying unreleased changes

Updating a published plugin cannot fetch unpublished checkout changes. From your
existing command-center directory, exit Claude Code and load the local source:

```bash
claude --continue --plugin-dir /absolute/path/to/my-cc/plugins/cc
```

Use `--resume <session-id>` to select a particular conversation. This is a
session-only plugin override; it does not publish a version or replace the
marketplace installation. Use its `/cc:*` commands, and optionally `/cc:upgrade`
to refresh standalone compatibility files. A normal marketplace release still
requires an intentional version change and publication; none is performed by
the workspace upgrade command.
