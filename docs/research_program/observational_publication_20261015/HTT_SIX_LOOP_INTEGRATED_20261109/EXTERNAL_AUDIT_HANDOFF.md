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
* One independent review by a real subagent (scientific-diff-reviewer) of PR #574's three original commits: five intended repairs confirmed; one major miss found (fixed afterwards); two shear-amplitude norms (`htt/src/common/source_bound_gaia_vsh_operator.py:199`, `scripts/r38/run_gaia_vsh.py:191`) need a decision on the VSH coefficient chart and were **not changed**.
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

## 9. Re-fit (added after the user's re-fit decision, 2026-11-12)
Hypotheses H_0, H_loc, H_tilt, H_mix were re-fitted on six real-data channels (Quasars, Radio, Gaia, SNe, PV, DESI; n=1526) **without** the Planck PR4 CMB channel (NPIPE exclusion honoured; the likelihood now constructs only enabled probes, test-first). See `REFIT_RECEIPT.json` and `REFIT_HYPOTHESES_NO_CMB_RESULT.json`.
Point estimates only. Fit adequacy is poor (SNe chi2 ~34000/490, PV ~13700/1000), beta_RM does not enter any enabled channel, and the fitted |beta_MO| (4.9e-3) is not an observer-velocity estimate. The BIC ranking is not evidence for any hypothesis. No claim of departure from FLRW is made. This run is not the CORE-07 production inference; input-file hashes for the loaded data are not recorded in the receipt (open item).
