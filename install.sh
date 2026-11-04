#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET="$HOME/.local/share/command-center-starter"
BIN="$HOME/.local/bin"
SKILL="$HOME/.claude/skills/cc-init/SKILL.md"
if [ -e "$BIN/cc" ] || [ -L "$BIN/cc" ]; then
  printf 'Refusing to overwrite existing executable: %s/cc\n' "$BIN" >&2
  printf 'Review and remove/rename the existing file first if replacement is intended.\n' >&2
  exit 1
fi
if [ -e "$SKILL" ]; then
  printf 'Refusing to overwrite existing /cc-init Skill: %s\n' "$SKILL" >&2
  exit 1
fi
mkdir -p "$TARGET" "$BIN"
cp "$ROOT/cc" "$TARGET/cc"
chmod 755 "$TARGET/cc"
ln -s "$TARGET/cc" "$BIN/cc"
"$BIN/cc" install-init-skill
printf 'Installed cc to %s/cc\n' "$BIN"
case ":${PATH}:" in
  *":$BIN:"*) : ;;
  *) printf '\nAdd this to ~/.zshrc if `cc` is not found in new terminals:\nexport PATH="$HOME/.local/bin:$PATH"\n' ;;
esac
