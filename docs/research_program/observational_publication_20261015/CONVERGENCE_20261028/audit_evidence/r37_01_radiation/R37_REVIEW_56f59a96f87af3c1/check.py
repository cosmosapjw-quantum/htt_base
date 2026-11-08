from pathlib import Path
import csv, hashlib, importlib.util, json, subprocess, sys
import numpy as np
import matplotlib, pytest
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=Path(__file__).resolve().parent
BASE=ROOT/'docs/research_program/observational_publication_20261015'
P=BASE/'CONVERGENCE_20261028/products/R37-01-RADIATION'
R36=BASE/'OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-05-RADIATION-RESPONSE'
packet=json.loads((OUT.parent/'R37_NEXT_012_20261029.json').read_text())
a=json.loads(packet['spawn_args']['message'].split('Assignment:\n',1)[1])
d=json.loads((P/'RADIATION_IMAGE_RESULT.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(x,msg):
 if not x:raise AssertionError(msg)
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
manifest=json.loads((P/'ARTIFACT_MANIFEST.json').read_text())
check('sha256:'+sha(P/'ARTIFACT_MANIFEST.json')==packet['candidate_identity'],'candidate')
for x in manifest['artifacts']:
 p=P/x['path'];check(sha(p)==x['sha256'] and p.stat().st_size==x['size_bytes'],'artifact '+str(p))
for x in a['spec']['input_sources']: check(sha(ROOT/x['path'])==x['sha256'],'source '+x['path'])
for x in a['history_refs']:check(sha(Path(x['receipt']['path']))==x['receipt']['sha256'],'history receipt')
prior=Path(manifest['prior_backup']);prior_m=json.loads((prior/'ARTIFACT_MANIFEST.json').read_text())
check('sha256:'+sha(prior/'ARTIFACT_MANIFEST.json')==manifest['prior_candidate_identity'],'prior candidate')
for x in prior_m['artifacts']:check(sha(prior/x['path'])==x['sha256'],'preserved prior artifact')
npz=R36/'source_backup/derived/sample_arrays.npz'
check(sha(npz)==d['source_bindings']['R36_ARRAYS_sha256'],'array binding')
check(sha(R36/'PUBLICATION_STATUS.json')==d['source_bindings']['R36_PUBLICATION_STATUS_sha256'],'status binding')
status=json.loads((R36/'PUBLICATION_STATUS.json').read_text());check(status['acceptance_met'],'source status')
core=load(R36/'radiation_core.py','review_core')
# Core provides quadrature/STF conventions only. Independently construct the
# direct and rank-0/2/4 kernels rather than aliasing common output to full.
n,w=core.sphere_rule(24,49);S=core.STF_BASIS;eye=np.eye(3)
e=-n
stf=lambda x:(x+np.swapaxes(x,-1,-2))/2-np.trace(x,axis1=-2,axis2=-1)[...,None,None]*eye/3
Q=np.einsum('ni,nj->nij',e,e)-eye/3
picoord=np.einsum('aij,nij->na',S,Q)
SE=np.einsum('aij,nj->nai',S,e)
K=2*np.einsum('nai,nbi->nab',SE,SE)-np.einsum('na,nb->nab',picoord,picoord)
# Assemble fourth STF tensor directly from the six symmetrized delta terms.
H=np.einsum('ni,nj,nk,nl->nijkl',e,e,e,e)
H-= (np.einsum('ij,nk,nl->nijkl',eye,e,e)+np.einsum('ik,nj,nl->nijkl',eye,e,e)+np.einsum('il,nj,nk->nijkl',eye,e,e)+np.einsum('jk,ni,nl->nijkl',eye,e,e)+np.einsum('jl,ni,nk->nijkl',eye,e,e)+np.einsum('kl,ni,nj->nijkl',eye,e,e))/7
H+=(np.einsum('ij,kl->ijkl',eye,eye)+np.einsum('ik,jl->ijkl',eye,eye)+np.einsum('il,jk->ijkl',eye,eye))/35
Kdrop=np.empty_like(K)
for j,s in enumerate(S):Kdrop[:,:,j]=np.einsum('aij,nij->na',S,8/15*s+10/7*stf(np.einsum('ij,njk->nik',s,Q)))
Kcommon=Kdrop-np.einsum('aij,nijkl,bkl->nab',S,H,S)
proj=eye-np.einsum('ni,nj->nij',n,n)
ps=proj@S[0]@proj
pol=.12*(ps-.5*proj*np.trace(ps,axis1=1,axis2=2)[:,None,None])
polcoord=np.einsum('aij,nij->na',S,pol)
screen=proj/2+pol
# Independent Lorentz sky reconstruction from the stated speed and quadrupole.
v=.3*np.array([.6,0.,.8]);g=1/np.sqrt(1-v@v)
p0=g*(1-e@v);pspace=e+((g-1)*(e@v)/(v@v)-g)[:,None]*v
zrest=-pspace[:,2]/p0
temp=(1+.02*(3*zrest*zrest-1)/2)**.25/p0
R=np.array(d['target']['R_tau_center']);true=np.array(d['target']['STF5_shear']);gamma=.4
basis=np.column_stack([n,picoord]);tb=w@temp
kernels={'full':(w[:,None,None]*K).reshape(len(n),25),'common_carrier':(w[:,None,None]*Kcommon).reshape(len(n),25),'H4_dropped_closure':(w[:,None,None]*Kdrop).reshape(len(n),25)}
piK=w[:,None]*picoord;polK=w[:,None]*polcoord

def evaluate(bright):
 pi=bright@piK;Pstar=bright@polK
 mats={k:(bright@v).reshape(-1,5,5) for k,v in kernels.items()}
 mats['unpolarized']=mats['full']
 result={k:np.linalg.solve(L,-(R+gamma*(.9*pi+(.2*Pstar if k!='unpolarized' else 0)))[...,None])[...,0] for k,L in mats.items()}
 return result,mats
central_arr,mats0=evaluate((temp**4)[None]);centers={k:v[0] for k,v in central_arr.items()}
L0=mats0['full'][0];Ldrop=mats0['H4_dropped_closure'][0]
check(max(np.max(abs(centers[k]-d['centers'][k])) for k in centers)<2e-10,'centers')
check(np.max(abs(centers['full']-true))<2e-10,'target')
archive=np.load(npz);law={};min_temperature=1e100;min_eig=1e100;full_common_matrix_error=0.;full_common_shear_error=0.
for split in ['cal','test']:
 eta=archive[f'a0.02_b0.3_eta_{split}'];acc={k:[] for k in centers}
 check(eta.shape==((8191 if split=='cal' else 4096),8),'draw shape')
 for start in range(0,len(eta),256):
  noisy=temp[None]+tb*eta[start:start+256]@basis.T
  min_temperature=min(min_temperature,float(noisy.min()))
  vals,mats=evaluate(noisy**4)
  min_eig=min(min_eig,float(np.linalg.eigvalsh(mats['full']).min()))
  full_common_matrix_error=max(full_common_matrix_error,float(np.max(abs(mats['full']-mats['common_carrier']))))
  full_common_shear_error=max(full_common_shear_error,float(np.max(abs(vals['full']-vals['common_carrier']))))
  for k in acc:acc[k].append(vals[k])
 law[split]={k:np.concatenate(v) for k,v in acc.items()}
check(min_temperature>0,'positive all saved draws')
# Explicit order statistics, independent of producer np.quantile calls.
cal_deviation=abs(law['cal']['full']-centers['full'])
index=int(np.ceil(.95*(len(cal_deviation)-1)))
scales=np.sort(cal_deviation,axis=0)[index]
score={split:np.max(np.stack([abs(law[split][k]-centers[k])/scales for k in centers]),axis=(0,2)) for split in law}
q=np.sort(score['cal'])[index];radius=q*scales
hits=int(np.sum(score['test']<=q));old_hits=int(np.sum(np.all(abs(law['test']['full']-true)<=scales,axis=1)))
check(hits==3888 and old_hits==3389,'joint and old hits')
check(np.max(abs(scales-d['matched_law']['joint_event']['common_scales']))<1e-15,'scales')
check(abs(q-d['matched_law']['joint_event']['threshold'])<1e-9,'threshold')
check(np.max(abs(radius-d['matched_law']['joint_event']['radii']))<1e-15,'radii')
# Recompute every numeric field in both main tables.
with (P/'MATCHED_COVERAGE.csv').open() as f:rows=list(csv.DictReader(f))
max_coverage_numeric_difference=0.
for row in rows:
 k=row['method'];j=int(row['direction'][-1])-1
 marginal=np.sort(abs(law['cal'][k]-centers[k]),axis=0)[index,j]
 expected={'marginal_radius_diagnostic':marginal,'marginal_target_coverage_test_diagnostic':np.mean(abs(law['test'][k][:,j]-true[j])<=marginal),'joint_event_radius':radius[j],'joint_event_width':2*radius[j],'joint_direction_centered_coverage_test':np.mean(abs(law['test'][k][:,j]-centers[k][j])<=radius[j]),'joint_direction_target_coverage_test':np.mean(abs(law['test'][k][:,j]-true[j])<=radius[j]),'cal_N':8191,'test_N':4096,'signed_bias':centers[k][j]-true[j]}
 for key,value in expected.items():
  delta=abs(float(row[key])-value);max_coverage_numeric_difference=max(max_coverage_numeric_difference,delta);check(delta<1e-14,'coverage row '+str((k,j,key,delta)))
U=np.array(d['physical_error']['U']);V=np.array(d['physical_error']['V'])
with (P/'SHEAR_SUPPORT.csv').open() as f:support=list(csv.DictReader(f))
max_support_difference=0.;max_independent_vs_shared=0.
for row in support:
 k=row['method'];j=int(row['direction'][-1])-1;er=float(row['epsilon_R']);ep=float(row['epsilon_P']);L=Ldrop if k=='H4_dropped_closure' else L0
 mapped=np.linalg.solve(L,er*U+gamma*ep/5*V);expected=np.linalg.norm(mapped[j])
 max_support_difference=max(max_support_difference,abs(expected-float(row['physical_support'])))
 check(abs(expected-float(row['physical_support']))<2e-14,'physical support')
 check(abs(expected+radius[j]-float(row['fixed_operator_sensitivity_half_width']))<2e-14,'sensitivity half width')
 check(abs(centers[k][j]-float(row['center']))<2e-14,'support center')
 independent=np.linalg.norm(np.linalg.solve(L,er*U)[j])+np.linalg.norm(np.linalg.solve(L,gamma*ep/5*V)[j])
 max_independent_vs_shared=max(max_independent_vs_shared,independent-expected)
# Actual rank6 gain and deterministic positive fibre, independent projector via QR.
full_kernel=np.column_stack([kernels['full'],piK,polK]);drop_kernel=np.column_stack([w,piK,polK]);gain_kernel=np.column_stack([w,-.5*piK+polK])
rank_info={}
for name,k in [('full_fixed_profile',full_kernel),('H4_dropped_retaining_rho_pi_Pstar',drop_kernel),('true_thomson_gain_at_V_zero',gain_kernel)]:
 sv=np.linalg.svd(k,compute_uv=False);rank=int(np.sum(sv>1e-12*sv[0]));rank_info[name]={'rank':rank,'singular_values':sv.tolist()}
 check(rank==d['carrier']['fixed_profile_angular_kernel_ranks'][name],'rank '+name)
qgain,_=np.linalg.qr(gain_kernel,mode='reduced');delta=piK[:,0]-qgain@(qgain.T@piK[:,0]);delta/=max(abs(delta))
pair=np.stack([temp**4+.02*delta,temp**4-.02*delta]);sameM=pair@gain_kernel
vals,mats=evaluate(pair);member_shear=vals['full'];gainsep=np.linalg.norm(member_shear[0]-member_shear[1])
check(pair.min()>0,'fibre positivity');check(np.max(abs(sameM[0]-sameM[1]))<2e-10,'same M');check(gainsep>1e-5,'different shear')
check(np.max(abs(member_shear-np.array(d['true_gain_only_identified_set']['member_shears'])))<1e-14,'gain members')
with (P/'GAIN_IDENTIFIED_SUPPORT.csv').open() as f:gain_rows=list(csv.DictReader(f))
gain_max_table_error=0.
for row in gain_rows:
 j=int(row['direction'][-1])-1;er=float(row['epsilon_R']);ep=float(row['epsilon_P']);b=er*U+gamma*ep/5*V
 rad=np.linalg.norm(np.linalg.solve(mats['full'],np.broadcast_to(b,(2,5,2))),axis=2)[:,j]
 expected={'member_min':member_shear[:,j].min(),'member_max':member_shear[:,j].max(),'two_member_disk_inner_min':np.min(member_shear[:,j]-rad),'two_member_disk_inner_max':np.max(member_shear[:,j]+rad)}
 for key,value in expected.items():gain_max_table_error=max(gain_max_table_error,abs(value-float(row[key])));check(abs(value-float(row[key]))<1e-14,'gain support')
P0=temp**4@polK
omission=centers['full']-centers['unpolarized'];omission_exact=-np.linalg.solve(L0,gamma/5*P0)
check(np.max(abs(omission-omission_exact))<1e-14,'omission sign')
check(np.linalg.norm(omission)<=gamma*np.linalg.norm(P0)/(5*np.linalg.eigvalsh(L0)[0])+1e-14,'omission bound')
# Read-only original acceptance preservation, not a new admission.
dag=BASE/'PUBLICATION_DAG.json';dag_rel=dag.relative_to(ROOT)
head_dag=subprocess.check_output(['git','show',f'HEAD:{dag_rel}'],cwd=ROOT)
check(dag.read_bytes()==head_dag,'original DAG unchanged from HEAD')
legacy=json.loads((BASE/'CONVERGENCE_20261028/products/R37-00-FIRST-REPORT/LEGACY_SCOPE.json').read_text())
# 95% CP interval is descriptive only: reused test draws, not new prospective validation.
from scipy.stats import beta
cp=[float(beta.ppf(.025,hits,4096-hits+1)),float(beta.ppf(.975,hits+1,4096-hits))]
summary={'environment':{'python':sys.version,'numpy':np.__version__,'matplotlib':matplotlib.__version__,'pytest':pytest.__version__},'candidate_identity':packet['candidate_identity'],'manifest_artifacts_verified':len(manifest['artifacts']),'input_sources_verified':len(a['spec']['input_sources']),'prior_artifacts_verified':len(prior_m['artifacts']),'history_receipts_verified':len(a['history_refs']),'packet_sha256':sha(OUT.parent/'R37_NEXT_012_20261029.json'),'minimum_saved_temperature':min_temperature,'minimum_saved_coercivity':min_eig,'full_common_kernel_error':float(np.max(abs(K-Kcommon))),'full_common_all_draw_matrix_error':full_common_matrix_error,'full_common_all_draw_shear_error':full_common_shear_error,'joint_event':{'cal_N':8191,'test_N':4096,'order_index_1based':index+1,'threshold':q,'radii':radius.tolist(),'joint_centered_hits':hits,'joint_centered_fraction':hits/4096,'descriptive_CP95':cp,'old_marginal_full_joint_hits':old_hits,'per_method_target_hits':{k:int(np.sum(np.all(abs(law['test'][k]-true)<=radius,axis=1))) for k in centers}},'coverage_rows':len(rows),'max_coverage_numeric_difference':max_coverage_numeric_difference,'support_rows':len(support),'max_support_difference':max_support_difference,'maximum_gap_if_physical_sources_incorrectly_independent':max_independent_vs_shared,'rank_info':rank_info,'gain_fibre':{'minimum_brightness':float(pair.min()),'M_max_difference':float(np.max(abs(sameM[0]-sameM[1]))),'separation_norm':float(gainsep),'gain_rows':len(gain_rows),'max_gain_support_difference':gain_max_table_error},'omission_sign_error':float(np.max(abs(omission-omission_exact))),'original_dag_sha256':sha(dag),'original_dag_HEAD_equal':True,'legacy_scope':legacy,'candidate_unchanged':sha(P/'ARTIFACT_MANIFEST.json')==packet['candidate_identity'].split(':')[1]}
(OUT/'checks.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['rank_info','legacy_scope']},indent=2))
