"""R93 second exhaustive private legacy/source/zip inventory with code AST indexes.

User requested repeat deep-scan as R92 prior metadata failed to capture
some now-present extracted historical trees. Count every local file,
index all ZIP members (no extracting), AST parse small Python historical
sources to record function and class symbols. Create-only full private
SQLite/JSONL in ~/Downloads; publish only aggregate counts and curated hashes
to HTT research output. No legacy/external-drive source mutation.
"""
from pathlib import Path
from collections import Counter,defaultdict
import ast,gzip,hashlib,io,json,os,sqlite3,stat,time,zipfile

ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
LEGACY=ROOT/"legacy"
PRIVATE=Path.home()/"Downloads/htt_r93_legacy_index"
PUBLIC=ROOT/"docs/research_program/observational_publication_20261015/R93_THIRD_SCIENCE_LOOP_20261121/LEGACY_SECOND_DEEP_SCAN.json"
CANDIDATES=[
 "bass_htt_mio_github_ready_current/src/bass/PR13AG_projected_multipole_solver_restoration.py",
 "bass_htt_mio_github_ready_current/tests/test_pr13ag_projected_multipole_solver_restoration.py",
 "bass_htt_mio_github_ready_PR28_20260416/src/bass/PR13AG_projected_multipole_solver_restoration.py",
 "bass_htt_mio_github_ready_PR28_20260416/src/bass/PR20_background_geometry_depth.py",
 "bass_htt_mio_github_ready_PR28_20260416/src/bass/PR19_background_transport_collision_validation.py",
 "bianchi_departure_v091_github/htt/likelihood/biposh_masked.py",
 "bianchi_departure_v091_github/htt/likelihood/pixel_lowl.py",
 "code_package/catalog_likelihood.py",
 "bianchi-defect-framework-github/src/htt/infer/directional_likelihood.py",
 "cf4_p0/scripts/make_cf4_bulkflow_likelihood.py",
]
ZIPS=["bass_htt_mio_github_ready_current.zip","bass_htt_mio_github_ready_PR28_20260416.zip","bianchi_departure_v091_github.zip","code_package.zip"]
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for x in iter(lambda:f.read(2**20),b""):h.update(x)
 return h.hexdigest()
def analyze():
 if not LEGACY.is_dir():raise FileNotFoundError(LEGACY)
 if PUBLIC.exists() or PRIVATE.exists():
  raise RuntimeError("R93 create-only legacy index already exists")
 PRIVATE.mkdir(parents=True,exist_ok=False)
 start=time.monotonic()
 files=0;dirs=0;totalbytes=0;status=Counter()
 kinds=Counter();top=defaultdict(lambda:{"files":0,"bytes":0})
 code_rows=[];zip_rows=[]
 with gzip.open(PRIVATE/"all_files.jsonl.gz","wt") as fmeta, gzip.open(PRIVATE/"archive_members.jsonl.gz","wt") as fzip:
  for here,subdirs,names in os.walk(LEGACY,followlinks=False):
   dirs+=1
   for name in names:
    path=Path(here)/name
    try:st=path.lstat()
    except OSError as e:
     status["read_errors"]+=1;continue
    files+=1;totalbytes+=st.st_size
    rel=str(path.relative_to(LEGACY))
    fmeta.write(json.dumps({"rel":rel,"size":st.st_size,"mtime_ns":st.st_mtime_ns},ensure_ascii=False)+"\n")
    t=rel.split("/",1)[0]
    top[t]["files"]+=1;top[t]["bytes"]+=st.st_size
    suffix=path.suffix.lower()
    kinds[suffix]+=1
    if suffix==".py" and st.st_size<1_000_000:
     try:
      raw=path.read_bytes()
      node=ast.parse(raw,filename=rel)
      code_rows.append({"rel":rel,"sha256":hashlib.sha256(raw).hexdigest(),
         "func":[x.name for x in node.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))],
         "class":[x.name for x in node.body if isinstance(x,ast.ClassDef)]})
     except (SyntaxError,UnicodeDecodeError) as e:
      status["ast_parse_error"]+=1
    if suffix==".zip":
     try:
      with zipfile.ZipFile(path) as z:
       records=z.infolist()
       zip_rows.append({"zip":rel,"n_members":len(records),
                        "uncompressed_bytes":sum(x.file_size for x in records),
                        "zip_sha256":sha(path),
                        "zip_status":"ZIP_CENTRAL_DIRECTORY_INDEXED"})
       for x in records:
        fzip.write(json.dumps({"archive":rel,"member":x.filename,"size":x.file_size,"crc32":x.CRC},ensure_ascii=False)+"\n")
     except Exception as e:
      zip_rows.append({"zip":rel,"zip_status":"ERROR","reason":repr(e)})
 if status["read_errors"]: raise RuntimeError("source metadata traversal errors")
 selected=[]
 byrel={x["rel"]:x for x in code_rows}
 for name in CANDIDATES:
  if name in byrel:
   selected.append({**byrel[name],"known_limit":"source candidate, not automatically production validated"})
  else:selected.append({"rel":name,"status":"NOT_IN_CURRENT_TREE"})
 compare={}
 for name in ZIPS:
  path=LEGACY/name
  if not path.is_file():continue
  count_same=count_diff=count_missing=0
  with zipfile.ZipFile(path) as z:
   for info in z.infolist():
    if info.is_dir() or info.file_size>5_000_000:continue
    # For archives with root prefix, compare to extracted same-member path.
    target=LEGACY/info.filename
    if not target.is_file():
     target=LEGACY/name.removesuffix(".zip")/info.filename
    if not target.is_file():
     count_missing+=1;continue
    with z.open(info) as f: data=f.read()
    content_sha=hashlib.sha256(data).hexdigest()
    if content_sha==sha(target):count_same+=1
    else:count_diff+=1
  compare[name]={"bytes_identical":count_same,"content_mismatch":count_diff,
                  "extracted_missing_or_unmapped":count_missing}
 with (PRIVATE/"python_symbols.json").open("x") as f:
  json.dump({"symbols":code_rows},f,ensure_ascii=False)
 db=sqlite3.connect(PRIVATE/"legacy_search.sqlite")
 db.execute("create virtual table searchable using fts5(rel, symbol, kind, archive)")
 for z in code_rows:
  db.execute("insert into searchable (rel,symbol,kind,archive) values(?,?,?,?)",
   (z["rel"]," ".join(z["func"]+z["class"]),"python",""))
 with gzip.open(PRIVATE/"archive_members.jsonl.gz","rt") as f:
  for line in f:
   z=json.loads(line)
   db.execute("insert into searchable (rel,symbol,kind,archive) values(?,?,?,?)",
    (z["member"],"","archive_member",z["archive"]))
 db.commit()
 fts=db.execute("select count(*) from searchable").fetchone()[0]
 db.close()
 output={
  "schema":"htt.r93.legacy_repeat_exhaustive_index/1",
  "root":str(LEGACY),"physical_file_count":files,"directory_count":dirs,
  "physical_file_bytes_sum":totalbytes,
  "python_AST_parsed_count":len(code_rows),
  "zip_count":len(zip_rows),
  "zip_status_counts":dict(Counter(z["zip_status"] for z in zip_rows)),
  "zip_member_count":sum(z.get("n_members",0) for z in zip_rows),
  "zip_uncompressed_bytes_sum":sum(z.get("uncompressed_bytes",0) for z in zip_rows),
  "sqlite_FTS_search_entries":fts,
  "private_search_database":str(PRIVATE/"legacy_search.sqlite"),
  "private_full_filename_index":str(PRIVATE/"all_files.jsonl.gz"),
  "private_full_zipmember_index":str(PRIVATE/"archive_members.jsonl.gz"),
  "code_candidate_symbols":selected,
  "top_extracted_trees":dict(top),
  "selected_archive_extracted_identity":compare,
  "status":dict(status),
  "no_source_modification":True,"archives_not_extracted":True,
  "scan_duration_seconds":round(time.monotonic()-start,2)
 }
 PUBLIC.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"files":files,"dirs":dirs,"zips":len(zip_rows),"zip_members":output["zip_member_count"],
    "AST_python":len(code_rows),"FTS_index":fts,"seconds":output["scan_duration_seconds"],
    "archived_extracted_identity":compare},ensure_ascii=False)[:3900])
if __name__=="__main__":analyze()
