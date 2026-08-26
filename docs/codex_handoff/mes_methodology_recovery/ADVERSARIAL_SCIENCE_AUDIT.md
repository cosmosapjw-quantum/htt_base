# MES methodology recovery — adversarial science audit

## Exact audit identity

```yaml
repository: cosmosapjw-quantum/htt_base
planning_base_branch: changeset/pr320-hsc-kids-cross-covariance-20260825
planning_base_sha: a968e11461ed28c8d5cc1244f0122edc704579c4
planning_base_tree: 3e1f1cf27683d122618de6b8296dbc1ca4f6f27f
operating_profile: private_single_researcher_local_v1
canonical_DAG_changed: false
science_code_changed: false
observed_data_executed: false
```

## Executive verdict

```yaml
current_observed_MES_result_count: 0
current_observed_local_global_result_count: 0
PR314:
  preserve: true
  family_rank: 133/301
  role: DELIVERED_FULLSKY_SMICA_CONDITIONAL_GENERIC_LOWELL_CONTROL
  MES_method_result: false
  local_global_result: false
methodology_drift:
  severity: P0
  finding: >-
    The only executed observed result bypasses the active MES authority,
    typed vector/tensor state and physical local/global response layer. A
    generic anomaly scan was becoming the publication spine.
recovery:
  theory_core: SUBSTANTIALLY_RECOVERED
  observational_bridge: NOT_IMPLEMENTED
  controlling_contract: this_package_after_human_acceptance
```

The intended scientific chain is

\[
\text{verified MES premise anchors}
\to
\text{direction-indexed scalar observables}
\to
\text{O(3)-typed vector/tensor moments}
\to
\text{finite-null anomaly analysis}
\to
\text{depth-dependent local-boost/global-tilt discrimination}.
\]

The existing generic low-multipole analysis remains useful as a benchmark and
control. It is not allowed to replace this chain.

## 1. Repository capability versus realised science

### Present and authoritative

- verified geodesic MES shear and vorticity branches with exact coefficient
  triples and source/lineage receipts;
- typed premise anchors carrying frame, congruence, normalisation, branch,
  perturbative order and shared nuisance identity;
- a joint anisotropy state separating congruence kinematics, velocities between
  radiation/matter/observer frames, and geometry tensors;
- O(3)-typed tensor functionals, orbit invariants and response-rank diagnostics;
- local-boost/global-tilt hypothesis vocabulary and null/rank gates;
- observation-inclusive finite ranks;
- an executed Planck PR3 SMICA 300-pair low-ell feature result.

### Missing from the observed path

The Planck worker does not consume:

- the active typed MES anchor factory;
- the joint vector/tensor anisotropy state;
- a legal scalar-to-directional-moment bridge;
- physical local/global response matrices;
- a depth-path statistic;
- the x_C,Q,Pi,F,G_F reporting layer.

The current local/global response library is a pre-solver support/rank skeleton.
Its binary support vectors are not covariant physical response templates.

## 2. Research-loop results

### 2.1 Scalar-only equivariant no-go

Let s be any collection of rotational scalars and let F(s) be an O(3)-equivariant
vector. Since s is fixed by every rotation R,

\[
F(s)=F(Rs)=R F(s)\quad\forall R\in SO(3).
\]

The only vector fixed by all rotations is zero. The same argument in the
irreducible STF2 representation gives only the zero tensor.

**Result.** A scalar MES anchor cannot create a preferred axis, vorticity
vector, shear eigenframe or tilt vector. A code path doing so is P0-invalid.

Wolfram solved the infinitesimal generator equations J_i v=0 and
[J_i,T]=0 with tr(T)=0 and found only v=0 and T=0.

### 2.2 Constructive directional scalar to vector/STF theorem

The no-go does not apply to a scalar field q(n,z), because the sky direction n
is independent observed structure. Define

\[
V_a(z)=\frac{3}{4\pi}\int q(\boldsymbol n,z)n_a\,d\Omega,
\]

\[
T_{ab}(z)=\frac{15}{8\pi}\int q(\boldsymbol n,z)
 n_{\langle a}n_{b\rangle}\,d\Omega.
\]

For q(n)=v_a n^a+S_ab n^a n^b plus harmonics orthogonal to l=1,2, with
S_ab STF,

\[
V_a=v_a,\qquad T_{ab}=S_{ab}.
\]

Wolfram exact sphere integration reproduced both identities component by
component. These maps are O(3)-equivariant. A masked/discrete implementation
must bind its exact quadrature or joint harmonic estimator.

### 2.3 MES anchor is scale, not orientation or new information

For fixed U>0, replacing q by q/U scales V and T by U^{-1} while preserving
normalised directions, tensor eigenspaces and homogeneous shape invariants.
For example

\[
J_T=\sqrt6\,\frac{\operatorname{tr}(T^3)}
 {\operatorname{tr}(T^2)^{3/2}}
\]

is invariant under T->cT for c>0.

For response R and invertible parameter normaliser D,

\[
F_D=(RD)^T C^{-1}(RD)=D^T F D.
\]

Rank and response subspaces do not change. MES normalisation can create an
interpretable stress coordinate and alter conditioning, but cannot create
identification or independent evidence.

A row-dependent self-anchor is a new nonlinear statistic rather than a fixed
invertible reparameterisation. It is admissible only when preregistered and
applied identically to the observation and every null row.

### 2.4 Local boost/global tilt single-shell no-go

For a vector observable in depth shell z_i,

\[
\boldsymbol V_i=f_L(z_i)\boldsymbol\beta_L+
 f_G(z_i)\boldsymbol\beta_G+\boldsymbol\epsilon_i.
\]

With directional metric S and depth Gram matrix

\[
K=\begin{pmatrix}
\langle f_L,f_L\rangle&\langle f_L,f_G\rangle\\
\langle f_L,f_G\rangle&\langle f_G,f_G\rangle
\end{pmatrix},
\]

the six-parameter Fisher matrix is K tensor S and

\[
\det F=\det(K)^3\det(S)^2.
\]

Thus local and global three-vectors are identified only when directional
support is rank three and f_L,f_G are linearly independent in covariance-weighted
depth space. With one shell K has rank one. Planck alone cannot identify local
boost versus global tilt without an additional physical response restriction.

### 2.5 Finite reverse-martingale depth-path theorem

For a finite decreasing filtration G_0 superset ... superset G_n and
M_j=E[X|G_j], reverse the sequence to obtain a forward martingale. Applying
Doob's inequality to |M|^2 gives

\[
P\left(\max_j|M_j|^2\ge\lambda^2E[X^2]\right)\le\frac1{\lambda^2}.
\]

This establishes the general finite-path theorem. It does not show that nested
sky masks are sigma fields, that data-fitted rung estimators are conditional
expectations, or that observed calibration is free. Those are separate matched-
mock or estimator-identity obligations.

### 2.6 Row-equivariant finite-rank theorem

If Z_0,...,Z_m are exchangeable and the complete scoring map is permutation
equivariant, the score rows remain exchangeable. The conservative rank

\[
p_0=\frac{\#\{j:S_j\ge S_0\}}{m+1}
\]

is super-uniform, with ties conservative. A nested family score is valid when
every layer is row-equivariant. The current Planck max scan is structurally
consistent with this theorem, but a permanent row-permutation/observation-swap
regression is still required.

At alpha=0.05 the first nonempty rejection region occurs at m=19 calibration
rows; in general its worst-case size is floor(alpha(m+1))/(m+1).

### 2.7 Zero-mean spherical second-moment cone

For a probability measure on S2, M=E[n n^T] is PSD and tr(M)=1. Conversely,
write any PSD trace-one M as sum lambda_i e_i e_i^T. The antipodal measure

\[
\mu=\frac12\sum_i\lambda_i(\delta_{e_i}+\delta_{-e_i})
\]

has zero mean and second moment M. This closes the stated zero-flux second-
moment realizability problem, not higher moments or dynamics.

### 2.8 VT-T8 transverse generic slice

For a simple-spectrum diagonal STF tensor S, the infinitesimal orbit tangent is
[A,S]. The rotation-parameter to off-diagonal-component map has determinant

\[
-(\lambda_1-\lambda_2)(\lambda_1-\lambda_3)(\lambda_2-\lambda_3).
\]

It is nonzero on the simple-spectrum locus. Combined with the existing nonzero
14-coordinate Jacobian, this supports a local quotient chart on a fixed ordered-
eigenvalue and residual-sign branch. Sage/Singular and Lean/Rocq receipts are
still required before publication wording is promoted.

### 2.9 Reclassified prior claims

- broad J1/J2 anchor conjectures are REFUTED_OR_RESTRICTED by PR254; only the
  one-way containment statement survives;
- PR197 finite-rank resolution is established, not unresolved;
- non-geodesic MES coefficients remain BLOCKED_PRIMARY_SOURCE;
- PR210 is a type-safe bridge but not a derived physical frame transform;
- PR216 remains partial until branch-complete constraints/native development.

## 3. Frozen observed science

The PR314 family rank remains

\[
p_{\rm family}=133/301=19/43.
\]

It is a legitimate delivered-product SMICA/FFP10 conditional generic low-ell
control and is not a MES-method result.

Using the active verified geodesic MES coefficients, the frozen observed C2 and
C3, and explicit residual cosmological epsilon1=0 gives

```yaml
epsilon2: 3.222100796619276e-6
epsilon3: 6.017158726898917e-6
B_sigma: 1.2245084701385934e-5
B_omega: 4.296134395492368e-7
Sigma2_max: 2.249131490161738e-10
W2_max: 2.768515611619886e-13
```

These values are diagnostic only. They use the frozen PR314 estimator and have
no rowwise null distribution. PR315 must close the cut-sky estimator before
publication-facing values are frozen. The quarantined historical Planck MES
module uses different coefficients and must not be reactivated.

## 4. Correct observational architecture

### Observer-space MES index

Input: a directional observable scalar field plus a positive typed anchor.
Output: MES-normalised scalar/vector/STF morphology. This is an observational
coordinate and does not identify physical shear or vorticity without a response
map.

### Physical MES stress

Input: a data-identified physical-sector numerator plus a channel-matched MES
anchor. Required metadata include response/transfer, frame, congruence,
normalisation, covariance and identification status. Output is a one-way premise
stress or identified interval, never a converse or evidence term.

### Planck Paper A

1. Complete the existing PR315 joint cut-sky estimator.
2. Compute active typed MES anchors for the observation and the same 300 nulls.
3. Separate amplitude anchors from quadrupole/octupole shapes, axes and parity.
4. Apply the full nonlinear row map symmetrically to all 301 rows.
5. Report MES-anchored finite ranks and retain the generic result as a control.
6. Report structural single-shell local/global nonidentification.

### Tomographic Paper B

Use low-redshift direction/depth fields plus covariant local and global response
profiles. Require full nuisance-projected whitened rank. A missing response or
proportional depth profile returns typed nonidentification. The first exact
admitted low-z lane is sufficient; do not wait for every probe.

## 5. Final disposition

```yaml
theory_updates:
  scalar_to_vector_tensor_no_go: ESTABLISHED
  directional_moment_reconstruction: ESTABLISHED
  anchor_scale_shape_invariance: ESTABLISHED
  local_global_single_shell_no_go: ESTABLISHED
  local_global_depth_rank_criterion: ESTABLISHED
  finite_reverse_martingale_Doob: ESTABLISHED
  row_equivariant_finite_rank: ESTABLISHED
  zero_mean_second_moment_cone: ESTABLISHED
  VT_T8_transversality: ESTABLISHED_ON_FIXED_GENERIC_BRANCH
  J1_J2_broad_claims: REFUTED_OR_RESTRICTED
remaining_local_work:
  - xAct frame/boost bridge
  - xAct branch-complete constraints
  - Sage/Singular VT-T8 discrete branch
  - Lean/Rocq no-go, finite-rank and moment-cone proofs
  - non-geodesic MES only after primary-source recovery
observational_status:
  generic_control: EXECUTED
  MES_anchored_observed_analysis: NOT_YET_EXECUTED
  local_global_observed_discrimination: NOT_YET_EXECUTED
```
