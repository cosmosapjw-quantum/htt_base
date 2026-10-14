#!/usr/bin/env python3
"""Bounded continuation packets, not an unattended scheduler."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'docs/solver_free_research_20261014/PLAN.json'

def validate(plan):
    tasks=plan['tasks'];byid={t['id']:t for t in tasks}
    if len(byid)!=len(tasks):raise ValueError('duplicate task IDs')
    visiting=set();done=set()
    def visit(i):
        if i in visiting:raise ValueError('dependency cycle')
        if i in done:return
        visiting.add(i)
        for d in byid[i]['depends']:
            if d not in byid:raise ValueError('missing dependency '+d)
            visit(d)
        visiting.remove(i);done.add(i)
    for t in tasks:
        visit(t['id'])
        for k in ('goal','status','inputs','outputs','acceptance','next_action','model','effort'):
            if k not in t:raise ValueError('missing field '+k)
        if t.get('build_solver') or t.get('integrate_ode'):raise ValueError('excluded execution')
    return byid

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--validate',action='store_true');g.add_argument('--ready',action='store_true');g.add_argument('--task')
    a=p.parse_args();plan=json.loads(PLAN.read_text());byid=validate(plan)
    if a.validate:result={'valid':True,'tasks':len(byid),'scientific_admission':'HOLD_UNCHANGED'}
    elif a.ready:
        result={'ready':[t['id'] for t in byid.values() if t['status']=='ready' and all(byid[d]['status']=='completed_scoped' for d in t['depends'])],
                'blocked':[{'id':t['id'],'missing':t.get('missing_inputs',[])} for t in byid.values() if t['status']=='blocked_input'],
                'rule':'Agent executes the returned task, checkpoints results and chooses the next ready task. No automatic process is launched.'}
    else:result=byid[a.task]
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
