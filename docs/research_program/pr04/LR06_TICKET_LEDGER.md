# LR-06 ticket ledger (full-DAG status)

Branch `research/pr04-multicomponent`. Status as of 2026-06-25. Fail-closed: a
ticket without its inputs terminates with its registered blocker code and emits
no substitute estimate.

| Ticket | Phase | Depends on | Status | Evidence / blocker |
| --- | --- | --- | --- | --- |
| **LR-06A** | foundation | — | **DONE** | PR04-002..007 merged; 23/23 gates, compileall, import smoke, forbidden-dep scan, fast/smoke/ci regression all pass; `rev-r108`. |
| **LR-06B** (PAPER-A) | theory | A | **GATES PASS; proof-review open** | `make paper-a-gates` (14 tests) + symbolic A-rank/A-flrw/A-wigner QED; radial-vorticity no-go, single-shell degeneracy, temporal tensor rank are `BLOCKED_PROOF_REVIEW` corollaries; `rev-r109`. |
| **LR-06C** (PAPER-B) | theory | A | **GATES PASS; dynamics-review open** | `make paper-b-gates` (9 tests) + symbolic B-nonsuff/B-psd/B-dust/B-shear QED; exact FLRW oracle + Gauss transport verified; `BLOCKED_DYNAMICS_REVIEW` for independent review; `rev-r109`. |
| **LR-06D** | data | A | **DONE (descriptor)** | CF4 full release bound via new `cf4_full` pipeline stage (VizieR J/ApJ/944/94, 38053 groups); minimum-variance bulk flow ~345 km/s toward (293,21), forward-mock coverage ~0.68; `rev-r112`. Full selection forward model + frame ablation = follow-up. |
| **LR-06E** | data | A | **PIPELINE-EXTENDED; calibration BLOCKED** | new `planck_npipe` stage added (fail-closed, PLA-portal-gated); `BLOCKED_MISSING_E2E_SIMULATIONS` — the NPIPE end-to-end sim ensemble needed to calibrate boost injection is not feasibly downloadable. Not a solver dependency. |
| **LR-06F** | data | A | **DONE** | affine velocity-gradient posterior on the local CF4++ field; bulk 152→422 km/s, vorticity ~0 (reconstruction-conditioned), curl-injection recovery 3e-16; `rev-r111`. Cross-reconstruction `BLOCKED_MISSING_FIELD_REALIZATIONS`. |
| **LR-06G** | data-theory | C | **BLOCKED** | `BLOCKED_UPSTREAM_TRANSFER` — no validated ray-tracing/transfer owner; ties to LR-06L. |
| **LR-06H** | joint | D,E,F,G | **BLOCKED (upstream)** | `BLOCKED_UPSTREAM` — requires release hashes, covariance ownership, injection coverage, response manifests from D–G. |
| **LR-06I** | joint | C,H | **BLOCKED (upstream)** | `BLOCKED_RESPONSE_MANIFOLD` — needs the LR-06H joint posterior + a registered branch manifold. |
| **LR-06J** | reporting | H | **READY (fail-closed), no input yet** | `physical_pushforward.py` is installed + gate-tested; with no identified LR-06H posterior it correctly returns `BLOCKED_UNIDENTIFIED_COMPONENTS`. |
| **LR-06K** | publication | H,I,J | **BLOCKED (upstream)** | `BLOCKED_GLOBAL_CALIBRATION` — global mock replay requires the joint posterior + analysis family from H/I/J. |
| **LR-06L** | separate Rust | A,C | **DESIGN STARTED** | `AWAITING_RUST_DESIGN_PACK` lifted to a design doc (`RUST_NEW_PROJECT_DESIGN.md`); implementation is a separate long-term project; exact FLRW oracle is the first science gate. |

## Summary (updated after the pipeline-extension pass)

- Closed/advanced: **LR-06A** (integration), **LR-06B/C** (theory papers),
  **LR-06D** (CF4 bulk-flow descriptor on the newly-bound full release),
  **LR-06F** (CF4 affine local-flow decomposition).
- Pipeline extended (`dl_pipeline`): new `cf4_full` stage (live VizieR download,
  unblocked LR-06D) and `planck_npipe` stage (fail-closed, PLA-portal-gated).
- Still blocked, honestly: **LR-06E** calibration (`BLOCKED_MISSING_E2E_SIMULATIONS`
  — the NPIPE sim ensemble is not feasibly downloadable; not a solver issue),
  **LR-06G** (`BLOCKED_UPSTREAM_TRANSFER` — needs a validated transfer owner,
  the one item tied to the excluded low-ell solver), and the joint chain
  **LR-06H/I/K** (`BLOCKED_UPSTREAM` — needs an independent CMB-boost channel +
  transfer with covariance ownership; the CF4 D/F channels are not independent
  of each other, so a D+F-only joint would double-count).
- **LR-06J** wired and fail-closed; emits `BLOCKED_UNIDENTIFIED_COMPONENTS` until
  LR-06H delivers an identified posterior.
- **LR-06L** separate Rust project; design captured, no old-solver inheritance.
