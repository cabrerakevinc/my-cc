#!/usr/bin/env python3
"""Static smoke checks. The authoritative plugin check is `claude plugin validate`."""
import json
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
market = json.loads((root / '.claude-plugin' / 'marketplace.json').read_text())
assert market['name'] == 'my-cc-marketplace'
assert len(market['plugins']) == 1
entry = market['plugins'][0]
assert entry['source'] == './plugins/my-cc'
plugin = root / entry['source']
manifest = json.loads((plugin / '.claude-plugin' / 'plugin.json').read_text())
assert entry['name'] == manifest['name'] == 'my-cc'
assert entry['version'] == manifest['version'] == '0.1.0'
assert (plugin / 'scripts' / 'cc').read_bytes() == (root / 'cc').read_bytes()
for name in ('cc-init','cc-pickup','cc-save','cc-resume','cc-status','cc-work','cc-draft'):
    skill = plugin / 'skills' / name / 'SKILL.md'
    assert skill.is_file(), skill
    assert skill.read_text().startswith('---\n'), name
# No unconfigured external integration should be installed by this plugin.
assert not (plugin / '.mcp.json').exists()
print('Static marketplace/plugin packaging checks passed.')
print('Run `claude plugin validate ./plugins/my-cc` and `claude plugin validate .` on a machine with Claude Code.')
