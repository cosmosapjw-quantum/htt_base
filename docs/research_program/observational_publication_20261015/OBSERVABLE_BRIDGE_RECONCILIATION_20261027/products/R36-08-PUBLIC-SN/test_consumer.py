#!/usr/bin/env python3
"""Independent finite GLS and chart falsifiers for the R36-08 consumer."""
import importlib.util
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag

spec = importlib.util.spec_from_file_location('r36_sn',Path(__file__).with_name('consumer.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

rng = np.random.default_rng(3608)
n = 64
ra = rng.uniform(0,360,n)
dec = np.rad2deg(np.arcsin(rng.uniform(-1,1,n)))
high = np.arange(n)>=n//2
_, N, A = mod.design(ra,dec,high)
B = rng.normal(size=(n,n))
C = B@B.T/n + np.eye(n)*.4 + .04*np.ones((n,n))
y = N@np.array([24.1,.02]) + A@rng.normal(0,.02,16) + rng.multivariate_normal(np.zeros(n),C)

fit = mod.fit(y,C,N,A)
assert fit['status']=='FULL_RANK'
L = np.linalg.cholesky(C)
X = np.column_stack((N,A))
Xw = np.linalg.solve(L,X)
yw = np.linalg.solve(L,y)
q,r = np.linalg.qr(Xw)
b = np.linalg.solve(r,q.T@yw)
K = np.linalg.solve(r,np.eye(18))
cov = K@K.T
np.testing.assert_allclose(fit['coefficients_mag'],b[2:],rtol=1e-9,atol=1e-10)
np.testing.assert_allclose(fit['covariance_mag2'],cov[2:,2:],rtol=1e-9,atol=1e-10)
np.testing.assert_allclose(fit['T_full'],np.linalg.norm(yw-Xw@b)**2,rtol=1e-9,atol=1e-10)

perm = rng.permutation(16)
scale = rng.uniform(.5,2,16)
variant = mod.fit(y,C,N,A[:,perm]*scale)
np.testing.assert_allclose(np.array(variant['coefficients_mag'])*scale,
                           np.array(fit['coefficients_mag'])[perm],rtol=1e-10,atol=1e-10)
np.testing.assert_allclose(variant['delta_T'],fit['delta_T'],rtol=1e-10,atol=1e-10)

# The selected marginal block is invariant when an excluded source entry changes;
# the full-source asymmetry diagnostic still detects that excluded change.
selected = np.arange(2,n)
source_changed = C.copy()
source_changed[0,1] += .01
assert np.array_equal(source_changed[np.ix_(selected,selected)],
                      C[np.ix_(selected,selected)])
assert np.max(np.abs(source_changed-source_changed.T))>.01/2
mod.validate_selected_covariance(source_changed[np.ix_(selected,selected)])

# A one-sided consumed entry must fail the original selected symmetry tolerance.
bad = C.copy()
bad[3,4] += .01
try:
    mod.validate_selected_covariance(bad)
    raise AssertionError('selected asymmetry was accepted')
except AssertionError as e:
    assert str(e)=='selected covariance symmetry'

# A symmetric but indefinite selected block fails without jitter or adjustment.
bad = C.copy()
bad[3,3] = -1
try:
    mod.validate_selected_covariance(bad)
    raise AssertionError('selected non-PD covariance was accepted')
except AssertionError as e:
    assert str(e)=='selected covariance positive definite'

z = rng.uniform(.01,.15,n)
mu,_ = mod.reference(z,z,64)
chart = 10*np.log10(1+z)
observed = y+mu
np.testing.assert_allclose((observed-chart)-(mu-chart),y,atol=1e-13)
assert np.max(np.abs((observed-chart)-mu-y))>1e-3
print('PASS independent QR GLS, covariance, permutation/unit invariance, chart, excluded-asymmetry invariance, selected-asymmetry rejection, non-PD rejection')
