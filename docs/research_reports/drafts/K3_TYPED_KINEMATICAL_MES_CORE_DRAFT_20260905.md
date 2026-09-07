# Report A — typed kinematical MES inheritance: core-section draft

## Draft status and source boundary

This is a substantive draft of proposed Sections 4–6 and their transition to
Sections 7–9. It is not the complete revised manuscript, a replacement for the
current canonical manuscript, or an executed K2F output. The canonical claim
ledger remains T9 v4 with thirty claims. The forty-claim surface and the
three-entry bibliography supplement remain candidates.

The source basis was inspected at report-branch commit
`55550e66c04912f0f204d1c02d8003f986d23202`:

- `docs/research_reports/theory_packs/K1R_TYPED_KINEMATICAL_MES_THEOREM_PACK.md`,
  Git blob `d93ab24adbb089e9d568512ebf10591dc6880414`;
- `K0_TYPED_KINEMATICAL_MES_AUTHORITY_CROSSWALK_V2.yaml`,
  Git blob `9ed7b47f23b5515ab42defcaa94431a758a57e74`;
- `K2_40_CLAIM_CANDIDATE_OVERLAY.yaml`,
  Git blob `394378a796a24410a4174a8222e40c5c59e9700a`;
- `K2_REPORT_A_CLAIM_ARCHITECTURE.md`,
  Git blob `da4edec5db72863e4b1234a4e0b3027f66413897`.

The original physical-state donor is merged PR #367, published head
`6bafca66285ef071081453313bb7d2d6b261599c`. Its semantics are used without
claiming that its code or execution history has become a linear ancestor of
the report branch. Citation keys below are existing formal or explicitly
candidate keys; this draft does not merge bibliography authorities.

The distinction between a realised compatibility set and population
identification in Section 6.3 is an explicit editorial clarification informed
by the partial-identification literature. It does not change the canonical
claim ledger or assert a new coverage theorem.

## 4. Physical kinematics, frame relations and tensor morphology

### 4.1 Observable and physical state spaces

The observable low-multipole state is

\[
\mathcal O_{\rm low}=(Q_{ab},O_{abc},\ldots),
\qquad
Q_{ab}\in\mathrm{STF}_2(\mathbb R^3),
\quad
O_{abc}\in\mathrm{STF}_3(\mathbb R^3).
\]

These tensors retain the angular temperature morphology in the corrected
harmonic normalisation. The physical state is a different object,

\[
\mathcal X_{\rm phys}
=\mathcal K_u\times\mathcal V_{\rm frame}\times\mathcal G,
\qquad
\mathcal K_u=(\sigma_{ab},\omega_a,A_a).
\]

The shear, vorticity and acceleration refer to a specified timelike
congruence. We use signature \((-+++ )\), a unit observer
\(u^a u_a=-1\), and retain the channel's declared units and normalisation.
In particular, \(Q_{ab}\) and \(\sigma_{ab}\) both transform as rank-two
STF tensors, but equality of representation types supplies neither a physical
identity nor a response operator between them. The covariant separation of
kinematics, matter and radiation provides the background for this distinction;
the present state partition additionally fixes the metadata required by each
sector. [@ELLIS_VAN_ELST_1999]

The state description records frame, congruence, epoch or window, averaging
scale, basis, units and perturbative branch. An untyped legacy vector cannot
be assigned a physical frame role without an explicit adapter. Similarly,
an unavailable physical component is not set to zero. A zero value is a
physical assertion; missingness is a statement about the available input or
provider.

### 4.2 Frame velocities and the scope of the local response

The velocity block is

\[
\mathcal V_{\rm frame}
=(\beta_{\rm RO}^a,\beta_{\rm RM}^a,\beta_{\rm MO}^a),
\qquad \beta^a=v^a/c,
\]

with radiation, matter and observer roles retained separately. In the
registered first-order closure convention,

\[
\beta_{\rm RO}^a
=\beta_{\rm RM}^a+\beta_{\rm MO}^a+O(\beta^2).
\]

This relation is not an exact relativistic velocity-addition law and is not a
measurement of any of its three terms. In particular,
\(\beta_{\rm RO}=\beta_{\rm MO}\) requires an additional premise concerning
\(\beta_{\rm RM}\).

The existing full-sky thermodynamic-temperature local-observer response acts
in the radiation-observer lane, \(\beta_{\rm RO}\). Its availability is
therefore a concrete response result, but does not identify radiation-matter
tilt, matter-observer velocity or congruence shear. The observable dipole,
frame closure and global matter-frame tilt are not interchangeable objects.

### 4.3 Geometry, parity and conditional dimension counts

The scalar \(\Delta\Omega_k\) is a signed curvature-budget coordinate. It
is distinct from an optional anisotropic spatial-curvature tensor
\({}^{(3)}S_{ab}\), and from optional electric Weyl, magnetic Weyl and
anisotropic-stress tensors. These quantities are admitted only under their
separately declared geometric and matter conventions.

The shear is a five-dimensional polar STF2 block, vorticity a three-dimensional
axial-vector block and acceleration a three-dimensional polar-vector block.
The three velocity fields are polar vectors. The scalar curvature-budget
coordinate has one component; each optional STF2 field has five. The magnetic
Weyl block is axial, whereas the other listed STF2 geometry blocks are polar.
Parity is attached to the representation and is not inferred from a component's
numerical sign.

Excluding optional geometry fields and treating \(\beta_{\rm RO}\) as a
closure-derived view in the first-order chart gives

\[
\dim\mathcal X_{\rm core}^{\rm general}
=5+3+3+3+3+1=18.
\]

On a locally free \(SO(3)\) stratum the quotient dimension is consequently
\(18-3=15\). On the geodesic subdomain \(A_a=0\), the corresponding raw
and locally free quotient dimensions are \(15\) and \(12\). These counts
refer to the declared kinematical parameter space, not the dimension of a
space of Einstein-equation solutions or an observationally identified model.
They also do not establish global orbit separation. Non-trivial stabilisers,
additional constraints and different admitted blocks require their own count.

### 4.4 Physical tensor functionals and orbit morphology

A registered functional

\[
\phi:\mathcal X_{\rm phys}\longrightarrow W_\phi
\]

retains the state identity and the tensor type of its output. Its codomain may
be scalar, pseudoscalar, vector, STF tensor, set or path valued. Representative
physical functionals include

\[
\operatorname{tr}\sigma^2,\qquad
\operatorname{tr}\sigma^3,\qquad
\omega_a\omega^a,
\]

\[
\beta_{\rm RM}\cdot\omega,
\qquad
\beta_{\rm RM}^{a}\sigma_{ab}\beta_{\rm RM}^{b}.
\]

The first quadratic invariant records a shear magnitude; the cubic invariant
retains additional shape information. The velocity-vorticity contraction is
a pseudoscalar under the declared polar/axial convention. Such functionals
can describe physical morphology and relative orientation without being
observational estimates. A missing input remains a typed failure, and a scalar
projection does not erase the tensor-valued source from which it was obtained.

## 5. MES inequalities as physical-sector constraints

### 5.1 What is inherited from the scalar bounds

Tensorisation does not discard the physical restrictions supplied by the MES
inequalities. It places them on named sectors of the physical state while
retaining the complete observable tensor representation. The current
geodesic channels constrain the registered invariants

\[
\psi_\sigma(X)=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},
\qquad
\psi_\omega(X)=\frac{\omega_{ab}\omega^{ab}}{6H^2},
\]

using the exact vorticity vector-to-tensor adapter and rate convention of the
channel. The common rate normalisation is assumed valid, with \(H\ne0\).
No factor is inferred by identifying the axial-vector norm with the
antisymmetric-tensor contraction. The associated ceilings are denoted
\(U_\sigma\) and \(U_\omega\); their numerical use requires the original
multipole, congruence and approximation premises. [@MES_1995_LIMITS;
@SAG_1999_COBE]

For a maintained policy \(\eta\), the matched constraints take the form

\[
\psi_\sigma(X)\le U_\sigma(y;\eta),
\qquad
\psi_\omega(X)\le U_\omega(y;\eta).
\]

The argument \(y\) is retained when the ceilings are constructed from the
same low-multipole data used elsewhere in the analysis. An externally fixed
calibration is a different conditioning regime. In neither regime is the
ceiling itself an observation of shear or vorticity. It constrains an
invariant under maintained premises and supplies no converse FLRW result.

The geodesic condition \(A_a=0\) and the absence of a numerical acceleration
anchor must also remain distinct. The first is a branch premise. The second
means that no numerical denominator is provided. It is not a measured
zero-radius acceleration constraint, and it does not impose \(A_a=0\) in a
general non-geodesic physical state. Optional geometry sectors similarly do
not acquire MES anchors by analogy.

### 5.2 Radial constraints do not determine physical morphology

For a registered Euclidean sector ball

\[
B_j=\{x_j:\|x_j\|\le R_j\},\qquad R_j>0,
\]

an orthogonal representation action preserves the norm. Thus
\(x_j\in B_j\) if and only if \(g x_j\in B_j\), for every allowed
orthogonal transformation \(g\). The anchor status is constant along the
entire orbit.

The MES restriction therefore cannot select a vector direction, tensor
eigenframe or handedness. For these norm-only constraints, states with the
same magnitude also receive the same admission decision even when their
non-radial shape invariants differ. This does not deny the existence of
physical morphology. It locates that information in separately typed
functionals, additional directional data or a declared response, rather than
in the scalar ceiling.

### 5.3 Product geometry, squared stress and denominator conditioning

For a finite nonempty collection of matched, positive-radius Euclidean sector
balls, the product-body Minkowski gauge is

\[
\rho_{B_{\rm prod}}(x)
=\max_j\frac{\|x_j\|}{R_j},
\qquad B_{\rm prod}=\prod_jB_j.
\]

Indeed, membership of \(tB_{\rm prod}\) requires
\(t\ge\|x_j\|/R_j\) for every sector, so the infimum of admissible
\(t\) is the displayed maximum. This prevents signed cancellation between
sector excesses.

If \(N_j=\|x_j\|^2\), \(U_j=R_j^2\) and
\(S_j=N_j/U_j\), then

\[
\rho_{B_{\rm prod}}^2=\max_j S_j.
\]

The gauge and quadratic saturation therefore share the threshold one, but
their exceedance margins are not numerically identical. Neither margin is
automatically a probability or an evidence term.

The maximum formula concerns the factorised anchor body, not the full feasible
set after response, physical or nuisance constraints couple sectors. For
example, the square \(B_0=[-1,1]^2\) has
\(\rho_{B_0}(1,1)=1\), whereas
\(F=B_0\cap\{x_1+x_2\le1\}\) has \(\rho_F(1,1)=2\).
Replacing the latter geometry by independent sector marginals loses a real
constraint.

A numerical sector ratio additionally requires identical sector, invariant,
frame, congruence, normalisation, perturbative order and branch. For a fixed
ensemble-calibrated \(U_j>0\), an identified numerator interval maps to

\[
[\underline N_j,\overline N_j]/U_j
=[\underline N_j/U_j,\overline N_j/U_j].
\]

A realisation-conditioned random denominator is not divided as though it were
fixed. It remains ratio-unidentified until the joint random-anchor inference
problem is specified. This restriction is compatible with using a realised
anchor in a joint feasibility calculation; it prevents that calculation from
being mislabelled as independently calibrated ratio inference.

## 6. Response-constrained sets and finite-null interpretation

### 6.1 One jointly conditioned feasible system

Let \(\eta\) record the maintained frame, congruence, branch, attribution
and nuisance policy, together with the data-processing procedure. Define

\[
\Theta(y;\eta)
=D_\eta\cap B_{\rm MES}(y;\eta)
\cap\mathcal R_\eta^{-1}(C_y(\eta)).
\]

Here \(D_\eta\) is the declared physical domain, \(B_{\rm MES}\) contains
the available matched sector restrictions, \(\mathcal R_\eta\) is a
separately declared response and \(C_y\) is an observational compatibility
region. The set intersection is meaningful only with those objects and their
conditioning specified. It does not construct a response where none exists.

If the same data construct the MES ceilings and the response compatibility
region, these are two restrictions within one feasible system, not two
independent observations. A likelihood or evidence factorisation requires an
additional joint-law argument. The general distinction between a model's
identified set, its estimation and confidence procedures is discussed in the
partial-identification literature; the present tensor and anchor contracts
remain direct project-specific constructions. [@MOLINARI_2020;
@KAIDO_MOLINARI_STOYE_2022]

### 6.2 Exact affine fibres

For an exact linear response, an exact observed vector \(y\), and a feasible
\(X_0\), write \(F_y=D_\eta\cap B_{\rm MES}(y;\eta)\). Then

\[
\Theta(y;\eta)=F_y\cap(X_0+\ker\mathcal R_\eta).
\]

It is a singleton precisely when

\[
\{h\in\ker\mathcal R_\eta:X_0+h\in F_y\}=\{0\}.
\]

Full column rank is sufficient but need not be necessary: predeclared
inequalities may exclude every nonzero kernel displacement. The example
\(\mathcal R=(1\ \ 1)\), \(y=0\) and \(x_1,x_2\ge0\) has the unique
feasible solution \((0,0)\), although the response has rank one.

An empty feasible set reports inconsistency with the maintained constraints,
not a detection. A bounded non-singleton set retains partial ambiguity.
Unbounded or disconnected sets must retain their corresponding geometry.
Failure to establish a response or to solve its constraints is not evidence
for a physical null.

### 6.3 Sampling uncertainty and the transition to finite-null tests

For noisy finite data, \(\Theta(y;\eta)\) above is first a realised
compatibility construction. Its cardinality alone does not establish
population point identification or a confidence level. A coverage statement
requires a specified sampling law and a justified construction of both the
compatibility region and any data-derived anchors. The exact affine-fibre
criterion is retained in its exact-response domain; it is not extended to a
statistical consistency theorem by terminology alone.

The same dependence must be retained in a finite-null rank. The complete
analysis map includes MES ceiling construction and conditioning, chart
availability, nuisance treatment, adaptive selection, missingness, tie handling
and the final score. Jointly exchangeable observation/reference rows and a
null-invariant transformation-group orbit remain different comparison
constructions. Their validity conditions are not combined into a single
exchangeability-or-group assumption.

## Transition to the response and numerical sections

The local \(\beta_{\rm RO}\) response provides the presently closed
connection to one frame-velocity sector. It does not supply physical CMB
response operators for shear, vorticity, acceleration, global matter-frame
tilt or the optional geometry blocks. The subsequent processed-response
quotient and numerical-error analysis therefore determine which proposed
attributions survive nuisance and numerical uncertainty; they do not fill
missing physical responses by scalar normalisation.

The resulting methodology keeps three questions separate: which physical
components are represented, which are restricted by matched MES premises,
and which are identifiable through an available response. This retains the
kinematical content of the original MES programme while preserving observable
Q/O morphology. No corrected Planck result, physical kinematical point estimate,
finite-HEALPix containment theorem or native BASS result is introduced here.

## Draft-to-claim mapping and editorial receipt

The proposed Sections 4–6 address candidate additions
`RA-KIN-001/002/003`, `RA-GEO-001`, `RA-KFUNC-001`,
`RA-MESA-001/002/003` and `RA-ID-001/002`, and the intended revisions of
`RA-MES-002`, `RA-MES-003`, `RA-STAT-002` and `RA-RESP-001`.
This is a mapping for review, not a claim-admission decision.

Academic Writing Toolkit reviewed the seven-paragraph prose synopsis of this
argument for paragraph logic and conservative British English, returning zero
issues in both checks. It did not verify the equations, source identities,
statistical coverage or scientific correctness. The mathematical content
remains source-derived/directly reasoned; no fresh CAS or repository execution
receipt was obtained in this drafting pass.
