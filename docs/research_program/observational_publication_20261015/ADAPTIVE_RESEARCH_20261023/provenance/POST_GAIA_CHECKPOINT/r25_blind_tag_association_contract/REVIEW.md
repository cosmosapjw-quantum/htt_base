# Independent prospective review: Gaia release-tag association

Date: 2026-10-23. Reviewer: `/root/r25_blind_tag_association_contract`. Requested role: Astra/xhigh; observed runtime: UNKNOWN. Controller-supplied repository HEAD: `d93605e66adfececa89b90681124b232a5f90220`. No Git command was run. This is independent method scrutiny and a recommended frozen numerical contract, not execution, intake acceptance, outcome review, or scientific admission.

**Decision: CONDITIONALLY EXECUTABLE after the controller freezes the clarifications below and the separate intake review qualifies the actual input product.** The question is scientifically meaningful as a selected-sample, release-tag association of specified angular projections. I found no fatal contradiction in its estimand, 13-coordinate tensor carrier, or sphere-RMS formula. The original method is preserved. Its currently unspecified scaling, numerical-rank decisions, fixtures and tolerances are material execution gaps; the recommendations here resolve them prospectively. No reported coefficient or observed numerical condition informed these choices.

## Evidence and independence

Read: the proposed `r25_gaia_property_method/METHOD.md`; the intake's `inputs/contract.json`, `products/AVAILABILITY.json`, `RAW_RECEIPT.json`, `MANIFEST.json`; the beginning of its property table and wire-mask file; and the raw VOTable header and initial metadata rows. Intake author conclusions and status strings are not independent scientific evidence. No prior review verdict, PM outcome, fit coefficient/result/plot, source NPZ array, numerical rank, or fit was inspected or computed. No repository skill/harness was used, no implementation was written, and no child was spawned. Only this external review file is owned.

Current SHA-256 identities read directly from the named files:

- Method: `a612b20e88997ae8e1e30d2f3a0f2cbc35102e0a2f69dd84e0b8741eefcc4246`.
- Intake contract: `00508df7ec44ab6680ab8291868acaa203247aba18aaabfe2eaf029fc6ddad60`.
- Property table: `76d523bb28a1176fa3e81139b6581f3fa176ae4745129f8ec5c9dd995d207c4e`.
- Wire masks: `1c385a8154c778997328023869385624f5ec8d070f2f1aa6162fb58fa3411486`.

The intake reports 4756 exact joined rows, 3216 literal AGN labels, 1540 wire-null labels, and host categories 3/5/6/ROW_NULL with counts 3149/43/669/895. Its frozen source-NPZ identity is `41b6ddcb13131b49b97efd6107816af4518fa9e23725cf3b4272c2f3a70acb8f`; canonical ID identity is `a5df0e9ec295b127beaa1309618b62540564d7e5f70abdc1ab27c9ac8747a614`. Those latter two identities were read from intake provenance, not independently recomputed here. Its raw VOTable identity is reported as `bf727de832da868235b3064e667138b01185ebf3428d0966a5070d8e7b3ae521`.

The controller confirmed that intake review/admission is still pending separately. This review neither repeats nor substitutes for it. Execution must bind the actually qualified property table plus masks and exact source IDs; a changed semantic candidate requires an outcome-blind reassessment, not silent rebinding.

## Scientific assessment

`AGN` versus accepted wire-null is an observable release distinction, not AGN versus non-AGN or variable versus constant. The integrated table combines processing channels, and the general variability classification differs from the more restrictive Vari-AGN product. The primary Gaia paper explicitly distinguishes these products. Thus the score-availability count cannot replace the class label. [Gaia DR3 extragalactic content, sections 2.5 and 3](https://arxiv.org/html/2206.05681v1#S2.SS5)

Astrometric selection, frame construction and spatial systematics limit interpretation. The Gaia-CRF3 paper describes astrometric filtering and VSH fits to systematic proper-motion patterns; reattaching metadata does not provide independent astrometry. [Gaia-CRF3, sections 2, 3.4 and 5](https://arxiv.org/html/2204.12574v2)

The ESA general-classification processing page timed out during this review. I did not independently verify its detailed score-ranking construction; no proposed operation depends on interpreting that score numerically. Primary-paper checks above concern release semantics only, not an empirical calibration for these 4756 sources.

M0 has 32 columns: common B1 spin, common E1/E2/B2 FULL13, differential B1 spin, and the target FULL13 contrast. Its differential spin is necessary nuisance freedom when sky support differs. M0 is equivalent, when identifiable, to separate complete 16-coordinate fields for the two tags, with their FULL13 difference reported. M1 has four 16-coordinate processing baselines plus one 16-coordinate tag interaction, hence 80 columns before structural redundancy. It estimates a common within-processing tag contrast; under misspecification its weighted projection differs from M0's. A single-tag stratum contributes no within-stratum contrast. Neither model isolates a causal photocentre mechanism, a population effect, or an intrinsic spacetime tensor.

The unsupported host-1/2 contrast remains unsupported: its exposure is zero. Host 5/6/null categories, host_detected, and label availability cannot replace that exposure. Positive rank for the new tag question cannot close the old one.

The Cartesian basis is coherent: `P g` is E1, `P S_E n` is E2, `n cross (S_B n)` is B2, and `omega cross n` is B1. The five displayed symmetric trace-free matrices are Frobenius-orthonormal. No scalar-Ylm normalization should be imported into their coefficients. In particular the magnetic field uses `n cross (S_B n)`, while spin uses `omega cross n`; reversing either cross product changes its sign.

For trace-free symmetric S, uniform-sphere moments give `E|S n|^2=||S||_F^2/3` and `E(n^T S n)^2=2||S||_F^2/15`; therefore `E|P S n|^2=||S||_F^2/5`. The magnetic quadrupole has the same squared norm. Mixed terms vanish by parity or contraction of a symmetric tensor with the antisymmetric cross product. Together with `E|P g|^2=2|g|^2/3`, this verifies the proposed RMS metric. This is an analytic check here, not a CAS or numerical execution claim.

All coefficients have microarcseconds/year units; covariance has their square. `mu_alpha_star` already includes cos(dec). Outcome conversion from mas/year multiplies by 1000 and covariance by 1000000. `x_tag=delta/(1 microarcsecond/year)` is a fixed change of units. Physical Q and radial-depth G_F remain unavailable; no new F functional or calibrated Pi is supplied.

## Material gaps and minimal counterexamples

1. **Scaling and rank must be frozen before outcomes.** With nuisance `Z=e1` and target `D=e1+10^-14 e2`, the residual target has condition number one and is nonzero in exact arithmetic. Normalizing that residual to length one, or testing rank only relative to its own largest singular value, hides its almost complete nuisance aliasing. Thirteen orthogonal copies give the FULL13 version. Preprojection scaling, augmented spectra and the residual absolute floor below prevent this failure.
2. **A small singular value is not proof of exact nuisance redundancy.** An unresolved nuisance direction changes the residualizer and can change delta. Only an explicit algebraic dependency licenses removing nuisance columns without changing the specified column space. Rank ambiguity is a HOLD, not a pseudoinverse convention.
3. **The two estimates share the same PM data.** Treating their covariance as zero gives the wrong covariance of their difference. In the special case of identical estimator maps, the difference is exactly zero while the independence formula incorrectly gives `2 V`. Retain the maps and their cross-covariance.
4. **Execution stopping needs branch scope.** M1-only rank failure must not suppress an otherwise eligible M0. Shared input/domain or implementation failure does stop both. This distinction supersedes a literal global reading of “stop on first rank condition” in the proposal.

## Frozen numerical criteria recommended for the worker

The following definitions are one bounded implementation contract, not additional permanent campaign gates. Freeze them verbatim or return any unresolved scientific change before reading PM values.

### Inputs, layout, whitening

Use float64 with `eps=2^-52`, one deterministic source order (ascending exact integer source ID), and rows `(alpha_star,delta)` for each source. Freeze M0 order `[omega(3), beta(13), eta(3), delta(13)]`. Freeze M1 order `[omega_h(3),beta_h(13)]` for `h=(3,5,6,ROW_NULL)`, followed by `[eta(3),delta_H(13)]`. Within FULL13 use g xyz, then the five E matrices, then the same five B matrices in method order. Keep every source; no score, PM, residual or quality clipping.

Before PM access load only IDs, directions, accepted properties/masks, and working marginal covariance. Require finite directions and a declared angular unit; form n and tangent basis from the supplied RA/dec with the usual ICRS definitions. Unexpected labels/missing joins stop the common input stage. A null is accepted through the semantic state plus wire mask, never by converting arbitrary empty or whitespace strings into a negative class.

For each 2-by-2 C, require finite entries and positive diagonal. Let `d=max(C11,C22)`, `a=C11/d`, `b=C22/d`. Require `a,b>0`; underflow is a domain HOLD, not a repaired variance. Require `abs(C12/d-C21/d) <= 32 eps sqrt(a b)`; within this roundoff bound use their arithmetic mean and record the maximum asymmetry. Otherwise HOLD. Define `c=(C12/d+C21/d)/2`, `sigma1=sqrt(d)*sqrt(a)`, `sigma2=sqrt(d)*sqrt(b)`, and `rho=(c/sqrt(a))/sqrt(b)`. Require finite positive sigmas and `abs(rho)<1`. Set `s=sqrt((1-rho)*(1+rho))`; require finite positive s. Do not clip rho, add jitter, discard correlation, or rescale from fitted RSS.

Whiten every two-row vector or design block by the same lower-Cholesky solve:

```
w1 = v1/sigma1
w2 = (v2/sigma2 - rho*w1)/s
```

This corresponds to `L=[[sigma1,0],[rho*sigma2,sigma2*s]]`, `C=L L^T`. Evaluate whitening residuals with scaled arithmetic. Require `maxabs(W C W^T-I2) <= 1e-10` for observed covariance before PM access. A failed finite/domain/whitening check stops both designs; no covariance alteration is authorized.

### Column space, zero columns and rank

Let `Zw=W Z`, `Dw=W D`. Record their preprojection column Euclidean norms using overflow-safe norm evaluation. For every nonzero column divide by its own norm; retain these diagonal scale matrices `G_Z,G_D` and undo their factors in coefficients/maps/covariance. An exact-zero target column fails full-target support. A zero nuisance column may be omitted only with its structural reason recorded. Set a recorded zero-column scale to 1 only as a storage convention; never turn it into a unit data column. Nonfinite norms or unexplained underflow are HOLD.

Only explicitly known structural identities permit a reduced nuisance representation: empty indicators, duplicate columns deliberately introduced by a test, or a label/stratum indicator identity demonstrated from exact categorical inputs. Store the identity and mapping. Numerical near-dependence alone is not “exact redundancy”. Full nuisance coefficients in a redundant original parametrization are nonunique; report the chosen reduced coordinates and mapping, with nonidentifiable original nuisance coordinates UNKNOWN. Do not represent a pseudoinverse's zeros as measured nuisances.

After such structural reduction, set `Zs=Zw G_Z^-1`, `Ds=Dw G_D^-1`. Factor Zs orthogonally, and use `K=Ds-Qz(Qz^T Ds)`; do not construct a dense row-space projector. Do not renormalize K's columns. Retain every singular value of Zs, `[Zs,Ds]`, and K, including reported zeros, and each condition number. Rank at threshold tau counts `s_j > tau*s_max`; the zero matrix has rank zero.

Use `tau0=max(9512,80)*eps` for the observed design and `max(m,p)*eps` for each toy, with the diagnostic set `{tau0,1e-12,1e-10,1e-8}`. A model is eligible only if, at every threshold, the structurally reduced Zs has full column rank, `[Zs,Ds]` adds exactly 13 ranks, and K has rank 13. Also require `s_min(K) > 1e-8*max(1,s_max(K))`. This floor is in the frozen preprojection scaling. Equality fails. These are conservative numerical resolvability criteria, not a theorem of physical identifiability.

A threshold-dependent decision gives `HOLD_NUMERICAL_IDENTIFIABILITY`. Structurally absent exposure gives `NO_EXPOSURE_SUPPORT`. Other deficient target designs retain their full spectra and a design-only supported subspace, with unsupported modes UNKNOWN; this baseline contract does not fit outcomes in a partial subspace. No ridge, truncation selected after outcomes, merging of strata, threshold changes or alternate fit is allowed.

Report tag-by-host and tag-by-fixed-ICRS-octant counts, using sign bits of n with zero assigned positive. Report source and octant leverage shares from K's retained left singular vectors: `ell_i=sum of squares of its two rows`, `sum_i ell_i=13`, and share `ell_i/13`; include largest source share and octant totals. These describe concentration. No arbitrary minimum count or overlap quota is introduced. Rank does not remove extrapolation/model-dependence when the sky overlap is poor.

### Estimator and covariance, including comparison

Use QR/SVD and triangular solves, not an inverse of normal equations. If `K=U Sigma V^T`, define the map on whitened observations

```
T = G_D^-1 V Sigma^-1 U^T
A = T W
V0 = T T^T
```

Then `delta_hat=T y_w`, `A D=I13`, `A Z=0`. V0 is in physical coefficient units and equals the Schur-complement covariance. All cross terms are retained. The covariance identity requires the specified second moments C0; Gaussianity is additionally needed for a Gaussian law or chi-square reference. Neither assumption is empirically calibrated here.

Before PM access require `maxabs((G_D T) Ds-I13) <= 1e-8` and `maxabs((G_D T) Zs) <= 1e-8`. This fixed numerical ceiling may hold an otherwise rank-eligible ill-conditioned design; do not relax it after seeing that design or outcomes.

For two eligible fits, use their common source ordering and common W:

```
V01 = T0 T1^T
Vdiff = (T1-T0)(T1-T0)^T
```

Retain V00, V11, V01 and full maps; `V10=V01^T`. The stable direct formula for Vdiff avoids cancellation. For these nested model spaces the additional working-covariance identity `V01=V00` follows from `T1 F0` selecting the same delta in M0. It is a useful toy check, not independent evidence or a substitute for computing the maps. Do not form a new significance claim for the difference.

Preserve the full joint covariance in identifiable joint coordinates, not merely the target block. Optional W is computed using the target factorization, without scalar-RSS rescaling. W is a descriptive working quadratic. Actual selection law, Gaussian law, cross-source covariance, null coverage and astrophysical significance remain NOT_CALIBRATED.

### One deterministic fixture family and tolerances

Use these synthetic inputs only; do not inspect real PM outcomes to build or tune fixtures. Let `z=(-sqrt(3/5),0,+sqrt(3/5))`, `alpha=j*pi/4`, `j=0..7`, and `n=(sqrt(1-z^2)cos(alpha),sqrt(1-z^2)sin(alpha),z)`. Take all 24 directions for each of four h indices `0..3` and each t in `{0,1}`: 192 sources, 384 rows. Let q index the 24 directions in z-then-alpha order. In microarcseconds/year set `sigma1=2+(h+2*t)/4`, `sigma2=3+(2*h+t)/4`, `rho=(-1)^(q+h+t)/4`; form C from these exact prescriptions. Require the nonzero singular condition numbers of the scaled complete and residual target designs to be at most 100 for this validation family. This is a prospective low-condition fixture requirement, not a measured fact. If it fails, preserve the failure and return before observed fits; do not tune it silently.

For M0 and M1 separately inject each of their 32 or 80 physical coefficients one at a time with amplitude `u0=1 microarcsecond/year`, and one composite vector `c_j=(-1)^j*(j+1)/16*u0`, zero-based j in the frozen order. Generate fields independently from Cartesian vectors, tensor matrices and cross products, rather than using the estimator's design-matrix multiplication as its own oracle. Batch these right-hand sides using each fixture factorization. No random draws are needed.

At `n=(1,0,0)` the fixture must recover the explicit signs: `omega_z` produces positive alpha-star, `omega_y` negative delta; E-xy produces alpha-star `+1/sqrt(2)` and B-xy delta `+1/sqrt(2)` per unit coefficient. Check all five STF matrices for symmetry, zero trace and Frobenius inner products. Check common spin, differential spin, and every FULL13 coordinate independently.

Also use the same family for: (a) one exact duplicated nuisance column, with the same target estimates/covariance after its recorded removal; (b) t=0 everywhere, requiring target-support failure before any toy outcome solve; (c) t constant within each h, requiring M1 target-support failure; (d) an arbitrary tangent rotation `theta_q=(q mod 7)*pi/14`, transforming y, both design rows and C consistently; and (e) converting the full fixture to mas/year and back. None may change the recovered physical contrast or covariance. The simple near-aliasing example above must fail the frozen residual floor; it must not be normalized into eligibility.

Reference the residualized-SVD estimator against a full-model reduced QR solve and its triangular-solve covariance/map. Do not invert `F^T F` as the independent reference. The required tolerances for these condition-at-most-100 toys are:

| Quantity | Fixed acceptance |
|---|---|
| Coefficient recovery | `||c_hat-c||_inf/max(u0,||c||_inf) <= 1e-10` |
| Noiseless whitened residual | `||y_w-F_w c_hat||_2/max(1,||y_w||_2) <= 1e-11` |
| Coefficient/map agreement between SVD and QR | relative Frobenius error `<=1e-10`; coefficient scale as above |
| V00, V11 and nonzero V01 agreement with QR | relative Frobenius error `<=1e-10` |
| Vdiff or a theoretically zero covariance comparison | Frobenius error divided by `max(||V00||_F,||V11||_F) <=1e-10` |
| Scaled target identity and nuisance annihilation | maximum absolute error `<=1e-10` |
| Toy whitening and STF/tangent identities | maximum absolute error `<=5e-13` |
| Duplicate-column, tangent-rotation and unit-conversion invariance | coefficient criterion above and relative covariance error `<=1e-10` |

The tolerances allow substantial margin above float64 rounding for a small, bounded-condition QR/SVD problem without erasing sign, factor-of-1000, omitted-covariance, or aliasing defects. They are numerical implementation criteria, not coverage or physical-error budgets. No tolerance is to be relaxed to fit an observed outcome. A toy failure stops outcome access and preserves its first failing values.

If the optional sphere RMS is emitted, verify it by the same 24-point quadrature: z weights `(5/18,4/9,5/18)` and uniform azimuth weight `1/8`. These integrate the relevant degree-four Cartesian moments. Require absolute squared-RMS discrepancy divided by `max(u0^2,A_sphere^2) <=1e-11` for the coordinate/composite probes. Do not give a preferred eigenvector at zero amplitude or a degenerate tensor spectrum.

## Execution transition and claim ceiling

Numerical worker: first freeze this contract and input binding; then complete shared domain/toy checks and outcome-blind support for both M0 and M1. Store the spectra, scales, structural dependencies, support diagnostics and eligibility decisions before opening PM values. No observed support/rank is asserted by this review.

If M0 is eligible, execute its single authorized observed fit. If M1 is independently eligible, execute its single sensitivity fit; an M1-only rank/support HOLD leaves M0 executable. Conversely a shared input, covariance or implementation failure stops both. Consume an observed-fit attempt when an observed solve starts, including a failed solve. One PM load may feed both already frozen fits. No fit retries or extra label/score/model variants are included.

Hard limits for this new question: two observed fits total; 300 seconds cumulative numerical execution including tests and failures; at most 2 GiB incremental RAM; one process and one BLAS thread. All substantial outputs/logs are external. These local limits do not reset earlier task costs, exhausted allowances, or historical identities. No pair pass, catalogue query, ODE/native solver, bootstrap, empirical-null simulation, or ultra escalation is authorized here. Preserve a cap failure and its exact next checkpoint.

A fresh read-only reviewer must inspect the actual implementation, frozen support record, raw test failures/successes and numerical outputs before any admission/publication decision. This prospective decision does not admit outcomes. Original 17/42, alternate 18/42, historical48, one-use/ultra histories and R9 UNKNOWN remain unchanged. The next executable action is contract-bound preparation/validation once the actual intake product is qualified, with M0 and M1 eligibility treated separately.
