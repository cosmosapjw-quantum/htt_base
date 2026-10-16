"""Finite-shell universal conservative mask-independent certificate.

The archived finite source matrix is never interpreted as a physical EGS or
Bianchi transfer.  This file only needs NumPy and the archived SHA-pinned NPZ.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np

EXPECTED_SHA = 'a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007'
CONDITION = 3.6013785311890616
NPIX = 26846
NSIDE = 64


def source_only_certificate(npz_path: Path) -> dict:
    source = Path(npz_path)
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual != EXPECTED_SHA:
        raise ValueError('original PR536 finite-source NPZ SHA mismatch')
    with np.load(source, allow_pickle=False) as z:
        k36 = np.asarray(z['K_full_36x253'], float)
        k12 = np.asarray(z['K_ell23_12x253'], float)
        k32 = np.asarray(z['K_ell2to5_32x253'], float)
    if k36.shape != (36,253) or k12.shape != (12,253) or k32.shape != (32,253):
        raise ValueError('source matrices changed shape')
    if not (np.array_equal(k12,k36[4:16]) and np.array_equal(k32,k36[4:36])):
        raise ValueError('unregistered retained row ordering')
    norms = {name: float(np.linalg.norm(k,ord=2)) for name,k in [('all_0_5',k36),('ell2_3',k12),('ell2_5',k32)]}
    assert np.isclose(norms['ell2_5'],2.255720291177002,atol=1e-12,rtol=0)
    # Spherical addition theorem: sum_m |Y_lm(n)|²=(2l+1)/(4pi)
    # For real orthonormal harmonics it holds for each pixel, hence the
    # Frobenius identity for any N selected directions, independently of mask.
    nnew=33**2-17**2
    conservative_upper = CONDITION*np.sqrt(nnew)
    return {'schema':'htt.c8_ell17_32.source_only_certificate/1',
            'claim':'FINITE_MASK_GEOMETRY_UPPER_BOUND_ONLY',
            'source_npz_sha256':actual,'prior_branch_head':'37db458319fd10e353a722345cb9a4ea6a39c698',
            'n_selected_nside64_ring':NPIX,'n_full_nside64':12*NSIDE**2,
            'masked_sky_fraction':NPIX/(12*NSIDE**2),
            'low_fit_ells':[0,5],'low_condition_from_prior_source':CONDITION,
            'archived_old_ell6_16_operators':norms,
            'new_shell_ells':[17,32],'new_shell_coefficients':nnew,
            'new_shell_actual_mask_specific_operator_norm':'NOT_COMPUTED_SOURCE_MASK_UNAVAILABLE_IN_SANDBOX',
            'new_shell_conservative_operator_norm_upper':float(conservative_upper),
            'combined_ell6_32_retained_ell2_5_operator_norm_interval':[
                norms['ell2_5'],float(np.hypot(norms['ell2_5'],conservative_upper))],
            'derivation':'K=Y_L^+Y_H; ||Y_H||_F²=N*M/(4π); sigma_max(Y_L)>=sqrt(N/(4π)); cond(Y_L)=kappa; thus ||K||_2<=kappa*sqrt(M). For retained rows projection does not increase the norm.',
            'bounds_assume':'same fixed source mask, exact real orthonormal harmonic sample, unweighted QR OLS with same 36 low columns',
            'not_bounded':['observed high mode amplitude','ell>=33 omitted tail','beam/component separation','physical covariant EGS epsilon','Bianchi shear or tilt']}


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--npz',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=source_only_certificate(args.npz)
    if args.output.exists():
        raise FileExistsError('create-only output')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'SOURCE_ONLY_BOUND_PASS','upper':result['new_shell_conservative_operator_norm_upper']}))

if __name__=='__main__':main()
