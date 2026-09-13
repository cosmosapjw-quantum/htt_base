#!/usr/bin/env python3
"""Execute one retained release-conditional product through R9 common APIs.

This is scalar background qiso, not observed tomography or physical shear.
Gaussian mock draws validate this conditional pipeline only, not catalogue law.
"""
from pathlib import Path
import argparse
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
import platform
import sys
import numpy as np
import scipy
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT/'htt/src', ROOT/'htt', ROOT/'htt/htt'):
    sys.path.insert(0, str(path))
from obsstat.r9_product_intake import read_desi_qiso
from common.depth_path import DepthRepresentation
from common.r9_product import ProductIntake, SharedStateEmbedding
from common.r7_contracts import content_id, json_value
from htt.infer.r7_desi_law import build_compressed_bao_law
from htt.infer.r7_confidence import PhysicalDomain, GaussianAcceptanceRule, invert_acceptance
from htt.infer.r9_depth_law import embed_product, depth_law, depth_diagnostic
from htt.infer.r9_confidence_image import physical_confidence_image

SEED, DRAWS, ATOL, MC_TOL = 20260912, 100000, 1e-10, .005
ALPHA = Fraction(1, 80)


def run_product(path):
    payload = read_desi_qiso(path)
    original = build_compressed_bao_law(payload)
    original = replace(original, scope=replace(original.scope,
        method_config_id=content_id({'alpha': str(ALPHA), 'selection': 'retained syst alternative only'})))
    intake = ProductIntake(original.scope.experiment_id, 'DESI_DR1_FULLSHAPE_BGS_v1.2',
        tuple(original.specification['source_ids']), original.measurement_ids, ('1',),
        'NONANGULAR_BACKGROUND_COMPRESSION', f"zeff={payload['zeff']}", 'released qiso scalar',
        original.specification['selection_law'], 'released GCcomb sample', 'released fiducial DV/rd',
        'NOT_APPLICABLE_NONANGULAR_SUMMARY', original.specification['covariance_source'],
        original.measurement_ids, 'RELEASE_CONDITIONAL_GAUSSIAN')
    embedding = SharedStateEmbedding('R9_DESI_QISO_BACKGROUND', ('qiso',), ('1',), ('OBSERVABLE',),
        intake.frame, intake.epoch, ('qiso',), ('1',), (), (), [[1]], np.empty((0, 1)))
    embedded = embed_product(original, intake, embedding)
    representation = DepthRepresentation((1,), (), original.measurement_ids, 'R9_QISO_ONE_BLOCK_NO_TOMOGRAPHY')
    law = depth_law(embedded, intake, representation)
    domain = PhysicalDomain('R9_POSITIVE_QISO', ('qiso',), lambda x, e: x[0] > 0,
                            ((0., np.inf),), assumptions=(law.conditioning_target,))
    rule = GaussianAcceptanceRule(float(ALPHA))
    region = invert_acceptance(law, domain, rule)
    center = float(law.observed[0]); sigma = float(np.sqrt(law.covariance[0, 0]))
    critical = float(norm.ppf(1-float(ALPHA)/2))
    interval = [max(0., center-critical*sigma), center+critical*sigma]
    assert region.contains([center])
    for q in (center, .5, 1., 1.5):
        assert abs(law.loglik([q])-original.loglik([q])) < ATOL
    # Same fixed transform, mean, known released C and candidatewise rule in
    # each pseudo-observation; no fitted K/C/selection step exists in this law.
    rng = np.random.default_rng(SEED)
    samples = 1.+sigma*rng.standard_normal(DRAWS)
    transformed = (representation.T @ samples[None, :]).T
    quadratic = ((transformed[:, 0]-1.)/sigma)**2
    inside = quadratic <= critical**2
    # Compare vectorized results with the actual acceptance API and independent
    # scalar normal inverse-CDF oracle. Probe tails as well as first draws.
    indices = np.unique(np.r_[np.arange(64), np.argsort(quadratic)[-64:]])
    for i in indices:
        actual = rule(transformed[i]-law.mean([1.], None), law.covariance)
        assert actual.accepted == bool(inside[i])
        assert abs(actual.quadratic-quadratic[i]) < ATOL
    rejection_rate = float(1-inside.mean())
    assert abs(rejection_rate-float(ALPHA)) <= MC_TOL
    physical = physical_confidence_image(region, None)
    return {'owner': 'HTT', 'scope': 'ONE_RETAINED_RELEASE_CONDITIONAL_QISO_ANALYSIS',
        'claim_tier': 'CONDITIONAL_DIAGNOSTIC', 'transfer_source': 'OBSERVATION_SPACE',
        'sky_support_status': 'NONANGULAR_SUMMARY', 'null_mock_status': 'FIXED_RELEASE_GAUSSIAN_MODEL_ONLY',
        'payload': payload, 'intake': intake, 'embedding': embedding, 'H': representation.H, 'T': representation.T,
        'observed': law.observed, 'covariance': law.covariance, 'mean_at_qiso_1': law.mean([1.], None),
        'jacobian': law.jacobian_theta([1.], None), 'law_specification': law.specification,
        'alpha': str(ALPHA), 'family_alpha': '1/20', 'no_redistribution': True,
        'qiso_interval': interval, 'confidence_lower': region.coverage_lower,
        'DV_over_rd_interval': [q*payload['DV_over_rd_fid'] for q in interval],
        'depth_diagnostic': depth_diagnostic(embedded, intake, representation, [1.]),
        'physical_image': physical, 'product_multi_depth_law': 'UNAVAILABLE',
        'mocks': {'seed': SEED, 'draws': DRAWS, 'rejections': int((~inside).sum()),
                  'rejection_rate': rejection_rate, 'nominal_alpha': str(ALPHA), 'mc_tolerance': MC_TOL,
                  'actual_api_crosschecks': len(indices), 'status': 'PASS_CONDITIONAL_PIPELINE'},
        'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
        'holds': ['R8 STOP_INVALID', '25 unresolved R8 pools', 'CF4 quarantine', 'PR4 skip',
                  'production admission HOLD', 'empirical admission HOLD', 'novelty HOLD', 'four-axis CAS HOLD'],
        'caveats': ['Previously explored release; no new holdout or raw-survey coverage claim.',
                    'One scalar block has no depth contrast or angular morphology.',
                    'No native transfer, global tilt, physical shear/vorticity or family identification.',
                    'No multiplication of transformed view, same sky, stat alternative or depth score.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve prior evidence and select an unused output path')
    result = run_product(args.input)
    sources = [Path(__file__), ROOT/'htt/obsstat/r9_product_intake.py', ROOT/'htt/src/common/depth_path.py',
               ROOT/'htt/src/common/r9_product.py', ROOT/'htt/htt/htt/infer/r9_depth_law.py',
               ROOT/'htt/htt/htt/infer/r9_confidence_image.py', ROOT/'htt/htt/htt/infer/r7_desi_law.py',
               ROOT/'htt/htt/htt/infer/r7_gaussian_law.py', ROOT/'htt/htt/htt/infer/r7_confidence.py']
    result['source_hashes'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(json_value(result), indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': 'PASS_CONDITIONAL_PRODUCT_PATH', 'output': str(args.output),
                      'qiso_interval': result['qiso_interval'], 'depth': 'NO_DEPTH_CONTRASTS'}))


if __name__ == '__main__':
    main()
