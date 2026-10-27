import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

root=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
out=Path("/mnt/extdrive/workdir/htt_open_data/r36_collection_shadow_independent_review")
author=Path("/mnt/extdrive/workdir/htt_open_data/r36_collection_shadow_repair")
files=["htt/htt/tests/test_bass_d2_transfer.py", "htt/htt/tests/test_peculiar_jeans.py"]
sha=lambda b:hashlib.sha256(b).hexdigest()
def dump(name,obj): (out/name).write_text(json.dumps(obj,indent=2)+"\n")
def git(*args): return subprocess.check_output(["git",*args],cwd=root)
def snapshot():
    status=git("status","--porcelain=v1","-uall","-z")
    entries=[]
    for row in status.split(b"\0"):
        if not row: continue
        relative=os.fsdecode(row[3:]); path=root/relative
        stat=path.lstat()
        entries.append({"status":os.fsdecode(row[:2]),"path":relative,"size":stat.st_size,"mtime_ns":stat.st_mtime_ns,"mode":stat.st_mode,"symlink":os.readlink(path) if path.is_symlink() else None})
    return {"head":git("rev-parse","HEAD").decode().strip(),"branch":git("branch","--show-current").decode().strip(),"origin":git("remote","get-url","origin").decode().strip(),"status_sha256":sha(status),"status_entries":entries,"source_sha256":{p:sha((root/p).read_bytes()) for p in files},"tracked_diff_sha256":sha(git("diff","--binary")),"index_diff_sha256":sha(git("diff","--cached","--binary"))}
return_doc=json.loads((author/"RETURN.json").read_text())
bindings={}
for relative in files:
    before=(author/(Path(relative).name+".preimage")).read_bytes()
    after=(root/relative).read_bytes()
    old=b'for _p in [_root, _root + "/htt", _root + "/bass"]:'
    new=b'for _p in [_root, _root + "/htt"]:'
    assert before.count(old)==1
    assert after==before.replace(old,new), relative
    assert before==git("show","HEAD:"+relative), relative
    assert sha(before)==return_doc["owned_source_files"][relative]["before_sha256"]
    assert sha(after)==return_doc["owned_source_files"][relative]["after_sha256"]
    bindings[relative]={"before_sha256":sha(before),"after_sha256":sha(after),"only_expected_line_replaced":True,"preimage_matches_HEAD":True}
dump("SOURCE_BINDINGS.json",bindings)
(out/"REVIEWED_PATCH.diff").write_bytes(git("diff","--",*files))
before=snapshot(); dump("CHECKOUT_BEFORE.json",before)
env=os.environ.copy(); env["PYTHONDONTWRITEBYTECODE"]="1"
def run(label,argv):
    assert not (out/(label+".command.json")).exists()
    start=datetime.datetime.now(datetime.timezone.utc).isoformat(); tick=time.monotonic()
    with (out/(label+".stdout")).open("wb") as stdout,(out/(label+".stderr")).open("wb") as stderr:
        process=subprocess.Popen(argv,cwd=root,stdout=stdout,stderr=stderr,env=env)
        receipt={"argv":argv,"cwd":str(root),"pid":process.pid,"started_utc":start,"status":"RUNNING","environment_override":{"PYTHONDONTWRITEBYTECODE":"1"},"inherited_PYTHONPATH":env.get("PYTHONPATH"),"inherited_PYTEST_ADDOPTS":env.get("PYTEST_ADDOPTS"),"source_sha256":before["source_sha256"]}
        dump(label+".command.json",receipt)
        print(json.dumps({"label":label,"pid":process.pid,"status":"RUNNING"}),flush=True)
        code=process.wait()
    receipt.update({"status":"COMPLETED","exit_code":code,"elapsed_seconds":time.monotonic()-tick,"finished_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()})
    receipt["stdout_sha256"]=sha((out/(label+".stdout")).read_bytes()); receipt["stderr_sha256"]=sha((out/(label+".stderr")).read_bytes())
    dump(label+".command.json",receipt)
    print(json.dumps({"label":label,"pid":process.pid,"exit_code":code,"elapsed_seconds":receipt["elapsed_seconds"]}),flush=True)
    return receipt
falsifier=run("ORDERED_IMPORT",[str(root/".venv/bin/python"),"-c",(out/"ORDERED_IMPORT_FALSIFIER.py").read_text()])
assert falsifier["exit_code"]==0,"Falsifier failed; stop before collection"
collection=run("FULL_COLLECTION",[str(root/".venv/bin/python"),"-m","pytest","--collect-only","-q"])
after=snapshot(); dump("CHECKOUT_AFTER.json",after)
dump("CHECKOUT_PRESERVATION.json",{"same_snapshot":before==after,"same_source_hashes":before["source_sha256"]==after["source_sha256"],"same_tracked_diff":before["tracked_diff_sha256"]==after["tracked_diff_sha256"],"same_index_diff":before["index_diff_sha256"]==after["index_diff_sha256"],"same_status":before["status_sha256"]==after["status_sha256"],"dirty_path_count":len(before["status_entries"])})
print((out/"FULL_COLLECTION.stdout").read_text()[-3500:],flush=True)
