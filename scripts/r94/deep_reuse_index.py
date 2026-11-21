"""R94 source-identity deep scan for dossier PDFs, BASS, and HTT legacy.

Full metadata, archive central-directory paths and Python AST symbols are
kept ONLY in ~/Downloads/htt_r94_source_index. Only sanitized aggregate
metrics and selected scientific source SHA256 are deposited under R94 docs.
No PDF payload, private file paths beyond user-authorized roots, binaries or
raw FITS are copied into repo. Source directories remain read-only.
"""
from __future__ import annotations
import ast
from collections import Counter,defaultdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time
import zipfile

ROOTS=[
 Path("/home/cosmosapjw/Dropbox/dossier"),
 Path("/home/cosmosapjw/bass"),
 Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/legacy"),
]
HTT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
REPORT=HTT/"docs/research_program/observational_publication_20261015/R94_SIX_PAPER_ACCEL_HANDOFF_20261122/SOURCE_REUSE_INDEX.json"
PRIVATE=Path.home()/"Downloads/htt_r94_source_index"
KEYWORDS=(
 "bianchi","thomson","pstf","collision","moment","transport","sachs",
 "jacobi","polari","multipole","tilt","covariance","mock","lie","gaunt",
 "biposh","background","opacity","frame","boltzmann","hierarchy","closure",
 "reion","radiative","likelihood","beam","lensing","optical","geodesic")
CURATED=[
 (0,"Dossier_I_Homogeneous_Geometry.pdf","general Lie/Jacobi/Codazzi and tilted Einstein constraints"),
 (0,"Dossier_II_Kinetic_Transport.pdf","photon collision, screen polarization and emission geometry"),
 (0,"Dossier_III_Atomic_Processes.pdf","atomic/recombination source candidate, not direct high-ell likelihood"),
 (0,"Dossier_IV_Reionization.pdf","time-dependent electron/Thomson source, no full posterior assumed"),
 (0,"Dossier_V_Conservative_Approximation.pdf","hierarchy error/adjoint and finite-order closure"),
 (0,"Dossier_VI_Nuclear_Reactions.pdf","initial nuclear composition source; not a direct anisotropy likelihood"),
 (0,"Dossier_VII_Observation.pdf","finite aperture/observer reception"),
 (0,"BASS_Integrated_Dossier.pdf","integrated material and claim provenance"),
 (1,"bianchi/q/polarization.py","actually executed exact rank-nine basis-free Thomson collision"),
 (1,"bianchi/q/transport.py","native Rust dependent angular/frequency transport"),
 (1,"bianchi/matter/hierarchy.py","dense PSTF up to LMAX6 only"),
 (1,"bianchi/matter/grid_boltzmann.py","existing angle-grid collision and moments"),
 (1,"bianchi/charts/class_b_tilted.py","Class B tilt Einstein momentum"),
 (1,"bianchi/physical/frame_transport.py","orthonormal observer frame"),
 (2,"bass_htt_mio_github_ready_current/src/bass/PR13AG_projected_multipole_solver_restoration.py","synthetic finite L4/L6/L8 projected solver, not physical native"),
 (2,"bass_htt_mio_github_ready_current/src/bass/exact_thomson_tensor.py","legacy exact Thomson reference"),
 (2,"bianchi_departure_v091_github/htt/likelihood/biposh_masked.py","old fsky positive-|alm|² invalid BipoSH estimator"),
 (2,"bianchi_departure_v091_github/htt/likelihood/pixel_lowl.py","historical pixel likelihood, review before reuse"),
 (2,"cf4_p0/scripts/make_cf4_bulkflow_likelihood.py","historical CF4 model and source handling"),
]
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(2**18),b""):h.update(c)
 return h.hexdigest()
def pdf_metadata(p):
 proc=subprocess.run(["pdfinfo",str(p)],text=True,capture_output=True,timeout=15)
 pg=None
 if proc.returncode==0:
  for line in proc.stdout.splitlines():
   if line.startswith("Pages:"):pg=int(line.split(":",1)[1].strip())
 text=subprocess.run(["pdftotext","-f","1","-l",str(pg or 1000),"-layout",
      str(p),"-"],capture_output=True,text=True,timeout=30)
 contents=text.stdout if text.returncode==0 else ""
 # Identify keyword occurrence counts; no reproduction of protected source.
 count={k:len(re.findall(re.escape(k),contents,re.IGNORECASE)) for k in KEYWORDS}
 return {"pages":pg,"text_chars":len(contents),"keyword_hits":{k:v for k,v in count.items() if v>0},
          "pdftotext_exit":text.returncode}
def build():
 if REPORT.exists() or PRIVATE.exists():
  raise RuntimeError("R94 deep-scan outputs already exist (create-only)")
 for p in ROOTS:
  if not p.is_dir():raise FileNotFoundError(p)
 PRIVATE.mkdir(parents=True)
 begin=time.perf_counter()
 results=[]
 badarchives=[]
 pythons=[]
 nentries=0
 with gzip.open(PRIVATE/"file_metadata.jsonl.gz","wt") as fw, gzip.open(PRIVATE/"zip_members.jsonl.gz","wt") as mw:
  for rid,root in enumerate(ROOTS):
   nfiles=ndirs=bytes_=nzip=nmembers=0
   errors=[]
   kinds=Counter()
   top=defaultdict(lambda:[0,0])
   def err(e):errors.append(str(e))
   for directory,subdirs,names in os.walk(root,followlinks=False,onerror=err):
    ndirs+=1
    for name in names:
     path=Path(directory)/name
     try:stat=path.lstat()
     except OSError as e:errors.append(str(e));continue
     rel=str(path.relative_to(root))
     nfiles+=1;bytes_+=stat.st_size
     kinds[path.suffix.lower()]+=1
     t=rel.split("/",1)[0]
     top[t][0]+=1;top[t][1]+=stat.st_size
     fw.write(json.dumps({"root":rid,"rel":rel,"bytes":stat.st_size,
          "mtime_ns":stat.st_mtime_ns},ensure_ascii=False)+"\n")
     if path.suffix.lower()==".zip":
      nzip+=1
      try:
       with zipfile.ZipFile(path) as z:
        for info in z.infolist():
         nmembers+=1
         mw.write(json.dumps({"root":rid,"archive":rel,"member":info.filename,
                  "bytes":info.file_size,"crc32":info.CRC},ensure_ascii=False)+"\n")
      except Exception as e:badarchives.append({"root":rid,"rel":rel,"reason":str(e)[:200]})
     if path.suffix.lower()==".py" and stat.st_size<300_000:
      # Only study source scripts in root trees, not venv/site-packages.
      if rid==1 and any(x in path.parts for x in (".venv","target","__pycache__")):continue
      if rid==2 and "__pycache__" in path.parts:continue
      try:
       code=path.read_bytes()
       a=ast.parse(code)
       names=[x.name for x in a.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
       if any(k in rel.lower() for k in KEYWORDS) or any(any(k in t.lower() for k in KEYWORDS) for t in names):
        pythons.append({"root":rid,"rel":rel,"sha256":hashlib.sha256(code).hexdigest(),
                        "code_symbols":names[:180]})
      except (SyntaxError, UnicodeError):pass
   if errors:raise RuntimeError("OS traversal errors: "+repr(errors[:4]))
   results.append({"root_id":rid,"root_path":str(root),"files":nfiles,"directories":ndirs,
                   "bytes":bytes_,"zip_archives":nzip,"zip_members":nmembers,
                   "top_tree_counts":{k:{"files":v[0],"bytes":v[1]} for k,v in top.items()},
                   "top_extensions":kinds.most_common(15)})
   print("R94_SCAN_ROOT",rid,nfiles,ndirs,nzip,nmembers,flush=True)
   nentries+=nfiles+nmembers
 with (PRIVATE/"relevant_python_symbols.json").open("x") as f:
  json.dump({"scientific_code_symbols":pythons},f,ensure_ascii=False)
 con=sqlite3.connect(PRIVATE/"search.sqlite")
 con.execute("CREATE VIRTUAL TABLE idx USING fts5(rel, symbols, archive)")
 for d in pythons:
  con.execute("INSERT INTO idx VALUES(?,?,?)",(d["rel"]," ".join(d["code_symbols"]),""))
 with gzip.open(PRIVATE/"zip_members.jsonl.gz","rt") as f:
  for l in f:
   v=json.loads(l)
   con.execute("INSERT INTO idx VALUES(?,?,?)",(v["member"],"",v["archive"]))
 con.commit()
 search_count=con.execute("SELECT COUNT(*) FROM idx").fetchone()[0]
 con.close()
 choice=[]
 for rid,rel,role in CURATED:
  path=ROOTS[rid]/rel
  if not path.is_file():raise RuntimeError("missing curated file "+str(path))
  entry={"root_id":rid,"rel":rel,"role":role,"bytes":path.stat().st_size,"sha256":sha(path)}
  if path.suffix==".pdf":
   entry.update(pdf_metadata(path))
  choice.append(entry)
 record={"schema":"htt.r94.deep_reuse_three_paths/1",
         "local_roots":results,
         "all_physical_files":sum(x["files"] for x in results),
         "all_zip_member_records":sum(x["zip_members"] for x in results),
         "invalid_zip":badarchives,
         "curated_source_sha256":choice,
         "source_python_symbol_candidates":len(pythons),
         "private_local_index":str(PRIVATE/"search.sqlite"),
         "private_all_filename_index":str(PRIVATE/"file_metadata.jsonl.gz"),
         "private_all_zip_members":str(PRIVATE/"zip_members.jsonl.gz"),
         "source_modification":False,"file_extract_or_copy_to_repo":False,
         "duration_seconds":time.perf_counter()-begin}
 REPORT.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
 print("R94_DEEP_INDEX",json.dumps({"files":record["all_physical_files"],
       "zip_members":record["all_zip_member_records"],"curated":len(choice),
       "python_candidates":len(pythons),"duration":round(record["duration_seconds"],3)}))
 return record
if __name__=="__main__":build()
