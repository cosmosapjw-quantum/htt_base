"""Read-only recursive filesystem census for the two user-chosen roots.

Writes ONLY to ~/Downloads/htt_r91_local_inventory; every file and directory
metadata recorded in a local compressed private index. No user filenames
from Downloads are published to git. No symlink traversal, content reading,
git mutations, or external-drive writes. Exit 2 on unreadable subtree.
"""
from __future__ import annotations
import argparse, collections, datetime, gzip, json, os, pathlib, sys, time

ROOTS = [
 pathlib.Path("/home/cosmosapjw/Downloads"),
 pathlib.Path("/mnt/extdrive/workdir"),
]
OUTPUT = pathlib.Path("/home/cosmosapjw/Downloads/htt_r91_local_inventory")
# Scientific shortlist is derived from metadata only, not assertion of valid source.
PATTERNS = {
 "planck_likelihood": ("plik","clik","cilk","pilk","lowl","lowl","simall","lollipop","hillipop","commander_likelihood","likelihood"),
 "cf4_upstream_calibration": ("cf4","cosmicflows","intercalibration","zero_point","zeropoint","zero-point","calibration","mcmc","posterior","tf_fp"),
 "bianchi_transfer": ("bianchi","aniclass","anicosmo","sachs","tilt","transfer","morpholog"),
 "survey_kinematics": ("gaia","quaia","icrf3","vlba","racs","nvss","spice","lotss","sumss","pantheon","desi","flow","peculiar","sdss"),
 "camb_cobaya": ("camb","cobaya","classy","plc_","cosmosis","cosmopower","firecrown"),
}
DATA_EXT={".fits",".fit",".fits.gz",".h5",".hdf5",".hdf",".npz",".npy",".csv",".csv.gz",".dat",".dat.gz",".parquet",".chain",".clik",".clik_lite",".txt",".tar",".zip",".json",".yaml",".ini",".sqlite",".db",".fz"}
NONSCI_SEGS={"site-packages",".git","node_modules","venv",".venv","__pycache__",".mypy_cache","conda-meta",".cache","dist-info","wheelhouse","bin","include","lib","lib64","tests"}
def bucket(rel):
 p=rel.parts
 if len(p)>=1:return p[0]
 return "."
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--verbose-every",type=int,default=25000)
 args=ap.parse_args()
 if ROOTS[0].resolve() not in OUTPUT.resolve().parents:
  raise RuntimeError("output is not under Downloads")
 OUTPUT.mkdir(exist_ok=True,parents=True)
 prefix=OUTPUT/"DEEP_SCAN_20261121"
 archive=prefix.with_suffix(".ndjson.gz")
 summaryfile=prefix.with_suffix(".summary.json")
 errfile=prefix.with_suffix(".errors.json")
 # Fresh only: avoid silently replacing any historical inventory.
 if archive.exists() or summaryfile.exists():
  raise FileExistsError("R91 archive already exists; create-only census")
 tmp=OUTPUT/(archive.name+".partial")
 if tmp.exists():raise FileExistsError("previous partial inventory; inspect before retry")
 t0=time.monotonic()
 metrics={}
 errors=[]
 shortlist=[]
 counted=0
 with gzip.open(tmp,"wt",encoding="utf-8",compresslevel=3) as gz:
  for root in ROOTS:
   label="Downloads" if "Downloads" in root.parts else "workdir"
   counts=collections.Counter()
   extensions=collections.Counter()
   bytop=collections.defaultdict(lambda:{"files":0,"bytes":0,"dirs":0})
   science_counts=collections.Counter()
   total_bytes=0
   # root itself exists; os.walk() follows no directory symlinks by default
   if not root.is_dir():
    errors.append({"root":str(root),"error":"missing root"})
    continue
   def onerror(e):
    errors.append({"root":label,"path":getattr(e,"filename",None),"error":str(e)})
   for current, subdirs, filenames in os.walk(root,topdown=True,followlinks=False,onerror=onerror):
    relp=pathlib.Path(current).relative_to(root)
    counts["directories"]+=1
    bytop[bucket(relp)]["dirs"]+=1
    for file in filenames:
     path=pathlib.Path(current)/file
     rel=path.relative_to(root)
     try:
      st=path.lstat()
     except (OSError,PermissionError) as e:
      errors.append({"root":label,"path":str(rel),"error":str(e)});continue
     size=int(st.st_size)
     counts["files"]+=1
     total_bytes+=size
     ext=("".join(path.suffixes[-2:]) if path.suffix==".gz" else path.suffix.lower())
     extensions[ext]+=1
     top=bucket(rel)
     bytop[top]["files"]+=1
     bytop[top]["bytes"]+=size
     rec={"root":label,"rel":str(rel),"bytes":size,"mtime_ns":int(st.st_mtime_ns),"mode":int(st.st_mode)}
     gz.write(json.dumps(rec,separators=(",",":"),ensure_ascii=False)+"\n")
     counted+=1
     # TAG ONLY; no content/execution or publication of sensitive filenames.
     low=str(rel).lower()
     looks_data=any(low.endswith(ext) for ext in DATA_EXT)
     included=not any(seg in NONSCI_SEGS for seg in rel.parts)
     categories=[cat for cat, patterns in PATTERNS.items() if any(w in low for w in patterns)]
     if categories and looks_data and included and (size>=128 or ext in (".json",".yaml",".ini")):
      science_counts.update(categories)
      shortlist.append({"root":label,"rel":str(rel),"bytes":size,"categories":categories})
     if args.verbose_every>0 and counted%args.verbose_every==0:
      print(f"SCAN_PROGRESS files={counted} root={label} elapsed_s={time.monotonic()-t0:.1f}",flush=True)
   metrics[label]={"path":str(root),"files":counts["files"],"directories":counts["directories"],
                   "total_bytes":total_bytes,"top_subtrees":dict(bytop),
                   "top_extensions":extensions.most_common(35),"science_metadata_hits":dict(science_counts)}
 os.replace(tmp,archive)
 shortpath=prefix.with_suffix(".science_candidates.json")
 # Candidate list local-only and includes no content, may include personal names; do not publish.
 shortpath.write_text(json.dumps({"schema":"htt.r91.private_local_metadata_candidates/1","candidates":shortlist},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 result={"schema":"htt.r91.full_two_root_metadata_census/1",
         "method":"os.walk no followlinks, metadata lstat all regular filename entries (including hidden), no contents read",
         "start_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "duration_s":round(time.monotonic()-t0,3),
         "roots":metrics,"metadata_errors":len(errors),
         "file_records":counted,"candidate_count":len(shortlist),
         "private_archive":str(archive),"private_candidates":str(shortpath),
         "complete":len(errors)==0 and len(metrics)==len(ROOTS)}
 summaryfile.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 errfile.write_text(json.dumps(errors,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("SCAN_FINISHED "+json.dumps({k:v for k,v in result.items() if k not in ("roots",)},ensure_ascii=False),flush=True)
 for k,v in metrics.items():
  print("ROOT_STAT "+k+" "+json.dumps({x:v[x] for x in ("files","directories","total_bytes","science_metadata_hits")},ensure_ascii=False),flush=True)
 return 0 if result["complete"] else 2

if __name__=="__main__":
 raise SystemExit(main())
