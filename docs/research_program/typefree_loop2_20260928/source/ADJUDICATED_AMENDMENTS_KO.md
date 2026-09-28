# 独立 판정에 따른 정확한 채택 문장과 필수 보완

2026-09-28. 후보 원고의 범위보다 이 문서의 정확한 문장과 가정이 우선한다.
새 분석 항목 13개를 INDEPENDENTLY_REVIEWED_ANALYTIC으로 채택했다.
수치/CAS/Lean/관측 검증 및 학술적 신규성 승격은 없다. 원 historical 상태는 유지한다.

## TF-P1 — 임의 관측자 congruence 1-jet의 국소 실현

고정 smooth Lorentzian metric g, 사건 p 및 미래 timelike U0·U0=−c²를 주면, U0^b K_ab=0인 모든 K_ab는 U(p)=U0, ∇_aU_b(p)=K_ab인 smooth 정규화 미래 congruence의 1-jet로 국소 실현된다. 이 공간은 12차원이며 θ(1), σ_STF(5), ω(3), A(3)와 일대일 대응한다. 고정 Einstein (g,T)도 별도 관측자 U에 대한 결론을 바꾸지 않는다. 고정 N(p), β(p)는 U0만 정하므로 12개 미분 성분의 유한 보편 bound를 주지 않는다.

**필수 가정**

- 4차원, signature (−+++), x0=ct를 포함한 길이 좌표, U·U=−c², A=∇_U U.
- U는 독립 관측자장이다. U를 stress eigenvector, geodesic, dust flow, 공간균질 invariant flow 등으로 추가 제한하지 않는다.
- 각 유한 K마다 충분히 작은 근방을 허용한다. K 전체에 공통 근방 또는 uniform derivative bound는 요구하지 않는다.

**보완/적용 범위**

- 추가 수정 불필요. 표현 시 arbitrary observer와 physically selected matter congruence를 계속 구별하고 국소 존재만 표시한다.

## TF-P2 — stress eigenvector의 spectral-gap 복원 및 공동 상계

T^a_b U^b=−εU^a인 smooth 미래 timelike branch U를 물리 congruence로 선택한다. h=g+u⊗u, u=U/c, S=hTh|rest, L=S+εI, δ=min_i|ε+λ_i|>0 및 D_μ=h(∇_{Eμ}T)u를 정의하면 ∇_{Eμ}U=−cL^(−1)D_μ이고, θ²/3+||σ||_F²+2|ω|²+|A|²/c² ≤ c² Σ_μ|D_μ|²/δ²이다. δ≥δ*>0, ||D||≤d*<∞가 같은 상태에서 주어지면 B*=cd*/δ*라는 공동 rate budget을 얻는다.

**필수 가정**

- T는 symmetric C1 이상이고 선택된 timelike eigenvalue는 spatial eigenvalues와 분리된다.
- E0=u 및 right-handed orthonormal rest triad를 사용한다. D의 norm은 Σ_{μ=0}^3Σ_i(D_μ^i)²라는 observer-positive norm이며 Lorentzian contraction이 아니다.
- 이것은 stress 1-jet와 gap을 입력으로 받는 조건부 bound다. 실제 측정된 d*, δ* 또는 MES 원전의 상계가 제공되었다고 가정하지 않는다.
- T는 실제로 지정한 특정 smooth symmetric stress이다. 그 energy-frame congruence가 historical dust/matter congruence와 동일하다고 자동 가정하지 않는다.

**보완/적용 범위**

- 추가 수정 불필요. norm과 gap의 동일 상태 조건, 실제 stress derivative 예산의 미확보, β가 T와 N에서 결정된다는 범위를 그대로 유지한다.
- P2의 T-selected bound를 dust-MES 또는 다른 component/congruence의 광학 bound와 교차하려면 stress component, frame, congruence, epoch, units 및 같은 상태의 compatibility를 먼저 선언한다. energy frame와 dust rest frame를 조용히 동일시하지 않는다.

## TF-P3 — Einstein-selected congruence: metric 3-jet의 충분성과 2-jet 반례

상수 κ=8πG_N/c⁴, Λ와 Einstein 식 T=κ^(−1)(G+Λg), TF-P2의 비축퇴 timelike eigenvector 선택을 채택하면 metric 3-jet가 U(p), ∇U(p)를 정한다. 일반 smooth Einstein-source class에서는 metric 2-jet, T(p), U(p), β(p), gap를 모두 고정해도 ∇U(p)는 유계이지 않다. 명시적 conformal family g_λ=e^(2φ_λ)η, φ_λ=−b(x0)²−(b/2)Σ_i(xi)²+(λ/2)(x0)²x1, b>0에서 선택 가속도 A1(p)=c²λ/(3b), θ=σ=ω=0이다. 여기서 Einstein 식으로 복원되는 T는 선언한 Λ 배치 아래의 total stress이다. 별도 component stress는 그 split과 필요한 first derivative가 추가로 주어져야 복원할 수 있으며 total-energy congruence가 historical dust/matter congruence와 같다는 결론은 없다.

**필수 가정**

- p=0, x0=ct, b 단위 length^(−2), λ 단위 length^(−3), curvature convention [∇c,∇d]v^a=R^a_bcd v^b.
- 반례에서 Λ=0 및 T_λ=G[g_λ]/κ로 정의한다. congruence는 T의 unique 미래 timelike energy-eigenvector branch다.
- 각 유한 λ마다 충분히 작은 근방만 주장한다. 전역해, λ-공통 근방, dust EOS, perfect-fluid EOS 또는 고정 물질 작용은 가정하지 않는다.

**보완/적용 범위**

- 반례를 Einstein-dust solution으로 명명하지 않는다. p에서 pressureless인 사실은 근방의 EOS를 정하지 않는다.
- 3-jet의 최소 일반 충분 차수라는 말은 선택된 nondegenerate stress-eigenvector 계약에만 적용한다. arbitrary observer는 metric 전체 germ에도 별도 congruence 자료가 필요하다.
- metric 3-jet는 Einstein total stress를 정한다. 물질 성분별 split이 별도로 알려지지 않으면 historical geodesic dust congruence를 복원했다고 부르지 않는다. P2 body와 dust-MES를 합성할 때 explicit component/frame/congruence compatibility를 요구한다.

## TF-S1 — same-latent uncertain-body support/gauge 쌍대성

dim E≥1인 유한 차원 내적공간, 각 상태 Z의 compact convex Bχ(Z)⊂E 및 0∈int Bχ(Z), 비어 있지 않은 joint C를 사용한다. y(Z)=φ(X)−φ_ref(r), r_Z(u)=〈u,y(Z)〉/h_Bχ(Z)(u), U_C(u)=sup_Z r_Z(u)이면 γ_Bχ(y)=sup_{||u||=1}r_Z(u), sup_{||u||=1}U_C(u)=sup_Z γ_Bχ(Z)(y(Z))이다. 모든 Z에서 y(Z)∈Bχ(Z)인 것과 모든 방향 U_C≤1인 것은 동치다. E={0}인 별도 branch는 y=0, gauge=0, membership=true이며 direction profile은 NO_DIRECTIONS로 반환한다.

**필수 가정**

- 분자·기준·몸체가 동일 Z에서 함께 변한다. 서로 다른 marginal extrema나 독립 posterior 곱으로 대체하지 않는다.
- 각 body는 해당 functional output, frame, epoch, 단위, support에 적용 가능한 실제 anchor 또는 명시된 outer body여야 한다.
- maximum/witness를 주장하려면 C compact, y continuous, χ→Bχ Hausdorff-continuous, uniform b0>0 with b0 unit ball⊂Bχ가 추가로 필요하다.

**보완/적용 범위**

- S1의 sphere equality에는 dim E≥1을 추가한다. E={0}이면 sphere가 empty이므로 usual extended-real sup(empty)=−∞를 gauge 0과 동일시하지 않는다. gauge 0 및 NO_DIRECTIONS를 명시한다.
- body가 없거나 유한하지 않거나 0 interior 조건을 충족하지 않으면 본 정리와 비율을 적용하지 않는다. MISSING_ANCHOR/UNBOUNDED_ANCHOR/DEGENERATE_ANCHOR 등 typed 상태를 유지하며 ∞ support를 유한값이나 관측 0으로 바꾸지 않는다.
- 전체 공간에서 lower-dimensional body를 쓰려면 먼저 실제 affine/reference slice의 유한 차원 span으로 제한하고 membership를 확인한다. slice 밖 상태를 0으로 채우지 않는다.

## TF-S2 — joint confidence/predictive/posterior pushforward와 ratio domain

실제로 유효한 joint coverage P_Z{Z∈Cα(D)}≥1−α와 measurable Ψ/event를 가정하면 P_Z{Ψ(Z)∈Ψ(Cα(D))}≥1−α이다. 같은 사건에서 모든 registered functional, direction 및 depth profile의 inf/sup coverage가 동시에 따른다. joint posterior μ_d의 image mass도 같은 포함관계로 보존되지만 frequentist coverage와 다른 주장이다. G_rad=Fa/Fb는 Fb>0에서만 정의하며 이 domain에서 유한 upper bound의 필요충분조건은 모든 상태에 대해 Fa≤M Fb인 finite M의 존재다.

**필수 가정**

- Z에는 참 numerator, reference, anchor/body, 공유 nuisance, 여러 depth와 transport 입력을 함께 포함한다.
- Ψ가 모든 참 상태에서 정의되거나 undefined/unavailable을 명시적 반환값으로 보존한다. positive-denominator branch만 남기는 경우 그 조건부 대상과 coverage를 별도로 지정한다.
- 메커니즘의 calibration이나 실자료 posterior는 이 정리의 결론이 아니라 입력이다. 통계 사건과 random set image의 measurability를 가정한다.

**보완/적용 범위**

- Cα(D)=empty일 때 image도 empty로 유지한다. S1/S3의 nonempty profile을 무리하게 평가하지 말고 EMPTY_SET 상태로 기록한다.
- unavailable anchor 또는 Fb=0인 branch를 삭제한 뒤 원래 무조건 target의 coverage를 주장하지 않는다. typed undefined output 또는 명시된 restricted target/domain을 사용한다.
- 같은 데이터의 reference/body plugin은 참 joint axis를 삭제하므로 원 theorem의 보장이 자동 상속되지 않는다. 실제 joint set/law 또는 별도로 보정된 plugin target을 요구한다.

## TF-S3 — response quotient의 gauge는 fiber 최소값

TF-S1의 compact full-dimensional B와 고정 선형 p:E→V=p(E)에 대해 γ_pB(v)=min_{py=v}γ_B(y), h_pB(u)=h_B(p*u)이다. dim V≥1에서는 sup_{||u||V=1}U_C^p(u)=sup_Z min_{py′=py(Z)}γ_Bχ(Z)(y′)≤sup_Zγ_Bχ(Z)(y(Z))이다. V={0}이면 pB={0}, quotient gauge와 fiber minimum은 0, profile은 NO_DIRECTIONS다. quotient gauge≤1은 B 내부 lift 하나의 존재만 뜻한다.

**필수 가정**

- p는 해당 y-output에 실제 적용되는 response quotient다. k에 대한 response를 임의 nonlinear φ(k)에 그대로 적용하지 않는다.
- fiber minimum에서 각 Z의 χ를 고정한다. 이 algebraic fiber는 실제 coupled physical state C의 fiber와 같다고 가정하지 않는다.
- nonzero kernel 방향의 gauge divergence는 unrestricted full-E fiber에 한정한다. 제한된 physical domain에서는 허용 lift만 사용한다.

**보완/적용 범위**

- dim V=0이면 unit sphere가 없으므로 directional supremum formula를 적용하지 않는다. S3.1 및 S3.2는 그대로 유효하되 gauge/minimum=0, h_{0}(0)=0, NO_DIRECTIONS로 명시하며 0/0을 계산하지 않는다.
- min_{py=v}의 attained lift는 unconstrained fixed-body algebraic lift다. 실제 joint C나 nonlinear physical constraints 아래의 attainment로 확대하지 않는다. 그 경우 C의 허용 fiber에 제한해 별도 infimum을 평가한다.
- missing/unbounded/degenerate anchor에는 compact-body theorem을 적용하지 않는다. 필요시 적용 가능한 상대 span과 참 기준을 먼저 지정한다.

## TF-S4 — 동일 자료법칙의 fiber 및 confidence-diameter 한계

D=μ0+Rk+Nη+ε에서 ε의 전체 법칙이 (k,η)에 무관하고 Rh=Nc이면 두 허용 상태 (k,η),(k+h,η−c)는 동일 자료법칙 P를 갖는다. 함수 f는 허용 response-equivalence fiber마다 상수일 때에만 그 quotient로 내려간다. 동일 law인 두 상태의 f값이 f0≠f1이고 confidence set Aα가 각 상태에서 coverage≥1−α이면 P{diam Aα≥d(f0,f1)}≥max(0,1−2α)이다. 같은 linear response columns를 가진 local boost와 physical tilt는 그 실험에서 분리되지 않으며 모든 depth에서 같은 kernel이면 stacking도 이를 제거하지 않는다.

**필수 가정**

- 관심 함수와 equivalence quotient의 domain을 일치시킨다. full-state nuisance/reference/body가 변하면 실제 full-law 동등성을 확인한다.
- 정리의 실질적 lower bound는 0≤α<1/2에서 양수다. 모든 α∈[0,1]에서는 max(0,1−2α)로 쓴다.
- 두 서로 다른 동일-law 상태가 실제 physical domain에 존재해야 한다. Jacobian에만 성립하는 관계는 해당 선형 근사에만 적용한다.

**보완/적용 범위**

- quotient factorization의 증명은 set-theoretic이다. measurable/continuous quotient function이 필요한 통계 사용에서는 quotient measurable structure 또는 그 regularity를 별도로 명시한다.
- 동일 mean만으로 동일 law를 주장하지 않는다. nuisance 보상 두 상태의 admissibility와 전체 noise/covariance 법칙 고정을 함께 유지한다.

## TF-C1 — compact 선형상의 올바른 connected/semialgebraic 분기

nonempty compact F⊂R^d와 linear l에 대해 l(F)는 compact이고 extrema를 달성한다. F가 connected이면 l(F)는 closed interval이며, F가 semialgebraic이면 l(F)는 finitely many closed intervals and points의 합집합이다. compact와 nonconvex만으로 finite-union 결론은 성립하지 않는다.

**필수 가정**

- finite-dimensional real space, continuous linear l.
- finite-union 결론에는 semialgebraic 가정 또는 별도로 입증된 finite-component 성질이 필요하다.

**보완/적용 범위**

- 원문 general compact/nonconvex finite-union 명제와 corrected semialgebraic successor를 DB에서 별개 statement로 유지한다.
- support/convex hull가 같아도 nonconvex 내부 구조가 같다고 추론하지 않는다.

원 주장에 대한 별도 판정: {"decision": "REJECT", "scope": "compact/nonconvex이면 언제나 finite union이라는 보편 절", "reason": "Cantor counterexample", "preserve": "compact-extrema 부분과 조건을 보강한 successor는 유지; historical DB status는 덮어쓰지 않음."}

## TF-C2 — Gaussian Fisher tail의 수렴과 sufficiency의 구별

독립 full-sky real Gaussian mode degrees of freedom a_lm~N(0,C_l(q)) 또는 q-independent means, C_l(q)>0를 갖는 고정 실험에서 r_l=∂q log C_l at a declared q이면 tail Fisher information은 I_tail=(1/2)Σ_{l>L}(2l+1)r_l²이며 그 유한성은 이 합의 수렴과 동치다. r_l=l^(−p)이면 p>1에서만 수렴한다. Exact low-l sufficiency의 충분조건은 모든 q에서 p_q(dL,dH)=p_{L,q}(dL)g(dH|dL)이고 g가 q-independent인 것이다. Gaussian의 간단한 충분조건은 μH,CHH가 q-independent이고 CLH=0인 것이다. 작은 local Fisher tail만으로 global approximate sufficiency는 증명되지 않는다.

**필수 가정**

- tail formula의 means는 q-independent, modes는 full-sky independent, multiplicity는 real 2l+1이다. q가 log F이면 그것을 명시한다.
- Fisher score/미분은 선언한 regular parameter domain에서 존재한다. infinite sum은 finite-block information의 monotone limit로 해석할 수 있다.
- exact factorization은 특정 q의 한 점이 아니라 전체 parameter domain에서 성립해야 한다. approximate sufficiency는 별도 global law/domain/error metric를 요구한다.

**보완/적용 범위**

- 후보의 response가 정확히 0이라는 문구에는 모든 q와 q-independent mean을 명시한다. 한 parameter 점에서의 ∂qC=0은 exact sufficiency를 주지 않는다.
- cross-block도 q와 무관하게 factorize라는 문구는 위 conditional-factorization 식으로 교체하거나 Gaussian CLH=0의 간단한 충분조건으로 쓴다. 단순히 nonzero CLH가 q-independent인 것은 충분조건이 아니다.
- 수정본의 충분조건 표현을 유지한다. f_sky 곱은 일반 masked experiment의 exact covariance/Fisher law로 승격하지 않는다. r2=1, r_l>0 또는 실제 astrophysical transfer는 별도 검증 대상이다.

원 주장에 대한 별도 판정: {"decision": "REJECT", "scope": "any decaying r_l이면 Fisher tail 수렴이라는 절", "additional_decision": "REOPEN", "additional_scope": "실제 low-l approximate sufficiency 및 astrophysical response", "reason": "1/l 반례; 실제 law와 global error criterion 미제공"}

## TF-C3 — Frobenius에서 universal shear/vorticity ratio는 나오지 않음

timelike smooth congruence의 local hypersurface orthogonality와 vorticity 소멸은 동치지만, 모든 congruence에서 W²=R_WS²Σ²인 고정 universal positive proportionality는 성립하지 않는다. Minkowski에서 u=sqrt(1+|Bx|²)e0+(Bx)^i ei를 쓰면 p=0에서 antisymmetric nonzero B는 θ=σ=0, ω≠0이고 symmetric tracefree nonzero B는 θ=ω=0, σ≠0이다.

**필수 가정**

- 일반 smooth timelike congruence의 국소 진술이며 특정 EOS, spatial symmetry 또는 field equation branch를 추가하지 않는다.
- u·u=−1, physical U=cu. B는 length^(−1)이고 physical kinematic rates는 c를 곱한다.

**보완/적용 범위**

- 특정 물질·기하 branch에서 별도로 증명된 비례식은 그 branch에만 남긴다. 일반 joint budget은 실제 coupled constraints 또는 정당화한 별도 bounds로 만든다.

원 주장에 대한 별도 판정: {"decision": "REJECT", "scope": "Frobenius가 모든 congruence에 양의 고정 shear/vorticity 비례를 강제한다는 해석", "preserve": "추가 branch-specific 물리 가정이 있는 비례식은 별도 REOPEN/검증 가능"}

## TF-C4 — constant source는 depth-independent observable을 보장하지 않음

선언된 line-of-sight response q(L)=∫_0^L s dχ with constant s≠0에서 q=sL이고 F_rad(L)/F_rad(L0)=(L/L0)² for L0>0이다. 따라서 source가 depth-independent라는 사실만으로 accumulated observable 또는 그 radial growth가 depth-independent라는 결론은 나오지 않는다.

**필수 가정**

- 유한 L≥0, fixed nonzero constant source, identity kernel, 동일 units/frame, positive reference L0.
- 이 반례는 선형 integral-response 계약에 대한 것이다. 실제 Einstein–Boltzmann 우주해나 모든 cosmological kernel을 구성하지 않는다.

**보완/적용 범위**

- 현재 G_F는 structured depth/mask/feature transport와 coherence다. 이 반례의 scalar는 별도 G_rad alias로만 사용한다.
- 실제 shear-to-observable kernel, boundaries, visibility, redshift/time mapping가 없는 원 cosmological G_F≡1 주장은 해소되지 않은 것으로 남긴다.

원 주장에 대한 별도 판정: {"decision": "REJECT", "scope": "constant source alone implies constant accumulated observable라는 일반 함의", "additional_decision": "REOPEN", "additional_scope": "특정 물리 transfer에서 constant shear⇒G_F=1이라는 원 cosmological 명제"}

## TF-C5 — unsigned octupole amplitude의 자동 subtraction bound 불가

선형 residual 관계 Lσ=r2−D3에서 선언된 norm과 ||D3||≤b만 있으면 최악의 일반 upper bound는 ||Lσ||≤||r2||+b이며 부호 없는 b를 단순 차감할 수 없다. 작은 octupole amplitude만으로 그 spacetime derivative correction D3의 작은 bound도 얻지 못한다. 실제 추가 공동 제약은 feasible set를 줄일 수 있지만 임의 scalar 감소인자를 정당화하지 않는다.

**필수 가정**

- r2와 D3는 같은 vector/tensor space, norm, frame, epoch와 units에서 비교한다.
- octupole amplitude와 derivative가 다른 함수이면 그 사이의 derivative budget 또는 dynamical relation은 별도 가정이다.
- σ 자체의 bound는 L의 relevant inverse/quotient와 nuisance 조건을 추가해야 한다.

**보완/적용 범위**

- 원 scalar sharpening formula를 theorem으로 승격하지 않는다. exact adopted weak law, derivative budget, signed alignment 및 joint residual inverse-image로 후속 bound를 정의해야 한다.
- plus bound는 ||Lσ||의 bound다. invertibility/target kernel 조건 없이 ||σ|| 또는 MES ceiling로 바꾸지 않는다.

원 주장에 대한 별도 판정: {"decision": "REOPEN", "scope": "원 f=1−min(a3/a2,fmax) physical sharpening formula", "rejected_inference": "unsigned amplitude bound alone licenses subtraction", "reason": "signed opposite correction attains plus bound; amplitude does not control derivative"}

## TF-W1 — finite-window weak response와 bounded target criterion

고정 유한 차원 transported spaces에서 m∈AC([a,b]), s∈L1, A∈L1, w∈C1이고 m′+Ak=s a.e.라 하자. k0=k(t0), finite L≥0 및 ||k(t)−k0||≤L|t−t0| a.e.이면 K_w=∫wAk=∫(ws+w′m)−[wm]_a^b이고 ||Abar_w k0−K_w||≤L∫|w| ||A|| |t−t0| where Abar_w=∫wA. 유한 공통 residual budget를 가진 nonempty finite-dimensional feasible set에서 free linear nuisance를 project한 B=P_N^⊥M에 대해 target Pk가 유계일 필요충분조건은 ker B⊆ker P이다. domain이 k*+S이면 ker B∩S⊆ker P로 바꾼다.

**필수 가정**

- a<b finite, t0∈[a,b]. derivative와 integral는 동일 transported frame에서 비교하며 moving-frame connection은 채택한 balance에 이미 포함한다.
- matrix A는 conditional declared coefficient다. finite β 또는 불확실 A까지 unknown rate에 선형이라고 가정하지 않는다.
- s 및 A integrable, k0 finite와 uniform L finite로 Ak와 모든 displayed integrals가 정의된다. 더 약한 가정도 가능하지만 여기서는 이 충분조건을 채택한다.
- nuisance range는 고정 유한 차원 subspace이고 projected data/residual budget는 finite이며 admissible k에 uniform하다. target은 선형 P, feasible set은 nonempty다.

**보완/적용 범위**

- A 자체의 integrability, displayed weighted norm/error integrals의 finiteness 및 endpoint traces를 명시한다. balance가 Ak만 integrable이라고 보장할 뿐 Abar_w가 자동 정의되는 것은 아니다.
- kernel iff에는 finite-dimensional spaces, fixed projected operator, uniform finite residual bound 및 nonempty feasible set를 명시한다. proper affine domain k*+S이면 ker B∩S⊆ker P를 사용한다.
- 작은 singular value에 따른 큰 bound constant ||H||를 숨기지 않는다. kernel 조건은 boundedness criterion이며 자동 numerical stability나 useful empirical precision을 뜻하지 않는다.
- 실제 m(t),s(t) 또는 동등한 finite-window 자료가 입력되어야 한다. 하나의 static sky에서 확보되었다고 간주하지 않는다. redshift bins에는 dt/dz, source/congruence, path, selection 및 covariance 계약이 필요하다.

