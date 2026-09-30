import json,pathlib,subprocess,sys
here=pathlib.Path(__file__).resolve().parent
argv=["wolframscript","-file",str(here/"wolfram_check.wl")]
try:p=subprocess.run(argv,cwd=here,capture_output=True,text=True,timeout=300)
except Exception as exc:
 (here/"wolfram.execution_error.log").write_text(repr(exc)+"\n");sys.exit(3)
(here/"wolfram.stdout.log").write_text(p.stdout);(here/"wolfram.stderr.log").write_text(p.stderr)
if p.returncode or "CAS_JSON_BEGIN\n" not in p.stdout or "\nCAS_JSON_END" not in p.stdout:
 print("Wolfram engine or marker failure; see raw logs",file=sys.stderr);sys.exit(3)
s=p.stdout.split("CAS_JSON_BEGIN\n",1)[1].split("\nCAS_JSON_END",1)[0]
try:obj=json.loads(s)
except Exception as exc:print(repr(exc),file=sys.stderr);sys.exit(3)
if obj.get("full_scope") is not True:print("unresolved full-scope theorem",file=sys.stderr);sys.exit(3)
print(json.dumps({"checks":{"CAS13-C04-RELATIVE-MINIMAX":True},"domain_assumption_diff":[],"counterexample":None,"engine_certificate":obj}))
