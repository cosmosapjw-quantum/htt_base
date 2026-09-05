# Tensorised Low-Multipole CMB Morphology, Kinematical Isotropy Bounds and Response-Limited Identification

**Report A — complete integrated research-report draft, K3 revision 1**  
Date: 2026-09-05  
Status: `FULL_DRAFT_FOR_REVIEW_NOT_CANONICAL_NOT_PUBLICATION_APPROVED`

This complete draft integrates the existing representation, statistics, response and numerical sections with the physical-kinematics/MES core. It is a manually assembled, source-grounded manuscript candidate, not an output of an executed authority compiler. The canonical ledger remains T9 v4 with 30 claims; the intended 40-claim and 20-reference surfaces remain candidates. Existing canonical files are not replaced. Source identities, the candidate claim map, editorial qualifications and unperformed verification are recorded in the appendices. Numerical results reproduced in the text are inherited from the cited repository evidence, not rerun in this drafting pass.

## Abstract

Low-multipole cosmic-microwave-background morphology and spacetime kinematics are related physical questions, but they are not the same state. We construct a theory and methods framework that retains both the full quadrupole–octupole temperature tensors and a separately typed physical state of congruence shear, vorticity, acceleration, frame-relative velocities and geometry. The Maartens–Ellis–Stoeger inequalities are inherited as one-way, premise-matched radial constraints on named physical sectors, rather than discarded or treated as observations of those sectors. Physical tensor functionals retain shape, parity and relative orientation that scalar ceilings cannot determine.

The orthonormal real harmonic carrier maps exactly to symmetric trace-free tensors \(Q_{ab}\) and \(O_{abc}\). On a nonzero cyclic forward-image domain, an overcomplete Krylov packet reconstructs a deterministic proper-oriented representative. The physical state remains distinct from this observable representation: attribution requires a declared response and a jointly conditioned feasible set. We distinguish exact affine-fibre uniqueness from population identification and sampling coverage, and retain dependence when the same data construct both MES ceilings and observational compatibility regions. Finite-null validity consequently applies to the complete data-dependent analysis, including anchor construction, rather than to rank arithmetic alone.

The exact full-sky local-observer response closes the radiation–observer velocity lane, not the general shear, vorticity or global-tilt response. After a declared cut-sky processing operation, the low-source response is identifiable only modulo a high-source nuisance image. The inherited continuum wide-mask analysis has row rank 32 at source cutoff \(L=12\), with an exact axial certificate and numerical evidence for the other registered directions. The finite-HEALPix matched-control operator remains rank unresolved. A frozen matrix-valued numerical-error envelope gives a conditional robust-rank criterion, while subspace interpretation additionally requires a perturbation-to-gap bound. No corrected Planck rank, empirical kinematical estimate or native-solver result is reported. The central result is a unified separation of observable morphology, physical-sector constraints and response-limited identification.

## 1. Physical question, scope and supersession

A complete description of a low-multipole temperature pattern does not, by itself, identify its physical origin. Conversely, an upper bound on a physical kinematical invariant does not reconstruct the direction or morphology of the underlying tensor. These two limitations motivate a framework in which observable representation, physical state, conditional constraints and inference are distinct but connected objects.

The observable state is the quadrupole–octupole pair

\[
\mathcal O_{\rm low}=(Q_{ab},O_{abc},\ldots).
\]

The physical state contains kinematics of a declared congruence, velocities between declared frames and separately typed geometry. A family of MES anchors restricts selected physical invariants under specified premises. A response-constrained set describes which physical states remain compatible with the observations and those premises. None of these objects is a substitute for another.

The original MES approach uses matter–radiation equations to constrain departures from a Friedmann–Robertson–Walker geometry. Its physical content is therefore not exhausted by a collection of scalar anomaly statistics. Its inequalities nevertheless require maintained assumptions and do not constitute a model-free inverse map from one observed sky to a spacetime tensor field. The later improved limits and the connection between covariant multipole norms and COBE-era quantities supply the relevant lineage. [@MES_1995_LIMITS; @MES_1995_IMPROVED; @SAG_1999_COBE]

The present report retains that physical lineage while replacing scalar-only observable compression by a tensorial carrier. It also restores the physical-state programme in which shear, vorticity, acceleration, frame velocities and geometry remain component-native. The resulting methodology does not infer shear from the temperature quadrupole merely because both transform in an STF2 representation. It asks separately which components are represented, which are constrained, which have an available response and which are identifiable.

The scientific order is therefore observable tensor representation and orbit geometry; typed physical kinematics and functionals; premise-matched MES constraints; response-constrained sets; finite-null validity; local-observer response; processed nuisance quotients; and numerical uncertainty. The existing repository lineages supplying these ingredients are composed by their source and semantic roles, not presented as one fictitious linear Git ancestry.

This report is theory-only. Scalar-only MES observational ranks and withdrawn WU-006–008 tensor-rank, foreground and carrier-injection interpretations remain historical provenance. There is no corrected tensorised Planck result in this phase. Local observer motion is not equated with global matter-frame tilt. No finite-HEALPix containment theorem, Bianchi-family identification, or native BASS background, recombination, reionisation or solver result enters the report. A model-family label would require a separate forward model and identification argument.

## 2. Conventions and observable tensor representation

### 2.1 Observer, photon and sky direction

The metric signature is \((-,+,+,+)\), and the spatial orientation convention is \(\epsilon_{123}=+1\). The future-directed observer obeys \(u^a u_a=-1\). For future-directed null photon momentum,

\[
p^a p_a=0,
\qquad E_\gamma=-c\,p_a u^a>0,
\]

we define the propagation direction by

\[
p^a=\frac{E_\gamma}{c}(u^a+e^a),
\qquad u_a e^a=0,
\qquad e_a e^a=1.
\]

The outward sky direction is \(n^a=-e^a\). These conventions are used consistently in the local-observer response below. Physical frame and congruence labels are not removed by a coordinate change.

### 2.2 Orthonormal and raw real harmonic coordinates

For a real temperature field,

\[
T(\hat n)=\sum_{\ell m}a_{\ell m}Y_{\ell m}(\hat n),
\qquad a_{\ell,-m}=(-1)^m a_{\ell m}^{*}.
\]

The orthonormal stored-real carrier is

\[
c_{\ell0}=a_{\ell0},\qquad
c_{\ell m,c}=\sqrt2\,\Re a_{\ell m},\qquad
c_{\ell m,s}=-\sqrt2\,\Im a_{\ell m}
\quad(m>0).
\]

It satisfies the exact isometry

\[
\|c_\ell\|_2^2
=\sum_{m=-\ell}^{\ell}|a_{\ell m}|^2
=(2\ell+1)C_\ell.
\]

The processed-response construction also uses raw real and imaginary components,

\[
r_{\ell0}=a_{\ell0},\qquad
r_{\ell m,R}=\Re a_{\ell m},\qquad
r_{\ell m,I}=\Im a_{\ell m}.
\]

Their metric is

\[
G_\ell=\operatorname{diag}(1,2,2,\ldots,2),
\qquad c_\ell=D_\ell r_\ell,
\qquad D_\ell^TD_\ell=G_\ell.
\]

The two coordinate descriptions encode the same temperature field but do not have the same Euclidean component metric. Singular values or conditioning estimates computed in raw coordinates require the declared metric adapter before comparison with orthonormal-carrier results.

### 2.3 Harmonic-to-STF map

The quadrupole and octupole are defined by

\[
T_2(\hat n)=Q_{ab}n^a n^b,
\qquad Q_{ab}=Q_{(ab)},\qquad Q^a{}_a=0,
\]

\[
T_3(\hat n)=O_{abc}n^a n^b n^c,
\qquad O_{abc}=O_{(abc)},\qquad O^a{}_{ac}=0.
\]

The real dimensions are \(5\) and \(7\), respectively. In the retained normalisation,

\[
\boxed{Q:Q=\frac{15}{8\pi}\|c_2\|_2^2
=\frac{75}{8\pi}C_2},
\]

\[
\boxed{O:O=\frac{35}{8\pi}\|c_3\|_2^2
=\frac{245}{8\pi}C_3}.
\]

Here \(Q\) and \(O\) have temperature units when the harmonic coefficients do. These are observable temperature tensors, not Hubble-normalised shear or vorticity. Retaining their complete components avoids replacing the observable morphology by powers or a small set of scalar summaries.

## 3. Proper-rotation orbit geometry of the observable state

### 3.1 Domain and invariant packet

On a locally free stratum of \(\mathrm{STF}_2\oplus\mathrm{STF}_3\), the proper-rotation quotient has dimension \(5+7-3=9\). This is a conditional dimension count, not a global orbit atlas. General tensor-invariant and orbit-space constructions provide adjacent methods, but do not constitute a proof of the specific reconstruction used here. [@OLIVE_KOLEV_AUFFRAY_2013; @BORNSEN_VANDEVEN_2018; @LOPATIN_FERREIRA_2018]

For nonzero amplitudes

\[
A_Q=(Q:Q)^{1/2},\qquad A_O=(O:O)^{1/2},
\qquad \bar Q=Q/A_Q,\qquad \bar O=O/A_O,
\]

define

\[
v_a=\bar O_{abc}\bar Q_{bc},
\qquad \mathscr K_{QO}=[v,\bar Qv,\bar Q^2v].
\]

In an ordered eigenframe of \(\bar Q\),

\[
\det\mathscr K_{QO}
=v_1v_2v_3\prod_{i<j}(\lambda_j-\lambda_i)
\]

with the inherited ordering convention. The chart is cyclic when the quadrupole spectrum is simple and every eigenframe component of \(v\) is nonzero.

The normalised packet contains

\[
s_2=\operatorname{tr}\bar Q^2=1,
\qquad s_3=\operatorname{tr}\bar Q^3,
\]

\[
\mu_r=v^T\bar Q^rv\quad(r=0,1,2),
\qquad \chi=\det\mathscr K_{QO},
\]

and the ten symmetric entries

\[
\tau_{ijk}=\bar O(\bar Q^iv,\bar Q^jv,\bar Q^kv),
\qquad 0\le i\le j\le k\le2.
\]

Together with the two amplitudes, these data give an overcomplete representation on the declared domain. No assertion is made that arbitrary numerical packet values lie in its image.

### 3.2 Reconstruction and orientation

Cayley–Hamilton gives

\[
\bar Q^3=\frac{s_2}{2}\bar Q+\frac{s_3}{3}I,
\]

hence

\[
\mu_3=\frac{s_2}{2}\mu_1+\frac{s_3}{3}\mu_0,
\qquad
\mu_4=\frac{s_2}{2}\mu_2+\frac{s_3}{3}\mu_1.
\]

The packet therefore fixes

\[
G=\mathscr K_{QO}^{T}\mathscr K_{QO}
=\begin{pmatrix}
\mu_0&\mu_1&\mu_2\\
\mu_1&\mu_2&\mu_3\\
\mu_2&\mu_3&\mu_4
\end{pmatrix},
\qquad \det G=\chi^2.
\]

The conditions \(B^TB=G\) and \(\det B=\chi\) alone do not select a canonical frame: \(RB\) satisfies them for every \(R\in SO(3)\). We instead use the unique upper-triangular positive-diagonal Cholesky factor \(B_+\), followed by a fixed orientation correction,

\[
B_+^TB_+=G,\qquad
S_\chi=\operatorname{diag}(1,1,\operatorname{sgn}\chi),
\qquad B=S_\chi B_+.
\]

On the cyclic domain, \(G\) is positive definite and \(\det B_+=|\chi|\). Thus

\[
B^TB=G,\qquad \det B=\chi.
\]

With

\[
C=\begin{pmatrix}
0&0&s_3/3\\
1&0&s_2/2\\
0&1&0
\end{pmatrix},
\]

the canonical quadrupole is \(\bar Q_{\rm can}=BCB^{-1}\). If \(T_{ijk}\) is the symmetric coordinate tensor determined by the ten trilinear entries, then

\[
(\bar O_{\rm can})_{abc}
=(B^{-1})_{ia}(B^{-1})_{jb}(B^{-1})_{kc}T_{ijk}.
\]

These formulae reconstruct a symmetric, trace-free, unit-normalised octupole on the exact packet image. For the ordered coordinate vectors \(e_0,e_1,e_2\), the image conditions include

\[
Ce_0=e_1,\qquad C^2e_0=e_2,
\qquad \boxed{\bar O_{\rm can}:\bar Q_{\rm can}=Be_0}.
\]

Equivalently,

\[
\bar O:\bar Q=\mathscr K_{QO}e_0,
\qquad O:Q=A_QA_O\,\mathscr K_{QO}e_0.
\]

An image-safe numerical decoder must enforce these constraints and complete forward replay. A stable implementation may solve for an octupole in a fixed Frobenius-orthonormal STF3 basis instead of applying an inverse Krylov basis independently in three slots. Source-level and local source-equivalent decoder evidence do not become exact-head execution evidence merely by being cited in this report.

### 3.3 Mirror information and chart failures

The signed volume \(\chi\) is an \(SO(3)\) scalar and an \(O(3)\) pseudoscalar. It distinguishes a registered cyclic mirror pair sharing

\[
(Q:Q,\ O:O,\ \operatorname{tr}Q^3,\ Q_{ij}O_{ikl}O_{jkl}).
\]

This is a limitation of that named scalar compression, not a non-separation theorem for every possible bispectrum. The orbit theorem is confined to nonzero cyclic forward-image packets. Zero tensors, contraction-null states, repeated spectra, noncyclic states and condition-limit cases remain typed chart failures. Original tensors and row membership are preserved; no axis or zero statistic is manufactured to conceal a chart failure. Global invariant-ring completeness, an all-strata atlas and novelty adjudication remain outside the established result.

## 4. Physical kinematics, frame relations and tensor morphology

### 4.1 Physical state and unavailable components

The physical state is

\[
\mathcal X_{\rm phys}
=\mathcal K_u\times\mathcal V_{\rm frame}\times\mathcal G,
\qquad \mathcal K_u=(\sigma_{ab},\omega_a,A_a).
\]

Shear, vorticity and acceleration describe the declared timelike congruence, not the angular temperature field. This covariant separation is standard background; the present framework further retains the metadata needed to compare or constrain individual sectors. [@ELLIS_VAN_ELST_1999]

Every component carries its frame, congruence, epoch or window, averaging scale, basis, units and perturbative branch. An untyped legacy vector is not assigned a frame role without an explicit adapter. A missing component is not a numerical zero: the former reports unavailable information or a missing provider, whereas the latter is a physical assertion. Typed abstention is therefore part of the state description rather than a cosmetic output label.

Representation equivalence is also not physical identification. A map from \(Q_{ab}\) to \(\sigma_{ab}\) requires dynamics, a specified observational response and the associated assumptions. None is supplied by the fact that both tensors are STF2.

### 4.2 Three frame velocities

The frame block is

\[
\mathcal V_{\rm frame}
=(\beta_{\rm RO}^a,\beta_{\rm RM}^a,\beta_{\rm MO}^a),
\qquad \beta^a=v^a/c.
\]

Radiation–observer, radiation–matter and matter–observer labels are retained separately. The registered first-order closure is

\[
\boxed{\beta_{\rm RO}^a
=\beta_{\rm RM}^a+\beta_{\rm MO}^a+O(\beta^2)}.
\]

This is not an exact relativistic velocity-addition law or a measurement of any term. In particular, identifying \(\beta_{\rm RO}\) with \(\beta_{\rm MO}\) requires an additional premise concerning \(\beta_{\rm RM}\). The available local-observer temperature response acts in the radiation–observer lane. It does not by itself estimate matter-frame tilt or congruence kinematics.

### 4.3 Geometry, parity and dimension

The signed scalar curvature-budget coordinate \(\Delta\Omega_k\) is distinct from anisotropic spatial curvature. Optional geometry or matter blocks include \({}^{(3)}S_{ab}\), \(E_{ab}\), \(H_{ab}\) and \(\pi_{ab}\), each admitted under its own convention and provider.

| Block | Raw dimension | Representation | Role |
|---|---:|---|---|
| \(\sigma_{ab}\) | 5 | polar STF2 | congruence shear |
| \(\omega_a\) | 3 | axial vector | congruence vorticity |
| \(A_a\) | 3 | polar vector | congruence acceleration |
| \(\beta_{\rm RM}\), \(\beta_{\rm MO}\) | 3 each | polar vectors | independent frame relations in the first-order chart |
| \(\beta_{\rm RO}\) | 3 | polar vector | closure-derived view in that chart |
| \(\Delta\Omega_k\) | 1 | scalar | signed curvature budget |
| \({}^{(3)}S_{ab}\), \(E_{ab}\), \(\pi_{ab}\) | 5 each | polar STF2 | optional curvature, Weyl or stress blocks |
| \(H_{ab}\) | 5 | axial STF2 | optional magnetic Weyl block |

Excluding optional tensors and treating \(\beta_{\rm RO}\) as closure-derived gives

\[
\dim\mathcal X_{\rm core}^{\rm general}
=5+3+3+3+3+1=18.
\]

On a locally free \(SO(3)\) stratum only, the quotient dimension is \(15\). On the geodesic subdomain \(A_a=0\), the raw and corresponding locally free quotient dimensions are \(15\) and \(12\). These are dimensions of the declared kinematical parameter space, not a count of Einstein-equation solutions or observationally identified degrees of freedom. Additional constraints and stabilisers require their own analysis. Each optional STF2 block adds five raw components before such constraints are imposed.

### 4.4 Physical tensor functionals and orbit morphology

A registered functional

\[
\phi:\mathcal X_{\rm phys}\longrightarrow W_\phi
\]

retains input-state identity, output tensor type, parity, frame, congruence, epoch, scale, normalisation and branch. Its codomain may be scalar, pseudoscalar, vector, STF, set or path valued. Relevant examples are

\[
\sigma_{ab},\quad\omega_a,\quad A_a,
\quad\operatorname{tr}\sigma^2,
\quad\operatorname{tr}\sigma^3,
\quad\omega_a\omega^a,
\]

\[
\beta_{\rm RM}\cdot\omega,
\qquad\beta_{\rm RM}^{a}\sigma_{ab}\beta_{\rm RM}^{b}.
\]

The quadratic shear invariant records a magnitude, while the cubic invariant carries additional shape information. The polar–axial velocity-vorticity contraction is a pseudoscalar. These functionals preserve physical morphology beyond a scalar budget, but their definition is not an observational estimate. A legacy scalar projection remains one functional of a richer state rather than becoming the primary physical representation.

## 5. MES inequalities as premise-matched sector constraints

### 5.1 Multipole normalisation and inherited ceilings

In the retained PSTF normalisation,

\[
\epsilon_2=\frac1{T_0}\sqrt{\frac{75C_2}{8\pi}},
\qquad
\epsilon_3=\frac1{T_0}\sqrt{\frac{245C_3}{8\pi}}.
\]

These quantities are dimensionless when \(T_0\), \(Q\) and \(O\) use consistent temperature units. The residual dipole amplitude \(\epsilon_1\) is a declared attribution scenario, not a result obtained by inverting a scalar bound.

After the explicitly maintained gradient and characteristic-time estimates, the registered geodesic reduction is

\[
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
\qquad
B_\omega=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2,
\]

\[
U_\sigma=\frac32B_\sigma^2,
\qquad U_\omega=\frac32B_\omega^2.
\]

The coefficients are inherited from the repository's MES/PSTF reduction and its primary-source authority, not rederived from a new observational analysis here. Their use retains the declared congruence and frame, the geodesic almost-EGS branch, the all-observer or Copernican extension, the derivative-hierarchy reduction and the residual-dipole scenario. [@MES_1995_LIMITS; @MES_1995_IMPROVED; @SAG_1999_COBE]

The named physical invariants are

\[
\psi_\sigma(X)=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},
\qquad
\psi_\omega(X)=\frac{\omega_{ab}\omega^{ab}}{6H^2},
\]

with \(H\ne0\), the common registered rate convention, and the explicit vorticity vector-to-tensor adapter. One must not replace the antisymmetric-tensor contraction by the axial-vector norm without that adapter. In particular, no unregistered factor of two or factor of \(c\) is inferred by notation.

For maintained choices \(\eta\), the MES sector body imposes

\[
\psi_\sigma(X)\le U_\sigma(y;\eta),
\qquad \psi_\omega(X)\le U_\omega(y;\eta).
\]

The data argument is retained when the ceilings are computed from the same sky as other parts of the analysis. A fixed external or ensemble calibration is a distinct conditioning regime. Neither construction makes the ceiling an observation of the shear or vorticity. Compliance does not establish the premises, saturation of a bound or a converse FLRW result.

### 5.2 Acceleration premise and anchor availability

On the registered geodesic branch, \(A_a=0\) is a structural domain condition. The statistical interface separately records the absence of a numerical acceleration denominator. These statements are compatible but not identical. `NO_MES_ANCHOR` is not a zero-radius measured acceleration ball.

Outside the geodesic branch, acceleration remains a typed physical component, and no active verified numerical MES ceiling is supplied. Optional geometry sectors also receive no anchor by analogy. An external physical bound would require its own matter assumptions, gradients and convention; it is not admitted merely by retaining the state component.

### 5.3 Radial information versus tensor direction

For a positive-radius Euclidean sector ball

\[
B_R=\{x:\|x\|\le R\},\qquad R>0,
\]

an orthogonal representation action gives

\[
\|gx\|^2=\langle x,g^Tgx\rangle=\|x\|^2.
\]

Hence \(x\in B_R\) if and only if \(gx\in B_R\). A norm-only anchor is constant on every rotational orbit and, more strongly, assigns the same decision to states of the same norm even when their non-radial shape invariants differ. It cannot select an eigenframe, direction or handedness.

This is consistent with the exact equivariance obstruction: a rotation-equivariant map from rotational scalars alone must return an object fixed by all rotations. The only such vector is zero, and the only such rank-two tensor is proportional to the spatial identity, whose STF part vanishes. Directional reconstruction therefore requires additional data or a response; it is not hidden inside the scalar normalisation.

### 5.4 Product geometry, quadratic stress and matching

For a finite nonempty family of matched positive-radius Euclidean blocks,

\[
B_{\rm prod}=\prod_jB_j,
\qquad
\rho_{B_{\rm prod}}(x)=\max_j\frac{\|x_j\|}{R_j}.
\]

Indeed, \(x\in tB_{\rm prod}\) requires all sector gauges to be at most \(t\), so the infimum admissible value is their maximum. Sector excesses consequently cannot cancel through a signed sum.

With quadratic numerator \(N_j=\|x_j\|^2\), ceiling \(U_j=R_j^2\), and \(S_j=N_j/U_j\),

\[
\boxed{\rho_{B_{\rm prod}}(x)^2=\max_jS_j}.
\]

The gauge and quadratic saturation share the threshold one, but their exceedance margins are different numbers. Neither is automatically a probability, posterior or evidence term. The formula applies to the factorised anchor body, not to a full response-constrained set. For example,

\[
B_0=[-1,1]^2,\qquad
F=B_0\cap\{x_1+x_2\le1\}
\]

gives \(\rho_{B_0}(1,1)=1\) and \(\rho_F(1,1)=2\).

A numerical sector ratio requires matching sector, invariant, frame, congruence, normalisation, order and branch. For fixed ensemble-calibrated \(U_j>0\), an identified numerator interval maps to

\[
[\underline N_j,\overline N_j]/U_j
=[\underline N_j/U_j,\overline N_j/U_j].
\]

A realisation-conditioned random denominator is not divided as though fixed. It remains `RATIO_UNIDENTIFIED` until the joint random-anchor inference problem is specified. Missing numerators, absent anchors and channel mismatches similarly remain typed non-numerical outcomes. Degenerate zero-radius anchors are not covered by the positive-radius gauge or division formulae.

## 6. Jointly conditioned response sets and identification

### 6.1 The joint feasible construction

Let \(\eta\) collect the maintained frame, congruence, perturbative branch, attribution and nuisance policy, together with the registered analysis procedure. Define

\[
\boxed{
\Theta(y;\eta)
=D_\eta\cap B_{\rm MES}(y;\eta)
\cap\mathcal R_\eta^{-1}(C_y(\eta)).
}
\]

The physical domain \(D_\eta\), sector constraints \(B_{\rm MES}\), response \(\mathcal R_\eta\) and observational compatibility region \(C_y\) must each be specified. The intersection does not create a response where none is available.

If the same data construct the MES ceilings and the compatibility region, the factors are restrictions within one jointly conditioned system, not independent observations. Any likelihood or evidence factorisation requires an additional joint-law argument. Partial-identification literature distinguishes characterisation of admissible parameter sets from their estimation and confidence procedures; it provides context rather than a proof of the project-specific tensor response. [@MOLINARI_2020; @KAIDO_MOLINARI_STOYE_2022]

### 6.2 Exact affine fibres

For an exact linear response and exact observed vector \(y\), let \(X_0\) be feasible and write \(F_y=D_\eta\cap B_{\rm MES}(y;\eta)\). Then

\[
\Theta(y;\eta)=F_y\cap(X_0+\ker\mathcal R_\eta).
\]

Thus

\[
\boxed{
\Theta(y;\eta)=\{X_0\}
\quad\Longleftrightarrow\quad
\{h\in\ker\mathcal R_\eta:X_0+h\in F_y\}=\{0\}.
}
\]

The equivalence follows by translating every other feasible point by \(-X_0\). Full column rank is sufficient but need not be necessary: predeclared inequalities may exclude every nonzero kernel displacement. The exact example

\[
\mathcal R=(1\ \ 1),\qquad y=0,\qquad x_1,x_2\ge0
\]

has only the feasible point \((0,0)\), although the response has rank one.

An empty feasible set reports inconsistency with the maintained constraints, not a detection. A bounded non-singleton set retains partial ambiguity; unbounded and disconnected sets retain their corresponding geometry. Failure to supply or solve a response is undetermined, not evidence for a physical null. No shear, vorticity, acceleration or global-tilt estimate is inferred in a sector whose physical response is absent.

### 6.3 Sampling uncertainty is a separate question

For noisy finite data, the displayed \(\Theta(y;\eta)\) is first a realised compatibility construction. Its cardinality alone does not establish population point identification or confidence coverage. A statistical statement requires a sampling law and justified constructions of both the compatibility region and any data-derived anchors. The exact affine-fibre criterion is not extended to such a theorem by terminology alone.

This distinction already appears in the K3 core draft and is retained here as an explicit interpretation boundary. It does not silently replace the canonical claim ledger. It also explains why the next statistical step must calibrate the complete data-to-output operation rather than attach a nominal rank to an already selected physical explanation.

## 7. Finite-null validity of the complete analysis

### 7.1 Exchangeable observation/reference rows

Let \(Z=(Z_0,\ldots,Z_N)\) contain an observation and reference rows, and let the complete analysis return \(S(Z)=(S_0(Z),\ldots,S_N(Z))\). Complete analysis includes observable construction, MES ceilings and their conditioning, chart availability, nuisance fitting, adaptive selection, missingness, ties and final scoring.

If the rows are jointly exchangeable under the null and

\[
S_i(\pi Z)=S_{\pi^{-1}i}(Z)
\]

for every row permutation, the observation-inclusive upper-tail rank

\[
\boxed{
p_{\rm row}(Z)=
\frac{1+\sum_{i=1}^N\mathbf1\{S_i(Z)\ge S_0(Z)\}}{N+1}
}
\]

is conservative and super-uniform. Joint exchangeability and complete row equivariance are substantive premises; they are not implied by the denominator \(N+1\).

### 7.2 Finite transformation-group randomisation

For a finite transformation group \(\mathcal G\) under which the null law is invariant, the exact orbit rank is instead

\[
\boxed{
p_{\mathcal G}(Z)=\frac1{|\mathcal G|}
\sum_{g\in\mathcal G}\mathbf1\{T(gZ)\ge T(Z)\}.
}
\]

A sampled set of transformations requires a valid identity-including conditional-Monte-Carlo construction, not an arbitrary collection of reference rows. [@RANDOMIZATION_2024; @PHIPSON_SMYTH_2010; @HEMERIK_GOEMAN_2018]

The inherited exact counterexample assigns probability \(1/2\) to each of

\[
z^{(1)}=(10,0,-100,-100),\qquad
z^{(2)}=(0,10,-100,-100).
\]

This law is invariant under swapping rows 0 and 1. Ranking row 0 against all four rows gives \(p_{\mathrm{all}}=1/4\) or \(1/2\), so

\[
\Pr(p_{\mathrm{all}}\le1/2)=1>1/2.
\]

Ranking over the actual two-element orbit instead gives \(1/2\) or \(1\). Proper-subgroup invariance therefore does not license comparison with rows outside that orbit. These two finite-sample theorems retain different reference objects and are not merged into an exchangeability-or-group premise.

### 7.3 Adaptation, chart failures and null fidelity

Adaptive selection is valid only when the complete map preserves the relevant symmetry or uses a separately justified independent design. In the registered four-row enumeration, one asymmetric tie rule gives 12 permutations at \(p=1/2\) and 12 at \(p=3/4\); the alternative asymmetric tie rule gives 6 and 18. Both have rejection probability one at \(\alpha=3/4\), an exact size excess \(1/4\). The registered pooled permutation-invariant rule has zero maximum super-uniformity violation. These are inherited finite enumeration results, not newly executed simulations.

Chart failure belongs to the analysis map. Deleting chart-unavailable reference rows while retaining an available observation changes the comparison law. A valid construction uses a statistic for every row, a symmetric pooled fallback or abstention. Data-derived anchor construction is subject to the same requirement.

Null fidelity is separate from valid rank arithmetic. A noisy observation and noise-free CMB-only simulations are not jointly exchangeable without a matched joint law. Multiple outputs sharing the same sky or simulation rows are not independent replications merely because they have different names or use different tensor summaries.

## 8. Exact local radiation–observer response

### 8.1 Domain and pullback

For the local response, identify \(\beta_{\rm obs}\) with the radiation–observer velocity \(\beta_{\rm RO}\), retaining

\[
u_a\beta_{\rm obs}^a=0,\qquad
0\le\beta_{\rm obs}^2<1,
\]

\[
\widetilde u^a=\gamma(u^a+\beta_{\rm obs}^a),
\qquad \gamma=(1-\beta_{\rm obs}^2)^{-1/2}.
\]

These conditions imply \(\widetilde u^a\widetilde u_a=-1\). With the outward sky convention of Section 2, the exact full-sky thermodynamic-temperature pullback for Doppler weight \(d=1\) is

\[
\widetilde T(\widetilde n)
=\frac{T(n(\widetilde n))}
{\gamma(1-\beta_{\rm obs}\cdot\widetilde n)}.
\]

The absolute-temperature field is strictly positive. The retained first-order generator is

\[
\delta_\beta T
=(\beta_{\rm obs}\cdot n)T
-[\beta_{\rm obs}-(\beta_{\rm obs}\cdot n)n]\cdot\nabla_{S^2}T.
\]

Harmonic aberration operators and general Doppler-weight kernels provide the relevant response background. Frequency-dependent observables are not silently assigned the \(d=1\) temperature law. [@DAI_CHLUBA_2014; @YASINI_PIERPAOLI_2017]

### 8.2 Quadrupole-to-octupole response

For the registered STF convention,

\[
\boxed{(B_Q\beta)_{abc}=3\beta_{\langle a}Q_{bc\rangle}},
\]

and the inherited adjoint normal matrix is

\[
\boxed{M_Q=q_2I+\frac65Q^2},\qquad q_2=Q:Q.
\]

For a nonzero quadrupole, the trace-free eigenvalue constraints give the retained sharp conditioning bound

\[
\boxed{\kappa_2(M_Q)\le\frac53}.
\]

The ideal inverse leaves a four-dimensional STF3 residual orthogonal to the quadrupole-response image. This is a response-space residual, not automatically a physical intrinsic octupole. The local-boost and intrinsic-dipole interpretations remain distinct physical hypotheses. [@ROLDAN_NOTARI_QUARTIN_2016]

An available response operator is not an empirical velocity estimate. It also does not identify \(\beta_{\rm RM}\), \(\beta_{\rm MO}\), physical shear or global matter-frame tilt. This scoped response is the concrete link to one physical-state sector; it does not close all other physical responses.

## 9. Processed response and the high-source nuisance quotient

### 9.1 Ordered estimator

The processed construction applies a positive absolute thermodynamic-temperature sky, then the exact or first-order local boost, source beam and pixel-window transfer, spherical synthesis, a weighted joint \(\ell=0,\ldots,5\) fit, post-fit source/target commonisation and retention of \(\ell=2,\ldots,5\). This order is part of the estimator definition.

Partial-sky masks mix modes, and filtering can require a matrix-valued transfer rather than a scalar transfer function. [@MASTER_2002; @LEUNG_2022] Consequently, a response defined before masking or fitting cannot simply be inserted after those operations without establishing the required equivalence.

The retained output has 32 coordinates. The low-source coordinate includes the physical monopole and raw real harmonics through \(\ell=6\), giving the first-order Jacobian shape

\[
J\in\mathbb R^{3\times32\times49}.
\]

A constant physical monopole produces a pure dipole at first order. Because the simultaneous fit includes \(\ell=0,1\) and the retained carrier starts at \(\ell=2\), its physical \(T_0\) column is an exact structural null. Finite transform leakage is separately recorded as a numerical replay diagnostic rather than promoted into a physical column.

### 9.2 Quotient identity and nested nuisance spaces

For fixed boost direction \(\hat b\), let

\[
J_{\hat b}\in\mathbb R^{32\times48},
\qquad
K_{\hat b}^{\rm hi}(L)
=[K_{\hat b}^{(7)}|\cdots|K_{\hat b}^{(L)}].
\]

The unrestricted deterministic high-source band has column dimension

\[
d_H(L)=(L-6)(L+8).
\]

Define \(\mathcal H_{\hat b}(L)=\operatorname{Im}K_{\hat b}^{\rm hi}(L)\). The low-source survivor is

\[
J_{\rm surv}(L)=P_{\mathcal H_{\hat b}(L)^\perp}J_{\hat b},
\]

and the exact rank relation is

\[
\boxed{
\operatorname{rank}J_{\rm surv}(L)
=\operatorname{rank}[K_{\hat b}^{\rm hi}(L)\;J_{\hat b}]
-\operatorname{rank}K_{\hat b}^{\rm hi}(L).
}
\]

The identity compares the dimension added by \(J\) to the nuisance image with the dimension of its projected image. The high-source images are nested as \(L\) increases. Once valid containment has been established, increasing the unrestricted nuisance cutoff cannot restore a model-free survivor. Column count alone, however, is not a rank certificate.

### 9.3 Finite-operator evidence boundary

The inherited frozen Task-7B atlas found no registered cut-sky case satisfying all conditioning, \(\ell=6\)-alias and extended-tail criteria. This is a result for that atlas, not a theorem about all masks or physical sources. The last accepted byte-exact matched-control Task-7C result remains rank unresolved: 17 registered coordinates were ambiguous, one had a resolved survivor and none was a containment candidate.

These statements retain their original source and execution grades. They are not rerun here. They do not establish a finite-HEALPix no-go theorem, nor do they identify a physical high-source amplitude distribution. The quotient is defined for the stated deterministic nuisance class; a physical covariance, prior or bounded nuisance body is a different inference problem.

## 10. Registered continuum wide-mask evidence

For the registered axisymmetric wide mask,

\[
w(\mu)=\operatorname{clip}\!\left(\frac{\mu+3/4}{3/2},0,1\right),
\]

let

\[
N_{\alpha\beta}=\int wY_\alpha^*Y_\beta\,d\Omega,
\qquad
R_{\alpha p}^{(\hat b)}=\int wY_\alpha^*\mathcal B_{\hat b}Y_p\,d\Omega,
\]

\[
K_{\hat b}^{\rm cont}(L)=P_{2:5}N^{-1}R_{\hat b}^{7:L}.
\]

The model uses the registered continuum identity-transfer construction. It is not the finite-HEALPix operator with its numerical implementation errors omitted by declaration.

For the axial direction at \(L=12\), the inherited exact rational complex-block ranks for \(m=0,\ldots,5\) are

\[
(4,4,4,3,2,1).
\]

The corresponding stored-real count is \(4+2(4+4+3+2+1)=32\). Independent high-precision and direct-quadrature calculations in the source evidence report:

| Source cutoff \(L\) | Axial \(Z\) rank | \(X/Y\) rank | Registered diagonal rank |
|---:|---:|---:|---:|
| 8 | 20 | 24 | 24 |
| 9 | 27 | 29 | 32 |
| 12 | 32 | 32 | 32 |

At \(L=12\), the inherited smallest singular values are

\[
\sigma_{\min}^{Z}\simeq0.00690566498,
\qquad
\sigma_{\min}^{X/Y}\simeq0.01049033491,
\qquad
\sigma_{\min}^{\rm diagonal}\simeq0.00851032278.
\]

These numerical scales belong to the registered continuum coordinate and transfer convention. They are not dimensionless physical kinematical bounds. The axial result has an exact author-artifact rank certificate; the other five registered directions have multi-engine numerical evidence, not portable interval certificates. This draft copies the source results and their qualifications without claiming fresh computation.

Continuum full row rank does not certify finite-HEALPix robust full row rank. Weak singular modes can be affected by transform, quadrature, iterative-fit and roundoff errors. A numerical-error bridge is required before the finite operator can inherit a containment conclusion. The current finite result therefore remains unresolved even though the registered continuum model has full row rank at the stated cutoff.

## 11. Matrix-valued numerical uncertainty

### 11.1 Frozen error families and a Loewner envelope

Let each nonempty error family contain matrices \(E_{fi}\) of compatible shape. Fix the partition, basis, radii \(r_f>0\), calibration and holdout sets, processing settings and coordinate identity before examining rank or holdout outcomes. For

\[
\Delta_f=\sum_i b_{fi}E_{fi},\qquad \|b_f\|_2\le r_f,
\qquad
\Delta=\sum_{f=1}^{N_{\rm fam}}\Delta_f,
\]

Cauchy–Schwarz yields

\[
\Delta\Delta^T
\preceq N_{\rm fam}\sum_f r_f^2\sum_iE_{fi}E_{fi}^T.
\]

The registered regularised envelope is

\[
\boxed{
\Gamma_E=N_{\rm fam}\sum_f r_f^2\sum_iE_{fi}E_{fi}^T
+\lambda_{\rm reg}^2I,
\qquad\lambda_{\rm reg}>0.
}
\]

Its terms have the same squared response units in the chosen coordinates. For nonzero \(x\),

\[
x^T\Gamma_Ex
=N_{\rm fam}\sum_f r_f^2\sum_i\|E_{fi}^Tx\|^2
+\lambda_{\rm reg}^2\|x\|^2>0,
\]

so \(\Gamma_E^{-1/2}\) exists. This ordered quadratic-form argument is retained as a direct justification of the domain, not presented as a newly kernel-checked proof.

Within the fixed partition, compensated positive scaling

\[
E_{fi}\mapsto c_fE_{fi},\qquad r_f\mapsto r_f/c_f,
\qquad c_f>0,
\]

and orthogonal mixing within each family leave the envelope unchanged. An exactly zero family must be omitted or rejected: it leaves the perturbation set unchanged while altering the conservative factor \(N_{\rm fam}\).

### 11.2 Conditional robust rank and subspace limits

If the actual numerical error belongs to the declared class, then

\[
\Delta\Delta^T\preceq\Gamma_E,
\qquad\|\Gamma_E^{-1/2}\Delta\|_2\le1.
\]

For \(\widetilde K_{\rm obs}=\Gamma_E^{-1/2}K_{\rm obs}\), singular values above one give a robust nonzero-rank lower bound. All retained row singular values above a preregistered margin certify full row rank for that error class. The whitening makes this threshold dimensionless in the declared coordinate metric.

The implication is conditional. It does not establish that the present finite-HEALPix family registry contains the actual error, and it does not permit tuning radii after inspecting the signal. The coverage of the numerical-error class is a separate mathematical and computational obligation.

A rank lower bound also does not certify the orientation of a singular subspace. A stable nuisance projector requires perturbation control relative to a positive singular-value gap. Singular-subspace perturbation results provide that additional type of bound; they do not follow from the number of singular values exceeding a threshold. [@CAI_ZHANG_2018; @LI_1999; @LYU_WANG_2020]

## 12. Integrated interpretation, evidence boundary and conclusions

### 12.1 What the integrated framework retains

The framework retains two tensorial descriptions without conflating them. The observable \(Q/O\) carrier preserves low-multipole morphology, and its cyclic packet supplies a proper-rotation chart on the stated forward-image domain. The physical state separately retains congruence kinematics, frame relations, scalar curvature budget and optional geometry tensors. Physical functionals can retain shape, parity and relative orientation before any scalar diagnostic is selected.

MES inequalities are inherited within this physical state as premise-matched radial constraints on shear and vorticity. They neither disappear into a historical appendix nor become directional tensor estimators. The distinction between the geodesic acceleration premise and absence of a numerical acceleration anchor prevents a structural assumption from being misreported as a measured zero. The exact channel and denominator rules also prevent a convenient scalar ratio from concealing frame or conditioning mismatches.

The relation to observations is supplied by a declared response and a joint feasible construction. Shared-data constraints are not independent evidence. Exact fibre uniqueness, finite-sample compatibility and statistical identification remain distinct questions. Consequently, a complete observable tensor representation can coexist with a broad or unavailable physical identified set.

### 12.2 What is and is not established

The local \(\beta_{\rm RO}\) response is a concrete available lane, but it does not close the physical shear, vorticity, acceleration, global-tilt or geometry responses. After the stated processing operation, nuisance quotienting and numerical uncertainty further limit attribution. The registered continuum calculation provides exact or numerical full-row-rank evidence according to direction, whereas the finite-HEALPix matched-control result remains rank unresolved.

| Result layer | Evidence retained from source | Limitation in this draft |
|---|---|---|
| Real carrier and STF norm map | exact derivation; implementation source | not a new execution |
| Cyclic \(Q/O\) reconstruction | exact result on the declared forward image | no arbitrary-packet or all-strata theorem |
| Physical state and functionals | typed donor source and K1R semantics | donor execution not inherited |
| MES sector inequalities | conditional primary-source/repository reduction | premises and attribution remain explicit |
| Radial/gauge/fibre relations | direct conditional or exact derivations | no new CAS receipt |
| Finite-null constructions | separate row/orbit theorems; inherited exact counterexamples | no certification of an actual Planck/FFP10 pool |
| Local-observer response | frozen-scope implementation evidence | not a measured velocity or global-tilt response |
| Processed quotient | exact linear-algebra identities | depends on the declared nuisance class |
| Registered finite atlas and matched control | inherited frozen numerical evidence | finite robust containment unresolved |
| Continuum axial/non-axial results | exact axial artifact; non-axial numerical evidence | no finite-HEALPix implication |
| Numerical-error envelope | exact conditional inequality | actual error-class completeness unproved here |

The literal observational boundary remains

```text
CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE
CURRENT_OBSERVATIONAL_RESULT = NONE
PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER
FINITE_HEALPIX_CONTAINMENT = RANK_UNRESOLVED
```

### 12.3 Conclusions

The physical content of MES bounds is compatible with tensorised inference, provided that observable morphology, physical kinematics, anchor constraints and identification are kept distinct. The original physical-state programme and the later \(Q/O\), finite-null and response developments can therefore be combined without reverting to the retired scalar-collection observational methodology.

The resulting report does not force a physical point estimate. It states which sectors are represented, which are conditionally restricted, which have a response and which remain unresolved. A physical covariance or prior, polarisation, frequency dependence, additional angular modes or independent depth information may refine the feasible set, but each requires its own response and statistical premises. These extensions are not silently supplied by the present formulation.

Corrected observational analysis remains a subsequent, separately authorised task. The immediate output is a coherent theory-and-methods draft with explicit mathematical domains and evidence boundaries, not an observational claim or publication approval.

# Appendix A. Forty-claim candidate map

The following map preserves the existing thirty identities and places the ten kinematical candidates in the complete manuscript. The four revised existing claims are explicitly marked. This is a source-level drafting map, not the materialised T9 v5 or an automated bijection receipt.

| Claim ID | Location | Draft role and status relative to T9 v4 |
|---|---|---|
| `RA-SCOPE-001` | 1 | retained scope and supersession |
| `RA-REP-001` | 2.2 | retained real-carrier isometry |
| `RA-REP-002` | 2.2 | retained metric adapter |
| `RA-REP-003` | 2.3 | retained STF norms |
| `RA-ORBIT-001` | 3.1 | retained locally free quotient dimension |
| `RA-ORBIT-002` | 3.2 | retained cyclic forward-image reconstruction |
| `RA-ORBIT-003` | 3.3 | retained named mirror-separation result |
| `RA-ORBIT-004` | 3.3 | retained typed chart failures |
| `RA-KIN-001` | 4.1 | candidate physical-state factorisation |
| `RA-KIN-002` | 4.2 | candidate frame-velocity semantics |
| `RA-KIN-003` | 4.1 | candidate typed missingness |
| `RA-GEO-001` | 4.3 | candidate scalar/tensor geometry and dimension |
| `RA-KFUNC-001` | 4.4 | candidate physical tensor functionals |
| `RA-MES-001` | 5.1 | retained PSTF normalisation |
| `RA-MES-002` | 5.1–5.2 | revised: named physical-sector radial constraints |
| `RA-MES-003` | 5.3 | revised: equivariance obstruction and radial interpretation |
| `RA-MESA-001` | 5.1–5.2 | candidate active anchors and acceleration dual status |
| `RA-MESA-002` | 5.4 | candidate channel and denominator admissibility |
| `RA-MESA-003` | 5.4 | candidate product gauge and coupled-set boundary |
| `RA-ID-001` | 6.1, 6.3 | candidate shared-data jointly conditioned set |
| `RA-ID-002` | 6.2 | candidate exact feasible-fibre criterion |
| `RA-STAT-001` | 7.1 | retained exchangeable-row theorem |
| `RA-STAT-002` | 7.1, 7.3 | revised: complete analysis includes anchor construction |
| `RA-STAT-003` | 7.3 | retained null-fidelity boundary |
| `RA-STAT-004` | 7.2 | retained transformation-group orbit theorem |
| `RA-RESP-001` | 8.1 | revised: radiation–observer response only |
| `RA-RESP-002` | 8.2 | retained STF response and conditioning |
| `RA-PROC-001` | 9.1 | retained processing order |
| `RA-PROC-002` | 9.1 | retained structural monopole null |
| `RA-PROC-003` | 9.2 | retained quotient identity and nesting |
| `RA-PROC-004` | 9.3 | retained registered-atlas negative result |
| `RA-PROC-005` | 9.3 | retained finite rank-unresolved result |
| `RA-CONT-001` | 10 | retained exact axial continuum certificate |
| `RA-CONT-002` | 10 | retained non-axial numerical evidence |
| `RA-CONT-003` | 10 | retained continuum/discrete boundary |
| `RA-ERR-001` | 11.1 | retained family-ball Loewner envelope |
| `RA-ERR-002` | 11.1 | retained fixed-partition invariances |
| `RA-ERR-003` | 11.2 | retained conditional robust-rank criterion |
| `RA-ERR-004` | 11.2 | retained singular-subspace gap requirement |
| `RA-BOUNDARY-001` | 12.2 | retained absence of observation-bearing results |

# Appendix B. Source identity and evidence provenance

The assembly input snapshot was PR #449 head
`6bea7a5e2cda1b3e001657061d329fe5cec6bed2`, tree
`77b598236da2d0b3332dec9edda9e306a2b95263`, base
`687234128d7c12d04e68aad0f303c21d2d470393`.
The principal files read at that snapshot were:

| Source | Git blob | Use in this draft |
|---|---|---|
| `docs/research_reports/HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md` | `16f8fdd4db4dac384c5c64a8d3f86e0dbbf62e34` | retained observable, statistics, response, continuum and error theory |
| `docs/research_reports/drafts/K3_TYPED_KINEMATICAL_MES_CORE_DRAFT_20260905.md` | `abf6c80d40bc2cfba27888d34f3dff16f94f012d` | physical-state/MES/identified-set core and sampling clarification |
| `docs/codex_handoff/htt_tensorized_report_first_20260903/REPORT_SECTION_CLAIM_MAP_V2_CANDIDATE.csv` | `d42a666ff0eba8fdca8afc9b4e719de6e5e12a8d` | twelve-section, forty-ID candidate organisation |
| `docs/research_reports/HTT_REPORT_A_REFERENCES.bib` | `ba37321119725e52f1a2b0ac827050ee895e5466` | existing seventeen-key bibliography |
| `docs/research_reports/report_a/K2_BIBLIOGRAPHY_SUPPLEMENT_CANDIDATE.bib` | `930457120f5def21321008f4f77cc2b9c0f5694a` | three contextual candidate references |

The original typed physical-state donor is merged PR #367 at published head
`6bafca66285ef071081453313bb7d2d6b261599c`. Its semantic contribution is traced
through the K0/K1R and core-draft authorities; this assembly does not constitute
a fresh repository-wide donor audit or execution replay.

The former thirty-claim manuscript, the core-section draft, T9 v4, candidate
overlays and bibliography files remain unchanged by this new document. Existing
frozen numerical evidence retains its original provenance and limitations. In
particular, the continuum table, singular values and finite atlas counts were
transferred from the original manuscript, not computed during assembly.

# Appendix C. Citation roles and preserved interpretation boundaries

This draft uses the existing seventeen citation keys and the three candidate
keys `ELLIS_VAN_ELST_1999`, `MOLINARI_2020` and
`KAIDO_MOLINARI_STOYE_2022`. It does not claim that a new twenty-entry canonical
bibliography has been materialised. The future rendering step must consume
the reviewed existing bibliography and explicit supplement, or the accepted
compiled successor, rather than a manually invented reference list.

The MES papers and COBE-era source provide the physical and normalisation
lineage. Ellis–van Elst supplies covariant background. Molinari is an
authoritative survey of partial identification, and Kaido–Molinari–Stoye
provides research context for constraint geometry. None is cited as a proof
of the repository-specific tensor response or exact channel contract.
Invariant-theory references remain adjacent sources rather than a proof of
this exact Krylov reconstruction. Novelty is unresolved.

The contextual web check in this assembly confirmed that the original MES
papers describe matter–radiation restrictions and improved assumption-dependent
limits, and that the Molinari chapter is a review. It was not an equation-level
rederivation of the MES coefficients. Search-index duplicate records, ingestion
dates and abbreviated author lists were not substituted for the existing
formal bibliography.

Editorial qualification inherited from the core draft: a realised noisy-data
compatibility set is not automatically a population identified set or a
confidence region. The exact affine-fibre argument is confined to exact linear
response and exact data. Domain qualifications made explicit in this assembly
are the nonzero quadrupole for the conditioning ratio, positive compensated
family scalings, nonzero rate normalisation and positive sector radii for
gauge/division formulae. They restrict interpretation; they do not assert new
observational or formal-verification results.

The word rank is separated into algebraic rank, tolerance-dependent numerical
rank, error-class-conditional robust rank, quotient rank and finite-pool order
rank. The continuum and finite operators are not identified by sharing matrix
shape. Likewise, shear/vorticity bounds and kinematical point estimates are not
identified by sharing a normalisation.

# Appendix D. Work not performed by this draft

This assembly did not execute the K2FR0 compiler or its tests, generate T9 v5,
replay the required SymPy/Lean axes, compile TeX or PDF, or perform a page-level
visual audit. It did not run Planck/FFP10, estimate a physical kinematical state,
resolve finite-HEALPix containment or authorise publication/merge. A complete
source draft is a writing milestone, not a release or scientific-verification
milestone.

The next manuscript task is a whole-draft review of equations, assumptions,
source support, the forty-ID mapping and citation roles. In parallel, the
existing exact-runtime materialisation and formal-verification tasks remain
necessary for their own acceptance decisions. The reviewed source may then be
typeset and visually inspected; final release requires the applicable receipts
and an explicit owner decision. No additional audit-only infrastructure is
required merely to begin reading or revising this full draft.
