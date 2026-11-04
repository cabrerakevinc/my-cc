#!/usr/bin/env python3
"""CC: local, dependency-free command center starter.

No vendor API calls are made by this program. External CLIs are detected only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import uuid

VERSION = "0.1.0"
PHASES = (
    "discovered", "investigating", "planning", "ready", "implementing",
    "testing", "in-review", "awaiting-deployment", "verifying", "completed", "blocked",
)
PROFILES = ("engineering", "business", "academic", "general")
TICKET_RE = re.compile(r"^[A-Z][A-Z0-9]{1,15}-[1-9][0-9]{0,9}$")
NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]{0,63}$")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def fail(message, code=2):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def out(message):
    print(message)


def json_read(path: Path, default=None):
    if not path.exists():
        if default is not None:
            return default
        fail(f"Missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        fail(f"Cannot read {path}: {exc}")


def atomic_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".cc-", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        try:
            os.chmod(path, 0o600 if ("state" in path.parts or "context" in path.parts) else 0o644)
        except OSError:
            pass
    finally:
        if os.path.exists(name):
            os.unlink(name)


def json_write(path: Path, obj):
    atomic_write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def workspace_root(args=None) -> Path:
    explicit = getattr(args, "workspace", None)
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if (candidate / "workspace.json").exists():
            return candidate
        fail(f"Not a CC workspace: {candidate}")
    for parent in (Path.cwd(), *Path.cwd().parents):
        if (parent / "workspace.json").exists() and (parent / "state" / "tickets").is_dir():
            return parent
    if os.environ.get("CC_WORKSPACE"):
        candidate = Path(os.environ["CC_WORKSPACE"]).expanduser().resolve()
        if (candidate / "workspace.json").exists():
            return candidate
    fail("No command center found. Run from its directory, pass --workspace, or set CC_WORKSPACE.")


def workspace_config(root: Path):
    return json_read(root / "workspace.json")


def ticket_id(raw: str) -> str:
    value = raw.upper()
    if not TICKET_RE.fullmatch(value):
        fail("Ticket ID must look like PAY-104 or AUTH-203.")
    return value


def ticket_dir(root: Path, value: str) -> Path:
    value = ticket_id(value)
    return root / "state" / "tickets" / value.split("-", 1)[0] / value


def ticket_load(root: Path, value: str):
    path = ticket_dir(root, value) / "ticket.json"
    if not path.exists():
        fail(f"Unknown ticket {value}. Use `cc pickup {value} --title ...` first.")
    return json_read(path)


def db_connect(root: Path):
    db = sqlite3.connect(root / "state" / "index.sqlite", timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    try:
        os.chmod(root / "state" / "index.sqlite", 0o600)
    except OSError:
        pass
    db.execute("""CREATE TABLE IF NOT EXISTS tickets (
      id TEXT PRIMARY KEY, title TEXT, phase TEXT, paused INTEGER, sprint TEXT,
      next_action TEXT, updated_at TEXT, summary TEXT
    )""")
    return db


def index_ticket(root: Path, ticket):
    with db_connect(root) as db:
        db.execute("""INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?)
          ON CONFLICT(id) DO UPDATE SET title=excluded.title, phase=excluded.phase,
          paused=excluded.paused, sprint=excluded.sprint, next_action=excluded.next_action,
          updated_at=excluded.updated_at, summary=excluded.summary""", (
            ticket["id"], ticket["title"], ticket["phase"], int(ticket["paused"]),
            ticket.get("sprint", ""), ticket.get("next_action", ""),
            ticket["updated_at"], ticket.get("summary", ""),
        ))


def ticket_save(root: Path, ticket):
    ticket["updated_at"] = now()
    json_write(ticket_dir(root, ticket["id"]) / "ticket.json", ticket)
    index_ticket(root, ticket)


def skill(name: str, description: str, steps: str, manual: bool = False):
    header = f"---\nname: {name}\ndescription: {description}\n"
    if manual:
        header += "disable-model-invocation: true\n"
    return header + "---\n\n" + textwrap.dedent(steps).strip() + "\n"


def workspace_skills():
    skills = {
        "cc-pickup": skill("cc-pickup", "Start or investigate a ticket with local, persisted context", """
            Ticket: $ARGUMENTS
            1. Check `cc show <TICKET>`; if missing, retrieve Jira details using the approved TWG CLI after inspecting available `twg --help` commands. Do not invent flags or use unapproved MCP connectors.
            2. Create the local ticket with `cc pickup <TICKET> --title '...'` and save an accurate `brief.md`. Never fabricate Jira facts.
            3. Identify candidate repositories from the ticket, known repo registry, and targeted metadata searches. Avoid scanning all repositories.
            4. Investigate only the necessary code, preserving existing repo instructions.
            5. Explain findings and proposed scope. Do not edit code, create PRs, or transition Jira at pickup.
        """),
        "cc-save": skill("cc-save", "Checkpoint ticket facts, decisions, and next action", """
            Ticket: $ARGUMENTS
            1. Resolve the ticket with `cc show <TICKET>`.
            2. Distill verified findings and decisions; preserve rejected alternatives and reasons with `cc decision`.
            3. Keep `brief.md`, `plan.md`, and `decisions.md` factual, concise, and current. Do not copy whole transcripts or raw logs.
            4. Run `cc checkpoint <TICKET> --summary '...' --next '...'` and verify it succeeds.
            5. Report the exact phase, pause state, and next action. Never claim success unless the command succeeds.
        """),
        "cc-resume": skill("cc-resume", "Restore the latest checkpoint for one ticket only", """
            Ticket: $ARGUMENTS
            1. Execute `cc resume <TICKET>` and read only the listed ticket documents as needed.
            2. If the ticket was paused for days, recheck relevant Jira requirements and Git branch/contract changes through approved tools.
            3. Explain new information, decisions, risks, and next action. Do not silently change an approved plan.
            4. If ready to implement, request explicit approval. Coding must occur in a repository-specific session via `cc work`.
        """),
        "cc-status": skill("cc-status", "Summarize sprint tickets without loading all ticket histories", """
            Run `cc status` with the filters requested in $ARGUMENTS. Use the SQLite status index, not the contents of every ticket folder. Summarize blockers, pending decisions, and the next actions. Keep Jira and local phase distinct.
        """),
        "cc-work": skill("cc-work", "Launch repo-specific Claude Code implementation worker", """
            Ticket / repository: $ARGUMENTS
            1. Run `cc show <TICKET>` and verify the approved plan and implementation approval.
            2. Discover/confirm the target repository. Register it first with `cc repo add` if necessary.
            3. Explain that `cc work <TICKET> --repo <REPO>` starts a *separate* Claude Code coding session from that repo's isolated worktree.
            4. Never implement code in the command-center checkout. Repository instructions, including AGENT.md and AGENTS.md, govern implementation details.
            5. Do not perform merge, push, deploy, or Jira Done transitions without separate authorization.
        """, manual=True),
        "cc-draft": skill("cc-draft", "Draft communication using workspace voice and task context", """
            Request: $ARGUMENTS
            Read `context/communication/principles.md` then the relevant `slack.md`, `email.md`, or `stakeholder-updates.md`. If a ticket is named, use `cc resume <TICKET>` for verified facts. Check workspace people/business reference files only when relevant. Produce a draft; do not send messages automatically.
        """),
    }
    return {name: body.replace("`cc ", "`python3 .cc/cc ") for name, body in skills.items()}


def global_init_skill():
    return skill("cc-init", "Initialize an independent CC workspace in the current directory", """
        Initialize a new local command center from the installed `cc` CLI.
        1. Ask for workspace name and profile (engineering, business, academic, general) if missing.
        2. Explain what will be created, and get approval before modifying the filesystem.
        3. Execute `cc init . --name 'WORKSPACE NAME' --profile engineering` using the user's answers.
        4. Do not overwrite an existing workspace or install new external connectors.
        5. Tell the user to run `cc doctor` and `cc status`, and where to edit `context/`.
    """, manual=True)


def create_workspace(args):
    root = Path(args.path).expanduser().resolve()
    if root.exists() and (root / "workspace.json").exists():
        fail(f"Workspace already exists at {root}; initialization is non-destructive.")
    if root.exists() and any(root.iterdir()):
        fail(f"Directory is not empty: {root}. Choose a fresh command-center folder.")
    if args.dry_run:
        out(f"Would initialize {root} with {args.profile} profile and name '{args.name}'.")
        return
    root.mkdir(parents=True, exist_ok=True)
    cfg = {
        "schema_version": 1, "workspace_id": str(uuid.uuid4()),
        "name": args.name, "profile": args.profile, "created_at": now(),
        "repo_base": "../repositories", "worktree_base": "../.cc-worktrees",
        "default_model": "sonnet",
    }
    json_write(root / "workspace.json", cfg)
    json_write(root / "config" / "integrations.json", {
        "atlassian": {"kind": "cli", "binary": "twg", "status": "unconfigured", "commands": {}},
        "aws": {"kind": "cli", "binary": "aws", "status": "unconfigured", "commands": {}},
        "context7": {"kind": "mcp", "status": "use existing Claude Code MCP", "auto_install": False},
    })
    json_write(root / "state" / "repos.json", {})
    (root / "state" / "tickets").mkdir(parents=True, exist_ok=True)
    for protected in (root / "state", root / "state" / "tickets"):
        protected.chmod(0o700)
    with db_connect(root) as db:
        db.execute("SELECT 1")
    atomic_write(root / ".gitignore", "# Private local state and business context (review before sharing)\nstate/\ncontext/\nconfig/integrations.local.json\n.cc/\n.DS_Store\n")
    atomic_write(root / "CLAUDE.md", f"""# {args.name} — Command Center

You are a **coordinator**, not the repository coding session.

- Workspace profile: `{args.profile}`. Use `python3 .cc/cc` for durable state (or global `cc` if installed).
- One ticket = one independently checkpointed workspace. Never load all tickets into context.
- Use TWG for Jira/Bitbucket/Rovo only after discovering approved commands; never invent CLI syntax.
- Use the company's approved AWS CLI/MCP CLI only when configured; prefer read-only diagnostics.
- Context7 is for third-party library documentation, not company source of truth.
- Put work and decisions into `state/tickets/` with `python3 .cc/cc checkpoint` after meaningful milestones.
- Always preserve ticket acceptance criteria, approved scope, and contradictory decisions.
- For coding, run `python3 .cc/cc work TICKET --repo NAME` in a **separate terminal**; this launches Claude **inside the repository worktree**. Do not spawn nested Claude Code processes from within this conversation.
- Repository `CLAUDE.md`, `AGENTS.md`, and `AGENT.md` govern implementation. Report conflicts; never override them with workspace style preferences.
- Never push, merge, deploy, send messages, or transition Jira issues without explicit authorization.
- Do not claim a CLI action succeeded until it actually ran successfully.
- For writing, use communication profiles under `context/communication/` on demand.
- Keep sensitive workspace data separate from other command centers; do not cross-read them.

Supported starter commands: `pickup`, `status`, `resume`, `checkpoint`, `decision`, `approve`, `repo add`, `work`, and `sync` via `python3 .cc/cc`.
""")
    files = {
        "context/identity.md": f"# {args.name}\n\nPurpose: {args.profile} workspace.\n\n## Principles\n- Keep facts distinct from assumptions.\n- Confirm before external actions.\n",
        "context/communication/principles.md": "# Communication voice\n\n- Professional, direct, and conversational.\n- Do not invent commitments, dates, or people's views.\n- Tailor length and detail to the audience.\n",
        "context/communication/slack.md": "# Slack\n\n- Concise, natural, and friendly.\n- Prefer useful status, blockers, and next steps.\n- Do not send without approval.\n",
        "context/communication/email.md": "# Email\n\n- State purpose early; keep the tone helpful and clear.\n- Match the recipient and situation.\n- Do not send without approval.\n",
        "context/communication/stakeholder-updates.md": "# Stakeholder updates\n\n- Start with outcome, then risks, decisions, and next steps.\n- Distinguish confirmed status from forecasts.\n",
        "context/people/directory.md": "# Professional people directory\n\nStore only relevant work roles and communication preferences. Avoid personal or sensitive details.\n",
        "context/business/overview.md": "# Workspace overview\n\nAdd approved business context here.\n",
        "context/business/glossary.md": "# Business glossary\n\nAdd terminology, acronyms, and source references here.\n",
        "context/business/systems.md": "# Systems / services\n\nMaintain high-level service relationships, not code dumps.\n",
        "context/references/index.md": "# Reference index\n\nLink approved local resources and their relevance.\n",
    }
    for name, content in files.items():
        atomic_write(root / name, content)
    (root / "context").chmod(0o700)
    for name, content in workspace_skills().items():
        atomic_write(root / ".claude" / "skills" / name / "SKILL.md", content)
    # Keep a self-contained, versioned CLI in each workspace. The Claude plugin
    # therefore works without requiring a global cc executable or PATH changes.
    local_cli = root / ".cc" / "cc"
    local_cli.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve(), local_cli)
    local_cli.chmod(0o700)
    out(f"Initialized {args.name} at {root}\nNext: cd {root} && python3 .cc/cc doctor && claude")


def install_skill(args):
    target = Path(args.destination).expanduser().resolve() if args.destination else Path.home() / ".claude" / "skills" / "cc-init" / "SKILL.md"
    if target.exists() and not args.force:
        fail(f"Skill exists: {target}. Use --force only if you want to replace it.")
    atomic_write(target, global_init_skill())
    out(f"Installed /cc-init skill at {target}")


def pickup(args):
    root = workspace_root(args)
    value = ticket_id(args.ticket)
    directory = ticket_dir(root, value)
    if directory.exists():
        fail(f"{value} already exists. Use `cc resume {value}`.")
    summary = args.summary or "Not yet investigated."
    directory.mkdir(parents=True, exist_ok=False)
    directory.chmod(0o700)
    directory.parent.chmod(0o700)
    record = {
        "id": value, "title": args.title or "Unverified Jira title", "sprint": args.sprint or "",
        "jira_status": "unknown", "phase": "discovered", "paused": False,
        "summary": summary, "next_action": "Fetch Jira details through approved tools; investigate",
        "approved_plan": False, "implementation_approved": False, "repos": {},
        "created_at": now(), "updated_at": now(), "notes": [],
    }
    ticket_save(root, record)
    brief = "# Brief — " + value + "\n\n**Source:** local draft; verify with Jira.\n\n## Problem\n\n" + summary + "\n\n## Acceptance criteria\n\nNot yet imported.\n"
    if args.brief_file:
        brief = Path(args.brief_file).expanduser().read_text(encoding="utf-8")
    atomic_write(directory / "brief.md", brief)
    atomic_write(directory / "plan.md", f"# Plan — {value}\n\nNo approved plan yet.\n")
    atomic_write(directory / "decisions.md", f"# Decision log — {value}\n\n")
    atomic_write(directory / "handoff.md", f"# Handoff — {value}\n\nCurrent phase: discovered\n\nNext: {record['next_action']}\n")
    out(f"Created {value}: {record['title']}\nFiles: {directory}\nUse `cc checkpoint {value} --summary '...' --next '...'` to save progress.")


def ticket_mutate(args, modifier):
    root = workspace_root(args)
    t = ticket_load(root, args.ticket)
    modifier(root, t)
    ticket_save(root, t)
    return root, t


def phase_cmd(args):
    def change(root, t):
        t["phase"] = args.phase
        if args.next:
            t["next_action"] = args.next
        if args.phase == "completed":
            t["paused"] = False
    _, t = ticket_mutate(args, change)
    out(f"{t['id']}: {t['phase']}")


def decision_cmd(args):
    def change(root, t):
        path = ticket_dir(root, t["id"]) / "decisions.md"
        existing = path.read_text(encoding="utf-8")
        if len(existing) > 250_000:
            fail("Decision log unusually large; archive older material before adding more.")
        entry = f"\n## {now()} — {args.text}\n\nReason: {args.reason or 'Not recorded'}\nStatus: {args.status}\n"
        atomic_write(path, existing + entry)
    _, t = ticket_mutate(args, change)
    out(f"Recorded decision for {t['id']}.")


def plan_cmd(args):
    def change(root, t):
        text = Path(args.file).expanduser().read_text(encoding="utf-8")
        if not text.strip():
            fail("Plan file is empty.")
        atomic_write(ticket_dir(root, t["id"]) / "plan.md", text)
        t["approved_plan"] = False
        t["implementation_approved"] = False
        t["phase"] = "planning"
        t["next_action"] = "Review and approve plan"
    _, t = ticket_mutate(args, change)
    out(f"Updated {t['id']} plan. Previous approval reset; run `cc approve {t['id']} --plan` when approved.")


def approve_cmd(args):
    def change(root, t):
        if args.plan:
            plan = (ticket_dir(root, t["id"]) / "plan.md").read_text(encoding="utf-8")
            if "No approved plan yet." in plan or not plan.strip():
                fail("Cannot approve a placeholder plan. Use `cc plan TICKET --file plan.md`.")
            t["approved_plan"] = True
            t["phase"] = "ready"
            t["next_action"] = "Request implementation approval"
        if args.implementation:
            if not t.get("approved_plan"):
                fail("Approve the implementation plan first.")
            t["implementation_approved"] = True
            t["next_action"] = "Start a repo-specific coding session"
    _, t = ticket_mutate(args, change)
    out(f"{t['id']}: plan approved={t['approved_plan']}, implementation authorized={t['implementation_approved']}")


def checkpoint_cmd(args):
    def change(root, t):
        if args.summary:
            t["summary"] = args.summary
        if args.next:
            t["next_action"] = args.next
        if args.pause:
            t["paused"] = True
        if args.unpause:
            t["paused"] = False
        if args.note:
            t["notes"] = (t.get("notes", []) + [{"at": now(), "text": args.note}])[-50:]
        handoff = f"""# Handoff — {t['id']}

Saved (UTC): {now()}
Phase: {t['phase']}
Paused: {'yes' if t['paused'] else 'no'}
Plan approved: {'yes' if t['approved_plan'] else 'no'}
Implementation approved: {'yes' if t['implementation_approved'] else 'no'}

## Current summary
{t['summary']}

## Next action
{t['next_action']}

## Resumption checklist
- Confirm Jira acceptance criteria and linked issues have not changed.
- Check relevant Git branches, PRs, and service contracts for changes.
- Review any newer decisions before coding.
- Request explicit authorization before any external or high-impact operation.

## Relevant files
- `brief.md` — requirements and acceptance criteria
- `plan.md` — implementation plan
- `decisions.md` — rationale and constraints
"""
        atomic_write(ticket_dir(root, t["id"]) / "handoff.md", handoff)
    _, t = ticket_mutate(args, change)
    out(f"Checkpoint saved for {t['id']} ({t['phase']}; paused={t['paused']}). Next: {t['next_action']}")


def show_cmd(args):
    root = workspace_root(args)
    t = ticket_load(root, args.ticket)
    out(f"{t['id']} — {t['title']}\nPhase: {t['phase']} | Paused: {t['paused']} | Sprint: {t.get('sprint') or '-'}")
    out(f"Jira status: {t.get('jira_status', 'unknown')}\nPlan approved: {t['approved_plan']} | Implementation approved: {t['implementation_approved']}")
    out(f"Summary: {t['summary']}\nNext: {t['next_action']}")
    out(f"Repositories: {', '.join(t.get('repos', {})) or '-'}\nFiles: {ticket_dir(root, t['id'])}")


def resume_cmd(args):
    root = workspace_root(args)
    t = ticket_load(root, args.ticket)
    directory = ticket_dir(root, t["id"])
    out(f"# Resume {t['id']} — {t['title']}")
    out(f"Phase: {t['phase']} | paused={t['paused']} | last saved: {t['updated_at']}")
    out(f"Approved plan: {t['approved_plan']} | implementation authorization: {t['implementation_approved']}")
    out(f"\nSummary: {t['summary']}\nNext: {t['next_action']}")
    for name, max_len in (("handoff.md", 4500), ("decisions.md", 3500), ("plan.md", 6500)):
        content = (directory / name).read_text(encoding="utf-8")
        out(f"\n## {name}\n{content[:max_len]}")
        if len(content) > max_len:
            out(f"[truncated; full file at {directory / name}]")
    out("\nCHECK BEFORE CODING: Refresh Jira requirements and Git branch/contract state if stale.")


def status_cmd(args):
    root = workspace_root(args)
    sql = "SELECT id,title,phase,paused,sprint,next_action,updated_at FROM tickets WHERE 1=1"
    params = []
    if args.sprint:
        sql += " AND sprint=?"
        params.append(args.sprint)
    if args.state:
        if args.state == "paused":
            sql += " AND paused=1"
        elif args.state == "active":
            sql += " AND paused=0 AND phase!='completed'"
        else:
            sql += " AND phase=?"
            params.append(args.state)
    if args.query:
        sql += " AND (id LIKE ? OR title LIKE ? OR summary LIKE ? OR next_action LIKE ?)"
        term = "%" + args.query + "%"
        params += [term] * 4
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(args.limit)
    with db_connect(root) as db:
        rows = db.execute(sql, params).fetchall()
    if not rows:
        out("No matching tickets.")
        return
    out(f"{'TICKET':<15} {'PHASE':<21} {'PAUSED':<7} {'SPRINT':<12} TITLE / NEXT")
    for value, title, phase, paused, sprint, nxt, _ in rows:
        out(f"{value:<15} {phase:<21} {('yes' if paused else 'no'):<7} {(sprint or '-'):<12} {title[:43]} | {nxt[:57]}")
    out(f"{len(rows)} result(s). Use `cc show TICKET` or `cc resume TICKET` for details.")


def rebuild_cmd(args):
    root = workspace_root(args)
    files = list((root / "state" / "tickets").glob("*/*/ticket.json"))
    with db_connect(root) as db:
        db.execute("DELETE FROM tickets")
    for file in files:
        t = json_read(file)
        index_ticket(root, t)
    out(f"Rebuilt ticket index from {len(files)} ticket records.")


def path_inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def repos_read(root):
    return json_read(root / "state" / "repos.json", {})


def repo_add(args):
    root = workspace_root(args)
    if not NAME_RE.fullmatch(args.name):
        fail("Repository name may contain only letters, digits, underscores, dots, and hyphens.")
    path = Path(args.path).expanduser().resolve()
    boundary = root.parent.resolve()
    if not path_inside(path, boundary) and not args.allow_external:
        fail(f"Path {path} is outside workspace area {boundary}; use --allow-external after checking the company boundary.")
    if path.exists() and not (path / ".git").exists():
        result = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if result.returncode != 0:
            fail(f"Not a Git repository: {path}")
    if not path.exists() and not args.remote:
        fail(f"Path does not exist: {path}. Set --remote to register an on-demand clone.")
    repos = repos_read(root)
    if args.name in repos:
        fail(f"Repository {args.name} already registered; no overwrite in starter version.")
    repos[args.name] = {"path": str(path), "remote": args.remote or "", "registered_at": now()}
    json_write(root / "state" / "repos.json", repos)
    out(f"Registered {args.name}: {path} (remote={'configured' if args.remote else 'not set'})")


def repo_list(args):
    root = workspace_root(args)
    repos = repos_read(root)
    if not repos:
        out("No repositories registered. Use `cc repo add NAME PATH [--remote URL]`.")
    for name, repo in sorted(repos.items()):
        out(f"{name}: {repo['path']} | {'cloned' if Path(repo['path']).exists() else 'not cloned'}")


def git_run(repo: Path, *args, check=True):
    cp = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and cp.returncode:
        fail(f"Git command failed in {repo}: {cp.stderr.strip() or cp.stdout.strip()}")
    return cp


def worktree_path(root: Path, name: str, ticket: str):
    cfg = workspace_config(root)
    base = (root / cfg["worktree_base"]).resolve()
    if not path_inside(base, root.parent.resolve()):
        fail("Unsafe worktree base outside workspace area; check workspace.json.")
    return base / name / ticket


def work_cmd(args):
    root = workspace_root(args)
    t = ticket_load(root, args.ticket)
    if not t.get("approved_plan") or not t.get("implementation_approved"):
        fail("Implementation needs an approved plan and explicit authorization. Use `cc approve TICKET --plan`, then `cc approve TICKET --implementation` after human approval.")
    repos = repos_read(root)
    if args.repo not in repos:
        fail(f"Unregistered repository {args.repo}; use `cc repo add` first.")
    record = repos[args.repo]
    repo = Path(record["path"])
    if not repo.exists():
        if not record.get("remote"):
            fail("Repository is missing and has no registered remote.")
        if not args.clone:
            fail(f"Repository not cloned. Re-run with --clone to explicitly clone {args.repo}.")
        if args.dry_run:
            out(f"Would clone {record['remote']} into {repo}")
        else:
            repo.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", record["remote"], str(repo)], check=True)
    if not repo.exists() and not args.dry_run:
        fail(f"Missing repo: {repo}")
    workpath = repo if args.no_worktree else worktree_path(root, args.repo, t["id"])
    branch = f"cc/{t['id'].lower()}"
    base_ref = args.base or "HEAD"
    if not args.no_worktree and not workpath.exists():
        if args.dry_run:
            out(f"Would create worktree at {workpath} for branch {branch}")
        else:
            workpath.parent.mkdir(parents=True, exist_ok=True)
            exists = git_run(repo, "show-ref", "--verify", f"refs/heads/{branch}", check=False).returncode == 0
            if exists:
                git_run(repo, "worktree", "add", str(workpath), branch)
            else:
                git_run(repo, "worktree", "add", "-b", branch, str(workpath), base_ref)
    if workpath.exists() and not args.dry_run:
        git_run(workpath, "rev-parse", "--show-toplevel")
    instruction_files = []
    if workpath.exists():
        for name in ("CLAUDE.md", "AGENTS.md", "AGENT.md", ".claude/CLAUDE.md", ".claude/AGENTS.md"):
            if (workpath / name).exists():
                instruction_files.append(name)
    if not instruction_files:
        out("WARNING: No repository-level instruction file detected at worktree root. Nested files may still apply.")
    if "AGENT.md" in instruction_files:
        out("INFO: AGENT.md (singular) needs explicit reading; launcher includes an instruction to do so.")
    if "AGENTS.md" in instruction_files and "CLAUDE.md" in instruction_files:
        out("INFO: Both CLAUDE.md and AGENTS.md exist. Check Claude Code Project instructions setting 'claude-md-and-agents-md'.")
    folder = ticket_dir(root, t["id"])
    brief = (folder / "brief.md").read_text(encoding="utf-8")[:7000]
    plan = (folder / "plan.md").read_text(encoding="utf-8")[:12000]
    decisions = (folder / "decisions.md").read_text(encoding="utf-8")[-6000:]
    workorder = f"""# Repo-specific implementation work order

Ticket: {t['id']}
Repository: {args.repo}
Ticket title: {t['title']}

The repository and its applicable instructions govern HOW to implement. Jira and the approved ticket plan govern WHAT to deliver. Company policy and safety restrictions take precedence. If constraints conflict, stop and ask. Do not load the command-center workspace's unrelated context. Start by explicitly reading any applicable AGENT.md (singular) and any AGENTS.md/CLAUDE.md not auto-loaded; verify nested instructions when entering subdirectories. Do not assume a file was loaded just because it exists. For both CLAUDE.md and AGENTS.md, confirm the Project instructions setting supports both, or explicitly read the relevant files.

Make the smallest correct change. No unrelated refactoring or dependencies. No commits, pushes, PRs, deployment or Jira transitions without explicit authorization. Always verify actual tests. Report what you changed, tests, limitations and blockers. Before ending, run `python3 "$CC_WORKSPACE/.cc/cc" sync {t['id']} --repo {args.repo} --summary 'concise verified result'` (if approved), or provide a concise manual handoff.

## Requirements
{brief}

## Approved plan
{plan}

## Decisions
{decisions}
"""
    orderpath = folder / "work-orders" / f"{args.repo}.md"
    if not args.dry_run:
        atomic_write(orderpath, workorder)
        actual_base = git_run(workpath, "rev-parse", "HEAD").stdout.strip()
        old = t.setdefault("repos", {}).get(args.repo, {})
        t["repos"][args.repo] = {"path": str(repo), "worktree": str(workpath), "branch": branch if not args.no_worktree else "", "base_sha": old.get("base_sha") or actual_base, "last_sync": old.get("last_sync", "")}
        t["phase"] = "implementing"
        t["paused"] = False
        t["next_action"] = f"Implement and test in {args.repo}"
        ticket_save(root, t)
    argsv = ["claude", "--model", args.model or workspace_config(root)["default_model"], "--name", f"{t['id']}-{args.repo}", "--append-system-prompt-file", str(orderpath), f"Implement ticket {t['id']} in this repository according to the provided approved work order. First confirm local repository instruction files and scope, then ask before changing code if constraints conflict."]
    out(f"Coding location: {workpath}\nRepo instructions detected: {', '.join(instruction_files) or '(none at root)'}")
    if args.dry_run:
        out("Would launch: " + " ".join(argsv[:6]) + " [work-order path] [initial prompt]")
        return
    if not shutil.which("claude"):
        out("Claude Code CLI not found on PATH. Worktree and work order prepared. Install Claude Code then retry `cc work`.")
        return
    env = os.environ.copy()
    env["CC_WORKSPACE"] = str(root)
    out("Launching repository Claude. Use /plan and /code-review normally inside this session.\n")
    try:
        subprocess.run(argsv, cwd=workpath, env=env, check=False)
    finally:
        try:
            sync_cmd(argparse.Namespace(workspace=str(root), ticket=t["id"], repo=args.repo, summary=None, tests=None))
            out("Repository session closed; Git state checkpointed. Preserve decisions and test evidence with /cc-save if not yet recorded.")
        except SystemExit:
            out(f"Repository session closed; automatic sync failed. Run `cc sync {t['id']} --repo {args.repo}`.")


def sync_cmd(args):
    root = workspace_root(args)
    t = ticket_load(root, args.ticket)
    rec = t.get("repos", {}).get(args.repo)
    if not rec:
        fail(f"No work session recorded for {args.repo} on {t['id']}.")
    path = Path(rec["worktree"])
    if not path.exists():
        fail(f"Worktree missing: {path}")
    branch = git_run(path, "branch", "--show-current").stdout.strip()
    sha = git_run(path, "rev-parse", "HEAD").stdout.strip()
    status = git_run(path, "status", "--short").stdout.strip()
    diff = git_run(path, "diff", "--stat", rec.get("base_sha") or "HEAD").stdout.strip()
    resultpath = ticket_dir(root, t["id"]) / "work-results" / f"{args.repo}.json"
    previous = json_read(resultpath, {})
    result = {"at": now(), "branch": branch, "commit": sha, "git_status": status[:6000], "diff_stat": diff[:5000], "summary": args.summary or previous.get("summary", "Not supplied"), "tests": args.tests or previous.get("tests", "Not reported")}
    json_write(resultpath, result)
    rec["last_sync"] = result["at"]
    rec["branch"] = branch
    ticket_save(root, t)
    out(f"Synced {t['id']} / {args.repo}: branch {branch}, HEAD {sha[:12]}. Tests: {result['tests']}")


def doctor_cmd(args):
    root = workspace_root(args)
    cfg = workspace_config(root)
    out(f"CC v{VERSION} | workspace: {cfg['name']} ({cfg['profile']})\nLocation: {root}")
    for binary in ("python3", "git", "claude", "twg", "aws"):
        out(f"  {binary:<10} {'found' if shutil.which(binary) else 'not found (optional unless used)'}")
    out("  Context7: check with `claude /mcp` inside your Claude Code installation.")
    out("  TWG/AWS adapters: not wired automatically; discover and configure approved commands on work machine.")
    count = len(list((root / "state" / "tickets").glob("*/*/ticket.json")))
    out(f"  saved tickets: {count}")
    if (root.parent / "CLAUDE.md").exists():
        out("  WARNING: parent CLAUDE.md exists; verify it contains no unrelated business instructions.")


def build_parser():
    p = argparse.ArgumentParser(prog="cc", description="Local AI command center starter (no vendor credentials or background services)")
    p.add_argument("--workspace", help="Workspace directory (or use CC_WORKSPACE)")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="Initialize an independent workspace")
    s.add_argument("path", nargs="?", default=".")
    s.add_argument("--name", required=True)
    s.add_argument("--profile", choices=PROFILES, default="engineering")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=create_workspace)

    s = sub.add_parser("install-init-skill", help="Install global /cc-init skill")
    s.add_argument("--destination")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=install_skill)

    s = sub.add_parser("pickup", help="Create a ticket record locally (TWG integration to be configured)")
    s.add_argument("ticket")
    s.add_argument("--title")
    s.add_argument("--sprint")
    s.add_argument("--summary")
    s.add_argument("--brief-file")
    s.set_defaults(func=pickup)

    s = sub.add_parser("show", help="Show ticket metadata")
    s.add_argument("ticket")
    s.set_defaults(func=show_cmd)

    s = sub.add_parser("resume", help="Read durable ticket handoff and plan")
    s.add_argument("ticket")
    s.set_defaults(func=resume_cmd)

    s = sub.add_parser("phase", help="Set local phase (not Jira)")
    s.add_argument("ticket")
    s.add_argument("phase", choices=PHASES)
    s.add_argument("--next")
    s.set_defaults(func=phase_cmd)

    s = sub.add_parser("decision", help="Append an immutable decision entry")
    s.add_argument("ticket")
    s.add_argument("--text", required=True)
    s.add_argument("--reason")
    s.add_argument("--status", choices=("proposed", "approved", "superseded"), default="approved")
    s.set_defaults(func=decision_cmd)

    s = sub.add_parser("plan", help="Replace plan with a reviewed file; reset approval")
    s.add_argument("ticket")
    s.add_argument("--file", required=True)
    s.set_defaults(func=plan_cmd)

    s = sub.add_parser("approve", help="Record human-provided approval in local state")
    s.add_argument("ticket")
    group = s.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--implementation", action="store_true")
    s.set_defaults(func=approve_cmd)

    s = sub.add_parser("checkpoint", help="Save handoff and update local ticket status")
    s.add_argument("ticket")
    s.add_argument("--summary")
    s.add_argument("--next")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--pause", action="store_true")
    g.add_argument("--unpause", action="store_true")
    s.add_argument("--note")
    s.set_defaults(func=checkpoint_cmd)

    s = sub.add_parser("status", help="Search tickets from SQLite index")
    s.add_argument("--sprint")
    s.add_argument("--state", choices=("paused", "active", *PHASES))
    s.add_argument("--query")
    s.add_argument("--limit", type=int, default=100)
    s.set_defaults(func=status_cmd)

    s = sub.add_parser("rebuild-index", help="Rebuild disposable SQLite index from ticket JSON files")
    s.set_defaults(func=rebuild_cmd)

    s = sub.add_parser("repo", help="Register and discover repositories")
    repo_sub = s.add_subparsers(dest="repo_action", required=True)
    a = repo_sub.add_parser("add", help="Register repository path/remote")
    a.add_argument("name")
    a.add_argument("path")
    a.add_argument("--remote")
    a.add_argument("--allow-external", action="store_true")
    a.set_defaults(func=repo_add)
    a = repo_sub.add_parser("list", help="List registered repositories")
    a.set_defaults(func=repo_list)

    s = sub.add_parser("work", help="Launch Claude inside a repository worktree")
    s.add_argument("ticket")
    s.add_argument("--repo", required=True)
    s.add_argument("--model", default=None)
    s.add_argument("--base", default="HEAD", help="Base ref for a new worktree, e.g. origin/main; no automatic fetch")
    s.add_argument("--clone", action="store_true", help="Explicitly clone registered remote if absent")
    s.add_argument("--no-worktree", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=work_cmd)

    s = sub.add_parser("sync", help="Record git status and tests for one repo worker")
    s.add_argument("ticket")
    s.add_argument("--repo", required=True)
    s.add_argument("--summary")
    s.add_argument("--tests")
    s.set_defaults(func=sync_cmd)

    s = sub.add_parser("doctor", help="Check local tools and workspace")
    s.set_defaults(func=doctor_cmd)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (FileNotFoundError, PermissionError, subprocess.CalledProcessError) as exc:
        fail(str(exc))


if __name__ == "__main__":
    main()
