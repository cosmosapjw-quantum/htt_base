# MES R4 — 공간 미분의 대수적 closure와 거리 보상 관측량

2026-09-27 KST · 이론 연구 결과 v2

## 0. 결과와 범위

이번 루프는 R3가 남긴 “실제 사용할 수 있는 derivative/source allowance”를 두 방향에서 구체화한다. (i) 공간균질 branch에서는 Lie 구조상수와 한 시점의 공간 metric으로 공간 미분을 유한차원 행렬로 계산한다. (ii) 일반 근거리 광학 branch에서는 세 거리의 관측을 조합해 공통 고유속도와 첫 거리 보정항을 제거하고 나머지의 엄밀한 상한을 얻는다. 이 두 branch는 서로 다른 조건부 결과이며 하나의 일반 우주론 가정으로 합치지 않는다.

**실제 관측으로 MES 기준보다 좁은 전단/가속도 구간을 얻는 R3의 empirical 목표는 이번에도 달성하지 않았다.** 이를 계획 완료로 대체하지 않는다. 원논문의 실제 통계 규모, 거리 정의, 기준틀 조건과 미확인 잔차를 대조하여 그 목표가 현재 입력에서 닫히지 않는 이유를 특정했다. 새로 완료한 것은 조건부 정리, 재현 가능한 CAS 및 실제 자료가 통과해야 할 수치 조건이다. 일반 비선형 MES 정리, 카탈로그 fit, observed percentage, 생산 코드 변경은 없다.

이 연구의 원래 목표는 유지한다. 같은 관측/전제 아래의 허용 경계로 운동학 tensor를 정규화하여 유형 간 비교를 만들되 morphology와 부호를 보존한다. θ,σ,ω,A,β 전체를 대상으로 삼지만 관측 또는 가정으로 닫힌 성분만 값을 낸다. normal homogeneous branch의 ω=0을 일반 와도에 대한 관측 상한으로 쓰지 않는다.

## 1. 입력과 컨벤션

SSOT는 로컬 `MES_R3_OBSERVABLE_JET_AND_SOURCE_BOUNDS_20260927_KO.md`이다. 원 repo 자료는 R3가 고정한 commit `85e261f49c9df9389946eef74d80c1ccd0509816`에서 읽었다. 현재 main 전체를 감사한 것은 아니다.

- 55쪽 보고서 대응 markdown, blob `4f4dcf050e2d71b79a6a7bcc739d3045f23bfe62`: 도입·운동학·§6의 조건부 기준과 의미를 읽음. 첨부 PDF와 byte identity는 주장하지 않음.
- R7 THEORY, blob `166e38093a4eed7a4bd4f59848c8eecbc96b6e3c`: 공간/시간 derivative를 가진 전단식과 tensor norm 재사용.
- R9 THEORY, blob `53f39fa80ec6fb65cb0be6bfa1fc4b3fe35c71e6`: 공통 nuisance, confidence image, 동일 상태의 분모를 재사용.
- Astra 연구 하네스 v4.0.0을 실제 읽고 적용. ZIP SHA-256 `dae76c90f2e5d691bcdd595dadbe470bacacba3bb2a036ff9788ffe7d3bfabb7`. 사용자가 채택한 하네스 선택을 계속하며 모델 변경·ultra 설정 인증은 하지 않는다.

계량은 (-,+,+,+), U·U=-c², dot=U·∇, h=g+UU/c², H=Θ/3, a=A/c. rate Θ,σ,ω,a의 단위는 s⁻¹이고 β는 무차원이다. 공간 미분은 \(\bar D=cD\). 광원 방향은 n, 광자 전파 방향은 e=-n이다. \(\Omega_{ab}=h_a{}^ch_b{}^d\nabla_{[c}U_{d]}\), \(\omega^a=\epsilon^{abc}\Omega_{bc}/2\), \(\|\Omega\|_F=\sqrt2|\omega|\). R7/55쪽 보고서의 반대 index-order 와도와 부호를 바꾸어 연결한다.

## 2. 먼저 고정할 부족 정보: 작은 sky amplitude는 derivative bound가 아니다

MES 원문의 B2–B3, Eqs. (43)–(45)는 시간·공간 미분에 대한 별도 가정이다. characteristic-scale 대입 역시 C1–C2 가정이다. [MES 1995, pp.8–10](https://arxiv.org/pdf/astro-ph/9501016).

이를 단순 주장으로 남기지 않기 위해 Minkowski 배경의 정확한 collisionless witness를 쓴다. 광자 방향 e와 \(0<\epsilon<1\), 파수 k에 대해

\[
f(t,x,E,e)=f_0(E)\{1+\epsilon\sin[k(x_1-ce_1t)]\}.
\tag{1}
\]

\((\partial_t+ce^i\partial_i)f=0\)이고 f는 양수다. 관측 사건 t=x=0에서 모든 방향은 정확히 f0(E)를 보므로 모든 비등방 multipole가 0이다. 그러나 \(\partial_1\rho/\rho_0=\epsilon k\). k를 늘리면 동일한 한 사건의 sky를 유지하면서 gradient는 제한 없이 커진다. finite-dimensional angular truncation으로 이 공간 파수를 제한할 수 없다.

이것은 **고정 Minkowski 배경의 test radiation 역문제 반례**다. expanding self-consistent Einstein–radiation 해의 반례, MES 가정을 만족하는 해의 반례, Planckian-temperature closure의 반례로 확대하지 않는다. 필요한 결론은 한 sky의 amplitude만으로 spacetime derivative 상한을 만들 수 없다는 것이다. 다음 절은 이 부족 정보를 공간균질성으로 실제 보충한다.

## 3. Lie algebra + metric으로 공간 미분을 닫는 정리

### 3.1 입력과 연결

한 공간균질 slice에서 invariant frame X_i가 \([X_i,X_j]=C^k{}_{ij}X_k\)를 만족하고, metric h_ij가 같은 frame에서 공간적으로 일정하며 양의 정부호라고 하자. C는 반대칭과 Jacobi를 만족해야 한다. E_a=L_a{}^i X_i를 직교 frame으로 택하면

\[
LhL^T=I,\qquad
[E_a,E_b]=f^c{}_{ab}E_c,
\quad f^c{}_{ab}=L_a{}^iL_b{}^j C^k{}_{ij}(L^{-1})_k{}^c.
\tag{2}
\]

단면 Levi-Civita 연결 \(\nabla^{(3)}_{E_a}E_b=\gamma^c{}_{ab}E_c\)은 Koszul 공식으로

\[
2\gamma^c{}_{ab}=f^c{}_{ab}-f^a{}_{bc}+f^b{}_{ca}.
\tag{3}
\]

지표 위치는 E_a가 미분 방향, b가 미분되는 frame index이다. \(\gamma_a\)를 row c, column b의 행렬로 두면 \(\gamma_a^T=-\gamma_a\), \(\gamma^c{}_{ab}-\gamma^c{}_{ba}=f^c{}_{ab}\). 이는 metric compatibility와 zero torsion이다. Covariant slot의 성분 작용에는 이 행렬의 transpose가 들어가며 Eq.(4)의 지표식이 권위이다. 특정 Bianchi 이름이나 분류표는 필요하지 않다.

### 3.2 tensor derivative operator

공간균질 covariant rank-r tensor T의 E-frame 성분은 공간 미분이 0이다. 따라서

\[
(\bar D_a T)_{b_1\ldots b_r}
=-c\sum_{j=1}^r\gamma^d{}_{ab_j}
 T_{b_1\ldots d\ldots b_r}
\equiv (\mathsf M_r(C,h)T)_{a b_1\ldots b_r}.
\tag{4}
\]

이 식은 단면의 tensor 미분에 대한 정확한 항등식이다. 공간균질 **hypersurface-normal congruence**의 완전 공간투영 D와 일치한다. tensor의 rank는 그대로 추적하며, STF1/2/3 orthonormal basis를 쓰면 \(\mathsf M_r\)는 각각 유한 행렬이다. sharp 상수는 그 행렬의 최대 singular value이고, covariance 대신 실제 tensor metric으로 adjoint를 만든다.

\(G^2=\sum_a\|\gamma_a\|_{op}^2\)라 두면

\[
\boxed{\|\bar DT\|_F\le crG\|T\|_F},\qquad
\boxed{\|\bar D^2T\|_F\le c^2r(r+1)G^2\|T\|_F}.
\tag{5}
\]

증명: 고정 a에서 r개의 slot 작용 각각의 norm은 \(\|\gamma_a\|_{op}\|T\|\) 이하이다. 합에 triangle inequality를 적용하고 a에 대해 제곱합한다. 두 번째에는 \(\bar DT\)가 rank r+1인 homogeneous tensor임을 이용한다. **이미 생긴 derivative index에도 연결이 작용한다.** 그 slot을 빠뜨리고 같은 r-rank 연산자를 두 번 곱하면 일반적으로 틀린다. 이 coarse 상수는 안전한 상한이며 최적이라고 주장하지 않는다.

고정 C에 대해 h→λ²h이면 f,γ,G→λ⁻¹(f,γ,G). 따라서 **C만으로 dimensional 상한은 정해지지 않는다.** h의 uncertainty가 λ_min(h)>0인 compact domain에 묶이면 \(\sup_h\|\mathsf M_r(C,h)\|\)는 유한하다. 한 geometry에 대한 ellipsoid를 모든 h에 대한 동일 ellipsoid로 치환하지 않고 joint domain의 image/union을 사용한다.

### 3.3 MES 전단 잔차의 구체화

R3의 일차식에 explicit higher-order remainder를 넣으면

\[
\sigma=-\dot\vartheta_2-\mathrm{STF}(\bar D\vartheta_1)
-\frac37\operatorname{div}_{\bar D}\vartheta_3+\eta_2+R_\sigma.
\tag{6}
\]

따라서 expanding branch \(\Theta>0\)에서 \(\chi=cG/\Theta\), \(\epsilon_r\ge\|\vartheta_r\|\)를 사용하면

\[
\frac{\|\sigma\|}{\Theta}\le
\frac{\|\dot\vartheta_2\|}{\Theta}
+\chi\epsilon_1+\frac{9\sqrt3}{7}\chi\epsilon_3
+\frac{\|\eta_2\|+\|R_\sigma\|}{\Theta}.
\tag{7}
\]

\(\|\operatorname{div}T_3\|\le\sqrt3\|\bar DT_3\|\)만을 써서 얻은 충분상한이다. 더 유용한 morphology는 Eq.(4)의 실제 행렬을 Eq.(6)에 넣어 유지한다. 시간 quadrupole derivative와 source/remainder는 여전히 별도 입력이다. 같은 multipole 방정식으로 이 항들을 역산하고 다시 전단을 ‘독립 측정’했다고 하지 않는다.

이 branch는 normal congruence의 ω=0을 구조적으로 전제한다. homogeneous lapse N(t)이면 A=0이다. 일반 tilted 물질 흐름의 와도·가속도를 이 0으로 대체하지 않는다. 또한 Eq.(4)의 정확성은 Eq.(6)의 유한 비등방 고차항까지 정확하게 만들지 않는다. Rσ가 없으면 일차 truncated-model 결과로 남긴다.

## 4. tilt를 유지하는 동일시점 jet 경로

일반 homogeneous tilted 흐름에는 단면 metric만으로 충분하지 않다. 4차원 직교 tetrad E_A, \(\eta_{AB}=\operatorname{diag}(-1,1,1,1)\), \(\nabla_{E_A}E_B=\Gamma^C{}_{AB}E_C\)를 주고

\[
u^A=\gamma_\beta(1,\beta^i),\qquad U^A=cu^A,
\quad \gamma_\beta=(1-|\beta|^2)^{-1/2}
\tag{8}
\]

로 둔다. \(F_{AB}=\nabla_{E_A}U_B\)는

\[
F_{AB}=c(E_Au_B-\Gamma^C{}_{AB}u_C).
\tag{9}
\]

metric과 extrinsic curvature K, lapse/triad gauge로 Γ를 구성하고 \(\beta,E_0\beta\)를 주면, homogeneous 성분의 \(E_i\beta=0\)이므로 Eq.(9)는 한 시점의 대수계산이다. 그 뒤

\[
\Theta=\eta^{AB}F_{AB},\quad A_B=U^AF_{AB},\quad
\sigma_{AB}=h_A{}^Ch_B{}^DF_{(CD)}-\Theta h_{AB}/3,
\quad \Omega_{AB}=h_A{}^Ch_B{}^DF_{[CD]}.
\tag{10}
\]

이 방식은 모든 운동학 성분을 남기며 ODE/PDE 진화를 요구하지 않는다. 하지만 **β의 값만으로 결과가 정해지지 않고 β의 time jet와 Γ가 필요하다.** tilted 공간투영은 E0 성분도 섞으므로 복사 tensor의 time jet도 들어간다. Eq.(5)의 normal-frame 상한을 tilted D로 그대로 옮기지 않는다. 주어진 jet가 Einstein 제약과 matter 조건을 만족하는지는 별도의 algebraic/differential compatibility gate이다. 이 절은 그 제약을 풀었거나 자료에서 jet를 측정했다는 주장이 아니다.

## 5. 일반 광학 branch: 세 거리 조합의 상쇄 정리

### 5.1 관측 계약

같은 방향, 같은 기준틀, 같은 angular response, 같은 distance coordinate의 D,2D,4D에서 얻은 scalar/vector/tensor 관측을 공통 Euclidean/Hilbert carrier에 놓자. 거리 단위는 length이며 0부터 4D까지 regular part의 C² 통제를 가정한다.

\[
y(r)=u/r+g(r)+e(r),\quad g(0)=k_0,
\quad \sup_{0\le r\le4D}\|g''(r)\|\le M.
\tag{11}
\]

u는 **공통** coherent peculiar-velocity/angular pattern이다. 서로 다른 물체의 임의 고유속도를 같은 u라고 선언하지 않는다. 독립·상관 고유운동, calibration, 거리 변환·오차, 서로 다른 mask, 기준틀 변화는 e에 남긴다. r은 관측 redshift와 같은 변수가 아니다. d_L 또는 d_A를 쓰면 그 coordinate 변환과 자체 derivative bound를 포함해야 한다.

\(y=cz/r\)이면 \(k_0(n)=H-a\cdot n+\sigma:nn\). proper motion이면 \(k_0(n)=P_n\sigma n+(\omega-\Omega_{frame})\times n+P_nb_{pec}\). 일반 관측량 연결의 원전은 [Heinesen–Korzyński 2024, Appendix C/E](https://arxiv.org/html/2406.06167v1)이며 공통 congruence, geometric optics, caustic 없는 local expansion 조건을 유지한다.

### 5.2 정리와 증명

\[
\boxed{\widehat k_0=-2y(D)+5y(2D)-2y(4D)}.
\tag{12}
\]

가중치 w=(-2,5,-2)는 \(\sum w_i=1\), \(\sum w_i/r_i=0\), \(\sum w_ir_i=0\)이다. 따라서 u/r와 g'(0)r은 제거되고 k0는 보존된다.

Taylor의 적분형 \(g(r)=g(0)+rg'(0)+\int_0^r(r-t)g''(t)dt\)에 대입하면 잔차의 Peano kernel은

\[
K_D(t)=\begin{cases}
-t,&0\le t\le D,\\
2D-3t,&D\le t\le2D,\\
-2(4D-t),&2D\le t\le4D.
\end{cases}
\tag{13}
\]

K≤0이고 \(\int|K|dt=7D^2\). 그러므로

\[
\boxed{\|\widehat k_0-k_0\|\le7MD^2+\|-2e(D)+5e(2D)-2e(4D)\|}.
\tag{14}
\]

g''가 norm M인 일정 tensor이면 등호가 성립하므로, 주어진 C² class에서 7은 sharp하다. 각 shell마다 별도 triangle bound를 취해 얻는 27보다 강하다. 논문의 기존 관측 estimator에 대한 novelty를 주장하는 것은 아니다. 표준 extrapolation/Peano 기법의 이 문제에 대한 직접 유도다.

### 5.3 손실과 이득을 함께 유지

- \(\|e_i\|\le\delta\)만 알면 filtered deterministic error≤9δ.
- 독립·동일분산의 한 coefficient 오차 s이면 filtered variance=33s². 일반적으로 \(C_{filtered}=(w^T\otimes I)C(w\otimes I)\); cross-shell covariance를 버리지 않는다.
- 모든 shell에 동일한 additive calibration은 \(\sum w=1\) 때문에 남는다. 일정 frame spin 역시 남으므로 absolute ω 퇴화는 해결되지 않는다.
- random distance를 결과에 맞춰 fixed design처럼 취급할 수 없다. bin width·distance calibration을 공통 latent state에서 전파한다.

u를 제거한 출력만 보관하면 β 관측 정보도 잃는다. 이를 피하기 위해 원 세 shell을 유지하거나 다음 invertible 변환을 사용한다:

\[
\begin{pmatrix}\widehat k_0\\\widehat u\\\widehat q\end{pmatrix}=
\begin{pmatrix}
-2&5&-2\\8D/3&-4D&4D/3\\1/(3D)&-1/D&2/(3D)
\end{pmatrix}
\begin{pmatrix}y(D)\\y(2D)\\y(4D)\end{pmatrix}.
\tag{15}
\]

q=g'(0). Eq.(15)은 r² 이상의 나머지가 없을 때 정확하다. 나머지가 있으면 같은 함수 g에서 생긴 **공동** 잔차 image를 쓰며 세 독립 오차볼로 바꾸는 것은 느슨한 outer approximation이다. 이 변환은 정보를 추가하지 않는다. 원자료 likelihood 또는 covariance까지 변환한 likelihood 중 하나만 쓰고 둘을 독립 데이터로 곱하지 않는다.

## 6. 실제로 유용한 tensor interval의 충분조건

구면평균을 \(\langle\cdot\rangle=(4\pi)^{-1}\int d\Omega\)로 놓는다. R3의 leading responses에서

\[
\langle(\sigma:nn)^2\rangle=2\|\sigma\|^2/15,
\quad \langle|P_n\sigma n|^2\rangle=\|\sigma\|^2/5.
\tag{16}
\]

따라서 full-sky L² drift에서 E2 shear inverse의 norm은 √5이다. distance response에서는 √(15/2), a의 dipole inverse는 √3, ω의 rotational inverse는 √(3/2)이다. mask가 있으면 이 상수를 그대로 쓰지 않고 그 joint design의 inverse/identified subspace로 교체한다.

proper-motion E2 estimator \(\widehat\sigma\)와 원래 단위 drift의 공동 noise radius rα, filtered deterministic residual radius bdet가 있으면

\[
\|\sigma-\widehat\sigma\|\le R_\sigma^{obs}
=\sqrt5(r_\alpha+b_{det}),\qquad
b_{det}=7MD^2+b_{noncoherent}+b_{cal}+b_{distance}+\cdots.
\tag{17}
\]

rα는 실제 selected experiment의 joint coverage를 가진 반경이어야 한다. 각 계수의 1σ를 대신 넣지 않는다. mask inversion, correlation, law uncertainty는 R9 방식의 공동 집합으로 유지한다.

사전에 고정한 reference radius \(b_{\sigma,ref}=3HB_\sigma>0\)에 대해 관측 상한이 더 작아지는 충분조건은

\[
\boxed{\|\widehat\sigma\|+\sqrt5(r_\alpha+b_{det})<3HB_\sigma}.
\tag{18}
\]

예를 들어 나머지를 빼고 M을 허용할 여유가 양수이면

\[
M<\frac{(3HB_\sigma-\|\widehat\sigma\|)/\sqrt5-r_\alpha-b_{other}}{7D^2}.
\tag{19}
\]

이는 필요한 calibration/regularity 수준을 수치로 설계하는 식이다. M을 RHS에 맞춰 임의로 고르는 것이 관측 증거는 아니다. local physics와 photon propagation이 정당화하는 M을 이 조건과 비교해야 한다.

## 7. 관측 문헌을 넣은 실제 감도 판별

현재 원문으로 확인한 QSO proper-motion 분석 [Kouvelis et al. 2025, Table 1](https://arxiv.org/html/2508.02810v1)은 E2 개별 계수 통계오차 0.23–0.46 μas/yr를 보고한다. 그러나 Eq.(15)의 likelihood에는 source 간 covariance가 없고, §§4–6은 calibration/systematic 문제를 논의한다. 관측된 quadrupole 자체를 우주 전단으로 확정하지 않는다. 적색편이 bin은 0–1.25, 1.25–2.2, 2.2–6이며, 우리의 근거리 D,2D,4D matched-distance 실험이 아니다.

이를 실관측 MES 값으로 사용하지 않고, **선언된 감도 benchmark**와 비교한다:

\[
H_*=70\ {\rm km\,s^{-1}Mpc^{-1}},\quad
\epsilon_1=0,\quad\epsilon_2=\epsilon_3=10^{-5},
\quad B_\sigma=3\epsilon_2+3\epsilon_3/7.
\tag{20}
\]

이 epsilon은 실제 CMB fit이 아니며, intrinsic dipole=0도 시나리오다. 55쪽 보고서의 동일 MES-style normalization을 그대로 사용했다. 1 Julian yr=31,557,600 s, parsec 정의와 radian 변환을 써서

| 양 | 값 | 근거 상태 |
|---|---:|---|
| H* | 2.2685455026×10⁻¹⁸ s⁻¹ = 14.76646686 μas/yr | 단위 환산, CAS checked |
| Bσ | 3.42857143×10⁻⁵ | 선언된 epsilon의 대수결과 |
| 3H*Bσ | 0.0015188366 μas/yr | shear Frobenius benchmark |
| 3H*Bσ/√5 | 0.0006792444 μas/yr | 그 shear가 만드는 drift RMS scale |

문헌의 개별 계수 0.23–0.46는 마지막 scale보다 수백 배 크다. **이는 서로 다른 carrier의 단위 규모 비교이며 detection significance·필요한 정확한 개선배수·관측 상한 비교가 아니다.** 해당 논문의 VSH basis, 전체 covariance, local response 및 source residual을 동일 계약으로 옮기지 않았으므로 그런 결론을 내릴 수 없다. 다만 이 입력을 가져와 R3의 유용한 local-MES interval이 완성됐다고 주장할 근거가 없다는 판별은 가능하다.

nearby distance+proper-motion 자료가 전혀 없는 것은 아니다. Paine et al.의 232 nearby galaxy 분석(Cosmicflows-3/Gaia DR2)과 Maloney et al. 2026의 galaxy proper-motion 연구는 후속 pilot 후보다. 이 루프에서 카탈로그를 취득·fit하지 않았으며, 각 거리의 관측/모형 의존성과 residual envelope를 검증한 뒤 선택해야 한다. QSO 결과의 높은 z까지 local series를 늘리는 대안은 채택하지 않는다.

## 8. opacity와 local/global tilt를 혼동하지 않기

R3의 cold-Thomson relation \(\eta_1=\Gamma(\beta_e-\vartheta_1)\)은 local Γ가 필요하다. 적분 optical depth \(\tau=\int\Gamma dt\)가 양수라는 사실은 어느 한 사건의 Γ>0, Γ_min 또는 ∇Γ 상한을 주지 않는다. 예를 들어 \(0\le t\le\Delta t\)에서 \(\Gamma(t)=(2\tau/\Delta t)\sin^2(\pi t/\Delta t)\)는 적분 τ와 양의 총 column을 유지하지만 t=0에서 Γ=0이다. support를 국소화하면 그 외의 열린 구간에서도 Γ=0일 수 있다.

따라서 kSZ/remote dipole의 column-weighted information은 우선 그 가중 평균의 제약으로 유지한다. local electron β로 옮기려면 column geometry, intrinsic radiation dipole, opacity variation 및 point-to-average remainder가 필요하다. Eq.(15)의 u 역시 방향별 coherent motion carrier이며 자동으로 global matter tilt가 아니다. β_o, β_e와 β field의 jet는 동일 congruence/frame 정의 아래에서만 연결한다.

## 9. T,Q,F,Π,G_F에 전달하는 최종 객체

관측으로 만든 joint state Xi(d)에 기하 closure, regularity/source allowance, frame 및 CMB denominator를 함께 담는다. general branch와 homogeneous branch는 다른 premise labels를 붙여 별도로 보고한다. 전단 예에서는

\[
\mathcal C_\sigma=\{\widehat\sigma+\delta:\delta\in\mathcal E_{noise}\oplus\mathcal E_{physical}\},
\quad
\mathcal T=\{\sigma/[3H B_\sigma(\xi)]:\xi\in\Xi(d)\}.
\tag{21}
\]

geometry uncertainty를 포함한 실제 joint image는 generally ellipsoid가 아니다. support function과 관측 식별공간을 보존한다. reference body가 구형이 아니면 R2의 gauge normalization을 사용한다.

고정 양의 b에 대한 구형 예에서 \(\sigma\in B(\widehat\sigma,R)\)이면

\[
r_{lo}=\max(0,\|\widehat\sigma\|-R)/b,
\quad r_{hi}=(\|\widehat\sigma\|+R)/b,
\quad D\in[100(1-r_{hi}),100(1-r_{lo})].
\tag{22}
\]

denominator가 자료 의존이면 같은 Xi 위에서 극값을 구해야 하며 Eq.(22)의 고정 b 대입을 하지 않는다. MES 안으로 관측집합을 먼저 clipping하지 않는다. 양의 D는 기준 경계 대비 여유이며 확률이나 FLRW 성분비가 아니다.

\(Q_{outer}=T\otimes T\), \(F_{amp}=\|T\|^2\), \(D=100(1-\sqrt F)\)를 유지한다. R3가 구분한 legacy signed x, Q_gauge, F_support, G_path를 바꾸지 않는다. Π_tail은 sampling/posterior 법칙이 있어야 계산 가능하고 deterministic 허용집합만으로 확률을 만들지 않는다. 서로 다른 z의 G_tensor에는 지정된 transport와 양의 분모가 필요하다.

## 10. 검증과 판정

사전 계약 `PREREGISTRATION.json`은 후보의 탐색 유도 후, 이번 Wolfram 계산 전에 저장했다. 따라서 새로운 후보 자체의 사전 예측을 주장하지 않고 CAS test만 frozen confirmatory로 구분한다.

- CAS_SHELL_AND_SCALE: 상쇄 {1,0,0}, Peano 면적 {D²/2,5D²/2,4D²}, sharp 7MD², quadratic saturator -7MD², noise factor33, deterministic factor9, 단위 환산을 실제 Wolfram에서 확인.
- CAS_ADAPTERS_SOURCE: 세 성분 inverse residual 0행렬, 네 angular norm 항등식 잔차0, collisionless witness 수송잔차0, 동일 관측 sky1 및 gradient εk를 실제 Wolfram에서 확인.
- CAS_GEOMETRY_TILT_V2: 두 비가환 class-A/class-B 검산 예에서 Jacobi·metric compatibility·torsion 잔차가 0이었다. Rank 1/2/3 전체 tensor 공간에서 second derivative의 재귀 계산과 닫힌 행렬이 일치하고, derivative-index slot은 실제로 비영이며, 1·2차 coarse bound의 Gram 차가 양의 준정부호임을 확인했다. 이는 두 검산 예의 확인이며 일반 정리의 증명을 대체하지 않는다.
- 같은 CAS에서 Minkowski β=(1/3,1/4,0)와 arbitrary symbolic βdot의 four-velocity 정규화, F·U=0, A·U=0, shear trace/공간성, vorticity 공간성, 전체 분해, β=0에서 A=cβdot, normal K 극한을 확인했다.
- 최초 geometry CAS V1은 singleton KroneckerProduct와 matrix stacking의 구현 오류로 실패했다. 원 code/raw를 보존했고 두 표현을 수정한 V2만 최종 공간 미분 검산 증거로 사용한다. 이는 이론 반례나 runtime unavailable 판정이 아니다.
- 코드의 gamma matrix는 row b,column d로 covariant slot에 직접 작용한다. 본문의 row d,column b 정의의 transpose이며 receipt에 대응을 명시했다.
- 최종 과학적 판정과 검토 대상 identity는 동봉 `INDEPENDENT_REVIEW.md`가 권위이다. 후보 생성자는 자신의 결과를 승격 판정하지 않았다.

현재 evidence class: 직접 정리 `derived`; 위 식의 symbolic 확인 `CAS-checked`; 관측 숫자 `literature-supported`; actual local normalized interval `unresolved/not run`. Python은 파일 패키징에만 사용하며 과학 numerical full suite나 ODE/PDE solver는 수행하지 않는다. 앞선 턴의 runtime 상태를 이번 능력 판정으로 상속하지 않았다.

## 11. 다음 단계의 단일 우선 과제

다음 R5는 **homogeneous tilted one-time-jet closure를 실제 finite tensor operator로 완성**하는 것을 우선한다. 이유는 Eq.(4)가 불명확한 spatial derivative 상수를 관측 tensor와 metric으로 바꿀 수 있는 실제 구조를 제공하기 때문이다. C,h,K,β,βdot와 radiation time jets의 공동 허용영역에서 θ,σ,ω,A 및 radiative source의 동시 image를 만들고, 시간 derivative/source에 어떤 최소 관측 또는 물리 조건을 더해야 finite radius가 되는지 한 개의 명시적 example과 counterexample로 닫는다. 특정 Bianchi class 선택, 수치 진화, 새 broad solver는 필요하지 않다.

관측 pilot은 Paine/후속 galaxy 자료의 실제 거리 정의와 joint calibration을 확인하는 별도 lane으로 유지한다. 균일 M이나 source residual이 정당화되기 전 observed percentage를 게시하지 않는다. 이번에 완성한 shell 보상식은 그 검증을 통과한 경우에만 실제 자료에 적용한다.

## 12. 전체 운동학 부문과 실제 반환 상태

| 부문 | R4에서 확보한 경로 | 남은 입력/식별 조건 |
|---|---|---|
| Θ | 일반 거리 response의 monopole 및 exact jet trace | absolute distance calibration, finite-distance/source budget; 보편적 MES Θ ceiling은 없음 |
| σ_ab | E2/거리 quadrupole inverse, homogeneous spatial derivative matrix | radiation time derivative·source·고차항 또는 관측 drift residual |
| A_a | 거리 response dipole와 full tilt-jet acceleration | observer Doppler/calibration 분리; proper-motion glide를 바로 A라고 동일시하지 않음 |
| ω_a | drift B1의 relative rotation과 projected jet antisymmetric part | 독립 frame-spin 조건; normal branch의 0은 관측값 아님 |
| β_a | 세 shell의 u carrier를 함께 보존, full geometric jet adapter | u→특정 local/global β의 response, βdot, optical-depth/local-rate 구분; 보편적 MES β ceiling 없음 |

첫 세 shell은 같은 관측자 사건의 vertex k0를 추정한다. 이를 세 redshift 사건의 k(z) 측정으로 해석하지 않는다. 깊이에 따른 T나 G를 만들려면 field transport와 다른 사건의 response를 추가해야 한다.

실제 폭을 가진 shell j에 정규화된 selection measure p_j(r)를 쓰면 moment 조건을
\(\sum_jw_j=1,\ \sum_jw_j\langle r^{-1}\rangle_j=0,\ \sum_jw_j\langle r\rangle_j=0\)
로 바꾼다. 이 경우 Peano kernel도 \(K(t)=\sum_jw_j\langle(r-t)_+\rangle_j\)로 다시 계산한다. 중심거리 가중치 -2,5,-2나 상수 7을 자동 재사용하지 않는다. 평균거리의 역수와 역거리 평균은 다르다. 거리오차 law가 미확인인 경우 이 kernel 역시 조건부 입력이다.
