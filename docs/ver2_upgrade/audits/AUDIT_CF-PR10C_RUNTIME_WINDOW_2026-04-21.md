# AUDIT_CF-PR10C_RUNTIME_WINDOW_2026-04-21

## Scope
- `htt/bass/forward/ver2_solver_output.py`
- `htt/bass/validation/ver2_campaign_evidence.py`
- `htt/workspace/contracts/validation_registry.py`
- related tests only

## Finding
- The shipped Type-I native runtime keeps `visibility_reionization_mode="tanh"` but does not evolve far enough in scale factor to cover the late-time low-`z` reionization source window.
- Synthetic late-time probes can show the expected low-`z` `gΠ` bump, but that support does not exist on the shipped runtime domain.
- Therefore the correct repair is a no-claim honesty guard, not a fake runtime reionization validation pass.

## Applied repair
- Added explicit metadata:
  - `source_builder_low_z_probe_status`
  - `reionization_source_claim_status`
- Added executable BF-05 check:
  - `tier_b_runtime_explicitly_flags_missing_late_time_reionization_window`
- Added `late_time_reionization_window_missing` to theorem/campaign/null/runbook no-claim conditions.

## Result
- The shipped runtime now records the missing late-time reionization window as an explicit limitation.
- Validation remains `pass` for the bounded Type-I runtime bridge because the pass condition now includes honesty about the missing window rather than hiding it.
- No new physics claim was promoted.
