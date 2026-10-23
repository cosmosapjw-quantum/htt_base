import json, math
from pathlib import Path
from statistics import NormalDist
import numpy as np
p = Path('docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/SDSS_SOURCE_NULL_20261018')
out = p / 'SOURCE_ANALYSIS'
s = json.loads((out / 'SUMMARY.json').read_text())
selection = json.loads((p / 'SELECTED_MEMBERS.json').read_text())
bindings = json.loads((out / 'INPUT_BINDINGS.json').read_text())
assert s['source_bindings'] == bindings
assert len(selection['members']) == 64
assert [m['box'] for m in selection['members']] == list(range(64))
assert all(m['observer'] == 0 for m in selection['members'])
files = sorted(out.glob('MOCK_*_BOX_*_Y0.json'))
assert len(files) == 64
records = [json.loads(f.read_text()) for f in files]
for i, r in enumerate(records):
    assert r['member'] == selection['members'][i]
    assert 0 < r['rows_in_frozen_z_selection'] <= r['rows_in_source']
values = np.asarray([r['coefficients_mag'] for r in records], dtype=float)
covs = np.asarray([r['working_covariance_mag2'] for r in records], dtype=float)
assert values.shape == (64, 16) and covs.shape == (64, 16, 16)
assert np.isfinite(values).all() and np.isfinite(covs).all()
for key, actual in [('coefficients_mag', values), ('working_covariances_mag2', covs), ('weighted_scalar_mean_errors_mag', [r['weighted_scalar_mean_errors_mag'] for r in records]), ('profiled_intercepts_mag', [r['profiled_intercepts_mag'] for r in records])]:
    np.testing.assert_array_equal(np.asarray(s[key]), np.asarray(actual))
    assert np.isfinite(np.asarray(actual, dtype=float)).all()
diagonal = np.diagonal(covs, axis1=1, axis2=2)
assert (diagonal > 0).all()
eps = np.finfo(float).eps
psd_ratios = []
for c in covs:
    sym = (c + c.T) / 2
    ev = np.linalg.eigvalsh(sym)
    scale = max(float(np.max(np.abs(ev))), np.finfo(float).tiny)
    bound = 64 * eps * scale
    assert np.max(np.abs(c - c.T)) <= bound
    assert ev[0] >= -bound
    psd_ratios.append(float(ev[0] / scale))
means = values.sum(axis=0) / 64
centered = values - means
emp = centered.T @ centered / 63
scatter = np.sqrt(np.diag(emp))
mean_work = covs.sum(axis=0) / 64
corr_den = scatter[:, None] * scatter[None, :]
corr = np.divide(emp, corr_den, out=np.full_like(emp, np.nan), where=corr_den > 0)
t = np.max(np.abs(values) / np.sqrt(diagonal), axis=1)
threshold = NormalDist().inv_cdf(1 - .05 / 32)
expected = {'coefficient_means_mag': means, 'coefficient_scatter_mag': scatter, 'empirical_covariance_mag2': emp, 'mean_working_covariance_mag2': mean_work, 'empirical_to_mean_working_variance_ratio': np.diag(emp) / diagonal.mean(axis=0), 'T_descriptive': t, 'descriptive_threshold': threshold}
for key, v in expected.items():
    stored = np.asarray(s[key], dtype=float)
    assert np.isfinite(stored).all() and np.isfinite(v).all()
    np.testing.assert_allclose(stored, v, atol=1e-10, rtol=1e-8)
for key, v in [('empirical_correlation', corr), ('empirical_crosswindow_correlation', corr[:8, 8:])]:
    stored = np.asarray(s[key], dtype=float)
    np.testing.assert_array_equal(np.isnan(stored), np.isnan(v))
    np.testing.assert_allclose(stored, v, atol=1e-10, rtol=1e-8, equal_nan=True)
k = int(np.count_nonzero(t > threshold))
assert s['N_boxes'] == 64 and s['K_exceeding_descriptive_threshold'] == k
assert s['K_over_64_descriptive'] == k / 64
assert s['bias_centering'] == 'NONE'
assert s['coverage_claim'] == 'NOT_CALIBRATED_PHYSICAL_OR_H02'
assert s['metadata']['claim_tier'] == 'C0' and s['metadata']['scientific_admission'] == 'HOLD'
assert s['metadata']['covariance_status'] == 'DIAGONAL_WORKING_PLUS_FINITE_SOURCE_EMPIRICAL'
assert s['metadata']['null_status'] == 'SDSS_SOURCE_ONLY_SEPARATE_BOX_INDEPENDENCE_NOT_CERTIFIED'
print(json.dumps({'status':'PASS_CACHED_OUTPUT_INTERNAL_CONSISTENCY_ONLY','records':64,'K':k,'threshold_independent':threshold,'minimum_working_covariance_eigenvalue_over_spectral_scale':min(psd_ratios),'PSD_negative_roundoff_limit_in_scale_units':-64*eps,'source_refits':0,'scientific_admission':'HOLD'}, sort_keys=True))
