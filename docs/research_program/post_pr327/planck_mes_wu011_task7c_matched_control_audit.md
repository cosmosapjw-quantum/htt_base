# PMG-WU-011 Task-7C matched full-sky control audit

Date: 2026-09-02
Owner: OBSSTAT / PHYS-MATH / PHYS-MATH-CODE
Claim tier: diagnostic only
Scientific terminal authorized: no
Empirical beta fit: no
Global-tilt claim: no
Bianchi attribution: no
Merge authorized: no

## Purpose

Close the numerical-rank prerequisite left open by the Task-7C low-ell no-go
bridge.  The generic repository no-go against finite-low-ell sufficiency is not
re-derived here.  This node asks only whether the registered cut-sky
high-source response spans the registered low-source response after a
matched full-sky replay floor is removed.

For one fixed boost direction, write

```text
J_b             : registered low-source response into retained ell=2..5
K_b(L)          : cumulative source ell=7..L cut-sky nuisance response
K_b^full(L)     : numerically identical full-sky replay control
```

The candidate threshold is

```text
tau_K = max(
    rho_rel sigma_1(K),
    s_ctrl sigma_1(K_full),
    c_mach eps_machine max(m,n) sigma_1(J)
).
```

A singular value in `[tau_K/2, 2 tau_K]` is ambiguous and yields no
containment decision.  A resolved containment result must also satisfy

```text
rank(P_Im(K)^perp J) = rank([K J]) - rank(K).
```

## Exact PHYS-MATH checks

A fresh Wolfram calculation verified:

1. the rank-one angular selection rule has no channel from source
   `ell=7..20` into retained `ell=2..5` on the exact full sky;
2. the first available channels are nearest neighbours, beginning with
   `7 -> 6,8`;
3. `sum_(ell=7)^L (2 ell+1) = (L-6)(L+8)`, giving dimensions
   `15,32,51,120,240,392` at `L=7,8,9,12,16,20`;
4. exact integer-matrix trials gave zero residual for
   `rank(P_Im(K)^perp J) - [rank([K J])-rank(K)]`.

All statements are dimensionless angular or finite-dimensional linear-algebra
checks.  They do not use a physical high-ell prior.

## Direct arXiv anchors

The literature was read from the arXiv sources rather than from secondary
summaries.

- Aluri, Pant, Rotti, and Souradeep, arXiv:1510.02454: a first-order CMB
  Doppler boost is an off-diagonal nearest-neighbour harmonic response;
  masking produces additional mode coupling and its mean-field/bias must be
  characterized with unboosted simulations.
- Leung et al., arXiv:2111.01113: a scalar transfer function cannot in general
  represent realistic filtering-induced mode mixing; a two-dimensional
  response matrix is required and should be calibrated by simulations.
- Ferreira and Quartin, arXiv:2107.10846: aberration, Doppler modulation, and
  the dipole must remain separated in a realistic beam/noise/mask pipeline,
  with an independent implementation used as a cross-check.
- Chluba and Ravenni, arXiv:2505.02080: the general boost operator is generated
  from aberration kernels; its first-order harmonic structure supplies the
  nearest-neighbour selection rule used by the exact full-sky control.

These papers support a matrix-valued, simulation-controlled response.  They do
not choose the numerical SVD rank threshold for this project.

## TDD lineage

### RED

```text
head: c58e1938b2dcb0a33428102cd9385209ac56683e
workflow: WU011 Task7C rank policy #4 / 33639016182
result: 1 failed, 6 passed
failure: processed_boost_matched_control absent
```

### GREEN core

```text
head: 1dc5b6b0d7290b92468c542c948c7170d4e3325e
workflow: WU011 Task7C rank policy #5 / 33639476183
result: 7 passed
```

Implemented surfaces:

```text
htt/obsstat/processed_boost_matched_control.py
htt/test_wu011_task7c_matched_control.py
htt/test_wu011_task7c_rank_policy.py
```

The implementation rebuilds the source operator and the full-sky control from
the same `Task7COperatorSpec`.  It requires equality of `nside`,
`processing_lmax`, transfer kind, source cutoffs, source-operator identity, and
direction/cutoff registries.  Only the mask and therefore the joint-estimator
operator identity may differ.

## Integration state

The Task-7C runner now writes and verifies a non-terminal companion directory:

```text
matched_control/
  summary.json
  rank_sensitivity.csv
  control_to_cutsky_operator_ratio.png
  survivor_rank_vs_cutoff.png
  SHA256SUMS
```

At head `d0c74f7ad604aab3a13b751e4a84b34a525850f2`, the rank-policy workflow is
green.  The first main Task-7C integration attempt was stopped before artifact
generation by the pre-existing principal-angle exact-zero flake:

```text
expected 8.5377364625e-07 deg; obtained 0.0 deg
1 failed, 9 passed
```

That difference is an SVD/arccos last-bit representation of the same coincident
subspace.  It is not evidence against the matched-control module.  It remains
a P2 regression-quality defect: future repair should compare subspace
projectors/cosines or canonicalize the machine-zero angle, rather than demand
picodegree equality of two equivalent SVD bases.

## Current verdict

```text
MATCHED_FULLSKY_CONTROL_CORE_GREEN
/
PRODUCTION_RUNNER_CONNECTED
/
EXACT_HEAD_RECEIPT_PENDING_CLEAN_RERUN
/
NO_SCIENTIFIC_TERMINAL
```

The next admissible operation is a clean rerun of the exact-head Task-7C
workflow.  If the old angle test again blocks the run, repair that test by a
subspace-invariant comparison before touching the scientific matrices.  If the
runner succeeds, inspect the generated control/cut-sky norm ratios,
control-factor sensitivity, survivor ranks, and ambiguity states before any
adaptive-containment terminal is designed.
