# 독립 Referee 보고서: Bianchi 공간기하 유사성 및 tilt-orbit 진단

- 심사 성격: **가상의 독립 referee 시뮬레이션**. 실제 학술지 심사나 외부 전문가의 승인이 아니다.
- 심사 기준일: 2026-11-09 (Asia/Seoul)
- 대상: R48 geometry-only Bianchi similarity / normal-frame tilt-orbit extension
- 권고: **Major Revision; novelty claim HOLD**
- 범위: 11개 Bianchi Lie algebra, \(a,n,C\) 분류, 좌불변 3차원 공간곡률, \(SO(3)\) orbit 및 normal-frame matter tilt. Einstein-fluid 배경 진화, Boltzmann/LOS/CMB transfer, likelihood는 심사 대상이 아니다.

## 1. 총평

제안된 계산은 기존 Bianchi 구조상수 형식과 tilted homogeneous cosmology의 기하학을 재사용하여 (i) 추상 Lie-algebra label, (ii) 주어진 불변 계량의 intrinsic curvature, (iii) normal congruence에 대한 matter-tilt orbit을 서로 다른 진단 층으로 분리한다. 이 분리는 개념적으로 타당하다. 곡률만으로 군 작용을 역식별할 수 없는 경우와 반복 고유값에서 tilt 방향의 식별성이 줄어드는 경우를 코드 테스트로 고정하려는 목적도 유용하다.

그러나 핵심 수학적 재료인 \(a,n\) 분해, Bianchi rank/inertia/\(h\) 분류, 좌불변 연결·곡률, tilted-fluid라는 설정은 신규하지 않다. Ferrando–Sáez (2020)는 이미 3차원 homogeneous Riemannian metric의 transitive isometry action을 Ricci tensor와 그 공변미분을 사용해 intrinsic/algorithmic하게 분류하고, 구조 텐서를 대칭 텐서 \(N\)과 벡터 \(a\)로 분해한다. Sáez–Mengual–Ferrando (2024)는 이 접근을 spatially homogeneous cosmology에 적용한다. 더 직접적으로, 2026-07-18 공개된 저자 프리프린트 *A Clifford-algebraic framework for Bianchi cosmologies*는 모든 3차원 skew bilinear operation을 self-adjoint \(N\)과 벡터 \(q\)로 나타내고 Jacobi를 \(Nq=0\)으로 줄이며, Bianchi classification, invariant coframes, 공간/시공간 곡률 및 tilted perfect fluid까지 포괄한다고 초록에서 주장한다. 따라서 현 작업을 새로운 Bianchi 기하 형식이나 새로운 일반 분류 정리로 포지셔닝하면 우선권·중복성 반론이 강하다.

현재 구현의 방어 가능한 기여는 훨씬 좁다. 기존 BASS canonical representative에 연결되는 **geometry-only executable diagnostic**, tilt orbit의 rank/degeneracy stratum을 명시적으로 출력하는 소프트웨어, curvature-only false-positive를 검출하는 exact regression suite다. 이 실용적 방법론 기여가 독립적으로 재현되고 기존 구현과의 차이가 명확해질 때만 짧은 software/methods note로 검토할 수 있다.

## 2. 주요 심사의견

### M1. Bianchi 분류와 \(a,n\) 분해는 선행 결과다

오른손 직교 triad에서
\[
C^k{}_{ij}=a_i\delta^k_j-a_j\delta^k_i+\epsilon_{ijm}n^{mk},
\qquad n^T=n, \qquad n^{ij}a_j=0
\]
로 쓰는 Ellis–MacCallum/Schücking–Kundt–Behr 계열의 분해와 Class A/B, rank/inertia, Class-B \(h\) 분류는 표준 도구다. Ferrando–Sáez (2020)는 구조상수 분류와 metric/transitive action 분류를 구별하면서, 구조 텐서 \(Z\)를 \(N\)과 \(a\)로 분해하고 Ricci tensor 기반의 intrinsic characterization을 전개한다. 따라서 “모든 Bianchi 유형을 처음으로 불변적으로 분류했다”는 주장은 방어하기 어렵다.

### M2. Intrinsic geometry와 Bianchi group action을 구별해야 한다

Ricci tensor가 3차원 Riemann tensor의 대수적 정보를 결정한다는 사실과, Ricci **고유값 스펙트럼만**으로 local-isometry class 또는 simply-transitive group action이 결정된다는 주장은 다르다. 현재 구현이 스펙트럼을 screening fingerprint로 제한한 것은 적절하다. 문서와 API에서는 다음을 계속 분리해야 한다.

1. 추상 3차원 Lie algebra의 Bianchi label.
2. 특정 불변 양의정부호 계량을 가진 metric Lie algebra의 \(SO(3)\) frame orbit.
3. 주어진 Riemannian metric의 local-isometry class.
4. 그 metric에 작용하는 maximal/transitive isometry group 및 선택된 simply-transitive subgroup.

Ferrando–Sáez (2020)는 Ricci eigenvalues/eigenvectors만이 아니라 미분 정보를 사용해 Bianchi–Behr 작용을 intrinsic하게 판별한다. 현재의 Ricci-spectrum screening과 그 논문의 완전한 IDEAL labeling을 동등한 방법으로 표현해서는 안 된다.

### M3. 곡률 퇴화는 유용한 no-go test이지 신규 등가정리가 아니다

Wolfram Language에서 동일한 Koszul/Ricci 컨벤션으로 기호 계산을 재실행했을 때 다음 결과가 재현되었다.

- \(a=0,n=0\) 및 \(a=0,n=\mathrm{diag}(p,0,p)\): 두 경우 모두 \(R_{ij}=0\).
- \(a=(a,0,0),n=0\) 및 \(a=(a,0,0),n=\mathrm{diag}(0,p,p)\): 두 경우 모두 \(R_{ij}=-2a^2\delta_{ij}\).

3차원에서 \(R_{ij}=2K g_{ij}\)이면 해당 계량은 constant sectional curvature \(K=-a^2\)를 갖는다. 이 예들은 서로 다른 Bianchi label 또는 simply-transitive action이 동일한 flat/hyperbolic intrinsic geometry를 가질 수 있음을 보이는 정확한 회귀 테스트로 유용하다. 하지만 flat/open FLRW와 homogeneous geometry의 알려진 관계를 고려하면 이를 새로운 기하학적 발견으로 주장해서는 안 된다.

### M4. \(SO(3)\) × 양의 homothety quotient의 범위를 고정할 것

\[
\kappa^2=|a|^2+\|n\|_F^2,\qquad
(\hat a,\hat n)=(a/\kappa,n/\kappa)
\]
와 \(\hat n\)의 정렬된 고유값은 선언된 **오른손 orthonormal-frame의 proper \(SO(3)\) 작용과 공통 양의 scale**에 대한 제한된 표현의 분류량으로는 자연스럽다. 그러나 이것을 전체 automorphism group, 임의의 basis change, Bianchi metric의 local isometry, 또는 모든 단순추이 작용의 동치류와 혼동해서는 안 된다. Christodoulakis–Korfiatis–Papadopoulos (2002), Schücking–Surowitz–Zhao (2003), Rainer–Schmidt (1995) 계열의 automorphism/similarity 및 locally-isometric homogeneous-space 문헌을 비교표에 포함해야 한다.

또한 \(n\)은 bracket의 antisymmetric index pair를 \(\epsilon_{ijk}\)로 dualize하여 얻은 객체다. orientation-reversing \(Q\in O(3)\setminus SO(3)\) basis change를 논하려면 \(a\)와 \(n\)의 유도된 변환법칙을 각각 명시해야 한다. 단순히 \(n'=QnQ^T\)라고 둘 수 없다. 현재 문서의 “parity-reflected configuration은 구별된다”는 표현은 고정된 orientation 및 \(SO(3)\) quotient 선언을 넘어 물리적 parity-odd invariant를 주장하는 것으로 읽힐 수 있다. 유도된 pseudo-tensor 변환을 증명하기 전에는 “orientation-preserving frame quotient만 수행하며 orientation-reversing 식별은 본 작업에서 정의하지 않는다”로 좁힐 것을 권한다.

### M5. Tilt-orbit moment rank는 유용하지만, orbit completeness 증명이 필요하다

고정된 대칭 \(N=\hat n\)과 벡터 \(v\)에 대해
\[
p_0=v^Tv,\quad p_1=v^TNv,\quad p_2=v^TN^2v
\]
를 쓰면 고유기저에서
\[
(p_0,p_1,p_2)^T=
\begin{pmatrix}1&1&1\\
\lambda_1&\lambda_2&\lambda_3\\
\lambda_1^2&\lambda_2^2&\lambda_3^2\end{pmatrix}
(v_1^2,v_2^2,v_3^2)^T.
\]
이 Vandermonde형 행렬의 rank가 서로 다른 고유값의 수와 같다는 주장은 맞다. 세 고유값이 서로 다르면 세 제곱 성분을 복원할 수 있고, Class A의 \(\det[v,Nv,N^2v]\)는 남은 부호 곱/방향 정보를 담는다. 반복 고유공간에서는 그 eigenspace의 stabilizer가 남아, 그 공간으로 tilt가 투영될 때 연속적인 방향 자유도가 남는다.

Class B의 Jacobi 조건은 \(a\in\ker N\)를 주므로, \(\hat a\cdot v\)와 \(\hat a\cdot(v\times Nv)\)를 추가하면 kernel 축 및 두 nonzero eigendirection에 관한 상대 방향 정보를 보충할 수 있다. 특히 rank-0(Type V), rank-1(Type IV), rank-2의 unequal/repeated nonzero eigenvalue stratum을 분리한 증명이 필요하다. 모멘트 행렬 rank는 squared component 복원 가능성을 말하며, 전체 \(SO(3)\) orbit의 complete invariant 여부는 stabilizer와 추가 pseudoscalar를 포함해 별도로 보여야 한다.

현재 문서의 설명은 증명의 개요로는 합리적이지만, 모든 stratum에서 필요충분하다는 정리·증명이 아직 제출되지 않았다. 2026 Clifford 프리프린트의 초록은 complete orbit proofs를 부록에 둔다고 주장한다. 해당 파일이 restricted되어 line-by-line 비교를 할 수 없으므로, 본 연구의 tilt-orbit 조합에 우선권이 있다고 말할 수 없다.

### M6. 구현 입력 계약과 검증 계층

코드 검사에서 세 경계 문제가 발견되어 이번 patch로 보완했다.

- structure tensor builder는 대칭성은 검사했지만 \(na=0\) Jacobi 조건을 직접 검사하지 않았다.
- Ricci ingress는 하위 두 지수의 antisymmetry만 검사했으므로, Lie bracket가 아닌 skew bilinear map에도 Ricci contraction을 수행할 수 있었다.
- tilt squared-component recovery는 입력 \((a,n)\)의 Jacobi 조건을 재확인하지 않았고 \(speed_squared\ge1\)도 허용할 수 있었다.

이번 patch는 builder와 recovery ingress에서 \(na=0\)를 확인하고, Ricci ingress에서 bracket Jacobi identity를 직접 확인하며, 역산 입력에 \(0\le |v|^2<1\)을 요구한다. 추가 회귀 테스트는 위 실패 입력과 11개 canonical Bianchi 유형 각각의 proper-rotation/common-scale 변환을 대상으로 한다. 실제 통과 여부는 새 전용 GitHub Actions 결과로 판단해야 하며, 커밋 직후에는 **PENDING**이다.

### M7. 통합 CI 실패는 물리·수학 오류와 분리해야 한다

현재 PR04 matrix의 Python 3.10–3.13 job은 compile, import compatibility, theorem/property gate, architecture boundary까지 통과했다. 그 뒤 broad pytest collection에서 Cobaya 테스트 4개와 Astropy 테스트 3개가 선택적 의존성 부재로 import되지 않아 중단되었다. 즉, 기록된 실패는 Bianchi 수학 테스트가 실패한 것이 아니라 기존 broad regression tier의 optional dependency 문제다. 그렇더라도 full regression gate를 PASS로 부를 수는 없다. 이를 분리하기 위해 새 Bianchi 전용 matrix workflow를 추가했으며, 결과가 돌아오기 전까지 구현 검증은 pending이다.

## 3. 항목별 판정

| Claim | 심사 판정 | 근거 및 허용 표현 |
|---|---|---|
| Ellis–MacCallum \((a,n)\) 및 11-type label | ESTABLISHED | 표준 Bianchi 분류. 신규성 주장 금지 |
| 제한된 \(SO(3)\) × positive homothety fingerprint | DERIVED / NARROW | 선언된 표현 공간에서의 spectral normal form. 전체 metric equivalence는 아님 |
| Ricci-spectrum screening 및 두 cross-type degeneracy | DERIVED + SYMBOLICALLY CHECKED | 정확한 no-go regression examples. 새 기하학적 발견으로 주장하지 않음 |
| Tilt moments와 Vandermonde rank | DERIVED | squared eigenframe component map의 rank statement |
| Class-A/B pseudoscalar를 포함한 전체 orbit completeness | PLAUSIBLE / PROOF REQUIRED | stabilizer별 필요충분 증명과 parity convention이 남음 |
| 2026 Clifford preprint 대비 우선권 | UNRESOLVED / HIGH OVERLAP | DOI metadata와 abstract 확인. full text restricted, peer review 전 |
| 현재 코드 통합 검증 | PENDING_TARGETED_CI | 새 전용 workflow 결과 전에는 PASS 불가 |
| 관측 가능한 Bianchi family 식별 | NOT CLAIMED | 관측 forward model·Einstein constraints·likelihood 없음 |

## 4. 필수 수정과 게이트

1. 이 연구를 “새 Bianchi classification” 또는 “새로운 coordinate-free Bianchi formalism”이 아니라 **기존 BASS 구조를 이용한 geometry-only software diagnostic 및 rank-stratified tilt identifiability audit**로 재포지셔닝한다.
2. Ferrando–Sáez 2020/2024와 2026 Clifford preprint를 related-work 표에 넣고, 해당 문헌 대비 차이를 코드 API·canonical fixture provenance·테스트 계약으로 특정한다.
3. 모든 rank/eigenvalue multiplicity stratum에 대해 stabilizer, orbit parameter, invariant set, residual ambiguity를 표로 정리한다. orientation-reversing frame change의 \(n\) 변환도 별도 유도한다.
4. 새 전용 workflow에서 Python 3.10–3.13 실제 pytest/compile이 통과해야 한다. 전체 PR04 회귀는 선택적 의존성을 정리하기 전까지 별도 blocker로 남긴다.
5. 실제 tilted Einstein-fluid solution 또는 관측 가능량을 주장하기 전에는 Hamiltonian/momentum constraints와 물질 보존식을 만족하는 background를 별도로 구성해야 한다. 이번 scope에는 추가하지 않는다.

## 5. 출판 가능성 판단

현재 상태로는 **신규 일반 기하 이론 논문으로는 Major Revision 이상**이며, 우선권은 HOLD다. 다만 독립 테스트가 통과하고 orbit completeness 증명이 닫히면, 기존 Bianchi algebra/metric theory를 새로 주장하지 않는 범위에서 software/methods note를 검토할 수 있다. 핵심 문장은 “Bianchi geometry를 새로 분류했다”가 아니라 “주어진 canonical \((a,n,C)\) 데이터에서 구조 label, intrinsic curvature screen 및 normal-frame tilt orbit의 식별가능성과 비식별 strata를 서로 분리해 계산하고, 알려진 geometry degeneracy를 regression guard로 제공한다”여야 한다.

## 6. 핵심 선행문헌

1. Ellis & MacCallum (1969), *A class of homogeneous cosmological models*, Commun. Math. Phys. 12, DOI: https://doi.org/10.1007/BF01645908.
2. King & Ellis (1973), *Tilted homogeneous cosmological models*, Commun. Math. Phys. 31, DOI: https://doi.org/10.1007/BF01646266.
3. Wainwright & Ellis (eds.) (1997), *Dynamical Systems in Cosmology*, DOI: https://doi.org/10.1017/CBO9780511524660.
4. Ferrando & Sáez (2020), *Homogeneous three-dimensional Riemannian spaces*, Class. Quantum Grav. 37 185011, arXiv: https://arxiv.org/abs/2004.01877, DOI: https://doi.org/10.1088/1361-6382/ab9880.
5. Sáez, Mengual & Ferrando (2024), *Spatially-homogeneous cosmologies*, Class. Quantum Grav. 41, arXiv: https://arxiv.org/abs/2409.15854, DOI: https://doi.org/10.1088/1361-6382/ad7664.
6. Christodoulakis, Korfiatis & Papadopoulos (2002), *Automorphism Inducing Diffeomorphisms, Invariant Characterization of Homogeneous 3-Spaces and Hamiltonian Dynamics of Bianchi Cosmologies*: https://scispace.com/papers/automorphism-inducing-diffeomorphisms-invariant-26u04ayuwj.
7. Rainer & Schmidt (1995), *Inhomogeneous Cosmological Models with Homogeneous Inner Hypersurface Geometry*: https://arxiv.org/abs/gr-qc/9507013.
8. Jakub (2026-07-18), *A Clifford-algebraic framework for Bianchi cosmologies*, author preprint (not peer-reviewed; files restricted): https://doi.org/10.5281/zenodo.21432742.
9. Luminet (2026), *A Primer on Spacetime Singularities II: Spatially Homogeneous Cosmologies*, arXiv: https://arxiv.org/abs/2609.25112.

## 7. 최종 판정

**MAJOR REVISION / NOVELTY HOLD / BOUNDED SOFTWARE-METHODS CANDIDATE.** 수학적 핵심 계산은 정당한 표준 도구 위에 세워져 있고 일부 exact no-go 결과는 재현되었다. 그러나 일반적인 Bianchi 분류·intrinsic geometry·tilted-fluid formalism의 신규성은 선행문헌에 의해 강하게 제한된다. 차별성은 orbit-stratified executable diagnostics, 엄격한 입력/Jacobi 검증, 재현 가능한 all-type regression evidence로 한정해야 한다. 실제 CI와 orbit completeness proof 전에는 구현/정리 완결을 주장하지 않는다.


### M8. 일반 회전 불변량 이론과의 관계

이번 문헌 확장에서는 Bianchi 특화 문헌 외에 tensor/vector invariant theory도 확인했다.

- Yehorchenko (2018), *Invariants for sets of vectors and rank 2 tensors, and differential invariants for vector functions* (arXiv:1812.02918)는 임의 차원 Euclidean 공간에서 회전군 아래 벡터와 rank-2 tensor 집합에 대한 functional basis 구성 알고리즘을 다룬다. [원문](https://arxiv.org/abs/1812.02918).
- Shariff (2019 preprint; 2021 Engineering Letters), *The number of independent invariants for m unit vectors and n symmetric second order tensors is 2m+6n−3* (arXiv:1907.09941)는 대칭 2계 텐서와 단위벡터 집합의 독립 회전 불변량 수 및 classical integrity basis 사이의 관계를 다룬다. [arXiv](https://arxiv.org/abs/1907.09941), [published record](https://khazna.ku.ac.ae/en/publications/on-the-number-of-independent-invariants-for-m-unit-vectors-and-n-/).
- Shariff (2023), *On the Smallest Number of Functions Representing Isotropic Functions of Scalars, Vectors and Tensors*, QJMAM 76, 143–161, DOI 10.1093/qjmam/hbac022는 scalar/vector/tensor-valued isotropic functions의 irreducible representation 개수를 더 일반적으로 다룬다. [원문](https://academic.oup.com/qjmam/article/76/2/143/6986233).

따라서 “대칭 텐서와 벡터의 회전 불변량을 구성한다”는 추상적 발상은 신규하지 않다. 다만 이들 자료가 현재의 특정 제약계 (n a=0), Bianchi class/rank strata, normal-frame tilt, Class-A/B 별 stabilizer와 handedness 데이터의 필요충분 orbit separation까지 동일하게 제공하는지는 별도 비교가 필요하다. 이번 심사는 그 정리를 직접 대조·증명하지 못했으므로, 이 차이는 잠정적 연구 질문이지 선점되지 않은 신규성의 증거가 아니다.

**M5 보강 판정:** moments와 pseudoscalars의 조합을 완전한 invariant basis라고 부르지 않는다. 현재 입증된 것은 Vandermonde moment map의 rank statement와 일부 canonical/synthetic tests다. 모든 strata에서의 (SO(3))-orbit completeness는 명시적 stabilizer 분석 및 invariant-theory 선행결과와의 직접 비교가 끝날 때까지 **PROOF REQUIRED**로 남긴다.
