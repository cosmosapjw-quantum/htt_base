"""Compare host replay with the actual read-only author's returned path values."""
import json
from pathlib import Path
import numpy as np

p = Path(__file__).resolve().parent
x = json.loads((p / 'RESULT.json').read_text())
expected = [
    [[-.01501419015095612, -.029817466152182212, -.045249790070685206,
      -.060613283001699665, -.07525857287437011],
     [.679500739544499, .6391615838709612, .5891438993335129,
      .5281499599949807, .4563184733309499], .0766476324374357],
    [[-.009201420087358848, -.028394895883366213, -.04850730778835011,
      -.06846183613697135, -.08711968371353189],
     [.7947398942251443, .708219610399351, .6166807774365899,
      .5465868218693715, .4308598392717916], .09685725202993926],
    [[-.008149705425950018, -.014675544763872686, -.021441118610857308,
      -.028392312463226228, -.03547024722905872],
     [.04692716703440256, .023206662679184347, .00042352849934177014,
      .10787024738623725, .3674834810052279], .01869418566800851],
]
diff = []
for row, (j, a, f) in zip(x['rows'], expected, strict=True):
    actual = [t['features']['J234'] for t in row['path']]
    actual_a = [t['features']['alignment23_squared'] for t in row['path']]
    np.testing.assert_allclose(actual, j, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(actual_a, a, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(row['removed_power_fraction'], f, rtol=1e-12, atol=1e-12)
    diff.extend(np.abs(np.asarray(actual)-j))
    diff.extend(np.abs(np.asarray(actual_a)-a))
    diff.append(abs(row['removed_power_fraction']-f))
    assert row['rank'] == 2
    assert max(row['validation'].values()) < 1e-12
    assert all(t['features']['axis_status'] == 'DEFINED' for t in row['path'])
result = {
    'status': 'PASS_ACTUAL_AUTHOR_TO_HOST_REPLAY',
    'comparisons': 33,
    'max_absolute_difference': float(max(diff)),
    'absolute_and_relative_tolerance': 1e-12,
    'algebra_controls_per_operator': 7,
    'algebra_max': max(max(r['validation'].values()) for r in x['rows']),
    'axis_points_defined': 15,
    'min_axis_gap': min(min(t['features']['largest_axis_gaps']) for r in x['rows'] for t in r['path']),
    'independent_scientific_review': 'PENDING_SEPARATE_REVIEWER',
    'empirical_null_coverage': 'NOT_ESTABLISHED',
}
print(json.dumps(result, indent=2))
