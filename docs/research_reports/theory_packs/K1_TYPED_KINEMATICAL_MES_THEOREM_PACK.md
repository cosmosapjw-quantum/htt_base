# K1 — Typed kinematical MES theorem pack

## Status and scope

This pack restores the physical-state inheritance lane of the original
vector/tensor programme while preserving the corrected low-multipole
observable tensorisation. It is a theory and authority result. It contains no
Planck/FFP10 execution, no physical shear or vorticity estimate, no global-tilt
attribution, no finite-HEALPix no-go theorem and no native BASS result.

The load-bearing source authority is Git-diverged:

```text
Report-A head at K0 closeout:
07a9b447331564dde297b118607cc94b8843bfb4

Merged physical-state donor PR #367 head:
6bafca66285ef071081453313bb7d2d6b261599c
```

The donor source is bound by Git blob identity in the K0 crosswalk. The report
branch imports its semantics, not its production code or execution status.

## 1. Definition of the four layers

Let the observable low-multipole state be

\[
\mathcal O_{\rm low}
=(Q_{ab},O_{abc},\ldots),
\]

where \(Q_{ab}\in\mathrm{STF}_2\) and
\(O_{abc}\in\mathrm{STF}_3\) use the corrected stored-real harmonic
normalisation.

Let the typed physical state be

\[
\mathcal X_{\rm phys}
=\mathcal K_{\rm cong}\times\mathcal V_{\rm frame}\times\mathcal G,
\]

with

\[
\mathcal K_{\rm cong}=(\sigma_{ab},\omega_a,A_a),
\]

\[
\mathcal V_{\rm frame}
=(\beta_{RO}^{a},\beta_{RM}^{a},\beta_{MO}^{a}),
\]

and \(\mathcal G\) the registered scalar and optional tensor geometry
components. Congruence kinematics and frame-relative velocities are different
physical objects. Missing components are typed and are not replaced by zero.

Let \(\mathfrak A_{\rm MES}\) denote the family of registered MES anchors.
Each anchor is attached to exactly one target sector and invariant and carries
its frame, congruence, normalisation, perturbative order, branch, attribution,
conditioning and validity domain.

Finally, for an observational compatibility region \(C_y\subseteq\mathcal Y\)
and a separately declared response \(\mathcal R_D:D\subseteq\mathcal X_{\rm
phys}\rightarrow\mathcal Y\), define the physical identified set

\[
\Theta(y;D,\mathfrak A_{\rm MES})
=
\left\{
X\in D:
X\text{ satisfies every available matched anchor and }
\mathcal R_D(X)\in C_y
\right\}.
\]

The objects \(\mathcal O_{\rm low}\), \(\mathcal X_{\rm phys}\),
\(\mathfrak A_{\rm MES}\) and \(\Theta\) are not interchangeable.

## Proposition K1-T1 — typed state partition

The physical state separates congruence kinematics, frame-relative velocities
and geometry. The decomposition is semantic, not merely architectural:
\(\sigma_{ab}\), \(\omega_a\) and \(A_a\) are kinematics of a declared
congruence, whereas \(\beta_{RO}\), \(\beta_{RM}\) and \(\beta_{MO}\) are
relations between radiation, matter and observer frames.

The first-order closure

\[
\beta_{RO}^{a}=\beta_{RM}^{a}+\beta_{MO}^{a}+O(\beta^2)
\]

is a frame-relation diagnostic. It does not convert one velocity into a global
tilt detection, nor does it reinterpret an untyped legacy velocity component.

**Evidence:** source-defined exact typing and validation contracts.

**Claim ceiling:** diagnostic/pre-solver state transport only.

## Proposition K1-T2 — state–anchor separation

A MES anchor is a conditional bound object on one physical invariant. It is not
an element of \(\mathcal X_{\rm phys}\), an observation, a likelihood, a
posterior or an estimator of a tensor direction.

The active verified channels are

\[
\texttt{MES\_G\_SIGMA}
:\quad
\texttt{sigma\_ab\_sigma\_ab\_over\_6H2},
\]

and

\[
\texttt{MES\_G\_OMEGA}
:\quad
\texttt{omega\_ab\_omega\_ab\_over\_6H2}.
\]

The registered source names are retained because conversion between a
vorticity vector and antisymmetric vorticity tensor is convention dependent.
No numerical factor is imported without the matching registered
normalisation.

Acceleration is present in the general typed state but has
`NO_MES_ANCHOR` on the registered geodesic lane. The anisotropic-curvature
coordinate likewise has no active MES curvature ceiling. This inventory is
asymmetric and must not be completed by analogy.

**Evidence:** exact active-anchor registry and typed absence contracts.

## Theorem K1-T3 — radial-only information

Let \(V\) be a finite-dimensional orthogonal representation of \(O(3)\), and
let

\[
B_R=\{x\in V:\|x\|\le R\},\qquad R>0.
\]

Then \(B_R\) is \(O(3)\)-invariant. For every \(g\in O(3)\),

\[
\|gx\|^2=\langle gx,gx\rangle
=\langle x,g^Tgx\rangle
=\|x\|^2,
\]

so

\[
x\in B_R\quad\Longleftrightarrow\quad gx\in B_R.
\]

Therefore an invariant sector bound restricts orbit radius but supplies no
orientation, eigenframe, handedness or non-radial morphology coordinate. If a
non-zero physical state has a non-trivial orbit, every state on that orbit has
the same anchor status.

This theorem is compatible with the scalar-to-vector/STF equivariance
obstruction. It does not imply that physical morphology is absent; it implies
that morphology must enter through separately typed functionals, a response
model or additional directional data.

**Evidence:** direct exact proof. Fresh Wolfram replay was attempted but blocked
by upstream HTTP 502 and is not counted as a verification pass.

## Theorem K1-T4 — product-body gauge and anti-cancellation

Suppose every sector in an available index set \(J\) has a Euclidean anchor
ball

\[
B_j=\{x_j:\|x_j\|\le R_j\},\qquad R_j>0,
\]

and define

\[
\mathcal B=\prod_{j\in J}B_j.
\]

The Minkowski gauge of \(\mathcal B\) is

\[
\boxed{
\rho_{\mathcal B}(x)
=
\max_{j\in J}\frac{\|x_j\|}{R_j}
}.
\]

**Proof.** By definition, \(x\in t\mathcal B\) if and only if
\(\|x_j\|\le tR_j\) for every \(j\). Thus the admissible values of \(t\) are
exactly those satisfying

\[
t\ge\frac{\|x_j\|}{R_j}\quad\text{for every }j,
\]

and their infimum is the displayed maximum. \(\square\)

The combined stress is therefore controlled by the worst sector and cannot
hide a shear excess behind a signed vorticity contribution or vice versa.
This theorem applies only to available matched blocks. A missing or withheld
anchor does not acquire a zero, infinite or guessed radius; the global gauge
remains typed as unavailable or conditional.

## Proposition K1-T5 — channel-matched stress

Let \(N_j\) be a non-negative identified numerator range for sector \(j\), and
let \(A_j>0\) be a verified anchor. A numerical saturation range

\[
S_j=N_j/A_j
\]

is admitted only if numerator and anchor have the same channel key:

\[
(\text{sector},\text{invariant},\text{frame},\text{congruence},
\text{normalisation},\text{order},\text{branch}).
\]

Otherwise the result is one of the typed states

```text
NUMERATOR_UNIDENTIFIED
ANCHOR_UNAVAILABLE
CHANNEL_MISMATCH
RATIO_UNIDENTIFIED
```

rather than a fabricated number. For a defined ensemble-calibrated stress,

\[
E_j=\max(S_j-1,0).
\]

A value \(S_j\le1\) is consistency with the registered one-way premise; it is
not evidence for an FLRW converse, distance, occupancy or family identity.

**Evidence:** source-defined factory and failure-state contracts.

## Proposition K1-T6 — typed no-anchor sectors

On the active geodesic MES lane:

- shear has a verified `MES_G_SIGMA` anchor;
- vorticity has a verified `MES_G_OMEGA` anchor;
- acceleration has `NO_MES_ANCHOR`, because the geodesic premise removes the
  need for a numerical acceleration ceiling rather than supplying one;
- anisotropic curvature has `NO_MES_ANCHOR`, because no registered MES
  curvature ceiling exists.

A typed no-anchor outcome is informative metadata. It is neither a zero bound
nor evidence that the physical component vanishes outside the declared
premise.

## Theorem K1-T7 — response-constrained identified set

Let \(D\subseteq\mathcal X_{\rm phys}\) be a predeclared physical domain,
\(C_y\subseteq\mathcal Y\) an observational compatibility region and
\(\mathcal R_D\) a declared response. Let \(A(X)\) mean that every available
matched anchor constraint is satisfied. Then

\[
\Theta(y)=\{X\in D:A(X),\ \mathcal R_D(X)\in C_y\}
\]

is the identified set under the declared model.

The parameter is point identified only if \(\Theta(y)\) is a singleton. A
non-singleton bounded set is partial identification, a set with recession
directions is unbounded identification, the empty set is model infeasibility,
and solver or authority failure is undetermined. None of these states may be
silently reported as a central estimate.

If a response is absent for a physical sector, MES anchor information alone
restricts at most the registered radial invariant. It cannot identify the
sector's orientation or collapse the full tensor state to a point. If the
response is rank deficient, the identified set must retain the corresponding
null or recession directions unless additional predeclared restrictions close
them.

**Evidence:** direct set-theoretic derivation plus repository identified-set
semantics. Sharpness for the final cosmological response is not claimed.

## Proposition K1-T8 — current response boundary

Within Report A, WU-010 supplies the closed scoped local observer-radiation
velocity response for \(\beta_{RO}\). It does not identify
\(\beta_{RM}\), \(\beta_{MO}\) or a global matter-frame tilt.

No current Report-A theorem closes the full physical CMB responses for
\(\sigma_{ab}\), \(\omega_a\), \(A_a\), \(\beta_{RM}\), \(\beta_{MO}\) or
the optional geometry tensors. Those sectors may be described and bounded
where an anchor exists, but point attribution remains withheld.

## Proposition K1-T9 — physical morphology remains separately typed

The physical tensor state admits functionals with different codomains and
parity classes, including

\[
\sigma_{ab},\quad \omega_a,\quad A_a,
\]

\[
\operatorname{tr}\sigma^2,
\qquad
\operatorname{tr}\sigma^3,
\qquad
\omega^2,
\]

\[
\beta_{RM}\!\cdot\!\omega,
\qquad
\beta_{RM}^{a}\sigma_{ab}\beta_{RM}^{b}.
\]

These functionals carry component, shape, parity or relative-orientation
information. They are not generated by the radial MES anchors, and their
existence does not imply that they are observationally identified. Missing
input components remain typed failures rather than zeros.

## Proposition K1-T10 — scalar inheritance is not scalar-method revival

Two uses of a scalar must be kept distinct.

1. The retired scalar-only observational lane used a scalar collection as the
   primary morphology representation or current anomaly rank.
2. The retained MES lane uses scalar quantities only as one-way, typed radial
   constraints on named sectors of a distinct physical tensor state.

The second is a legitimate inheritance of the original MES inequalities and
does not reverse the corrected Q/O tensorisation. The observable state remains
fully tensorial, while the physical state remains component-native and the
response/identified-set layer controls attribution.

## Integrated report consequence

The Report-A scientific spine must become

```text
observable Q/O tensor state
→ typed physical kinematical/frame/geometry state
→ sector-wise MES anchor bodies
→ physical tensor functionals and morphology
→ response-constrained identified sets and abstention
→ finite-null validity
→ local observer beta_RO response
→ processed-response quotient
→ continuum/finite numerical boundary
→ conditional robust-rank certification
```

No arrow from an anchor body to a tensor state is generative. No arrow from an
observable tensor to a physical tensor is admitted without a declared response.

## Evidence summary

| Result | Evidence grade | Remaining obligation |
|---|---|---|
| typed state partition | source-verified | none at definition level |
| active anchor inventory | source-verified | preserve exact normalisations |
| radial-only theorem | derived exact | optional independent CAS replay |
| product-body gauge | derived exact | applies only to available blocks |
| channel-matched stress | source-verified | no execution on Report-A head |
| typed no-anchor sectors | source-verified | do not infer outside premise |
| identified-set theorem | derived/source-supported | response-specific sharpness open |
| beta_RO boundary | literature/source/implementation supported | no local/global promotion |
| physical functional catalogue | source-verified | observational identification open |
| scalar inheritance distinction | derived policy result | K2 ledger integration |

## Terminal

```text
PASS_K1_TYPED_KINEMATICAL_MES_THEOREM_PACK_SOURCE
/
PHYSICAL_RESPONSE_SECTORS_EXCEPT_BETA_RO_UNRESOLVED
/
WOLFRAM_REPLAY_BLOCKED_BY_HTTP_502
/
NO_OBSERVATIONAL_OR_POINT_ATTRIBUTION_CLAIM
```
