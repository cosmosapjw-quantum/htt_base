# 실제 SMICA/NILC low-ell morphology와 ideal local boost Q->O 수치 비교

beta=0.0012335735, nominal boost-generated STF octupole norm=0.066895582, relative to fitted O=0.112277%.
| processed map | change in octupole / nominal O (%) | same change / ideal Q->O beta response |
|---|---:|---:|
| SMICA_HM1 | 0.46388% | 4.1316 |
| SMICA_HM2 | 0.4161% | 3.706 |
| SMICA_OE1 | 0.60164% | 5.3586 |
| SMICA_OE2 | 0.56593% | 5.0405 |
| NILC_HM1 | 1.4999% | 13.359 |
| NILC_HM2 | 1.7336% | 15.44 |
| SMICA_FULL | 0% | 0 |
| SMICA_noSZ_FULL | 6.1346% | 54.638 |
| NILC_FULL | 1.5278% | 13.607 |

This is a contrast of the size of actual algorithm-dependent Q/O changes against a fixed purely algebraic full-sky response. It is NOT a noise covariance or physical boost contamination budget.
The observed map is already processed; frequency weights and higher harmonic transfer are not included in the algebraic denominator.
Neither numerical ratio nor morphology chirality change creates an anomaly p-value or a Bianchi shear observation.
