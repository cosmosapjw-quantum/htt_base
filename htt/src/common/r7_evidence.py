"""Read and bind existing R7 evidence; never execute or promote new science.

This consumer supports the four-axis, seven-obligation R7 algebra contract.
It checks the observed-result schema emitted by cas_gate.py run-adjudicate,
not that command's different stored axis-envelope schema.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

AXES = ('wolfram_xact', 'sympy', 'sage_singular', 'lean')
OBLIGATIONS = frozenset((
    'T1_trace_and_contraction', 'T1_no_proper_signed_stabilizer',
    'T3_normalized_derivative_and_odd_signs', 'T5_first_order_inverse_coefficient',
    'T5_scalar_cost_implication', 'T6_scalar_information_one_fifth',
    'L10_accepted_minors_and_minimal_cutoff',
))
OBSERVED_ORIGIN = 'runner_observed_local_subprocess'


def file_state(path):
    """Identity of a named local dependency, including its absence."""
    path = Path(path)
    try:
        return {'status': 'PRESENT', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    except FileNotFoundError:
        return {'status': 'MISSING'}
    except OSError as exc:
        return {'status': 'UNREADABLE', 'error': type(exc).__name__}


def read_evidence_json(path):
    """Unavailable or malformed optional evidence cannot award a capability."""
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        return {}, [f'{path}: {type(exc).__name__}']
    if not isinstance(value, dict):
        return {}, [f'{path}: expected JSON object']
    return value, []


def source_binding(root, expected):
    """Compare declared source pins with current files without changing pins."""
    errors = []
    states = {}
    if not isinstance(expected, dict) or not expected:
        return {'eligible': False, 'errors': ['nonempty source binding required'], 'source_states': states}
    for name, digest in expected.items():
        if not isinstance(name, str) or not name:
            errors.append('source path is missing')
            continue
        path = Path(root) / name
        state = file_state(path)
        states[name] = state
        if not isinstance(digest, str) or len(digest) != 64 or state.get('sha256') != digest:
            errors.append(f'source identity mismatch or unavailable: {name}')
    return {'eligible': not errors, 'errors': errors, 'source_states': states}


def review_evidence_binding(root, review_path):
    review, errors = read_evidence_json(review_path)
    binding = source_binding(root, review.get('final_source_sha256'))
    errors += binding['errors']
    if review.get('status') != 'PASS':
        errors.append('review status is not PASS')
    return review, {**binding, 'eligible': not errors, 'errors': errors}


def cas_evidence_binding(root, report_path, contract_path):
    report, errors = read_evidence_json(report_path)
    contract, contract_errors = read_evidence_json(contract_path)
    errors += contract_errors
    identity = contract.get('identity', {})
    target = contract.get('target', {})
    if not isinstance(identity, dict): identity = {}
    if not isinstance(target, dict): target = {}
    required = contract.get('required_axes')
    obligations = target.get('exact_test_obligations')
    supported_obligations = (isinstance(obligations, list)
        and all(isinstance(item, str) for item in obligations)
        and len(obligations) == len(OBLIGATIONS) and set(obligations) == OBLIGATIONS)
    if (contract.get('schema_version') != 2 or contract.get('risk_tier') != 'R3'
            or required != list(AXES)
            or identity.get('contract_id') != 'R7-ELEMENTARY-AND-EXTENDED-IMPLICATIONS'
            or not supported_obligations):
        errors.append('unsupported R7 contract scope/schema/axes/obligations')
    source_refs = identity.get('source_input_hashes')
    expected = {}
    if isinstance(source_refs, list):
        for item in source_refs:
            if not isinstance(item, dict) or not isinstance(item.get('path'), str):
                errors.append('invalid contract source binding')
            else:
                expected[item['path']] = item.get('sha256')
        if len(expected) != len(source_refs): errors.append('duplicate or invalid contract source binding')
    sources = source_binding(root, expected)
    errors += sources['errors']
    contract_state = file_state(contract_path)
    if (report.get('schema_version') != 2
            or report.get('contract_id') != identity.get('contract_id')
            or report.get('contract_sha256') != contract_state.get('sha256')
            or contract_state['status'] != 'PRESENT'
            or report.get('risk_tier') != 'R3'
            or report.get('required_axes') != list(AXES)):
        errors.append('CAS report does not bind the current contract and four required axes')
    if (report.get('aggregate_status') != 'CAS_4AXIS_PASS'
            or report.get('verification_state') != 'RUNNER_OBSERVED_EXECUTION'
            or report.get('evidence_origin') != OBSERVED_ORIGIN
            or report.get('claim_promotion_cas_eligible') is not True
            or report.get('claim_promotion_cas_requirement') != 'SATISFIED'
            or any(report.get(key) != [] for key in ('errors', 'missing_axes', 'exceptions_applied'))):
        errors.append('CAS aggregate is not eligible observed four-axis PASS')
    statuses = report.get('axis_statuses')
    evidence = report.get('execution_evidence')
    if not isinstance(statuses, dict): statuses = {}
    if not isinstance(evidence, dict): evidence = {}
    if set(statuses) != set(AXES) or set(evidence) != set(AXES):
        errors.append('CAS axis status/execution set differs from required axes')
    for axis in AXES:
        record = evidence.get(axis, {})
        if not isinstance(record, dict): record = {}
        payload = record.get('payload', {})
        if not isinstance(payload, dict): payload = {}
        checks = payload.get('checks')
        if (statuses.get(axis) != 'PASS' or record.get('derived_status') != 'PASS'
                or record.get('axis') != axis or record.get('evidence_origin') != OBSERVED_ORIGIN
                or record.get('solver_executed') is not True or record.get('timed_out') is not False
                or type(record.get('exit_code')) is not int or record['exit_code'] != 0
                or record.get('errors') != [] or not record.get('argv')
                or not record.get('started_at') or not record.get('completed_at')
                or not isinstance(checks, dict) or set(checks) != OBLIGATIONS
                or any(value is not True for value in checks.values())
                or payload.get('domain_assumption_diff') != []
                or 'counterexample' not in payload or payload['counterexample'] is not None):
            errors.append(f'{axis}: incomplete, failed, or inconsistent observed execution')
    return report, {'eligible': not errors, 'errors': errors,
                    'contract_state': contract_state, 'source_states': sources['source_states'],
                    'scope': identity.get('claim_ceiling')}


def evidence_dependencies(root, report_path, contract_path=None):
    """Named evidence and every explicitly pinned source, even when absent."""
    root = Path(root)
    paths = [Path(report_path)]
    if contract_path is not None:
        paths.append(Path(contract_path))
        contract, _ = read_evidence_json(contract_path)
        identity = contract.get('identity', {})
        refs = identity.get('source_input_hashes', []) if isinstance(identity, dict) else []
        if isinstance(refs, list):
            paths += [root / item['path'] for item in refs
                      if isinstance(item, dict) and isinstance(item.get('path'), str)]
    else:
        review, _ = read_evidence_json(report_path)
        refs = review.get('final_source_sha256', {})
        if isinstance(refs, dict): paths += [root / p for p in refs if isinstance(p, str)]
    return paths
