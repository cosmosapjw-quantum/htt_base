# HTT-B Execution Prompt

Read first:

1. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_04_HTT_PARALLEL.md`
2. `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
3. `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
4. `docs/ver2_upgrade/BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md` sections `3.8`, `PR-HTT-09`, and `PR-HTT-11`

Goal:

- continue `HTT-B` by turning the current local/global discrimination shell into a bounded conditional pre-inference identifiability audit;
- keep the output as `DiscriminationMatrix`, not posterior odds;
- let Result Pack `B` reflect the calibrated HTT discrimination surface when current O-lane morphology support is sufficient.

Write scope:

- `htt/htt/htt/infer/local_global_discrimination.py`
- selected `htt/htt/htt/infer/ver2_directional_shell.py`
- selected `htt/htt/tests/test_ver2_local_global_discrimination.py`
- selected `htt/htt/tests/test_ver2_directional_shell.py`
- selected `scripts/ver2_artifact_export.py`
- selected `scripts/test_ver2_artifact_export.py`
- generated `docs/ver2_upgrade/generated/result_pack_B_local_global.*` and `figures/paper/ver2_generated/fig_ver2b_local_global_discrimination_matrix.*` only if exporter rerun changes them

Required closure for this slice:

1. Replace fixed overlap stubs with observable-aware whitened overlaps.
2. Use current O-lane support only:
   - `SkySupport.selection_mode`
   - `mock_coverage_status`
   - atlas/template presence
   - basis-reduced morphology support from `BiPoSH`, `EE`, `BB`, and covariance metadata
3. Allow `conditional` only for the local-boost/global-tilt pair when the observable support and overlap threshold justify it.
4. Keep geometry/systematic pairs `exploratory` or `blocked` unless the current morphology support genuinely warrants more.
5. Preserve the hard rule that this is a pre-inference audit, not posterior odds or family detection.

Guardrails:

- do not widen into `HTT-C`;
- do not merge MIO semantics or TSC caveats into HTT claim ownership;
- do not promote basis-reduced morphology into validated BiPoSH or geometry detection;
- do not treat the discrimination matrix as a substitute for null/PPC/LOOCV evidence;
- if exporter tests fail, distinguish stale assertions from real HTT regressions before editing runtime code.

Verification:

- `venv/bin/python -m py_compile htt/htt/htt/infer/local_global_discrimination.py htt/htt/htt/infer/ver2_directional_shell.py htt/htt/htt/infer/__init__.py htt/htt/tests/test_ver2_local_global_discrimination.py htt/htt/tests/test_ver2_directional_shell.py scripts/ver2_artifact_export.py scripts/test_ver2_artifact_export.py`
- `venv/bin/python -m pytest htt/htt/tests/test_ver2_local_global_discrimination.py htt/htt/tests/test_ver2_directional_shell.py -q`
- `venv/bin/python -m pytest htt/htt/tests -q`
- `venv/bin/python -m pytest scripts/test_ver2_artifact_export.py -q`
- if exporter surfaces change: `venv/bin/python scripts/ver2_artifact_export.py` and `venv/bin/python scripts/ver2_artifact_export.py --check`

Success condition:

- HTT discrimination is conditional only where the current low-`ell` morphology support actually breaks the local/global degeneracy,
- HTT tests stay green,
- exporter/result-pack `B` surfaces match the calibrated HTT state,
- remaining debt is clearly deferred to `HTT-C` or later morphology/null validation work.
