# REV-R110 - LR-06 data/joint/calibration track + LR-06L Rust design (fail-closed)

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
generating_command: `dl_pipeline fetch (cf4, camb_refs) + honest ticket triage`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Full-DAG attempt with raw-data acquisition started. Execute the delegated data
tickets (LR-06D-G), the joint/reporting tickets (LR-06H/I/J), the calibration
branch (LR-06K), and the new Rust project (LR-06L) - terminating blocked tickets
with their registered blocker codes rather than substitute estimates.

## Raw-data acquisition

Started `dl_pipeline` acquisition of the available products: `fetch.py
--stages cf4,camb_refs` completed 2/2 (regenerated the CF4++ grid products and
CAMB references; `artifacts/pr04/fetch_cf4_camb.log`). Disk free ~508 GB.

The available pipeline stages (Planck PR3, DESI Y1, ACT, SPT, BICEP/Keck, CF4++
grid, CAMB) do **not** own the delegated inputs the data tickets require. Honest
mapping recorded in `DATA_ACQUISITION_STATUS.md`:

| Ticket | Missing delegated input | Blocker |
| --- | --- | --- |
| LR-06D | full CF4 release method/group/selection hierarchy | `BLOCKED_MISSING_FULL_RELEASE_BINDING` |
| LR-06E | Planck PR4/NPIPE maps + end-to-end simulations | `BLOCKED_MISSING_E2E_SIMULATIONS` |
| LR-06F | constrained 3D velocity-field realizations | `BLOCKED_MISSING_FIELD_REALIZATIONS` |
| LR-06G | validated ray-tracing/transfer artifacts | `BLOCKED_UPSTREAM_TRANSFER` |

## Joint / reporting / calibration

- LR-06H (joint posterior), LR-06I (restricted Bianchi-I), LR-06K (global
  calibration -> PAPER-C) are upstream-blocked (`BLOCKED_UPSTREAM`,
  `BLOCKED_RESPONSE_MANIFOLD`, `BLOCKED_GLOBAL_CALIBRATION`) until D-G deliver
  release-hashed, covariance-owned artifacts.
- LR-06J (legacy x_C/Q/Pi/F/G_F pushforward) is wired and fail-closed: with no
  identified LR-06H posterior it correctly returns
  `BLOCKED_UNIDENTIFIED_COMPONENTS` (verified by the PR04 pushforward gate).

Full status: `docs/research_program/pr04/LR06_TICKET_LEDGER.md`.

## LR-06L new Rust solver (separate project)

Design pack `RUST_NEW_PROJECT_DESIGN.md` lifts `AWAITING_RUST_DESIGN_PACK`: six
golden contracts with the **exact flat-FLRW oracle as the first science gate**
(the `B-dust` symbolic result is its reference), a salvage/quarantine boundary
over the existing `bass_rs` crate (no old-solver science inheritance), and a
Python/Rust parity harness. Separate long-term repository; does not block
PAPER-A/B.

## Claim boundary

No scalar-to-family promotion, no MIO-as-posterior, no old-Rust inheritance, no
radial-vorticity claim. Every blocked ticket carries its registered blocker code
and emits no substitute number, per `CLAIM_AND_STOP_GATES.md`.

## Outcome of the full-DAG attempt

Closed without raw data: LR-06A (integration), LR-06B/C (theory papers, gates +
symbolic proofs). The data->joint->calibration chain is honestly blocked on
delegated inputs `dl_pipeline` does not own; LR-06J is fail-closed-ready; LR-06L
design captured. No envelope was exceeded.
