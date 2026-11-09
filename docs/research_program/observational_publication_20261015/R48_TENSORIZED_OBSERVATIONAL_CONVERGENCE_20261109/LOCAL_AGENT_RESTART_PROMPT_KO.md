# R48 local restart — geometry-only tilted Bianchi similarity atlas

## Scope lock

This task is limited to **geometry-only Bianchi type similarity and tilt-orbit identifiability across all 11 Bianchi types**. Do not build or extend a Boltzmann solver, perturbation hierarchy, Thomson kernel, recombination/visibility, line-of-sight transfer, CMB C_l/polarization, Cobaya likelihood or sampler. Do not acquire Planck maps or run observational inference.

The Bianchi-I temperature map from R48-T2 is historical supporting work only. Do not generalize it to all types in this task. The R10 optical first-jet, WU-009/010/011 and FB-8 GlobalTilt/ObserverBoost materials are prior work to preserve, not implementation targets here.

## Repository and branch

- Repository: cosmosapjw-quantum/htt_base
- Branch: research/r48-tensorized-observational-convergence-20261109
- PR #572 remains OPEN/DRAFT and must not be merged or retargeted.
- Resolve the live branch HEAD before work; embedded hashes are historical.
- Inspect git status, branch, HEAD, remotes and uncommitted work. Never reset, clean, stash or overwrite user changes.
- All changes remain on the R48 branch. No raw data in Git.

## Read these SSOT files first

- BIANCHI_TYPE_SIMILARITY_METHODS_KO.md
- BIANCHI_TYPE_SIMILARITY_SPEC.json
- BIANCHI_TYPE_SIMILARITY_ORACLE_REPORT.json
- BIANCHI_NOVELTY_AND_SIGNIFICANCE_ASSESSMENT_KO.md
- HISTORICAL_SOURCE_MATRIX.json
- RESEARCH_DAG.json
- htt/bass/background/bianchi_types.py
- htt/bass/diagnostics/bianchi_similarity.py
- htt/bass/diagnostics/test_bianchi_similarity.py
- htt/bass/hierarchy/tilt_kinematics.py
- docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md
- docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md
- docs/generated/king_ellis_frame_seal.json

## First action: exact-head repository verification

1. Inspect current worktree without changing it.
2. Run:
   PYTHONPATH=htt pytest -q htt/bass/diagnostics/test_bianchi_similarity.py
   PYTHONPATH=htt python -m compileall -q htt/bass/diagnostics
3. Record exact command, exit code, Python/NumPy/pytest versions, branch HEAD, stdout/stderr and output hashes.
4. The standalone canonical-fixture oracle receipt in BIANCHI_TYPE_SIMILARITY_ORACLE_REPORT.json is not a substitute for this exact-head repository run.
5. If import/tests fail, classify source/API mismatch, mathematical assertion, numerical tolerance or environment/runtime. Make at most one bounded repair pass; preserve red output.

## Mathematical adversarial review

Review these exact questions:
- Does the BASS Ellis–MacCallum (a,n,C) builder satisfy the stated convention and Jacobi n@a=0 for every type?
- Is the SO(3) plus positive-homothety quotient stated exactly, with no implicit O(3) parity identification?
- Are Type I/VII_0 and Type V/special-VII_h curvature degeneracies derived from actual Ricci tensors?
- Is Ricci spectrum correctly described as a screening fingerprint, not a general complete local-isometry classifier?
- Does the tilt moment matrix have rank equal to the number of distinct eigenvalues, and do class-specific pseudoscalars restore only the discrete orientation they encode?
- Does every repeated-eigenvalue stratum retain a continuous azimuth only when v projects into that eigenspace?
- Does near-degeneracy cause condition-number inflation before exact rank loss?
- Are FB-3.2/FB-3.4 tilt adapters accurately described as partial kinematic terms, not a complete acceleration/vorticity solution?
- Is GlobalTilt kept distinct from ObserverBoost per FB-8?

Do not silently claim arbitrary (a,n,v) is a constraint-satisfying Einstein-fluid solution. Do not infer a Bianchi group action from Ricci curvature alone.

## Next deliverable

Produce one focused adversarial review and, if needed, one bounded correction:
- INDEPENDENT_GEOMETRY_REVIEW_KO.md
- GEOMETRY_CLAIM_LEDGER.json

Novelty priority remains provisional until invariant theory and metric-Lie-algebra equivalence literature have been independently checked. The task ends after this review and one repair pass, or a narrow BLOCKED result.

## Stop conditions

Stop if:
- a type-orbit distinction depends on an unstated frame convention;
- a curvature degeneracy is mistaken for full group equivalence;
- a tilt component is asserted identifiable outside the orbit-map rank;
- a physical tilted solution is claimed without Einstein constraints;
- the task expands toward Boltzmann, LOS, CMB transfer or Bayesian inference.
