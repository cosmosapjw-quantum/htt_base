#!/usr/bin/env python3
"""New diagnostic wrapper. Engine/marker errors produce no scientific JSON."""
import argparse,json,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument("--script",default="check_fixed.wl");p.add_argument("--engine",default="wolframscript");p.add_argument("--log-stem",default="wrapper");a=p.parse_args()
here=pathlib.Path(__file__).resolve().parent;argv=[a.engine,"-file",str(here/a.script)]
try:r=subprocess.run(argv,cwd=here,text=True,capture_output=True,timeout=300)
except Exception as exc:(here/"wrapper.execution_error.log").write_text(repr(exc)+"\n");print(repr(exc),file=sys.stderr);sys.exit(3)
(here/(a.log_stem+".raw.stdout.log")).write_text(r.stdout);(here/(a.log_stem+".raw.stderr.log")).write_text(r.stderr)
if r.returncode != 0 or "CAS_JSON_BEGIN\n" not in r.stdout or "\nCAS_JSON_END" not in r.stdout:
 print(f"engine_exit={r.returncode}; marker_present={ 'CAS_JSON_BEGIN' in r.stdout }; no result payload",file=sys.stderr);sys.exit(3)
try:obj=json.loads(r.stdout.split("CAS_JSON_BEGIN\n",1)[1].split("\nCAS_JSON_END",1)[0])
except Exception as exc:print(f"unparseable marker: {exc}",file=sys.stderr);sys.exit(3)
if not isinstance(obj,dict) or not isinstance(obj.get("checks"),dict):print("invalid engine payload",file=sys.stderr);sys.exit(3)
print(json.dumps(obj,separators=(",",":")))
sys.exit(0)
