"""Cache-only matched-radius summary repair for R36-02 SAME02.

No source rows, Fourier modes, quadrature nodes, models or covariance matrices are
generated here. The original candidate remains byte-identical.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
EXTERNAL = Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual')
BASE_CANDIDATE = 'dd3cb2d77c97e33380ec06e04bc5465f65129dc319f8795dc30e3bc84b3e877b'
RADII = (5, 10, 20)
CASES = ('north_ICRS_nz_nonnegative', 'south_ICRS_nz_negative', 'exclude_FP', 'exclude_TF')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def source_cache_check():
    manifest_path = BASE/'ARTIFACT_MANIFEST.json'
    if sha256(manifest_path) != BASE_CANDIDATE:
        raise ValueError('base candidate manifest identity mismatch')
    manifest = json.loads(manifest_path.read_text())
    for name in ('RESULT.json', 'SENSITIVITY.json', 'INTERPRETATION.md',
                 'TABLE.csv', 'FIGURE.png', 'run_correlated.py',
                 'run_sensitivity.py', 'validate_extensions.py', 'CONTROLS.json'):
        path = BASE/name
        if sha256(path) != manifest['product_files'][name]['sha256']:
            raise ValueError(f'base product changed: {name}')
    for name in ('STAGE_C.npz', 'SENSITIVITY_MATRICES.npz',
                 'RESULT_MATRICES.npz', 'PV_FACTORS.npz'):
        path = EXTERNAL/name
        if sha256(path) != manifest['external_files'][name]['sha256']:
            raise ValueError(f'retained cache changed: {name}')
    return manifest


def matched_radius_summary(full_total: np.ndarray, subset: np.ndarray,
                           radii=RADII) -> list[dict]:
    if full_total.shape != (108, 108) or subset.shape != (108, 108):
        raise ValueError('expected retained 108 x 108 common-field matrices')
    rows = []
    for ir, radius in enumerate(radii):
        sl = slice(36 * ir, 36 * (ir + 1))
        reference = full_total[sl, sl]
        block = subset[sl, sl]
        trace = float(np.trace(block))
        relative = float(np.linalg.norm(block - reference) / np.linalg.norm(reference))
        ratio = trace / float(np.trace(reference))
        eigen = np.linalg.eigvalsh(block)
        rows.append({
            'R_hinv_Mpc': radius,
            'trace': trace,
            'trace_ratio_to_full_sample': ratio,
            'frobenius_relative_to_full_sample': relative,
            'rank_1e_10': int(np.sum(eigen > 1e-10 * eigen[-1])),
        })
    return rows


def cache_matrices():
    with np.load(EXTERNAL/'STAGE_C.npz', allow_pickle=False) as z:
        full = z['total']
    with np.load(EXTERNAL/'SENSITIVITY_MATRICES.npz', allow_pickle=False) as z:
        subsets = {name: z[name] for name in CASES}
    return full, subsets


def main():
    manifest = source_cache_check()
    full, subsets = cache_matrices()
    old = json.loads((BASE/'SENSITIVITY.json').read_text())
    repaired = json.loads((BASE/'SENSITIVITY.json').read_text())
    assert set(repaired['results']) == set(CASES)
    for name in CASES:
        rows = matched_radius_summary(full, subsets[name])
        # Only the two wrong comparison fields change in the old R=10/20 rows.
        for ir, row in enumerate(rows):
            previous = old['results'][name]['bands_sum_blocks'][ir]
            for field in ('R_hinv_Mpc', 'trace', 'rank_1e_10'):
                if row[field] != previous[field]:
                    raise AssertionError(f'unaffected summary drift: {name} {ir} {field}')
            if ir == 0 and row != previous:
                raise AssertionError(f'R=5 summary drift: {name}')
            repaired['results'][name]['bands_sum_blocks'][ir] = row
    repaired['repair'] = {
        'kind': 'SAME02 matched-radius cache-only comparison',
        'base_packet_id': '0c0fab5631cb19001cba35e3da1de5cd44d64dc0157950afb82d383496472c40',
        'base_candidate_identity': 'sha256:' + BASE_CANDIDATE,
        'source_cache_sha256': {
            key: manifest['external_files'][key]['sha256']
            for key in ('STAGE_C.npz', 'SENSITIVITY_MATRICES.npz')},
        'affected_fields': ['trace_ratio_to_full_sample',
                            'frobenius_relative_to_full_sample'],
        'source_modes_or_covariance_recomputed': False,
    }
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE/'SENSITIVITY.json').write_text(json.dumps(repaired, indent=2, sort_keys=True)+'\n')
    result = json.loads((BASE/'RESULT.json').read_text())
    result['footprint_method_sensitivity'] = 'repair_01/SENSITIVITY.json'
    result['repair'] = {
        'kind': 'SAME02 matched-radius sensitivity summary only',
        'base_candidate_identity': 'sha256:' + BASE_CANDIDATE,
        'base_result_sha256': manifest['product_files']['RESULT.json']['sha256'],
        'retained_covariances_unchanged': True,
    }
    (HERE/'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'cases': len(CASES), 'summaries': len(CASES)*len(RADII),
        'exclude_FP_R20_ratio': repaired['results']['exclude_FP']['bands_sum_blocks'][2]
                                ['trace_ratio_to_full_sample'],
        'base_candidate_unchanged': sha256(BASE/'ARTIFACT_MANIFEST.json') == BASE_CANDIDATE}))


if __name__ == '__main__':
    main()
