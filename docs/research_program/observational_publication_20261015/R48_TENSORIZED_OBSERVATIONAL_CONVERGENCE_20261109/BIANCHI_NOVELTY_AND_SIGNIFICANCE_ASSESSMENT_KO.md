# Novelty / scientific significance assessment — geometry-only tilted Bianchi atlas

Date: 2026-11-09  
Decision: **PROMISING METHODS CONTRIBUTION; NOVELTY PRIORITY NOT YET ESTABLISHED**

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