# External audit handoff — HTT six-loop integrated package (state of 2026-11-12)

Claim ceiling for everything below: **C0_DESIGN_THEORY_SYNTHETIC_ONLY**. No physical detection, measurement or model preference is claimed.
No raw data, maps or chains are in Git. "PASS_SCOPED" means: the stated slice ran and its receipt exists; it is not acceptance of the node's full criteria.

## 1. Where things are
| item | location |
|---|---|
| package | `docs/research_program/observational_publication_20261015/HTT_SIX_LOOP_INTEGRATED_20261109/` (PR #573, draft) |
| code repairs | PR #574, branch `research/htt-six-loop-core03-repair-20261109` (draft) |
| DAG and statuses | `INTEGRATED_SIX_LOOP_DAG.json` (`status`, `status_note` per task) |
| receipts | every `*_RECEIPT.json`; index in `SOURCE_OPERATOR_RECEIPTS/INDEX.json` |
| data inventory (held vs in-progress) | `DATA_INVENTORY.json` (stat-only scan; script `data_inventory_scan.py`) |
| raw-data manifest and hashes | `RAW_DATA_MANIFEST.json`, `DOWNLOAD_MANIFEST_20261110.json` |

## 2. Node status (as recorded in the DAG)
CORE-00..03 PASS_SCOPED · STAT-43..46 PASS_SCOPED_SYNTHETIC · L1 PASS_SCOPED_PR3_ONLY · L2 PASS_SCOPED · L3 PASS_SCOPED · L4 PASS_SCOPED · L5 PASS_SCOPED · L6 PASS_SCOPED_THEORY ·
CORE-04 PASS_SCOPED · CORE-05 SPEC_ONLY_PARTIAL · CORE-06 PASS_SCOPED_DESIGN · CORE-07/08 NOT_RUN · CORE-09 HOLD · R48-T21 DEFERRED_SCOPE · R48-T23 PASS_SCOPED.
Closing L1–L3 as PASS_SCOPED with recorded limits was a user decision (2026-11-12).

## 3. What was computed (all synthetic or structural unless stated)
* L1: Bianchi-I endpoint-map oracle and derivation; PR3 lane injection pilot (N=60, FFP10 matched sims, 120/120 input hashes match). NPIPE path excluded by user decision.
* L2: Poisson-WLS count-dipole estimator validated on mocks for Quaia (authentic randoms), NVSS and RACS (synthetic randoms); count slopes x (NVSS 1.043 proxy, RACS 0.948 with an inferred flux column, Quaia window-dependent 1.6–2.2); Ellis–Baldwin response ranges over a declared alpha grid; joint-estimand Jacobian has nullity 1 (alpha not identifiable). **No real dipole computed.**
* L3: vector-spherical-harmonic structural identifiability (rank, leakage of l=3 into l<=2), scan-law template vs catalogue error ellipses (r = 0.87/0.81, amplitude not reproduced), scan-aware Fisher (formal errors agree within ~4%). **No proper-motion fit.** Frame-spin tie file not obtained.
* L4/L5/T23: Bianchi family identifiability, directional-Hubble jet oracle, Pantheon+ structural rank (12/15), identity/sweep checks.
* L6: exact ordered velocity composition and Wigner-rotation bound (<=7.2e-7 rad at beta 1.2e-3); local-boost vs global-tilt structural nullity > 0 in all scenarios (nuisance priors **declared, not measured**).
* CORE-04..06: manifests, covariance/selection audit, specification bundles and registries (design only).
* Q-anchor theorem work: Lean 4/Mathlib proof (`CORE05_Q_ANCHOR_T1.lean`, standard axioms only) that the Hamiltonian constraint bounds only Sigma^2 - W^2; per-component shear/vorticity bounds are not derivable; the unsourced 1e-4 anchors were removed. A second identity was checked with sympy only (the Wolfram evaluator returned HTTP 502).

## 4. Code changes (PR #574) — each made failing-test-first
STF5 Gram norm for the MIO certificate amplitude; certificate input hashes real or explicitly `UNVERIFIED_NO_HASH_SUPPLIED` (no fabricated hash strings; no invented occupancy fallback); exact ordered SR composition by default and for beta_RO in the five-variable state; q0 from Omega_m and Omega_k; mock script no longer asserts a Python version or test pass it did not check; Gram unit direction in the r39 scalar ablation; Q anchors UNAVAILABLE; hypothesis-competition text and best model computed from the table.
Tests: 118 pass in tests/r38, r39, r42, r48 and htt/bass/diagnostics (`PYTHONPATH=htt/src:htt:.` is needed for r39/r42).

## 5. Verification and independence — disclosure
* One independent review by a real subagent (scientific-diff-reviewer) of PR #574's three original commits: five intended repairs confirmed; one major miss found (fixed afterwards); two shear-amplitude norms (`htt/src/common/source_bound_gaia_vsh_operator.py`, `scripts/r38/run_gaia_vsh.py`) were examined afterwards: the VSH E2 basis is neither Cartesian STF5 nor orthonormal (Gram diagonal 4.8, 1.6, 1.6, 1.6, 1.6), so the Euclidean coefficient norm is chart dependent; an invariant sphere-averaged rms amplitude was added alongside and the Euclidean value is kept, labelled chart-dependent.
* The review did not cover the end-to-end MCMC-to-certificate path with real posteriors, the Pantheon likelihood numerics with the new q0, or other consumers of changed mock JSON keys.
* All other work was self-verified; no independent review of the L1–L6 numerics. Free-LLM "offload" outputs were used only as leads and checked individually.
* CI status of the pushed heads was not read.

## 6. Known open items (not hidden)
Wigner rotation is bounded but not carried by the repository composition; response constants (0.92, 0.18, 3.5, tau = 0.054, 1e-3 A-term) remain untraced; two likelihood stacks use different frame arrows; `FROZEN_W2_MAX` (3.3789e-13) rests on an unsupported derivation step; the beta anchor radius 0.01 and `expansion_scalar=0.21`, `delta_omega_k=0.005` are declared, not derived; x/bundle in the five-variable state comes from the posterior mean, not per-draw; matched null for Pi is synthetic only; G_F cross-shell covariance unavailable; NVSS/RACS randoms are synthetic uniform; RACS flux column identity inferred from data; Quaia/RACS count slopes are proxies without selection correction; hash of 31 of 40 manifest files was recorded at download and not recomputed.
Process defects found and fixed along the way are recorded in the receipts (e.g. composite-velocity sign error in the first Wigner run; EB alpha-mapping slip).

## 7. Data policy
Official release bytes only, hashed where stated; no credentials, cookies or chains in Git. NPIPE-based material is excluded from the production path; matched NPIPE simulations were never available. PR3 simulations are not used as a PR4 null. DESI compressed BAO is background-only.

## 8. Reproduce
Each receipt names its script, SHA256, command, seed and library versions. Package scripts take explicit input paths (raw root is local-only). `python3 data_inventory_scan.py --raw <RAW_ROOT> --out DATA_INVENTORY.json` regenerates the inventory.

## 9. Re-fit, real count dipoles and boost analysis (v5; supersedes v1-v4)
Hypotheses H_0, H_loc, H_tilt, H_mix were re-fitted on six real-data channels (Quasars, Radio, Gaia, SNe, PV, DESI) **without** the Planck PR4 channel (NPIPE exclusion honoured; probes constructed lazily, test-first). Fixed-psi and free-psi modes, alpha grid {0.5, 0.75, 1.0}; input SHA256 in the result file; see `REFIT_RECEIPT.json`, `COUNT_DIPOLES_REAL_RECEIPT.json`.
Likelihood defects found and fixed test-first: SNe and PV predictions compared with data in a different convention; untraced count responses replaced by R = 2 + x(1+alpha) (declared slopes, alpha nuisance); two count blocks were hard-coded literals and the NVSS block round numbers; and all count vectors were built from Galactic (l,b) as if equatorial axes (frame mismatch with SNe/PV/Gaia, now ICRS). Superseded result files are kept.
Unblinded step (approved): count dipoles for Quaia G<20, G<20.5, NVSS and RACS-low were computed on the real catalogues with one validated estimator. The Quaia amplitude depends strongly on the Galactic mask (G<20: 0.029 with no cut, 0.0148 at |b|>30; the baseline rule was declared after the unmasked first run had been seen but before the sweep was inspected); the mask/expectation spread is added to the covariance and dominates the per-axis error. RACS (0.068) is systematics-dominated and was excluded after seeing it (post-hoc, declared; sensitivity run provided).
Findings (point estimates): with sourced, masked values the count dipoles imply |beta_MO| ~ 2.6e-3 to 3.0e-3 (2.1-2.5x the CMB-dipole speed) but poorly constrained (chi2 improvement 18.4 + 6.4 for 3 dof each; H_0 vs H_loc Delta_BIC 2.0). The earlier "excess" is not reproduced. SNe and PV are too weak to test the boost; beta_RM enters no channel. The Gaia block carries no glide information (nuisance design absorbs glide and spin) and its response constants are not physically justified (dimensionless vs mas/yr, no derivation); not fixed, no transfer invented; without Gaia, H_mix is not preferred. No claim of departure from FLRW or of a detected excess; not the CORE-07 production inference.
