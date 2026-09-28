# 78개 theorem 후보의 증명·반증 판정

## 범위와 증거의 의미

이 문서는 직전 답변의 A01–A14, B01–B22, C01–C18, D01–D08, E01–E16을 같은 번호로 판정한다. N1–N6은 이 목록의 중복 명제로 별도 count에 더하지 않는다. 원문 축약 진술과 수정된 가정은 THEOREM_LEDGER.json에 별도 필드로 보존한다. `PROVED`는 여기 명시한 가정하의 수학적 증명, `PROVED_STRENGTHENED`는 더 강한 정리, `CORRECTED`는 원문에 필요한 substantive 수정, `REFUTED`는 원문에 대한 반례, `NOT_A_DEFINED_PROPOSITION`은 참·거짓의 대상이 되도록 명제가 정의되지 않았다는 판정이다. 후자의 자연스러운 보편화에는 구체적 반례도 제시한다.

여기서 증명은 수학적 논증이다. Wolfram의 유리수·기호 항등식은 그 논증의 유한 대수 부분을 재확인한다. 무작위 수치실험의 PASS를 보편 명제의 증명으로 사용하지 않는다. 별도 독립 referee나 Lean/Isabelle 커널을 거친 형식증명이라고 주장하지 않는다. 원시 Planck 지도를 열거나 철회된 관측 rank를 복권하지 않는다.

## 공통 규약

공간은 양의 definite 내적을 갖는 지향된 실수 3차원 공간이다. `STF_l`는 대칭·무흔적 rank-l tensor의 공간이다. Q,S∈STF₂, O∈STF₃; Q:Q=tr Q², O:O=ΣO_ijk²이다. 괄호의 대칭화는 평균, 꺾쇠는 STF projection이다. 공간 orientation ε123=+1. Proper rotations는 SO(3), 반사를 포함하면 O(3)이다. 이 둘을 혼용하지 않는다.

시공간은 η=diag(-1,1,1,1), c=1. 물리 shear는 지정한 congruence의 σ, H=Θ/3>0. S=σ/(√6 H), w=ω/(√3 H), Uσ,Uω≥0. `MES body`는 해당 MES 전제가 성립할 때의 norm 외부 허용영역이며, Einstein 제약을 자동으로 충족하는 모든 실제 우주들의 집합이라는 뜻이 아니다.

하늘 방향 n은 바깥쪽 시선이고 photon propagation 방향은 e=-n이다. Boost 식은 n convention을 사용한다. Stored orthonormal real coefficient는

\[
c_\ell=(a_{\ell0},\sqrt2\Re a_{\ell1},-\sqrt2\Im a_{\ell1},\ldots).
\]

원 historical 17쪽 관측 보고서 §3.1의 unscaled Re/Im 저장 설명과 다르다. 이 문서는 그 historical 데이터 결과의 수용 증거가 아니라 위 corrected convention에서의 수학을 다룬다. 첨부된 formula SSOT는 cold non-tilted electron-rest Thomson 범위이며, 그 자체가 finite-electron-tilt solver validation을 주지는 않는다.

Finite-rank 식에서는 N이 관측행을 포함한 전체 행 수다. 큰 score가 더 극단적이라는 convention이다. 보수적 rank는

\[
p_i=N^{-1}\sum_j1\{S_j\ge S_i\}.
\]

`exact`는 보편적으로 정확한 유의수준 α의 등호가 아니라 finite-sample superuniformity를 뜻한다. Ties가 없고 α가 1/N 격자에 있을 때에만 등호가 일반적으로 성립한다. 필요한 곳에서는 이 표현을 명시적으로 고친다.


---

# A. Representation, orbit, invariant geometry

## P01 — Harmonic/STF 표현과 MES norm 변환
대상: A01–A02, B01.

### A01 — Stored-real harmonic isometry
**판정: PROVED.**

현실 조건 a_{l,-m}=(-1)^m a*_{lm} 및 orthonormal complex Y_lm를 가정한다. 그러면
\[
T_l(n)=a_{l0}Y_{l0}+2\sum_{m>0}\Re(a_{lm}Y_{lm})
=c_{l0}Y_{l0}+\sum_{m>0}(c_{lm,c}\sqrt2\Re Y_{lm}+c_{lm,s}\sqrt2\Im Y_{lm}).
\]
괄호의 real basis는 orthonormal이므로 Parseval로
\[
\int T_l^2d\Omega=\|c_l\|_2^2=a_{l0}^2+2\sum_{m>0}|a_{lm}|^2.
\]
따라서 unscaled Re/Im vector에 필요한 diag(1,2,2,...) metric을 c에 다시 곱하면 안 된다. 이 결과는 저장 규약이 실제 exporter와 일치한다는 별도의 구현 검사를 대체하지 않는다.

### A02 — Harmonic–STF intertwining
**판정: PROVED.**

τ∈STF_l에 대응하는 homogeneous polynomial Hτ(x)=τ_L x^L는 ΔHτ=0이고, 차원은 2l+1이다. 반대로 차수 l의 harmonic homogeneous polynomial의 계수 tensor는 STF다. 따라서 Hτ|S²와 degree-l spherical harmonic space 사이에 선형 전단사가 있다. 회전 G에 대해
\[
H_{G^{\otimes l}\tau}(n)=H_\tau(G^{-1}n).
\]
이 항등식이 intertwining을 증명한다. 구면 적분의 isotropy를 사용하면
\[
\int H_\tau H_\xi\,d\Omega=\Delta_l\tau:\xi,
\quad \Delta_l={4\pi l!\over(2l+1)!!}.
\]
증명: ∫n_{i1}⋯n_{i2l}는 4π/(2l+1)!! 곱하기 모든 δ pairing의 합이다. 각 τ 또는 ξ 내부 index끼리 연결하는 pairing은 trace 때문에 0이고, 양 tensor 사이의 l! pairing만 남는다. 특히 Q:Q=15||c₂||²/(8π), O:O=35||c₃||²/(8π). 이 증명은 round-trip이 아니라 실제 sphere function의 유일성에 근거한다.



### B01 — MES PSTF norm conversion
위 integral identity를 δT_l/T₀=τ_Ln^L에 적용하면
\[
e_l^2\equiv\frac1{4\pi}\int(\delta T_l/T_0)^2d\Omega
=\frac{l!}{(2l+1)!!}\,\tau_L\tau^L.
\]
따라서
\[
\epsilon_l^{\rm PSTF}=\|\tau_l\|=
\sqrt{\frac{(2l+1)!!}{l!}}e_l,\qquad
e_l=\sqrt{\frac{(2l+1)C_l}{4\pi T_0^2}}.
\]
특히 ε₂=√(15/2)e₂, ε₃=√(35/2)e₃이다. 이는 coefficient convention을 명시한 exact angular identity다. MES에 필요한 congruence, domain, derivative smallness 가정이나 measured norm이 전 영역의 upper bound라는 사실을 증명하지는 않는다 [R2,R3].

## P02 — O(3)와 SO(3)의 harmonic-cubic invariant ring
대상: A03.

### A03 — Pure STF3의 네 불변량
**판정: CORRECTED — O(3) 한정판은 성립하고, SO(3) 완전성 해석은 반증된다.**

원 문장의 '2,4,6,10차 네 개가 minimal integrity basis'는 O(3)의 isotropic polynomial invariants에 대한 Smith–Bao/Chen–Hu–Qi–Zou 정리다. SO(3)에서는 parity-odd invariant가 추가로 필요하다. [R1]은 §3의 quotient를 명시적으로 St(3,3)/O(3)로 쓴다.

구체적 반례를 만든다. 일곱 독립 성분
\[
(O_{111},O_{112},O_{113},O_{122},O_{123},O_{222},O_{223})=(1,2,3,4,5,6,7)
\]
에 대칭성 및 O133=-5,O233=-8,O333=-10을 적용한다. A_ij=O_ikl O_jkl, u_i=O_ijk A_jk, χ=det[u,Au,A²u]라 하면 정확 연산으로
\[
A=\begin{pmatrix}118&182&-9\\182&284&6\\-9&6&386\end{pmatrix},\quad
u=(58,302,296),\quad\chi=20640382199000\ne0.
\]
χ는 degree 15 SO(3)-invariant이고 O→-O이면 χ→-χ. 네 even-degree invariants는 O와 -O에서 같다. 만일 두 tensor가 proper-rotation equivalent라면 χ가 같아야 하므로 모순이다. 따라서 네 개로 SO(3) orbit을 분리하거나 모든 SO(3) polynomial invariants를 생성할 수 없다. Wolfram 유리수 계산이 이 반례를 독립 확인했다.

수정판의 생성 정리까지 다음 exact certificate로 증명할 수 있다. Define I₂=tr A, I₄=tr A², I₆=u·u, I₁₀=O(u,u,u). 위 integer witness에서 이 네 polynomial의 Jacobian의 첫 네 열 minor는
\[
-110423733041843712000\ne0,
\]
따라서 네 개는 algebraically independent다. V₃의 torus weights는 −3,−2,…,3이므로 Molien–Weyl constant-term formula는
\[
H(t)=\operatorname{CT}_z\frac{1-z^{-1}}{\prod_{m=-3}^{3}(1-tz^m)}
=\frac{1+t^{15}}{(1-t^2)(1-t^4)(1-t^6)(1-t^{10})}.
\]
이는 finite Taylor series 일치가 아니다. |t|<1에서 z^m=t(m=1,2,3)의 pole들에 대한 정확한 rational residue trace로 전체 rational function identity를 계산했으며, `code/invariant_ring_certificate.py`와 `wolfram/05_molien.wl`에 독립 계산을 둔다.

R=ℝ[I₂,I₄,I₆,I₁₀]라 하자. Algebraic independence 때문에 Hilbert series는 위 denominator의 역수다. R⊕χR는 SO(3) invariant ring의 graded subspace이다: 첫 summand는 even degree, 둘째는 odd degree이고, χ≠0이며 polynomial ring에 zero divisor가 없으므로 direct sum이다. 이 subspace의 Hilbert series가 Molien–Weyl로 구한 전체 ring과 정확히 같아 각 finite-degree piece가 같아야 한다. 따라서 전체 SO(3) invariant ring은 R⊕χR이고 χ²∈R다. O(3)는 추가 inversion O→−O를 요구하므로 even subring R만 남는다. 네 even generator의 algebraic independence 및 χ의 odd degree가 minimality를 증명한다.

결론: **O(3)는 2,4,6,10차 네 generator, SO(3)는 여기에 15차 χ를 추가한 다섯 generator와 χ²의 한 relation**이다. 구체적 relation polynomial의 전체 expansion을 계산하지 않아도 위 Hilbert-series proof는 생성 정리와 존재를 증명한다. 이 증명은 compact-group Molien–Weyl formula를 표준 보조정리로 사용한다; 독립성·residue identity·χ≠0은 exact 계산으로 제공한다.



### 네 even generators와 한 odd generator가 충분하다는 전차수 증명
반례에서 사용한 A와 u에 대해
\[
I_2=\operatorname{tr}A,\quad I_4=\operatorname{tr}A^2,
\quad I_6=u^Tu,\quad I_{10}=O(u,u,u),\quad
\chi_{15}=\det[u,Au,A^2u]
\]
를 택한다. 위 정수 witness의 일곱 독립 O 성분에 대해 (I₂,I₄,I₆,I₁₀)의 Jacobian에서 첫 네 열의 determinant는 정확히
\[
-110423733041843712000\ne0.
\]
따라서 이 네 even polynomial은 algebraically independent다. 이 determinant는 재실행 가능한 exact SymPy certificate에 저장돼 있다.

생성성은 일부 차수의 수치 fitting이 아니라 전차수 Hilbert-series identity로 증명한다. V₃의 weights는 −3,…,3이다. 각 Sym^n(V₃)에서 trivial multiplicity는 weight-zero multiplicity minus weight-one multiplicity이므로
\[
H(t)=\operatorname{CT}_z\frac{1-z^{-1}}{\prod_{m=-3}^3(1-tz^m)}
=\frac{1+t^{15}}{(1-t^2)(1-t^4)(1-t^6)(1-t^{10})}.
\]
마지막 exact rational identity는 contour integrand
\[
\frac{z^5-z^4}{(1-t)\prod_{m=1}^3(1-tz^m)(z^m-t)}
\]
의 |t|<1 내부 pole z^m=t (m=1,2,3)의 residue 합으로 평가한다. 각 q_m=z^m−t에 대해 나머지 denominator의 polynomial inverse modulo q_m을 계산하면 residue 합은 m 곱하기 그 remainder의 constant coefficient다. `code/invariant_ring_certificate.py`와 `wolfram/10_molien_all_degrees.wl`은 이 rational identity의 residual을 정확히0으로 계산한다. Wolfram과 SymPy에서 독립 실행됐으며 truncated power-series 일치는 사용하지 않았다.

A₀=R[I₂,I₄,I₆,I₁₀]라 하자. Algebraic independence 때문에 H_A0=1/∏(1−t^d)이다. χ₁₅는 nonzero이고 odd이므로 A₀와 χ₁₅A₀는 vector-space direct sum이다: f+χg=0에 O→−O를 적용해 더하고 빼면 f=g=0이다. 이 graded subspace의 Hilbert series는 위 SO(3) invariant ring과 정확히 같다. 따라서 모든 차수의 차원이 같고
\[
R[V_3]^{SO(3)}=A_0\oplus\chi_{15}A_0.
\]
특히 χ₁₅²는 A₀의 polynomial이며, 다섯 generator가 SO(3) ring을 생성한다. O(3)는 추가로 O→−O 불변성을 요구하므로 even part A₀만 남는다. 네 even generator의 algebraic independence와 χ의 parity가 minimality도 준다. 이것은 알려진 invariant-ring 결과 [R1]와 일치하지만, 본 판정에는 exact residue/independence certificate를 추가했다.

## P03 — Quotient 차원과 여덟 좌표의 no-go
대상: A04.

### A04 — 여덟 smooth scalar의 불완전성
**판정: PROVED.**

V=STF₂⊕STF₃의 차원은 12다. 아래 A06의 κ≠0인 예에서는 stabilizer가 세 독립 vector를 고정해야 하므로 identity뿐이다. 따라서 generic orbit 차원은 3이고 free quotient는 9차원 smooth manifold다. 그 열린 chart에서 여덟 continuous scalar가 orbit을 분리한다면 열린 R⁹의 부분집합을 R⁸에 연속 단사 매장한다. R⁸↪R⁹와 합성한 뒤 invariance of domain을 적용하면 image가 R⁹에서 열려야 하지만 codimension-one hyperplane에 포함된다. 모순. 이 주장은 단순한 수치 Jacobian-rank 측정보다 강하다.

## P04 — (S,v)의 orbit reconstruction
대상: A05–A06.

### A05 — (S,v)의 generic orbit reconstruction
**판정: PROVED_WITH_HYPOTHESES.**

S는 real STF₂, simple spectrum λ1<λ2<λ3, v는 cyclic, 즉 각 eigenspace의 성분이 0이 아니라고 하자. s₂,s₃는 특성다항식 λ³-s₂λ/2-s₃/3을 정하므로 ordered eigenvalues를 정한다. m_k=vᵀS^k v (k=0,1,2)는 Vandermonde system으로 p_i=v_i²를 정한다(B07). 두 state의 이 다섯 scalar가 같으면 eigenframe에서 |v_i|가 같다. 같은 κ 부호를 요구하면 대응하는 sign matrix의 determinant가 +1이다. 이 sign matrix와 eigenframe 회전의 합성으로 두 state가 SO(3)-equivalent다. 역은 invariant 정의에서 즉시 나온다. 따라서 다섯 연속 scalar와 discrete sign κ가 generic orbit을 정한다. Degenerate spectrum에서 이 좌표식을 division 없이 사용해서는 안 된다.

### A06 — Krylov determinant factorization
**판정: PROVED.**

지향된 eigenframe에서
\[
K=[v,Sv,S^2v]=\operatorname{diag}(v_1,v_2,v_3)
\begin{pmatrix}1&\lambda_1&\lambda_1^2\\1&\lambda_2&\lambda_2^2\\1&\lambda_3&\lambda_3^2\end{pmatrix}.
\]
따라서 κ=v1v2v3∏_{i<j}(λ_j-λ_i). 특별히 Q=diag(1,2,-3), A03의 O이면 v=O:Q=(24,38,47), κ=857280. 이 예는 generic open stratum이 공집합이 아님을 증명한다.

## P05 — Proper Krylov canonicalization과 nine-dimensional slice
대상: A07–A09.

### A07 — Orientation-fixed QR frame
**판정: PROVED.**

κ≠0에서 e1=v/||v||, w=Qv-(e1·Qv)e1, e2=w/||w||, e3=e1×e2로 정의하라. E=[e1,e2,e3]∈SO(3). R=EᵀK는 upper triangular이고 R11,R22>0, R33의 부호는 detK와 같다. 첫 두 QR vector와 cross-product가 강제되므로 유일하다. Proper rotation G에 대해 e_i(Gx)=G e_i(x), 즉 E(Gx)=G E(x). 부호를 따로 정하지 않는 일반 QR routine을 사용하면 이 정리의 구현이 아니다.

### A08 — Canonical pair의 orbit separation
**판정: PROVED.**

Qc=EᵀQE, Oc=(Eᵀ)^{⊗3}O라 하자. A07의 equivariance로 canonical pair는 SO(3)-invariant다. 두 canonical pair가 같으면 G=E2 E1ᵀ∈SO(3)가 Q1을 Q2로, O1을 O2로 보낸다. 역방향도 즉시 성립한다. 따라서 κ≠0에서 canonical pair equality는 orbit equality의 필요충분조건이다. Raw tensor amplitude를 임의로 normalize해 버리면 amplitude까지 포함한 injectivity는 사라진다.

### A09 — Nine-dimensional smooth slice
**판정: PROVED.**

Canonical pair는 v2=v3=0, v1>0, Q31=0, Q21>0을 만족한다. 세 equality가 independent임을 확인하면 된다. ω=(ω1,ω2,ω3)의 미소 회전에 대해, v=(r,0,0)에서
\[
\delta v_2=r\omega_3,\quad\delta v_3=-r\omega_2,\quad
\delta Q_{31}=Q_{12}\omega_1+(Q_{33}-Q_{11})\omega_2-Q_{23}\omega_3.
\]
세 constraint의 orbit-direction Jacobian determinant의 절댓값은 r² Q12>0이다. Implicit-function theorem으로 12-3=9차원 local slice이며, A08에 의해 generic quotient chart다. 전역 Euclidean chart 또는 polynomial rational chart라는 추가 주장은 하지 않는다.

## P06 — Stabilizer obstruction과 scalar-to-direction no-go
대상: A10, B22.

### A10 — 모든 degenerate strata를 덮는 finite canonical-frame atlas
**판정: REFUTED_AS_STATED.**

Q=diag(-1,-1,2), O=STF(e3^{⊗3})를 취하면 이 pair는 z축 주위의 모든 SO(2) 회전에 고정된다. Equivariant frame E가 존재한다면 stabilizer h에 대해 E(x)=E(hx)=hE(x), 따라서 h=I여야 한다. 비자명 SO(2)와 모순. Equivariant vector를 아무리 많이 만들어도 이 점에서 모두 z축을 따라야 한다. 여러 chart를 붙이는 것으로 isotropy obstruction을 제거할 수 없다.

수정 정리: free stratum은 유한 개의 polynomial equivariant-vector pair로 정의한 open charts로 덮을 수 있다. 표준 Hilbert finite-generation theorem을 사용하면 covariant module의 유한 생성계 {f_j}가 존재한다. Free orbit에서 임의 vector 값의 continuous equivariant map을 만들고 polynomial approximation 후 Haar 평균하면, polynomial covariant들의 평가값이 R³을 생성함을 알 수 있다. 따라서 유한 생성계 중 두 개가 independent인 open set들이 free stratum을 덮고 Gram–Schmidt/cross product로 frame을 준다. Stabilizer가 있는 strata에서는 invariant coordinates 또는 stabilizer-valued equivalence class를 써야 한다. A13의 orbital-measure kernel은 이 문제를 피한다.



### B22 — Scalar premise에서 방향을 만들 수 없는 이유
Scalar input x는 SO(3)의 trivial representation이다. Nontrivial irreducible vector/STF_l (l>0)로의 deterministic equivariant map f는 모든 g에 대해 f(x)=f(gx)=g f(x)를 만족해야 한다. Nontrivial irrep의 공통 fixed subspace는 {0}이므로 f(x)=0이다. 여러 scalar의 목록도 여전히 trivial representation의 곱이므로 같다. 반면 모든 방향을 포함하는 set-valued ball이나 별도 random seed로 뽑은 isotropic random vector는 가능하지만, 이는 측정된 source direction이 아니다. 외부 tensor/vector가 이미 주어진 경우 그것과 scalar amplitude를 결합하는 것은 이 no-go의 가정 밖이다.

## P07 — Bispectrum equivalence의 반증과 polynomial 대체물
대상: A11.

### A11 — Krylov field와 degree-bounded bispectrum field의 rational equivalence
**판정: REFUTED_AS_STATED; 'degree-bounded'의 상한을 안 정한 판은 NOT_SPECIFIED.**

표준 bispectrum은 degree 3 invariant다. V₂⊕V₃에서 quadratic power invariants 둘과 nonzero cubic invariants trQ³, Q_ab O_acd O_bcd만 얻는다. QQO는 두 동일 l=2 factor의 symmetric product가 odd J=3을 포함하지 않아 0, OOO도 동일-factor의 odd interchange parity 때문에 0이다. 따라서 power+bispectrum generated field의 transcendence degree≤4<9. Generic separating field와 같을 수 없다.

A06의 Q,O와 Q,-O는 모든 이 power/bispectrum에서 같지만 κ의 부호는 반대다. 이는 discrete 반례이며, 차원 논증은 continuous 결손도 보여준다. 더욱이 normalized QR에는 제곱근이 있으므로 canonical components 자체를 아무 조건 없이 rational invariant field라고 부를 수 없다.

증명 가능한 대체물: s₂,s₃,m0,m1,m2,κ와 열 개 O(K_i,K_j,K_k), i≤j≤k를 합친 16개 polynomial invariant는 κ≠0에서 orbit을 분리한다. 다섯 moment scalar가 KᵀK와 QK=KC의 companion action을 정한다. 두 state에서 값이 같으면 G=K2K1⁻¹는 Gram equality로 orthogonal, 같은 κ로 proper이며 companion action으로 Q2G=GQ1. 열 개 cubic components equality는 O2=G^{⊗3}O1을 준다. 이것은 'bispectrum으로 충분하다'와 다른 정리다.

## P08 — Quotient characteristic kernels
대상: A12–A13.

### A12 — Injective canonical chart의 Gaussian kernel
**판정: PROVED_WITH_HYPOTHESES.**

Free quotient의 Borel injective chart φ를 사용하고 k(x,y)=exp(-||φ(x)-φ(y)||²/(2h²)), h>0라 하자. Gaussian kernel은 Euclidean probability measures에 characteristic하다. 따라서 zero MMD이면 두 pushforward probability measures가 같다. Standard Borel 공간의 Borel injective map은 image 위 Borel inverse를 가지므로 원 quotient distributions도 같다. 이 증명은 kernel의 distribution-separation 성질이지 관측 1개에서의 consistent two-sample test 성질이 아니다(E16).

### A13 — Haar-averaged quotient kernel
**판정: PROVED_WITH_HYPOTHESES; 잘못된 단측 평균은 반례가 있다.**

Compact G의 연속 작용, bounded feature map Φ를 갖는 PD kernel k를 가정하고
\[
\bar k(x,y)=\int_G\int_G k(gx,hy)\,dg\,dh
=\langle\bar\Phi(x),\bar\Phi(y)\rangle
\]
로 정의한다. 따라서 PD이고 양 argument에서 invariant다. Ambient Gaussian처럼 k가 characteristic이면 zero MMD는 두 orbital-mixture measures가 같다는 뜻이다. 이 measure의 quotient pushforward가 원 quotient measure이므로 \bar k는 quotient-characteristic하다. 이 증명은 nonfree strata에도 적용된다.

단측 평균 ∫k(gx,y)dg를 사용하려면 k(gx,gy)=k(x,y)가 추가로 필요하다. 그렇지 않으면 G={±1}, k(x,y)=(1+x)(1+y)에서 단측 평균=1+y이므로 symmetric조차 아니다. 두 평균의 정의 또는 동시 불변성 조건을 생략해서는 안 된다.

### A14 (증명 P19에 연결) — Quotient-kernel finite-rank validity
**판정: PROVED_WITH_HYPOTHESES.**

X1,...,XN이 exchangeable이고 kernel bandwidth/training/score 선택 전체가 row-equivariant이면 scores도 exchangeable이다. E01의 rank lemma로 보수적 p는 superuniform. 고정 external training 또는 모든 행에 동일한 leave-one-out kernel score는 충분한 구성이다. 관측행만 보고 bandwidth를 선택한 뒤 그 선택을 다른 pseudo-observation에는 재실행하지 않는 절차는 이 정리를 만족하지 않는다.


---

# B. MES tensor geometry, cubic terms, dynamics

## B01 — Sky RMS와 PSTF norm
**판정: PROVED.**

τ_L n^L=δT_l/T0, e_l²=(2l+1)C_l/(4πT0²)로 정의한다. A01–A02의 Parseval과 Δ_l identity를 결합하면
\[
||\tau_l||²={||c_l||²\over T0²\Delta_l}
={(2l+1)!!\over l!}e_l².
\]
따라서 ε2^PSTF=√(15/2)e2, ε3^PSTF=√(35/2)e3이다. 이것은 norm 변환 정리다. 한 observer에서의 norm이 MES 적용 domain 전체의 상한이라는 명제는 여기서 나오지 않는다. [R2]의 multipole normalization과 비교한다.

## B02 — STF₂ orbit의 semialgebraic cusp
**판정: PROVED.**

s₂=trS²,s₃=trS³이면 characteristic polynomial은 z³-s₂z/2-s₃/3이고 discriminant는 D=s₂³/2-3s₃²이다. Real symmetric S이므로 s₂≥0,D≥0. 반대로 s₂≥0,D≥0인 실수 pair는 이 cubic의 세 실근을 주고 근의 합=0, 제곱합=s₂, 세제곱합=s₃다. 그 근을 diagonal에 놓은 S가 존재한다. 같은 spectrum의 symmetric S들은 orthogonally conjugate이며, 필요하면 eigenframe의 한 축 부호를 바꿔 conjugator를 SO(3)로 만들 수 있다. 따라서
\[
0\le s₂\le U_σ,\quad 6s₃²\le s₂³
\]
는 이 norm body의 정확한 orbit image다. 원 tensor body가 convex라고 해서 이 cusp image도 convex라고 결론내리지는 않는다.

## B03 — Sharp cubic inequality
**판정: PROVED.**

B02의 D≥0에서 |s₃|≤s₂^{3/2}/√6. 등호는 D=0, 즉 두 고유값이 같은 경우이며 spectrum=(2a,-a,-a)에서 직접 포화된다. S=σ/(√6H)이므로
\[
{|trσ³|\over H³}\le6U_σ^{3/2}.
\]
S의 norm upper bound가 물리적으로 정당화된다는 전제와 이 순수 대수적 implication을 구분한다.

## B04 — Higher traces의 recurrence
**판정: PROVED.**

Cayley–Hamilton S³=(s₂/2)S+(s₃/3)I에 S^{n-3}을 곱하고 trace하면
\[
r_n={s₂\over2}r_{n-2}+{s₃\over3}r_{n-3},\qquad
r_0=3,\ r_1=0,\ r_2=s₂.
\]
특히 r4=s₂²/2. 따라서 S 하나의 higher trace들은 독립적인 고유값 정보가 아니다. Wolfram에서 arbitrary 다섯 성분 STF matrix에 대한 CH와 r4 residual을 정확히 0으로 확인했다.

## B05 — Spectral 및 directional bound
**판정: PROVED.**

어떤 eigenvalue λ에 대해서도 다른 두 근 μ,ν의 합=-λ. Cauchy inequality로 μ²+ν²≥λ²/2, 따라서 λ²≤2s₂/3. 그러므로
\[
||S||op\le\sqrt{2s₂/3}\le\sqrt{2U_σ/3},\qquad
{|nᵀσn|\over H}\le2\sqrt{U_σ},\quad||n||=1.
\]
Uniaxial S와 maximal eigenvector n에서 sharp하다.

## B06 — Closed shear–vector moment cone
**판정: STRENGTHENED.**

m_k=vᵀS^k v라 하자. CH가 m3=s₂m1/2+s₃m0/3, m4=s₂m2/2+s₃m1/3을 준다. 따라서
\[
G=\begin{pmatrix}m0&m1&m2\\m1&m2&m3\\m2&m3&m4\end{pmatrix}\succeq0.
\]
여기서는 necessary condition을 넘어 충분성도 증명할 수 있다. s₂,s₃가 B02의 real-spectrum 조건을 만족한다고 하자. 다항식 p(z)=z³-s₂z/2-s₃/3의 companion multiplication matrix를
\[
C=\begin{pmatrix}0&0&s₃/3\\1&0&s₂/2\\0&1&0\end{pmatrix}
\]
라 하면 정의상 GC=CᵀG이다. 이 항등식은 Wolfram exact algebra로도 확인했다. G≥0이면 kerG는 C-invariant이며 quotient R³/kerG에서 G가 양의 definite inner product를 정의하고 C가 self-adjoint가 된다. Spectral theorem으로 C의 eigenvalues는 p의 실근이고, cyclic vector [1]의 spectral weights p_j≥0가 있어 m_k=Σp_j λ_j^k다. 같은 distinct eigenvalue에 속하는 무게를 S의 해당 eigenspace 내 한 vector 성분에 배치하면 실제 (S,v)를 얻는다. Repeated roots도 quotient self-adjointness가 Jordan part를 제거하므로 이 증명에 포함된다. G=0이면 v=0을 택한다.

따라서 real-spectrum 조건, m0≥0, CH closure, G≥0은 이 finite moment problem의 정확한 feasibility characterization이다. 이는 dynamics나 Einstein constraints까지 충족한다는 충분조건은 아니다.

## B07 — Spectral weights 복원
**판정: PROVED_WITH_HYPOTHESES.**

Simple roots λ_i에서 Lagrange projector는
\[
P_i={S²+\lambda_i S+(\lambda_i²-s₂/2)I\over3\lambda_i²-s₂/2}.
\]
Polynomial p를 (z-λ_i)로 나눈 식과 p'(λ_i)를 쓰면 P_iP_j=δijP_i, ΣP_i=I다. 따라서
\[
p_i=vᵀP_i v={m2+\lambda_i m1+(\lambda_i²-s₂/2)m0\over3\lambda_i²-s₂/2}=v_i²\ge0.
\]
이 식은 distinct eigenvalues에만 직접 적용된다. Degenerate eigenspace 안의 individual components는 invariants에서 복원되지 않고 total spectral weight만 정의된다.

## B08 — Gram positivity
**판정: PROVED.**

임의 z∈R³에 대해 zᵀGz=||z0v+z1Sv+z2S²v||²≥0이므로 G≥0. 또한 detG=det[v,Sv,S²v]². Simple-spectrum case에서는 G=Vdiag(p_i)Vᵀ, V invertible이므로 G≥0 iff 모든 p_i≥0. Degenerate case의 충분성은 B06의 quotient argument가 제공한다.

## B09 — Sharp coupled determinant bound와 parity
**판정: PROVED.**

A06에서 κ²=(p1p2p3)D. p1+p2+p3=m0 및 p_i≥0에 AM–GM를 적용하면
\[
\kappa²\le{m0³\over27}\left({s₂³\over2}-3s₃²\right).
\]
D>0일 때 p_i=m0/3에서 sharp하며 D=0이면 양변0이다. s₂,m0>0에서
\[
{|\kappa|\over m0^{3/2}s₂^{3/2}}\le{\sqrt{1-J_S²}\over3\sqrt6},\quad
J_S=\sqrt6s₃/s₂^{3/2}.
\]
Polar v이면 improper rotation 아래 κ→det(R)κ. Axial v이면 각 열에 det(R)가 한 번씩 더 붙으므로 전체 factor는 det(R)^4=1이다. Vorticity vector를 polar tilt처럼 취급해서는 안 된다.

## B10 — STF(S⊗v) norm identity
**판정: PROVED.**

T_abc=S_(ab v_c)이고 t_a=T_abb=(2/3)(Sv)_a다. STF rank3는
\[
T_{\langle abc\rangle}=T_{abc}-{1\over5}(δab t_c+δac t_b+δbc t_a).
\]
직접 contraction하면 ||T||²=s₂m0/3+2m2/3, trace subtraction의 norm 감소는 3||t||²/5=4m2/15. 따라서
\[
||T_{\langle abc\rangle}||²={s₂m0\over3}+{2m2\over5}\le{3\over5}U_σm0.
\]
마지막 부등식은 m2≤(2/3)s₂m0에서 나온다. Uniaxial S와 maximal eigenvector v로 equality가 가능하다. C02의 boost tensor는 이 STF tensor의 세 배다.

## B11 — Vorticity decay envelope
**판정: PROVED_WITH_HYPOTHESES.**

선택한 congruence가 geodesic이고 expansion H>0인 구간에서 exact kinematic identity
\[
\dot\omega_{\langle a\rangle}+2H\omega_a=\sigma_{ab}\omega^b
\]
를 사용한다. ω≠0이면 d ln|ω|/dt=-2H+\hatωᵀσ\hatω. B05로
\[
-2H-2H\sqrt{U_σ}\le{d\ln|\omega|\over dt}\le-2H+2H\sqrt{U_σ}.
\]
ω=0은 geodesic source-free equation의 invariant state이나 log는 정의되지 않는다. Accelerated congruence의 curl A source가 있거나 Uσ가 시간구간 전체에 유효하지 않으면 이 bound를 그대로 적분할 수 없다. Triad rotation은 이 ω와 다르다.

## B12 — Tilt stress와 cubic shear dynamics
**판정: PROVED_WITH_HYPOTHESES.**

Perfect fluid rest-frame (ρ,p), u=γ(n+v), γ=(1-v²)^(-1/2)로부터 stress-energy를 n에 project하면 π_ab=(ρ+p)γ²v_<a v_b>. 따라서
\[
tr(σ²π)=(ρ+p)γ²\left(vᵀσ²v-{v²\over3}trσ²\right).
\]
이는 exact algebra다. 8πG=c=1에서 일반 geodesic shear-propagation equation의 π contribution은 +π/2이므로 d trσ³/dt의 해당 source는 **3/2 tr(σ²π)**다. 반면 spatially flat Bianchi-I normal-frame Einstein equation에서 dotσ+3Hσ=π가 성립할 때는
\[
\dot I₃=-9H I₃+3(ρ+p)γ²\left(vᵀσ²v-{v² I₂\over3}\right).
\]
이 두 evolution equation의 계수는 다른 축약을 사용하므로 섞지 않는다. Bianchi-I momentum constraint를 충족시키려면 total flux가0이어야 하므로 임의의 single tilted fluid를 그대로 삽입하지 않는다. 이 source의 존재가 모든 초기조건에서 cubic sign flip을 보장한다는 명제도 아니다.

## B13 — MES product body support function
**판정: PROVED.**

K={S∈STF₂:||S||F≤r; ||w||≤s}, r=√Uσ,s=√Uω. 선형 functional A:S+b·w는 A의 STF part에만 의존한다. Cauchy inequality와 독립적인 두 ball의 optimizer로
\[
h_K(A,b)=r||A_{STF}||F+s||b||.
\]
r,s 또는 A_STF,b가0일 때도 해당 항은0이며 optimizer를0으로 선택할 수 있다. 실제 물리 constraints를 더 붙인 K_phys⊂K에서는 이 값이 일반적으로 upper bound일 뿐 equality를 보장하지 않는다.

## B14 — Response image와 SOCP
**판정: PROVED.**

y=L_s S+L_w w라면 LK=L_s B_r+L_w B_s로, 선형 image인 두 (possibly degenerate) ellipsoid의 Minkowski sum이다. Membership은 존재하는 S,w에 대해 y=L_sS+L_ww, ||S||≤r,||w||≤s를 푸는 second-order cone feasibility다. Support는 h_LK(t)=r||L_s^Tt||+s||L_w^Tt||. 이 finite-radius body는 일반적으로 **cone가 아니다**. E07에서 cone projection score를 쓸 때 이 차이를 반영해야 한다.

## B15 — Polynomial response의 compact optimization
**판정: PROVED_WITH_HYPOTHESES.**

독립 STF/vector coordinates에서 K는 polynomial norm inequalities로 정의되는 compact semialgebraic set이다. 실제 response f가 그 coordinates의 polynomial이면 Weierstrass theorem으로 extrema가 존재하며 polynomial optimization으로 표현된다. Rational response는 분모가0에서 떨어져 있다는 조건과 보조변수 constraints가 필요하다. Tilt를 |v|<1이라는 열린 영역으로만 제한하면 compactness가 없고 γ는 발산하므로 이 theorem을 적용할 수 없다. βmax<1 같은 closed bound가 필요하다.

## B16 — SOS hierarchy convergence
**판정: PROVED_WITH_HYPOTHESES (표준 Putinar 정리를 사용한 증명).**

K={g_i≥0,h_j=0}, f polynomial, quadratic module+ideal이 Archimedean이라고 하자. f*=min_K f. 임의 ε>0에서 f-f*+ε>0 onK이므로 Putinar Positivstellensatz에 의해 finite-degree SOS certificate가 존재한다. 충분히 높은 hierarchy order d에서는 lower bound ρ_d≥f*-ε, 모든 d에서는ρ_d≤f*, 그리고ρ_d는 단조증가한다. 따라서ρ_d→f*. 이것은 arbitrary finite d에서 exact optimum 또는 finite termination을 보장하지 않는다. 제시한 norm balls에는 R-||x||² constraint를 포함해 Archimedean 조건을 명시적으로 확보할 수 있다. [R6]

## B17 — Commuting shear history
**판정: PROVED.**

[σ(t),σ(s)]=0인 적분가능 symmetric STF history에서 F'=σF,F(t*)=I이면 F=exp(∫σdt)는 SPD. 따라서 B=(1/2)log(FᵀF)=∫σdt이고
\[
||B||F\le\int||σ||Fdt\le\sqrt6\mathcal I,
\quad|trB³|\le6\mathcal I³,
\quad\mathcal I=\int H\sqrt{Uσ}\,dt.
\]
이 bound의 **norm 상수는 비가환 경우에도 동일하게 유지됨**을 B18에서 증명한다. Commutativity가 필요한 것은 B=∫σdt라는 행렬 등호이지 이 Frobenius bound가 아니다.

## B18 — Noncommuting logarithmic endpoint bound
**판정: STRENGTHENED.**

σ(t) symmetric STF이고 integrable, F'=σF,F(t*)=I라 하자. Singular values s_i(F)>0의 log를 b_i=log s_i라 한다. b_i는 절대연속이며 거의 모든 t에서 left singular frame U에 대해
\[
\dot b_i=u_iᵀσu_i.
\]
Repeated singular value에서는 해당 block에 restriction된 symmetric σ를 diagonalize하는 frame을 선택하면 같은 derivative statement가 성립한다. 따라서
\[
||\dot b||₂²=\sum_i(u_iᵀσu_i)²\le||σ||F².
\]
b(t*)=0이고 B_eff=(1/2)log(FᵀF)의 eigenvalues는 b_i이므로
\[
\boxed{||B_{eff}||F\le\int||σ||Fdt\le\sqrt6\mathcal I.}
\]
또 각 |dot b_i|≤||σ||op로 ||B_eff||op≤∫||σ||opdt≤2I. Liouville formula detF=exp∫trσ=1로 trB_eff=0.

원문의 2√2 I Frobenius bound는 참이지만 비최적이다. 비가환성 때문에 그 느슨한 계수를 지불할 필요가 없다. Skew frame-rotation Ω가 F'=(σ+Ω)F에 있어도 uᵀΩu=0이라 같은 singular-value bound가 성립한다.

더 강한 reachable-set 명제: a(t)=√6H√Uσ, R=∫a>0로 정하고 다른 dynamics constraints 없이 ||σ(t)||F≤a(t)만 요구하면 가능한 B_eff의 집합은 정확히 {B∈STF₂:||B||F≤R}다. Necessity는 위 증명. Sufficiency는 σ(t)=a(t)B/R를 택하면 budget 안에서 F=expB를 얻는다. R=0이면 B=0만 가능하다. 이 충분성은 unconstrained matrix flow에 대한 것이며 Einstein–matter admissibility가 아니다.

## B19 — Endpoint cubic bound의 sharp constant
**판정: STRENGTHENED; 원문의 16/√3을 sharp라고 부른 부분은 거짓.**

B03와 B18을 결합하면 비가환 history까지
\[
\boxed{|trB_{eff}³|\le6\mathcal I³.}
\]
σ(t)=H(t)√Uσ(t)diag(2,-1,-1)를 택하면 B=I diag(2,-1,-1), trB³=6I³이므로 constant6은 sharp하다. 따라서 16/√3≈9.24라는 더 큰 계수는 유효한 느슨한 upper bound일 수 있지만 sharp일 수 없다. Sharper Frobenius 결과 없이도 operator bound와 tracezero로 직접 constant6을 얻을 수 있다.

## B20 — MES endpoint incompatibility
**판정: PROVED_WITH_HYPOTHESES.**

Exact inverse가 동일한 tensor/endpoint convention의 B_obs를 제공하고, 전 구간·동일 congruence에서 MES norm budget이 유효하다고 하자. ||B_obs||op>2I 또는 ||B_obs||F>√6I 또는 |trB_obs³|>6I³이면 B18–B19의 필요조건과 모순이므로 해당 가정들의 conjunction을 만족하는 history는 없다. 이는 위반 원인이 Bianchi geometry인지, emission model인지, MES premise인지 판별하지 않는다. Bound 내부에 있다는 사실만으로 Einstein–matter solution의 존재는 증명되지 않는다. 관측 uncertainty가 있는 B_obs의 point estimate 하나만으로 물리 가정을 기각할 수도 없다.

## B21 — Perturbative remainder와 Hausdorff stability
**판정: REFUTED_AS_STATED WITHOUT A COMMON PARAMETERIZATION; 제한판 증명.**

'모든 실제 state가 선형 state 하나와 δ 이내다'는 one-sided approximation만으로 양방향 Hausdorff bound는 나오지 않는다. K_lin=unit ball, K_exact={0}, δ=0이면 모든 exact point는 K_lin에 정확히 들어가지만 d_H(K_lin,K_exact)=1이다. 같은 parameter domain Θ의 maps f,g가 sup_θ||f(θ)-g(θ)||≤δ를 만족할 때에만 image sets의 양방향 d_H≤δ가 직접 성립한다. MES body가 실제 solution 집합의 outer bound일 뿐이라면 K_exact⊂K_lin⊕Bδ라는 directed inclusion만 주장해야 한다.

점별 cubic remainder는 독립적으로 참이다. S=S1+R이면 trace cyclicity와 Frobenius inequalities로
\[
|trS³-trS1³|\le3||S1||F²||R||F+3||S1||F||R||F²+||R||F³.
\]
S1=O(ε),R=O(ε²)이면 error=O(ε⁴). 실제 bound의 상수와 uniform domain은 별도 assumptions다. Ball radii를 U로 parameterize할 때 d_H=|√U-√V|이므로 U=0 근처에 uniform Lipschitz inU를 주장할 수도 없다.

## B22 — Scalar-only directional fabrication no-go
**판정: PROVED.**

입력 z가 trivial SO(3) representation에 속하고 f(z)∈STF_l, l≥1가 equivariant라면 모든 G에서 f(z)=f(Gz)=Gf(z). STF_l에는 nonzero invariant vector가 없으므로 f(z)=0. Vector도 동일하다. 일반 rank2 tensor에는 δ_ab가 invariant이므로 f(z)δ_ab는 가능하지만 STF shape가 아니다. Direction-indexed scalar field q(n)는 trivial representation이 아니므로 그 angular moments를 계산하는 것은 이 no-go와 충돌하지 않는다. Randomly sampled isotropic directions도 결정된 물리 방향의 추출이 아니다.


---

# C. Boost response와 exact endpoint inverse

## P16 — 정확한 Lorentz pullback과 quadrupole→octupole coupling
**대상: C01–C02.**

먼저 바깥쪽 시선 n과 boost 부호를 고정한다. β∈R³, |β|<1, γ=(1−β²)^−1/2 및
\[
J_\beta=I+\frac{\gamma^2}{\gamma+1}\beta\beta^T,
\quad D(n)=\frac1{\gamma(1-\beta\cdot n)},
\quad n_r=\frac{J_\beta n-\gamma\beta}{\gamma(1-\beta\cdot n)}
\]
로 두면 thermodynamic blackbody temperature의 정확한 변환은
\[
T_o(n)=D(n)T_r(n_r).
\]
이는 null four-momentum의 Lorentz 변환과 occupation number의 불변성에서 나온다. 이 정의를 harmonics에 대입하면
\[
a'_{\ell m}=\sum_{jk}{\cal K}_{\ell m,jk}(\beta)a_{jk},\qquad
{\cal K}_{\ell m,jk}=\int Y_{\ell m}^*(n)D(n)Y_{jk}(n_r)\,d\Omega.
\]
따라서 정확한 harmonic mixing은 임의 truncation을 가정하지 않은 선형 연산자다. 다른 intensity 변수나 Doppler weight에는 해당 변환을 다시 사용해야 한다. 표준 aberration-kernel 이론과 일치하는 출발점이다 [R5].

1차로 전개하면 D=1+β·n+O(β²), n_r=n−β+(β·n)n+O(β²)이므로
\[
\delta_\beta T=(\beta\cdot n)T-[\beta-(\beta\cdot n)n]\cdot\nabla_{S^2}T.
\]
T_Q=Q:nn에 대해 ∇S²T_Q=2(Qn−(Q:nn)n)이므로
\[
\delta_\beta T_Q=3(\beta\cdot n)(Q:nn)-2(Q\beta)\cdot n.
\]
P11의 STF₃ 항을 n 세 개로 contraction하면
\[
(B_Q\beta):n^3=3(\beta\cdot n)(Q:nn)-\frac65(Q\beta)\cdot n.
\]
따라서
\[
\boxed{\delta O=B_Q\beta=3\mathrm{STF}(\beta_{(a}Q_{bc)})},\qquad
\boxed{\delta d=-\frac45Q\beta}.
\]
원래의 ℓ=4 등 다른 입력 multipole에서 오는 coupling까지 없어진다는 주장이 아니다. 이것은 Q 입력의 선형 response block이다.

## P17 — Orthogonal nuisance와 unrestricted nuisance를 혼동한 C07의 반례
**대상: C07. 원문은 REFUTED.**

원문은 C06에서 정의한 O_perp를 그대로 사용하면서 'arbitrary intrinsic O_perp를 허용하면 β가 point identified되지 않는다'고 했다. 그러나
\[
O_{\rm obs}=B_Q\beta+O_\perp,\qquad O_\perp:Q=0
\]
이면 contraction으로
\[
O_{\rm obs}:Q=M_Q\beta.
\]
Q≠0에서 M_Q가 invertible이므로 β=M_Q^−1(O_obs:Q)는 유일하다. β₁,β₂가 둘 다 가능하다고 해도 M_Q(β₁−β₂)=0이므로 같다. 이것이 **CE07**이며, 직교 nuisance의 크기에는 어떤 제한도 필요 없다.

증명 가능한 수정판은 'unrestricted intrinsic octupole O_int∈STF₃'이다. 이 경우 임의의 d∈R³에 대해
\[
\beta' =\beta+d,\qquad O'_{\rm int}=O_{\rm int}-B_Qd
\]
가 같은 O_obs를 준다. 따라서 unrestricted nuisance는 response 방향을 흡수하여 β를 비식별로 만든다. 실제 primordial octupole이 boost-response와 직교한다는 물리 전제가 없으므로 실제 CMB에 단순 β_hat를 peculiar velocity로 해석하는 것은 여전히 정당화되지 않는다. 원 수학 문장과 물리적으로 의도한 문장을 구분해야 한다.

## P18 — Bianchi-I T^-2 quadratic theorem, 존재·유일성, 퇴화, adequacy
**대상: C08–C14. C11은 generic보다 강한 전역 positive-domain 정리로 증명된다.**

### P18.1. 정확한 endpoint forward map

가정은 homogeneous Bianchi I, 하나의 동일 emission time, 그 emission congruence에서 위치·방향에 무관한 isotropic blackbody T_*, 이후 collisionless achromatic propagation이다. 자유로운 primordial anisotropy, 산란, 전경, 일반 lensing, detector noise를 이 이상화 모형에 몰래 포함하지 않는다. Bianchi I의 spatial translation Killing vectors 때문에 photon covector p_i가 보존된다 [R6].

관측 normal frame의 orthonormal coframe matrix를 L_o, emission spatial metric을 g_*라고 쓰면 p=E_o L_oᵀn이며
\[
\frac{E_*^2}{E_o^2}=n^TL_o g_*^{-1}L_o^Tn.
\]
Phase-space occupation 보존으로 T_r(n)=T_* E_o/E_*이다. 따라서
\[
T_r(n)^{-2}=n^TMn,\qquad
M=T_*^{-2}L_o g_*^{-1}L_o^T\succ0.
\]
SPD matrix는 유일하게
\[
M=T_{\rm iso}^{-2}e^{2B},\qquad \operatorname{tr}B=0,
\quad T_{\rm iso}=(\det M)^{-1/6}
\]
로 분해된다. B는 endpoint anisotropy tensor이며 instantaneous σ(t_o)가 아니다.

P16의 정확한 boost를 적용하면 Doppler denominator가 정확히 소거되어
\[
\boxed{F(n)\equiv T_o(n)^{-2}
=(J_\beta n-\gamma\beta)^TM(J_\beta n-\gamma\beta)}.
\]
따라서 F는 sphere 위에서 정확히 ℓ≤2이다. 일반 비가환 shear에서는 endpoint tensor의 observed-frame 표현은 left strain과 연결되고, right strain과는 polar rotation으로 연결된다. P14의 norm·cubic bound는 양쪽에 동일하지만 절대 orientation을 비교할 때는 이 frame adapter가 필요하다.

### P18.2. Null-cone gauge

η=diag(−1,1,1,1), k=(1,−n),
\[
\Lambda_\beta=\begin{pmatrix}\gamma&\gamma\beta^T\\\gamma\beta&J_\beta\end{pmatrix},
\quad D_0=\begin{pmatrix}0&0\\0&M\end{pmatrix},
\quad A=\Lambda_\beta^TD_0\Lambda_\beta
\]
라 하면 F(n)=kᵀAk. kᵀηk=0이므로 A→A+hη는 F를 바꾸지 않는다.

이 gauge가 유일한 ambiguity임도 증명할 수 있다. 대칭 ΔA가 모든 |n|=1에서 kᵀΔAk=0을 만족한다고 하자. n과 −n을 빼면 시간–공간 cross vector가 0이다. 남은 식은 a+nᵀCn=0이고 모든 방향의 Rayleigh quotient가 일정하므로 C=−aI. 즉 ΔA=−aη다. 이는 단순한 충분조건이 아니라 null-cone restriction의 정확한 kernel이다.

### P18.3. 모든 strictly positive quadratic sky에 대한 inverse existence

이전 후보는 generic uniqueness를 미증명으로 두었지만 더 강한 명제를 증명할 수 있다.

> **정리.** 실수 quadratic sphere function F(n)>0 for every n∈S²가 주어지면, |β|<1과 M≻0의 유일한 쌍이 P18.1의 forward map으로 F를 생성한다. M의 성분은 고정한 rotation-free boost convention의 rest frame에서 표현한다.

임의의 대표 A를 택하고 future unit hyperboloid
\[
\mathbb H^3=\{u:u^T\eta u=-1,\ u_0>0\}
\]
에서 q(u)=uᵀAu를 최소화한다. u=(√(1+r²),rn)로 쓰면
\[
q(u)=r^2\{A_{00}+2A_{0i}n_i+A_{ij}n_in_j\}+O(1).
\]
중괄호는 F(−n)>0이고 sphere compactness 때문에 양의 최소값 δ를 갖는다. O(1)은 n에 대해 uniform이다. 따라서 q는 r→∞에서 ∞로 가며 최소값을 갖는다.

Minimizer u에서 Lagrange multiplier 식은
\[
Au=\lambda_t\eta u,
\quad \eta Au=\lambda_tu,
\quad a\equiv q(u)=-\lambda_t.
\]
이 u를 e₀로 보내는 Lorentz frame에서 A는
\[
A_{\rm rest}=\begin{pmatrix}a&0\\0&C\end{pmatrix}
\]
이고 null positivity는 모든 |n|=1에 대해 a+nᵀCn>0을 요구한다. 따라서 M=C+aI≻0. Gauge를 A+aη로 바꾸면 rest matrix는 diag(0,M)이다. 관측 frame으로 되돌리면 위 forward representation을 얻는다.

### P18.4. 유일성 및 반복 고유값

같은 rest frame에서 다른 future unit vector w=(√(1+|x|²),x)에 대해
\[
q(w)=a+x^TMx>a=q(e_0)\quad(x\ne0).
\]
따라서 timelike minimizer/eigendirection은 유일하다. β=−u_spatial/u₀도 유일하다. 그 β로 inverse boost하고 gauge를 고정하면 M도 유일하다. Repeated spatial eigenvalues는 해당 eigenspace 안의 eigenaxis 선택만 불정으로 만든다. M 자체, matrix log B, T_iso와 β의 유일성은 유지된다. M∝I일 때도 β는 유일하며 anisotropy orientation만 의미가 없다.

ηA의 timelike eigenvalue λ_t와 spacelike eigenvalues λ_i의 차이는 M의 positive eigenvalues다:
\[
\Delta_i=\lambda_i-\lambda_t>0,
\quad
\boxed{T_{\rm iso}=(\Delta_1\Delta_2\Delta_3)^{-1/6}},
\quad
\boxed{B_i=\frac12\log\frac{\Delta_i}{(\Delta_1\Delta_2\Delta_3)^{1/3}}}.
\]
Gauge shift는 ηA→ηA+hI이므로 eigenvectors와 이 differences는 불변이다. 실제 tensor B를 얻으려면 observed eigenvectors에 지정한 inverse boost를 적용한다. 고유값만으로 절대 orientation을 복원했다고 주장하지 않는다.

Strict positivity가 필수다. **CE08:** F=(1−n_z)²는 nonnegative quadratic이지만 n_z=1에서 0이다. |β|<1,M≻0인 forward map은 모든 n에서 strictly positive이므로 이를 만들 수 없다. 이는 infinite-boost/degenerate-rest boundary다.

### P18.5. Adequacy의 의미

정리가 주는 중요한 제한도 있다. **Ideal forward family는 positive quadratic sphere functions 전체와 같다.** 그러므로 F에서 ℓ>2 residual이 0이라는 것만으로 Bianchi I가 원인이라고 식별할 수 없다. 적절한 intrinsic anisotropy도 같은 F를 만들 수 있다. 반대로 noiseless full sky에서 ℓ>2 residual이 nonzero이면 이 이상화된 assumptions의 conjunction은 거짓이다. Mask·beam·noise가 있는 partial data에 동일한 단순 harmonic cutoff를 적용할 수는 없고 그 observation operator를 forward-model해야 한다.

이 inverse에는 calibrated absolute positive T(n), 특히 monopole와 dipole 정보가 필요하다. 이미 제거된 monopole/dipole를 가진 ℓ=2,3 carrier만으로 이 theorem의 full input을 확보했다고 볼 수 없다.

### P18.6. Multifrequency extension와 C14 수정

한 방향의 spectrum이 실제 Planck law B_ν(T)이면 알려진 bandpass R_i(ν)≥0가 0이 아닌 channel에서
\[
I_i(T)=\int R_i(\nu)B_\nu(T)\,d\nu
\]
는 T의 strictly increasing 함수다. 따라서 각 channel의 full nonlinear inversion은 동일 T(n)를 복원하고, 동일 F와 같은 β,M을 준다. 이 증명은 linearized K_CMB calibration이나 서로 다른 beam을 무시하는 것과 다르다.

Frequency incoherence는 *동일 achromatic sky + 올바른 calibration/beam/bandpass + noise 처리*라는 공통 모형의 conjunction을 반증한다. 전경·spectral distortion·instrumental error 중 어느 하나가 원인인지 유일하게 정하지는 못한다. **CE09:** 동일한 T(n)에 channel 하나의 gain 오류만 넣어도 서로 다른 복원 T를 만들 수 있고, 실제 sky의 spectral contamination도 같은 현상을 만든다. 따라서 원래 C14의 causal reading은 이 one-way rejection statement로 좁혀야 한다.

## P20 — Direct-temperature MLE와 모형 오차의 국소 bias
**대상: C15–C17.**

Y_i=f_i(θ)+ε_i, independent ε_i~N(0,σ_i²), known σ_i>0라 하자. θ에 대한 negative log likelihood는 상수항을 제외하면
\[
\frac12\sum_i\frac{(Y_i-f_i(\theta))^2}{\sigma_i^2}.
\]
따라서 direct-T weighted least squares의 global minimizer는 MLE다. Local optimizer가 global minimum을 찾았다는 것은 별도의 수치 주장이다. Parametric identifiability나 finite-sample 효율성도 이 한 줄에서 자동으로 따라오지 않는다.

Unweighted inverse-square fit는 일반적으로 이 likelihood와 다르다. 두 양의 관측 1,2를 constant-temperature 모형에 fit하면 direct estimator는 3/2지만 F=T^−2 unweighted estimator는
\[
\widehat T_F=\frac1{\sqrt{(1+1/4)/2}}=2\sqrt{2/5}\ne3/2.
\]
Full one-to-one transformed likelihood를 Jacobian과 함께 사용하면 정보는 보존되므로, 문제는 invertible coordinate transformation 자체가 아니라 잘못된 noise likelihood다.

**추가로 Gaussian model의 중요한 경계(CE23).** σ>0인 untruncated Gaussian Y는 y=0 부근에 양의 density를 갖는다. 작은 δ에 대해 f_Y(y)≥c>0이므로
\[
E(Y^{-2})\ge c\int_{-\delta}^{\delta}y^{-2}\,dy=\infty.
\]
따라서 E(Y^−2)=μ^−2+3σ²μ^−4+…는 이 Gaussian law에서 유한 expectation의 정확한 식이 아니다. 그것은 0에서 떨어진 bounded/truncated noise 영역에서의 local delta expansion, 또는 rare near-zero events를 제외한 형식 전개로만 사용할 수 있다. 유한 trial에서 관찰한 transform bias는 유용하지만 이 무한-moment 문제를 반증하지 않는다. Positive-domain에서 변환이 invertible이어도 0에 임의로 접근하는 truncated Gaussian에는 같은 divergence가 남는다. Negative branch를 잃는 T→T^−2 변환은 full Gaussian line 전체에서 one-to-one조차 아니다.

이제 y=f(θ₀)+εr로 모형 불일치를 넣고 weighted local least squares를 고려하자. W≻0, J=Df(θ₀) full column rank, θ₀가 interior regular point라면 normal equation을 1차 전개하여
\[
J^TW(J\,\delta\theta-\epsilon r)=O(\epsilon^2),
\quad
\boxed{\delta\theta=\epsilon(J^TWJ)^{-1}J^TWr+O(\epsilon^2)}.
\]
Implicit-function theorem이 regular local solution의 존재를 정당화한다. JᵀWr=0이면 δθ=O(ε²), 즉 first-order bias가 사라진다. Rank deficiency, constrained boundary, multiple minima에는 이 역행렬식이 적용되지 않는다. 더 잘 최적화한 estimator가 모형 불일치 아래 더 편향될 수 있다는 합성 결과와도 모순되지 않는다.

## P21 — Polarization의 'projective generalization'은 아직 명제가 아니다
**대상: C18. 판정: NOT_A_DEFINED_PROPOSITION.**

원 항목은 'T,Q,U 전체에 대한 finite-boost inverse-square/projective generalization'이라는 연구 제목뿐이다. 어떤 transform, emission class, tensor bundle, 관측 domain 또는 결론인지 정의되지 않았으므로 그 문장 자체에는 증명하거나 반증할 truth value가 없다. 이를 증명 완료로 분류하지 않는다.

자연스러운 보편화인 'arbitrary polarized emission도 유한 quadratic representation으로 닫힌다'는 거짓이다(**CE11**). B=0, β=0인 정지 isotropic geometry에서도 intensity는 상수로 두고 arbitrarily high ℓ의 작은 spin-2 polarization을 emission에 줄 수 있다. 작은 amplitude를 택하면 coherency positivity를 보존한다. Collisionless propagation은 이 독립 high-ℓ polarization 자유도를 없애지 않는다. 유한 quadratic scalar coefficients로 임의의 무한-dimensional polarization field를 가역적으로 담을 수 없다. Q 또는 U는 0을 지나고 basis에 따라 부호가 바뀌므로 그 역제곱을 scalar T처럼 취급하는 방법도 일반적으로 정의되지 않는다.

반대로 emission을 strictly isotropic unpolarized blackbody로 제한하면 coherency는 screen identity에 비례한다. Parallel transport와 local Lorentz screen rotation은 identity를 유지하므로 Q=U=0이 보존된다. 이것은 증명 가능한 제한판이지만 새 polarization inverse 정보를 주지 않는 trivial invariant-subspace 결과다. 실제 Thomson source, electron tilt, frequency-dependent polarization을 넣는 다른 정리는 새로 명시해야 한다.


---

# D/E. Identifiability, finite ranks, adaptation, and confidence

## P19 — Finite-rank 기본 정리와 adaptive·weighted 확장
**대상: A14, E01–E04, E08. E02는 decreasing transform 조건을 수정한다.**

### P19.1. 보수적 rank lemma

N개 score s_i에서
\[
r_i=\#\{j:s_j\ge s_i\},\qquad p_i=r_i/N
\]
라 하자. 임의의 정수 k에 대해 r_i≤k인 i는 많아야 k개다. 증명은 scores를 내림차순 tie blocks로 정렬하면 각 block의 rank가 그 block까지의 누적 개수라는 사실이다.

X₁,…,X_N이 jointly exchangeable이고 전체 score map S(X)가 permutation-equivariant이면 scores도 exchangeable이다. 따라서
\[
P(p_1\le\alpha)
=E\left[\frac1N\sum_i1\{r_i\le N\alpha\}\right]
\le\frac{\lfloor N\alpha\rfloor}{N}\le\alpha.
\]
무작위 trial 수나 asymptotic approximation에 의존하지 않는 정확한 finite-sample **superuniformity**다. 모든 scores가 distinct일 때 discrete uniformity가 성립한다. **CE10:** s_i가 전부 같으면 p_i=1이므로 일반 ties에서 uniform equality를 주장하면 거짓이다. Independent continuous tie-breaking을 각 행에 equivariantly 붙이거나 randomized p를 정의하면 정확한 continuous uniform 판도 만들 수 있지만 현재 보수적 규칙과는 다른 검정이다.

Exchangeability는 marginal distribution equality보다 강하다. **CE21:** N=3, U~Uniform(0,1), scores=(U,1−U,1−U)이면 모든 marginal은 Uniform이다. 그러나 P(p₁≤1/3)=P(U>1/2)=1/2>1/3이다. 따라서 각 좌표의 marginal null만 맞거나 score arithmetic만 exact하다는 것으로 joint calibration을 대체하지 못한다.

### P19.2. LOO-ECDF의 정확한 invariance

L_i=#{j≠i:X_j<X_i}, E_i=#{j≠i:X_j=X_i}라 하면
\[
u_i=\frac{2L_i+E_i}{2(N-1)}.
\]
Strictly increasing g는 각 <,= 관계를 보존하므로 정수 numerator 자체를 보존한다. 따라서 fixed upper/lower/two-sided score와 그 complete-family rank도 보존된다. 이 부분은 machine float tie를 사용하지 않고 정수 비교로 구현할 수 있다.

Strictly decreasing g는 L_i를 N−1−L_i−E_i로 바꾸므로 u_i→1−u_i다. 따라서 |u_i−1/2|는 동일하지만 upper와 lower는 서로 교환해야 한다. **CE22:** X=(1,2,3)의 upper rank는 (1,2/3,1/3), g(X)=−X의 upper rank는 (1/3,2/3,1)이다. 원래 E02의 'strictly monotone에서 같은 tail로 불변'이라는 넓은 문장은 거짓이며, increasing 또는 decreasing+tail-swap으로 수정해야 한다.

### P19.3. 선택 과정 전체를 포함한 outer adaptation

각 i에 대해 나머지 행의 unordered data에서 동일 알고리즘 A를 실행해 feature/tail/combiner/model choice를 만들고, 그 choice로 X_i의 score를 계산하자. A가 training-row permutation에 불변이고 evaluation 규칙도 동일하면 S_i(X_π)=S_{π(i)}(X)이다. P19.1을 바로 적용한다. 적절히 행과 함께 순열되는 independent random seeds를 붙여도 같다.

이 증명은 '각 pseudo-observation마다 *전체* adaptation을 다시 수행한다'는 조건에 의존한다. 관측행을 본 사람이 선택한 가설을 그대로 다른 pseudo-observation에 적용하면서 선택 자체는 재실행하지 않는 절차는 포함하지 않는다. 같은 이유로 kernel bandwidth나 cone orientation도 row0만 보고 정하면 안 된다. Gaussian 분포 가정 없이 validity는 성립하지만 power가 높다는 결론은 아니다.

### P19.4. Weighted exchangeability

Unordered pool을 조건으로 어느 행이 query인지의 확률이 정확히 w_i/W, W=Σw_i, w_i≥0라고 하자. 각 candidate score가 query label과 독립적으로 대칭 계산되면
\[
p_i^{w}=\frac{\sum_{j:s_j\ge s_i}w_j}{W}
\]
는 weighted superuniform이다. Proof: scores를 내림차순 block으로 정렬하면 p_i^w≤α인 blocks의 총 weight는 αW 이하이고, query가 그 blocks에 놓일 조건부 확률이 바로 그 weight/W다.

Training law P, query law Q의 density ratio w=dQ/dP가 알려졌다면 joint density를 \(\prod_j p(x_j)\,w(x_i)\)로 쓸 수 있어 이 conditional-label probability를 얻는다. Covariate shift에서 Y|X가 같으면 w(X)로 충분하다 [R10]. 임의/추정 weight가 같은 conditional probability를 갖는다는 추가 증명 없이 이 theorem을 적용할 수 없다.

같은 rank lemma는 quotient-kernel score(A14)와 response-cone score(E08)에 모두 적용한다. Cone score를 Gaussian GLRT라고 해석하는 별도 가정(P25)은 rank validity의 가정이 아니다.

## P22 — Low-z와 remote-shell response의 정확한 rank 조건
**대상: D01–D05.**

### P22.1. Affine radial velocity

V(x)=V₀+(H I+S+W)x, Sᵀ=S,tr S=0,Wᵀ=−W라 하자. x=rn, |n|=1이면
\[
v_r=n\cdot V_0+rH+r n^TSn,
\]
왜냐하면 nᵀWn=−nᵀWn=0이기 때문이다. W의 세 rotation 자유도는 어떤 radial sample에도 나타나지 않으므로 식별 불가다(D02). 이 identity는 xAct abstract index로도 0이 나왔다.

고정 r>0인 full sphere에서 세 bulk coefficients는 ℓ=1, H는 ℓ=0, 다섯 S coefficients는 ℓ=2이다. 서로 다른 harmonic subspaces는 독립이므로 design rank는 9이다. 유한 observation에서는 실제 9-column design matrix의 rank=9가 필요충분조건이다. 방향 coverage, distance errors, radial selection이 주어진 실제 자료에서 이를 충족하는지는 별도 검증한다.

### P22.2. 두 shell의 local/global 분리

Known g_s를 갖는 d_s=β+g_su에서
\[
X=\begin{pmatrix}I&g_1I\\\vdots&\vdots\\I&g_mI\end{pmatrix}.
\]
따라서 rank X=3 rank([1,g])이고
\[
\det(X^TX)=\left(m\sum_sg_s^2-(\sum_sg_s)^2\right)^3.
\]
괄호는 mΣ(g_s−g_bar)²이므로 rank6 iff g_s가 모두 같지 않다. 두 shell이면
\[
u=\frac{d_2-d_1}{g_2-g_1},\qquad
\beta=\frac{g_2d_1-g_1d_2}{g_2-g_1}.
\]
이것은 known response에 대한 대수 정리다. Actual kSZ/pSZ fields의 g_s나 optical-depth calibration이 확보되었다는 뜻이 아니다.

### P22.3. Nuisance-projected condition

y=Rθ+Nη+ε, known C≻0 및 unrestricted additive linear η라 하자. A=C^−1/2R, B=C^−1/2N, P=I−BB^+라고 쓰면 θ의 선형 식별성은 PA의 full column rank와 동치다.

증명: rank deficient이면 nonzero δ에 대해 PAδ=0, 즉 Aδ∈col B이므로 어떤 nuisance 변화로 Rδ를 상쇄할 수 있다. 반대로 같은 noiseless mean을 만드는 두 parameter 쌍은 PA(θ₁−θ₂)=0이므로 full rank이면 θ₁=θ₂다. Noise가 고정 location family로 들어가면 평균 mapping의 식별성이 distributional 식별성과 일치한다. Nonlinear models, bounded/positivity-constrained nuisance의 boundary에는 이 iff를 무조건 적용하지 않는다.

Optical-depth가 amplitude와 곱으로만 나타나 y_s=τ_s A r_s라면 A→cA, τ_s→τ_s/c의 변환이 관측을 보존한다. 자유로운 τ_s 아래 amplitude는 식별되지 않는다(D05). Direction이나 다른 parameter combination까지 모두 비식별이라는 주장은 아니다.

## P23 — Identified sets, test inversion, projection, shared simulations
**대상: D06–D08, E10–E11.**

Population identified set I(P)와 정확한 physical feasible set K가 있으면 새 집합 I(P)∩K는 원 집합의 부분집합이다. 따라서 추가 물리 조건이 식별 영역을 넓힐 수는 없지만, 엄격히 줄어든다는 보장은 없다. I(P)⊂K이면 그대로다. 모든 parameter에서 양인 noisy likelihood support를 곧바로 population identified set이라고 부르지 않는다.

각 θ의 null에서 p_θ(Y)가 superuniform이면
\[
C_\alpha(Y)=\{\theta:p_\theta(Y)>\alpha\}
\]
는
\[
P_{\theta_0}\{\theta_0\in C_\alpha(Y)\}\ge1-\alpha
\]
를 만족한다. 증명은 complement가 정확히 p_θ0≤α인 사건이라는 한 줄이다. Nuisance η가 존재하면 p_θ=sup_ηp_θη는 true η₀의 p보다 작지 않으므로 보수적으로 valid하다. 최적 fit η 하나를 고른 p는 이 논증을 갖지 않는다.

Truth θ₀∈K가 확실하면 Cα∩K도 θ₀에 대해 같은 coverage를 유지한다. 임의의 여러 함수 g_j(θ), 예를 들어 cubic·mixed invariants의 projection intervals를
\[
[L_j,U_j]=[\inf_{\theta\in C_\alpha\cap K}g_j(\theta),\sup_{\theta\in C_\alpha\cap K}g_j(\theta)]
\]
로 만들면 사건 θ₀∈Cα∩K 하나에서 모든 g_j(θ₀)가 동시에 포함된다. 추가 Bonferroni는 필요 없다. 이것이 E11의 정확한 simultaneous 의미다.

두 가지 과장을 막아야 한다.

**CE16 — true-point coverage와 전체 identified-set coverage는 다르다.** 서로 관측적으로 동등한 θ_a,θ_b의 data law가 U~Uniform(0,1)이고 p_a=U,p_b=1−U라 하자. 각 point는 level α에서 coverage1−α지만 두 점을 모두 포함할 확률은 1−2α(α<1/2)이다. 따라서 pointwise-valid test inversion만으로 I(P) 전체의 동시 포함을 주장할 수 없다. 전체 identified set의 inclusion에는 별도의 simultaneous construction이 필요하다.

**CE17 — 추정된 MES body를 공짜로 교차할 수 없다.** Data-dependent K(Y)가 truth를 확률1−β 이상 포함하는 경우에만 union bound로
\[
P\{\theta_0\in C_\alpha\cap K(Y)\}\ge1-\alpha-\beta
\]
를 보장한다. 두 coverage failure를 서로 다른 U interval에 놓으면 이 하한이 포화된다. 같은 CMB에서 만든 two criteria의 독립성을 가정하지 않는다. 전체 data-dependent normalization을 pseudo-observation마다 재계산하는 하나의 rank procedure로 묶는 다른 설계는 P19의 조건 아래 가능하다.

D08의 'shared seed면 반드시 paired contrast rank만 써야 한다'는 필요조건은 거짓이다(**CE12**). 임의로 의존하는 valid p₁,p₂라도 각자 α/2에서 reject한 사건의 union은 확률 α 이하이다. 또는 두 pipeline의 joint statistic을 동일 joint simulation으로 calibrate할 수 있다. Paired contrast는 과학 질문이 difference이고 paired covariance를 활용할 때 좋은 방법이지만 유일한 valid 방법은 아니다.

## P24 — Null-shift 분류와 TV/Wasserstein bound의 정확한 조건
**대상: E05–E06.**

E05는 'exact exchangeability / known covariate shift / concept shift'라는 운영 분류이며 mathematical theorem이 아니다. 세 항목이 exhaustive·disjoint라는 정의도 주어지지 않았다. **CE13:** X marginal이 달라지고 Y|X는 같지만 density ratio를 모르는 경우는 unknown covariate shift다. Known shift가 아니고 concept shift도 아니며 pooled exchangeability도 아니다. 시간 의존성, observation operator mismatch 등도 별도 축이다. 따라서 이 분류를 universal trichotomy theorem으로 선언하지 않는다.

E06의 TV 부분은 정확하다. 전체 실험 law P,Q와 임의 rejection event A에 대해 정의상
\[
|P(A)-Q(A)|\le d_{\rm TV}(P,Q).
\]
P에서 levelα이면 Q에서는 최대 α+d_TV이다. Rank가 전체 pool에 의존할 때 single-row marginal TV만 대입해서는 안 된다. P19의 CE21은 marginals가 같아도 joint rank validity가 실패할 수 있음을 보인다.

일반적인 threshold probability는 W₁ 거리의 연속 함수가 아니다. **CE14:** P=δ_{−ε},Q=δ_{+ε}이면 W₁=2ε→0이지만 threshold0의 upper-tail 확률 차이는 1이다. 따라서 아무 regularity 없는 '작은 Wasserstein이면 작은 coverage gap'은 거짓이다.

증명 가능한 한 버전은 다음과 같다. Coupling(S₀,S₁)이 E|S₁−S₀|≤δ를 만족하고 ideal law의 threshold 부근 concentration이 P(t−h≤S₀<t)≤Lh이면
\[
P(S_1\ge t)\le P(S_0\ge t)+Lh+\delta/h.
\]
증명: S₁≥t,S₀<t이면 S₀≥t−h 또는 |S₁−S₀|≥h이고, 두 번째 사건에 Markov inequality를 적용한다. h=√(δ/L)로 잡으면 excess≤2√(Lδ). 이 조건을 stated interval 범위에서만 사용한다.

또 calibrated p-value 자체의 coupling이면 density 조건 없이도 bound가 있다. p₀가 superuniform이고 E|p−p₀|≤δ이면
\[
P(p\le\alpha)\le P(p_0\le\alpha+h)+\delta/h
\le\alpha+h+\delta/h\le\alpha+2\sqrt\delta
\]
(범위를 넘으면1로 cap). 따라서 Wasserstein 제어를 사용하려면 어떤 law, 어떤 score, 어떤 coupling과 calibration을 뜻하는지 명시해야 한다. 이것은 arbitrary score threshold의 반례를 회피하기 위해 다른 정리를 몰래 대입한 것이 아니라 별도의 sufficient condition이다 [R11].

## P25 — Cone GLRT와 dense alternative의 power
**대상: E07, E09.**

Whitened Gaussian z~N(μ,I)에서 H₀:μ=0 대 H₁:μ∈C, closed convex cone C를 고려한다. Likelihood maximization으로
\[
2\log\Lambda=\|z\|^2-\inf_{c\in C}\|z-c\|^2.
\]
Projection characterization 또는 Moreau decomposition에서 z=Π_Cz+r, Π_Cz·r=0이므로
\[
\boxed{2\log\Lambda=\|\Pi_Cz\|^2}.
\]
Additive unrestricted linear nuisance를 먼저 whitening/project한 경우에도 projected cone이 closed라는 조건 아래 동일하다. Linear image가 nonclosed이면 closure나 attained supremum 여부를 따로 처리해야 한다. Gaussianity는 이 GLRT 해석에 필요하며, finite-rank calibration의 validity는 P19의 exchangeability 조건으로 따로 증명한다 [R9].

**CE15:** MES norm ball은 일반적으로 cone이 아니다. C=[0,1], z=2이면 GLRT score=4−1=3이지만 squared projection은1이다. Bounded convex body에서는 \|z\|²−dist(z,C)²를 사용해야 하며 projection-square 공식을 그대로 사용하면 틀린다.

이제 d≥2, X~N(δ1,I_d), H₀:δ=0, δ>0의 dense equal-sign alternative를 고려한다. Fixed δ의 likelihood ratio는
\[
\exp\left(\delta\sum_iX_i-d\delta^2/2\right)
\]
이므로 Neyman–Pearson lemma에서 levelα의 most-powerful test는 ΣX_i>√d z_{1−α}다. 이 rejection region은 δ>0에 대해 동일하므로 common-positive-mean family에서 UMP다. Continuous likelihood ratio 때문에 같은 size의 다른 region이 positive null probability에서 다르면 power는 엄격히 작다. Max/min-p rejection region은 d≥2,0<α<1에서 이 half-space와 다르므로 모든 δ>0에 대해 strict lower power다.

따라서 원 E09의 '높은 power를 갖는 영역이 존재'보다 강한 판이 증명된다. 다만 independent known-unit Gaussian, same-size, one-sided equal-sign alternative 조건이다. Arbitrary correlations, mixed signs, sparse signals 또는 실제 rank-transformed CMB feature에서는 universal superiority theorem이 아니다.

## P26 — Conditional e-process, optional continuation, lane 선택
**대상: E12–E14.**

F_t에 adapted된 E_t≥0가 E[E_t|F_{t−1}]≤1이고 M₀=1, M_t=∏_{s≤t}E_s라고 하자. 그러면
\[
E[M_t|F_{t-1}]=M_{t-1}E[E_t|F_{t-1}]\le M_{t-1}.
\]
즉 M_t는 nonnegative supermartingale이다. τ_a=inf{t:M_t≥a}에 bounded optional stopping을 적용하면 aP(τ_a≤n)≤1, n→∞에서
\[
P(\sup_tM_t\ge1/\alpha)\le\alpha.
\]
이것이 optional continuation을 포함한 anytime validity의 정확한 내용이다 [R12].

**CE18:** marginal e-values만으로는 곱이 valid하지 않다. U~Bernoulli(1/2), E₁=E₂=2U이면 각각 기대값1이지만 E(E₁E₂)=2다. Shared p-values U,U의 product U² 역시 independent-product law를 따르지 않는다. 예를 들어 c=0.01에서 independent Uniform product tail은 c(1−log c)≈0.0561이지만 perfect dependence의 tail은 √c=0.1이다. '독립성이 없어도 valid한 조합이 존재한다'와 'independence formula를 써도 된다'는 다르다.

각 후보 lane j의 increment가 full past를 조건으로 valid하고 J_t가 F_{t−1}-measurable인 predictable choice이면 E_t=E_{t,J_t}도 conditional expectation≤1을 만족한다. 그래서 새로운 lane을 이전 결과에 따라 선택하면서도 하나의 fixed-null evidence process를 계속할 수 있다. 반면 현재 lane 결과를 모두 본 뒤 가장 큰 값을 선택하는 것은 일반적으로 안 된다. **CE19:** E₁=2·1{U<1/2}, E₂=2·1{U≥1/2}는 각각 mean1이지만 max=2가 확실하다.

이 정리는 statistical evidence를 제어한다. 서로 다른 physical claims/nulls를 추가하려면 그 null별 conditional validity와 error allocation/closure를 별도로 명시해야 한다. 하나의 e-process가 scalar observation을 vector source로 바꾸거나 model assumption을 증명해 주지는 않는다. E13의 유연한 claim envelope는 이 통계적 범위에서만 성립한다.

## P27 — Typed absence의 selection-independence는 필요조건이 아니다
**대상: E15–E16.**

E15의 'selection-independent일 때만'은 거짓이다. **CE20:** iid X_i에서 X_i>1/2인 행만 남기는 symmetric rule을 생각하자. 선택은 명백히 data-dependent다. Unordered 전체 pool을 조건으로 observation label은 모든 N개 행에 uniform이고, 그 label이 retained subset에 있다는 조건을 추가하면 retained m개 행에 uniform이다. Retained-row scores가 equivariant이면 P19의 tie-block argument로 retained rank의 conditional rejection probability≤α다. 제외된 observation에는 p=1을 부여하면 unconditional rejection probability도 ≤α다.

또 다른 valid 방식은 하나라도 typed absence가 있으면 전체 계산을 중단하는 것이다. Absence event가 permutation-invariant이면 no-abort를 조건으로 exchangeability가 유지된다. Abort 시 rejection하지 않거나 p=1로 정의하면 unconditional validity도 보존된다. 이 방법은 실행 가능성이 낮다는 engineering 단점은 있지만, selection-independence가 없어 validity가 자동 파괴되는 것은 아니다. Observation만 특혜로 삭제하거나 한쪽 row만 다른 처리를 하면 이런 증명이 사라진다.

E16의 single-observation 한계는 information bound로 보인다. Reference law P는 무한 reference로 정확히 알려졌다고 해도, query alternative가 Q=(1−ε)P+εR인 경우 모든 levelα test φ∈[0,1]에 대해
\[
E_Q\phi=(1-\epsilon)E_P\phi+\epsilon E_R\phi
\le(1-\epsilon)\alpha+\epsilon<1
\]
(0<ε<1,α<1). 따라서 reference sample size만 키우는 한 query alternative에 대해 power→1인 일반 two-sample consistency를 얻지 못한다. Characteristic kernel이 population distributions를 분리한다는 A12/A13과 모순이 아니다. 두 sample size가 함께 증가하는 consistency와 한 query의 conditional rank는 다른 통계적 목표다.


---

