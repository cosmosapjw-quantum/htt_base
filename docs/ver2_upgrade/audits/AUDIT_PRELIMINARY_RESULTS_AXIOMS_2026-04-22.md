# AUDIT_PRELIMINARY_RESULTS_AXIOMS_2026-04-22

## Scope

- `docs/ver2_upgrade/lowell_bianchi_solver_SDD_PR_WBS_pstf_tetrad.md`
- `docs/ver2_upgrade/VER2_PHASE_PROMPTS_05_PRELIMINARY_RESULTS.md`
- `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
- `docs/manuscript/ch01_introduction.tex`
- `docs/manuscript/ch03_framework.tex`
- `docs/manuscript/ch06_pipeline.tex`
- `docs/manuscript/ch07_results.tex`
- selected current implementation anchors:
  - `htt/bass/background/bianchi_types.py`
  - `htt/bass/runtime/ver2_execution.py`

## Purpose

Encode the user-requested architectural constraints as hard preliminary-results
axioms instead of leaving them implicit:

1. all eleven Bianchi types with orthogonal/tilted branching remain the solver
   domain;
2. global tilt and local boost remain distinct contracts;
3. the 1+3 gauge-invariant covariant PSTF formalism remains the semantic
   authority while the tetrad approach remains the implementation backbone;
4. constraints continue to descend from the identity path, and family extension
   should prefer algebra substitution over family-specific rewrites.

## Readout

### From the SDD

- the solver domain is explicitly all eleven Bianchi types;
- both orthogonal and tilted branches are in scope for each type;
- the mathematical authority is the 1+3 gauge-invariant PSTF Einstein-Boltzmann
  system in an orthonormal tetrad;
- Bianchi type enters through the spatial commutator algebra;
- constraint generation is explicitly tied to Ricci/Jacobi/Bianchi identity
  logic.

### From the manuscript

- the science target is departure from FLRW under assumption-explicit low-`ell`
  modeling;
- tilt-vs-geometry and CMB-vs-matter attribution remain central;
- the distinction between matter-frame tilt and observer-frame artifacts is not
  optional bookkeeping; it is part of the claim structure.

### From the current code anchors

- `htt/bass/background/bianchi_types.py` already carries all-eleven-type algebra
  objects plus branch metadata;
- `htt/bass/runtime/ver2_execution.py` already preserves explicit runtime
  feature/coupling metadata and is compatible with keeping observer/boost logic
  separate from background tilt logic;
- the current preliminary-results packet order was still vulnerable to a
  misreading in which the representative-family sweep could be mistaken for a
  semantic narrowing of the solver domain.

## Audit conclusion

The requested conditions are compatible with the manuscript goal and the SDD.
They should therefore be encoded as hard rules for preliminary-results mode:

1. representative-family sweeps are a staging order, not a domain reduction;
2. global tilt and local boost must stay distinct all the way through forward
   outputs and downstream interop;
3. PSTF objects remain the equation-level source of truth and tetrad components
   remain the implementation representation;
4. new family enablement should default to algebra substitution on the shared
   tetrad/PSTF backbone unless the SDD explicitly demands a family-specific
   operator.

## Action taken

- updated `VER2_PHASE_PROMPTS_05_PRELIMINARY_RESULTS.md`
- updated `NEXT_SESSION_PROMPT_VER2.md`

## Non-goals

- this audit does not claim that all eleven families are already equally
  executable on the live preliminary-results path;
- this audit does not claim that non-Type-I exact propagation is closed;
- this audit does not promote direction-resolved microphysics or full geometry
  identification.
