# R62 historical source and observable-carrier map

Scope: R1/C1 and R2/C2 source mapping only. Remote actions were read-only in the existing checkout `/home/cosmosapjw/Dropbox/bianchi/htt_base`, device `edd1b263-56a0-4391-8a2a-677dd00eabf5`. No remote fetch, checkout, implementation, test execution, or publication was performed by this mapper. Root owns the R62 branch. Baseline source commit: `c118982e56ee50d68dd0446aa10f16ffe65bd02b`.

## Decisions supported by reused work

1. Start from observed anisotropy phenotypes, preserving signed vectors/STF multipoles, covariance, frame, epoch and selection. The repository already implements all-eleven Bianchi algebra classification and geometry-only tilt invariants. Reimplementing that catalogue, axisymmetry feasibility, a single principal-axis comparison, or affine-z STF slope repeats completed work.
2. An observational phenotype is not an algebra input. No saved observed carrier supplies the Bianchi structure constants `(a,n)`. Transporting the algebra classifier to a sky requires an explicit forward or inverse map with its assumptions.
3. R49 has actual all-family constraint/evolution code and archived numerical receipts, beyond its original design-only prose. Its physical all-family 24D posterior remains under major revision after R50 found arbitrary transfer/probe response factors, invalid velocity-null construction, and bad PPC. Preserve valid algebra/constraints and finite numerical tests; do not reuse those posterior numbers as physical Bianchi constraints.
4. A concrete next classification computation is cross-window common-eigenframe/coaxiality compatibility, or uncertainty-preserving commutator images, on the existing full CF4 joint carrier. This distinguishes fixed-axis from changing-axis apparent STF patterns and is not the already completed axisymmetric-single-tensor or affine-slope analysis. It needs no Boltzmann hierarchy. Physical Bianchi attribution still depends on a separately declared geometric/kinematic history map.

## Exact branch / PR lineage

Live authenticated `gh pr list --state all` was read during this mapping. These are stacked branches, not claims of merging into main.

| Work | Local branch head | Live PR |
|---|---|---|
| R47 solver-free morphology | aae07cb83b8899dd7495d550722068d8bcbf3bcb | #571 OPEN, base R46 |
| R48 tensorized / all-type geometry | 0052c10a5fa7a1fa1fb757bc82547879fdc6d5fc | #572 OPEN, base R47 |
| R48 integrated six-loop | 1b8abb1399f9f80b8e69bd57c2cc1592e2d1bcd4 | #573 OPEN, base R48 |
| companion repairs | 8a6ae269751a8a6878eaf9e1192c28fe1c067523 | #574 OPEN, base R48 |
| R49 general tilted Bianchi | 36bd9030a0759c5563e273dd83836b40034dcda3 | #575 OPEN, base six-loop |
| R50 observed convergence | 6fd5d8661ebc8530b19edabc92482b42fc5b32b5 | #576 OPEN, base R49 |
| R54 tensor frame | 77f61c17ba33ff28ff4f16a7d42621d8041e5ce4 | #577 OPEN, base R50 |
| R54 theorem addendum | 3b23189245fb040a78915a69b0e5dda21f4a5e5a | #578 MERGED into R54 |
| R58/R59 current branch | 6fe19c5139004a1f281ec85c592e5ab4c7590d5f | no later live PR in returned recent list |
| R60 | fb6ae9f21585e194ef29dabc91d79a529e0ac57e | local branch inspected |
| R61 baseline | c118982e56ee50d68dd0446aa10f16ffe65bd02b | local branch inspected |

PR URLs follow `https://github.com/cosmosapjw-quantum/htt_base/pull/<number>`. Source identities below bind baseline file blobs and current file SHA256 in the companion JSON. The older R49 `CURRENT_AUTHORITY.json` names a historical worktree/head `448a9c9e...`; this is historical metadata, not current checkout authority.

## Algebra / geometry / tilt reuse

All relative paths below start at the baseline repository root.

- `htt/bass/background/bianchi_types.py`: canonical all-11 `BianchiAlgebra`, `build_structure_tensor`, `build_bianchi_algebra`, class-A/B and h strata; Jacobi `n a=0`. Class A types I,II,VI0,VII0,VIII,IX; class B V,IV,III/VIh,VIIh. III is h=-1, not a disjoint duplicated continuous family.
- `htt/bass/diagnostics/bianchi_similarity.py`: `classify_bianchi_type` line76, `geometry_fingerprint`192, `tilt_orbit_fingerprint`233, `recover_tilt_squared_components`294. Sibling `test_bianchi_similarity.py` covers type fixtures, rotation/positive-scale invariance, exact curvature degeneracies, invalid Jacobi/tilt and eigenspace strata. Last code change `effb46279cbc69138c9e72503a1a86a35013ed4e` clarifies oriented quotient/parity.
- Source derivation `docs/research_program/observational_publication_20261015/R48_TENSORIZED_OBSERVATIONAL_CONVERGENCE_20261109/BIANCHI_TYPE_SIMILARITY_METHODS_KO.md`, sections2–5: `C^k_ij=a_i delta^k_j-a_j delta^k_i+epsilon_ijm n^mk`; normalize by `kappa²=|a|²+||n||²`; use structure spectrum, Ricci spectrum and tilt moments `p_j=vᵀ n_hat^j v`. Quotient SO(3) and common positive scale only; parity/O(3) is not defined for the pseudotensor n.
- Exact retained examples: I and special VII0 have flat intrinsic metrics despite different group actions; V and special VIIh have Ricci `-2a² I` and same constant-curvature metric. These are explicit scope-limited nonuniqueness examples, not an unrestricted new observational no-go.
- `htt/bass/background/convention_bridge.py`: `exact_spatial_ricci_from_compact`365 and `exact_momentum_divergence`396; bridges legacy representations. `tilted_bianchi_state.py` and `general_tilted_evolution.py` contain typed species/normal states and later vector-tilt evolution. R49 archived GBI03 receipt reports all-family residual/refinement checks; not independently rerun here.
- R49 distinction: normal N, species matter/radiation u_s and observer O are separate. Single homogeneous perfect-fluid Bianchi I with nonzero enthalpy has zero tilt under its momentum constraint; multi-fluid counterflows are allowed if total normal-frame momentum cancels. Geometric tilt invariants alone do not enforce the Einstein constraints.
- Reduced legacy `nonperturbative_tilt.py`, `codazzi_tilt_rhs.py`, `einstein_bianchi.py` have restricted family/scalar-direction coverage and are not substitutes for the later vector state.

### Minimal reuse defects to avoid transporting

The code labels `moment_jacobian_rank` with rank of Vandermonde M of n's eigenvalues. For derivative with respect to v, however,
`D_v(p0,p1,p2)=2 M diag(v)` in an eigenframe. For `a=0,n=diag(-1,0,1),v=(t,0,0)`, 0<t<1, M is rank3 while this derivative is rank1; at v=0 it is rank0. Generic nonzero eigencomponents give rank3. Thus reuse M's rank as the squared-component moment-map rank, not a universal local v-Jacobian rank.

For repeated eigenvalues `n=diag(1,1,-2),v=(r cos(phi),r sin(phi),z)`, rotations around z preserve n and carry any phi to another. Under the stated simultaneous SO(3) quotient these pairs occupy one orbit. The reported continuous azimuth degree is a coordinate/stabilizer freedom before quotient, not by itself distinct unobserved physical states. R48 final source itself leaves necessary/sufficient global orbit separation as an open obligation.

## Actual observed carriers and nearest completed classification

Let P denote `docs/research_program/observational_publication_20261015/`.

| Carrier or result | Exact path under P | Fields / result | Usable scope and limitation |
|---|---|---|---|
| CMB T/E/B ell2–6 | `R50_OBSERVED_CONVERGENCE_20261115/R51/observed_carrier.npz` | `mode_labels`135; `d_commander_135_uK`, `d_smica_135_uK`; J135x5; STF basis5x3x3; SMICA FFP10 covariance135x135, n_mc300 | Frame Galactic; stored-real [a_l0,sqrt2 Re,-sqrt2 Im]; Commander deterministic; SMICA MC cannot calibrate Commander |
| Commander quadrupole | `R60_COVARIANCE_CALIBRATION_20261117/RESULTS/COMMANDER_MORPHOLOGY.json` | `commander_primary.temperature_tensor_uK`, `STF5_uK`, `eigenaxes_ascending`, `shape_sqrt6_trQ3_over_trQ2_3half` | Shape -0.1193055035; eigs(-17.96753,.808864,17.15867)uK; C2=207.06244uK². Deterministic masked-estimator tensor, not physical shear or unbiased unknown full sky |
| Same-sky reduction robustness | same JSON | `same_estimator_comparison` | Commander–SMICA tensor difference8.274%; matched axes2.07–2.51°; largest-absolute-eigenvalue selector88.499° branch flip. Already completed |
| CF4 full joint law | `R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS/NATIVE_REPLAY/OWNED_TENSOR_CARRIERS.npz` | per7 variants `__y32`, `__cov32`, `__response32x11`, `__estimate11`, `__cov11`, theta36/white36/body36 | 35,970 groups; four windows polar3+STF5, ICRS/sourceward, fixed z_CMB; V in km/s, dH,K dimensionless. Preserve cross-window/polar-STF covariance |
| CF4 fit records | adjacent `OWNED_TENSOR_RESULT.json` | `variants.<m>.fit.estimate,covariance,rank`; `robust` | rank11 apparent coordinates. Physical22D pullback rank11/nullity11 with free calibration; vorticity absent. Exact catalogue sufficiency not claimed |
| Prior axis classification | R58 `RESULTS/AXIS_DIAGNOSTICS.json` | `variants.<m>.D2_principal_frame,D4_fixed_axis_contrasts,D5_alignment` | Full eigensystems and same-Gaussian alignment MC already done. Post-hoc reference family: conditional tails are exploratory |
| Axisymmetric feasibility | R60 `RESULTS/AXISYMMETRIC_WITNESSES.json` | `variants.<m>.observed_kappa5,observed_eigenvalues,observed_invariant_shape,candidate_delta_chi2,full_11d_profile_lift` | All7 axisym witnesses feasible; delta chi2=1.091–5.029<11.0705. No need to reprove intersection; no global optimization minimum or calibrated triaxiality p claimed |
| STF redshift evolution | `R61_KINEMATIC_MEASUREMENT_20261117/RESULTS/DEPTH_CORRECTED/KINEMATIC_DEPTH.json` | `model_max_p_slope=.9432869179435148`; `model_union_depth_contrast_rms` | Affine-z apparent STF slope not required. Not time derivative of shear. Calibration endpoint control valid only in declared affine subspace or estimator bias operator |
| Gaia signed VSH normal law | `OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-03-PM-HISTORY/audit_backup/derived_inputs/full_stats.npz` | G102x102,b102,ywy,logdetN,n,zcounts,cut_Q; SHA4d9406de... | 755,850 sources; conditional marginal PM covariance/independent sources. R50 nuisance-profiled E2 target in uas/year, not sigma/H |
| Gaia existing benchmark | `R50_OBSERVED_CONVERGENCE_20261115/OBSERVED_GAIA_BENCHMARK.json` | E2 chi2(5)=110.4207 or144.6222 under different nuisance; means differ7.06252uas/year | Target-specific information preservation tied with optimal Gaussian score. Spatial systematics/source history unresolved |
| Earlier common-axis scan | `R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L5_LOWZ_FRAMES.json` | `benchmark.axis`, `cf4.analysis`; generating `scripts/r54/run_r54_lowz_frames.py` | Constant axisymmetric quadrupole+aligned dipole scan already exists, but earlier ideal-sky covariance; do not repeat or silently upgrade |

The separate D05_GAIA_RADIO `sufficient_statistics.npz` is a 16D radio/VSH carrier; it is not the 102D Gaia source above.

R54 theorem T6 (Schur selection/parity blocks) and T7 (distance zero-point versus Hubble multipoles, spin versus vorticity) provide the existing mechanism-based observation taxonomy. Scalar distance at first order has no direct vorticity column; proper-motion E2 is shear-type, B1 is rotation/spin-type with an external anchor needed. The theorem's full-sky first-order idealization must remain distinct from actual masked response matrices.

## Strongest next executable classification

Observation-space route: take each declared 32D CF4 working Gaussian law and group its STF coefficients K_b across four windows. Test pairwise commutators `[K_b,K_c]` (zero iff symmetric matrices are simultaneously diagonalizable), or fit `K_b=R diag(l_b1,l_b2,-l_b1-l_b2) Rᵀ`. Keep the twelve dipole coordinates as joint nuisance and all covariance. At generic nondegenerate axes, common-frame STF has11 coordinates versus20 unrestricted; repeated/zero eigenvalues change strata, so a bare chi2_9 law is not automatic. Same-law simulation or confidence-set feasibility gives bounded conditional classification.

This is explicitly an observation-space phenotype. Existing `response32x11` contains the constant-state source response only. A physical arbitrary-depth shared-eigenframe model requires an extended raw `O_m D`, frame transport and window response; do not silently assign window coefficients to pointwise shear. Common frame is compatible with some fixed-principal-axis constructions, not a Bianchi family label. A noncoaxial example can reject that particular observational submodel without excluding general tilted Bianchi solutions.

Targeted searches found no common/shared-eigenframe implementation in the R54/R58/R60/R61 scripts and inference modules inspected. This is not proof of absence across every archive.

## Older history reused with exact limits

- R47 README sections2–3 and METHODS_NO_BOLTZMANN: exact Bianchi-I endpoint positive metric carrier `T(n)/Tbar=[nᵀ exp(-2B_*)n]^-1/2` under isotropic emission/collisionless propagation. Integrated endpoint/history tensor, not present-day shear; all-family finite-curvature transfer absent.
- R48 HISTORICAL_SOURCE_MATRIX / SOURCE_REUSE_AND_CONTRADICTION_LEDGER retain earlier T1 stored-real STF pack, WU009 positive-quadratic inverse, WU010 observer Lorentz pullback, WU011 cut-sky response, FB6 fixture proxy coverage, FB8 GlobalTilt versus ObserverBoost, R10 first-jet ray-generator source, and old kinematic seals. These indexes are source pointers; this mapper did not re-read each original proof or certify their CAS ancestry.
- R50 HISTORY_REUSE retains the October five-theory-loop operator, optical/PM history and explicit constraint examples. Useful for further response derivation; no need to reconstruct generic tensorization.
- R42 low ESS, pseudo nulls, arbitrary coefficients and transfer stubs are quarantined, not discarded as historical failure evidence.
- R49 exact abelian family-label floor was repaired in R50; finite-curvature transfer remains phenomenological unless derived/calibrated. GBI04 all_passed receipt includes explicitly rejected out-of-scope likelihood families and does not establish a native all-family Boltzmann solver.
- R54 Type-I Thomson T/E result is already first-order homogeneous mode only; E2 B-null gate failed in stored SMICA data, masked E operator/calibration limitations persist. It is not evidence for a physical Bianchi family or generic polarized solver.
- PR metadata/source inventory is not semantic reading of all prior PR diffs. No exhaustive historical-completion claim is made.

Skill context used: cloud physmath-research-loop1.3.0 SKILL, POLICY_INTEGRATION, THEORY_LOOP selected R1/R2, CODING_LOOP selected C1/C2. Requested model/effort: inherited parent, no explicit override; observed model/effort UNKNOWN. Child delegation NOT_RUN (bounded assignment forbids). Source-map tests here: direct read/hash/shape inspection only; no scientific numerical rerun and no new result implementation.

## Four-window interface clarification (consumer-critical)

`scripts/r58/run_r58_owned_tensor.py`166–173 constructs `dip=[9*w+1,9*w+2,9*w+3]`, `quad=[9*w+4,...,9*w+8]`, and **`rows=np.r_[dip,quad]`**. Saved `row_indices32` is authoritative. Thus y32 contains **all12 dipoles first, then all20 STF components**; it is not interleaved8/window. For w=0..3,

`kappa_w = y32[12+5*w:17+5*w] = theta36[9*w+4:9*w+9]`,
`K_w = sum_a kappa_wa E_a`.

The E_a are unit-Frobenius STF matrices in `r54_tensor_five_view.STF5_BASIS`: diag(1,-1,0)/sqrt2; diag(1,1,-2)/sqrt6; symmetric xy/xz/yz offdiagonal entries1/sqrt2. No a_lm-to-STF sqrt2 conversion applies to these angular regression coefficients.

`scripts/r54/run_r54_cf4_exact.py`61 fixes centers(.025,.04,.06,.08) in z_CMB and Gaussian sigma .012. `r54_distance_estimators.gaussian_window_weights`65 and `log_window_operator`98 implement weights `exp[-(z_i-z_w)^2/(2*.012^2)]/tau_i²` on the same full selected catalogue, with optional explicit selection and per-window nuisance columns. All windows overlap; they are not disjoint physical shells. The normal design is [1,n,E:nn] with appended nuisance. Each window WLS returns9 coefficients; only nuisance rows are dropped. O@eta gives theta36; white covariance=O diag(tau²) Oᵀ and the cached cosmic body add shared-object and shared-field cross-window covariance.

The source design is O@[g*n,n,E:nn]. Its first3 columns contain the actual coherent-velocity response, including nonzero leakage into STF rows from survey geometry. Merely allowing twelve free observed dipole means does not remove that STF leakage. A classification of K_w can be explicitly apparent/retained-observable; an intrinsic morphology interpretation should include the explicit V response and corresponding ambiguity. Window values are angular estimator coefficients and not shear at z_w.

Parent-provided R3 follow-up: the blanket IX single-fluid tilt exclusion based on canonical n=I must not be transported to arbitrary IX n with offdiagonal shear. A separate physics constructor supplies a diag(1,2,3) counterexample. This mapper records that reuse warning without claiming independent derivation or verification.


