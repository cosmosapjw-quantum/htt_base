from pathlib import Path
import datetime, hashlib, json, os, subprocess, tempfile
T = Path(__file__).resolve().parent.parent
O = Path('/home/cosmosapjw/lean_oracles/viii_oracle')
L = T / 'coercivity_logs' / datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
L.mkdir(exist_ok=False)
sources = [('CAS15ProjectionAccepted', T/'Projection.lean'), ('CAS15Frobenius', T/'Frobenius.lean'),
           ('CoercivityBridge', T/'CoercivityBridge.lean')]
r = {'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for _,p in sources}, 'steps': []}
with tempfile.TemporaryDirectory(prefix='cas15-coercivity-') as tmp:
    env = {**os.environ, 'LEAN_PATH': tmp}
    for name,p in [('version', None)] + sources:
        if p:
            dst = Path(tmp)/(name+'.lean'); dst.write_bytes(p.read_bytes())
            cmd = ['lake','env','lean','-R',tmp,'-o',str(Path(tmp)/(name+'.olean')),str(dst)]
        else: cmd = ['lake','env','lean','--version']
        q = subprocess.run(cmd,cwd=O,env=env,capture_output=True,text=True)
        (L/(name+'.stdout')).write_text(q.stdout); (L/(name+'.stderr')).write_text(q.stderr)
        r['steps'].append({'name':name,'argv':cmd,'cwd':str(O),'exit':q.returncode})
        (L/'execution.json').write_text(json.dumps(r,indent=2)+'\n')
        print(name,q.returncode,flush=True)
        if q.returncode: print(q.stdout,flush=True); break
print(L,flush=True)
raise SystemExit(q.returncode)
