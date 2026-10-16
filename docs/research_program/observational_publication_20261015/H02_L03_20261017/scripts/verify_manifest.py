"""Verify immutable archived payload identities (excluding manifest itself)."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'MANIFEST_SHA256.json').read_text())
assert manifest['schema']=='htt.h02_l03_payload_manifest/1'
for row in manifest['files']:
    p=R/row['path']
    if not p.is_file():sys.exit('missing '+str(p))
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual!=row['sha256'] or p.stat().st_size!=row['size_bytes']:
        sys.exit('HASH/SIZE FAIL '+str(p))
print(f"MANIFEST_VERIFIED {len(manifest['files'])}/{len(manifest['files'])} exact SHA256 payloads")
