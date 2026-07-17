# BASS Package Guidelines

This file supplements the repo-root `AGENTS.md` for work under `htt/bass/`.
All commands below assume the repository root.

## Scope
- `htt/bass/` is the Python-side solver and physics layer.
- Keep background evolution, species/reference tables, hierarchy evolution, transport, line-of-sight projection, collision terms, recombination, runtime gating, observational thresholds, and validation helpers here.
- Do not move BASS-owned solver physics, numerical evolution, or runtime allow/block semantics into `htt/htt/`, `htt/mio/`, `htt/tsc/`, or `htt/src/common/` unless ownership has been explicitly redefined.

## Ownership Map
- `background`, `species`, `recombination`: cosmological state inputs and reference tables.
- `hierarchy`, `perturbation`, `transport`, `los`, `collision`, `closure`, `forward`, `spectrum`: evolution and observable assembly.
- `runtime`, `validation`, `observational`: production gating, labels, policy checks, and threshold logic.

## Boundary Rules
- `bass/runtime/*` is the only production allow/block owner. Only that surface may construct `CanonicalDecision` or instantiate `ValidationLabel` in production code.
- Keep `bass/background/*` and `bass/transport/*` free of `tsc` imports. Preserve the existing ownership freeze instead of adding ad hoc exceptions.
- Do not import model-dependent HTT logic or MIO reporting semantics into solver modules. Downstream translation belongs in explicit bridge or integration layers.
- Promote code to `htt/src/common/` only when the semantics are genuinely shared by multiple active packages. Solver-internal physics, normalization, and policy logic stay in `bass/`.
- If a change touches physics definitions, normalization, or exported semantics, check the relevant SSOT entry in `docs/SSOT_POLICY.md`, update the local docstring/comments if needed, and add regression coverage rather than duplicating constants locally.

## Change Checklist
Before committing BASS changes, verify:
1. ownership did not move implicitly;
2. solver semantics were not leaked into HTT/MIO/TSC/common;
3. normalization or units changes have an SSOT trace;
4. production labels/gates are still constructed only from `bass/runtime/*`.

## Testing
Run the narrowest relevant battery first, then widen only as needed.

- Localized BASS change:
  - `venv/bin/python -m pytest htt/bass/<touched_subpackage> -q`
- General BASS coverage:
  - `venv/bin/python -m pytest htt/bass -q`
- Ownership / package-boundary change:
  - `venv/bin/python -m pytest htt/test_ownership_freeze.py -q`
- If the Python change mirrors or depends on Rust-side solver semantics:
  - also run the root Rust gates required by the main `AGENTS.md`

## Stop Conditions
Stop and escalate to a decision note if:
- a change requires `CanonicalDecision` or `ValidationLabel` construction outside `bass/runtime/*`;
- importing HTT/MIO/TSC into solver code appears to be the easiest fix;
- a shared-helper extraction to `common/` is being proposed for logic that is still solver-specific;
- the SSOT path for a physics-semantic change cannot be identified.
