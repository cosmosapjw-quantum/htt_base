# T6 — Processed local-observer response, nuisance quotient, and finite-operator boundary

Date: 2026-09-03  
Evidence grades: `DERIVED`, `SOURCE_IMPLEMENTED`, and selected
`IMPLEMENTATION_VERIFIED` frozen results  
Observational data used: none  
Native BASS solver used: no

## 1. Scope

This pack synthesizes WU-011 as an observation-independent processed-response
problem. It combines:

- the accepted WU-010 local-observer thermodynamic-temperature pullback;
- finite source transfer and HEALPix synthesis;
- the existing weighted joint `ell=0..5` estimator;
- retained `ell=2..5` response geometry;
- unrestricted deterministic high-source nuisance images;
- numerical-rank and error-model boundaries.

It does not fit an empirical velocity, subtract a boost, identify global matter
frame tilt, use a current Planck temperature product, or identify a Bianchi
family.

Fixed conventions are

\[
g_{ab}=(-,+,+,+),\qquad n^a=-e^a,
\]

\[
\widetilde u^a=\gamma(u^a+\beta_{\rm obs}^a),
\qquad \beta_{\rm obs}=v_{\rm obs}/c,
\qquad d=1.
\]

## 2. Two real harmonic coordinates and their adapter

Report A distinguishes two equivalent but non-identical real coordinates.

The orthonormal stored-real carrier is

\[
c_{\ell0}=a_{\ell0},\qquad
c_{\ell m,c}=\sqrt2\,\Re a_{\ell m},\qquad
c_{\ell m,s}=-\sqrt2\,\Im a_{\ell m}.
\]

It has Euclidean metric.

The public WU-011 source coordinate, called `scientific stored-real` in the
source code, is renamed here

\[
r_{\ell0}=a_{\ell0},\qquad
r_{\ell m,R}=\Re a_{\ell m},\qquad
r_{\ell m,I}=\Im a_{\ell m}.
\]

Its Parseval metric is

\[
G_\ell=\operatorname{diag}(1,2,2,\ldots,2).
\]

The explicit adapter is

\[
\boxed{c_\ell=D_\ell r_\ell},
\]

where each `m>0` pair is multiplied by `(sqrt(2),-sqrt(2))`. Hence

\[
D_\ell^TD_\ell=G_\ell.
\]

All invariant rank and singular-value claims must either transform to
`c_l` or retain `G_l` explicitly. The coordinates are semantically equivalent,
but they are not byte-identical.

## 3. Exact processing order

The source code freezes the following composition:

```text
strictly positive absolute thermodynamic-temperature sky
→ exact finite or first-order local-observer boost
→ source beam and pixel-window transfer
→ HEALPix synthesis
→ fixed weighted joint ell=0..5 solve
→ post-fit target/source commonization
→ retained ell=2..5 carrier
```

Transfer-before-boost is a named hostile mutation rather than an alternative
interpretation. Post-fit commonization may smooth but may not sharpen the
fitted sky.

The finite operator is content-bound to:

- the mask and joint-estimator identity;
- `nside` and processing cutoff;
- source and target beam/pixel transfers;
- source, fit, and retained harmonic registries;
- processing order and coefficient adapters.

## 4. Source and output spaces

The low-source coordinate is

\[
s_{\rm low}
 =(T_0,r_1,\ldots,r_6)\in\mathbb R^{49},
\]

where `T0` is physical monopole temperature and

\[
a_{00}=\sqrt{4\pi}\,T_0.
\]

The anisotropy part has dimension

\[
\sum_{\ell=1}^{6}(2\ell+1)=48.
\]

The retained output is

\[
y_{\rm ret}=(r_2,r_3,r_4,r_5)\in\mathbb R^{32}.
\]

The three-axis first-order coefficient Jacobian is

\[
J_{i\alpha A}
 =\left.
 \frac{\partial^2 y_{\alpha}}
 {\partial\beta_{{\rm obs},i}\,\partial s_A}
 \right|_{\beta_{\rm obs}=0},
\qquad
J\in\mathbb R^{3\times32\times49}.
\]

All entries are dimensionless because source and output coefficients use the
same temperature unit and `beta_obs` is dimensionless.

## 5. Structural monopole null and replay leakage

For a constant physical monopole,

\[
\delta_\beta T_0=T_0\,\beta_{\rm obs}\cdot n,
\]

which is a pure dipole. The simultaneous fitted nuisance band contains
`ell=0,1`, while the public retained output starts at `ell=2`. Therefore

\[
\boxed{J_{i\alpha,T_0}^{\rm scientific}=0.}
\]

Finite HEALPix transform leakage is stored separately as a replay diagnostic;
it is not promoted into a physical monopole response.

The source and output metric diagonals are

\[
G_S=\operatorname{diag}(4\pi,G_1,\ldots,G_6),
\qquad
G_R=\operatorname{diag}(G_2,G_3,G_4,G_5).
\]

For the stacked Jacobian,

\[
\boxed{
\widetilde J
 =(I_3\otimes G_R^{1/2})J_{\rm stack}G_S^{-1/2}.
}
\]

## 6. Exact full-sky reference

For the registered full-sky `ell=1..6 -> ell=2..5` first-order response, the
source-sector squared singular values are

\[
\boxed{
\left\{
\frac83,\frac{27}{5},13,21,\frac{125}{11},\frac{216}{13}
\right\}
}
\]

with multiplicities

\[
(3,5,7,9,11,13).
\]

Thus

\[
\operatorname{rank}_{\rm alg}\widetilde J_{\rm aniso}=48,
\qquad
\operatorname{nullity}_{T_0}=1,
\]

and the nonzero-subspace condition number is

\[
\boxed{
\kappa_+=\sqrt{63/8}=2.80624304008\ldots
}.
\]

The full 49-column scientific matrix has infinite condition number because the
physical monopole null is structural.

## 7. Low-source and high-source directional responses

For a unit boost direction \(\hat b\), define

\[
J_{\hat b}=\sum_{i=1}^{3}\hat b_iJ_i
\in\mathbb R^{32\times48},
\]

where the exact physical-monopole null has been removed from the source domain.

For unrestricted deterministic source multipoles `ell=7..L`, define

\[
K_{\hat b}^{\rm hi}(L)
 =\bigl[K_{\hat b}^{(7)}|\cdots|K_{\hat b}^{(L)}\bigr]
 \in\mathbb R^{32\times d_H(L)},
\]

\[
\boxed{d_H(L)=(L-6)(L+8).}
\]

The relevant images are

\[
\mathcal L_{\hat b}=\operatorname{Im}J_{\hat b},
\qquad
\mathcal H_{\hat b}(L)=\operatorname{Im}K_{\hat b}^{\rm hi}(L).
\]

## 8. Response quotient theorem

Let \(P_{\mathcal H^\perp}\) be the orthogonal projector onto the complement
of the declared high-source image in the whitened retained space. Define

\[
J_{\rm surv}(L)
 =P_{\mathcal H_{\hat b}(L)^\perp}J_{\hat b}.
\]

Then

\[
\boxed{
\operatorname{rank}_{\rm alg}J_{\rm surv}(L)
 =\operatorname{rank}_{\rm alg}
  [K_{\hat b}^{\rm hi}(L)\ J_{\hat b}]
 -\operatorname{rank}_{\rm alg}K_{\hat b}^{\rm hi}(L).
}
\]

### Proof

The quotient

\[
(\operatorname{Im}K+\operatorname{Im}J)/\operatorname{Im}K
\]

has dimension

\[
\dim(\operatorname{Im}K+\operatorname{Im}J)-\dim\operatorname{Im}K.
\]

Orthogonal projection onto \((\operatorname{Im}K)^\perp\) has kernel
\(\operatorname{Im}K\) when restricted to
\(\operatorname{Im}K+\operatorname{Im}J\), so its image of
\(\operatorname{Im}J\) is isomorphic to that quotient. Replacing image
dimensions by matrix ranks proves the identity. ∎

Consequently,

\[
J_{\rm surv}(L)=0
\iff
\mathcal L_{\hat b}\subseteq\mathcal H_{\hat b}(L).
\]

This is identifiability relative to the declared observable and nuisance class,
not a statement that either source is physically impossible.

## 9. Nested-image theorem and short circuit

Because

\[
K_{\hat b}^{\rm hi}(L+1)
 =[K_{\hat b}^{\rm hi}(L)|K_{\hat b}^{(L+1)}],
\]

one has

\[
\boxed{
\mathcal H_{\hat b}(L)
 \subseteq
\mathcal H_{\hat b}(L+1).
}
\]

If containment is robustly certified at one cutoff \(L_0\), no larger cutoff
can restore a model-free survivor. A sufficient special case is

\[
\operatorname{rank}_{\rm rob}K_{\hat b}^{\rm hi}(L_0)=32.
\]

Tail-amplitude convergence remains relevant for a physical covariance or
amplitude model, but it is not a logical prerequisite for deterministic image
containment once robust full-row rank is certified.

## 10. Dimension obstruction is not a rank proof

The high-source dimensions are

\[
d_H(7,8,9,12,16,20)=(15,32,51,120,240,392).
\]

At `L=9`, a three-axis augmented source has `48+51=99` coordinates for 96
stacked outputs. For one fixed direction, 51 nuisance coordinates map to a
32-dimensional output.

These facts forbid an unrestricted point inverse in general, but column count
alone does not prove that the actual processed nuisance matrix has row rank 32.
A numerical or exact image certificate is still necessary.

## 11. Exact full-sky high-source control

At first order, a scalar boost couples only nearest harmonic neighbours.
Therefore no direct full-sky channel exists from source `ell>=7` to retained
`ell=2..5`.

The matched full-sky high-source matrix is consequently a numerical replay
control, not a physical nuisance signal. Any rank policy that assigns full
physical image rank to an arbitrarily small full-sky replay floor is invalid.

## 12. Frozen numerical evidence ladder

### Task-7B — successful no-candidate characterization

At exact source head `13d40cb4...`, all seven registered cases executed and
verified. No cut-sky case simultaneously met the rank, condition, source-ell6
alias, and `ell=7..9` tail floors.

The best registered wide-apodization case had approximately

```text
response condition: 32.21
ell6 alias / physical neighbour: 2.516
ell7..9 tail / physical neighbour: 5.279
projection of tail into low-source image: 0.961207
```

Its condition passed the registered ceiling, but its alias and tail did not.
The terminal was

```text
PASS_TASK7B_ATLAS_NO_CANDIDATE
```

and is a successful negative engineering result, not a source-identification
result.

### Task-7C — matched-control rank unresolved

The last byte-exact execution-backed head is

```text
f635d873cf5e77f7cb0d2756469acde60b8609e5
```

with terminal

```text
PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED
```

At nominal control factor `s_ctrl=5`:

```text
registered direction/cutoff coordinates: 18
rank ambiguous: 17
resolved: 1
containment candidates: 0
resolved survivor coordinates: 1
control-factor sensitivity stable: false
```

The one resolved coordinate, `Z` at `L=9`, had

\[
\operatorname{rank}_{\rm num}K=21,
\qquad
\operatorname{rank}_{\rm num}J_{\rm surv}=11,
\]

with the augmented-rank identity satisfied. The best smallest-singular-value
margin was only

\[
\mu_{\max}=0.20406518155\ldots,
\]

well inside the ambiguity region. Thus finite-operator containment was not
established.

## 13. Current A4 source and execution boundary

The current PR #444 source adds a matrix-valued numerical-error envelope,
compensated family-scaling invariance, exact-zero-family refusal, holdout
validation, and generalized singular-value diagnostics. Its current exact-head
GitHub workflows ended before runner assignment and executed zero steps.

Accordingly:

```text
current A4 mathematics: SOURCE_IMPLEMENTED / DERIVED
current A4 exact-head runtime: PRESTART_NO_EXECUTION
last accepted finite-operator science: MATCHED_CONTROL_RANK_UNRESOLVED
```

A source-equivalent local Python run is useful debugging evidence but does not
replace the byte-exact GitHub execution authority.

## 14. Deterministic nuisance versus statistical high-source models

The quotient theorem above uses an unrestricted deterministic high-source
nuisance class. A physical statistical model with a declared high-source
covariance or prior is a different problem. For example, a covariance-aware
model may induce

\[
\Sigma_{\rm eff}(\beta)
 =\Sigma_0+A(\beta)C_HA(\beta)^T.
\]

Deterministic containment does not by itself imply absence of statistical
information under such a restricted stochastic model. Conversely, a prior-
dominated estimate is not a model-free identification theorem.

## 15. Literature boundary

The processed matrix architecture is consistent with literature showing:

- first-order full-sky boost nearest-neighbour coupling;
- mask-induced mode mixing and mean-field/bias corrections;
- the inadequacy of a single scalar transfer factor for general filtering;
- the need to separate Doppler modulation, aberration, dipole, beam, noise,
  and mask effects.

Those sources motivate the architecture but do not determine this repository's
matrix ranks, numerical threshold, or error-family completeness.

## 16. T6 terminal

```text
PASS_WU011_PROCESSED_RESPONSE_QUOTIENT_SYNTHESIS
/
TASK7B_NO_CANDIDATE_RETAINED
/
FINITE_OPERATOR_CONTAINMENT_UNRESOLVED
/
CURRENT_A4_RUNTIME_UNOBSERVED
```

This closes the Report-A operator and quotient theory. It opens:

- T7 continuum wide-mask proof strengthening;
- T8 matrix-valued numerical-error and partial-subspace theory.

It does not authorize observational execution, empirical beta, boost
subtraction, local/global equivalence, finite-HEALPix no-go promotion, physical
source attribution, publication, or merge.
