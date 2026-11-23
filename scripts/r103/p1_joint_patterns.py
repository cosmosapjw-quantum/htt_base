"""Sharp k-of-four intervals from coupled CF4 P1 event summaries at fixed threshold."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


SOURCE = Path('docs/research_program/observational_publication_20261015/CONTINUATION_20261018/P1/results/FUNCTIONAL_SENSITIVITY_RESULT.json')
SOURCE_SHA = '80792f508bd2be07fae153f662c9726ce5dc0ddabf78ea15ef66a0d27219355b'
ARRAY = SOURCE.with_name('paired_functional_arrays.npz')
ARRAY_SHA = 'cd38f438a0bf07385b07478c7b5c122df5af1e9bb48a5575fe1cad40ef261f27'


def observed_patterns(root, thresholds):
    path = root / ARRAY
    if hashlib.sha256(path.read_bytes()).hexdigest() != ARRAY_SHA:
        raise ValueError('P1 paired array identity mismatch')
    with np.load(path, allow_pickle=False) as archive:
        q = archive['q_app']
        weights = archive['weights']
        if (q.shape != (2048, 4) or not np.all(np.isfinite(q)) or len(set(archive['sample_id'])) != 2048
                or not np.all(weights == 1/2048) or np.any(np.isfinite(archive['physical_Q']))):
            raise ValueError('P1 registered draw shape, IDs, weights or physical support differ')
        values = {}
        for threshold in thresholds:
            m = (q > threshold)
            k = m.sum(axis=1)
            values[str(threshold)] = {'observed_exactly_k': np.bincount(k, minlength=5).tolist(),
                                      'observed_marginals': m.sum(axis=0).tolist()}
    return values


def pattern_bounds(marginals, union, intersection, n):
    raw = np.asarray([n, *marginals, union, intersection], dtype=float)
    if raw.shape != (7,) or not np.all(np.isfinite(raw)) or np.any(raw != np.rint(raw)) or n <= 0:
        raise ValueError('four integer marginal counts, union, intersection and positive total required')
    patterns = np.array(list(itertools.product((0, 1), repeat=4)), dtype=int)
    counts = patterns.sum(axis=1)
    constraints = np.vstack((np.ones(16, dtype=int), patterns.T, counts >= 1, counts == 4))
    target = np.asarray(raw, dtype=int)
    limits = LinearConstraint(constraints, target, target)
    results = {}
    for k in (2, 3):
        event = (counts >= k).astype(int)
        endpoints, witnesses = [], []
        for sign in (1, -1):
            fit = milp(sign * event, integrality=np.ones(16), bounds=Bounds(0, n),
                       constraints=limits, options={'mip_rel_gap': 0.})
            if not fit.success:
                raise ValueError(f'no exact integer allocation: {fit.message}')
            allocation = np.rint(fit.x).astype(int)
            if (np.any(allocation < 0) or not np.array_equal(constraints @ allocation, target)
                    or abs(fit.fun-sign*int(event @ allocation)) > 1e-7):
                raise ArithmeticError('integer endpoint witness failed exact substitution')
            endpoint = int(event @ allocation)
            # Different HiGHS builds can return different valid tables at a
            # tied endpoint. Select the lexicographically first integer table.
            fixed = LinearConstraint(np.vstack((constraints, event)), np.append(target, endpoint),
                                     np.append(target, endpoint))
            lower, upper = np.zeros(16), np.full(16, float(n))
            for idx, objective in enumerate(np.eye(16)):
                if allocation[idx] != 0:
                    pick = milp(objective, integrality=np.ones(16), bounds=Bounds(lower, upper),
                                constraints=fixed, options={'mip_rel_gap': 0.})
                    if not pick.success:
                        raise ArithmeticError(f'no canonical witness at endpoint {endpoint}')
                    allocation = np.rint(pick.x).astype(int)
                lower[idx] = upper[idx] = allocation[idx]
            if (np.any(allocation < 0) or not np.array_equal(constraints @ allocation, target)
                    or int(event @ allocation) != endpoint):
                raise ArithmeticError('canonical witness failed exact substitution')
            endpoints.append(endpoint)
            witnesses.append({''.join(map(str, bits)): int(mass) for bits, mass in zip(patterns, allocation) if mass})
        results[str(k)] = {'counts_min_max': endpoints, 'mass_min_max': [m/n for m in endpoints],
                           'feasible_witnesses_min_max': witnesses}
    return results


def analyze(root, observed=None):
    raw = (root / SOURCE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('P1 source digest mismatch')
    data = json.loads(raw)
    n = data['sample_count']
    if data['weight'] * n != 1:
        raise ValueError('equal empirical row weights required')
    if observed is None:
        observed = observed_patterns(root, [r['threshold'] for r in data['strict_exceedance']])
    rows = []
    for entry in data['strict_exceedance']:
        m = np.array(entry['per_window']) * n
        u, i = n*entry['any_window'], n*entry['all_windows']
        counts = observed[str(entry['threshold'])]
        exact = counts['observed_exactly_k']
        if (counts['observed_marginals'] != m.tolist() or len(exact) != 5 or sum(exact) != n
                or n-exact[0] != u or exact[4] != i):
            raise ValueError('P1 empirical joint patterns disagree with committed marginal summary')
        results = pattern_bounds(m, u, i, n)
        for k in (2, 3):
            lo, hi = results[str(k)]['counts_min_max']
            if not lo <= sum(exact[k:]) <= hi:
                raise ArithmeticError('joint multiplicity lies outside certified bounds')
        rows.append({'threshold': entry['threshold'], 'marginal_counts': m.astype(int).tolist(),
                     'union_count': int(u), 'intersection_count': int(i),
                     'observed_exactly_k': exact, 'at_least_k': results})
    return {
        'schema': 'htt.r103.p1_joint_pattern_bounds/1', 'source_summary': str(SOURCE),
        'source_sha256': SOURCE_SHA, 'paired_array_sha256': ARRAY_SHA, 'source_group_count': data['source_group_count'],
        'draws': n, 'observable': data['q_app_definition'], 'strict_thresholds': rows,
        'bounds_scope': 'Coordinatewise sharp at each threshold among equal-weight joint patterns with the recorded per-window, union and intersection counts. Different endpoints can use different allocations. Retaining row-level vectors supplies the actual pattern and can narrow these intervals.',
        'physical_unknown_mass': 1., 'physical_Pi': None,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    text = json.dumps(analyze(Path(__file__).resolve().parents[2]), indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
