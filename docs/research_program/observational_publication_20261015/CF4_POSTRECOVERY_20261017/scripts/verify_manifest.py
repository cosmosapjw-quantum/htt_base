#!/usr/bin/env python3
"""Verify immutable payload hashes after unpacking research ZIP. Standard library."""
from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parents[1]
obj=json.loads((root/'MANIFEST_SHA256.json').read_text())
for x in obj['files']:
    p=root/x['path']
    if not p.is_file():raise SystemExit(f'MISSING {x["path"]}')
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=x['sha256']:raise SystemExit(f'MISMATCH {x["path"]} {h}')
print('PAYLOAD_HASHES_PASS',len(obj['files']))
