# My CC v0.1.1 — Quick start (Mac)

## Place the downloaded source in your preferred directory

The release ZIP contains a single `my-cc/` root. From Terminal on your Mac:

```bash
mkdir -p /Users/kevincabrera/Code
cd /Users/kevincabrera/Code
unzip ~/Downloads/my-cc-v0.1.1-source.zip
cd /Users/kevincabrera/Code/my-cc
```

If `/Users/kevincabrera/Code/my-cc` already exists and has files, **do not extract over it**; inspect and reconcile first.

## Validate and install locally

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
claude plugin validate ./plugins/cc
claude plugin validate .
claude plugin marketplace add /Users/kevincabrera/Code/my-cc
claude plugin install cc@my-cc-marketplace
```

Start Claude Code inside a fresh command-center directory and use `/cc:init`:

```bash
mkdir -p ~/work/bbc/command-center
cd ~/work/bbc/command-center
claude
```

After initialization, use `python3 .cc/cc` for local CLI operations and keep normal `/plan` and `/code-review`.

Prefer namespaced `/cc:*` commands in Claude Code: they use the installed plugin
engine, so existing workspaces receive command updates after a plugin update and
reload. `/cc:upgrade` optionally refreshes terminal `.cc/cc` compatibility. Tickets,
`workspace.json`, context, instructions and existing local Skills stay untouched
by default. See the [upgrade guide](docs/UPGRADING.md).

## Push and release (from your Mac)

See [docs/RELEASING.md](docs/RELEASING.md). An SSH or HTTPS Git credential on your Mac is required. Publishing has **not** been done by packaging the ZIP.

## View your tickets

After updating or installing `cc@my-cc-marketplace`, run `/cc:dashboard` in Claude Code from your initialized workspace. It opens a local read-only dashboard; refresh to see saved changes. Ask the skill to stop the server when finished. See the [dashboard guide](README.md#open-your-dashboard) for terminal commands and existing-workspace compatibility.

For planning that resumes days later: `/cc:pickup TICKET` → native `/plan` in the
same session → finalize and leave without native execution approval → explicitly
accept the revision for future work → `/cc:save TICKET`. Later use `/cc:resume`
and `/cc:work`; authorize launch separately, then approve editing in the repository
session. See the [planning workflow guide](docs/PLANNING-WORKFLOW.md) for exact
plan import, controls, and existing-workspace compatibility.
