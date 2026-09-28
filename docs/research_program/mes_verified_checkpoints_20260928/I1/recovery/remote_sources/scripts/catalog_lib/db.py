"""Portable, version-aware read model; original registries retain authority."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from . import SCHEMA_VERSION


def js(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def identity(*parts):
    return hashlib.sha256(js(parts).encode()).hexdigest()[:32]


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,kind TEXT NOT NULL,locator TEXT NOT NULL,
 origin TEXT,head TEXT,history_scope TEXT,details TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS commits(source_id TEXT NOT NULL REFERENCES sources(id),sha TEXT NOT NULL,
 tree_sha TEXT NOT NULL,parents TEXT NOT NULL,timestamp INTEGER,subject TEXT,
 PRIMARY KEY(source_id,sha));
CREATE TABLE IF NOT EXISTS refs(source_id TEXT NOT NULL REFERENCES sources(id),name TEXT NOT NULL,
 commit_sha TEXT NOT NULL,PRIMARY KEY(source_id,name));
CREATE TABLE IF NOT EXISTS trees(source_id TEXT NOT NULL REFERENCES sources(id),tree_sha TEXT NOT NULL,
 name TEXT NOT NULL,oid TEXT NOT NULL,kind TEXT NOT NULL,mode TEXT NOT NULL,
 PRIMARY KEY(source_id,tree_sha,name));
CREATE TABLE IF NOT EXISTS contents(id TEXT PRIMARY KEY,bytes INTEGER NOT NULL,language TEXT,
 processing_status TEXT NOT NULL,parser_version TEXT NOT NULL,summary TEXT,parsed TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(id),
 path TEXT NOT NULL,content_id TEXT REFERENCES contents(id),git_blob TEXT,observed_commit TEXT,
 role TEXT NOT NULL,language TEXT NOT NULL,processing_status TEXT NOT NULL,bytes INTEGER,
 container_id TEXT REFERENCES files(id),root_file_id TEXT,details TEXT NOT NULL DEFAULT '{}',
 UNIQUE(source_id,path,git_blob,container_id));
CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,file_id TEXT NOT NULL REFERENCES files(id),
 local_id TEXT NOT NULL,kind TEXT NOT NULL,name TEXT NOT NULL,owner TEXT NOT NULL,
 language TEXT NOT NULL,status TEXT NOT NULL,recorded_status TEXT NOT NULL,
 evidence_level TEXT NOT NULL,line INTEGER,end_line INTEGER,summary TEXT NOT NULL,
 details TEXT NOT NULL,UNIQUE(file_id,kind,local_id));
CREATE TABLE IF NOT EXISTS edges(id TEXT PRIMARY KEY,from_id TEXT NOT NULL REFERENCES records(id),
 relation TEXT NOT NULL,target TEXT NOT NULL,target_id TEXT,resolution TEXT NOT NULL,
 details TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS filesystem(source_id TEXT NOT NULL REFERENCES sources(id),path TEXT NOT NULL,
 kind TEXT NOT NULL,bytes INTEGER,mtime_ns INTEGER,device INTEGER,inode INTEGER,
 target TEXT,status TEXT NOT NULL,file_id TEXT REFERENCES files(id),PRIMARY KEY(source_id,path));
CREATE TABLE IF NOT EXISTS gaps(id TEXT PRIMARY KEY,source_id TEXT REFERENCES sources(id),
 path TEXT NOT NULL,operation TEXT NOT NULL,status TEXT NOT NULL,detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS commit_aliases(old_sha TEXT PRIMARY KEY,new_sha TEXT NOT NULL,basis TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS snapshots(source_id TEXT NOT NULL,commit_sha TEXT NOT NULL,
 PRIMARY KEY(source_id,commit_sha));
CREATE TABLE IF NOT EXISTS members(source_id TEXT NOT NULL,commit_sha TEXT NOT NULL,
 file_id TEXT NOT NULL REFERENCES files(id),PRIMARY KEY(source_id,commit_sha,file_id));
CREATE INDEX IF NOT EXISTS file_path ON files(source_id,path,git_blob);
CREATE INDEX IF NOT EXISTS file_content ON files(content_id);
CREATE INDEX IF NOT EXISTS file_root ON files(root_file_id);
CREATE INDEX IF NOT EXISTS record_kind ON records(kind,status,owner);
CREATE INDEX IF NOT EXISTS record_file ON records(file_id);
CREATE INDEX IF NOT EXISTS record_name ON records(local_id,name);
CREATE INDEX IF NOT EXISTS edge_from ON edges(from_id);
CREATE INDEX IF NOT EXISTS edge_target ON edges(target);
CREATE INDEX IF NOT EXISTS member_file ON members(file_id);
CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(record_id UNINDEXED,name,summary,terms,
 tokenize='unicode61');
CREATE VIEW IF NOT EXISTS catalog AS
 SELECT r.*,f.path,f.source_id,f.observed_commit,f.git_blob,f.content_id,f.role,
 f.processing_status AS file_status,COALESCE(f.root_file_id,f.id) AS root_file_id
 FROM records r JOIN files f ON f.id=r.file_id;
"""


def connect(path, *, readonly=False):
    path = Path(path)
    if readonly:
        c = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    if not readonly:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.executescript(SCHEMA)
        prior = c.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        if prior and int(json.loads(prior[0])) != SCHEMA_VERSION:
            raise ValueError("catalog schema version differs; rebuild in a new database")
        put_meta(c, "schema_version", SCHEMA_VERSION)
    return c


def put_meta(c, key, value):
    c.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, js(value)))


def get_meta(c, key, default=None):
    row = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default


def gap(c, source, path, operation, status, detail):
    c.execute("INSERT OR REPLACE INTO gaps VALUES (?,?,?,?,?,?)",
              (identity(source, path, operation, status), source, path, operation, status, str(detail)))


def reindex(c):
    c.execute("DELETE FROM search")
    c.execute("""INSERT INTO search(record_id,name,summary,terms)
      SELECT r.id,r.name,r.summary,f.path||' '||r.local_id||' '||r.recorded_status||' '||r.details
      FROM records r JOIN files f ON r.file_id=f.id""")


def counts(c):
    out = {t: c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
           for t in ("sources", "commits", "refs", "trees", "contents", "files", "records", "edges", "filesystem", "gaps")}
    for label, sql in {
        "records_by_kind": "SELECT kind,count(*) FROM records GROUP BY kind",
        "files_by_status": "SELECT processing_status,count(*) FROM files GROUP BY processing_status",
        "files_by_language": "SELECT language,count(*) FROM files GROUP BY language",
        "gaps_by_status": "SELECT status,count(*) FROM gaps GROUP BY status",
        "records_by_status": "SELECT status,count(*) FROM records GROUP BY status",
        "edges_by_resolution": "SELECT resolution,count(*) FROM edges GROUP BY resolution",
    }.items():
        out[label] = dict(c.execute(sql).fetchall())
    return out

def version_members(c,sid,sha):
    root=c.execute('SELECT tree_sha FROM commits WHERE source_id=? AND sha=?',(sid,sha)).fetchone()
    if not root:return []
    return [r[0] for r in c.execute("""WITH RECURSIVE walk(path,oid,kind) AS (
      SELECT name,oid,kind FROM trees WHERE source_id=? AND tree_sha=?
      UNION ALL SELECT w.path||'/'||t.name,t.oid,t.kind FROM walk w
      JOIN trees t ON t.source_id=? AND t.tree_sha=w.oid WHERE w.kind='tree')
      SELECT f.id FROM walk w JOIN files f ON f.source_id=? AND f.path=w.path AND f.git_blob=w.oid
      WHERE w.kind<>'tree' AND f.container_id IS NULL""",(sid,root[0],sid,sid))]
