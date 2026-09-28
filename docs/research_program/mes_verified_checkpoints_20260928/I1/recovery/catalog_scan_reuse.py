from pathlib import Path
import gzip,json,hashlib,collections,zipfile,io,csv,re,subprocess
ROOT=Path(__file__).resolve().parent
P=ROOT/'catalog'; E=P/'exports'
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def rows(name):
 with gzip.open(E/(name+'.jsonl.gz'),'rt') as f:
  for line in f:yield json.loads(line)
# Validate each portable artifact against its preserved manifest, then count/parse every compressed JSONL.
a=json.loads((P/'artifact_manifest.json').read_text()); checks=[]
for v in a['files']:
 b=(P/v['path']).read_bytes();checks.append({'path':v['path'],'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'matches':len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']})
counts={};schemas={};topicstats={}
for path in E.glob('*.jsonl.gz'):
 n=path.name[:-9];c=0;ks=set();kinds=collections.Counter();sources=collections.Counter();truncated=0
 for d in rows(n):
  c+=1;ks.update(d)
  if n.startswith('topic_'):kinds[d.get('kind')]+=1;sources[d.get('source_id')]+=1;truncated+=bool(d.get('summary_truncated'))
 counts[n]=c;schemas[n]=sorted(ks)
 if n.startswith('topic_'):topicstats[n]={'rows':c,'kind_counts':dict(kinds),'source_counts':dict(sources),'truncated_excerpt_count':truncated}
expected=json.loads((E/'verification.json').read_text())
countmatch={x['path']:counts[x['path'][:-9]]==x['rows'] for x in expected['exports']}
write(P/'REUSE_VALIDATION.json',{'artifact_checks':checks,'all_artifacts_match':all(c['matches'] for c in checks),'counts':counts,'count_matches_historical_receipt':countmatch,'schema_keys':schemas,'topic_stats':topicstats,'original_db_materialized':False,'original_db_deleted_this_turn':False,'science_revalidated':False})
# Full file-locator scan; matches are candidates, never new source reading claims.
patterns={
 'mes_tensor':r'(mes.*(tensor|rederiv|bound|theorem|response|jet|residual)|tensor.*mes|radiation_jet)',
 'local_global_identification':r'(local.global|identifi|anchored.response|physical.response|depth.response|feasible.fib|observer.*boost)',
 'optics_redshift':r'(reloptics|optical.mapping|geometrical.optics|ray.generator|sachs|kinematic.*redshift|cmb_kinematics)',
 'theory_candidate':r'(conjectur|theorem|proposition|research.program|theory)'}
pat={k:re.compile(v,re.I) for k,v in patterns.items()}
srcs={x['id']:x for x in rows('sources')}
loc=[];bytopic=collections.Counter()
for d in rows('files'):
 topics=[k for k,p in pat.items() if p.search(d['path'])]
 if not topics:continue
 d['topics']=topics;d['read_depth']='locator_metadata_only';d['catalog_status']='historical_snapshot_20260912';d['origin']=srcs[d['source_id']].get('origin');d['source_locator']=srcs[d['source_id']]['locator']
 try:d['content_sha256']=json.loads(d.get('details','{}')).get('content_sha256')
 except Exception:pass
 loc.append(d);bytopic.update(topics)
with gzip.open(P/'selected_file_locators.jsonl.gz','wt') as f:
 for d in loc:f.write(json.dumps(d,ensure_ascii=False)+'\n')
# Baseline source paths: pick precise code/theory consumers, retain all version locators separately.
candidates=[]
for d in loc:
 if d['source_id']=='htt_base' and d.get('role') in ['code','documentation'] and not d.get('container_id') and d['path'].startswith(('htt/','docs/','tests/')) and any(t!='theory_candidate' for t in d['topics']): candidates.append(d)
by_path={}
for d in candidates:by_path.setdefault(d['path'],[]).append(d)
write(P/'targeted_source_paths.json',[{'path':k,'topics':sorted(set(t for d in v for t in d['topics'])),'versions':[{'file_id':d['id'],'commit':d['observed_commit'],'blob':d['git_blob'],'sha256':d.get('content_sha256')} for d in v],'read_depth':'locator_metadata_only'} for k,v in sorted(by_path.items())])
# Excerpts retained for targeted hypotheses; each query is reproducible and keeps locators.
queries={
 'observer_global_separation':['local boost','global tilt'],
 'joint_response_identifiability':['response','identif'],
 'tensor_jet_mes':['tensor','derivative'],
 'optics_redshift_candidates':['optical','redshift']}
chosen={k:[] for k in queries}
for tn in ['topic_local_global','topic_MES_departure','topic_CMB_product_law']:
 for d in rows(tn):
  if not d.get('baseline_membership') or d.get('source_id')!='htt_base':continue
  hay=' '.join(str(d.get(k,'')) for k in ['path','name','summary']).lower()
  for key,terms in queries.items():
   if all(t in hay for t in terms):
    if len(chosen[key])<80:chosen[key].append(d)
write(P/'targeted_topic_excerpts.json',{'query_terms_all_required':queries,'per_query_cap':80,'results':chosen,'read_depth':'preserved_excerpt_not_original_source'})
replays=[]
for args in [['mes','--topic','MES_departure','--limit','2'],['local boost','--topic','local_global','--limit','2'],['response','--limit','2']]:
 r=subprocess.run(['python','-B',str(P/'query_exports.py'),*args],capture_output=True,text=True)
 replays.append({'args':args,'exit_code':r.returncode,'rows':[json.loads(x) for x in r.stdout.splitlines()],'stderr':r.stderr})
write(P/'QUERY_REPLAY.json',replays)
write(P/'SELECTION_SUMMARY.json',{'file_locator_rows_scanned':counts['files'],'matched_file_versions':len(loc),'matched_topic_counts_overlapping':dict(bytopic),'targeted_unique_paths':len(by_path),'targeted_versions':len(candidates),'newer_than_catalog_limitation':'R9/R10 reloptics/CMB mapping dated after 2026-09-12 must be recovered from research archive or current remote; observed_commit is not latest-version assertion.'})
print(json.dumps({'counts':counts,'all_artifacts_match':all(c['matches'] for c in checks),'countmatch':all(countmatch.values()),'selected':len(loc),'targeted_paths':len(by_path)},ensure_ascii=False))
