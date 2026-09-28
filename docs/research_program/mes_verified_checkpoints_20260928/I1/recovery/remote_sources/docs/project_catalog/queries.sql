-- Open restored catalog.sqlite with sqlite3 or another SQLite client.
-- These queries only read the catalog; they do not execute research code.

-- Full coverage by source, language and processing status.
SELECT source_id,language,processing_status,count(*) AS versions
FROM files GROUP BY source_id,language,processing_status ORDER BY source_id,language;

-- Recorded proposition statuses, never a fresh proof verdict.
SELECT local_id,name,recorded_status,status,source_id,path,observed_commit
FROM catalog WHERE kind='proposition' ORDER BY path,local_id;

-- CF4 analysis candidates with exact static details.
SELECT id,name,status,path,observed_commit,details
FROM catalog WHERE kind='analysis' AND id IN
 (SELECT record_id FROM search WHERE search MATCH 'CF4');

-- Definitions that explicitly lack a body, excluding abstract interfaces.
SELECT id,name,path,source_id,observed_commit,details
FROM catalog WHERE kind='code' AND status='stub';

-- Follow-up items with their reasons and successor references.
SELECT id,name,path,status,details FROM catalog WHERE kind='update';

-- Unresolved source links on recorded-active proposition records.
SELECT r.id,r.name,r.recorded_status,f.path,f.observed_commit,e.target,e.resolution
FROM edges e JOIN records r ON r.id=e.from_id JOIN files f ON f.id=r.file_id
WHERE r.kind='proposition' AND r.status IN ('recorded_active','recorded_conditional','recorded_proven_or_derived')
 AND e.relation='references' AND e.resolution='unresolved_at_source_version';

-- Physical aliases: repeated worktrees do not imply additional implementations.
SELECT file_id,count(*) AS locations FROM filesystem WHERE file_id IS NOT NULL
GROUP BY file_id HAVING count(*)>1 ORDER BY locations DESC LIMIT 50;

-- Scanned branch and dependency versions.
SELECT s.id,s.kind,s.locator,s.head,s.history_scope,count(c.sha) AS commit_records
FROM sources s LEFT JOIN commits c ON s.id=c.source_id GROUP BY s.id ORDER BY s.id;

-- Explicit coverage gaps, including files that could not be parsed.
SELECT source_id,path,operation,status,detail FROM gaps ORDER BY source_id,path;

-- Migration statements (including plans and rejected migrations), not verified ports.
SELECT id,name,status,path,observed_commit,summary,details
FROM catalog WHERE kind='port';

-- Explicit old/new commit mapping retained from the history rewrite.
SELECT old_sha,new_sha,basis FROM commit_aliases ORDER BY old_sha;

-- A saved reference is bound to this occurrence, not to every later ref.
SELECT r.id,r.local_id,r.recorded_status,f.observed_commit,e.target,e.resolution,e.target_id
FROM records r JOIN files f ON f.id=r.file_id JOIN edges e ON e.from_id=r.id
WHERE r.kind='proposition' AND e.relation='references' LIMIT 100;

-- Chronological representative occurrences of a path (not inferred introduction dates).
SELECT f.path,f.source_id,f.observed_commit,datetime(c.timestamp,'unixepoch') AS observed_commit_utc,
 f.git_blob,f.processing_status
FROM files f LEFT JOIN commits c ON c.source_id=f.source_id AND c.sha=f.observed_commit
WHERE f.path='htt/src/common/theorem_registry.py'
ORDER BY c.timestamp,f.source_id,f.id;

-- Plans for which this static scan has no bound implementation-file reference.
-- This does not prove that no dynamic, indirect or unregistered implementation exists.
SELECT p.id,p.name,p.recorded_status,f.source_id,f.path,f.observed_commit,
 'NO_BOUND_IMPLEMENTATION_REFERENCE' AS static_wiring_status
FROM records p JOIN files f ON f.id=p.file_id
WHERE p.kind='plan' AND p.status='candidate' AND NOT EXISTS (
 SELECT 1 FROM edges e JOIN files implementation ON implementation.id=e.target_id
 WHERE e.from_id=p.id AND e.relation='references' AND implementation.role='code')
ORDER BY f.source_id,f.path,p.id LIMIT 100;
