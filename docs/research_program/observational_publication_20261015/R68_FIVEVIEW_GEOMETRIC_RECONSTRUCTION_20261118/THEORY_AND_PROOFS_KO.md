# R68: 5변수 방법론의 발산적 재구성 및 수리·물리의미론적 정초

기준: 2026-11-18; parent commit 8089721e9ba74d79dadbb53d3158a5f76e9f96bf. Convention (-,+,+,+), c, ħ, k_B 유지. 기존 R39/R42/R48/R54/R60–R67 연구의 증거상태를 보존한다. 새 cosmological anisotropy 검출, Bianchi 유형 posterior, 또는 새로운 일반 정보이론 정리를 주장하지 않는다.

## 1. 대상과 연구 방향

기존 다섯 출력 (x,Q,Π,F,G_F)을 다섯 독립 통계량이 아니라 **하나의 출처가 고정된 관측 실험에 종속된 다섯 역할**로 해석한다. 이를 위해 \(\mathcal E=(\Theta,\Psi,\mathcal Y,P_{\theta,\psi},T,M,C,\mathcal B)\)를 물리 상태, nuisance, 관측공간, likelihood, 광학·운동학 transfer, mask/selection 측정 연산자, 전체 공분산, 물리적 허용영역의 타입 묶음으로 정의한다.

| 역할 | 추천 정의 | 정의되지 않을 경우 |
|---|---|---|
| x | 부호·tensor rank·frame·epoch·parity/spin과 공동 law를 보존한 observable/physical carrier | 측정 불가능 state 성분은 UNAVAILABLE |
| Q | **물리적** convex feasible body의 gauge 또는 명시된 **통계적** reference body의 gauge | 물리적 ceiling 미확보시 PRIOR_CONDITIONAL/UNAVAILABLE |
| Π | 지정된 null/predictive/posterior 법칙에서 정의된 event tail | matched law/selection 없으면 UNCALIBRATED |
| F | 실제 finite measure μ, body K, event E를 명시한 occupancy μ(E∩K)/μ(K) | support ratio와 혼동 금지; 측도 없으면 UNAVAILABLE |
| G_F | 비교 가능한 depth/time별 물리적 F가 실제 transport·공통 law·측도를 가질 때의 gap | 하나의 CMB sky·release 차이에서는 NOT_APPLICABLE |

보조 진단 \(\mathcal I\) (identified set), \(h_\mathcal I(u)\) (support), \(G_x\) (tensor depth contrast), \(\kappa_{\varphi|\mathcal E}\) (target stability), \(\mathcal R\) (source/transfer qualification)는 추가로 둘 수 있으나 F 또는 G_F의 의미를 소급 변경하지 않는다. R42의 support-F 구현은 historical semantics, R66의 occupancy-F를 현재 정식 기준으로 구별한다.

발산적 경로는 (A) score 및 nuisance-orthogonality, (B) 부분식별과 약한 물리 방향, (C) physics-derived gauge, (D) SO(3)/Lorentz frame 궤도와 singular strata, (E) 미지축 nonregular null, (F) occupancy의 measure/naturality, (G) covariant time-depth transport, (H) 다중관측 실험설계, (I) physical mechanism/explanation graph의 아홉 경로다. 각 경로는 정보 증가, 정보 회복, 또는 설명력 향상 가운데 무엇을 증명하는지 구별한다.

## 2. 정리 I: 표현만 바꾸어 full-likelihood 정보를 늘릴 수 없다

정규 dominated model \(Y\sim P_\theta\)에 square-integrable score \(s_Y\)가 존재하고 parameter-independent deterministic statistic \(Z=f(Y)\)라 하자. 미분-적분 교환 등 regularity 아래 임의 bounded h에 대해
\[
\partial_\theta E_\theta h(Z)=E_\theta[h(Z)s_Y(Y)]
=E_\theta[h(Z)s_Z(Z)].
\]
따라서 \(s_Z(Z)=E[s_Y|Z]\). Total-variance identity를 적용하면
\[
\boxed{I_Y-I_Z=E[\mathrm{Cov}(s_Y|Z)]\succeq0.}
\]
모든 interest parameter 방향의 score가 Z-measurable일 때 Fisher 동등이다. 이는 Alsing–Wandelt score compression의 기초와 합치한다. **결론:** 다섯 뷰가 full likelihood를 능가할 수는 없다. 부호를 버린 scalar norm/선택된 하나의 축과 비교해 정보를 회복하는 것은 가능하다. 예: \(Y\sim N(\pm1,1)\)의 equal-prior hypothesis에서 signed Y로 Bayes 분류 정확도 \(\Phi(1)=0.8413447\), \(|Y|\)만 남기면 두 법칙이 동일하여 정확도 0.5.

## 3. 정리 II: 특정 물리량의 식별성과 안정도

정해진 선형/whitened 관측 \(y=A\theta\), 물리 target \(\varphi=L\theta\), unrestricted finite-dimensional state에 대해
\[
\boxed{L\theta\text{가 }A\theta\text{로 유일하게 결정됨}\iff\ker A\subseteq\ker L.}
\]
증명: 같은 관측을 주는 두 상태의 차는 \(\ker A\)에 속하며, L이 이를 소거할 때만 target이 같다. 이때 \(L=LA^+A\)이고 관측공간 \(\mathrm{ran}A\)에서 유일한 안정적 선형 복원은 \(LA^+y\)이며 optimal Euclidean Lipschitz 상수는
\[
\boxed{\kappa_{\varphi|A}=\|LA^+\|_{\rm op}}.
\]
조건이 실패하면 같은 관측에서 무제약 target 변동이 존재한다. 비선형 Jacobian 적용은 first-order/regular **진단**이지 일반적인 비선형 불가능 정리가 아니다. 반례 \(y=\theta^3\), \(\varphi=\theta\)는 \(\theta=0\)에서 관측 미분이 0이나 정확한 법칙은 단사다.

## 4. 정리 III: 공유 nuisance를 가진 다른 실험의 진짜 정보 증가

Gaussian \(y=J\theta+N\eta+\epsilon,\ C\succ0\)에서 whitening 뒤 nuisance column space의 projector를 제거하면
\[
F_{\rm eff}=J^\top\{C^{-1}-C^{-1}N(N^\top C^{-1}N)^+N^\top C^{-1}\}J.
\]
이는 Schur/orthogonal nuisance score의 직접 결과다. 예:
\(y_1=\theta+\eta+\epsilon_1\),
\(y_2=\theta-\eta+\epsilon_2\),
\(\epsilon_i\sim N(0,1)\).
단일 관측의 \(\theta\) 정보는 자유 nuisance로 0이지만 **동일한** \(\eta\)를 공유하는 두 관측의 합/2는 \(\theta\)를 분산1/2로 추정하여 \(F_{\rm eff}=2\). 별개의 \(\eta_1,\eta_2\)면 그 이득은 사라진다. 이것은 새 관측 **응답**의 정보이지 5뷰 재표현의 정보가 아니다. R67 CF4 같은 그룹의 공통거리 소거가 관련 실제 사례다.

## 5. 정리 IV: STF(3) SO(3) orbit 불변량과 비정규 층

실대칭 trace-free tensor \(S\mapsto RSR^\top\), \(R\in SO(3)\)에서
\[
I_2=\mathrm{tr}(S^2),\quad I_3=\mathrm{tr}(S^3),\quad
\chi=\frac{\sqrt6 I_3}{I_2^{3/2}}\ (S\ne0).
\]
특성다항식은 \(\lambda^3-I_2\lambda/2-I_3/3\)이므로 \((I_2,I_3)\)는 unordered eigenvalues 및 SO(3) orbit를 완전히 결정한다. Spectral theorem에서 고유기저가 O(3)로만 맞아도 고유벡터 하나의 부호를 바꾸어 SO(3) 변환을 구성할 수 있다.
\[
\Delta=\frac12I_2^3-3I_3^2
=\prod_{i<j}(\lambda_i-\lambda_j)^2\ge0.
\]
이 항등식은 monic depressed cubic의 discriminant \(-4p^3-27q^2\)에 \(p=-I_2/2,q=-I_3/3\)을 넣으면 얻는다. \(\Delta=0\)은 반복 고유값, \(S\ne0\)에서 \(|\chi|=1\)은 축대칭이다. Generic orbit 차원3, 축대칭 orbit 차원2, 원점 orbit 차원0. 고유축의 불연속성은 실제 층화된 quotient space의 문제이므로 특정 eigenvector를 임의로 continuity-정의하지 않는다.

SO(3) spectral 분해의 infinitesimal offdiagonal은 \(\delta S_{ij}=(\lambda_j-\lambda_i)\Omega_{ij}\). 따라서 \(dS\)의 고유값·Haar-angle 표현에는 \(\prod_{i<j}|\lambda_i-\lambda_j|\) Jacobian이 존재한다. Tensor 5성분 균등 prior와 unordered eigenvalues 균등 prior는 **같은 측도가 아니다**. 이 차이를 F와 Bayesian evidence에 반드시 표시해야 한다.

## 6. 정리 V: radiation positivity body의 물리적 Q

비음수 복사 angular intensity \(I(n)\)에서
\[
P=\frac{\int I(n)\,nn^\top\,d\Omega}{\int I(n)\,d\Omega},\quad
S=\pi/\rho=P-I/3
\]
이면 \(P\succeq0,\ \mathrm{tr}P=1\).
\[
\mathcal K_{\rm rad}=\{S=S^\top,\mathrm{tr}S=0,I/3+S\succeq0\}.
\]
역으로 임의 PSD trace-one P의 spectral decomposition을 \(\pm\) 고유벡터 방향에 비음수 가중한 radiation angular measure로 구현할 수 있으므로 이는 비음수 intensity moment의 정확한 폐포다. 모든 smooth blackbody cosmological history를 얻었다는 뜻은 아니다.

Minkowski gauge \(Q_{\rm rad}(S)=\inf\{t>0:S\in tK_{\rm rad}\}\)에서 \(I/3+S/t\succeq0\iff t\ge-3\lambda_{\min}(S)\)이므로
\[
\boxed{Q_{\rm rad}(S)=\max(0,-3\lambda_{\min}(S)).}
\]
\(Q_{\rm rad}\le1\)은 이 moment의 정확한 물리적 positivity 범위다. 이것은 **비대칭 gauge**이며 norm이 아니다. \(S=\mathrm{diag}(2/3,-1/3,-1/3)\)일 때 \(Q(S)=1,\ Q(-S)=2\). 같은 Frobenius norm에서 다른 physical admissibility margin을 보여주는 설명력 향상이다. 이 gauge는 공간 rotation에는 invariant하나 일반 Lorentz boost 아래 photon stress가 불변이라는 뜻은 아니다.

## 7. 정리 VI: occupancy의 좌표 불변성과 영상 event의 위험

\(0<\mu(K)<\infty\)이고 \(F_{\mu,K}(E)=\mu(E\cap K)/\mu(K)\)라 하자. 역변환도 measurable인 가역 변환(bimeasurable isomorphism) T에서 \(E'=TE,K'=TK,\mu'=T_*\mu\)를 같이 변환하면 pushforward 정의로 \(F_{\mu',K'}(E')=F_{\mu,K}(E)\). 단 **측도도 전송**해야 한다.

비단사 T일 때 E가 fiber-saturated하지 않으면 영상 사건 TE는 다른 의미를 가질 수 있다. 정확한 유한 반례: K={0,1}, 균등 μ, E={0}, T(0)=T(1)=0. 원래 \(F=1/2\)이나 naive image ratio는1이다. Scalar \(x_c\)로 압축하거나 SO(3) orbit quotient로 이동해 동일 occupancy라고 주장하려면 event semantics의 보존 또는 조건부 measure를 증명해야 한다. Support function \(h_\mathcal I\)는 유용한 부속 진단이나 **원래 F가 아니다**.

## 8. 정리 VII: 프레임 공변 수송과 cross-depth covariance

같은 물리적 타입을 가진 두 심도 state \(x_i,x_j\)에 실제 transport T를 지정한 뒤에만 \(\Delta_{ji}=x_j-Tx_i\)를 정의한다. 그 정확한 covariance는
\[
\boxed{C_\Delta=C_{jj}+TC_{ii}T^\top-TC_{ij}-C_{ji}T^\top.}
\]
\(\Delta=[-T,I](x_i,x_j)\)의 공동 covariance 선형 변환으로 증명된다. 동일 sky·중첩 shell의 \(C_{ij}\)를 0으로 놓으면 일반적으로 오차를 잘못 센다.

시간에 따라 바뀌는 triad에서 \(S'=RSR^\top\), \(\Omega=\dot R R^\top\)라면 \(\dot S'=R\dot SR^\top+[\Omega,S']\). 따라서 공변 derivative
\(D_t S'=\dot S'-[\Omega,S']=R\dot SR^\top\).
원시 eigenframe rotation은 물리적 vorticity/tilt와 다르다. 실제 spacetime에서는 Fermi/parallel tetrad connection과 source/observer congruence를 지정해야 한다. \(G_x\) tensor contrast는 부속 진단이며, 물리적으로 비교 가능한 occupancy F가 없는 상태에서 이를 원래 \(G_F\)라고 바꾸어 부르지 않는다.

## 9. 정리 VIII: 미지 축의 비정규 Gaussian STF 검정

White \(z\sim N_5(0,I_5)\), \(Z=\sum_A z_AE_A\)와 축대칭 평균
\(\mu=a B(n)\), \(a\in\mathbb R\), \(n\in S^2\),
\(B(n)=\sqrt{3/2}(nn^\top-I/3)\), \(\|B\|_F=1\)을 사용하자.
고정 n에서 Gaussian mean fit의 likelihood improvement는
\(\langle Z,B(n)\rangle^2\)로 \(\chi_1^2\) null을 갖는다. 그러나 방향 n까지 최적화하면 Rayleigh–Ritz extremal theorem에 따라
\[
\boxed{T(z)=\sup_{n,a}\Delta\chi^2
=\frac32\max_i|\lambda_i(Z)|^2.}
\]
진폭 a=0에서는 축 n이 정의되지 않는다. 일반 Wilks \(\chi_1^2\)가 아니라 eigenvalue extremal law를 써야 한다. Seed20261118, isotropic white STF5 toy null 85,000개에서 95% quantile 약9.86782; \(\chi_1^2(0.95)=3.84146\) 임계값 적용 시 실제 false-rejection 약0.49653, \(\chi_5^2(0.95)=11.0705\)에서는 약0.0300이었다. 실제 Commander mask/foreground/selection null은 전혀 포함되지 않은 **toy mathematical warning**이다. Drton (2009) 및 Davies/Chernoff의 singular-test 선행문헌과 양립하며 새로운 일반 LRT 정리가 아니다.

## 10. 일곱 연구 주제별 특화

| 연구축 | x와 Q | Π 특화 | F 및 G_F |
|---|---|---|---|
| P1 tensorized 기본 | full signed data, physical \(\theta\), identified set; 실제 bounds가 있는 Q만 | score/predictive/null의 law 분리 | 점유율에 body+measure 필수, 물리 depth에만 G_F |
| P2 low-ell CMB | signed \(a_{\ell m}\)와 \(\pi_\gamma/\rho\), radiation positivity Q와 shape χ | 동일 sky matched Commander null; 축 최적화 nonregular | 물리 순간응력 body에 occupancy 가능, 한 sky에서는 G_F=NA |
| radio dipole | source count vector, flux bins, mask, membership; selection body Q | clustering/LSS, ring-conditional, paired source covariance | flux threshold 변화는 cosmic depth가 아님 |
| P6 kinematics | \(\sigma/H,\omega/H,A/(cH),\beta\)의 frame-specific carrier; energy/causality bounds | 실제 CF4/Gaia likelihood & calibration | F는 물리 측도 있을 때만, covariant time/path transport |
| P5 Bianchi | \(a_i,n_{ij}\), intrinsic curvature, tilt, STF; Jacobi/Codazzi/Hamiltonian | physical optical/polarized transfer 없으면 family likelihood UNAVAILABLE, singular strata 유의도 보수 | 무한 군 공간의 uniform occupancy 자동 생성 금지 |
| P3 directional Hubble | \(\eta(z,n),H_D,q_D\)와 상대 error, physical positivity | source/method selection & PV covariance | matched redshift/window만 G_F; derivative domain 명시 |
| P4 boost vs tilt | observer/radiation/matter-relative speeds, Gaia E1는 acceleration, B1는 frame spin | count/CMB/Gaia/remote-kSZ matched null 분리 | 실제 shared-frame history 없으면 G_F=NA |

## 11. 이미 계산된 R66 Commander 상태에 새 기하 읽기 적용

R66 원본 OBSERVABLES.json의 carrier SHA256은 807b8eb391b6d150596ab431885f4b720bcafedd52fffdfe61c6db132661cc48. 그 자료가 실제로 저장한 restored \(\ell\le6\) temperature-family normalized radiation moment에서 \(\pi/\rho\) STF5를 재구성했으며 추가 CMB fit은 수행하지 않았다.

| 자료 | \(\|S\|_F\) | \(Q_{\rm rad}\) | signed \(\chi\) |
|---|---:|---:|---:|
| PR3 | \(4.91816475\,10^{-6}\) | \(1.16370051\,10^{-5}\) | -0.70744858 |
| PR4 | \(5.28497883\,10^{-6}\) | \(1.24852860\,10^{-5}\) | -0.69503411 |

이들은 **선언한 finite-band/released-map 모형**에서 얻은 물리적으로 해석 가능한 새 읽기 방식이다. 전체 실제 하늘의 stress 검출이나 Bianchi type assignment가 아니며, \(Q_{\rm rad}\ll1\)은 positivity feasible body 내부라는 뜻이지 ΛCDM probability가 아니다. Source data의 모델 한계는 R66에서 상속한다.

## 12. 검증·신규성·후속 판단

- 기존 source 재사용: R39/R42/R48/R54/R61/R66의 관련 원천 파일과 status. 새로운 일반 score compression, nuisance projection, SO(3) spectral theorem, Minkowski gauge, Gaussian nonregular testing의 최초성 주장 금지.
- 구현: scripts/r68/fiveview_geometry.py, tests/test_r68_fiveview_geometry.py, R68_NUMERICAL_CHECKS.json. 원 R66 actual retained tensor를 읽고 별도 85,000 toy white-STF null을 계산한다. 모든 결과는 input law가 타입으로 구분됨.
- 대체 독립 sanity suite: fiveview_reconstruction_checks.py/json은 12개 toy/symbolic-numeric 실험; 이들 숫자를 실제 observational p-value로 쓰지 않는다.
- 새로운 검정력은 full likelihood를 넘는 것이 아니라 scalar norm/axis-only ablation 대비 **loss recovery** 또는 실제 물리적으로 다른 관측을 추가해 nuisance nullspace를 제거할 때에만 주장할 수 있다.
- 물리적 설명력은 positivity Q, signed orbit invariants, tensor frame transport, 목표별 identification modulus, nonregular Π로 강화할 수 있다.
- 유한한 다음 실험: R66 Commander source-matched T MC가 준비되면 fixed axis vs scanned axis, full signed STF vs power/axis-only의 동일-data coverage를 대조하거나, R64/R67 CF4 같은 group original에서 physically qualified source-calibration likelihood 아래 target modulus 및 F measure sensitivity를 검정. 실패하면 방법론 읽기 체계로 보존하고 독립 우월성 주장을 종결한다.
- 상태: theoretical constructions derived; toy numerically checked; R66 readout inherited/implementation-verified in declared finite band; new cosmological science claim UNRESOLVED. **기본 6편 제출 acceptance를 이 파일로 변경하지 않는다.**


## 13. 수치 구현의 정리-정확성 경계 및 독립 심사

정리들은 정확한 실수 연산에 관한 derived 명제이다. Float64 구현은 논리적으로 구별한다. 한 번의 독립 read-only 심사는 최초 NEEDS_REPAIR를 보고했고, 두 high-impact 수치 오류와 두 low-impact source/scale 사안을 한 번의 범위 고정 수정에서 처리했다.

1. Nuisance 단위 스케일: 비영 nuisance 열이 10^-12라는 이유로 실제 column space가 0이면 안 된다. Cholesky whitening 후 각 비영 열을 정규화하여 SVD rank를 계산하고 수치 경계에서는 fail closed한다. 원 반례 J=C=1, N=1 및 N=10^-12 양쪽의 projected Fisher가 0임을 검사했다.
2. 미세한 target leakage: 정확한 kernel 포함을 근사 0으로 대체하여 identified=True를 반환하지 않는다. True/False/None 세 상태로 나누고 작은 미확정 leakage는 NUMERICALLY_AMBIGUOUS_NULL_LEAKAGE, modulus 미인증으로 기록한다. 원 반례 A=(1,0), L=(0,10^-12)가 성공으로 승격되지 않는다.
3. 극소 STF: 입력 유효성은 자기 component scale 기준의 상대 오차로 검사하고 signed chi는 정규화한 텐서에서 계산한다. scale=10^-26인 비영 axial 텐서도 chi=1을 유지한다. 원래 I2/I3/discriminant의 absolute float64 표현에는 underflow 제한이 남아 있다.
4. Source identity: R66 OBSERVABLES.json의 전체 SHA256 6d9c3f11a23995565dca25fe8ae02ef1ad79b3bc3f8ddf99f3c8c0a497b39d01을 직접 검사한다. Embedded carrier SHA는 별개이며 둘을 함께 검사한다. 이는 현재 tracked 분석 JSON의 byte identity를 인증할 뿐 R66 FITS upstream source의 end-to-end 검증은 아니다.

수정 후 focused 14 tests passed. 최초 독립 reviewer의 판정 NEEDS_REPAIR는 남기며, 한정 수정 이후에는 parent-owned targeted regression PASS만 주장한다. 두 번째 독립 심사 PASS와 실제 물리적 출판가능성을 주장하지 않는다. R68은 방법론 연구이고 기존 P1–P6 submission state는 변경하지 않는다.
