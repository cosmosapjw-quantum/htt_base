# R64 R2/C2 bounded history and source map

Scope: R2/C2 only. Remote read-only in the existing checkout /home/cosmosapjw/Dropbox/bianchi/htt_base on device edd1b263-56a0-4391-8a2a-677dd00eabf5; parent supplied baseline 33d87dd3e4a787e477327d37ee00b40e790211c9 and branch research/r64-directional-hubble-20261117. No remote write, fit, science test rerun, clone, worktree, fetch, push or branch mutation. Requested runtime gpt-6.1-sol/high; observed UNKNOWN. All original untracked files preserved.

Applied PhysMath 1.3.0 SKILL, POLICY_INTEGRATION, selected THEORY R2 and CODING C2, SUBAGENT_MODE with no child delegation, root AGENTS first25, current native-runtime first25 and htt-dag-orchestrator. Current root/native policy governs; continuous42/CUH text is historical where superseded by the user's current single full10 branch.

P denotes docs/research_program/observational_publication_20261015/. Exact SHA256/current baseline blobs for 44 sources are in r64_history_sources.json. Code/report excerpts are read; several arrays/results are identity-inspected plus reused through cited producers rather than freshly refit. Read/inventory distinctions are explicit in JSON. Reused local r63_history.md/r63_history_sources.json, r61_owned_inputs.md and r61_paper_positioning.md; no repeat of the 573-PR acquisition.

## Actual result and non-repetition boundary

The best new finite unit is a **source-integrated full36 radial eta mean**, transported through each retained actual O_m, followed by distance-derived H_D and radial ratios. This adds a new nonlinear distance-derivative functional to actual data. It must retain monopoles: R58 y32, R61 and R62 omit all four h rows and cannot alone reconstruct an absolute distance profile or its calibrated derivative. Source-integrated response means evaluating basis functions at each catalogue z_i before O_m, not fitting polynomials through four window centers as if they were independent shells.

Already executed and reusable:

- H01: actual 35,970-group frozen source, four Gaussian depths .025,.040,.060,.080, width .012, north-weighted branch, exact working H_W contraction and overlap covariance. Formula H_W=sum(w d cz)/sum(w d²), km/s/Mpc. At alpha0 H_W=(74.629348,74.343818,72.516333,70.810223). Fixed weights give H_W→10^(-Delta_mu/5)H_W. This is cz/d apparent proxy.
- H03: full4x9 apparent h,D3,STF5 fits and complete36x36 shared-row covariance. h=(75.167996,75.303212,74.559217,72.445152) km/s/Mpc. Existing four method-family deletions,12 ICRS patch deletions and north weighting are correlated sensitivities, not independent heldout observations. H03 code already verifies first-order calibration mean-design rank12 of13, projected angular rank8.
- H02 actual:20 method/window angular fits, full40x40 per-method cross-window covariance, coupled same-gamma calibration LP, actual raw table2/3/4 joins and group-hash heldout released-method contrasts. Data and procedure below.
- R32-03 repaired structured response: correlated12D H03 dipoles; same bulk+constant-rate residual23.3967, full covariance essential (block-diagonal gives8.9257); depth-slope irreducible floor15.3160 vs fixed6-dof reference12.5916, FP proxy/joint coefficient radii5.7509/1.5897. These are stipulated finite response budgets, not measured calibration.
- R32-08 paper: retains full36 and signed tensors, corrected five-coordinate dimensionless tensor0.0326568 Frobenius norm, physical leading H_u=H−A.n/c+sigma:nn, full common PV field in restricted-band model, separate signed SN comparison. No general H_D history.
- R37-03: actual selected SN full16 covariance, directional apparent H_F ratios plus declared opacity/geometric budgets, depth contrast, same-input scalar equivalence, separate CF4 full36 displayed H windows, synthetic CBL first derivative control and transmission intervals. It explicitly says actual radial distance derivative and overlapping independently qualified H(z)/joint law are absent. New work must not count this existing H-ratio exercise again.
- R54: replaces biased noisy-distance cz~d regression by modulus-linear eta, source-velocity g(z), actual catalogue pair-sum PV body and seven nuisance variants. Existing exact-vs-linear distance comparison and law discrimination must be reused.
- R58: original owned mixed tensor full36 arrays, all seven nuisance models, full32/11D fits and polar–STF covariance; source-velocity response leaks into STF due to actual selected sky.
- R61: already has affine-z STF source response, calibrated common-angular invariance, actual bias operator and counterexample for arbitrary depth calibration; exact-log vs linear closure and pivot/extrapolation sensitivity. A new common-calibration theorem must identify extension to H_D radial ratios rather than relabel K(z_h)−K(z_l).
- R62: already actual source-propagated Legendre-z STF series degree2 primary/degree3 sensitivity through same O_m/full32, and common angular constant cancels varying STF component. It does not include general new monopole/dipole histories.
- R63: actual published q chart reconstruction and deterministic mean transport in fixed experiment; full distance/photometry deboost remains unresolved.

## Formula/data/code crosswalk

H01/H03 define d=10^((DMzp−25)/5) Mpc, u=cz_CMB km/s, sigma²=250²+[70(ln10/5)d e_mu]², W(z)=exp[-(z−z_w)²/(2*.012²)]. H03 velocity_design(d,n)=d*[1,n_x,n_y,n_z,E_a:nn]; fit returns QR influence A. joint_covariance(A,sigma)=A diag(sigma²) A^T. Window-major ordering [h,D3,STF5] is rates, not fractional quantities.

Files:
- P/H01_20261016/src/hubble_window.py: distance_proxy_mpc51, radial_weights66, moments89, window_hubble109, cross_window_covariance116.
- P/H03_20261016/src/h03_tomography.py: velocity_design82, window88, fit105, joint_covariance123, patch_id141.
- P/H03_20261016/src/run_h03.py: compute45; method delete93–105; sky delete106–116; saved full covariance134.
- P/H03_20261016/src/h03_method_gauge.py: calibration_rank13; Z_m=d1_method, sumZ=d monopole identity17–19.

Current eta branch:
- htt/htt/htt/infer/r54_lcdm_body.py: flat_lcdm_distance_factors208–219 returns chi_hat=int dz/E, y=c(1+z)chi_hat [km/s], E, g=[(1+z)/(E chi_hat)−1]/c [s/km]. g is the first-order **source radial velocity** response including observed luminosity distance's squared source-Doppler factor, not automatically observer response.
- htt/htt/htt/infer/r54_distance_estimators.py: multipole_basis39; wls_operator48; log_distance_ratio86 returns eta=ln[y(z_CMB)/d]; log_noise_variance93 returns tau²=[ln10/5 e_mu]²+(250g)²; log_window_operator98 stacks9rows/window, fitted nuisance rows dropped; white_covariance113 contracts shared source noise.
- Numerically eta includes constant ln H_ref (unit convention is absorbed by fitted intercept). For a dimensionless eta=ln[D_L,ref/D_L], subtract the same declared ln H_ref before interpreting exp(eta). Parent's exact H_D formula must use that normalization consistently.
- scripts/r54/run_r54_cf4_exact.py load86–99 enforces raw operator/source hashes and exact group order; build_operators102 uses [1,n,STF5] and nuisance below. Full covariance is white36+body36, dimensionless log-coefficient². The body is O diag(g) C_uu diag(g) O^T, not ideal sky.
- r54_lcdm_body.py velocity_correlation142 and radial_velocity_covariance_product177 implement C_uu=Psi_perp n_i.n_j+(Psi_par−Psi_perp)(n_i.rhat)(n_j.rhat), positions r_i=(c/Hfid)chi_hat(z_CMB). This is conditional linear LCDM covariance from pinned P(k); true selection/common calibration covariance remains unknown.

Seven **correlated views of one experiment**, never independent likelihood factors:
log: no extra nuisance;
log_mono: FP,SN,TF indicators relative OTHER;
log_split: those3 plus sign(dec) steps for all4 families;
log_survey: survey indicator columns relative reference;
log_mono_radial: method3 plus z;
log_mono_galactic: method3 plus abs(n_Galactic,z);
log_mono_error: method3 plus [(ln10/5)e_mu]².
Nuisance columns fitted separately in each Gaussian window. A general radial monopole can partly coincide with log_mono_radial nuisance; characterize actual rank instead of assuming all radial coefficients remain identifiable.

Original R58 carrier:
P/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS/OWNED_TENSOR_CARRIERS.npz,
SHA25642f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d.
Freshly inspected every key/shape. Per m:
theta36(36), white36/body36(36x36), response36x11;
y32(32),cov32,response32x11,estimate11,cov11.
36 order is four [h,d3,kappa5]. 32 order is dipole12 then STF20:
row_indices32=[1,2,3,10,11,12,19,20,21,28,29,30,4,5,6,7,8,13,14,15,16,17,22,23,24,25,26,31,32,33,34,35].
11 parameters=(V_x,V_y,V_z)[km/s],dH_x,y,z,kappa0..4[dimensionless].
Original source and covariance, not NATIVE_REPLAY, are baseline. STF basis is Frobenius orthonormal: diag(1,−1,0)/sqrt2; diag(1,1,−2)/sqrt6; xy,xz,yz symmetric1/sqrt2. Do not use harmonic alm sqrt2 conversion.

## Raw joins and heldout reality

Raw selected source:
docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz,
SHA25686dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c.
Alternate H02 historic source under theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/ has the same pinned SHA in producers; this mapper did not rehash that alternate path.

P/CONTINUATION_20261018/H02_EXECUTION_20261018/h02_actual.py:
RAW=/mnt/extdrive/workdir/htt_open_data/cf4/J_ApJ_944_94.
table2 SHA8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f,
table3 SHAc2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d,
table4 SHAb6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94.
These identities are source pins read in code; no fresh raw source analysis here.

overlap_diagnostics215–248 authenticates tables, builds1PGC→row, rejects duplicate/absent groups, checks Vcmb/c and J2000, exact ID-set membership of all .01≤z_CMB≤.1 raw groups, and exact DMzp/error fields. Definitions249–262 retain raw CAL/SNIA/FP/TF/SBFO/SBFI/SNII presence/count distinctions. Table2 galaxy→group join298–314 uses fixed slice8:15 for group1PGC, preserves12 unmatched distinct group IDs. Source report: raw38053groups; selected35970;55877galaxy rows;52810 connect selected. Pooled family partitions FP26916,TF7614,SN700,OTHER740 are not pure independent method measurements.

Heldout code265–292:
whole-group split int(sha256(str(group_id))[:8],16)%5==0;
same-group released modulus differences;
training angular8 fit with separate profiled intercept, test WRMS using1/(e_left²+e_right²);
SNIA–FP149train/33test: constant.303796 vs angular.306344mag;
SNIA–TF162/47:.324443 vs.357259;
FP–TF529/109:.475214 vs.471794.
All distances were already jointly calibrated upstream: these heldouts diagnose downstream angular overfit and do not validate independent calibration. Existing H03 method/sky deletions likewise have no independent joint noise calibration. True heldout covariance and upstream selection/calibration simulation law are not supplied by these products.

P/CONTINUATION_20261018/H02_UPSTREAM_SELECTION_20261018/upstream_selection.py:
UPSTREAM=/mnt/extdrive/workdir/htt_open_data/cf4/upstream_20261018, CF4 sibling J_ApJ_944_94. Parses official CDS fixed-width schemas from ReadMe, joins upstream galaxyPGC→CF4 galaxyPGC→group1PGC, preserving missing counts and statuses. Official2020 table1/table4 have10737/9792rows; selected7573galaxies connect6697groups. Depth support and band/quality composition are already calculated. Reported inclusion fractions are within-release membership, not initial detection/targeting probabilities. Shared raw HI/band/calibration genealogy prevents treating optical/W1 routes as independent.

Current R63 published chart:
scripts/r63/r63_cf4_q_check.py62–102 and transport_r63_catalogue_chart.py35–52 use workdir/raw/cf4_full/table4.dat.gz, SHA compressedbe91d4fae6fa01552ab3bc85db695411fca3249eeae08b566a712e6ea790bd99; decompressed matches table4 above.
groupID bytes0:7,DMzp8:14,error15:20,Vh27:32,V3k39:44,RA83:91,Dec92:100; exact selected order and four parity maxima0 in saved diagnostic.
q_pub=c log[(1+V3k/c)/(1+Vh/c)] = c log1p[(V3k−Vh)/(c+Vh)], km/s; this q is a **chart correction**, not deceleration q_D.
Additive V3k−Vh fit a=(-360.19066679,76.46973556,−45.14102988)km/s, amplitude370.975268; residualRMS.289467km/s. Pure multiplicative q=n.b residualRMS5.497647km/s. Fixed offset uses O_m[(A+1)(q_pub−n.a)/c]; covariance/design/catalogue unchanged. It supplies no distance/photometry deboost p, no independent observer velocity likelihood and no full finite Lorentz transport.

## Radial invariance and optics reuse boundaries

Targeted rg searches of current htt/scripts and canonical publication markdown/TeX, excluding copied source backups/raw/fixtures, did not locate a prior implemented empirical H_D=c/[d(D_L/(1+z))/dz] or q_D radial history under that notation. Many H_D hits are **Buchert domain Hubble H_D**, unrelated. This bounded search is not a repository-wide novelty proof. The source-integrated H_D construction remains parent science to derive/execute.

Closest actual predecessors:
- R37-03 REPORT_DELTA.md13 and compute_hubble.py58–90: finite synthetic CBL uses distance first derivative, common opacity family across windows; no observed derivative.
- R61 THEORY.md142–181 and DEPTH_CORRECTED/KINEMATIC_DEPTH.json: common angular calibration cancels affine-STF depth contrast; arbitrary non-affine depth contamination needs actual5x32 estimator bias operator, endpoint bounds alone insufficient.
- R61 THEORY.md183–219: ln[D_fid/D_L]=ln[H_o(n)/H_f]+z[Q_o(n)−q_f]/2+O(z²); observed-redshift slope is a cosmographic combination, not shear time derivative.
- R62 THEORY.md108: constant source angular tensor shiftsK0 only; source-injected varying part invariant in that finite model.
- R32-08 main.tex43: H_u=H−A.n/c+sigma:nn, dL=cz/H_u+O(z²).
Therefore H_D radial ratios under arbitrary z-independent angular multiplicative zero-point extend an existing cancellation principle; they do not establish local physical expansion without declared optical/congruence closure.

For parent normalization D_L=(1+z)chi_ref exp(−eta), exact identity is H_D/H_ref=exp(eta)/(1−B eta_z), B=H_ref chi_ref/c. Calibration eta→eta+b(n) gives H_D→exp(b)H_D, so same-direction radial ratios cancel b at function level. Finite fit invariance additionally requires affine-equivariance within fitted nuisance/image space; arbitrary angular b outside [1,n,STF2] can leak into radial coefficients under selected sky. A theorem for arbitrary b at continuum-function level is not automatically a theorem for this truncated fitted estimator. This is a real minimal implementation obligation.

Under attenuation D_L,obs=exp(tau/2)D_L,geom, eta_obs=eta_geom−tau/2. A nonconstant tau_z affects1−B eta_z, so angular zero-point cancellation does not remove redshift-dependent opacity. Keep reference normalization and regular denominator explicit. No newly verified physical H/q or coverage claimed.

## P3, old branches and useful next experiment

PUBLICATION_DAG: P3 asks H_eff(z,n),q(z), dipole/STF vs velocity/calibration/selection; minimum robust CF4 result or informative null with method/sky heldout and explicit selection-covariance response. H01,H03 completed_scoped; H02,H04,H05,H06 pending; submission NOT_READY_TO_SUBMIT. R64 may complete its own current selected unit while preserving original42 scientific gates.

Exact existing refs, no fetch:
PR540 origin/research/htt-sixpaper-p3-h01-window-20261016 @8e5bb45dddd512a0c9f2c51013079b15a07b6c11;
PR541 origin/research/htt-sixpaper-p3-h03-tomography-20261016 @2a5d47b2f6af69e049ce41c068b77d99a1592d7f;
PR551 origin/research/htt-sixpaper-h02-l03-calibration-prior-paired-null-20261017 @6c97e3be2fae0fbbdb5a7392258f3a78cdc3556c;
PR560 research/htt-sixpaper-goals-robustness-20261018 @4a68995507bf8e672b2551d9030f3ad9f0d2152e;
PR561 research/htt-open-input-theory-20261018 @10f3ea585c6608e794900efe7e4f8f42c0747a3b.
Older precedents identity-only: PR510 obs/obs02-cf4-information-20261013 @c3c2e5f00757d5e7c57d6df149db86f82dc59cfa; PR513 obs/obs03-cf4-latent-20261013 @5f3fbbee1d48d348bdf889fe2e27abdcb05073f4; PR518 r2/02-cf4-provider-20261014 @f72ab7bdd2e4a16321368264bbfa1ffcd3fc7129. Do not claim whole branch diff read. PR index573 is reused as dated inventory, not current GitHub state.

Recommended finite experiment: keep originalR58 theta36,C36 and source rows/operators; propagate one low-order radial basis for monopole,dipole,STF with source velocity g nuisance and fixed background; fit same law jointly; report actual rank/condition and denominator support before evaluating H_D radial ratio at interior redshifts. Compare matched low-degree alternative and nuisance union, not independent p multiplication. Use R61/R62's demonstrated estimator-bias framework for omitted radial/angular calibration. Retain velocity-slope/g-history sensitivity from R60/R63 rather than presume a fixed source velocity is exact. A finite output can be conditional apparent radial-ratio regions and identified rank even when physical closure remains open.

Actual same-source method/sky validation may reuse existing deletion masks or group-hash IDs, but a new predictive heldout fit must construct its response/cross-covariance. Existing full36 contains only original all-source window observables; it cannot manufacture sufficient statistics for arbitrary source holdouts or new covariance operators. A new science fit can use full36 fixed covariance without repeating O(N²) PV pair sum; a genuinely new raw holdout covariance is separate work.

SN: R37 sources P/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-08-PUBLIC-SN/RESULT.json and R36-01-CF4-OPERATOR/RESULT.json. Selected490SN (342low/148high),705overlapping sensitivity, 62/114duplicateCIDrows, full16x16 retained coefficientcovariance. Magnitude intercept and high-bin level profile absolute scale; zHD integral and zHEL luminosity factor. Full1701cov failed symmetry outside certified selected union. These cohorts and CF4 differ, but unknown common PV/calibration and unverified source overlap prohibit multiplying as independent. Do not infer independent tracer confirmation from distinct filenames.

R42 Loop05 report asserts1580SN and isotropy-confirmed numeric headline with abbreviated hashes; this mapper did not find/verify its bound execution carrier. Treat report assertions as historical unqualified, not load-bearing empirical evidence. Current R37 selected-covariance/R54/R58 producers have precise actual qualification and should be the data authority.

Completed selected-stage result: reusable code/data/formula map and finite non-repetition boundary. No new scientific numerical result, theorem proof or empirical source null produced here. Parent owns later stages, actual fit/validation and remote durable integration.
