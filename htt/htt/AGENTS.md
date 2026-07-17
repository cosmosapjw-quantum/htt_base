# HTT Package Guidelines

This file supplements the repo-root `AGENTS.md` for work under `htt/htt/`.
All commands below assume the repository root.

## Scope
- `htt/htt/` is the model-dependent observation and inference layer.
- Keep likelihoods, posterior summaries, matched-complexity logic, structured null families, survey-facing integration, tilt-history handling, and figure assembly here.
- HTT may consume upstream artifacts, but it does not own solver physics, MIO certificates, or TSC realizability semantics.

## Ownership Map
- `core`: pipeline logic, bounds, constants, diagnostics, and HTT-local SSOT helpers.
- `infer`: model-dependent inference utilities and comparison logic.
- `nulls`: structured null families and null runners.
- `bridge`, `integration`, `tilt`: bridge metadata and cross-package handoff helpers.
- `figures`: reproducible figure generation.
- Tests and fixtures live under `htt/htt/tests/`.

## Boundary Rules
- HTT is model-dependent. Do not turn MIO certificates or TSC diagnostics into HTT likelihood terms, posterior inputs, or merged scalar scores.
- Keep direct `tsc` imports out of HTT production code. TSC-facing comparisons belong in `tsc.integration` or another explicit sibling bridge.
- Preserve production gates around `PreferredAxis.production_allowed`, PR13AH four-summary outputs, and PR13AM handoff behavior. These are contracts, not convenience flags.
- `htt/htt/PR13AM_te_sign_d1d3_bridge.py` is physically located in HTT but semantically MIO-owned. If touched, preserve `__mio_owned__`, the `mio_` artifact-prefix contract, and the production-allowed gate.
- Prefer fixtures and explicit env/config plumbing over hard-coded output paths when changing figures or pipeline wiring.

## Change Checklist
Before committing HTT changes, verify:
1. no MIO/TSC quantity has been silently promoted into an HTT posterior input;
2. production gates still fail closed;
3. bridge code did not absorb package ownership accidentally;
4. figure/output changes remain reproducible from explicit config or fixtures.

## Testing
Run the narrowest relevant battery first, then widen only as needed.

- Normal HTT changes:
  - `venv/bin/python -m pytest htt/htt/tests -q`
- Protected surfaces:
  - `venv/bin/python -m pytest htt/htt/tests/test_PR13AH.py -q`
  - `venv/bin/python -m pytest htt/htt/tests/test_PR13AJ_gate.py -q`
  - `venv/bin/python -m pytest htt/htt/tests/test_PR13AM_production_gate.py -q`
  - `venv/bin/python -m pytest htt/htt/tests/test_figures_smoke.py -q`
- Cross-package contract or MIO-facing bridge change:
  - run the relevant `htt/mio/tests` and/or `htt/workspace/contracts/tests` battery too

## Stop Conditions
Stop and write a decision note if:
- an HTT change seems to require direct TSC production imports;
- an MIO certificate field is being reused as if it were a posterior input;
- a bridge file located in HTT needs ownership semantics that contradict its package location;
- a figure/output change cannot be reproduced without a hidden local path.
