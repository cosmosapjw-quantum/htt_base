# R48-T1: 물리 상태, frame 및 epoch 계약

상태: **계약 초안 고정, 기존 코드의 전면 준수는 아직 검증되지 않음**  
기준: htt_base R48 branch; R42 source chart와 R48 observation-likelihood spec을 조정한 계약.

## 1. 상태 차트와 단위

Metric signature는 \((- + + +)\), 광속 \(c\)는 명시적으로 유지한다. 기준 congruence의 unit 4-velocity를 \(u^a\), 이를 첫 번째 tetrad leg \(e_0^a=u^a\)로 둔다. 공간 tetrad \(e_i^a\)는 오른손 직교 triad이며, 모든 공간 성분과 관측 방향은 해당 triad에 대한 성분이다.

\[
\theta_K =
\left(
\sigma_{\mathrm{STF2}}^{[5]},
\omega^{[3]},
A^{[3]},
\beta_{RM}^{[3]},
\beta_{MO}^{[3]}
\right)\in\mathbb R^{17}.
\]

R42 코드의 실제 인덱스 계약은 다음과 같다.

| Index | Component | 의미 및 chart |
|---|---|---|
| 0–4 | \((\sigma_{xx},\sigma_{yy},\sigma_{xy},\sigma_{xz},\sigma_{yz})\) | STF shear, \(\sigma_{zz}=-\sigma_{xx}-\sigma_{yy}\) |
| 5–7 | \((\omega_x,\omega_y,\omega_z)\) | axial vorticity vector |
| 8–10 | \((A_x,A_y,A_z)\) | polar 4-acceleration의 공간 성분 |
| 11–13 | \((\beta_{RM,x},\beta_{RM,y},\beta_{RM,z})\) | radiation-to-matter 상대 속도 |
| 14–16 | \((\beta_{MO,x},\beta_{MO,y},\beta_{MO,z})\) | matter-to-observer 상대 속도 |

무차원 표본 chart는 \(\sigma_{ij}/H_{\rm ref}\), \(\omega_i/H_{\rm ref}\), \(A_i/(cH_{\rm ref})\), \(\beta_i=v_i/c\)로 정의한다. \(H_{\rm ref}\), 기준 event, epoch, tetrad, 좌표 단위는 run manifest에 고정한다. R42 runner에서 \(\omega_i\)와 \(A_i\)가 0으로 고정된 사실은 관측되었다는 뜻이 아니라 prior/model restriction이다. 17D physical chart와 실제 샘플러가 탐색한 차원을 구별한다.

Cartesian STF 행렬은
\[
\Sigma =
\begin{pmatrix}
s_{xx}&s_{xy}&s_{xz}\\
s_{xy}&s_{yy}&s_{yz}\\
s_{xz}&s_{yz}&-s_{xx}-s_{yy}
\end{pmatrix}.
\]
Frobenius metric은
\[
\|\Sigma\|_F^2=s_{xx}^2+s_{yy}^2+(s_{xx}+s_{yy})^2
+2(s_{xy}^2+s_{xz}^2+s_{yz}^2)
\]
이며, 저장된 5개 숫자의 naive Euclidean norm과 같지 않다. STF basis chart 변환은 이 metric을 보존해야 한다.

## 2. Frame 화살표와 정확한 boost 합성

세 congruence를 서로 혼동하지 않는다: \(R\)은 radiation/CMB rest frame, \(M\)은 matter/source congruence frame, \(O\)는 observer/instrument frame이다. \(\beta_{RM}\)과 \(\beta_{MO}\)의 방향을 source 계약에서 명시하고 이 순서의 Lorentz map만 합성한다.

현재 compose_velocities_sr(beta_RM, beta_MO)의 documented convention에서는
\[
\beta_{RO}
=
\frac{\beta_{RM}+\beta_{MO,\parallel}
+\gamma_{RM}^{-1}\beta_{MO,\perp}}
{1+\beta_{RM}\cdot\beta_{MO}},
\quad
\gamma_{RM}=(1-|\beta_{RM}|^2)^{-1/2},
\]
\[
\beta_{MO,\parallel}
=\frac{\beta_{RM}\cdot\beta_{MO}}{|\beta_{RM}|^2}\beta_{RM},
\qquad
\beta_{MO,\perp}=\beta_{MO}-\beta_{MO,\parallel}.
\]
\(|\beta_{RM}|\to0\) limit은 \(\beta_{RO}=\beta_{MO}\)이다. 비공선 boost는 Wigner rotation도 만든다. 따라서 벡터/텐서 성분과 covariance를 동일한 합성 convention으로 회전시켜야 한다.

정확한 composition kernel은 존재하지만 full_observable_x_bundle.py는 두 boost가 모두 nonzero인 경우에만 이 함수를 호출한다. 한 boost만 0인 경우 model.state.beta_RO로 건너뛰므로 그 값과 exact zero-boost limit의 일치를 별도 assertion으로 검증해야 한다. R42 runner와 test fixture의 beta_RM + beta_MO는 1차 근사일 뿐 exact relation이 아니다.

## 3. Event와 epoch transport

하나의 공통 기준 event \(p_\star\)에 대해 \(\theta_K(p_\star)\), tetrad, congruence, averaging scale을 정의한다. 관측자별/탐침별 event \(p_i\)로 옮길 때는 source/observer congruence와 frame arrow, 동역학적 transport 또는 optical response operator, redshift/proper time/scale-factor convention, tetrad parallel transport 및 basis map, 해당 probe의 selection/beam/mask/pixelization/transfer/covariance를 모두 기록한다.

값을 단순 복사하거나 \(\sigma(z)=\sigma_0/(1+z)\)로 대체하지 않는다. G_F의 R42 default PHYSICAL_EXPANSION_TRANSPORT는 실제 코드에서 transport factor 1을 선택한다. 대안 LINEAR_OPTICAL_EXPANSION은 \(1/(1+z)\)를 곱하지만 field equation 또는 Jacobi/optical transport에서 유도된 kernel이라는 증거가 없다. 두 경로 모두 현재는 물리적으로 검증된 depth transport로 승격하지 않는다.

Bianchi-I endpoint anisotropy \(B_\star\)는
\[
B_\star \sim \int_{t_\star}^{t_0}\sigma(t)\,dt
\]
에 해당하는 history-dependent quantity이며 현재 \(\sigma(t_0)\)와 동일시하지 않는다. R47 temperature map 자체는 recombination/visibility/foreground/beam transfer나 polarization prediction을 제공하지 않는다.

## 4. Gauge, nuisance 및 identifiability

Gaia VSH \(B_1\) catalogue spin과 \(\omega_a/H\)는 외부 inertial/quasar-frame anchor가 없으면 leading optical order에서 gauge-degenerate다. 이 둘을 독립적인 cosmological measurements로 세지 않는다. \(A_a=0\)는 geodesic model restriction일 수 있지만 empirical anchor가 아니다. Shear upper bound는 source와 prior/likelihood dependence를 명시하지 않는 한 local measurement로 취급하지 않는다.

목표량 \(\ell^T\theta\)의 point-identifiability는 유효 Jacobian과 nuisance projection에서
\[
\ker(J_{\rm eff})\subseteq\ker(\ell^T)
\]
를 검증한다. 모든 probe의 frame/basis/covariance를 함께 변환하고, 공통 systematic 또는 shared LSS를 독립 likelihood 곱으로 숨기지 않는다.

## 5. 변경 시 invalidation rule

Frame arrow, tetrad, orientation, \(H_{\rm ref}\), epoch, transport, mask, selection, beam, pixel, transfer 또는 covariance가 바뀌면 영향받는 source response와 posterior push-forward를 다시 검증한다. Byte hash 변화와 semantic 변화는 구분하되, 관측 source identity가 바뀌면 관련 likelihood evidence는 새 identity로 다시 고정한다.

**현재 판정:** 이 문서는 물리-state contract다. R42 구현의 전체 충족이나 관측 inference 통과를 의미하지 않는다.