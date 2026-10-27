# R36-05 conditional radiation-stress comparison

This is an oracle synthetic experiment under the frozen
`IMPLEMENTATION_CONTRACT.json` (SHA-256
`01e5cbafcc2ba5fefe242d04f4b49dd8727411cdbb1e5397e22c1ec30458637d`).
Both adapters consume the same positive complete temperature sky and each
realization of the same correlated eight-coordinate temperature error. The
exact adapter integrates the fourth power of that sky; the linear adapter
uses its dipole and quadrupole to approximate the radiation tensor. Both then
use the same finite-boost (\mathscr D\) and Landau (\mathcal A_\gamma\)
definitions. The higher temperature modes and monopole are known noiseless
parts of this synthetic input, which limits transfer to a measured sky.

| Intrinsic (a) | Observer (\beta) | Exact (D) cover | Linear (D) cover | Exact (A\) cover | Linear (A\) cover | Exact/linear (D) diameter, (10^{-6}\) | Exact/linear mean nonempty (A) width, (10^{-6}\) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.00123 | 94.53% | 74.10% | 95.56% | 37.72% | 3.390 / 3.381 | 0.639 / 1.491 |
| 0 | 0.3 | 96.04% | 0% | 95.39% | 0% | 8.369 / 27.695 | 1.885 / 33.420 |
| (2\times10^{-5}\) | 0.00123 | 94.97% | 74.58% | 94.29% | 89.21% | 3.396 / 3.389 | 1.887 / 1.932 |
| (2\times10^{-5}\) | 0.3 | 95.68% | 0% | 95.02% | 0% | 8.454 / 27.748 | 5.066 / 33.723 |
| 0.02 | 0.00123 | 94.92% | 0% | 95.34% | 0% | 3.416 / 3.421 | 1.990 / 1.995 |
| 0.02 | 0.3 | 94.56% | 0% | 95.24% | 0% | 8.441 / 27.648 | 6.450 / 33.858 |

Each entry uses 4,096 independent test skies after 8,191 calibration skies
for that case, without tuning seeds or quantiles. The largest exact 95%
Clopper–Pearson halfwidth among the displayed physical coverage estimates is
0.0076; the largest over both methods is 0.0151. Continuous-error
calibration-content intervals are 0.94525–0.95468 for the (D) ball and
0.94538–0.95480 for the (A) equal-tail construction. Those intervals
describe finite calibration uncertainty; they do not cover possible error-law
misspecification. There were no tied calibration order statistics and no
invalid physical-domain or Landau samples. The exact (a=0) cases have
nonempty-(A) interval rates 97.83% and 97.09%, respectively; empty
intervals are counted as noncoverage and excluded from the labeled nonempty
width means. `RESULT.json` gives all exact counts, per-method covariances,
cross blocks, signed biases, paired width differences and MC intervals.
`sample_arrays.npz` retains every input draw, validity flag, normalized
\(\rho,T^{\mu\nu},f,P,\mathscr D,\mathcal A_\gamma\), hit and width needed to
recount the table.

The linear adapter's **method-target** coverage remains close to 95% in all
six cases. Its physical-target coverage deteriorates because the linear
temperature-to-moment conversion is biased relative to the exact finite-boost
radiation stress. In the (a=0,\beta=0.3) case, its noiseless (D) bias has
norm 0.06530 and its (A\) bias is 0.08161, compared with a (D) diameter
of (2.77\times10^{-5}). At low boost with (a=0.02), the linear widths
look similar, but physical-target coverage is zero. A width alone therefore
does not rank these methods. This result is conditional on the deliberately
authored Gaussian temperature law and the full synthetic sky; it is not an
empirical Planck interval.

The complete five-dimensional radiative response assembled from energy
moments of ranks 0, 2 and 4 agrees with an independent angular kernel. Using
the saved positive brightness and saved entropy-fit coefficients, the rank-2
projection differs by (0.006542435355818444\,\rho_0\) in operator norm;
rank 4 differs by (3.34\times10^{-16}\,\rho_0\) at the primary quadrature.
Its positive angular entropy residual is
(9.37160902728905\times10^{-5}\). Thus exact moment matching preserves
this response despite unresolved higher angular/spectral information. For
the retained (e^{8\mu^2}) family the sufficient entropy lower bound is
negative ((-0.352935\,\rho\)); the actual five-eigenvalue matrix has
(\lambda_{\min}/\rho=0.1282328197>0\). A failed sufficient bound does not
establish loss of coercivity.

The operator is an instantaneous radiation response. A matter-shear inverse
also needs the separate transport derivative residual (R), its frame and
errors. No such residual was supplied here. The conditional experiment does
not use polarization (E) as intensity, derive an independent photon-number
channel from one blackbody map, or establish native Bianchi morphology.
Calibrated intensity, spectral completion, mask/beam processing and a
measured joint error law are required before any observational interval.

The physical owner is HTT for the conditional statistical comparison;
`radiation_core.py` owns the source-bound static moments and response
calculation. Claim status is `PROPOSED_PENDING_INDEPENDENT_REVIEW`.
