# Planck PR3 다중 분할과 spin-2 low-ell 실제 관측 source-bound 연구

T 공동 픽셀 26846/49152, 편광 공동 픽셀 30021/49152.
분할 간 source mean 비교는 동일 low-ell fit mask에서 시행하며 각 모형은 같은 CMB 하늘을 공유한다.

| 관측 동일하늘 대비 | norm (microK) | same-mask SMICA full 기준 비율 |
|---|---:|---:|
| SMICA_HM_vs_SMICA_OE | 0.101587 | 0.10211% |
| SMICA_FULL_vs_HM_mean | 0.0750023 | 0.075391% |
| SMICA_FULL_vs_OE_mean | 0.0751996 | 0.075589% |
| NILC_HM_mean_vs_SMICA_HM_mean | 2.09797 | 2.1088% |
| NILC_FULL_vs_NILC_HM_mean | 0.0914325 | 0.091906% |
| SMICA_noSZ_FULL_vs_SMICA_FULL | 5.32419 | 5.3518% |
| SMICA_FULL_vs_NILC_FULL | 2.10737 | 2.1183% |

## 실제 split low-ell half differences
| product | norm (microK) |
|---|---:|
| SMICA_HM | 0.424724 |
| SMICA_OE | 0.540939 |
| NILC_HM | 0.509779 |

## spin-2 E/B finite harmonic joint fit, intensity와 다른 missing mask
| 비교 | EB norm (microK) |
|---|---:|
| SMICA_HM_split_difference_EB_norm_microK | 0.43128 |
| SMICA_OE_split_difference_EB_norm_microK | 0.345864 |
| SMICA_HM_vs_SMICA_OE_mean_EB_norm_microK | 0.145848 |
| NILC_vs_SMICA_HM_mean_EB_norm_microK | 0.737348 |
| SMICA_FULL_vs_SMICA_HM_EB_norm_microK | 0.590775 |

**주의:** 모든 비교는 하나의 하늘을 다른 split·성분분리 조건으로 본 결과다. Noise/foreground null simulation이나 CMB anomaly p-value가 없다.
Cut sky finite E/B fitting remains contaminated by modes outside the truncated l2..5 spin basis. Spin2 frames and mask conventions are explicitly fixed; no true physical EB cosmology inference.
Same-sky common-mode cancellation is algebraic only if processed physical sky response is the same in each split.
Source: official Planck PR3 component separation and missing pixel products, A&A 641 A4 (2020).
