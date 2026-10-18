"""Print a bounded task packet against the live scientific DAG; never mark done."""
import argparse
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROGRAM=ROOT/'docs/research_program/observational_publication_20261015'

def packet(dag,plan,node=None,task=None):
    nodes={n['id']:n for n in dag['nodes']}
    goals={n['id']:n for n in plan['all_original_nodes']}
    if set(nodes)!=set(goals):raise ValueError('Scientific node inventory changed; reconcile plan first')
    for key,n in nodes.items():
        if n['acceptance']!=goals[key]['acceptance'] or n['depends_on']!=goals[key]['depends_on']:
            raise ValueError('Scientific acceptance/dependencies changed: '+key)
    tasks={t['id']:t for t in plan['tasks']}
    if task:return tasks[task]
    if node:
        visited=set()
        def walk(key):
            if key in visited:return
            visited.add(key)
            for parent in nodes[key]['depends_on']:walk(parent)
        walk(node)
        routes=sorted({r for key in visited for r in goals[key]['input_routes']})
        return {'live_node':nodes[node],'acquisition_routes':[tasks[r] for r in routes],
                'data_manifest':str(PROGRAM/'OPEN_INPUTS_20261018/ACQUISITION_MANIFEST.json')}
    done={key for key,n in nodes.items() if n['state']=='completed_scoped'}
    ready=[key for key,n in nodes.items() if key not in done and not n['external_missing'] and set(n['depends_on'])<=done]
    return {'scientific_completed':len(done),'scientific_total':len(nodes),'scientific_ready':ready,
            'direct_external':[key for key,n in nodes.items() if key not in done and n['external_missing']],
            'acquisition_entrypoints':[{k:t[k] for k in ('id','goal','status')} for t in plan['tasks'] if not t['depends_on']],
            'notice':'Acquisition status is an intake plan; inspect local receipts. Zero scientific ready does not end available data/theory work.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dag',type=Path,default=PROGRAM/'PUBLICATION_DAG.json');p.add_argument('--plan',type=Path,default=PROGRAM/'OPEN_INPUTS_20261018/CONTINUATION_TASKS.json');g=p.add_mutually_exclusive_group();g.add_argument('--node');g.add_argument('--task');a=p.parse_args()
    print(json.dumps(packet(json.loads(a.dag.read_text()),json.loads(a.plan.read_text()),a.node,a.task),ensure_ascii=False,indent=2))
