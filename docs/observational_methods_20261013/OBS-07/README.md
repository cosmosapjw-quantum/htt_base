# OBS07-SENSITIVITY-v1

This is a dimensionless manufactured sensitivity calculation. It reports a fixed GLS statistic, conditional Gaussian standard error, and worst-case coefficient shifts under separately assumed box and ellipsoid radii. The radii are not measured physical K, M2, or L inputs, and they are not certified upper bounds.

`OBS07_PHYSICAL_BRIDGE_HOLD` remains active. The result supplies no coverage, cosmological, or physical remainder claim. Box and ellipsoid supports remain separate; no Minkowski sum support is reported.

The manufactured calculation gives `theta_hat=0.2`, conditional `SE=1/sqrt(3)`, box support `4*rho/3`, and ellipsoid support `2*sqrt(2)*rho/3`. The focused tests verify all eight box corners and the analytic ellipsoid extremizer. `execution.json` records the test and artifact receipts; independent review remains pending.

Run:

```bash
PYTHONPATH=htt python -m pytest --confcutdir=tests/htt tests/htt/test_obs07_remainder_sensitivity.py -q
python scripts/obs07_remainder_sensitivity.py --output docs/observational_methods_20261013/OBS-07
```
