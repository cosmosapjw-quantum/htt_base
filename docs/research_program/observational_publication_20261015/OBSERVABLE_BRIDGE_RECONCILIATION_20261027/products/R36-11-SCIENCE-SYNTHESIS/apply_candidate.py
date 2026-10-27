#!/usr/bin/env python3
"""Apply only the sealed bounded P4 file overlay after independent review.
Every destination must match either its preimage or expected final hash before any write.
An already-applied overlay is a no-op. No science regeneration or Git mutation.
"""
import pathlib,json,hashlib,shutil,argparse
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def apply(target):
 plan=json.loads((H/'APPLICATION_PLAN.json').read_text())
 for rel,v in plan['files'].items():
  assert sha(H/'candidate/R32-06-P4-DESIGN'/rel)==v['final_sha256'],('candidate drift',rel)
  assert sha(target/rel) in [v['preimage_sha256'],v['final_sha256']],('destination drift',rel)
 changed=[]
 for rel,v in plan['files'].items():
  if sha(target/rel)==v['final_sha256']:continue
  (target/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(H/'candidate/R32-06-P4-DESIGN'/rel,target/rel);assert sha(target/rel)==v['final_sha256'];changed.append(rel)
 return changed
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--apply-reviewed-candidate',action='store_true');p.add_argument('--test-target',type=pathlib.Path);a=p.parse_args();assert a.apply_reviewed_candidate
 plan=json.loads((H/'APPLICATION_PLAN.json').read_text());target=a.test_target or pathlib.Path(plan['destination'])
 if a.test_target:assert target.resolve().is_relative_to(H.resolve())
 print(json.dumps({'target':str(target),'changed':apply(target)},indent=2))
