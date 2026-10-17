"""Verify package payload byte hashes, no recursive self-hash."""
import hashlib, json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
manifest=json.loads((base/'MANIFEST_SHA256.json').read_text())
for rel,entry in manifest['files'].items():
    p=base/rel
    data=p.read_bytes()
    if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
        raise RuntimeError(f'PAYLOAD_DIGEST_MISMATCH {rel}')
print(json.dumps({'schema':manifest['schema'],'verified_files':len(manifest['files']),'status':'PASS_PAYLOAD_SHA256'},indent=2))
