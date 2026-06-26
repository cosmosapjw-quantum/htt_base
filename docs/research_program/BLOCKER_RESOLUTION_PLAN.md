# Blocker Resolution Plan

owner: COMMON
implementation_scope: research_program_blocker_resolution_plan
claim_tier: diagnostic_only
transfer_source: mixed_public_input_pending_external_proxy_and_none
sky_support_status: planned_per_blocker
null_mock_status: planned_per_blocker
config_hash: sha256:332fe81c7ad0447c4cd39fe285bc2d28a7da7f2179af5a36006bab0e4991d309
generating_command: manual expansion of docs/research_program/BLOCKERS.md, 2026-06-26
git_commit_or_worktree_state: 8e104e573d78fd515044e6c268edb3d46e4c5d51 with dirty .claude/settings.json and .codex/rules/default.rules before this plan
caveats:
- This is an execution plan, not blocker discharge evidence.
- A blocker closes only when the named real input, manifest, command log, and exit gate are present.
- Synthetic stand-ins remain synthetic and must not be used as replacement estimates.
- Native-atlas-dependent family/classification language remains blocked outside PR10.

## Input Hashes

| Input | SHA256 |
| --- | --- |
| `docs/research_program/BLOCKERS.md` | `948b22608b24b3e9aeb4cd2db896fdcec63dc35cad156045f789556197fd62c0` |
| `docs/research_program/pr07/BLOCKER_RESOLUTION_MATRIX.md` | `57b08112978aee95be25c68dd7d5b2560373a80ddad5fc07aeeb9affb83f1677` |
| `docs/research_program/egs2/BLOCKER_DISCHARGES.md` | `03186afca2a553f7e2dc09ab09e6164a53dac8ded1eee1d5335ab85751a94c60` |
| `docs/research_program/egs3/BLOCKER_SOLUTIONS.md` | `fa57108d69263f577efc2f7f06b7fd9827ecd09154709ab0f0555bb797cb3e9c` |
| `docs/generated/egs_results_table.json` | `be0885b8e963990636f963fa9483d92d99f78a671aed076a3a510c60ac3a92df` |
| `Makefile` | `0cbfbe14f0c73d84e236ea91ca3193f768b2f05cb535fb641056f24014b7be4c` |

External source checks:

- Planck Legacy Archive official portal: https://pla.esac.esa.int/
- Planck PR4/NPIPE overview mirrored by the CMB-S4 data portal: https://data.cmb-s4.org/planck_pr4.html
- Hoffman et al. CF4 WF/CR paper, arXiv:2311.01340: https://arxiv.org/abs/2311.01340
- MNRAS version of the CF4 velocity-field paper: https://academic.oup.com/mnras/article/527/2/3788/7419869

## Strategy

Resolve blockers in this order:

1. Audit hygiene preflight: stale generated files, invalid manifests, and active claim-scan findings.
2. K1: public Planck E2E simulation access and global low-ell max-scan.
3. K6 and K5: CF4 constrained field realizations and release-matched forward mocks.
4. PR08-006: joint artifact only after K1/K5/K6 each close independently.
5. PR10: separate native low-ell solver project; no substitute implementation in this repo.

This order maximizes near-term measurement value without weakening the claim firewall. K1 is highest leverage because the needed input class is public. K5/K6 are deeper because they require CF4 reconstruction/mock ownership. PR08-006 is a downstream join, not an independent measurement. PR10 is a separate solver project.

## Preflight Blockers Surfaced By Audit

These are not the research-program blockers in `BLOCKERS.md`, but they should be repaired before any blocker-discharge PR is treated as release-grade.

| Audit blocker | Evidence | Required repair | Exit gate |
| --- | --- | --- | --- |
| Stale generated/provenance artifacts | targeted suite: 852 passed, 8 failed | rerun controlled generators for CF4++ LNB, code capability audit, current manuscript figures, external input inventory, PDF claim lint, semantic firewall fuzz | failing tests rerun clean |
| Invalid figure manifests | `scripts/check_artifact_manifests.py --dry-run` failed | add missing required fields and canonical sky-support statuses | manifest dry-run passes or invalid surfaces are quarantined |
| Broad active-claim scan failures | claim-language/status scripts failed on current broad scan | downword active text or add narrow generated hash-bound exemptions | active-surface scans pass |
| Stale narrative handoff | `PROJECT_STATE.md` still says PR-075 while status is 62/62 | regenerate handoff/project-state docs from machine-readable status | progress and narrative docs agree |
| Mock-result checker noise | no-mock checker reports historical markers | split active surfaces from archive/history | active-surface checker has zero findings |

## `BLOCKED_MISSING_PR4_E2E_ACCESS`: K1 Global Low-Ell Calibration

Current state:

- Blocks K1 promotion from a local/single-sky low-ell morphology score to a global rank calibrated against an end-to-end ensemble.
- Mechanics are ready in `htt/obsstat/lowell_global_calibration.py:e2e_maxscan_from_summaries`.
- Current `docs/generated/egs_results_table.md` row is blocked and shows only a labelled synthetic stand-in.

External input:

- Planck FFP10 products from the Planck Legacy Archive.
- Planck PR4/NPIPE E2E simulations where usable for the same statistic/mask/beam path.
- The repo ticket expects `dx12_v3_{method}_{cmb,noise}_mc_*` style FFP10 products across Commander, NILC, SEVEM, and SMICA plus NPIPE-style E2E realizations.

Resolution work package:

1. Create an input-manifest schema before download:
   - `simulation_id`;
   - release family (`FFP10` or `NPIPE_PR4`);
   - component-separation method;
   - map path;
   - noise path if separate;
   - beam/FWHM;
   - input NSIDE and downgraded NSIDE;
   - mask path/hash;
   - frequency/component metadata;
   - source URL or archive query;
   - SHA256 or archive checksum;
   - license/access note.

2. Download or bind inputs read-only:
   - keep raw maps outside git;
   - write a manifest under `docs/generated` or `workdir/raw` sidecar;
   - record the exact download/query command and date.

3. Build per-simulation compact summaries:
   - downgrade to NSIDE=16;
   - apply the matched low-ell mask;
   - smooth to the registered beam;
   - compute the frozen six K1 statistics per realization;
   - emit Parquet/JSON summaries only.

4. Run frozen max-scan:
   - feed summaries into `e2e_maxscan_from_summaries`;
   - compute tail scores and max statistic for each realization;
   - compute +1 global rank p-value;
   - bind config hash to statistic list, mask, beam, ell range, and release method.

5. Validate:
   - rerun K1 unit tests and EGS2/EGS3 gates;
   - run smoke/collect/package;
   - run active claim scans;
   - add a regression fixture with a tiny synthetic ensemble, not the full data.

Exit gate:

- global rank p-value;
- matched-pipeline config hash;
- ensemble provenance manifest with map IDs, mask, beam, NSIDE, method, and input hashes;
- `docs/generated/egs_results_table.*` row flips from blocked to measured only through the generator.

Kill switches:

- stop if map/mask/beam path differs between observed map and simulations;
- stop if component-separation methods are mixed without method labels;
- stop if fewer simulations are available than declared;
- stop if the p-value path is recomputed with an unfrozen statistic set;
- stop if output text claims global significance without matched E2E provenance.

## `BLOCKED_MISSING_FIELD_REALIZATIONS`: K6 Curl/Vorticity Posterior

Current state:

- Blocks K6 realization-conditioned posterior over the curl/vorticity sector.
- Mechanics are represented by `htt/obsstat/constrained_realizations.py:curl_posterior` and `htt/obsstat/affine_flow.py`.
- The current row is blocked; any toy CR output is only a labelled synthetic stand-in.

External input:

- A constrained 3D CF4 velocity-field realization ensemble.
- Hoffman et al. describe CF4 velocity-field reconstruction using Bias Gaussianization, Wiener filtering, and constrained realizations.

Resolution work package:

1. Create a CF4 realization manifest:
   - field realization ID;
   - grid geometry and units;
   - coordinate frame;
   - smoothing scale;
   - WF/CR method tag;
   - BGc status;
   - CF4 release binding;
   - input hashes;
   - random seed or realization provenance where available.

2. Bind field ensemble:
   - do not use only the WF mean as a posterior;
   - require multiple constrained realizations or explicitly emit a no-go row.

3. Run affine/curl extraction per realization:
   - compute Cartesian components before norms;
   - preserve sign and component covariance;
   - record radius, boundary, and subsample stability.

4. Detect curl-suppressed inputs:
   - if the reconstruction is potential-flow-only, close with an explicit structural no-go rather than a false posterior.

5. Validate:
   - run `tests/obsstat/test_affine_flow.py`;
   - run K6/EGS2 blocker-discharge tests;
   - run claim scans to ensure no physical-vorticity wording escapes from curl-suppressed inputs.

Exit gate:

- realization-conditioned posterior with median and 16/84 percentiles, or explicit no-go;
- field realization manifest;
- component covariance and stability report;
- claim text capped at diagnostic/conditional unless the full field ensemble supports more.

Kill switches:

- stop if only a point WF field is available;
- stop if field frame/units are missing;
- stop if boundary/radius choices dominate the sign;
- stop if a curl-suppressed reconstruction is used to claim a physical curl sector.

## `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP`: K5 Cosmic-Variance Coverage

Current state:

- Blocks cosmic-variance-inclusive coverage for the CF4 bulk-flow apex/depth.
- Mechanics are ready through `htt/obsstat/bulkflow_mle.py:hierarchical_coverage_experiment`.
- `PR08-002` mechanics are closed, but release-matched mock ownership is not.

External input:

- CF4 release-matched forward mocks with selection, grouping, sky coverage, distance-error model, frame conventions, nonlinear velocities, and release binding.
- The CF4 WF/CR/BGc machinery is the natural source for consistent mocks.

Resolution work package:

1. Define release binding:
   - exact CF4 group catalog version;
   - selection function;
   - sky mask and completeness;
   - distance variable and uncertainty model;
   - frame convention;
   - grouping logic.

2. Generate or acquire forward mocks:
   - sample release-matched positions/selection;
   - inject distance errors;
   - preserve nonlinear velocity assumptions;
   - record mock seed/provenance.

3. Run bulk-flow estimator per mock:
   - use the same hierarchical/GLS estimator as data;
   - compute component and amplitude coverage;
   - separate cosmic variance from measurement noise.

4. Stress tests:
   - method/depth/frame ablations;
   - held-out subcatalog checks;
   - bias and coverage at each depth shell.

5. Figure repair:
   - regenerate the K5 figure with current wording and a valid manifest;
   - do not rely on stale internal PNG title text.

Exit gate:

- component/amplitude coverage report with bias gates;
- mock manifest with release binding;
- config/input hashes;
- figure/report manifest;
- K5 row flips only through generated results table.

Kill switches:

- stop if mocks do not match the release selection;
- stop if data and mocks use different frame conventions;
- stop if coverage uses self-injection only;
- stop if cosmic variance and measurement uncertainty are collapsed into one unlabeled number.

## `BLOCKED_UPSTREAM`: PR08-006 Joint Artifact

Current state:

- Pure downstream join.
- Depends on K1, K5, and K6.
- Must not set missing sectors to zero.
- Must keep HTT evidence semantics separate from MIO diagnostics.

Resolution work package:

1. Wait for K1, K5, and K6 exit gates.
2. Build a joint artifact schema:
   - component owner;
   - data rank;
   - prior-conditioned rank;
   - missing/blind sectors;
   - cross-covariance availability;
   - transfer source;
   - null/PPC/LOOCV support;
   - caveats.
3. Assemble only identified vector/tensor components into x/Q/Pi/F/G_F pushforwards.
4. Emit missing sectors explicitly as fail-closed.
5. Run result-pack tests, MIO/HTT firewall tests, claim scans, and manifest checks.

Exit gate:

- all component blockers closed;
- joint artifact has a manifest;
- rank and missing-sector status are explicit;
- no MIO/HTT lane merge;
- generated table and claim ledger updated by generator.

Kill switches:

- stop if any component still has a synthetic or blocked row;
- stop if cross-covariance is missing but the artifact reports a combined scalar;
- stop if diagnostic MIO outputs are consumed as HTT likelihood/evidence inputs.

## `AWAITING_NATIVE_LOWELL_SOLVER`: Native Low-Ell Atlas Ceiling

Current state:

- Separate long-term PR10 project.
- The repo may build schemas, adapters, semi-native single-mode transfer, and pre-solver diagnostics.
- The repo must not implement a fake native solver or relabel external/proxy outputs as native.

Resolution work package outside this repo:

1. PR10-001: convention and oracle contract.
2. PR10-002: FLRW perturbation comparator against CAMB/CLASS.
3. PR10-003: collision/TCA conservation.
4. PR10-004: LOS convergence surface.
5. PR10-005: nearly-FLRW Bianchi-I seed.
6. PR10-006: family x mode x orientation support truth matrix.

Allowed interim work in this repo:

- schema-only native adapter contracts;
- `AtlasEntryLite` metadata;
- transfer provenance registry;
- semi-native single-mode shear-to-low-ell transfer;
- observable-vector and morphology feature plumbing;
- null/mask/covariance/equivalence gate design.

Exit gate:

- native solver artifacts;
- convergence and comparator reports;
- morphology atlas;
- matched masks/nulls/covariance;
- response-rank and equivalence-class gates;
- PPC/LOOCV where model-dependent inference is claimed.

Kill switches:

- stop if old Rust spectra/evidence/atlas are proposed as native validation;
- stop if external transfer is renamed native;
- stop if scalar-only or MIO-only diagnostics are promoted into native-atlas language.

## Execution Schedule

Stage A: Audit hygiene PRs.

1. Regenerate stale reports and manifests.
2. Repair active claim-scan failures.
3. Sync stale handoff docs.
4. Rerun focused failed tests plus smoke/collect/package.

Stage B: K1 public-data discharge.

1. Write input manifest schema.
2. Bind/download FFP10/NPIPE inputs.
3. Generate compact simulation summaries.
4. Run max-scan and update generated result row.

Stage C: CF4 realization/mock discharge.

1. Bind CF4 WF/CR ensemble.
2. Run K6 per-realization affine/curl posterior or no-go.
3. Generate K5 release-matched forward mocks.
4. Run coverage/bias report.

Stage D: PR08-006 join.

1. Bind component result manifests.
2. Assemble joint artifact with explicit blind/missing sectors.
3. Run result-pack, claim, and manifest gates.

Stage E: PR10 handoff.

1. Keep PR10 outside this repo unless explicitly scoped as schema/adapter work.
2. Package solver-interface requirements, not solver outputs.

## Required Validation Bundle Per Blocker PR

Minimum:

```bash
venv/bin/python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py smoke
env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py collect
env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/check_claim_language.py --dry-run --format json <changed active docs>
venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <changed active docs>
venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <changed active docs>
venv/bin/python scripts/check_artifact_manifests.py --dry-run
```

Blocker-specific:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH=$PWD:$PWD/htt:$PWD/htt/htt venv/bin/python -m unittest discover -s research_gates/egs2/tests -p 'test_egs2_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONPATH=$PWD:$PWD/htt:$PWD/htt/htt venv/bin/python -m unittest discover -s research_gates/egs3/tests -p 'test_egs3_*.py' -v
```

Run narrower module tests for the touched blocker:

- K1: `tests/obsstat/test_lowell_map_features.py`, `tests/obsstat/test_null_ensembles.py`, and any new K1 calibration tests.
- K6: `tests/obsstat/test_affine_flow.py` plus constrained-realization tests.
- K5: `tests/obsstat/test_bulkflow_mle.py` plus CF4 catalog tests.
- PR08-006: result-pack, MIO/HTT firewall, posterior pushforward, and claim-gate tests.

## Publication Rule

The first publication-grade measurement candidate is not the current synthetic K1/K6 stand-in. It is the first generated row whose real input manifest, command log, config hash, input hashes, null/mock/covariance support, and claim ledger all agree.

Until then, the correct public posture is:

- theorem/mechanics content: allowed under explicit assumptions;
- current data rows: blocked or diagnostic-only;
- transfer-dependent outputs: transfer-conditional;
- native-atlas-dependent language: unavailable in this repo state.
