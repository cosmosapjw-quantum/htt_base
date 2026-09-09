#!/usr/bin/env python3
import pathlib, os, subprocess, time, json, hashlib, sys, datetime
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[4]
PKGS=pathlib.Path('/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages')
PIN=(REPO/'formal/lean-toolchain').read_text().strip()
ENV=dict(os.environ, LEAN_PATH=':'.join(str(PKGS/p/'.lake/build/lib/lean') for p in ['Cli','LeanSearchClient','Qq','aesop','batteries','importGraph','mathlib','plausible','proofwidgets']))
argv=['/home/cosmosapjw/.elan/bin/lean','+'+PIN,'-o',str(HERE/'O4.olean'),str(HERE/'O4.lean')]
start=time.monotonic()
timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(argv,cwd=REPO,env=ENV,capture_output=True,text=True,timeout=3300)
log=HERE/('build-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.log')
log.write_text(r.stdout+r.stderr)
receipt=dict(argv=argv,cwd=str(REPO),exit_code=r.returncode,elapsed_seconds=time.monotonic()-start,started_at=timestamp,completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),transcript=str(log.relative_to(REPO)),source_sha256=hashlib.sha256((HERE/'O4.lean').read_bytes()).hexdigest(),toolchain=PIN,lean_path=ENV['LEAN_PATH'])
(HERE/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt)); print(r.stdout+r.stderr)
sys.exit(r.returncode)
