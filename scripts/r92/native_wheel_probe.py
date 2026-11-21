"""R92 isolated native wheel capability probe: never install into BASS or HTT.

Extracts one explicit local wheel into temporary PRIVATE Downloads sandbox,
checks module symbol and executes two BASS high-l tests if capability present.
All temporary material removed; original BASS repository untouched.
"""
import json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path

BASS=Path("/home/cosmosapjw/bass")
WHEEL=BASS/"repro/native/BASS-RF02B-R4-DELTA-20260826/rf02b-wheel/bianchi_rustcore-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl"
DEST=Path("/home/cosmosapjw/Downloads/htt_r92_private_index/R92_BASS_NATIVE_ISOLATED_PROBE.json")
if DEST.exists():raise RuntimeError("create-only wheel probe receipt exists")
with tempfile.TemporaryDirectory(prefix="r92-bass-native-",dir=DEST.parent) as scratch:
 d=Path(scratch)
 with zipfile.ZipFile(WHEEL) as z:
  info=z.infolist()
  if sum(x.file_size for x in info)>20*2**20:raise RuntimeError("wheel too large")
  for x in info:
   p=(d/x.filename).resolve()
   if d.resolve() not in p.parents:raise RuntimeError("wheel path traversal")
  z.extractall(d)
 env=os.environ.copy()
 env.update(PYTHONPATH=str(d)+os.pathsep+str(BASS),PYTHONDONTWRITEBYTECODE="1",
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1")
 py=BASS/".venv/bin/python"
 inspect=subprocess.run([str(py),"-B","-c",
     "import bianchi_rustcore; print(bianchi_rustcore.__file__); print(hasattr(bianchi_rustcore,'rayon_thread_pool_size'))"],
     env=env,text=True,capture_output=True,timeout=15)
 ok=(inspect.returncode==0 and "True" in inspect.stdout)
 test={"status":"NOT_RUN_NO_SYMBOL"}
 if ok:
  tst=subprocess.run([str(py),"-B","-m","pytest","-p","no:cacheprovider","-q",
     "tests/test_v1_high_l_signs.py","-k",
     "l_max_supported_covers_rank6 or equation12_holds_at_l4"],
     cwd=BASS,env=env,text=True,capture_output=True,timeout=65)
  test={"exit":tst.returncode,"status":"PASS" if tst.returncode==0 else "FAIL",
        "stdout_tail":tst.stdout[-2000:],"stderr_tail":tst.stderr[-900:]}
 record={"schema":"htt.r92.native_wheel_isolation_smoke/1",
         "wheel_path":str(WHEEL),"wheel_exists":True,
         "wheel_bytes":WHEEL.stat().st_size,
         "module_probe_stdout":inspect.stdout[:1500],
         "module_probe_stderr":inspect.stderr[:1500],
         "module_probe_exit":inspect.returncode,
         "rayon_capability_available":ok,
         "test":test,
         "installed_bass_env_modified":False,
         "result_scope":"Runtime/ABI compatibility only, not validated high ell likelihood"}
DEST.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(record,ensure_ascii=False)[:4000])
