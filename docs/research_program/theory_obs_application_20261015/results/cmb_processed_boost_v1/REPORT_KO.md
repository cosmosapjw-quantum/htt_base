# HTT 기존 boost·식별성 정리의 실제 Planck 지도 적용

결과 등급: **실제 원자료/관측상품 계산 완료, 모델 조건부 탐색적 진단**.

계산은 동일 SMICA 관측 하늘을 여러 source cutoff로 재구성한 제한 모델이며,
추정 속도, 전단 또는 Bianchi family 검출이 아니다. Planck 원자료를 재보정한 결과도 아니다.

| mask threshold | source L | ||J||F [microK/beta] | ||J beta_ref|| [microK] | relative to observed low-l norm | extra-stress A=0 conditional sigma |
|---|---:|---:|---:|---:|---:|
| 0.5 | 5 | 355.944 | 0.249173 | 0.00258178 | 0.0149946 |
| 0.5 | 8 | 409.586 | 0.301678 | 0.0031258 | 0.0165011 |
| 0.5 | 12 | 455.705 | 0.365444 | 0.0037865 | 0.0199204 |
| 0.8 | 5 | 356.554 | 0.249188 | 0.00259323 | 0.0148738 |
| 0.8 | 8 | 411.301 | 0.302654 | 0.00314964 | 0.0162938 |
| 0.8 | 12 | 465.668 | 0.379152 | 0.00394572 | 0.0199561 |

## 물리적 해석 경계

조건부 Fisher 행렬은 실제 kinematic beta의 추정치가 아니라, 해당 source model에 주입된 beta 변화의 상대적 민감도이다.
C_null은 동일 저장 모의하늘 240개의 샘플 공분산이다. 추가 A²KKᵀ를 실제 nuisance로 사용할 경우 기존 하늘의 cosmic variance 중복계산 가능성을 평가해야 한다.
T0의 일차 도플러 dipole은 joint-fit의 ell1에 흡수되므로 retained ell2..5에 기여하지 않는다.
mask/fit 효과는 *cache 단계*에서만 계산; upstream Planck compsep, true full-sky high modes, emission physics는 포함하지 않는다.
Finite cutoff 변화를 bias 인증이나 사후 유의성 재보정으로 해석하지 않는다.

연관 정리: HTT Report A의 local-observer temperature pullback, WU-010, nuisance projection, covariance-whitening.
선행 문헌: Planck Collaboration 2014 A&A Doppler Boosting (aa21556-13); Challinor & van Leeuwen 2002; Dai & Chluba 2014 aberration kernels.
