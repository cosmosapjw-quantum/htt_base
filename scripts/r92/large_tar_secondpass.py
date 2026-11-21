"""R92 second-pass metadata-only GNU tar stream listing of large deferred archives.

No extraction and no source mutation. timeout=50s per archive, 5 known exact
paths only, make create-only private outputs in user's Downloads. Failing archives
remain explicitly unindexed.
"""
from pathlib import Path
import subprocess,json,hashlib,time
ROOT=Path("/home/cosmosapjw/Downloads/htt_r92_private_index")
SRC=Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi")
A=json.loads((ROOT/"R92_DEEP_INDEX_20261121.archives.json").read_text())["archives"]
tar=[x for x in A if x["status"]=="DEFERRED_TAR_COMPRESSED_SIZE"]
rec=[]
for n,item in enumerate(tar):
 p=SRC/item["rel"]
 path=ROOT/f"R92_LARGETAR_{n}.members.txt"
 if path.exists():raise ValueError("create-only large TAR output exists")
 t=time.perf_counter()
 with path.open("x") as f:
  try:
   x=subprocess.run(["tar","-tzf",str(p)],stdout=f,stderr=subprocess.PIPE,
                    timeout=50,text=True,check=False)
   status="INDEXED_TAR_SECOND_PASS" if x.returncode==0 else "TAR_ERROR"
   detail=x.stderr[:200]
  except subprocess.TimeoutExpired:
   status="DEFERRED_TIMEOUT"
   detail="per-archive 50s safety limit"
 names=path.read_text(errors="replace").splitlines()
 rec.append({"original":item["rel"],"archive_bytes":item["bytes"],
             "status":status,"elapsed_s":round(time.perf_counter()-t,2),
             "member_names_partial_or_full":len(names),"detail":detail,
             "private_member_index":str(path)})
 print("R92_DEFERRED_RESULT",n,status,len(names),round(time.perf_counter()-t,2),flush=True)
result=ROOT/"R92_LARGETAR_SECOND_PASS.json"
if result.exists():raise ValueError("create-only summary exists")
result.write_text(json.dumps(rec,indent=2)+"\n")
