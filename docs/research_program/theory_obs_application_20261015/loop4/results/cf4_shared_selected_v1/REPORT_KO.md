# 실제 CF4 SNIa method field 공유 영점·선택법칙 분석

원자료: 그룹 38053, 저장된 정확한 SNIa-only 24개 그룹.
DMzp와 method-specific DMsnIa는 공유 원본의 의존 파생물이며 독립 data likelihood를 곱하면 안 된다.

| Published delta DMzp-DMsnIa (mag) | Group count |
|---:|---:|
| -0.422 | 1 |
| -0.326 | 1 |
| -0.147 | 22 |

### 원본 Method-only 오류 및 속도폭 시나리오
| Extra radial velocity σv (km/s) | Dipole norm in magnitude residual | Intercept-profile χ² |
|---:|---:|---:|
| 0.0 | 0.17757 | 25.54 |
| 150.0 | 0.17733 | 22.63 |
| 300.0 | 0.1793 | 17.11 |
| 500.0 | 0.18443 | 11.13 |

η shared calibration prior = 0, .05, .1, .3 mag is a *hypothetical input*; unspecified actual release cross-method calibration is not reconstructed.
Hreference in the displayed formula is a redshift velocity/distance proxy. With unrestricted zero point, profile likelihood exactly independent of this H reference.

| Assumed sigma_eta (mag) | Implied relative log-distance-scale sigma | Pre-minus-slot selected log likelihood (counterfactual) |
|---:|---:|---:|
| 0.0 | 0 | 1.77636e-15 |
| 0.05 | 0.0230259 | 0.000597434 |
| 0.1 | 0.0460517 | 0.00632472 |
| 0.3 | 0.138155 | 0.169322 |

The preselection/slot comparison uses counterfactual selection in method modulus [31,35.6], NOT the actual outcome-selected DMzp 31..35 + hash ordering. Do not use the resulting likelihood as a CF4 cosmological posterior.
Direct fit of angular residual is a fixed-cohort phenomenological morphology, not generalized GR shear/acceleration/geodesicity.
Exact Etherington reciprocity is an *upstream same-source-congruence requirement* for a future physical distance model, not implemented by using a crude Vcmb/Href proxy.
Required next independent sources: per-survey selection flags and flux limits, SN event group membership, cross-method calibration covariance, source-frame true redshift and velocity law.
