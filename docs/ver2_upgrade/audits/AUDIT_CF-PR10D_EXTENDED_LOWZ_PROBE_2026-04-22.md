# AUDIT_CF-PR10D_EXTENDED_LOWZ_PROBE_2026-04-22

## Scope

- `htt/bass/background/evolution.py`
- `htt/bass/species/barotropic_closures.py`
- `htt/bass/runtime/ver2_execution.py`
- `htt/bass/forward/ver2_solver_output.py`
- `htt/bass/runtime/test_ver2_tier_b_execution.py`
- `htt/bass/validation/ver2_campaign_evidence.py`
- `htt/bass/validation/test_ver2_campaign_evidence.py`
- `htt/scripts/ver2_bass_validation.py`

## DAG node

- current node: baseline / limit validation + local patch on the Type-I extended low-z reionization probe
- prerequisite status:
  - native Tier-B runtime: closed
  - live low-z probe availability: closed after the species-backed background / physical-eta remap patch
  - shipped BF-05 gate: remains unchanged and bounded

## Trigger

The previous no-claim repair only proved that the runtime could expose a `z=8`
probe. Plot-backed adversarial review showed that this was too narrow to treat
as a meaningful late-time validation surface. The next minimal step was to
promote a bounded extended low-z probe, not a full reionization-science claim.

## Key findings

1. The original runtime/background mismatch was real: the old background monitor
   solved on an internal `eta(a)` grid unrelated to the requested runtime
   `eta_final_mpc`.
2. The species-backed closure plus physical-`eta` remap closes that mismatch and
   lets the Type-I runtime reach `z=4` stably with `BDF`.
3. Plot evidence shows the current claim must stay narrow:
   - the extended run exposes live low-z source metadata;
   - reionization on/off changes the low-z carrier;
   - this still does **not** promote direction-resolved reionization
     microphysics or non-Type-I exact propagation.

## Plots used as evidence

- `/tmp/ver2_runtime_reionization_plots/runtime_reionization_gpi_lowz.png`
- `/tmp/ver2_runtime_reionization_plots/runtime_reionization_resolution.png`
- `/tmp/ver2_runtime_reionization_plots/summary.json`

### Plot readout

- `runtime_reionization_gpi_lowz.png`
  - surviving claim: the extended Type-I runtime does expose a live low-z
    visibility-weighted polter carrier, and reionization-on is larger than
    reionization-off at the declared probe.
  - rejected claim: this plot does **not** justify a full late-time
    reionization-window science promotion by itself.
- `runtime_reionization_resolution.png`
  - surviving claim: the low-z probe survives a coarse/fine mutation.
  - narrowed claim: stability is sufficient for a bounded probe campaign, not
    yet for a broad microphysics claim.

## Applied fix

- Added a bounded executable validation surface:
  - `validation.bass_type_i_extended_reionization_probe`
- This surface checks:
  - extended runtime reaches the declared low-z endpoint,
  - low-z probe is available in both reionization modes,
  - claim-status / mode metadata stay distinct,
  - reionization increases low-z visibility and `|g Π|`,
  - exact Type-I propagator metadata stays attached.

## Verifications

- `venv/bin/python -m py_compile htt/bass/validation/ver2_campaign_evidence.py htt/bass/validation/__init__.py htt/bass/validation/test_ver2_campaign_evidence.py htt/bass/runtime/test_ver2_tier_b_execution.py htt/scripts/ver2_bass_validation.py`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_bass_validation.py --check`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_bass_validation.py --reion-probe-check`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/validation/test_ver2_campaign_evidence.py::test_type_i_reionization_probe_evidence_passes_for_extended_low_z_runtime htt/bass/validation/test_ver2_campaign_evidence.py::test_type_i_reionization_probe_payload_is_json_ready htt/bass/runtime/test_ver2_tier_b_execution.py::test_execute_tier_b_solver_can_reach_low_z_reionization_probe_with_extended_eta_domain -q`

## Remaining no-claim conditions

- `tier_a_validation_bridge_only`
- `non_type_i_exact_propagator_missing`
- `homogeneous_reionization_only`
- `direction_resolved_reionization_microphysics_missing`

## Final audit verdict

- status: partial pass
- fixed now:
  - Type-I extended low-z probe is executable, machine-readable, and separately
    validated from the shipped BF-05 gate.
- still not fixed:
  - full late-time reionization science promotion
  - direction-resolved reionization microphysics
  - non-Type-I exact PR-15 closure
