"""Read-only fixed-identity helper checks. No production entrypoint or Git calls."""
from pathlib import Path
from types import SimpleNamespace
import copy, hashlib, importlib.util, json, tempfile

O=Path(__file__).resolve().parent
P=O.parent/'r29_controller_publication'
W=O.parent/'r29_protocol_baseline_repair'
spec=importlib.util.spec_from_file_location('r29_baseline_readonly',P/'protocol_baseline_v2.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
m=SimpleNamespace(O=P,B=P.parent,R=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base'),
                  PARENT='71b272db893a92ec336c28164bc7efccf7c340b2',
                  LOCAL='d93605e66adfececa89b90681124b232a5f90220',
                  URL='https://github.com/cosmosapjw-quantum/htt_base.git',
                  REF='refs/heads/research/htt-adaptive-methods-20261023')
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
groups=[]
with tempfile.TemporaryDirectory(prefix='v2-review-fixture-',dir=O) as temp:
    T=Path(temp)
    def write(name,value):
        p=T/name;p.write_text(json.dumps(value,sort_keys=True)+'\n')
        return {'path':str(p),'sha256':sha(p)}
    # Recorded snapshots are fixture input here, never a live root approval.
    prior=json.loads((P/'CANONICAL_METADATA_AFTER_TREE.json').read_bytes())
    live=json.loads((O/'REVIEW_METADATA_BEFORE.json').read_bytes())
    a=json.loads((W/'COMMIT_INPUT_V2.example.json').read_bytes())
    rec=json.loads((W/'COMMIT_RECONCILIATION.example.json').read_bytes())
    a['execution_baseline']=write('SYNTHETIC_BASELINE.json',live)
    rec['execution_baseline']=a['execution_baseline']
    rec['status']='ROOT_RECONCILED_EXACT_TRANSITION'
    rec['metadata_changes']=[]
    for group in sorted(prior):
        for path in sorted(set(prior[group])|set(live[group])):
            old,new=prior[group].get(path),live[group].get(path)
            if old!=new:
                rec['metadata_changes'].append({'group':group,'path':path,'before':old,'after':new,
                    'classification':'Recorded independent R29 fieldwise classification used only in this pure fixture'})
    def bind():a['reconciliation']=write('SYNTHETIC_RECONCILIATION.json',rec)
    bind()
    assert b.validate_action(a,'commit',live,m)==live
    groups.append('full validate_action commit identity path accepts exact fixture seals and complete snapshot')
    def reject(candidate,current=live):
        try:b.validate_action(candidate,'commit',current,m)
        except (AssertionError,KeyError,ValueError):return
        raise AssertionError('unexpected acceptance')
    for field,value in [('tree','0'*40),('parent','0'*40)]:
        bad=copy.deepcopy(a);bad[field]=value;reject(bad)
    bad=copy.deepcopy(a);bad['prior_anchor']=write('SYNTHETIC_WRONG_PRIOR_PATH.json',prior);reject(bad)
    groups.append('wrong frozen tree, sole parent and substitute prior path reject')
    changed=copy.deepcopy(live);changed['non_object_metadata']['config']['sha256']='0'*64
    reject(a,changed)
    for path in [str(m.R/'scripts/codex_harness/research_controller.py'),str(P/'protocol_baseline_v2.py'),str(P/'prepare_publication.py')]:
        bad=copy.deepcopy(a);r=copy.deepcopy(rec)
        bad['review_seals']=[s for s in bad['review_seals'] if s['path']!=path]
        r['review_seals']=bad['review_seals'];bad['reconciliation']=write('SYNTHETIC_MISSING_REQUIRED.json',r)
        reject(bad)
    groups.append('live config drift and missing actual source/helper/original protocol seal reject')
    bad=copy.deepcopy(a);r=copy.deepcopy(rec);r['metadata_changes'].reverse()
    bad['reconciliation']=write('SYNTHETIC_REORDERED_DELTA.json',r);reject(bad)
    bad=copy.deepcopy(a);r=copy.deepcopy(rec);r['context']['remote_ref']='refs/heads/unrelated'
    bad['reconciliation']=write('SYNTHETIC_WRONG_REMOTE.json',r);reject(bad)
    groups.append('delta order and fixed remote context reject')
    # Confirm all production inputs stay sealed after all reads.
    report=json.loads((W/'IMPLEMENTATION_RETURN.json').read_bytes())
    for row in report['scripts']+report['unchanged_frozen_inputs']+report['live_source_state_pointer_seals']:
        assert sha(row['path'])==row['sha256'],row['path']
    groups.append('all v2 scripts, original frozen inputs, source, STATE and pointer remain sealed')
result={'status':'PASS','groups':groups,'groups_passed':len(groups),'production_main_imported':False,
        'production_state_or_git_writes':False,'actual_commit_or_push':False,
        'root_authorization_files_written':False,'scope':'pure recorded-metadata fixtures only'}
(O/'V2_INDEPENDENT_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
