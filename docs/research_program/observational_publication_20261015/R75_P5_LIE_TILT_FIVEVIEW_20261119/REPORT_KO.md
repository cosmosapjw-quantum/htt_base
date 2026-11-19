# R75 · P5 일반 Bianchi Lie–Tilt × 물리적 5뷰: 종합 연구 보고서

**연구일:** 2026-11-19 (KST). **범위:** P5 다섯 번째 논문에 대한 physmath-research-loop 이론 **R1–R10 전부**. 원본 source는 R49의 2026-11-15 생산 추론 기록과 4,000개 동일 모델 posterior draw, R69의 일반 Lie–Codazzi 정리, R70 photon kinetic, R71 finite-z Sachs, R62 CF4 apparent, R66 CMB finite-band, R72/R74 radio source law. 여섯 논문과 일곱 조합의 명시적 적용은 APPLICATIONS.json. **과학적 지위:** 정확한 수학/유한 검증 및 기존 관측자료의 조건부 기하학적 재해석. 새로운 Bianchi 가족 검출이나 모든 유형의 완전한 Einstein–Boltzmann solver는 아니다.

## 1. P5에서 실제로 선택할 x와 물리적 필요 입력
\[
x=(\Sigma_{11},\Sigma_{22},\Sigma_{12},\Sigma_{13},\Sigma_{23}),\quad
\Sigma_{ij}=\sigma_{ij}/H\in\mathrm{STF}(3).
\]
관측자/방출원과 일치하는 정규직교 normal tetrad, 방향·시점·거리·소스 측도와 \(a_i,N^{ij},H,\rho_N,j_N,\pi_N\) 및 fluid tilt 벡터들을 별도 *state packet*에 보존한다. R49의 24D chain 첫 다섯 좌표는 실제 source-model \`sigma_AB_stf5\` Cartesian chart이며, source/normal-H mapping이 확정되지 않은 상태에서 직접 GR shear 관측량이라고 승격할 수 없다. R49 원래 8-probe posterior는 전파/선택법칙이 제한된 **TRANSFER_CONDITIONAL framework**, family-level posterior 식별 아님.

## 2. P5-T1: Lie algebra가 제한하는 정상계 물질 운동량의 rank
\[
C^k{}_{ij}=\epsilon_{ij\ell}N^{\ell k}+a_i\delta^k_j-a_j\delta^k_i,\quad N^Ta=0.
\]
부호 (-,+,+,+), c 유지, a,N 차원 m^{-1}, σ 차원 s^{-1}인 R69 normal-frame convention에서
\[
\mathscr L_i=-3\Sigma_{ij}A^j+\epsilon_{ijk}\Sigma^j{}_\ell\mathsf N^{\ell k}
=-3\Omega_N\frac{j_i^N}{\rho_N},\quad
A=ca/H,\quad\mathsf N=cN/H,\quad
\Omega_N=8\pi G\rho_N/(3c^2H^2).
\]
Class A에서 N eigenvalues \(n_1,n_2,n_3\)의 서로 다른 값 수에 따라 \(\mathrm{rank}\mathscr L=0,2,3\)이다 (각각 1,2,3 distinct). Class B에서 a=(a,0,0), N=diag(0,n2,n3)일 때 5→3 matrix
\[
M=\begin{pmatrix}-3a&0&0&0&n_3-n_2\\0&0&-3a&-n_3&0\\0&0&n_2&-3a&0\end{pmatrix},
\quad \Delta=9a^2+n_2n_3.
\]
\(\mathrm{rank}M=3\) for Δ≠0, but rank2 for Δ=0 (exceptional VI_-1/9 in \(h=a^2/(n_2n_3)\) convention). On that stratum \(n_2j^N_2+3a j^N_3=0\) is an exact necessary normal-momentum condition; three distinct normal velocity directions are not equally admissible. At least two shear dimensions are not determined by Codazzi even generically. R49 saved convention atlas gave instantaneous exemplar ranks: FLRW0, I0, II2, III3, IV3,V3, VI0 3, VIh3, VII0 2, VIIh3, VIII2, IX0, with special VI_-1/9 rank2; rank can vary *inside* a named family with N's instantaneous eigenspectrum. Exact determinant and SO3 covariance confirmed (max residual 8.34e−15). These known Lie constraints are a direct *identifiability geometry* for source-level statistics, not a novel cosmological classification theorem.

## 3. Q physics: DEC momentum cone and barotropic tilt inversion
\[
\boxed{Q_{\rm Lie}=\|\mathscr L(x)\|/(3\Omega_N)=|j_N|/\rho_N\le1\quad
\text{(Einstein + total dominant energy condition)}.}
\]
Q는 normal-frame 총 energy flux의 상대적인 크기이며, observed-significance가 아니다. \(\rho_N>0\) 및 실제 Lie/normal geometry가 없으면 Q 숫자는 미정이다. 하나의 positive-enthalpy perfect fluid \(p=w\epsilon,0\le w\le1\)에서
\[
Q_{\rm Lie}=\frac{(1+w)\beta}{1+w\beta^2},\qquad
\beta=\frac{2Q_{\rm Lie}}{1+w+\sqrt{(1+w)^2-4wQ_{\rm Lie}^2}}.
\]
Dust w=0에서 Q=β, radiation w=1/3에서 Q=4β/(3+β²). 실제 \(\beta=.001,.15,.6,.9\), \(w=0,1/3,1\)의 모든 inverse 계산은 3e−14 이내에서 원본을 재현했다. 하지만 다중 fluid 반대 방향 흐름이면 total j=0, Q=0이어도 각 fluid β≠0와 total \(\pi_N\ne0\) 가능하다. **Q는 총 flux compatibility이지 개별 tilt의 보편적 속도계가 아니다.**

추가 local normal direction expansion positivity에는 \(Q_H=-\lambda_{\min}\Sigma\)를 별도로 정의할 수 있다 (H>0, normal source/vertex). \(Q_H<1\)이면 모든 정규직교 방향의 local \(H_N(n)=H(1+n\Sigma n)>0\). 이는 유한 redshift 거리 미분 \(H_D\)의 positivity와 다르다.

## 4. F morphology와 같은 Q에서 달라지는 geometry
전천 round solid-angle measure를 고정하고 비영 Σ에서 \(F_\Omega=\mathrm{area}_{S²}\{n:n\Sigma n>0\}/4\pi\). \(\chi=\sqrt6\,\mathrm{tr}\Sigma^3/(\mathrm{tr}\Sigma^2)^{3/2}\)와 \(F_\Omega=\mathcal F(\chi)\)는 결정론적 관계이므로 독립 두 증거가 아니다.
- Type V, N=0, a≠0, **j_total=0** ⇒ Σa=0 ⇒ eigenvalues \((-\lambda,0,\lambda)\), \(\chi=0,F_\Omega=1/2\) for Σ≠0. R75 수치 예 x=(0,.3,0,0,.09)는 exact χ=0, numerical F=.499999987 (192-node quadrature endpoint error; analytic 1/2).
- 예외적 VI_-1/9, a=1,n2=3,n3=-3에서 x=(-2,0,0,0,1)는 Mx=0이지만 \(\chi=0.4647580015,F_\Omega\simeq0.44624631\). **같은 Q_Lie=0이라도 두 Lie stratum에서 허용되는 signed morphology가 다르다.**
- Type V 총 j≠0의 tilted 단일-dust 순간 제약 예 c=8πG=1,a=.1e3,σ=diag(-1/6,-1/6,1/3),ρ=1,j=.1e3은 χ=+1이고 Codazzi+Hamiltonian을 만족하도록 H² 선택 가능. 이는 전체 시간진화 해가 아니므로 검출/해 존재의 증명으로 올릴 수 없다.
- 관측 scale 없는 전체 Bianchi 초기자료 공간은 비콤팩트하므로 자연스러운 uniform F_state measure가 자동으로 존재하지 않는다. P5에서는 정확히 round-sky FΩ 또는 실제 posterior pushforward 측도만 이름/분모를 지정해 사용한다.

## 5. 실제 R49 기존 posterior의 형태 readout
\`/mnt/extdrive/workdir/r49_chains/r49_joint_posterior_chains.npz\` 원본 SHA256 \`4063be94180c5c8a28b43115ba70539a043cd6cb160c3e3251f5fb52c74c2c70\`을 production receipt와 직접 대조했고, 4,000개 동일 source thinned 24D draw에서 x Cartesian STF5를 복원했다. 실제 Gram \(G_{\rm cart}=[[2,1],[1,2]]\oplus2I_3\)와 \(\mathrm{tr}\Sigma²\)가 draw별 일치; Frobenius norm mean \(8.16529348269\times10^{-7}\)로 원래 R49 receipt를 재현했다. Posterior \(\chi\) 5/16/50/84/95 분위수는 \(-.589713,-.216537,+.358611,+.794554,+.940832\); \(F_\Omega\)는 \(.424604,.429982,.453408,.534400,.560776\). \(\chi>0\)와 \(F_\Omega<.5\)는 동일 72.925%로 **그대로 같은 source posterior 사실을 다른 방식으로 읽은 것**이다. 이는 independent observed Bianchi family preference나 cosmological anomaly p-value가 아니다.
원 R49 production의 Q_shear anchor는 UNAVAILABLE이며 PPC 문제는 심각하다: CMB χ²/dof≈2.015, Gaia≈47.035, CF4≈2.749 (원 receipt PPC p=0; finite simulation 수치로 exact probability 0 아님). 따라서 family-level \(\Pi\) admission 불가, 기존 morpho-compatibility equivalence class 수준에 한정한다.

## 6. P5에서 \(\Pi\)를 실제로 계산하려면
동일 epoch/normal tetrad에서 물리적으로 **독립** 측정한 \(\hat x\in\mathbb R^5\), \(\hat u=\widehat{j_N/\rho_N}\in\mathbb R^3\)와 그 공동 covariance C가 확보되면 고정 Lie/Ω source 하
\[
r=\hat u+(3\Omega_N)^{-1}M\hat x,\quad
C_r=D C D^\top,\quad D=[(3\Omega_N)^{-1}M,I_3].
\]
그때 matched fixed Gaussian null이면 \(T=r^\top C_r^+r\)의 적절한 rank-aware tail을 계산할 수 있다. 이 rank는 \(\operatorname{rank}C_r\)이며 Class B의 shear-to-flux map rank와 다를 수 있다. a,N,Ω의 측정 불확실성이 크면 그 joint nuisance/source Jacobian을 추가하거나 source-level posterior sampling으로 대체한다. 오직 x에서 j를 *Codazzi로 정의*하고 같은 식으로 만든 residual은 항등적으로 0이므로 독립 관측 검정이 아니다. 실제 R49에는 해당 정상계 독립 물질 flux 측정이 없어 **\(\Pi_{\rm Bianchi,family}\)는 미정**이다.

## 7. \(G_F\): 물리적 형상 진화, 경계와 단일 해의 조건
Geodesic homogeneous normal에서
\[
D_t\sigma+3H\sigma=D,\quad
D=\frac{8\pi G}{c^2}\pi_N-c^2{}^{(3)}R_{\rm STF},
\]
\[
\dot\chi=\frac{3\sqrt6}{I_2^{3/2}}
\left[\mathrm{tr}(\sigma^2D)-\frac{I_3}{I_2}\mathrm{tr}(\sigma D)\right],
\quad I_2=\mathrm{tr}\sigma^2,\ I_3=\mathrm{tr}\sigma^3.
\]
정상계의 round sky와 고정 물리적 source event의 sign zero-set이 정칙인 동안에는 \(\dot F_\Omega=(4\pi)^{-1}\oint_{\sigma:nn=0}\dot f/|\nabla_{S²}f|\,d\ell\). \(\chi=0\) 근처에서는 nodal saddle로 일반적인 delta method/coarea가 비정칙일 수 있으므로 정확한 sphere area 및 수송된 source bootstrap을 쓴다. Type V total j=0 for an entire interval ⇒ \(\chi=0,F_\Omega=1/2\)를 직접 제약으로 유지한다. 현재 R49 one-epoch posterior의 depth G_F summary는 그 모델의 conditional transport이며, 독립 관측 시간진화를 측정한 증거로 취급하지 않았다.

## 8. 6 papers와 7 physical combinations
\`APPLICATIONS.json\`에 P1–P6와 정확히 PHY-01..07 각각의 **구체 방정식, 원/source carrier, Q/Π/F/G_F 의미, 가능한 관측·검정, blocker**를 보존했다. P1 CF4 apparent STF, P2 photon stress/flux, P3 H_D/kinematic Hcal, P4 radio observer count, P5 normal Lie tilt, P6 Gaia covariant kinematics를 공동 Einstein/Boltzmann/Sachs forward map으로 연결하는 조건을 명시했으며, 이미 존재하는 서로 의존적인 source product를 독립 7개 증거로 취급하지 않았다.

## 9. 재현·근거 판정
\`verify_p5.py\`: arbitrary symmetric N/a Jacobi/Codazzi canonical symbolic identity, original R49 모든 Bianchi 예제+두 특별 alias/exceptional의 Lie rank, 40 random SO3 frame-equivariance residual≤8.34e-15, Type V/VI_-1/9/tilted dust/two-dust counterexamples, 15 barotropic tilt inversions, 정확한 full-sky area quadrature and 4k conditional posterior source hash checks. Wolfram에서 독립 2×2 예외 determinant \((−3a)^2+n_2 n_3\)를 대입해 원 주장과 차이가 0임을 확인. 기존 R49+R62+R69 targeted regression 60개 PASS. Early finite program bug는 1D/2D N indexing, 너무 엄격한 quadrature endpoint tolerance로 판별/수정했고 이론식의 결함과 구분하여 보존했다.
Evidence labels: established/literature-supported = Lie split, Codazzi, exceptional VI_-1/9, tilted stress and Einstein shear evolution; derived = source-specific x/Q/Π/F/G_F mathematical mapping and T1–T4 conditional implications; numerically checked = source atlas, exact/tangent tests and R49 conditional posterior pushforward; unresolved = independently calibrated family predictive null, physical normal rho/j and full nonlinear anisotropic Einstein–Boltzmann CMB/CF4 transfer; native independent subagent NOT_RUN; family-level astrophysical publication claim NOT_READY_TO_SUBMIT.

## 10. 수렴·다음 한정 작업
우선순위는 먼저 **한 Bianchi Lie stratum에서 실제 source-compatible normal \(\rho_N,j_N,\sigma\)와 independent source transfer를 확보하여** \(M\Sigma=-3\Omega_N j/\rho_N\)의 rank-aware joint constraint를 한 번 검정하는 것이다. Type V와 exceptional VI_-1/9의 서로 다른 zero-flux morphology는 좋은 물리적 판별 예제지만, 실제 관측자의 CMB/CF4/kinetic normal-frame map과 covariance를 통과하기 전에는 family-level 발견이 아니다. Physical Q 값과 GF time path를 임의로 가정하여 채우는 일을 금지한다.

**R1–R10** 모두 범위 내에서 수행하며 단계별 Git commit/push를 실제 원격 확인했다. 최종 remote SHA는 R10 실제 Git provider receipt가 authority이며 추정/기재하지 않는다. Original P1–P6 42-node science DAG, R49의 별도 worktree, 원 R49 4k chain, 기존 R69–R74 자료와 무관한 untracked 파일은 변경하지 않았다.
