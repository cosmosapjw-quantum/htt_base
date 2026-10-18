#!/usr/bin/env python3
"""Fixed Gaia estimator sensitivity to a declared PSD angular Gaussian family.

Numerical dependencies: NumPy; optional Matplotlib for plots. No fit or data query.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np

NAMES = ['spin_x','spin_y','spin_z','glide_x','glide_y','glide_z']
HALF_ANGLES = [1.,5.,20.,90.]
RHOS = [0.,.01,.05,.2,.5,1.]
ROOT = Path(__file__).resolve().parents[1]
INPUT = 'docs/observational_reboot_20261014/results/gaia_bias_sensitivity_v1/influence_blocks.npz'
ROWS = 'docs/observational_reboot_20261014/results/gaia_frame_v1/qualified_rows.npz'
BASELINE = 'docs/observational_reboot_20261014/results/gaia_bias_sensitivity_v1/result.json'
EXPECTED = {INPUT:'d5384f57138f4e8ea7b986153bf0133f846e9f7806bdf82b2cb7ac4d6a676c9f',ROWS:'41b6ddcb13131b49b97efd6107816af4518fa9e23725cf3b4272c2f3a70acb8f',BASELINE:'7af1f6b3508826b69f7170891146536398104779962de76d9d4355c8b9e4415d'}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def real(value, name):
    if np.iscomplexobj(value):
        raise ValueError(f'{name} must be real')
    a=np.asarray(value,dtype=float)
    if not np.isfinite(a).all():
        raise ValueError(f'{name} must be finite')
    return a


def scalar(value, name, low, high, strict_low=False):
    a=real(value,name)
    if a.ndim or a>high or (a<=low if strict_low else a<low):
        raise ValueError(f'{name} outside declared domain')
    return float(a)


def sky_frame(ra_deg,dec_deg):
    """ICRS unit directions and (mu_alpha*cos delta, mu_delta) tangent rows."""
    ra=real(ra_deg,'ra');dec=real(dec_deg,'dec')
    if ra.ndim!=1 or dec.shape!=ra.shape or np.any((ra<0)|(ra>=360)) or np.any(np.abs(dec)>90):
        raise ValueError('aligned ICRS RA [0,360), Dec [-90,90] degrees required')
    a,d=np.deg2rad(ra),np.deg2rad(dec)
    n=np.column_stack((np.cos(d)*np.cos(a),np.cos(d)*np.sin(a),np.sin(d)))
    east=np.column_stack((-np.sin(a),np.cos(a),np.zeros(len(a))))
    north=np.column_stack((-np.sin(d)*np.cos(a),-np.sin(d)*np.sin(a),np.cos(d)))
    return n,np.stack((east,north),axis=1)


def principal_root(covariance):
    c=real(covariance,'source covariance')
    if c.ndim!=3 or c.shape[1:]!=(2,2) or not np.allclose(c,c.transpose(0,2,1),rtol=1e-12,atol=0):
        raise ValueError('symmetric source covariance (N,2,2) required')
    w,u=np.linalg.eigh(c)
    if np.any(w<=0):
        raise ValueError('source covariance must be positive definite; no floor applied')
    return np.einsum('nia,na,nja->nij',u,np.sqrt(w),u)


def kernel_block(nleft,nright,half_angle_deg):
    angle=scalar(half_angle_deg,'half-angle',0.,180.,strict_low=True)
    x=real(nleft,'directions');y=real(nright,'directions')
    if x.ndim!=2 or y.ndim!=2 or x.shape[1]!=3 or y.shape[1]!=3:
        raise ValueError('Cartesian direction arrays required')
    # Direct squared chord distances avoid cancellation at coincident sky points.
    distance=np.zeros((len(x),len(y)))
    for a in range(3):
        delta=x[:,a,None]-y[None,:,a]
        distance+=delta*delta
    # 2(1-cos theta_half)=4 sin²(theta_half/2); stable at small angles.
    denominator=4*math.sin(math.radians(angle)/2)**2
    distance*= -math.log(2)/denominator
    np.exp(distance,out=distance)
    return distance


def latent_response(m,covariance,tangent):
    m=real(m,'M');e=real(tangent,'tangent frame')
    s=principal_root(covariance)
    if m.ndim!=3 or m.shape[0]!=6 or m.shape[2]!=2 or e.shape!=(m.shape[1],2,3) or len(s)!=m.shape[1]:
        raise ValueError('aligned M (6,N,2), covariance, tangent (N,2,3) required')
    if not np.allclose(np.einsum('nia,nja->nij',e,e),np.eye(2)[None],rtol=1e-12,atol=1e-12):
        raise ValueError('tangent rows must be orthonormal')
    a=np.einsum('nij,nja->nia',s,e)
    h=np.einsum('pni,nia->npa',m,a)
    independent=np.einsum('npa,nqa->pq',h,h)
    return h,independent,a


def correlated_coefficient_covariance(n,h,half_angle_deg,block_size=256):
    n=real(n,'sky directions');h=real(h,'latent response')
    if n.shape!=(len(h),3) or h.shape[1:]!=(6,3):
        raise ValueError('aligned sky (N,3) and response (N,6,3) required')
    if not isinstance(block_size,(int,np.integer)) or isinstance(block_size,bool) or not 1<=block_size<=4096:
        raise ValueError('block size integer [1,4096] required')
    if not np.allclose(np.sum(n*n,axis=1),1,rtol=1e-12,atol=1e-12):
        raise ValueError('unit sphere directions required')
    v=np.zeros((6,6));flat=h.reshape(len(h),18)
    for i in range(0,len(n),block_size):
        stop=min(i+block_size,len(n))
        k=kernel_block(n[i:stop],n,half_angle_deg)
        action=(k@flat).reshape(stop-i,6,3)
        v+=np.einsum('npa,nqa->pq',h[i:stop],action)
    return (v+v.T)/2


def mixed_covariance(independent,correlated,rho):
    r=scalar(rho,'rho covariance fraction',0.,1.)
    return (1-r)*independent+r*correlated


def dense_fixture(n,a,m,half_angle_deg,rho):
    """Independent dense Kronecker/congruence assembly, used only on small fixtures."""
    r=scalar(rho,'rho covariance fraction',0.,1.)
    count=len(n)
    if count>64:
        raise ValueError('dense fixture restricted to at most 64 sources')
    block_map=np.zeros((2*count,3*count))
    block_c=np.zeros((2*count,2*count))
    for i in range(count):
        block_map[2*i:2*i+2,3*i:3*i+3]=a[i]
        block_c[2*i:2*i+2,2*i:2*i+2]=a[i]@a[i].T
    # Explicit pairwise Euclidean differences, separate from block kernel utility.
    d2=np.sum((n[:,None,:]-n[None,:,:])**2,axis=2)
    k=np.exp(-math.log(2)*d2/(4*math.sin(math.radians(half_angle_deg)/2)**2))
    source=(1-r)*block_c+r*block_map@np.kron(k,np.eye(3))@block_map.T
    flat=m.reshape(6,2*count)
    return flat@source@flat.T,source


def checks_fixture():
    rng=np.random.default_rng(20261014)
    n,e=sky_frame([0,1e-5,180,90,270,45,200,359],[0,0,0,90,-90,42,-35,12])
    raw=rng.normal(size=(8,2,2));c=raw@raw.transpose(0,2,1)+.3*np.eye(2)
    m=rng.normal(size=(6,8,2));h,v0,a=latent_response(m,c,e)
    errors=[];eigen=[];marginal=[]
    for angle in HALF_ANGLES:
        correlated=correlated_coefficient_covariance(n,h,angle,3)
        for rho in RHOS:
            dense,full=dense_fixture(n,a,m,angle,rho)
            errors.append(float(np.linalg.norm(mixed_covariance(v0,correlated,rho)-dense)/np.linalg.norm(dense)))
            eigen.append(float(np.linalg.eigvalsh(full).min()))
            marginal.append(float(max(np.linalg.norm(full[2*i:2*i+2,2*i:2*i+2]-c[i])/np.linalg.norm(c[i]) for i in range(8))))
    # Independent local tangent changes must transform covariance and M together.
    angles=rng.uniform(-np.pi,np.pi,8);r=np.empty((8,2,2))
    r[:,0,0]=r[:,1,1]=np.cos(angles);r[:,0,1]=-np.sin(angles);r[:,1,0]=np.sin(angles)
    er=r@e;cr=r@c@r.transpose(0,2,1)
    mr=np.einsum('pni,nji->pnj',m,r)
    hr,vr,_=latent_response(mr,cr,er)
    # Global Cartesian rotations preserve pair distances and latent contractions.
    q,_=np.linalg.qr(rng.normal(size=(3,3)))
    c0=correlated_coefficient_covariance(n,h,20,3)
    local=correlated_coefficient_covariance(n,hr,20,5)
    global_v=correlated_coefficient_covariance(n@q,h@q,20,4)
    result={'fixture_source_count':8,'dense_relative_error_max':max(errors),'source_covariance_eigenvalue_min':min(eigen),'marginal_relative_error_max':max(marginal),'local_tangent_rotation_relative_error':float(np.linalg.norm(c0-local)/np.linalg.norm(c0)),'global_cartesian_rotation_relative_error':float(np.linalg.norm(c0-global_v)/np.linalg.norm(c0)),'block_partition_relative_error':float(np.linalg.norm(c0-correlated_coefficient_covariance(n,h,20,8))/np.linalg.norm(c0))}
    if max(result[k] for k in result if k.endswith('error') or k.endswith('error_max'))>1e-11 or min(eigen)<-1e-11:
        raise AssertionError(f'fixture checks failed: {result}')
    return result


def make_plot(out,result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for angle in HALF_ANGLES:
        rows=[r for r in result['grid'] if r['half_correlation_angle_deg']==angle]
        x=[r['rho'] for r in rows]
        axes[0].plot(x,[r['largest_directional_sigma_ratio'] for r in rows],'o-',label=f'{angle:g}° half correlation')
        axes[1].plot(x,[r['smallest_directional_sigma_ratio'] for r in rows],'o-')
    for ax in axes:
        ax.set(xlabel='Declared correlated marginal fraction rho',ylabel='Directional sigma / independent baseline')
        ax.axhline(1,color='black',linewidth=.6);ax.grid(alpha=.25)
    axes[0].set_title('Largest directional change');axes[1].set_title('Smallest directional change')
    axes[0].legend(fontsize=8)
    fig.text(.5,.015,'HTT | DESCRIPTIVE_CONDITIONAL | declared PSD family, fixed selected cohort and estimator | empirical covariance unavailable',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.04,1,1))
    for ext in ['png','svg']:fig.savefig(out/f'angular_correlation_sensitivity.{ext}',dpi=180)
    plt.close(fig)


def run(args):
    start=time.monotonic();root=Path(args.repo_root)
    hashes={p:sha256(root/p) for p in EXPECTED}
    if hashes!=EXPECTED:
        raise ValueError(f'immutable input identity mismatch: {hashes}')
    with np.load(root/INPUT,allow_pickle=False) as d:
        ids,m,saved_v=d['source_id'],d['M'],d['covariance']
    with np.load(root/ROWS,allow_pickle=False) as d:
        if not np.array_equal(ids,d['source_id']) or len(ids)!=4756 or len(np.unique(ids))!=len(ids):
            raise ValueError('frozen 4756-row identity/alignment mismatch')
        c,ra,dec,y=d['covariance'],d['ra'],d['dec'],d['proper_motion']
    baseline=json.loads((root/BASELINE).read_text())
    if baseline['coefficient_order']!=NAMES:
        raise ValueError('coefficient order differs')
    coeff=real(baseline['coefficients_mas_year'],'baseline coefficients')
    if baseline['units']!='coefficients/supports mas/year internally; displayed widths microas/year' or coeff.shape!=(6,):
        raise ValueError('baseline units/coefficient shape differs')
    n,e=sky_frame(ra,dec);h,v0,a=latent_response(m,c,e)
    parity=float(np.linalg.norm(v0-saved_v)/np.linalg.norm(saved_v))
    coeff_parity=float(np.max(np.abs(np.einsum('pni,ni->p',m,y)-coeff)))
    if parity>1e-10 or coeff_parity>1e-12:
        raise AssertionError('saved covariance or coefficient parity failed')
    checks=checks_fixture();checks.update({'baseline_covariance_relative_error':parity,'baseline_coefficient_max_abs_mas_year':coeff_parity})
    root0=np.linalg.cholesky(v0);invroot=np.linalg.solve(root0,np.eye(6))
    q=math.sqrt(12.591587243743977) # chi2(df=6) 95% quantile
    grid=[];correlated=[]
    for angle in HALF_ANGLES:
        t=time.monotonic();vc=correlated_coefficient_covariance(n,h,angle,args.block_size)
        correlated.append({'half_correlation_angle_deg':angle,'covariance_mas2_year2':vc.tolist(),'elapsed_seconds':time.monotonic()-t})
        for rho in RHOS:
            v=mixed_covariance(v0,vc,rho)
            eig=np.linalg.eigvalsh(v)
            if eig.min()<=0:
                raise AssertionError('nonpositive coefficient covariance; no floor applied')
            w=np.linalg.eigvalsh(invroot@v@invroot.T)
            distance=float(np.sqrt(coeff@np.linalg.solve(v,coeff)))
            grid.append({'half_correlation_angle_deg':angle,'rho':rho,'covariance_mas2_year2':v.tolist(),'component_sigma_microas_year':(1000*np.sqrt(np.diag(v))).tolist(),'joint_95_projection_halfwidth_microas_year':(q*1000*np.sqrt(np.diag(v))).tolist(),'smallest_directional_sigma_ratio':float(np.sqrt(w[0])),'largest_directional_sigma_ratio':float(np.sqrt(w[-1])),'six_dimensional_region_volume_ratio':float(np.exp(.5*(np.linalg.slogdet(v)[1]-np.linalg.slogdet(v0)[1]))),'coefficient_mahalanobis_distance':distance,'zero_in_joint_95_region':distance<=q})
        print(f'half-angle {angle:g} deg completed',flush=True)
    # One real-data small fixture validates the saved layout as well as synthetic case.
    ix=np.arange(0,len(ids),len(ids)//12)[:12]
    dense,_=dense_fixture(n[ix],a[ix],m[:,ix],20,.2)
    hs,vs,_=latent_response(m[:,ix],c[ix],e[ix])
    block=mixed_covariance(vs,correlated_coefficient_covariance(n[ix],hs,20,5),.2)
    actual_fixture=float(np.linalg.norm(block-dense)/np.linalg.norm(dense))
    checks['real_data_dense_fixture_relative_error']=actual_fixture
    if actual_fixture>1e-11:raise AssertionError('real-data dense parity failed')
    result={'schema':'htt.gaia-angular-correlation-sensitivity/1','owner':'HTT','scope':'fixed selected Gaia EDR3 cohort and saved linear estimator; declared correlation-family sensitivity','claim_tier':'DESCRIPTIVE_CONDITIONAL','transfer_source':'NOT_APPLICABLE','source_commit':args.source_commit,'runtime':{'requested_model':'gpt-6.1-sol','requested_effort':'high','observed_model':'UNKNOWN','observed_effort':'UNKNOWN'},'source_sha256':hashes,'cohort_count':len(ids),'coefficient_order':NAMES,'coefficients_mas_year':coeff.tolist(),'units':'source and coefficient covariance mas^2/year^2; displayed widths microas/year; kernel dimensionless','tangent_convention':'ICRS east=mu_alpha*cos(delta), north=mu_delta; principal symmetric covariance square root','kernel':'k=exp[-ln(2)*||n_i-n_j||^2/(4 sin^2(theta_half/2))]','covariance_family':'Cij=(1-rho)*deltaij*Ci + rho*kij*Si*Ei*Ej^T*Sj; Si=principal sqrt(Ci), Ei=2x3 tangent rows','rho_meaning':'fraction of every source marginal covariance assigned to correlated component; sqrt(rho) latent amplitude, not universal pair correlation','half_angle_meaning':'angular separation where scalar latent kernel equals one half; tangent/coloring factors change observed cross correlation','grid_status':'fixed declared sensitivity grid; not empirical fit','half_angle_grid_deg':HALF_ANGLES,'rho_grid':RHOS,'estimator':'saved M unchanged; compute M C M^T, no GLS refit','sky_support_status':'fixed outcome-selected 4756-row cohort, directions treated exact','null_mock_status':'algebraic dense fixtures only; empirical Gaia joint law unavailable','joint_region_radius_95':q,'numerical_checks':checks,'fully_correlated_covariances':correlated,'grid':grid,'execution':{'block_size':args.block_size,'elapsed_seconds':time.monotonic()-start,'maximum_kernel_block_entries':min(args.block_size,len(ids))*len(ids),'full_2N_covariance_materialized':False},'caveats':['This is an assumed covariance family; the actual Gaia cross-source law and amplitude are unmeasured.','Keeping each marginal covariance fixed redistributes variance; directional widths can shrink or grow and need not be monotone relative to independence.','The coefficient center uses the original estimator; correlation-sensitive optimal estimation is not evaluated.','Conditioning on the outcome-selected upstream cohort does not remove selection bias.','No empirical p-value, physical Gaia coverage, native solver or Bianchi family identification follows.'],'reference':'https://gaussianprocess.org/gpml/chapters/RW4.pdf; squared exponential covariance section 4.2.1'}
    result['gaussian_reference_mean_law']='beta_hat - beta_ref ~ N(0,V), beta_ref=M E[y], conditional on fixed design and the declared covariance; physical-coefficient coverage additionally requires zero or separately bounded deterministic bias'
    out=Path(args.output)
    if out.exists():raise ValueError('output exists; preserve historical output')
    out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if not args.no_plots:make_plot(out,result)
    return result


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source-commit',default='2fb4ae497eecc6d5fd73f931f250c763ee6d266d')
    p.add_argument('--block-size',type=int,default=256)
    p.add_argument('--no-plots',action='store_true')
    return p


if __name__=='__main__':
    result=run(parser().parse_args())
    print(json.dumps({'checks':result['numerical_checks'],'elapsed_seconds':result['execution']['elapsed_seconds']},indent=2))
