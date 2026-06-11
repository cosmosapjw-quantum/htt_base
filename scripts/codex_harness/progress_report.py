#!/usr/bin/env python3
import argparse, yaml, json
from pathlib import Path
from collections import defaultdict, deque

def topo(prs):
    ids=[p['id'] for p in prs]; indeg={i:0 for i in ids}; adj=defaultdict(list)
    for p in prs:
        for d in p.get('depends',[]): adj[d].append(p['id']); indeg[p['id']]+=1
    q=deque([i for i in ids if indeg[i]==0]); out=[]
    while q:
        x=q.popleft(); out.append(x)
        for y in adj[x]:
            indeg[y]-=1
            if indeg[y]==0:q.append(y)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('backlog')
    ap.add_argument('status')
    ap.add_argument('--checkpoint-every', type=int, default=5)
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args()
    data=yaml.safe_load(Path(args.backlog).read_text())
    status_path=Path(args.status)
    if status_path.exists(): st=yaml.safe_load(status_path.read_text()) or {}
    else: st={}
    prs=data['prs']; ids=[p['id'] for p in prs]
    completed=set(st.get('completed',[]) or [])
    blocked=set(st.get('blocked',[]) or [])
    unblocked=[]
    for p in prs:
        if p['id'] in completed or p['id'] in blocked: continue
        if all(d in completed for d in p.get('depends',[])): unblocked.append(p['id'])
    pct=100*len(completed)/len(prs) if prs else 0.0
    next_checkpoint=((len(completed)//args.checkpoint_every)+1)*args.checkpoint_every
    out={'total':len(prs),'completed':len(completed),'blocked':sorted(blocked),'percent_complete':round(pct,2),'unblocked_next':unblocked[:10],'next_checkpoint_at':next_checkpoint,'checkpoint_due':len(completed)>0 and len(completed)%args.checkpoint_every==0}
    if args.json: print(json.dumps(out, indent=2))
    else:
        print(f"Completed {out['completed']}/{out['total']} = {out['percent_complete']}%")
        print("Unblocked next:", ", ".join(out['unblocked_next']) or "none")
        print("Checkpoint due:" , out['checkpoint_due'])
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
