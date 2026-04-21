# AUDIT_PRM-01_BASS_INTEROP_2026-04-22

## Scope

- `docs/ver2_upgrade/VER2_PHASE_PROMPTS_05_PRELIMINARY_RESULTS.md`
- `docs/ver2_upgrade/lowell_bianchi_solver_SDD_PR_WBS_pstf_tetrad.md`
- `htt/bass/forward/ver2_solver_output.py`
- `htt/bass/observational/observable_vector_builder.py`
- `htt/bass/observational/atlas_entry_lite_builder.py`
- `htt/bass/likelihood/live_binding.py`
- touched tests under `htt/bass/{forward,observational,likelihood,inference}/`

## Purpose

Close `PRM-01-BASS-INTEROP`: stabilize the current BASS output contracts so
HTT/MIO/TSC and exporter consumers can read branch/family/tilt semantics
without package-local glue or silent semantic inference.

## CoVe / metacognitive audit

### Touched claim

Current BASS outputs are already live enough for preliminary results, but they
were still under-specified for downstream consumers in one important way:
branch, algebra-family, and tilt-vs-boost semantics were not consistently
materialized on the observer-neutral export path.

### What changed

- `SolverCoreOutput` now emits explicit preliminary-results interop metadata:
  - all-11-type solver-domain scope,
  - explicit orthogonal-vs-tilted branch,
  - theory-family tag,
  - global-tilt contract,
  - local-boost contract,
  - explicit tilt/boost non-merger marker,
  - tetrad/algebra and identity-derived constraint contracts,
  - default geometry/kinematic/tilt payload blocks.
- native/Lowell wrappers now enrich those blocks with concrete structure and
  runtime branch metadata.
- `ObservableVector`, `AtlasEntryLite`, and live likelihood bindings now carry
  the same semantics forward instead of forcing downstream modules to infer
  them from type names or side channels.

### What this does not justify

- this does not close non-Type-I exact propagation;
- this does not upgrade any claim tier;
- this does not turn observer-local boost into a geometry claim;
- this does not widen the representative sweep into full 11-type runtime
  coverage.

### Downstream misread blocked by this packet

The main blocked misread is:

> “tilt-enabled output” means the same thing as an observer-frame boost surface,
> or branch/family can be reconstructed downstream from the type label alone.

That is now explicit in the machine-readable payload.

## Equation-to-code consistency check

The SDD requires:

1. all-eleven-type algebra/tetrad architecture remains the solver domain;
2. orthogonal and tilted matter branches remain explicit;
3. global tilt and observer/local boost stay distinct;
4. tetrad components implement 1+3 PSTF quantities rather than replacing them;
5. constraints descend from the Jacobi/Ricci/Gauss/Codazzi/Bianchi identity
   path.

This packet does not add new evolution equations. It aligns the export surface
with those frozen equations/contracts by ensuring the output metadata reflects
them directly.

## Verification

- `venv/bin/python -m py_compile ...` on touched code/tests: pass
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/forward/test_ver2_solver_output.py htt/bass/observational/test_ver2_observable_atlas.py htt/bass/likelihood/test_ver2_live_binding.py htt/bass/inference/test_ver2_live_binding.py -q`
  - `20 passed`
  - warnings limited to the known recombination table early-`z` coverage warning

## Conclusion

`PRM-01-BASS-INTEROP` is closed.

The next DAG-correct step is `PRM-02-BASS-FAMILY-SWEEP`: use the now-stable
interop payloads while expanding the bounded representative-family runtime path
for `V`, `VII_0`, and `VIII` without blurring branch or tilt/boost semantics.
