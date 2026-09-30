# Independent implementation review

Decision: **PASS_WITH_DECLARED_SCOPE** after one targeted repair closeout. No blocking implementation defect remains in the reviewed files. This is code review against inherited conditional theory, not scientific admission, formal proof checking, observational identification, or posterior/coverage calibration. Reviewer actual model/effort metadata were unavailable and are not inferred from profile names.

## Scope and provenance

Read the repository root, common and HTT AGENTS. Reviewed the files listed in `REVIEWED_FILES_SHA256.json` against frozen TBO/BIC claim scopes, the geometry/observation derivations, the F1–F7 formalism mapping and W1 erratum. The root agent remained the sole production writer. The reviewer wrote only within the separate review directory and ran read-only verification commands. No external engines, catalogues or full repository campaign were run.

## Findings and repairs

1. **Repaired — causal type cannot be relaxed by tolerance.** At the original `common/relativistic_kinematics.py:36–42`, `unit_timelike([1,1,0,0], tolerance=2)` returned a null vector. Current code checks the Lorentz norm is strictly negative independently and bounds the normalization tolerance to 1e-6.
2. **Repaired — finite input cannot produce silently malformed geometry.** `homogeneous_scalar_curvature(1e200*eye(3),[0,0,0])` returned NaN and `perfect_fluid_normal_projection(1e308,0,[.9,0,0])` returned Inf/NaN. The same issue appeared in extreme inverse-temperature and ideal drift-moment outputs. The shared representability check now raises `NumericalUnresolved` on these outputs; regression tests cover the reproduced cases.
3. **Repaired — ambiguous covariance is not declared valid.** The original F5 check accepted `diag([-1e-15,1])` and returned a negative initial variance with `SUPPLIED_JOINT_COVARIANCE`. The current function raises `NumericalUnresolved` on the ambiguous nonzero-eigenvalue stratum; no jitter or clipped covariance is introduced.

## Mathematical and statistical checks

- Boost signature/sourceward direction, same-ray endpoint optics, Hubble null-form representative/eigenline lift and repeated-eigenvalue refusal agree with the frozen derivation.
- Codazzi index order, homogeneous Koszul connection, invariant simple-eigenframe reconstruction, normal-frame Hamiltonian curvature and ideal position-drift coefficients are consistent with the stated conventions. Velocity-jet projection retains the explicit antisymmetric-index convention and physical c factors.
- P2 retains theta squared/3, the full shear norm, twice the vorticity-vector norm squared and A squared/c squared. W1 retains the signed endpoint term and the supplied coefficient-error requirement.
- F1–F3 preserve same-state references, relative-span membership and undefined probability mass; strict exceedance does not renormalize unavailable atoms.
- F4 distinguishes the quotient gauge from hidden-state identification and point fibers from zero projected directions. The rational adapter has an actual finite box and exact rational constraints.
- F5 preserves signs and full cross-depth covariance; fitted transport remains scenario-only.
- Endpoint inference has a free four-coefficient intercept and nine area-distance slope coefficients. Dense scaled GLS, known noise covariance, deterministic remainder bias, row masks and permutations are coherent. Unknown remainders, rank deficiency and unimplemented distance-error integration fail closed.
- F6 requires both mean and covariance equality on the same complete finite Gaussian observation identity; no allclose promotion occurs. HTT owns the finite posterior adapter, whose toy posterior is explicitly independent of the endpoint GLS fixture.
- The narrow legacy MIO ratio repair preserves finite and zero-denominator behavior while blocking nonfinite inputs/output. No legacy matrix pseudoinverse quadratic was relabeled as a body gauge.

## Independently observed verification

Command, from the verified partial source workspace:

```bash
PYTHONPATH=/workspace/scratch/83eeacddad29/htt_port_20260930/test_dependencies:htt/src:htt/htt:htt python3 -m pytest htt/src/common/test_relativistic_kinematics.py htt/src/common/test_typefree_functionals.py htt/src/common/test_typefree_fibers.py htt/src/common/test_typefree_depth.py htt/htt/tests/test_endpoint_cosmography.py htt/mio/tests/test_typefree_ratio_boundary.py -q
```

Result: **42 passed in 0.87s**. This command used normal package imports; no namespace shim or initializer bypass.

```bash
python3 scripts/run_typefree_predata_fixture.py
```

Result: `SYNTHETIC_PRE_DATA_INTEGRATION_PASSED`, design rank 13, scaled condition 6.10806715720823. Maximum intercept velocity residual 6.3144e-16; slope velocity residual 1.3637e-14; symmetric-gradient residual 3.2969e-12. Separate two-atom toy posterior retained undefined mass 0.75 and tail interval [0.25,1]. These numbers are deterministic numerical checks, not empirical results.

## Remaining limits

- Floating ellipsoid `EMPTY_SET` is a numerical result under its declared error/conditioning rule, not a formal infeasibility certificate for empirical BIC-06 exclusion. Exact rational support certifies only the supplied finite polytope. Neither constructs physical outer sets or confidence calibration.
- Fixed independent area distances, fixed selection, known Gaussian covariance and source/observer semantics are supplied premises. Actual distance uncertainty, outcome-dependent selection, coarse-graining and finite-distance response must be admitted before data analysis.
- No Wolfram+xAct, SymPy, Sage+Singular or Lean/mathlib campaign was executed by this reviewer; local checks remain required for their intended scientific admission.
- I2 remains `DEFENDED_CONDITIONAL`; I3 remains `HOLD_INPUT_INCOMPLETE`; observational normal reconstruction and actual tilt/Bianchi classification remain unresolved.
- This report reviews the listed code/tests and synthetic integration. Subsequent publication metadata and local handoff documents are the root agent’s delivery responsibility.
