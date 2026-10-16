#!/usr/bin/env python3
"""Validate SHA-256 manifest for a fresh archive extraction."""
from pathlib import Path
import hashlib
import json
import sys
root=Path(__file__).resolve().parents[1]
records=json.loads((root/'results'/'MANIFEST_SHA256.json').read_text())['files']
for entry in records:
    fp=root/entry['relative_path']
    if fp.stat().st_size!=entry['bytes'] or hashlib.sha256(fp.read_bytes()).hexdigest()!=entry['sha256']:
        raise SystemExit('PAYLOAD_IDENTITY_FAIL '+entry['relative_path'])
print('MANIFEST_PASS',len(records))
