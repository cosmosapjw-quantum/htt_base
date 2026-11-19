# R76 · P6 Beyond-FLRW Covariant Kinematics / 물리적 5뷰: R1–R10 결과

작성일: 2026-11-19 KST. 기준 입력 HEAD: 829adadb73bce9ea2c26ea22833c64c4d3634add, branch research/r69-observable-physics-bridges-20261118. 범위는 여섯 번째 P6 논문의 **전체 이론 R1–R10**, 실제 R61 CF4·R69 Gaia source의 조건부 재계산, 정확한 6개 논문·7개 PHY 조합의 수리물리적 적용. 원래 42개 science DAG 노드나 외부 R49 tilted Bianchi branch·원자료를 바꾸지 않았다.

## 1. x의 정확한 물리적 타입과 5뷰 의미

Metric (-,+,+,+), u·u=-c², sourceward sky direction n. \(H=\Theta/3>0\), \(d=-A/(cH)\in\mathbb R^3\), \(S=\sigma/H\in\mathrm{STF}(3)\).
\[
\boxed{x_{\rm physical,vertex}=(d_3,S_5),\qquad h(n)=\mathfrak H(n)/H=1+d\cdot n+nSn.}
\]
물리적 전체 state \((H,d_3,S_5,\omega_3,\beta_3)\)는 15차원으로, 유도하려는 5뷰는 \(x,Q,\Pi,F,G_F\) **각각 종속된 역할**이며 5차원 벡터를 강제하지 않는다. 실제 R61 관측 \(x_{\rm CF4}=(V_{3}{\rm\ km/s},d_{H,3},\kappa_{5})\)는 선택된 35,970 CF4 그룹의 11D fixed-Gaussian working carrier, seven **dependent** source variants and common 95% 11D confidence ellipsoid. Zero calibration local-source approximation에서 \(d=d_H,S=\kappa\), 더 일반적으로 \(d=d_H-d_{\rm cal},S=\kappa-q_{\rm cal}\). Vorticity와 absolute H는 R61 retained32D에서 미식별.
Gaia 실제 \(x_{\rm Gaia}=(E1_3,B1_3,E2_5,B2_5)\)는 고유 E/B template 16D의 1,580,645 quality-source ICRS proper motion \(\mu{\rm as/yr}\) 및 공분산이며, local GR shear/rotation이 아니다. P4 radio boost, P5 Lie normal constraints, P3 finite-z distance H_D, P2 photon stress는 별도의 물리적 source/전방전달이 필요하다.

5뷰의 물리적 계약:
- \(Q_H=\max[0,-\min_{S^2}(d\cdot n+nSn)]\)는 실제 하나의 GR congruence에 대해 \(Q_H<1\iff h(n)>0\) for all n인 일방향 물리적 local-expansion positivity gauge. CF4 \(d_H,\kappa\)로 계산한 \(Q_H\)는 *conditional apparent-source* gauge. 물리적 \(Q_\beta=|\beta|\)와 관측 Gaia whitening \(Q_{\rm stat}\)는 구별한다.
- \(\Pi\)는 선언된 source-selected null의 tail. R61 fixed-C Gaussian nominal inference와 R69 Gaia formal/patch working Gaussian은 각각 조건부 통계법칙이며 관측 우주의 vorticity/shear p-value가 아니다. 두 자료의 물리적 joint \(\Pi\)를 계산하지 않는다.
- \(F_{H+}=\mathrm{area}\{n:h(n)>0\}/4\pi\)는 실제 공통 관측자 round sky 위의 **물리적 방향별 팽창 양성 영역**, \(F_{S+}=\mathrm{area}\{n:nSn>0\}/4\pi\)는 signed shear potential lobe. 관측 survey source fraction, 11D confidence ellipsoid parameter-volume F 및 Gaia apparent-E2 lobe는 서로 다른 유형이다.
- \(G_F(t_1,t_2)=F_{H+}(t_2)-F_{H+}(t_1)\)는 Einstein–Ricci congruence+observer frame에서 실제 **물리적 시간** 수송이 있을 때만 계산된다. R61 \(K(.08)-K(.02)\) 또는 Gaia north/south/redshift-bin 차이는 \(G_x\), not physical \(G_F\).

## 2. T1: Scalar quadrupole–tangent E2 same-physical-shear 정리

한 Fermi observer 주위의 실제 국소 Euclidean affine flow \(v(x)=B x\), \(B=H(I+S)+W\), \(Wn=\Omega\times n\)에서
\[
V(n)=H P_n S n+\Omega\times n,\quad
g(n)=nSn,\quad \frac{V_{E2}}{H}=\frac12\nabla_{S²}g.
\]
\[
\boxed{\frac{\langle |V_{E2}|^2\rangle}{H^2}
=\frac15\operatorname{tr}S^2
=\frac32\langle g^2\rangle,\qquad
\langle|\Omega\times n|^2\rangle=\frac23|\Omega|^2.}
\]
Scalar field g와 E2는 같은 signed STF5의 서로 다른 기하학적 실현이고, W는 B1만 생성하며 **독립 B2는 이 제한적인 local affine 모델에서 없다**. 이는 광학적 고적색편이 Gaia cosmic drift에서 B2가 결코 없다는 뜻도, B2가 vorticity라는 뜻도 아니다. 일반 Bianchi Lie \(N,a\), matter tilt와 Weyl/Sachs 광선 전달은 source 적색편이에서 새로운 E/B를 만들 수 있다.
독립 Wolfram exact integral for S=diag(s,-s,0): \(\langle g^2\rangle=4s²/15\), \(\langle|P_nSn|²\rangle=2s²/5\)로 확인. Python 네 random STF quadrature/gradient finite-difference도 일치.
일반 low-L Hodge 정리: \(\mu=\nabla\Phi+n\times\nabla\Psi\)이고 \(\langle|\nabla\Phi|²\rangle=(4\pi)^{-1}\sum_{\ell m}\ell(\ell+1)|\Phi_{\ell m}|²\). 동일 물리 가설이 \(\Phi_{\ell m}=\frac12g_{\ell m}\)를 강제할 때에만 \(\ell(\ell+1)/4\)의 scalar/vector power 비율을 얻는다. 이는 모든 finite-z에 자동 적용되는 Einstein 법칙이 아니다.

## 3. T2: CF4의 실제 11D 신뢰영역 전체를 인증하는 전천 양성 하한

선택한 원래 R61 모형의 11D 추정 \(\hat\theta=(V,d_H,\kappa)\), 공분산 C, 공통 simultaneous c11=χ²11(.95)=19.67513757라 두자. STF5 orthonormal basis E_A에서 \(w(n)=(0_3,n_3,nE_A n)\). 정확한 Frobenius STF projector로 \(\sum_A(nE_A n)^2=2/3\), \(\|w(n)\|²=5/3\). 계수 공분산 \(C_8=C_{11}[3:11,3:11]\)를 쓰면 전천의 어떤 방향과 **공동 타원체 내 모든 모수**에서도
\[
\boxed{
h_{\rm cal}(n)\ge 1-\|\hat d_H\|-\|\hat\kappa\|_{\rm op}
-\sqrt{\frac53c_{11}\lambda_{\max}(C_8)}
-\sqrt8\,\rho,
\quad \rho=\frac{\ln10}{5}\,m_{\rm mag}.
}
\]
여기서 \(\rho\)는 원래 R61 fullsky RMS calibration body \(|d_{\rm cal}|²/3+2\|q_{\rm cal}\|_F²/15\le\rho²\)에서 유도한다. Pointwise dual bound의 dipole3+STF5가 정확히 \(3+5=8\). 측정한 calibration posterior가 아니라 정해진 10 mmag sensitivity allowance.
실제 **동일 35,970개** CF4 source의 일곱 대안 모형에 계산한 10 mmag 하한:
| 변형 | 보수적 전천 lower bound | Point apparent Q_H |
| log | 0.82887 | 0.06171 |
| log_mono | 0.84614 | 0.04167 |
| log_mono_error | 0.85022 | 0.03823 |
| log_mono_galactic | **0.77588** | 0.03901 |
| log_mono_radial | 0.84919 | 0.03808 |
| log_split | 0.84186 | 0.03858 |
| log_survey | 0.85133 | 0.03603 |
따라서 선언한 각 95% working source-model confidence region과 calibration-body에서는 해당 *apparent local-vertex* \(h(n)\)가 전천에서 양수라고 충분조건으로 인증한다. 이 결론은 단순 유한 방향 pixel scan이 아니라 정확한 pointwise Gram 및 global operator bound에 근거한다. 일곱 변형은 같은 자료의 별도 nuisance laws이므로 전체 union을 새로운 95% independent evidence라 부르지 않으며, 물리적 H·σ를 직접 측정했다는 뜻도 아니다. 현재 point \(F_{H+}=1\), \(Q_H<1\)은 데이터 압축의 사용 가능한 수리적 정의역을 명확히 보여 준다.

## 4. T3: 실제 Gaia sky에서 E2/B2의 기하학적 직교성과 마스크 혼합

전천 round uniform sky에서 \(E_A=P_nE_A^{\rm STF}n\), \(B_A=n\times E_A^{\rm STF}n\)은 \(\langle E_A\cdot B_B\rangle=0\), 각각 Gram=δ_AB/5. 하지만 실제 Gaia의 16D per-source 가중 likelihood에서는 \(F=X^\top W X\)를 갖고, E1/B1 nuisance를 Schur로 제거한 E2/B2 Fisher의 cross-block는 일반적으로 0이 아니다.
R69의 실제 original 16×16 fitted formal C를 역산하고 nuisance를 profile해 canonical correlation 최대 특이값을 평가했다:
| Gaia 선택 | Source 수 | E2/B2 최대 canonical correlation |
| all | 1,614,173 | 0.080466 |
| quality | 1,580,645 | **0.080424** |
| quality_north | 862,532 | **0.881094** |
| quality_south | 718,113 | **0.878854** |
이는 sky/weight design 의존성을 직접 측정한 *관측 통계량의 기하학적 특성*이며, "전천 수학적 직교"와 "부분하늘 데이터에서의 조건부 상관"을 정밀하게 구분한다.
Quality E2 signed STF \(\chi=+.710893\), 이상적 전천의 **apparent E2 scalar potential** positive sky area \(F_{\Omega,E2}=.434485\). 이 F는 실제 GR 정상계 expanding-sky F가 아니다.
공분산 선택에 따라 nominal E2/B2 p가 크게 바뀐다:
| Working covariance | E2 Wald5 / nominal p | B2 Wald5 / nominal p |
| Per-star formal C | 117.5344 / 1.0443e-23 | 49.6965 / 1.5988e-9 |
| Exploratory 192-region patch C | 17.8577 / .003130 | 7.76694 / .169556 |
서로 다른 source error model이며 patch C가 천체물리적 LSS/스캐닝을 완전히 보정한 것은 아니다. **독립 vorticity/FLRW 위반 검출 주장은 하지 않는다.**

## 5. T4: 물리적 \(G_F\)는 Raychaudhuri와 동일 source-sky time transport에서

Raychaudhuri in metric (-,+,+,+), U·U=-c²:
\[
\dot\Theta=-\Theta²/3-\sigma_{ab}\sigma^{ab}
+\omega_{ab}\omega^{ab}-R_{ab}U^aU^b+\nabla_aA^a.
\]
그러나 \(\dot S=\dot\sigma/H-S\dot H/H\), \(\dot d=-\dot A/(cH)-d\dot H/H\)를 알기 위해서는 shear propagation, acceleration/matter evolution 및 sky frame transport까지 필요하다. 정칙한 \(h(t,n)=1+d(t)\cdot n+nS(t)n=0\) contour에서
\[
\boxed{\dot F_{H+}=\frac{1}{4\pi}
\oint_{\{h=0\}}\frac{\dot h}{|\nabla_{S^2}h|}\,d\ell.}
\]
d-only toy a(t)=|d|=1.5+.2t gives \(F(0)=5/6,\dot F(0)=-.04444444\), finite-difference agreement < 4e-12. a=1은 경계가 정칙한 닫힌 곡선이 아니므로 위 도함수를 무조건 대입하지 않는다. 실제 R61 K1이나 Gaia source-redshift 차이가 물리 시간 \(\dot S\)라는 주장은 성립하지 않는다.

## 6. T5: 실제 CF4/Gaia 공동 shear 검정이 가능한 조건

같은 물리 정상계·epoch의 s∈STF5에 대해 \(\hat\kappa=T_Cs+\epsilon_C\), \(\hat e=T_Gs+\epsilon_G\)라 하고, 실제 물리적 광학 source Jacobians \(T_C,T_G\)가 정규 정의되면 T_C invertible identified image에서 \(R=T_GT_C^{-1}\),
\[
\boxed{r=\hat e-R\hat\kappa,\quad
C_r=C_G+RC_CR^\top-RC_{CG}-C_{GC}R^\top.}
\]
고정/정규 Gaussian null에서만 \(r^\top C_r^+r\)의 rank-aware \(\Pi\)를 사용할 수 있고, 일반적으로 calibration/PV/reference spin과 cross-source covariance를 profile하거나 동시 표본화해야 한다. 원래 R61/R69에는 \(T_C,T_G,C_{CG}\)가 확보돼 있지 않아 이 공동 물리 검정은 **아직 실행 불가**다. 데이터를 얻을 수 있는 최소 다음 단계는 한 명시적인 observer+emitter Jacobi/position drift forward map을 두 source footprint에 적용하고 heldout source/redshift로 예측을 비교하는 것이다.

## 7. 여섯 논문과 일곱 결합

전체 typed 수리물리 계약은 APPLICATIONS.json에 P1–P6와 PHY-01..07 정확히 모두 존재한다. 각각 실제 signed x, physically justified Q, source/null Pi, sky/exposure/parameter F, time-transport GF, Einstein/kinetic/optical equation, 가능한 최소 검정, blocker를 포함한다. 일반 arbitrary low-\(\ell\) Hodge E/B 및 finite-redshift Sachs/Jacobi/observer boost는 P6의 제한적인 local affine 유도와 **명시적으로 다른** 물리 전달이다. 원래 결합들은 서로 독립적인 7 likelihood가 아니다.

## 8. 검산 및 주장 상한

독립 Wolfram 구면 적분, Python exact STF angular completeness/gradient/rotation 실험, 원 R58 CF4 source carrier hash 검증, R61 7×11D original point/C/tolerance 보존, 원 Gaia CRF3 raw FITS SHA256 e69cfff82f762c00d1d6a259c6d003fd20f805f3b1fcd4acc81d847c485120c0의 재해시, R69 16D formal/patch/north/south source identity, full 16D Schur/SVD 검산, finite GF toy가 성공했다. 기존 R61/R67/R69/R64/R65 관련 **117 regression tests PASS**. 원 자료를 다시 추론하는 production solver나 새 astrophysical null은 실행하지 않았다.
- established/literature-supported: covariant cosmography, Hodge harmonics, Raychaudhuri, affine shear position drift identity, Gaussian Schur/support.
- derived: 같은 물리 STF5의 scalar↔vector transfer 계약, R61 11D+calibration allsky robust certificate, Gaia masked-sky source alias and 5뷰 type inference.
- numerically checked: 위 7 CF4 variants, Gaia 4 samples, independent symbolic/finite tests and 117 regressions.
- unresolved: 물리적 source-frame H/σ/ω, finite-z Gaia/CF4 \(T_C,T_G\), correlated physical joint null, observed actual time GF, calibrated cosmological anisotropy significance.

R1–R10 이론 루프 수행은 단계별 Git commit/push를 원격으로 검증했으며 마지막 authoritative SHA는 R10 실제 원격 receipt에 둔다. Original six-paper science DAG 42 nodes and R49/R61/R69–R75 sources not mutated. Publication gate P6 remains NOT_READY_TO_SUBMIT.
