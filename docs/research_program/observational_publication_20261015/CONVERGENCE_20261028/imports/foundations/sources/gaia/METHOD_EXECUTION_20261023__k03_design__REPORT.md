# R24-K03-DESIGN: retained Gaussian power sensitivity

This is a conditional design calculation from the retained profiled history covariance. No catalogue replay, new observational moment, or physical response estimate was made. The one-sided level is 0.05. The illustrative domain R||b|| <= epsilon is not a physical remainder certificate.

The maximum Mahalanobis separation is (K_H epsilon/R) sqrt(lambda_max(Cprime^{-1})). The simple-direction Gaussian Neyman-Pearson power is an oracle upper bound for each scenario. Every target multiplier scales *all* information at the scenario's covariance and holds the response law fixed; it is a requirement, not a demonstrated achievable observing program.

| epsilon | baseline upper power | baseline power excess (ppm) | baseline information multiplier for 50% | 80% | 90% |
|---:|---:|---:|---:|---:|---:|
| 0.01 | 0.050002493775 | 2.493775 | 4.6278e+09 | 1.05752e+10 | 1.46484e+10 |
| 0.1 | 0.050024942216 | 24.942216 | 4.6278e+07 | 1.05752e+08 | 1.46484e+08 |
| 0.3 | 0.050074856412 | 74.856412 | 5.142e+06 | 1.17502e+07 | 1.6276e+07 |

The original covariance eigenvalues (ascending, in (microarcsec/year)^2) are 0.663189609, 0.696790781, 0.878898866. Each row below adds a rank-one PSD covariance term along one of those *original* eigenvectors.

Eigenvector 1 controls the best allowed direction at baseline. Adding variance along it lowers the oracle power; by tau=0.3 its updated eigenvalue exceeds the second eigenvalue, so the optimum switches to eigenvector 2 and the bound plateaus. Adding variance along eigenvector 2 or 3 alone leaves the first eigenvector as the best direction, hence their identical bound in the figure. This is an optimized-direction upper bound; power for a fixed physical direction can change even when this maximum does not.

| eigenvector (ascending eigenvalue) | tau (microarcsec/year) | best information / baseline | power excess at epsilon=.3 (ppm) | 80% information multiplier at epsilon=.3 |
|---:|---:|---:|---:|---:|
| 1 | 0 | 1.000000000 | 74.856412 | 1.17502e+07 |
| 1 | 0.1 | 0.985145344 | 74.298018 | 1.19274e+07 |
| 1 | 0.3 | 0.951777243 | 73.028157 | 1.23456e+07 |
| 1 | 1 | 0.951777243 | 73.028157 | 1.23456e+07 |
| 2 | 0 | 1.000000000 | 74.856412 | 1.17502e+07 |
| 2 | 0.1 | 1.000000000 | 74.856412 | 1.17502e+07 |
| 2 | 0.3 | 1.000000000 | 74.856412 | 1.17502e+07 |
| 2 | 1 | 1.000000000 | 74.856412 | 1.17502e+07 |
| 3 | 0 | 1.000000000 | 74.856412 | 1.17502e+07 |
| 3 | 0.1 | 1.000000000 | 74.856412 | 1.17502e+07 |
| 3 | 0.3 | 1.000000000 | 74.856412 | 1.17502e+07 |
| 3 | 1 | 1.000000000 | 74.856412 | 1.17502e+07 |

The inverse of the retained Cbb agrees with the Schur complement of the six-parameter joint information: scaled residual 8.58e-16. Across all updates, direct inverse versus Sherman-Morrison scaled residual is at most 3.54e-16; maximum negative eigenvalue magnitude of I0-Iprime is 5.61e-16. The epsilon=.1, tau=0 T6 power differs from the retained result by 0.

## Acquisition needed to change the design

The retained Cbb and six-parameter F quantify this existing experiment. I checked the selected-row cache `/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_gaia_full_join.npz`: it has 755850 selected rows with reported Quaia z, sky directions, proper motions, per-source errors/correlation, and template fields. The frozen `/mnt/extdrive/workdir/htt_open_data/a22_20261023/astrometry/full_stats.npz` stores the 102-column G and score; `/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz` stores 6x6 A, 6x102 K, and the six-score for the already-run history/local fit. Those files permit a separately contracted finite reported-z design experiment, but they do not contain expanded depth/VSH moments.

For actual depth-layer or VSH performance, define the new channel response and windows at the specified epoch/units, then obtain its X^T W X, X^T W Z, Z^T W Z and cross-depth/channel blocks under a declared covariance and selection law. The stored per-source 2x2 errors supply only the old block-diagonal working weights; spatial/source correlations, cross-channel covariance, selected reported-to-true-depth law, nuisance profiling, and optical/radio centroid and matter response must be qualified for physical use. Their expanded Schur information is absent, so a specific new-design improvement factor is NOT_EVALUABLE. The table states the required information multiplier in the retained working model.

Original centroid/matter response and the neglected physical remainder remain HOLD. R23-Q's used ultra escalation is unchanged. This result does not promote original K03 acceptance or claim an empirical physical exclusion.

Figure: [PNG](POWER_SENSITIVITY.png) · [PDF](POWER_SENSITIVITY.pdf). Complete numeric rows and checks are in [RESULT.json](RESULT.json).
