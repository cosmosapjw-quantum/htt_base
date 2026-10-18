"""One bounded D07 campaign under D07_CONTRACT.md. No physical admission."""
from pathlib import Path
import csv, hashlib, json, os, sys, time, warnings
from statistics import NormalDist
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import numpy as np
from scipy.optimize import linprog, OptimizeWarning

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
PROGRAM=ROOT/'docs/research_program/observational_publication_20261015'
D03=HERE.parent/'D03_PANTHEON_CF4'
sys.path.insert(0,str(D03))
import d03 as source
H02=PROGRAM/'CONTINUATION_20261018/H02_EXECUTION_20261018/results/h02_actual_centers.json'
SOURCE=ROOT/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz'
METHODS=['FP','TF','SN','OTHER']
WINDOWS=['all_selected','z025','z040','z060','z080']
BASIS=['nx','ny','nz','nx2-nz2','ny2-nz2','2nxny','2nxnz','2nynz']
FROZEN={SOURCE:'86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c',
 H02:'c3f70ae28c860d3aa0276df17afc56db9f29586b0d329b773c27d01890ae7ac3',
 D03/'results/D03_RESULT.json':'c711a82bf5dbe95fd7bd847fea2d7b7d8f30e18463d9113de406ae16dbbf7296',
 D03/'results/OBJECT_GRAPH.csv':'e0cbb0e5cf8df60a0f381ff2955038fdcfd3719bb171ff244691e91df6d2482b'}


def shape8(n):
    x,y,z=np.asarray(n).T
    return np.column_stack([x,y,z,x*x-z*z,y*y-z*z,2*x*y,2*x*z,2*y*z])


def rank_info(A):
    u,s,vt=np.linalg.svd(A,full_matrices=False)
    tol=max(A.shape)*np.finfo(float).eps*(s[0] if len(s) else 0.)
    ranks=[int(np.sum(s>tol*f)) for f in [.1,1,10]]
    if len(set(ranks))!=1:raise ValueError('UNSTABLE_RANK: '+str(ranks))
    rank=ranks[1]
    return {'shape':list(A.shape),'rank':rank,'tolerance':float(tol),'ranks_0p1_1_10':ranks,'singular_values':s.tolist(),
            'nullspace_basis':vt[rank:].tolist()},u[:,:rank],vt[rank:].T


def quotient(A,N):
    info,q,_=rank_info(N)
    return A-q@(q.T@A),info


def symmetric_whitener(C):
    """Principal inverse square root: permutation-equivariant l-infinity norm."""
    e,q=np.linalg.eigh((C+C.T)/2)
    if e.min()<=0:raise ValueError('reference norm covariance not positive definite')
    W=(q/np.sqrt(e))@q.T
    err=float(np.max(np.abs(W@C@W-np.eye(len(C)))))
    if err>1e-9:raise ValueError('reference whitener residual exceeds 1e-9')
    return W,{'min_eigenvalue':float(e.min()),'max_eigenvalue':float(e.max()),'whitener_max_residual':err,
              'definition':'principal symmetric inverse square root, not Cholesky; permutation-equivariant infinity norm'}


def scalar_design(rows,partitions=None):
    surveys=sorted(set(map(int,rows['IDSURVEY'])))
    names=['common_offset']+[f'survey_{s}' for s in surveys]
    cols=[np.ones(len(rows))]+[(rows['IDSURVEY']==s).astype(float) for s in surveys]
    if partitions is not None:
        for p in sorted(set(partitions)):
            names.append('partition_'+str(p));cols.append((partitions==p).astype(float))
    return np.column_stack(cols),names


def valid_host_coordinates(m):
    if m is None or m['has_host']!='1' or not m['host'].strip():return False
    try:ra,dec=float(m['RA_host']),float(m['Dec_host'])
    except (ValueError,TypeError):return False
    return bool(np.isfinite([ra,dec]).all() and 0<=ra<360 and -90<=dec<=90)


def layout(na,nc):
    blocks={};n=0
    for key,size in [('eta',8),('theta',40),('gamma',32),('kappaP',8),('kappaC',8),('alpha',na),('beta',nc)]:
        blocks[key]=slice(n,n+size);n+=size
    blocks['t']=n
    return blocks,n+1


def build_angular_design(Xg,Xh,partitions,Za,Zc):
    sl,size=layout(Za.shape[1],Zc.shape[1]);nh=5*4*8
    H=np.zeros((nh,size));Da=np.zeros((len(Xg),size));Dc=np.zeros((len(Xh),size))
    k=0
    for w in range(5):
        for m in range(4):
            for j in range(8):
                H[k,sl['theta'].start+w*8+j]=1;H[k,sl['eta'].start+j]=1;H[k,sl['gamma'].start+m*8+j]=1;k+=1
    Da[:,sl['eta']]=Xg;Da[:,sl['kappaP']]=-Xg;Da[:,sl['alpha']]=Za
    for m,label in enumerate(METHODS):Da[partitions==label,slice(sl['gamma'].start+m*8,sl['gamma'].start+(m+1)*8)]=Xg[partitions==label]
    Dc[:,sl['kappaP']]=Xh;Dc[:,sl['kappaC']]=-Xh;Dc[:,sl['beta']]=Zc
    G=np.zeros((size,8))
    G[sl['eta']]=np.eye(8);G[sl['kappaP']]=np.eye(8);G[sl['kappaC']]=np.eye(8)
    for w in range(5):G[slice(sl['theta'].start+w*8,sl['theta'].start+(w+1)*8)]=-np.eye(8)
    return H,Da,Dc,G,sl


def targets(sl,size):
    z=np.zeros((8,size));psi=np.zeros((40,size));chi=np.zeros((8,size))
    z[:,sl['eta']]=np.eye(8);z[:,sl['kappaP']]=-np.eye(8)
    chi[:,sl['kappaP']]=np.eye(8);chi[:,sl['kappaC']]=-np.eye(8)
    for w in range(5):
        psi[w*8:(w+1)*8,slice(sl['theta'].start+w*8,sl['theta'].start+(w+1)*8)]=np.eye(8)
        psi[w*8:(w+1)*8,sl['kappaP']]=np.eye(8)
    return z,psi,chi


def prepare(calibrator_support):
    for p,h in FROZEN.items():source.sealed(p,h)
    result=json.loads((D03/'results/D03_RESULT.json').read_text())
    candidate=json.loads((D03/'CANDIDATE.json').read_text())
    if candidate['candidate_digest_sha256']!='c326fc79b4cfd255d4655cb47b27a4b399403179c3342ac30ae7113c80dcc388':raise ValueError('D03 frozen candidate mismatch')
    for p,h in source.EXPECTED.items():source.sealed(p,h)
    source.sealed(source.EXTRA/'all_redshifts_PVs.csv',result['pantheon_metadata']['sha256'])
    p=np.genfromtxt(source.PANTHEON/'Pantheon_SH0ES.dat',names=True,dtype=None,encoding='utf8')
    raw=np.loadtxt(source.PANTHEON/'Pantheon_SH0ES_STAT_SYS.cov');Craw=raw[1:].reshape(int(raw[0]),int(raw[0]));C=(Craw+Craw.T)/2
    with (D03/'results/OBJECT_GRAPH.csv').open() as stream:graph=list(csv.DictReader(stream))
    with np.load(SOURCE,allow_pickle=False) as old:
        ids=old['group_id'].copy();directions=old['n_J2000'].copy();families=old['method_family'].copy();dm=old['dmzp'].copy();sigma=old['e_dmzp'].copy();z=old['z_CMB'].copy()
    loc={int(g):i for i,g in enumerate(ids)}
    ai=np.array([int(g['row_index']) for g in graph if g['in_previous_H02_selected_groups']=='True'],int)
    if len(ai)!=559:raise ValueError('expected559 selected associations before exclusions')
    gi=np.array([loc[int(graph[i]['group_1PGC'])] for i in ai]);pgc=np.array([int(graph[i]['PGC']) for i in ai])
    if np.any(sigma[gi]<=0) or not np.isfinite(dm[gi]).all():raise ValueError('selected pooled DMzp/error incomplete')
    Xg=shape8(directions[gi]);a=dm[gi]-p['MU_SH0ES'][ai]
    unique,gmap=np.unique(ids[gi],return_inverse=True);B=np.eye(len(unique))[gmap]
    sd=np.array([sigma[loc[int(g)]] for g in unique]);Va=C[np.ix_(ai,ai)]+(B*sd**2)@B.T
    Wa,wa_info=symmetric_whitener(Va)
    ci_all=np.flatnonzero(p['IS_CALIBRATOR']==1)
    if len(ci_all)!=77:raise ValueError('expected77 published calibrator residuals')
    with (source.EXTRA/'all_redshifts_PVs.csv').open() as stream:meta=list(csv.DictReader(stream))
    lookup=source.aliases(meta);ci=[];host=[];excluded=[];provenance=[]
    for i in ci_all:
        r=p[i];m,status=source.choose_metadata(r['CID'],source.direction(r['RA'],r['DEC']),lookup)
        cf4=bool(graph[i]['PGC'])
        valid=valid_host_coordinates(m)
        if calibrator_support=='CF4_65':valid=valid and cf4
        if not valid:
            excluded.append({'row_index':int(i),'CID':str(r['CID']),'direction':'UNKNOWN','reason':status if m is None else 'host_not_corroborated_under_support_rule','CF4_correlated_host':cf4});continue
        ci.append(int(i));host.append(source.direction(float(m['RA_host']),float(m['Dec_host'])))
        provenance.append({'row_index':int(i),'CID':str(r['CID']),'SNID':m['SNID'],'IAUC':m['IAUC'],'host':m['host'],'host_RA':float(m['RA_host']),'host_DEC':float(m['Dec_host']),'CF4_host_corroboration':cf4})
    ci=np.array(ci,int);Xh=shape8(np.array(host));c_all=p['MU_SH0ES'][ci_all]-p['CEPH_DIST'][ci_all];c=p['MU_SH0ES'][ci]-p['CEPH_DIST'][ci]
    if len(ci)!=(75 if calibrator_support=='ALIAS_SKY_HOST_75' else 65):raise ValueError('clarified calibrator support count changed')
    Wc,wc_info=symmetric_whitener(C[np.ix_(ci,ci)])
    Za,za_names=scalar_design(p[ai],families[gi]);Zc,zc_names=scalar_design(p[ci])
    H,Da,Dc,G,sl=build_angular_design(Xg,Xh,families[gi],Za,Zc);size=Da.shape[1]
    Rz,Rpsi,Rchi=targets(sl,size)
    prior=json.loads(H02.read_text());centers=[];radii=[]
    crit=NormalDist().inv_cdf(1-.05/(2*160))
    for w in WINDOWS:
        for m in METHODS:
            fit=prior['fits'][w][m]
            centers.extend(fit['coefficients_mag']);radii.extend(crit*np.sqrt(np.diag(fit['working_covariance'])))
    centers=np.array(centers);radii=np.array(radii)
    # All original gamma/window boxes; no repeated H02 data fitting.
    basis_idx=np.arange(sl['kappaC'].stop)
    angular=np.vstack([H[:,basis_idx],Da[:,basis_idx],Dc[:,basis_idx]])
    nuisance=np.zeros((len(angular),Za.shape[1]+Zc.shape[1]));nuisance[160:160+len(a),:Za.shape[1]]=Za;nuisance[160+len(a):,Za.shape[1]:]=Zc
    projected,nuisance_info=quotient(angular,nuisance);joint_info,_,K=rank_info(projected)
    chi_projection,zc_info=quotient(Xh,Zc);chi_info,_,_=rank_info(chi_projection)
    def estimability(R):return {'target_rank':int(np.linalg.matrix_rank(R[:,basis_idx])),'target_nullspace_maxabs':float(np.max(np.abs(R[:,basis_idx]@K))),
                               'design_only_estimable':bool(np.max(np.abs(R[:,basis_idx]@K))<=1e-10)}
    gauge={name:float(np.max(np.abs(M@G)))/max(1.,float(np.linalg.norm(M,np.inf))*float(np.linalg.norm(G,np.inf))) for name,M in [('H02',H),('pair',Da),('calibrator',Dc)]}
    if max(gauge.values())>1e-12:raise ValueError('gauge witness failure')
    # Reversing inputs then independently rebuilding the principal norm must
    # leave the reference infinity constraints invariant up to roundoff.
    pa=np.arange(len(a))[::-1];pc=np.arange(len(c))[::-1]
    Wap,_=symmetric_whitener(Va[np.ix_(pa,pa)]);Wcp,_=symmetric_whitener(C[np.ix_(ci[pc],ci[pc])])
    permutation={'pair_whitened_design_maxabs':float(np.max(np.abs(Wap@Da[pa]-(Wa@Da)[pa]))),
                 'calibrator_whitened_design_maxabs':float(np.max(np.abs(Wcp@Dc[pc]-(Wc@Dc)[pc]))),
                 'pair_whitened_data_maxabs':float(np.max(np.abs(Wap@a[pa]-(Wa@a)[pa]))),
                 'calibrator_whitened_data_maxabs':float(np.max(np.abs(Wcp@c[pc]-(Wc@c)[pc])))}
    if max(permutation.values())>1e-9:raise ValueError('permutation reference norm disagreement')
    host_labels=np.array([r['host'].strip() for r in provenance]);host_unique,host_inverse=np.unique(host_labels,return_inverse=True)
    Bc=np.eye(len(host_unique))[host_inverse]
    d02_path=HERE.parent/'D02_HI_CF4/D02_RESULT.json';d02=json.loads(d02_path.read_text());ledger=d02['external_all_target_ledger'];source.sealed(Path(ledger['path']),ledger['sha256'])
    with Path(ledger['path']).open() as stream:hi=list(csv.DictReader(stream))
    hi_by_pgc={int(r['pgc']):r for r in hi};hi_by_group={}
    for r in hi:
        if r['CF4_group']:hi_by_group.setdefault(int(r['CF4_group']),[]).append(r['outcome'])
    hi_host=np.array([hi_by_pgc[int(k)]['outcome'] if int(k) in hi_by_pgc else 'NO_TARGET_ID_OVERLAP' for k in pgc])
    hi_group=np.array(['|'.join(sorted(hi_by_group.get(int(k),[]))) or 'NO_TARGET_GROUP_OVERLAP' for k in ids[gi]])
    arrays={'a_row_index':ai,'group_id':ids[gi],'host_PGC':pgc,'group_direction':directions[gi],'pooled_DMzp_mag':dm[gi],
            'pooled_eDMzp_mag':sigma[gi],'pooled_partition':families[gi],'group_zCMB':z[gi],
            'a_mag':a,'c_all77_row_index':ci_all,'c_all77_mag':c_all,'c_supported_row_index':ci,'c_supported_mag':c,
            'calibrator_host_direction':np.array(host),'B_group_incidence':B,'CF4_unique_group_ids':unique,'CF4_unique_group_error':sd,
            'calibrator_named_host_incidence':Bc,'calibrator_named_host_labels':host_unique,'calibrator_row_host_labels':host_labels,
            'D02_host_outcome_annotation':hi_host,'D02_group_outcome_annotation':hi_group,
            'Pantheon_a_subblock':C[np.ix_(ai,ai)],'Pantheon_c_subblock':C[np.ix_(ci,ci)],
            'Pantheon_row_error_ac_component':-C[np.ix_(ai,ci)],'Wa':Wa,'Wc':Wc,'Za':Za,'Zc':Zc,'Xg':Xg,'Xh':Xh,
            'H02_design':H,'pair_design':Da,'calibrator_design':Dc,'gauge_witnesses':G,
            'H02_centers':centers,'H02_radii':radii,'target_zeta':Rz,'target_psi':Rpsi,'target_chi':Rchi,
            'projected_joint_angular_design':projected}
    metadata={'owner':'htt','claim_tier':'C0','status':'CONDITIONAL_NON_CLAIM_BEARING','transfer_source':'none',
              'calibrator_support_rule':calibrator_support,'pair_rows_before_exclusions':len(ai),'pair_rows_retained':len(a),'calibrator_all_rows':len(ci_all),
              'calibrator_direction_support':len(ci),'calibrator_direction_exclusions':excluded,'calibrator_provenance':provenance,
              'pair_unique_groups':len(unique),'pair_unique_hosts':len(set(pgc)),'block_overlap_Pantheon_rows':sorted(set(map(int,ai))&set(map(int,ci))),
              'partitions':dict(zip(*[list(x) for x in np.unique(families[gi],return_counts=True)])),
              'Za_columns':za_names,'Zc_columns':zc_names,'reference_norm_pair':wa_info,'reference_norm_calibrator':wc_info,
              'reference_zero_crossblock':'CHOSEN_BLOCK_NORM_NOT_MEASURED_CROSSCOV; full underlying overlapping row crossblock retained separately',
              'nuisance_rank':nuisance_info,'joint_angular_rank_after_nuisance':joint_info,
              'calibrator_nuisance_rank':zc_info,'chi_relative_response_rank':chi_info,
              'estimability':{'zeta':estimability(Rz),'psi':estimability(Rpsi),'chi':estimability(Rchi)},
              'scaled_gauge_infinity_residual':gauge,'physical_eta_theta':'UNBOUNDED whenever feasible by retained gauge witnesses',
              'permutation_invariance':permutation,'H02_unchanged_boxes':{'windows':WINDOWS,'partitions':METHODS,'comparisons':160,'alpha':.05,'law':'gaussian_marginals','critical_value':crit,'delta_relative_mag':.02},
              'basis':BASIS,'angular_units':'mag','missing_pair_remainder':'unmeasured angular/depth transport; t is not physical finite-z/flow bound',
              'D02_use':'overlap/outcome annotations only; no inverse selection weights',
              'D02_ledger':ledger,'D02_host_overlap_rows':int(np.sum(hi_host!='NO_TARGET_ID_OVERLAP')),'D02_group_overlap_rows':int(np.sum(hi_group!='NO_TARGET_GROUP_OVERLAP')),
              'calibrator_unique_named_host_labels':len(host_unique),'calibrator_CF4_corroborated_subset_rows':sum(r['CF4_host_corroboration'] for r in provenance),
              'forbidden_uses':['physical eta/theta bounds','independent anchor','calibrated joint confidence','physical shear/tilt','original node admission']}
    metadata['partitions']={str(k):int(v) for k,v in metadata['partitions'].items()}
    return arrays,metadata,sl


class Campaign:
    def __init__(self,arrays,sl,start):
        self.d=arrays;self.sl=sl;self.start=start;self.calls=0;self.raw=[];self.witness=[]
        H=arrays['H02_design'];Da=arrays['Wa']@arrays['pair_design'];Dc=arrays['Wc']@arrays['calibrator_design'];ya=arrays['Wa']@arrays['a_mag'];yc=arrays['Wc']@arrays['c_supported_mag']
        self.A=np.vstack([H,-H,Da,-Da,Dc,-Dc]);self.b=np.r_[arrays['H02_centers']+arrays['H02_radii'],-arrays['H02_centers']+arrays['H02_radii'],ya,-ya,yc,-yc]
        self.A[320:,sl['t']]=-1
        self.bounds=[(None,None)]*H.shape[1]
        for i in range(sl['gamma'].start,sl['gamma'].stop):self.bounds[i]=(-.02,.02)
        self.bounds[sl['t']]=(0,None)

    def verify(self,p,t):
        d=self.d;s=self.sl
        # Reconstruct predictions separately from the assembled LP matrices.
        eta=p[s['eta']];kp=p[s['kappaP']];kc=p[s['kappaC']];theta=p[s['theta']].reshape(5,8);gamma=p[s['gamma']].reshape(4,8)
        pred=np.array([theta[w]+eta+gamma[m] for w in range(5) for m in range(4)]).ravel()
        h=max(0.,float(np.max(np.abs(pred-d['H02_centers'])-d['H02_radii'])))
        fam=d['pooled_partition'];ga=np.array([gamma[METHODS.index(str(m))] for m in fam])
        pa=d['Za']@p[s['alpha']]+np.sum(d['Xg']*(eta+ga-kp),axis=1)
        pc=d['Zc']@p[s['beta']]+d['Xh']@(kp-kc)
        ref=max(0.,float(np.max(np.abs(d['Wa']@(d['a_mag']-pa)))-t),float(np.max(np.abs(d['Wc']@(d['c_supported_mag']-pc)))-t))
        gv=max(0.,float(np.max(np.abs(gamma))-.02))
        if h>1e-7 or ref>1e-7 or gv>1e-7:raise ValueError(f'ENDPOINT_WITNESS_FAILURE H02={h}mag reference={ref} gamma={gv}mag')
        return {'H02_violation_mag':h,'reference_violation_units':ref,'gamma_violation_mag':gv}

    def solve(self,objective,t=None,label=''):
        if self.calls>=97:raise RuntimeError('97 LP hard cap')
        remaining=600-(time.monotonic()-self.start)
        if remaining<=0:raise RuntimeError('10 minute hard cap')
        bounds=self.bounds.copy()
        if t is not None:bounds[self.sl['t']]=(t,t)
        self.calls+=1
        status={'call':self.calls,'label':label,'t_fixed':t,'started_elapsed_s':time.monotonic()-self.start,'state':'STARTED'}
        self.raw.append(status);self.save()
        with warnings.catch_warnings(record=True) as notices:
            warnings.simplefilter('always',OptimizeWarning)
            sol=linprog(objective,A_ub=self.A,b_ub=self.b,bounds=bounds,method='highs',
                        options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9,'time_limit':remaining,'threads':2})
        status.update(status=int(sol.status),message=sol.message,state='FINITE' if sol.success else 'INFEASIBLE' if sol.status==2 else 'UNBOUNDED' if sol.status==3 else 'UNKNOWN',
                      elapsed_s=time.monotonic()-self.start,warnings=[str(w.message) for w in notices])
        if sol.success:
            status.update(objective=float(sol.fun),verification=self.verify(sol.x,float(sol.x[self.sl['t']])))
            self.witness.append(sol.x.copy());status['witness_index']=len(self.witness)-1
        self.save()
        if not sol.success:raise RuntimeError('LP_UNRESOLVED_STOP: '+json.dumps(status))
        return sol,status

    def save(self):
        (HERE/'LP_RAW.json').write_text(json.dumps({'calls_started':self.calls,'hard_cap':97,'elapsed_s':time.monotonic()-self.start,'runs':self.raw},indent=2)+'\n')


def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ['ALIAS_SKY_HOST_75','CF4_65']:raise SystemExit('explicit Astra-confirmed support rule required')
    if (HERE/'LP_RAW.json').exists():raise RuntimeError('one campaign already started; preserve prior identity and ask framer')
    start=time.monotonic();d,meta,sl=prepare(sys.argv[1]);camp=Campaign(d,sl,start)
    objective=np.zeros(d['H02_design'].shape[1]);objective[sl['t']]=1
    sol,_=camp.solve(objective,label='minimum_reference_compatibility_t');tmin=float(sol.x[sl['t']]);endpoints=[]
    target=np.vstack([d['target_zeta'],d['target_psi'][:8]])
    labels=['zeta_'+j for j in BASIS]+['psi_all_selected_'+j for j in BASIS]
    for increment in [0,1,2]:
        level=[]
        for label,objective in zip(labels,target):
            low,ls=camp.solve(objective,tmin+increment,label=f'tplus{increment}:{label}:lower')
            high,hs=camp.solve(-objective,tmin+increment,label=f'tplus{increment}:{label}:upper')
            level.append({'target':label,'lower_mag':float(low.fun),'upper_mag':float(-high.fun),'lower_call':ls['call'],'upper_call':hs['call'],'status':'FINITE'})
        endpoints.append({'reference_increment':increment,'t':tmin+increment,'projections':level})
    if camp.calls!=97:raise RuntimeError('campaign LP count mismatch')
    d['LP_endpoint_witnesses']=np.array(camp.witness)
    np.savez_compressed(HERE/'D07_DESIGN_WITNESSES.npz',**d)
    result={**meta,'minimum_compatible_reference_t':tmin,'projections':endpoints,'LP_calls':camp.calls,'elapsed_s':time.monotonic()-start,
            'input_sha256':{str(p):source.sha(p) for p in FROZEN},'source_contract_sha256':source.sha(HERE.parent/'D07_CONTRACT.md'),
            'source_head':'6219ff0923890aab487135c98db5dd0d5f6dbdf7','scientific_acceptance':'HOLD','review':'PENDING_INDEPENDENT_EXECUTION_REVIEW',
            'requested_model':'gpt-6-sol','requested_effort':'high','observed_model':'UNKNOWN','observed_effort':'UNKNOWN',
            't_interpretation':'dimensionless reference-norm compatibility sensitivity only; no noise quantile, coverage or physical remainder budget'}
    (HERE/'D07_RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'pair_rows':len(d['a_mag']),'calibrator_all':77,'calibrator_support':len(d['c_supported_mag']),'tmin':tmin,'LP_calls':camp.calls,'elapsed_s':result['elapsed_s'],'estimability':meta['estimability']}))


if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        with (HERE/'FIRST_FAILURE.txt').open('a') as f:traceback.print_exc(file=f)
        raise
