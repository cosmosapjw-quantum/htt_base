import csv, hashlib, importlib.util, json, math
from pathlib import Path
import numpy as np
from scipy.stats import chi2

ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=Path(__file__).resolve().parent
PACKET=Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/R37_NEXT_018_20261029.json')
P=ROOT/'docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-03-HUBBLE'
B=ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products'
checks=[]
def check(name,condition,detail=None):
    checks.append(dict(name=name,passed=bool(condition),detail=detail))
    if not condition: raise AssertionError((name,detail))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(n): return list(csv.DictReader((P/n).open()))
def eq(a,b): return bool(np.allclose(a,b,rtol=2e-12,atol=2e-14))
packet=json.loads(PACKET.read_text())
assignment=json.loads(packet['spawn_args']['message'].split('Assignment:\n',1)[1])
manifest=json.loads((P/'ARTIFACT_MANIFEST.json').read_text())
check('candidate manifest exact SHA256','sha256:'+sha(P/'ARTIFACT_MANIFEST.json')==packet['candidate_identity'])
for n,d in manifest['artifacts'].items():
    f=P/n
    check('manifest '+n,sha(f)==d['sha256'] and f.stat().st_size==d['bytes'])
for s in assignment['spec']['input_sources']:
    check('frozen source '+s['path'],sha(ROOT/s['path'])==s['sha256'])
check('independent reviewer is not author','/root/rc_3dab57f35de21656' not in assignment['authors'])
sn=json.loads((B/'R36-08-PUBLIC-SN/RESULT.json').read_text())
raw=json.loads((B/'R36-08-PUBLIC-SN/source_backup/actual_execution/RESULT_RAW.json').read_text())
cf=json.loads((B/'R36-01-CF4-OPERATOR/RESULT.json').read_text())
result=json.loads((P/'HUBBLE_OPACITY_RESULT.json').read_text())
check('SN source binding',sha(B/'R36-08-PUBLIC-SN/RESULT.json')==result['input_sha256']['R36-08_RESULT'])
check('CF4 source binding',sha(B/'R36-01-CF4-OPERATOR/RESULT.json')==result['input_sha256']['R36-01_RESULT'])
for name,n,nlow,dup in [('primary',490,342,62),('lower_z_sensitivity',705,557,114)]:
    s,r=sn[name],raw[name]
    check(name+' retained source rows',len(r['original_indices'])==n and s['n_low']==nlow and s['n_high']==148 and s['duplicate_CID_rows']==dup)
    check(name+' retained selected covariance',s['covariance']['dimension']==n and s['covariance']['max_symmetry_residual']==0 and s['covariance']['min_eigenvalue_mag2']>0)
    for k in ('row_key_sha256','low_8_mag','high_8_mag','full_16x16_covariance_mag2'):
        check(name+' retained source exact '+k,s[k]==r[k])
    z=np.array(r['plot']['zHD'])
    check(name+' frozen redshift domain',np.min(z)>=s['selection_lower_zHD'] and np.max(z)<=.15 and np.count_nonzero(z>=.06)==148)
    C=np.array(s['full_16x16_covariance_mag2'])
    check(name+' full16 positive covariance',eq(C,C.T) and np.linalg.eigvalsh(C).min()>0 and np.count_nonzero(C[:8,8:])==64)
    check(name+' profiled joint GLS exact covariance',s['full_16x16_covariance_mag2']==s['fits']['full']['covariance_mag2'])
check('490 cohort subset of 705 sensitivity',set(raw['primary']['original_indices']).issubset(raw['lower_z_sensitivity']['original_indices']))
check('same high depth rows',set(np.array(raw['primary']['original_indices'])[np.array(raw['primary']['plot']['high'])])==set(np.array(raw['lower_z_sensitivity']['original_indices'])[np.array(raw['lower_z_sensitivity']['plot']['high'])]))
check('chi square quantile',abs(chi2.ppf(.95,16)-26.296227604864242)<1e-12)
q=chi2.ppf(.95,16); k=math.log(10)/5
dirs={'x':np.array([1.,0,0]),'y':np.array([0.,1,0]),'z':np.array([0.,0,1]),'minus_x':np.array([-1.,0,0])}
def feat(n):
    x,y,z=n
    return np.array([x,y,z,(x*x-y*y)/math.sqrt(2),(x*x+y*y-2*z*z)/math.sqrt(6),math.sqrt(2)*x*y,math.sqrt(2)*x*z,math.sqrt(2)*y*z])
def law(cohort):
    d=sn[cohort]
    return np.r_[d['low_8_mag'],d['high_8_mag']],np.array(d['full_16x16_covariance_mag2'])
max_endpoint_residual=0.; min_normalized_denominator=1e9
rows=readcsv('LOCAL_H_IDENTIFIED_REGION.csv')
check('all planned local sensitivity rows',len(rows)==48)
for i,r in enumerate(rows):
    mu,C=law(r['cohort']);offset=0 if r['depth']=='low' else 8
    u,v=np.zeros(16),np.zeros(16)
    u[offset:offset+8]=feat(dirs[r['direction']]);v[offset:offset+8]=feat(dirs['z'])
    L=u-v;m=L@mu;se=math.sqrt(L@C@L);w=math.sqrt(q)*se
    bg,bt=float(r['geometric_difference_bound']),float(r['optical_depth_difference_bound']);b=bg+bt/2
    expected={'delta_m_mag':m,'delta_m_se_mag':se,'apparent_delta_logH':-k*m,'apparent_logH_95sim_low':-k*m-k*w,'apparent_logH_95sim_high':-k*m+k*w,'physical_logH_conditional_low':-k*m-k*w-b,'physical_logH_conditional_high':-k*m+k*w+b,'physical_ratio_conditional_low':math.exp(-k*m-k*w-b),'physical_ratio_conditional_high':math.exp(-k*m+k*w+b)}
    check('local row '+str(i),all(eq(float(r[key]),val) for key,val in expected.items()))
    for sign,label in [(1,'low'),(-1,'high')]:
        delta=sign*math.sqrt(q)*C@L/se
        check('support extremizer event '+str((i,sign)),eq(delta@np.linalg.solve(C,delta),q))
        endpoint=math.exp(-k*L@(mu+delta)-sign*b)
        max_endpoint_residual=max(max_endpoint_residual,abs(endpoint-float(r['physical_ratio_conditional_'+label])))
        denominator_min=math.exp(-k*(v@mu+math.sqrt(q*(v@C@v))))
        min_normalized_denominator=min(min_normalized_denominator,denominator_min)
        check('attained common-event endpoint '+str((i,sign)),eq(endpoint,float(r['physical_ratio_conditional_'+label])) and denominator_min>0)
check('per-direction component sum',all(eq(float(r['apparent_delta_logH']),float(r['dipole_delta_logH'])+float(r['stf_delta_logH'])) for r in rows))
cross=[]
for r in readcsv('joint_depth_contrasts.csv'):
    mu,C=law(r['cohort']);f=feat(dirs[r['direction']])-feat(dirs['z']);L=np.r_[-f,f]
    se=math.sqrt(L@C@L);wrong=math.sqrt(f@C[:8,:8]@f+f@C[8:,8:]@f)
    check('cross-depth '+r['cohort']+r['direction'],eq(se,float(r['joint_se_mag'])) and eq(wrong,float(r['independent_bin_se_wrong_mag'])) and eq(-k*L@mu-k*math.sqrt(q)*se,float(r['apparent_95sim_low'])) and eq(-k*L@mu+k*math.sqrt(q)*se,float(r['apparent_95sim_high'])))
    cross.append(dict(cohort=r['cohort'],direction=r['direction'],joint_se=se,wrong_independent_se=wrong))
for r in readcsv('same_input_scalar_comparator.csv'):
    mu,C=law(r['cohort']);f=feat(dirs[r['direction']])-feat(dirs['z']);L=np.r_[f,np.zeros(8)]
    m,se=L@mu,math.sqrt(L@C@L)
    check('same input scalar '+r['cohort']+r['direction'],eq(m,float(r['scalar_same_input_delta_m_mag'])) and eq(m,float(r['tensor_signed_delta_m_mag'])) and eq(se,float(r['scalar_and_tensor_joint_se_mag'])))
    for bg,bt in [(0,0),(.01,0),(.01,.02),(.02,.04)]:
        scalar=np.exp(-k*m+np.array([-1,1])*(k*math.sqrt(q)*se+bg+bt/2))
        match=next(t for t in rows if t['cohort']==r['cohort'] and t['depth']=='low' and t['direction']==r['direction'] and float(t['geometric_difference_bound'])==bg and float(t['optical_depth_difference_bound'])==bt)
        check('scalar identical physical region '+str((r['cohort'],r['direction'],bg,bt)),eq(scalar,[float(match['physical_ratio_conditional_low']),float(match['physical_ratio_conditional_high'])]))
for r in readcsv('CF4_retained_H_windows.csv'):
    L=np.zeros(36);i=cf['window_centers'].index(float(r['window_z_CMB']));L[i*9:(i+1)*9]=np.r_[1,feat(dirs[r['direction']])]
    check('CF4 source-specific mapping '+str((i,r['direction'])),eq(L@np.array(cf['theta4x9']).ravel(),float(r['apparent_H_km_s_Mpc'])) and eq(math.sqrt(L@np.array(cf['covariance36x36'])@L),float(r['marginal_se_km_s_Mpc'])))
c=299792.458;H=70.;a_true=.2;grid=np.arange(251)/1000
all_k=[]
for r in readcsv('synthetic_CBL_first_derivative.csv'):
    z=float(r['z']);dr=c*z/H*math.exp(.1*z);drp=c/H*math.exp(.1*z)*(1+.1*z)
    # Independent reconstruction: de-attenuate distance and derivative, then use standard curvature identity.
    d=dr*np.exp(-grid*z/2);dp=(drp-grid*dr/2)*np.exp(-grid*z/2)
    cur=((H*dp/c)**2-1)/d**2;all_k.append(cur)
    check('synthetic curvature '+str(z),eq(dr,float(r['d_r_Mpc'])) and eq(drp,float(r['d_r_prime_Mpc'])) and abs(cur[200])<1e-18 and eq(cur[0],float(r['naive_kappa_invMpc2'])) and eq(cur.min(),float(r['compatible_min_invMpc2'])) and eq(cur.max(),float(r['compatible_max_invMpc2'])))
spreads=np.ptp(all_k,axis=0)
check('one common opacity parameter for all windows',np.argmin(spreads)==200 and spreads[200]<1e-18 and spreads[0]>1e-10)
for r in readcsv('distance_transmission_interval.csv'):
    lo,hi=float(r['distance_lower_length_units']),float(r['distance_upper_length_units']);tm,tx=float(r['t_min']),float(r['t_max']);qv=np.array([1/9,1/25])
    check('transmission interval formula '+str(tm),eq(lo,math.sqrt(tm/qv.min())) and eq(hi,math.sqrt(tx/qv.max())))
    check('transmission endpoints feasible '+str(tm),np.min(lo*lo*qv)>=tm-1e-14 and np.max(hi*hi*qv)<=tx+1e-14)
    check('outside transmission region infeasible '+str(tm),np.min((lo*.99)**2*qv)<tm and np.max((hi*1.01)**2*qv)>tx)
    def Xi(v): return np.log(v)-np.log(v).mean()
    check('grey-scale does not change traceless log '+str(tm),eq(Xi(lo*lo*qv),Xi(hi*hi*qv)))
summary=dict(status='PASS',checks=len(checks),candidate_identity=packet['candidate_identity'],input_identity=packet['input_identity'],packet_id=packet['packet_id'],max_attained_endpoint_residual=max_endpoint_residual,min_normalized_reference_H_on_ellipsoids=min_normalized_denominator,cross_depth=cross,common_opacity_minimizer=float(grid[np.argmin(spreads)]),common_opacity_spread=float(spreads[200]),zero_opacity_spread=float(spreads[0]),checks_detail=checks)
(OUT/'INDEPENDENT_CHECKS.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='checks_detail'},indent=2))
