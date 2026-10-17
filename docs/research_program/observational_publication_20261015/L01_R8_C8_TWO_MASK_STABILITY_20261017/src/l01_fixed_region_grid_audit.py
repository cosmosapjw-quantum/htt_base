"""Fixed-band, fixed-region quadrature audit for existing L01 checkpoints.

No new native Q/U transform or data download. Original coarse binary pixels
are interpreted as fixed regions: each NESTED child inherits its parent's mask.
Changing the integration grid is NOT a replacement of the archived estimator.
Only scalar PMASK FITS are reread to reproduce the original region identities.
"""
from __future__ import annotations
import argparse
import importlib
import json
from pathlib import Path
import sys
import time
import zipfile
import numpy as np

SCHEMA = 'htt.L01_fixed_region_output_quadrature/1'
BASELINE_RTOL = 2e-9  # existing producer closure scale; never a physical accuracy
GRAM_CONDITION_LIMIT = 1e8  # diagnostics refuse ill-conditioned normal equations


def _real(value, ndim):
    x = np.asarray(value)
    if x.ndim != ndim or x.dtype.kind not in 'fiu' or np.iscomplexobj(x):
        raise ValueError('REAL_ARRAY_SHAPE_OR_TYPE')
    x = x.astype(np.float64, copy=False)
    if not np.isfinite(x).all():
        raise ValueError('NONFINITE_ARRAY')
    return x


def _norm(x, axis=None):
    z = np.linalg.norm(x, axis=axis)
    if not np.isfinite(z).all():
        raise ValueError('NUMERICAL_NORM_RANGE')
    return z


def _power_two(n):
    return isinstance(n, (int, np.integer)) and not isinstance(n, bool) and n > 0 and n & (n-1) == 0


def refine_nested_mask(mask, base_nside, nside):
    """Exact mask semantics in the NESTED hierarchy, not rethresholded data."""
    m = np.asarray(mask)
    if (not _power_two(base_nside) or not _power_two(nside) or nside < base_nside
            or m.dtype != np.bool_ or m.shape != (12*base_nside**2,)):
        raise ValueError('NESTED_MASK_OR_REFINEMENT_INVALID')
    count = (nside//base_nside)**2
    return np.repeat(m, count)


class Moments:
    """Bounded-memory equal-area least squares, shared Q/U support."""
    def __init__(self, ncoeff, nfields):
        if min(ncoeff, nfields) < 1:
            raise ValueError('MOMENT_DIMENSIONS')
        self.g = np.zeros((ncoeff, ncoeff))
        self.b = np.zeros((ncoeff, nfields))
        self.selected = 0

    def add(self, design, data, mask):
        a, d, m = _real(design, 2), _real(data, 2), np.asarray(mask)
        if (m.ndim != 1 or m.dtype != np.bool_ or a.shape != (2*m.size, self.g.shape[0])
                or d.shape != (2*m.size, self.b.shape[1])):
            raise ValueError('MOMENT_BLOCK_SHAPE')
        rows = np.r_[m, m]
        x, y = a[rows], d[rows]
        self.g += x.T @ x
        self.b += x.T @ y
        self.selected += int(m.sum())

    def solve(self, solid_angle):
        if not np.isfinite(solid_angle) or solid_angle <= 0:
            raise ValueError('PIXEL_SOLID_ANGLE')
        return solve_moments(self.g*solid_angle, self.b*solid_angle, self.selected)


def solve_moments(gram, rhs, selected_pixels):
    g, b = _real(gram, 2), _real(rhs, 2)
    if not g.size or g.shape[0] != g.shape[1] or b.shape[0] != g.shape[0] or selected_pixels <= 0:
        raise ValueError('NORMAL_EQUATION_SHAPE')
    scale = max(float(_norm(g)), np.finfo(float).tiny)
    if float(_norm(g-g.T))/scale > 1e-13:
        raise ValueError('GRAM_NOT_SYMMETRIC')
    # Products A.T A are symmetric; average only antisymmetric roundoff.
    g = (g+g.T)/2
    ev = np.linalg.eigvalsh(g)
    if ev[0] <= 0 or ev[-1]/ev[0] > GRAM_CONDITION_LIMIT:
        raise ValueError('GRAM_NOT_POSITIVE_OR_CONDITIONED')
    y = np.linalg.solve(g, b)
    denom = max(float(ev[-1]*_norm(y)+_norm(b)), np.finfo(float).tiny)
    residual = float(_norm(g@y-b)/denom)
    if residual > 1e-12:
        raise ValueError('NORMAL_SOLVE_RESIDUAL')
    return {'gram': g, 'rhs': b, 'coefficients': y, 'selected_pixels': int(selected_pixels),
            'lambda_min': float(ev[0]), 'gram_condition': float(ev[-1]/ev[0]),
            'design_condition': float(np.sqrt(ev[-1]/ev[0])),
            'normal_residual_relative': residual}


def moment_change(old, new):
    """Exact finite-grid identity; bound is for this measured step only.

    dy = G_new^-1 [(b_new-b_old)-(G_new-G_old)y_old].
    It is not a bound on the error to a continuum or physical sky target.
    """
    forcing = (new['rhs']-old['rhs'])-(new['gram']-old['gram'])@old['coefficients']
    predicted = np.linalg.solve(new['gram'], forcing)
    change = new['coefficients']-old['coefficients']
    scale = np.maximum(_norm(old['coefficients'], axis=0)+_norm(new['coefficients'], axis=0), np.finfo(float).tiny)
    residual = _norm(change-predicted, axis=0)/scale
    if np.max(residual) > 2e-11:
        raise ValueError('FINITE_GRID_IDENTITY_FAILED')
    return {'change': change, 'identity_residual_relative': residual,
            'finite_step_bound_K_CMB': _norm(forcing, axis=0)/new['lambda_min']}


def baseline_residual(measured, archived, reference):
    a, b = _real(measured, 2), _real(archived, 2)
    if a.shape != b.shape or not np.isfinite(reference) or reference < 0:
        raise ValueError('BASELINE_SHAPE_OR_REFERENCE')
    scale = max(float(_norm(a)), float(_norm(b)), float(reference), np.finfo(float).tiny)
    err = float(_norm(a-b)/scale)
    if err > BASELINE_RTOL:
        raise ValueError('BASELINE_NSIDE64_ARCHIVED_VECTOR_MISMATCH')
    return err



def mixed_step(first_low, first_high, second_low, second_high):
    """Grid/cutoff interaction: Delta_L at fine grid minus Delta_L at coarse."""
    a, b, c, d = (_real(v, 1) for v in (first_low, first_high, second_low, second_high))
    if not a.size or any(x.shape != a.shape for x in (b,c,d)):
        raise ValueError('MIXED_STEP_SHAPES')
    return (d-c)-(b-a)


def _jsonable(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, dict):
        return {k: _jsonable(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)):
        return [_jsonable(v) for v in x]
    return x


def run(band_dirs, root, native_receipt, nsides=(64, 128), chunk_pixels=16384):
    # Deliberately lazy: math/unit tests and --help do not need healpy or FITS.
    import l01_cutoff_band_diagnostics as base
    import l01_smica_processed_bands as producer
    import healpy as hp
    if (not 1 <= len(band_dirs) <= 3 or not nsides or nsides[0] != 64
            or any(n not in (64, 128, 256) for n in nsides)
            or list(nsides) != sorted(set(nsides)) or not 256 <= chunk_pixels <= 65536):
        raise ValueError('GRID_RUN_BOUNDS')
    runs = [base.load_run(p) for p in band_dirs]
    for lo, hi in zip(runs, runs[1:]):
        base.compare_runs(lo, hi)
    contract = runs[0]['contract']
    if (hp.__version__ != contract['healpy_version']
            or base.shared.digest(producer.__file__) != contract['analysis_code_sha256']
            or base.shared.digest(native_receipt) != contract['native_receipt_sha256']):
        raise ValueError('REPLAY_PRODUCER_VERSION_OR_SOURCE_MISMATCH')
    for name, expected in contract['dependency_sha256'].items():
        module = importlib.import_module(name)
        if base.shared.digest(module.__file__) != expected:
            raise ValueError('REPLAY_DEPENDENCY_BYTE_MISMATCH_'+name)
    native, _ = producer.verify_receipt(native_receipt, enforce_reported_pins=True)
    window, coarse, window_sha = producer.read_windows(root, hp, native)
    del window
    if window_sha != contract['native_window_sha256']:
        raise ValueError('FIXED_NATIVE_WINDOW_MISMATCH')
    nested = {name: hp.reorder(mask.astype(np.uint8), r2n=True).astype(bool) for name, mask in coarse.items()}
    names = tuple(base.MASKS)
    products = tuple(base.shared.PRODUCTS)
    keys = [(r['contract']['lmax'], p) for r in runs for p in products]
    all_alms = [r['arrays'][p] for r in runs for p in products]
    archived = {name: np.column_stack([
        base.shared._json(Path(folder)/(p+'.json'))['result']['masks'][name]['total_K_CMB']
        for folder in band_dirs for p in products]) for name in names}
    grids, grid_raw = [], []
    for nside in nsides:
        start = time.perf_counter(); npix = 12*nside**2
        masks = {name: hp.reorder(refine_nested_mask(m, 64, nside).astype(np.uint8), n2r=True).astype(bool)
                 for name, m in nested.items()}
        for name in names:
            if int(masks[name].sum()) != int(coarse[name].sum())*(nside//64)**2:
                raise ValueError('FIXED_REGION_AREA_CHANGED')
        data = np.empty((2, npix, len(keys)))
        for j, ((L, _), a) in enumerate(zip(keys, all_alms)):
            q, u = hp.alm2map_spin(a, nside, spin=2, lmax=L, mmax=L)
            data[0, :, j] = q; data[1, :, j] = u
            del q, u
        moments = {name: Moments(64, len(keys)) for name in names}
        for first in range(0, npix, chunk_pixels):
            stop = min(npix, first+chunk_pixels)
            theta, phi = producer.pix2ang_ring(nside, np.arange(first, stop, dtype=np.int64))
            design = producer.block_design(theta, phi, 2, 5)
            values = np.vstack((data[0, first:stop], data[1, first:stop]))
            for name in names:
                moments[name].add(design, values, masks[name][first:stop])
        del data
        solved = {name: moments[name].solve(4*np.pi/npix) for name in names}
        baseline = None
        if nside == 64:
            baseline = {name: baseline_residual(solved[name]['coefficients'], archived[name], 0.) for name in names}
        d = solved['three_way_intersection']['coefficients']-solved['common']['coefficients']
        subjects = {str(r['contract']['lmax']): base._derived_subjects({p:d[:,i*5+j] for j,p in enumerate(products)})
                    for i,r in enumerate(runs)}
        grids.append({'nside': nside, 'seconds': time.perf_counter()-start,
            'baseline_vector_residuals': baseline, 'masks': solved,
            'contrasts': subjects, 'cutoff_changes': {
                str(a['contract']['lmax'])+'_to_'+str(b['contract']['lmax']): {
                    p: subjects[str(b['contract']['lmax'])][p]-subjects[str(a['contract']['lmax'])][p]
                    for p in subjects[str(a['contract']['lmax'])]}
                for a,b in zip(runs,runs[1:])}})
        grid_raw.append(solved)
    changes = []
    for i, (old, new) in enumerate(zip(grid_raw, grid_raw[1:])):
        per_mask = {name: moment_change(old[name], new[name]) for name in names}
        delta = per_mask['three_way_intersection']['change']-per_mask['common']['change']
        by_subject = {}
        for col, (L, p) in enumerate(keys):
            x = grids[i]['contrasts'][str(L)][p]
            e = delta[:, col]
            by_subject[str(L)+'_'+p] = {field: {
                'increment_norm_K_CMB': float(_norm(e[ix])),
                'relative_to_old_target': float(_norm(e[ix])/_norm(x[ix])) if _norm(x[ix]) else None}
                for field, ix in base.low_indices().items()}
        mixed = {}
        for lo, hi in zip(runs, runs[1:]):
            L, H = (str(r['contract']['lmax']) for r in (lo, hi))
            for subject in grids[i]['contrasts'][L]:
                a0, a1 = (np.asarray(grids[i]['contrasts'][j][subject]) for j in (L,H))
                b0, b1 = (np.asarray(grids[i+1]['contrasts'][j][subject]) for j in (L,H))
                e = mixed_step(a0,a1,b0,b1)
                mixed[L+'_to_'+H+'_'+subject] = {field: {
                    'interaction_norm_K_CMB': float(_norm(e[ix])),
                    'relative_to_coarse_cutoff_step': float(_norm(e[ix])/_norm((a1-a0)[ix])) if _norm((a1-a0)[ix]) else None}
                    for field,ix in base.low_indices().items()}
        changes.append({'nsides': [nsides[i], nsides[i+1]], 'mask_moment_changes': per_mask,
                        'target_changes': by_subject, 'grid_cutoff_interaction': mixed})
    return _jsonable({'schema': SCHEMA, 'status': 'PASS_FIXED_REGION_QUADRATURE_ACCOUNTING',
        'cutoffs': [r['contract']['lmax'] for r in runs], 'nsides': list(nsides),
        'columns': keys, 'input_evidence': [{'contract': r['contract'], 'evidence':r['evidence']} for r in runs],
        'native_mask_receipt_sha256': base.shared.digest(native_receipt),
        'region': 'UNCHANGED_UNION_OF_ORIGINAL_NSIDE64_NESTED_PIXELS',
        'weights': 'EQUAL_SOLID_ANGLE_4PI_OVER_NPIX', 'fixed_harmonic_coefficients': True,
        'native_QU_transform_rerun': False, 'original_estimator_replaced': False,
        'gram_condition_limit': GRAM_CONDITION_LIMIT, 'chunk_pixels': chunk_pixels,
        'grids': grids, 'grid_changes': changes,
        'beam_applied_again': False, 'convergence_certified': False,
        'infinite_tail_bound': 'NOT_ESTABLISHED', 'physical_sky_claim': False,
        'paper_gate': 'NOT_READY_TO_SUBMIT'})


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--band-dirs', nargs='+', required=True)
    p.add_argument('--root', required=True)
    p.add_argument('--native-receipt', required=True)
    p.add_argument('--nsides', type=int, nargs='+', default=[64,128])
    p.add_argument('--chunk-pixels', type=int, default=16384)
    p.add_argument('--out', required=True)
    a=p.parse_args(argv)
    try:
        import l01_split_checkpoint_spectra as shared
        if Path(a.out).exists() or Path(a.out).is_symlink():
            raise ValueError('OUTPUT_EXISTS_NOT_OVERWRITTEN')
        report=run(a.band_dirs,a.root,a.native_receipt,a.nsides,a.chunk_pixels)
        report['code_sha256']=shared.digest(__file__)
        report['helper_code_sha256']={name:shared.digest(sys.modules[name].__file__) for name in
             ('l01_cutoff_band_diagnostics','l01_split_checkpoint_spectra')}
        shared.write_new_json(a.out,report)
    except (ValueError,OSError,ImportError,KeyError,TypeError,FloatingPointError,np.linalg.LinAlgError,zipfile.BadZipFile) as e:
        print(json.dumps({'status':'BLOCKED','error_type':type(e).__name__,'error':str(e)}),file=sys.stderr)
        return 2
    print(json.dumps({'status':report['status'],'cutoffs':report['cutoffs'],'nsides':report['nsides'],
        'baseline':report['grids'][0]['baseline_vector_residuals'],
        'full_grid_changes':[{'nsides':x['nsides'],'targets':{k:v for k,v in x['target_changes'].items() if k.endswith('_full')},
             'interactions':{k:v for k,v in x['grid_cutoff_interaction'].items() if k.endswith('_full')}} for x in report['grid_changes']],
        'convergence_certified':False,'out':a.out,'paper_gate':report['paper_gate']},indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
