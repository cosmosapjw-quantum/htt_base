#!/usr/bin/env python3
"""Synthetic falsification checks for MQ1/MQ2; sampled distances are lower witnesses."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import platform
import numpy as np

TOL = 1e-10
ELL = np.sqrt(3 / 5)
K = 3 / np.sqrt(5)
A = np.sqrt(2) * K
SEED = 20260914


def stf3(t):
    s = sum(t.transpose(p) for p in itertools.permutations(range(3))) / 6
    tr = np.einsum('iik->k', s)
    e = np.eye(3)
    return s - (np.einsum('ij,k->ijk', e, tr) + np.einsum('ik,j->ijk', e, tr)
                + np.einsum('jk,i->ijk', e, tr)) / 5


STF = np.column_stack([stf3(e.reshape(3, 3, 3)).ravel() for e in np.eye(27)])


def normalize_q(raw):
    q = (raw + raw.T) / 2
    q -= np.eye(3) * np.trace(q) / 3
    norm = np.linalg.norm(q)
    if norm == 0:
        raise ValueError('Q=0: normalized q unavailable')
    return q / norm


def maps(q):
    raw_l = np.zeros((3, 27))
    for i in range(3):
        raw_l[i, 9*i:9*(i+1)] = q.ravel()
    l = raw_l @ STF
    # Explicit T5 Cartesian B_q, independent of a kernel basis.
    b = np.empty((27, 3))
    eye = np.eye(3)
    for j, w in enumerate(eye):
        qw = q @ w
        t = (np.einsum('i,jk->ijk', w, q) + np.einsum('j,ki->ijk', w, q)
             + np.einsum('k,ij->ijk', w, q)
             - 2/5*(np.einsum('ij,k->ijk', eye, qw) + np.einsum('ik,j->ijk', eye, qw)
                    + np.einsum('jk,i->ijk', eye, qw)))
        b[:, j] = t.ravel()
    m = np.eye(3) + 6/5 * q @ q
    r = b @ np.linalg.inv(m)
    p = STF - r @ l
    return l, r, p, m


def fibre(q, direction, eta_target):
    if not 0 <= eta_target <= 1:
        raise ValueError('eta>1: empty fibre excluded from finite Hausdorff comparison')
    l, r, p, m = maps(q)
    direction = np.asarray(direction, dtype=float)
    if np.linalg.norm(direction) == 0:
        raise ValueError('nonzero synthetic radial direction required')
    v = direction * np.sqrt(eta_target/(3*direction @ np.linalg.solve(m, direction)))
    c = r @ v
    # Radius uses the declared analytic synthetic eta target, not a clipped fitted eta.
    eta_residual = abs(float(c @ c) - eta_target)
    if eta_residual > TOL:
        raise AssertionError(('synthetic eta construction', eta_residual))
    return {'q': q, 'v': v, 'c': c, 'p': p, 'r': r, 'l': l,
            'rho': np.sqrt(1-eta_target), 'eta': eta_target, 'eta_residual': eta_residual}


def sample_points(f, rng, count=96):
    z = rng.normal(size=(count, 27)) @ f['p']
    norms = np.linalg.norm(z, axis=1)
    if np.any(norms == 0):
        raise AssertionError('zero sampled kernel vector')
    u = z / norms[:, None]
    return f['c'] + f['rho']*u, u


def distances_to_fibre(points, f):
    # Exact point-to-affine-sphere formula, evaluated in floating point.
    t = points-f['c']
    proj = t @ f['p']
    normal = t-proj
    return np.sqrt(np.sum(normal*normal, axis=1)+(np.linalg.norm(proj, axis=1)-f['rho'])**2)


def check_pair(f, g, rng):
    h = np.linalg.norm(f['q']-g['q'])
    b = np.linalg.norm(f['v']-g['v'])
    eps = h+b
    centre = np.linalg.norm(f['c']-g['c'])
    proj = np.linalg.norm(f['p']-g['p'], 2)
    rad = abs(f['rho']-g['rho'])
    d = np.sqrt(3)*b + A*h
    separated = d+np.sqrt(2*d)+np.sqrt(2)*min(1, K*h)
    global_bound = 2*A*eps+np.sqrt(2*A)*np.sqrt(eps)
    x, u = sample_points(f, rng)
    y, w = sample_points(g, rng)
    witness = max(distances_to_fibre(x, g).max(), distances_to_fibre(y, f).max())
    delta = 1-max(f['eta'], g['eta'])
    interior_bound = (A*(2+np.sqrt((1-delta)/delta))*eps if delta>0 else None)
    residual = max(np.max(abs(np.linalg.norm(x, axis=1)-1)), np.max(abs(x @ f['l'].T-f['v'])),
                   np.max(abs(np.linalg.norm(y, axis=1)-1)), np.max(abs(y @ g['l'].T-g['v'])))
    checks = {'centre': centre <= d+TOL, 'projection': proj <= min(1,K*h)+TOL,
              'radius': rad <= np.sqrt(2*d)+TOL, 'sampled_global': witness <= global_bound+TOL,
              'sampled_separated': witness <= separated+TOL,
              'sampled_interior': interior_bound is None or witness <= interior_bound+TOL,
              'unit_contraction': residual < TOL}
    checks = {name: bool(value) for name, value in checks.items()}
    if not all(checks.values()):
        raise AssertionError({'checks': checks, 'h':h, 'b':b, 'delta':delta})
    return {'h':float(h), 'b':float(b), 'epsilon':float(eps), 'eta':f['eta'], 'eta_prime':g['eta'],
            'centre_difference':float(centre), 'projection_difference':float(proj),
            'radius_difference':float(rad), 'sampled_hausdorff_lower_witness':float(witness),
            'analytic_global_upper':float(global_bound), 'analytic_separated_upper':float(separated),
            'analytic_interior_upper':None if interior_bound is None else float(interior_bound),
            'delta':float(delta), 'constraint_residual':float(residual), 'checks':checks}


def run():
    rng=np.random.default_rng(SEED)
    rows=[]
    etas=[0.,.5,.99,1-1e-8,1.]
    for j in range(360):
        q=normalize_q(rng.normal(size=(3,3)))
        scale=[1.,.1,.001,1e-6,1e-9][j%5]
        qp=normalize_q(q+scale*rng.normal(size=(3,3)))
        direction=rng.normal(size=3)
        f=fibre(q,direction,etas[j%5])
        g=fibre(qp,direction+scale*rng.normal(size=3),etas[(j//5)%5])
        rows.append(check_pair(f,g,rng))
    # Old radial example is reused as an oracle, never counted as a new discovery.
    sharp=[]
    q=np.diag([-1.,0.,1.])/np.sqrt(2)
    for t in [1e-2,1e-4,1e-6,1e-8]:
        f=fibre(q,[1.,2.,3.],1.)
        g=fibre(q,[1.,2.,3.],(1-t)**2)
        row=check_pair(f,g,rng)
        exact=np.sqrt(2*t)
        error=abs(row['sampled_hausdorff_lower_witness']-exact)
        if error>TOL: raise AssertionError(('prior sharpness identity',error))
        sharp.append({'t':t,'exact_prior_distance':float(exact),'error':float(error),
                      'distance_over_epsilon':float(exact/row['epsilon'])})
    negative={}
    for label,fn in [('Q_zero',lambda:normalize_q(np.zeros((3,3)))),
                     ('infeasible',lambda:fibre(q,[1,0,0],1.01))]:
        try: fn()
        except ValueError as e: negative[label]=str(e)
        else: raise AssertionError('missing undefined/empty guard')
    # One contraction-nullspace rotation with v=0 proves centres alone miss motion.
    f=fibre(q,[1,0,0],0.)
    g=fibre(normalize_q(np.diag([2.,-1.,-1.])),[1,0,0],0.)
    row=check_pair(f,g,rng)
    if row['sampled_hausdorff_lower_witness']<.1 or row['centre_difference']!=0:
        raise AssertionError('moving kernel negative control did not separate')
    return {'status':'SYNTHETIC_COMPONENT_AND_WITNESS_CHECKS_PASS','seed':SEED,'tolerance':TOL,
            'owner':'HTT/common observable-tensor research','claim_tier':'DIAGNOSTIC_ONLY',
            'transfer_source':'none','pair_count':len(rows),'sampled_directions_per_fibre':96,
            'constants':{'ell':float(ELL),'k':float(K),'A':float(A),'C1':float(2*A),'C2':float(np.sqrt(2*A))},
            'pairs':rows,'reused_prior_sharpness':sharp,'negative_controls':negative,
            'centre_only_countercontrol':row,
            'runtime':{'python':platform.python_version(),'numpy':np.__version__},
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'limits':['Samples supply lower witnesses only; upper bounds come from MQ1/MQ2 derivation.',
                      'Synthetic radii use declared analytic eta targets; computed centre norms verified at inherited tolerance.',
                      'No observed inference, confidence coverage, formal four-axis admission or alpha consumption.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    result=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    serialized = json.dumps(result,indent=2)+'\n'
    with args.output.open('x') as f: f.write(serialized)
    print(json.dumps({'status':result['status'],'pairs':result['pair_count'],'constants':result['constants']}))
