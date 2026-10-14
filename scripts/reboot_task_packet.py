#!/usr/bin/env python3
"""Read the reboot DAG and emit bounded worker packets; never execute its commands."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'docs/observational_reboot_20261014/REBOOT_PLAN.json'
DONE={'completed_scoped','completed'}


def validate(plan):
    tasks=plan['tasks']; external=plan.get('external_dependencies',{})
    ids=[t['id'] for t in tasks]
    if len(set(ids))!=len(ids) or set(ids)&set(external):
        raise ValueError('duplicate or overlapping task identity')
    prs=[t['pr_id'] for t in tasks]
    if len(set(prs))!=len(prs):
        raise ValueError('duplicate PR identity')
    by_id={t['id']:t for t in tasks}
    visiting=set();visited=set()
    def visit(i):
        if i in external:return
        if i not in by_id:raise ValueError('missing dependency '+i)
        if i in visiting:raise ValueError('dependency cycle at '+i)
        if i in visited:return
        visiting.add(i)
        t=by_id[i]
        if t['status'] not in DONE|{'pending','in_progress','blocked_input','needs_native'}:
            raise ValueError('unknown status '+t['status'])
        for key in ('files','work','acceptance','next_action','input_obligations','worker'):
            if key not in t:raise ValueError('missing field '+key)
        if t['status'] in DONE and any((external.get(d) or by_id.get(d) or {}).get('status') not in DONE for d in t['depends']):
            raise ValueError('completed task has incomplete prerequisite '+i)
        for d in t['depends']:visit(d)
        visiting.remove(i);visited.add(i)
    for i in ids:visit(i)
    return by_id


def ready_tasks(plan):
    by_id=validate(plan);states={k:v['status'] for k,v in by_id.items()}
    states.update({k:v['status'] for k,v in plan.get('external_dependencies',{}).items()})
    return [t for t in plan['tasks'] if t['status']=='pending' and all(states[d] in DONE for d in t['depends'])]


def packet(plan,task_id):
    tasks=validate(plan)
    if task_id not in tasks:raise ValueError('unknown task '+task_id)
    t=tasks[task_id]
    result={'task':t,'dependency_status':{d:(tasks.get(d) or plan['external_dependencies'][d])['status'] for d in t['depends']},
      'read_first':['AGENTS.md','docs/harness/CURRENT_CODEX_RUNTIME.md','docs/observational_reboot_20261014/AUTONOMOUS_GOALS_KO.md'],
      'authority':'REBOOT_PLAN status is an execution queue, not scientific admission. Read exact evidence before promotion.',
      'next_transition':'Return patch/results and one precise next action; coordinator records state and immediately dispatches the next ready task.',
      'author_observation':'Record requested settings and actually observed runtime separately; UNKNOWN remains UNKNOWN.'}
    text=json.dumps(result,indent=2,ensure_ascii=False)
    if len(text)>12000:raise ValueError('worker packet exceeds 12000-char core bound; narrow this task')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,default=DEFAULT)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ready',action='store_true')
    group.add_argument('--task')
    group.add_argument('--validate',action='store_true')
    args=parser.parse_args()
    plan=json.loads(args.plan.read_text())
    validate(plan)
    if args.task:result=packet(plan,args.task)
    elif args.ready:result={'ready_for_work':[{'id':t['id'],'pr':t['pr_id'],'title':t['title'],'lane':t['lane'],'next_action':t['next_action']} for t in ready_tasks(plan)],
      'meaning':'Dependency-ready to investigate/implement, not necessarily ready for an empirical run; inspect input obligations.',
      'coverage_queue':'docs/observational_reboot_20261014/GOALS.json',
      'when_empty':'Reconcile completed work; inspect coverage goals for next feasible analysis or acquisition. Do not call all science complete while physical inputs remain blocked.'}
    else:result={'status':'VALID_DAG','tasks':len(plan['tasks']),'ready':[t['id'] for t in ready_tasks(plan)]}
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
