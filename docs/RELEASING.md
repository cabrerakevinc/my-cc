# Releasing My CC

## Versioning

Use Semantic Versioning: Git tag `v0.1.0` corresponds to plugin manifest `version: 0.1.0` and the marketplace entry version. Do not reuse a published tag.

## Preflight on your Mac

```bash
cd /Users/kevincabrera/Code/my-cc
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
claude plugin validate ./plugins/my-cc
claude plugin validate .
git status --short
```

Review the files, especially scripts and any company-specific notes. No private workspace state should be included.

## First publication to an empty GitHub repository

**Only use this section if the remote really is empty and the folder is not already a git repo.**

```bash
cd /Users/kevincabrera/Code/my-cc
git init -b main
git remote add origin git@github.com:cabrerakevinc/my-cc.git
git add .
git diff --cached --check
git diff --cached --stat
git commit -m "feat: initial My CC Claude Code marketplace release"
git push -u origin main
git tag -a v0.1.0 -m "My CC v0.1.0"
git push origin v0.1.0
```

If `.git` or `origin` already exists, inspect with `git status`, `git remote -v`, and `git log` first and use the existing history instead of reinitializing or force pushing. If the remote contains initial commits, clone/merge/reconcile it first. **Never force-push.**

## Create GitHub Release

With GitHub CLI authenticated (`gh auth status`):

```bash
gh release create v0.1.0 --repo cabrerakevinc/my-cc \
  --title "My CC v0.1.0 — Initial Release" \
  --notes-file docs/releases/v0.1.0.md
```

Alternatively use GitHub web UI: Releases → Draft a new release → Select tag `v0.1.0` → paste `docs/releases/v0.1.0.md` → Publish release.

## Verify

```bash
git ls-remote --tags origin v0.1.0
gh release view v0.1.0 --repo cabrerakevinc/my-cc
claude plugin marketplace add cabrerakevinc/my-cc
claude plugin install my-cc@my-cc-marketplace
```

This document is a publishing guide, **not evidence that the remote tag/release exists**.
