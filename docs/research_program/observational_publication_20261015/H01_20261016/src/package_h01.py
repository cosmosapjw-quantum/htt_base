"""Build deterministic-ish SHA manifest archive for independent verification.
Zip itself is hashed as a transport artifact, payload SHA manifest is authoritative.
"""
from pathlib import Path
import hashlib,zipfile,json,sys
ROOT=Path(__file__).resolve().parents[1]

def sha(path):
 h=hashlib.sha256();
 with Path(path).open('rb') as src:
  for chunk in iter(lambda:src.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()

def build(stage, out):
 files=[ROOT/'src/hubble_window.py',ROOT/'tests/test_hubble_window.py',ROOT/'src/run_h01.py',ROOT/'src/plot_h01.py',ROOT/'src/package_h01.py',ROOT/'source/selected_source_observables.npz',ROOT/'docs/H01_THEORY_KO.md',ROOT/'docs/CODEX_HANDOFF_KO.md',ROOT/'docs/H01_STAGE1_DAG.json']
 if stage=='S2':
  files += [ROOT/'results/H01_SOURCE_WINDOW_RESULT.json',ROOT/'figures/H01_WINDOW_TRAJECTORIES.png',ROOT/'figures/H01_WINDOW_CORRELATION.png',ROOT/'docs/H01_STAGE2_DAG.json',ROOT/'docs/H01_S2_REPORT_KO.md',ROOT/'docs/H01_RUN_RECEIPT.json']
 entries={p.relative_to(ROOT).as_posix():{'sha256':sha(p),'size':p.stat().st_size} for p in files}
 payload={'schema':'htt.sixpaper.h01.archive_manifest/1','stage':stage,'payload_count':len(entries),'files':entries}
 out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:z.write(p,p.relative_to(ROOT).as_posix())
  z.writestr('MANIFEST.json',json.dumps(payload,indent=2,sort_keys=True)+'\n')
 with zipfile.ZipFile(out) as z:
  assert z.testzip() is None
  assert len(z.namelist())==len(files)+1
  for k,v in entries.items():assert hashlib.sha256(z.read(k)).hexdigest()==v['sha256'],k
 return {'zip':str(out),'zip_sha256':sha(out),'zip_bytes':out.stat().st_size,'files':len(files),'zip_verified':True,'stage':stage,'manifest':payload}

if __name__=='__main__':
 t=sys.argv[1]; f=ROOT/'checkpoints'/f'H01_SIX_PAPER_{t}_20261016.zip'
 r=build(t,f); print(json.dumps({k:v for k,v in r.items() if k!='manifest'},indent=2))
 (ROOT/'checkpoints'/f'{t}_RECEIPT.json').write_text(json.dumps({k:v for k,v in r.items() if k!='manifest'},indent=2)+'\n')
