"""Bounded saved-carrier consumer. Numerical imports occur only in the GO child."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import traceback
import uuid

HERE = Path(__file__).resolve().parent
REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BANDS = (30, 44, 70, 100, 143, 217, 353)
TARGETS = (44, 70, 100, 217)
ACCOUNTS = tuple(map(str, BANDS)) + ('SMICA',)
MAX_WALL = 60.0
KILL_RESERVE = 2.0
RSS_CAP = 2 * 1024**3
PRELAUNCH_MEM = 10 * 1024**3
RUNTIME_MEM_FLOOR = 4 * 1024**3


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
    temporary.replace(path)


def seal(ref):
    path = Path(ref['path'])
    if path.stat().st_size != ref['bytes'] or sha(path) != ref['sha256']:
        raise RuntimeError('IMMUTABLE_SOURCE_SEAL ' + str(path))
    return path


def shared_debit(base_cumulative, elapsed):
    if not (0 < elapsed <= MAX_WALL):
        raise RuntimeError('INVALID_MEASURED_ELAPSED')
    debit = elapsed / len(ACCOUNTS)
    cumulative = {key: base_cumulative[key] + debit for key in ACCOUNTS}
    if any(cumulative[key] >= 900 for key in ACCOUNTS):
        raise RuntimeError('INHERITED_ACCOUNT_CAP_EXCEEDED')
    return debit, cumulative


def build_ledger_delta(base, base_ref, elapsed, attempt_id, packet_id, status):
    charged = min(elapsed, MAX_WALL)
    debit, cumulative = shared_debit(base['cumulative_charged_seconds'], charged)
    return {'schema': 'htt.delivered_seven_frequency_ledger_delta/1',
        'attempt_id': attempt_id, 'base_ledger_ref': base_ref, 'packet_id': packet_id,
        'charged_total_wall_seconds': charged, 'elapsed_measured_wall_seconds': elapsed,
        'shared_debit_each_of_eight_seconds': debit, 'accounts': list(ACCOUNTS),
        'cumulative_charged_seconds': cumulative, 'status': status,
        'old_first_failures_preserved': base.get('first_failures', []),
        'old_stage_preserved': base.get('stage')}


def mem_available():
    for row in Path('/proc/meminfo').read_text().splitlines():
        if row.startswith('MemAvailable:'):
            return int(row.split()[1]) * 1024
    raise RuntimeError('MEMAVAILABLE_UNOBSERVED')


def proc_rss(pid):
    try:
        for row in Path(f'/proc/{pid}/status').read_text().splitlines():
            if row.startswith('VmRSS:'):
                return int(row.split()[1]) * 1024
    except (FileNotFoundError, ProcessLookupError):
        pass
    return 0


def verify_binding(args):
    input_path, packet_path = Path(args.input), Path(args.packet)
    if sha(input_path) != args.input_sha or sha(packet_path) != args.packet_sha:
        raise RuntimeError('INPUT_OR_PACKET_SHA_MISMATCH')
    input_data, packet = read_json(input_path), read_json(packet_path)
    contract = read_json(seal(input_data['contract']))
    if input_data['stage'] != 'PREPARED_NOT_DISPATCHED':
        raise RuntimeError('INPUT_STAGE_DRIFT')
    if packet.get('task_id') != input_data['task_id'] or packet.get('input_identity') != 'sha256:' + args.input_sha:
        raise RuntimeError('PACKET_TASK_OR_INPUT_MISMATCH')
    ack = packet.get('acknowledgement', {})
    if (packet.get('launch_performed') is not True or not packet.get('packet_id')
            or not packet.get('agent_id') or ack.get('status') != 'GO'
            or ack.get('packet_id') != packet['packet_id']
            or ack.get('agent_id') != packet['agent_id']):
        raise RuntimeError('GENUINE_CONTROLLER_GO_REQUIRED')
    if packet.get('source_sha256') != sha(HERE / 'consume.py'):
        raise RuntimeError('PREPARED_SOURCE_DRIFT')
    if contract['task_id'] != input_data['accounting_parent_task_id']:
        raise RuntimeError('CONTRACT_PARENT_TASK_MISMATCH')
    if tuple(contract['input_bands_GHz']) != BANDS:
        raise RuntimeError('BAND_CONTRACT_DRIFT')
    return input_data, contract, packet


def numerical_child(input_data, contract, packet):
    # This function is entered only from the bound GO subprocess.
    import importlib.util
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from threadpoolctl import threadpool_info

    refs = contract['immutable_sources']
    qualification = read_json(seal(input_data['qualification']))
    if (qualification['all_seven_canonical24_finite'] is not True
            or qualification['support'] != contract['operator']['support']):
        raise RuntimeError('SOURCE_QUALIFICATION_CONFLICT')
    for key in ('old_math', 'decoder', 's4_equivalence', 's4_manifest', 's4_validation',
                'frozen_input', 'first_raw_receipt', 'terminal_ledger', 'original_selected_support'):
        seal(refs[key])
    math_path = seal(refs['old_math'])
    spec = importlib.util.spec_from_file_location('sealed_full7_math', math_path)
    old_math = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old_math)
    if Path(old_math.__file__).resolve() != math_path.resolve():
        raise RuntimeError('OLD_MATH_IMPORT_PATH_DRIFT')
    if tuple(old_math.BANDS) != BANDS or tuple(old_math.TARGETS) != TARGETS:
        raise RuntimeError('OLD_MATH_CONSTANT_DRIFT')

    # Narrow source and synthetic control is part of this one accounted child.
    ae = np.zeros((12, 2)); ae[0, 0] = 1e-5; ae[1, 1] = 2e-5
    ab = np.zeros((12, 2)); ab[0, 0] = 3e-6; ab[1, 1] = -4e-6
    fixture = {b: np.zeros(24) for b in BANDS}
    fixture[30] = np.r_[ae[:, 0], ab[:, 0]]
    fixture[353] = np.r_[ae[:, 1], ab[:, 1]]
    fixture[44] = np.r_[ae @ np.array([2., -1.]), ab @ np.array([2., -1.]) + 1e-7]
    synthetic = old_math.crossprediction(fixture)
    expected = np.array([2., -1.])
    if not np.allclose(synthetic['targets']['44']['coefficients'], expected):
        raise RuntimeError('SYNTHETIC_FIT_FAILURE')
    fixture_changed = {b: v.copy() for b, v in fixture.items()}
    fixture_changed[44][12:] += 7e-6
    if synthetic['targets']['44']['coefficients'] != old_math.crossprediction(fixture_changed)['targets']['44']['coefficients']:
        raise RuntimeError('B_TARGET_INFLUENCED_E_FIT')
    deficient = {b: np.zeros(24) for b in BANDS}
    deficient[30][0] = 1e-5
    deficient[353][0] = 2e-5
    failed = old_math.crossprediction(deficient)['targets']['44']
    if failed['conditioning'] != 'ANCHOR_FIT_ILL_CONDITIONED' or 'B_prediction_12_K_CMB' in failed:
        raise RuntimeError('RANK_GATE_FAILURE')
    try:
        old_math.crossprediction({k: v for k, v in fixture.items() if k != 353})
    except ValueError:
        pass
    else:
        raise RuntimeError('MISSING_353_WAS_ACCEPTED')
    old_base = read_json(Path(contract['same_accounting']['base']['path']))
    try:
        raise RuntimeError('SIMULATED_CONSUMER_EXCEPTION')
    except RuntimeError:
        simulated = build_ledger_delta(old_base, contract['same_accounting']['base'],
                                       .5, 'synthetic-only', packet['packet_id'], 'FAILED_PRESERVED')
    if (simulated['shared_debit_each_of_eight_seconds'] != .5 / 8
            or simulated['old_first_failures_preserved'] != old_base['first_failures']
            or simulated['old_stage_preserved'] != old_base['stage']
            or any(simulated['cumulative_charged_seconds'][key] <= old_base['cumulative_charged_seconds'][key]
                   for key in ACCOUNTS)):
        raise RuntimeError('EXCEPTION_DEBIT_CONTROL_FAILURE')

    s7_path, s4_path = seal(refs['s7_support']), seal(refs['s4_support'])
    seal(refs['s4_equivalence'])
    equivalence = read_json(Path(refs['s4_equivalence']['path']))
    if equivalence['decision'] != 'NUMERICAL_EQUIVALENCE_REUSE_APPROVED':
        raise RuntimeError('S4_REUSE_NOT_APPROVED')
    with np.load(s7_path, allow_pickle=False) as s7, np.load(s4_path, allow_pickle=False) as s4:
        ring7 = np.asarray(s7['s7_mask_ring64'], dtype=bool)
        ring4 = np.asarray(s4['s4_mask_ring64'], dtype=bool)
        selected = np.asarray(s4['selected_mask_ring64'], dtype=bool)
        if (ring7.shape != (49152,) or not np.array_equal(ring7, ring4)
                or not np.array_equal(ring7, selected) or int(ring7.sum()) != 30021
                or np.asarray(s7['s7_mask_nest64']).shape != (49152,)):
            raise RuntimeError('S7_S4_SELECTED_SUPPORT_DRIFT')
    with np.load(Path(refs['original_selected_support']['path']), allow_pickle=False) as original:
        if not np.array_equal(ring7, np.asarray(original['selected_mask_ring64'], dtype=bool)):
            raise RuntimeError('S7_ORIGINAL_SUPPORT_DRIFT')

    s4_manifest = read_json(Path(refs['s4_manifest']['path']))
    if (s4_manifest['files_sha256']['FULL_CARRIER_AND_CONTRASTS.npz'] != refs['completed_carriers']['S4']['sha256']
            or s4_manifest['files_sha256']['COMMON_SUPPORT_S4.npz'] != refs['s4_support']['sha256']):
        raise RuntimeError('S4_MANIFEST_CONFLICT')
    carriers = {}
    tensor_names = ('E2', 'E3', 'B2', 'B3')
    tensor_shapes = ((3, 3), (3, 3, 3), (3, 3), (3, 3, 3))
    tensors = {}
    with np.load(seal(refs['completed_carriers']['S4']), allow_pickle=False) as saved:
        if list(saved['bands_GHz']) != [30, 44, 70, 100] or saved['carrier_canonical_96'].shape != (4, 24):
            raise RuntimeError('S4_CARRIER_LAYOUT')
        for i, b in enumerate((30, 44, 70, 100)):
            carriers[b] = np.asarray(saved['carrier_canonical_96'][i], dtype=float).copy()
            tensors[b] = [np.asarray(saved[n + '_stf'][i], dtype=float).copy() for n in tensor_names]
    for b in (143, 217, 353):
        with np.load(seal(refs['completed_carriers'][str(b)]), allow_pickle=False) as saved:
            carriers[b] = np.asarray(saved['canonical24'], dtype=float).copy()
            tensors[b] = [np.asarray(saved[n], dtype=float).copy() for n in tensor_names]
    for b in BANDS:
        c = carriers[b]
        if c.shape != (24,) or not np.isfinite(c).all():
            raise RuntimeError('CARRIER_SHAPE_OR_FINITE ' + str(b))
        decoded = old_math.decode_stf(c, REPO)
        for name, actual, expected_tensor, shape in zip(tensor_names, tensors[b], decoded, tensor_shapes):
            if actual.shape != shape or not np.isfinite(actual).all() or not np.allclose(actual, expected_tensor, rtol=1e-9, atol=1e-12):
                raise RuntimeError('STF_DECODE_PARITY ' + str(b) + ' ' + name)
    for b in (143, 217, 353):
        control = read_json(seal(refs['completed_controls'][str(b)]))
        tolerance = 1e-12 + 1e-9 * np.abs(carriers[b])
        for name in ('main_reduction_bound24', 'second_reduction_bound24'):
            bounds = np.asarray(control[name], dtype=float)
            if bounds.shape != (24,) or not np.isfinite(bounds).all() or np.any(bounds < 0) or np.any(bounds > tolerance / 8):
                raise RuntimeError('PRESERVED_REDUCTION_CONTROL ' + str(b) + ' ' + name)
        if (control['main_rows'] != 131072 or control['second_rows'] != 131071
                or control['selected_native_pixels'] != 30741504):
            raise RuntimeError('PRESERVED_CONTROL_LAYOUT ' + str(b))

    fit = old_math.crossprediction(carriers)
    frequency = old_math.computational_frequency_image(carriers)
    grid = np.stack([carriers[b] for b in BANDS]); contrasts = np.stack([carriers[b] - carriers[143] for b in BANDS if b != 143])
    anchor_e = np.asarray(fit['anchor_E_12x2_K_CMB']); anchor_b = np.asarray(fit['anchor_B_12x2_K_CMB'])
    target_e = np.stack([fit['targets'][str(b)]['target_E_12_K_CMB'] for b in TARGETS])
    target_b = np.stack([fit['targets'][str(b)]['target_B_12_K_CMB'] for b in TARGETS])
    rank_ok = fit['s2_over_s1'] > 1e-8
    coefficients = np.full((4, 2), np.nan); pred_b = np.full((4, 12), np.nan)
    residual_e = np.full((4, 12), np.nan); residual_b = np.full((4, 12), np.nan)
    if rank_ok:
        for i, b in enumerate(TARGETS):
            row = fit['targets'][str(b)]
            coefficients[i] = row['coefficients']; pred_b[i] = row['B_prediction_12_K_CMB']
            residual_e[i] = row['E_residual_12_K_CMB']; residual_b[i] = row['B_residual_12_K_CMB']
            if not np.allclose(target_b[i] - pred_b[i], residual_b[i], rtol=1e-13, atol=1e-15):
                raise RuntimeError('B_RESIDUAL_SIGN ' + str(b))
    block_labels = []
    for kind in ('E', 'B'):
        for ell in (2, 3):
            block_labels.append(f'{kind}{ell}:m0')
            for m in range(1, ell + 1):
                block_labels += [f'{kind}{ell}:sqrt2Re{m}', f'{kind}{ell}:-sqrt2Im{m}']
    if len(block_labels) != 24 or grid.shape != (7, 24) or contrasts.shape != (6, 24):
        raise RuntimeError('SIGNED_COORDINATE_LAYOUT')

    # No native arrays or source data are read by rendering.
    np.savez_compressed(HERE / 'FULL7_CARRIER.npz', bands_GHz=np.asarray(BANDS),
        frequency_canonical_7x24=grid, reference143_bands_GHz=np.asarray([b for b in BANDS if b != 143]),
        reference143_contrasts_6x24=contrasts, coordinate_labels=np.asarray(block_labels),
        E2_stf=np.stack([tensors[b][0] for b in BANDS]), E3_stf=np.stack([tensors[b][1] for b in BANDS]),
        B2_stf=np.stack([tensors[b][2] for b in BANDS]), B3_stf=np.stack([tensors[b][3] for b in BANDS]),
        s7_support_ring64=np.flatnonzero(ring7), anchor_E=anchor_e, anchor_B=anchor_b,
        target_bands_GHz=np.asarray(TARGETS), target_E=target_e, target_B=target_b,
        coefficients_E_fit=coefficients, prediction_B=pred_b, residual_E=residual_e,
        residual_B=residual_b, prediction_valid=np.full(4, rank_ok))

    fig, ax = plt.subplots(figsize=(15, 5.5), constrained_layout=True)
    scale = float(np.max(np.abs(grid))) or 1.0
    im = ax.imshow(grid, aspect='auto', cmap='RdBu_r', vmin=-scale, vmax=scale)
    ax.set_yticks(range(7), [str(b) for b in BANDS]); ax.set_xticks(range(24), block_labels, rotation=75, ha='right', fontsize=7)
    ax.set_ylabel('Frequency (GHz)'); ax.set_title('Seven delivered signed spin-2 carriers | S7 = S4, 30,021 cells | descriptive')
    fig.colorbar(im, ax=ax, label='K_CMB'); fig.savefig(HERE / 'signed24.png', dpi=150); plt.close(fig)

    fig, axes = plt.subplots(4, 1, figsize=(13, 11), sharex=True, constrained_layout=True)
    x = np.arange(12)
    for i, b in enumerate(TARGETS):
        ax = axes[i]; ax.axhline(0, color='0.5', lw=.7)
        ax.plot(x, target_b[i], 'o-', label='target B')
        if rank_ok:
            ax.plot(x, pred_b[i], 's--', label='E-fit prediction B')
            ax.plot(x, residual_b[i], 'x:', label='target - prediction')
        else:
            ax.text(.01, .86, 'ANCHOR_FIT_ILL_CONDITIONED; prediction omitted', transform=ax.transAxes)
        ax.set_ylabel(f'{b} GHz\nK_CMB'); ax.legend(fontsize=8, ncol=3, loc='upper right')
    axes[-1].set_xticks(x, block_labels[12:], rotation=60, ha='right')
    fig.suptitle('143-relative heldout B coordinates | algorithmic E-to-B check, descriptive')
    fig.savefig(HERE / 'heldout_B12.png', dpi=150); plt.close(fig)

    q = [frequency['Q'][str(b)] for b in BANDS]
    thresholds = frequency['F_frequency']['ordered_thresholds']
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    axes[0].bar([str(b) for b in BANDS], q); axes[0].set_xlabel('Frequency (GHz)'); axes[0].set_ylabel('Q = ||c/1e-5 K_CMB||')
    axes[1].step([0] + thresholds, [0] + [i/7 for i in range(1, 8)], where='post')
    axes[1].set_xlabel('Threshold t'); axes[1].set_ylabel('F_frequency(t)')
    axes[1].set_ylim(0, 1.04)
    fig.suptitle('Computational frequency image | uniform mass 1/7, no calibrated law')
    fig.savefig(HERE / 'frequency_image.png', dpi=150); plt.close(fig)

    with np.load(HERE / 'FULL7_CARRIER.npz', allow_pickle=False) as saved:
        if not np.array_equal(saved['frequency_canonical_7x24'], grid) or not np.array_equal(saved['target_B'], target_b):
            raise RuntimeError('NPZ_JSON_PARITY')
        if rank_ok and (not np.array_equal(saved['prediction_B'], pred_b) or not np.array_equal(saved['residual_B'], residual_b)):
            raise RuntimeError('NPZ_JSON_PREDICTION_PARITY')
    result = {
        'schema': 'htt.delivered_seven_frequency_descriptive_result/1',
        'task_id': input_data['task_id'], 'packet_id': packet['packet_id'],
        'input_identity': packet['input_identity'],
        'source_product_input_support_identities': refs,
        'operator': contract['operator'], 'bands_GHz': list(BANDS), 'target_bands_GHz': list(TARGETS),
        'coordinate_labels': block_labels, 'units': 'K_CMB',
        'frequency_canonical_7x24_K_CMB': grid.tolist(),
        'reference143_bands_GHz': [b for b in BANDS if b != 143],
        'reference143_contrasts_6x24_K_CMB': contrasts.tolist(),
        'E2_stf': np.stack([tensors[b][0] for b in BANDS]).tolist(),
        'E3_stf': np.stack([tensors[b][1] for b in BANDS]).tolist(),
        'B2_stf': np.stack([tensors[b][2] for b in BANDS]).tolist(),
        'B3_stf': np.stack([tensors[b][3] for b in BANDS]).tolist(),
        'crossprediction': fit, 'computational_frequency_image': frequency,
        'S7_equals_S4_observed': True, 'selected_support_count': 30021,
        'SMICA_status': 'OPTIONAL_COMPARATOR_NOT_DELIVERED_FAILED_ONE_USE',
        'same_account_debit_ref': str(HERE / 'LEDGER_DELTA.json'),
        'claim_ceiling': contract['claim_ceiling'], 'independent_result_review': 'REQUIRED',
        'scientific_admission': 'HOLD',
        'loaded_threadpools': threadpool_info(),
        'validation_evidence': ['sealed_inputs', 'S7_equals_S4', 'seven_finite_24', 'STF_decode_parity',
            'preserved_controls', 'synthetic_independent_fit_and_B_invariance', 'rank_gate',
            'missing353_rejected', 'NPZ_JSON_parity', 'three_scientific_plots']}
    write_json(HERE / 'DESCRIPTIVE_RESULT.json', result)
    serialized = read_json(HERE / 'DESCRIPTIVE_RESULT.json')
    if (serialized['frequency_canonical_7x24_K_CMB'] != grid.tolist()
            or serialized['crossprediction']['targets'] != fit['targets']):
        raise RuntimeError('NPZ_JSON_RESULT_PARITY')
    magnitudes = np.abs(grid)
    top = sorted(((float(magnitudes[i,j]), int(BANDS[i]), block_labels[j], float(grid[i,j]))
                  for i in range(7) for j in range(24)), reverse=True)[:5]
    residuals = {str(b): fit['targets'][str(b)].get('B_residual_norm_K_CMB', 'ILL_CONDITIONED') for b in TARGETS}
    (HERE / 'REPORT.md').write_text(
        '# Delivered seven-frequency descriptive result\n\n'
        'Seven saved Planck PR3 carrier vectors use the sealed 30,021-cell support and Galactic COSMO K_CMB convention. '
        'The largest absolute signed coordinates (magnitude, GHz, coordinate, signed K_CMB) are '
        + json.dumps(top) + '.\n\n'
        'Four fixed E-derived fits give B residual norms (K_CMB): ' + json.dumps(residuals) + '. '
        'These are algorithmic heldout coordinates with mask leakage and cross-frequency dependence unmodelled. '
        'Q and F_frequency are computational images of seven frequency points. '
        'No calibrated null, physical mixture fraction, true-sky E/B separation or Bianchi-family claim follows. '
        'SMICA remains the preserved optional failed comparator; the original full8 acceptance remains HOLD.\n')
    return result


def child_main(args):
    data, contract, packet = verify_binding(args)
    result = numerical_child(data, contract, packet)
    print(json.dumps({'status': 'CANDIDATE_READY_REVIEW_REQUIRED', 'result': str(HERE / 'DESCRIPTIVE_RESULT.json'),
                      'carrier': str(HERE / 'FULL7_CARRIER.npz'), 'targets': len(result['crossprediction']['targets'])}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True); parser.add_argument('--input-sha', required=True)
    parser.add_argument('--packet', required=True); parser.add_argument('--packet-sha', required=True)
    parser.add_argument('--child', action='store_true')
    args = parser.parse_args()
    if args.child:
        child_main(args); return
    start = time.monotonic(); utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    attempt_id = uuid.uuid4().hex
    child = None; wait_status = None; usage = None; exception = None; trigger = None
    sampled_peak = 0; minimum_mem = 2**63-1
    output = {'status': 'PRELAUNCH'}
    try:
        data, contract, packet = verify_binding(args)
        ledger_path = seal(contract['same_accounting']['base'])
        base = read_json(ledger_path)
        if base['cumulative_charged_seconds'] != contract['same_accounting']['base_cumulative_charged_seconds']:
            raise RuntimeError('TERMINAL_ACCOUNT_HEAD_DRIFT')
        if any(900 - base['cumulative_charged_seconds'][k] < MAX_WALL / 8 for k in ACCOUNTS):
            raise RuntimeError('INHERITED_ACCOUNT_CAP_TOO_SMALL')
        before = mem_available()
        if before < PRELAUNCH_MEM:
            raise RuntimeError('PRELAUNCH_MEMAVAILABLE_BELOW_10GIB')
        if any((HERE / name).exists() for name in ('STARTED.json', 'LEDGER_DELTA.json', 'DESCRIPTIVE_RESULT.json')):
            raise RuntimeError('ATTEMPT_ALREADY_STARTED_OR_OUTPUT_EXISTS')
        write_json(HERE / 'STARTED.json', {'attempt_id': attempt_id, 'packet_id': packet['packet_id'],
            'input_sha256': args.input_sha, 'base_ledger_sha256': contract['same_accounting']['base']['sha256'],
            'start_utc': utc, 'wall_envelope_seconds': MAX_WALL})
        command = [sys.executable, '-B', str(HERE / 'consume.py'), '--input', args.input,
                   '--input-sha', args.input_sha, '--packet', args.packet, '--packet-sha', args.packet_sha, '--child']
        env = os.environ.copy()
        for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS',
                    'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS'):
            env[key] = '1'
        env['PYTHONDONTWRITEBYTECODE'] = '1'; env['MPLCONFIGDIR'] = str(HERE / '.mplconfig')
        with (HERE / 'child.stdout').open('xb') as stdout, (HERE / 'child.stderr').open('xb') as stderr:
            child = subprocess.Popen(command, cwd=HERE, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            while True:
                pid, status, ru = os.wait4(child.pid, os.WNOHANG)
                if pid:
                    wait_status, usage = status, ru
                    child.returncode = os.waitstatus_to_exitcode(status)
                    break
                minimum_mem = min(minimum_mem, mem_available())
                sampled_peak = max(sampled_peak, proc_rss(os.getpid()) + proc_rss(child.pid))
                if sampled_peak > RSS_CAP:
                    trigger = 'OWNED_GROUP_RSS_CAP'; break
                if minimum_mem < RUNTIME_MEM_FLOOR:
                    trigger = 'HOST_MEMAVAILABLE_FLOOR'; break
                if time.monotonic() - start >= MAX_WALL - KILL_RESERVE:
                    trigger = 'WALL_CAP_KILL_RESERVE'; break
                time.sleep(.05)
            if trigger:
                os.killpg(child.pid, signal.SIGKILL)
                pid, wait_status, usage = os.wait4(child.pid, 0)
                child.returncode = os.waitstatus_to_exitcode(wait_status)
        if trigger:
            raise RuntimeError(trigger)
        if child.returncode != 0:
            raise RuntimeError('CONSUMER_CHILD_FAILED exit=' + str(child.returncode))
        required = ('FULL7_CARRIER.npz', 'DESCRIPTIVE_RESULT.json', 'signed24.png', 'heldout_B12.png',
                    'frequency_image.png', 'REPORT.md')
        if any(not (HERE / name).is_file() for name in required):
            raise RuntimeError('REQUIRED_OUTPUT_MISSING')
        output = {'status': 'CANDIDATE_READY_REVIEW_REQUIRED',
                  'output_sha256': {name: sha(HERE / name) for name in required}}
    except BaseException as err:
        exception = ''.join(traceback.format_exception(type(err), err, err.__traceback__))
        output = {'status': 'FAILED_PRESERVED', 'failure': str(err)}
    finally:
        elapsed = time.monotonic() - start
        # A started process is charged once even after an exception. The old ledger is immutable.
        if 'contract' in locals():
            base = read_json(Path(contract['same_accounting']['base']['path']))
            delta = build_ledger_delta(base, contract['same_accounting']['base'], elapsed,
                                       attempt_id, packet.get('packet_id'), output['status'])
            write_json(HERE / 'LEDGER_DELTA.json', delta)
        receipt = {'schema': 'htt.delivered_seven_frequency_raw_receipt/1', 'attempt_id': attempt_id,
            'command': sys.argv, 'cwd': str(HERE), 'start_utc': utc, 'elapsed_measured_wall_seconds': elapsed,
            'packet_sha256': args.packet_sha, 'input_sha256': args.input_sha, 'outcome': output,
            'child_pid': child.pid if child else None, 'child_reaped': wait_status is not None,
            'wait_status': wait_status, 'exit_code': child.returncode if child else None,
            'wait4_ru_maxrss_bytes': usage.ru_maxrss * 1024 if usage else None,
            'combined_sampled_peak_bytes': sampled_peak,
            'minimum_host_mem_available_bytes': None if minimum_mem == 2**63-1 else minimum_mem,
            'trigger': trigger, 'exception': exception,
            'stdout': str(HERE / 'child.stdout'), 'stderr': str(HERE / 'child.stderr')}
        write_json(HERE / 'RAW_RECEIPT.json', receipt)
    if output['status'] != 'CANDIDATE_READY_REVIEW_REQUIRED':
        raise SystemExit(output.get('failure', output['status']))
    print(json.dumps(output, sort_keys=True))


if __name__ == '__main__':
    main()
