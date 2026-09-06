import os, sys, json, subprocess, time
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path('/tmp/pr450-current-run-path').read_text().strip()
OUT=Path(ROOT)/'evidence'
def run(label, argv, cwd='/home/cosmosapjw/Dropbox/bianchi/htt_base', validation=False, timeout=60, env=None):
    record=OUT/(label+'.json')
    if record.exists(): raise RuntimeError('Invocation already exists: '+label)
    records=[json.loads(p.read_text()) for p in OUT.glob('*.json')]
    used=sum(x.get('elapsed_seconds',0) for x in records if isinstance(x,dict) and x.get('validation_budget',False))
    if validation: timeout=min(timeout,900-used)
    if timeout<=0: raise RuntimeError('Validation budget exhausted')
    rec={'label':label,'argv':argv,'cwd':str(cwd),'invocation_count':1,'started_at':datetime.now(timezone.utc).isoformat(),'timeout_seconds':timeout,'validation_budget':validation,'environment_overrides':env or {}}
    t=time.monotonic()
    with (OUT/(label+'.stdout')).open('xb') as so, (OUT/(label+'.stderr')).open('xb') as se:
        try:
            cp=subprocess.run(argv,cwd=cwd,stdout=so,stderr=se,timeout=timeout,env={**os.environ,**(env or {})})
            rec.update(exit_code=cp.returncode,timed_out=False)
        except OSError as exc:
            rec.update(exit_code=None,timed_out=False,spawn_error=repr(exc))
        except subprocess.TimeoutExpired:
            rec.update(exit_code=None,timed_out=True)
    rec.update(elapsed_seconds=time.monotonic()-t,ended_at=datetime.now(timezone.utc).isoformat())
    record.write_text(json.dumps(rec,indent=2)+'\n')
    print(label,rec['exit_code'],rec['elapsed_seconds'],flush=True)
    return rec
if __name__=='__main__':
    r=run(sys.argv[1],sys.argv[2:])
    sys.exit(r['exit_code'] if r['exit_code'] is not None else 124)
