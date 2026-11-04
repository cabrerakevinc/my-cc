# Releasing My CC

## Versioning

Use Semantic Versioning: Git tag `v0.3.0` corresponds to plugin manifest `version: 0.3.0` and the marketplace entry version. Do not reuse a published tag.

## Check publication first

The workspace worktree-setting release is prepared as v0.3.0. Leave all existing tags and releases untouched. Before creating any new tag or release, check both:

```bash
git ls-remote --tags origin 'refs/tags/v0.3.0*'
gh release view v0.3.0 --repo cabrerakevinc/my-cc
```

If either exists, inspect it and choose a new version rather than replacing it. Authentication or network errors do not establish that a release is absent.

## Preflight on your Mac

```bash
cd /Users/kevincabrera/Code/my-cc
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
claude plugin validate ./plugins/cc
claude plugin validate .
git status --short
```

Review the files, especially scripts and any company-specific notes. No private workspace state should be included.

## Commit and tag the reviewed changes

Use the existing repository and history. Review and stage only the intended release files, commit them, and push the release commit before tagging:

```bash
git diff --check
git diff --cached --check
git diff --cached --stat
git commit -m "feat: make worktrees an opt-in workspace setting"
git push origin HEAD
git tag -a v0.3.0 -m "CC v0.3.0"
git push origin v0.3.0
```

Never force-push or replace an existing published tag. Repeat the publication checks immediately before tagging.

## Create GitHub Release

With GitHub CLI authenticated (`gh auth status`):

```bash
gh release create v0.3.0 --repo cabrerakevinc/my-cc \
  --title "CC v0.3.0 — Opt-in workspace worktrees" \
  --notes-file docs/releases/v0.3.0.md
```

Alternatively use GitHub web UI: Releases → Draft a new release → Select tag `v0.3.0` → paste `docs/releases/v0.3.0.md` → Publish release.

## Verify

```bash
git ls-remote --tags origin v0.3.0
gh release view v0.3.0 --repo cabrerakevinc/my-cc
claude plugin marketplace add cabrerakevinc/my-cc
claude plugin install cc@my-cc-marketplace
```

This document is a publishing guide, **not evidence that the remote tag/release exists**.
