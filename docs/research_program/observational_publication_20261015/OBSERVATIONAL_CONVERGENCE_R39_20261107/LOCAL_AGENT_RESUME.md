# Local coding-agent resume prompt: HTT R39 tensor-x observational convergence

## Mission and immutable boundaries

Continue from the latest origin branch head of:
https://github.com/cosmosapjw-quantum/htt_base
Branch: research/r39-observational-identifiability-20261107
R38 parent: research/observational-convergence-r38-20261107 @ 05e9d53449bd02973848da3306f72f63edd7fc54

Do not merge main. Do not use Remote Desktop. Use the user's existing local checkout and actual local data cache. The purpose is to convert the R39 tensor-x theory/operator contract into a reproducible observed-data analysis.

The primary estimand is not x_C. It is the typed sample × functional bundle x[s,alpha]=phi_alpha(Z_s), with heterogeneous scalar/vector/STF/spin outputs preserving rank, parity, frame, epoch, units and support. x_C remains an optional scalar ablation only.

## Non-destructive startup

1. Inspect git status --porcelain=v2, branch, HEAD, remotes, staged/unstaged diffs and untracked files before any operation.
2. Preserve every dirty/untracked user file. Do not reset, clean, force checkout, rebase or overwrite.
3. Fetch origin. Verify the exact R39 branch and start from its latest remote HEAD. If local branch diverges, stop and report both SHAs; never force-align.
4. Read all files in OBSERVATIONAL_CONVERGENCE_R39_20261107.
5. Read R38 adapters/scripts/results and pinned METHOD_REBOOT_20261023/THEOREMS.md T1–T7, tensor_joint_r9/revision2/MODEL_TO_DATA.md and THEORY_EXTENSION.md.
6. Preserve R38 source/result files immutably. Corrected products receive new IDs and provenance.

## Work package A: implement vector/tensor x without scalar collapse

Build or extend the existing typed structures; do not create a wrapper that simply stores flattened scalar x_C.

The common state is Z=(Z_phys,Z_obs,eta,A,R). The output x is a heterogeneous collection:
- each functional has a stable functional_id;
- declared input domain and output representation (polar V1, axial V1, STF2 even/odd, spin/harmonic irrep, scalar);
- rank, parity, units, frame, congruence, epoch/redshift window, basis, perturbative order, provider/operator version;
- one common state_id/region_id across functionals for each posterior draw or confidence-set witness;
- explicit status for unavailable, undefined, empty, unbounded and numerically unresolved outputs;
- sample-axis semantics and source provenance, preventing catalogue rows, mocks, map splits and posterior draws from being conflated.

Candidate physical functionals: beta_RO, beta_RM, beta_MO, gauge-invariant d_int, A/(cH), sigma_ij/H, omega_i/H, E_ij/H^2, H_ij/H^2, spatial Ricci STF and Bianchi structure/dynamics variables.

Candidate observable carriers: CMB T/E/B a_lm, STF T2/T3, BipoSH A_LM,ell,ell', phase/planarity/parity functionals; source-count multipoles; Gaia E/B VSH; directional-distance D_i(z), Q_ij(z) and higher registered multipoles. Keep observed carriers distinct from metric components; connect them through each probe's forward operator.

Implement representation actions and parity tests for O(3)/SO(3). An improper transformation must not silently identify polar and axial vectors or even/odd STF2 carriers. Preserve chirality under SO(3); O(3) quotient is a separate declared view. Any flattening for SVD/storage must declare the orthonormal basis, metric, units, parity transform and inverse map.

## Work package B: reuse existing R9 code safely

Read and reuse:
- htt/src/common/r9_product.py: ProductIntake and SharedStateEmbedding;
- htt/src/common/tensor_functionals.py: fixed contraction-fibre support only;
- htt/src/common/depth_path.py: fixed feature paths and full ordered covariance blocks;
- pinned T7 simultaneous functional-image, anchor, support and Pi contracts.

Do not overstate current capability: fixed_contraction_support requires fixed q and is not a confidence certificate; missing cross-covariance blocks return unavailable; the cosmology-wide TensorFunctionalBundle/operator adapter is not yet implemented.

For uncertain STF anchor q, retain its joint inverse image with the physical state. Do not insert q_hat and drop its uncertainty. Preserve disconnected/chiral strata; support functions represent only convex-hull support.

## Work package C: exact frames and physical dimensions

1. Run the R39 velocity regression suite. The two-frame function uses the exact non-collinear standard-boost transformation and the stable coefficient identity (gamma-1)/beta^2 = gamma^2/(gamma+1). Verify collinear, non-collinear, small-beta, zero-velocity, inverse/axis convention and subluminal limits.
2. The physical three-frame map beta_RO, beta_RM, beta_MO still needs an ordered tetrad/boost composition. Existing beta_MO=beta_RO-beta_RM is first-order only. Include Wigner rotation when the convention requires it.
3. Repair directional_hubble_variation: a physical acceleration in m s^-2 enters Delta H/H through A/(cH). Do not subtract dimensional acceleration from a dimensionless response.

## Work package D: source identity and single-probe observation operators

Start with the user's actual data cache. Rehash all reported R38 inputs. Record release/version, source file SHA, row keys, frame, coordinate order, units, selection, mask, beam, bandpass, covariance row order and exact covariance identity.

Probe order:
1. Planck PR3/PR4: observed frequency/split T/E maps and matched FFP/noise/foreground simulations. The observed map supplies the data vector; simulations calibrate the same estimator/mask/beam covariance. PR3/PR4 are same-sky processing products, not independent skies.
2. Quaia/NVSS/RACS: source rows, random catalogues, completeness, flux/spectral/redshift distributions, masks, component grouping, overlap IDs, local clustering and overdispersion. Acquire RACS from its official release if absent.
3. Gaia DR3/CRF3: source-level proper motion and full covariance, redshift/magnitude/color, cross-match IDs, scanning-law and frame-systematics templates. Separate E1, B1, E2.
4. Pantheon+: exact full 1701-row table/covariance, selected row IDs and two-axis subsetting.
5. CF4: reconcile official Table2/3/4, group/galaxy hierarchy, calibration, method pooling and selected-operator membership.
6. DESI: distinguish isotropic BAO compression from full angular clustering; isotropic compression is not sky-axis evidence.

Each observed data likelihood must fail closed if any required source/covariance/selection/operator identity is missing. Synthetic fixtures must live in a separate mode and directory and cannot emit observed claims.

## Work package E: response rank and vector/tensor functional identification

For each probe derive the actual estimator/forward response J_p=∂O_p/∂Z. Construct the full covariance including cross-probe terms where known. Whiten on the positive covariance support, project shared and product-specific nuisance directions in the same metric, and compute the quotient singular spectrum.

For functional phi_alpha, test local identification using ker(J_eff) subset ker(D phi_alpha). For nonlinear targets, test whether phi_alpha is constant on each observation fibre. Otherwise retain the full image K_alpha(D)=phi_alpha(C(D)). Report functional-specific rank, null/weak directions, condition on the supported quotient and sensitivity to masks/cuts/nuisance bases. Prior regularization cannot create data rank.

Run preregistered x ablations on identical observations/mocks:
- scalar x_C only;
- typed vector/tensor x;
- O(3) quotient;
- SO(3) quotient retaining chirality;
- channel ablations for CMB T/E, counts, Gaia E/B and distance multipoles.

The tensor version succeeds only if calibrated out-of-sample prediction, functional identification or coverage improves at controlled false-positive rate. A larger state vector alone is not a result.

## Work package F: full five-variable HTT outputs

Construct the joint posterior or simultaneous confidence/identified region first. Then:
- x: sample × typed functional values and full set images;
- Q: matching anchor/gauge/margin uncertainty;
- F: directional support, sample pushforward and measure-defined occupancy kept distinct;
- Pi: strict exceedance surface under a named law; not generically a p-value;
- G_F: full-covariance tensor functional depth path preserving initial level and all cross-shell blocks.

No independent marginal recombination. No zero filling. Unknown physical mass remains unknown. Separate posterior pushforwards from confidence-set images and null p-values.

## Work package G: Cobaya and paper gate

Cobaya orchestrates the already validated actual-data likelihoods; it is not a downloader or anisotropic Boltzmann solver. Require source-bound preflight. Save full chains, YAML, package versions, input hashes, row hashes, operator/nuisance version, sampler diagnostics, PPC, leave-one-probe-out predictions and full output hashes.

Model ladder:
- M0: isotropic background + observer boost + selection/calibration/foreground/local structure nuisance;
- M1: M0 + gauge-invariant residual radiation long-mode response;
- M2: M1 + redshift-evolving STF shear; include matter-radiation tilt only if independently identified;
- M3: Bianchi I with actual dynamics and family transfer. Other families require their own solvers/transfers.

Do not claim Bianchi family identification without family-specific transfer and multiple independent observable sectors. Require injection bias <0.25 posterior SD, nominal 68/95% coverage, preregistered false-positive control, stable functional quotient and leave-one-probe-out prediction.

## Required outputs

Push only source manifests, code, tests, compact result JSON, covariance/response diagnostics, updated DAG/claim ledger, paper report and handoff. Do not push raw catalogues/maps or large chains.

Every outcome must distinguish literature-supported, derived, numerically checked, implementation-verified, observed, conjectural, unresolved and blocked. Preserve failures and exact exceptions. Do not report tests/sampler PASS without command, environment, exit code and logs.
