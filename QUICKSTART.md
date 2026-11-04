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

## Push and release (from your Mac)

See [docs/RELEASING.md](docs/RELEASING.md). An SSH or HTTPS Git credential on your Mac is required. Publishing has **not** been done by packaging the ZIP.

## View your tickets

After updating or installing `cc@my-cc-marketplace`, run `/cc:dashboard` in Claude Code from your initialized workspace. It opens a local read-only dashboard; refresh to see saved changes. Ask the skill to stop the server when finished. See the [dashboard guide](README.md#open-your-dashboard) for terminal commands and existing-workspace compatibility.
