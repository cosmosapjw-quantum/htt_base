# R71 · P3 directional/redshift Hubble — 물리적 5뷰 연구 R1–R10 결론

2026-11-19 KST. 기준 브랜치: research/r69-observable-physics-bridges-20261118, 입력 commit b9cede3a957a47f6186c7751beae61520f243f4d. 본 연구는 R64/R69/P1/P2 이후 **세 번째 논문 P3의 유한 적색편이 GR–Sachs 광학 설명력**에 집중한 독립적인 10단계 이론 루프다. 6개 논문·7개 원래 R69 결합 축의 적용은 APPLICATIONS.json에 구조화했다. 이 연구에서 새로운 관측원, 새로운 p-value, Bianchi family 식별, 실제 null-energy 위반이나 native Einstein–Boltzmann 구현을 얻었다고 주장하지 않는다.

## 1. 정확히 구별해야 하는 세 가지 Hubble 관측량
\[
\mathcal H(\lambda,n)=\Theta/3+\sigma_{nn}-A_n/c,\quad
H_D(z,n_o)=\frac{c}{\partial_z[D_L(z,n_o)/(1+z)]},\quad
H_W=\text{실제 source/window 추정량}.
\]
첫째는 지정한 source congruence의 물리적 광선별 운동학적 팽창, 둘째는 관측자 방향 n_o의 거리 함수 미분, 셋째는 R64에서 실제 선택·보정·window 연산자로 얻은 통계적 관측량이다. 국소 vertex의 선도값은 적절한 조건에서 일치하지만, 유한 적색편이·observer boost·optical focusing·tilt가 있으면 일반적으로 같지 않다. 따라서 각 STF5는 서로 다른 source·frame의 estimand이지 동일 텐서로 미리 선언할 수 없다.

## 2. P3-T1·T2: Sachs+Einstein NEC가 강제하는 광학 기하 조건
과거 방향으로 증가하는 길이단위 affine λ와 동일 source congruence에 대해, caustic 이전 D_A>0, \(\mathcal H>0\), \(D_A(0)=0,D_{A,\lambda}(0)=1\), \(dz/d\lambda=(1+z)^2\mathcal H/c\), \(\mathscr F=|\sigma_{\rm opt}|^2+\tfrac12 R_{ab}k^ak^b\ge0\)를 가정한다. 그러면
\[
\boxed{M=\frac{(1+z)^2\mathcal H D_{A,z}}c=D_{A,\lambda},\quad M_z=-\frac{c\,\mathscr F D_A}{(1+z)^2\mathcal H}\le0,\quad M(0)=1.}
\]
\(R=D_L/(1+z)=(1+z)D_A,\ Y=\mathcal H^2\)라 두면 정확히
\[
\boxed{\frac12\left(R'-\frac{R}{1+z}\right)Y'+R''Y+\frac{c^2\mathscr F R}{(1+z)^4}=0,\quad
\frac12\left(R'-\frac{R}{1+z}\right)Y'+R''Y\le0.}
\]
이것은 광학/운동학의 *공통 물리 방정식*으로, 모든 Bianchi Class A/B와 tilted/multifluid/kinetic matter를 포함하는 임의 시공간의 NEC 보유 광선에서 성립한다. Lie \(a,N\), tilt, optical Weyl/Ricci source는 \(\mathcal H,\mathscr F\)의 *실제 값*을 결정하지만 Sachs의 위 항등식 자체를 바꾸지 않는다. 이미 알려진 Sachs 법칙에서 도출된 정밀한 조건부 정리이며 최초성은 주장하지 않는다.

필요한 관측 작업은 같은 frame/광선/시점에서 거리 \(D_L(z,n)\)와 독립적인 물리 \(\mathcal H(z,n)\)를 결합하는 것이다. 현재 R64는 \(H_D\)에 대한 거리 기반 계산을 수행했지만 그 자체로 독립 \(\mathcal H\)가 아니다. Optical focusing을 나중에 반드시 측정한다는 약속도 하지 않는다.

## 3. P3-T3: 물리 가정이 명시된 보정불변 focusing comparator
추가 가정 \(\mathcal H(z,n)=H_{\rm ref}(z)\), flat smooth reference \(\chi' =c/H_{\rm ref}\), \(\eta=\ln(\chi/R)\) 하에서,
\[
\boxed{\mathscr F_{\rm inf}=\frac{(1+z)^4}{c^2}
\left[H^2(\eta_{zz}-\eta_z^2)+\left(2H^2\frac{\chi'}{\chi}+HH'\right)\eta_z+\frac{HH'}{1+z}\right].}
\]
\(z\)-독립 angular offset \(\eta\mapsto\eta+a(n)\)는 *연속 함수 수준에서 정확히 소거된다.* R64 실제 finite estimator에 이 결론을 적용하려면 그 보정 함수가 source operator의 nuisance span에 포함되어야 한다. R71의 \(\mathscr F_{\rm inf}<0\)는 **강제로 둔 \(\mathcal H=H_{\rm ref}\)**, 현재 R64 distance polynomial, NEC의 삼중 가정이 맞지 않는다는 조건부 비교일 뿐 실제 NEC 위반이 아니다.

## 4. P3-T4: 일반 low-ℓ의 비선형 적색편이 응답
\(B=H_{\rm ref}\chi/c,\ D=1-B\eta_z>0\)이면 거리 정의로부터
\[
\ln(H_D/H_{\rm ref})=\eta-\ln(1-B\eta_z).
\]
만일 \(\sup|B\eta_z|<1\)라면 \(-\ln(1-B\eta_z)=\sum_{p\ge1}(B\eta_z)^p/p\)가 균등수렴하여, ell<=L signed radial derivative의 p차 곱은 ell<=pL의 고조화 성분을 생성한다. 이들은 독립 자료가 아니라 비선형 coordinate image이다. 국소 angular field \(\eta=\eta_0+d\cdot n+nSn\)의 2차 이미지에서
\[
\begin{aligned}
[\ln H_D]_{\ell3}
 &=B^2\left[(d_z\cdot n)(nS_z n)-\frac25(S_zd_z)\cdot n\right]+O((B\eta_z)^3),\\
[\ln H_D]_{\ell4}
 &=\frac{B^2}{2}\left[(nS_z n)^2-\frac47 n(S_z^2)_{\rm STF}n-\frac2{15}\mathrm{tr}(S_z^2)\right]+O((B\eta_z)^3).
\end{aligned}
\]
따라서 finite z에서 보이는 octupole·hexadecapole이 모두 별도 GR 자유도라는 주장은 성립하지 않는다. 반대로 관측된 higher ell만으로 정상계 shear를 확정할 수도 없다.

## 5. P3-T5: \(Q,\Pi,F,G_F\)를 실제 물리적 의미와 결합
- x: R64 동일 35,970 CF4 selected source에서 보존한 signed eta_lm(z), eta_z, eta_zz, source/method/full covariance; 각 \ell=2는 STF5로 저장하며 부호를 버리지 않는다.
- Q_D(z) = max(0,B(z) sup_n eta_z(z,n))는 현재 distance derivative의 **one-sided domain gate**. Q_D<1이면 그 모델의 전천 D>0를 보증하지만 local GR \(\mathcal H\)나 shear의 물리적 상한은 아니다. 다른 null/parameter precision Q_stat와 분리한다.
- Pi: R64 원래 fixed-C Gaussian probability law에 따른 조건부 tail만 존재한다. 실제 cosmic anisotropy, NEC 또는 tilted Bianchi family의 calibrated 물리 Pi는 현재 UNAVAILABLE.
- F: 실제 온전한 same-frame full-sky \(D>0\) 사건의 round-solid-angle 점유율 \(F_\Omega\)는 하나의 정의된 기하학적 F이다. 54개 저장 방향의 비율은 그 점유율이 아니다; 전천 모형으로 계산한 F=1도 물리적 신뢰 질량이 아니다. 거리에 대한 matched source inference가 불완전한 경우 F는 모델 조건부이다.
- G_F: 적색편이별 단순 F 변화나 \(\eta(z_2)-\eta(z_1)\)은 관측자/방출원 congruence와 selection/covariance transport가 검증되지 않았다면 물리적 \(G_F\)가 아니다. 그러한 입력이 없어 현재 UNAVAILABLE; signed depth G_x만 auxiliary.
- 보조 \(\chi(S_z)\)는 amplitude를 제거한 shape orbit coordinate로 유용하지만 네 의존 뷰와 별도의 Fisher 정보를 만들지 않는다.

## 6. 실제 R64 CF4 source readout과 새로운 조건부 계산
원본 R64 source: AUGMENTED_RESULT.json SHA256 c9a68a7e79de910185757acd43ca0e5a91e8d36a1c2a818a184804962de5160b; 35,970 selected groups, 68D mono_method+24 nuisance, same shared covariance. 기존 J3 mean 39/39 rank 회복은 보존하며, 이번에 새로운 independent source를 추가하지 않았다.

| 모형 | z=.08 전천 point \(D_{\min}\) | 54방향 중 joint95% \(D>0\) 하한 인증 | z=.08 정확한 tied \ell4 RMS in \(\ln H_D/H_{\rm ref}\) |
|---|---:|---:|---:|
| J1 | 0.9536635 | 54/54 | 0.00027116 |
| J2 | 1.0091092 | 54/54 | 0.00274961 |
| J3 | 1.1982267 | **0/54** | 0.00215664 |

J3는 source mean의 대수적 rank39/39, 그리고 그 점값의 전천 양의 거리미분 조건을 갖지만, same Gaussian joint confidence support로는 z=.08의 어떤 저장 방향에서도 denominator 양성을 인증하지 못한다. 이 대비가 현재 P3 관측자료의 중요한 *과학적 설명력*이다. 54방향은 실제 source들을 독립적으로 나눈 sky pixel이 아니라 R64 저장 evaluation geometry다.

정확한 nonlinear high-ell RMS는 112×192 Gaussian-sphere quadrature에서 원래 \ell<=2 eta/eta_z를 결정론적으로 사상한 것이다. J2/J3의 \(|B\eta_z|_{\max}\approx0.63,0.83\)에서는 formal Taylor convergence가 성립해도 quadratic approximate l4 RMS(0.00472/0.00485)가 exact(0.00275/0.00216)보다 상당히 크므로 finite-z에는 exact log가 낫다.

추가 reference \(\mathcal H=H_{\rm ref}\)를 강제한 NEC optical comparator는 z=.08에서 음의 focusing ratio가 J1 44/54, J2 49/54, J3 54/54개 방향이었다. 이 수치는 실제 null-energy 위반의 빈도, 검정 p 또는 sky solid-angle fraction이 아니다. 이미 고려한 PV/source/method/optical transfer/clock의 불일치를 가시화하는 **반증가능한 가정 검사**이다.

## 7. 물리적 일반성과 여섯 논문 / 일곱 결합의 유효범위
일반 Bianchi Lie \([e_i,e_j]=\epsilon_{ij\ell}N^{\ell k}e_k+a_i e_j-a_j e_i,\,N^{ij}a_j=0\)와 normal Einstein Gauss/Codazzi, 총 tilted matter \(T_{ab}\)를 물리적 optical source에 입력하면, Type I에 제한하지 않고 P3 T1/T2를 적용할 수 있다. 다만 frame conversion을 생략한 정상계 shear와 tilted 방출원의 광학적 redshift를 혼동해서는 안 된다.

여섯 논문 P1–P6과 기존 PHY-01..PHY-07의 각각에 대해 실제 물리 방정식, source 계약, 5뷰의 정의 가능 여부 및 다음 최소 검증을 APPLICATIONS.json에 제공했다. P3 중심으로 P1 signed tensor/마스크, P2 photon Ricci source, P4 observer boost/radio dipole, P5 general Lie/tilt, P6 covariant kinematics를 연결했다. 일곱 조합은 일곱 새로운 joint likelihood가 아니다.

## 8. 검산 및 논문화 판단
Wolfram의 R64 Sachs-redshift ODE 재유도, 별도의 R/R'/R'' 대수 구현에 의한 focusing ratio 일치(<5e-13), Milne/closed-FLRW 선행 반례와 독립 synthetic positive-focusing/H_D<0 광학 ODE, axial nonlinear P4 coefficient Gauss–Legendre 적분, R64 source 648 point-field identity, full-sphere STF global extremum, 기존 R64 테스트 28개 PASS를 확인했다.

**Claim status:** established/literature-supported = general GR Sachs/NEC and expansion multipoles; derived = optical NEC inequality + source-referenced calibration-invariant focusing comparator + tied high-ell; numerically checked = conditional R64 source geometry and toy ODE. Observational physical null and Bianchi family/tilt identification = unresolved. Publication readiness = NOT_READY_TO_SUBMIT. Native independent subagent review NOT_RUN (host has no native dispatcher); this report is not an independently refereed proof or astrophysical detection.

**Convergence decision:** R64의 실자료 방법별 충분성/보정 이슈를 먼저 해결한 뒤, 하나의 독립 physical \(\mathcal H\) 또는 제한된 tilted Einstein–Jacobi forward model로 P3-T1/T2를 실제 joint likelihood에 투영하는 것이 가장 실질적인 다음 경로다. 검정력 향상이 없어도 \(\mathcal H,H_D,H_W\)를 분리하고 higher ell의 근원을 해석하는 명확한 물리적 기여가 남는다.

## 9. R1–R10 단계 이행
R1 연구 질문·SSOT 및 물리적 성공조건 고정, R2 원자료/선행연구 대조, R3 정확한 frame과 5뷰 계약, R4 7개 후보 발산과 첫 축대칭 예제, R5 다섯 개 조건부 정리 유도, R6 반례·가정·차원·부호 감사, R7 실제 source numerical checks, R8 과학적 수렴과 stop condition, R9 여섯 논문·일곱 조합의 typed 계약, R10 현 산출물과 stage Git identity를 인계. 각 단계의 실제 변경은 독립 commit/push로 기록되며 해당 Git SHA는 PROVENANCE.json에 목록화했다.

원래 P1–P6 42 scientific node, R64 정본 자료, R69/R70 코드와 다른 연구자의 미추적 파일은 변경하거나 stage하지 않았다. 이 연구는 향후 coding 루프를 자동으로 실행하지 않는다.
