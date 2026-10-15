# S4: Conditional Schur identifiability and CF4 method deletion

2026-10-16 KST. This is a **review-only staged research result**, not a physical claim. Source: original uncommitted 2026-10-15 Loop6 selected CF4 groups, same baseline `13d8d85fa470d645d008986e8f77d8d0f70fdf54`. The original 35,970 source identities were recovered from read-only Dropbox-synced data with sha256 of the selected NPZ `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c` and exact original result JSON `9764f6e865832e921bd9801e45790f378fa306931e7d4db41a3f4fa38352d254`.

Conditional law (not empirically calibrated): `sigma_mu_i^2 = (published e_DMzp_i)^2 + (0.15mag)^2 + (250km/s*velocity-gradient-magnitude-basis)^2`, four source method families `FP,TF,SN,OTHER`. Five orthonormal STF angular columns `T`, nuisance columns `N`, all whitened. Exact profile Fisher `F=T^T (I-P_N)T`, QR projection. Nuisance spaces nested and Fisher matrices ordered under Loewner PSD order.

| Nuisance channels | Nuisance rank | STF5 trace retained |
|---|---:|---:|
| Method intercept | 4 | 0.83924589295336 |
| + Method log(z) slope | 8 | 0.83348932415552 |
| + 3 bulk components | 11 | 0.77992415293830 |
| + 3 angular dipole | 14 | 0.59488567740044 |

The 5-dimensional profiled design remains full rank under **this declared diagonal law only**. The recovered covariance inverse of Fisher matches archived original 5x5 conditional covariance with relative Frobenius residual **8.313917029883273e-16**. The original group hash was directly checked against saved selection-ID digest.

Leave-one-method-family-out fits:

| Left out | Rows retained | Formal distance in original WLS covariance norm | `||a_STF||` |
|---|---:|---:|---:|
| FP | 9,054 | 6.83770 | 0.03584077 |
| OTHER | 35,230 | 0.39280 | 0.03286750 |
| SN | 35,270 | 0.87247 | 0.03376937 |
| TF | 28,356 | 4.29718 | 0.03681453 |

**Never treat these distances as detection sigmas**: deleting observations correlates estimates and the source survey selection/shared calibration and cross-source covariance are not supplied. These values measure methodology sensitivity only. Conditional source projector does not establish Bianchi shear, global tilt, genuine common sky likelihood or family identification.

Verified: 13 scoped Python tests PASS in 0.23 s in isolated ChatGPT container (not user's Linux workstation), synthetic Schur=block-inverse and row-permutation invariance and rank failure, plus the original STF tests. The full executed standalone script, three new tests, immutable NPZ and JSON, complete `SCHUR_METHOD_IDENTIFIABILITY.json`, manifest/README are in the **independent archival checkpoint** `HTT_CF4_SCHUR_METHOD_CHECKPOINT_20261016.zip` (1,253,671 bytes, SHA256 `7c7537506f0510d05dac137e6ee1e94cc9381fed42be54c808995e4a8b3ecd7c`). The available local desktop tool reached its monthly quota; local execution NOT_RUN. Native fresh independent review NOT_RUN. No main merge or scientific posterior admission.

**DAG outcome:** C8-CF4-METHOD → `COMPLETED_SCOPED_CONDITIONAL`; actual empirical source/covariance/selection and C8-REAL-JOINT remain `BLOCKED_PHYSICAL_INPUT`. Continue `C8-OBS-MES-EPS` as a separate ready diagnostic if inputs verify.
