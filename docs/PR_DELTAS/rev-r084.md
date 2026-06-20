# REV-R084 - Theorem extension registry and synthetic verification

## Scope

- Owner: COMMON for registry/assets; MIO for dynamic-budget and bound-pushforward diagnostics; BASS for kinetic/geometry synthetic theorem helpers.
- Plan source: `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`.
- Canonical PR DAG status remains complete at `62/62`; this supplemental delta tracks revision-slice task `REV-R084`.
- Claim ceiling: `diagnostic_only`.

## Artifact Metadata

- owner: COMMON
- implementation_scope: `common`
- claim_tier: `diagnostic_only`
- transfer_source: `none`
- sky_support_status: `not_directional`
- covariance_status: `synthetic_only`
- null_mock_status: `synthetic_only`
- production_status: `diagnostic_only`
- native_solver_result: false
- family_identification: false
- production_claim_allowed: false
- observation_claim_allowed: false
- caveats:
  - synthetic/manufactured verification only
  - diagnostic-only theorem-obligation registry
  - not HTT evidence
  - not a MIO certificate
  - not native solver validation
  - not geometry or family identification
- config_hash: `89ee66075b730891126741eb2215e54fefd8a476797b795860a7744d0f0c4e4a`
- generated_on: `2026-06-20T02:40:38+00:00`
- input_hashes:
  - `scripts/generate_theorem_extension_assets.py:b9203657f8b5e66c99e25af60860428d1b07eac87e7e2815a82e487001f86e75`
  - `htt/src/common/theorem_registry.py:a83a86c952fe2bf4bda78a8fb0868231b6c302a76f3e7a4679b3bdd4fdc2e43d`
  - `htt/mio/formalism/dynamic_budget.py:11132baea55ce3d879a03ded84a11cce42252a893f51bcf2d5a346c82ea168e4`
  - `htt/mio/formalism/bound_pushforward.py:250da9000a61bb1210b6aa63662988612a40304f960e55f21bb53f2703a9a76a`
  - `htt/bass/kinetic/boltzmann_memory.py:65900d82579773ba3935dd222e9db9191ffe357f988e9b7ac1149342a2874ce1`
  - `htt/bass/kinetic/tight_coupling_bounds.py:b70879061d9d0f748121ca5e9c0816d43b0e19e6391e16cd75271e59f3ae99f4`
  - `htt/bass/kinetic/visibility_rigidity.py:f33eb3f0ef0e02e1b43168008486433f261802dc1986039837db3e8ff9a0475a`
  - `htt/bass/geometry/egs_rigidity.py:65ed1bbc7bd1813755c21fb84e8f7decaa9988e52e81607e8c82286e5651c5b0`
  - `tests/contracts/test_theorem_registry.py:45265116be36217e387dd59d0e120fc63163e03d5b394d343b1058216019492b`
  - `tests/mio/test_dynamic_budget.py:cda433d79e86e4217e360ee89010e0bb9d017fd76e788dbfb02c7cc3e5cbd5b9`
  - `tests/bass/test_boltzmann_memory_bounds.py:b57b3bb7a98991aa92427f787046c5a2037afceed09ff4f4de1c6c93dc95832f`
  - `tests/bass/test_egs_rigidity_theorems.py:ca16d0a03cebf4d870a95b936f4b7d77f037744d0f947d16c6d48f02aac0e424`
- generated_assets:
  - `docs/generated/theorem_extension_registry.json` (`sha256:04481f4a0e633c4347b57e79f60544475103be283c70aab6a0cace1dedd5b1f9`)
  - `docs/generated/theorem_extension_registry.md` (`sha256:ea35e06a700e33cb67139f72f55b5ad74ff665ea242b4bae3b7d5f9d23c0dcdb`)
- generating_command: `/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python scripts/generate_theorem_extension_assets.py --write`
- git_commit_or_worktree_state: `430926a+dirty`

## Evidence Read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-physics-math-audit/SKILL.md`
- `.agents/skills/htt-xqpi-fg-formalism/SKILL.md`
- `.agents/skills/htt-transfer-provenance/SKILL.md`
- `.agents/skills/htt-family-identification-gate/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`
- `scripts/codex_harness/generate_theorem_to_test_map.py`
- `tests/contracts/test_theorem_to_test_map.py`
- `htt/mio/formalism/budget_spec.py`
- `htt/mio/formalism/exceedance.py`
- `htt/test_packaging_imports.py`

## Web/Doc Checks

- WEB_CHECK_STATUS: done.
- Python dataclasses documentation checked for generated record semantics: <https://docs.python.org/3/library/dataclasses.html>.
- Python JSON documentation checked for `sort_keys`, `allow_nan`, and deterministic serialization behavior: <https://docs.python.org/3/library/json.html>.
- NumPy `trapezoid` documentation checked for current composite trapezoid semantics: <https://numpy.org/doc/stable/reference/generated/numpy.trapezoid.html>.

## Divergence And Review

- code cartographer:
  - Steelman: add a narrow `common.theorem_registry`, MIO formalism helpers, new BASS `kinetic` and `geometry` packages with `__init__.py`, deterministic generator, and package import smoke.
  - Attack: do not extend legacy TSC theorem maps; avoid copying old MES formulas into active theorem claims.
- harness engineer:
  - Steelman: generator must own JSON and Markdown from one payload and support `--check` byte comparison.
  - Attack: broad directory staging is risky; commit exact files only and run `git status --short --untracked-files=all`.
- physics/statistics auditor:
  - Steelman: P0 primitives are useful synthetic tests for positivity, denominator matching, samplewise domination, finite cover bounds, boost orbits, slope degeneracy, and visibility no-go behavior.
  - Attack: split proof status from implementation-test status; synthetic tests do not prove observational theorem validity.
- claim-gate reviewer:
  - Steelman: allowed statuses are analytic, convention-conditional, program-theorem, and observational-blocked.
  - Attack: forbid observational theorem claims, native solver validation, geometry/family interpretation, MIO posterior/evidence semantics, and theorem figures in this PR.
- regression tester:
  - Steelman: protect package imports, MIO Q/F/Pi semantics, transfer provenance, native adapter stubs, generator drift, and focused tests.
  - Attack: generated assets can become stale if only `--write` is tested.

Subagents closed: yes. Post-implementation review ran two rounds:

- Round 1 found under-gated S5/B4/G2 permissions and missing Markdown provenance/hash metadata.
- Round 2 found registry SSoT drift for the new B4/G2 kill switches and stale delta metadata.
- Final re-review found no blockers.

## Implemented Changes

- Added `common.theorem_registry`:
  - `TheoremEntry`, `TheoremRegistry`, and default registry for S1/S3/S4/S5/G2/G5/B4.
  - Separate `status`, `proof_status`, `implementation_test_status`, and `claim_status`.
  - Required kill switches and blocked observational-use map.
- Added MIO synthetic theorem helpers:
  - `dynamic_comparison_budget_barrier`,
  - `bound_to_pi_domination`,
  - `finite_cover_union_bound`.
- Added BASS synthetic theorem helpers:
  - `exponential_memory_bound`,
  - `angular_kl_multipole_bound`,
  - `visibility_cancellation_no_go`,
  - `boosted_radiation_orbit`,
  - `classify_slope_degeneracy`,
  - `almost_egs_promotion_gate`,
  - `bianchi_i_exact_flow_gate`.
- Added deterministic generator:
  - `scripts/generate_theorem_extension_assets.py --write`
  - `scripts/generate_theorem_extension_assets.py --check`
- Added generated assets:
  - `docs/generated/theorem_extension_registry.json`
  - `docs/generated/theorem_extension_registry.md`
- Updated `mio.formalism` package exports and package import smoke.
- Post-review hardening:
  - S5 physical-cover use now fails closed by default and requires explicit metric/mask/Lipschitz `bound` statuses.
  - B4 source-upper-bound use now requires source rank, sign/phase coherence, positive collision-gap provenance, positive kernel-floor provenance, and mask-support provenance.
  - G2 data-facing residual use now requires systematics, mask, null, raw-data provenance, covariance, PPC/LOOCV, prior sensitivity, transfer provenance, and native-atlas statuses all bound.
  - Registry/generated assets now list the B4/G2 active provenance kill switches.
  - Markdown generated artifact now carries `input_hashes`, `generated_on`, `generating_command`, and git state.

## Validation

| Command | Result | Notes |
|---|---:|---|
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_theorem_registry.py tests/mio/test_dynamic_budget.py tests/bass/test_boltzmann_memory_bounds.py tests/bass/test_egs_rigidity_theorems.py` before implementation | FAIL | Red phase: `20 failed`; missing registry, generator, MIO helpers, BASS kinetic/geometry packages, and generated assets. |
| `venv/bin/python -B scripts/generate_theorem_extension_assets.py --write` | PASS | Wrote JSON and Markdown generated assets. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_theorem_registry.py tests/mio/test_dynamic_budget.py tests/bass/test_boltzmann_memory_bounds.py tests/bass/test_egs_rigidity_theorems.py` | PASS | Final focused REV-R084 suite: `24 passed`. |
| `venv/bin/python -B scripts/generate_theorem_extension_assets.py --check` | PASS | Generated assets are byte-current. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q htt/test_packaging_imports.py tests/mio/test_budget_spec.py tests/mio/test_exceedance.py tests/bass/test_external_transfer_registry.py tests/bass/test_native_adapter_stub.py` | PASS | `66 passed`; package imports, MIO semantics, transfer provenance, native stub regressions. |
| `venv/bin/python -B scripts/check_claim_language.py --dry-run ...REV-R084 files...` | PASS | No forbidden claim language detected. |
| `venv/bin/python -B -m py_compile ...REV-R084 files...` | PASS | Touched Python files compile. |
| `venv/bin/python -B -m pytest -m smoke -q` | PASS | `6 passed, 7612 deselected`; smoke suite. |
| `venv/bin/python -B -m pytest --collect-only -q` | PASS | `7559/7618 tests collected (59 deselected)`. |
| `venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | PASS | `OK: 62 PRs, DAG valid`. |
| `venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` | PASS | Completed `62/62 = 100.0%`; dependency-weighted completion `100.0%`; unblocked next `none`. |

## Claim-Tier Impact

REV-R084 creates theorem-obligation and synthetic/manufactured verification artifacts only. It creates no observational theorem claim, no HTT evidence term, no MIO certificate, no posterior odds, no native solver result, no morphology compatibility claim, and no Bianchi geometry/family-identification support.

Residual blockers:

- observational theorem use remains blocked until raw data provenance, masks/randoms, covariance, matched nulls, PPC/LOOCV, prior sensitivity, transfer provenance, and native atlas gates are bound;
- S1 remains density-fixture-only without a KL-to-temperature bridge;
- S3 requires same channel/operator/frame budget metadata;
- S4 requires samplewise domination and cannot imply truth probability;
- S5 physical-cover use requires metric, mask/selection, and Lipschitz provenance;
- G2/G5/B4 remain synthetic no-go/gate diagnostics, not source or family classification.
