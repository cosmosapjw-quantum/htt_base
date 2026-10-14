import json,pathlib,subprocess
p=pathlib.Path(__file__).resolve().parent
rows=[]
for name in ('repro_self_reference.wl','repro_disjoint.wl'):
 argv=['wolframscript','-file',str(p/name)]
 try:
  r=subprocess.run(argv,cwd=p,capture_output=True,text=True,timeout=45)
  (p/(name+'.stdout.log')).write_text(r.stdout)
  (p/(name+'.stderr.log')).write_text(r.stderr)
  rows.append({'script':name,'argv':argv,'exit_code':r.returncode,'stdout_path':name+'.stdout.log','stderr_path':name+'.stderr.log','recursion_message':'RecursionLimit' in r.stdout+r.stderr,'marker_present':'CAS_JSON_BEGIN' in r.stdout})
 except Exception as exc:
  rows.append({'script':name,'argv':argv,'execution_error':repr(exc)})
(p/'repro_result.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows))
