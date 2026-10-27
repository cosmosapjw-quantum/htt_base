from pathlib import Path
import sys,json,hashlib,os
import numpy as np
import mpmath as mp
from scipy.linalg import norm
P=Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_repair_independent_review')
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
R=ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027'
C=R/'products/R36-04-OPTICAL-JOINT/repair_01'
sys.path.insert(0,str(C))
from optical_joint import *
import consume
mp.mp.dps=90
cases=json.loads((P/'INITIAL_COUNTEREXAMPLES.json').read_text())
falsereject=next(q for q in cases if q['name'].startswith('narrow_direct_1e-06_B5'))
falseaccept=next(q for q in json.loads((P/'EXTREME_RATIO_INTERVAL_COUNTEREXAMPLES.json').read_text()) if q['inputs']['e_d']==.1 and q['inputs']['d_max']==.0001 and q['inputs']['d_obs']==[0.,0,0] and q['physical_violation']>8e-13)
def matrix(a):return mp.matrix([[mp.mpf(float(z)) for z in row] for row in a])
def vec(a):return mp.matrix([mp.mpf(float(z)) for z in a])
s=np.asarray(falseaccept['inputs']['s']);k=KAPPA*lift_matrix(s)
km=matrix(k);o=vec(falseaccept['inputs']['o']);radius=mp.mpf(falseaccept['inputs']['d_max']);budget=mp.mpf(falseaccept['inputs']['budget'])
eigs=mp.eigsy(km.T*km,eigvals_only=True);kn=mp.sqrt(max(eigs));on=mp.norm(o)
lower=on-kn*radius
allowance=mp.mpf(64)*mp.mpf(float(np.finfo(float).eps))*max(on,kn*radius)
falseaccept['independent_high_precision_bound']={'arithmetic':'mpmath 90 digits on exact binary64 O,K,Dmax; triangle inequality ||O-Kd|| >= ||O||-||K||op Dmax for all feasible d','K':k.tolist(),'operator_norm':str(kn),'lower_bound':str(lower),'budget':str(budget),'lower_over_budget':str(lower/budget),'max_existing_signal_roundoff_allowance':str(allowance),'lower_minus_budget_minus_allowance':str(lower-budget-allowance),'bound_remains_strict':bool(lower>budget+allowance),'all_source_inputs_finite':True}
rargs=falsereject['inputs'];s=np.asarray(rargs['s']);k=KAPPA*lift_matrix(s);w=np.asarray(falsereject['witness']['d']);wm=vec(w);om=vec(rargs['o']);km=matrix(k)
falsereject['independent_high_precision_witness']={'arithmetic':'mpmath 90 digits on exact binary64 supplied O,K,d','residual_norm':str(mp.norm(om-km*wm)),'direct_distance':str(mp.norm(wm-vec(rargs['d_obs']))),'physical_norm':str(mp.norm(wm)),'budget':rargs['budget'],'residual_below_budget':bool(mp.norm(om-km*wm)<mp.mpf(rargs['budget']))}
# Rotation and common output-unit rescaling must preserve these mathematical facts.
rotations=[]
axis=np.array([1.,2.,3.]);axis/=norm(axis);theta=.73
cross=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
rot=np.eye(3)*np.cos(theta)+(1-np.cos(theta))*np.outer(axis,axis)+np.sin(theta)*cross
for name,case in [('false_reject',falsereject),('false_accept',falseaccept)]:
 args=case['inputs'];s=np.asarray(args['s']);o=np.asarray(args['o']);do=np.asarray(args['d_obs'])
 tensor=np.einsum('a,aijk->ijk',o,B3);tr=np.einsum('ia,jb,kc,abc->ijk',rot,rot,rot,tensor);orc=np.einsum('aijk,ijk->a',B3,tr)
 for factor in (1.,1e-150,1e100):
  for rotated in (False,True):
   ss=(rot@s@rot.T if rotated else s)*factor;oo=(orc if rotated else o)*factor;dd=rot@do if rotated else do
   row={'case':name,'factor':factor,'rotated':rotated}
   try:
    out=joint_test(oo,ss,dd,args['budget']*factor,args['e_d'],args['d_max']);row['compatible']=out['compatible'];row['profiled_d']=out['profiled_d'];row['residual_norm']=out['residual_norm'];row['certificate']=out['profile_certificate']
   except Exception as ex:row['exception']={'type':type(ex).__name__,'code':getattr(ex,'code',None),'message':str(ex)}
   rotations.append(row)
# Reuse consumer code without changing any repository outputs.
consume.HERE=P/'consumer_replay';consume.HERE.mkdir(exist_ok=True)
replay=consume.run()
saved=json.loads((C/'RESULT.json').read_text())
consumer={'redirection':'Only consume.HERE output directory redirected after module import; SOURCE/MANIFEST/ROOT unchanged. No code edit.','result_equal':replay==saved,'table_equal':(consume.HERE/'TABLE.csv').read_bytes()==(C/'TABLE.csv').read_bytes(),'source':replay['source'],'output':str(consume.HERE)}
files=json.loads((R/'EVIDENCE_MANIFEST.json').read_text())['files']
source_checks=[]
for q in files:
 f=ROOT/q['path'];actual=hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else None
 source_checks.append({'path':str(f),'sha_match':actual==q['sha256'],'size_match':f.stat().st_size==q['bytes'] if f.is_file() else False,'actual':actual,'expected':q['sha256']})
result={'false_rejection':falsereject,'false_acceptance':falseaccept,'rotation_scale_checks':rotations,'consumer_replay':consumer,'all_source_checks':source_checks,'source_file_count':len(source_checks),'source_mismatches':[q for q in source_checks if not q['sha_match'] or not q['size_match']]}
(P/'FINAL_CHECKS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'high_precision_false_reject':falsereject['independent_high_precision_witness'],'high_precision_false_accept':falseaccept['independent_high_precision_bound'],'rotation_scale_checks':rotations,'consumer_replay':consumer,'source_file_count':len(source_checks),'source_mismatches':result['source_mismatches']},indent=2))
