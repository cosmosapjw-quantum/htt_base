#!/usr/bin/env python3
"""Execute the frozen six-case x three-order x three-tolerance R3 experiment."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT/'htt', ROOT/'htt/src', ROOT/'htt/htt'): sys.path.insert(0, str(p))
from bass.transfer.r8_restricted_history import (Initial, read_donors, integrate, residuals,
                                                stress, temperature, screen_basis, trace_distance)


def execute(out, archive):
    out.mkdir(parents=True, exist_ok=True)
    donors = read_donors(archive)
    normalization = donors['moments']([1, 1, 1], 0, donors['bose'])[0]
    donor_checks = []
    for a, b in ((1., 0.), (1.5, .01), (2., -.01)):
        m = stress(a, b, Initial(), 128)
        rho, pressure, pi = donors['moments'](m['scales'], 0, donors['bose'])
        expected = np.array([m['photons'], m['photon_perpendicular'], m['photon_parallel']])
        actual = .1/normalization*np.array([rho, pressure+pi[0, 0], pressure+pi[2, 2]])
        donor_checks.append(dict(a=a, b=b, max_absolute_error=float(np.max(abs(actual-expected)))))
    directions = [*np.eye(3), np.ones(3)/np.sqrt(3)]
    donor_screen_error = max(float(np.max(abs(screen_basis(n)-donors['screen_basis'](n)))) for n in directions)
    histories = {}; rows = []; rays = []
    for kappa in (0., .01, .1):
        for zeta in (0., .01):
            for order in (32, 64, 128):
                for tol in (1e-6, 1e-8, 1e-10):
                    key = (kappa, zeta, order, tol)
                    try:
                        h = integrate(Initial(kappa, zeta), order, tol); histories[key] = h
                        r = residuals(h)
                        rows.append(dict(kappa=kappa, zeta=zeta, order=order, tolerance=tol,
                                         end=h.end, final=h.solution.y[:, -1].tolist(), residuals=r))
                        for ni, n in enumerate(directions):
                            for beta in ((0., 0., 0.), (.001, 0., 0.)):
                                val = trace_distance(h, n, beta, tol)
                                rays.append(dict(kappa=kappa, zeta=zeta, order=order, tolerance=tol,
                                                 direction=ni, observer=beta, **val))
                    except Exception as exc:
                        rows.append(dict(kappa=kappa, zeta=zeta, order=order, tolerance=tol,
                                         error=type(exc).__name__+': '+str(exc)))
    for row in rows:
        if 'error' in row: row['numerical_status'] = 'FAIL'; continue
        ref = histories[(row['kappa'], row['zeta'], 128, 1e-10)].solution.y[:, -1]
        delta = np.abs(np.array(row['final'])-ref)
        row['state_convergence_ratio'] = float(np.max(delta/(1e-10+1e-7*np.abs(ref))))
        row['numerical_status'] = 'PASS' if row['state_convergence_ratio'] <= 1 and max(row['residuals'].values()) <= 1e-7+1e-10 else 'FAIL'
    lookup = {(r['kappa'], r['zeta'], r['direction'], tuple(r['observer'])): r for r in rays if r['order'] == 128 and r['tolerance'] == 1e-10}
    for r in rays:
        ref = lookup[(r['kappa'], r['zeta'], r['direction'], tuple(r['observer']))]
        ratios = [abs(r[k]-ref[k])/(1e-9+1e-6*abs(ref[k])) for k in ('angular_distance', 'redshift')]
        ratios += [r['reciprocity_residual']/(1e-9+1e-6*abs(r['reverse_angular_distance'])),
                   r['return_position_residual']/(1e-9+1e-6*r['angular_distance'])]
        ratios += [v/(1e-9+1e-6) for v in [*r['invariants'].values(), *r['reverse_invariants'].values()]]
        r['convergence_ratio'] = float(max(ratios)); r['numerical_status'] = 'PASS' if max(ratios) <= 1 else 'FAIL'
    mutations = []
    for scale in (0., 2.):
        h = integrate(Initial(.1, .01), pi_scale=scale)
        mutations.append(dict(kind='pi_scale', value=scale, detected=residuals(h)['einstein_spatial'] > 1e-5,
                              residuals=residuals(h)))
    mutant = integrate(Initial(.1, .01), rapidity_mutant=True)
    mutations.append(dict(kind='wrong_rapidity', detected=residuals(mutant)['killing_rapidity'] > 1e-5, residuals=residuals(mutant)))
    skies = []
    for kappa in (0., .01, .1):
        for zeta in (0., .01):
            h = histories[(kappa, zeta, 128, 1e-10)]; a, b = h.solution.y[:2, -1]
            mu, w = np.polynomial.legendre.leggauss(128)
            n = np.column_stack([np.sqrt(1-mu*mu), np.zeros_like(mu), mu])
            t = temperature(n, a, b); mono = np.dot(w, t)/2
            skies.append(dict(kappa=kappa, zeta=zeta, a=a, b=b,
                              monopole=mono, quadrupole_legendre=5*np.dot(w, t*(3*mu*mu-1)/2)/2,
                              octupole_legendre=7*np.dot(w, t*(5*mu**3-3*mu)/2)/2,
                              parity_error=float(np.max(abs(t-temperature(-n, a, b)))),
                              scope='THERMAL_SKY_WITHOUT_PRODUCT_BANDPASS_LAW'))
    sources = ['htt/bass/transfer/r8_restricted_history.py', 'scripts/observed_runs/run_r8_restricted_history.py',
               'docs/research_program/tensor_joint_r7/R3_MODEL_REFERENCE.md']
    result = dict(owner='BASS restricted benchmark', scope='NON_CLAIM_BEARING_R3_HISTORY', units='c=H_i=1; 8piG/(3c^2)=1',
                  source_archive=str(archive), donor_members=donors['members'], donor_license=donors['license'],
                  source_hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources},
                  donor_moment_checks=donor_checks, donor_screen_error=donor_screen_error,
                  histories=rows, rays=rays, sky=skies, mutations=mutations,
                  history_status='PASS' if len(rows)==54 and all(r['numerical_status']=='PASS' for r in rows) else 'FAIL',
                  distance_status='PASS' if len(rays)==432 and all(r['numerical_status']=='PASS' for r in rays) else 'FAIL',
                  sky_status='PASS' if all(r['parity_error']<1e-12 for r in skies) else 'FAIL',
                  jet_status='INPUT_UNAVAILABLE', scientific_admission='NOT_ADMITTED',
                  limitations=['Restricted LRS benchmark; no general native solver', 'Correlated host numerical verification; independent four-axis CAS not completed',
                               'Photon radial Planck integral normalized to initial energy; no detector bandpass or observed covariance law',
                               'Finite fixed grid and preconjugate endpoints only; no universal error certification'])
    (out/'results.json').write_text(json.dumps(result, indent=2, default=lambda x: x.item() if hasattr(x,'item') else str(x))+'\n')
    print(json.dumps({k:result[k] for k in ('history_status','distance_status','sky_status','jet_status')}), flush=True)
    return result

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True); p.add_argument('--archive',type=Path,required=True)
    args=p.parse_args(); execute(args.out,args.archive)
