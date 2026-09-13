from dataclasses import replace
from fractions import Fraction as F
import numpy as np
import pytest
from common.r7_contracts import ScopeKey, UnavailableLaw
from common.r9_product import SharedStateEmbedding
from htt.infer.r7_gaussian_law import JointObservationLaw
from htt.infer.r7_confidence import PhysicalDomain, GaussianAcceptanceRule, invert_acceptance, BoundCertificate
from htt.infer.r9_confidence_image import JointCoverageEvent, StateFunctional, physical_confidence_image


def event_fixture():
    names = ('state', 'jet', 'anchor')
    embedding = SharedStateEmbedding('test-state', names, ('1',)*3, ('PHYSICAL', 'JET', 'ANCHOR'),
        'frame', 'epoch', names, ('1',)*3, (), (), np.eye(3), np.empty((0, 3)))
    law = JointObservationLaw(ScopeKey('event', 'law', 'model', ('test',), method_config_id='alpha1/80'),
        np.ones(3), names, names, ('1',)*3, lambda x, e: np.asarray(x), np.eye(3),
        {'source_ids':['test'], 'selection_law':'fixed', 'covariance_source':'known', 'mean_definition':'joint state'},
        'test-domain', lambda x, e: True)
    domain = PhysicalDomain('test-domain', names, lambda x, e: True,
                            witnesses=((1, 1, 1), (1, 1, 0)))
    region = invert_acceptance(law, domain, GaussianAcceptanceRule(1/80))
    event = JointCoverageEvent(region, embedding, 'test-joint-inversion', names, 'TRUE_POINT',
                              'fixed Gaussian joint inversion', 'test fixture law', (('DESI', F(1, 80)),))
    return region, event


def test_common_jet_anchor_coverage_is_required_and_not_stacked_marginals():
    region, event = event_fixture()
    target = StateFunctional('ratio', lambda x: float(x[0]*x[1])/float(x[2]), ('state', 'jet', 'anchor'))
    assert isinstance(physical_confidence_image(region, target), UnavailableLaw)
    with pytest.raises(ValueError, match='ordered'):
        replace(event, covered_variables=('state', 'jet'))
    with pytest.raises(ValueError, match='region'):
        physical_confidence_image(replace(region), target, event=event)
    with pytest.raises(ValueError, match='coverage'):
        replace(event, region=replace(region, coverage_lower=.95*.95))
    with pytest.raises(ValueError, match='redistribution'):
        replace(event, prospective_error_allocation=(('DESI', F(1, 20)),))
    assert isinstance(physical_confidence_image(region, target, event=replace(event, coverage_target='FULL_IDENTIFIED_SET')), UnavailableLaw)
    assert isinstance(physical_confidence_image(region, replace(target, fixed_parameters=('anchor',)), event=event), UnavailableLaw)


def test_same_tuple_ratio_keeps_zero_branch_and_does_not_invent_outer_bound():
    region, event = event_fixture()
    target = StateFunctional('ratio', lambda x: float(x[1])/float(x[2]), ('jet', 'anchor'))
    result = physical_confidence_image(region, target, event=event)
    assert result['projection'].status == 'OUTER_RANGE_UNRESOLVED'
    assert result['coverage_lower'] is None
    assert result['projection'].undefined_witnesses == ((1, 1, 0),)
    # An explicitly supplied outer bound is scoped to the same joint event.
    def bound(r, f):
        return BoundCertificate((-np.inf, np.inf), 'UNBOUNDED_OUTER_IMAGE', 0.,
                                'full real relaxation retains nonzero-anchor ratios', r.scope_ids, f.functional_id, r.domain.domain_id)
    result = physical_confidence_image(region, target, event=event, bound_provider=bound)
    assert result['coverage_lower'] is None
    assert result['event_coverage_lower'] == 1-1/80
    assert result['projection'].undefined_witnesses == ((1, 1, 0),)
