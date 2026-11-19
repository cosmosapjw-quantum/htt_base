# R74 · P4의 물리적 5뷰 정리 및 실제 NVSS source-conditioned 결과

2026-11-19 KST. 현재 작업은 P4의 네 번째 논문을 위한 R1–R10 전체 **이론** 연구 루프이다. Source input: htt_base  \`research/r69-observable-physics-bridges-20261118\` branch HEAD \`be98cde64623415007b183e06edc946fd56400b0\`. P1–P6 논문 42개 canonical science DAG, 기존 R63/R65/R72/R73 원자료와 다른 미추적 파일을 수정하지 않았다. 핵심 결과는 새로운 우주론적 이상도 검출/실제 global tilt 측정이 아니라, 각 물리적 입력과 현재 radio counts x의 관계를 정직하게 구조화한 정리와 실제 source-likelihood 계산이다.

## P4에서 x 선정: 6D 원관측 + 4D 공유 자료 대비 + latent physical state
1. **기본 x:** R65 original \`base64_dipole\` 3개 disjoint flux bin × 2개 ICRS transverse dipole coefficient, 총 6D signed log-count field + 동일 원실험의 block C6. 각각 source density positive를 유지하는 declination-ring profiled exponential conditional multinomial law. 33,000개 실제 mask pixel, 185개 고정 declination ring, 115906/65260/55581개 선택된 component. P4에서 x가 5성분인 척하는 것은 부적절하다.
2. **대조 x:** R65 \`base64_dipole_stf\`는 각 bin에서 angular STF 자유도를 추가한 별도 모형의 signed transverse 6D carrier와 다른 C6. 동일한 sky/counts의 대안 fit이므로 **독립 관측이 아님**. Same-provider peak와 integrated selection의 4D 공분산 대비도 동일 source ID의 correlated selection이며 독립이 아니다.
3. **물리적 잠재 대상:** \(\beta_{O|S}^i=v_{O|S}^i/c\), intrinsic selected source dipole \(a_b^i\), matter–radiation velocity invariant \(\Gamma_{MR}=-g(U_M,U_R)/c^2\), 그리고 별도 Bianchi normal \(a_i,N^{ij},\sigma_{ij},j_i^N\). 실제 radio x는 이들 중 beta_z, \(\Gamma_{MR}\), geometry family를 측정하지 않는다.

## 새 정리 1: Flux-bin collinearity/ordering은 source physics의 조건부 예측
만약 source selection이 bin별 k_b로만 달라지고 **하나의 공통** residual a가 유지된다면
\[
v_b=a+k_b\beta_\perp \Longrightarrow
\det(v_2-v_1,v_3-v_1)=0.
\]
이를 통해 **기본 x의 관측 부호/방향을 제거하지 않고** 세 flux bin의 물리적 공통-velocity 가능성을 비교할 수 있다. 자유 k_b에서는 collinearity가 필요충분하나 실제 flux selection k_b의 가능성과 무관하므로 그것만으로 Lorentz 증명이 되지는 않는다. 정해진 \(k_1<k_2<k_3\)에서는 \(v_2\)가 \(v_1,v_3\) 사이의 같은 직선 구간에 있어야 한다. 실제 R65 pure-dipole 점추정은 determinant \(+1.778647546\times10^{-6}\) 및 \(|v_2-v_1|>|v_3-v_1|\)로 이 정확한 점모형에서 벗어난다. 하지만 source uncertainty 아래 기각 증거가 아니다.

## 새 정리 2: nuisance-profile score Qstat와 조건부 Pi는 하나의 법칙
고정 k와 공유 residual a를 갖는 6D Gaussian 근사에서 \(X=[k\otimes I_2,\mathbf1\otimes I_2]\in\mathbb R^{6\times4}\)이고
\[
T=\min_{\beta,a}(x-X\vartheta)^\top C^{-1}(x-X\vartheta),\quad
Q_{\rm stat}=\sqrt T,\quad\Pi_{\rm working}=\exp(-T/2).
\]
정규 고정-C Gaussian에서 T~χ²2. 원 R65 pure-dipole 저장 source로 재계산하면 \(T=1.787959566,\ \Pi=0.409024680\); **dipole+STF nuisance** 저장 source는 \(T=1.668857013,\ \Pi=0.434122509\)로 원 R65 기록을 재현한다. 서로 다른 Gaussian carriers와 모델이며 독립적인 두 검출이 아니다.
순수 dipole의 작은 행렬식은 조건부 고정-k Gaussian 50,000-draw bootstrap에서 \(p_{\rm det}\approx0.97468\)로 이 working model과 모순되지 않는다. 이는 k-free 불규칙 null이나 cosmic LSS/overdispersion law의 calibrated p가 아니다. 또 실제 source conditional \(\hat\beta_\perp\)는 매우 넓은 오차와 a의 퇴화를 가지며 3D \(\beta\)는 미측정. 따라서 **\(Q_\beta=|\beta|\)와 GR global tilt에 대한 Pi는 여전히 UNAVAILABLE**이다.

## 새 정리 3: 실제 NVSS mask가 만드는 F susceptibility 및 axial null
선택된 count의 \(F_A=N(A)/N\)는 원래 finite empirical source measure 아래 정당하게 정의된다. R65 실제 CMB 축으로 반구를 나누면 raw selected F는 세 flux bin에서 각각 0.511983849, 0.512794974, 0.511343805다. 이는 full-sky intrinsic occupancy가 아니다.

**같은** R65 fitted log-link와 고정된 185 ring 총량을 보존하며 \(\beta\)를 score로 삽입한 경우에만
\[
F_{b,A}(\beta)=\sum_r(N_{br}/N_b)\sum_{p\in r}1_A(p)
\frac{w_{brp}e^{k_b\beta\cdot n_p}}{\sum_{q\in r}w_{brq}e^{k_b\beta\cdot n_q}},
\quad w_{brp}=e^{\hat v_{b,\perp}\cdot n_{p,\perp}}.
\]
따라서
\[
\boxed{\nabla_\beta F_{b,A}(0)=k_b\sum_r(N_{br}/N_b)
\mathrm{Cov}_{p_b(\cdot|r)}(1_A,n).}
\]
원래 declination ring에서 \(n_{pz}=z_r\)는 정확히 일정하므로 axial β_z의 지수인자 \(e^{k_b\beta_z z_r}\)는 ring normalization에서 사라진다. \(\partial_{\beta_z}F=0\)이 **모든 β_z에서** 정확히 성립한다. 이것은 광학적으로 불변적인 global 3D velocity no-go가 아니라 R65 conditional log-link의 source nuisance symmetry다. 같은 mask를 ring-profile 없이 globally normalize하면 z-score derivative는 세 bin에서 +0.0128234, +0.0138056, +0.0159572로 0이 아니다.

계산된 CMB-axis \(\nabla_{\beta_\perp}F\)는 bin1 (-0.940535,+0.075561), bin2 (-0.987719,+0.078832), bin3 (-1.157262,+0.093058)이다. 고정 pixel/ring model에 CMB 기준 \(\beta=369.82/c\)를 가상으로 주입한 score increment는 bin별 +0.00114557,+0.00120291,+0.00140955. **이는 실제 Lorentz boosted radio sky 관측이나 physical G_F가 아니라** 하나의 source-selected 조건부 반응값이다. 부호/크기·frame·측도를 모두 지정한 물리적 설명력이 있으며 full data의 Fisher를 더하지 않는다.

## 새 정리 4: 실제 G_F가 존재하려면 source flow와 선택법칙이 필요
하나의 시간적으로 식별된 source population에 대해 \(\partial_\tau\rho+\nabla_{S²}\cdot(\rho V)=s\), 관측 영역 A의 boundary velocity W_A, F_A=N_A/N이면
\[
\boxed{\dot F_A=-
\frac1N\oint_{\partial A}\rho(V-W_A)\cdot\nu\,d\ell
+\frac1N\left(\int_A s\,d\Omega-F_A\int_{S²}s\,d\Omega\right).}
\]
이는 angular continuity/selected-source balance의 정확한 Reynolds corollary다. R65 flux-bin/peak-integrated 선택은 물리적 시간 수송이 아니므로 \(G_F\)를 측정하지 못한다. 예제 두 반구에서 s=±ρ,V=0을 정하면 \(F=e^\tau/(e^\tau+e^{-\tau})\), \(\dot F=2F(1-F)\). τ=.3에서 0.457568481을 수치 검산했다. 실제 general Bianchi/tilt에 적용하려면 \(N^{ij}a_j=0\), Einstein normal Codazzi 및 source/observer lightcone transport, selection-migration s를 함께 입력해야 한다.

## 네 변수와 직관
- **Q:** 현재 source의 \(Q_{\rm stat}=\sqrt T\)는 common-response mean에 대한 *조건부 적합 거리*이다. 실제 물리적 Lorentz causal \(Q_\beta=|\beta|\)는 3D observer–source 상대속도 미식별로 계산 불가. 같은 값을 둘로 바꾸지 않는다.
- **Π:** 고정 α,k,C와 공유 a의 Gaussian tail \(\exp(-Q_{\rm stat}^2/2)\)은 하나의 원 source-law 확률; LSS/selection/observer-motion physical rarity가 아니다. 따라서 Q_stat와 Pi는 독립 증거가 아니다.
- **F:** 실제 source-count empirical hemisphere fraction과 ring-conditioned fitted \(F_A(\beta)\)는 둘 다 finite selected-source 측도를 갖는다. 전천 STF χ로 결정되는 \(F_{\Omega,2}\), 파라미터 body의 volume occupancy와는 다르다. \(\partial_\beta F\)는 mask/source selection geometry를 묘사한다.
- **G_F:** 실제 source time matching과 V,s, moving event가 있어야 정의한다. R65에 없으므로 현재 값은 unavailable. 물리적 flow가 제공되면 T4를 그대로 사용할 수 있다.
- **x:** full signed 6D carrier (필요시 free STF 추가), 실제 pixel/mask/flux bin/response와 원 source covariance를 보존한다. 물리적 latent x=(β,\(\Gamma_{MR}\), normal geometry)는 별도 전방 전달 과정 없이는 대체 불가.

## P1–P6 및 PHY-01..07 응용
\`APPLICATIONS.json\`에는 원래 여섯 논문에 대한 물리적 x, Q,Pi,F,GF, 실제 equations, cross-channel estimability, next test, blocker 및 원 R69 일곱 결합 PHY-01..07에 대응하는 정확한 조건부 물리 예측과 acceptance 제한을 보존했다. 반복된 이론을 7개의 데이터 검출로 포장하지 않았다. P1의 optical selected STF와 P3의 distance-derived H_D는 같은 GR shear가 아니며, P2의 photon flux/stress와 radio count IMF/selection은 다른 kinetic source, P5 일반 Lie/tilt와 P6 Gaia proper motion은 다른 observer/normal frames를 갖는다. 공통 Lorentz/optical/kinetic forward model과 source crossover C가 없으면 joint posterior를 만들지 않는다.

## 판별·검증 상태 및 다음 물리 계산
주요 T1/T3는 초등 선형대수와 log-normalizer 미분에서 직접 유도했고, Wolfram T1 determinant=0, 실제 source 3-bin GLS와 185 ring score 및 finite difference, 50,000 source-conditioned parametric Gaussian null, strict normalized-count source transport toy를 계산했다. 기존 R63/R65 관련 57개 회귀 테스트가 R7에서 통과했다. 원래 R65 source data, R63 restricted history, and six-paper science DAG remain unchanged. Native subagents unavailable, independent referee NOT_RUN. No LSS-null calibrated PTE, no 3D physical observer velocity, no global tilted Bianchi Einstein–Boltzmann solver.

수렴 선택: **동일 source ID를 보존한 실제 peak/integrated selection의 \(k_b,\kappa_b\), α/SED/beam/morphology response를 측정한 뒤**, 고정된 순수 count-score reweight보다 실제 Lorentz flux+aberration/reselection injection과 cluster-aware source covariance를 수행하는 한정된 coding slice를 우선한다. 그 뒤에도 필요하면 electron-frame photon/kSZ를 별도 source와 공통 frame으로 연결해야 global matter–radiation tilt를 논할 수 있다. Scope status R1–R10 THEORY_COMPLETE_SCOPED, physical P4 science NOT_READY_TO_SUBMIT; no automatic next loop.
