# R63 R2/C2 reuse and source map

Selected scope: existing-source/data mapping only. Baseline `f29bbab420a33aecb1c398ddd961fd45097f536b`, branch `research/r63-local-boost-global-tilt-20261117`, existing checkout `/home/cosmosapjw/Dropbox/bianchi/htt_base`, device `edd1b263-56a0-4391-8a2a-677dd00eabf5`. Remote operations were read-only. No fetch, branch mutation, code change, science rerun, new catalogue start, or scientific admission was performed. Parent alone writes remote files.

## Main reusable conclusion

The actual CF4 source law supports a signed coherent-velocity coefficient V jointly with an apparent angular dipole d and STF K under seven calibration models. It does not establish global spatial coherence, a homogeneous matter-normal tilt, or an independently measured observer boost. Source-level relative-motion/optical response plus common covariance is the constructive path; repeating the already executed CONST_V/count closure or the synthetic PR255/256 rank benchmark is not new work.

The highest-value bounded computation is to transport a physically derived local observer / source velocity response through the **same actual CF4 operator**, project the same nuisance space, and characterize its supported response rank, null combinations and covariance. The calculation can return identified *relative* combinations even where separate observer/source components are unidentified. Use the current 11D/32D source measurement only for response histories it contains; an arbitrary new depth history requires the actual raw source operator, since a score sufficient for one mean family is not generally sufficient for another. No need to create another registry or reopen all historical campaigns.

## Authority and evidence reuse

Read root AGENTS.md and the current top of docs/harness/CURRENT_CODEX_RUNTIME.md: native execution in existing checkout is current; CUH-G below is historical. Exact source records with current SHA256 and baseline git blobs are in r63_history_sources.json. Current model/effort observation stays UNKNOWN. This bounded mapper used the PhysMath 1.3.0 SKILL, POLICY_INTEGRATION and selected THEORY R2 / CODING C2. No recursive delegation or review.

The preserved full historical PR inventory is R54_TENSOR_FRAME_TOMOGRAPHY_20261116/HISTORY_PR_INDEX.json (573 indexed PRs on its retrieval date); R62/REVIEW/history_map.md and history_sources.json supply the closest integrated reuse map. These were reused rather than issuing another repository-wide PR acquisition. Fresh semantic inspection was confined to relevant source and data boundaries; inventory presence is not a claim to have read every PR diff.

Let P = docs/research_program/observational_publication_20261015/.

## Source identity and exact CF4 packing

**Use original R58 as the continuation baseline**:

- P/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS/OWNED_TENSOR_CARRIERS.npz SHA256 `42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d`.
- Adjacent OWNED_TENSOR_RESULT.json SHA256 `264160d6b53112e7b21278bbeb19baaa9c45e22037b8269debc20baa294f09b9`.
- P/R58.../RESULTS/NATIVE_REPLAY/OWNED_TENSOR_CARRIERS.npz is a distinct artifact, SHA256 `5bbca876f141a58674aa763eee6c75a97d849290354ab0d58cf4ee3bcc4ae338`. Do not silently substitute it for the original. Byte difference alone does not invalidate scientific replay, but no fresh numerical equivalence check was executed by this mapper.
- R61/R62 follow the original. scripts/r62/build_r62_source_carriers.py:27–29,70–80 explicitly opens original R58 RESULTS, checks its result-bound hash and reuses its full covariance.
- R62 source follow-on P/R62_ANISOTROPY_CLASSIFICATION_20261117/RESULTS/SOURCE/SOURCE_TENSOR_CARRIERS.npz SHA256 `1d0f3c353ea9189bffbab5728f295264c6925d4a3d82561c4457e48746beefd2`. It extends the mean with finite Legendre-z STF coefficients; it is not a GR shear-history solver.

scripts/r58/run_r58_owned_tensor.py:151–178 loads n_J2000,z_CMB,dmzp,e_dmzp, uses eta and g below, builds actual O_m, and defines rows = [all12 dipoles, all20 STF], not interleaved eight rows/window. Saved row_indices32 is authoritative. For w=0,...,3:
`kappa_w=y32[12+5*w:17+5*w]=theta36[9*w+4:9*w+9]`.
Per variant retain y32, cov32, response32x11, estimate11, cov11; theta36/white36/body36 retain the complete 36D observable law. The 11 fitted columns are
`[V_x,V_y,V_z,dH_x,dH_y,dH_z,kappa_0,...,kappa_4]`.
V is km/s; dH and kappa are dimensionless log-distance response coefficients. All seven original fits and full 11x11 covariance matrices are copied into r63_history_sources.json.baseline_fits, so no refit is required just to recover them.

STF basis is Frobenius orthonormal: diag(1,-1,0)/sqrt2, diag(1,1,-2)/sqrt6, xy,xz,yz symmetric offdiagonal entries 1/sqrt2. No harmonic alm sqrt2 conversion is applicable to these angular regression coefficients. The actual source design is `D=[g*n,n,E:nn]`, response `O_m D`. Velocity leaks into STF rows on the selected sky; free observed dipole coefficients alone do not remove that leakage. Full polar-STF and cross-window covariance must survive.

scripts/r54/run_r54_cf4_exact.py:61 fixes Gaussian window centres z_CMB=(.025,.04,.06,.08), width .012. r54_distance_estimators.py:65,98 constructs exp[-(z-z_w)^2/(2*.012^2)]/tau² weights on the same selected catalogue with optional selection/nuisance. These overlap and are not disjoint physical shells. The body is the retained exact catalogue operator pair-sum O diag(g) C_uu diag(g) O^T, plus O diag(tau²) O^T; the former ideal-sky R36/R54 first-pass approximation is superseded.

## Actual redshift / distance / boost contract

Actual raw source: docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz, 35,970 grouped sources, SHA256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`. Its paired loop6_result.json explicitly records: "published Vcmb/C, not observer heliocentric redshift; J2000 sky. Frame boost/distance selection not physically reconstructed." This is an existing source qualification limit, not a new prohibition.

scripts/r54/run_r54_cf4_exact.py:80–96 loads only z_CMB,dmzp,e_dmzp,n_J2000,method_family,group_id; group identity/order must match R36 A_RAW_36x35970.npz. It makes no new observer distance deboost. Directions n are observer-to-source in ICRS/J2000; z_CMB is an observed catalogue redshift, not a reconstructed normal-frame emission scale factor.

r54_distance_estimators.py:86–96:
`eta=ln[y(z_CMB)/distance_mpc(dmzp)]`,
`tau²=[(ln10/5)e_mu]²+(250 km/s*g)²`.
A free fitted intercept absorbs the constant H0 unit factor in y/d. r54_lcdm_body.py:29–31,209 ff.:
`chi_hat=int_0^z dz'/E(z'), y=c(1+z)chi_hat [km/s]`,
`g(z)=[(1+z)/(E(z)chi_hat(z))-1]/c [(km/s)^-1]`.
The module explicitly defines g as the response to **source radial velocity** u, accounting for Doppler redshift and the squared source Doppler factor of d_L,obs. Low-z leading g~1/(c z). This is not automatically the observer-boost coefficient. Applying an untransformed observed-distance column to the already CMB-corrected z must be separately justified; changing only redshift is insufficient.

Thus `eta=n.gV+n.d+n.K.n` permits the declared current V measurement. Label V a conditional coherent source/CMB response coefficient, not an independently established matter-frame velocity or global tilt. A real observer/source split needs an explicitly derived redshift-and-luminosity-distance transformation, its catalogue frame corrections and selection response, and the shared error law. Missing absolute-frame information does not erase the valid apparent coefficient fit.

## Frame sign crosswalk

There are two historical beta_RM conventions. They must not be concatenated by matching labels.

- htt/obsstat/publication_frame_kinematics.py:27–36,64–71: beta_RO=O in R, beta_RM=M in R, beta_MO=O in M. Exact relative_beta uses Einstein composition; at first order beta_RO=beta_RM+beta_MO.
- R52/R54 convention (scripts/r54/run_r54_cf4_exact.py:571–573 and THEORY_LOOPS.md:83): beta_RM=(v_R-v_M)/c, CMB dipole=beta_MO-beta_RM. Here V_CF4=-c beta_RM, count excess D/c_EB-beta_CMB=+beta_RM.
- Therefore beta_RM[R52/R54] = -beta_RM[publication_frame_kinematics] at first order in one common transported frame. Source-arrow words and equations take authority over reused symbol names.
- At finite velocity use ordered Lorentz matrices; generic vector addition is only first order. Rapidity atanh|beta| is not beta. Normal N, material species and observer O remain separate; a chosen irrotational hypersurface normal does not set matter vorticity to zero.

## Already executed work and scope

P/PUBLICATION_DAG.json P4 card asks a data-bound rank/remainder-certified identified set or robust physical nonidentifiability with at least two distinct channel/depth responses. V01 is scoped finite frame kinematics. V02 has actual processed-Planck finite boost response and native-child extension. V03 has a **restricted** derived compensated dust+radiation optical history, not general external EB response. V04–V06 remain pending; P4 is NOT_READY_TO_SUBMIT. Publication DAG current P5 route does not change P4 scientific status.

PR-255 is internal card number, actual historical GitHub PR #363: branch changeset/pr255-anchored-response-geometry @ d70ad4c7f30bf953f036319e2262ef151862fde1. Its docs/PR_DELTAS/pr-255.md and common anchored_response_geometry implementation provide supported-covariance whitening, one nuisance projection and same-law Schur increment:
`R_m|b=R_m-C_mb C_bb^+ R_b`,
`S=C_mm-C_mb C_bb^+ C_bm`.
Its benchmark was synthetic only. Preserve covariance-null responses, supported quotient inherited from the joint law, and identified subspace when comparing increments.

PR-256 internal card is historical GitHub #364: changeset/pr256-local-global-velocity @5867fae35b43321e66dfc8ab8ad5567e467b9142. Read its PR delta and velocity_frame_decomposition.py on that exact branch; the file is absent from current working HEAD. It supplies first-order frame closure and source-provider geometry, explicit SUM_ONLY/NON_IDENTIFIED/MISSING_RESPONSE_PROVIDER/SEPARABLE_CANDIDATE, block-preserving coordinate scaling. Its direct-sum rank and large-angle benchmark are hypothesis-only synthetic, not an observed local/global separation. Branch changeset/pr328-mes-local-global-identifiability-design-20260830 @28b8e0834ab531a646d7e3d56338becc2d4c3bc1 was identity-inspected only.

P/PUBLICATION_ACCELERATION_20261025/products/R32-06-P4-DESIGN/science/MANUSCRIPT.md:18,47,115,160–181 constructs n.(b-ell), independent endpoint/history anchors and illustrative rank12→15→18. These are finite design coefficients and stipulated metric; not actual CF4 boost/tilt transfer. Its actual Gaia part (369–441) consumes 755,850-source 102D normal G,b. A common PM E2 observable has rank5; the expanded ten-coordinate endpoint/derivative history map retains five null directions. Existing score cannot create arbitrary new depth moments.

R32-05 repaired optical note and R36-04-OPTICAL-JOINT distinguish same-congruence optical inverse from observer transformations. R36 RESULT explicitly uses synthetic96-direction design, lacks actual CF4 direct/octupole covariance and physical source qualification; retain derived algebra, not an empirical optical likelihood. The R32-01 same-congruence q(n)=d.n+S:nn with d=-A/(cH), S=sigma/H is dimensionless; logarithmic multipole mixing is distinct from observer aberration.

P/FRONTIER_20261020/theory/THEORY.md:1–39, assumptions section provides restricted physical subcase:
`delta d_L/d_L=n.[A(z) ell+h(z)b]+r`,
`A=c(1+z)/(H chi), h=1+z-zA`.
ell=observer velocity relative to local dust /c; b=present dust relative total-energy normal /c; dust velocity at emission=(1+z)b. Conserved post-decoupling compensated dust+radiation, finite interval, first order, bolometric optics. Ideal h/A derivative =H'chi/c establishes distinct radial columns before observation operators. This source cannot be copied blindly onto CF4 eta or V02 map units. R50 history reuse explicitly retains this input and its audit; general histories and remainder calibration stay open.

R54 L06 already executes CONST_V counts-vs-CF4 and gV-vs-constant-dipole comparisons. THEORY_LOOPS.md:162–177 says depth-constant velocity only; no evolving global-tilt map T(z). With method nuisance the apparent law preference disappears, and observed-size injection discrimination was below its fixed 90/10 target. A new R63 result must go beyond this existing benchmark rather than rebrand CONST_V as unrestricted global tilt.

R47–R62 reuse boundaries from closest R62 history map: R47 endpoint exp(-2B*) CMB carrier is integrated type-I history, not present shear. R49 all-family algebra/constraints valid within checked scopes; 24D physical posterior had arbitrary response coefficients and failed PPC and is quarantined after R50. R50/R51 source-bound policy rejects unsupported CF4/Gaia/Pantheon physical columns. R54 same-sky/axis/polarization observations, R58 mixed fit, R60 covariance sensitivity, R61 depth and R62 morphology all supply actual reusable apparent carriers but no automatic Bianchi/global-tilt admission. Old false-PASS, runtime failures and missing inputs remain preserved.

## Other actual carriers and independent anchors

- Count dipoles: P/R54.../RESULTS/R54_L03_RESULT.json contains signed ICRS Quaia_G20/NVSS excesses, mock3x3 covariance, receipt systematic increments, and finite-mock Pi. scripts/r54/run_r54_l03_counts.py:45–59 names existing raw Quaia catalogue/random/selection at /mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0 and NVSS /mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/NVSS_nrao_20261110/CATALOG.FIT. No new catalogue processing was launched. R54 owned excess claim is underpowered; R60 sensitivities vary covariance, not a newly calibrated physical tilt posterior. Published RACS scalar replication is not interchangeable with an owned joint count field.
- CMB: P/R50.../R51/observed_carrier.npz SHA256 f0c08a115854a6f287d39eddf984291f676e6f7bb79bb2324eb92cd6eb2c0dca, 135 real T/E/B ell2–6; Galactic stored real alm=[a_l0,sqrt2 Re,-sqrt2 Im]. SMICA FFP10 covariance belongs to SMICA, not Commander. V02 finite boost injection proves response under its processing, not an independent observed beta measurement.
- **No owned map-level aberration/Doppler 3-vector likelihood** was found in these source carriers. R54_L06_JOINT anchors E21 (redshift tomography v196 +92/-79 km/s) and E22 (aberration+Doppler v300 +111/-93 toward l276,b51, angular sd33,19 deg) are explicitly "published anchor; not part of a block", scalar Gaussian symmetrizations. They have no saved full Cartesian covariance or common-data cross covariance. Do not manufacture an isotropic3D covariance from these errors.
- Planck solar dipole v369.82 km/s is a conditional radiation-dipole anchor; interpreting it as pure observer velocity assumes no intrinsic dipole and propagates shared data dependencies.
- SN: P/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-08-PUBLIC-SN/RESULT.json SHA256 f1a9246b7e1ab216fd6fb927a3fc2e28360cf2e5626aba5d7a88f2af05f7e82b and R62/RESULTS/INHERITED_SN_REUSE.json preserve signed two-depth10D STF, full covariance in mag² and nuisance profiles. Physical sky frame, boost response, raw-to-congruence response and CF4 shared PV law remain UNKNOWN. An independent SN physical boost likelihood cannot be asserted.
- Gaia: actual normal G102x102,b102 carrier mapped in R62 history; marginal PM covariance and independent sources, not measured spatial covariance. Constant observer velocity gives static aberration, not proper-motion drift; E1 acceleration/spin and E2 history responses must remain distinct.

## Recommended consumption and stop

The present stage is complete as source/data mapping. Parent may now use original R58 full joint Gaussian and its raw operator, with one explicit frame convention, to construct and calculate source/observer response images and null combinations. A valid negative outcome can be a conditional relative-motion identified set and quantified information loss; do not claim global physical nonidentifiability from a missing provider, or a new universal no-go without its proof. Keep independent-observer-anchor and physical-history qualification gaps attached to stronger claims only; they do not block the bounded apparent-data computation.

Evidence status: source reading/hash binding IMPLEMENTATION-INSPECTED; saved historical executions REUSED with original scope; new scientific computation NOT_RUN here; exact R63 theorem/result adjudication remains parent work. Scope ended after R2/C2.
