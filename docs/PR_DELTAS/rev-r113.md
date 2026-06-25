# REV-R113 - dl_pipeline planck_npipe stage (fail-closed) + LR-06 ledger update

owner: COMMON
implementation_scope: dl_pipeline + common
claim_tier: diagnostic_only
transfer_source: none
generating_command: `fetch.py --stages planck_npipe (fail-closed) + ledger refresh`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Finish the download-pipeline modification for the remaining external data and
update the ticket status after the data tickets that became runnable.

## Changes

- `dl_pipeline/config/sources.json` + `dl_pipeline/scripts/fetch.py`: new
  `planck_npipe` stage for the PR4/NPIPE maps (LR-06E). Fail-closed: it
  auto-fetches only if a direct map URL is supplied via `PLANCK_NPIPE_URL` (the
  PLA serves maps through an interactive portal, not a plain file URL), otherwise
  it logs the portal requirement and the standing
  `BLOCKED_MISSING_E2E_SIMULATIONS` calibration blocker. The NPIPE end-to-end
  simulation ensemble (hundreds of GB, needed to calibrate boost-injection
  recovery) is not auto-downloaded; this is a data-availability limit, not a
  low-ell-solver dependency.
- `docs/research_program/pr04/LR06_TICKET_LEDGER.md`: D advanced to a calibrated
  descriptor (rev-r112), F done (rev-r111), E pipeline-extended/calibration-
  blocked; summary refreshed.
- `docs/research_program/pr04/DATA_ACQUISITION_STATUS.md`: update banner.

## Net state of the data track

- Downloaded + analyzed without a low-ell solver: CF4 full release (`cf4_full`
  stage) -> LR-06D bulk-flow descriptor; local CF4++ field -> LR-06F affine-flow
  decomposition.
- Pipeline extended for NPIPE (`planck_npipe`), but LR-06E calibration and
  LR-06G transfer remain honest blockers; the joint chain LR-06H/I/K stays
  upstream-blocked (no independent CMB-boost channel; the CF4 D/F channels are
  mutually dependent and cannot form a non-double-counting joint).

## Validation

| Command | Status |
| --- | --- |
| `python -c json.load(sources.json)` | valid |
| `fetch.py --stages planck_npipe` | fail-closed; logs portal + BLOCKED_MISSING_E2E_SIMULATIONS |
| `fetch.py --list` | shows cf4_full + planck_npipe |
