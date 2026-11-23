"""R105 same-source projections, conditional bounds and numerical checks for PHY-01..07."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.r103 import manticore_cf4_pv as pv
from scripts.r103.program import DAG, AUTHORITY, verified_json
from scripts.r104 import cf4_2mrs_field as field

ROOT = Path(__file__).resolve().parents[2]
PAPER = Path('docs/research_program/observational_publication_20261015')
PRIOR = PAPER/'R104_DATA_SOLVER_CONTINUATION_20261124'
TARGET = PAPER/'R105_RESEARCH_20261124/CROSS_RESULTS.json'


def normal_direction_coverage(n, r):
    """Worst whitened inverse-distance dipole information retained after fitting a constant dipole."""
    if np.any(np.asarray(r) <= 0):
        raise ValueError('source distances must be positive')
    x,y,z=n.T
    nuisance=np.column_stack((np.ones(len(n)), x*y, y*z, z*x, x*x-z*z,y*y-z*z))
    q=np.linalg.qr(nuisance,mode='reduced')[0]
    a=n-q@(q.T@n)
    b=n*(100./r[:,None])
    b-=q@(q.T@b)
    qa,ra=np.linalg.qr(a,mode='reduced')
    qb,rb=np.linalg.qr(b,mode='reduced')
    if min(np.linalg.matrix_rank(ra),np.linalg.matrix_rank(rb))!=3:
        raise ValueError('singular dipole response before profiling')
    s=np.linalg.svd(qa.T@qb,compute_uv=False)
    leftover=np.eye(3)-(qb.T@qa)@(qa.T@qb)
    return {'canonical_correlations':s.tolist(),
            'retained_fraction_extremes':np.linalg.eigvalsh(leftover)[[0,-1]].tolist(),
            'profiled_design_residual_spectrum':np.linalg.svd(b-qa@(qa.T@b),compute_uv=False).tolist()}


def missing_support(w, directions):
    # |v_los,i|<=V independently OR v_los,i=n_i.b with ||b||<=V globally.
    w=np.asarray(w); directions=np.asarray(directions)
    if w.ndim!=2 or directions.shape!=(w.shape[1],3) or not np.isfinite(w).all():
        raise ValueError('design/directions disagree')
    if not np.allclose(np.linalg.norm(directions,axis=1),1.,rtol=0.,atol=1e-10):
        raise ValueError('direction vectors must have unit length')
    return np.sum(np.abs(w),axis=1),np.linalg.norm(w@directions,axis=1)


def source_geometry(axis_lb):
    ids,n,r,w=pv.geometry()
    ng=field.to_galactic(n)
    vv,ok=field.interpolate(field.load_field(),ng*(r*field.H_LITTLE)[:,None])
    covered=w[:,ok]@np.einsum('ij,ij->i',vv[ok],ng[ok])
    missing=w[:,~ok]
    independent,bulk=missing_support(missing,ng[~ok])
    if np.any(bulk>independent+1e-14):
        raise ArithmeticError('coherent flow support must be a subset of independent velocities')
    axis=np.array([np.cos(np.deg2rad(axis_lb[0]))*np.cos(np.deg2rad(axis_lb[1])),
                   np.sin(np.deg2rad(axis_lb[0]))*np.cos(np.deg2rad(axis_lb[1])),
                   np.sin(np.deg2rad(axis_lb[1]))])
    sides=(ng@axis)>0
    rows={}
    for k,mask in {'all_selected':np.ones(len(n),dtype=bool),'field_covered':ok,'field_missing':~ok}.items():
        plus=ng[mask&sides];minus=ng[mask&~sides]
        delta=(plus.T@plus)/len(plus)-(minus.T@minus)/len(minus)
        lam=np.linalg.eigvalsh(delta-np.eye(3)*np.trace(delta)/3)
        amp=0.03
        rows[k]={
            'total':int(mask.sum()),'positive_negative_n':[len(plus),len(minus)],
            'window_quadrupole_eigenvalues':lam.tolist(),
            'max_fixed_shape_leakage':float(amp*np.ptp(lam)),
            'equal_weight_radial_design':normal_direction_coverage(ng[mask],r[mask])}
    return rows,{
        'source_sha256':pv.SOURCE_SHA,'velocity_axes_sha256':field.FIELD_SHA,
        'n_total':len(ids),'n_unmeasured':int((~ok).sum()),'known_36':covered.tolist(),
        'box_support_per_kms_36':independent.tolist(),'bulk_support_per_kms_36':bulk.tolist(),
        'individual_coordinate_sign_cancellation_speed_kms':{
            'independent':[None if e==0 else float(abs(a)/e) for a,e in zip(covered,independent)],
            'coherent':[None if e==0 else float(abs(a)/e) for a,e in zip(covered,bulk)]},
        'max_4monopole_consecutive_difference_per_kms':missing_support(np.diff(missing[::9],axis=0),ng[~ok])[0].tolist(),
        'scope':'Box-constrained z=0 radial velocities on missing rows; coherent case restricts them to projections of one common vector. Each coordinate and each contrast has its own maximizing assignment. g(z)/g(0) acts once.'}


def ray_stress(run):
    state=run['final_species']['radiation']
    f=np.array(state['q_over_E_sky'])
    s=np.array(state['pi_over_E_sky'])
    t=np.array(run['history']['species']['radiation']['final_pi_over_E_fluid'])
    ev=np.linalg.eigvalsh(np.eye(3)/3+s-np.outer(f,f))
    s-=np.eye(3)*np.trace(s)/3
    t-=np.eye(3)*np.trace(t)/3
    a,b=np.linalg.eigvalsh(s),np.linalg.eigvalsh(t)
    raw=np.linalg.norm(s-t)
    # Same ordered eigenvalues under proper rotations (eigenvector signs are arbitrary).
    shape=np.linalg.norm(a-b)
    orient=np.sqrt(max(0.,raw*raw-shape*shape))
    fdelta=f-np.array(state['q_over_E_fluid'])
    return {'family':run['family'],'cells':run['value'],
            'f_cov_psd_min':float(min(ev)),
            'f_ellipsoid_budget':float(f@np.linalg.solve(np.eye(3)/3+s,f)),
            'q_sky_minus_fluid_norm':float(np.linalg.norm(fdelta)),
            'stf_sky_norm':float(np.linalg.norm(s)),
            'stf_fluid_vs_sky_raw':float(raw),
            'stf_fluid_vs_sky_min_over_SO3':float(shape),
            'stf_fluid_vs_sky_orientation_part':float(orient)}


def radio_axis(d,c,a):
    d,c,a=map(np.asarray,(d,c,a))
    ci_a=np.linalg.solve(c,a)
    amp=float(ci_a@d/(ci_a@a))
    res=d-amp*a
    return {'best_amplitude':amp, 'amplitude_formal_sd':float(1/np.sqrt(a@ci_a)),
            'orthogonal_residual':res.tolist(),'profiled_wald':float(res@np.linalg.solve(c,res)),
            'working_wald_before':float(d@np.linalg.solve(c,d)),
            'GLS_orthogonality_abs':float(abs(ci_a@res))}


def analyze():
    dag=verified_json(ROOT,DAG,AUTHORITY)
    entry={n['id']:n for n in dag['nodes']}
    raw=json.loads((ROOT/PRIOR/'R104_RESULTS.json').read_bytes())
    hashes=raw['artifacts_sha256']
    def inp(name):
        return verified_json(ROOT,PRIOR/name,hashes[name])
    axis=entry['PHY-01']['observable_evidence']['CMB_axis_galactic_deg']
    geometry,h02=source_geometry(axis)
    parent_2mrs=inp('CF4_2MRS_FIELD.json')['cf4_windows']
    replay=float(np.max(abs(np.asarray(h02['known_36'])-parent_2mrs['b_2mrs_fullA_zero_filled_36'])))
    if replay>1e-12 or h02['n_total']-h02['n_unmeasured']!=parent_2mrs['n_common']:
        raise ValueError('2MRS projection or support differs from R104')
    h02['known_36_R104_replay_max_abs']=replay
    sd=[ray_stress(run) for run in inp('SOLVER_AXIS_SWEEP.json')['runs']
        if run['solver']=='R104' and run['axis']=='cells' and run['value'] in (96,192)]
    if len(sd)!=6:
        raise ValueError('unexpected family and resolution population')
    # Convert named Galactic axis into ICRS to use R104 ICRS-xy source response.
    l,b=np.deg2rad(axis)
    cmb_gal=np.array([np.cos(l)*np.cos(b),np.sin(l)*np.cos(b),np.sin(b)])
    cmb_eq=field.to_galactic(np.eye(3))@cmb_gal
    radio={}
    for grid in (4,8):
        d=inp(f'RADIO_BLOCK_JACKKNIFE_NSIDE{grid}.json')
        radio[str(grid)]={k:radio_axis(d['linear_contrast_icrs_xyz'][:2],np.asarray(d[k])[:2,:2],cmb_eq[:2])
                          for k in ['jackknife_cov','poisson_cov']}
    gaia=[]
    for row in inp('GAIA_PATCH_INFLUENCE.json')['rows']:
        u=row['norm'];radius=row['delete_two_shift_norm_quantiles_50_90_99_max'][-1]
        gaia.append({'shells':row['shell_indices'],'sector':row['sector'],'magnitude':u,
                     'all_pairs_shift_radius':radius,'minimum_full_axis_projection':u-radius,
                     'max_rotation_cone_deg':float(np.rad2deg(np.arcsin(radius/u))) if radius<u else None})
    mrec=entry['PHY-05']['observable_evidence']
    M=np.array(mrec['exceptional_M_signed_STF5_to_u']); w=np.asarray(mrec['exceptional_left_normal_flux_constraint'],float)
    w/=np.linalg.norm(w)
    # Small basis orientation uncertainty delta permits leakage up to ||u||sin(delta)
    # from an exactly allowed vector u; a rigid rotation of M cannot lift its rank.
    examples=entry['PHY-02']['observable_evidence']
    moves={}
    for key in ('normal_flux_allowed_unit_example','normal_flux_excluded_unit_example'):
        v=np.asarray(examples[key]);cos=float(np.clip(abs(w@v)/np.linalg.norm(v),0,1))
        moves[key]={'source':v.tolist(),'minimum_frame_rotation_to_Codazzi_plane_deg':float(np.rad2deg(np.arcsin(cos)))}
    return {'schema':'htt.r105.cross_routes/1','source_base_commit':'5a5f3b44d4fa5be65b71c2f80e715ebf9d1abf0a',
            'H02_missing_velocity_projection':h02,
            'PHY-01':{'axis_galactic_deg':axis,'amplitude_STF_eigenvalues':[-.03,0,.03],
                      'unweighted_windows':{k:{i:j for i,j in v.items() if i!='equal_weight_radial_design'} for k,v in geometry.items()}},
            'PHY-02':{'numerical_moment_realizability':[{k:r[k] for k in ('family','cells','f_cov_psd_min','f_ellipsoid_budget')} for r in sd]},
            'PHY-03':{'axis_icrs_xyz':cmb_eq.tolist(),'linear_integrated_minus_peak':radio,
                      'scope':'Unknown signed amplitude along common source axis, two transverse coordinates. Jackknife covariance conditional on this catalogue and mask.'},
            'PHY-04':{'sectorwise_delete_two_cones':gaia, 'scope':'Conservative deterministic bound for deletion of any observed two patches; angle unbounded by this argument when radius >= magnitude.'},
            'PHY-05':{'left_null':w.tolist(),'left_null_residual':float(np.linalg.norm(w@M)),
                      'unit_flux_plane_examples':moves,
                      'max_unit_leakage_under_frame_rotation':{str(d):float(np.sin(np.deg2rad(d))) for d in (0,1,5,10)},
                      'scope':'R78 canonical VI_-1/9 triad examples; no independent observed total flux in this triad.'},
            'PHY-06':{'numerical_stress_shape_rotation_decomposition':[{k:v for k,v in r.items() if not k.startswith('f_')} for r in sd]},
            'PHY-07':{k:v['equal_weight_radial_design'] for k,v in geometry.items()},
            'physical_Pi':None,'physical_GF':None,'calibrated_p':None,'family_attribution':None}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/TARGET)
    a=p.parse_args()
    a.output.write_text(json.dumps(analyze(),indent=2,allow_nan=False)+'\n')
