#!/usr/bin/env python3
"""Selected-file overlay verification. All controller mutations are disposable fixtures."""
from pathlib import Path
import argparse,copy,hashlib,json,shutil,subprocess,sys,tempfile,traceback
import yaml

SOURCE_DIR=Path(__file__).resolve().parent
AUDIT_ROOT=next((p for p in SOURCE_DIR.parents if (p/'baseline').is_dir() and (p/'patch').is_dir()),None)
parser=argparse.ArgumentParser(description=__doc__+' Requires the selected baseline snapshot and candidate patch; does not access live state.')
parser.add_argument('--baseline',type=Path,default=AUDIT_ROOT/'baseline' if AUDIT_ROOT else None)
parser.add_argument('--patch',type=Path,default=AUDIT_ROOT/'patch' if AUDIT_ROOT else None)
parser.add_argument('--work',type=Path,help='Disposable output folder outside both input trees')
args=parser.parse_args()
if args.baseline is None or args.patch is None:parser.error('--baseline and --patch are required outside the original audit workspace')
BASE=args.baseline.resolve();PATCH=args.patch.resolve()
HERE=(args.work or (AUDIT_ROOT/'lanes/integration_tests' if AUDIT_ROOT else Path(tempfile.mkdtemp(prefix='htt_r36_verification_')))).resolve()
if any(HERE==p or HERE.is_relative_to(p) or p.is_relative_to(HERE) for p in (BASE,PATCH)):
    parser.error('--work must be disjoint from both input trees')
HERE.mkdir(parents=True,exist_ok=True);OVER=HERE/'overlay'
REL=Path('docs/research_program/observational_publication_20261015')
NEW=REL/'OBSERVABLE_BRIDGE_RECONCILIATION_20261027'
OLD=REL/'PUBLICATION_ACCELERATION_20261025'
RESULTS=[]

def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def require(cond,msg):
    if not cond: raise AssertionError(msg)
def test(name,fn):
    try:
        detail=fn();RESULTS.append({'name':name,'status':'PASS','detail':detail})
    except Exception as exc:
        RESULTS.append({'name':name,'status':'FAIL','error':str(exc),'traceback':traceback.format_exc()})
def command(name,args):
    proc=subprocess.run([sys.executable,*map(str,args)],cwd=OVER,capture_output=True,text=True)
    (HERE/(name+'.stdout')).write_text(proc.stdout)
    (HERE/(name+'.stderr')).write_text(proc.stderr)
    require(proc.returncode==0,f'exit {proc.returncode}: {proc.stderr[:2000]}')
    return {'exit_code':proc.returncode,'stdout':proc.stdout[:1500]}

if OVER.exists(): shutil.rmtree(OVER)
shutil.copytree(BASE,OVER,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(PATCH,OVER,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
dependency=BASE/'scripts/codex_harness/pr167_intake_contract.py'
if not dependency.is_file():dependency=SOURCE_DIR/'deps/pr167_intake_contract.py'
shutil.copy2(dependency,OVER/'scripts/codex_harness/pr167_intake_contract.py')
sys.path.insert(0,str(OVER/'scripts/codex_harness'))
import research_controller as rc
import publication_frontier_preflight as pf

backrel=Path('docs/codex_handoff/pr_backlog.yaml')
statusrel=Path('docs/codex_handoff/pr_status.yaml')
oldback=yaml.safe_load((BASE/backrel).read_text());newback=yaml.safe_load((OVER/backrel).read_text())
oldstatus=yaml.safe_load((BASE/statusrel).read_text());newstatus=yaml.safe_load((OVER/statusrel).read_text())
oldscience=load(BASE/REL/'PUBLICATION_DAG.json');newscience=load(OVER/REL/'PUBLICATION_DAG.json')
f=load(OVER/NEW/'FRONTIER.json');ids=[t['id'] for t in f['tasks']]
newcards=[r for r in newback['prs'] if r['id'] not in {x['id'] for x in oldback['prs']}]


def preserve_science():
    for key in ('nodes','papers','planned_pr_cards','policy'):
        require(oldscience[key]==newscience[key],f'original scientific {key} changed')
    require(len(newscience['nodes'])==42 and len(newscience['papers'])==6,'original42/sixpapers size changed')
    require(newscience['canonical_pr_backlog']=='docs/codex_handoff/pr_backlog.yaml','canonical locator remains wrong')
    return {'nodes':42,'papers':6,'original_nodes_papers_policy_cards_unchanged':True}
test('original scientific contracts preserved',preserve_science)

def preserve_cards():
    require(newback['prs'][:len(oldback['prs'])]==oldback['prs'],'old cards changed or reordered')
    require(len(newcards)==12,'expected integration card plus11taskcards')
    for k,v in oldback['policy'].items():
        if k in ('topological_order','strict_extension_cards'):
            require(newback['policy'][k][:len(v)]==v,f'old {k} prefix changed')
        else: require(newback['policy'][k]==v,f'old policy {k} changed')
    for k,v in oldstatus.items():
        if k=='pending': require([x for x in newstatus[k] if x in v]==v,'old pending objects changed or reordered')
        else: require(newstatus[k]==v,f'old status {k} changed')
    require(set(r['id'] for r in newcards)<=set(newstatus['pending']),'newcards not pending')
    return {'old_cards':len(oldback['prs']),'new_cards':12,'all_existing_status_objects_preserved':True}
test('canonical cards and historical statuses preserved',preserve_cards)

def policy_registration():
    new_ids={c['id'] for c in newcards}
    require(new_ids<=set(newback['policy']['topological_order']),'missing topological policy registration')
    missing=new_ids-set(newback['policy']['strict_extension_cards'])
    require(not missing,'missing strict_extension_cards: '+str(sorted(missing)))
    return {'registered_new_cards':len(new_ids)}
test('both canonical extension registries updated',policy_registration)

def cardinality():
    roots=[t['id'] for t in f['tasks'] if t['requires']=={'all':[]}]
    require(len(ids)==11 and len(set(ids))==11,'frontier task count')
    require(len(roots)==9,'frontier root count')
    require(all(t['initial_state']=='ready' for t in f['tasks']),'imported completed task')
    require(all(t['promotes_original_acceptance'] is False for t in f['tasks']),'original acceptance promotion')
    for t in f['tasks']:
        card=next(c for c in newcards if c['id']=='PR-'+t['id'])
        require(card['product_requires']==t['requires'],'canonical product gate mismatch '+t['id'])
    return {'new_tasks':len(ids),'initial_roots':roots,'canonical_typed_gates_match':True}
test('11tasks9roots and canonical typed dependencies',cardinality)

test('actual canonical DAG validator',lambda:command('validate_pr_dag',['scripts/codex_harness/validate_pr_dag.py',backrel,'--status',statusrel,'--json']))
test('actual mirror validator',lambda:command('check_mirrors',['scripts/codex_harness/sync_pr_dag_mirrors.py','--check']))
test('actual parameterized production preflight CLI',lambda:command('preflight',['scripts/codex_harness/publication_frontier_preflight.py','--frontier',NEW/'FRONTIER.json','--manifest',NEW/'EVIDENCE_MANIFEST.json']))
test('production focused parameterization tests',lambda:command('preflight_regression',['tests/test_publication_frontier_preflight_parameterized.py']))

# No real state is read: these explicit sentinel histories check append preservation.
s=rc.initialize({'campaign_id':'DISPOSABLE_R36_INTEGRATION',
    'original_science_contract':{'nodes':copy.deepcopy(oldscience['nodes'])},
    'tasks':[{'id':'HISTORICAL-SENTINEL','goal':'preserved original contract','acceptance':'unchanged','input_identity':'fixture'}]},'disposable test only')
s['tasks']['HISTORICAL-SENTINEL'].update(state='held',attempt=9,history=[{'one_use':'consumed','outcome':'historical procedure failure'}],failures=[{'exhausted':True}],ultra_used=['USED-ONCE'],hold={'reason':'preserved scoped input hold'})
s['ultra_repairs']['USED-ONCE']={'task_id':'HISTORICAL-SENTINEL','actual_fixture':True}
s['events'].append({'type':'historical_sentinel'})
rc.append_frontier(s,load(OVER/OLD/'FRONTIER.json'),'disposable oldfrontier fixture')
for task in s['tasks'].values():
    if task['spec']['id'].startswith('R32-'):
        task.update(state='completed',qualified_products=[])
before=copy.deepcopy(s)

def preflight_existing():
    r=pf.check(OVER,s,frontier_path=NEW/'FRONTIER.json')
    require(r['status']=='APPEND_READY','append not ready against priorfrontier fixture')
    require(s==before,'preflight mutated existing state')
    require(len(r['candidate_root_tasks'])==9,'preflight root count')
    return r
test('preflight existing frontier and historical state unchanged',preflight_existing)

def append_actual_cli():
    statepath=HERE/'disposable_state.json';statepath.write_text(json.dumps(s,indent=2)+'\n')
    policy=HERE/'disposable_route_policy.json';policy.write_text(json.dumps({'schema_version':1,'routes':{}})+'\n')
    result=command('append_frontier',['scripts/codex_harness/research_controller.py','--state',statepath,'--policy',policy,'append-frontier','--frontier',NEW/'FRONTIER.json','--authorization','disposable integration fixture only'])
    after=load(statepath)
    for key,task in before['tasks'].items():require(after['tasks'][key]==task,'historicaltaskchanged '+key)
    for key,value in before.items():
        if key not in ('tasks','frontiers','events'):require(after[key]==value,'protectedstatechanged '+key)
    require(after['frontiers'][:len(before['frontiers'])]==before['frontiers'],'oldfrontierchanged')
    require(after['events'][:len(before['events'])]==before['events'],'eventsrewritten')
    require(set(rc.summary(after)['ready'])=={t['id'] for t in f['tasks'] if t['requires']=={'all':[]}},'actual readiness not9roots')
    s.clear();s.update(after)
    return {'cli_exit':result['exit_code'],'original_admission':rc.summary(s)['original_science'],'ready':rc.summary(s)['ready'],'history_budget_campaign_unchanged':True}
test('actual controller CLI append preserves history and yields9roots',append_actual_cli)

def append_once():
    original=copy.deepcopy(s)
    r=pf.check(OVER,s,frontier_path=NEW/'FRONTIER.json')
    require(r['status']=='ALREADY_APPENDED','identity not recognized')
    try:rc.append_frontier(s,f,'fixture repeat')
    except rc.ControllerError as exc:require('already appended' in str(exc),'wrong rejection')
    else:raise AssertionError('duplicate accepted')
    require(s==original,'duplicate attempt changed state')
    return {'exact_identity_recognized':True,'repeat_append_rejected_transactionally':True}
test('appendonce exactidentity protection',append_once)


def dependencies():
    q=copy.deepcopy(s)
    intake='R36-01-CF4-OPERATOR'; consumer='R36-02-CF4-CORRELATED';synth='R36-11-SCIENCE-SYNTHESIS'
    require(consumer not in rc.summary(q)['ready'] and synth not in rc.summary(q)['ready'],'consumer ready initially')
    q['tasks'][intake].update(state='completed',qualified_products=['gap_report'])
    require(consumer not in rc.summary(q)['ready'],'gap qualifiesCF4')
    q['tasks'][intake]['qualified_products']=['h03_exact_operator']
    require(consumer in rc.summary(q)['ready'],'exactoperatorfailsunblock')
    require(synth not in rc.summary(q)['ready'],'intakequalifiessynthesis')
    q['tasks']['R36-09-ATLAS-INTAKE'].update(state='completed',qualified_products=['external_atlas_intake'])
    require(synth not in rc.summary(q)['ready'],'atlasintakequalifiessynthesis')
    for leaf in f['tasks'][-1]['requires']['any']:
        q['tasks'][leaf['task_id']].update(state='completed',qualified_products=['gap_report'])
    require(synth not in rc.summary(q)['ready'],'allcompletedgapqualifiesynthesis')
    first=f['tasks'][-1]['requires']['any'][0]
    q['tasks'][first['task_id']]['qualified_products']=[first['product']]
    require(synth in rc.summary(q)['ready'],'oneexactresultfailsunblock')
    # Exactname is necessary but not enough until actual completed acceptance.
    q['tasks'][first['task_id']]['state']='held'
    require(synth not in rc.summary(q)['ready'],'heldproductqualifiessynthesis')
    return {'gap_reports_never_unblock':True,'intake_products_never_unblock_synthesis':True,'one_completed_exact_result_unblocks_synthesis':True,'held_exact_product_does_not_unblock':True}
test('product gates reject gapreports and accept first qualified scientific result',dependencies)


def frozen_input_manifest():
    manifest=load(OVER/NEW/'EVIDENCE_MANIFEST.json')
    rows=manifest['files'];seen=set()
    for row in rows:
        require('__pycache__' not in Path(row['path']).parts and Path(row['path']).suffix not in ('.pyc','.pyo'),'generated interpreter cache in frozen scientific manifest')
        require(row['path'] not in seen,'duplicate manifest path');seen.add(row['path'])
        require(sha(OVER/row['path'])==row['sha256'],'manifesthashchanged '+row['path'])
    changed=copy.deepcopy(f)
    changed['tasks'][0]['acceptance']+=' changed acceptance'
    path=OVER/NEW/'FRONTIER.json';original=path.read_bytes()
    path.write_text(json.dumps(changed))
    try:
        try:pf.check(OVER,s,frontier_path=NEW/'FRONTIER.json')
        except ValueError as exc:require('different frozen content' in str(exc),'wrong frozenidentity rejection')
        else:raise AssertionError('changed frontier admitted under sameID')
    finally:path.write_bytes(original)
    return {'verified_files':len(rows),'same_id_changed_frontier_rejected':True}
test('all sourcehashes and frozen frontier identity',frozen_input_manifest)


def acquisition_preservation():
    path=REL/'FRONTIER_20261020/ACQUISITION_MANIFEST.json'
    a=load(BASE/path);b=load(OVER/path)
    keys=[k for k in a if isinstance(a[k],list)]
    changed=[]
    for key in a:
        if a[key]!=b[key]:changed.append(key)
    for key in changed:
        if isinstance(a[key],list):require(b[key][:len(a[key])]==a[key],'old acquisitionentries changed '+key)
        else:require(key in ('updated_on','updated_at','notes'),'old acquisitionpolicy changed '+key)
    return {'modified_keys':changed,'old_list_entries_preserved':True}
test('acquisition manifest existing entries preserved',acquisition_preservation)

receipt={'schema':'htt.r36_disposable_integration_review/1','base_head':'a55036ad09c53a9215dee3282e425d37cfb95443',
    'selected_file_overlay_only':True,'full_repository_ci_claimed':False,'actual_controller_and_router_import':True,
    'live_state_read':False,'live_state_mutated':False,'dispatch_performed':False,'tests':RESULTS,
    'passed':sum(x['status']=='PASS' for x in RESULTS),'failed':sum(x['status']=='FAIL' for x in RESULTS),
    'frontier_sha256':sha(PATCH/NEW/'FRONTIER.json'),'backlog_sha256':sha(PATCH/backrel),'preflight_sha256':sha(PATCH/'scripts/codex_harness/publication_frontier_preflight.py')}
(HERE/'RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='tests'},indent=2))
for item in RESULTS:print(item['status'],item['name'],item.get('error',''))
sys.exit(0 if not receipt['failed'] else 1)
