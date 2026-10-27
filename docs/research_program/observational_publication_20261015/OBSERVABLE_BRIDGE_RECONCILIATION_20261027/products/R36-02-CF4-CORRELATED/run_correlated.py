"""Conditional CF4 H03 covariance for a fixed source catalogue and linear estimator.

The EH98 common-field modes are a declared approximation. This module does not
interpret the H03 working variance as independent measurement noise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from scipy.special import spherical_jn

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
EXTERNAL = Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual')
R30 = REPO / 'docs/research_program/observational_publication_20261015/EXTERNAL_AUDIT_20261025_R35/CF4_FINITE_COMPONENT/sources/r30_cf4_pv_tensor_numeric/fast_window_fixture_repair'
sys.path.insert(0, str(R30))
sys.path.insert(0, str(EXTERNAL/'deps'))
import science as old  # reviewed R30 scalar and positive-quadrature definitions
import finufft

SOURCE = REPO/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz'
OPERATOR = Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_exact_operator_actual/A_RAW_36x35970.npz')
BRIDGE_DIR = REPO/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/covariance'
sys.path.insert(0, str(BRIDGE_DIR))
from covariance_bridge import gls_svd, transport_covariance

SHA_SOURCE = '86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
SHA_OPERATOR = 'e835df014bf0eb96fd715994c823eec9c8449f98d3f132b1dc736b760fd2772e'
PACKET = '0c0fab5631cb19001cba35e3da1de5cd44d64dc0157950afb82d383496472c40'
INPUT = 'sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43'
STAGES = [('A',35,16),('B',53,16),('C',53,32)]
RADII = np.array([5.,10.,20.]) / old.H


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def require(ok, label):
    if not bool(ok): raise AssertionError(label)


def write_json(path, obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def quadrature_inventory(stages):
    targets=[]; indices={}; maps={}
    for name,order,radial in stages:
        _,_,directions,weights=old.angular_rule(order)
        bands=[]
        for lo,hi in old.BANDS:
            k,wk=old.cc_rule(radial,lo,hi)
            ind=np.empty((len(k),len(directions)),np.int64)
            for ik,kv in enumerate(k):
                for iu,u in enumerate(directions):
                    key=(float(kv).hex(),*(float(v).hex() for v in u))
                    if key not in indices:
                        indices[key]=len(targets);targets.append((kv,*u))
                    ind[ik,iu]=indices[key]
            bands.append(dict(k=k,wk=wk,u=directions,wu=weights/(4*math.pi),indices=ind))
        maps[name]=bands
    return np.asarray(targets,float),maps


def direct_modes(targets,positions,n,g,A):
    out=np.empty((len(targets),A.shape[0]),complex)
    for i,(k,*u) in enumerate(targets):
        u=np.asarray(u)
        source=g*(n@u)*np.exp(1j*k*(positions@u))
        out[i]=A@source
    return out


def finufft_modes(targets,positions,n,g,A,eps):
    # A*g*n has 36*3 source fields; u contracts the resulting three axes.
    xmax=np.max(np.abs(positions),axis=0)
    scale=np.array([2.**max(0,math.ceil(math.log2(v/(math.pi/2)))) for v in xmax])
    scaled=np.ascontiguousarray((positions/scale).T)
    frequency=np.ascontiguousarray((targets[:,1:]*targets[:,:1]*scale).T)
    coeff=np.ascontiguousarray((A[:,:,None]*(g[:,None]*n)[None,:,:]).transpose(0,2,1).reshape(108,-1),complex)
    plan=finufft.Plan(3,3,n_trans=108,eps=eps,isign=1,dtype='complex128',nthreads=1,
                      upsampfac=2.0,maxbatchsize=1,fftw=64)
    plan.setpts(*(np.ascontiguousarray(v) for v in scaled),
                *(np.ascontiguousarray(v) for v in frequency))
    field=np.asarray(plan.execute(coeff)).reshape(36,3,len(targets))
    return np.einsum('adt,td->ta',field,targets[:,1:]),scale


def pair_kernel_fixture(amp):
    # Independent integral on a deliberately smooth fixture with duplicate x.
    n=np.array([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.],[-1.,0.,0.],
                [1/math.sqrt(2),1/math.sqrt(2),0.],[1.,0.,0.]])
    x=np.array([[3.,0.,0.],[0.,4.,0.],[0.,0.,5.],[-6.,0.,0.],
                [2.,2.,0.],[3.,0.,0.]])
    g=np.array([60.,61.,59.,62.,58.,60.])
    A=np.array([[.3,-.2,.1,.15,-.1,.05],[-.08,.2,.13,-.17,.09,.07]])
    target,maps=quadrature_inventory([('F',53,32)])
    w=direct_modes(target,x,n,g,A)
    actual=cov_from_modes(maps['F'],w,amp,one_radius=True)[0]
    expected=[]
    for lo,hi in old.BANDS:
        pair=np.zeros((6,6))
        for i in range(6):
            for j in range(6):
                sep=x[i]-x[j];radius=np.linalg.norm(sep);ndot=n[i]@n[j]
                if radius: factor=(n[i]@sep)*(n[j]@sep)/radius**2
                else:factor=0.
                def integrand(k):
                    t=k*radius
                    J=((spherical_jn(0,t)+spherical_jn(2,t))*ndot/3-
                       spherical_jn(2,t)*factor)
                    return old.power(k,amp)*J/(2*math.pi**2)
                pair[i,j]=g[i]*g[j]*quad(integrand,lo,hi,epsrel=1e-11)[0]
        expected.append(A@pair@A.T)
    rel=[];entry=[]
    for c,e in zip(actual,expected):
        rel.append(float(np.linalg.norm(c-e)/np.linalg.norm(e)))
        norm=np.sqrt(np.outer(np.diag(e),np.diag(e)))
        entry.append(float(np.max(np.abs(c-e)/norm)))
    require(max(rel)<=1e-5 and max(entry)<=1e-6,'independent pair-kernel fixture')
    return {'relative_frobenius':rel,'max_normalized_entry':entry,
            'duplicate_position':True,'source_rows':6}


def cov_from_modes(bands,modes,amp,one_radius=False):
    radii=np.array([0.]) if one_radius else RADII
    outputs=[];factors=[]
    for band in bands:
        p=modes.shape[1]; parts=[]
        for ik,k in enumerate(band['k']):
            w=modes[band['indices'][ik]]
            smooth=np.exp(-.5*(k*radii)**2)
            scale=np.sqrt(band['wk'][ik]*old.power(k,amp)*band['wu']/(2*math.pi**2))
            block=np.einsum('r,ta,t->rat',smooth,w,scale).reshape(len(radii)*p,-1)
            parts.extend([block.real,block.imag])
        F=np.concatenate(parts,axis=1)
        C=F@F.T
        outputs.append((C+C.T)/2);factors.append(F)
    return outputs,factors


def diagnostics(C):
    v=np.linalg.eigvalsh(C);tr=float(np.trace(C))
    require(tr>0 and v[0]>=-1e-12*tr,'PSD covariance')
    return {'trace':tr,'min_eigenvalue':float(v[0]),'max_eigenvalue':float(v[-1]),
            'rank_1e_12':int(np.sum(v>1e-12*v[-1])),
            'rank_1e_10':int(np.sum(v>1e-10*v[-1])),
            'rank_1e_8':int(np.sum(v>1e-8*v[-1]))}


def compare(early,late):
    rows=[];passes=[]
    for a,b in zip(early,late):
        d=np.sqrt(np.diag(b)); diff=b-a
        rel=float(np.linalg.norm(diff)/np.linalg.norm(b))
        entry=float(np.max(abs(diff)/np.outer(d,d)))
        spectral=[]
        for r in range(3):
            sl=slice(36*r,36*(r+1));block=b[sl,sl];delta=diff[sl,sl]
            ev,U=np.linalg.eigh(block);keep=ev>1e-10*ev[-1]
            W=(U[:,keep]/np.sqrt(ev[keep]))@U[:,keep].T
            spectral.append(float(np.linalg.norm(W@delta@W,2)))
        passes.append(entry<=.005 and rel<=.003 and max(spectral)<=.02)
        rows.append({'max_normalized_entry':entry,'frobenius_relative':rel,
                     'whitened_spectral_each_radius':spectral,'pass':passes[-1]})
    return rows,all(passes)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pilot',action='store_true');args=ap.parse_args()
    start=time.monotonic();EXTERNAL.mkdir(parents=True,exist_ok=True);HERE.mkdir(parents=True,exist_ok=True)
    require(sha(SOURCE)==SHA_SOURCE and sha(OPERATOR)==SHA_OPERATOR,'immutable source/operator')
    with np.load(SOURCE,allow_pickle=False) as z:
        data={k:z[k] for k in ['z_CMB','dmzp','e_dmzp','n_J2000','method_family','group_id']}
    with np.load(OPERATOR,allow_pickle=False) as z:
        A=z['A_raw'];ids=z['group_id'];theta=z['theta36'];baseline=z['covariance36'];sigma=z['sigma']
    require(A.shape==(36,35970) and np.array_equal(ids,data['group_id']),'source order')
    chi,g,*_=old.background(data['z_CMB'],64)
    chi32,g32,*_=old.background(data['z_CMB'],32)
    bgerr=float(max(np.max(abs(chi-chi32)/chi),np.max(abs(g-g32)/abs(g))))
    require(bgerr<=1e-9,'background 32/64')
    x=chi[:,None]*data['n_J2000'];n=data['n_J2000']
    amp,norm=old.power_amplitude()
    fixture=pair_kernel_fixture(amp)
    if args.pilot:
        targets,maps=quadrature_inventory(STAGES)
        probe=np.vstack([targets[:24],targets[len(targets)//2:len(targets)//2+24]])
        t=time.monotonic();nu,scale=finufft_modes(probe,x,n,g,A,1e-12)
        d=direct_modes(probe,x,n,g,A)
        err=float(np.max(abs(nu-d))/max(np.max(abs(d)),1e-20))
        require(err<1e-6,'pilot nufft/direct')
        write_json(EXTERNAL/'PILOT.json',{'target_count_full':len(targets),'pilot_target_count':len(probe),
            'pilot_seconds':time.monotonic()-t,'total_seconds':time.monotonic()-start,
            'relative_max_nufft_direct':err,'pair_fixture':fixture,'bgerr':bgerr,
            'scales':scale.tolist(),'stages':STAGES,'source_rows':len(g)})
        return
    targets,maps=quadrature_inventory(STAGES)
    np.savez_compressed(EXTERNAL/'TARGET_INVENTORY.npz',target=targets,
        **{f'{name}{b}':v['indices'] for name,grp in maps.items() for b,v in enumerate(grp)})
    t=time.monotonic();modes,scale=finufft_modes(targets,x,n,g,A,1e-12)
    transform_seconds=time.monotonic()-t
    probe=targets[[0,1,2,len(targets)//3,len(targets)//2,len(targets)-1]]
    direct=direct_modes(probe,x,n,g,A)
    lookup={tuple(v):i for i,v in enumerate(targets)}
    picked=np.array([modes[lookup[tuple(v)]] for v in probe])
    direct_error=float(np.max(abs(picked-direct))/max(np.max(abs(direct)),1e-20))
    require(direct_error<1e-6,'actual subset nufft/direct')
    stages={};factors={}
    for name,_,_ in STAGES:
        cov,fac=cov_from_modes(maps[name],modes,amp)
        stages[name]=cov;factors[name]=fac
        np.savez_compressed(EXTERNAL/f'STAGE_{name}.npz',band1=cov[0],band2=cov[1],
                            total=cov[0]+cov[1])
    angular,angular_pass=compare(stages['A'],stages['B'])
    radial,radial_pass=compare(stages['B'],stages['C'])
    total=stages['C'][0]+stages['C'][1]
    pvdiag=[diagnostics(v) for v in stages['C']]+[diagnostics(total)]
    # The three pieces below stipulate distinct independent latent sources.
    D=np.full(len(g),150.**2) # hypothetical conditional source noise, km/s
    Z=np.column_stack([10**((data['dmzp']-25)/5)*(data['method_family']==m)
                       for m in ('FP','OTHER','SN','TF')])
    K=A@Z # output/(km/s/Mpc), method mean-design response
    Sigma=np.diag([.4,.4,.4,.4])**2 # hypothetical method offset law
    np.savez_compressed(EXTERNAL/'PV_FACTORS.npz',band1=factors['C'][0],band2=factors['C'][1])
    # Bridge V is source level; use no N-by-r materialization for the all-band
    # numerical law because the streamed projected factor is already A V.
    bridge=transport_covariance(A,D,calibration_response=K,
        calibration_covariance=Sigma,
        ownership={'independent':['stipulated independent 150 km/s source law'],
                   'calibration':['stipulated four-method mean-design offsets']})
    conditional=bridge['total']+total[:36,:36] # each R is a distinct smoothing law
    # R=0 unsmoothed H03 statistic has no supplied finite-band smoothing choice;
    # the declared R=5 h^-1 Mpc branch is used here and explicitly labelled.
    chol=np.linalg.cholesky(conditional)
    y=theta
    designs={
      'shared_monopole':np.tile(np.eye(9)[:,0],4)[:,None],
      'affine_monopole':np.column_stack((np.tile(np.eye(9)[:,0],4),
          np.repeat(np.array([.025,.04,.06,.08])-.05,9)*np.tile(np.eye(9)[:,0],4))),
      'shared_nine_coordinate_mean':np.tile(np.eye(9),(4,1)),
    }
    fits={name:gls_svd(y,X,conditional,relative_rank_tolerance=1e-10)
          for name,X in designs.items()}
    score={name:fit['statistic']+fit['rank']*math.log(36) for name,fit in fits.items()}
    chosen=min(score,key=score.get)
    # Known-covariance Gaussian reference. Selection calibration uses deterministic
    # draws under the shared-monopole fitted mean; finite MC error is reported.
    rng=np.random.default_rng(3602);draws=2000;counts={k:0 for k in designs};stats=[]
    mu=fits['shared_monopole']['fitted_mean']
    for i in range(draws):
        sample=mu+chol@rng.standard_normal(36)
        sim={name:gls_svd(sample,X,conditional,relative_rank_tolerance=1e-10)
             for name,X in designs.items()}
        best=min(sim,key=lambda k:sim[k]['statistic']+sim[k]['rank']*math.log(36))
        counts[best]+=1
        stats.append(sim[best]['statistic'])
    tail=(1+sum(v>=fits[chosen]['statistic'] for v in stats))/(draws+1)
    np.savez_compressed(EXTERNAL/'RESULT_MATRICES.npz',band1=stages['C'][0],band2=stages['C'][1],
        pv_total=total,baseline=baseline,method_K=K,method_Sigma=Sigma,
        conditional_R5=conditional,theta=theta)
    result={'schema':'htt.r36.cf4_correlated/1','task_id':'R36-02-CF4-CORRELATED',
      'packet_id':PACKET,'input_identity':INPUT,'status':'PROPOSED_PENDING_INDEPENDENT_REVIEW',
      'claim_tier':'CONDITIONAL_MODEL_COVARIANCE','transfer_source':'EH98_NO_WIGGLE_APPROXIMATION',
      'source_sha256':SHA_SOURCE,'operator_sha256':SHA_OPERATOR,'source_rows':len(g),
      'coordinate_order':'four H03 windows x nine raw theta coordinates',
      'frames':{'direction':'outward ICRS J2000','redshift':'released z_CMB proxy',
                'metric_signature':'(-,+,+,+)','c_km_s':old.C},
      'bands_h_Mpc':[[.005,.02],[.02,.05]],'smoothing_R_hinv_Mpc':[5,10,20],
      'units':'(km/s/Mpc)^2','amplitude':amp,'normalization':norm,
      'background_32_64_relative':bgerr,'fixture':fixture,'nufft_direct_subset_relative':direct_error,
      'nufft_eps':1e-12,'transform_seconds':transform_seconds,'target_count':len(targets),
      'angular_A_B':angular,'radial_B_C':radial,'angular_pass':angular_pass,
      'radial_pass':radial_pass,'band_and_total_diagnostics':pvdiag,
      'baseline_semantics':'inherited working covariance only; not independent source noise',
      'conditional_law':{'D_km_s_squared':'150^2 per selected group, stipulated independent',
        'calibration':'four independent method mean-design offsets, SD 0.4 km/s/Mpc',
        'K_units':'output/(km/s/Mpc); not a magnitude zero-point Jacobian',
        'PV':'R=5 h^-1 Mpc EH98 Gaussian band component, common field',
        'outside_bands':'UNKNOWN','cross_source_error_blocks':'UNKNOWN',
        'empirical_noise_decomposition':'UNKNOWN','observer_field':'fixed CMB metadata'},
      'conditional_R5_diagnostics':diagnostics(conditional),
      'mean_comparison':{'selection':'minimum chi2 + rank ln(36), fixed three designs',
        'scores':score,'chosen':chosen,'ranks':{k:v['rank'] for k,v in fits.items()},
        'known_covariance_gaussian_selected_tail':tail,
        'calibration_draws':draws,'calibration_MC_se':math.sqrt(tail*(1-tail)/(draws+1)),
        'selection_counts_under_shared_monopole':counts,
        'observed_chi2':{k:v['statistic'] for k,v in fits.items()}},
      'full_tensor_x_F_Pi_Q_G':'UNKNOWN; requires separate physical model and acceptance',
      'original42_promotion':False,'elapsed_seconds':time.monotonic()-start}
    write_json(HERE/'RESULT.json',result)
    with open(HERE/'TABLE.csv','w') as f:
        f.write('band,R_hinv_Mpc,trace_36,min_eigenvalue,rank_1e10\n')
        for b,C in enumerate(stages['C']):
            for r,R in enumerate((5,10,20)):
                v=C[36*r:36*(r+1),36*r:36*(r+1)];d=diagnostics(v)
                f.write(f'{b+1},{R},{d["trace"]},{d["min_eigenvalue"]},{d["rank_1e_10"]}\n')
    fig,ax=plt.subplots(1,2,figsize=(10,4))
    for i,C in enumerate(stages['C']):
        d=np.sqrt(np.diag(C[:36,:36]));corr=C[:36,:36]/np.outer(d,d)
        im=ax[i].imshow(corr,vmin=-1,vmax=1,cmap='coolwarm');ax[i].set_title(f'PV band {i+1}, R=5 h^-1 Mpc')
    fig.colorbar(im,ax=ax.tolist(),shrink=.8,label='correlation')
    fig.savefig(HERE/'FIGURE.png',dpi=160);plt.close(fig)
    print(json.dumps({'status':result['status'],'angular_pass':angular_pass,
        'radial_pass':radial_pass,'elapsed_seconds':result['elapsed_seconds']}))


if __name__=='__main__': main()
