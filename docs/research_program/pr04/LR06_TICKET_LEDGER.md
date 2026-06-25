# LR-06 ticket ledger (full-DAG status)

Branch `research/pr04-multicomponent`. Status as of 2026-06-25. Fail-closed: a
ticket without its inputs terminates with its registered blocker code and emits
no substitute estimate.

| Ticket | Phase | Depends on | Status | Evidence / blocker |
| --- | --- | --- | --- | --- |
| **LR-06A** | foundation | — | **DONE** | PR04-002..007 merged; 23/23 gates, compileall, import smoke, forbidden-dep scan, fast/smoke/ci regression all pass; `rev-r108`. |
| **LR-06B** (PAPER-A) | theory | A | **GATES PASS; proof-review open** | `make paper-a-gates` (14 tests) + symbolic A-rank/A-flrw/A-wigner QED; radial-vorticity no-go, single-shell degeneracy, temporal tensor rank are `BLOCKED_PROOF_REVIEW` corollaries; `rev-r109`. |
| **LR-06C** (PAPER-B) | theory | A | **GATES PASS; dynamics-review open** | `make paper-b-gates` (9 tests) + symbolic B-nonsuff/B-psd/B-dust/B-shear QED; exact FLRW oracle + Gauss transport verified; `BLOCKED_DYNAMICS_REVIEW` for independent review; `rev-r109`. |
| **LR-06D** | data | A | **BLOCKED** | `BLOCKED_MISSING_FULL_RELEASE_BINDING` — only the CF4++ grid is local; the full release method/group/selection hierarchy is not owned by `dl_pipeline`. |
| **LR-06E** | data | A | **BLOCKED** | `BLOCKED_MISSING_E2E_SIMULATIONS` — pipeline is Planck PR3; no PR4/NPIPE maps or end-to-end simulations. |
| **LR-06F** | data | A | **BLOCKED** | `BLOCKED_MISSING_FIELD_REALIZATIONS` — no constrained 3D velocity-field ensemble present. |
| **LR-06G** | data-theory | C | **BLOCKED** | `BLOCKED_UPSTREAM_TRANSFER` — no validated ray-tracing/transfer owner; ties to LR-06L. |
| **LR-06H** | joint | D,E,F,G | **BLOCKED (upstream)** | `BLOCKED_UPSTREAM` — requires release hashes, covariance ownership, injection coverage, response manifests from D–G. |
| **LR-06I** | joint | C,H | **BLOCKED (upstream)** | `BLOCKED_RESPONSE_MANIFOLD` — needs the LR-06H joint posterior + a registered branch manifold. |
| **LR-06J** | reporting | H | **READY (fail-closed), no input yet** | `physical_pushforward.py` is installed + gate-tested; with no identified LR-06H posterior it correctly returns `BLOCKED_UNIDENTIFIED_COMPONENTS`. |
| **LR-06K** | publication | H,I,J | **BLOCKED (upstream)** | `BLOCKED_GLOBAL_CALIBRATION` — global mock replay requires the joint posterior + analysis family from H/I/J. |
| **LR-06L** | separate Rust | A,C | **DESIGN STARTED** | `AWAITING_RUST_DESIGN_PACK` lifted to a design doc (`RUST_NEW_PROJECT_DESIGN.md`); implementation is a separate long-term project; exact FLRW oracle is the first science gate. |

## Summary

- Closed/advanced without raw data: **LR-06A** (integration) and **LR-06B/LR-06C**
  (theory papers, gates + symbolic proofs).
- The entire **data → joint → calibration** chain (D, E, F, G, H, I, K) is
  blocked on delegated inputs that `dl_pipeline` does not own (full CF4 release,
  PR4/NPIPE + E2E sims, constrained velocity fields, validated transfer). These
  are honest terminal blocker states, not failures.
- **LR-06J** is wired and fail-closed; it will produce legacy scalar pushforwards
  the moment LR-06H delivers an identified posterior.
- **LR-06L** is a separate Rust project; design captured, no old-solver
  inheritance.
