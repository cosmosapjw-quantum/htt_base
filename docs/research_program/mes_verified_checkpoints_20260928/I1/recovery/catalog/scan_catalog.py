"""Read-only inventory and discovery export; no research source is executed."""
import collections, csv, gzip, hashlib, json, os, platform, shutil, sqlite3, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'exports'; OUT.mkdir(exist_ok=True)
START=time.monotonic()
COMMIT='57ecfe2176bf8be28327edf500a4ca5136c6b15b'
DB=ROOT/'catalog.sqlite'
CON=sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True)
CON.row_factory=sqlite3.Row
CON.execute('PRAGMA query_only=ON')
CON.execute('PRAGMA cache_size=-131072')
CON.execute('PRAGMA mmap_size=0')
CON.execute('PRAGMA temp_store=FILE')
COUNTS={}

def log(stage,**kw):
    line=json.dumps(dict(stage=stage,elapsed_s=round(time.monotonic()-START,3),**kw),ensure_ascii=False)
    print(line,flush=True)
    with (ROOT/'scan.jsonl').open('a') as f:f.write(line+'\n')

def dump(name,rows):
    path=OUT/(name+'.jsonl.gz'); n=0
    prior=[]
    if (ROOT/'scan.jsonl').exists():
        prior=[json.loads(x) for x in (ROOT/'scan.jsonl').read_text().splitlines()]
    successful=[x for x in prior if x.get('stage')=='export' and x.get('name')==name]
    if successful and path.exists() and path.stat().st_size==successful[-1]['bytes']:
        # Reuse complete immutable input-table exports, never topic generators with side effects.
        if not name.startswith('topic_') and name not in ('selected_file_edges','acquisition_candidates'):
            COUNTS[name]={k:successful[-1][k] for k in ('rows','bytes')}
            log('export_reused',name=name,**COUNTS[name]);return
    with gzip.open(path,'wt',encoding='utf-8',compresslevel=5) as f:
        for row in rows:
            f.write(json.dumps(dict(row),ensure_ascii=False,separators=(',',':'))+'\n');n+=1
            if n%100000==0 and shutil.disk_usage(ROOT).free<6*2**30:raise RuntimeError('space floor')
    COUNTS[name]=dict(rows=n,bytes=path.stat().st_size)
    log('export',name=name,**COUNTS[name])

def main():
    log('start',commit=COMMIT,python=platform.python_version(),sqlite=sqlite3.sqlite_version)
    prior=[json.loads(x) for x in (ROOT/'scan.jsonl').read_text().splitlines()]
    qc=['ok'] if any(x.get('stage')=='quick_check' and x.get('result')=='ok' for x in prior) else [r[0] for r in CON.execute('PRAGMA quick_check')]
    if qc!=['ok']:raise RuntimeError('SQLite quick_check '+repr(qc))
    log('quick_check',result='ok')
    tables=['meta','sources','refs','commits','commit_aliases','snapshots','members','trees','files','filesystem','gaps']
    table_counts={t:CON.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables+['contents','records','edges','search']}
    expected=json.loads((ROOT/'support/summary.json').read_text())
    comparison={t:table_counts[t]==expected[t] for t in table_counts if isinstance(expected.get(t),int)}
    if not all(comparison.values()):raise RuntimeError('published count mismatch '+repr(comparison))
    if table_counts['records']!=table_counts['search']:raise RuntimeError('FTS cardinality mismatch')
    groupings={key:dict(CON.execute(sql).fetchall()) for key,sql in {
        'records_by_kind':'SELECT kind,count(*) FROM records GROUP BY kind',
        'files_by_status':'SELECT processing_status,count(*) FROM files GROUP BY processing_status',
        'gaps_by_status':'SELECT status,count(*) FROM gaps GROUP BY status',
        'records_by_status':'SELECT status,count(*) FROM records GROUP BY status',
        'edge_relations':'SELECT relation,count(*) FROM edges GROUP BY relation'
    }.items()}
    meta={r['key']:json.loads(r['value']) for r in CON.execute('SELECT * FROM meta')}
    baseline=meta['baseline']
    roots={r[0] for r in CON.execute('SELECT file_id FROM members WHERE source_id=? AND commit_sha=?',(baseline['source_id'],baseline['commit']))}
    sources={r['id']:dict(r) for r in CON.execute('SELECT * FROM sources')}
    timestamps={(r['source_id'],r['sha']):r['timestamp'] or 0 for r in CON.execute('SELECT source_id,sha,timestamp FROM commits')}
    log('inventory',counts=table_counts,baseline=baseline,baseline_roots=len(roots))
    for t in tables:dump(t,CON.execute('SELECT * FROM '+t))
    (OUT/'schema.sql').write_text('\n\n'.join(r[0]+';' for r in CON.execute('SELECT sql FROM sqlite_master WHERE sql IS NOT NULL')),encoding='utf-8')
    topics={
        'CF4':'CF4 OR Cosmicflows OR CORAS OR Carrick OR Lilow',
        'CMB_product_law':'PR3 OR FFP10 OR SMICA OR Commander OR NILC OR SEVEM OR WMAP',
        'full_QO_morphology':'"full Q" OR "full QO" OR "full tensor" OR "multipole vector" OR morphology OR "orbit distance"',
        'MES_departure':'"tensorized MES" OR MES OR departure OR "filling fraction" OR "radiation jet" OR "closure frontier"',
        'local_global':'"local boost" OR "global tilt" OR "shared cause" OR "common cause" OR "response rank" OR identifiability',
        'JWST_calibration':'JWST OR JAGB OR CCHP OR SH0ES OR TRGB',
        'DESI_Union3':'DESI OR qiso OR Union3 OR UNITY',
        'Teff_error':'Teff OR "closure error" OR "model bias" OR "observable error"'
    }
    topics_summary={}; ranked={}; file_topics=collections.defaultdict(set)
    fields='v.*,substr(v.summary,1,4000) AS summary_excerpt,length(v.summary)>4000 AS summary_truncated'
    kinds=('analysis','proposition','plan','feature','evidence','port','update','document')
    priorities={'analysis':8,'proposition':7,'evidence':6,'plan':5,'feature':4,'update':4,'port':3,'document':1}
    for topic,query in topics.items():
        matched=collections.Counter(); files={}; totals=collections.Counter()
        sql='SELECT '+fields+' FROM search JOIN catalog v ON v.id=search.record_id WHERE search MATCH ? AND v.kind IN ('+','.join('?'*len(kinds))+')'
        def rows():
            for row in CON.execute(sql,(query,*kinds)):
                d=dict(row);d['summary']=d.pop('summary_excerpt')
                in_base=d['root_file_id'] in roots
                d['baseline_membership']=in_base; d['topic']=topic
                totals['records']+=1;totals['baseline_records' if in_base else 'historical_or_external_records']+=1
                matched[d['kind']]+=1
                fid=d['file_id'];file_topics[fid].add(topic)
                score=priorities[d['kind']]+(20 if in_base else 0)
                if any(x in d['path'].lower() for x in ('theory','report','design','likelihood','analysis','validation','readme','handoff','response')):score+=3
                solver=any(x in d['path'].lower() for x in ('restricted_history','r3_model','boltzmann','recombination','reionization'))
                if solver:score-=12
                item=files.setdefault(fid,dict(file_id=fid,path=d['path'],source_id=d['source_id'],observed_commit=d['observed_commit'],baseline_membership=in_base,score=score,example_record_id=d['id'],example_name=d['name'],record_count=0,external_solver_pointer=solver,timestamp=timestamps.get((d['source_id'],d['observed_commit']),0)))
                item['record_count']+=1
                if score>item['score']:item.update(score=score,example_record_id=d['id'],example_name=d['name'])
                yield d
        dump('topic_'+topic,rows())
        selected=[]
        for in_base,limit in [(True,16),(False,12)]:
            seen=set()
            for item in sorted(files.values(),key=lambda x:(-x['score'],-x['timestamp'],-x['record_count'],x['path'])):
                if item['baseline_membership']!=in_base:continue
                src=sources.get(item['source_id'],{})
                key=(src.get('origin') or item['source_id'],item['path'])
                if key in seen:continue
                seen.add(key);selected.append(item)
                if len(seen)>=limit:break
        ranked[topic]=selected
        topics_summary[topic]=dict(query=query,**totals,files=len(files),records_by_kind=dict(matched),selected_files=len(selected))
        log('topic',topic=topic,**topics_summary[topic])
    selected={item['file_id']:dict(item,topics=[]) for items in ranked.values() for item in items}
    for topic,items in ranked.items():
        for item in items:selected[item['file_id']]['topics'].append(topic)
    dep_targets=set(); resolution_counts=collections.Counter()
    def edge_rows():
        for fid in selected:
            for row in CON.execute('SELECT e.* FROM records r JOIN edges e ON e.from_id=r.id WHERE r.file_id=?',(fid,)):
                d=dict(row);d['from_file_id']=fid;resolution_counts[d['resolution']]+=1
                if d['target_id']:dep_targets.add(d['target_id'])
                yield d
    dump('selected_file_edges',edge_rows())
    dependency_files=set()
    for tid in dep_targets:
        r=CON.execute('SELECT id FROM files WHERE id=?',(tid,)).fetchone()
        if r:dependency_files.add(r[0])
        else:
            r=CON.execute('SELECT file_id FROM records WHERE id=?',(tid,)).fetchone()
            if r:dependency_files.add(r[0])
    need=set(selected)|dependency_files
    for fid in list(need):
        row=CON.execute('SELECT container_id,root_file_id FROM files WHERE id=?',(fid,)).fetchone()
        for parent in row or []:
            while parent and parent not in need:
                need.add(parent)
                p=CON.execute('SELECT container_id FROM files WHERE id=?',(parent,)).fetchone()
                parent=p[0] if p else None
    acquisition=[]
    for fid in sorted(need):
        row=CON.execute('SELECT * FROM files WHERE id=?',(fid,)).fetchone()
        if not row:continue
        d=dict(row);details=json.loads(d['details']);src=sources.get(d['source_id'],{})
        d.update(origin=src.get('origin'),source_locator=src.get('locator'),source_kind=src.get('kind'),content_sha256=details.get('content_sha256'),reason='topic_candidate' if fid in selected else 'direct_dependency_or_archive_parent',topics=selected.get(fid,{}).get('topics',[]),retrieval_status='NOT_ACQUIRED',remote_availability='NOT_CHECKED',scientific_validation='NOT_PERFORMED')
        acquisition.append(d)
    dump('acquisition_candidates',acquisition)
    fields=['id','source_id','origin','path','observed_commit','git_blob','content_sha256','bytes','processing_status','reason','topics','retrieval_status']
    with (OUT/'acquisition_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(acquisition)
    summary=dict(commit=COMMIT,baseline=baseline,quick_check=qc,table_counts=table_counts,published_counts_match=comparison,groupings=groupings,topics=topics_summary,ranked_candidates=ranked,selected_topic_files=len(selected),direct_dependency_files=len(dependency_files),acquisition_files=len(acquisition),selected_edge_resolutions=dict(resolution_counts),exports=COUNTS,claim_scope='Static catalog read-only inventory and retrieval candidates; original source, scientific calculations and proofs NOT RECHECKED; no completeness guarantee for future dependencies',software=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version))
    (OUT/'scan_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    log('complete',selected_topic_files=len(selected),acquisition_files=len(acquisition),export_bytes=sum(x['bytes'] for x in COUNTS.values()))

if __name__=='__main__':main()
