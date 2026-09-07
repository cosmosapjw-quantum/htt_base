# Code and data reuse after the mock reviews

MAIN, 2026-09-07. This is a source-informed capability inventory, not a successful checkout build or a workstation-wide data verification.

## Scan scope and source identity

The repository default is `research/pr04-multicomponent`, freshly resolved to `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`. Root metadata/tree, branch collection/searches, directory inventories and targeted code searches were read. The complete `htt/src/common` tree at `22693c4b8632dae2eb77ad157c35517873454e2b` returned `truncated:false`. Its bodies are not all reviewed merely because their names were listed. The newer WU010/WU011 and accepted decoder/report branches were inspected separately because default-branch search does not include unmerged branches.

The structure contains multiple lineages and mirrored package roots: `htt/src/common`, `htt/htt/htt/infer`, `htt/obsstat`, and `external_fusion_round3/src/htt_ext`. A search miss in a guessed root is not absence of a feature. Conversely, matching names are not proof that the later scientific repair is present in the default branch. Local integration must pin actual imports and source bytes, not rely on directory spelling.

This scan covers the global structure and selected high-value code paths. It does not claim full semantic review of every historical file, all PRs or the roughly 1.5 TB local asset inventory. No installed package was imported or native suite executed here.

## Reuse matrix

| Component | Actual source read or identified | Reuse decision |
|---|---|---|
| Exact observer pullback and STF boost | WU010 PR442 snapshot `29427a1f7f2c5d46e43ffe03053c4ac13e969228`; `htt/obsstat/boost_response.py`, blob `7a8be6fdc56547ddd6363e730364d5843c014cf7`; companion `lorentz_sky_pullback.py` located | Reuse the actual positive-temperature pullback and STF maps, not a newly typed approximate aberration formula. Verify release boost/kinematic-quadrupole conventions. The inspected STF code has finite-input/domain checks. |
| Cyclic Q/O decoder | Accepted PR451 source `9f7d06dec0fce1c3a8a53fa5372c84d9c679c037`, `htt/src/common/mes_krylov_completion.py`, blob `f22132c7a3f247abd00f01cf1cce13dcad091070`; native 28-node evidence in PR456 | Preserve the exact source, typed failures, contraction-image and replay semantics. This is inherited accepted evidence, not a new test execution in this scan. Do not assume the default common tree already contains it. |
| Processed beta/source Jacobian | PR444 head `de73549c16ac6ceb63f924c86611e0a5ceb4711d`; `htt/obsstat/processed_boost_jacobian.py`, blob `10e52bbd4340d67470da7e17139c1d11a35daf52` | Reuse the (3,32,49) axis/source layout and explicit metric/monopole semantics. Construct a 32-by-3 velocity derivative only after contracting the source argument. Keep source-ell-6 physical and aliased contributions separate. |
| Processed fit, nuisance span and error geometry | Same PR444 lineage: `processed_boost_operator.py`, response/linearization/nuisance/matched-control modules; inspected `processed_boost_error_envelope.py`, blob `ab5d792c699566c40b0bca0230333991519d974c` | Reuse algebra/builders and their existing tests; do not label current finite-error membership proven. Existing Task7C rank-unresolved and historical source-equivalent/native distinctions remain. Upgrade with bounded cost and conditional high-mode covariance, not by replacing all modules. |
| Existing boost-BiPoSH diagnostics | `htt/obsstat/boost_biposh_residual.py` at PR442 snapshot, blob `98c757a315876cc9891fcc05b77e9e70b1921605`; first 130 lines inspected; `biposh_features.py`, `biposh_smica.py` located | Its own scope is a zero-parameter consistency statistic with a fixed dipole and a boosted FFP10 null. It is NOT an independently fitted high-ell velocity likelihood. Reuse synthesis/feature mechanics after input audit, not its historical inference label. |
| Bulk-flow likelihood | Default source; `htt/src/common/bulkflow_likelihood.py`, blob `6a64f5a9162a4e28c2186c3f95b8fe3929297de8`, substantial body read | Normalised Gaussian and sampler adapter exist, but selection weights are treated as precision/multiplicity. Do not use as the final CF4 physical likelihood until weight roles and distance/selection law are resolved. Preserve old records; add a typed consumer or bounded repair with explicit regression. |
| Bulk-flow and angular geometry infrastructure | Default tree lists `bulkflow_estimator.py`, `sky_geometry.py`, `healpix_selection.py`, `cf4_manifest.py`, tests | Useful candidate infrastructure; file listing is not implementation verification. Read the selected functions during fixed integration, not the entire historical repository again. |
| CF4 forbidden historical result paths | Default `cf4_p0_quarantine.py`, blob `ad641fef94cb815ec07269ecbcf21a74d83f08b7`, header/policy bindings read | The P0 quarantine explicitly blocks refuted numerical headlines. New inventory availability does not lift it. Use primary catalogue rows under a new likelihood, not cached old reported bulk-flow results. |
| Local/global decision code | Default `htt/htt/htt/infer/local_global_discrimination.py`, blob `995c516b01610753ccd688f7ad07397a6a3d769c`, first 200 lines read | Explicitly a skeleton/pre-inference diagnostic, not posterior odds. Keep overlap helpers where mathematically applicable, but do not wrap its heuristic features or threshold as physical tilt inference. |
| Frame typing | Default `frame_typed_algebra.py`, blob `ddca0043830a0723dd406348ead3d3cab8d78ba3`; `frame_contract.py` and `joint_anisotropy_state_v1.py` located | Types/metadata are reusable. A value-preserving legacy bridge or a symbolic beta plus minus-beta roundtrip is not an observed Lorentz transformation. New physical lanes use beta_RO/beta_RM/beta_MO with a real response. |
| Radial shell integration | Default `external_fusion_round3/src/htt_ext/lowell/transfer.py`, blob `b6b0adf5f2c0f4e5afc8df6668d20e1ab63ace51`, full body read | Reuse typed kernel and additive shell quadrature; it consumes an already supplied transfer and is not an Einstein–Boltzmann calculation. Verify convention/source identity and shared edges on refinement. |
| Low-redshift shell mock generator | Same directory `shells.py`, blob `63696a8e27f6659e200b2b84e5a209b006786c42`, full body read | Existing Gaussian-correlated shells and profiles are useful software fixtures only. The global 1/sqrt(1+z), local exp[-(z/0.18)^2] and 0.65/0.35 mixtures are explicitly toy assumptions, not physical discrimination templates. |
| Pole and external transfer utilities | Same lowell subtree `587d585e22f831f1d712bc742ab1ee5bf8dcf4fe`: alm.py, poles.py, identified.py, discrimination.py; broader remote/stats/plugin directories located | Candidate reuse rather than rewrite. Their names do not certify empirical adequacy. No shell contribution is relabelled an independently observed CMB at that redshift. |
| Finite-null ranks | Default `finite_null_ranking.py`, blob `8d5baac7cd974881bb4dac1f2beb6b59c5b5c5b0`, relevant functions read; cluster rank/dependency holdout/SBC modules located | Reuse exact Fraction rank and within-row max reduction after adding strict finite/status handling at the consumer. The code cannot itself establish exchangeability, and NaN observation scores must not become minimum p-values. |
| Physical functional/inference libraries | Default inventory includes tensor_functionals, vector_tensor_statistical_foundations/inference, joint_feasible_set, identified_set, weak_id_coverage, source_response_types and dependency_holdout | Retain typed domain separation and relevant tested mathematics. Large historical modules are not automatically current scientific authority; selected interfaces need pinning and a targeted test on the new integration snapshot. |

Source-level issues above are not labelled newly executed failures. The code/research loop in this session is: inspect actual implementation -> identify a semantic mismatch -> derive an independent counterexample -> specify a minimal regression and repair boundary. Native RED/GREEN remains unexecuted because the runtime was unavailable.

## Regression oracles already determined by the analysis

1. All four sky rows n_i=e1, positive errors/weights: active-count admission may succeed in the old constructor, but X has rank one. New inference must return a two-dimensional unidentified parameter subspace, not a three-dimensional measured vector.
2. For a fixed data covariance, rescaling inverse-inclusion weights by a common positive constant must not shrink a sandwich uncertainty. Precision weights are a different explicit type; their covariance scaling is expected.
3. NaN or infinity in an observed score, reference score, velocity, standard error or active weight is rejected before ranking/likelihood evaluation. Unavailable charts are typed outcomes with a prespecified symmetric policy, not NaNs silently compared.
4. Passing an array of shape (32,48) to a velocity-response consumer expecting (32,3) is a type/shape error. A source vector contraction of the (3,32,49) object is explicit and tested.
5. Same-data high-mode conditioning must include C_yz. The two-dimensional nuisance example in THEORY_RESULTS has identical trace and different Fisher information; a trace-ratio shortcut fails the oracle.
6. A shell kernel with a different frame, units, epoch convention or missing range is not accepted merely because ell and source_name match. Adjacent partition integration must add back to the unpartitioned window to numerical accuracy justified by that quadrature.
7. Already boosted simulations and dipole/kinematic-quadrupole-corrected maps require an explicit frame/correction transform once, not another unconditional beta injection.

These are small consumer-level tests, not permission to globally repair unrelated legacy modules or rewrite published historical receipts.

## Asset inventory: what is available versus statistically admissible

The following entries are the owner's reported metadata survey, not content verified by MAIN. The survey identified roughly 179 bundles and 1.499 TB; directory entries, symlinks, inode uniqueness and content hashes are different counts. No full data-tree rehash is requested.

Locators:
- W = `/home/cosmosapjw/Dropbox/bianchi/htt_base/workdir`
- E = `/mnt/sn850x2t/htt_base_e2e`
- inventory link `W/asset_inventory_20260907`
- reported inventory target `E/inventories/EXTERNAL_ASSETS_20260907T071735Z`
- reports: assets.csv/json, git_repositories.csv, python_distributions.csv and filesystem.sqlite.

| Asset family | Reported availability | Decision for the next campaign |
|---|---|---|
| Planck PR3/component products | Eleven primary files around 3.75 GiB; four component-control files around 3.375 GiB | First candidate data lane because existing PR3 operators and FFP10 lineage are present. Pin exact release/product/mask/transfer conventions; a path count alone is not admission. |
| FFP10 | 1312 paths around 735.9 GiB, including non-realisation metadata | Do not call this 1312 independent or paired universes. Reuse a validated manifest's CMB+noise pair IDs; do not blindly inherit the historical count 300. |
| Commander incomplete downloads | Five reported partial files | Exclude from active input without deleting or silently completing them; partial files are not valid map controls. |
| PR4/NPIPE | Dedicated W/raw/planck_npipe_pr4 reported empty; a separate RRSS PR4 folder has nine files around 3 GiB | Do not make PR4 the primary analysis by recommendation alone. First identify actual contents and matched simulations. Otherwise stay with PR3; no substitute PR3-null/PR4-observation mixture. |
| WMAP | WMAP9 nine files around 2.87 GB; WMAP7 simulation bundle six files around 13.5 GB | Potential independent instrument crosscheck, but these releases are not a matched null pair. Scientific rank is held until the release-specific model exists. |
| Cosmoglobe/BeyondPlanck | 36 and 32 reported files | Determine whether they are posterior draws conditional on the same sky. Do not count them as new forward-null realisations or independent evidence. |
| ACT DR6 lensing | About 85 products and 400-plus kappa simulation records | Lensing reconstruction is not a primary-temperature or independent-CMB velocity data set. Use only under its explicit tracer/cross-covariance role. |
| CF4 catalogue/reconstructions | Raw, full, compact and pecvel bundles in several locations | Select actual distance/redshift rows, grouping and calibration fields. Reconstructed velocity fields and old refuted result cards are not interchangeable with primary likelihood input. Existing P0 quarantine remains. |
| 2M++, CORAS/2MRS, neural reconstructions | Several existing bundles, sharing underlying galaxy information | Useful dynamical/covariance sensitivity controls; not independent anchors whose likelihoods can simply be multiplied. |
| DESI/catalogue mocks | Eight data files, over ten thousand mock files reported | Redshift/angular tracer windows are useful. Exact sample, selection and cross-survey overlap are a MAIN modelling decision; filenames do not define a velocity field. |
| HSC/KiDS/COSMOS/JWST | Lensing and smaller-field data are present in the broader inventory | Lensing shear is not spacetime congruence shear, and narrow-field data cannot be treated as all-sky low-pole estimators. These are later distinct-response lanes, not first-campaign substitutes. |
| ELC/new external catalogue | Not reported locally available | No large new download is part of this pass. Resolve theory and current assets before acquiring a new survey. |

Existing Python environment locator: `E/venvs/htt_base-py312-20260829`. Inventory package listings are not current successful imports. Future local execution verifies only needed installed tools and selected input files; it does not repeat a complete mathematics/runtime census.

## Reuse strategy

Keep obsstat responsible for actual observed summaries/transforms, HTT for response and likelihood/identified-set semantics, and common mathematics for reusable numerical operations. The accepted exact boost/decoder donors should be integrated explicitly into one tested snapshot, not imported through accidental PYTHONPATH shadowing among mirrored roots. Existing scientific claim ledgers and quarantines remain intact.

A code file being present is not enough to classify a feature as production-ready. The static scan shows substantial reusable representation, exact response, fit, shell, null-rank and sampler machinery. The missing scientific work is the physical likelihood and joint data contract tying those pieces together, not wholesale reimplementation of the repository.
