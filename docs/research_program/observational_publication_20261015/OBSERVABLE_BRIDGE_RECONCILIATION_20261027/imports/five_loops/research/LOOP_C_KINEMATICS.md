# LOOP C — A local covariant optical inverse for expansion, shear, vorticity and acceleration

**Owner:** HTT internal theory loop C. **Date:** 2026-10-26. **Scope:** solver-free, local theory and exact finite algebra; no observational estimate. Source baseline is `a55036ad09c53a9215dee3282e425d37cfb95443`, supplied by the parent inventory. This report does not change the production repository or claim acceptance. Independent parent review remains pending.

**국문 초록.** 한 관측자의 근방에서 같은 매끄러운 시간꼴 합동을 따르는 광원들의 적색편이–거리 기울기와 고유운동을 결합하면 팽창 1성분, 전단 5성분, 와도 3성분, 가속도 3성분의 조건부 국소 역사상을 구성할 수 있다. 전단은 접벡터장의 E형 사중극, 와도는 B형 쌍극에 대응한다. 본 계산은 구면 사영의 정확한 정규화와 공동 반응행렬의 계수를 유도하고 기호계산으로 검산한다. 관측자와 광원이 같은 가속 합동을 따를 때 가속도는 고유운동의 영차 E형 쌍극에 나타나지 않는다. 관측자 가속 항과 광원의 지연된 운동이 상쇄되기 때문이다. 가속도는 적색편이–거리 기울기의 쌍극에서 얻는다. 반면 먼 준성의 세속 수차 쌍극은 별도로 선언한 기준계에 대한 상대속도 변화를 측정한다. 미보정 망원경 기준틀 회전은 물리적 와도와 같은 B형 쌍극을 만들므로 자이로 또는 독립적인 기준틀 보정이 필요하다. 전체 텐서와 관측 공분산을 공동 가능집합으로 사상한 뒤 기존 x·Q·F·Pi·G_F 정규화를 적용한다.

## R1 — Question and completed construction

Can an optical catalogue add the antisymmetric velocity-gradient sector missing from a radial local Hubble diagram, while retaining which congruence and reference frame the measurement concerns? The result is an explicit twelve-component inverse, its exact full-sphere response norm, and finite-catalogue Jacobian. It also supplies a radial–transverse shear closure test and separates two physically different acceleration measurements.

The retained affine radial recipe already gives bulk motion, expansion and shear: `20-report-1-.txt`, §13, PDF p15; the source inventory also locates it in `legacy_reconstruction_chapter.md`. This loop adds the optical justification, transverse inversion, reference-frame kernel and joint carrier contract. The shear/vorticity E/B interpretation is established literature, not a claim of first discovery.

## R2 — Sources and convention matching

The local geometric starting point is Ellis, Maartens and MacCallum, *Relativistic Cosmology*, printed pp80–82, PDF pp96–98, equations (4.26)–(4.34). Its projected connecting-vector equation gives nearby relative velocity; (4.32) gives directional expansion and (4.33) gives direction change in a Fermi frame. The text explicitly restricts the linear description to a smooth continuum in a sufficiently small neighbourhood. Printed p192, PDF p208, equations (8.39)–(8.40), supplies the optical Hubble coefficient, including acceleration.

Heinesen and Korzyński, [PRD 110, 043525 (2024)](https://doi.org/10.1103/PhysRevD.110.043525), [arXiv:2406.06167v2](https://arxiv.org/html/2406.06167v2), equations (9)–(12), Appendix C and Appendix E, supplies the null-boundary derivation and vector-harmonic interpretation. Its Appendix C retains acceleration even though the main-text drift expansion specializes to geodesic observers. The final Appendix-C equation is (C10) in the paper numbering and (46) in the retrieved HTML. These different labels refer to the same displayed expansion. Marcori et al., [PRD 98, 023517 (2018)](https://doi.org/10.1103/PhysRevD.98.023517), [arXiv:1805.12121](https://arxiv.org/abs/1805.12121), treats general-observer direction drift and distinguishes parallax from aberration drift. Exa search and primary HTML retrieval were performed on 2026-10-26.

The project convention is fixed by `FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.txt`, §5, PDF pp17–18. The metric is \((-+++ )\), \(u^a u_a=-1\), and geometric rates differentiate proper length \(s=c\tau\). Thus
\[
\nabla_bu_a=H_g h_{ab}+\sigma_{ab}+\omega_{ab}-A_a u_b,
\quad \omega_{ab}=\epsilon_{abc}\omega_c,\quad\epsilon_{123}=+1.
\tag{C1}
\]
The vector \(\omega\) is therefore the project's axial convention, with its stated sign. We do not silently replace it by half the ordinary Euclidean curl. Define auxiliary physical-rate coordinates
\[
h=cH_g,\quad S=c\sigma,\quad v=c\omega,\quad\alpha=cA.
\tag{C2}
\]
All four have inverse-time units; physical four-acceleration is \(c^2A=c\alpha\). The state carrier retains the original geometric \(\sigma,\omega,A\).

## R3 — Assumptions and observable definitions

Let a \(C^3\) timelike field describe observer and emitters in a convex normal neighbourhood. Work before caustics, with geometric optics, differentiable source tracking and a specified Fermi–Walker transported observer triad. The expansion is local in source distance, not a perturbation about FLRW. No Einstein matter equation, dust equation of state or Bianchi model is needed for the leading kinematic map.

Let \(n\) point outward toward a source and let \(r\) be an independently calibrated local optical distance whose first-order normalization equals observer-normalized affine distance. Angular-diameter and luminosity distances have this normalization under the usual optical conditions. Define
\[
d(n)=\lim_{r\to0}\frac{cz(n,r)}r,
\qquad \mu(n)=\lim_{r\to0}\frac{dn_{\rm obs}}{d\tau},
\qquad P(n)=I-nn^T.
\tag{C3}
\]
No division by directional Hubble rate is required; contracting directions with zero or negative leading redshift remain mathematically admissible. Estimating these limits from a finite survey requires a distance-window and remainder model. A sparse set of bound sources is not automatically a sample of this continuum.

## R4 — Candidate response and its optical, rather than Newtonian, origin

The candidate is
\[
\boxed{d=h+S:nn-\alpha\cdot n,
\qquad\mu=PSn+n\times v.}
\tag{C4}
\]
The radial sign follows by contracting (C1) with the past-directed, observer-normalized ray \(\ell=-u+n\): \(c\ell^a\ell^b\nabla_a u_b=h+S:nn-\alpha\cdot n\). Antisymmetry removes \(\omega\). This is the first optical redshift–distance coefficient, as in Ellis (8.39)–(8.40), after converting Ellis's incoming photon direction to outward \(n\).

For a simultaneous connecting vector \(\xi=rn\), Ellis (4.29) gives projected relative velocity \(cD_\xi u\). Splitting its radial and transverse parts yields \(\dot r/r=h+S:nn\) and \(\dot n=PSn+n\times v\). This establishes the spacetime kinematics, but simultaneous separation alone is insufficient to establish apparent sky drift. The following null-boundary step closes that gap.

## R5 — Optical lemma and exact inverse

Consider two infinitesimally separated light rays connecting the same observer and emitter worldlines. Set \(k=E(u-n)\). Their deviation vector \(X\) obeys the endpoint conditions \(X_O=u_O\), \(X_E=u_E/(1+z)\). Smooth endpoint expansion and the null Jacobi equation imply
\[
P\nabla_kX\big|_O=P\nabla_ku\big|_O+O(r).
\]
The derivative of the observed direction is
\[
\frac\mu c=PA-\frac1E P\nabla_kX
=PA-P(A-\nabla_nu)+O(r)
=P\nabla_nu+O(r).
\tag{C5}
\]
The endpoint factor contributes only a multiple of \(u_O\) at leading order and disappears under \(P\). Curvature and second derivatives enter the next distance order through the Jacobi and endpoint expansions. This derivation follows the structure of Appendix C while displaying the acceleration cancellation explicitly. It proves (C4) for an accelerated common congruence as well as its geodesic specialization.

Consequently a term \(cPA\) must not be appended independently to (C4): it would count the observer aberration while omitting the compensating retarded emitter motion. On bounded normal neighbourhoods the omitted rate terms have size \(O(crK_2)\), where \(K_2\) contains curvature, second derivatives of \(u\), and quadratic first derivatives. This is an asymptotic order statement; no finite survey error constant is certified here.

Write \(\langle f\rangle=(4\pi)^{-1}\int f\,d\Omega\). The isotropic moments \(\langle n_in_j\rangle=\delta_{ij}/3\) and \(\langle n_in_jn_kn_l\rangle=(\delta_{ij}\delta_{kl}+\delta_{ik}\delta_{jl}+\delta_{il}\delta_{jk})/15\) give the inverse
\[
h=\langle d\rangle,\qquad
\alpha=-3\langle dn\rangle,\qquad
S_{ij}=\frac{15}{2}\left\langle d(n_in_j-\delta_{ij}/3)\right\rangle,
\tag{C6}
\]
\[
S_{ij}=5\langle\mu_{(i}n_{j)}\rangle,
\qquad v=-\frac32\langle n\times\mu\rangle.
\tag{C7}
\]
The second shear formula has zero trace because \(\mu\cdot n=0\). To verify its normalization directly, average \(\mu_i n_j\): the shear contribution is \(S_{ij}/3-2S_{ij}/15=S_{ij}/5\); symmetrization removes rotation. For rotation, \(n\times(n\times v)=n(n\cdot v)-v\) averages to \(-2v/3\). These computations fix both the factor and the sign.

Use orthonormal scalar harmonics and define \(E_{\ell m}=\nabla_{S^2}Y_{\ell m}/\sqrt{\ell(\ell+1)}\), \(B_{\ell m}=n\times E_{\ell m}\). For \(f=S:nn\) and \(g=v\cdot n\),
\[
\mu=\tfrac12\nabla_{S^2}f+n\times\nabla_{S^2}g,
\quad \mu^E_{2m}=\frac{\sqrt6}{2}f_{2m},
\quad\mu^B_{1m}=\sqrt2g_{1m}.
\tag{C8}
\]
Thus \(\nabla_{S^2}\cdot\mu=-3f\); the oriented surface curl of the B part is \(-2g\). Isotropic expansion produces no transverse signal. An additional \(PD\) term would give \(\mu^E_{1m}=\sqrt2(D\cdot n)_{1m}\) and \(D=\tfrac32\langle\mu\rangle\). This is a separate population/reference response, not the common-congruence \(A\).

## R6 — Frames, clocks, sources and discriminating limits

Let the catalogue triad rotate relative to Fermi–Walker axes with angular velocity \(\Omega\), defined by \(\dot e_i=\Omega\times e_i\). Components then drift by \(-\Omega\times n=n\times\Omega\). Its measured B1 coefficient is
\[
v_{\rm cat}=c\omega+\Omega.
\tag{C9}
\]
A calibrated nonrotating triad makes (C7) a physical vorticity measurement. Merely setting the mean quasar spin to zero selects an astrometric frame; it does not independently establish \(\Omega=0\) for a rotating matter congruence. Physical vorticity and tetrad rotation are different objects even though this observation channel sums them.

At first order in small peculiar velocities, observer translation \(V\) relative to the chosen source frame contributes \(-PV/r\), while source slip contributes \(Pv_{\rm slip}/r\). This local expression is not a finite-distance cosmological parallax transfer law. A relative velocity drift contributes secular aberration \(P\dot V/c\) under the accompanying stationary-source/reference closure. The coefficient measures \(\dot V/c\) in that specified reference, and need not equal the congruence four-acceleration \(cA\). Distant quasars have jets, structural centroid drift, source velocities and propagation corrections; declaring them dust would remove real nuisance terms without evidence.

The two E1 responses \(PD\) and \(-PV/r\) are identical angular patterns in one shell. Two distinct known distances give the coefficient matrix with rows \((1,-1/r_j)\), invertible when \(r_1\ne r_2\). This separates those two idealized coefficients only if their shared depth laws and source populations are valid. A smooth unknown source-slip gradient can mimic physical shear or vorticity across every shell.

Let \(k=d\tau/dt_{\rm cat}>0\). The transverse response becomes \(k[PSn+n\times(v+\Omega)]\). Radial distances/redshifts provide an independent rate scale. If \(S\ne0\), the E2 closure measures \(k\), in principle: \(k=\langle\mu_E,PSn\rangle/\langle PSn,PSn\rangle\). When \(S=0\), a transverse-only amplitude cannot calibrate the clock. Distance-scale uncertainty must likewise be carried as a radial calibration nuisance.

Useful limiting cases are FLRW comoving motion, where \(S=v=\alpha=0\) and \(\mu=0\); pure shear, which gives E2 only; rigid local rotation, which gives B1 only; and a common accelerated congruence with vanishing instantaneous spatial gradient, where the radial acceleration dipole survives while the leading transverse field vanishes.

## R7 — Actual algebra and response-rank checks

`cas/loop_c.wl` was executed with the connected Wolfram Language evaluator. Exact monomial integration verifies (C6)–(C7), the E1 inverse, and
\[
\left\langle d^2+|\mu|^2\right\rangle
=h^2+\frac13 S:S+\frac13|\alpha|^2+\frac23|v|^2.
\tag{C10}
\]
With an extra E1 coefficient \(D\), its right-hand side gains \(2|D|^2/3\). Every returned residual was exactly zero; the response is preserved in `cas/loop_c_wolfram_receipt.json`. WolframContext returned an internal error; the evaluator itself succeeded. Optional SymPy import failed in the available Python environment. A dependency-free exact rational check replaced that finite-design calculation.

In orthonormal STF coordinates, (C10) gives the ideal full-sphere Gram diagonal \((1,I_5/3,I_3/3,2I_3/3)\). Radial rank is nine, transverse rank eight, and joint rank twelve. `python cas/loop_c_check.py` also verified these ranks on twelve explicit rational unit directions: coordinate axes, the three positive 3–4–5 pair directions, and their antipodes. Adding three unknown triad-spin columns leaves rank twelve and creates exactly three kernel directions \((\delta v,\delta\Omega)=(-q,q)\). The output is `cas/loop_c_python_receipt.json`. These checks validate polynomial identities and a finite design; they do not constitute four-axis spacetime CAS validation.

## R8 — Verdict and closure conditions

The local inverse is constructed under R3. Its geometric origin and exact angular normalization are established; optical input and algebra agree. Its literature-known ingredients are explicitly credited. The project addition is the joined observation map with calibrated physical interpretation, the acceleration distinction, and a usable response/closure contract.

The shear consistency residual is
\[
C_{2m}=\mu^E_{2m}-\frac{\sqrt6}{2}d_{2m}.
\tag{C11}
\]
It vanishes in the leading common-clock/common-congruence model. E1 and higher multipoles are additional residual channels. Their nonzero values diagnose failure of a collection of assumptions or finite-distance effects; assigning a particular cause requires the corresponding nuisance/transfer model. No universal strong no-go or new impossibility claim is adopted. The explicit finite linear kernel is retained as a response property with its stated design and nuisance assumptions. Independent review is the remaining acceptance step.

## R9 — Joint observable image and the existing x·Q·F·Pi·G_F objects

For source \(a\), choose measured tangent basis \(t_{aA}\). A Jacobian row for \(\theta=(h,S_I,\alpha_j,v_j)\), with orthonormal STF basis \(E_I\), is
\[
J^{r}_a=(1,n^TE_In,-n_j,0),\quad
J^\mu_{aA}=(0,t_{aA}^TE_In,0,t_{aA}\cdot(n\times e_j)).
\tag{C12}
\]
These are derivatives of the actual source-level response. Fit raw redshift and distances jointly when division by uncertain \(r\) would distort the law. Apply angular masks, tangent-frame conversion, distance windows and nuisance operators before computing rank. With a covariance-support whitener \(W\), nuisance matrix \(N\), and anchor-coordinate map \(L\), use \(P^\perp_{WN}WJL\), retaining residuals in covariance null directions. No full-sphere orthogonality is presumed after selection.

For a declared observation law or tolerance set, form the joint inverse image
\[
\mathcal I_Y=\{X:\exists\eta,\nu,\epsilon;\ Y=R_\eta(X)+N\nu+\epsilon,\ (\eta,\nu,\epsilon)\in\mathcal A\}.
\tag{C13}
\]
Here \(X=(\sigma,\omega,A,\beta_{RM},\beta_{MO},\ldots)\) preserves the report's carrier; unreconstructed channels remain unavailable. A compatible CMB response can be intersected with this image using shared frame and covariance, rather than equating a CMB temperature tensor to \(\sigma\).

`20-report-1-.txt`, §23, PDF pp24–26, defines sample-by-functional \(x\), anchor gauge/margin \(Q\), directional support profiles \(F\), law-bound exceedance surfaces \(\Pi\), and structured depth paths \(G_F\). Apply the original \(\phi_j\) and normalization to each joint state from (C13). Preserve paired reference states. In the inspected current `typefree_functionals.py`, `support_utilization` is specifically \(u^T[\phi(X)-\phi(X_{ref})]/h_B(u)\), with positive denominator required. Taking its supremum over an explicitly supplied finite image yields the corresponding finite support profile; it does not certify a continuous supremum. A `FINITE_SET` carries no probability weights. \(\Pi_\phi\) therefore requires a named empirical, sampling, null or posterior law before exceedance is evaluated.

There are distinct F namespaces in the materials: the legacy `mio/formalism/filling_fraction.py` implements a certified diagnostic under a sign-clean ceiling and rejects material/volume-occupancy interpretations; the structured report retains directional support; the newer skill prose mentions explicit-measure occupancy. This construction uses the report/typefree support namespace and does not identify these quantities. `typefree_depth.py` transports signed paired features through `DepthRepresentation`, requiring one shared latent realization, frame endpoints and full cross-bin covariance for uncertainties. That is the applicable structured depth connection. A scalar legacy depth-gap is used only under its own definition. Deterministic images remain computable when a probability law is unavailable.

## R10 — Next executable checkpoint

The next integration is a source-level synthetic catalogue with known frame spin, clock scale, distance errors and shared source-slip nuisance. Generate it directly from (C12), recover its injected coefficients, and compare the shear closure across shrinking distance windows. Then add a declared finite-distance coefficient from the primary optical expansion and measure the induced bias. Real catalogue attribution requires population selection, an independent triad-spin calibration and the joint observation law. None of these steps requires an ODE or a Bianchi solver. The present unit ends with the explicit inverse, optical cancellation, exact projection checks and reusable joint-response contract delivered for independent review.
