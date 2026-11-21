"""R92 private metadata and archive-member deep index.

Seven exact user-scoped directories; os.walk is exhaustive, with followlinks=False.
It never extracts archive payloads or mutates input sources. ZIP central directories
are indexed, plus nested ZIP/TAR only when payload <= 12 MiB and depth < 2.
TAR metadata indexed for archives <= 250 MiB; above that size is explicitly
DEFERRED_SIZE, not silently treated as empty. Archive processing failure is
recorded, not a PASS. Private filenames remain under local Downloads only.
"""
from __future__ import annotations
import collections,datetime,gzip,hashlib,io,json,os,pathlib,stat,sys,tarfile,time,zipfile
from pathlib import Path

ROOTS=[
 Path("/home/cosmosapjw/Dropbox/dossier"),
 Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi"),
 Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi"),
 Path("/home/cosmosapjw/Dropbox/Mayukh_cowork/ver3"),
 Path("/home/cosmosapjw/Dropbox/Mayukh_cowork/ver2"),
 Path("/home/cosmosapjw/bass"),
 Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/legacy"),
]
OUT=Path("/home/cosmosapjw/Downloads/htt_r92_private_index")
PREFIX=OUT/"R92_DEEP_INDEX_20261121"
TAR_CAP=250*2**20
NESTED_CAP=12*2**20
LIMIT_MEMBERS=100000
ARCHIVE_EXT=(".zip",".tar",".tgz",".tar.gz",".tar.bz2",".tar.xz",".7z",".rar",".tar.zst")
RELEVANT=("bianchi","tetrad","geometry","einstein","codazzi","tilt","boltzmann","transport","thomson",
          "geodesic","sachs","jacobi","beam","scalar","tensor","bipo","high_l","high-l","multipole","cmb",
          "photon","polariz","cosmo","reion","anisotro","covarian","shear","vortic","kinematic","null",
          "morpholog","observable","rate","collision","likelihood","projection","closure")
CODE_EXT=(".py",".rs",".f90",".f",".c",".h",".cpp",".cc",".jl",".m",".wl",".nb",".ipynb",".toml",".yaml",".yml")
TEXT_EXT=(".tex",".md",".txt",".bib",".rst",".json",".yaml",".yml",".pdf",".html",".qmd")
def label(path:Path)->str: return str(ROOTS.index(next(r for r in ROOTS if r==path or r in path.parents)))
def kind(name:str)->str:
 lo=name.lower()
 if any(lo.endswith(ex) for ex in CODE_EXT):return "code"
 if any(lo.endswith(ex) for ex in TEXT_EXT):return "document"
 if lo.endswith(ARCHIVE_EXT):return "archive"
 if lo.endswith((".fits",".fit",".h5",".hdf5",".npz",".npy",".dat",".csv",".parquet",".db",".sqlite")):return "data"
 return "other"
def arch_fmt(n):
 name=n.lower()
 if name.endswith(".zip"): return "zip"
 if any(name.endswith(x) for x in (".tar",".tgz",".tar.gz",".tar.bz2",".tar.xz")):return "tar"
 return "unsupported"
def member_summary(iter_items, record, cap=LIMIT_MEMBERS):
 i=0; interesting=[]
 for mname,msize,isdir in iter_items:
  i+=1
  if i>cap:raise ValueError("member count cap >100000")
  if len(interesting)<250 and any(t in mname.lower() for t in RELEVANT):
   interesting.append({"name":mname[:300],"bytes":int(msize),"type":kind(mname)})
  record({"name":mname,"bytes":int(msize),"is_dir":bool(isdir),"kind":kind(mname)})
 return i,interesting

def inspect_archive(path,rootid,rel,g):
 ans={"root":rootid,"rel":str(rel),"bytes":path.stat().st_size,"format":arch_fmt(path.name),
      "status":"UNKNOWN","entries":0,"selected_member_examples":[],"nested_attempts":0,"nested_success":0}
 def member_rec(x):
  g.write(json.dumps({"archive":str(rel),"root":rootid,**x},ensure_ascii=False,separators=(",",":"))+"\n")
 if ans["format"]=="zip":
  with zipfile.ZipFile(path) as z:
   its=((v.filename,v.file_size,v.is_dir()) for v in z.infolist())
   count,ex=member_summary(its,member_rec)
   ans.update(status="INDEXED_CENTRAL_DIRECTORY",entries=count,selected_member_examples=ex)
   # Nested zip archives for manageable containers only. 7z/rar remain unsupported.
   for item in z.infolist():
    if item.is_dir() or item.file_size>NESTED_CAP or not item.filename.lower().endswith(".zip"):
     continue
    ans["nested_attempts"]+=1
    try:
     with z.open(item) as stream: raw=stream.read(NESTED_CAP+1)
     if len(raw)>NESTED_CAP:continue
     with zipfile.ZipFile(io.BytesIO(raw)) as inner:
      x,selected=member_summary(
       ((e.filename,e.file_size,e.is_dir()) for e in inner.infolist()),
       lambda v:member_rec({"nested_archive":item.filename,**v}))
     ans["nested_success"]+=1
     ans.setdefault("nested_indexed_entries",0)
     ans["nested_indexed_entries"]+=x
    except Exception as e:
     ans.setdefault("nested_errors",[]).append({"name":item.filename[:200],"error":str(e)[:180]})
 elif ans["format"]=="tar":
  if path.stat().st_size>TAR_CAP:
   ans.update(status="DEFERRED_TAR_COMPRESSED_SIZE",reason=f"file>{TAR_CAP} bytes")
  else:
   with tarfile.open(path,"r:*") as t:
    count,ex=member_summary(((z.name,z.size,z.isdir()) for z in t),member_rec)
   ans.update(status="INDEXED_TAR",entries=count,selected_member_examples=ex)
 else:
  ans.update(status="DEFERRED_UNSUPPORTED_FORMAT",
             reason="7z/rar/zst require dedicated sandboxed listing tool")
 return ans

def main():
 if any(not p.is_dir() for p in ROOTS): raise ValueError("one or more requested source roots missing")
 OUT.mkdir(parents=True,exist_ok=True)
 paths={name:PREFIX.with_suffix(ext) for name,ext in (
   ("FILES",".files.jsonl.gz"),("MEMBERS",".archive_members.jsonl.gz"),
   ("ROOT",".summary.json"),("ARCHIVE",".archives.json"),("CANDIDATE",".candidates.json"))}
 # with_suffix collisions? all unique suffixes, verify.
 if len(set(map(str,paths.values())))!=5:raise ValueError("bad output names")
 if any(p.exists() for p in paths.values()):raise FileExistsError("output exists; create-only")
 t0=time.monotonic()
 archives=[];candidates=[];roots=[];errors=[];total=0
 with gzip.open(paths["FILES"],"wt",encoding="utf8") as fil, gzip.open(paths["MEMBERS"],"wt",encoding="utf8") as mem:
  for rid,base in enumerate(ROOTS):
   count=0;dirs=0;size=0
   exts=collections.Counter();kinds=collections.Counter()
   entries=[]
   def onerr(e):errors.append({"root":rid,"error":str(e),"path":str(getattr(e,"filename",""))})
   for here,sub,names in os.walk(base,followlinks=False,onerror=onerr):
    dirs+=1
    for name in names:
     p=Path(here)/name
     try: st=p.lstat()
     except OSError as e:
      errors.append({"root":rid,"rel":str(p.relative_to(base)),"error":str(e)})
      continue
     count+=1;total+=1;size+=st.st_size
     rel=p.relative_to(base);typ=kind(str(rel))
     kinds[typ]+=1
     exts["".join(p.suffixes[-2:]) if p.suffix.lower()==".gz" else p.suffix.lower()]+=1
     file_rec={"root":rid,"rel":str(rel),"bytes":int(st.st_size),"mtime_ns":st.st_mtime_ns,
               "mode":st.st_mode,"type":typ}
     fil.write(json.dumps(file_rec,ensure_ascii=False,separators=(",",":"))+"\n")
     low=str(rel).lower()
     if any(t in low for t in RELEVANT) and (typ in ("code","document","data")):
      candidates.append({**file_rec,"match_terms":[t for t in RELEVANT if t in low][:5]})
     if low.endswith(ARCHIVE_EXT) and stat.S_ISREG(st.st_mode):
      try:
       entry=inspect_archive(p,rid,rel,mem)
      except Exception as e:
       entry={"root":rid,"rel":str(rel),"status":"ERROR","bytes":int(st.st_size),
              "error":str(e)[:400]}
      archives.append(entry)
     if total%30000==0:print("R92_SCAN_PROGRESS",total,rid,round(time.monotonic()-t0,1),flush=True)
   roots.append({"root_id":rid,"root":str(base),"files":count,"dirs":dirs,"bytes":size,
                 "kinds":dict(kinds),"top_ext":exts.most_common(24)})
   print("R92_ROOT_FINISHED",rid,count,dirs,"archives",len(archives),flush=True)
 result={"schema":"htt.r92.user_scoped_seven_root_index/1",
         "utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "elapsed_seconds":round(time.monotonic()-t0,2),
         "roots":roots,"total_files":total,"total_bytes":sum(x["bytes"] for x in roots),
         "archive_count":len(archives),
         "archive_status":dict(collections.Counter(v["status"] for v in archives)),
         "archive_member_count":sum(v.get("entries",0) for v in archives),
         "nested_archive_entries":sum(v.get("nested_indexed_entries",0) for v in archives),
         "candidate_count":len(candidates),"errors":errors,
         "privacy":"full filename/member index remains in Downloads; public repo only sanitized thematic summary"}
 paths["ROOT"].write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 paths["ARCHIVE"].write_text(json.dumps({"archives":archives},indent=2,ensure_ascii=False)+"\n")
 paths["CANDIDATE"].write_text(json.dumps({"candidates":candidates},ensure_ascii=False)+"\n")
 print("R92_FINAL",json.dumps({k:result[k] for k in (
   "elapsed_seconds","total_files","archive_count","archive_status",
   "archive_member_count","nested_archive_entries","candidate_count")},ensure_ascii=False),flush=True)
 return 0 if not errors else 2
if __name__=="__main__":sys.exit(main())
