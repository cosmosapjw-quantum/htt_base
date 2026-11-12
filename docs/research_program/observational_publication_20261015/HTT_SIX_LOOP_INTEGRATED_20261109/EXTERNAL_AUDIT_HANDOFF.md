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

## 9. Re-fit and boost-tension analysis (v4; supersedes v1-v3)
Hypotheses H_0, H_loc, H_tilt, H_mix were re-fitted on six real-data channels (Quasars, Radio, Gaia, SNe, PV, DESI; n=1526) **without** the Planck PR4 channel (NPIPE exclusion honoured; probes constructed lazily, test-first). Fixed-psi and free-psi modes; input SHA256 in the result file; see `REFIT_RECEIPT.json` and `BOOST_TENSION_RECEIPT.json`.
Likelihood defects found and fixed test-first: SNe and PV predictions were compared with data in a different convention (absolute/mu(z) vs residual); the untraced count-dipole response constants (3.50/3.30/3.50) were replaced by the derived R = 2 + x(1+alpha) with declared slopes and an alpha grid {0.5, 0.75, 1.0}. Superseded result files are kept.
Findings (point estimates): SNe 433/490 and PV 903/1000 adequate. The count dipoles imply |beta_MO| = 3.7e-3 to 4.4e-3 (alpha 1.0 to 0.5), i.e. 3.0-3.6x the CMB-dipole speed; per-axis statistical sd 3e-4 to 7e-4. SNe and PV are too weak to test this (sd >= 4e-3; cost of the count best fit dchi2 ~4 and ~6.5 for 3 dof), so no conflict is claimed (an earlier "tension" statement is withdrawn). Gaia does not constrain beta_MO in this likelihood (glide response absorbed by nuisance modes; design question open). H_loc is best by BIC for all alpha, H_mix saturates the Gaia block, beta_RM enters no channel.
**Provenance defect:** two of the four count blocks (Quaia G<20.5, RACS) are hard-coded literals in the likelihood module with no source file; the Gaia glide response (0.92) is still untraced. No physical reading is warranted until the literals are replaced by sourced values. Inputs for the other count blocks and Gaia are earlier derived result files. No uncertainties from sampling, not the CORE-07 production inference, no claim of departure from FLRW.
