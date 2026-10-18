import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('legacy_intake', Path(__file__).with_name('legacy_intake.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_real_official_unit_pair():
    a, b = [m.read_map(m.RAW/'test'/name, blob)[0] for name, blob in m.FILES.items()]
    r = m.unit_comparison(a, b)
    assert abs(r['least_squares_scale']/2725-1) < 2e-6
    assert r['relative_residual_declared_2725'] < 2e-6


def test_source_tamper_rejected():
    with pytest.raises(ValueError, match='GIT_BLOB'):
        m.read_map(m.RAW/'test'/'sky_bianchi_test.fits', '0'*40)


def test_no_zero_second_map():
    with pytest.raises(ValueError): m.unit_comparison(np.ones(3), np.zeros(3))


def test_derived_nonclaim_contract():
    import json
    r = json.loads(Path(__file__).with_name('RESULT.json').read_text())
    assert r['polarization'] == 'NOT_SUPPLIED_NOT_ZERO'
    assert r['B02_original_acceptance'] == 'HOLD'
    assert not r['physical_atlas_eligibility'] and not r['native_solver']
    assert r['fit']['rank'] == 169
    assert r['parameter_binding'] == 'UPSTREAM_DECLARED_PARAM_PAR_TEST_MAP_BINDING'
    assert r['parameter_binding_execution_verification'].startswith('NOT_RUN')
