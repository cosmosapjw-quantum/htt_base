# A22-04 independent read-only review

Reviewer native task `/root/a22_optics_review`, separate from author and theory
contract task. Requested gpt-6-astra/xhigh, observed UNKNOWN. Base d256ed4669b1ded62fa0db606929af108160ccf6.

Scoped PASS: finite spectral/refit experiment and conditional radial component.
Independent four tests passed. Twelve independently replayed fits match stored
parameters exactly; smallest Jacobian singular ratio .00273565. Paired residual
identity error <=6.18e-15mag; omitted time/wavelength negative controls >=.00920
relative error. Donor aberration reproduces eta7.76085186e-7. SNANA source identity,
Carr correction convention, plot and claim limits checked. No numerical blocker.

Two nonblocking report clarifications (intake versus generation base; dimensionless
q and initial-reference perpendicular chart) were corrected. Reviewer targeted
closeout confirmed both CLOSED and all numerical identities unchanged. No rerun
was required for these documentation changes. Empirical SALT2/BBC/PV closure and
original V04/H04 acceptance remain HOLD/UNKNOWN. No four-axis CAS claim.

Final reviewed SHA-256:

```json
{
  "spectral.py": "e755f47e64d3ffe68aa6fec49399b0b33557de391e54f08d02cc1484788534f2",
  "test_spectral.py": "9eb76576c024a96c55929ca059ff369ef62dd2c96c71b25c91cd3a7a2d2623ca",
  "RESULT.json": "1ed5b4065ac67fed03cdd8557421b41a2b8369aed02903815d2967b26090c330",
  "SPECTRAL.png": "ca2b299f243a65a82891c13268019c0daa2403813f238d70dfe83b459ab401a0",
  "SPECTRAL.pdf": "25febe9a92abe05971d9042b8e516255c7d17ab65f6639400e9169e4795dd13f",
  "REPORT.md": "3f0ef47af1d579f92090077b54e8c1f64b171325cbd1aa1f851f3dfed62c8bc6"
}
```
