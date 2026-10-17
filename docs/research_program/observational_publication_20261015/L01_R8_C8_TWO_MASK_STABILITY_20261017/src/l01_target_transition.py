"""Target-relative cutoff geometry for the existing L01 checkpoint pipeline.

Read only two or three completed native band directories. Reuse the unchanged
cutoff validator, E/B ordering and no-clobber writer. Angles live in the real
harmonic-coefficient space, not on the sky. No SHT, new beam, noise prior or
infinite-tail convergence certificate is constructed here.
"""
from __future__ import annotations
import argparse
import json
import sys
import zipfile

import numpy as np
import l01_cutoff_band_diagnostics as base

SCHEMA = 'htt.L01_target_relative_cutoff_geometry/1'


def transition(before, after):
    """Separate radial and transverse changes of a fixed low-ell estimand.

    alpha=<x,e>/||x||^2, beta=||e-alpha*x||/||x||, e=y-x.
    Energy ratio = 1+2*alpha+r^2 = (1+alpha)^2+beta^2.
    Norm-only intervals and angle upper bounds refer to this measured step,
    never to the unknown error beyond the last cutoff. Zero bases stay null.
    """
    x, y = base._vector(before), base._vector(after)
    result = {}
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        for name, ix in base.low_indices().items():
            a, b = x[ix], y[ix]
            n0, n1, ne = (base._norm(z) for z in (a, b, b-a))
            rec = {'before_norm_K_CMB': n0, 'after_norm_K_CMB': n1,
                   'increment_norm_K_CMB': ne,
                   'relative_increment_target': None, 'radial_fraction': None,
                   'transverse_fraction': None, 'energy_after_over_before': None,
                   'coefficient_angle_degrees': None, 'angle_upper_bound_degrees': None,
                   'power_ratio_interval_given_increment_norm': None,
                   'energy_identity_relative': None,
                   'status': 'ZERO_BASE_RELATIVE_GEOMETRY_UNDEFINED'}
            if n0:
                unit, e = a/n0, (b-a)/n0
                alpha = float(unit @ e)
                beta = base._norm(e-alpha*unit)
                r = base._norm(e)
                ratio = base._norm(b/n0)**2
                predicted = 1+2*alpha+r*r
                closure = abs(ratio-predicted)/max(1., r*r, ratio)
                bounds = [abs(1-r)**2, (1+r)**2]
                if not np.isfinite([alpha,beta,r,ratio,predicted,closure,*bounds]).all():
                    raise ValueError('TARGET_GEOMETRY_NUMERICAL_RANGE')
                if closure > 2e-12:
                    raise ValueError('TARGET_ENERGY_IDENTITY_FAILED')
                rec.update(relative_increment_target=r, radial_fraction=alpha,
                    transverse_fraction=beta, energy_after_over_before=ratio,
                    coefficient_angle_degrees=float(np.degrees(np.arctan2(beta,1+alpha))) if n1 else None,
                    angle_upper_bound_degrees=float(np.degrees(np.arcsin(r))) if r<1 else None,
                    power_ratio_interval_given_increment_norm=bounds,
                    energy_identity_relative=closure,
                    status='MEASURED_FINITE_TARGET_CHANGE' if n1 else 'ZERO_ENDPOINT_ANGLE_UNDEFINED')
            result[name] = rec
    return result


def successive_steps(first, second):
    """Empirical increment ratio from two observed steps, not a future bound."""
    a, b = base._vector(first), base._vector(second)
    out = {}
    for name, ix in base.low_indices().items():
        u, v = a[ix], b[ix]
        n1, n2 = base._norm(u), base._norm(v)
        ratio = n2/n1 if n1 else None
        align = float((u/n1) @ (v/n2)) if n1 and n2 else None
        if ratio is not None and not np.isfinite(ratio):
            raise ValueError('STEP_RATIO_NUMERICAL_RANGE')
        out[name] = {'first_step_norm_K_CMB':n1, 'second_step_norm_K_CMB':n2,
            'second_step_over_first':ratio, 'step_alignment':align,
            'status':'EMPIRICAL_TWO_INCREMENT_RATIO' if n1 else 'ZERO_FIRST_INCREMENT_RATIO_UNDEFINED',
            'is_future_contraction_bound':False}
    return out


def analyze(band_dirs):
    if len(band_dirs) not in (2,3):
        raise ValueError('TWO_OR_THREE_BAND_DIRECTORIES_REQUIRED')
    runs = [base.load_run(path) for path in band_dirs]
    pairs = []
    for low, high in zip(runs, runs[1:]):
        # Validates strictly increasing cutoff and exactly equal producer
        # contracts except lmax, and reuses the actual band/alm accounting.
        existing = base.compare_runs(low, high)
        subjects = {name:transition(low['vectors'][name][0],high['vectors'][name][0])
                    for name in low['vectors']}
        pairs.append({'cutoffs':existing['cutoffs'], 'subjects':subjects,
            'common_mode_checks':existing['products'],
            'projected_change_budgets':existing['projected_contrast_changes']})
    empirical = {'status':'NOT_EVALUATED_REQUIRES_THREE_CUTOFFS'}
    if len(runs)==3:
        empirical = {'status':'RECORDED_TWO_SUCCESSIVE_FINITE_INCREMENTS',
            'cutoffs':[r['contract']['lmax'] for r in runs],
            'subjects':{name:successive_steps(
                runs[1]['vectors'][name][0]-runs[0]['vectors'][name][0],
                runs[2]['vectors'][name][0]-runs[1]['vectors'][name][0]) for name in runs[0]['vectors']},
            'future_decay_assumption':'NOT_SUPPLIED', 'extrapolated_limit':None}
    return {'schema':SCHEMA, 'status':'PASS_TARGET_GEOMETRY_ACCOUNTING',
        'cutoffs':[r['contract']['lmax'] for r in runs],
        'input_evidence':[{'contract':r['contract'],'evidence':r['evidence']} for r in runs],
        'transitions':pairs, 'empirical_successive_steps':empirical,
        'angle_space':'REAL_LOWELL_EB_COEFFICIENT_SPACE_NOT_SKY_OR_POLARIZATION_ANGLE',
        'arithmetic_status':'CHECKED', 'convergence_certified':False,
        'infinite_tail_bound':'NOT_ESTABLISHED', 'p_value':None,
        'claim':base.shared.CLAIM, 'paper_gate':'NOT_READY_TO_SUBMIT'}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--band-dirs',nargs='+',required=True,help='Two or three completed directories in increasing lmax order')
    ap.add_argument('--out',required=True)
    args = ap.parse_args(argv)
    try:
        result = analyze(args.band_dirs)
        result['code_sha256'] = base.shared.digest(__file__)
        result['dependency_sha256'] = {'cutoff':base.shared.digest(base.__file__),
                                     'reader':base.shared.digest(base.shared.__file__)}
        base.shared.write_new_json(args.out,result)
    except (ValueError,OSError,KeyError,TypeError,OverflowError,FloatingPointError,zipfile.BadZipFile) as exc:
        print(json.dumps({'status':'BLOCKED','error_type':type(exc).__name__,'error':str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps({'status':result['status'], 'cutoffs':result['cutoffs'],
        'full_transitions':[{'cutoffs':p['cutoffs'],'geometry':p['subjects']['full']} for p in result['transitions']],
        'full_empirical_steps':result['empirical_successive_steps'].get('subjects',{}).get('full'),
        'angle_space':result['angle_space'], 'convergence_certified':False,
        'infinite_tail_bound':result['infinite_tail_bound'], 'out':args.out,
        'paper_gate':result['paper_gate']},indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
