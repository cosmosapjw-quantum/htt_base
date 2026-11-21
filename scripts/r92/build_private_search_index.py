"""R92 persistent private searchable index over all seven user-specified trees.

Combines metadata census, ZIP/TAR member indexes, successful large-TAR second
pass into SQLite FTS5, create-only under ~/Downloads. Never extracts archive
payloads. Includes source IDs only, content SHA only in separate curated
source-lock records. No Git upload of full path/user file inventory.
"""
import gzip,json,sqlite3
from pathlib import Path

OUT=Path("/home/cosmosapjw/Downloads/htt_r92_private_index")
PREFIX=OUT/"R92_DEEP_INDEX_20261121"
DB=OUT/"R92_SEARCH_INDEX.sqlite"
if DB.exists():raise RuntimeError("R92 create-only: search index already exists")
con=sqlite3.connect(DB)
con.execute("PRAGMA journal_mode=OFF")
con.execute("PRAGMA synchronous=OFF")
con.execute("CREATE TABLE files (id INTEGER PRIMARY KEY, root_id INTEGER NOT NULL, source_type TEXT NOT NULL, rel TEXT NOT NULL, archive TEXT, bytes INTEGER NOT NULL, category TEXT)")
con.execute("CREATE VIRTUAL TABLE file_fts USING fts5(rel, archive, content='files',content_rowid='id',tokenize='unicode61')")
def store(obj):
 rel=obj.get("rel") or obj.get("name") or ""
 arc=obj.get("archive","")
 size=int(obj.get("bytes",0))
 c=obj.get("kind",obj.get("type",""))
 if "archive" in obj and "name" in obj:
  rel=obj["name"]
  if obj.get("nested_archive"):
   arc=arc+"::"+obj["nested_archive"]
  typ="archive_member"
 else:typ="physical_file"
 con.execute("INSERT INTO files(root_id,source_type,rel,archive,bytes,category) VALUES(?,?,?,?,?,?)",(
     int(obj["root"]),typ,rel,arc,size,c))
with gzip.open(PREFIX.with_suffix(".files.jsonl.gz"),"rt",encoding="utf8") as f:
 for line in f:store(json.loads(line))
with gzip.open(PREFIX.with_suffix(".archive_members.jsonl.gz"),"rt",encoding="utf8") as f:
 for line in f:store(json.loads(line))
big=json.loads((OUT/"R92_LARGETAR_SECOND_PASS.json").read_text())
for i,item in enumerate(big):
 if item["status"]!="INDEXED_TAR_SECOND_PASS":continue
 memberpath=Path(item["private_member_index"])
 for line in memberpath.read_text(errors="replace").splitlines():
  store({"root":1,"archive":item["original"],"name":line,"bytes":0,"kind":"unknown"})
con.execute("INSERT INTO file_fts(file_fts) VALUES('rebuild')")
con.execute("CREATE INDEX idx_files_root ON files(root_id,source_type)")
con.commit()
total=con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
data={"schema":"htt.r92.searchable_private_code_archive_index/1",
 "database":str(DB),"count":total,
 "by_type":dict(con.execute("SELECT source_type,COUNT(*) FROM files GROUP BY source_type").fetchall()),
 "examples":{}}
for term in ("biposh","thomson","high_l","bianchi","sachs","geodesic","vorticity"):
 rows=con.execute("SELECT COUNT(*) FROM file_fts WHERE file_fts MATCH ?",(term,)).fetchone()[0]
 data["examples"][term]=rows
con.close()
manifest=OUT/"R92_SEARCH_INDEX_STATUS.json"
if manifest.exists():raise RuntimeError("R92 search status exists")
manifest.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(data,ensure_ascii=False,indent=2))
