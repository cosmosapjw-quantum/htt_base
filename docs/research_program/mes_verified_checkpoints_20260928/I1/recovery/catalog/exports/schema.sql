CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);

CREATE TABLE sources(id TEXT PRIMARY KEY,kind TEXT NOT NULL,locator TEXT NOT NULL,
 origin TEXT,head TEXT,history_scope TEXT,details TEXT NOT NULL DEFAULT '{}');

CREATE TABLE commits(source_id TEXT NOT NULL REFERENCES sources(id),sha TEXT NOT NULL,
 tree_sha TEXT NOT NULL,parents TEXT NOT NULL,timestamp INTEGER,subject TEXT,
 PRIMARY KEY(source_id,sha));

CREATE TABLE refs(source_id TEXT NOT NULL REFERENCES sources(id),name TEXT NOT NULL,
 commit_sha TEXT NOT NULL,PRIMARY KEY(source_id,name));

CREATE TABLE trees(source_id TEXT NOT NULL REFERENCES sources(id),tree_sha TEXT NOT NULL,
 name TEXT NOT NULL,oid TEXT NOT NULL,kind TEXT NOT NULL,mode TEXT NOT NULL,
 PRIMARY KEY(source_id,tree_sha,name));

CREATE TABLE contents(id TEXT PRIMARY KEY,bytes INTEGER NOT NULL,language TEXT,
 processing_status TEXT NOT NULL,parser_version TEXT NOT NULL,summary TEXT,parsed TEXT NOT NULL);

CREATE TABLE files(id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(id),
 path TEXT NOT NULL,content_id TEXT REFERENCES contents(id),git_blob TEXT,observed_commit TEXT,
 role TEXT NOT NULL,language TEXT NOT NULL,processing_status TEXT NOT NULL,bytes INTEGER,
 container_id TEXT REFERENCES files(id),root_file_id TEXT,details TEXT NOT NULL DEFAULT '{}',
 UNIQUE(source_id,path,git_blob,container_id));

CREATE TABLE records(id TEXT PRIMARY KEY,file_id TEXT NOT NULL REFERENCES files(id),
 local_id TEXT NOT NULL,kind TEXT NOT NULL,name TEXT NOT NULL,owner TEXT NOT NULL,
 language TEXT NOT NULL,status TEXT NOT NULL,recorded_status TEXT NOT NULL,
 evidence_level TEXT NOT NULL,line INTEGER,end_line INTEGER,summary TEXT NOT NULL,
 details TEXT NOT NULL,UNIQUE(file_id,kind,local_id));

CREATE TABLE edges(id TEXT PRIMARY KEY,from_id TEXT NOT NULL REFERENCES records(id),
 relation TEXT NOT NULL,target TEXT NOT NULL,target_id TEXT,resolution TEXT NOT NULL,
 details TEXT NOT NULL DEFAULT '{}');

CREATE TABLE filesystem(source_id TEXT NOT NULL REFERENCES sources(id),path TEXT NOT NULL,
 kind TEXT NOT NULL,bytes INTEGER,mtime_ns INTEGER,device INTEGER,inode INTEGER,
 target TEXT,status TEXT NOT NULL,file_id TEXT REFERENCES files(id),PRIMARY KEY(source_id,path));

CREATE TABLE gaps(id TEXT PRIMARY KEY,source_id TEXT REFERENCES sources(id),
 path TEXT NOT NULL,operation TEXT NOT NULL,status TEXT NOT NULL,detail TEXT NOT NULL);

CREATE TABLE commit_aliases(old_sha TEXT PRIMARY KEY,new_sha TEXT NOT NULL,basis TEXT NOT NULL);

CREATE TABLE snapshots(source_id TEXT NOT NULL,commit_sha TEXT NOT NULL,
 PRIMARY KEY(source_id,commit_sha));

CREATE TABLE members(source_id TEXT NOT NULL,commit_sha TEXT NOT NULL,
 file_id TEXT NOT NULL REFERENCES files(id),PRIMARY KEY(source_id,commit_sha,file_id));

CREATE TABLE 'search_data'(id INTEGER PRIMARY KEY, block BLOB);

CREATE TABLE 'search_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;

CREATE TABLE 'search_content'(id INTEGER PRIMARY KEY, c0, c1, c2, c3);

CREATE TABLE 'search_docsize'(id INTEGER PRIMARY KEY, sz BLOB);

CREATE TABLE 'search_config'(k PRIMARY KEY, v) WITHOUT ROWID;

CREATE INDEX file_path ON files(source_id,path,git_blob);

CREATE INDEX file_content ON files(content_id);

CREATE INDEX file_root ON files(root_file_id);

CREATE INDEX record_kind ON records(kind,status,owner);

CREATE INDEX record_file ON records(file_id);

CREATE INDEX record_name ON records(local_id,name);

CREATE INDEX edge_from ON edges(from_id);

CREATE INDEX edge_target ON edges(target);

CREATE INDEX member_file ON members(file_id);

CREATE VIRTUAL TABLE search USING fts5(record_id UNINDEXED,name,summary,terms,
 tokenize='unicode61');

CREATE VIEW catalog AS
 SELECT r.*,f.path,f.source_id,f.observed_commit,f.git_blob,f.content_id,f.role,
 f.processing_status AS file_status,COALESCE(f.root_file_id,f.id) AS root_file_id
 FROM records r JOIN files f ON f.id=r.file_id;