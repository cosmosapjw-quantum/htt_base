"""Independent targeted saved-factor metadata closeout. No author import.

Actual arithmetic is confined to exact L-column sums for zero-leverage masks.
Previously reached full-data value/response checks transfer only by full parity.
"""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def same_bits(a, b, name):
    assert a.dtype == b.dtype and a.shape == b.shape, name + ': dtype/shape'
    assert a.tobytes(order='C') == b.tobytes(order='C'), name + ': element bytes'

def same_json(a, b, path='$'):
    assert type(a) is type(b), path + ': type'
    if isinstance(a, dict):
        assert a.keys() == b.keys(), path + ': keys'
        for key in a:
            same_json(a[key], b[key], path + '.' + key)
    elif isinstance(a, list):
        assert len(a) == len(b), path + ': length'
        for j, (x, y) in enumerate(zip(a, b)):
            same_json(x, y, path + '[' + str(j) + ']')
    elif isinstance(a, float):
        assert struct.pack('>d', a) == struct.pack('>d', b), path + ': float bits'
    else:
        assert a == b, path + ': value'

def exact_zero_columns(l, nonrefs, channels, refs, mixed):
    """Decode IEEE bits as integer multiples of 2**-1074, never square/norm."""
    assert l.dtype == np.float64 and l.shape == (5, len(nonrefs))
    bits = np.ascontiguousarray(l).view(np.uint64)
    assert np.all(((bits >> np.uint64(52)) & np.uint64(2047)) != 2047)
    z = mixed.copy()
    z[nonrefs] = np.all((bits & np.uint64((1 << 63) - 1)) == 0, axis=0)
    sums = [[0] * 5 for _ in refs]
    for j, c_raw in enumerate(channels):
        c = int(c_raw)
        for a in range(5):
            raw = int(bits[a, j])
            exponent = (raw >> 52) & 2047
            fraction = raw & ((1 << 52) - 1)
            units = fraction if exponent == 0 else ((1 << 52) | fraction) << (exponent - 1)
            sums[c][a] += -units if raw >> 63 else units
    for c, r_raw in enumerate(refs):
        r = int(r_raw)
        if r >= 0:
            z[r] = all(v == 0 for v in sums[c])
        else:
            assert sums[c] == [0] * 5
    return z, sums

def controls():
    sub = float.fromhex('0x0.0000000000001p-1022')
    l = np.zeros((5, 4), dtype=np.float64)
    l[0] = [1., -1., sub, -0.]
    nr = np.array([1, 2, 6, 7], dtype=np.int64)
    ch = np.array([0, 0, 2, 2], dtype=np.int64)
    refs = np.array([0, 3, 5, -1], dtype=np.int64)
    mixed = np.array([False, False, False, False, True, False, False, False])
    z, sums = exact_zero_columns(l, nr, ch, refs, mixed)
    assert z.tolist() == [True, False, False, True, True, False, False, True]
    assert sums[0] == [0] * 5 and sums[1] == [0] * 5 and sums[3] == [0] * 5
    assert sums[2] == [1, 0, 0, 0, 0]
    # Tiny independent rational operation witnesses; no actual-data replay.
    f = lambda x: Fraction(*float(x).as_integer_ratio())
    assert f(1.) * (f(sub) - f(-sub)) == Fraction(2, 1 << 1074)
    assert f(sub) * (f(1.) - f(0.)) == Fraction(1, 1 << 1074)
    assert f(sub) * (f(1.) - f(1.)) == 0
    assert f(sub) != 0 and f(sub) ** 2 * (1 << 2148) == 1
    return {'one_row_channel': True, 'empty_channel': True,
            'exact_reference_cancellation': True, 'signed_zero': True,
            'nonzero_subnormal_column': True, 'exact_subnormal_contrasts': True,
            'tiny_nonzero_unbounded_scaling_witness': True}

def main():
    inp = json.loads((HERE / 'REVIEW_INPUT.json').read_text())
    assert inp['controller_go'] is True
    bindings = inp['bindings']
    for name, obj in bindings.items():
        assert sha(obj['path']) == obj['sha256'], 'INITIAL_SHA:' + name
    read = lambda name: json.loads(Path(bindings[name]['path']).read_text())
    packet = read('review_packet_ack')
    assert packet['packet_id'] == inp['packet_id']
    assert packet['agent_id'] == inp['agent_id'] == '/root/r28_exact_factor_metadata_actual_closeout'
    assert packet['task_id'] == inp['task_id']
    assert packet['input_identity'] == inp['input_identity'] == 'sha256:' + bindings['frozen_input']['sha256']
    assert packet['candidate_identity'] == inp['candidate_identity'] == 'sha256:' + bindings['candidate_result']['sha256']
    assert packet['launch_performed'] is True
    account = read('account_head')
    assert account['unit_review_used_seconds'] == 3.0 and account['unit_review_remaining_seconds'] == 17.0
    assert account['unit_review_cap_seconds'] == 20 and account['unit_consumer_used_seconds'] == 10.5
    assert account['cf4_cumulative_used_seconds'] == 214.79277764664457
    path_binding = read('output_path_binding')
    assert path_binding['actual_candidate_identity'] == inp['candidate_identity']
    assert str(Path(bindings['candidate_result']['path']).parent) == path_binding['actual_products_path']
    assert path_binding['science_input_conventions_tolerances_values_changed'] is False
    old_result = read('original_result')
    result = read('candidate_result')
    assert set(result) == set(old_result) | {'metadata_repair'}
    unchanged_fields = sorted(set(old_result) - {'factor_product_sha256', 'factor_product_bytes'})
    for key in unchanged_fields:
        same_json(old_result[key], result[key], key)
    assert result['factor_product_sha256'] == bindings['candidate_factor']['sha256']
    assert result['factor_product_bytes'] == Path(bindings['candidate_factor']['path']).stat().st_size
    prior_receipt = read('prior_review_receipt')
    prior_stderr = Path(bindings['prior_review_stderr']['path']).read_text()
    assert prior_receipt['status'] == 'FIRST_CHECK_FAILURE' and prior_receipt['returncode'] == 1
    assert prior_receipt['reason'] is None and prior_receipt['numeric_groups_started'] == 1
    assert prior_receipt['source_sha256']['check.py'] == bindings['prior_review_checker']['sha256']
    assert prior_receipt['source_sha256']['REVIEW_INPUT.json'] == bindings['prior_review_input']['sha256']
    assert 'line 161, in main' in prior_stderr
    assert prior_stderr.rstrip().endswith('AssertionError: NEW_ZERO_LEVERAGE_MASK_MISMATCH')
    old_binding = read('prior_review_input')['bindings']
    for old_name, new_name in [('candidate_factor', 'original_factor'), ('candidate_result', 'original_result'), ('author_input', 'frozen_input')]:
        same_json(old_binding[old_name], bindings[new_name], 'historical_binding.' + old_name)
    with np.load(bindings['original_factor']['path'], allow_pickle=False) as old_npz, np.load(bindings['candidate_factor']['path'], allow_pickle=False) as new_npz:
        old = {key: old_npz[key] for key in old_npz.files}
        new = {key: new_npz[key] for key in new_npz.files}
    assert len(old) == len(set(old_npz.files)) and len(new) == len(set(new_npz.files))
    assert set(new) == set(old) | {'exact_zero_leverage_mask', 'legacy_parent_extra_zero_leverage_mask'}
    unchanged_arrays = sorted(set(old) - {'extra_zero_leverage_mask'})
    for name in unchanged_arrays:
        same_bits(old[name], new[name], name)
    same_bits(old['extra_zero_leverage_mask'], new['legacy_parent_extra_zero_leverage_mask'], 'legacy mask')
    ids = new['group_id']; support = new['selected_support_7']
    singleton = new['active_singleton_mask']; mixed = new['mixed_zero_leverage_mask']
    nr = new['nonreference_row_index']; channels = new['nonreference_channel']
    refs = new['reference_row_by_channel']; refrows = new['difference_reference_row_index']
    l = new['L_binary64']; d = new['d_binary64']
    count = len(ids)
    assert count == 35970 and ids.dtype == np.int64 and len(set(map(int, ids))) == count
    assert support.shape == (count, 7) and support.dtype == np.bool_
    assert singleton.dtype == mixed.dtype == np.bool_ and singleton.shape == mixed.shape == (count,)
    assert np.array_equal(singleton, support.sum(axis=1) == 1)
    assert np.array_equal(mixed, support.sum(axis=1) > 1)
    assert np.all(singleton | mixed) and not np.any(singleton & mixed)
    for index in [nr, channels, refs, refrows]:
        assert index.dtype == np.int64 and index.ndim == 1
    assert refs.shape == (7,) and nr.shape == channels.shape == refrows.shape
    assert np.all((refs >= -1) & (refs < count)) and np.all((nr >= 0) & (nr < count))
    assert np.all((channels >= 0) & (channels < 7)) and np.all(np.diff(nr) > 0)
    valid_refs = refs[refs >= 0]
    assert len(set(map(int, valid_refs))) == len(valid_refs)
    coverage = np.zeros(count, dtype=np.int64)
    coverage[mixed] += 1; coverage[valid_refs] += 1; coverage[nr] += 1
    assert np.all(coverage == 1), 'FACTOR_PARTITION'
    assert np.array_equal(refrows, refs[channels]) and np.all(refrows >= 0)
    assert np.array_equal(support[nr], support[refrows])
    assert np.all(singleton[nr]) and np.all(singleton[valid_refs])
    assert np.all(support[nr, channels])
    counts = []
    for c, r in enumerate(refs):
        rows = np.flatnonzero(singleton & support[:, c])
        counts.append(len(rows))
        assert (r == -1) == (len(rows) == 0)
        if r >= 0:
            assert int(r) == min(map(int, rows), key=lambda i: (float(d[i]), int(ids[i])))
    assert counts == result['channel_row_counts'] and len(nr) == result['nonreference_count']
    full_zero, exact_sums = exact_zero_columns(l, nr, channels, refs, mixed)
    extra = full_zero & ~mixed
    for name, expected in [('exact_zero_leverage_mask', full_zero), ('extra_zero_leverage_mask', extra)]:
        assert new[name].dtype == np.bool_ and new[name].shape == (count,)
        assert np.array_equal(new[name], expected), 'INDEPENDENT_MASK:' + name
    legacy = new['legacy_parent_extra_zero_leverage_mask']
    added = np.flatnonzero(extra & ~legacy); removed = np.flatnonzero(legacy & ~extra)
    zero_rows = np.flatnonzero(full_zero); effective_ids = ids[~full_zero]
    witness = int(np.flatnonzero(ids == 11274)[0])
    assert witness == 1484 and bool(extra[witness]) and bool(full_zero[witness]) and not bool(mixed[witness])
    assert refs[3] == witness and counts[3] == 1 and not np.any(channels == 3)
    # Metadata assertions are bound to independently computed quantities below.
    metadata_expected = {
        'row_count': count, 'mixed_zero_count': int(mixed.sum()),
        'legacy_extra_zero_count': int(legacy.sum()), 'current_extra_zero_count': int(extra.sum()),
        'exact_zero_count': int(full_zero.sum()), 'effective_nonzero_count': int((~full_zero).sum()),
        'current_extra_row_indices': np.flatnonzero(extra).tolist(),
        'current_extra_group_ids': ids[extra].tolist(),
        'added_row_indices': added.tolist(), 'added_group_ids': ids[added].tolist(),
        'removed_row_indices': removed.tolist(), 'removed_group_ids': ids[removed].tolist(),
    }
    for item in inp['metadata_assertions']:
        got = result['metadata_repair']
        for key in item['path']:
            got = got[key]
        expected = metadata_expected[item['derived']] if 'derived' in item else item['equals']
        same_json(got, expected, 'metadata_repair.' + '.'.join(item['path']))
    required_derived_metadata = {'legacy_extra_zero_count', 'current_extra_zero_count', 'exact_zero_count',
                                 'current_extra_row_indices', 'current_extra_group_ids',
                                 'added_row_indices', 'added_group_ids', 'removed_row_indices', 'removed_group_ids'}
    assert required_derived_metadata <= {item.get('derived') for item in inp['metadata_assertions']}
    # Complete the previously unexecuted deterministic combined remapping check.
    p = np.arange(count, dtype=np.int64)[::-1]
    q = np.asarray([6, 2, 0, 5, 3, 1, 4], dtype=np.int64)
    permuted_support = support[p][:, q]
    for new_c, old_c in enumerate(q):
        rows = np.flatnonzero(singleton[p] & permuted_support[:, new_c])
        if len(rows):
            chosen = min(map(int, rows), key=lambda j: (float(d[p[j]]), int(ids[p[j]])))
            assert int(p[chosen]) == int(refs[old_c])
    inv = np.empty(count, dtype=np.int64); inv[p] = np.arange(count)
    assert np.array_equal(p[inv[nr]], nr) and np.array_equal(p[inv[refrows]], refrows)
    assert np.array_equal(permuted_support[inv[nr]], permuted_support[inv[refrows]])
    toy = controls()
    for name, obj in bindings.items():
        assert sha(obj['path']) == obj['sha256'], 'FINAL_SHA:' + name
    output = {
        'status': 'ALL_TARGETED_INDEPENDENT_CHECKS_PASSED',
        'independent_mask_algorithm': 'IEEE binary64 bit decomposition into integer multiples of 2^-1074; exact per-channel L sums',
        'all_unaffected_array_names': unchanged_arrays, 'all_unaffected_result_fields': unchanged_fields,
        'all_unaffected_arrays_bit_identical': True, 'all_unaffected_json_fields_type_and_value_or_float_bit_identical': True,
        'partition_and_integer_same_support_identity': True, 'all_mask_meanings_independently_verified': True,
        'mask_counts_and_mismatch': metadata_expected,
        'exact_zero_row_indices': zero_rows.tolist(), 'exact_zero_group_ids': ids[zero_rows].tolist(),
        'effective_group_ids_count': len(effective_ids),
        'effective_group_ids_sha256_int64_le': hashlib.sha256(effective_ids.astype('<i8', copy=False).tobytes()).hexdigest(),
        'combined_row_channel_reference_remapping': True, 'boundary_controls': toy,
        'full_actual_value_and_response_replayed': False,
        'prior_reached_evidence_transferred_by_full_parity': ['exact five-component direct/correction values', 'exact old contraction and channel sums', 'exact correction price', 'display errors and tensor', 'full numerical B/N responses and reported diagnostics'],
        'prior_whole_failed_review_relabelled_pass': False,
        'all_bound_sources_and_candidates_unchanged_after_check': True,
        'environment': {'python': sys.executable, 'python_version': sys.version, 'numpy_version': np.__version__, 'numpy_file': np.__file__},
    }
    (HERE / 'NUMERIC_CHECK.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({'status': output['status'], 'counts': metadata_expected}), flush=True)

if __name__ == '__main__':
    main()
