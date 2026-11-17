"""Deterministic Commander PR3 T-quadrupole morphology from an owned R51 carrier.

No simulation/covariance field is read. This is an invertible representation of
measured estimator coefficients, not a fitted shear or a significance analysis.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import numpy as np
import scipy
from scipy.special import sph_harm_y

REL=Path('docs/research_program/observational_publication_20261015/R50_OBSERVED_CONVERGENCE_20261115/R51')
K=math.sqrt(8*math.pi/15)
MODES=['T_2_0','T_2_1r','T_2_1i','T_2_2r','T_2_2i']

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_from_repo(root):
    root=Path(root);base=root/REL;path=base/'observed_carrier.npz'
    fields=['mode_labels','d_commander_135_uK','d_smica_135_uK','response_J_135x5_uK','response_J_ideal_135x5_uK','stf_basis_5x3x3']
    with np.load(path,allow_pickle=False) as z:
        labels=z['mode_labels'];ti=np.array([str(s).startswith('T_') for s in labels]);t2i=np.array([str(s).startswith('T_2_') for s in labels])
        out={'schema':'r60.commander_deterministic_source_excerpt/1',
             'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
             'carrier_path':str(REL/'observed_carrier.npz'),'carrier_sha256':sha(path),'carrier_bytes':path.stat().st_size,
             'contract_path':str(REL/'R51_SOURCE_OPERATOR_CONTRACT.json'),'contract_sha256':sha(base/'R51_SOURCE_OPERATOR_CONTRACT.json'),
             'read_fields':fields,'T_labels':[str(s) for s in labels[ti]],'T2_labels':[str(s) for s in labels[t2i]],
             'd_commander_T45_uK':z['d_commander_135_uK'][ti].tolist(),'d_smica_T45_uK':z['d_smica_135_uK'][ti].tolist(),
             'J_T45x5_uK':z['response_J_135x5_uK'][ti].tolist(),'J_ideal_T45x5_uK':z['response_J_ideal_135x5_uK'][ti].tolist(),
             'STF_basis':z['stf_basis_5x3x3'].tolist(),'T_CMB_reference_uK':2.72548e6}
    result=json.loads((base/'R51_PR3_LOWELL_RESULT.json').read_text())
    out['input_sha256']=result['input_sha256']
    out['source_code_sha256']={f:sha(root/f) for f in ['scripts/r51/run_r51_pr3_lowell.py','scripts/r49/run_r49_cmb_and_multiprobe_lanes.py','htt/htt/htt/infer/r49_general_bianchi_likelihood.py']}
    return out

def tensor_from_packed(d,basis):
    d=np.asarray(d,dtype=float)
    if d.shape!=(5,) or not np.isfinite(d).all(): raise ValueError('finite five-component packed quadrupole required')
    q=np.array([d[3],-d[0],d[4],-d[1],-d[2]])/K
    return q,np.einsum('a,aij->ij',q,basis)

def packed_from_tensor(q):
    q=np.asarray(q,dtype=float)
    return K*np.array([-q[1],-q[3],-q[4],q[0],q[2]])

def axis_record(v):
    v=np.asarray(v,dtype=float).copy()
    # An eigenaxis is unoriented. Choose b>=0 solely to serialize one endpoint.
    if v[2]<0 or (abs(v[2])<1e-15 and v[np.argmax(np.abs(v))]<0):v=-v
    lon=math.degrees(math.atan2(v[1],v[0]))%360;lat=math.degrees(math.asin(np.clip(v[2],-1,1)))
    return {'unit_vector_galactic':v.tolist(),'l_deg':lon,'b_deg':lat,'opposite_l_deg':(lon+180)%360,'opposite_b_deg':-lat,'semantics':'unoriented eigenaxis, endpoints +/- equivalent'}

def morphology(d,basis):
    q,Q=tensor_from_packed(d,basis);eig,vec=np.linalg.eigh(Q);tr2=float(np.trace(Q@Q));tr3=float(np.trace(Q@Q@Q))
    i=int(np.argmax(np.abs(eig)))
    return {'packed_ell2_uK':np.asarray(d).tolist(),'STF5_uK':q.tolist(),'temperature_tensor_uK':Q.tolist(),
      'eigenvalues_uK_ascending':eig.tolist(),'eigenaxes_ascending':[axis_record(vec[:,k]) for k in range(3)],
      'principal_abs_eigenvalue_index':i,'principal_axis':axis_record(vec[:,i]),
      'trace_uK':float(np.trace(Q)),'trace_square_uK2':tr2,'trace_cube_uK3':tr3,
      'frobenius_uK':math.sqrt(tr2),'shape_sqrt6_trQ3_over_trQ2_3half':math.sqrt(6)*tr3/(tr2**1.5) if tr2 else None,
      'eigenvalue_gaps_uK':np.diff(eig).tolist(),'C2_uK2':float(np.dot(d,d)/5),
      'sky_quadrupole_RMS_uK':math.sqrt(2*tr2/15),
      'quadrupole_sky_min_uK':float(eig[0]),'quadrupole_sky_max_uK':float(eig[-1])}

def analyze(source):
    labels=source['T_labels'];index=[labels.index(k) for k in MODES]
    if source['T2_labels']!=MODES:raise ValueError('unexpected quadrupole real-mode convention')
    b=np.asarray(source['STF_basis'],float)
    if b.shape!=(5,3,3):raise ValueError('STF basis shape')
    gram=np.einsum('aij,bij->ab',b,b)
    if np.max(np.abs(gram-np.eye(5)))>1e-13:raise ValueError('STF basis is not orthonormal')
    commander=np.asarray(source['d_commander_T45_uK'],float);smica=np.asarray(source['d_smica_T45_uK'],float)
    d=commander[index];ds=smica[index]
    cm=morphology(d,b);sm=morphology(ds,b)
    q,Q=tensor_from_packed(d,b);qs,Qs=tensor_from_packed(ds,b)
    # Verify the analytic harmonic map against the independently generated R51 template.
    H=np.column_stack([packed_from_tensor(np.eye(5)[a]) for a in range(5)])
    ji=np.asarray(source['J_ideal_T45x5_uK'])[index];jm=np.asarray(source['J_T45x5_uK'])[index]
    rel=float(np.max(np.abs(ji+source['T_CMB_reference_uK']*H))/np.max(np.abs(ji)))
    if rel>1e-10:raise ValueError('analytic real harmonics disagree with R51 ideal template convention')
    # Independent numerical harmonic synthesis, Condon-Shortley convention.
    zz,ww=np.polynomial.legendre.leggauss(12);phi=np.arange(32)*2*math.pi/32
    Z,P=np.meshgrid(zz,phi,indexing='ij');theta=np.arccos(Z);nx=np.sqrt(1-Z*Z)*np.cos(P);ny=np.sqrt(1-Z*Z)*np.sin(P)
    n=np.stack([nx,ny,Z],axis=-1)
    a20=d[0];a21=(d[1]-1j*d[2])/math.sqrt(2);a22=(d[3]-1j*d[4])/math.sqrt(2)
    sky_h=(a20*sph_harm_y(2,0,theta,P)+2*np.real(a21*sph_harm_y(2,1,theta,P)+a22*sph_harm_y(2,2,theta,P))).real
    sky_q=np.einsum('...i,ij,...j->...',n,Q,n)
    sky_error=float(np.max(np.abs(sky_h-sky_q)));integral=float(np.sum(ww[:,None]*sky_q**2)*(2*math.pi/32))
    power_error=abs(integral-float(d@d));packed_error=float(np.max(np.abs(packed_from_tensor(q)-d)))
    # Exact operator-equivalent coordinates are diagnostic only: J uses the SMICA beam.
    if np.linalg.matrix_rank(jm)!=5:raise ValueError('reference masked quadrupole response is singular')
    reference_coeff=np.linalg.solve(jm,d)
    reference_reconstruction_error=float(np.max(np.abs(jm@reference_coeff-d)))
    reference_temperature=-source['T_CMB_reference_uK']*np.einsum('a,aij->ij',reference_coeff,b)
    vc=np.asarray(cm['principal_axis']['unit_vector_galactic']);vs=np.asarray(sm['principal_axis']['unit_vector_galactic'])
    angle=math.degrees(math.acos(np.clip(abs(vc@vs),-1,1)))
    matched_angles=[];matched_residual_bounds=[]
    perturbation_norm=float(np.linalg.norm(Q-Qs,2))
    ec=np.asarray(cm['eigenvalues_uK_ascending']);es=np.asarray(sm['eigenvalues_uK_ascending'])
    for k in range(3):
        ca=np.asarray(cm['eigenaxes_ascending'][k]['unit_vector_galactic']);sa=np.asarray(sm['eigenaxes_ascending'][k]['unit_vector_galactic'])
        matched_angles.append(math.degrees(math.acos(np.clip(abs(ca@sa),-1,1))))
        sep=float(np.min(np.abs(ec[k]-np.delete(es,k))))
        bound=math.degrees(math.asin(min(1.,perturbation_norm/sep))) if sep>0 else 90.
        matched_residual_bounds.append(bound)
    branch_switch=bool(cm['principal_abs_eigenvalue_index']!=sm['principal_abs_eigenvalue_index'])
    ellpowers=[]
    for ell in range(2,7):
        ids=[i for i,k in enumerate(labels) if int(k.split('_')[1])==ell]
        if len(ids)!=2*ell+1:raise ValueError('incomplete multipole')
        ellpowers.append({'ell':ell,'Commander_C_ell_uK2':float(commander[ids]@commander[ids]/len(ids)),
           'SMICA_C_ell_uK2':float(smica[ids]@smica[ids]/len(ids)),
           'difference_field_C_ell_uK2':float((commander[ids]-smica[ids])@(commander[ids]-smica[ids])/len(ids))})
    if sky_error>1e-10 or power_error>1e-9 or packed_error>1e-12:raise ValueError('harmonic/STF cross-check failed')
    return {'schema':'htt.r60.commander_deterministic_morphology/1','status':'OBSERVED_DETERMINISTIC_REPRESENTATION',
      'source':{k:source[k] for k in ['head','carrier_path','carrier_sha256','carrier_bytes','contract_path','contract_sha256','read_fields','source_code_sha256','input_sha256']},
      'conventions':{'frame':'Galactic Cartesian x=(l=0,b=0), y=(l=90,b=0), z=north Galactic pole','temperature_unit':'microkelvin thermodynamic CMB',
        'real_mode_labels':MODES,'real_mode_values':'[a20, sqrt(2)Re a21, -sqrt(2)Im a21, sqrt(2)Re a22, -sqrt(2)Im a22]',
        'STF5_order':'[(xx-yy)/sqrt2,(xx+yy-2zz)/sqrt6,xy_sym/sqrt2,xz_sym/sqrt2,yz_sym/sqrt2]',
        'analytic_STF5_map':'q=[d_2r,-d_0,d_2i,-d_1r,-d_1i]/sqrt(8*pi/15)',
        'sky_field':'T_ell2(n)=n^T Q_T n, Q_T=sum_a q_a E_a',
        'inherited_processing':'PR3 common Int mask; l<=6 finite coupling inverse with monopole/dipole columns; maps read at NSIDE2048; source estimator includes map beam and high-ell leakage','kinematic_quadrupole':'no subtraction applied; upstream convention unresolved','raw_map_hash_status':'inherited original R51 receipt, not rehashed in this derived-data run'},
      'commander_primary':cm,'smica_deterministic_comparison':sm,'same_estimator_comparison':{
        'ell2_packed_difference_norm_uK':float(np.linalg.norm(d-ds)),'ell2_STF_difference_norm_uK':float(np.linalg.norm(Q-Qs)),
        'quadrupole_difference_sky_RMS_uK':math.sqrt(2/15)*float(np.linalg.norm(Q-Qs)),
        'relative_tensor_difference_to_Commander':float(np.linalg.norm(Q-Qs)/np.linalg.norm(Q)),
        'principal_abs_eigenaxis_angle_deg':angle,
        'matched_eigenaxis_angles_by_ascending_eigenvalue_deg':matched_angles,
        'residual_perturbation_matched_axis_upper_bounds_deg':matched_residual_bounds,
        'tensor_perturbation_operator_norm_uK':perturbation_norm,
        'principal_abs_extremum_branch_switch':branch_switch,
        'principal_abs_branch_note':'The extremal-absolute-value selector compares different ordered eigenaxes when the middle eigenvalue changes sign. Use matched eigenaxes for cross-pipeline morphology.',
        'shape_difference':cm['shape_sqrt6_trQ3_over_trQ2_3half']-sm['shape_sqrt6_trQ3_over_trQ2_3half']},
      'T_multipole_powers_ell2_6':ellpowers,
      'reference_masked_response_diagnostic':{'interpretation':'coordinates reproducing the five measured Commander ell2 estimator values in the stored SMICA-beam template response; not Commander beam deconvolution or physical shear',
        'rank':int(np.linalg.matrix_rank(jm)),'condition_number':float(np.linalg.cond(jm)),
        'response_equivalent_coefficients':reference_coeff.tolist(),'equivalent_temperature_tensor_uK':reference_temperature.tolist(),
        'reconstruction_max_abs_uK':reference_reconstruction_error,
        'relative_tensor_difference_from_primary':float(np.linalg.norm(reference_temperature-Q)/np.linalg.norm(Q))},
      'checks':{'STF_gram_max_abs':float(np.max(np.abs(gram-np.eye(5)))),'analytic_vs_R51_ideal_template_relative':rel,
        'independent_scipy_harmonic_synthesis_max_abs_uK':sky_error,'quadrature_integral_vs_sum_abs_alm2_abs_uK2':power_error,
        'packed_roundtrip_max_abs_uK':packed_error,'quadrature':'12-point Gauss-Legendre cos(theta) x 32-point uniform phi; integrates degree-four squared quadrupole',
        'scipy_version':scipy.__version__,'numpy_version':np.__version__},
      'inference_status':{'Commander_matched_MC':'NOT_USED_UNAVAILABLE_IN_THIS_R51_CARRIER','SMICA_MC':'NOT_USED_FOR_THIS_RESULT',
        'confidence_intervals':'NOT_COMPUTED','p_values':'NOT_COMPUTED','posterior':'NOT_COMPUTED','present_shear':'NOT_INFERRED','Bianchi_family':'NOT_INFERRED'},
      'limits':['Equivalent tensor of the stored masked-estimator coefficients, not an unbiased estimate of an unknown exact full sky.',
        'Map beam, finite-lmax mask inversion, high-ell leakage, foreground residuals, and unbound kinematic-quadrupole convention remain inherited systematics.',
        'No matched Commander null is available in the audited R51 carrier. SMICA comparison is deterministic in common units.',
        'An angular STF tensor is an observable representation. A shear-history or current-shear interpretation needs a separate physical transfer and stochastic model.']}

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--repo-root');g.add_argument('--source-excerpt');p.add_argument('--out',required=True);args=p.parse_args()
    src=source_from_repo(args.repo_root) if args.repo_root else json.loads(Path(args.source_excerpt).read_text())
    out=analyze(src);out['generating_script_sha256']=sha(__file__)
    if args.source_excerpt:out['source_excerpt_sha256']=sha(args.source_excerpt)
    Path(args.out).write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'output':args.out,'commander':out['commander_primary'],'comparison':out['same_estimator_comparison'],'checks':out['checks']},indent=2))
if __name__=='__main__':main()
