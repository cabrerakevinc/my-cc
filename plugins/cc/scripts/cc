#!/usr/bin/env python3
"""CC: local, dependency-free command center starter.

No vendor API calls are made by this program. External CLIs are detected only.
"""
from __future__ import annotations

import html
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import secrets
import shlex
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
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

VERSION = "0.2.0"
PHASES = (
    "discovered", "investigating", "planning", "ready", "implementing",
    "testing", "in-review", "awaiting-deployment", "verifying", "completed", "blocked",
)
PROFILES = ("engineering", "business", "academic", "general")
TICKET_RE = re.compile(r"^[A-Z][A-Z0-9]{1,15}-[1-9][0-9]{0,9}$")
NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]{0,63}$")

# Exact generated snapshots from repository history (v0.1.0-v0.1.2).
# Unknown or customized files are never treated as generated merely by name.
LEGACY_MANAGED_HASHES = {
    ".cc/cc": [
        "85194d8b1551922ecc618aa85f500402c64dda29499db159c71b673872af0f25",
        "01757a4ae395725e92ccfc28fc0e112916caeceb2842e1e9c891892303ab72a6",
        "02368339124a796651af17fe189263fbe08f6e5f2a93e7898e314371d097f6c1",
        "562a12b77c070adcd50ab541b91026369f7392c814021cc62cd6ae379bd56053",
        "d91e277a51f19febe8c9cc69034a63bfadba0db653b219aa47b1b988f3e51bd1"
    ],
    ".claude/skills/cc-dashboard/SKILL.md": [
        "aa8c1d993c01fc0e522c2e4d3cc59786a571a58f802309a20b445b21dc83d214"
    ],
    ".claude/skills/cc-draft/SKILL.md": [
        "e17519424e0220b87a6aa3233aa1c273aca03581a104281fabd6459a9c820c96"
    ],
    ".claude/skills/cc-pickup/SKILL.md": [
        "1908f0f4fa85846e19b9738f8fd3421b6083def1c4690f13719cfd7e66571163",
        "a4d32b6ca4922c843aa63ce349b2e5f06d4b81f1d462192c58c7deaa66d67a5a"
    ],
    ".claude/skills/cc-resume/SKILL.md": [
        "94cf4679befd389731257ff939e6f74cc97f2b852fccc2e45ac8dc136c6ddfde",
        "ee9a5bd092f10187674ed26d81ad1d0ddaec5b64737fe1af6a06b0d1a505ff43"
    ],
    ".claude/skills/cc-save/SKILL.md": [
        "65cc330ccea9d50c034414672b42a4f5b0019f1cfa66a0030f5224fcd5398e48",
        "81d7e775071cdd122e5a3a8e3bd9a7bb7260921024f4b67b5dbd359d18f11573"
    ],
    ".claude/skills/cc-status/SKILL.md": [
        "7eb0a199fc673eeb13f27785c1e0fa6dcfe652f30fe0eff032da56d5723df399"
    ],
    ".claude/skills/cc-work/SKILL.md": [
        "8d3f3f0fbe7b6045d47f71a922f3d1c304ab62e42e46c76e8919e77886336ffd",
        "db737268b68dafac9e2d7cf7dbbc0138ff339abd92e18f102e640a81533b813f"
    ],
    ".claude/skills/cc-upgrade/SKILL.md": [
        "8555390cb4d4f474b46af2c00c862e82355551e34cb6c929b2b57805b31b7b87"
    ]
}


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


NEXT_STEPS_YAML = "workflow:\n  next_steps:\n    enabled: true\n    display: both\n    max_suggestions: 2\n"


def next_steps_config(root):
    """Merge defaults, YAML, then explicit JSON settings (per key)."""
    config = yaml_next_steps_config(root)
    workspace = workspace_config(root)
    workflow = workspace.get("workflow", {})
    if not isinstance(workflow, dict):
        fail("workspace.json: workflow must be an object")
    settings = workflow.get("next_steps", {})
    if not isinstance(settings, dict):
        fail("workspace.json: workflow.next_steps must be an object")
    for key, value in settings.items():
        valid = (
            (key == "enabled" and type(value) is bool)
            or (key == "display" and isinstance(value, str) and value in ("slash", "cli", "both"))
            or (key == "max_suggestions" and type(value) is int and value > 0)
        )
        if not valid:
            fail(f"workspace.json: invalid next_steps.{key}: {value}")
        config[key] = value
    return config


def yaml_next_steps_config(root):
    """Read the guidance block only; retain the dependency-free engine.

    This deliberately supports block mappings and scalar values, not general
    YAML constructs (anchors, tags, flow mappings or multiline values).
    Other workspace sections are ignored, never evaluated.
    """
    config = {"enabled": True, "display": "both", "max_suggestions": 2}
    path = root / "workspace.yaml"
    if not path.exists():
        return config
    stack = []
    seen = set()
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or line.strip() in ("---", "..."):
            continue
        indent = len(line) - len(line.lstrip(" "))
        while stack and indent <= stack[-1][0]:
            stack.pop()
        match = re.fullmatch(r" *([a-zA-Z_][a-zA-Z0-9_-]*):\s*(.*?)", line)
        parents = [key for _, key in stack]
        relevant = parents[:2] == ["workflow", "next_steps"]
        if not match:
            if relevant or line.lstrip().startswith(("workflow:", "next_steps:")):
                fail(f"workspace.yaml:{number}: use block mappings for workflow.next_steps")
            continue
        key, value = match.groups()
        keys = parents + [key]
        if keys in (["workflow"], ["workflow", "next_steps"]):
            if value:
                fail(f"workspace.yaml:{number}: use a block mapping for {'.'.join(keys)}")
        if relevant:
            if len(parents) != 2 or key not in config or key in seen:
                fail(f"workspace.yaml:{number}: unknown or duplicate next_steps setting: {key}")
            seen.add(key)
            value = value.strip("\"'")
            if key == "enabled" and value.lower() in ("true", "false"):
                config[key] = value.lower() == "true"
            elif key == "display" and value in ("slash", "cli", "both"):
                config[key] = value
            elif key == "max_suggestions" and value.isdigit() and int(value) > 0:
                config[key] = int(value)
            else:
                fail(f"workspace.yaml:{number}: invalid next_steps.{key}: {value}")
        if not value:
            stack.append((indent, key))
    return config


def recommend_next_steps(ticket, has_plan, plan_finalized=False, standalone=False):
    """Deterministic actions from effective ticket state; never execute them."""
    tid = ticket["id"]
    prefix = "/cc-" if standalone else "/cc:"

    def action(text, slash=None, cli=None):
        return {"text": text, "slash": slash, "cli": cli}

    resume = action(f"Review the saved handoff for {tid}", f"{prefix}resume {tid}", f"resume {tid}")
    phase = ticket["phase"]
    if phase == "blocked" or ticket.get("blockers"):
        return [action(f"Resolve the recorded blockers for {tid} before continuing; review the handoff",
                       resume["slash"], resume["cli"])]
    if phase == "completed":
        return [action(f"{tid} is completed; review its saved outcome if needed", resume["slash"], resume["cli"])]
    if ticket.get("paused"):
        return [action(f"{tid} is paused; review the handoff before deciding to continue", resume["slash"], resume["cli"])]
    save = action(f"When the native plan for {tid} is finalized, save its exact path or full content manually",
                  f"{prefix}save {tid}")
    if plan_finalized:
        save["text"] = f"Save the finalized native plan for {tid} using its exact path or full content"
        return [save]
    if not has_plan:
        return [action(f"Plan {tid} in this same Claude Code session",
                       f"/plan Prepare the implementation and test plan for {tid}"), save]
    if not ticket.get("approved_plan"):
        return [action(f"Review the saved plan for {tid}; record approval only after explicit acceptance",
                       cli=f"approve {tid} --plan")]
    if not ticket.get("implementation_approved"):
        return [action(f"Request explicit implementation/launch authorization for {tid}; record it only when granted",
                       cli=f"approve {tid} --implementation")]
    if phase in ("discovered", "investigating", "planning", "ready"):
        # Repository selection belongs to the existing work Skill. Render a
        # terminal form only when one repository is already recorded for this ticket.
        repos = list(ticket.get("repos", {}))
        cli = f"work {tid} --repo {shlex.quote(repos[0])}" if len(repos) == 1 else None
        return [action(f"Confirm the repository and prepare the separate-terminal worker for {tid}; native approval is still required before edits",
                       f"{prefix}work {tid}", cli)]
    followup = {
        "implementing": "Review implementation progress and record test evidence",
        "testing": "Review test evidence before preparing review",
        "in-review": "Check review feedback and PR status through approved tools",
        "awaiting-deployment": "Confirm deployment authorization and readiness through the repository workflow",
        "verifying": "Verify deployment evidence and acceptance criteria before marking complete",
    }.get(phase, "Review the saved handoff and recorded next action")
    return [action(f"{followup} for {tid}; start with the saved handoff", resume["slash"], resume["cli"])]


def next_steps_cmd(args):
    root = workspace_root(args)
    config = next_steps_config(root)
    if not config["enabled"]:
        return
    standalone = getattr(args, "surface", "plugin") == "standalone"
    tid = getattr(args, "ticket", None)
    if tid:
        # Preserve blocker/completion priority even if approval validation would
        # otherwise downgrade the effective phase after a direct plan edit.
        ticket = json_read(ticket_dir(root, tid) / "ticket.json")
        saved_phase = ticket["phase"]
        validate_plan_state(root, ticket)
        if saved_phase in ("blocked", "completed"):
            ticket["phase"] = saved_phase
        plan = ticket_dir(root, tid) / "plan.md"
        content = plan.read_text(encoding="utf-8") if plan.exists() else ""
        has_plan = bool(content.strip() and "No approved plan yet." not in content)
        actions = recommend_next_steps(ticket, has_plan, getattr(args, "plan_finalized", False), standalone)
        phase = f"{ticket['id']} · {ticket['phase']}" + (" · paused" if ticket.get("paused") else "")
    else:
        phase = "workspace overview (no ticket selected)"
        prefix = "/cc-" if standalone else "/cc:"
        actions = [{"text": "Select a ticket from workspace status", "slash": prefix + "status", "cli": "status"}]
    out(f"Workflow: {phase}")
    # Use the invoking engine, including a bundled engine in an older workspace.
    engine = f"python3 {shlex.quote(str(Path(__file__).resolve()))} --workspace {shlex.quote(str(root))}"
    for index, action in enumerate(actions[:config["max_suggestions"]]):
        formats = ("slash", "cli") if config["display"] == "both" else (config["display"],)
        available = [kind for kind in formats if action.get(kind)]
        if not available:
            available = [kind for kind in ("slash", "cli") if action.get(kind)]
        commands = []
        for kind in available:
            label = "Claude Code" if kind == "slash" else "Terminal"
            command = action[kind] if kind == "slash" else f"{engine} {action[kind]}"
            commands.append(f"{label}: `{command}`")
        out(f"{'Next' if index == 0 else 'Optional'}: {action['text']}. " + " | ".join(commands))


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
    ticket = json_read(path)
    validate_plan_state(root, ticket)
    return ticket


def plan_digest(root: Path, ticket):
    path = ticket_dir(root, ticket["id"]) / "plan.md"
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def validate_plan_state(root: Path, ticket):
    """Compute effective approvals without writing during read-only commands.

    Legacy booleans cannot prove which revision was approved. Keep documents and
    on-disk metadata intact until an explicit mutation, but require reapproval.
    """
    digest = plan_digest(root, ticket)
    was_approved = ticket.get("approved_plan") or ticket.get("implementation_approved")
    ticket["approved_plan"] = bool(digest and ticket.get("approved_plan")
                                   and ticket.get("approved_plan_sha256") == digest)
    ticket["implementation_approved"] = bool(ticket["approved_plan"]
        and ticket.get("implementation_approved")
        and ticket.get("implementation_plan_sha256") == digest)
    if was_approved and not ticket["approved_plan"]:
        ticket["phase"] = "planning"
        ticket["next_action"] = "Review current plan and record content-bound approval"
        for key in ("approved_plan_sha256", "approved_plan_at"):
            ticket.pop(key, None)
    if not ticket["implementation_approved"]:
        for key in ("implementation_plan_sha256", "implementation_approved_at"):
            ticket.pop(key, None)
    ticket["plan_sha256"] = digest


def import_plan(root: Path, ticket, filename):
    source = Path(filename).expanduser().resolve()
    data = source.read_bytes()
    text = data.decode("utf-8")
    if not text.strip() or "No approved plan yet." in text:
        fail("Plan is empty or a placeholder; provide the complete finalized plan.")
    digest = hashlib.sha256(data).hexdigest()
    changed = digest != plan_digest(root, ticket)
    atomic_write(ticket_dir(root, ticket["id"]) / "plan.md", text)
    if plan_digest(root, ticket) != digest:
        fail("Plan verification failed; approval was not recorded.")
    ticket["plan_source"] = str(source)
    ticket["plan_sha256"] = digest
    if changed:
        ticket["approved_plan"] = False
        ticket["implementation_approved"] = False
        for key in ("approved_plan_sha256", "implementation_plan_sha256",
                    "approved_plan_at", "implementation_approved_at"):
            ticket.pop(key, None)
        ticket["phase"] = "planning"
        ticket["next_action"] = "Review and approve plan"
    return changed


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
        "cc-upgrade": skill("cc-upgrade", "Refresh My CC compatibility files without changing ticket state", """
            Run the updated plugin's /cc:upgrade to refresh this workspace's compatibility engine.
            When using a standalone updated engine, run `cc upgrade --dry-run`, then `cc upgrade`.
            Existing local Skills are untouched by default. Add --refresh-skills only if the user explicitly requests refreshing unchanged generated My CC Skills; customized and unrelated Skills are preserved.
            Do not initialize again, modify workspace.json, ticket state, context or instructions, or install connectors.
        """, manual=True),
        "cc-dashboard": skill("cc-dashboard", "Open the local read-only ticket dashboard", """
            Run `python3 .cc/cc dashboard --background` from the workspace.
            Report the returned URL. Stop with `python3 .cc/cc dashboard --stop`.
            If this workspace has an older CLI, use the updated plugin's /cc:dashboard.
        """, manual=True),
        "cc-pickup": skill("cc-pickup", "Start or investigate a ticket with local, persisted context", """
            Ticket: $ARGUMENTS
            1. Check `cc show <TICKET>`; if missing, retrieve Jira details using the approved TWG CLI after inspecting available `twg --help` commands. Do not invent flags or use unapproved MCP connectors.
            2. Create the local ticket with `cc pickup <TICKET> --title '...'` and save an accurate `brief.md`. Never fabricate Jira facts.
            3. Identify candidate repositories from the ticket, known repo registry, and targeted metadata searches. Avoid scanning all repositories. Record repository paths, branches/HEADs, relevant files, and source references in `brief.md`.
            4. Investigate only the necessary code, reading applicable repository instructions from outermost to innermost directories.
            5. Explain findings and proposed scope. Do not edit code, create PRs, or transition Jira at pickup.
            6. Continue in the same session with native `/plan` for the minimal implementation and testing plan. Do not create a competing /cc:plan command. Keep findings in the conversation until a manual /cc:save.
        """),
        "cc-save": skill("cc-save", "Checkpoint ticket facts, decisions, and next action", """
            Ticket: $ARGUMENTS
            1. Resolve the ticket with `cc show <TICKET>`. This is a manual checkpoint, never permission to implement.
            2. If native planning occurred, locate the exact finalized Markdown plan using the path known in this conversation or supplied by the developer. Native plans default to `~/.claude/plans/`; `plansDirectory` can change that. Never select by newest timestamp, infer ticket ownership from a filename, or inspect private session JSONL/internal mappings. If the exact plan is unavailable or ambiguous, ask for its path or complete content and stop the plan checkpoint until supplied. Do not silently save a summary as the full plan. If content is supplied, write it in full to a ticket-scoped file before importing.
            3. Import the complete plan with `cc plan <TICKET> --file '<EXACT-PATH>'`. This is a file importer, not a planner. Preserve every implementation/testing step, constraint, and alternative; keep only the handoff concise. For a progress save with no new planning, retain the existing plan; an investigation-only checkpoint may remain unapproved.
            4. Preserve verified findings, repository references and observed branches/HEADs in `brief.md`; preserve technical decisions and rejected alternatives with `cc decision <TICKET> --text '...' --reason '...'`. Review existing entries first to avoid duplicates.
            5. Record `cc approve <TICKET> --plan` only when the developer explicitly accepts this exact revision for future implementation. If approval is unclear, ask whether to save it as a draft or approve it for future work. Native execution approval, dismissing a dialog, and requesting a save do not imply this approval. Never run `approve --implementation` as part of saving. Identical imports retain existing approval; changed content resets both approvals.
            6. Run `cc checkpoint <TICKET> --summary '...' --next '...'` (add `--pause` when stopping). Then run `cc show <TICKET>` and read the persisted `plan.md` to verify full content, hash, and effective approval status. Report the exact saved path, phase, approval status, pause state and next action. Never claim success before verification.
        """),
        "cc-resume": skill("cc-resume", "Restore the latest checkpoint for one ticket only", """
            Ticket: $ARGUMENTS
            1. Execute `cc resume <TICKET>` and read the complete saved plan, brief, decisions, and handoff for this ticket only. Resume is read-only; it neither approves implementation nor clears pause state. Content-bound approval is checked against the current plan; legacy unbound approval requires explicit reapproval.
            2. Recheck relevant Jira requirements and repository branch/HEAD, PR and contract changes through approved tools before implementation, especially after days or weeks. Explain what changed; do not reconstruct the entire conversation.
            3. Do not silently change an approved plan. If changes are needed, import the revised full plan and request fresh plan and implementation approvals.
            4. For implementation, use /cc:work to prepare a separate repository session. Request explicit authorization before recording `cc approve <TICKET> --implementation`; saving or approving a plan alone never grants it. The worker starts in native Plan Mode and requests approval before editing.
        """),
        "cc-status": skill("cc-status", "Summarize sprint tickets without loading all ticket histories", """
            Run `cc status` with the filters requested in $ARGUMENTS. Use the SQLite status index, not the contents of every ticket folder. Summarize blockers, pending decisions, and the next actions. Keep Jira and local phase distinct.
        """),
        "cc-work": skill("cc-work", "Launch repo-specific Claude Code implementation worker", """
            Ticket / repository: $ARGUMENTS
            1. Run `cc show <TICKET>` and read the complete saved plan, brief and decisions. Confirm content-bound plan approval and revalidate relevant Jira and repository changes. If the plan changed, import it and obtain fresh approval first.
            2. Request explicit implementation/launch authorization before recording `cc approve <TICKET> --implementation`. Prior plan approval or a saved checkpoint does not grant this authorization. If launch authorization is already recorded for the unchanged plan, do not ask to record it again.
            3. Discover/confirm the target repository. Register it first with `cc repo add` if necessary. Explain the precise `cc work <TICKET> --repo <REPO>` command for a separate terminal; do not run interactive Claude as a nested Bash process.
            4. The launcher starts a separate Claude Code session in the repository's isolated worktree, with the complete saved work package and `--permission-mode plan`. The worker must read applicable repository instructions, revalidate scope, and request implementation approval before source edits. Use native approval there when ready to implement.
            5. Never implement code in the command-center checkout. Repository instructions, including AGENT.md, AGENTS.md, CLAUDE.md and applicable MEMORY.md, retain authority. Check outermost-to-innermost instructions and repeat when entering subfolders.
            6. Do not perform merge, push, deploy, or Jira Done transitions without separate authorization.
        """, manual=True),
        "cc-draft": skill("cc-draft", "Draft communication using workspace voice and task context", """
            Request: $ARGUMENTS
            Read `context/communication/principles.md` then the relevant `slack.md`, `email.md`, or `stakeholder-updates.md`. If a ticket is named, use `cc resume <TICKET>` for verified facts. Check workspace people/business reference files only when relevant. Produce a draft; do not send messages automatically.
        """),
    }
    guidance = """

At completion, run `cc next-steps <TICKET> --surface standalone` for the ticket
involved, or omit <TICKET> when no ticket is selected. Display the returned
Workflow/Next/Optional lines once, preserving command labels and configuration.
If output is empty, omit guidance. Never invent or execute a suggested command.
After native /plan is finalized in this conversation but not imported, add
--plan-finalized to this read-only query; do not infer completion from files or
approval dialogs. Without that signal, show the returned manual save fallback.
"""
    return {name: (body + guidance).replace("`cc ", "`python3 .cc/cc ") for name, body in skills.items()}


def global_init_skill():
    return skill("cc-init", "Initialize an independent CC workspace in the current directory", """
        Initialize a new local command center from the installed `cc` CLI.
        1. Ask for workspace name and profile (engineering, business, academic, general) if missing.
        2. Explain what will be created, and get approval before modifying the filesystem.
        3. Execute `cc init . --name 'WORKSPACE NAME' --profile engineering` using the user's answers.
        4. Do not overwrite an existing workspace or install new external connectors.
        5. Tell the user to run `cc doctor` and `cc status`, and where to edit `context/`.
        6. After successful initialization, run `cc next-steps --surface standalone` from the workspace and display its configured guidance once. Omit guidance if output is empty; never execute the suggestions.
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
    atomic_write(root / "workspace.yaml", NEXT_STEPS_YAML)
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

- Workspace profile: `{args.profile}`. Prefer namespaced `/cc:*` commands with the installed plugin; they use its bundled engine. `python3 .cc/cc` is a standalone compatibility snapshot; refresh it with `/cc:upgrade`. Existing local Skills are untouched by default.
- One ticket = one independently checkpointed workspace. Never load all tickets into context.
- Use TWG for Jira/Bitbucket/Rovo only after discovering approved commands; never invent CLI syntax.
- Use the company's approved AWS CLI/MCP CLI only when configured; prefer read-only diagnostics.
- Context7 is for third-party library documentation, not company source of truth.
- Put work and decisions into `state/tickets/` with `python3 .cc/cc checkpoint` after meaningful milestones.
- Always preserve ticket acceptance criteria, approved scope, and contradictory decisions.
- Use native `/plan` in this session. Leave it without authorizing execution when saving for later. Manual `/cc-save` imports the complete plan; plan approval is separate from implementation authorization.
- For coding, run `python3 .cc/cc work TICKET --repo NAME` in a **separate terminal**; this launches Claude **inside the repository worktree**. Do not spawn nested Claude Code processes from within this conversation.
- Repository `CLAUDE.md`, `AGENTS.md`, and `AGENT.md` govern implementation. Report conflicts; never override them with workspace style preferences.
- Never push, merge, deploy, send messages, or transition Jira issues without explicit authorization.
- Do not claim a CLI action succeeded until it actually ran successfully.
- For writing, use communication profiles under `context/communication/` on demand.
- Keep sensitive workspace data separate from other command centers; do not cross-read them.

Supported starter commands: `pickup`, `status`, `resume`, `checkpoint`, `decision`, `approve`, `repo add`, `work`, `sync`, and read-only `next-steps` via `python3 .cc/cc`. Guidance preferences live under `workflow.next_steps` in `workspace.yaml` or `workspace.json`; explicit JSON settings take precedence.
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
    # Standalone compatibility snapshot. Namespaced plugin Skills use the bundled
    # engine directly, so plugin updates do not depend on refreshing this copy.
    local_cli = root / ".cc" / "cc"
    local_cli.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve(), local_cli)
    local_cli.chmod(0o700)
    json_write(root / ".cc" / "managed-files.json", {
        "format": 1, "hashes": {
            name: hashlib.sha256(data).hexdigest()
            for name, data in managed_workspace_files().items()
        },
    })
    out(f"Initialized {args.name} at {root}\nNext: cd {root} && python3 .cc/cc doctor && claude")


def managed_workspace_files():
    return {
        ".cc/cc": Path(__file__).resolve().read_bytes(),
        **{f".claude/skills/{name}/SKILL.md": body.encode("utf-8")
           for name, body in workspace_skills().items()},
    }


def upgrade_cmd(args):
    """Refresh only recognized generated files; never migrate user data."""
    root = workspace_root(args)
    files = managed_workspace_files()
    names = list(files) if args.refresh_skills else [".cc/cc"]
    manifest = root / ".cc/managed-files.json"
    # Reject redirected paths before creating backups or changing any file.
    directories = {".cc/backups", ".cc/upgrade-candidates"}
    for name in [*names, ".cc/managed-files.json", *directories,
                 *(f".cc/upgrade-candidates/{name}" for name in names)]:
        target = root / name
        for path in (target, *target.parents):
            if path == root:
                break
            if path.is_symlink():
                fail(f"Upgrade refuses a symlink in managed path: {path}")
        if target.exists() and not (target.is_dir() if name in directories else target.is_file()):
            fail(f"Unexpected file type at {target}; nothing upgraded.")
    record = json_read(manifest, {"format": 1, "hashes": {}})
    if not isinstance(record, dict) or record.get("format") != 1 or not isinstance(record.get("hashes"), dict):
        fail("Unsupported managed-files manifest; nothing upgraded.")
    hashes = dict(record["hashes"])
    updates, conflicts = [], []
    for name in names:
        path = root / name
        current = path.read_bytes() if path.exists() else None
        digest = hashlib.sha256(current).hexdigest() if current is not None else None
        desired = hashlib.sha256(files[name]).hexdigest()
        if digest == desired:
            hashes[name] = desired
            out(f"Current: {name}")
        elif current is None or digest == hashes.get(name) or digest in LEGACY_MANAGED_HASHES.get(name, ()):
            updates.append(name)
            hashes[name] = desired
            out(f"{'Would refresh' if args.dry_run else 'Refresh'}: {name}")
        else:
            conflicts.append(name)
            out(f"Preserved customized or unrecognized file: {name}")
    if not args.refresh_skills:
        out("Existing local Skills untouched. Use --refresh-skills only to refresh unchanged generated My CC Skills.")
    if args.dry_run:
        out(f"Preview only: {len(updates)} refresh(es), {len(conflicts)} preserved conflict(s). No files changed.")
        return
    backup = root / ".cc/backups" / (dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    # Back up every existing file before the first replacement. A failed write
    # can be recovered without relying on a Claude session or installed plugin.
    to_backup = [root / name for name in updates if (root / name).exists()]
    new_manifest = {**record, "hashes": hashes}
    manifest_changed = not manifest.exists() or record != new_manifest
    if manifest_changed and manifest.exists():
        to_backup.append(manifest)
    for path in to_backup:
        destination = backup / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    for name in updates:
        atomic_write(root / name, files[name].decode("utf-8"))
        if name == ".cc/cc":
            (root / name).chmod(0o700)
    for name in conflicts:
        candidate = root / ".cc/upgrade-candidates" / name
        atomic_write(candidate, files[name].decode("utf-8"))
        out(f"New template for manual comparison: {candidate}")
    if manifest_changed:
        json_write(manifest, new_manifest)
    if to_backup:
        out(f"Backups: {backup}")
    out(f"Upgrade finished: {len(updates)} refreshed, {len(conflicts)} preserved conflict(s). Ticket state, workspace.json, context and instructions untouched.")


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
        import_plan(root, t, args.file)
    _, t = ticket_mutate(args, change)
    out(f"Saved full {t['id']} plan ({t['plan_sha256']}). Plan approved={t['approved_plan']}; changed content requires fresh approval.")


def approve_cmd(args):
    def change(root, t):
        if args.plan:
            plan = (ticket_dir(root, t["id"]) / "plan.md").read_text(encoding="utf-8")
            if "No approved plan yet." in plan or not plan.strip():
                fail("Cannot approve a placeholder plan. Use `cc plan TICKET --file plan.md`.")
            t["approved_plan"] = True
            t["approved_plan_sha256"] = plan_digest(root, t)
            t["approved_plan_at"] = now()
            t["phase"] = "ready"
            t["next_action"] = "Request implementation approval"
        if args.implementation:
            if not t.get("approved_plan"):
                fail("Approve the implementation plan first.")
            t["implementation_approved"] = True
            t["implementation_plan_sha256"] = plan_digest(root, t)
            t["implementation_approved_at"] = now()
            t["next_action"] = "Start a repo-specific coding session"
    _, t = ticket_mutate(args, change)
    out(f"{t['id']}: plan approved={t['approved_plan']}, implementation authorized={t['implementation_approved']}")


def checkpoint_cmd(args):
    def change(root, t):
        if args.plan_file:
            import_plan(root, t, args.plan_file)
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
Plan SHA-256: {t.get('plan_sha256') or 'not imported'}

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
    root, t = ticket_mutate(args, change)
    out(f"Checkpoint saved for {t['id']} ({t['phase']}; paused={t['paused']}). Next: {t['next_action']}")
    out(f"Plan file: {ticket_dir(root, t['id']) / 'plan.md'}\nPlan SHA-256: {t.get('plan_sha256')}\nPlan approved: {t['approved_plan']} | Implementation approved: {t['implementation_approved']}")


def show_cmd(args):
    root = workspace_root(args)
    t = ticket_load(root, args.ticket)
    out(f"{t['id']} — {t['title']}\nPhase: {t['phase']} | Paused: {t['paused']} | Sprint: {t.get('sprint') or '-'}")
    out(f"Jira status: {t.get('jira_status', 'unknown')}\nPlan approved: {t['approved_plan']} | Implementation approved: {t['implementation_approved']}")
    out(f"Summary: {t['summary']}\nNext: {t['next_action']}")
    out(f"Repositories: {', '.join(t.get('repos', {})) or '-'}\nFiles: {ticket_dir(root, t['id'])}")
    out(f"Plan SHA-256: {t.get('plan_sha256')} | Source: {t.get('plan_source', 'not imported')}")


def resume_cmd(args):
    root = workspace_root(args)
    t = ticket_load(root, args.ticket)
    directory = ticket_dir(root, t["id"])
    out(f"# Resume {t['id']} — {t['title']}")
    out(f"Phase: {t['phase']} | paused={t['paused']} | last saved: {t['updated_at']}")
    out(f"Approved plan: {t['approved_plan']} | implementation authorization: {t['implementation_approved']}")
    out(f"\nSummary: {t['summary']}\nNext: {t['next_action']}")
    for name in ("brief.md", "handoff.md", "decisions.md", "plan.md"):
        content = (directory / name).read_text(encoding="utf-8")
        out(f"\n## {name} ({directory / name})\n{content}")
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
    brief = (folder / "brief.md").read_text(encoding="utf-8")
    plan = (folder / "plan.md").read_text(encoding="utf-8")
    decisions = (folder / "decisions.md").read_text(encoding="utf-8")
    workorder = f"""# Repo-specific implementation work order

Ticket: {t['id']}
Repository: {args.repo}
Ticket title: {t['title']}
Approved plan SHA-256: {t['approved_plan_sha256']}

Before editing code, revalidate relevant Jira requirements and repository state,
explain the intended scope, and request explicit implementation approval in this
repository session. Saved plan approval and launch authorization do not replace
this gate. Start in native Plan Mode; do not edit source before human approval.
Implement only the steps assigned to the named repository. Cross-repository
steps provide context; return a handoff for them rather than editing other repos.

The repository and its applicable instructions govern HOW to implement. Jira and the approved ticket plan govern WHAT to deliver. Company policy and safety restrictions take precedence. If constraints conflict, stop and ask. Do not load the command-center workspace's unrelated context. Start by explicitly reading any applicable AGENT.md (singular) and any AGENTS.md/CLAUDE.md not auto-loaded, plus applicable MEMORY.md, from outermost to innermost directories; verify nested instructions when entering subdirectories. Do not assume a file was loaded just because it exists. For both CLAUDE.md and AGENTS.md, confirm the Project instructions setting supports both, or explicitly read the relevant files.

Make the smallest correct change. No unrelated refactoring or dependencies. No commits, pushes, PRs, deployment or Jira transitions without explicit authorization. Always verify actual tests. Report what you changed, tests, limitations and blockers. Before ending, run `python3 "$CC_ENGINE" sync {t['id']} --repo {args.repo} --summary 'concise verified result'` (if approved), or provide a concise manual handoff.

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
    argsv = ["claude", "--model", args.model or workspace_config(root)["default_model"], "--name", f"{t['id']}-{args.repo}", "--permission-mode", "plan", "--append-system-prompt-file", str(orderpath), f"Review the approved work order for {t['id']}. Confirm local repository instructions, revalidate requirements and repository state, then request implementation approval before editing code. Do not reconstruct or replace the saved plan unless changes are needed."]
    out(f"Coding location: {workpath}\nRepo instructions detected: {', '.join(instruction_files) or '(none at root)'}")
    if args.dry_run:
        out("Would launch: " + " ".join(argsv[:8]) + " [work-order path] [initial prompt]")
        return
    if not shutil.which("claude"):
        out("Claude Code CLI not found on PATH. Worktree and work order prepared. Install Claude Code then retry `cc work`.")
        return
    env = os.environ.copy()
    env["CC_WORKSPACE"] = str(root)
    env["CC_ENGINE"] = str(Path(__file__).resolve())
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


DASHBOARD_STYLE = """
:root{font-family:system-ui,sans-serif;color:#172c32;background:#f2f5f3}*{box-sizing:border-box}
body{margin:0}header{background:#143d39;color:#fff;padding:32px max(24px,calc((100vw - 1160px)/2))}
header p{color:#c5dcd4}main{max-width:1160px;margin:28px auto;padding:0 24px}h1{margin:8px 0;font-size:32px}
a{color:#126658}header a{color:#fff}.eyebrow{text-transform:uppercase;letter-spacing:.15em;font-size:12px}
.stats{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px}.stat,article{background:white;border:1px solid #d8e2dc;border-radius:12px;padding:22px}.stat{flex:1;min-width:150px}.stat strong{display:block;font-size:28px}
form{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:22px}input,select,button{font:inherit;padding:10px 14px;border:1px solid #b6cbc0;border-radius:7px;background:white}input{flex:1;min-width:180px}button{cursor:pointer;background:#155c50;color:white}button:focus,a:focus,input:focus,select:focus{outline:3px solid #d99e36;outline-offset:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px}article h2{font-size:19px}article p{line-height:1.6}.badge{font-size:12px;background:#e6eee8;padding:4px 8px;border-radius:20px}.muted{color:#526860}.next{border-top:1px solid #e0e7e2;padding-top:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.65 ui-monospace,monospace}details{background:white;border:1px solid #d8e2dc;border-radius:10px;margin:14px 0;padding:18px}summary{cursor:pointer;font-weight:600}.empty{padding:40px;border:1px dashed #a5bcb0;border-radius:12px}nav{display:flex;gap:20px;align-items:center;flex-wrap:wrap}footer{margin:30px 0;color:#526860;font-size:13px}
"""


def dashboard_db(root):
    # Never create, rebuild, or update the index while browsing.
    return sqlite3.connect((root / "state/index.sqlite").as_uri() + "?mode=ro", uri=True)


def dashboard_document(root, token, path, query):
    esc = lambda value: html.escape(str(value), quote=True)
    base = f"/{token}/"
    cfg = workspace_config(root)
    body = ""
    if path == "":
        term = query.get("q", [""])[0][:200]
        state = query.get("state", ["active"])[0]
        with dashboard_db(root) as db:
            db.row_factory = sqlite3.Row
            counts = db.execute("SELECT COUNT(*), COALESCE(SUM(phase!='completed' AND paused=0),0), COALESCE(SUM(paused),0) FROM tickets").fetchone()
            sql = "SELECT * FROM tickets WHERE 1=1"
            params = []
            if state == "active": sql += " AND paused=0 AND phase!='completed'"
            elif state == "paused": sql += " AND paused=1"
            elif state in PHASES:
                sql += " AND phase=?"; params.append(state)
            if term:
                sql += " AND (id LIKE ? OR title LIKE ? OR summary LIKE ? OR next_action LIKE ?)"
                params += [f"%{term}%"] * 4
            rows = db.execute(sql + " ORDER BY updated_at DESC", params).fetchall()
        body += '<div class="stats">' + ''.join(f'<div class="stat"><strong>{value}</strong>{label}</div>' for value, label in zip(counts, ('Total tickets', 'Active', 'Paused'))) + '</div>'
        options = ''.join(f'<option value="{s}" {"selected" if state == s else ""}>{esc(s.replace("-", " ").title())}</option>' for s in ('active', 'paused', 'all', *PHASES))
        body += f'<form><input aria-label="Search tickets" name="q" placeholder="Search tickets or next actions" value="{esc(term)}"><select aria-label="Ticket phase" name="state">{options}</select><button>Filter tickets</button></form><div class="grid">'
        for row in rows:
            body += f'<article><span class="badge">{esc(row["phase"])}{" · paused" if row["paused"] else ""}</span><h2><a href="{base}ticket/{esc(row["id"])}">{esc(row["id"])} · {esc(row["title"])}</a></h2><p>{esc(row["summary"] or "No summary saved yet.")}</p><p class="next"><b>Next</b> · {esc(row["next_action"] or "Not recorded")}</p><small class="muted">Sprint {esc(row["sprint"] or "—")} · {esc(row["updated_at"])}</small></article>'
        body += '</div>'
        if not rows: body += '<p class="empty">No matching tickets. Pick up a ticket in Claude Code, or change your filters.</p>'
    elif path.startswith("ticket/"):
        tid = path.removeprefix("ticket/")
        if not TICKET_RE.fullmatch(tid): raise FileNotFoundError()
        directory = root / 'state/tickets' / tid.split('-')[0] / tid
        def read_safe(file):
            if not file.resolve().is_relative_to((root / 'state/tickets').resolve()): raise FileNotFoundError()
            return file.read_text(encoding='utf-8')
        ticket = json.loads(read_safe(directory / 'ticket.json'))
        if (directory / 'plan.md').exists():
            read_safe(directory / 'plan.md')  # Preserve document path confinement.
        validate_plan_state(root, ticket)
        body = f'<p><a href="{base}">← All tickets</a></p><h1>{esc(tid)} · {esc(ticket["title"])}</h1><p>{esc(ticket["phase"])} · {"Paused" if ticket["paused"] else "Active"}</p><p>Plan approved: {esc(ticket.get("approved_plan", False))} · Implementation authorized: {esc(ticket.get("implementation_approved", False))}</p><p><b>Next:</b> {esc(ticket.get("next_action", ""))}</p><article><label for="resume">Resume in Claude Code</label><p><input id="resume" readonly value="/cc:resume {esc(tid)}"> <button id="copy">Copy resume command</button><span id="copied" role="status"></span></p></article>'
        for name in ('brief.md', 'plan.md', 'decisions.md', 'handoff.md'):
            file = directory / name
            content = read_safe(file) if file.exists() else 'No saved document yet.'
            body += f'<details open><summary>{esc(name)}</summary><pre>{esc(content)}</pre></details>'
        for folder in ('work-orders', 'work-results'):
            for file in sorted((directory / folder).glob('*')):
                if file.suffix not in ('.md', '.json') or not file.is_file(): continue
                body += f'<details><summary>{esc(folder + "/" + file.name)}</summary><pre>{esc(read_safe(file))}</pre></details>'
    else: raise FileNotFoundError()
    script = "document.getElementById('copy')?.addEventListener('click',async()=>{const i=document.getElementById('resume');try{await navigator.clipboard.writeText(i.value);document.getElementById('copied').textContent=' Copied';}catch(e){i.select();document.getElementById('copied').textContent=' Select and copy the command';}});"
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(cfg["name"])} · CC dashboard</title><style>{DASHBOARD_STYLE}</style><header><span class="eyebrow">CC / Workspace overview</span><h1>{esc(cfg["name"])}</h1><p>Your tickets, decisions, and next steps.</p><nav><a href="{base}">Tickets</a><a href="">Refresh</a><span>Read-only · local workspace</span></nav></header><main>{body}<footer>Saved state only. Refresh for updates. Continue implementation in Claude Code.</footer></main><script>{script}</script></html>'


def dashboard_server(root, port, token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # Do not log token URLs or ticket data.
        def respond(self, status, content, kind='text/plain; charset=utf-8'):
            data = content.encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)
        def authorized(self):
            expected = f'127.0.0.1:{self.server.server_port}'
            return self.headers.get('Host') == expected and self.path.startswith(f'/{token}/') and self.headers.get('Origin', f'http://{expected}') == f'http://{expected}'
        def do_GET(self):
            if not self.authorized(): return self.respond(403, 'Forbidden')
            parsed = urllib.parse.urlsplit(self.path)
            path = parsed.path[len(token)+2:]
            if path == 'health': return self.respond(200, str(root))
            try:
                page = dashboard_document(root, token, path, urllib.parse.parse_qs(parsed.query))
                self.respond(200, page, 'text/html; charset=utf-8')
            except (FileNotFoundError, ValueError, KeyError): self.respond(404, 'Ticket not found')
            except (OSError, sqlite3.Error): self.respond(503, 'Cannot read workspace. Check its files and run rebuild-index from the CLI if needed.')
        def do_POST(self):
            if not self.authorized(): return self.respond(403, 'Forbidden')
            if self.path != f'/{token}/stop': return self.respond(405, 'Read-only dashboard')
            self.respond(200, 'Dashboard stopped')
            threading.Thread(target=self.server.shutdown, daemon=True).start()
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def dashboard_cmd(args):
    root = workspace_root(args)
    if not 0 <= args.port <= 65535: fail('Port must be between 0 and 65535.')
    runtime = root / 'state/dashboard.json'
    running = None
    if runtime.exists():
        try:
            rec = json.loads(runtime.read_text())
            url = f'http://127.0.0.1:{int(rec["port"])}/{rec["token"]}/'
            with urllib.request.urlopen(url + 'health', timeout=1) as response:
                if response.read().decode() == str(root): running = url
        except (OSError, ValueError, KeyError): pass
    if args.stop:
        if running:
            urllib.request.urlopen(urllib.request.Request(running + 'stop', method='POST'), timeout=3).close()
            out('Dashboard stopped.')
        else: out('No running dashboard for this workspace.')
        return
    if running:
        out(f'Dashboard already running: {running}')
        if not args.no_browser: webbrowser.open(running)
        return
    if args.background:
        command = [sys.executable, str(Path(__file__).resolve()), '--workspace', str(root), 'dashboard', '--port', str(args.port), '--no-browser']
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        for _ in range(50):
            time.sleep(.1)
            if process.poll() is not None: fail('Dashboard could not start. Try foreground mode to see the error.')
            if runtime.exists():
                try:
                    rec = json.loads(runtime.read_text())
                    url = f'http://127.0.0.1:{int(rec["port"])}/{rec["token"]}/'
                    with urllib.request.urlopen(url + 'health', timeout=.2) as response:
                        if response.read().decode() != str(root): continue
                    out(f'Dashboard: {url}')
                    if not args.no_browser: webbrowser.open(url)
                    return
                except (OSError, ValueError, KeyError): pass
        process.terminate()
        process.wait(timeout=3)
        fail('Dashboard startup timed out. Try foreground mode.')
    token = secrets.token_urlsafe(24)
    try: server = dashboard_server(root, args.port, token)
    except OSError as exc: fail(f'Cannot start dashboard: {exc}. Try --port 0 for a free port.')
    url = f'http://127.0.0.1:{server.server_port}/{token}/'
    json_write(runtime, {'port': server.server_port, 'token': token})
    print(f'Dashboard: {url}\nStop with Ctrl+C or dashboard --stop.', flush=True)
    if not args.no_browser: webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        server.server_close()
        if runtime.exists() and json.loads(runtime.read_text()).get('token') == token: runtime.unlink()


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

    s = sub.add_parser("upgrade", help="Refresh generated compatibility engine; preserve workspace data and custom files")
    s.add_argument("--dry-run", action="store_true", help="Preview without writing anything")
    s.add_argument("--refresh-skills", action="store_true", help="Also refresh unchanged generated My CC Skills; preserve custom Skills")
    s.set_defaults(func=upgrade_cmd)

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

    s = sub.add_parser("next-steps", help="Display configured workflow guidance without changing or executing anything")
    s.add_argument("ticket", nargs="?")
    s.add_argument("--surface", choices=("plugin", "standalone"), default="plugin", help="Installed slash-command names (default: plugin)")
    s.add_argument("--plan-finalized", action="store_true", help="Manual conversation hint: native plan finalized but not imported; does not record approval")
    s.set_defaults(func=next_steps_cmd)

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

    s = sub.add_parser("plan", help="Import a full plan file; changed content resets approvals")
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
    s.add_argument("--plan-file", help="Import the exact native/exported plan; never infer approval")
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

    s = sub.add_parser("dashboard", help="Open the local read-only ticket dashboard")
    s.add_argument("--port", type=int, default=8765, help="Loopback port; 0 selects a free port")
    s.add_argument("--no-browser", action="store_true")
    group = s.add_mutually_exclusive_group()
    group.add_argument("--background", action="store_true", help="Run independently of this terminal")
    group.add_argument("--stop", action="store_true", help="Stop this workspace's running dashboard")
    s.set_defaults(func=dashboard_cmd)

    s = sub.add_parser("doctor", help="Check local tools and workspace")
    s.set_defaults(func=doctor_cmd)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
        if args.command in ("pickup", "show", "resume", "phase", "decision", "plan", "approve", "checkpoint", "sync", "work"):
            # Guidance must not turn a successful ticket operation into a
            # reported failure, e.g. when optional workspace YAML is malformed.
            try:
                args.surface = "standalone"
                next_steps_cmd(args)
            except (SystemExit, OSError, UnicodeError):
                print("Workflow guidance unavailable; check workspace.yaml and workspace.json.", file=sys.stderr)
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        fail(str(exc))


if __name__ == "__main__":
    main()
