#!/usr/bin/env python3
"""Read-only raw-join audit and six finite witness checks; stdlib only.

Does not import or execute author code, project harness, or a full-cohort fit.
"""
import ast
import hashlib
import itertools
import json
import struct
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parent / 'r26_cf4_fp_pooling_closure'
CONTRACT = HERE.parent / 'r26_sdss_genealogy_independent_review'
result = json.loads((AUTHOR / 'RESULT.json').read_text())
witnesses = json.loads((AUTHOR / 'WITNESSES.json').read_text())
bindings = json.loads((CONTRACT / 'SOURCE_BINDINGS.json').read_text())
paths = {Path(x['path']).name: Path(x['path']) for x in bindings}
hashes = {}
for rec in bindings:
    raw = Path(rec['path']).read_bytes()
    assert len(raw) == rec['bytes'], rec['path']
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == rec['sha256'], rec['path']
    hashes[rec['path']] = digest
candidate_hashes = {n: hashlib.sha256((AUTHOR/n).read_bytes()).hexdigest()
                    for n in ['RESULT.json', 'RESULT.md', 'WITNESSES.json',
                              'SOURCE_BINDING_RECEIPT.json', 'CONTINUED_BUDGET.jsonl',
                              'run_closure.py', 'test_controls.py', 'test_real_witnesses.py']}

# NPY identity column is decoded with stdlib directly, independently of numpy.
with zipfile.ZipFile(paths['selected_source_observables.npz']) as archive:
    blob = archive.read('group_id.npy')
assert blob[:6] == b'\x93NUMPY'
version = tuple(blob[6:8])
length_size = 2 if version == (1, 0) else 4
head_len = int.from_bytes(blob[8:8+length_size], 'little')
head_end = 8 + length_size + head_len
header = ast.literal_eval(blob[8+length_size:head_end].decode('ascii'))
assert header['descr'] in ('<i8', '<i4', '<u8', '<u4'), header
assert len(header['shape']) == 1 and not header['fortran_order'], header
fmt = {'<i8': '<q', '<i4': '<i', '<u8': '<Q', '<u4': '<I'}[header['descr']]
ids = [x[0] for x in struct.iter_unpack(fmt, blob[head_end:])]
assert len(ids) == header['shape'][0] == 35970
assert len(set(ids)) == len(ids)
selected = set(ids)

sdss_lines = paths['SDSS_PV_public.dat'].read_text().splitlines()
assert sdss_lines[0].split()[1] == 'PGC'
sdss_list = [int(line.split()[0]) for line in sdss_lines[1:]]
sdss = set(sdss_list)
assert len(sdss_list) == len(sdss) == 34059

def raw_table(path, is_galaxy):
    rows = {}
    offset = 0
    for lineno, binary in enumerate(path.read_bytes().splitlines(keepends=True), 1):
        line = binary.rstrip(b'\r\n').decode('ascii')
        identifier = int(line[0:7])
        assert identifier not in rows
        if is_galaxy:
            row = dict(pgc=identifier, group=int(line[8:15]), dm=line[65:71].strip(),
                       err=line[72:76].strip())
        else:
            row = dict(group=identifier, count=line[113:116].strip(),
                       dm=line[117:123].strip(), err=line[124:129].strip())
        row.update(line=lineno, byte_offset_zero_based=offset, raw=line)
        rows[identifier] = row
        offset += len(binary)
    return rows

t2 = raw_table(paths['table2.dat'], True)
t3 = raw_table(paths['table3.dat'], False)
assert len(t2) == 55877 and len(t3) == 38053
grouped = defaultdict(list)
for row in t2.values():
    assert bool(row['dm']) == bool(row['err'])
    if row['dm']:
        assert F(row['err']) > 0
        F(row['dm'])  # rejects nonfinite or malformed source values
        grouped[row['group']].append(row)
cohort = {t2[p]['group'] for p in sdss if p in t2 and t2[p]['group'] in selected}
assert len(cohort) == 22653
observed_exclusions = []
qualified = []
totals = Counter()
for group in sorted(cohort):
    rows = grouped[group]
    target = t3.get(group)
    n_sdss = sum(row['pgc'] in sdss for row in rows)
    n_other = len(rows) - n_sdss
    totals.update(all_FP_contributors=len(rows), SDSS_FP_contributors=n_sdss,
                  other_FP_contributors=n_other, groups_with_other_FP_contributors=int(n_other > 0),
                  ALL_GALAXY_IDS_IN_SDSS=int(n_other == 0))
    if target is None or any(not target[k] for k in ('count', 'dm', 'err')):
        reason = 'MISSING_TABLE3_FP_FIELDS'
    elif int(target['count']) != len(rows):
        reason = 'TABLE3_FP_COUNT_MISMATCH'
    else:
        assert F(target['err']) > 0
        F(target['dm'])
        reason = None
    if reason:
        observed_exclusions.append(dict(group=group, reason=reason))
    else:
        qualified.append(group)
assert len(qualified) == 22599
assert Counter(x['reason'] for x in observed_exclusions) == {
    'MISSING_TABLE3_FP_FIELDS': 46, 'TABLE3_FP_COUNT_MISMATCH': 8}
for key, val in totals.items():
    assert val == result['structure'][key], (key, val)
for summary in result['rounding_conventions'].values():
    assert summary['included_group_ids'] == qualified
    assert summary['excluded_group_ids_with_reasons'] == observed_exclusions
assert len(witnesses['structural']) == len(observed_exclusions)
for rec in witnesses['structural']:
    g = rec['group']
    assert rec['witness']['table2_rows'] == grouped[g]
    assert rec['witness']['table3_row'] == t3[g]
    assert rec['observed_contributors'] == len(grouped[g])
    assert rec['table3_o_DMfp'] == t3[g]['count']

def box(token, factor):
    value = F(token)
    places = -Decimal(token).as_tuple().exponent
    quantum = F(10) ** (-places)
    return value - factor*quantum, value + factor*quantum

def extremum(values, low, high, maximum):
    # Dinkelbach fixed-point iteration; exact sign certificate proves optimum.
    current = sum(values, F()) / len(values)
    for iteration in range(len(values) + 3):
        weights = [hi if ((v > current) if maximum else (v < current)) else lo
                   for v, lo, hi in zip(values, low, high)]
        nxt = sum((v*w for v, w in zip(values, weights)), F()) / sum(weights, F())
        if nxt == current:
            assert sum((w*(v-current) for v,w in zip(values,weights)), F()) == 0
            for v, w, lo, hi in zip(values, weights, low, high):
                if maximum:
                    assert w*(v-current) == max(lo*(v-current), hi*(v-current))
                else:
                    assert w*(v-current) == min(lo*(v-current), hi*(v-current))
            return current, weights
        current = nxt
    raise AssertionError('independent extremum failed to stabilize')

def enclosed_pair(pair, exactlo, exacthi):
    lo, hi = F(pair['lower']), F(pair['upper'])
    assert lo <= exactlo <= exacthi <= hi
    assert exactlo-lo < F(1, 10**44) and hi-exacthi < F(1, 10**44)

checks = []
for name, groups in witnesses['precision'].items():
    factor = F(1, 2) if name == 'ROUND_TO_NEAREST_LAST_PRINTED_PLACE' else F(1)
    for group_id, record in groups.items():
        g = int(group_id)
        rows = grouped[g]
        assert record['table2_rows'] == rows
        assert record['table3_row'] == t3[g]
        means = [box(row['dm'], factor) for row in rows]
        errors = [box(row['err'], factor) for row in rows]
        assert all(a > 0 for a,b in errors)
        low_weights = [1/(b*b) for a,b in errors]
        high_weights = [1/(a*a) for a,b in errors]
        lower, lower_w = extremum([a for a,b in means], low_weights, high_weights, False)
        upper, upper_w = extremum([b for a,b in means], low_weights, high_weights, True)
        enclosed_pair(record['modulus_interval'], lower, upper)
        if len(rows) == 2:
            vertices = list(itertools.product(*zip(low_weights, high_weights)))
            assert lower == min(sum(w*m[0] for w,m in zip(ws,means))/sum(ws) for ws in vertices)
            assert upper == max(sum(w*m[1] for w,m in zip(ws,means))/sum(ws) for ws in vertices)
        by_id = {row['pgc']: (row, m, lo, hi) for row,m,lo,hi in zip(rows,means,low_weights,high_weights)}
        for side, exact in [('lower', lower), ('upper', upper)]:
            choices = record[side+'_extremizing_weights']
            assert len(choices) == len(by_id) and {x['pgc'] for x in choices} == set(by_id)
            num = den = F()
            for choice in choices:
                row, m, lo, hi = by_id[choice['pgc']]
                assert choice['endpoint'] in ('weight_low', 'weight_high')
                weight = hi if choice['endpoint'] == 'weight_high' else lo
                num += weight*m[0 if side == 'lower' else 1]
                den += weight
            assert num/den == exact
        target_lo, target_hi = box(t3[g]['dm'], factor)
        offset = (target_lo-upper, target_hi-lower)
        enclosed_pair(record['offset_interval'], *offset)
        qlo, qhi = F(record['q_interval']['lower']), F(record['q_interval']['upper'])
        whi, wlo = sum(high_weights, F()), sum(low_weights, F())
        assert 0 < qlo <= qhi and qlo*qlo*whi <= 1 <= qhi*qhi*wlo
        with localcontext() as ctx:
            ctx.prec = 100
            def dec(x): return Decimal(x.numerator)/Decimal(x.denominator)
            exact_qlo = 1/dec(whi).sqrt()
            exact_qhi = 1/dec(wlo).sqrt()
            assert Decimal(0) <= exact_qlo-dec(qlo) < Decimal('1e-44')
            assert Decimal(0) <= dec(qhi)-exact_qhi < Decimal('1e-44')
        elo, ehi = box(t3[g]['err'], factor)
        assert qlo <= ehi and qhi >= elo
        enclosed_pair(record['error_target_interval'], elo, ehi)
        summary = result['rounding_conventions'][name]
        if g == summary['all_group_max_lower_group']:
            assert F(summary['all_group_offset_bounds']['lower']) <= offset[0]
            assert offset[0] - F(summary['all_group_offset_bounds']['lower']) < F(1, 10**44)
        if g == summary['all_group_min_upper_group']:
            assert F(summary['all_group_offset_bounds']['upper']) >= offset[1]
            assert F(summary['all_group_offset_bounds']['upper']) - offset[1] < F(1, 10**44)
        assert F(summary['all_group_offset_bounds']['lower']) <= F(summary['all_group_offset_bounds']['upper'])
        nominal_w = [1/F(row['err'])**2 for row in rows]
        nominal = sum(F(row['dm'])*w for row,w in zip(rows,nominal_w))/sum(nominal_w)
        assert nominal == F(int(record['nominal']['numerator']), int(record['nominal']['denominator']))
        if g == 29807:
            assert sum(row['pgc'] in sdss for row in rows) == 27
            assert sum(row['pgc'] not in sdss for row in rows) == 7
            kept = [(row,w) for row,w in zip(rows,nominal_w) if row['pgc'] in sdss]
            assert nominal != sum(F(row['dm'])*w for row,w in kept)/sum(w for row,w in kept)
        checks.append(dict(convention=name, group=g, contributors=len(rows),
                           exact_optimality_certificate=True, raw_witness_bytes=True,
                           outward_sqrt_and_offset=True, nominal_exact=True))
assert len(checks) == 6
assert t2[20919]['dm'] == '36.956' and t2[20919]['err'] == '0.46'
assert t3[20919]['dm'] == '36.980' and t3[20919]['err'] == '0.460'
assert t3[20919]['raw'][15:21].strip() == '37.107'
assert t3[20919]['raw'][8:14].strip() == '36.960'
assert result['simultaneous_modulus_error_feasibility'] == 'NOT_ESTABLISHED'
assert result['quoted_error_law'] == 'NOT_ESTABLISHED'
assert result['H02'] == 'HOLD_UNCHANGED'
assert result['status'] == 'STRUCTURAL/NUMERICAL_HOLD'
out = dict(status='PASS_FOCUSED_INDEPENDENT_CHECK', validation_scope='full raw structure; six numerical witness cases only',
           source_hashes=hashes, candidate_hashes=candidate_hashes, npy_header=header,
           table_rows=dict(table2=len(t2), table3=len(t3), sdss=len(sdss), selected=len(selected)),
           cohort=22653, qualified=22599, totals=dict(totals), exclusions=observed_exclusions,
           numerical_checks=checks, full_cohort_numerical_replay=False)
(HERE/'INDEPENDENT_CHECK.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps(out, indent=2))
