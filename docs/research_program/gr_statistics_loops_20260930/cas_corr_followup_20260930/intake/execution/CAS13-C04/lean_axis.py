import json,os,pathlib,subprocess,sys
here=pathlib.Path(__file__).resolve().parent
repo=here.parents[6]
argv=["lake","env","lean",str(here/"Main.lean")]
env=dict(os.environ,ELAN_TOOLCHAIN="leanprover/lean4:v4.31.0")
try:p=subprocess.run(argv,cwd=repo/"formal_mathlib",env=env,capture_output=True,text=True,timeout=600)
except Exception as exc:
 (here/"lean.execution_error.log").write_text(repr(exc)+"\n");sys.exit(3)
(here/"lean.stdout.log").write_text(p.stdout);(here/"lean.stderr.log").write_text(p.stderr)
(here/"lean.exit.txt").write_text(str(p.returncode)+"\n")
if p.returncode or "grstat_cas13_minimax" not in p.stdout or "sorryAx" in p.stdout:
 print(json.dumps({"checks":{"CAS13-C04-RELATIVE-MINIMAX":False},"domain_assumption_diff":["Lean compilation or theorem output incomplete"],"counterexample":None}));sys.exit(2)
print(json.dumps({"checks":{"CAS13-C04-RELATIVE-MINIMAX":True},"domain_assumption_diff":[],"counterexample":None,"theorem":"grstat_cas13_minimax","scope":"uniform bound; both endpoint equalities; every real competitor; L=U included"}))
