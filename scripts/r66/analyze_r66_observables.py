#!/usr/bin/env python3
"""Consume the R66 real Commander carrier; no raw map reads or downloads."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/'htt',ROOT/'htt/src'):sys.path.insert(0,str(p))
import numpy as np
from scipy import stats, linalg
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from htt.htt.infer import r66_radiation_quotient as rq

PUB=ROOT/'docs/research_program/observational_publication_20261015'
DOC=PUB/'R66_LOWELL_PHYSICAL_OBSERVABLES_20261117'
OUT=DOC/'RESULTS'
CORE=PUB/'OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-05-RADIATION-RESPONSE/radiation_core.py'
spec=importlib.util.spec_from_file_location('r66_reused_r36_core',CORE)
core=importlib.util.module_from_spec(spec);sys.modules[spec.name]=core;spec.loader.exec_module(core)


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def plain(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [plain(v) for v in x]
    return x


def empirical_lower(obs,draws):
    count=int(np.sum(draws<=obs));n=len(draws)
    lo=0. if count==0 else stats.beta.ppf(.025,count,n-count+1)
    hi=1. if count==n else stats.beta.ppf(.975,count+1,n-count)
    return {'count_lower_or_equal':count,'N':n,'rank_probability':(count+1)/(n+1),
            'binomial_reference_tail_interval_95':[lo,hi],
            'status':'CONDITIONAL_IDEAL_GAUSSIAN_REFERENCE','physical_PTE_qualified':False}


def tensor_summary(q):
    s=rq.stf5_to_matrix(q)
    return {'stf5_uK':q,'tensor_uK':s,'norm_uK':np.linalg.norm(q),
            'C2_uK2':8*np.pi/75*(q@q),
            'eigenvalues_uK':np.linalg.eigvalsh(s),
            'linear_pi_over_rho0':rq.STRESS_PER_UK*s,
            'linear_pi_Pa':rq.RHO0_SI*rq.STRESS_PER_UK*s}


def nonlinear_family(coeff,u):
    n,w=core.sphere_rule(32,64);h,labels=rq.harmonic_design(n,6)
    coeff=coeff.copy();coeff[:4]=0 # fitted map offset/dipole are not absolute radiation
    background=h@coeff/rq.T0_UK
    d=rq.BETA*(n@rq.DIPOLE_DIRECTION)
    dq=h[:,4:9]@rq.DQ_UK/rq.T0_UK
    rows=[]
    for alpha in [-2.,-1.,0.,1.,2.]:
        theta=background+d+alpha*dq
        m=core.moments(n,w,core.temperature_brightness(theta),rq.RHO0_SI)
        exact=rq.matrix_to_stf5(m.pi/m.rho)
        linear=rq.STRESS_PER_UK*(coeff[4:9]+alpha*rq.DQ_UK)
        read=core.stress_readout(m)
        rows.append({'alpha_added_DQ':alpha,'rho_over_rho0':m.rho/rq.RHO0_SI,
                     'pi_over_rho':exact,'quotient4_pi_over_rho':u.T@exact,
                     'quotient_nonlinear_difference_equivalent_uK':u.T@(exact-linear)/rq.STRESS_PER_UK,
                     'boost_null_D_norm':read['D_norm'],'Landau_A_gamma':read['A_gamma'],
                     'retained_remainder':rq.nonlinear_remainder(theta,w)})
    # Isolate the octupole contribution in this declared restored-temperature sky.
    no_oct=background.copy()-h[:,9:16]@coeff[9:16]/rq.T0_UK
    m=core.moments(n,w,core.temperature_brightness(no_oct+d),rq.RHO0_SI)
    no_oct_p=rq.matrix_to_stf5(m.pi/m.rho)
    exact0=np.array(rows[2]['pi_over_rho'])
    oct_linear_cross=12*d*(h[:,9:16]@coeff[9:16]/rq.T0_UK)
    oct_cross=core.stf2(np.einsum('n,n,ni,nj->ij',w,oct_linear_cross,n,n))
    eq_cross=u.T@rq.matrix_to_stf5(oct_cross)/rq.STRESS_PER_UK
    m0=core.moments(n,w,core.temperature_brightness(background+d),rq.RHO0_SI)
    transport=core.response_from_moments(m0)/m0.rho
    direct=core.response_direct(n,w,core.temperature_brightness(background+d),rq.RHO0_SI)/m0.rho
    response_image={'matrix_L_over_rho':transport,
                    'eigenvalues_L_over_rho':np.linalg.eigvalsh(transport),
                    'relative_anisotropic_norm':np.linalg.norm(transport-8/15*np.eye(5))/(8/15),
                    'moment_vs_direct_max_abs':np.max(abs(transport-direct)),
                    'pi5_over_rho':rq.matrix_to_stf5(m0.pi/m0.rho),
                    'H4_over_rho':m0.h4/m0.rho,
                    'definition':'L_I[S]=8rho S/15+10 STF(S pi)/7-H4:S; reused R36 static response',
                    'interpretation':'local radiation response image; no shear inversion without derivative/transport jet'}
    return {'status':'EXACT_IN_DECLARED_RESTORED_ELL_LE_6_TEMPERATURE_FAMILY',
            'monopole':'T0=2.72548 K restored; map-fitted offset excluded',
            'dipole':'3362.08 uK toward Galactic (264.021,48.253) deg restored',
            'DQ_alpha':'sensitivity coordinates only; no prior or inferred correction',
            'quadrature':'32 Gauss-Legendre x 64 azimuth; sufficient through degree26',
            'rows':rows,
            'octupole_delta_quotient_equivalent_uK':u.T@(exact0-no_oct_p)/rq.STRESS_PER_UK,
            'leading_dipole_octupole_equivalent_uK':eq_cross,
            'radiation_moment_bundle':response_image,
            'missing_temperature_modes':'no bound on true sky high-ell/foreground/spectral completion supplied',
            'exact_total_sky_stress_measured':False}


def run():
    source=OUT/'observed_temperature_carrier.npz'
    extraction=json.loads((OUT/'OBSERVED_EXTRACTION.json').read_text())
    if extraction['status']!='OBSERVATIONS_COMPLETE':raise RuntimeError('actual observed carrier required')
    reference_meta=json.loads((OUT/'IDEAL_REFERENCE.json').read_text())
    reference_source=OUT/'ideal_gaussian_reference.npz'
    if reference_meta['status']!='COMPLETE_IDEAL_REFERENCE' or sha(reference_source)!=reference_meta['carrier_sha256']:
        raise RuntimeError('ideal reference identity mismatch')
    with np.load(reference_source,allow_pickle=False) as zz:
        simulated={key:zz[f'REF_{key}'].copy() for key in ['n64_l6','n128_l6','n64_l8']}
        known_joint=zz['joint_covariance_uK2'].copy()
        ref_ids=zz['reference_ids'].copy()
    nref=len(ref_ids);ntrain=nref//2
    if sha(source)!=extraction['carrier_sha256']:raise RuntimeError('carrier identity mismatch')
    u=rq.quotient_basis(rq.DQ_UK);result={'schema':'htt.r66.actual_observables/1',
        'status':'ACTUAL_OBSERVATIONS_IDEAL_REFERENCE_COMPLETE','carrier_sha256':sha(source),
        'analysis_code_sha256':sha(Path(__file__)),'module_sha256':sha(ROOT/'htt/htt/htt/infer/r66_radiation_quotient.py'),
        'reused_r36_core_sha256':sha(CORE),'T0_K':rq.T0_K,'rho0_J_m3':rq.RHO0_SI,
        'stress_per_uK':rq.STRESS_PER_UK,'DQ_uK':rq.DQ_UK,'DQ_norm_uK':np.linalg.norm(rq.DQ_UK),
        'reference':reference_meta,'qualified_actual_Commander_temperature_MC_count':0,
        'operators':{},'same_sky_release_contrast':{},'controls':{},'nonlinear':{},
        'physical_PTE_qualified':False,'instantaneous_spacetime_shear_measured':False,
        'novelty_status':'empirical candidate; standard moment/quotient mathematics and R36/R60 antecedents reused'}
    with np.load(source,allow_pickle=False) as z:
        for ikey,key in enumerate(('n64_l6','n128_l6','n64_l8')):
            sims=simulated[key];known_cov=known_joint[5*ikey:5*(ikey+1),5*ikey:5*(ikey+1)]
            block={'MC':{'N':nref,'kind':'synthetic ideal Gaussian operator carrier','mean_stf5_uK':sims.mean(axis=0),
                          'mean_over_rms':sims.mean(axis=0)/np.sqrt(np.mean(sims*sims,axis=0)),
                          'known_zero_covariance_stf5_uK2':sims.T@sims/nref},'maps':{}}
            simnorm=np.linalg.norm(sims@u,axis=1)
            for release in ('PR3','PR4'):
                q=z[f'{release}_{key}'][4:9];perp=u@(u.T@q)
                views=rq.five_views(q,sims,known_covariance_uk2=known_cov)
                views['Pi']['reference_model']='ideal Gaussian fixed-spectrum pixel model; not Commander E2E'
                views['Pi']['finite_N_diagnostic']=rq.ConditionalReference.from_draws(sims@u).tail(u.T@q)
                if release=='PR3':
                    views['Pi']['warning']='PR4-native ideal operator does NOT source-calibrate PR3; sensitivity only'
                    views['Pi']['status']='CROSS_RELEASE_REFERENCE_ONLY'
                    views['F']['status']='CROSS_RELEASE_REFERENCE_OCCUPANCY_ONLY'
                block['maps'][release]={'full':tensor_summary(q),'quotient':tensor_summary(perp),
                    'retained_norm_fraction':np.linalg.norm(perp)/np.linalg.norm(q),'views':views,
                    'empirical_quotient_lower':empirical_lower(np.linalg.norm(perp),simnorm)}
                pt=rq.power_tensor_quadrupole(q)
                pt['sign_reversal_max_difference']=np.max(abs(pt['tensor_uK2']-rq.power_tensor_quadrupole(-q)['tensor_uK2']))
                pt['same_input_comparison']='Aluri & Patel 2506.22795v1 Eq2; R66 finite estimator, not their inpainted data'
                block['maps'][release]['conventional_power_tensor']=pt
                if release=='PR3':block['maps'][release]['empirical_quotient_lower']['status']='CROSS_RELEASE_REFERENCE_ONLY'
            result['operators'][key]=block
            delta=z[f'PR4_{key}'][4:9]-z[f'PR3_{key}'][4:9]
            alpha=delta@rq.DQ_UK/(rq.DQ_UK@rq.DQ_UK)
            rem=delta-alpha*rq.DQ_UK
            result['same_sky_release_contrast'][key]={'delta_PR4_minus_PR3_uK':delta,
                'best_scalar_DQ_amplitude':alpha,'DQ_orthogonal_residual_uK':rem,
                'total_norm_uK':np.linalg.norm(delta),'residual_norm_uK':np.linalg.norm(rem),
                'residual_power_fraction':(rem@rem)/(delta@delta),
                'uncertainty':'no paired PR3-PR4 MC law; deterministic processing contrast, not new sky'}
        primary=z['PR4_n64_l6'][4:9]
        for key in ('n128_l6','n64_l8'):
            delta=z[f'PR4_{key}'][4:9]-primary
            paired=simulated[key]-simulated['n64_l6']
            result['controls'][key]={'delta_stf_uK':delta,'quotient_delta_norm_uK':np.linalg.norm(u.T@delta),
                'relative_quotient_shift':np.linalg.norm(u.T@delta)/np.linalg.norm(u.T@primary),
                'paired_MC_rms_quotient_shift_uK':np.sqrt(np.mean(np.sum((paired@u)**2,axis=1))),
                'interpretation':'paired estimator sensitivity, not independent cosmological evidence'}
        for release in ('PR3','PR4'):
            result['nonlinear'][release]=nonlinear_family(z[f'{release}_n64_l6'],u)
        # Constructive response to the observed finite-band sensitivity. This is
        # an exploratory secondary experiment; the preregistered primary stays.
        joint=np.column_stack((simulated['n64_l6']@u,simulated['n64_l8']@u))
        design=np.vstack((np.eye(4),np.eye(4)))
        weights,train_cov=rq.paired_operator_weights(joint[:ntrain],design)
        heldout=joint[ntrain:]@weights.T
        joint_projection=np.zeros((8,15));joint_projection[:4,:5]=u.T;joint_projection[4:,10:]=u.T
        known8=joint_projection@known_joint@joint_projection.T
        reference=rq.KnownGaussianReference(rq.STRESS_PER_UK**2*(weights@known8@weights.T))
        old_ref=rq.KnownGaussianReference(rq.STRESS_PER_UK**2*known8[:4,:4])
        heldref=rq.ConditionalReference.from_draws(heldout*rq.STRESS_PER_UK)
        eig=linalg.eigvalsh(reference.covariance,old_ref.covariance)
        secondary={'status':'EXPLORATORY_PAIRED_OPERATOR_CONSTRUCTION',
            'reason':'finite-band control changed the real-data estimate; primary remains n64_l6',
            'training_id_range':[0,ntrain-1],'validation_id_range':[ntrain,nref-1],
            'reference_kind':'synthetic ideal Gaussian model; analytic covariance known',
            'paired_input':'[DQ-orthogonal n64_l6 four-vector, DQ-orthogonal n64_l8 four-vector]',
            'design_8x4':design,'weights_4x8':weights,'training_covariance_8x8_uK2':train_cov,
            'training_covariance_condition':np.linalg.cond(train_cov),
            'response_identity_max_abs':np.max(abs(weights@design-np.eye(4))),
            'analytic_covariance4':reference.covariance,'heldout_covariance4':heldref.covariance,
            'analytic_variance_ratios_to_primary':eig,
            'heldout_to_analytic_covariance_relative_frobenius':np.linalg.norm(heldref.covariance-reference.covariance)/np.linalg.norm(reference.covariance),
            'analytic_volume_ratio_to_primary':np.sqrt(np.linalg.det(reference.covariance)/np.linalg.det(old_ref.covariance)),
            'shared_sky':'full cross-operator covariance retained; never independent copies',
            'statistical_interpretation':'frozen training weights, analytic conditional Gaussian population law; no post-selection discovery PTE',
            'realized_sky_measurement_error':False,'maps':{}}
        for release in ('PR3','PR4'):
            y=np.r_[u.T@z[f'{release}_n64_l6'][4:9],u.T@z[f'{release}_n64_l8'][4:9]]
            x=weights@y
            secondary['maps'][release]={'quotient4_equivalent_uK':x,'representative_stf5_uK':u@x,
                'norm_equivalent_uK':np.linalg.norm(x),'pi_linear_quotient4_over_rho0':rq.STRESS_PER_UK*x,
                'reference_status':'CROSS_RELEASE_REFERENCE_ONLY' if release=='PR3' else 'EXPLORATORY_CONDITIONAL_REFERENCE',
                'conditional_reference':reference.tail(rq.STRESS_PER_UK*x),
                'prior4_logpdf_zero_mean':reference.logpdf(rq.STRESS_PER_UK*x)}
        result['paired_operator_secondary']=secondary
        # Compare old R60 actual tensor only as a provenance/operator crosscheck.
        old_path=PUB/'R50_OBSERVED_CONVERGENCE_20261115/R51/observed_carrier.npz'
        with np.load(old_path,allow_pickle=False) as old:
            labels=list(old['mode_labels']);ix=[labels.index(t) for t in ['T_2_0','T_2_1r','T_2_1i','T_2_2r','T_2_2i']]
            d=old['d_commander_135_uK'][ix];qold=np.array([d[3],-d[0],d[4],-d[1],-d[2]])/np.sqrt(8*np.pi/15)
        result['R60_reuse']={'carrier_sha256':sha(old_path),'previous_C2_uK2':8*np.pi/75*(qold@qold),
            'previous_norm_uK':np.linalg.norm(qold),'new_PR3_operator_shift_uK':z['PR3_n64_l6'][4:9]-qold,
            'meaning':'different post-release mask/finite-estimator definitions; no new R60 claim'}
        figure(z,result,u,simulated)
    (OUT/'OBSERVABLES.json').write_text(json.dumps(plain(result),indent=2,allow_nan=False)+'\n')
    print(json.dumps(plain({'PR4_primary':result['operators']['n64_l6']['maps']['PR4'],
                           'contrast':result['same_sky_release_contrast']['n64_l6'],
                           'controls':result['controls'],'paired_secondary':secondary}),indent=2))


def figure(z,result,u,simulated):
    fig,ax=plt.subplots(2,2,figsize=(11,8),constrained_layout=True)
    colors={'PR3':'#ce5b27','PR4':'#245bb2'}
    for release in ('PR3','PR4'):
        q=z[f'{release}_n64_l6'][4:9]
        ax[0,0].plot(np.arange(1,5),rq.STRESS_PER_UK*(u.T@q)*1e6,'o-',label=release,color=colors[release])
        alpha=np.linspace(-2,2,200)
        ax[0,1].plot(alpha,np.linalg.norm(q[None,:]+alpha[:,None]*rq.DQ_UK,axis=1),label=f'{release} full',color=colors[release])
        ax[0,1].axhline(np.linalg.norm(u.T@q),color=colors[release],ls='--',label=f'{release} quotient')
    ax[0,0].set(xlabel='Retained STF coordinate (fixed U)',ylabel=r'$10^6\,\pi_{\rm lin,\perp}/\rho_0$',title='Signed physical proxy; common sky')
    ax[0,0].axhline(0,color='gray',lw=.7);ax[0,0].legend()
    ax[0,1].set(xlabel='Added DQ amplitude (sensitivity only)',ylabel=r'Tensor norm [$\mu$K]',title='Declared rank-one nuisance')
    ax[0,1].legend(fontsize=8)
    sim=np.linalg.norm(simulated['n64_l6']@u,axis=1)
    ax[1,0].hist(sim,bins=15,color='#a3b3c8',edgecolor='white',label=f'{len(sim)} ideal Gaussian draws')
    for release in ('PR3','PR4'):
        norm=np.linalg.norm(u.T@z[f'{release}_n64_l6'][4:9])
        ax[1,0].axvline(norm,color=colors[release],lw=2,label=release)
    ax[1,0].set(xlabel=r'DQ-orthogonal tensor norm [$\mu$K]',ylabel='Realizations',title='Explicit ideal Gaussian reference')
    ax[1,0].legend(fontsize=8)
    keys=['n64_l6','n128_l6','n64_l8'];x=np.arange(3)
    for release,offset in [('PR3',-.16),('PR4',.16)]:
        norms=[np.linalg.norm(u.T@z[f'{release}_{k}'][4:9]) for k in keys]
        ax[1,1].bar(x+offset,norms,width=.3,color=colors[release],label=release)
    ax[1,1].set_xticks(x,['64 / l6','128 / l6','64 / l8'])
    ax[1,1].set(xlabel='NSIDE / fitted band',ylabel=r'Quotient norm [$\mu$K]',title='Predeclared processing controls')
    ax[1,1].legend()
    fig.suptitle('R66 Commander low-ell radiation-stress study\nPost-release quantities; no unconditional anomaly or shear inference',fontsize=13)
    fig.savefig(OUT/'lowell_physical_observables.png',dpi=170)
    fig.savefig(OUT/'lowell_physical_observables.pdf')
    plt.close(fig)


if __name__=='__main__':run()
