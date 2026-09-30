# Independent analytical GR decision

Date: 2026-09-30. Reviewer: separately executed agent `/root/gr_independent_decision`; not an author of the candidate manuscripts. The reviewer received the actual manuscripts, claim ledgers, and auxiliary algebra outputs, then independently reproduced the substantive algebra and local-existence arguments. This is independent proof review, not a formal proof-assistant certificate, independent numerical experiment, exhaustive novelty search, or journal recommendation.

**Decision: PROMOTE_ANALYTIC_CONDITIONAL for the bounded analytical statements listed below.** No fatal mathematical error was found in the supplied candidate statements. “Conditional” preserves their declared source field, data, regularity, local-domain, spectral-gap, and segment-bound assumptions; it does not mean that a statistical study or a large numerical run is needed to complete these proofs. Priority and publication-level novelty remain unestablished.

## 1. Inputs and independence boundary

Actually read: `gr/OPTICAL_THEOREMS.md`, `gr/OPTICAL_CLAIMS.json`, `gr/ENERGYFRAME_THEOREMS.md`, `gr/ENERGYFRAME_CLAIMS.json`, `gr/FINITE_DISTANCE_THEOREM.md`, `REFERENCES_AND_CORRECTIONS.md`, `RESEARCH_CONTRACT.json`, `SOURCE_MANIFEST.json`, and the three auxiliary evidence pairs `optical_checks.*`, `tov_curvature_check.*`, and `maartens_eq37_check.*`. SHA-256 digests of the reviewed inputs are recorded in the companion JSON. The harness phase-05 and phase-06 instructions were read.

The supplied Ellis text was checked for its energy-frame and conservation definitions, velocity-gradient index order, and optical-distance identities. Maartens et al., [arXiv:2312.09875v3](https://arxiv.org/html/2312.09875v3), especially Eqs. (3)–(5), (15)–(29), (32)–(37), was opened directly. The supplementary literature search in `REFERENCES_AND_CORRECTIONS.md` is acknowledged as that audit's work; this reviewer does not claim independently to have read every additional paper there.

The root supplied symbolic residual outputs. Those outputs were treated only as supporting checks. The decisions below follow from the displayed analytic arguments, including independent hand reconstruction of the EF3 cubic perturbations and EF5 existence/curvature calculation. No statistical likelihood, simulation coverage, catalogue fit, or scientific-runtime gate enters this decision.

## 2. First findings and corrections retained

| Finding | Initial assessment | Final disposition |
|---|---|---|
| FD segment assumptions | The Jacobi majorant and Taylor argument are valid; neither segment bound follows from curvature at one event. | Retain all segmentwise assumptions. GR-FD is promoted only under them. |
| Arbitrary congruence versus material realization | A normalized test-source first jet in a fixed metric does not establish an Einstein–matter solution. | OPT04 keeps the kinematic scope; EF2–EF3 keep unrestricted Einstein-defined stress; EF5 supplies the stronger fixed-matter construction for acceleration. |
| Maartens v3 Eq. (37) used with unrestricted shear | Direct substitution into Eq. (34b) leaves a term linear in velocity, proportional to shear squared. | The formula-specific unrestricted-shear reading is rejected. OPT09's full matrix inverse is accepted. The exact boost law is not rejected. |
| Vorticity convention | Ellis uses the opposite index order to the derivative-first physical tensor in this packet. | Accept the adapter `W_ab = -c omega_book_ab`; a signed drift formula cannot be copied without it. No drift-reconstruction theorem is promoted here. |
| Restoring units | With `B = ∇_(a U_b)` and `U=c u`, acceleration is `A=2c B.u`. | Accepted. The coefficient would be `2c²` for a symmetric derivative of unit `u` instead. |
| EF5a sound-speed typography | One prose bullet initially displayed `c_s=√α,c`. | Root corrected it to `c_s=c√α` before the final provenance snapshot. The substantive equation was already `c_s²=α c²`. No proof or classification changes. |

For the Eq. (37) issue, let `D=H I+Σ` and `d=-2D v+O(|v|²)`. Its displayed truncated inverse returns `(I-Σ²/H²)v+O(|v|²)`. Taking `Σ/H=diag(1/2,-1/4,-1/4)` and `v=(ε,0,0)` returns `(3ε/4,0,0)` at leading order. This is an independent algebraic correction to the named version's arbitrary-shear interpretation, not an author-acknowledged erratum or a claim that the whole paper is invalid. A separate weak-shear expansion can justify a correspondingly weaker formula.

## 3. Exact optical statements accepted

All nine OPT claims receive **PROMOTE_ANALYTIC_CONDITIONAL**.

| Claim | Exact accepted statement and boundary |
|---|---|
| OPT01 | For the declared smooth source field, absolute endpoint redshift, observer-normalized past affine tangent, and vertex area distance, `Z=u.K`, `H=c dz/dd_A|0=B(K,K)`, and `d_A=ell+O(ell³)`. This is a distance derivative, not observer-time drift. |
| OPT02 | The exact joint kinematic image is the product of future unit mass-shell monopole/dipole intercepts and arbitrary real degree-at-most-two slopes. The unique value and symmetric derivative are `u=(ζ0,ζ)` and `B=S+S(u,u)g` with the displayed coefficient representative. |
| OPT03 | All compatible first derivatives are exactly `Q=B+b⊗u-u⊗b+W`, where `b=B.u`, `W` is antisymmetric and annihilates `u`. Thus `A=2c b`, expansion and shear are fixed, and precisely three spatial vorticity components remain free. |
| OPT04 | Every allowed pair and fibre element is realized locally by a normalized smooth field in any fixed smooth Lorentzian metric. The neighbourhood may shrink; no material field equations are implied. |
| OPT05 | For two admissible pairs with rapidities at most `R`, `M=√cosh(2R)`, and `L=min(||S||op,||S_tilde||op)`, the stated finite bound `||ΔB||F ≤ (1+2M²)ε_H+4ML ε_Z` holds. The rate-amplitude factor and common observer norm are essential. |
| OPT06 | The dipole clipping/re-normalization map has error at most `√(1+tanh²R) η_d`, with the separately stated monopole compatibility bound. It is a conditional reconstruction map, not a test that raw data satisfy the image conditions. |
| OPT07 | Under `A(p)=0`, a slope is admissible iff `S^a_b` has a timelike eigenvector. Its timelike eigenvalue and `B` are unique; compatible future unit velocities form `H^r` when exactly `r` source spatial expansion eigenvalues vanish. |
| OPT08 | The displayed epsilon family disproves a uniform slope-only velocity modulus over a class approaching a zero expansion eigenvalue, even with bounded rapidity and rates. Its intercepts differ, so it does not contradict the joint inverse. |
| OPT09 | For fixed invertible `D` and small observer/source relative velocity, `β=-(1/2)D^(-1)h1+O(|β|²)` is the valid first-order inverse without a weak-shear expansion. Constants depend on the inverse of `D`. |

Independent proof checks:

1. In an observer tetrad, `K=(-1,n)`. A symmetric tensor vanishing on every such null vector has vanishing time-space entries and spatial block proportional to the identity, with the opposite time-time coefficient. The null-sky kernel is exactly `span(g)`, not a larger ambiguity.
2. Unit normalization imposes `Q_ab u^b=0` and hence `B(u,u)=0`. Since `g(u,u)=-1`, it fixes the sole metric ambiguity to `S(u,u)`. The formula for `Q` then has the required symmetric part and second-index contraction; its first-index contraction is `2b`, fixing the acceleration sign and factor of `c`.
3. In normal coordinates, the seed field with derivative `Q/c` has normalization denominator derivative zero at the event. Renormalization therefore preserves the prescribed first jet. This proves sufficiency rather than merely counting parameters.
4. The finite-error proof uses `|u|E≤M`, `||g||F=2`, and a finite bilinear difference. Interchanging the two pairs legitimately gives the minimum of the two representative norms. No hidden eigenvalue gap enters.
5. A Lorentz-self-adjoint operator with a timelike eigenvector splits into that timelike line and a positive-definite invariant complement. Two distinct timelike eigenvalues are impossible because their eigenvectors would be orthogonal. This establishes the complete geodesic fibre and shows why repeated nonzero spatial eigenvalues cause no velocity ambiguity.

The exact data contract remains idealized. Unknown absolute redshift calibration, finite angular sampling, finite source distances, or missing distance calibration require a separate inference argument. Neither an orbit normal nor matter tilt relative to such a normal is recovered by these theorems.

## 4. Energy-frame statements accepted

All eight EF ledger entries receive **PROMOTE_ANALYTIC_CONDITIONAL**, with their different matter classes retained.

| Claim | Exact accepted statement and boundary |
|---|---|
| EF1 | For a selected smooth unit timelike stress eigenfield and nonzero enthalpy eigenvalue gaps, `∇_Eμ U=-c L^(-1)Dμ`, the exact common squared-rate identity holds, and the `c²/δ²` bound is optimal. Every perfect-fluid stress with nonzero enthalpy saturates this gap estimate. |
| EF2 | The displayed conformal family has the same metric 2-jet, fixed point stress/gap, arbitrary acceleration in one direction, and strict DEC plus a unique energy frame on a member-dependent neighbourhood. The explicit degeneracy at distance `3b/|λ|` rules out a common advertised coordinate ball. No fixed EOS is supplied. |
| EF3 | The explicit cubic metric perturbation realizes every real `4×3` energy-frame derivative matrix at one fixed strict-DEC metric 2-jet, fixed stress, and fixed energy frame. This is an unrestricted Einstein-defined-source theorem, not a fixed-EOS theorem. |
| EF4 | Conserved perfect fluids satisfy `A=-c² Dp/(ε+p)`, and barotropes satisfy `A=-c_s² Dε/(ε+p)`. A density-gradient bound and positive enthalpy lower bound yield the stated acceleration bound. Positive-density dust is geodesic. |
| EF5a | For the stated fixed constants and causal EOS `p=αε`, the local static spherical germs exist, have identical full comoving-frame Riemann tensors and matched normal-coordinate metric 2-jets at the selected events, and have fixed stress/gap but unbounded acceleration as `F0→0+`. |
| EF5b | The stated `Λ=0`, `μ=κε0/6` choice has zero Weyl tensor at the selected event, identical isotropic curvature there, and unbounded acceleration in any chosen spatial direction. It does not assert conformal flatness on a neighbourhood. |
| EF5c | The entire EF5 family solves one fixed timelike-gradient scalar theory `P(X)=P_* X^s`, with the same `s`, `P_*`, and coordinate slope `q`; its scalar equation and stress match exactly, and `c_s²=α c²`. |
| EF6 | With fixed gravitational constants and a nondegenerate selected future energy eigenline, a metric 3-jet determines its first covariant derivative. A metric 2-jet does not uniformly bound acceleration even in the explicit fixed causal EOS/scalar classes; all twelve directions are attainable only in the unrestricted source class established here. |

### EF3: explicit surjectivity, not dimension counting

At the event the cubic perturbation and its first two derivatives vanish. Therefore its contribution to the first derivative of the exact nonlinear Einstein tensor is precisely the flat linear principal expression in Eq. (7); curvature or connection cross terms do not survive at this jet order.

For `H_ij=δij x0 f`, `f=-S_kl xk xl/2`, the relevant Einstein component is `-∂i f=S_ij xj`. For `H_0i=-x0 r² q_i/2`, the combination `(∂i div H0-ΔH0i)/2` equals `x0 q_i`. For `H_0i=-r² W_ij xj/5`, antisymmetry gives zero divergence and `Δ(r² W x)=10 W x`, yielding `W_ij xj`. Their sum gives all twelve desired mixed stress derivatives. The energy-frame derivative formula then returns the prescribed matrix. Exact Bianchi conservation holds because these are actual smooth metrics, not freely assigned stress jets.

### EF5: why the physical existence claim is sufficient

At each member's chosen radius, `r0>0`, `F0>0`, and `ε0>0`. The displayed first-order ODE vector field is smooth on that open domain, so standard local ODE existence provides a smooth solution interval preserving those inequalities. The density and radial Einstein equations are solved directly. The radial Bianchi identity plus the prescribed Euler equation forces the two angular pressures to equal the radial pressure; no Einstein component is left unsatisfied.

The independent curvature formulas are

`R0101=F(ν''+ν'^2)+F'ν'/2`, `R0202=Fν'/r`, `R1212=-F'/(2r)`, and `R2323=(1-F)/r²`.

Substitution gives exactly Eq. (17). Each depends only on `ε0,p0,μ,Λ`, not on the varying selected radius. The vanishing mixed components follow from the static spherical connection. Thus the proof matches the full curvature tensor, not just scalar invariants. Identifying oriented comoving tetrads then gives identical centered normal-coordinate metric 2-jets.

Meanwhile `A=c²√F ν' E1`, so `|A|=c²|B|r0/√(1-Cr0²)` diverges along the stated sequence. The source spatial derivative matrix vanishes, hence expansion, shear, and vorticity vanish. The positive fixed enthalpy gap does not deteriorate; its derivative input grows. Strict DEC follows from `ε>|p|=αε`. The scalar extension independently satisfies its field equation because its current has only a time component and all coefficients are time independent. Its characteristic coefficients `P_X` and `P_X+2X P_XX` are positive, with ratio `α`.

Dimensions are consistent: `κ ε`, `μ`, `Λ`, `B`, and `C` have inverse-length-squared units; `m` and `r` have length units; `c² B r` has acceleration units. The dimension of `P_*` is chosen to make `P(X)` an energy density for the selected scalar-field units. This does not vary the action across family members.

The limiting `F0=0` point is excluded. These are local germs, with no regular center, complete star, boundary matching, common domain, global stability, or microscopic ultraviolet-validity statement. They nevertheless establish the advertised local derivative-order obstruction in a fixed classical matter theory. The dust limit is singular and cannot be used to produce accelerating dust.

## 5. Finite-distance certificate accepted

**GR-FD: PROMOTE_ANALYTIC_CONDITIONAL.** Assume the stated observer-normalized affine ray, vertex Jacobi data, `||Ropt||op≤Kc` and `|Z''|≤M2` throughout `0≤s≤L`, with `eta(L)<1`. Then the displayed matrix bound, positive area-distance bounds, and FD1–FD3 all hold, including the tighter distance-only envelope evaluated at `min(L,d_A/(1-etaL))`.

The Volterra series is bounded termwise by `Σ Kc^j s^(2j+1)/(2j+1)!`. Subtracting its first term gives `||D-sI||≤f-s`. Singular-value bounds imply invertibility; continuity from the vertex fixes positive determinant, so the product of singular values gives the stated area-distance interval. Taylor's integral remainder then gives FD1. The lower distance bound gives FD2 and division gives FD3. The right-hand side of FD1 is nondecreasing in `s`, justifying its distance-only envelope.

`Kc` and `M2` both have inverse-length-squared units. The optical-distance error term is locally cubic, whereas using one uniform `etaL` deliberately weakens that order. The certificate is sufficient, not a sharp caustic test. Failure of `eta(L)<1` is inconclusive. A value of curvature at one event, a small sky multipole, or Einstein's equations alone does not supply either full-segment bound. A boosted non-unit redshift intercept must be retained.

## 6. Stronger readings not promoted

| Stronger reading | Decision | Reason |
|---|---|---|
| The proved packet establishes original priority or sufficient JCAP novelty. | HOLD | The standard antecedents overlap substantially; no exhaustive theorem-level novelty exclusion has been completed. |
| All twelve first-jet directions are realized within one fixed Einstein–Euler or `P(X)` matter model. | HOLD | EF3 proves this only for unrestricted Einstein-defined stress; EF5 proves a fixed-matter acceleration subfamily. |
| The local TOV family is a sequence of complete regular stars or has one common admissible neighbourhood. | HOLD | No global extension or common-domain theorem is supplied. |
| Positive-density conserved Einstein dust can realize the accelerating family. | REJECT | Its Euler equation forces zero acceleration. |
| Scalar slope data alone uniquely identify an unrestricted accelerated source velocity, or remain uniformly stable near a lost geodesic expansion gap. | REJECT | The explicit fibres and epsilon family disprove these statements. |
| Local curvature or low multipole values alone certify the finite-distance remainder. | REJECT | The certificate requires independent segmentwise curvature and source-derivative bounds. |
| The optical inverse identifies a homogeneous-orbit normal or Bianchi tilt from these data alone. | REJECT | Such a normal is absent from the local information contract. |

## 7. Novelty and closeout

The strongest physical result in the reviewed packet is EF5's fixed-matter, matched-full-curvature, unbounded-acceleration construction. The strongest optical result is the complete accelerated joint image/fibre with the explicit finite-error inverse. EF3 is a complete constructive result within its broader source class. GR-FD is a useful explicit sufficient certificate assembled from standard Jacobi and Taylor arguments.

These are mathematical assessments of the exact statements, not priority findings. EF1, EF4, the optical endpoint identities, the kinematic decomposition, TOV equations, and the scalar-fluid mapping have standard antecedents. The algebraic kernel, fibre, and norm bounds are elementary enough that a lack of a located identical formulation would not by itself establish a substantial new physical contribution. The appropriate novelty status is **UNESTABLISHED / NO PRIORITY CLAIM**.

The bounded analytical loop is complete at this review gate. No additional scientific computation is required for the promoted statements. Observational estimators, finite-sample performance, nuisance calibration, global matter extensions, and publication novelty are separate unresolved tasks.
