# A22-05 independent review

Fresh read-only `/root/a22_astrometry_review`, separate from theory-contract
writer and parent implementer. Requested gpt-6-astra/xhigh; observed UNKNOWN.
SCOPED_PASS for the declared Gaussian experiment, original physical K03/K05 HOLD.
Base d256ed4669b1ded62fa0db606929af108160ccf6; no full row/mock rerun.

Six focused tests passed independently in15.03s. Independent active-prior solves
for all32models in both cached cohorts reproduce component means <=1.06e-10,
weights<=1.47e-12, mixture means<=6.00e-12 and covariance<=1.14e-11. Mixture-interval
CDF residual<=1.23e-11; contrast mean/covariance exact. Input cache, join result,
config, two stats and producer template hashes match. Recomputed template scaling
is exact; angular marginal covariance5000I agrees<=4.55e-12 for both lmax choices.

PSD integration, proper priors, correlated contrasts, score covariance, compact
radial-cut bound and physical B1 sign pass. Report/PNG/PDF preserve omitted-l4 and
template-mean failures and unknown classifier/spatial-law caveats. One low-severity
representation finding (promised exact contrast intervals although only contrast
mean/covariance emitted) was corrected to distinguish the18individual coordinate
intervals. Reviewer targeted closeout CLOSED it and bound the final report after
its review-status wording update. No tolerance relaxation or original-node promotion.

Final reviewed hashes:

```json
{
  "model.py": "c132f01d9d35e267aa67e8465987bb8cfbab94f46e4f8adc32e9c793f5b74659",
  "test_model.py": "1cf06194c9916f023d4c58f95a1bc0bcb79e985b8f0ab9105f455909f3ac07a0",
  "CONFIG.json": "196774e641c0ee85b356762fcb6397c1592f0d701ccc99b587f5ce417c175fc2",
  "REPORT.md": "2f4e55f69ffbc20b0cd45521254279a920431ac10a1944e642ce82fb2b31d44e",
  "RESULT.json": "7af7bd6b3c68998181e281afe5c4e1ec2104ca0f37cb4a53588073ed3bf50ed7",
  "ASTROMETRY.png": "94213455afd5ea3249fcf72c15a36ec2761a8f206811725d6c4309daecff4b67",
  "ASTROMETRY.pdf": "310bb0638c219ff7b29df1ae0c9c76f3ebffb6399c9e7789a4b19b1f6b39daa9"
}
```
