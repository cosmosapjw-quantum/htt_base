# 유형 미지정 Loop 2 — 국소 exact 결과와 판정 범위

## 고정 계약과 입력

공통 계약은 [CLAIM_CONTRACT.json](CLAIM_CONTRACT.json), SHA-256
37af2ace41312d18d08fee68f0ca88e92f7e728871224cdfa2dd43fb6dca47c3이다.
원 Loop 1 ZIP SHA-256은 0f896823faa03ed82b8cf484cfc893a56ea913e259dc16d59c50d5f97e68670c,
그 안의 manifest SHA-256은 7a62a820c348786c77f129c4bdc0a88f1e599dec46c67b1531a533a37e0682f5다.
manifest 101/101 항목의 byte size·SHA-256이 맞았다. 별도 전달된 SQLite gzip은
ZIP 내부 바이트와 같고 SHA-256 17288a47268253aa3e0eb4b6a7f8027562dd8995febd0b917db8632772521614다.
새 이름으로 푼 SQLite의 SHA-256은 6587bf88aa161ff2bd345610cdc8485c5e50095c750643359e2de4851537a4cc,
크기 548917248 byte, integrity_check=ok다.

signature (−+++), x⁰=ct, U²=−c², κ=8πG_N/c⁴,
[∇_c,∇_d]vᵃ=Rᵃ_bcd, Λ=0을 채택한다. xAct의 Riemann sign은 +1이다.
T=G/κ는 총 Einstein source이며 성분별 dust stress가 아니다.

## TF-P2: 조건부 gap bound의 exact rest-frame 대수

smooth symmetric T와 미래 단위 timelike eigenvector u=U/c가
T(u)=−εu를 만족하고, rest space의 L=S+εI가 invertible이라고 하자.
이 식을 E_μ 방향으로 미분하고 rest projection을 취하면

\[
D_\mu+L(\nabla_{E_\mu}u)=0,\qquad
D_\mu=h(\nabla_{E_\mu}T)u,
\quad \nabla_{E_\mu}U=-cL^{-1}D_\mu .
\]

u·u=−1의 미분 때문에 ∇u는 rest space에 있다. self-adjoint L의 세
고유값 ℓ_i와 δ=min|ℓ_i|>0을 쓰면 열마다
\(\|\nabla_{E_\mu}U\|^2
=c^2\sum_i(D_\mu^i)^2/\ell_i^2
\le c^2\|D_\mu\|^2/\delta^2\).
spatial 행렬 \(K_{ij}=\langle E_j,\nabla_{E_i}U\rangle\)은
\(K=(\theta/3)I+\sigma+\omega\)로 Frobenius 직교 분해된다.
derivative-first \(\omega_{ij}=(K_{ij}-K_{ji})/2\)에서
\(\|\omega\|_F^2=2|\boldsymbol\omega|^2\), \(A=c\nabla_uU\)이므로

\[
\frac{\theta^2}{3}+\|\sigma\|_F^2+2|\boldsymbol\omega|^2
+\frac{|A|^2}{c^2}
=\sum_{\mu=0}^3\|\nabla_{E_\mu}U\|^2
\le\frac{c^2\|D\|^2}{\delta^2}.
\]

[Wolfram script](wolfram/tf_p2_exact.wl)의 [raw 출력](wolfram/tf_p2_raw.txt)은
직교분해 잔차 0과 일반 diagonal L의 열별 식을 exact로 확인한다.
eigenvector 미분의 미분기하 전제와 spectral theorem은 이 실행에서 수기 유도다.
δ=0인 Tᵃ_b=−ρδᵃ_b (cosmological-constant 형태)에서는 L=0이며 모든 미래 단위
timelike u가 eigenvector다. 선택 유일성이 깨져 inverse bound는 적용되지 않는다.

## TF-P3: metric 2-jet 반례와 P2 포화

\[
\phi=-b(x^0)^2-\tfrac b2\sum_i(x^i)^2
+\tfrac\lambda2(x^0)^2x^1,\quad g=e^{2\phi}\eta,\quad b>0,\ \lambda\in\mathbb R.
\]

p=0에서 φ와 그 1-jet는 0이고 metric 2-jet에는 λ가 없다.
Christoffel도 0이다. [xAct script](wolfram/tf_p3_xact.wl)의
[최종 raw 출력](wolfram/tf_p3_xact_final_raw.txt)은 일반 기호 b,λ에 대해
\(G_{ab}(0)=\mathrm{diag}(6b,0,0,0)\),
\(\partial_0G_{10}(0)=-2\lambda\),
\(D_0^1=\nabla_0T^1{}_0=-2\lambda/\kappa\) 및 다른 D 열=0을 낸다.
p에서 \(L=(6b/\kappa)I\)이므로
\(\nabla_0 U^1=c\lambda/(3b)\),
\(A^1=c^2\lambda/(3b)\), θ=σ=ω=0이다.
[SymPy의 Christoffel 미분 경로](sympy/tf_p3_connection.py)는
별도 symbolic 수식으로 같은 점 결과를 확인했다.

이 가족에서는 p에서 P2 부등식이 **등호**다:
\[
\frac{|A|^2}{c^2}
=\frac{c^2\lambda^2}{9b^2}
=\frac{c^2\|D\|^2}{\delta^2},
\quad\delta=6b/\kappa,\quad\|D\|=2|\lambda|/\kappa .
\]
따라서 metric 2-jet와 gap만 고정하면 가속도 상계가 없다.
P2의 유한 예산에는 stress 1-jet의 \(\|D\|\)가 실제로 필요하다.
p에서 ε=6b/κ>0, pressure eigenvalues=0이고 strict type-I DEC다.
매 유한 λ에서 충분히 작은 근방에는 이 strict 조건과 단순 timelike branch가
연속성으로 유지된다. λ 전체에 공통 근방, 근방 전체 dust/perfect-fluid EOS,
물질 작용, global cosmological solution은 얻지 않았다.

derivative-first 와도 부호를 반대로 정의하면 axial vorticity의 부호가 뒤집힌다.
공간 벡터 A⊥U에 대해 \(\nabla_aA^a=D_aA^a+|A|^2/c^2\)다.
4-divergence를 spatial divergence로 대체하면 이 항을 잃는다.

## Lean/mathlib: 실제 kernel 증명 범위

[Lean 원문](../../../formal_mathlib/Egs3V8Mathlib/TypefreeLoop2.lean)은
mathlib v4.31.0 (fabf563a7)에서 컴파일됐다. [최종 raw 출력](lean/lean_final_raw.txt)은
TF-S2의 참 공동 피복 사건 \(\subseteq\) image 피복 사건과 measure monotonicity,
TF-S4의 bounded confidence set에 두 값이 들어간 사건 \(\subseteq\) 직경 하한 사건,
두 marginal coverage와 union bound에서 \(1-2\alpha\) 하한을 얻는 실수 부등식,
TF-P2의 diagonal gap 아래 3열 norm estimate와 명시적 3×3 trace/STF/antisymmetric
Frobenius 항등식을 검증한다. 첫 정리는 axiom 의존이 없고 나머지는 mathlib/Lean 기본
propext, Classical.choice, Quot.sound만 출력됐다. sorry/admit/새 project axiom은 없다.

이것은 TF-S2/S4의 **구성요소 증명**이다. full-law 동일성·confidence
calibration·event measurability·typed unavailable target과 하나의 결합된 확률 정리는
아직 Lean statement로 닫지 않았다. TF-P2의 일반 self-adjoint spectral
diagonalization과 미분기하 연결, TF-S1/S3의 compactness·0-interior·measurability·dim=0
가지는 이 파일에서 아직 kernel formalization되지 않았다. 해당 수기 증명이나
기존 native-evaluation 기록을 이 새 kernel proof로 부르지 않는다.

## SageMath + Singular: 미분류 대수와 실수 가지

[Sage 원문](sage/typefree_c1.sage)의 [raw 출력](sage/sage_raw.txt)은 3차원
antisymmetric \(C_{ij}{}^k\)의 독립 9변수와 Jacobi 3다항식을 기호 그대로
입력했고 Singular std로 Gröbner basis 5개를 얻었다. zero structure는 실제
Jacobi feasible 대조다. 이는 특정 Bianchi type 선택이 아니다.
물리 domain에는 \(g_{11}>0\),
\(g_{11}g_{22}-g_{12}^2>0\), \(\det g>0\), lapse \(N>0\),
\(1-g_{ij}\beta^i\beta^j>0\), metric/velocity jets와 source가 별도로 필요하다.
\(C\)만으로 rate magnitude bound를 만들지 않는다.

새 예시 명제: \(F=\{(u,v):u^2+v^2\le1\}\),
\(y=u/(1+v^2)\)의 실수 image는 정확히 [-1,1]이다.
증명은 \(|y|\le|u|\le1\)과 각 y∈[-1,1]에 대해 (u,v)=(y,0)의 실현이다.
denominator \(d=1+v^2>0\)를 \(d=1+v^2,\ dy=u,\ hd=1\)로 보존한
elimination ideal의 y 부분은 zero ideal이다. 따라서 ideal-membership만으로
실수 image의 boundedness를 증명할 수 없다. \(y=u/v\)를 사용할 때는 \(v\ne0\)
가 필수이고 \(vy-u=0\)만 남기면 (u,v)=(0,0)에서 가짜 전체 y fiber가 생긴다.
singular stratum을 버리지 않는다. 표본 Jacobian rank를 전체 parameter의
rank 정리로 승격하지 않았다.

## TF-W1과 과학 판정

[TF-W1 입력 계약](TF_W1_INPUT_KO.md)은 R2 exact monopole의 한 창, operator,
source decomposition, endpoint 및 derivative 예산을 구체화했다. 현재 실제
source/time law와 joint anchor가 없어 식별 tensor, 물리 budget percentage,
p-value는 unavailable이다. local boost와 global tilt의 같은 응답 열을 가진
실험에는 차이의 kernel을 유지한다.

Loop 1의 독립 판정은 원문 13개 **보정된 수기 분석 명제**에만 해당한다.
이 Loop 2의 새 CAS/formal 근거에 대한 새 독립 과학 판정은 아직 받지 못했다.
따라서 Loop 2의 science admission은 HOLD다. I2 DEFENDED_CONDITIONAL,
I3 HOLD_INPUT_INCOMPLETE 및 기존 science HOLD는 그대로다.
