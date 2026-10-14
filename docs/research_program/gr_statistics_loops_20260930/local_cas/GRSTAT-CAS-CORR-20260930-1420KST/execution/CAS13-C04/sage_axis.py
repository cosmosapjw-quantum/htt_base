import json,subprocess,sys,pathlib
here=pathlib.Path(__file__).resolve().parent
argv=["sage","-python",str(here/"sage_check.py")]
p=subprocess.run(argv,cwd=here,capture_output=True,text=True,timeout=240)
(here/"sage.stdout.log").write_text(p.stdout);(here/"sage.stderr.log").write_text(p.stderr)
if p.returncode:
 print(p.stderr,file=sys.stderr);sys.exit(p.returncode)
print(p.stdout.strip())
