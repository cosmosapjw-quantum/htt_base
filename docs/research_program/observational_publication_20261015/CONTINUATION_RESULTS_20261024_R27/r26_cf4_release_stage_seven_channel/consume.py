#!/usr/bin/env python3
"""Release-stage singleton identification and seven-channel fixed-E1 response.

The identified coefficients are deterministic data summaries under a stated
additive model.  Mixed rows never influence their selection.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
TABLE = Path('/mnt/extdrive/workdir/htt_open_data/cf4/J_ApJ_944_94/table3.dat')
OLD = Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_fp_pooling_closure/RESULT.json')
SOURCE = ROOT / 'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz'
E1 = ROOT / 'docs/research_program/cf4_schur_loop8_20261015/results/result.json'
MODEL = ROOT / 'htt/obsstat/cf4_apparent_kinematic_distribution.py'
RUNNER = ROOT / 'scripts/run_htt_cf4_schur_20261015.py'
CONTRACT_ROOT = Path('/mnt/extdrive/workdir/htt_open_data/r26_existing_results_dag_consumption')
ACQUISITION = Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_1490017_release_source_acquisition')
Y0 = ROOT / 'docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/SDSS_SOURCE_NULL_20261018/SOURCE_ANALYSIS/SUMMARY.json'
SHA = {
    TABLE.parent/'ReadMe': '2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4',
    TABLE.parent/'table2.dat': '8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f',
    TABLE: 'c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d',
    TABLE.parent/'table4.dat': 'b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94',
    OLD: '8d15167ecc1cedd8ccb0efde42b66155a3de885c254bc838d89873d7e70d4b0a',
    SOURCE: '86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c',
    E1: 'a2d7777cea0aab1a80af2944ae49b39b8bff718e1a2804f2ec96829458346995',
    MODEL: '843b19e464817d14455df68e9043a93cc71cc7449ab339052c3ddfe1c7298c19',
    RUNNER: '365798845bcc640ba65396aa22c89ce831b07624cd0f92ba24ae5b5b8605a419',
    CONTRACT_ROOT/'H02_FINAL_SOURCE_MODEL.md': 'e6f64e65770760e6a8d057f5b26d01054587616471fc51406100c24af20de313',
    CONTRACT_ROOT/'RETURN_H02.json': 'a83e933ecc5955d1ab8933ddbc9bbb1dbf7a4eb33ecb051bd08cece03cfdb3bc',
    ACQUISITION/'RETURN.json': '42b001905bcd4ffb641adb64714422e976484564b32d50d5afda54e1d1aeab0c',
    ACQUISITION/'SOURCE_OPERATOR_CELLS.json': '5723b75463998f28b2f48d9f2b62b68c2e807aa2fd3d6caab3aeaeadf89834c1',
    ACQUISITION/'FP_groups-MCMC-erratum.ipynb': '785c6fca0513553b25678c1a78090c17aab58999516a805a7119a2221e6ee485',
    ACQUISITION/'FP_catal-erraturm.ipynb': 'd730a9037ce9d2d005e85bab8b7681d6e1e6290c0d0f1e091c1cff5dc6a7aa80',
    ACQUISITION/'ALL_groups_catal-erratum-20221125.ipynb': '30c0534d725b071089708639b3ca6c3b4ece70aae9ae04ec90b688fedea3f517',
    Y0: '9853bd0210774bc0522458f987f3642367f6aa6a5c3113fb1b6dd21acb5a10e0',
}
ID_SHA = 'f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88'
METHODS = ('SNIa', 'FP', 'TFR', 'SBFm', 'SBFir', 'SNII')
WIDTHS = {'round_nearest': F(1, 2), 'one_place_outer': F(1)}
WORK = Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_release_stage_seven_channel')
INPUT = WORK / 'INPUT.json'
CONTRACT = Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_actual_source_model_review/CONTRACT.md')
REVIEW = CONTRACT.with_name('ACTUAL_RESULT_REVIEW.json')
FROZEN = Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_final_group_operator_consumer/FROZEN_INPUT_SOURCE_LAYOUT.json')
SOURCE_SEALS = {
    INPUT: '2fe3811319d2dd7b6b1d43507339f410c559036ab8b0e044a5dcfa413830f004',
    CONTRACT: 'cdf94aaf6d39a01baae0d2fc03342032b1eb5f82ef34555e83ca8631d43f7992',
    REVIEW: '5b3998c322d8262b96b7922f90e0b30011ab10c73b2ffb8365ff812262ccfc13',
    FROZEN: 'bdb71210368d44cf4fc52e844d4d1e2577e07d306fb25a1de3d202c04b0e2adf',
}
MODEL_SLICES = ((100, 106, 107, 112), (117, 123, 124, 129),
                (133, 139, 140, 145), (150, 156, 157, 162),
                (165, 171, 172, 177), (178, 184, 185, 190))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def verify_sources() -> dict:
    seals = SHA | SOURCE_SEALS
    found = {str(p): digest(p) for p in seals}
    for p, expected in seals.items():
        if found[str(p)] != expected:
            raise RuntimeError(f'IMMUTABLE_SOURCE_MISMATCH {p} {found[str(p)]} != {expected}')
    return found


def quantum(token: str) -> F:
    return F(1, 10 ** len(token.split('.', 1)[1])) if '.' in token else F(1)


def interval(token: str, width: F) -> tuple[F, F]:
    x = F(token)
    delta = width * quantum(token)
    return x - delta, x + delta


def parse_table3(path: Path) -> list[dict]:
    rows = []
    seen = set()
    # Optional CDS fields may be omitted after a complete physical field.
    # These are the ReadMe's zero-based half-open numeric/count byte spans.
    fields = ((88, 90), (91, 97), (98, 99), (100, 106), (107, 112),
              (113, 116), (117, 123), (124, 129), (130, 132),
              (133, 139), (140, 145), (146, 149), (150, 156),
              (157, 162), (163, 164), (165, 171), (172, 177),
              (178, 184), (185, 190))
    with path.open('r', encoding='ascii', newline='') as f:
        for line_no, line in enumerate(f, 1):
            s = line[:-1] if line.endswith('\n') else line
            if s.endswith('\r'):
                s = s[:-1]
            physical_width = len(s)
            if physical_width < 87 or physical_width > 190:
                raise ValueError(f'TABLE3_WIDTH line={line_no} width={physical_width}')
            if any(ord(ch) < 32 or ord(ch) > 126 for ch in s):
                raise ValueError(f'TABLE3_NONPRINTABLE_ASCII line={line_no}')
            for start, end in fields:
                if start < physical_width < end and s[start:physical_width].strip(' '):
                    raise ValueError(f'TABLE3_PARTIAL_NONBLANK_FIELD line={line_no} start={start} end={end}')
            s = s.ljust(190, ' ')
            pgc = int(s[0:7])
            if pgc in seen:
                raise ValueError(f'DUPLICATE_TABLE3_PGC {pgc}')
            seen.add(pgc)
            rows.append({'pgc': pgc, 'line': line_no, 'dmzp': s[8:14].strip(),
                         'dmav': s[15:21].strip(), 'e_dmav': s[22:27].strip(),
                         'dmcal': s[91:97].strip(),
                         'methods': [(s[ml:mh].strip(), s[el:eh].strip())
                                     for ml, mh, el, eh in MODEL_SLICES],
                         'count_fp': s[113:116].strip()})
    return rows


def parse_table3_singletons(path: Path) -> list[dict]:
    """Read only singleton numeric fields; do not load mixed target means."""
    rows = []
    with path.open('r', encoding='ascii', newline='') as stream:
        for line_no, line in enumerate(stream, 1):
            s = line.rstrip('\r\n').ljust(190, ' ')
            methods = [(s[ml:mh].strip(), s[el:eh].strip())
                       for ml, mh, el, eh in MODEL_SLICES]
            if sum(bool(dm and err) for dm, err in methods) != 1:
                continue
            rows.append({'pgc': int(s[0:7]), 'line': line_no,
                         'dmzp': s[8:14].strip(), 'dmav': s[15:21].strip(),
                         'e_dmav': s[22:27].strip(), 'methods': methods})
    if len(rows) != 36691:
        raise RuntimeError(f'SINGLETON_SOURCE_CARDINALITY_CHANGED {len(rows)}')
    return rows


def intersect(a: tuple[F, F], b: tuple[F, F]) -> tuple[F, F]:
    return max(a[0], b[0]), min(a[1], b[1])


def difference(a: tuple[F, F], b: tuple[F, F]) -> tuple[F, F]:
    return a[0] - b[1], a[1] - b[0]


def translate(a: tuple[F, F], x: F) -> tuple[F, F]:
    return a[0] + x, a[1] + x


def midpoint(a: tuple[F, F]) -> F:
    if a[0] > a[1]:
        raise ValueError('EMPTY_INTERVAL')
    return (a[0] + a[1]) / 2


def pair_indices(row: dict) -> list[int]:
    return [j for j, (dm, err) in enumerate(row['methods']) if dm and err]


def identify_singletons(rows: list[dict], width: F) -> dict:
    """Exact joint reduction; inspect no mixed numeric values."""
    ds: list[tuple[F, F] | None] = [None] * 6
    hs: list[tuple[F, F] | None] = [None] * 6
    z: tuple[F, F] | None = None
    counts = [0] * 6
    for row in rows:
        ids = pair_indices(row)
        if len(ids) != 1:
            continue
        j = ids[0]
        counts[j] += 1
        dm, err = row['methods'][j]
        if not (row['dmav'] and row['e_dmav'] and row['dmzp']):
            return {'status': 'SINGLETON_MISSING_FIELD', 'witness': row['pgc'], 'method': METHODS[j]}
        if min(F(dm), F(err), F(row['dmav']), F(row['e_dmav']), F(row['dmzp'])) <= 0:
            return {'status': 'SINGLETON_INVALID_DOMAIN', 'witness': row['pgc'], 'method': METHODS[j]}
        im, ie, ia, it, iz = (interval(token, width) for token in
                                (dm, err, row['dmav'], row['e_dmav'], row['dmzp']))
        if ie[0] <= 0 or it[0] <= 0 or intersect(ie, it)[0] > intersect(ie, it)[1]:
            return {'status': 'SINGLETON_ERROR_INCOMPATIBLE', 'witness': row['pgc'], 'method': METHODS[j],
                    'method_error_interval': [str(x) for x in ie],
                    'combined_error_interval': [str(x) for x in it]}
        d_new, h_new, z_new = difference(ia, im), difference(iz, im), difference(ia, iz)
        ds[j] = d_new if ds[j] is None else intersect(ds[j], d_new)
        hs[j] = h_new if hs[j] is None else intersect(hs[j], h_new)
        z = z_new if z is None else intersect(z, z_new)
        if ds[j][0] > ds[j][1] or hs[j][0] > hs[j][1] or z[0] > z[1]:
            return {'status': 'SINGLETON_GLOBAL_INTERVAL_EMPTY', 'witness': row['pgc'], 'method': METHODS[j],
                    'D': [str(x) for x in ds[j]], 'H': [str(x) for x in hs[j]],
                    'Z': [str(x) for x in z]}
    absent = [METHODS[j] for j, count in enumerate(counts) if count == 0]
    if absent:
        return {'status': 'NO_SINGLETON_CHANNEL', 'channels': absent, 'counts': counts}
    assert z is not None and all(v is not None for v in ds + hs)
    if not ds[0][0] <= 0 <= ds[0][1]:
        return {'status': 'FIXED_SNIA_REFERENCE_INCOMPATIBLE', 'D_SNIa': [str(x) for x in ds[0]]}
    ds[0] = (F(), F())
    zstar = z
    for d, h in zip(ds, hs):
        zstar = intersect(zstar, (d[0] - h[1], d[1] - h[0]))
    if zstar[0] > zstar[1]:
        return {'status': 'GLOBAL_ZETA_INTERVAL_EMPTY', 'Zstar': [str(x) for x in zstar],
                'D': [[str(x) for x in d] for d in ds],
                'H': [[str(x) for x in h] for h in hs]}
    zeta = midpoint(zstar)
    delta = []
    for d, h in zip(ds, hs):
        feasible = intersect(d, translate(h, zeta))
        if feasible[0] > feasible[1]:
            raise AssertionError('joint midpoint construction failed')
        delta.append(midpoint(feasible))
    assert delta[0] == 0
    return {'status': 'SINGLETON_JOINT_FEASIBLE', 'counts': counts, 'training_count': sum(counts),
            'D': [[str(x) for x in d] for d in ds],
            'H': [[str(x) for x in h] for h in hs],
            'Z': [str(x) for x in z], 'Zstar': [str(x) for x in zstar],
            'delta_star': [str(x) for x in delta], 'zeta_star': str(zeta)}


def _at_total(lower: list[F], upper: list[F], values: list[F], total: F,
              reverse: bool) -> tuple[F, list[F]]:
    q = lower.copy()
    remaining = total - sum(q)
    for j in sorted(range(len(q)), key=lambda j: (values[j], j), reverse=reverse):
        add = min(remaining, upper[j] - lower[j])
        q[j] += add
        remaining -= add
        if remaining == 0:
            break
    if remaining != 0:
        raise AssertionError('fixed-S fill failed')
    return sum((q[j] * values[j] for j in range(len(q))), F()) / total, q


def precision_extreme(lower: list[F], upper: list[F], values: list[F],
                      total_lo: F, total_hi: F, reverse: bool) -> tuple[F, list[F]]:
    order = sorted(range(len(lower)), key=lambda j: (values[j], j), reverse=reverse)
    breakpoints = [sum(lower)]
    t = breakpoints[0]
    for j in order:
        t += upper[j] - lower[j]
        breakpoints.append(t)
    candidates = {total_lo, total_hi}
    candidates.update(t for t in breakpoints if total_lo <= t <= total_hi)
    computed = [_at_total(lower, upper, values, s, reverse) for s in candidates]
    return (max(computed, key=lambda x: x[0]) if reverse else min(computed, key=lambda x: x[0]))


def _choose_q_for_target(q_lo: list[F], q_hi: list[F], lows: list[F], highs: list[F],
                         target: F) -> tuple[list[F], list[F]]:
    def mean(q: list[F], values: list[F]) -> F:
        return sum((a*b for a, b in zip(q, values)), F()) / sum(q)
    q = q_lo
    if mean(q, highs) < target:
        n0 = sum((a*b for a, b in zip(q_lo, highs)), F())
        s0 = sum(q_lo)
        dn = sum(((b-a)*v for a, b, v in zip(q_lo, q_hi, highs)), F())
        ds = sum(q_hi) - s0
        t = (target*s0 - n0) / (dn - target*ds)
        if not F(0) <= t <= F(1):
            raise AssertionError('connected-box witness parameter out of range')
        q = [a + t*(b-a) for a, b in zip(q_lo, q_hi)]
    low_mean, high_mean = mean(q, lows), mean(q, highs)
    if not low_mean <= target <= high_mean:
        raise AssertionError('joint witness mean not attained')
    alpha = F(0) if low_mean == high_mean else (target-low_mean)/(high_mean-low_mean)
    return q, [a + alpha*(b-a) for a, b in zip(lows, highs)]


def classify(row: dict, width: F, offsets: tuple[F, ...], zero_point: F) -> dict:
    present = []
    for j, (dm, err) in enumerate(row['methods']):
        if not dm and not err:
            continue
        if not dm or not err:
            return {'status': 'INCOMPLETE_METHOD_PAIR', 'method': METHODS[j]}
        if F(dm) <= 0 or F(err) <= 0:
            return {'status': 'INVALID_METHOD_DOMAIN', 'method': METHODS[j]}
        present.append(j)
    if not present:
        if row['dmcal'] and row['dmzp'] and F(row['dmcal']) > 0 and F(row['dmzp']) > 0:
            cal, zp = interval(row['dmcal'], width), interval(row['dmzp'], width)
            return {'status': 'DIRECT_CALIBRATOR_COMPATIBLE' if row['dmcal'] == row['dmzp'] and intersect(cal, zp)[0] <= intersect(cal, zp)[1]
                    else 'DIRECT_CALIBRATOR_INCOMPATIBLE', 'direct_intervals': (cal, zp)}
        return {'status': 'NO_METHOD_OR_DIRECT_CALIBRATOR'}
    if not row['dmav'] or not row['e_dmav'] or not row['dmzp']:
        return {'status': 'MISSING_TARGET_FIELD', 'methods': len(present)}
    if F(row['dmav']) <= 0 or F(row['e_dmav']) <= 0 or F(row['dmzp']) <= 0:
        return {'status': 'INVALID_TARGET_DOMAIN', 'methods': len(present)}
    lows, highs, qlo, qhi = [], [], [], []
    for j in present:
        dm, err = row['methods'][j]
        l, u = interval(dm, width)
        a, b = interval(err, width)
        if a <= 0:
            return {'status': 'ERROR_INTERVAL_CROSSES_ZERO', 'method': METHODS[j]}
        lows.append(l + offsets[j]); highs.append(u + offsets[j])
        qlo.append(1 / b**2); qhi.append(1 / a**2)
    a, b = interval(row['e_dmav'], width)
    if a <= 0:
        return {'status': 'TARGET_ERROR_INTERVAL_CROSSES_ZERO'}
    slo, shi = max(sum(qlo), 1/b**2), min(sum(qhi), 1/a**2)
    target_l, target_u = interval(row['dmav'], width)
    zp_l, zp_u = interval(row['dmzp'], width)
    target_l, target_u = max(target_l, zp_l + zero_point), min(target_u, zp_u + zero_point)
    out = {'methods': len(present), 'method_indices': present,
           'total_precision_interval': (slo, shi), 'target_mean_interval': (target_l, target_u)}
    if slo > shi:
        out['status'] = 'ERROR_INCOMPATIBLE'; return out
    if target_l > target_u:
        out['status'] = 'DMAV_DMZP_INCOMPATIBLE'; return out
    low, q_lower = precision_extreme(qlo, qhi, lows, slo, shi, False)
    high, q_upper = precision_extreme(qlo, qhi, highs, slo, shi, True)
    out['possible_mean_interval'] = (low, high)
    if high < target_l or low > target_u:
        out['status'] = 'JOINT_MEAN_ERROR_INCOMPATIBLE'; return out
    target = max(low, target_l)
    q, m = _choose_q_for_target(q_lower, q_upper, lows, highs, target)
    assert slo <= sum(q) <= shi
    assert sum((a*b for a, b in zip(q, m)), F()) / sum(q) == target
    out.update(status='JOINT_COMPATIBLE', witness_q=q, witness_m=m,
               witness_mean=target)
    return out


def nominal_map(row: dict) -> np.ndarray:
    a = np.zeros(7)
    indices = [j for j, (dm, err) in enumerate(row['methods']) if dm and err and F(dm)>0 and F(err)>0]
    if indices:
        q = np.array([float(1/F(row['methods'][j][1])**2) for j in indices])
        a[indices] = q/q.sum()
    elif row['dmcal'] and row['dmzp']:
        a[6] = 1
    else:
        a[:] = np.nan
    return a


def _dec(x: F | None) -> float:
    return float(x) if x is not None else float('nan')


def build_operator(rows: list[dict], old_witnesses: list[dict], locked: dict) -> tuple[dict, dict]:
    pgcs = np.array([r['pgc'] for r in rows], dtype=np.int64)
    maps = np.vstack([nominal_map(r) for r in rows])
    nominal_residuals = np.full((len(rows), 2), np.nan)
    names = list(WIDTHS)
    status = np.empty((len(rows), len(names)), dtype='U40')
    witness_maps = np.full((len(rows), len(names), 7), np.nan)
    bounds = np.full((len(rows), len(names), 6), np.nan)
    # [feasible precision lower/upper, attainable mean lower/upper, printed target lower/upper]
    counts = {name: Counter() for name in names}
    examples = {name: {} for name in names}
    for i, row in enumerate(rows):
        if (np.isfinite(maps[i]).all() and row['dmav'] and row['e_dmav']
                and F(row['dmav']) > 0 and F(row['e_dmav']) > 0):
            nominal_mu = sum(maps[i, j]*(float(row['methods'][j][0])+float(F(locked['round_nearest']['delta_star'][j])))
                             for j in range(6) if maps[i, j] != 0)
            nominal_q = sum(float(1/F(row['methods'][j][1])**2)
                            for j in range(6) if maps[i, j] != 0)
            nominal_residuals[i] = [nominal_mu-float(row['dmav']),
                                    nominal_q**(-.5)-float(row['e_dmav'])]
        for k, (name, width) in enumerate(WIDTHS.items()):
            representative = locked[name]
            offsets = tuple(F(x) for x in representative['delta_star'])
            zero_point = F(representative['zeta_star'])
            result = classify(row, width, offsets, zero_point)
            label = result['status']
            status[i, k] = label
            counts[name][label] += 1
            examples[name].setdefault(label, [])
            if len(examples[name][label]) < 12:
                examples[name][label].append(row['pgc'])
            for start, key in ((0, 'total_precision_interval'), (2, 'possible_mean_interval'),
                               (4, 'target_mean_interval')):
                if key in result:
                    bounds[i, k, start:start+2] = [float(v) for v in result[key]]
            if label == 'JOINT_COMPATIBLE':
                ids = result['method_indices']; q = result['witness_q']; total = sum(q)
                witness_maps[i, k, ids] = [float(v/total) for v in q]
                witness_maps[i, k, [j for j in range(7) if j not in ids]] = 0
            elif label == 'DIRECT_CALIBRATOR_COMPATIBLE':
                witness_maps[i, k] = np.array([0, 0, 0, 0, 0, 0, 1], dtype=float)
    old_ids = {int(w['group']): w['reason'] for w in old_witnesses}
    index = {int(p): i for i, p in enumerate(pgcs)}
    cross = {'old_total': len(old_ids), 'count_only_blank_numeric': 0,
             'count_mismatch': 0, 'groups': []}
    for pgc, reason in sorted(old_ids.items()):
        if pgc not in index:
            raise RuntimeError(f'OLD_WITNESS_MISSING_TABLE3 {pgc}')
        row = rows[index[pgc]]
        if reason == 'MISSING_TABLE3_FP_FIELDS':
            if row['count_fp'] or not all(row['methods'][1]):
                raise RuntimeError(f'OLD_COUNT_BLANK_CORPUS_CHANGED {pgc}')
            cross['count_only_blank_numeric'] += 1
        elif reason == 'TABLE3_FP_COUNT_MISMATCH':
            cross['count_mismatch'] += 1
        else:
            raise RuntimeError(f'UNKNOWN_OLD_WITNESS_REASON {reason}')
        cross['groups'].append({'pgc': pgc, 'old_reason': reason,
                                'round_nearest': str(status[index[pgc], 0]),
                                'one_place_outer': str(status[index[pgc], 1])})
    if (len(old_ids), cross['count_only_blank_numeric'], cross['count_mismatch']) != (54, 46, 8):
        raise RuntimeError('OLD_CORPUS_CARDINALITY_CHANGED')
    arrays = {'pgc': pgcs, 'nominal_A': maps, 'witness_A': witness_maps,
              'bounds': bounds, 'status': status, 'nominal_residuals_mag': nominal_residuals,
              'width_names': np.array(names), 'channel_names': np.array((*METHODS, 'DirectCal'))}
    summary = {'table_rows': len(rows), 'method_counts': dict(Counter(sum(bool(dm and err) for dm, err in r['methods']) for r in rows)),
               'status_counts': {k: dict(v) for k, v in counts.items()}, 'status_examples': examples,
               'old_22599_plus_54': cross,
               'interval_columns': ['precision_lower', 'precision_upper', 'mean_lower', 'mean_upper', 'target_lower', 'target_upper']}
    return arrays, summary


def selected_arrays(arrays: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    with np.load(SOURCE, allow_pickle=False) as source:
        ids = np.asarray(source['group_id'], dtype='<i8')
        z = source['z_CMB']
        n = source['n_J2000']
        methods = source['method_family']
        errors = source['e_dmzp']
    if len(ids) != 35970 or hashlib.sha256(ids.tobytes()).hexdigest() != ID_SHA:
        raise RuntimeError('SELECTED_COHORT_IDENTITY_CHANGED')
    if len(np.unique(ids)) != len(ids) or len(np.unique(arrays['pgc'])) != len(arrays['pgc']):
        raise RuntimeError('DUPLICATE_GROUP_ID')
    index = {int(v): k for k, v in enumerate(arrays['pgc'])}
    missing = [int(v) for v in ids if int(v) not in index]
    if missing:
        raise RuntimeError(f'SELECTED_GROUP_MISSING {missing[:24]} count={len(missing)}')
    take = np.array([index[int(v)] for v in ids], dtype=int)
    return ids, take, (z, n, methods, errors), index


def fixed_e1_responses(ids: np.ndarray, maps: dict[str, np.ndarray],
                       design_inputs: tuple) -> dict:
    from obsstat.cf4_apparent_kinematic_distribution import model_matrix
    z, n, methods, errors = design_inputs
    design = model_matrix(z, n, methods, include_method_slope=True,
                          omega_m=.3153, H0=74.6)
    X = design['design']
    sl = design['slices']['shear']
    B = X[:, sl]
    N = np.delete(X, np.arange(sl.start, sl.stop), axis=1)
    if B.shape != (35970, 5) or N.shape != (35970, 14):
        raise RuntimeError(f'E1_DESIGN_SHAPE_CHANGED B={B.shape} N={N.shape}')
    dsqrt = np.sqrt(errors**2 + .15**2 +
                    (250.0*design['redshift_velocity_width_basis_mag_per_kms'])**2)
    if not np.isfinite(dsqrt).all() or np.any(dsqrt <= 0):
        raise RuntimeError('E1_DIAGONAL_DOMAIN')
    Bw = B/dsqrt[:, None]
    Nw = N/dsqrt[:, None]
    scale = np.linalg.norm(Nw, axis=0)
    if np.any(scale <= 0):
        raise RuntimeError('NUISANCE_ZERO_COLUMN')
    Q, R = np.linalg.qr(Nw/scale, mode='reduced')
    nsing = np.linalg.svd(R, compute_uv=False)
    if nsing[-1] <= 1e-10*nsing[0]:
        raise RuntimeError('NUISANCE_NUMERICAL_RANK_DEFICIENT')
    PB = Bw - Q @ (Q.T @ Bw)
    fisher = Bw.T @ PB
    saved = np.asarray(json.loads(E1.read_text())['source_comparisons']['all']['schur_fisher'])
    if not np.allclose(fisher, saved, rtol=1e-9, atol=1e-10):
        raise RuntimeError(f'E1_FISHER_REGRESSION_FAILURE maxabs={np.max(abs(fisher-saved))}')
    result = {'status': 'FULL_COHORT_FIXED_E1_SEVEN_CHANNEL_RESPONSE',
              'n': len(ids), 'channel_names': list((*METHODS, 'DirectCal')),
              'fisher_max_abs_delta': float(np.max(abs(fisher-saved))),
              'fisher_max_scaled_delta': float(np.max(abs(fisher-saved)/(1e-10+1e-9*abs(saved)))),
              'maps': {}}
    for label, A in maps.items():
        if A.shape != (35970, 7) or not np.isfinite(A).all():
            raise RuntimeError(f'FULL_COHORT_OPERATOR_UNDEFINED {label}')
        row_error = float(np.max(abs(A.sum(axis=1)-1)))
        if row_error > 1e-14:
            raise RuntimeError(f'A7_ROW_SUM_FAILURE {label} {row_error}')
        Aw = A/dsqrt[:, None]
        PA = Aw-Q@(Q.T@Aw)
        M = np.linalg.solve(saved, Bw.T@PA)
        common = M @ np.ones(7)
        if np.max(abs(common)) > 1e-10:
            raise RuntimeError(f'M7_COMMON_SHIFT_FAILURE {label} {common.tolist()}')
        singular_pa = np.linalg.svd(PA, compute_uv=False)
        singular_m = np.linalg.svd(M, compute_uv=False)
        relative = np.linalg.norm(PA, axis=0)/np.linalg.norm(Aw, axis=0)
        result['maps'][label] = {
            'signed_M7_5x7': M.tolist(),
            'A7_row_sum_max_abs_delta': row_error,
            'M7_common_shift': common.tolist(),
            'M6_only_common_shift_not_required': (M[:, :6] @ np.ones(6)).tolist(),
            'nuisance_containment_residual_ratio_by_channel': relative.tolist(),
            'nuisance_contained_at_1e_10_by_channel': (relative <= 1e-10).tolist(),
            'PA_singular_values': singular_pa.tolist(),
            'PA_rank_at_1e_10': int(np.sum(singular_pa > singular_pa[0]*1e-10)),
            'M_singular_values': singular_m.tolist(),
            'M_rank_at_1e_10': int(np.sum(singular_m > singular_m[0]*1e-10)),
        }
    return result


def write_json_create_only(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def run(out: Path) -> None:
    sources = verify_sources()
    out.mkdir(parents=True, exist_ok=True)
    for name in ('LOCKED_PARAMETERS.json', 'RESULT.json', 'GROUP_OPERATOR.npz', 'REPORT.md'):
        if (out/name).exists():
            raise FileExistsError(f'create-only result {out/name}')
    training_rows = parse_table3_singletons(TABLE)
    locked = {name: identify_singletons(training_rows, width) for name, width in WIDTHS.items()}
    # This separate file is created before mixed-method means are evaluated.
    lock_record = {'schema': 'htt.cf4_release_singleton_lock/1', 'source_sha256': sources,
                   'rounding_conventions': locked,
                   'mixed_groups_used_for_identification': 0,
                   'reference': 'delta_SNIa=0',
                   'representatives': 'midpoints of exact joint feasible intervals'}
    write_json_create_only(out/'LOCKED_PARAMETERS.json', lock_record)
    if any(v['status'] != 'SINGLETON_JOINT_FEASIBLE' for v in locked.values()):
        result = {'schema': 'htt.cf4_release_stage_seven_channel/1',
                  'status': 'SINGLETON_IDENTIFICATION_REJECTED',
                  'first_failures': {k: v for k, v in locked.items() if v['status'] != 'SINGLETON_JOINT_FEASIBLE'},
                  'response': 'NOT_COMPUTED', 'original_H02': 'HOLD_UNCHANGED'}
        write_json_create_only(out/'RESULT.json', result)
        (out/'REPORT.md').write_text('# CF4 release-stage result\n\nSingleton identification rejected; see RESULT.json. No mixed-row or response evaluation was performed.\n')
        return
    rows = parse_table3(TABLE)
    heldout_count = sum(len(pair_indices(r)) > 1 for r in rows)
    if heldout_count != 1134:
        raise RuntimeError(f'HELDOUT_SOURCE_CARDINALITY_CHANGED {heldout_count}')
    old = json.loads(OLD.read_text())
    if old['structure']['structurally_qualified'] != 22599:
        raise RuntimeError('OLD_22599_CORPUS_CHANGED')
    arrays, summary = build_operator(rows, old['structure']['witnesses'], locked)
    ids, take, design_inputs, index = selected_arrays(arrays)
    selected_status = {name: dict(Counter(str(v) for v in arrays['status'][take, k]))
                       for k, name in enumerate(WIDTHS)}
    heldout_failures = {}
    first_raw_witnesses = {}
    mixed_indices = [i for i, r in enumerate(rows) if len(pair_indices(r)) > 1]
    for k, name in enumerate(WIDTHS):
        failed = [{'pgc': rows[i]['pgc'], 'table3_line': rows[i]['line'],
                   'status': str(arrays['status'][i, k])}
                  for i in mixed_indices if arrays['status'][i, k] != 'JOINT_COMPATIBLE']
        heldout_failures[name] = failed
        if failed:
            witness = rows[next(i for i in mixed_indices if rows[i]['pgc'] == failed[0]['pgc'])]
            first_raw_witnesses[name] = {
                'row': witness,
                'classification': {key: str(value) for key, value in
                    classify(witness, WIDTHS[name],
                             tuple(F(x) for x in locked[name]['delta_star']),
                             F(locked[name]['zeta_star'])).items()}}
    direct_ids = [int(p) for p in ids if arrays['status'][index[int(p)], 0] == 'DIRECT_CALIBRATOR_COMPATIBLE']
    if len(direct_ids) != 2 or set(direct_ids) != {20679, 59927}:
        raise RuntimeError(f'DIRECT_CALIBRATOR_COHORT_CHANGED {direct_ids}')
    all_selected = all(selected_status[name].get('JOINT_COMPATIBLE', 0) == 35968 and
                       selected_status[name].get('DIRECT_CALIBRATOR_COMPATIBLE', 0) == 2
                       for name in WIDTHS)
    all_heldout = all(not heldout_failures[name] for name in WIDTHS)
    arrays['selected_pgc'] = ids
    arrays['selected_nominal_A7'] = arrays['nominal_A'][take]
    arrays['selected_witness_A7'] = arrays['witness_A'][take]
    response = 'NOT_COMPUTED_SELECTED_SOURCE_INCOMPATIBLE'
    if all_selected:
        maps = {'nominal': arrays['selected_nominal_A7'],
                'witness_round_nearest': arrays['selected_witness_A7'][:, 0],
                'witness_one_place_outer': arrays['selected_witness_A7'][:, 1]}
        response = fixed_e1_responses(ids, maps, design_inputs)
    np.savez_compressed(out/'GROUP_OPERATOR.npz', **arrays)
    result = {'schema': 'htt.cf4_release_stage_seven_channel/1',
              'status': 'COMPONENT_EXECUTED_REVIEW_REQUIRED' if all_selected and all_heldout else 'HELDOUT_REPRESENTATIVE_REJECTED',
              'source_sha256': sources, 'singleton_lock_sha256': digest(out/'LOCKED_PARAMETERS.json'),
              'training_count_by_convention': {k: v['training_count'] for k, v in locked.items()},
              'heldout_count': heldout_count,
              'operator': summary, 'selected_35970_status': selected_status,
              'heldout_failures_all': heldout_failures,
              'first_raw_heldout_witnesses': first_raw_witnesses,
              'selected_direct_calibrator_ids': direct_ids,
              'selected_35970_complete_under_both': all_selected,
              'heldout_complete_under_both': all_heldout,
              'response': response,
              'working_D': 'frozen e_DMzp^2+0.15^2+(250*j_v)^2; table2 direct calibrator errors .180/.560 vs table4 .100/.100 retained',
              'covariance': {'Gamma7': 'UNKNOWN_ARBITRARY_PSD_WITH_ALL_OFFDIAGONALS',
                             'calibration_contribution': 'M7 Gamma7 M7^T is conditional, not empirical',
                             'full_candidate': 'Let K=F^-1 Bw^T P D^-1/2 and J_v be the as-yet-unspecified velocity-to-magnitude map. Cov(theta)=L Sigma L^T, L=[K,K A7,K J_v], Sigma=Cov(epsilon,eta,v) with Sigma_epsilon_eta, Sigma_epsilon_v, Sigma_eta_v and transposes all retained. The two direct-anchor residual correlation belongs to Sigma_epsilon_epsilon and is unknown.',
                             'numeric_bound': 'NONE_WITHOUT_BOUNDED_COVARIANCE_CLASS'},
              'original_H02': 'HOLD_UNCHANGED',
              'claim_ceiling': 'release-stage conditional reconstruction and fixed E1 response only; no producer genealogy, empirical covariance, physical H02 or family identification'}
    write_json_create_only(out/'RESULT.json', result)
    (out/'REPORT.md').write_text(
        '# CF4 release-stage identification and anchor-aware response\n\n'
        f"Singleton training counts: {result['training_count_by_convention']}; held-out mixed groups: {result['heldout_count']}.\n\n"
        f"Selected 35,970 statuses: {selected_status}. Response: {response['status'] if isinstance(response, dict) else response}.\n\n"
        'The exact singleton joint feasible set and frozen representatives are in LOCKED_PARAMETERS.json. '
        'The 54 old FP exceptions remain in RESULT.json. This is a deterministic representative compatibility check, '
        'not independent validation or a producer parameter estimate. Signed 5x7 responses, when present, '
        'are conditional fixed-E1 working-reference derivatives. Gamma7, measurement, anchor-residual, '
        'peculiar-velocity and all cross-covariance blocks remain unknown. Original H02 remains HOLD.\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
