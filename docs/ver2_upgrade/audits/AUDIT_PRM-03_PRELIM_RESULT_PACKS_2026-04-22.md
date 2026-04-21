# AUDIT_PRM-03_PRELIM_RESULT_PACKS_2026-04-22

## Scope

- packet: `PRM-03-PRELIM-RESULT-PACKS`
- authority: `docs/ver2_upgrade/*`
- mode: preliminary-results mode
- verification style: CoVe + metacognitive audit + equation-to-code consistency + touched-surface tests + exporter/script checks

## Target

Refresh the manifest-backed preliminary result packs and generated figure/export
surfaces from the current BASS preliminary-results state, without reopening the
remaining deeper exactness debt.

In this packet, the load-bearing requirement was:

1. stop exporting Tier-B artifacts through the old Lowell-named runtime path;
2. make the exporter consume the current native preliminary BASS path;
3. surface the new representative family sweep evidence directly inside the
   generated result-pack bundle rather than leaving it as a registry-only side
   channel.

## Key finding

The main blocker was not figure generation itself. It was stale D-lane wiring:

- the exporter still referenced `execute_tier_b_lowell_solver`;
- the generated result packs did not yet carry the committed
  `validation.bass_representative_family_sweep` evidence as a first-class
  artifact;
- Pack `E` therefore underspecified the current preliminary-results ceiling.

## Closure chosen

`PRM-03` closes by:

1. retargeting the exporter to the current native Tier-B runtime entry point;
2. generating a dedicated manifest-backed artifact for the representative
   family sweep evidence;
3. inserting that artifact into result pack `E` alongside the validation
   registry summary;
4. regenerating the manuscript/export/generated figure surfaces and checking
   that they are internally up to date.

This packet does **not** promote new science claims. It refreshes the export
layer so the current bounded preliminary-results state is reflected honestly in
the generated bundles.

## Code changes

- exporter runtime retarget:
  - `scripts/ver2_artifact_export.py` now uses `execute_tier_b_solver`
    instead of the old Lowell-named compatibility entry point;
- new generated artifact:
  - `docs/ver2_upgrade/generated/artifacts/bass_ver2_export_representative_family_sweep.json`
- pack-level integration:
  - result pack `E` now includes both:
    - the validation registry summary
    - the representative family sweep evidence artifact
- figure/export refresh:
  - regenerated `docs/ver2_upgrade/generated/*`
  - regenerated `docs/manuscript/generated/*`
  - regenerated `figures/paper/ver2_generated/*`
  - refreshed `figures/paper/VER2_MANIFEST_INDEX.md`

## Physics / contract audit

- kept:
  - all-11-type domain metadata
  - explicit orthogonal-vs-tilted branch semantics
  - explicit global-tilt vs local-boost separation
  - representative-family preliminary ceiling
- promoted:
  - representative orthogonal family sweep from validation-side evidence into a
    generated result-pack artifact
- refused:
  - any new geometry-identification claim
  - any tilted runtime success claim
  - any non-Type-I exact-propagator promotion

The exporter now states the current contract more faithfully:

- orthogonal `I/V/VII_0/VIII` preliminary runs are executable;
- representative tilted runtime remains an explicit no-claim blocker;
- Pack `E` stays exploratory overall even though it carries one conditional
  BASS artifact inside it.

## Verification

- `venv/bin/python -m py_compile scripts/ver2_artifact_export.py scripts/test_ver2_artifact_export.py`
- `venv/bin/python -m pytest scripts/test_ver2_artifact_export.py -q`
  - result: `9 passed`
- `venv/bin/python scripts/ver2_artifact_export.py`
  - result: generated VER2 figure/export surfaces successfully
- `venv/bin/python scripts/ver2_artifact_export.py --check`
  - result: `VER2 export surfaces are up to date.`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_bass_validation.py --family-sweep-json`
  - result: confirms exported family-sweep evidence points at campaign
    `validation.bass_representative_family_sweep` with explicit no-claim
    conditions

Known warning retained:

- recombination table early-`z` coverage warning

## Carry-forward

- representative tilted runtime remains blocked and therefore exported only as
  an explicit no-claim condition;
- non-Type-I exact propagator remains unresolved;
- HTT/MIO/TSC still need a cleaner pack-level handoff path if they are to
  consume these preliminary result packs without local adapter glue.

## Verdict

`PRM-03` is closed for preliminary-results mode.

The generated result packs and figure/export surfaces now reflect the committed
preliminary BASS state instead of an older runtime/export wiring state. Pack
`E` is now honest about what exists:

- executable representative orthogonal family sweep evidence is present;
- tilted runtime blockers remain explicit;
- the overall pack remains exploratory rather than a promoted geometry claim.
