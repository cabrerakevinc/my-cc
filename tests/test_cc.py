import json
import os
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
        expected = {"dashboard", "init", "pickup", "save", "resume", "status", "work", "draft"}
        self.assertEqual({p.name for p in (plugin / "skills").iterdir()}, expected)
        for name in expected:
            text = (plugin / "skills" / name / "SKILL.md").read_text()
            self.assertTrue(text.startswith(f"---\nname: {name}\n"))
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
        plan.write_text("# Plan\nKeep minimal diff.\n")
        self.run_cc("plan", "PAY-104", "--file", str(plan))
        self.run_cc("approve", "PAY-104", "--plan")
        self.run_cc("approve", "PAY-104", "--implementation")
        self.assertIn("Would create worktree", self.run_cc("work", "PAY-104", "--repo", "payment-service", "--dry-run").stdout)
        fakebin = self.root / "fakebin"
        fakebin.mkdir()
        fakeclaude = fakebin / "claude"
        fakeclaude.write_text("#!/bin/sh\nprintf '%s\\n' \"$PWD\" > \"$CC_TEST_WORK_LOG\"\nprintf '%s\\n' \"$CC_WORKSPACE\" >> \"$CC_TEST_WORK_LOG\"\n")
        fakeclaude.chmod(0o755)
        log = self.root / "fakeclaude.log"
        result = self.run_cc("work", "PAY-104", "--repo", "payment-service", env={"PATH": f"{fakebin}:{os.environ.get('PATH', '')}", "CC_TEST_WORK_LOG": str(log)})
        self.assertIn("AGENT.md", result.stdout)
        lines = log.read_text().strip().splitlines()
        self.assertEqual(lines[0], str(self.ws.parent / ".cc-worktrees" / "payment-service" / "PAY-104"))
        self.assertEqual(lines[1], str(self.ws))
        order = self.ws / "state/tickets/PAY/PAY-104/work-orders/payment-service.md"
        self.assertIn("AGENT.md", order.read_text())
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
