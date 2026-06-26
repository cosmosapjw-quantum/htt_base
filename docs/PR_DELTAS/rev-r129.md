# REV-R129 - PR08-006 joint artifact + cobaya K1 check + hygiene finding

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_and_cf4_wf_proxy
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Revise the plan for the current state, finish all doable items, and check whether
cobaya (installed in venv) can download the K1 data.

## cobaya check (K1)

`cobaya-install planck_2018_lowl.TT` installs the Blackwell-Rao **C_ell-level**
low-ell TT likelihood (`cov.txt` 249x249, `mu.txt`, `cl2x_*.txt`), not a map/a_lm
ensemble. The K1 morphology statistics depend on a_lm phases, so a C_ell-only
product cannot generate the matched null. **cobaya does not unblock K1's E2E map
null** -- it serves likelihood data, not FFP10/NPIPE simulation maps. Recorded in
`scripts/k1_global_maxscan.py` + `docs/research_program/BLOCKERS.md`.

## Changes

- `scripts/pr08_006_joint_artifact.py` (new) -> `docs/generated/pr08_006_joint_artifact.json`:
  joint pushforward over the discharged sectors -- Omega_tilt **measured** (K5),
  Sigma^2 **partial** (K1 look-elsewhere), W^2 + Omega_k **fail-closed** (K6 structural
  no-go + no channel; NOT zeroed). Data rank 2 reported separately from
  prior-conditioned rank; no collapsed x_C scalar; no MIO-as-odds; no scalar->family.
  `tests/contracts/test_pr08_006_joint_artifact.py` enforces the discipline.
  Ticket `PR08-006.yaml` -> discharged.
- `docs/research_program/BLOCKERS.md`: PR08-006 discharge note + cobaya finding + a
  hygiene-pass finding documenting that 6/7 residual contract failures are a
  **structural `git_commit_or_worktree_state` embedding** issue (the generated file
  pins HEAD+dirty, so any commit re-stales it; only a generator refactor that drops
  that field fixes it durably) and the 7th is the manuscript pdf-lint debt.
- `scripts/build_pr04_research_audit_package.py`: +pr08_006 JSON + script; deltas r108..r129.

## Hygiene pass outcome

Confirmed the 7 residual pre-existing contract failures are not regeneration-stale:
6 embed a HEAD-tracking git_state and re-stale on every commit (durable fix = drop
`git_commit_or_worktree_state` from the emitters), 1 is genuine manuscript pdf-lint
debt. Regenerating them only churns, so it was reverted. The one durable field-based
failure (figure claim-lane policy) was already fixed in rev-r128. The generator
refactor is left as a separate, scoped PR.

## Claim discipline

PR08-006 reports only identified sectors; blind sectors are fail-closed and explicit;
no combined scalar over blind sectors; no MIO-as-odds, no scalar->family, no
native-atlas/geometry claim.

## Validation

| Command | Status |
| --- | --- |
| `pr08_006_joint_artifact.py` + `--check` | data rank 2; fail-closed {W2, Omega_k}; up to date |
| `pytest tests/contracts/test_pr08_006_joint_artifact.py` | 4 passed |
| `cobaya-install planck_2018_lowl.TT` | installs C_ell likelihood (not maps) |
| research-audit package + `--check` | byte-deterministic |
