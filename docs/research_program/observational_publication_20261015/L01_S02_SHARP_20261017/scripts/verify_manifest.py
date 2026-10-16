from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];d=json.loads((root/'MANIFEST_SHA256.json').read_text());n=0
for path,signature in d['files'].items():
 p=root/path
 if not p.exists():raise SystemExit('MISSING '+path)
 got=hashlib.sha256(p.read_bytes()).hexdigest()
 if got!=signature:raise SystemExit(f'DIGEST_DIFFER {path}')
 n+=1
print('PASS',n,'SHA256 payloads; manifest excludes itself')
