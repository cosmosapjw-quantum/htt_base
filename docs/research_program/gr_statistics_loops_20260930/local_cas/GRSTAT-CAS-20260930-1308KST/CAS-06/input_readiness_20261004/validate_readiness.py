"""Frozen task-local source-binding oracle; this is not a CAS campaign axis."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(ref):
    if sha(ref['path']) != ref['sha256']:
        raise ValueError('source identity changed: ' + ref['path'])
    return Path(ref['path']).read_text()


def pointer(value, path):
    for key in path.lstrip('/').split('/'):
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def bindings():
    neutral = json.loads((HERE / 'NEUTRAL_INPUT.json').read_text())
    follow = json.loads((HERE / 'FOLLOWUP_CONTRACT.json').read_text())
    checked(follow['neutral_input'])
    for ref in neutral['source_files'] + follow['permitted_inputs']:
        checked(ref)
    for row in neutral['formula_bindings']:
        actual = pointer(json.loads(checked(row['source'])), row['json_pointer'])
        if actual != row['exact_text']:
            raise ValueError('formula text mismatch: ' + row['name'])
        if row['upstream_class'] != 'UNCONTRACTED_REFERENCE':
            raise ValueError('upstream reference promoted')
    row = neutral['assumptions_binding']
    if pointer(json.loads(checked(row['source'])), row['json_pointer']) != row['exact_value']:
        raise ValueError('assumption mismatch')
    row = neutral['conventions_binding']
    source = checked(row['source'])
    if source != row['exact_text'] or row['lines'] != [1, len(source.splitlines())]:
        raise ValueError('neutral conventions mismatch')
    if any(v is not None for v in neutral['missing_definitions'].values()):
        raise ValueError('missing definition filled without source')
    if follow['campaign_engine_dispatch_authorized'] or follow['scientific_admission'] != 'HOLD':
        raise ValueError('readiness claim ceiling violated')
    return {'formula_bindings': len(neutral['formula_bindings']), 'missing_definitions_preserved': True}


def unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError('duplicate JSON key: ' + k)
        result[k] = v
    return result


def candidate(path):
    value = json.loads(Path(path).read_text(), object_pairs_hook=unique)
    expected = dict(metric=0, ode=1, einstein=2, curvature=3, rates=4, weyl=5, scalar=6)
    if set(value) != set(expected) | {'divergence', 'evidence_class'}:
        raise ValueError('classification schema mismatch')
    for key, index in expected.items():
        if type(value[key]) is not int or value[key] != index:
            raise ValueError('wrong source index: ' + key)
    if value['divergence'] is not None or value['evidence_class'] != 'exact':
        raise ValueError('missing divergence invented or evidence enum wrong')
    neutral = json.loads((HERE / 'NEUTRAL_INPUT.json').read_text())
    starts = ['Metric ', 'ODE ', 'All Einstein ', 'R0101=', '|A|=', 'Lambda0,', 'P=Pstar ']
    for key, index in expected.items():
        if not neutral['formula_bindings'][value[key]]['exact_text'].startswith(starts[index]):
            raise ValueError('source classification does not match extant text')
    return {'exact_source_indices': expected, 'divergence': 'NOT_SUPPLIED', 'candidate_sha256': sha(path)}


def scalar_action():
    import sympy as s
    # New helper calculation from supplied neutral action only. No metric/axis replay.
    X, Pstar, alpha = s.symbols('X Pstar alpha', positive=True)
    exponent = (1 + alpha) / (2 * alpha)
    P = Pstar * X**exponent
    PX, PXX = s.diff(P, X), s.diff(P, X, 2)
    rho = 2 * X * PX - P
    ratio = s.cancel(PX / (PX + 2 * X * PXX))
    residuals = {
        'rho_minus_2s_minus_1_P': s.simplify(rho - (2 * exponent - 1) * P),
        'rho_minus_P_over_alpha': s.simplify(rho - P / alpha),
        'sound_speed_ratio_minus_alpha': s.simplify(ratio - alpha),
    }
    if any(v != 0 for v in residuals.values()):
        raise ValueError('scalar-action residual nonzero')
    return {'engine': 'SymPy ' + s.__version__, 'assumptions': 'X>0, Pstar>0, 0<alpha<1; fixed exponent s=(1+alpha)/(2alpha)',
            'P_X': str(PX), 'P_XX': str(PXX), 'rho': str(s.simplify(rho)),
            'sound_speed_ratio': str(s.simplify(ratio)), 'residuals': {k: str(v) for k, v in residuals.items()},
            'scope': 'Formal action derivative identities only; no stress/current/TOV/local-existence proof'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = {'validator_sha256': sha(__file__), 'scientific_admission': 'HOLD', 'campaign_axis': False}
    try:
        result['bindings'] = bindings()
        if args.candidate:
            result['classification'] = candidate(args.candidate)
        result['scalar_action'] = scalar_action()
        result['status'] = 'PASS_READINESS_CHECK_ONLY'
    except (ValueError, KeyError, TypeError, IndexError, OSError, json.JSONDecodeError) as error:
        result.update(status='FAIL', error=str(error))
    with Path(args.output).open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['status'] == 'PASS_READINESS_CHECK_ONLY' else 1)


if __name__ == '__main__':
    main()
