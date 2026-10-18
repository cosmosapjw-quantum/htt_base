#!/usr/bin/env python3
"""Actual CF4 group distance-modulus directional quadrupole conditional distribution.

Under a declared arbitrary restricted source-processing model this measures
an APPARENT Hubble-modulus angular STF2 pattern.  It does NOT estimate
geometry-frame Bianchi shear sigma/Theta, physical vorticity, actual
4-acceleration, nor a global matter tilt.  Group covariance and
selection-normalization are NOT supplied by the released group tables.
"""
from __future__ import annotations
import argparse,hashlib,json,time,resource
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from obsstat.catalogs.cf4_raw import load_authenticated_cf4_raw_groups
from obsstat.cf4_apparent_kinematic_distribution import (
    xyz_from_equatorial, model_matrix,weighted_lsq,posterior_shear_proxy,
    profile_identified_shear_fraction,stf2_orthonormal
)
ROOT=Path(__file__).resolve().parents[1]
LOOP=ROOT/'docs/research_program/theory_obs_application_20261015/loop6_kinematics'
RAW=Path('/mnt/extdrive/workdir/raw/cf4_full')
SHA3='c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d'
SHA4='b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94'
T3=RAW/'table3.dat';T4=RAW/'table4.dat'
C=299792.458
KAPPA=5/np.log(10)


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for t in iter(lambda:f.read(8<<20),b''): h.update(t)
    return h.hexdigest()


def run(out, draws=30000, *, pool_rare_methods=False):
    if out.exists():raise ValueError('create-only output directory; preserve old results')
    start=time.perf_counter()
    if sha256(T3)!=SHA3 or sha256(T4)!=SHA4:raise ValueError('source release hash drift')
    c=load_authenticated_cf4_raw_groups(T3,T4,
       expected_table3_sha256=SHA3,expected_table4_sha256=SHA4)
    assert c.row_count==38053
    mask=c.primary_domain_mask(z_min=.01,z_max=.10)
    assert int(mask.sum())==35970
    z=c.vcmb_km_s[mask]/C
    mu=c.dmzp[mask]
    dm=c.e_dmzp[mask]
    n=xyz_from_equatorial(c.ra_deg[mask],c.dec_deg[mask])
    raw_method_families=c.method_family[mask]
    methods=raw_method_families.copy()
    if pool_rare_methods:
        # Documented MODEL choice, not a mutation of original CF4
        # method metadata: CAL2/SBF14/MIXED724 must share nuisance
        # rather than make a nearly empty method-specific redshift
        # slope that disappears under leave-one-sky-patch tests.
        methods=np.where(np.isin(methods,['CAL','SBF','MIXED_OTHER']),'OTHER',methods)
    ids=c.group_id[mask]
    sid=hashlib.sha256(np.asarray(ids,dtype='<i8').tobytes()).hexdigest()
    assert sid=='f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88',sid

    cases=[
      ('fiducial_slope_f015_v250_z01_10',.01,.10,.15,250.,True,None),
      ('no_method_depth_slope_f015_v250',.01,.10,.15,250.,False,None),
      ('floor030_slope_v250',.01,.10,.30,250.,True,None),
      ('velocity500_floor015',.01,.10,.15,500.,True,None),
      ('low_depth_001_005',.01,.05,.15,250.,True,None),
      ('high_depth_005_010',.05,.10,.15,250.,True,None),
      ('FP_only',.01,.10,.15,250.,True,'FP'),
      ('TF_only',.01,.10,.15,250.,True,'TF'),
      ('SN_only',.01,.10,.15,250.,True,'SN'),
    ]
    samples=None
    fits={}
    registry=[]
    for idx,(name,zlow,zhigh,floor,vel,slope,family) in enumerate(cases):
        chosen=(z>=zlow)&(z<=zhigh)
        if family is not None: chosen&=(methods==family)
        zz=z[chosen];nn=n[chosen];mm=methods[chosen]
        y=mu[chosen];reported=dm[chosen]
        X=model_matrix(zz,nn,mm,include_method_slope=slope,
            include_bulk=True,include_angular_dipole=True)
        # Velocity law is hypothetical and independent; scaling with z correctly
        # differentiated from the fixed cosmographic dL(z).
        error=np.sqrt(reported**2+floor**2+(vel*X['redshift_velocity_width_basis_mag_per_kms'])**2)
        resid=y-X['reference_mu_mag']
        fit=weighted_lsq(X['design'],resid,error)
        shear=fit['beta'][X['slices']['shear']]
        cov=fit['cov'][X['slices']['shear'],X['slices']['shear']]
        posterior=posterior_shear_proxy(fit['beta'],fit['cov'],X['slices']['shear'],
                                      draws=draws,seed=20261015+idx)
        prof=profile_identified_shear_fraction(X['design'],error,X['slices'])
        tensor=np.einsum('k,kij->ij',shear,stf2_orthonormal())
        omega=np.linalg.eigvalsh(tensor)
        amp=np.linalg.norm(shear)
        outrow={
          'case':name,'source_count':int(chosen.sum()),'sample_group_id_sha256':hashlib.sha256(np.asarray(ids[chosen],dtype='<i8').tobytes()).hexdigest(),
          'z_min_max':[float(zz.min()),float(zz.max())],
          'methods_counts':{str(k):int(v) for k,v in zip(*np.unique(mm,return_counts=True))},
          'mu_model':'mu_CMB-frame_proxy - mu_FLRW(z; H0=74.6,Om=.3153), with method offsets, optional method log(z) slopes, nuisance bulk and directional dipole',
          'floor_mag':floor,'peculiar_velocity_floor_km_s':vel,'method_depth_slope_nuisance':slope,
          'source_model_rank':fit['rank'],'condition_scaled':fit['condition_scaled'],
          'chi_squared_divided_dof':fit['chisq']/fit['dof'],
          'chi_squared':fit['chisq'],'dof':fit['dof'],
          'five_STF_apparent_shear_directional_H_fraction_coordinates':shear.tolist(),
          'five_STF_conditional_covariance':cov.tolist(),
          'norm_five_STF_apparent_shear_fraction':float(amp),
          'apparent_shear_sqrt_sigma2overTheta2':float(amp/3),
          'eigenvalues_apparent_tracefree_directional_H_fraction':omega.tolist(),
          'formal_conditioned_distribution':posterior,
          'source_nuisance_projection_diagnostics':prof,
          'apparent_angular_dipole_mag_coeff':fit['beta'][X['slices']['angular_dipole']].tolist(),
          'bulk_velocity_proxy_km_s':fit['beta'][X['slices']['bulk']].tolist(),
          'bulk_proxy_norm_km_s':float(np.linalg.norm(fit['beta'][X['slices']['bulk']])),
          'claim':'EXPLORATORY_SELECTED_GROUP_CONDITIONAL_GAUSSIAN_ANGULAR_DISTANCE_RESIDUAL_ONLY'
        }
        fits[name]=outrow
        registry.append((name,chosen,X,error,fit))
        print('RUN',name,'n',outrow['source_count'],'amp',round(amp,6),
             'chi2/dof',round(outrow['chi_squared_divided_dof'],4),
             'H_tensor eig',np.round(omega,6).tolist(),flush=True)
        if idx==0:
            rng=np.random.default_rng(20261015)
            samples=rng.multivariate_normal(shear,cov,size=draws)
            sample_template={'five_stf_shear_proxy':samples,'mean':shear,'cov':cov}

    # Local survey sensitivity (not independent sky replications): 12 HEALPix
    # nside1 celestial equal-area delete-one-angular patch groups.
    import healpy as hp
    main_name=cases[0][0]
    name,chosen,X,e,fit=registry[0]
    subset_mask=np.asarray(chosen,bool)
    ang=hp.vec2pix(1,n[:,0],n[:,1],n[:,2])
    J=[]
    for k in range(12):
        keep=(ang[subset_mask]!=k)
        if keep.sum()<=X['design'].shape[1]+100: continue
        try:
           f=weighted_lsq(X['design'][keep],(mu-X['reference_mu_mag'])[subset_mask][keep],e[keep])
           ss=f['beta'][X['slices']['shear']]
           delta=ss-fit['beta'][X['slices']['shear']]
           localcov=fit['cov'][X['slices']['shear'],X['slices']['shear']]
           departure=float(np.sqrt(delta@np.linalg.solve(localcov,delta)))
           J.append({'deleted_patch_id':k,'remaining_n':int(keep.sum()),
                'norm_apparent_shear_fraction':float(np.linalg.norm(ss)),
                'five_shear_proxy_coeff':ss.tolist(),
                'departure_in_units_of_naive_error_covariance':departure})
        except Exception as ex:
           J.append({'deleted_patch_id':k,'STATUS':'NEEDS_DIAGNOSIS','error':str(ex)[:140]})
    results={
       'schema':'htt.CF4_group_appHubble_STF2_conditional_distribution/1',
       'provenance':'AUTHENTICATED_CF4_2023_PUBLISHED_GROUP_DMZP_E_DMZP_VCMB_J2000_ONLY',
       'claim_status':'ACTUAL_CATALOG_APPEARANCE_CONDITIONED_EXPLORATORY_NOT_BIANCHI_KINEMATICAL_POSTERIOR',
       'source_table3_sha256':SHA3,'source_table4_sha256':SHA4,
       'n_release_groups':c.row_count,'n_z01_10':len(z),'selected_id_sha256':sid,
       'source_frame':'published Vcmb/C, not observer heliocentric redshift; J2000 sky. Frame boost/distance selection not physically reconstructed',
       'calibration':'reported DMzp is final cosmology-calibrated CF4 group modulus; shared method/host covariance UNKNOWN; method nuisance fitted but does not replace covariance',
       'reference_LCDM':{'Href_km_s_Mpc':74.6,'Om':.3153,'Ol':.6847},
       'observable':'model-conditioned angular residual in published group distance modulus mu- mu_flatLCDM(z_Vcmb)',
       'approximate_linear_response':'delta_mu=-5/ln10*[n_i(S/Href)ij n_j +(1+z)/c(d ln d_L/dz)n.b + n.a_dipole]+ method offsets and method-depth slopes',
       'kinematical_identification':'S/Href inferred numerically only under strong ansatz, not true geometry-frame sigma_ij/H or surface-optical shear; beta matter tilt, omega and four-acceleration not identified',
       'method_families_in_raw_source':sorted(set(raw_method_families)),
       'method_families_after_optional_low_support_pool':sorted(set(methods)),
       'method_pool_rare_CAL_SBF_MIXED_OTHER_into_OTHER':bool(pool_rare_methods),
       'method_families_available':sorted(set(methods)),
       'method_counts':{str(k):int(v) for k,v in zip(*np.unique(methods,return_counts=True))},
       'cases':fits,
       'fiducial_leave_one_healpix_nside1_region_out':J,
       'n_jackknife_patches_attempted':12,
       'reconstruction_step':'source data fit to conditional flat LCDM distance law plus four nuisance channel families; independent diagonal Gaussian + phenomenological velocity floor; unknown proper selection likelihood',
       'decisions':['NEVER publish shear constraints from these formal credible intervals without selection/E2E calibration',
                    'omega radial antisymmetry zero is exact; no finite omega posterior from this likelihood',
                    'fitted angular dipole is NOT four acceleration; fitted bulk b is NOT homogeneous matter-geometry beta'],
       'wall_seconds':time.perf_counter()-start,
       'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(out/'selected_source_observables.npz',
      group_id=ids,z_CMB= z,dmzp=mu,e_dmzp=dm,n_J2000=n,method_family=methods)
    np.savez_compressed(out/'conditional_fiducial_stf2_proxy_draws.npz',**sample_template)
    # Diagnostics: posterior distributions and method/floor depth sensitivity.
    from matplotlib.patches import Patch
    fig,axs=plt.subplots(1,2,figsize=(11,4.6),layout='constrained')
    vals=np.linalg.norm(samples,axis=1)/3
    axs[0].hist(vals,bins=80,density=True,histtype='step',linewidth=1.4,label='Conditional diagonal-Gaussian')
    axs[0].axvline(fits[main_name]['apparent_shear_sqrt_sigma2overTheta2'],color='k',lw=.8,ls='--')
    axs[0].set(xlabel=r'Apparent $\|\sigma_{\rm proxy}\|/\Theta$ (NOT background shear)',
               ylabel='Conditional probability density',title='CF4 0.01≤z≤0.10 apparent STF2')
    axs[0].legend(fontsize=7)
    ordered=list(fits)
    xx=np.arange(len(ordered))
    axs[1].scatter([fits[k]['apparent_shear_sqrt_sigma2overTheta2'] for k in ordered],xx,s=38)
    axs[1].set_yticks(xx,ordered,fontsize=7)
    axs[1].set(xlabel='Apparent anisotropic Hubble quadrupole proxy /3',
           title='Sensitivity to method, depth and scatter floor')
    axs[1].grid(alpha=.2)
    fig.savefig(out/'cf4_apparent_kinematical_distribution_and_sensitivity.png',dpi=165)
    plt.close(fig)
    readme=['# CF4 raw-group directional Hubble residual → STF2: observed-source conditional distribution',
    '', '자료: CF4 표3,4의 원본 Vcmb·DMzp·eDMzp·RA/Dec, 35970개 z∈[.01,.1] 그룹.',
    '독립적인 거리모듈러스 분포를 가진 것으로 **가정**한 forward 모델을 바탕으로',
    'directional quadrupolar Hubble modulus residual의 5개 계수 분포를 계산한다.',
    '',
    '| model | n | nominal ||S/H|| | sigma/Theta proxy | normalized chi2 |',
    '|---|---:|---:|---:|---:|']
    for label,val in fits.items():
        readme.append(f"| {label} | {val['source_count']} | {val['norm_five_STF_apparent_shear_fraction']:.5g} | {val['apparent_shear_sqrt_sigma2overTheta2']:.5g} | {val['chi_squared_divided_dof']:.4g} |")
    readme+=['','Units are dimensionless; the data source uses cosmological CMB-rest Vcmb, not uncorrected source z.',
       'No physical Bianchi kinematic measurement, full-C likelihood, true selection normalizer, optical Jacobi remainder or external cosmological validation is implied.',
       'The large method/depth sensitivity is part of the scientific result, not an uncertainty estimate from independent universes.',
       f"LOO HEALPix patches attempted: {len(J)}"]
    (out/'REPORT_KO.md').write_text('\n'.join(readme)+'\n')
    print('FINISHED',len(fits),'n',len(z),'seconds',results['wall_seconds'],
          'jackknife',len(J),'rssMiB',results['peak_rss_kib_linux']/1024,flush=True)
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--pool-rare-methods',action='store_true',
        help='join CAL(2)/SBF(14)/MIXED_OTHER(724) as OTHER nuisance ONLY; do not alter raw records')
    args=parser.parse_args()
    run(args.output_dir,pool_rare_methods=args.pool_rare_methods)
