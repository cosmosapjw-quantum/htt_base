# Verification and execution scope

2026-10-18. Primary existing checkout `/home/cosmosapjw/Dropbox/bianchi/htt_base`: UNKNOWN, not accessed or mutated after Desktop Commander monthly limit. This is a selected-source fixture, not a clone, worktree or whole repository. Exact GitHub source commit: `967ef7c8f0b132ecaaba343045d333d4ebf299c1`.

## Actual focused tests

| Suite | Command in its indicated directory | Result |
|---|---|---|
| P1 joint functional sensitivity | `python -m unittest -v test_functional_sensitivity` in P1 | 12 PASS; original source-summary counts plus40 LP endpoint optimizations |
| P2 shared-anchor geometry | `python -m unittest discover -s tests -v` in P2 | 8 PASS;500 independent vector comparisons and scale/witness tests |
| P3 calibration frontier | `python -m unittest -v test_calibration_frontier.py` in P3 | 8 PASS; exact source-pin/tamper test, spectral and simultaneous-error laws |
| Publication terminal/dependency semantics | `python tests/htt/test_sixpaper_goal_execution.py -v` at selected fixture root | 5 PASS |
| Explicit continuation checkout guard | `python -m unittest discover -s docs/research_program/observational_publication_20261015/L01_R8_C8_TWO_MASK_STABILITY_20261017/tests -p test_l01_checkout_guard_continuation.py -v` | 8 PASS; disposable tiny Git fixtures only |

Total: **41 focused tests**, independently rerun in the scoped review. No full repository pass is claimed. Existing pytest-based native adapter/legacy guard test collection is NOT_RUN here because pytest/healpy/full source installation is absent; compatible test source was updated and standalone guard tests cover the changed behavior.

Actual Python `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python`, 3.12.14; NumPy2.3.5, SciPy1.17.0, Matplotlib3.10.8. `pytest`, `healpy`, `sympy` unavailable in this scratch runtime. No installation added. Primary global CUH-G registration/telemetry NOT_RUN because primary execution access is unavailable; native collaboration calls were actually dispatched by the current host. Requested model/effort inherited; observed worker/reviewer model and effort UNKNOWN.

## Blocker reproduction and closure

Original strict command:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice
```

Base source failed with exactly four unregistered extension cards: PR-SF-CF4-PRECISION, PR-SF-GAIA-CORRELATION, PR-SF-METHODS-MANUSCRIPT, PR-SOLVER-FREE-DOSSIER. The unchanged validator, original status and original PR167 receipt pass245 after registering those four existing IDs in the candidate YAML. All card dictionaries and topological order are unchanged. Canonical/machine YAML and JSON mirrors agree; status is untouched.

Guard RED against old source:6 failures+1 error+1 pass. Candidate standalone GREEN:8/8. Default expected ref remains compatible; explicit origin branch refs are validated and resolved through refs/remotes, preventing revision-expression/tag shadowing. Exact HEAD, clean tree, top-level, Git trust and import checks remain. Parent native helper additionally requires explicit PLANCK_PYTHON from the existing native runtime receipt.

Publication validator previously unconditionally rejected every completed terminal, contradicting the documented readiness-decision objective. The candidate requires completed prerequisites and an evidenced HOLD/READY_FOR_OWNER_REVIEW with submitted=false. Actual node states, dependencies and acceptance remain unchanged. Supporting evidence and stale next actions change only for S02/S03/L01/H02; READY_QUEUE is re-exported. Validator output:6 papers,42 nodes,14 completed,28 pending,7 direct external-missing nodes,2 ready(S02,L01).

## Independent findings fixed

1. P3 source runner could label changed eigenvalue bytes with an expected Git blob. It now computes and checks the exact byte identity; a tampered-input regression passes.
2. Gaussian/Chebyshev absolute-error coverage needs centered conditional errors. The code metadata, generated result and report now explicitly require zero mean; known bounded bias may be included in delta. Numerical values did not change.
3. Apparent legacy guard test conflict was traced to immutable RED originals. The actual staged existing pytest test accepts an explicitly created continuation ref. No frozen original was relabelled.

## Scientific execution boundaries

P1 recomputed downstream finite-law quantities from actual committed H03 sufficient statistics; raw35970-row refit NOT_RUN. P2 computed new exact-formula numerical bounds from actual user-executed committed scalar summaries; raw native FITS/vector replay NOT_RUN. P3 computed actual-source geometry radii under assumed centered noise/calibration laws; observed method centers/physical intervals NOT_RUN. Physical null qualification, physical x posterior, native solver, ODE integration and whole-repository CI are NOT_RUN.

Scientific figures were generated with standard plotting code and visually inspected. Wolfram algebra result is in WOLFRAM_CHECK.json. Literature sources and scope are in PUBLICATION_ASSESSMENT_KO.md; the independent review did not independently re-fetch all external literature.

## Publication verification

Use routine R1 provider success plus new branch/commit/tree identity. No forced push, main merge or journal submission. CANDIDATE_FILES.json is consumed by the independent review and publication uploader; its digest excludes itself and the independent review report to avoid self-reference. Successful publication identities are returned by the provider and recorded in the final handoff, not inferred from local files.
