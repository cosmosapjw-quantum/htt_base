#!/usr/bin/env python3
import subprocess,json,pathlib,sys
p=pathlib.Path(__file__).resolve().parent
r=subprocess.run(['sage','-python',str(p/'check.py')],capture_output=True,text=True)
(p/'sage.stdout.log').write_text(r.stdout)
(p/'sage.stderr.log').write_text(r.stderr)
try: data=json.loads(r.stdout)
except Exception: data={'checks':{f'CAS-01-C{i:02d}':False for i in range(1,5)},'domain_assumption_diff':['engine_execution_failed'],'counterexample':r.stderr[-1000:] or None}
data['argv']=['sage','-python',str(p/'check.py')];data['exit_code']=r.returncode
print(json.dumps(data))
