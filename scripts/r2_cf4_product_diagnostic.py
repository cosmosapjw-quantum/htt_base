#!/usr/bin/env python3
"""R2-02 actual grouped coverage/sensitivity and manufactured latent injection."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'htt'),str(ROOT/'htt/htt'),str(ROOT/'htt/src')]
import numpy as np
from scipy.optimize import minimize
from obsstat.catalogs.cf4_grouped_observations import load_grouped_observations,GroupedObservations,METHODS
from htt.infer.cf4_information import NoiseScenario,profiled_rows,information
from htt.infer.cf4_product_provider import (CF4ResponseProvider,ResponseFamily,SlotAssumptions,
    ConditionalCF4CatalogueLaw,area_distance_to_modulus,luminosity_to_area_distance,calibration_templates)
from common.structured_inference import StructuredLinearModel
from common.bulkflow_covariance import SamplingCovariance


def injection(seed=2026101402):
    """Two directional coefficients, all other coefficients fixed by contract.

    This finite recovery assesses implementation. Observed-Hessian errors are
    conditional local estimates; no empirical coverage calibration is claimed.
    """
    rng=np.random.default_rng(seed)
    # Six sky axes, two area-distance shells, two repeats per shell/axis.
    direction=np.repeat(np.vstack((np.eye(3),-np.eye(3))),4,axis=0)
    radius=np.tile([40.,40.,130.,130.],6)
    provider=CF4ResponseProvider(ResponseFamily.WEAK12,'HELIOCENTRIC','HELIOCENTRIC','J2000_EQUATORIAL_SOURCEWARD','manufactured exact truncation',0.)
    theta=np.zeros(12);theta[0]=120.;theta[3]=70.;theta[4]=1.2
    eta=float(rng.normal(0,.03));mu=[];vobs=[];proposals=[];assumptions=[]
    for n,r in zip(direction,radius):
        a=SlotAssumptions((np.log(r)-.025,np.log(r)+.025),(-80.,80.),(-np.inf,35.65),.12,100.,
           'manufactured uniform log dA slot','manufactured upper mu cut','independent given eta','uniform bounded source motion')
        assumptions.append(a)
        for k in range(1,1001):
            rr=np.exp(rng.uniform(*a.log_distance_bounds));u=rng.uniform(-80,80)
            v=provider.velocity(n[None,:],[rr],theta)[0]+u
            m=float(area_distance_to_modulus(rr,v/299792.458,eta));mm=rng.normal(m,.12);vv=rng.normal(v,100)
            if mm<=35.65:mu.append(mm);vobs.append(vv);proposals.append(k);break
        else:raise RuntimeError('proposal cap HOLD')
    c=GroupedObservations(np.arange(1,len(mu)+1),np.array(mu),np.full(len(mu),.12),np.array(vobs),direction,np.zeros((len(mu),7),bool),{'source':'manufactured','redshift_frame':'HELIOCENTRIC','direction_frame':'J2000_EQUATORIAL_SOURCEWARD'})
    def law(order,eta_order):
        return ConditionalCF4CatalogueLaw(c,provider,assumptions,shared_zero_point_sigma_mag=.03,calibration_source='N(0,.03^2) conditional selected slot scheme',conditioned_field_convention='ZERO_METHOD_ANGULAR_VELOCITY_FIELDS_ASSUMED_FOR_SCENARIO',cross_covariance_mode='INDEPENDENT_GIVEN_SHARED_LATENTS',remainder_km_s=np.zeros(len(mu)),order=order,calibration_order=eta_order)
    base=law(24,32)
    def obj(x):
        t=theta.copy();t[[0,4]]=x*[100.,1.];return -base.log_likelihood(t)
    fit=minimize(obj,[0,0],method='BFGS',options={'gtol':1e-5,'maxiter':150})
    # Independent central difference Hessian of objective in scaled coordinates.
    x=fit.x;h=np.zeros((2,2));step=.002;eye=np.eye(2)*step
    f=obj(x)
    for j in range(2):h[j,j]=(obj(x+eye[j])-2*f+obj(x-eye[j]))/step**2
    h[0,1]=h[1,0]=(obj(x+eye[0]+eye[1])-obj(x+eye[0]-eye[1])-obj(x-eye[0]+eye[1])+obj(x-eye[0]-eye[1]))/(4*step**2)
    if np.min(np.linalg.eigvalsh(h))<=0:raise RuntimeError('observed Hessian HOLD')
    scale=np.array([100.,1.]);cov=np.linalg.inv(h)*scale[:,None]*scale[None,:]
    tf=theta.copy();tf[[0,4]]=x*scale
    refined_law=law(40,48)
    refined=refined_law.log_likelihood(tf);coarse=base.log_likelihood(tf)
    radial=np.column_stack((100*direction[:,0],radius*direction[:,0]))
    narrow=np.column_stack((100*direction[:,0],80*direction[:,0]))
    difference=tf[[0,4]]-theta[[0,4]]
    return {'radial_design':{'full_two_shell_singular_values':np.linalg.svd(radial,compute_uv=False).tolist(),'single_80_Mpc_shell_singular_values':np.linalg.svd(narrow,compute_uv=False).tolist(),'interpretation':'single shell Bx+r*Ax degeneracy; units fixed at B scale 100 km/s, A scale 1 km/s/Mpc'},'truth_minus_estimate_local_mahalanobis_squared':float(difference@np.linalg.solve(cov,difference)),'seed':seed,'slots':len(mu),'parameters_fitted':['Bx','Ax'],'truth':theta[[0,4]].tolist(),'estimate':tf[[0,4]].tolist(),
      'conditional_observed_hessian_standard_error':np.sqrt(np.diag(cov)).tolist(),'covariance':cov.tolist(),'correlation':float(cov[0,1]/np.sqrt(cov[0,0]*cov[1,1])),
      'optimization':{'success':bool(fit.success),'message':str(fit.message),'evaluations':int(fit.nfev),'gradient_norm':float(np.linalg.norm(fit.jac))},
      'latent_quadrature_orders':[24,40],'eta_quadrature':refined_law.last_eta_integration,'legacy_calibration_order_arguments_unused':[32,48],'conditioned_field_convention':'ZERO_METHOD_ANGULAR_VELOCITY_FIELDS_ASSUMED_FOR_SCENARIO','loglik_refinement_absolute_difference':abs(refined-coarse),
      'shared_zero_point_draw_mag':eta,'shared_zero_point_integrations_per_catalogue':1,'maximum_proposals_per_slot':max(proposals),
      'coverage':'NOT_CALIBRATED_ONE_MANUFACTURED_DRAW_COMPATIBILITY_ONLY','statistic_vs_bias':'observed-Hessian covariance describes local supplied sampling model; no actual-product bias/coverage claim',
      'selection_count':'fixed selected slots; proper eta prior conditional on slot/count scheme; no population Poisson count fit'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,default=ROOT/'workdir/raw/cf4_full');parser.add_argument('--output',type=Path,default=ROOT/'docs/observational_upgrade_r2/R2-02/raw/diagnostic.json');args=parser.parse_args()
    start=time.monotonic()
    c=load_grouped_observations(args.source/'table3.dat.gz',args.source/'table4.dat.gz',args.source/'ReadMe')
    z=c.vh_km_s/299792.458;dl=10**((c.modulus-25)/5);r=luminosity_to_area_distance(dl,z)
    low,high=np.quantile(r,[.49,.51]);masks={'full':np.ones(len(r),bool),'dA_20_200_Mpc':(r>=20)&(r<=200),'central_49_51_percent':(r>=low)&(r<=high)}
    masks.update({'delete_presence_'+name:~c.method_presence[:,j] for j,name in enumerate(METHODS)})
    scenarios=[NoiseScenario('mu_published_v100_motion300_fixed_cal',100,300),NoiseScenario('mu_published_v30_motion150_fixed_cal',30,150),NoiseScenario('free_common',100,300,True),NoiseScenario('free_common_and_method_presence',100,300,True,True)]
    sensitivity=[]
    for scenario in scenarios:
        signal,nuisance,_,_=profiled_rows(c,scenario)
        for name,mask in masks.items():
            info=information(signal,nuisance,mask)
            sensitivity.append({'scenario':scenario.__dict__,'sample':name,**{k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in info.items()}})
    # R2-01 core consumes OBS02's already noise-scaled/projected rows.
    x,n,_,_=profiled_rows(c,scenarios[0]);mask=masks['dA_20_200_Mpc']
    model=StructuredLinearModel(x[mask],SamplingCovariance(diagonal=np.ones(mask.sum())),observation_order_id=hashlib.sha256(c.group_id[mask].tobytes()).hexdigest(),selection_id='fixed catalogue-point mask; no calibrated selection law',observation_unit='scenario-whitened residual',coefficient_units=['km/s']*4+['km/s/Mpc']*9)
    t,tn=calibration_templates(c,method_modes=True,angular=c.direction)
    coverage=[]
    for name,mask in masks.items():
        coverage.append({'sample':name,'groups':int(mask.sum()),'fiducial_dA_min_median_max_Mpc':np.quantile(r[mask],[0,.5,1]).tolist(),
           'method_presence_counts':dict(zip(METHODS,c.method_presence[mask].sum(axis=0).tolist()))})
    source_stable=all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in c.provenance['source_sha256'].items())
    if not source_stable:raise RuntimeError('immutable CF4 input changed during diagnostic')
    report={'source_bytes_stable_across_run':source_stable,'task':'R2-02','owner':'HTT','scope':'actual grouped-product coverage and local conditional sensitivity; supplied manufactured selected latent recovery',
       'claim_tier':'diagnostic_only','transfer_source':'none','actual_posterior_status':'HOLD_MISSING_ALL_METHOD_SELECTION_AND_JOINT_COVARIANCE',
       'source':c.provenance,'groups':len(c.group_id),'negative_or_zero_vh_groups':int(np.sum(c.vh_km_s<=0)),
       'distance':'dL=10^((DMzp-25)/5); fiducial dA=dL/(1+Vh/c)^2; catalogue-point conditioning only',
       'observations':'one DMzp,e_DMzp,Vh per 1PGC; Table3 method presence only; Table4 Dist/Vpec not read',
       'frame':'heliocentric Vh as supplied; J2000 sourceward; no CMB correction inferred',
       'capabilities':[CF4ResponseProvider(f,'HELIOCENTRIC','HELIOCENTRIC','J2000_EQUATORIAL_SOURCEWARD','UNKNOWN',None).capability() for f in ResponseFamily],
       'actual_remainder':'UNKNOWN; physical provider refuses response/fit; OBS02 SVD remains local scenario sensitivity',
       'calibration_templates':{'columns':t.shape[1],'names':tn,'method_meaning':'Boolean presence templates are supplied scenario assumptions; no fractional method weights'},
       'coverage':coverage,'sensitivity':sensitivity,'R2_01_core':{'rank':model.rank,'singular_values_unscaled':model.all_singular_values.tolist(),'identity':model.identity,'use':'conditional scenario response only; no observed response fit'},
       'injection':injection(),
       'limitations':['full all-method source selection not supplied','full shared flow/calibration covariance not supplied','Vh uncertainties/group-motion law declared scenarios only','fixed-count conditional slot law differs from population sampling law','no actual data fit or significance; no inferred global tilt'],
       'runtime':{'requested_model':'gpt-6.1-sol','requested_effort':'medium','observed':'UNKNOWN','python':sys.executable,'python_version':platform.python_version(),'numpy':np.__version__,'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'elapsed_seconds':time.monotonic()-start}}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'groups':len(c.group_id),'output':str(args.output),'injection':report['injection']}))
if __name__=='__main__':main()
