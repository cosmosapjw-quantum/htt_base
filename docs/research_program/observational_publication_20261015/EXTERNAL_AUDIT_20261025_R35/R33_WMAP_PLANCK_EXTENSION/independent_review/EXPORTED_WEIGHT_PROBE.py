#!/usr/bin/env python3
"""Read-only exact-binary64 candidate residual probe; no integration, SVD, or weight solve."""
from pathlib import Path
from decimal import Decimal, localcontext
import hashlib,json,time
start=time.monotonic()
root=Path('/mnt/extdrive/workdir/htt_open_data')
out=root/'r35_wmap_planck_fresh_astra_review'
p=root/'r33_cmb_wmap_planck_numeric/stable_complement_repair/attempt_1b0195cebb59f27a/RESULT.json'
c=root/'r35_cmb_checker_api_fix/RESULT.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(p)=='c29360ba14d7bcf72d85be285ea61228c16148d35472c9dd4759e06c1eea0ee8'
assert sha(c)=='709f80e96f7b6ec343ba407ac9c7b43386bc121893e1a820c16bd2629399e1eb'
prod=json.loads(p.read_text());check=json.loads(c.read_text())
D=Decimal.from_float
def evaluate(w,F):
 w=list(map(D,w));F=[list(map(D,row)) for row in F]
 wa=sum(w,Decimal(0));wf=[sum((w[i]*F[i][j] for i in range(len(w))),Decimal(0)) for j in range(9)]
 scales=[sum((row[j]**2 for row in F),Decimal(0)).sqrt() for j in range(9)]
 wn=[wf[j]/scales[j] for j in range(9)]
 norm=lambda v:sum((x*x for x in v),Decimal(0)).sqrt()
 return {'wTa_signed_residual':str(wa-1),'wTF_raw':list(map(str,wf)),
  'wTF_raw_norm2':str(norm(wf)),'wTF_normalized_norm2':str(norm(wn)),
  'all24_HA_column_residuals':[str(abs(wa-1))]*24,
  'all216_HB_column_residuals':[str(abs(wf[j])) for j in range(9) for k in range(24)],
  'passed':abs(wa-1)<=Decimal('1e-9') and norm(wn)<=Decimal('1e-9') and max(map(abs,wf))<=Decimal('1e-9')}
branches={}
with localcontext() as ctx:
 ctx.prec=120
 for key,b in prod['branches'].items():
  row={}
  for n in ('F12','F17'):
   assert b[n]['raw_matrix']==b[n+'_raw']
   assert b[n]['raw_matrix'][:7]==b['Planck_rows_exact_binary64']
   q=evaluate(b[n]['w'],b[n]['raw_matrix'])
   q['exported_wTa_residual']=b[n]['wTa_signed_residual']
   q['exported_raw_norm2']=b[n]['wTF_raw_norm2']
   q['exported_normalized_norm2']=b[n]['wTF_normalized_norm2']
   q['matrix_and_weight_sha256']=hashlib.sha256(json.dumps({'F':b[n]['raw_matrix'],'w':b[n]['w']},sort_keys=True,separators=(',',':')).encode()).hexdigest()
   row[n]=q
  q=evaluate(b['lifted_compressed_weight']['w17'],b['F17']['raw_matrix'])
  q['passed']=q['passed'] and Decimal(q['wTF_raw_norm2'])<=Decimal('1e-9')
  row['lifted_F12_to_F17']=q
  branches[key]=row
result={'method':'decimal120 arithmetic on exact float.as_integer_ratio-equivalent Decimal.from_float inputs; all24 factors use H=w^T tensor I24 and B=F tensor I24; no source integration, SVD, weight recomputation, or scientific-library import','source_sha256':sha(Path(__file__)),'producer_sha256':sha(p),'checker_sha256':sha(c),'branches':branches,'passed':all(v['passed'] for b in branches.values() for v in b.values()),'execution_seconds':time.monotonic()-start}
(out/'EXPORTED_WEIGHT_PROBE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'systems':24,'lifts':12,'max_unity_residual':str(max(abs(Decimal(q['wTa_signed_residual'])) for b in branches.values() for q in b.values())),'max_raw_nuisance_norm':str(max(Decimal(q['wTF_raw_norm2']) for b in branches.values() for q in b.values())),'max_normalized_nuisance_norm':str(max(Decimal(q['wTF_normalized_norm2']) for b in branches.values() for q in b.values())),'probe_sha256':sha(out/'EXPORTED_WEIGHT_PROBE.json'),'execution_seconds':result['execution_seconds']},indent=2))
