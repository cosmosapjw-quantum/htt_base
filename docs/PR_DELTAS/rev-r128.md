# REV-R128 - Measured-rows report section + discharge figure + figure-manifest hygiene

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only_measured
transfer_source: mixed_none_and_cf4_wf_proxy
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Surface the rev-r127 real-data discharges in the research report + figures, and
clear the figure-manifest hygiene the audit flagged.

## Changes

- `scripts/make_blocker_discharge_figures.py` (new) -> `figures/current/fig_blocker_discharges.png`:
  three-panel measurement figure from the committed discharge JSONs (K1 local+global
  p, K5 coverage bars, K6 vorticity-vs-shear). Content-addressed sidecars (no git
  state), `--check`; claim-gated manifest. `tests/contracts/test_blocker_discharge_figure.py`.
- `docs/final_report/main.tex` (21 -> 22 pp): new \S10 "Measured rows from real data
  (K1/K5/K6)" with the figure + the K5/K6/K1 results; the standing-blocks \S updated
  (K5/K6 closed, K1 partial, K6 = structural no-go). `pdf_claim_lint` 0 failed
  (linted to scratch; canonical manuscript lint report untouched).
- Figure-manifest hygiene (audit F2/F3): added `promotion_blockers` to the PR04 paper
  figures (`make_pr04_paper_figures.py`) and `caption_policy` + `promotion_blockers`
  to the observed CF4 figures (`make_cf4_affine_flow.py`, `make_cf4_bulkflow_likelihood.py`);
  fixed the K5 figure title "minimum-variance" -> "weighted-GLS". This clears
  `test_current_and_observed_manifests_carry_claim_lane_policy` (8 -> 7 pre-existing failures).
- `scripts/build_pr04_research_audit_package.py` + `build_final_report_audit_package.py`:
  +`fig_blocker_discharges`, +discharge JSONs, +`make_blocker_discharge_figures.py`.
- Regenerated dependent artifacts: external audit package, publication claim freeze,
  both research/final-report audit packages (all byte-deterministic, --check clean).

## Claim discipline

All measured rows are model-independent OBSSTAT descriptors; K6 is a structural
no-go; K1 is a partial (look-elsewhere) discharge under a LambdaCDM null with the
E2E null still blocked. No Bianchi family, geometry, anisotropy-evidence, or
native-solver claim. `pdf_claim_lint` 0 failed / 0 warning.

## Validation

| Command | Status |
| --- | --- |
| `latexmk -pdf main.tex` | PASS; 22 pages |
| `pdf_claim_lint` (scratch) | Failed 0, Warning 0 |
| `make_blocker_discharge_figures.py --check` | up to date |
| claim-lane policy contract | PASS (was failing pre-existing) |
| audit_package_generator + both package contracts + figure contract | passed |
| full `tests/contracts` | 7 pre-existing stale-artifact failures remain (was 8) |

## Residual hygiene (documented, not blocking discharges)

7 pre-existing stale-generated-artifact contract failures remain (CF4++ LNB report,
code-capability manifest, current-manuscript-figure generator check, external-research
input inventory x2, manuscript audit-repair matrix, semantic-firewall fuzz). These
predate this work; several embed a HEAD-tracking `git_state` or reflect the manuscript
PDF carrying 2 lint findings under the current linter, and need a dedicated
regenerate-and-bless pass.
