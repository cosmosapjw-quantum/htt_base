"""Capture complete raw output of one existing independently authored axis."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
here=Path(__file__).resolve().parent
axis=sys.argv[1]
if axis not in {"wolfram_xact","sympy","sage_singular","lean"}: raise SystemExit(2)
script=here/axis/"run.py"
argv=["sage","-python","-B",str(script)] if axis=="sage_singular" else [sys.executable,"-B",str(script)]
start=datetime.now(timezone.utc).isoformat()
try:
 p=subprocess.run(argv,cwd=Path.cwd(),capture_output=True,timeout=3600 if axis=="lean" else 1800)
 stdout,stderr,code,timed_out=p.stdout,p.stderr,p.returncode,False
except subprocess.TimeoutExpired as e:
 stdout,stderr,code,timed_out=e.stdout or b"",e.stderr or b"",124,True
(here/axis/"raw.stdout").write_bytes(stdout)
(here/axis/"raw.stderr").write_bytes(stderr)
record={"axis":axis,"argv":argv,"cwd":str(Path.cwd()),"started_at":start,"completed_at":datetime.now(timezone.utc).isoformat(),"exit_code":code,"timed_out":timed_out,"script_sha256":hashlib.sha256(script.read_bytes()).hexdigest(),"stdout_path":str(here/axis/"raw.stdout"),"stderr_path":str(here/axis/"raw.stderr"),"stdout_sha256":hashlib.sha256(stdout).hexdigest(),"stderr_sha256":hashlib.sha256(stderr).hexdigest(),"execution_origin":"Host deterministic unchanged-contract validation"}
(here/axis/"EXECUTION.json").write_text(json.dumps(record,indent=2)+"\n")
sys.stdout.buffer.write(stdout);sys.stderr.buffer.write(stderr)
raise SystemExit(code)
