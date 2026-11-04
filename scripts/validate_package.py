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
assert entry['source'] == './plugins/cc'
plugin = root / entry['source']
manifest = json.loads((plugin / '.claude-plugin' / 'plugin.json').read_text())
assert entry['name'] == manifest['name'] == 'cc'
assert entry['version'] == manifest['version'] == '0.4.0'
assert (plugin / 'scripts' / 'cc').read_bytes() == (root / 'cc').read_bytes()
for name in ('approve','dashboard','init','pickup','save','resume','status','work','draft','upgrade'):
    skill = plugin / 'skills' / name / 'SKILL.md'
    assert skill.is_file(), skill
    assert skill.read_text().startswith(f'---\nname: {name}\n'), name
# No unconfigured external integration should be installed by this plugin.
assert not (plugin / '.mcp.json').exists()
print('Static marketplace/plugin packaging checks passed.')
print('Run `claude plugin validate ./plugins/cc` and `claude plugin validate .` on a machine with Claude Code.')
