"""Source-locked finite Planck PR3 temperature mask low/high leakage inverse.

One physical sky, nine component-separation/split processing treatments.
The 32 x 1053 mask operator is for ell 2..5 from ell 6..32 temperature
harmonics, NOT polarization, beam, foreground, E2E or ell>32 response.
The source lower-mode coefficients are a source cut-sky fit, not true alm.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.linalg import cho_factor, cho_solve

SHA = {
 'baseline_response_matrices.npz': 'a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007',
 'ell17_32_mask_response.npz': '91f496ca7cd1cbaed65153c64d83cf7abf84b21c141d8955d0cd8e07ed480a35',
 'retained_common_support_coefficients.npz': '900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459'
}


def read_sources(root):
    path=Path(root)
    for n, digest in SHA.items():
        if not (path/n).is_file() or hashlib.sha256((path/n).read_bytes()).hexdigest()!=digest:
            raise ValueError('L01 source mismatch: '+n)
    with np.load(path/'baseline_response_matrices.npz',allow_pickle=False) as z:
        lowblock=z['K_ell2to5_32x253'].copy()
    with np.load(path/'ell17_32_mask_response.npz',allow_pickle=False) as z:
        highblock=z['K_ell2to5_32x800'].copy()
    with np.load(path/'retained_common_support_coefficients.npz',allow_pickle=False) as z:
        names=z['names_T'].tolist(); t=z['coeff_T'].copy();enames=z['names_EB'].tolist()
    if lowblock.shape!=(32,253) or highblock.shape!=(32,800) or t.shape!=(9,32):
        raise ValueError('source shape mismatch')
    if len(set(names))!=9 or len(set(enames))!=8 or 'SMICA_noSZ_FULL' in enames:
        raise ValueError('same-sky processing/missing polarization contract violated')
    K=np.column_stack((lowblock,highblock))
    return K,t,names


def min_high_norm(K, y):
    """Sharp min ||h||2 for K h=y; requires full row rank.

    K^T (K K^T)^-1 y is a witness, norm = sqrt(y^T (K K^T)^-1 y).
    """
    K=np.asarray(K,dtype=float);y=np.asarray(y,dtype=float)
    if K.ndim!=2 or K.shape[0]>=K.shape[1] or y.shape!=(K.shape[0],):
        raise ValueError('full-row-rank K and matching y required')
    if not np.isfinite(K).all() or not np.isfinite(y).all():
        raise ValueError('nonfinite source')
    chol=cho_factor(K@K.T,check_finite=True)
    sol=cho_solve(chol,y)
    witness=K.T@sol
    residual=float(np.linalg.norm(K@witness-y))
    if residual>1e-9*max(1.,float(np.linalg.norm(y))):
        raise ValueError('source inverse residual too high')
    return float(np.linalg.norm(witness)),residual,witness


def sharp_linear_interval(K,y,v,radius):
    """Exact min/max v·(y-Kh) for ||h||2<=R in a fixed source basis."""
    K=np.asarray(K);y=np.asarray(y);v=np.asarray(v)
    if y.shape!=(K.shape[0],) or v.shape!=y.shape or not np.isfinite(radius) or radius<0:
        raise ValueError('invalid radius/contrast')
    mid=float(v@y);amp=float(radius*np.linalg.norm(K.T@v))
    return (mid-amp,mid+amp)


def run(root):
    K,y,names=read_sources(root)
    sv=np.linalg.svd(K,compute_uv=False)
    if sv[-1]<=1e-11:raise ValueError('mask design is not full row rank')
    band_rows=[]
    for band,operator in [('ell6_16',K[:,:253]),('ell17_32',K[:,253:]),('ell6_32',K)]:
        spectral=np.linalg.svd(operator,compute_uv=False)
        full_name=names.index('SMICA_FULL')
        bound,rr,_=min_high_norm(operator,y[full_name])
        band_rows.append({'band':band,'columns':operator.shape[1],
                         'row_rank':int(np.sum(spectral>spectral[0]*1e-12)),
                         'spectral_norm':float(spectral[0]),
                         'SMICA_FULL_min_high_norm_microK':bound,
                         'witness_residual':rr})
    rows=[]
    for i,name in enumerate(names):
        radius,resid,witness=min_high_norm(K,y[i])
        direction=y[i]/np.linalg.norm(y[i])
        rows.append({
           'product':name,
           'observed_low_l2_5_coeff_norm_microK':float(np.linalg.norm(y[i])),
           'min_high_l6_32_coeff_norm_microK_if_true_low_set_to_zero':radius,
           'relative_residual':float(resid/max(1.,np.linalg.norm(y[i]))),
           'linear_observed_direction_gain':float(np.linalg.norm(K.T@direction)),
           'directional_contrast_interval_if_R100_microK':list(sharp_linear_interval(K,y[i],direction,100.0)),
        })
    # Difference of two processing modes, not independent sky samples.
    idx={name:i for i,name in enumerate(names)}
    d=y[idx['SMICA_HM1']]-y[idx['SMICA_HM2']]
    rd,_,_=min_high_norm(K,d)
    return {
       'schema':'htt.L01_source_locked_minimal_high_lift/1',
       'claim':'SOURCE_FINITE_T_MASK_LINEAR_INVERSE_ONLY_NOT_CMB_PHYSICAL_NULL',
       'source_sha256':SHA,
       'mask_geometry_operator_dimensions':list(K.shape),
       'ell_low':[2,5],'ell_high':[6,32],
       'row_rank':int(np.sum(sv>sv[0]*1e-12)),
       'nullity':K.shape[1]-K.shape[0],
       'operator_norm':float(sv[0]),'smallest_nonzero_sv':float(sv[-1]),
       'condition_number':float(sv[0]/sv[-1]),
       'product_rows':rows, 'band_comparison':band_rows,
       'SMICA_HM1_minus_HM2_norm':float(np.linalg.norm(d)),
       'SMICA_HM1_minus_HM2_min_high_diff_norm':rd,
       'physical_sky_count':1,
       'not_measured':['physical ell6-32 CMB high-l coefficients','higher ell>32','polarization mask spin2 operator','beam','component separation','E2E null']
    }


if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--source',default='source');p.add_argument('--output',default='results/L01_SOURCE_FINITE_MINIMAL_LIFT.json')
 a=p.parse_args();r=run(a.source);q=Path(a.output);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(q, len(r['product_rows']),r['operator_norm'])
