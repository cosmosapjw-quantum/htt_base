"""Finite angular-calibration anchor design; no cosmological dynamics or ODE.

Public-source geometry is observed; precision is a conditional design calculation.
Run with the Codex primary-runtime Python. Results are C0/DIAGNOSTIC_ONLY.
"""
from pathlib import Path
import itertools, json, sys
import numpy as np

ROOT = Path(__file__).resolve().parent
NAMES = ['UGC3789','NGC6264','NGC6323','NGC5765b','CGCG074-064','NGC4258']
# First five positions: Villaraos+2022 Table 1, DOI 10.1093/mnras/stac2973,
# which explicitly credits original MCP astrometry. Last: NASA NGC4258 page.
RA = [(7,19,30.9490),(16,57,16.12780),(17,13,18.03991),(14,50,51.51950),(14,3,4.457746),(12,18,57.5)]
DEC = [(59,21,18.3150),(27,50,58.5774),(43,46,56.7465),(5,6,52.2502),(8,56,51.03483),(47,18,14)]
# Angular-diameter distance and percentile errors: Pesce+2020 Table 1.
DIST = np.array([51.5,132.1,109.4,112.2,87.6,7.58])
PLUS = np.array([4.5,21.,34.,5.4,7.9,.11])
MINUS = np.array([4.,17.,23.,5.1,7.2,.11])
H02_TARGET = json.loads((ROOT/'h02_target_interval.json').read_text())['selected_row']
H02_LOWER = H02_TARGET['lower_mag']
H02_UPPER = H02_TARGET['upper_mag']

def directions():
    ra = np.deg2rad([15*(h+m/60+s/3600) for h,m,s in RA])
    de = np.deg2rad([d+m/60+s/3600 for d,m,s in DEC])
    return np.column_stack([np.cos(de)*np.cos(ra),np.cos(de)*np.sin(ra),np.sin(de)])

def design(n):
    x,y,z = np.asarray(n).T
    return np.column_stack([np.ones(len(x)),x,y,z,x*x-z*z,y*y-z*z,2*x*y,2*x*z,2*y*z])

def nullspace(a, tol=1e-11):
    _,s,vh = np.linalg.svd(a,full_matrices=True)
    return vh[np.count_nonzero(s > tol):].T

def quotient(dip, nuisance):
    return dip - nuisance @ np.linalg.lstsq(nuisance,dip,rcond=None)[0]

def target_radius(a, target, epsilon=1., tol=1e-10):
    """Sharp support halfwidth of ||a p - a p0||2 <= epsilon.

    Returns inf if target is not estimable. Valid at a feasible exact-fit center.
    More general observed residual consumes squared radius; see report.
    """
    k = nullspace(a)
    if np.linalg.norm(k.T@target) > tol:
        return float('inf')
    return float(epsilon*np.linalg.norm(np.linalg.lstsq(a.T,target,rcond=None)[0]))

def method_bias_design(n, method_ids):
    """G gamma adds method-specific 8-component angular calibration.

    Actual contributor labels must be supplied; dominant pooled CF4 partitions
    are not automatically raw-method calibration labels.
    """
    x=design(n)[:,1:]
    labels=list(dict.fromkeys(method_ids))
    g=np.zeros((len(x),8*len(labels)))
    for i,label in enumerate(method_ids):
        j=labels.index(label)
        g[i,8*j:8*j+8]=x[i]
    return g

def method_uncertainty_outer(a, target, g, delta, noise_radius=0.):
    """Outer target error for y=A p+G gamma+e, |gamma_j|<=delta_j.

    |target.p-target.A^+y| <= R||w|| + sum_j delta_j |(G^T w)_j|,
    w=(A^+)^T target; assumes estimable target and ||e||<=R.
    This bound need not be sharp after residual-fit constraints are enforced.
    """
    gain=target_radius(a,target)
    if not np.isfinite(gain):
        return float('inf')
    w=np.linalg.lstsq(a.T,target,rcond=None)[0]
    return float(noise_radius*gain+np.sum(np.broadcast_to(delta,(g.shape[1],))*np.abs(g.T@w)))

def augment(a, count=64):
    """D-optimal three anchors among a fixed 64-point Fibonacci candidate grid.

    det(A_aug)^2 = pdet(A A^T) det(B K)^2, K orthonormal ker(A).
    Thus a 3x3 determinant exhaustively selects the three directions.
    """
    i=np.arange(count); z=1-2*(i+.5)/count
    phi=i*np.pi*(3-np.sqrt(5.))
    cand=np.column_stack([np.sqrt(1-z*z)*np.cos(phi),np.sqrt(1-z*z)*np.sin(phi),z])
    k=nullspace(a); projected=design(cand)@k
    triples=np.array(list(itertools.combinations(range(count),3)))
    dets=np.abs(np.linalg.det(projected[triples]))
    winner=triples[np.argmax(dets)]
    return cand[winner],winner,float(dets.max())

def main():
    n=directions(); a=design(n); d=a[:,1:4]; z=a[:,[0,4,5,6,7,8]]
    witness=-np.linalg.solve(z,d)
    dip_only=a[:,:4]; e=np.array([0.,1.,0.,0.])
    smu=5/np.log(10)*(.5*(PLUS+MINUS))/DIST
    weighted=dip_only/smu[:,None]
    cov=np.linalg.inv(weighted.T@weighted)
    extra,ids,volume=augment(a); a9=design(np.vstack([n,extra]))
    targets=np.eye(9)[1:4]
    gains=np.array([target_radius(a9,t) for t in targets])
    h02=json.loads((ROOT/'h02_base_summary.json').read_text())
    # These centers are only displayed as existing fitted apparent fields.
    centers={m:v['coefficients_mag'] for m,v in h02['base_fits'].items()}
    # Explicit scenario, not observed contributor identities: every anchor shares
    # one uncertain method calibration. Its x coefficient aliases common eta_x.
    same_method_g=method_bias_design(np.vstack([n,extra]),['SCENARIO_ONE_METHOD']*9)
    method_floor=method_uncertainty_outer(a9,targets[0],same_method_g,.02)
    result={
      'schema':'FINITE_ANGULAR_ANCHOR_BRIDGE_V1','owner':'htt','claim_tier':'C0',
      'status':'CONDITIONAL; DIAGNOSTIC_ONLY; NON_CLAIM_BEARING',
      'transfer_source':'none','physical_node_acceptance':'UNCHANGED_HOLD',
      'scope':'Published-direction design, exact finite regression lemma, prospective precision',
      'runtime':{'python':sys.version,'numpy':np.__version__},
      'names':NAMES,'J2000_unit_directions':n.tolist(),
      'angular_diameter_distance_Mpc':DIST.tolist(),
      'linearized_symmetrized_maser_modulus_scale_mag':smu.tolist(),
      'distance_error_caveat':'16/84 percentile errors converted to symmetric local planning scales, not confidence radii; optical comparison noise omitted',
      'relative_calibration_scope':'All reported precision numbers assume method-specific angular gamma_m and relative method monopoles are exactly known/subtracted (or fixed to zero). Raw catalogue-minus-geometric residuals constrain eta+gamma_m, not eta alone.',
      'uncertain_method_calibration':{'model':'raw residual = A p + G gamma + e; corrected residual subtracts G gamma_hat',
        'target_outer_bound':'R ||w||_2 + sum_j delta_j |(G^T w)_j|, w=(A^+)^T target, for |gamma-gamma_hat|<=delta',
        'actual_anchor_contributor_labels':'UNMEASURED; no actual G was assigned',
        'single_method_delta002_SCENARIO_x_calibration_floor_mag':method_floor,
        'scenario_interpretation':'Even exact distances retain a 0.02mag common-x ambiguity if all9anchors share one method with |gamma_x|<=0.02; same residuals result from eta_x shifts compensated by gamma_x.'},
      'design_A_singular_values':np.linalg.svd(a,compute_uv=False).tolist(),
      'nuisance_Z_singular_values':np.linalg.svd(z,compute_uv=False).tolist(),
      'nuisance_rank_perturbation_check':{'assumed_each_direction_error_arcmin':1.,
        'operator_perturbation_upper_bound':float(2*np.sqrt(30)*np.pi/(180*60)),
        'remaining_singular_value_lower_bound':float(np.linalg.svd(z,compute_uv=False)[-1]-2*np.sqrt(30)*np.pi/(180*60)),
        'status':'Analytic Weyl bound under stated angular perturbation; not astrometric error estimate'},
      'full_design_rank':int(np.linalg.matrix_rank(a)),'nuisance_rank':int(np.linalg.matrix_rank(z)),
      'dipole_quotient_rank_difference':int(np.linalg.matrix_rank(a)-np.linalg.matrix_rank(z)),
      'dipole_quotient_norm':float(np.linalg.norm(quotient(d,z),2)),
      'gauge_witness_nuisance_per_unit_dipole':witness.tolist(),
      'witness_max_residual':float(np.max(np.abs(z@witness+d))),
      'dipole_only_modulus_std_mag':np.sqrt(np.diag(cov)[1:]).tolist(),
      'dipole_only_unit_l2_anchor_error_to_x_gain':target_radius(dip_only,e),
      'dipole_only_uniform_independent_sigma_required_for_1p96_x_width_below_h02_lower_mag':H02_LOWER/(1.96*target_radius(dip_only,e)),
      'h02_base_apparent_centers_mag':centers,
      'h02_delta002_x_outer_interval_mag':[H02_LOWER,H02_UPPER],
      'design_augmentation':{'candidate_count':64,'candidate_rule':'Fibonacci midpoint equal-area grid; zero phase; golden-angle longitude',
        'chosen_indices':ids.tolist(),'new_directions_PROSPECTIVE_ONLY':extra.tolist(),
        'projected_volume':volume,'rank':int(np.linalg.matrix_rank(a9)),
        'singular_values':np.linalg.svd(a9,compute_uv=False).tolist(),
        'dipole_unit_l2_error_gains':gains.tolist(),
        'l2_anchor_residual_budget_required_for_x_width_below_h02_lower_mag':float(H02_LOWER/gains[0]),
        'uniform_independent_sigma_required_for_1p96_x_width_below_h02_lower_mag':float(H02_LOWER/(1.96*gains[0]))},
      'assumptions':['Matched same-object optical and geometric distance definitions, same frame and angular calibration basis',
        'Method-specific relative angular calibration and method scalar offsets known/subtracted for existing numerical precision curves; uncertain-case bounds are separate',
        'Common calibration transport from anchors to selected CF4 sample is assumed and needs empirical justification',
        'Global scalar zero point is free; angular model is exactly monopole+dipole+STF quadrupole',
        'Published anchors are not asserted independent of upstream CF4 calibration',
        'No observed optical-minus-geometric calibration residuals used; rank and precision design only'],
      'sources':{'distances':'https://arxiv.org/abs/2001.09213',
         'five_positions':'https://doi.org/10.1093/mnras/stac2973',
         'NGC4258_position':'https://science.nasa.gov/asset/hubble/ngc-4258/',
         'h02':h02['source']}}
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results/ANCHOR_BRIDGE.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savez(ROOT/'results/anchor_arrays.npz',directions=n,design=a,nuisance=z,witness=witness,augmented_design=a9,extra_directions=extra)
    print(json.dumps({k:result[k] for k in ['full_design_rank','nuisance_rank','dipole_quotient_rank_difference','witness_max_residual','dipole_only_modulus_std_mag','dipole_only_uniform_independent_sigma_required_for_1p96_x_width_below_h02_lower_mag','design_augmentation']},indent=2))
    return result

if __name__=='__main__': main()
