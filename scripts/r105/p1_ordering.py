"""Minimal common empirical-likelihood perturbation that ties two apparent CF4 tails."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from scripts.r103.p1_joint_patterns import ARRAY, ARRAY_SHA, SOURCE, SOURCE_SHA

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124/P1_ORDERING.json'


def tie_law(counts):
    """Minimize KL(Q||P) subject to E_Q D=0, D=-1,0,+1 and Q<<P."""
    counts = np.asarray(counts, dtype=float)
    if counts.shape != (3,) or not np.all(np.isfinite(counts)) or np.any(counts < 0) or counts.sum() <= 0:
        raise ValueError('three nonnegative finite masses with positive total are required')
    p = counts/counts.sum()
    minus, zero, plus = p
    common = math.sqrt(minus)*math.sqrt(plus)
    z = zero+2*common
    if z == 0:
        return {'feasible_tie':False, 'KL_nats_to_tie':None, 'tie_law_minus_zero_plus':None, 'strict_reversal_feasible':False}
    # Stable for almost identical p+ and p-; avoid rounding d=1 at a support boundary.
    d = (math.sqrt(plus)-math.sqrt(minus))**2
    cost = -math.log1p(-d) if d < 0.5 else -math.log(z)
    q = np.array([common,zero,common])/z
    return {'feasible_tie':True, 'KL_nats_to_tie':float(cost), 'tie_law_minus_zero_plus':q.tolist(),
            'strict_reversal_feasible':bool(plus>0 and minus>0 and plus!=minus)}


def analyze(root=ROOT):
    with (root/ARRAY).open('rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest()!=ARRAY_SHA:
            raise ValueError('P1 array changed')
    raw=(root/SOURCE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError('P1 reference summary changed')
    source=json.loads(raw)
    with np.load(root/ARRAY, allow_pickle=False) as archive:
        q=archive['q_app']
        if q.shape!=(2048,4) or not np.all(np.isfinite(q)) or np.unique(archive['sample_id']).size!=len(q):
            raise ValueError('P1 paired samples malformed')
        if not np.all(archive['weights']==1/len(q)) or np.isfinite(archive['physical_Q']).any():
            raise ValueError('P1 weighting or physical support changed')
        centers=archive['centers'].tolist()
        rows=[]
        for ref in source['strict_exceedance']:
            above=q>ref['threshold']
            if not np.array_equal(above.mean(axis=0),ref['per_window']):
                raise ValueError('P1 marginal replay mismatch')
            for i,j in itertools.combinations(range(4),2):
                score=above[:,i].astype(int)-above[:,j].astype(int)
                counts=np.bincount(score+1,minlength=3)
                rows.append({'threshold':ref['threshold'], 'windows_0based':[i,j],
                             'n_minus_zero_plus':counts.tolist(), 'tail_difference':float(score.mean()),
                             **tie_law(counts)})
    return {'schema':'htt.r105.p1_window_order/1', 'array_sha256':ARRAY_SHA, 'summary_sha256':SOURCE_SHA,
            'n_joint_draws':len(q), 'window_centers_from_archive':centers, 'rows':rows,
            'units':'natural-log relative entropy on the same normalized 2048-point support',
            'scope':'Source-conditioned apparent STF amplitude. Ties keep zero-mass events impossible. Strict reversal requires both discordant signs.',
            'physical_unknown_mass':1., 'physical_Pi':None}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=OUT)
    a=p.parse_args()
    a.output.write_text(json.dumps(analyze(),indent=2,allow_nan=False)+'\n')
