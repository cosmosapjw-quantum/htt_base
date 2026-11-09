# Novelty / scientific significance assessment — geometry-only tilted Bianchi atlas

Date: 2026-11-09  
Decision: **MAJOR REVISION; NOVELTY HOLD AFTER LITERATURE REVIEW**

## 1. Established prior art, not novelty

The following are established and must not be presented as original:
- Bianchi I–IX classification and Ellis–MacCallum (a,n) decomposition.
- Class A/B homogeneous dynamics and tilted perfect-fluid kinematics.
- Tilted class-IV/V/VI_h/VII_h evolution, equilibrium points and asymptotic stability.
- General-relativistic redshift/direction drift and optical Jacobi propagation.
- Bianchi CMB temperature/polarization transfer.

Primary references:
1. Ellis & MacCallum (1969), “A class of homogeneous cosmological models”, Commun. Math. Phys. 12, 108–141, DOI 10.1007/BF01645908.
2. King & Ellis (1973), “Tilted homogeneous cosmological models”, Commun. Math. Phys. 31, 209–242, DOI 10.1007/BF01646266.
3. Wainwright & Ellis (1997), Dynamical Systems in Cosmology, DOI 10.1017/CBO9780511524660.
4. Coley & Hervik (2005), “A dynamical systems approach to the tilted Bianchi models of solvable type”, arXiv:gr-qc/0409100.
5. Hervik, van den Hoogen & Coley (2005), tilted Bianchi IV/VII_h, DOI 10.1088/0264-9381/22/3/010.
6. Marcori, Pitrou, Uzan & Pereira (2018), “Direction and redshift drifts for general observers…”, arXiv:1805.12121.
7. Fleury, Pitrou & Uzan (2015), “Light propagation in a homogeneous and anisotropic universe”, DOI 10.1103/PhysRevD.91.043511.
8. Korzyński & Kopiński (2018), “Optical drift effects in general relativity”, DOI 10.1088/1475-7516/2018/03/012.
9. Pontzen (2009), “Rogues’ gallery: The full freedom of the Bianchi CMB anomalies”, DOI 10.1103/PhysRevD.79.103518.

## 2. Candidate differentiators

The candidate contribution is an operational combination of three layers in one all-11-type, source-backed atlas:

1. Algebraic type layer: recover the Bianchi label and h-stratum from actual (a,n) data, with the BASS canonical axis convention and Jacobi constraint explicit.
2. Intrinsic-geometry layer: compute the left-invariant 3D Ricci tensor directly from C^k_ij and exhibit exact cross-type curvature degeneracies. This makes explicit that a Bianchi label identifies a simply-transitive group action, not necessarily a unique local spatial metric.
3. Tilt-orbit layer: construct SO(3)-invariant moments and handedness pseudoscalars for v relative to the normal congruence, then give rank and condition-number obstructions to recovering its orientation. Repeated-eigenvalue strata create residual azimuthal degeneracies.

This is not “a new Bianchi classification” or “all tilted Bianchi dynamics”. It is a geometry-only similarity and identifiability diagnostic intended to prevent an incorrect mapping from curvature or anisotropy features to a unique Bianchi family.

## 3. Exact no-go examples

- Type I and the flat Type VII_0 representative have identical intrinsic Ricci tensors (zero), while their algebraic Bianchi labels differ.
- Type V and the Type VII_h submanifold n1=n3=p>0 with matched a have Ric=-2a^2 g. In three spatial dimensions this is constant negative sectional curvature K=-a^2, even though the simply-transitive Bianchi group actions have different labels.

The existence of these limits is not claimed as a new discovery. Their value here is to provide automated exact no-go tests for an all-type classifier and a basis for measuring what tilt-orbit information can and cannot recover.

## 4. Quantitative significance already checked

- All eleven canonical (a,n) fixtures classified to expected labels.
- 1,100 randomized SO(3) rotation/common-positive-rescaling cases preserved geometry and tilt fingerprints, with maximum residuals 8.9e-16 and 2.8e-16.
- The rank-three Type VI_0 moment inverse recovered squared eigenframe tilt components to 5.6e-17.
- Repeated-eigenvalue strata fail closed for a unique moment inverse and report a residual azimuth.

These are synthetic algebraic oracles; exact repository tests and independent review remain pending.

## 5. What could make the paper significant

A methods paper could matter if it demonstrates that “Bianchi type from anisotropy/curvature” claims are underidentified unless the group action and matter-frame tilt orbit are represented jointly. The atlas offers:
- invariant screening before expensive physical forward calculations;
- explicit no-go regions where curvature morphology cannot distinguish group labels;
- rank-based statements of which tilt components are recoverable and where inversion becomes ill-conditioned;
- exact boundary and repeated-eigenvalue tests usable by independent codes.

It can prevent over-interpretation and save computation. It does not identify the observed Universe's Bianchi type.

## 6. Novelty risks and hostile-review requirements

1. Invariant theory: review equivalence of metric Lie algebras, invariant theory of symmetric tensors with a distinguished vector, and local-isometry classification of 3D homogeneous metrics. The current search did not establish priority over this broader mathematical literature.
2. Completeness: the (a,n) orbit fingerprint is complete only for the declared orthonormal-frame SO(3) plus common-positive-homothety quotient. Ricci spectrum alone is not a complete local-isometry invariant in general.
3. Physical realizability: an arbitrary (a,n,v) is not automatically a constraint-satisfying tilted Einstein-fluid solution. Current BASS tilt adapters are partial kinematic terms; no all-type constraint solve was performed.
4. Conditioning: near repeated eigenvalues, the Vandermonde moment matrix becomes ill-conditioned before exact rank loss. Practical thresholds must be linked to input uncertainty.
5. Prior overlap: FB-8 already separates GlobalTilt and ObserverBoost. The current work must not duplicate or rename that observer-boost discriminator.

## 7. Provisional publication recommendation

Proceed with a bounded methods-note candidate titled “A rotation-invariant similarity and tilt-identifiability atlas for Bianchi spatial geometries”. Do not claim SCIE novelty as established yet. Priority against the broader invariant/equivalence literature is unresolved. If prior art covers the joint invariant construction, retain the software/benchmark contribution but downgrade the paper claim accordingly.

## 8. Stop rule

No Boltzmann solver, hierarchy completion, LOS, CMB transfer, polarization, Cobaya or observational Bayes factor is authorised. Exit after exact-head tests, one independent mathematical review and at most one bounded repair.

## 9. 독립 referee 문헌 대조 업데이트 (2026-11-09)

**결정 수정: MAJOR REVISION / NOVELTY HOLD.** 선행문헌 재검토 결과, 기존의 promising methods 표현은 지나치게 낙관적이므로 범위를 낮춘다.

- Ferrando & Sáez (2020), *Homogeneous three-dimensional Riemannian spaces* (Class. Quantum Grav. 37, 185011; [arXiv:2004.01877](https://arxiv.org/abs/2004.01877); [DOI](https://doi.org/10.1088/1361-6382/ab9880))는 3D homogeneous Riemannian metric의 transitive isometry actions에 대한 필요충분 intrinsic/algorithmic criteria를 제공한다. Ricci tensor의 eigenstructure와 공변미분을 사용하고, 구조 텐서를 대칭 텐서 N 및 벡터 a로 나타내어 Bianchi–Behr 작용을 구별한다. 따라서 일반적인 Ricci 기반 Bianchi geometry 분류의 신규성은 선행문헌에 의해 선점되어 있다.
- Sáez, Mengual & Ferrando (2024), *Spatially-homogeneous cosmologies* ([arXiv:2409.15854](https://arxiv.org/abs/2409.15854); [DOI](https://doi.org/10.1088/1361-6382/ad7664))는 이 intrinsic classification을 spatially homogeneous perfect-fluid cosmologies에 적용한다.
- Jakub (2026-07-18), *A Clifford-algebraic framework for Bianchi cosmologies* ([Zenodo DOI](https://doi.org/10.5281/zenodo.21432742))는 저자 프리프린트이며 DataCite/Zenodo metadata상 peer review를 거치지 않았다. 초록은 3D skew bracket를 self-adjoint N와 vector q로 encode하고 Jacobi Nq=0, Bianchi classification, invariant coframes, spatial/spacetime curvature 및 tilted perfect fluid까지 다룬다고 명시한다. 파일은 restricted되어 완전한 본문 대조는 하지 못했으므로 우선권의 최종 판정은 unresolved지만, broad coordinate-free formalism claim에는 높은 overlap risk가 있다.
- Tilted-fluid의 normal-to-homogeneity-surface 정의와 kinematics는 King & Ellis (1973)의 표준 범위다. 본 연구는 이를 새 물리 이론으로 주장하지 않는다.
- Automorphism/similarity quotient 및 locally-isometric homogeneous-space 분류는 Christodoulakis et al. (2002), Schücking et al. (2003), Rainer & Schmidt (1995)와 대조해야 한다. 현재 quotient는 오직 선언된 oriented orthonormal SO(3) frame과 common positive homothety에 한정한다.

**허용 가능한 기여 표현:** “BASS canonical (a,n,C) 입력에서 Bianchi label, intrinsic Ricci screening, normal-frame tilt orbit rank/degeneracy를 분리해 출력하고, curvature-only no-go cases와 all-type proper-rotation regression을 제공하는 재현 가능한 geometry-only diagnostic.”

**금지할 표현:** “새로운 Bianchi 분류”, “최초의 좌표독립 Bianchi 형식”, “Ricci spectrum만으로 local-isometry 분류”, “모든 Bianchi 유형에서 물리적으로 실현 가능한 tilted solution”.
자세한 가상 심사는 INDEPENDENT_GEOMETRY_REVIEW_KO.md, claim별 상태는 GEOMETRY_CLAIM_LEDGER.json을 따른다.


## 10. 회전 불변량 이론 선행문헌 추가 (2026-11-09)

일반적인 tensor/vector rotational invariants 자체도 신규 기여로 볼 수 없다. Yehorchenko (2018, [arXiv:1812.02918](https://arxiv.org/abs/1812.02918))는 회전군 아래 벡터 및 rank-2 tensor 집합의 functional invariant basis 구성 알고리즘을 제시한다. Shariff (2019/2021, [arXiv:1907.09941](https://arxiv.org/abs/1907.09941))는 대칭 2계 텐서 및 단위벡터 집합의 독립 불변량 수와 classical integrity basis의 관계를 다루며, Shariff (2023, [QJMAM DOI](https://doi.org/10.1093/qjmam/hbac022))는 scalar/vector/tensor-valued isotropic function의 irreducible representation을 일반화한다.

이 문헌들이 본 연구의 constrained Bianchi data \\(na=0\\)와 Class-A/B stabilizer strata에 대한 정확한 동일 정리를 제공한다고 단정하지는 않는다. 그러나 현재 moment/pseudoscalar 조합만으로 독창적 invariant theory를 주장할 수 없다는 점은 분명하다. 따라서 모든 stratum에 대한 필요충분 orbit-separation 증명 전까지 complete invariant-basis 주장을 보류한다.
