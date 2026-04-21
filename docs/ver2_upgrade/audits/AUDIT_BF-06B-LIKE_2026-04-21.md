# AUDIT_BF-06B-LIKE_2026-04-21

## Scope

- `htt/bass/observer/__init__.py`
- `htt/bass/likelihood/__init__.py`
- `htt/bass/likelihood/live_binding.py`
- `htt/bass/inference/__init__.py`
- `htt/bass/inference/live_binding.py`
- `htt/bass/inference/__main__.py`
- `htt/bass/test_ver2_public_surface.py`
- related BF-06 tests
- related VER2 ledgers/audit docs

Related load-bearing repair:

- `htt/bass/validation/__init__.py` lazy export to break a live-path import cycle discovered during BF-06 verification

## Intent

Retarget `bass/observer`, `bass/likelihood`, and `bass/inference` onto the completed BASS physics path and fence residual surrogate routes so they no longer coexist ambiguously with the live native Tier-B path.

## RE2 Reconstruction

### Target

1. Package-root observer surfaces must expose production boost/mixing helpers only.
2. Likelihood scaffolding must bind to live `SolverCoreOutput`, not only to heuristic decomposition dictionaries.
3. Inference must expose at least one shipped live BASS binding instead of remaining a surrogate-only CLI.

### Divergence

1. Leave package roots unchanged and only document that the old routes are surrogate.
2. Remove all legacy/surrogate helper modules entirely.
3. Keep legacy submodules for audited regression work, but narrow package-root exports and add explicit live BASS bindings.

### Convergence

Option 3 was selected.

- Option 1 would leave the public API ambiguous.
- Option 2 would discard useful audited regression scaffolding.
- Option 3 keeps regression coverage while making the canonical route explicit.

## Findings

### P0 public-surface ambiguity

- `bass.observer` still re-exported diagnostic-only composition/discriminator symbols at package root.
- `bass.likelihood` still re-exported heuristic FB-7/8 constructors at package root as if they were the canonical BASS API.
- `bass.inference.__main__` remained surrogate-only.

### P1 missing live binding

- No BASS-owned likelihood helper consumed live `SolverCoreOutput`.
- No BASS-owned inference adapter consumed the shipped Type-I native route.

### P1 import-cycle blocker

- BF-06 verification exposed a package-load cycle:
  `bass.inference.live_binding -> bass.background.einstein_bianchi -> bass.validation -> bass.validation.ver2_campaign_evidence -> bass.background.einstein_bianchi`.
- Fix: `bass.validation.__init__` now uses lazy exports.

## Implemented Surfaces

- `bass.likelihood.build_live_htt_decomposition_from_solver_output`
- `bass.likelihood.build_cosmological_frame_likelihood_from_solver_output`
- `bass.likelihood.build_observer_frame_likelihood_from_solver_output`
- `bass.inference.LiveObserverBoostProblem`
- `bass.inference.build_live_observer_boost_problem`
- `bass.inference.build_type_i_native_validation_problem`
- `bass.inference.run_type_i_native_validation_posterior`
- CLI dataset kind:
  - `type_i_native_validation`

## Contract / Mapping Audit

| Claim | Executable path | Status |
|---|---|---|
| observer root is production-only | `bass.observer.__all__` narrowed to boost + aberration/mixing helpers | passed |
| likelihood root prefers live BASS bindings | `bass.likelihood.__all__` narrowed to `SolverCoreOutput`-bound builders | passed |
| live likelihood binds to completed BASS path | `SolverCoreOutput -> anisotropic_covariance -> live decomposition -> CosmologicalFrameLikelihood` | passed |
| inference is no longer surrogate-only | `type_i_native_validation -> execute_tier_b_solver -> ObservableVector -> ObserverFrameLikelihood -> run_posterior` | passed |
| surrogate routes remain available but fenced | legacy FB-7/8 submodules remain importable only via explicit submodule paths | passed |

## Verification

- `venv/bin/python -m py_compile htt/bass/validation/__init__.py htt/bass/likelihood/live_binding.py htt/bass/inference/live_binding.py htt/bass/inference/__main__.py`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/test_ver2_public_surface.py htt/bass/likelihood/test_ver2_live_binding.py -q`
  - `6 passed, 1 warning`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/inference/test_ver2_live_binding.py -q`
  - `3 passed, 1 warning`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/observer/test_fb81_observer_boost_skeleton.py htt/bass/observer/test_fb83_observer_adapters_skeleton.py htt/bass/observer/test_fb84_composition_skeleton.py htt/bass/observer/test_fb85_discriminator_skeleton.py -q`
  - `132 passed`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/likelihood/test_fb74_cosmological_frame_skeleton.py htt/bass/likelihood/test_fb86_observer_frame_adapter_skeleton.py htt/bass/likelihood/test_fb75_planck2018_flrw_match_skeleton.py htt/bass/test_ver2_public_surface.py -q`
  - `77 passed`

Known warning unchanged:

- recombination-table early-`z` coverage warning from `bass.species.registry`

## Carry-Forward

1. BF-06 closes the binding/fencing gap, not the deeper physics debt:
   non-Type-I exact propagators, full BiPoSH inversion, and direction-resolved microphysics remain open.
2. The new live inference path is intentionally bounded to the shipped Type-I native route and remains a diagnostic BASS-side observer-boost posterior scaffold, not an HTT-owned model-selection surface.
3. Legacy cleanup is now optional follow-up only; the BASS-first packet sequence is closed.
