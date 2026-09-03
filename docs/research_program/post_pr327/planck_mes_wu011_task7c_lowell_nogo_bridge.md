# PMG-WU-011 Task-7C — Existing Low-ell No-go Reuse and Nuisance-Saturation Short-Circuit

## Status and frozen input

`CONTRACT_AMENDMENT / NO_NEW_SCIENTIFIC_TERMINAL`

- Repository: `cosmosapjw-quantum/htt_base`
- Draft PR: `#444`
- Input head inspected before this amendment: `ac3053d058d52954b47200f6cd88e2a79d20bbf6`
- Upstream scientific terminal retained: `PASS_TASK7B_ATLAS_NO_CANDIDATE`
- This document changes the Task-7C stopping logic only. It does not change the finite boost equations, Task-5B Jacobian, Task-7B atlas, masks, transfer functions, or claim boundary.

Fixed conventions remain metric `(-,+,+,+)`, outward sky direction `n=-e`, active local-observer boost `+beta`, `beta=v/c`, and thermodynamic-temperature Doppler weight `d=1`.

## 1. Existing repository no-go authorities

Task-7C must not re-prove a blanket statement that a finite low-multipole set is statistically sufficient or complete.

### PR-130: convergence is not sufficiency

`htt/src/common/nt2_tail_convergence.py` and `docs/research_program/long_horizon_rescue/pr130_spec.yaml` already enforce:

- convergence or a small high-ell tail does not imply finite-set statistical sufficiency;
- no finite multipole set may be called sufficient without a registered factorization theorem;
- the current factorization registry is empty;
- only truncation error and convergence rate may be reported for the registered toy response.

PR-130 is a toy/transfer-conditional governance theorem. It is not, by itself, a proof about the present processed boost operator.

### PR-127 / PR-219: identification is a quotient of the declared response

`htt/src/common/revival_response_quotient.py` already fixes the general interpretation:

- two physical labels or source directions that induce the same declared response are non-identified under that observable set;
- adding an observable may refine the quotient;
- an unobserved response direction is not a physical impossibility theorem.

For Task-7C, the relevant quotient is the low-source processed image modulo the unrestricted high-source processed image.

### Manuscript and PR-072 claim firewall

The manuscript framework and PR-072 already prohibit promoting scalar low-ell diagnostics or compressed low-ell summaries into Bianchi-family, geometry, or global-tilt identification. Task-7C is therefore a processed-response identifiability audit, not a new physical-source claim.

## 2. Project-specific bridge object

For a registered unit boost direction `bhat`, let

\[
J_{\hat b}\in\mathbb R^{32\times48}
\]

be the metric-whitened retained response of the registered low source, and let

\[
K_{\hat b}(L)
=
\left[K^{(7)}_{\hat b}\mid\cdots\mid K^{(L)}_{\hat b}\right]
\]

be the metric-whitened response of an unrestricted source band `ell=7..L`.

Define

\[
\mathcal L_{\hat b}=\operatorname{Im}J_{\hat b},
\qquad
\mathcal H_{\hat b}(L)=\operatorname{Im}K_{\hat b}(L).
\]

The model-free identified low-response subspace is represented by

\[
J_{\rm surv}(L)
=
P_{\mathcal H_{\hat b}(L)^\perp}J_{\hat b}.
\]

The exact rank witness is

\[
\boxed{
\operatorname{rank}J_{\rm surv}(L)
=
\operatorname{rank}\left[K_{\hat b}(L)\;J_{\hat b}\right]
-
\operatorname{rank}K_{\hat b}(L)
}.
\]

Hence

\[
J_{\rm surv}(L)=0
\quad\Longleftrightarrow\quad
\mathcal L_{\hat b}\subseteq\mathcal H_{\hat b}(L).
\]

## 3. Nested-image short-circuit theorem

The cumulative source registry is nested:

\[
K_{\hat b}(L+1)
=
\left[K_{\hat b}(L)\mid K^{(L+1)}_{\hat b}\right],
\]

so

\[
\mathcal H_{\hat b}(L)
\subseteq
\mathcal H_{\hat b}(L+1).
\]

Therefore, if at any finite registered cutoff `L0`

\[
\mathcal L_{\hat b}
\subseteq
\mathcal H_{\hat b}(L_0),
\]

then for every `L >= L0`

\[
\mathcal L_{\hat b}
\subseteq
\mathcal H_{\hat b}(L),
\qquad
J_{\rm surv}(L)=0.
\]

A sufficient special case is

\[
\operatorname{rank}K_{\hat b}(L_0)=32,
\]

because the fixed-direction retained output has dimension 32.

This is an exact linear-algebra short-circuit. Once robust containment is established, larger source cutoffs cannot restore an identified low-source direction. Tail-norm convergence is then unnecessary for the deterministic unrestricted-nuisance no-go terminal; it remains relevant only for quantitative amplitude or covariance modelling.

## 4. Dimension facts, not a proof of saturation

The high-source dimension is

\[
d_H(L)=\sum_{\ell=7}^{L}(2\ell+1)=(L-6)(L+8).
\]

Thus

```text
L=8  -> d_H=32
L=9  -> d_H=51
L=12 -> d_H=120
L=16 -> d_H=240
L=20 -> d_H=392
```

At `L=9`, the stacked low-plus-high source has `48+51=99` columns for 96 stacked outputs, giving nullity at least three. These dimension counts show why a point inverse is forbidden, but they do not prove that the actual processed `K_bhat(L)` has full image rank. The finite containment witness is still required.

## 5. Required numerical rank policy

A pure relative SVD threshold is insufficient. For `K_epsilon=epsilon I`, every positive `epsilon` is algebraically full rank under a threshold proportional only to `sigma_1(K_epsilon)`, falsely forcing a zero survivor even as `epsilon -> 0`.

Task-7C must use a matched full-sky control and a machine floor:

\[
\tau_K=
\max\left[
\rho_{\rm rel}\sigma_1(K),
\;s_{\rm ctrl}\sigma_1(K_{\rm full}),
\;c_{\rm mach}\epsilon_{\rm mach}\max(m,n)\sigma_1(J)
\right].
\]

Initial engineering controls for RED tests are

```text
rho_rel = 1e-10
s_ctrl in {2,5,10}
c_mach = 64
ambiguity band = [tau_K/2, 2*tau_K]
```

These are numerical controls, not physical high-ell priors. A singular value in the ambiguity band must produce `BLOCKED_BY_DIRECTIONAL_THRESHOLD_AMBIGUITY`.

## 6. Shortened Task-7C execution DAG

The previous unconditional `L=9,12,16` convergence ladder is replaced by an adaptive bridge witness.

### A1. Rank-policy repair

1. implement the control-anchored threshold;
2. use the same near-zero policy for survivor sector fractions;
3. verify the exact augmented-rank identity;
4. kill the `K=epsilon I` false-no-survivor mutation;
5. repair numerically stable principal-angle comparison near zero.

### B1. Adaptive containment witness

For each of the six registered boost directions:

1. evaluate the best cut-sky baseline at `L=9`;
2. if robust containment holds, stop that direction;
3. otherwise evaluate `L=12`;
4. evaluate `L=16` only for directions whose survivor remains nonzero or threshold-ambiguous;
5. evaluate the targeted `L=20` extension only if `L=12` and `L=16` disagree or ambiguity remains.

Full-sky matched controls remain mandatory at every numerical setting used to define `tau_K`. A single `nside=32` confirmation of the first saturation/containment cutoff is required before the terminal is admitted.

### B2. Terminals

```text
PASS_TASK7C_LOWELL_NONIDENTIFICATION_WITNESS
PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE
PASS_TASK7C_SOURCE_BAND_UNRESOLVED
BLOCKED_BY_DIRECTIONAL_THRESHOLD_AMBIGUITY
BLOCKED_BY_MIXED_DIRECTIONAL_OUTCOME
BLOCKED_BY_ARTIFACT_INTEGRITY
```

`PASS_TASK7C_LOWELL_NONIDENTIFICATION_WITNESS` requires every registered direction to satisfy, at a control-floor-safe cutoff,

\[
\operatorname{rank}[K\;J]-\operatorname{rank}K=0
\]

with stable nested registries and the declared resolution confirmation.

## 7. What is shortened and what is not

Eliminated:

- re-proving that finite low-ell convergence implies or does not imply statistical sufficiency;
- unconditional execution of every larger cutoff after robust containment is already established;
- treating cumulative tail-norm convergence as a prerequisite for a deterministic unrestricted-nuisance no-go.

Retained:

- numerical-floor-safe image rank;
- exact project-specific containment witness;
- six direction checks because the cut sky breaks rotational symmetry;
- one resolution confirmation;
- typed negative terminals, artifacts, manifest, and dual audit.

## 8. External literature role

Masked or partial-sky anisotropy analyses require explicit mode-coupling treatment. Aluri, Pant, Rotti, and Souradeep, `arXiv:1510.02454`, recover boost-induced statistical anisotropy with a BipoSH mask-coupling correction. Leung et al., `arXiv:2111.01113`, show why realistic filtering generally needs a two-dimensional transfer matrix rather than a scalar transfer factor. These support the processed-response architecture but do not replace the repository-specific containment witness above.

## 9. Claim boundary

The allowed conclusion is narrow:

> Under the registered processed operator, direction set, numerical-control policy, and unrestricted deterministic high-ell nuisance class, the retained low-source local-observer boost response has or lacks a model-free survivor.

This is not evidence that observer motion is absent, that all low-ell analyses are useless, that high-ell nuisance has arbitrary physical amplitude, or that a Bianchi geometry, family, global tilt, polarization signal, or empirical beta has been identified.
