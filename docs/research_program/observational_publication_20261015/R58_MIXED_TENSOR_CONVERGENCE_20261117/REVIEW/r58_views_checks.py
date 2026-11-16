"""Independent oracle for the fixed R58 five-view output; no production writes."""
from pathlib import Path
import hashlib
import json

import numpy as np
from scipy import stats

BASE = Path(__file__).resolve().parent
OUT = BASE / 'data_review_output'
files = [OUT / 'FIVE_VIEW_RESULT.json', OUT / 'OWNED_TENSOR_RESULT.json',
         OUT / 'OWNED_TENSOR_CARRIERS.npz',
         BASE / 'r58_patch/scripts/r58/build_r58_views.py',
         BASE / 'r58_patch/tests/r58/test_five_views.py',
         BASE / 'r58_patch/tests/r58/test_r54_repairs.py']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {str(p.relative_to(BASE)): sha(p) for p in files}
result = json.loads(files[0].read_text())
meta = json.loads(files[1].read_text())
assert result['source_result_sha256'] == sha(files[1])
assert result['source_carrier_sha256'] == meta['carrier_sha256'] == sha(files[2])
data = np.load(files[2], allow_pickle=False)
t = np.zeros((32, 32))
for w in range(4):
    for j in range(8):
        old = 3*w+j if j < 3 else 12+5*w+j-3
        t[8*w+j, old] = 1
        if w:
            initial = j if j < 3 else 12+j-3
            t[8*w+j, initial] = -1
assert abs(np.linalg.det(t)) == 1
c2 = stats.chi2.ppf(.95, 11)
rows = {}
max_errors = {'estimate': 0., 'covariance': 0., 'Q': 0., 'Pi': 0.,
              'support_interval': 0., 'direction_interval': 0., 'path': 0.,
              'path_covariance': 0., 'beta_interval': 0.}

def compare(key, observed, expected, atol=1e-9):
    observed, expected = np.asarray(observed), np.asarray(expected)
    max_errors[key] = max(max_errors[key], float(np.max(np.abs(observed-expected))))
    np.testing.assert_allclose(observed, expected, rtol=2e-10, atol=atol)

for name, model in result['models'].items():
    y, cov, x = (data[f'{name}__{suffix}'] for suffix in ('y32', 'cov32', 'response32x11'))
    j = x.T @ np.linalg.solve(cov, x)
    vc = np.linalg.inv(j)
    mean = np.linalg.solve(j, x.T @ np.linalg.solve(cov, y))
    rows[name] = (mean, vc)
    compare('estimate', model['x']['estimate'], mean)
    compare('covariance', model['x']['covariance'], vc)
    wald = mean @ j @ mean
    compare('Q', model['Q']['value_at_fit'], np.sqrt(wald/c2))
    compare('Pi', model['Pi']['p'], stats.chi2.sf(wald, 11))
    assert model['Pi']['not_independent_of_Q'] is True
    assert model['F']['occupancy']['status'] == 'UNAVAILABLE'
    assert model['Q']['physical_ceiling'] == 'UNAVAILABLE'
    for i, label in enumerate(meta['parameter_names']):
        half = np.sqrt(c2*vc[i, i])
        entry = model['F']['support'][label]
        compare('support_interval', [entry['lower'], entry['upper']], [mean[i]-half, mean[i]+half])
    compare('path', model['G_F']['path'], t @ y)
    compare('path_covariance', model['G_F']['covariance'], t @ cov @ t.T)
    physical = model['x']['physical_pullback']
    assert physical['rank'] == 11 and physical['dimension'] == 22
    for i, label in enumerate(physical['parameter_names']):
        entry = physical['intervals_95_simultaneous'][label]
        if 11 <= i < 14:
            index = i-11
            half = np.sqrt(c2*vc[index, index])
            compare('beta_interval', [entry['lower'], entry['upper']],
                    [(mean[index]-half)/299792.458, (mean[index]+half)/299792.458])
            assert entry['identified']
        else:
            assert not entry['identified']
            assert entry['lower'] == '-infinity' and entry['upper'] == '+infinity'
directions = {}
for name, entry in result['directional_observable']['directions'].items():
    nx, ny, nz = entry['n_ICRS']
    v = np.array([0, 0, 0, nx, ny, nz, (nx*nx-ny*ny)/np.sqrt(2),
                  (nx*nx+ny*ny-2*nz*nz)/np.sqrt(6), np.sqrt(2)*nx*ny,
                  np.sqrt(2)*nx*nz, np.sqrt(2)*ny*nz])
    np.testing.assert_allclose(entry['contrast_11'], v, atol=1e-15)
    lows, highs = [], []
    for mean, vc in rows.values():
        middle, half = v @ mean, np.sqrt(c2*(v @ vc @ v))
        lows.append(middle-half)
        highs.append(middle+half)
    expected = [min(lows), max(highs)]
    interval = entry['simultaneous_95_union_interval_hull']
    compare('direction_interval', [interval['lower'], interval['upper']], expected)
    assert interval['model_count'] == 7 and interval['simultaneous']
    directions[name] = expected
after = {str(p.relative_to(BASE)): sha(p) for p in files}
assert before == after
out = {'schema': 'htt.r58.views_independent_checks/1', 'checks': 'PASS',
       'model_count': len(rows), 'files_sha256': before,
       'maximum_absolute_errors': max_errors,
       'directional_logH_95_simultaneous_union_interval_hulls': directions,
       'inputs_unchanged': before == after,
       'scope': 'independent normal-equation GLS from frozen 32D carrier; no raw source or cosmic covariance revalidation'}
(BASE / 'r58_views_checks.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps(out, indent=2))
