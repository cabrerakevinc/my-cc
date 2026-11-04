import json
import hashlib
import os
import re
import runpy
import shlex
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.request
import urllib.error

CLI = Path(__file__).resolve().parent.parent / "cc"


class PluginPackagingTests(unittest.TestCase):
    def test_plugin_namespace_and_bundled_engine(self):
        root = CLI.parent
        marketplace = json.loads((root / ".claude-plugin/marketplace.json").read_text())
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "cc")
        self.assertEqual(entry["source"], "./plugins/cc")
        plugin = root / entry["source"]
        manifest = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "cc")
        self.assertEqual(manifest["version"], entry["version"])
        self.assertEqual((plugin / "scripts/cc").read_bytes(), CLI.read_bytes())
        expected = {"dashboard", "init", "pickup", "save", "resume", "status", "work", "draft", "upgrade"}
        self.assertEqual({p.name for p in (plugin / "skills").iterdir()}, expected)
        for name in expected:
            text = (plugin / "skills" / name / "SKILL.md").read_text()
            self.assertTrue(text.startswith(f"---\nname: {name}\n"))
            self.assertIn('${CLAUDE_PLUGIN_ROOT}/scripts/cc', text)
            self.assertNotIn('`python3 .cc/cc ', text)
        self.assertIn('${CLAUDE_PLUGIN_ROOT}/scripts/cc', (plugin / "skills/init/SKILL.md").read_text())


class CommandCenterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.ws = self.root / "bbc" / "command-center"
        self.run_cc("init", str(self.ws), "--name", "BBC Engineering", "--profile", "engineering")

    def run_cc(self, *args, success=True, env=None):
        e = os.environ.copy()
        if env:
            e.update(env)
        cp = subprocess.run([sys.executable, str(CLI), *args], cwd=self.ws if self.ws.exists() else self.root, capture_output=True, text=True, env=e)
        if success and cp.returncode != 0:
            self.fail(f"Command failed: {args}\nSTDOUT={cp.stdout}\nSTDERR={cp.stderr}")
        return cp

    def create_ticket(self, tid="PAY-104"):
        self.run_cc("pickup", tid, "--title", "Duplicate payment", "--sprint", "S24", "--summary", "Prevent duplicate charging")

    def test_init_installs_skills_and_private_state(self):
        self.assertTrue((self.ws / "CLAUDE.md").exists())
        self.assertTrue((self.ws / ".claude/skills/cc-save/SKILL.md").exists())
        self.assertTrue((self.ws / ".cc/cc").is_file())
        self.assertIn("python3 .cc/cc", (self.ws / ".claude/skills/cc-save/SKILL.md").read_text())
        self.assertTrue((self.ws / "context/communication/slack.md").exists())
        self.assertIn("state/", (self.ws / ".gitignore").read_text())
        self.assertNotEqual(self.run_cc("init", str(self.ws), "--name", "Clobber", success=False).returncode, 0)

    def recorded_old_engine(self):
        engine = self.ws / ".cc/cc"
        original = b"#!/usr/bin/env python3\nprint('old compatibility engine')\n"
        engine.write_bytes(original)
        manifest = self.ws / ".cc/managed-files.json"
        record = json.loads(manifest.read_text())
        record["hashes"][".cc/cc"] = hashlib.sha256(original).hexdigest()
        manifest.write_text(json.dumps(record))
        return engine, original

    def workspace_snapshot(self):
        return {str(p.relative_to(self.ws)): p.read_bytes()
                for p in self.ws.rglob("*") if p.is_file()}

    def test_upgrade_default_preserves_local_skills_data_and_instructions(self):
        self.create_ticket()
        self.run_cc("checkpoint", "PAY-104", "--summary", "Preserve this state", "--pause")
        (self.ws / "MEMORY.md").write_text("Local durable decisions\n")
        (self.ws / "AGENTS.md").write_text("Owner instructions\n")
        (self.ws / ".claude/skills/cc-save/SKILL.md").write_text("Customized My CC skill\n")
        unrelated = self.ws / ".claude/skills/my-reviewer/SKILL.md"
        unrelated.parent.mkdir()
        unrelated.write_text("My personal reviewer\n")
        engine, original = self.recorded_old_engine()
        before = self.workspace_snapshot()
        preview = self.run_cc("upgrade", "--dry-run")
        self.assertIn("Would refresh: .cc/cc", preview.stdout)
        self.assertEqual(before, self.workspace_snapshot())
        upgraded = self.run_cc("upgrade")
        self.assertIn("1 refreshed, 0 preserved", upgraded.stdout)
        self.assertEqual(engine.read_bytes(), CLI.read_bytes())
        self.assertTrue(os.access(engine, os.X_OK))
        self.assertEqual(subprocess.run([sys.executable, str(engine), "--version"], capture_output=True, text=True).returncode, 0)
        for name, data in before.items():
            if name not in (".cc/cc", ".cc/managed-files.json"):
                self.assertEqual((self.ws / name).read_bytes(), data, name)
        backups = list((self.ws / ".cc/backups").glob("*/.cc/cc"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        after = self.workspace_snapshot()
        self.assertIn("0 refreshed", self.run_cc("upgrade").stdout)
        self.assertEqual(after, self.workspace_snapshot())

    def test_upgrade_opt_in_refreshes_managed_skills_preserves_custom_skills(self):
        self.recorded_old_engine()
        path = self.ws / ".claude/skills/cc-resume/SKILL.md"
        path.write_text("Old generated resume instructions\n")
        manifest = self.ws / ".cc/managed-files.json"
        rec = json.loads(manifest.read_text())
        rec["hashes"][str(path.relative_to(self.ws))] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(rec))
        custom = self.ws / ".claude/skills/cc-save/SKILL.md"
        custom.write_text("My customized save behavior\n")
        before = self.workspace_snapshot()
        self.run_cc("upgrade", "--refresh-skills", "--dry-run")
        self.assertEqual(before, self.workspace_snapshot())
        result = self.run_cc("upgrade", "--refresh-skills")
        self.assertIn("Preserved customized or unrecognized file: .claude/skills/cc-save/SKILL.md", result.stdout)
        self.assertIn("complete saved plan", path.read_text())
        self.assertEqual(custom.read_text(), "My customized save behavior\n")
        candidate = self.ws / ".cc/upgrade-candidates/.claude/skills/cc-save/SKILL.md"
        self.assertIn("complete plan", candidate.read_text())
        # Keeping a conflict never adopts its customized hash as the baseline.
        self.assertNotEqual(json.loads(manifest.read_text())["hashes"][str(custom.relative_to(self.ws))], hashlib.sha256(custom.read_bytes()).hexdigest())
        after = self.workspace_snapshot()
        self.run_cc("upgrade", "--refresh-skills")
        self.assertEqual(after, self.workspace_snapshot())

    def test_upgrade_unknown_legacy_engine_is_preserved_without_reinitializing(self):
        manifest = self.ws / ".cc/managed-files.json"
        manifest.unlink()
        engine = self.ws / ".cc/cc"
        engine.write_text("# Unknown or customized legacy engine\n")
        result = self.run_cc("upgrade")
        self.assertIn("0 refreshed, 1 preserved", result.stdout)
        self.assertEqual(engine.read_text(), "# Unknown or customized legacy engine\n")
        self.assertEqual((self.ws / ".cc/upgrade-candidates/.cc/cc").read_bytes(), CLI.read_bytes())
        self.assertNotIn(".cc/cc", json.loads(manifest.read_text())["hashes"])

    def test_upgrade_recognizes_legacy_generated_skill_without_manifest(self):
        (self.ws / ".cc/managed-files.json").unlink()
        legacy = self.ws / ".claude/skills/cc-save/SKILL.md"
        legacy.write_text('''---
name: cc-save
description: Checkpoint ticket facts, decisions, and next action
---

Ticket: $ARGUMENTS
1. Resolve the ticket with `python3 .cc/cc show <TICKET>`.
2. Distill verified findings and decisions; preserve rejected alternatives and reasons with `python3 .cc/cc decision`.
3. Keep `brief.md`, `plan.md`, and `decisions.md` factual, concise, and current. Do not copy whole transcripts or raw logs.
4. Run `python3 .cc/cc checkpoint <TICKET> --summary '...' --next '...'` and verify it succeeds.
5. Report the exact phase, pause state, and next action. Never claim success unless the command succeeds.
''')
        result = self.run_cc("upgrade", "--refresh-skills")
        self.assertIn("Refresh: .claude/skills/cc-save/SKILL.md", result.stdout)
        self.assertIn("complete plan", legacy.read_text())

    def test_upgrade_rejects_symlinks_and_bad_manifest_before_writes(self):
        self.recorded_old_engine()
        external = self.root / "external-skill.md"
        external.write_text("Do not overwrite me\n")
        target = self.ws / ".claude/skills/cc-save/SKILL.md"
        target.unlink()
        target.symlink_to(external)
        before = self.workspace_snapshot()
        self.assertEqual(self.run_cc("upgrade", "--refresh-skills", success=False).returncode, 2)
        self.assertEqual(before, self.workspace_snapshot())
        self.assertEqual(external.read_text(), "Do not overwrite me\n")
        # Default refresh does not inspect, follow, or modify any local Skill.
        self.run_cc("upgrade")
        self.assertTrue(target.is_symlink())
        manifest = self.ws / ".cc/managed-files.json"
        manifest.write_text('{"format":999,"hashes":{}}')
        before = self.workspace_snapshot()
        self.assertEqual(self.run_cc("upgrade", success=False).returncode, 2)
        self.assertEqual(before, self.workspace_snapshot())

    def test_upgrade_refuses_redirected_candidates_before_refresh(self):
        self.recorded_old_engine()
        outside = self.root / "outside"
        outside.mkdir()
        (self.ws / ".cc/upgrade-candidates").symlink_to(outside, target_is_directory=True)
        before = self.workspace_snapshot()
        self.assertEqual(self.run_cc("upgrade", success=False).returncode, 2)
        self.assertEqual(before, self.workspace_snapshot())
        self.assertEqual(list(outside.iterdir()), [])

    def test_plan_approval_pause_resume_and_index(self):
        self.create_ticket()
        self.assertEqual(self.run_cc("approve", "PAY-104", "--implementation", success=False).returncode, 2)
        new_plan = self.root / "plan.md"
        new_plan.write_text("# Approved approach\n\nReuse existing idempotency records.\n")
        self.run_cc("plan", "PAY-104", "--file", str(new_plan))
        self.run_cc("approve", "PAY-104", "--plan")
        self.run_cc("decision", "PAY-104", "--text", "Do not add Redis", "--reason", "Existing idempotency support")
        self.run_cc("checkpoint", "PAY-104", "--summary", "Plan reviewed", "--next", "Implement next week", "--pause")
        output = self.run_cc("status", "--state", "paused").stdout
        self.assertIn("PAY-104", output)
        res = self.run_cc("resume", "PAY-104").stdout
        self.assertIn("Do not add Redis", res)
        self.assertIn("Implement next week", res)
        self.run_cc("rebuild-index")
        self.assertIn("PAY-104", self.run_cc("status", "--query", "payment").stdout)
        self.run_cc("approve", "PAY-104", "--implementation")
        self.assertIn("implementation authorization: True", self.run_cc("resume", "PAY-104").stdout)

    def ticket_files(self):
        return self.ws / "state/tickets/PAY/PAY-104"

    def guidance_config(self, display="both", enabled=True, maximum=2):
        (self.ws / "workspace.yaml").write_text(
            f"workflow:\n  next_steps:\n    enabled: {str(enabled).lower()}\n"
            f"    display: {display}\n    max_suggestions: {maximum}\n")

    def guidance(self, *args):
        return self.run_cc("next-steps", "PAY-104", *args).stdout

    def save_guidance_plan(self):
        plan = self.root / "native.md"
        plan.write_text("# Full plan\nImplement the fix and run targeted tests.\n")
        self.run_cc("plan", "PAY-104", "--file", str(plan))

    def test_guidance_defaults_native_plan_and_manual_save(self):
        self.assertIn("max_suggestions: 2", (self.ws / "workspace.yaml").read_text())
        created = self.run_cc("pickup", "PAY-104", "--title", "Payment fix").stdout
        self.assertIn("Workflow: PAY-104 · discovered", created)
        self.assertIn("/plan Prepare", created)
        text = self.guidance()
        self.assertIn("same Claude Code session", text)
        self.assertIn("/cc:save PAY-104", text)
        self.assertNotIn("Terminal:", text)  # No native planner/save CLI equivalent.
        self.assertNotIn("/cc:plan", text)
        before = self.workspace_snapshot()
        finalized = self.guidance("--plan-finalized")
        self.assertIn("Next: Save the finalized native plan", finalized)
        self.assertNotIn("/plan Prepare", finalized)
        self.assertEqual(before, self.workspace_snapshot())
        (self.ws / "workspace.yaml").unlink()  # Existing workspaces get defaults.
        self.assertEqual(text, self.guidance())

    def test_guidance_formats_fallbacks_and_maximum(self):
        self.create_ticket()
        self.run_cc("checkpoint", "PAY-104", "--pause")
        for display in ("slash", "cli", "both"):
            with self.subTest(display=display):
                self.guidance_config(display)
                text = self.guidance()
                self.assertEqual("Claude Code:" in text, display != "cli")
                self.assertEqual("Terminal:" in text, display != "slash")
                self.assertIn("PAY-104", text)
        self.run_cc("checkpoint", "PAY-104", "--unpause")
        self.guidance_config("cli", maximum=1)
        text = self.guidance()
        self.assertIn("Claude Code:", text)  # Native /plan has no CLI equivalent.
        self.assertNotIn("Optional:", text)
        self.save_guidance_plan()
        self.guidance_config("slash")
        text = self.guidance()
        self.assertIn("Terminal:", text)  # Approval has no slash equivalent.
        self.assertIn("approve PAY-104 --plan", text)
        self.assertNotIn("/cc:approve", text)
        self.assertIn("/cc-status", self.run_cc("next-steps", "--surface", "standalone").stdout)

    def test_guidance_disabled_and_invalid_configuration(self):
        self.create_ticket()
        self.guidance_config(enabled=False)
        self.assertEqual(self.guidance(), "")
        self.assertEqual(self.run_cc("next-steps").stdout, "")
        self.assertNotIn("Workflow:", self.run_cc("resume", "PAY-104").stdout)
        for key, value in (("display", "unknown"), ("enabled", "yes"),
                           ("max_suggestions", "0"), ("max_suggestions", "-1"),
                           ("max_suggestions", "1.5"), ("unknown", "true")):
            with self.subTest(key=key, value=value):
                (self.ws / "workspace.yaml").write_text(f"workflow:\n  next_steps:\n    {key}: {value}\n")
                cp = self.run_cc("next-steps", "PAY-104", success=False)
                self.assertEqual(cp.returncode, 2)
                self.assertIn("workspace.yaml", cp.stderr)
        cp = self.run_cc("checkpoint", "PAY-104", "--summary", "Still saved")
        self.assertIn("guidance unavailable", cp.stderr)
        self.assertEqual(json.loads((self.ticket_files() / "ticket.json").read_text())["summary"], "Still saved")

    def test_guidance_json_config_and_per_key_precedence(self):
        self.create_ticket()
        self.run_cc("checkpoint", "PAY-104", "--pause")
        path = self.ws / "workspace.json"
        workspace = json.loads(path.read_text())
        workspace["workflow"] = {"next_steps": {"display": "cli"}}
        path.write_text(json.dumps(workspace))
        self.guidance_config("slash", maximum=1)
        before = self.workspace_snapshot()
        text = self.guidance()
        self.assertIn("Terminal:", text)
        self.assertNotIn("Claude Code:", text)
        engine = runpy.run_path(str(CLI))
        self.assertEqual(engine["next_steps_config"](self.ws),
                         {"enabled": True, "display": "cli", "max_suggestions": 1})
        self.assertEqual(before, self.workspace_snapshot())
        (self.ws / "workspace.yaml").unlink()
        for display in ("slash", "cli", "both"):
            with self.subTest(display=display):
                workspace["workflow"]["next_steps"] = {"display": display, "max_suggestions": 1}
                path.write_text(json.dumps(workspace))
                text = self.guidance()
                self.assertEqual("Claude Code:" in text, display != "cli")
                self.assertEqual("Terminal:" in text, display != "slash")
        workspace["workflow"]["next_steps"]["enabled"] = False
        path.write_text(json.dumps(workspace))
        self.assertEqual(self.guidance(), "")
        self.assertNotIn("Workflow:", self.run_cc("resume", "PAY-104").stdout)
        self.guidance_config(enabled=True)
        self.assertEqual(self.guidance(), "")  # JSON disable overrides YAML defaults.

    def test_guidance_json_validates_types_and_structure(self):
        self.create_ticket()
        path = self.ws / "workspace.json"
        workspace = json.loads(path.read_text())
        invalid = [None, [], {"next_steps": None}, {"next_steps": []}]
        invalid += [{"next_steps": {key: value}} for key, value in (
            ("enabled", "false"), ("enabled", 0), ("display", "unknown"),
            ("display", []), ("max_suggestions", True), ("max_suggestions", 0),
            ("max_suggestions", "2"), ("unknown", True))]
        for workflow in invalid:
            with self.subTest(workflow=workflow):
                workspace["workflow"] = workflow
                path.write_text(json.dumps(workspace))
                cp = self.run_cc("next-steps", "PAY-104", success=False)
                self.assertEqual(cp.returncode, 2)
                self.assertIn("workspace.json", cp.stderr)

    def test_guidance_approval_gates_and_content_changes(self):
        self.create_ticket()
        self.save_guidance_plan()
        text = self.guidance()
        self.assertIn("approve PAY-104 --plan", text)
        self.assertNotIn("/cc:work", text)
        self.run_cc("approve", "PAY-104", "--plan")
        text = self.guidance()
        self.assertIn("approve PAY-104 --implementation", text)
        self.assertNotIn("/cc:work", text)
        self.run_cc("approve", "PAY-104", "--implementation")
        before = self.workspace_snapshot()
        text = self.guidance()
        self.assertIn("/cc:work PAY-104", text)
        self.assertNotIn("--repo", text)  # No guessed repository.
        self.assertEqual(before, self.workspace_snapshot())
        path = self.ticket_files() / "ticket.json"
        ticket = json.loads(path.read_text())
        ticket["repos"] = {"payment-service": {}}
        path.write_text(json.dumps(ticket))
        text = self.guidance()
        self.assertIn("work PAY-104 --repo payment-service", text)
        # Every rendered terminal example parses against the real CLI.
        engine = runpy.run_path(str(CLI))
        for command in re.findall(r"Terminal: `([^`]+)`", text):
            parsed = engine["build_parser"]().parse_args(shlex.split(command)[2:])
            self.assertEqual(parsed.ticket, "PAY-104")
        (self.ticket_files() / "plan.md").write_text("# Changed plan\nFresh scope\n")
        before = self.workspace_snapshot()
        self.assertIn("approve PAY-104 --plan", self.guidance())
        self.assertEqual(before, self.workspace_snapshot())

    def test_guidance_blocked_paused_completed_and_delivery_phases(self):
        self.create_ticket()
        self.save_guidance_plan()
        self.run_cc("approve", "PAY-104", "--plan")
        self.run_cc("approve", "PAY-104", "--implementation")
        checks = {"blocked": "Resolve the recorded blockers", "completed": "is completed",
                  "implementing": "implementation progress", "testing": "test evidence",
                  "in-review": "review feedback", "awaiting-deployment": "deployment authorization",
                  "verifying": "Verify deployment evidence"}
        for phase, expected in checks.items():
            with self.subTest(phase=phase):
                self.run_cc("phase", "PAY-104", phase)
                text = self.guidance("--plan-finalized") if phase in ("blocked", "completed") else self.guidance()
                self.assertIn(expected, text)
                self.assertIn(f"Workflow: PAY-104 · {phase}", text)
                self.assertNotIn("/cc:work", text)
        self.run_cc("checkpoint", "PAY-104", "--pause")
        self.assertIn("is paused", self.guidance("--plan-finalized"))
        self.assertIn("/cc-resume PAY-104", self.guidance("--surface", "standalone"))
        path = self.ticket_files() / "ticket.json"
        ticket = json.loads(path.read_text())
        ticket["blockers"] = ["Await security decision"]
        path.write_text(json.dumps(ticket))
        self.assertIn("Resolve the recorded blockers", self.guidance())
        ticket["phase"] = "blocked"
        path.write_text(json.dumps(ticket))
        (self.ticket_files() / "plan.md").write_text("# Direct edit\nNeeds reapproval\n")
        self.assertIn("Resolve the recorded blockers", self.guidance())

    def test_all_skills_query_guidance(self):
        for path in (CLI.parent / "plugins/cc/skills").glob("*/SKILL.md"):
            self.assertIn("next-steps <TICKET>", path.read_text(), str(path))
        for path in (self.ws / ".claude/skills").glob("*/SKILL.md"):
            self.assertIn("next-steps <TICKET> --surface standalone", path.read_text(), str(path))

    def test_full_native_plan_persistence_and_fresh_resume(self):
        self.create_ticket()
        native = self.root / "native-final.md"
        content = "# Native plan\r\n" + "Detailed implementation and test step.\r\n" * 700 + "FINAL CONSTRAINT: no schema change.\r\n"
        native.write_bytes(content.encode())
        self.run_cc("checkpoint", "PAY-104", "--plan-file", str(native),
                    "--summary", "Native plan finalized", "--next", "Review for future implementation", "--pause")
        folder = self.ticket_files()
        self.assertEqual((folder / "plan.md").read_bytes(), native.read_bytes())
        state = json.loads((folder / "ticket.json").read_text())
        self.assertFalse(state["approved_plan"])
        self.assertFalse(state["implementation_approved"])
        self.assertEqual(state["plan_source"], str(native))
        self.assertEqual(state["plan_sha256"], hashlib.sha256(native.read_bytes()).hexdigest())
        self.run_cc("approve", "PAY-104", "--plan")
        self.run_cc("decision", "PAY-104", "--text", "Reuse existing storage", "--reason", "Reject new database")
        self.run_cc("checkpoint", "PAY-104", "--summary", "Approved for next week", "--next", "Revalidate Jira and authorize launch")
        before = {f: f.read_bytes() for f in folder.rglob("*") if f.is_file()}
        native.unlink()  # Native source/session may no longer exist a week later.
        resumed = self.run_cc("resume", "PAY-104").stdout
        self.assertIn(content.replace("\r\n", "\n"), resumed)
        self.assertIn("Reject new database", resumed)
        self.assertIn("Approved plan: True | implementation authorization: False", resumed)
        self.assertIn("Revalidate Jira and authorize launch", resumed)
        for f, data in before.items():
            self.assertEqual(f.read_bytes(), data)  # Resume remains read-only.
        self.assertNotEqual(self.run_cc("work", "PAY-104", "--repo", "missing", success=False).returncode, 0)

    def test_identical_saves_keep_approval_and_changes_reset_both(self):
        self.create_ticket()
        native = self.root / "plan.md"
        native.write_text("# Plan\nTest retries.\n")
        self.run_cc("plan", "PAY-104", "--file", str(native))
        self.run_cc("approve", "PAY-104", "--plan")
        self.run_cc("approve", "PAY-104", "--implementation")
        folder = self.ticket_files()
        approved = json.loads((folder / "ticket.json").read_text())
        for command in ("plan", "checkpoint", "checkpoint"):
            self.run_cc(command, "PAY-104", "--file" if command == "plan" else "--plan-file", str(native))
            saved = json.loads((folder / "ticket.json").read_text())
            for key in ("approved_plan", "implementation_approved", "approved_plan_sha256", "implementation_plan_sha256", "approved_plan_at", "implementation_approved_at"):
                self.assertEqual(saved[key], approved[key])
        native.write_text("# Revised plan\nTest retries and concurrency.\n")
        self.run_cc("checkpoint", "PAY-104", "--plan-file", str(native))
        changed = json.loads((folder / "ticket.json").read_text())
        self.assertFalse(changed["approved_plan"])
        self.assertFalse(changed["implementation_approved"])
        self.assertNotIn("approved_plan_sha256", changed)
        self.assertEqual(changed["phase"], "planning")
        self.assertNotEqual(self.run_cc("approve", "PAY-104", "--implementation", success=False).returncode, 0)

    def test_failed_import_never_claims_or_overwrites_checkpoint(self):
        self.create_ticket()
        folder = self.ticket_files()
        before = {f: f.read_bytes() for f in folder.iterdir() if f.is_file()}
        candidate = self.root / "bad-plan.md"
        for data in (None, b"  ", b"No approved plan yet.", b"\xff\xfe"):
            if data is not None:
                candidate.write_bytes(data)
            result = self.run_cc("checkpoint", "PAY-104", "--plan-file", str(candidate), "--summary", "Must not save", success=False)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Checkpoint saved", result.stdout)
            for f, original in before.items():
                self.assertEqual(f.read_bytes(), original)

    def test_direct_plan_changes_and_missing_plans_block_implementation(self):
        self.create_ticket()
        folder = self.ticket_files()
        native = self.root / "plan.md"
        native.write_text("# Plan\nTest retries.\n")
        self.run_cc("plan", "PAY-104", "--file", str(native))
        self.run_cc("approve", "PAY-104", "--plan")
        self.run_cc("approve", "PAY-104", "--implementation")
        metadata = (folder / "ticket.json").read_bytes()
        (folder / "plan.md").write_text("# Unreviewed edit\nChange API contract.\n")
        self.assertIn("Plan approved: False | Implementation approved: False", self.run_cc("show", "PAY-104").stdout)
        self.assertEqual((folder / "ticket.json").read_bytes(), metadata)
        blocked = self.run_cc("work", "PAY-104", "--repo", "missing", "--dry-run", success=False)
        self.assertIn("Implementation needs", blocked.stderr)
        self.assertNotEqual(self.run_cc("approve", "PAY-104", "--implementation", success=False).returncode, 0)
        self.run_cc("checkpoint", "PAY-104", "--summary", "Plan needs review")
        (folder / "plan.md").write_bytes(native.read_bytes())
        self.assertIn("Plan approved: False", self.run_cc("show", "PAY-104").stdout)
        (folder / "plan.md").unlink()
        self.assertIn("Implementation needs", self.run_cc("work", "PAY-104", "--repo", "missing", success=False).stderr)

    def test_legacy_ticket_preserved_and_requires_content_bound_reapproval(self):
        self.create_ticket()
        folder = self.ticket_files()
        plan = folder / "plan.md"
        plan.write_text("# Legacy reviewed plan\nKeep the existing contract.\n")
        path = folder / "ticket.json"
        state = json.loads(path.read_text())
        state.update(approved_plan=True, implementation_approved=True, custom_field={"keep": "me"})
        path.write_text(json.dumps(state))
        before = path.read_bytes()
        self.assertIn("Approved plan: False | implementation authorization: False", self.run_cc("resume", "PAY-104").stdout)
        self.assertEqual(before, path.read_bytes())
        self.assertNotEqual(self.run_cc("work", "PAY-104", "--repo", "missing", success=False).returncode, 0)
        self.run_cc("approve", "PAY-104", "--plan")
        updated = json.loads(path.read_text())
        self.assertTrue(updated["approved_plan"])
        self.assertFalse(updated["implementation_approved"])
        self.assertEqual(updated["custom_field"], {"keep": "me"})
        self.assertIn("Legacy reviewed plan", plan.read_text())

    def test_repository_worktree_isolation_and_instruction_detection(self):
        self.create_ticket()
        repo = self.ws.parent / "repositories" / "payment-service"
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "AGENT.md").write_text("# Internal guidance\nUse existing patterns.\n")
        (repo / "README.md").write_text("# Payment service\n")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-q", "-m", "init"], check=True)
        self.run_cc("repo", "add", "payment-service", str(repo))
        self.assertIn("Implementation needs", self.run_cc("work", "PAY-104", "--repo", "payment-service", success=False).stderr)
        plan = self.root / "plan.md"
        plan.write_text("# Plan\n" + "Keep minimal diff.\n" * 800 + "FINAL WORKER STEP: test concurrent retries.\n")
        self.run_cc("plan", "PAY-104", "--file", str(plan))
        self.run_cc("approve", "PAY-104", "--plan")
        self.run_cc("approve", "PAY-104", "--implementation")
        preview = self.run_cc("work", "PAY-104", "--repo", "payment-service", "--dry-run").stdout
        self.assertIn("Would create worktree", preview)
        self.assertIn("--permission-mode plan", preview)
        fakebin = self.root / "fakebin"
        fakebin.mkdir()
        fakeclaude = fakebin / "claude"
        fakeclaude.write_text("#!/bin/sh\nprintf '%s\\n' \"$PWD\" > \"$CC_TEST_WORK_LOG\"\nprintf '%s\\n' \"$CC_WORKSPACE\" >> \"$CC_TEST_WORK_LOG\"\n")
        fakeclaude.write_text(fakeclaude.read_text() + "printf '%s\\n' \"$@\" > \"$CC_TEST_WORK_LOG.args\"\n")
        fakeclaude.chmod(0o755)
        log = self.root / "fakeclaude.log"
        result = self.run_cc("work", "PAY-104", "--repo", "payment-service", env={"PATH": f"{fakebin}:{os.environ.get('PATH', '')}", "CC_TEST_WORK_LOG": str(log)})
        self.assertIn("AGENT.md", result.stdout)
        argv = Path(str(log) + ".args").read_text().splitlines()
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "plan")
        self.assertNotIn("--dangerously-skip-permissions", argv)
        lines = log.read_text().strip().splitlines()
        self.assertEqual(lines[0], str(self.ws.parent / ".cc-worktrees" / "payment-service" / "PAY-104"))
        self.assertEqual(lines[1], str(self.ws))
        order = self.ws / "state/tickets/PAY/PAY-104/work-orders/payment-service.md"
        self.assertIn("AGENT.md", order.read_text())
        self.assertIn(plan.read_text(), order.read_text())
        self.assertIn("request explicit implementation approval", order.read_text())
        self.assertIn("MEMORY.md", order.read_text())
        self.assertIn('python3 "$CC_ENGINE" sync', order.read_text())
        self.run_cc("sync", "PAY-104", "--repo", "payment-service", "--summary", "No code changes yet", "--tests", "Not run")
        self.assertTrue((self.ws / "state/tickets/PAY/PAY-104/work-results/payment-service.json").exists())
        self.assertFalse((repo / "state").exists())

    def test_dashboard_http_lifecycle_filters_and_read_only_details(self):
        self.create_ticket()
        self.run_cc("checkpoint", "PAY-104", "--summary", "Investigated retries", "--next", "Review the plan", "--pause")
        directory = self.ws / "state/tickets/PAY/PAY-104"
        (directory / "brief.md").write_text('<script>alert("unsafe")</script>')
        (directory / "work-results").mkdir()
        (directory / "work-results/payment-service.json").write_text('{"tests":"targeted suite passed"}')
        before = {p: p.read_bytes() for p in (self.ws / "state").rglob("*") if p.is_file() and not p.name.startswith("index.sqlite")}
        result = self.run_cc("dashboard", "--background", "--no-browser", "--port", "0")
        runtime = self.ws / "state/dashboard.json"
        rec = json.loads(runtime.read_text())
        base = f'http://127.0.0.1:{rec["port"]}/{rec["token"]}/'
        self.addCleanup(lambda: self.run_cc("dashboard", "--stop"))
        def get(path):
            with urllib.request.urlopen(base + path, timeout=3) as response:
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                return response.read().decode()
        self.assertIn(base, result.stdout)
        self.assertIn("No matching tickets", get(""))
        self.assertIn("PAY-104", get("?state=paused&q=payment"))
        self.assertIn("No matching tickets", get("?state=all&q=absent"))
        detail = get("ticket/PAY-104")
        self.assertIn("/cc:resume PAY-104", detail)
        self.assertIn("targeted suite passed", detail)
        self.assertIn("&lt;script&gt;", detail)
        self.assertNotIn('<script>alert', detail)
        self.run_cc("checkpoint", "PAY-104", "--summary", "New checkpoint")
        self.assertIn("New checkpoint", get("ticket/PAY-104"))
        for path, status in (("../workspace.json", 404), ("ticket/PAY-999", 404)):
            with self.assertRaises(urllib.error.HTTPError) as error:
                get(path)
            self.assertEqual(error.exception.code, status)
        # Documents cannot escape their ticket storage via symlinks.
        external = self.root / "external.txt"
        external.write_text("outside workspace")
        (directory / "brief.md").unlink()
        (directory / "brief.md").symlink_to(external)
        with self.assertRaises(urllib.error.HTTPError) as error:
            get("ticket/PAY-104")
        self.assertEqual(error.exception.code, 404)
        (directory / "brief.md").unlink()
        (directory / "brief.md").write_bytes(before[directory / "brief.md"])
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(urllib.request.Request(base, headers={"Host": "untrusted.example"}), timeout=3)
        self.assertEqual(error.exception.code, 403)
        bad = urllib.request.Request(base, headers={"Origin": "https://example.com"})
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(bad, timeout=3)
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(base.replace(rec["token"], "wrong"), timeout=3)
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(urllib.request.Request(base, method="POST"), timeout=3)
        self.assertEqual(error.exception.code, 405)
        # Repeated launch reuses the same server without replacing its token.
        self.assertIn("already running", self.run_cc("dashboard", "--no-browser").stdout)
        self.assertEqual(rec, json.loads(runtime.read_text()))
        # Browsing leaves authoritative documents unchanged (apart from the explicit checkpoint above).
        for path, data in before.items():
            if path.name not in ("ticket.json", "handoff.md"):
                self.assertEqual(path.read_bytes(), data)
        self.assertIn("stopped", self.run_cc("dashboard", "--stop").stdout)

    def test_two_workspaces_do_not_share_records(self):
        self.create_ticket()
        second = self.root / "bevz" / "command-center"
        self.run_cc("init", str(second), "--name", "BEVZ", "--profile", "business")
        cp = subprocess.run([sys.executable, str(CLI), "status"], cwd=second, capture_output=True, text=True)
        self.assertIn("No matching tickets", cp.stdout)
        self.assertNotIn("PAY-104", cp.stdout)


if __name__ == "__main__":
    unittest.main()
