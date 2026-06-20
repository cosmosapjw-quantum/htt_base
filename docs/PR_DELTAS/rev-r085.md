# REV-R085 - Theorem appendix artifacts

## Scope

- Owner: COMMON for figure generation, manifests, source JSON, and manuscript snippet; source semantics remain theorem-helper-owned by BASS or MIO as recorded in each source JSON.
- Plan source: `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`.
- Canonical PR DAG status remains complete at `62/62`; this supplemental delta tracks revision-slice task `REV-R085`.
- Claim ceiling: `diagnostic_only`.

## Artifact Metadata

- owner: COMMON
- implementation_scope: `common`
- claim_tier: `diagnostic_only`
- transfer_source: `none`
- sky_support_status: `not_directional`
- covariance_status: `synthetic_manufactured_only`
- null_mock_status: `synthetic_manufactured_only`
- production_status: `diagnostic_only`
- artifact_mode: `paper_appendix_conditioned`
- allowed_use: `paper_appendix`
- native_solver_result: false
- family_identification: false
- production_claim_allowed: false
- observation_claim_allowed: false
- caveats:
  - synthetic/manufactured input mode only
  - appendix-only diagnostic figure
  - not HTT evidence
  - not a MIO certificate
  - not native solver validation
  - not geometry or family identification
- registry_config_hash: `c617a51f5028461257e8a60ee3abbae504b0cb3825dd4c2f04907fc5f80a8a46`
- generated_on: `2026-06-20T02:50:07+00:00`
- generating_command: `/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python scripts/generate_theorem_extension_assets.py --write`
- git_commit_or_worktree_state: `7b3ded5+dirty`

## Generated Assets

| Asset | SHA256 |
|---|---|
| `docs/generated/theorem_extension_registry.json` | `e9c442d3d3fc2bcb3e49c9390e68dd30600e605b3a83f8296df699f98f7fd232` |
| `docs/generated/theorem_extension_registry.md` | `067971fd3d7433dba2de57ce7a6d61640d6145635fd4d82c2b0a6c0e634957d2` |
| `docs/manuscript/generated/theorem_extension_appendix_figures.tex` | `308ac808adce7e89de15b075e89a22adf7ad0b1d1fc570db2d42901fd10501f2` |
| `figures/current/fig_theorem_angular_kl_bound.png` | `5a896cb480eb0534d57a6a966075b2c3d509540264aebc04aa0991cf0336bf35` |
| `figures/current/fig_theorem_angular_kl_bound.source.json` | `040284cba1723376cbecbf6e854a00126bc5bdaf61e24879bd2303ce368765e4` |
| `figures/current/fig_theorem_angular_kl_bound.manifest.json` | `16f379cb6dd3c48e0353900e2a97ff2f05fe163e9385c381bef9c4fc91826cde` |
| `figures/current/fig_theorem_dynamic_budget_barrier.png` | `8ea9c2802bf0595f2a88d42d0710de124dabe642174eb1987caa211290dae3c6` |
| `figures/current/fig_theorem_dynamic_budget_barrier.source.json` | `0cb17c444767c72cd6c21d5cedac229d1fff6945a2f75404e6202d388f453481` |
| `figures/current/fig_theorem_dynamic_budget_barrier.manifest.json` | `5cec35d044e1c8788091afebc20bd516251d57fcf519a152caf7521a71f8145b` |
| `figures/current/fig_theorem_boosted_radiation_orbit.png` | `2b8c4f17d2c5bd36d76a5670d020b0b38ab359f74583612ba3deb194b24b7ebc` |
| `figures/current/fig_theorem_boosted_radiation_orbit.source.json` | `fb9a8652189db131492a7a384e2675540717835af487497a95d41e01de6ea5a4` |
| `figures/current/fig_theorem_boosted_radiation_orbit.manifest.json` | `067d6a9203504aa8e1a646eaf75f96ad4b5240d3ccabb20e1b409ccc5065ca1c` |
| `figures/current/fig_theorem_slope_degeneracy.png` | `20f4cd1395467e3ba89f70b3636d8f3669fa85de56fa551dbb1c7f24d23ae6a4` |
| `figures/current/fig_theorem_slope_degeneracy.source.json` | `1326a8d1235640c97540bb9c1e10475c86ba51149a039ffecc23ae61f84f724e` |
| `figures/current/fig_theorem_slope_degeneracy.manifest.json` | `c9ea011aa8417cff310f2c51b3a2e523b754ab5c2f7b6857cb24041ea5d910ec` |
| `figures/current/fig_theorem_visibility_cancellation.png` | `ce2d7d0ebdb61a69387a807c65ef167e7180eee41b1e2920fcd1405f08380085` |
| `figures/current/fig_theorem_visibility_cancellation.source.json` | `b4541acf953bbcebc2cc2c07f179659894b2bfda503fc28ac507a42319fc5fea` |
| `figures/current/fig_theorem_visibility_cancellation.manifest.json` | `4b25707fd257864317be9d0824315375cb7d29ee586505749f9353405a7a53c9` |

## Evidence Read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-plot-provenance/SKILL.md`
- `.agents/skills/htt-manuscript-figure-audit/SKILL.md`
- `.agents/skills/htt-latex-paper-build/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`
- `scripts/generate_theorem_extension_assets.py`
- `scripts/generate_revision_experiment_assets.py`
- `scripts/make_current_manuscript_figures.py`
- `tests/contracts/test_revision_experiment_assets.py`
- `tests/contracts/test_theorem_registry.py`
- `htt/src/common/artifact_manifest.py`
- `htt/src/common/theorem_registry.py`
- `htt/bass/kinetic/tight_coupling_bounds.py`
- `htt/mio/formalism/dynamic_budget.py`
- `htt/bass/geometry/egs_rigidity.py`
- `htt/bass/kinetic/visibility_rigidity.py`

## Web/Doc Checks

- WEB_CHECK_STATUS: done.
- Matplotlib `savefig` official documentation checked for current PNG export controls, `metadata`, `dpi`, `format`, and `bbox_inches` behavior: <https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html>.

## Divergence And Review

- code cartographer:
  - Steelman: extend `scripts/generate_theorem_extension_assets.py` so registry JSON/Markdown and theorem appendix figures share one payload and one `--check` gate.
  - Attack: hand-authored PNG/TeX or test-generated figures would break the repo rule that figures require generated provenance and manifests.
- harness engineer:
  - Steelman: `--check` must fail if any PNG, source JSON, sidecar manifest, or TeX snippet is missing or stale.
  - Attack: `make_current_manuscript_figures.py --check` has unrelated existing drift and must not be used as REV-R085’s green gate.
- physics/statistics auditor:
  - Steelman: the five figures can make theorem-obligation surfaces readable if they show only synthetic/manufactured helper outputs and fail-closed gates.
  - Attack: observed maps, p-values, calibrated null rates, transfer curves, native-solver phrasing, or Bianchi-family labels would be blockers.
- claim-gate reviewer:
  - Steelman: appendix-only diagnostic theorem-obligation figures are safe if the manifests forbid HTT evidence, MIO certificate, native solver validation, and geometry/family use.
  - Attack: paper-main promotion, source-discrimination language, family ranking, or treating Pi/Q/F/G-like surfaces as truth/evidence must stay blocked.
- regression tester:
  - Steelman: tests should assert PNG magic bytes, source JSON, manifest validation, appendix lane, claim fields, and generator check mode.
  - Attack: registry-only `--check` would still pass while appendix assets are absent.

Subagents closed: yes. Post-implementation review:

- Claim-gate reviewer: no blockers. Confirmed appendix-only lane, source/manifest provenance, no paper-main promotion, and preserved COMMON vs BASS/MIO helper ownership split.
- Physics/statistics auditor: no blockers. Confirmed S1/S3/G2/G5/B4 surfaces are synthetic/manufactured diagnostics with blocked observational/native/family use. Residual risk: downstream consumers must keep source JSON paired with manifest because source JSON carries the strongest fail-closed booleans.
- Regression tester: no findings returned before shutdown after two long wait cycles. Local regression evidence is recorded below.

## Implemented Changes

- Extended `scripts/generate_theorem_extension_assets.py`:
  - robust repo import bootstrap for plain `python` script execution;
  - Matplotlib Agg theorem figure generation;
  - five appendix-only figure specs for S1/S3/G2/G5/B4;
  - source JSON generation beside each PNG;
  - sidecar manifest generation with `validate_manifest_payload`;
  - appendix TeX snippet generation;
  - canonical `--check` coverage for registry JSON/MD plus all figure/source/manifest/TeX assets.
- Added `tests/contracts/test_theorem_extension_assets.py`:
  - generator `--check` contract;
  - PNG/source JSON/manifest existence and metadata checks;
  - `paper_appendix_conditioned` / `paper_appendix` lane checks;
  - manifest validation;
  - appendix TeX lane checks.
- Regenerated theorem registry JSON/Markdown because the generator source hash changed.

## Validation

| Command | Result | Notes |
|---|---:|---|
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_theorem_extension_assets.py` before implementation | FAIL | Red phase: `2 failed, 1 passed`; missing appendix TeX and theorem figure artifacts. |
| `venv/bin/python -B scripts/generate_theorem_extension_assets.py --write` | PASS | Wrote registry JSON/Markdown and generated five PNG/source/manifest sets plus appendix TeX. |
| `venv/bin/python -B scripts/generate_theorem_extension_assets.py --check` | PASS | Theorem extension assets are current. |
| `python scripts/generate_theorem_extension_assets.py --check` | PASS | Plain Python import bootstrap works. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_theorem_registry.py tests/contracts/test_theorem_extension_assets.py tests/contracts/test_artifact_manifest.py tests/contracts/test_revision_experiment_assets.py` | PASS | `28 passed`; registry, theorem assets, manifest validation, and adjacent revision asset contracts. |
| `venv/bin/python -B scripts/check_claim_language.py --dry-run ...REV-R085 text/json surfaces...` | PASS | No forbidden claim language detected. |
| `venv/bin/python -B .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py ...REV-R085 text/json surfaces...` | PASS | No forbidden claim patterns detected. |
| `venv/bin/python -B -m py_compile scripts/generate_theorem_extension_assets.py tests/contracts/test_theorem_extension_assets.py` | PASS | Touched Python files compile. |
| PNG integrity scan with Pillow | PASS | All five PNGs are readable, nonblank, and `1074x658` pixels. |
| `venv/bin/python -B -m pytest -m smoke -q` | PASS | `6 passed, 7615 deselected`; smoke suite. |
| `venv/bin/python -B -m pytest --collect-only -q` | PASS | `7562/7621 tests collected (59 deselected)`. |
| `venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | PASS | `OK: 62 PRs, DAG valid`. |
| `venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` | PASS | Completed `62/62 = 100.0%`; dependency-weighted completion `100.0%`; unblocked next `none`. |

## Claim-Tier Impact

REV-R085 creates appendix-only theorem-obligation figures from synthetic/manufactured helper outputs. It creates no observational theorem claim, no HTT evidence term, no MIO certificate, no posterior odds, no native solver result, no morphology compatibility claim, and no Bianchi geometry/family-identification support.

Residual blockers:

- theorem figures are not paper-main result figures;
- generated source JSON and manifests remain synthetic/manufactured only;
- G2 data-facing residual use remains blocked unless all provenance gates are bound;
- B4 observed line-of-sight source bounds remain blocked without rank, sign/phase, gap, kernel-floor, and mask provenance;
- S1 observed CMB temperature bridge remains unbound;
- S3 observational denominator certification remains blocked;
- native low-ell solver and native morphology atlas remain unavailable.
- source JSON and manifest sidecars must remain paired for downstream consumption; manifests alone do not encode every helper-row boolean.
