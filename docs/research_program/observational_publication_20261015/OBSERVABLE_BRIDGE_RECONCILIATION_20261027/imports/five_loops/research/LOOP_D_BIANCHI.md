# Loop D — Bianchi geometry and the joint anisotropy image

**Internal theory note, 2026-10-26.** Owner: HTT internal theory campaign. Scope: homogeneous spatial initial data and conditional observability; no sky likelihood, evolution solver, native Bianchi transfer, or family identification. Source checkout snapshot supplied as `a55036ad09c53a9215dee3282e425d37cfb95443` (the extracted `sources/repo` has no `.git`, so that identity is supplied, not independently verified here). Signature is \((-,+,+,+)\); \(c\) is explicit. Main finite calculation: `cas/loop_d.wl`, with standard-library exact-rational cross-check `cas/loop_d_check.py` and receipt `cas/loop_d_receipt.json`.

## R1–R3. Question, sources, conventions, and claim domain

The question is what a local anisotropy evaluation can restrict about Bianchi spaces when kinematics, spatial curvature, and initial-value constraints are retained together. The object is a three-dimensional, simply transitive spatial isometry algebra acting on a homogeneous slice, with a positive definite invariant metric and normal \(N^\mu\). The normal is geodesic and hypersurface orthogonal in the synchronous description. Normal-frame shear \(\sigma_{ij}\), expansion \(H>0\), spatial Ricci \({}^{3}R_{ij}\), energy density \(\varepsilon_N\), energy flux \(q_i\), and cosmological constant enter the compatibility calculation. In this note \(\varepsilon_N\) is energy per volume; \(q_i\) is also the energy-flux variable in an orthonormal frame divided by \(c\), so both have energy-density units. Set \(\kappa=8\pi G/c^4\), \(h=H/c\), and \(S_{ij}=\sigma_{ij}/c\); these last two and spatial commutator coefficients have inverse-length units. We take \(K_{ij}=-(h\delta_{ij}+S_{ij})\) for the slice's extrinsic curvature. The sign of \(q_i\) is chosen by \(T_{0i}=-q_i\) in the orthonormal \(e_0=N\) convention.

The primary textbook input is Ellis, Maartens and MacCallum, *Relativistic Cosmology*, §§2.7, 4.7, 6.3–6.5, 18.3, especially equations (18.13)–(18.21) and Tables 18.1–18.2, locally extracted at `text/ellis-relativistic-cosmology.txt`, PDF pp. 479–482 (printed pp. 463–466). Its Table 18.1 gives the canonical nonzero \((n_i,a_i)\); its Table 18.2 explicitly places flat FLRW in I and VII\(_0\), and open FLRW in V and VII\(_h\). The original classification context is Ellis and MacCallum (1969), [*A class of homogeneous cosmological models*](https://link.springer.com/article/10.1007/BF01645908), *Commun. Math. Phys.* **12**, 108–141, DOI 10.1007/BF01645908; the publisher's bibliographic record was checked on 2026-10-26. The observational distinction between a measured sky tensor and a physical response is made in Park, *From a CMB Sky Map to Physical Constraints* (2026-09-07), local text §§1.2, 5–7, and the later `text/20-report-1-.txt`, PDF pp. 3, 13–17 and 24. The retained R32-07-P5 algebra product, `sources/repo/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/science/manuscript.md`, §§1–5, provides the narrower LRS V constraint and Bianchi I radiation-history example. This note extends the *spatial-geometry question* beyond that LRS chart; it does not reuse its LRS identity as a general Bianchi theorem.

The claims below concern a **finite algebraic instantaneous image**, not a posterior or a measured sky image. The Einstein constraints are imposed where stated. An arbitrary fluid can have normal-frame flux and anisotropic stress; the explicit same-matter matched example below uses orthogonal dust on one slice. Dynamical persistence, a photon history, and an observational response have additional inputs. The normal's vorticity is zero, which does not determine a tilted fluid's vorticity.

## R4–R5. Structure constants to spatial curvature

Choose an oriented orthonormal spatial triad \(e_i\), with \(\epsilon_{123}=+1\). Write

\[
 [e_i,e_j]=C^k{}_{ij}e_k,\qquad
 C^k{}_{ij}=\epsilon_{ij\ell}n^{\ell k}
                  +a_i\delta^k_j-a_j\delta^k_i,
 \quad n^{ij}=n^{ji},\qquad n^{ij}a_j=0.                 \tag{D1}
\]

The final equation is Jacobi. A rotation diagonalizes \(n\), and for class B its nonzero \(a\) may be chosen along axis 1; then \(n=\operatorname{diag}(0,n_2,n_3)\), \(a=(a,0,0)\). Class A has \(a=0\). The coefficients are physical inverse lengths in an orthonormal frame, not dimensionless Bianchi names. An orientation reversal changes some signed coefficients while preserving curvature invariants; the formulas here use the fixed orientation.

Here is a direct Levi-Civita construction, independent of a pretabulated Bianchi Ricci formula. Koszul's formula for the invariant spatial metric gives

\[
2\Gamma_{ijk}=C_{ijk}-C_{jki}+C_{kij},\qquad
\Gamma_{ijk}=\langle D_{e_i}e_j,e_k\rangle.              \tag{D2}
\]

With \(R(X,Y)Z=D_XD_YZ-D_YD_XZ-D_{[X,Y]}Z\), the coefficients, constant along each spatial invariant frame, give

\[
R^l{}_{mij}=\sum_p(\Gamma_{jmp}\Gamma_{ipl}
 -\Gamma_{imp}\Gamma_{jpl}-C^p{}_{ij}\Gamma_{pml}),
\qquad {}^3R_{jk}=\sum_iR^i{}_{jik}.                    \tag{D3}
\]

Substitution of (D1), *restricted by* \(n_1a=0\), yields

\[
{}^3R_{ii}=\tfrac12[n_i^2-(n_j-n_k)^2]-2a^2
 \quad(\{i,j,k\}=\{1,2,3\}),\quad
 {}^3R_{23}=a(n_2-n_3),\quad {}^3R_{12}={}^3R_{13}=0,             \tag{D4}
\]
\[
{}^3R=-\tfrac12\sum_i n_i^2+\sum_{i<j}n_i n_j-6a^2.          \tag{D5}
\]

The other off-diagonal entry is its symmetric partner. The unrestricted symbolic intermediate has an antisymmetric term proportional to \(an_1\); retaining it would be an algebraic false-positive geometry. In three dimensions the complete spatial Riemann tensor is algebraically determined by the Ricci tensor, so (D4) gives the entire intrinsic curvature at this slice, though not its derivatives or the embedding. Equations (D2)–(D3) exhibit the nontrivial transition from a group label to a tensor, and (D4) is the reusable finite evaluator.

Let \(u,v>0\), both inverse lengths. Actual substitutions give:

| Type / parameters \((n_1,n_2,n_3;a)\) | \({}^{3}R_{ij}\) in the chosen triad | \({}^{3}R\) |
|---|---|---|
| I: \((0,0,0;0)\) | \(0\) | \(0\) |
| II: \((u,0,0;0)\) | \(u^2\operatorname{diag}(1,-1,-1)/2\) | \(-u^2/2\) |
| IX, round: \((u,u,u;0)\) | \((u^2/2)I\) | \(3u^2/2\) |
| V: \((0,0,0;v)\) | \(-2v^2I\) | \(-6v^2\) |
| VII\(_0\), equal: \((0,u,u;0)\) | \(0\) | \(0\) |
| VII\(_0\), unequal: \((0,2u,u;0)\) | \((u^2/2)\operatorname{diag}(-1,3,-3)\) | \(-u^2/2\) |

The type II computation includes a sectional cross-check: since \({}^{3}R_{11}=u^2/2\) and \({}^{3}R=-u^2/2\), the three-dimensional identity \(R_{ijij}=R_{ii}+R_{jj}-R/2\) yields section curvatures \((+u^2/4,+u^2/4,-3u^2/4)\) for planes \((12,13,23)\). For IX, \(R_{ijij}=u^2/4>0\); for V, \(R_{ijij}=-v^2\). These signs independently check the scalar convention and the Bianchi V warped-slice curvature in the R32-P5 product, where \(v=A_0/X\). In physical units the corresponding curvature terms in time-rate equations are \(c^2{}^3R\) or \(c^2{}^3R_{ij}\).

The equal-\((n_2,n_3)\) VII\(_0\) row has the intrinsic Euclidean metric: the flat spatial Riemann tensor vanishes although its chosen simply transitive generators have a non-Abelian algebra. A local Euclidean geometry also admits the translational Bianchi I action. Thus I and flat VII\(_0\) are distinct *presentations of the same local spatial geometry*, not a counterexample showing two different intrinsic curvatures at that point. The symmetry subgroup, global identifications, and its relation to extrinsic data must be specified if a presentation is to have physical significance. An isotropically expanding flat FLRW realization has both presentations, as Ellis et al. Table 18.2 notes. The statement does not equate every anisotropically embedded I and VII\(_0\) spacetime.

## R5–R6. Joint Gauss–Codazzi image and a sharper matched pair

For homogeneous normal data the Hamiltonian constraint is

\[
3h^2=\kappa\varepsilon_N+\Lambda
       +\tfrac12 S_{ij}S_{ij}-\tfrac12{}^3R.             \tag{D6}
\]

The sign follows directly from \({}^3R+K^2-K_{ij}K^{ij}=2\kappa\varepsilon_N+2\Lambda\). The momentum constraint in the Ellis et al. equation (18.21) normalization reads

\[
\kappa q_i=3a S_{1i}+\sum_{jk}\epsilon_{ijk}n_j S_{jk}.
                                                               \tag{D7}
\]

To avoid a convention ambiguity, \(q_i\) here is chosen so that the right side agrees with the orthonormal signed LRS V branch: for \(a=v\) on axis 1, \(S=\operatorname{diag}(2s/c,-s/c,-s/c)\), equation (D7) gives \(\kappa q_1=6vs/c\), exactly the positive normal-frame momentum relation used in R32-P5 after its axes are permuted. Equation (D7) otherwise inherits the orientation and shear convention in (D1). This is a three-component constraint, not a shear-free rule. In class A with diagonal \(n,S\), \(q=0\) even when \(S\ne0\). In the LRS V tilted branch, \(q_1=0\) forces \(s=0\) for \(v>0\); transferring that conclusion to I, II or IX would discard the different structure constants.

The actual evaluator's algebraic compatibility set can therefore be written

\[
\mathcal J_{\mathcal B}(h,S,\varepsilon_N,q,\Lambda)
 =\{(n,a): n=n^T,\ na=0,\ (n,a)\text{ lies in canonical
 sign class }\mathcal B,\ (D4),(D6),(D7)\text{ hold}\}.       \tag{D8}
\]

One may intersect (D8) with measured or bounded *same-frame* curvature tensors, not with an uncalibrated sky quadrupole. The sign classes in Ellis et al. Table 18.1 supply finite canonical cells; the variables inside each cell are continuous. A quotient by rotations and actual local isometries prevents duplicate presentation counts. A scalar \({}^{3}R\) alone leaves greater degeneracy than the full \({}^{3}R_{ij}\).

An exact matched example makes this point beyond I versus II. Put the same normal-frame \(h>0\), diagonal \(S=\operatorname{diag}(s_1,s_2,s_3)\) with \(\sum s_i=0\), orthogonal dust \(q_i=0\), \(\Lambda\ge0\), and \(\varepsilon_N>0\) in two data sets. Take II data \(n=(u,0,0)\) and VII\(_0\) data \(n=(0,2u,u)\), both \(a=0\). Equation (D7) vanishes in each, and their scalar curvatures are identically \(-u^2/2\). Equation (D6) thus fixes **exactly the same** density

\[
\kappa\varepsilon_N=3h^2-\Lambda-\tfrac12\sum_i s_i^2-u^2/4,
                                                              \tag{D9}
\]

positive whenever the right side is positive (for example \(\Lambda=0\), \(h=2u\), \((s_1,s_2,s_3)=(u/10,-u/20,-u/20)\)). Yet the two spatial Ricci tensors are the distinct matrices in the table; their spectra cannot be made equal by a triad rotation. Consequently a common local normal-frame expansion/shear tensor, normal dust density, flux, \(\Lambda\), and scalar curvature do **not** uniquely recover even the local intrinsic curvature tensor. The STF Ricci difference is an immediate discriminator if a spatial tidal-curvature datum can be inferred independently. Einstein initial data with these smooth invariant spatial metric and extrinsic data satisfy both constraints; normal dust data are regular for the positive density chosen. Invoking their possible time developments requires the dust Cauchy equations, whereas the displayed statement needs only the initial slice.

The inverse direction is also useful. An independent full \({}^{3}R_{ij}\) measurement would exclude one member of this pair, but in flat constant-curvature sectors it still does not select a unique simply transitive presentation (I/VII\(_0\), likewise open V/VII\(_h\) in the FLRW limit). A Weyl electric/magnetic tensor or its time derivatives, a spatial-curvature-sensitive distance/parallel-transport response at more than one location, and a declared matter model could provide additional independent information. These are *candidate observables*, not results of evaluating the CMB sky. Weyl propagation and shear evolution also require anisotropic stress and initial conditions: Ellis et al. §6.4, equations (6.28), (6.33)–(6.36), make their coupling explicit. The spatial Ricci is an intrinsic slice tensor, whereas the Weyl tensor encodes four-dimensional free curvature; substituting one for the other without Gauss relations and extrinsic data would change the claim.

## R6–R8. Checks and verdict

The symbolic program computes (D2)–(D4), then substitutes six rows. Its first attempt used the protected Wolfram symbol `C`, generating an unresolved giant expression; changing it to `strC` is an implementation correction, not a physical counterexample. The successful evaluator output contains the six matrices and the class-B constrained matrix. A separate standard-library `Fraction` implementation uses integer permutations and performs exact-rational checks for \(u=2/7,v=3/11\). It prints six expected Ricci matrices and passes. Its independent finite enumeration is a cross-check of the finite identities at that substitution; the analytic derivation (D2)–(D4) supplies their symbolic scope. Positive sectional IX and negative constant sectional V provide a sign and unit check. The vanishing of the antisymmetric piece only on \(an_1=0\) checks the Jacobi dependence. No four-axis CAS admission or xAct validation is claimed by this targeted verification.

The proved result is an instantaneous, geometry-compatible image and a concrete degeneracy of kinematic-plus-scalar-curvature data. It is not framed as a new universal no-go theorem: the matched pair fixes the quantifiers it actually addresses and the curvature-tensor measurement that resolves it. In particular, an ordinary CMB quadrupole \(Q^{T}_{ij}\), a local optical shear tensor, and a spatial \({}^{3}R_{ij}\) are three distinct objects. The first depends on a photon history, source terms, observer, foreground/mask and transfer model; R32-P5 even supplies different Bianchi I shear histories with an identical full final collisionless temperature pattern. The second can arise as a local coefficient in a calibrated distance law; the third additionally probes spatial geometry. None follows numerically from the other in (D8) without a declared response. The P5 result and the present pair answer separate inverse questions, and neither licenses a Bianchi family identification from sky morphology alone.

For the project's \((x,Q,\Pi,F,G_F)\) vocabulary, (D8) supplies a *deterministic geometry carrier* and potential constraints on a same-frame \(x\). A normalized anchor score \(Q\) requires a named premise anchor and denominator; do not conflate it with \(Q^{T}_{ij}\) or a raw tensor norm. The current R32-05-P6 optical manuscript defines an occupancy \(F_\nu(B)=\nu(B\cap D)/\nu(D)\) under a declared finite support measure, whereas other project text uses directional-support language. Both need their own domain, measure, ceiling and mapping; this note chooses neither policy and computes no \(F\). A statistical \(\Pi\) requires a joint law; a depth functional \(G_F\) requires specified windows and dependence. Thus there is no posterior, occupancy, ceiling exceedance or empirical constraint in this calculation.

## R9–R10. Finite implementation contract and resume point

The reusable pre-solver evaluator accepts a real symmetric \(3\times3\) \(n\) with inverse-length units, real \(a\in\mathbb R^3\) with inverse-length units, oriented orthonormal frame, \((h,S,\varepsilon_N,q,\Lambda)\) in the units above, and an explicit tolerance only for noisy numeric data. It first checks \(\|n a\|=0\) algebraically or against a declared input uncertainty, constructs \(C\), \(\Gamma\), \({}^{3}R_{ij}\), and then checks (D6),(D7) jointly. It returns the curvature scalar, STF Ricci, Hamiltonian and three momentum residuals with units \(L^{-2}\), plus algebraic class and geometric equivalence flags. Exact input uses exact arithmetic; a zero curvature tensor in a non-Abelian presentation carries the flat equivalence flag. It does not convert residuals into a likelihood or infer a family. The six table rows and the II/VII\(_0\) matched pair are reference values; \(a\to0\) and \(n\to0\) are boundary limits, not automatic class relabelings of a nonzero datum.

The next independent scientific step is to specify one curvature-sensitive observational response and its uncertainty, then intersect its tensor image with (D8) while retaining source/observer history and equivalence classes. A practical candidate is a separately calibrated low-redshift distance/transport tensor or Weyl-sensitive response linked through explicit Gauss and propagation equations. Check the response on the matched II/VII\(_0\) pair first: it should distinguish their STF spatial Ricci when its assumptions actually expose that tensor. For flat I/VII\(_0\), record presentation equivalence rather than scoring a fictitious distinction. This is an executable mathematical target and does not invoke the absent native low-ell solver.

### 한국어 요약

공간 균질 절편의 구조상수 \((n^{ij},a_i)\)와 Jacobi 조건 \(n^{ij}a_j=0\)에서 Levi-Civita 연결과 삼차원 Ricci 텐서를 직접 계산했다. I·II·IX·V·VII\(_0\)의 명시적 행렬과 Hamiltonian·운동량 제약을 함께 사용한다. II의 \((u,0,0)\)과 VII\(_0\)의 \((0,2u,u)\)는 같은 팽창·대각 전단·밀도·우주상수·운동량 및 공간 스칼라곡률을 가질 수 있지만, STF 공간 Ricci 텐서는 서로 다르다. 반면 \((0,u,u)\)인 평탄 VII\(_0\)와 I는 국소 유클리드 공간을 나타내는 서로 다른 군 표현이다. 따라서 곡률 텐서와 관측 응답의 가정, 군 표현의 동치성을 분리해야 한다. 현재 산출물은 순간 제약의 이론 계산이며 CMB 우도나 Bianchi 계열 식별을 계산하지 않았다.
