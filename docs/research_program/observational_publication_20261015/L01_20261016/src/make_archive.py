"""Make readback-verifiable immutable ZIP from a declared project file allowlist."""
from __future__ import annotations
import hashlib,json,zipfile
from pathlib import Path

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def archive(project:Path,paths:list[str],dest:Path):
 project=Path(project);dest=Path(dest)
 if dest.exists():raise FileExistsError('create-only checkpoint path')
 hashes={}
 for n in paths:
  p=project/n
  if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(project.resolve()):raise ValueError('declared source not regular file')
  hashes[n]={'size':p.stat().st_size,'sha256':sha(p.read_bytes())}
 manifest={'schema':'htt.checkpoint.manifest/1','files':hashes}
 dest.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for name in sorted(paths):z.write(project/name,name)
  z.writestr('CHECKPOINT_MANIFEST.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None
  m=json.loads(z.read('CHECKPOINT_MANIFEST.json'))
  for n,info in m['files'].items():
   b=z.read(n)
   assert sha(b)==info['sha256'] and len(b)==info['size']
 return {'zip_path':str(dest),'zip_sha256':sha(dest.read_bytes()),'bytes':dest.stat().st_size,'payload_files':len(paths)}
