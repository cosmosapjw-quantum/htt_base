"""Read-only catalog queries, including any stored commit without a Git checkout."""
from __future__ import annotations

import csv
import io
import json
import sqlite3
from pathlib import Path

from .db import counts, get_meta, version_members


def resolve_ref(c, ref, source=None):
    if ref in (None,'all','working'): return None
    base=get_meta(c,'baseline',{})
    if ref=='baseline':return base['source_id'],base['commit']
    args=[]
    where=''
    if source:where=' AND source_id=?';args.append(source)
    rows=c.execute('SELECT source_id,commit_sha FROM refs WHERE (name=? OR name=? OR name=?)'+where,
                   [ref,'refs/heads/'+ref,'refs/remotes/'+ref,*args]).fetchall()
    if not rows:
        rows=c.execute('SELECT source_id,sha FROM commits WHERE sha LIKE ?'+where,[ref+'%',*args]).fetchall()
    values=set()
    for sid,sha in rows:
        metadata=c.execute('SELECT details FROM sources WHERE id=?',(sid,)).fetchone()
        canonical=json.loads(metadata[0]).get('canonical_source',sid) if metadata else sid
        values.add((canonical,sha))
    if len(values)!=1:raise ValueError(f'ref {ref!r}: expected one version, found {len(values)}; supply --source or a full commit')
    return next(iter(values))


def selected(c, ref, table, source=None):
    resolved=resolve_ref(c,ref,source)
    if resolved is None:return None
    sid,sha=resolved
    c.execute(f'CREATE TEMP TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY)')
    c.execute(f'DELETE FROM {table}')
    if c.execute('SELECT 1 FROM snapshots WHERE source_id=? AND commit_sha=?',(sid,sha)).fetchone():
        c.execute(f'INSERT INTO {table} SELECT file_id FROM members WHERE source_id=? AND commit_sha=?',(sid,sha))
    else:
        c.executemany(f'INSERT OR IGNORE INTO {table} VALUES (?)',[(x,) for x in version_members(c,sid,sha)])
    return resolved


def query(c, *, kind=None, text=None, owner=None, status=None, language=None,
          evidence=None, source=None, ref='baseline', not_in_ref=None, needs_update=False,
          port_status=None, limit=50, offset=0, stream=False):
    clauses=[];args=[]
    if kind in {'asset','gap','source','ref'}:
        table={'asset':'filesystem','gap':'gaps','source':'sources','ref':'refs'}[kind]
        fields={x[1] for x in c.execute(f'PRAGMA table_info({table})')}
        if source and 'source_id' in fields:clauses.append('source_id=?');args.append(source)
        elif source and kind=='source':clauses.append('id=?');args.append(source)
        if text:
            field='path' if 'path' in fields else 'name' if 'name' in fields else 'locator'
            clauses.append(field+' LIKE ?');args.append('%'+text+'%')
        if status and 'status' in fields:clauses.append('status=?');args.append(status)
        sql=f'SELECT * FROM {table}'+(' WHERE '+' AND '.join(clauses) if clauses else '')
        sql+=' ORDER BY '+('path' if 'path' in fields else 'name' if 'name' in fields else 'id')+' LIMIT ? OFFSET ?'
        rows=(dict(r) for r in c.execute(sql,[*args,limit,offset]))
        return rows if stream else list(rows)
    for column,value in [('kind',kind),('owner',owner),('status',status),('language',language),('evidence_level',evidence),('source_id',source)]:
        if value:clauses.append('v.'+column+'=?');args.append(value)
    if needs_update:clauses.append("v.kind='update'")
    if text:
        # Literal terms avoid exposing FTS syntax as accidental operators.
        terms=' AND '.join('"'+t.replace('"','""')+'"' for t in text.split())
        clauses.append("(v.id IN (SELECT record_id FROM search WHERE search MATCH ?) OR v.name LIKE ? OR v.path LIKE ?)")
        args.extend([terms,'%'+text+'%','%'+text+'%'])
    if ref=='working':clauses.append("EXISTS (SELECT 1 FROM filesystem fs WHERE fs.file_id=v.root_file_id AND fs.status='observed')")
    elif selected(c,ref,'query_selected',source):clauses.append('v.root_file_id IN (SELECT id FROM query_selected)')
    if not_in_ref:
        if not_in_ref in {'all','working'}:raise ValueError('--not-in-ref requires a concrete branch/commit or baseline, not all/working')
        selected(c,not_in_ref,'query_excluded')
        clauses.append('NOT EXISTS (SELECT 1 FROM files b JOIN query_excluded x ON b.id=x.id WHERE b.content_id=v.content_id AND b.path=v.path)')
    if port_status:
        selected(c,'baseline','query_baseline')
        exists='EXISTS (SELECT 1 FROM files b JOIN query_baseline x ON b.id=x.id WHERE b.content_id=v.content_id AND v.content_id IS NOT NULL)'
        if port_status=='byte-identical':clauses.append(exists)
        elif port_status=='no-identical-match':clauses.append('NOT '+exists)
    sql='SELECT v.* FROM catalog v'+(' WHERE '+' AND '.join(clauses) if clauses else '')
    sql+=' ORDER BY v.kind,v.path,v.local_id,v.id LIMIT ? OFFSET ?'
    rows=(dict(row) for row in c.execute(sql,[*args,limit,offset]))
    return rows if stream else list(rows)


def show(c, identifier):
    r=c.execute('SELECT * FROM catalog WHERE id=?',(identifier,)).fetchone()
    if not r:
        matches=c.execute('SELECT id FROM records WHERE local_id=? OR id LIKE ? LIMIT 3',(identifier,identifier+'%')).fetchall()
        if len(matches)!=1:raise ValueError(f'record {identifier!r}: not unique or absent; query its exact id')
        r=c.execute('SELECT * FROM catalog WHERE id=?',(matches[0][0],)).fetchone()
    out=dict(r);out['details']=json.loads(out['details'])
    out['relationships']=[dict(x) for x in c.execute('SELECT * FROM edges WHERE from_id=? ORDER BY relation,target',(r['id'],))]
    out['ref_membership']=[dict(x) for x in c.execute('SELECT refs.source_id,refs.name,refs.commit_sha FROM refs JOIN members ON refs.source_id=members.source_id AND refs.commit_sha=members.commit_sha WHERE members.file_id=? ORDER BY refs.source_id,refs.name',(r['root_file_id'],))]
    out['physical_locations']=[dict(x) for x in c.execute('SELECT source_id,path,status FROM filesystem WHERE file_id=? ORDER BY source_id,path',(r['root_file_id'],))]
    out['version_binding']='observed_commit is a representative occurrence, not an introduction date'
    out['relationship_binding']={'source_id':r['source_id'],'observed_commit':r['observed_commit'],
        'note':'stored relationships apply to this representative occurrence; no assertion of applicability to every ref containing unchanged source text'}
    if r['kind']=='proposition':
        registered_id=out['details'].get('registered_id')
        matched=[]
        references=[e for e in out['relationships'] if e['relation']=='references']
        for edge in references:
            if not edge['target_id'] or not registered_id:continue
            for evidence in c.execute("SELECT id,kind,recorded_status,details FROM records WHERE file_id=? AND kind IN ('proposition','evidence')",(edge['target_id'],)):
                details=json.loads(evidence['details'])
                if details.get('registered_id')==registered_id:
                    matched.append({'record_id':evidence['id'],'referenced_path':edge['target'],
                                    'recorded_status':evidence['recorded_status']})
        out['proof_evidence']={
            'recorded_proof_claim':r['status']=='recorded_proven_or_derived',
            'reference_count':len(references),
            'bound_reference_count':sum(e['target_id'] is not None for e in references),
            'matching_id_records':matched,
            'support_status':'REFERENCED_RECORD_WITH_MATCHING_ID' if matched else 'REFERENCED_FILES_ONLY' if any(e['target_id'] for e in references) else 'NO_BOUND_REFERENCE',
            'proof_validation':'NOT_RECHECKED',
            'assumption_alignment':'NOT_VERIFIED; matching IDs and file presence do not establish the same mathematical statement or a valid proof'}
    return out


def history(c, identifier, limit=100):
    row=c.execute('SELECT path,local_id,kind,name,content_id FROM catalog WHERE id=?',(identifier,)).fetchone()
    if row:
        if row['kind']=='code':
            return [dict(x) for x in c.execute('SELECT * FROM catalog WHERE kind=? AND name=? AND (path=? OR content_id=?) ORDER BY source_id,observed_commit,id LIMIT ?',
                (row['kind'],row['name'],row['path'],row['content_id'],limit))]
        return [dict(x) for x in c.execute('SELECT * FROM catalog WHERE path=? AND local_id=? AND kind=? ORDER BY source_id,observed_commit,id LIMIT ?',
            (row['path'],row['local_id'],row['kind'],limit))]
    return [dict(x) for x in c.execute('SELECT * FROM files WHERE path=? ORDER BY source_id,observed_commit,id LIMIT ?',(identifier,limit))]


def check(c):
    issues=[]
    integrity=c.execute('PRAGMA integrity_check').fetchone()[0]
    if integrity!='ok':issues.append(integrity)
    issues.extend(str(tuple(x)) for x in c.execute('PRAGMA foreign_key_check'))
    tests={
      'file_processing_status_missing':"SELECT count(*) FROM files WHERE processing_status IS NULL OR processing_status=''",
      'scientific_promotion_generated':"SELECT count(*) FROM records WHERE status IN ('PROVEN','VALIDATED','CAS_4AXIS_PASS','EXECUTABLE_CONFIRMED')",
      'dangling_edge_target':"SELECT count(*) FROM edges e WHERE e.target_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM files f WHERE f.id=e.target_id) AND NOT EXISTS (SELECT 1 FROM records r WHERE r.id=e.target_id)",
      'orphan_archive_root':"SELECT count(*) FROM files f WHERE f.root_file_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM files r WHERE r.id=f.root_file_id)",
      'fts_count_mismatch':"SELECT abs((SELECT count(*) FROM search)-(SELECT count(*) FROM records))",
      'observed_regular_file_without_version':"SELECT count(*) FROM filesystem WHERE kind='file' AND status='observed' AND file_id IS NULL",
      'git_leaf_without_file_version':"""WITH RECURSIVE walk(source_id,path,oid,kind) AS (
        SELECT t.source_id,t.name,t.oid,t.kind FROM trees t JOIN commits c
          ON t.source_id=c.source_id AND t.tree_sha=c.tree_sha JOIN sources s ON s.id=c.source_id WHERE s.kind='git'
        UNION SELECT t.source_id,w.path||'/'||t.name,t.oid,t.kind FROM walk w JOIN trees t
          ON t.source_id=w.source_id AND t.tree_sha=w.oid WHERE w.kind='tree')
        SELECT count(*) FROM walk w WHERE w.kind<>'tree' AND NOT EXISTS
          (SELECT 1 FROM files f WHERE f.source_id=w.source_id AND f.path=w.path
           AND f.git_blob=w.oid AND f.container_id IS NULL)""",
    }
    results={key:c.execute(sql).fetchone()[0] for key,sql in tests.items()}
    issues.extend(f'{k}: {v}' for k,v in results.items() if v)
    return {'status':'PASS' if not issues else 'FAIL','integrity':integrity,'checks':results,'issues':issues,
            'counts':counts(c),'claim_scope':'catalog structural checks only; research execution/proof not performed'}


def render(rows, format='table'):
    if format=='json':return json.dumps(rows,ensure_ascii=False,indent=2,default=str)+'\n'
    if format=='csv':
        buf=io.StringIO(); fields=list(rows[0]) if rows else ['id']
        w=csv.DictWriter(buf,fieldnames=fields);w.writeheader();w.writerows(rows);return buf.getvalue()
    if not rows:return '(no matches)\n'
    wanted=['id','kind','name','status','recorded_status','path','source_id','observed_commit']
    fields=[x for x in wanted if x in rows[0]] or list(rows[0])[:7]
    return '\t'.join(fields)+'\n'+'\n'.join('\t'.join(str(r.get(k,'')).replace('\n',' ') for k in fields) for r in rows)+'\n'


def write_rows(rows, path, format='table'):
    """Bounded-memory export for million-record catalogs."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    rows=iter(rows);first=next(rows,None)
    with path.open('w',newline='',encoding='utf8') as out:
        if format=='json':
            out.write('[')
            if first is not None:
                out.write('\n'+json.dumps(first,ensure_ascii=False,default=str))
                for row in rows:out.write(',\n'+json.dumps(row,ensure_ascii=False,default=str))
            out.write('\n]\n')
        elif format=='csv':
            writer=csv.DictWriter(out,fieldnames=list(first) if first is not None else ['id'])
            writer.writeheader()
            if first is not None:writer.writerow(first)
            writer.writerows(rows)
        elif first is None:out.write('(no matches)\n')
        else:
            header=render([first]).split('\n')[0];fields=header.split('\t')
            out.write(header+'\n')
            out.write('\t'.join(str(first.get(k,'')).replace('\n',' ') for k in fields)+'\n')
            for row in rows:out.write('\t'.join(str(row.get(k,'')).replace('\n',' ') for k in fields)+'\n')
