"""R36-07 actual-carrier geometry and marginal-noise support consumer.

The R32 finite common-response calculation is conditional.  No physical
foreground radius or cross-channel noise covariance is inferred here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import time

import numpy as np

REPO = Path(__file__).resolve().parents[6]
OUT = Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_budget_actual')
CONTRACT = Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_contract_preparation/IMPLEMENTATION_CONTRACT.json')
PACKET = '7f1ac3df12ebbc36c4e92086f2ccd51de69f544310d21528754067f9bc0cee4c'
INPUT = 'sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43'
BANDS = (30, 44, 70, 100, 143, 217, 353)
BRANCH = 'A_BT_1e-07'
R31 = REPO / 'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/evidence/R31/report/data/RESULT.json'
R32 = REPO / 'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-04-BANDPASS-BOUNDS/repair_05/RESULT.json'
NPZ = R32.parent / 'report/generated/A_BT_1e-07_full24.npz'
CARRIER = Path('/mnt/extdrive/workdir/htt_open_data/r26_delivered_seven_frequency_numeric/FULL7_CARRIER.npz')
SMICA = Path('/mnt/extdrive/workdir/htt_open_data/r27_eight_map_saved_tensor_comparison_numeric/run/products/FULL8_COMPARISON.npz')
S7 = Path('/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/run/COMMON_SUPPORT_S7.npz')
FROZEN = Path('/mnt/extdrive/workdir/htt_open_data/r26_streamed_spin2_numeric/FROZEN_INPUT.json')
MATH = Path('/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/full7_math.py')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def save_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n')


def source_check(contract: dict) -> None:
    if sha(CONTRACT) != 'ca09bcbcba470c7712a34c69c793703181b99836f4cb51febdd7471435121089':
        raise RuntimeError('FROZEN_CONTRACT_DRIFT')
    for row in contract['inputs']:
        path = Path(row['path'])
        if not path.is_file() or sha(path) != row['sha256']:
            raise RuntimeError(f"FROZEN_SMALL_INPUT_DRIFT: {path}")
    if contract['controller_binding']['spec']['input_identity'] != INPUT:
        raise RuntimeError('PACKET_INPUT_DRIFT')


def geometry(contract: dict) -> dict:
    with np.load(CARRIER, allow_pickle=False) as z:
        Y = z['frequency_canonical_7x24'].astype(float)
        bands = z['bands_GHz'].tolist()
        labels = z['coordinate_labels'].tolist()
    with np.load(NPZ, allow_pickle=False) as z:
        F, a, c = (z[k].astype(float) for k in ('F', 'a', 'c_primary'))
        saved_C = z['Kinv_primary'].astype(float)
        center_operator = z['full24_center_linear_operator'].astype(float)
    r31 = json.loads(R31.read_text())
    r32 = json.loads(R32.read_text())
    # R32 spells the same m labels with an extra "_m" marker.
    canonical_labels = [s.replace('Re_m','Re').replace('Im_m','Im')
                        for s in r32['full24_coordinate_order']]
    if bands != list(BANDS) or labels != canonical_labels:
        raise RuntimeError('CARRIER_BAND_OR_COORDINATE_ORDER')
    if Y.shape != (7, 24) or F.shape != (7, 9) or not np.isfinite(Y).all():
        raise RuntimeError('CARRIER_OR_OPERATOR_SHAPE')
    if not np.allclose(F, r31['branches'][BRANCH]['F2']['matrix_7xk'], rtol=0, atol=1e-14):
        raise RuntimeError('R31_R32_OPERATOR_MISMATCH')
    D = np.asarray(r32['common_reference_column_scales'], dtype=float)
    Minv = np.diag(D**-2)
    C = np.linalg.inv(F @ Minv @ F.T)
    if not np.allclose(C, saved_C, rtol=1e-11, atol=1e-11):
        raise RuntimeError('R32_KINV_MISMATCH')
    ell2 = float(a @ C @ a)
    ell = math.sqrt(ell2)
    if abs(ell - r32['branches'][BRANCH]['common_reference']['minimum_budget_ell']) > 1e-10:
        raise RuntimeError('R32_ELL_REPRODUCTION')
    s0 = Y.T @ C @ a / ell2
    if not np.allclose(s0, center_operator @ Y.ravel(), rtol=1e-10, atol=2e-11):
        raise RuntimeError('CENTER_OPERATOR_MISMATCH')
    residual = Y - np.outer(a, s0)
    U0 = Minv @ F.T @ C @ residual
    J0 = float(np.sum(residual * (C @ residual)))
    J0_alt = float(np.sum((D[:, None] * U0)**2))
    if J0 < 0 or abs(J0-J0_alt) > max(1e-12, 1e-9 * J0):
        raise RuntimeError('ACTUAL_J0_OR_BUDGET_MISMATCH')
    if np.linalg.norm(F @ c - a) > 1e-10:
        raise RuntimeError('R32_COMPENSATOR_MISMATCH')
    with np.load(SMICA, allow_pickle=False) as z:
        matches = np.flatnonzero(z['target_ids'] == 'SMICA')
        if len(matches) != 1:
            raise RuntimeError('SMICA_TARGET_MISSING')
        smica_B = z['residual_B'][matches[0]].astype(float)
        smica_scale = float(np.linalg.norm(smica_B))
    if abs(smica_scale - contract['identified_response']['comparator']['K_CMB']) > 1e-14:
        raise RuntimeError('SMICA_SAVED_COMPARATOR_MISMATCH')
    v = np.zeros(24)
    v[12:] = Y[4, 12:]
    v /= np.linalg.norm(v)
    compensators = []
    for amplitude in (0.0, 1e-6, 1e-5, 1e-4):
        s = s0 + amplitude*v
        U = U0 - amplitude*np.outer(c, v)
        res = F @ U + np.outer(a, s) - Y
        compensators.append({'amplitude_K_CMB': amplitude,
                             'center_shift_B_norm_K_CMB': float(np.linalg.norm(s[12:]-s0[12:])),
                             'budget_K_CMB': float(np.linalg.norm(D[:, None]*U)),
                             'reconstruction_max_abs_K_CMB': float(np.max(np.abs(res))),
                             'reconstruction_Frobenius_K_CMB': float(np.linalg.norm(res))})
    rho_min = math.sqrt(J0)
    curves = []
    for multiple in (1, 1.25, 1.5, 2, 3, 5, 10):
        rho = rho_min*multiple
        excess = rho*rho-J0
        if excess < -1e-12:
            raise RuntimeError('NEGATIVE_RADIUS_SQUARED')
        # The exact boundary is represented by construction, not via a clamp
        # of an unresolved floating negative inherited from repair_05.
        radius = 0.0 if multiple == 1 else math.sqrt(excess/ell2)
        curves.append({'rho_multiple_algebraic_minimum': multiple,
                       'rho_K_CMB': rho,
                       's_ball_radius_K_CMB': radius,
                       'B_ball_radius_K_CMB': radius,
                       'scope': 'CONDITIONAL_SENSITIVITY_ONLY_NO_PHYSICAL_RHO_UPPER'})
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT/'ACTUAL_GEOMETRY.npz', Y=Y, F=F, a=a, D=D, C=C,
                        s0=s0, U0=U0, residual=residual, compensator_c=c,
                        compensation_direction_v=v, smica_residual_B=smica_B,
                        labels=np.asarray(labels))
    out = {'bands_GHz':bands, 'coordinate_order':labels, 'units':'K_CMB',
           'ell':ell, 'J0_K_CMB_squared':J0, 'rho_min_algebraic_K_CMB':rho_min,
           'center_24_K_CMB':s0.tolist(), 'center_B_norm_K_CMB':float(np.linalg.norm(s0[12:])),
           'actual_Y_norm_K_CMB':float(np.linalg.norm(Y)),
           'actual_residual_Frobenius_K_CMB':float(np.linalg.norm(residual)),
           'SMICA_B_comparator_K_CMB':smica_scale,
           'compensators':compensators, 'conditional_curves':curves,
           'claim':'ACTUAL_Y_CONSUMED_CONDITIONAL_COMMON_RESPONSE; NO_PHYSICAL_UPPER_RHO'}
    save_json(OUT/'GEOMETRY.json',out)
    return out


def load_spin_math():
    spec = importlib.util.spec_from_file_location('retained_full7_math', MATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def coordinate_weights(ring: np.ndarray, nside: int, hp, math_module) -> tuple[np.ndarray,np.ndarray]:
    theta, phi = hp.pix2ang(nside, ring, nest=False)
    cosine, sine = np.cos(theta/2), np.sin(theta/2)
    area = 4*math.pi/(12*nside*nside)
    wq = np.empty((24,len(ring)))
    wu = np.empty_like(wq)
    row = 0
    for pol in ('E','B'):
        for ell in (2,3):
            for m in range(ell+1):
                phase = np.exp(1j*m*phi)
                yp = np.conj(math_module.spin_y(ell,m,2,cosine,sine,phase))
                ym = np.conj(math_module.spin_y(ell,m,-2,cosine,sine,phase))
                if pol == 'E':
                    q = -area*(yp+ym)/2
                    u = -1j*area*(yp-ym)/2
                else:
                    q = 1j*area*(yp-ym)/2
                    u = -area*(yp+ym)/2
                if m == 0:
                    wq[row],wu[row] = q.real,u.real
                    row += 1
                else:
                    wq[row],wu[row] = math.sqrt(2)*q.real,math.sqrt(2)*u.real
                    wq[row+1],wu[row+1] = -math.sqrt(2)*q.imag,-math.sqrt(2)*u.imag
                    row += 2
    assert row == 24
    return wq,wu


def noise(contract: dict) -> dict:
    import healpy as hp
    frozen = json.loads(FROZEN.read_text())['products']
    with np.load(S7,allow_pickle=False) as z:
        chosen = z['s7_mask_nest64'].astype(bool)
        retained = z['retained_ring64']
    if chosen.shape != (49152,) or chosen.sum() != 30021 or len(retained)!=30021:
        raise RuntimeError('S7_SOURCE_DRIFT')
    math_module = load_spin_math()
    sig_by_band = {}
    receipts = {}
    for band in BANDS:
        key = str(band)
        meta = frozen[key]
        path = Path(meta['path'])
        if path.stat().st_size != meta['size_bytes']:
            raise RuntimeError(f'MAP_SIZE_DRIFT_{key}')
        from astropy.io import fits
        started = time.monotonic()
        sigma = np.zeros(24)
        row_count = 0
        extrema = {'min_eigen': math.inf, 'min_QQ':math.inf,'min_UU':math.inf,'max_abs_QU':0.0}
        with fits.open(path,memmap=True,lazy_load_hdus=True) as hdul:
            hdu = hdul[meta['hdu_index']]
            h = hdu.header
            for field,value in [('NSIDE',meta['nside']),('ORDERING','NESTED'),('COORDSYS','GALACTIC'),(meta['pol_keyword'],'COSMO')]:
                if str(h[field]).strip()!=str(value):
                    raise RuntimeError(f'MAP_HEADER_DRIFT_{key}_{field}')
            for field in ('Q_STOKES','U_STOKES','QQ_COV','QU_COV','UU_COV'):
                col = hdu.columns[field]
                if col.unit not in (meta['unit_raw'], meta['unit_raw']+'^2', '('+meta['unit_raw']+')^2'):
                    raise RuntimeError(f'MAP_COLUMN_UNIT_{key}_{field}_{col.unit}')
            data=hdu.data
            child=(meta['nside']//64)**2
            # NESTED children are consecutive; omit unselected parents entirely.
            for lo_parent in range(0,49152,16):
                parents=np.flatnonzero(chosen[lo_parent:lo_parent+16])+lo_parent
                for parent in parents:
                    start=int(parent)*child;stop=start+child
                    native_rows=data[start:stop]
                    qq=np.asarray(native_rows['QQ_COV'],dtype=float)
                    qu=np.asarray(native_rows['QU_COV'],dtype=float)
                    uu=np.asarray(native_rows['UU_COV'],dtype=float)
                    if not (np.isfinite(qq).all() and np.isfinite(qu).all() and np.isfinite(uu).all()):
                        raise RuntimeError(f'NONFINITE_MARGINAL_COV_{key}_{parent}')
                    scale=np.maximum.reduce((np.abs(qq),np.abs(qu),np.abs(uu),np.full(child,np.finfo(float).tiny)))
                    mineig=(qq+uu-np.hypot(qq-uu,2*qu))/2
                    bad=mineig < -64*np.finfo(float).eps*scale
                    if np.any(bad):
                        raise RuntimeError(f'NONPSD_MARGINAL_COV_{key}_{parent}_{int(np.count_nonzero(bad))}')
                    extrema['min_eigen']=min(extrema['min_eigen'],float(mineig.min()))
                    extrema['min_QQ']=min(extrema['min_QQ'],float(qq.min()))
                    extrema['min_UU']=min(extrema['min_UU'],float(uu.min()))
                    extrema['max_abs_QU']=max(extrema['max_abs_QU'],float(np.max(np.abs(qu))))
                    nest=np.arange(start,stop,dtype=np.int64)
                    ring=hp.nest2ring(meta['nside'],nest)
                    wq,wu=coordinate_weights(ring,meta['nside'],hp,math_module)
                    variance=(wq*wq)*qq + 2*wq*wu*qu + (wu*wu)*uu
                    if np.min(variance) < -1e-27:
                        raise RuntimeError(f'NEGATIVE_WEIGHTED_VARIANCE_{key}_{parent}')
                    # Roundoff-level negative contractions of a PSD 2x2 block
                    # represent exact zero and are logged by the source PSD test.
                    sigma += np.sqrt(np.maximum(variance,0)).sum(axis=1)
                    row_count += child
                if lo_parent % 8192 == 0:
                    save_json(OUT/f'NOISE_PROGRESS_{key}.json',{'band':band,'last_parent_exclusive':lo_parent+16,
                              'selected_rows_consumed':row_count,'elapsed_seconds':time.monotonic()-started})
        if row_count != int(chosen.sum())*child:
            raise RuntimeError(f'NOISE_ROW_COUNT_{key}')
        sig_by_band[key]=sigma.tolist()
        receipts[key]={'source_path':str(path),'source_sha256_from_frozen_manifest':meta['sha256'],
                       'bytes_from_frozen_manifest':meta['size_bytes'],'native_nside':meta['nside'],
                       'selected_native_pixels':row_count,'header':{'ordering':'NESTED','coordinates':'GALACTIC',
                       'polarization':'COSMO','map_unit':meta['unit_raw']},'covariance_extrema':extrema,
                       'elapsed_seconds':time.monotonic()-started}
        save_json(OUT/'NOISE_PARTIAL.json',{'bands_complete':list(sig_by_band),'per_band_sigma_K_CMB':sig_by_band,
                  'receipts':receipts})
    marginal_sigma=np.asarray(list(sig_by_band.values()))
    # Each raw Y(b,i) has its own channel; the simultaneous 168-vector bound
    # therefore sums squares across both band and coordinate.
    raw_variance_sum=float(np.sum(marginal_sigma*marginal_sigma))
    with np.load(OUT/'ACTUAL_GEOMETRY.npz',allow_pickle=False) as z:
        C=z['C']; a=z['a']
    h=C@a/float(a@C@a)
    center_sigma=np.sum(np.abs(h[:,None])*marginal_sigma,axis=0)
    center_variance_sum=float(np.sum(center_sigma*center_sigma))
    raw_radii={str(alpha):math.sqrt(raw_variance_sum/alpha) for alpha in (0.1,0.05,0.01)}
    center_radii={str(alpha):math.sqrt(center_variance_sum/alpha) for alpha in (0.1,0.05,0.01)}
    out={'model':'zero_mean_released_native_QQ_QU_UU_marginals_only; unspecified_cross_pixel_and_cross_band_correlations_any_PSD_completion',
         'per_band_sigma_worst_coordinate_K_CMB':sig_by_band,
         'actual_Y_168_vector_variance_bound_sum_K_CMB_squared':raw_variance_sum,
         'actual_Y_168_simultaneous_Euclidean_Chebyshev_radii_K_CMB':raw_radii,
         'center_linear_channel_weights':h.tolist(),
         'center_24_sigma_worst_coordinate_K_CMB':center_sigma.tolist(),
         'center_24_variance_bound_sum_K_CMB_squared':center_variance_sum,
         'center_24_simultaneous_Euclidean_Chebyshev_radii_K_CMB':center_radii,
         'cross_coordinate_covariance_bound':'abs Cov(z_i,z_j) <= sigma_worst_i * sigma_worst_j; not a joint covariance matrix',
         'receipts':receipts,
         'scope':'statistical_marginal_noise_only; biases/systematics and calibration excluded'}
    save_json(OUT/'NOISE.json',out)
    return out


def scalar_support_oracle(directions_7x24: np.ndarray) -> float:
    """Sharp scalar SD over all PSD completions of released Q/U blocks.

    The input direction must be prespecified for a scalar confidence bound.
    This callable re-streams native FITS blocks and uses the same spin weights;
    it is not a dense covariance or an independence approximation.
    """
    import healpy as hp
    from astropy.io import fits
    d=np.asarray(directions_7x24,dtype=float)
    if d.shape!=(7,24) or not np.isfinite(d).all():
        raise ValueError('DIRECTION_7x24_REQUIRED')
    frozen=json.loads(FROZEN.read_text())['products']
    with np.load(S7,allow_pickle=False) as z:
        chosen=z['s7_mask_nest64'].astype(bool)
    if chosen.shape!=(49152,) or chosen.sum()!=30021:
        raise RuntimeError('S7_SOURCE_DRIFT')
    spin=load_spin_math()
    total=0.0
    for bi,band in enumerate(BANDS):
        meta=frozen[str(band)];path=Path(meta['path'])
        if path.stat().st_size!=meta['size_bytes']:
            raise RuntimeError('SOURCE_SIZE_DRIFT')
        nside=meta['nside'];child=(nside//64)**2
        with fits.open(path,memmap=True,lazy_load_hdus=True) as hdul:
            data=hdul[meta['hdu_index']].data
            for parent in np.flatnonzero(chosen):
                start=int(parent)*child;stop=start+child
                rows=data[start:stop]
                qq=np.asarray(rows['QQ_COV'],float)
                qu=np.asarray(rows['QU_COV'],float)
                uu=np.asarray(rows['UU_COV'],float)
                if not (np.isfinite(qq).all() and np.isfinite(qu).all() and np.isfinite(uu).all()):
                    raise RuntimeError('NONFINITE_COVARIANCE')
                ring=hp.nest2ring(nside,np.arange(start,stop,dtype=np.int64))
                wq,wu=coordinate_weights(ring,nside,hp,spin)
                lq=d[bi]@wq;lu=d[bi]@wu
                variance=lq*lq*qq+2*lq*lu*qu+lu*lu*uu
                if np.min(variance)<-1e-27:
                    raise RuntimeError('NONPSD_WEIGHTED_DIRECTION')
                total+=float(np.sqrt(np.maximum(variance,0)).sum())
    return total


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('phase',choices=('geometry','noise'))
    args=ap.parse_args()
    started=time.monotonic()
    contract=json.loads(CONTRACT.read_text())
    source_check(contract)
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        result=geometry(contract) if args.phase=='geometry' else noise(contract)
        status='COMPLETED'
    except Exception as ex:
        result={'exception_type':type(ex).__name__,'message':str(ex)}
        status='FIRST_FAILURE'
        save_json(OUT/f'FIRST_FAILURE_{args.phase}.json',result)
        raise
    finally:
        save_json(OUT/f'RUN_{args.phase}.json',{'packet_id':PACKET,'input_identity':INPUT,
                  'agent_id':'/root/rc_7f1ac3df12ebbc36','phase':args.phase,'status':status,
                  'elapsed_seconds':time.monotonic()-started,
                  'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'contract_sha256':sha(CONTRACT),'pid':os.getpid()})
    print(json.dumps({'phase':args.phase,'status':status,'elapsed_seconds':time.monotonic()-started,
                      'output_keys':list(result)},sort_keys=True))


if __name__=='__main__':
    main()
