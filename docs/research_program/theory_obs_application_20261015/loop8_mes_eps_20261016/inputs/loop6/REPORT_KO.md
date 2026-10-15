# Legacy x→Q→Π의 실제 Planck·CF4 조건부 전달

사용자가 준 main_FINAL.pdf의 2.7, 6, 7.8절의 수학적 map을 그대로 유지하되 새 관측물리 해석은 보류.
첨부 최신 code_package의 obs_defaults.json에는 기존 400±80 km/s 출처가 2009 COMPOSITE라고 명시돼 있다.
2009 원본과 Watkins CF4 2023 R150/R200은 서로 다른 survey window이며 후자끼리는 독립 표본이 아니다.

| source window | 1D mean±sigma km/s |
|---|---:|
| WFH_2009_COMPOSITE_50hMpc | 407.0±81.0 |
| CF4_2023_150hMpc | 387.0±28.0 |
| CF4_2023_200hMpc | 419.0±36.0 |

## 실제 SMICA full의 C2,C3 scalar rms, flat/orthogonal legacy x=Ωtilt 예시
| source | epsilon1 assignment | x_median | x_max | Q_median | Pi(Q>0.05) |
|---|---|---:|---:|---:|---:|
| WFH_2009_COMPOSITE_50hMpc | CMB_total_dipole_beta_dominated | 5.8132e-07 | 6.4743e-06 | 0.089789 | 0.8989 |
| CF4_2023_150hMpc | CMB_total_dipole_beta_dominated | 5.2548e-07 | 6.4743e-06 | 0.081164 | 0.9983 |
| CF4_2023_200hMpc | CMB_total_dipole_beta_dominated | 6.1599e-07 | 6.4743e-06 | 0.095144 | 0.9992 |
| WFH_2009_COMPOSITE_50hMpc | legacy_S3_matter_number_counts_NOT_CMB | 5.8132e-07 | 9.2374e-06 | 0.062931 | 0.7075 |
| CF4_2023_150hMpc | legacy_S3_matter_number_counts_NOT_CMB | 5.2548e-07 | 9.2374e-06 | 0.056886 | 0.8053 |
| CF4_2023_200hMpc | legacy_S3_matter_number_counts_NOT_CMB | 6.1599e-07 | 9.2374e-06 | 0.066684 | 0.9407 |
| WFH_2009_COMPOSITE_50hMpc | zero_CMB_intrinsic_dipole_sensitivity_only | 5.8132e-07 | 6.9925e-10 | 831.35 | 1 |
| CF4_2023_150hMpc | zero_CMB_intrinsic_dipole_sensitivity_only | 5.2548e-07 | 6.9925e-10 | 751.49 | 1 |
| CF4_2023_200hMpc | zero_CMB_intrinsic_dipole_sensitivity_only | 6.1599e-07 | 6.9925e-10 | 880.93 | 1 |

실제 CF4 local angular STF proxy Sigma²를 무비판적으로 동종 배경 shear로 등치하면 MES ceiling 대비 형식적 비율 median=30.07, 95%=[17.2,46.89].
이 불일치는 legacy MES 위반 검출이 아니라 survey/structure/nuisance 포함 local angular residual을 global background shear라고 잘못 식별하는 가정을 검증한 예제다.
W2·A2의 상한은 posterior가 아니며, 본 데이터는 geometry-frame omega/4-accel의 진짜 likelihood를 제공하지 않는다.
같은 Planck 하늘을 처리한 9개 map의 epsilon_l은 독립 관측이 아니다.
Legacy S3 number-count epsilon1은 이론적 MES CMB epsilon1이 아니며 cross-domain transfer 없이는 MES bound 입력으로 승인할 수 없다.
2009+2023 bulk 자료는 별개 surveys/windows이므로 합산 독립 likelihood를 만들지 않았다.
