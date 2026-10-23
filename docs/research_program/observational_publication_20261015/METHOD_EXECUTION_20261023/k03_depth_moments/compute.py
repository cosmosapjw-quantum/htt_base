"""R24-K03: one new reported-redshift VSH moment pass and conditional analysis."""
import hashlib
import importlib.util
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.optimize import brentq
from scipy.stats import chi2, ncx2

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = HERE.parents[4]
INPUT = BASE / 'R24-K03-DEPTH-MOMENTS_INPUT.json'
RAW = Path('/mnt/extdrive/workdir/htt_open_data/a22_20261023/r24_depth_moments')
MOMENTS = RAW / 'new_moments.npz'
MODEL = REPO / 'docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/astrometry/model.py'
SHA_INPUT = 'b835863bfe99b25db95e7e73a62e2eaf27b78bc850b44c0579457397e6f58998'
TEMPLATE_NAMES = ('dust','stars','m10','mcs','unwise','unwisescan','mcsunwise')


def sha(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def load_contract(verify=True):
    if sha(INPUT) != SHA_INPUT: raise ValueError('task input SHA mismatch')
    inp = json.loads(INPUT.read_text())
    if inp['base_head'] != 'dfaf171c37f2636c942a99bf2b9803b57295ac14': raise ValueError('base identity drift')
    if verify:
        for entry in inp['sources']:
            path = Path(entry['path']) if Path(entry['path']).is_absolute() else REPO / entry['path']
            if path.stat().st_size != entry['bytes'] or sha(path) != entry['sha256']:
                raise ValueError(f"immutable source identity mismatch: {path}")
    return inp


def model_module():
    spec = importlib.util.spec_from_file_location('pinned_astrometry_model',MODEL)
    mod = importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def scaled_spd(a,name,threshold=1e-10):
    a = np.asarray(a,dtype=float)
    if not np.isfinite(a).all() or np.max(np.abs(a-a.T)) > 1e-10*max(1,np.max(np.abs(a))):
        raise ArithmeticError(f'{name}: nonfinite or asymmetric')
    a = (a+a.T)/2
    d = np.sqrt(np.diag(a))
    if not np.isfinite(d).all() or np.any(d<=0): raise ArithmeticError(f'{name}: invalid diagonal')
    vals,vecs = np.linalg.eigh(a/d[:,None]/d[None,:])
    if vals[0] <= threshold*vals[-1] or vals[-1]/vals[0] > 1e10:
        raise ArithmeticError(f'{name}: scaled rank/condition unresolved {vals[0]} {vals[-1]}')
    return {'matrix':a,'scale':d,'scaled_eigenvalues':vals,'scaled_condition':float(vals[-1]/vals[0])}


def solve_checked(a,rhs,name):
    info=scaled_spd(a,name)
    out=np.linalg.solve(info['matrix'],rhs)
    residual=np.linalg.norm(info['matrix']@out-rhs,ord=np.inf)/max(1.,np.linalg.norm(rhs,ord=np.inf))
    if residual > 1e-10:raise ArithmeticError(f'{name}: scaled residual {residual}')
    return out,info,float(residual)


def new_moments(a,receipt,model,chunk=4096,limit_mib=768):
    if chunk>4096 or chunk<1: raise ValueError('chunk limit')
    reference=tuple(np.asarray(receipt[k],dtype=float) for k in ('reference_center','reference_scale','vector_column_RMS'))
    n=len(a['source_id']); A=np.zeros((6,6));K=np.zeros((6,102));q=np.zeros(6)
    zcounts=np.zeros(3,dtype=int); peak=0
    for start in range(0,n,chunk):
        sl=slice(start,min(start+chunk,n));ra=a['ra'][sl];dec=a['dec'][sl];z=a['redshift_quaia'][sl]
        temp=np.column_stack([a['template_'+name][sl] for name in TEMPLATE_NAMES])
        x,bins=model.design(ra,dec,z,temp,reference)
        if x.shape!=(len(ra),2,102):raise ValueError('pinned design shape mismatch')
        h=model.dipole(ra,dec)*(z/(1+z))[:,None,None]
        y=np.column_stack([a['pmra_uasyr'][sl],a['pmdec_uasyr'][sl]])
        sa=a['pmra_error_uasyr'][sl];sd=a['pmdec_error_uasyr'][sl];rho=a['gaia_pmra_pmdec_corr'][sl]
        wx,wy=model.whiten(x,y,sa,sd,rho)
        wh,_=model.whiten(h,y,sa,sd,rho)
        A+=wh.T@wh;K+=wh.T@wx;q+=wh.T@wy
        zcounts+=np.bincount(bins,minlength=3)
        peak=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        if peak>limit_mib:raise MemoryError(f'peak RSS {peak:.3f} MiB exceeds {limit_mib}')
    return A,K,q,zcounts,peak


def fit(G,b,A,K,q):
    B,gi,gres=solve_checked(G,K.T,'G_to_K')
    gb,_,_=solve_checked(G,b,'G_to_b')
    F=(A-K@B);F=(F+F.T)/2
    s=q-K@gb
    theta,fi,fres=solve_checked(F,s,'F_to_s')
    Ctheta,_,_=solve_checked(F,np.eye(6),'F_inverse')
    Cg,_,_=solve_checked(G,np.eye(102),'G_inverse')
    old=gb-B@theta
    oldnew=-B@Ctheta
    oldcov=Cg+B@Ctheta@B.T
    fullcov=np.block([[oldcov[:18,:18],oldnew[:18,:]],[oldnew[:18,:].T,Ctheta]])
    fullstate=np.r_[old[:18],theta]
    c=np.asarray([1/4,7/12,26/33])
    T=np.zeros((18,24))
    for i in range(3):T[6*i:6*i+6,6*i:6*i+6]=np.eye(6);T[6*i:6*i+6,18:24]=c[i]*np.eye(6)
    Y=T@fullstate;CY=T@fullcov@T.T
    D=np.zeros((18,18));D[:6,:6]=np.eye(6);D[6:12,6:12]=np.eye(6);D[6:12,:6]=-np.eye(6);D[12:18,12:18]=np.eye(6);D[12:18,6:12]=-np.eye(6)
    vals,vecs=np.linalg.eigh(F)
    crit=chi2.isf(.05,6)
    target_nc=brentq(lambda v:ncx2.sf(crit,6,v)-.8,0,1e6)
    power=[{'amplitude_uasyr':a,'strong':float(ncx2.sf(crit,6,a*a*vals[-1])),
            'weak':float(ncx2.sf(crit,6,a*a*vals[0])),
            'lambda_strong':float(a*a*vals[-1]),'lambda_weak':float(a*a*vals[0])} for a in (.1,1,10,100)]
    return {'theta_uasyr':theta.tolist(),'theta_cov_uasyr2':Ctheta.tolist(),
            'F':F.tolist(),'s':s.tolist(),'F_eigenvalues':vals.tolist(),'F_eigenvectors_columns':vecs.tolist(),
            'A_eigenvalues':np.linalg.eigvalsh(A).tolist(),
            'information_trace_retained_fraction':float(np.trace(F)/np.trace(A)),
            'information_trace_loss_fraction':float(1-np.trace(F)/np.trace(A)),
            'information_logdet_loss':float(np.linalg.slogdet(A)[1]-np.linalg.slogdet(F)[1]),
            'score_chi2_6_scenario':float(s@theta),'score_level_005_critical':float(crit),
            'score_level_005_exceeds':bool(s@theta>crit),
            'power_sphere':power,'power80_target_noncentrality':float(target_nc),
            'power80_amplitude_strong_uasyr':float(np.sqrt(target_nc/vals[-1])),
            'power80_amplitude_weak_uasyr':float(np.sqrt(target_nc/vals[0])),
            'full24_state_uasyr':fullstate.tolist(),'full24_cov_uasyr2':fullcov.tolist(),
            'Y18_state_uasyr':Y.tolist(),'Y18_cov_uasyr2':CY.tolist(),
            'anchored_difference18_state_uasyr':(D@Y).tolist(),
            'anchored_difference18_cov_uasyr2':(D@CY@D.T).tolist(),
            'depth_c_reported_z_centers':c.tolist(),
            'checks':{'G_scaled_condition':gi['scaled_condition'],'F_scaled_condition':fi['scaled_condition'],
                      'G_scaled_min_eigenvalue':float(gi['scaled_eigenvalues'][0]),
                      'F_scaled_min_eigenvalue':float(fi['scaled_eigenvalues'][0]),
                      'G_solve_residual':gres,'F_solve_residual':fres,
                      'F_min_eigenvalue':float(vals[0]),'A_minus_F_min_eigenvalue':float(np.linalg.eigvalsh((A-F+A.T-F.T)/2)[0])}}


def main():
    inp=load_contract(); model=model_module()
    if os.environ.get('OPENBLAS_NUM_THREADS')!='1':raise RuntimeError('OPENBLAS_NUM_THREADS must be 1')
    stats=Path(inp['sources'][1]['path']);receipt=json.loads(Path(inp['sources'][2]['path']).read_text())
    with np.load(stats,allow_pickle=False) as f:G=f['G'];b=f['b'];nstat=int(f['n']);zc=f['zcounts']
    with np.load(inp['sources'][0]['path'],allow_pickle=False) as f:a={k:f[k] for k in ['source_id','ra','dec','redshift_quaia','pmra_uasyr','pmdec_uasyr','pmra_error_uasyr','pmdec_error_uasyr','gaia_pmra_pmdec_corr']+[f'template_{n}' for n in TEMPLATE_NAMES]}
    if len(a['source_id'])!=755850 or nstat!=755850:raise ValueError('row count mismatch')
    started=time.time()
    A,K,q,zcounts,peak=new_moments(a,receipt,model)
    if not np.array_equal(zcounts,zc):raise ValueError('bin count mismatch')
    if time.time()-started>1800:raise TimeoutError('pass wall time exceeded')
    RAW.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(MOMENTS,A=A,K=K,q=q,zcounts=zcounts,n=len(a['source_id']))
    result=fit(G,b,A,K,q)
    result.update({'task_id':'R24-K03-DEPTH-MOMENTS','scope':'conditional reported-z independent-row Gaussian working experiment',
      'units':'microarcsec/year','coordinates':'ICRS E1 polar xyz then B1 axial xyz, three old reported-z bins, then six g(z) slopes',
      'g':'z/(1+z)','rows':len(a['source_id']),'zcounts':zcounts.tolist(),
      'moment_pass_seconds':time.time()-started,'peak_rss_mib':peak,
      'original_acceptance':'HOLD','physical_status':'HOLD: centroid/matter response, true-depth law, spatial covariance, selection, and history unqualified',
      'score_interpretation':'conditional Gaussian working-model scenario; not empirical p-value or physical exclusion',
      'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'executable':sys.executable}})
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(7,4.5));p=result['power_sphere'];ax.semilogx([r['amplitude_uasyr'] for r in p],[r['strong'] for r in p],'o-',label='strong F eigenvector');ax.semilogx([r['amplitude_uasyr'] for r in p],[r['weak'] for r in p],'o-',label='weak F eigenvector');ax.axhline(.8,color='gray',ls=':');ax.set(xlabel='Slope amplitude (microarcsec/year)',ylabel='Level 0.05 Wald power',ylim=(0,1),title='Conditional reported-z VSH slope sensitivity');ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(HERE/'POWER.png',dpi=170);plt.close(fig)
    print(json.dumps({'moment_sha256':sha(MOMENTS),'rows':len(a['source_id']),'seconds':result['moment_pass_seconds'],'peak_rss_mib':peak,'F_eigenvalues':result['F_eigenvalues'],'power80_strong_weak':[result['power80_amplitude_strong_uasyr'],result['power80_amplitude_weak_uasyr']]}))


if __name__=='__main__':main()
