# MES tensor research integration — local continuation

Repository: `cosmosapjw-quantum/htt_base`
Branch: `changeset/mes-tensor-research-integration-20260830`
Inspected source base: `e7dc5fd99c6574eee1e93b6a2ec05beb394de034`
Source tree: `439fc5ecc924e10b4fc5ebfb970733691a6fc3a3`

## Authority and scope

The current report and external-referee withdrawal on `codex_emergency` supersede historical WU-006–008 success labels. Do not restore those claims. The 78-candidate proof ledger is an author-derived analytic/CAS adjudication, not an independent review or proof-assistant certificate. Correct the symmetry-group, nuisance and confidence-coverage qualifications before using its results.

The isolated connector test is PR #439, merged into `connector-smoke/mes-synthesis-20260830-base`, not a research or production merge.

Use a fresh isolated worktree. Preserve the user's canonical checkout, recovered untracked files, raw maps, private evidence and legacy cleanup. Never query, rerun or gate on GitHub Actions. No downloads, environment rebuilding, research merge, approval, force-push or native-BASS substitution are authorized by this prompt.

## First actions

1. Read the live branch, its diff against the exact source base and all local integration tests. Do not assume a file exists because an earlier conversation named it.
2. Verify that the exact source commit is an ancestor and its tree equals the value above. Record the actual candidate head/tree before executing.
3. Run only the added/affected algebra, representation, codec and integration tests; preserve their exact commands and output. A partial source-projection test is not a full repository integration test.
4. If source files referenced by the integration are absent, report the exact missing path instead of fabricating an import, alias, solver, expected rank or successful receipt.

## Historical inputs, not historical conclusions

Read frozen Git objects at `ccba350d7b725b227c64436e32af96abfe786449` only as input data:

- `docs/generated/planck_pr3_paired300_irrep_carrier/carrier.npz`
- `docs/generated/planck_pr3_paired300_irrep_carrier/metadata.json`
- `docs/generated/pr315_planck_smica_feature_replay.npz`
- `docs/generated/planck_mes_smica_cmbonly_999_irrep/observable_irreps.npz`
- `docs/generated/planck_mes_smica_cmbonly_999_irrep/observable_irreps.json`

The paired carrier SHA-256 is `0a296c21902b691eb2e2b68a9b39f626020aa8c2b14fb93a1b12116215886b93`.
The frozen scalar NPZ SHA-256 is `b262425eb4f3a879513c02644bcbdd3ab313e487d101f6a29cb85284c30f845b`.
The historical source tree is `e91b8a4f57777c71c2bf1fc0f8c21395753481ba`.

Paired NPZ uses `observed_real_alm`, `null_real_alm`, `row_ids`, `real_alm_layout`. The 999-row NPZ uses `carrier_rows` and `scalar_features`. Its stored `q_components`, `o_components`, old invariant features and old ranks are withdrawn and must not be reused as corrected outputs. Use `allow_pickle=False`, reject unsafe dtype, missing keys, nonfinite entries, unexpected shapes or row order. Never reopen FITS maps merely to perform this representation repair.

Paired row order is `PLANCK-PR3-SMICA-OBSERVED`, then `FFP10-SMICA-CMBNOISE-00000` through `00299`. CMB-only row order uses `FFP10-SMICA-CMB-00000` through `00999`, excluding only `00970` and including `00818`.

## Scientific invariants that must be executed

Stored coefficients are `c_l0=a_l0`, `c_lm,c=sqrt(2) Re(a_lm)`, `c_lm,s=-sqrt(2) Im(a_lm)`. The carrier metric is Euclidean. Do not apply the unscaled-complex `diag(1,2,2,...)` metric to it.

For temperature STF tensors:

- `Q:Q = 15/(8*pi) * ||c_2||^2 = 75/(8*pi) * C_2`.
- `O:O = 35/(8*pi) * ||c_3||^2 = 245/(8*pi) * C_3`.
- Validate the actual exporter-to-consumer boundary with an independent spherical-function oracle and proper-rotation covariance, not merely self round-trip.

MES input epsilon is the dimensionless PSTF norm, not sky RMS:

- `epsilon_2 = sqrt(15/2) * sqrt(5*C_2/(4*pi*T0^2))`.
- `epsilon_3 = sqrt(35/2) * sqrt(7*C_3/(4*pi*T0^2))`.
- `B_sigma = (5/3)*epsilon_1 + 3*epsilon_2 + (3/7)*epsilon_3`.
- `B_omega = (10/3)*epsilon_1 + (2/15)*epsilon_2`.
- `U_sigma = (3/2)*B_sigma^2`; `U_omega = (3/2)*B_omega^2`.

Declare T0, units, residual-dipole attribution, congruence and derivative-premise assumptions explicitly. Keep historical scalar-function values as historical outputs; do not treat them as the corrected original-MES physical ceiling. Do not tune tolerances or expect a particular new family rank.

## Full tensor information versus low-order bispectrum

Keep the original corrected Q/O arrays. Ordinary power plus cubic bispectrum does not separate their generic nine-dimensional SO(3) quotient.

For the explicitly nondegenerate chart set `v=O:Q`, `K=[v,Qv,Q^2v]`. Preserve the six values `(tr(Q^2),tr(Q^3),v.v,v.Q.v,v.Q^2.v,det(K))` and all ten symmetric contractions `O(K_i,K_j,K_k)` for `i<=j<=k`. These sixteen polynomial contractions separate generic proper-rotation orbits; they add information relative to a low-order bispectrum, not relative to the full Q/O tensors.

Use explicit scaling and conditioning diagnostics. Singular or ill-conditioned charts retain their original tensors and a typed unavailable chart; do not invent transverse axes or delete the row. Record SO(3) versus O(3): the four even pure-octupole invariants do not encode SO(3) chirality.

## Local output and scientific admission

Write new outputs only under a new, nonexisting generated-results directory in the isolated worktree. Keep private execution details under `/mnt/sn850x2t/htt_base_e2e/workdir/analysis/mes_tensor_research_integration/`. No raw data or private full manifests enter Git.

Separate these outcomes:

1. Corrected representation and normalization: validate every available carrier row.
2. Recalculation under previously frozen questions: retain original families/tails and document semantic corrections.
3. Newly proposed Krylov/kernel/response statistics: exploratory registry and separately calibrated power study; no retroactive confirmatory claims.
4. CMB-only-999 sensitivity: descriptive because the noisy observation is not exchangeable with a noise-free null ensemble. Shared CMB rows do not constitute independent replication.
5. Physical inverse: synthetic/conditional research only. The ideal Bianchi-I inverse requires absolute positive temperature including monopole/dipole; the retained ell=2..5 carrier is not that input. Unrestricted intrinsic octupole destroys standalone boost identification; orthogonal residual nuisance does not.

Use a pending terminal first. No code may self-attest an independent review or visual PASS. Commit the candidate code before review; bind the external review to exact candidate head/tree, experiment registry, inputs and output manifest. An evidence-only closeout must not modify reviewed source. A failure preserves all numerical outputs and reports its narrow cause, rather than rerunning raw maps or creating a new governance package.

## Next scientific work after corrected carrier verification

Freeze one bounded analytic response/power experiment, with explicit template coefficients, amplitudes, rotations, calibration/evaluation split, noise and intrinsic nuisances. Do not reuse the withdrawn unscaled-carrier injection specification. Report coverage under joint exchangeability, not coverage conditional on every fixed reference pool. Use the correct bounded-body likelihood-ratio score rather than the cone formula unless the alternative is actually a cone.

The sharp noncommuting endpoint bounds and positive-quadratic inverse are conditional mathematical tools. They do not establish native BASS validity, real-data global tilt, vorticity, Bianchi-family identification or publication readiness. Claim strength may increase only when the relevant validity, power, robustness and identification evidence is acquired.
