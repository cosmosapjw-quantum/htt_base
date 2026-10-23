# R25 conditional distance evidence (exploratory)

On the retained 274 PGC rows and fixed complete-group folds (47, 55, 53, 69, 50), the arithmetic average of five conditional composite-null ratios is **E = 0.000183218358755319** (`log E = -8.604831899198585`). The numerator in each fold is the arithmetic mixture of eight normalized, saved-training-fit B/C conditional block densities. The denominator is the largest of four newly optimized A conditional null densities. The five folds share observations through their training sets, so their ratios are arithmetically averaged; they are never multiplied or maximized. A small observed ratio means this fixed mixture did not outperform the composite A null on these blocks. It does not establish that A is physically true or identify a Bianchi family.

| Held-out fold | Rows | log conditional E | E |
|---:|---:|---:|---:|
| 0 | 47 | -7.635043971606176 | 0.0004832173663932263 |
| 1 | 55 | -21.138171907543217 | 0.0000000006604023089865485 |
| 2 | 53 | -9.688013329877691 | 0.0000620225003503734 |
| 3 | 69 | -17.420856500646295 | 0.00000002717804114213675 |
| 4 | 50 | -7.899782762548909 | 0.0003708240885895445 |

The released R23 row order, J2000 directions, R24 coefficients, covariance scenarios, and R24 conditional OOF products are source sealed in `compute.py`. Forty reconstructed conditional means and block log densities agree with their saved R24 OOF records. Twenty new A null optimizations were finite and exceeded the corresponding saved training-fit A block log densities; the smallest margin was 4.193245576653762 log units. Independent QR and SVD residual calculations, direct Gaussian and analytic log densities, normalized normal equations, a correlated two-variable normalization fixture, a saturated zero-E fixture, and consistent row permutations passed. `RESULT.json` retains all 40 component means, 20 null fits, five ratios, controls, and the eight original B/C full coefficient, covariance, and angular tensor states. The figure displays the five log ratios.

This is a conditional model diagnostic on the data-selected, unqualified released cohort. The selection law, adaptive source/method choice, training-fit uncertainty, and an outward-rounded certificate for the computed null supremum are absent. Thus the mathematical conditional-E argument for fixed normalized alternatives under a covered null is not a certified e-valid claim for this actual data analysis. The low-z response includes PGC 9031 at 317 km/s. The angular STF is an optical effective selected-window tensor; it is not a physical Pi, Q, F, G_F, or a mapped u-to-G result. The 354 undefined distances, original 17/42 and alternate 18/42 counts, R9 UNKNOWN, old 48-ultra history, missing mass/physical anchor, and full tensor interpretation remain unchanged. A fold index supplies no joint depth support.

The first production attempt failed on a mechanical SciPy QR-control return shape and is preserved in `PRODUCTION.first_failure.txt` and `PRODUCTION.time`. A corrected production attempt and a separate permutation/control test passed under the cumulative limits. The Matplotlib Axes3D import warning did not affect this 2D figure.
