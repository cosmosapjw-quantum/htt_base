# REV-R140 - Local-boost vs global-tilt statistical-formalism note

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none_observed
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Write a self-contained, context-free, rudimentary LaTeX note (-> PDF at repo root)
describing the updated statistical formalism for how the current code distinguishes a
local boost from a global tilt, able to justify answers to the "Leaky Universe" toy test.

## Deliverable

`htt_local_global_formalism.{tex,pdf}` at repo root (5 pp). Text + one table only, no
`\includegraphics`. Built via the htt-latex-paper-build + htt-local-global-discrimination
skill workflows.

Code-grounded content:
- The two velocity-like sectors: Omega_tilt (global tilt / bulk flow) vs the observer boost
  beta (local, l=1 frame effect, not a sector of g).
- The leading-EGS-order response map D (`egs3_graded_comparator._RESPONSE_SUPPORT`):
  quadrupole -> Sigma^2, dipole -> Omega_tilt; block-diagonal in the two velocity sectors
  at O(beta), explicitly labelled leading-order-only.
- The O(beta^2) kinematic quadrupole (Doppler/aberration of the monopole, mu^2 = 2/3 P_2 +
  1/3): a boost deposits a beta^2 l=2 signal aligned with v-hat, so D gains a
  D_{quad,Omega_tilt} propto beta^2 entry -> non-block-diagonal -> nonzero Fisher off-diagonal
  F_{Sigma^2,Omega_tilt} = D^T C^{-1} D block. This is the correct content of the toy test.
- The five structural safeguards in the code that keep the leak from becoming a false
  measurement: (1) l_min=2 dipole removal; (2) Sigma^2 never reported as measured (K1
  partial, fail-closed); (3) `axis_to_cmb_dipole_deg` boost-alignment statistic (calibrated
  vs the null); (4) Omega_tilt anchored independently by CF4 velocities (K5), not the CMB
  quadrupole; (5) the `isotropy_gap` local/global firewall forbidding "global tilt" in G_F.
- Honest limitation: no kinematic-quadrupole deprojection in the OBSSTAT low-l path yet (the
  O(beta) Challinor kernel in `boost_kernel.py` is Boltzmann-source-side).
- The two upgrades made precise: (1) kinematic projection operator,
  Sigma_tilde^2 = Sigma^2 - alpha Omega_tilt^2 with analytic alpha; (2) coupled Fisher prior
  carrying F_{Sigma^2,Omega_tilt}. Shown to be point-estimate/Bayesian duals attaching to the
  existing response-design/`identifiable_rank` machinery.
- Explicit Q1-Q4 answers to the toy test.

## Claim discipline

Diagnostic-only; Omega_tilt is a model-independent kinematic descriptor; Sigma^2 stays
partial (not a measured amplitude); local boost and global tilt kept distinct. The only
"detected"/"identified" strings are negations.

## Validation

| Check | Status |
| --- | --- |
| `latexmk` | exit 0; 5 pages |
| undefined references | 0 (2-pass) |
| overfull boxes | none > 20 pt |
| claim-firewall scan | clean (negations only) |
