# MIO Package Guidelines

This file supplements the repo-root `AGENTS.md` for work under `htt/mio/`.
All commands below assume the repository root.

## Scope
- `htt/mio/` is the Model-Independent Observatory layer.
- It owns data-facing diagnostics, coherence studies, extraction, tension summaries, decomposition, and certificate-generation helpers.
- MIO reports what is visible in the data without assuming a model. It is not a posterior engine, not a truth-attestation layer, and not a replacement for HTT or TSC ownership.

## Ownership Map
- `coherence`, `extraction`, `tension`, `decomposition`: report-producing analysis families.
- `diagnostics`: caveats and data-quality or coverage diagnostics.
- `interface`: stable builder APIs such as `build_mio_certificate`.
- `bridges`: narrow re-export or explicitly documented cross-package handoff surface.

## Boundary Rules
- Public MIO outputs should terminate in explicit immutable contracts, normally `workspace.contracts.MioCertificate`.
- Never add public fields, kwargs, or schema keys containing `posterior` to MIO contracts or builders. Treat this as a hard boundary, not merely a naming preference.
- Cross-checks with HTT or TSC must remain explicit, one-way, and non-merged. Do not sum, average, or fold MIO scores into HTT lnB, posterior draws, or TSC admissibility results.
- Keep MIO modules data-facing. Model-dependent posterior logic belongs in HTT; physical realizability gates belong in TSC.
- Some MIO-owned bridge logic lives outside `htt/mio/`, notably `htt/htt/PR13AM_te_sign_d1d3_bridge.py`. If touching those files from MIO work, preserve the `__mio_owned__` tag and `mio_` artifact-prefix conventions.

## Change Checklist
Before committing MIO changes, verify:
1. the public contract still reads as model-independent;
2. no posterior-bearing field or alias was introduced indirectly;
3. cross-package comparisons remain explicit and one-way;
4. report-family changes have package-local regression coverage, not only contract tests.

## Testing
Run the narrowest relevant battery first, then widen only as needed.

- Normal MIO work:
  - `venv/bin/python -m pytest htt/mio/tests htt/workspace/contracts/tests -q`
- Contract / G19 / artifact-prefix surfaces:
  - `venv/bin/python -m pytest htt/mio/tests/test_mio_certificate_generator.py -q`
  - `venv/bin/python -m pytest htt/workspace/contracts/tests/test_mio_certificate.py -q`
  - `venv/bin/python -m pytest htt/workspace/contracts/tests/test_g19_enforcement.py -q`
  - `venv/bin/python -m pytest htt/workspace/contracts/tests/test_reg02_artifact_prefix.py -q`
- If a specific report family changes:
  - add or update a package-local regression in `htt/mio/tests/`

## Stop Conditions
Stop and escalate if:
- a proposed output schema wants to expose posterior semantics;
- a comparison helper is drifting toward a merged scalar score;
- a contract change relies only on downstream consumer tests;
- a bridge file outside `htt/mio/` is being edited without preserving explicit MIO ownership markers.
