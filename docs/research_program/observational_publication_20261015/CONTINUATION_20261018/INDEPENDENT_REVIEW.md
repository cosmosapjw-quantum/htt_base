# Independent review — PASS_SCOPED

Date: 2026-10-18. Reviewer: `/root/sixpaper_independent_review_20261018`, a separately dispatched native reviewer who did not author the candidate. No nested reviewers were used. Requested model/effort: inherited parent settings; observed model/effort: **UNKNOWN**. Actual native reviewer dispatch occurred; this is not an attestation of a particular model.

**Decision: PASS_SCOPED for the reviewed continuation candidate. No unresolved blocker, major, or minor finding remains.** This approves the bounded code, conditional calculations and continuation documentation for publication as a scoped research increment. It does not approve scientific node completion, manuscript submission, main merge, primary installation or whole-repository CI.

## Candidate identity

- Baseline: `cosmosapjw-quantum/htt_base@967ef7c8f0b132ecaaba343045d333d4ebf299c1` (#559).
- Candidate: selected files under `HTT_SIXPAPER_20261018/patches/`, described by `CONTINUATION_20261018/CANDIDATE_FILES.json`.
- Final manifest: **74 files, 5,181,109 bytes**. Every listed size, SHA-256 and Git blob identity was independently checked against staged bytes.
- Content digest: `99a2dd498d031e3f8c2d7e838231487a4af0fd539dfa082548c70284308379b5`.
- Digest procedure: SHA-256 of the manifest `files` array serialized with sorted keys and compact JSON separators. The manifest and this review are excluded to avoid self-reference; caches are not publication inputs.

I read the pinned `AGENTS.md` and `docs/harness/CURRENT_CODEX_RUNTIME.md`, new scientific kernels/tests/reports, changed validators, actual source summaries, goal contracts, final integration documents and relevant previous source. Review writes were limited to this report; tests used disposable tiny Git fixtures and did not touch the owner checkout.

## Findings and closeout

1. **Medium, closed — P3 input identity.** The initial `P3/calibration_frontier.py` could accept modified eigenvalues while labeling them with a hardcoded source Git blob. The final file reader computes and checks the actual byte identity. Dictionary-only computation records that byte validation was not performed. The added changed-eigenvalue regression passes; the final saved result carries the verified source identity.
2. **Medium, closed — P3 absolute-error coverage.** Covariance alone does not justify Gaussian/Chebyshev bounds about zero. Final code metadata, result JSON and `P3/RESULT_KO.md` explicitly assume `E[epsilon | fixed selected design]=0`; known bounded bias may enter calibration delta. The reported numerical radii are unchanged and remain conditional.
3. **Minor, closed — packaged guard documentation.** Worker-relative paths in `CHECKOUT_GUARD_PATCH.md` did not resolve in the integrated package. The final document uses repository-root production paths and a runnable standalone-test command.

An apparent legacy guard-test conflict was traced to immutable original files. The actual staged `test_l01_repo_checkout_guard.py` already tests an explicitly created continuation remote ref; that compatibility change is correct. Its pytest suite was inspected, not executed here.

## Scientific and implementation assessment

**P1:** The finite working-law reconstruction uses the actual committed 4×9 coefficients and full 36×36 covariance. Four windows share each draw ID and weight. The density-envelope formula follows from event/complement normalization; independent linear programs check endpoints. Anchor/floor contrasts retain signed coefficients and preserve physical unknown mass 1. Stored draws and apparent ratios agree exactly with read-only recomputation. These are conditional proxy sensitivities, not a physical posterior or anomaly p-value.

**P2:** The shared-anchor Gram construction and scalar-fit residual bound are correct. E/B endpoint constructions can be attained together in orthogonal blocks; the total scalar fit is computed from the combined geometry. Direct-vector tests include endpoint witnesses, scale changes and negative-amplitude exclusion. Pinned input summaries, saved per-group results and combined E/B endpoints were independently checked. Sharpness is conditional on the reported common anchor/convention; no raw map/vector replay or outward-rounded certification is claimed.

**P3:** Spectral bounds on a predeclared raw-basis unit contrast, centered Gaussian/Chebyshev union bounds, and scalar box intersection are correct under stated assumptions. Shared-method independence is not required. Missing method centers remain null, so no observed calibration threshold, common-parameter interval or physical detection is manufactured. Final stored numerical rows and centered-error metadata match recomputation.

**Continuation controls:** The unchanged strict backlog validator reproduces the base failure for exactly four existing extension IDs and passes **245 cards** after their registration, using original status and PR167 receipt. All four backlog formats agree. This repairs registration consistency without changing card criteria/status. Publication terminal completion now requires completed prerequisites plus an evidenced HOLD/READY_FOR_OWNER_REVIEW with `submitted=false`. The actual DAG changes only supporting evidence/next actions on S02, S03, L01 and H02; all states, dependencies and acceptance criteria are preserved. All 42 goal contracts validate, the ready queue exactly matches derivation, and only S02/L01 are ready. Completion stays **14/42**; all six papers remain **NOT_READY_TO_SUBMIT**.

The checkout guard resolves explicit validated `refs/remotes/origin/...` names, preventing revision-expression/tag shadowing, while retaining exact HEAD, clean tree, Git trust, top-level and import checks. The native helper requires an explicit interpreter. Goal packets are planning inputs, not a background scheduler or automatic acceptance mechanism.

## Independently executed validation

All commands used `PYTHONDONTWRITEBYTECODE=1` and the available Python 3.12.14 runtime. They were rerun against the final staged code; the last subsequent change was documentation only.

| Working directory | Command | Result |
|---|---|---|
| `CONTINUATION_20261018/P1` | `python -m unittest -v test_functional_sensitivity` | 12 PASS |
| `CONTINUATION_20261018/P2` | `python -m unittest discover -s tests -v` | 8 PASS |
| `CONTINUATION_20261018/P3` | `python -m unittest -v test_calibration_frontier` | 8 PASS |
| Selected candidate root | `python tests/htt/test_sixpaper_goal_execution.py` | 5 PASS |
| Selected candidate root | `python docs/research_program/observational_publication_20261015/L01_R8_C8_TWO_MASK_STABILITY_20261017/tests/test_l01_checkout_guard_continuation.py` | 8 PASS |

**Total: 41 focused tests passed.** Additionally: original strict backlog failure/pass reproduced; final manifest verified; DAG/queue/goal consistency checked; stored numerical arrays/rows checked. P1/P2 scientific plots were visually inspected. No full-CI claim follows from these checks.

## Remaining limits

The primary checkout remains UNKNOWN and was not accessed. Native FITS/healpy execution, raw 35,970-row CF4 refit, physical null qualification, native Bianchi solver/ODE, complete pytest collection and whole-repository CI remain NOT_RUN. The old pytest guard suite requires the full predecessor tree/runtime. An attempted external literature spot-check was blocked by arXiv DisabledError and A&A HTTP 403; this review assesses literature claim scope but does not independently certify every citation, novelty claim or published likelihood. Future publication feasibility still depends on the explicit missing physical/source inputs. These limitations are accurately retained by the candidate and do not invalidate its declared conditional computations.
