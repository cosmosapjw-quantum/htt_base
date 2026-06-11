#!/usr/bin/env python3
import sys, yaml
from collections import defaultdict, deque
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print("usage: validate_pr_dag.py <pr_backlog.yaml>", file=sys.stderr)
        return 2
    data = yaml.safe_load(Path(sys.argv[1]).read_text())
    prs = data.get('prs', [])
    ids = [p['id'] for p in prs]
    if len(ids) != len(set(ids)):
        dup = sorted({x for x in ids if ids.count(x)>1})
        raise SystemExit(f"duplicate PR ids: {dup}")
    idset=set(ids)
    missing=sorted({d for p in prs for d in p.get('depends', []) if d not in idset})
    if missing:
        raise SystemExit(f"missing dependency ids: {missing}")
    indeg={i:0 for i in ids}; adj=defaultdict(list)
    for p in prs:
        for d in p.get('depends', []):
            adj[d].append(p['id']); indeg[p['id']]+=1
    q=deque([i for i in ids if indeg[i]==0]); order=[]
    while q:
        x=q.popleft(); order.append(x)
        for y in adj[x]:
            indeg[y]-=1
            if indeg[y]==0:q.append(y)
    if len(order)!=len(ids):
        cycle=[i for i,v in indeg.items() if v>0]
        raise SystemExit(f"cycle detected involving: {cycle}")
    print(f"OK: {len(ids)} PRs, DAG valid")
    print("topological_order=" + ",".join(order))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
