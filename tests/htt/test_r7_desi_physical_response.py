"""Bounded flat-LCDM response checks for the released scalar BAO summary."""
import json
from pathlib import Path

import numpy as np
import pytest

from htt.infer.r7_desi_law import (build_compressed_bao_law,
    build_flat_lcdm_bao_law, flat_lcdm_qiso)


SOURCE=Path(__file__).resolve().parents[2]/'docs/observational_analysis_20261014/results/desi/analysis.json'


def payload():
    return json.loads(SOURCE.read_text())['source']


def test_physical_prediction_is_one_released_qiso_density():
    p=payload()
    physical=build_flat_lcdm_bao_law(p)
    scalar=build_compressed_bao_law(p)
    theta=(.3,10000.)
    q=flat_lcdm_qiso(*theta,zeff=p['zeff'],dv_over_rd_fid=p['DV_over_rd_fid'])
    assert physical.loglik(theta)==pytest.approx(scalar.loglik((q,)),abs=1e-13)
    assert physical.conditioning_target==scalar.conditioning_target
    np.testing.assert_array_equal(physical.covariance,scalar.covariance)
    assert physical.jacobian_theta is None  # Identity derivative in qiso is not physical.


def test_identified_product_ridge_and_distance_limit():
    p=payload(); y=p['observed'][0]
    law=build_flat_lcdm_bao_law(p)
    peaks=[]
    for omega in (.2,.3,.4):
        scale=flat_lcdm_qiso(omega,1.,zeff=p['zeff'],dv_over_rd_fid=p['DV_over_rd_fid'])
        best=scale/y
        assert flat_lcdm_qiso(omega,best,zeff=p['zeff'],dv_over_rd_fid=p['DV_over_rd_fid'])==pytest.approx(y)
        peaks.append(law.loglik((omega,best)))
    np.testing.assert_allclose(peaks,peaks[0],rtol=0,atol=1e-12)
    for omega in (.2,.4):
        z=1e-5
        q=flat_lcdm_qiso(omega,10000.,zeff=z,dv_over_rd_fid=1.)
        assert q/(299792.458*z/10000.)==pytest.approx(1.,rel=1e-5)


@pytest.mark.parametrize('theta',[(0.,10000.),(1.,10000.),(.3,0.),(.3,float('nan'))])
def test_invalid_physical_domain_refused(theta):
    p=payload()
    with pytest.raises(ValueError):
        flat_lcdm_qiso(*theta,zeff=p['zeff'],dv_over_rd_fid=p['DV_over_rd_fid'])
    assert build_flat_lcdm_bao_law(p).loglik(theta)==-np.inf
