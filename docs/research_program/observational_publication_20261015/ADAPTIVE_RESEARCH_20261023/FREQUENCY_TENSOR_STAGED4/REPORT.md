# R25 staged four-frequency native pseudo-tensors

Four delivered Galactic COSMO maps were qualified individually and projected at their native NSIDE on the same validity-only S4 support. The original selected support contains 30,021 RING64 cells; S4 also contains 30,021. One 100 GHz BAD_DATA pixel lies outside those selected cells. No Q/U map was downgraded, smoothed or deconvolved.

The complete result contains all 96 E2/E3/B2/B3 canonical coordinates, four sets of full STF tensors and six oriented 24-coordinate contrasts with their full STF tensors. The independent native Wigner-d quadrature agrees with healpy in every coordinate within the declared 1e-12 K absolute and 1e-9 relative tolerance. The 24-basis NSIDE16 synthetic fixture, parity, permutation, sentinel, mask, linearity, reduction and STF sign checks passed.

| Band (GHz) | Computational Q |
|---:|---:|
| 30 | 1.87189639181 |
| 44 | 0.486246658956 |
| 70 | 0.174452770909 |
| 100 | 0.22156837509 |

| Oriented pair (GHz) | Full 24-coordinate contrast Euclidean norm (K_CMB) |
|---:|---:|
| 30-44 | 1.39889398768e-05 |
| 30-70 | 1.72279563727e-05 |
| 30-100 | 1.72187018371e-05 |
| 44-70 | 3.41091140482e-06 |
| 44-100 | 3.75007907698e-06 |
| 70-100 | 1.62068780381e-06 |

The figure displays the canonical coordinates and the pair norms; the NPZ preserves every coordinate and tensor. Q uses the declared 1e-5 K ell-2 and ell-3 computational gauges. F_frequency_empirical is the four-point count with mass 1/4 at each band. It has no physical or sampling-law interpretation.

Delivered beams, mapmaking, pixelization, mask-induced E/B and higher-mode leakage and instrumental/systematic differences remain in the pseudo-modes. Physical MES/F are NOT_EVALUABLE; Pi is NOT_CALIBRATED; G_F is NOT_APPLICABLE because frequency is not depth. The result does not reject a foreground model, establish significance, invert a full-sky response, or promote the original all-seven acquisition. Independent review and scientific admission remain pending.

The first failed import-path synthetic probe and two native-run plumbing failures are retained in TEST_RECEIPT.json and RAW_RECEIPT.json, with cumulative product charges.
