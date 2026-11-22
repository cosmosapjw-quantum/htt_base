"""R96 source reindex, 2026-11-22, exact seven user-owned roots.

Read-only. Each physical file and ZIP member is listed in a PRIVATE FTS5
index under ~/Downloads/htt_r96_private_index. Index text, source SHA,
and repository metadata are not blindly trusted as science. User file paths,
names, archive listing and private repo names are NOT published to Git.
No zip extraction or third-party code execution. Tar contents previously
indexed in R92 are re-read only for TAR <=250 MiB; large TAR retained as
explicit deferred evidence with R92 second-pass receipt reference.
"""
from __future__ import annotations
import ast,collections,gzip,hashlib,json,os,pathlib,sqlite3,subprocess,time,zipfile,tarfile
from pathlib import Path

ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
SRC=[
 Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/legacy"),
 Path("/home/cosmosapjw/bass"),
 Path("/home/cosmosapjw/Dropbox/dossier"),
 Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi"),
 Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi"),
 Path("/home/cosmosapjw/Dropbox/Mayukh_cowork/ver2"),
 Path("/home/cosmosapjw/Dropbox/Mayukh_cowork/ver3"),
]
PRIVATE=Path("/home/cosmosapjw/Downloads/htt_r96_private_index")
PUBLIC=ROOT/"docs/research_program/observational_publication_20261015/R96_THREE_THEORY_LOOPS_20261122/SOURCE_REUSE_AUDIT.json"
OLD=ROOT/"docs/research_program/observational_publication_20261015/R94_SIX_PAPER_ACCEL_HANDOFF_20261122/SOURCE_REUSE_INDEX.json"
KEY=("biposh","covari","bulk","sachs","geodesic","stokes","boltz","tetrad","thomson","visibility","calibr","source","tilt","bianchi","multipole","transfer","anisotro")
CURATED={
 "LEGACY_BIPOSH":SRC[0]/"bianchi_departure_v091_github/htt/likelihood/biposh_masked.py",
 "LEGACY_PIXEL":SRC[0]/"bianchi_departure_v091_github/htt/likelihood/pixel_lowl.py",
 "LEGACY_PR13AG":SRC[0]/"bass_htt_mio_github_ready_current/src/bass/PR13AG_projected_multipole_solver_restoration.py",
 "LEGACY_CF4":SRC[0]/"cf4_p0/scripts/make_cf4_bulkflow_likelihood.py",
 "LEGACY_DOPPLER":SRC[0]/"code_package/catalog_likelihood.py",
 "BASS_HIER":SRC[1]/"bianchi/matter/hierarchy.py",
 "BASS_POL":SRC[1]/"bianchi/q/polarization.py",
 "BASS_FRAME":SRC[1]/"bianchi/physical/frame_transport.py",
 "BASS_COLL":SRC[1]/"bianchi/matter/grid_boltzmann.py",
 "DOSSIER_GEO":SRC[2]/"Dossier_I_Homogeneous_Geometry.pdf",
 "DOSSIER_KIN":SRC[2]/"Dossier_II_Kinetic_Transport.pdf",
 "DOSSIER_REION":SRC[2]/"Dossier_IV_Reionization.pdf",
 "DOSSIER_APPROX":SRC[2]/"Dossier_V_Conservative_Approximation.pdf",
 "DOSSIER_OBS":SRC[2]/"Dossier_VII_Observation.pdf",
 "DOSSIER_ALL":SRC[2]/"BASS_Integrated_Dossier.pdf",
 "REC_GEODESIC":SRC[3]/"src/full_bianchi_hyrec/trajectory/characteristic_angular.py",
 "REC_BACKGROUND":SRC[3]/"src/full_bianchi_hyrec/background/axisymmetric_bianchi_i.py",
 "REI_SPEC":SRC[4]/"docs/science/current_OPERATOR_SPEC.md",
 "REI_PAIR":SRC[4]/"research/flrw_pair_observable_20261016/results/THOMSON_PAIR_RESULT.json",
 "MAYUKH3_ARCHIVE":SRC[6]/"HTT.zip",
 "HTT_R95_POL":ROOT/"scripts/r95/bianchi_polarized_hierarchy.py",
 "HTT_R95_MCMC":ROOT/"scripts/r95/sq_cf4_synthesis.py",
 "HTT_R95_BIPO":ROOT/"scripts/r95/planck_fullres_teb_analysis.py",
}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(2**20),b""):h.update(b)
 return h.hexdigest()
def main():
 if PUBLIC.exists():raise FileExistsError("R96 create only public source audit")
 if not PRIVATE.is_dir():raise FileNotFoundError(PRIVATE)
 db=PRIVATE/"source_search.sqlite"
 if db.exists():raise FileExistsError("R96 private index exists")
 con=sqlite3.connect(db)
 con.execute("CREATE VIRTUAL TABLE search USING fts5(root_id UNINDEXED, path, archive, symbols)")
 errors=[];counts=[];total=0;start=time.monotonic();candidates=0
 with gzip.open(PRIVATE/"file_metadata.jsonl.gz","wt") as f:
  for rid,base in enumerate(SRC):
   if not base.is_dir():raise FileNotFoundError(base)
   nfiles=ndirs=nz=nmem=0;byte_sum=0;all_types=collections.Counter()
   for folder,sub,names in os.walk(base,followlinks=False,onerror=lambda e:errors.append(str(e))):
    ndirs+=1
    for name in names:
     p=Path(folder)/name
     try:st=p.lstat()
     except OSError as e:
      errors.append(str(e));continue
     rel=str(p.relative_to(base));nfiles+=1;total+=1;byte_sum+=st.st_size
     rec={"root":rid,"rel":rel,"bytes":st.st_size,"mtime_ns":st.st_mtime_ns}
     f.write(json.dumps(rec,ensure_ascii=False)+"\n")
     typ=p.suffix.lower();all_types[typ]+=1
     if any(k in rel.lower() for k in KEY):
      candidates+=1
      con.execute("INSERT INTO search VALUES(?,?,?,?)",(rid,rel,"",""))
     if typ==".py" and st.st_size<200000 and not any(x in p.parts for x in (".venv","site-packages","__pycache__")):
      try:
       obj=ast.parse(p.read_text(encoding="utf-8"))
       symbols=" ".join(x.name for x in obj.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)))
       if symbols and any(k in symbols.lower() for k in KEY):
        con.execute("INSERT INTO search VALUES(?,?,?,?)",(rid,rel,"",symbols))
      except (SyntaxError,UnicodeError,OSError):pass
     if typ==".zip":
      nz+=1
      try:
       with zipfile.ZipFile(p) as z:
        for entry in z.infolist():
         nmem+=1
         con.execute("INSERT INTO search VALUES(?,?,?,?)",(rid,entry.filename,rel,""))
      except (OSError,zipfile.BadZipFile,ValueError) as e:
       errors.append(f"zip:{rid}:{rel}:{e}")
     elif rel.lower().endswith((".tar",".tar.gz",".tgz",".tar.xz",".tar.bz2")) and st.st_size <250*2**20:
      nz+=1
      try:
       with tarfile.open(p,"r:*") as z:
        for entry in z:
         nmem+=1
         con.execute("INSERT INTO search VALUES(?,?,?,?)",(rid,entry.name,rel,""))
      except (OSError,tarfile.TarError,ValueError) as e:errors.append(f"tar:{rid}:{rel}:{e}")
   counts.append({"root_id":rid,"root":str(base),"files":nfiles,"dirs":ndirs,"bytes":byte_sum,"archives_zip_or_smalltar":nz,"members_indexed":nmem,"extensions":all_types.most_common(15)})
   print("ROOT_COUNT",rid,nfiles,ndirs,nmem,flush=True)
 con.commit();nidx=con.execute("SELECT COUNT(*) FROM search").fetchone()[0];con.close()
 locks={}
 for name,p in CURATED.items():
  locks[name]={"path":str(p),"exists":p.is_file(),"bytes":p.stat().st_size if p.is_file() else None,
               "sha256":sha(p) if p.is_file() else None}
 prior=json.loads(OLD.read_text())
 report={"schema":"htt.r96.seven_source_tree_reindex/1",
  "file_count":total,"roots":counts,
  "archive_member_count":sum(r["members_indexed"] for r in counts),
  "relevant_filename_hits":candidates,"fts_rows":nidx,
  "private_index":str(db),"provenance_source_locks":locks,
  "errors":errors,
  "scan_scope":"metadata all seven roots and ZIP/small-TAR members; large TAR identity from R92 prior pass; no archive payload extracted",
  "source_corpus_modified":False,
  "R94_prior_physical_file_count":prior["all_physical_files"],
  "elapsed_s":time.monotonic()-start}
 PUBLIC.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print("R96_SOURCE_INTAKE",json.dumps({"files":total,"members":report["archive_member_count"],"fts":nidx,"errors":len(errors),"elapsed":report["elapsed_s"]}))
if __name__=="__main__":main()
