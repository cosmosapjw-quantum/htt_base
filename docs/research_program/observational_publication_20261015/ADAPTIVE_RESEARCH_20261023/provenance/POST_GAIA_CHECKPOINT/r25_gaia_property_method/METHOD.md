# Prospective Gaia release-tag association method

Date: 2026-10-23. Owner: `/root/r25_gaia_property_method`. Role: scientific method advice, not execution, independent review, intake acceptance, or scientific admission. Requested runtime: `gpt-6-astra/xhigh`; observed runtime: `UNKNOWN`. Repository identity supplied by the controller: `research/htt-adaptive-methods-20261023`, HEAD `d93605e66adfececa89b90681124b232a5f90220`; no Git operation was performed here.

This note is non-claim-bearing prospective research. It changes no repository candidate, frozen assignment, campaign state, acceptance, allocation, or cost identity. Original acceptance 17/42, alternate acceptance 18/42, historical 48, consumed one-use/ultra allocations, and R9 UNKNOWN remain unchanged. It adds no permanent gate or campaign node. Any proposed future execution belongs to its actual controller-assigned continuation and cumulative accounting.

## Decision and the distinct question

One additional conditional question survives: **within these same 4756 selected frame sources, does the fitted FULL13 angular mean field differ between sources carrying the released `vari_best_class_name=AGN` tag and sources with a wire-null value in that field?** This is release-tag association. It is not an AGN/non-AGN, variable/nonvariable, or host/no-host contrast. A prespecified processing-stratified sensitivity can determine whether that descriptive association persists after allowing different baseline fields for the four observed host-processing categories.

The frozen host-flags 1–2 versus 3 question has no exposed members and remains `NO_EXPOSURE_SUPPORT`. Its design interaction is identically zero on the selected sample. Flag 5, flag 6, `host_galaxy_detected=True`, or missing host flags must not substitute for flags 1–2. The proposed release-tag question has a different exposure and estimand; it cannot close or rename the unsupported original question.

There is scientific value in checking dependence of angular coefficients on an auxiliary release label when interpreting an apparent common sky pattern. A detected association would challenge a **source-label-invariant mean-field working model** on this selected sample. It would not by itself identify optical-centroid motion, instrumental calibration, stellar contamination, local observer motion, cosmological shear, or global tilt. Conversely, no association would not exclude any of those mechanisms. Randomly oriented, zero-mean photocentre jitter can change scatter without changing any of the 13 mean coefficients. Neither source extent, photocentre/flux covariance, epoch astrometry, nor a physical centroid response is supplied by these nine metadata fields.

## Evidence read and outcome blindness

The inspected intake contract is `docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/R25-GAIA-SOURCE-PROPERTY-INTAKE_INPUT.json`. The inspected live metadata are `/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_properties_20261023/products/AVAILABILITY.json` and the adjacent `RAW_RECEIPT.json`. At inspection they report:

| Metadata item | Reported count or identity |
|---|---|
| Exact retained IDs / matched QSO rows | 4756 / 4756; no missing QSO row |
| Host flags 1, 2, 4 | 0, 0, 0 |
| Host flag 3 / 5 / 6 / wire null | 3149 / 43 / 669 / 895 |
| Variability class AGN / wire null | 3216 / 1540 |
| Available AGN membership score | 3014; a separate missingness pattern |
| DSC quasar / unclassified | 2069 / 2687 |
| Intake's selection-bit-1 indicator | true for all 4756; no contrast support |
| Canonical ID SHA-256 | `a5df0e9ec295b127beaa1309618b62540564d7e5f70abdc1ab27c9ac8747a614` |
| Frozen source NPZ SHA-256, from intake receipt | `41b6ddcb13131b49b97efd6107816af4518fa9e23725cf3b4272c2f3a70acb8f` |
| Raw property VOTable SHA-256, from intake receipt | `bf727de832da868235b3064e667138b01185ebf3428d0966a5070d8e7b3ae521` |

These are inspection-time reports from an intake still awaiting its final semantic/independent decision. This note does not independently certify them. The authoritative future tag is the final accepted semantic value plus original wire mask, not an assumed interpretation of an empty string. A final audit that changes the label/missingness counts requires revisiting the definition while still outcome-blind.

Only source code/schema was inspected for the astrometric model: `scripts/run_reboot_gaia_frame.py`, the basis/design/solver definitions at the start of `.../OPEN_INPUTS_20261018/EXECUTION_20261018/D05_GAIA_RADIO/observable_vsh.py`, and field-model portions of `R25-GAIA-PAIR-SEPARATION_INPUT.json`. No source NPZ was opened, no proper-motion/covariance array was loaded, and no current PM coefficient, result, plot, or outcome report was read. No fit, rank computation, catalogue query, simulation, production change, or state mutation was executed. Counts alone establish neither angular support nor numerical rank.

## Release semantics that constrain interpretation

The general variability classification supplies labels from light-curve processing. Its published best-class score is a combination of normalized classifier ranks; it must not be treated as a calibrated probability or an inverse-selection weight. A missing published label does not establish that a source is constant. [Gaia DR3 general-classification processing](https://gea.esac.esa.int/archive/documentation/GDR3/Data_analysis/chap_cu7var/sec_cu7var_cls/ssec_cu7var_cls_processing.html)

The integrated QSO table combines several selection/processing modules. DSC includes astrometric inputs. General variability classification and the more restrictive SOS-AGN product are distinct; the 3216 class tags and 3014 available membership scores must not be equated. [Gaia DR3 extragalactic-content paper, sections 2–3](https://arxiv.org/html/2206.05681v1#S2)

SOS-AGN selection is tuned using Gaia-CRF3 and includes cuts involving astrometry, colour, environment and scan-angle effects. In particular, its published procedure uses proper-motion significance and parallax, and reports incomplete, magnitude-dependent selection. Therefore score availability or membership is not an external, PM-independent validation channel. This statement concerns SOS-AGN and does not assert that every general-classification AGN tag passed that same filter. [Carnerero et al., sections 3 and 6](https://arxiv.org/html/2207.06849v1#S3)

`qso_candidates.n_transits` counts transits used for **morphological analysis**. It is not the astrometric observing baseline, PM transit count, photometric variability sampling count, or a source distance. `source_selection_flags` describes module eligibility; raw bit combinations are not ordinal physical quantities. [Gaia DR3 QSO table data model at AIP](https://gaia.aip.de/metadata/gaiadr3/qso_candidates/)

The retained source selection already used astrometric information and reference-frame processing. The Gaia-CRF3 paper discusses both that selection and angular systematics. Reattaching DR3 metadata does not create a statistically independent astrometric sample. [Gaia-CRF3 paper, sections 2, 3.4 and 5](https://arxiv.org/html/2204.12574v2)

Reference intake was cache-first: the existing contract/receipts/source pointers were read, and a filename inventory found no cached primary metadata/variability document for this question. The linked primary literature and release documentation were then checked on the web. The ESA QSO data-model page and direct AIP open initially timed out; the AIP indexed data-model response supplied the field description. No catalogue data were fetched and no new download cap was invented. These limitations concern document retrieval, not the already acquired property rows.

## Exact exposure, sample and mean model

The sample remains all 4756 exact IDs. Let `t_i=1` for the accepted exact literal AGN class and `t_i=0` for accepted `ROW_NULL` in that field. Here zero means **no released class value**, not a negative astrophysical class. Do not drop missing tags, threshold either score, substitute membership availability, infer a class from DSC, or select sources using the PM outcome. Unexpected nonnull labels, unavailable fields or missing joined rows invalidate this particular two-category definition until reframed before outcomes.

Use ICRS Cartesian coordinates and tangent components `y_i=(mu_alpha_star,mu_delta)`, with `mu_alpha_star` already containing cos(dec). Convert both outcomes and covariance consistently from mas/year to microarcseconds/year; covariance scales by 10^6. Directions, labels and working marginal covariance are conditioned on as fixed design inputs. The observable is the released fitted proper motion over the original astrometric window, not an instantaneous velocity derivative.

For unit direction n, let `P=I-n n^T` and let `E=[e_alpha_star,e_delta]` be the 3-by-2 orthonormal tangent basis. Define

```
X_i beta = E_i^T [P_i g + P_i S_E n_i + n_i cross (S_B n_i)],
B_i omega = E_i^T (omega cross n_i),
beta = (g_x,g_y,g_z,s_E1,...,s_E5,s_B1,...,s_B5).
```

Each S is symmetric and trace-free in the existing Frobenius-orthonormal basis:

```
diag(1,-1,0)/sqrt(2), diag(-1,-1,2)/sqrt(6),
(e_x e_y^T+e_y e_x^T)/sqrt(2),
(e_x e_z^T+e_z e_x^T)/sqrt(2),
(e_y e_z^T+e_z e_y^T)/sqrt(2).
```

The primary descriptive model is

```
E_work[y_i | n_i,t_i] = B_i omega + X_i beta
                         + t_i B_i eta + t_i X_i delta.       (M0)
```

There are 32 coefficients: baseline spin 3, baseline FULL13, tag-specific spin nuisance 3, and target FULL13 difference 13. The target is `delta=(delta_g,delta_S_E,delta_S_B)`, the fitted tagged-minus-null mean-field coefficient contrast. The `t_i B_i eta` nuisance prevents differential B1 structure from leaking into the desired E1/E2/B2 contrast through unequal sky support. A common spin alone assumes away that possible leakage. Neither spin is interpreted physically.

The primary null is `delta=0`, allowing baseline FULL13, common spin and differential spin to remain free. Its rejection within a valid working model means only that these 13 fitted mean-field coordinates depend on the released tag. If the finite-dimensional mean model is wrong, delta is the specified covariance-weighted least-squares projection contrast, not a universal source-population effect.

One fixed sensitivity allows a separate complete baseline angular field for each **unmerged** observed processing category `h in {3,5,6,ROW_NULL}`:

```
E_work[y_i | n_i,t_i,h_i] = sum_h 1(h_i=h) [B_i omega_h + X_i beta_h]
                            + t_i B_i eta + t_i X_i delta_H.  (M1)
```

This has at most 80 columns: four 16-coordinate nuisance baselines plus a 16-coordinate tag interaction. Delta_H assumes a common tag contrast across these processing categories. Under heterogeneity it is its own weighted projection; it is not an unweighted average of stratum-specific effects. Comparing delta and delta_H is one prespecified sensitivity on the same outcomes, not two independent replications. No fitted host coefficient is relabelled a detected-host effect. The 43 flag-5 rows are retained, with their support handled algebraically rather than by an invented minimum-size quota.

Scores, DSC labels, individual selection bits and morphology transit counts are retained in the provenance description but do not trigger more observed fits in this proposal. In particular, a selection bit that is identical to t, or determines t after stratification, cannot be simultaneously adjusted away and claimed as independent tag exposure. Adding every bitmap value as a stratum risks exactly that aliasing. Absent magnitude, colour, actual scan sampling and redshift covariates, neither M0 nor M1 is a fully confounder-adjusted physical comparison.

## Estimand, rank and support before outcome access

Write either model as `m=Z gamma+D delta`, where `D` stacks `t_i X_i`. For M0, Z stacks `[B_i,X_i,t_i B_i]`; for M1 it stacks the four processing-baseline blocks and `t_i B_i`. Let `C0=blockdiag(C_i)` retain every within-source 2-by-2 PM covariance. With its Cholesky factor L, form `Zw=L^-1 Z`, `Dw=L^-1 D` and `R_Z=I-Zw Zw^+` using an orthogonal factorization, never a dense 9512-by-9512 projection. Then

```
H_delta = Dw^T R_Z Dw,
delta_star = H_delta^-1 Dw^T R_Z L^-1 m_true,
delta_hat  = H_delta^-1 Dw^T R_Z L^-1 y                 [full rank only].
```

This defines the working estimand and estimator without selecting a preferred direction, tensor eigenvector or scalar amplitude from the outcome.

Before opening PM outcomes, the future worker must inspect exact tag-by-processing counts, tag-by-fixed-ICRS-octant counts, the column dependencies of Z, all singular values of the scaled residualized design, condition, and source/region information concentration. Empty angular cells and unequal information are reported; finite catalogue counts do not establish sky overlap. If only one tag exists in a processing stratum, that stratum supplies no independent within-stratum tag comparison. It is neither merged nor advertised as validation of the homogeneous-tag assumption.

The necessary full-contrast condition is `rank([Z,D])-rank(Z)=13`. Numerical rank uses an outcome-blind recorded scaling and a relative singular-value baseline `max(n_rows,n_columns)*eps`, accompanied by the full spectrum and diagnostic ranks at relative 1e-12, 1e-10 and 1e-8. These diagnostics do not prove exact rank. If the full-13 conclusion changes across these thresholds, the inversion is unresolved: retain `HOLD_NUMERICAL_IDENTIFIABILITY`, do not regularize it into a claimed FULL13 result. Exact redundant nuisance columns may be represented by their same column space with the dependency recorded; this is not permission to delete target directions.

If the target rank is below 13, a well-defined estimable projection `P_est delta` and its support basis may be reported descriptively. All unidentifiable modes remain UNKNOWN. A pseudoinverse's zero coordinates are not measurements, and a supported subspace cannot be renamed FULL13. The baseline proposal does not run a PM fit for an unresolved target: return the design/support result and its exact missing condition. Rank and support of both M0 and M1 remain NOT_MEASURED in this note. If only M0 passes, only its unadjusted tag association is executable; the M1 result remains on HOLD independently.

## Covariance and the permissible statistical output

`C0` is an explicitly chosen block-independent working covariance, not a measurement of the full catalogue covariance. No unit correlation, isotropic extra variance, equal per-group covariance, or independent source draw is silently introduced. From the joint fit retain the full coefficient covariance and its FULL13 contrast block. All 13-by-13 cross terms matter; norms or separate error bars are insufficient. For comparisons between M0 and M1, retain their linear estimator maps and cross-covariance under the same C0; their results cannot be combined as independent evidence.

If `delta_hat=A_delta y`, then the actual sampling covariance would be

```
V_true = A_delta C_true A_delta^T.
```

The marginal blocks do not determine the cross-source blocks of `C_true`. An unknown cross-source correction to C0 need not be positive semidefinite by itself. Without additional justified information no universal robust significance or coverage follows. The working formula `V0=H_delta^-1` applies when the specified linear Gaussian model with covariance C0 is valid. An arbitrary global rescaling cannot repair missing angular correlations or outcome-dependent source selection.

Report the full delta, both STF matrices, V0, coefficient units, design support and the descriptive working quadratic `W=delta_hat^T V0^-1 delta_hat` only if supported. A chi-square-13 reference is algebraically available under the stated unselected Gaussian linear model; its empirical null/coverage is **NOT_CALIBRATED** here because release/source selection and true cross-source covariance have not been modelled. Do not report a calibrated astrophysical p-value, Bayes factor or discovery probability. No label permutation is justified by these observational tags; labels are not exchangeable at fixed sky/selection. Formal Gaussian draws, if ever separately authorized, would validate only the working calculation.

## Tensor carrier, normalization and (x,F,Pi,Q,G_F)

Keep the canonical tuple `(delta_g,delta_S_E,delta_S_B)` and its full cross-covariance. For a dimensionless carrier choose the fixed unit `u0=1 microarcsecond/year`, not a fitted RMS, selected eigenvalue or noise significance, and define `x_tag=delta/u0`. Divide the coefficient covariance by u0 squared. This is a change of units, not physical normalization to a Hubble rate or MES bound. The STF matrices are signed tensors; do not force positive semidefiniteness or discard negative eigenvalues. Frobenius-orthonormal matrix coordinates are not normalized scalar-Ylm powers.

For interpretation retain the reconstructed angular contrast

```
d(n) = P_n delta_g + P_n delta_S_E n + n cross (delta_S_B n).
```

If a downstream scalar amplitude is wanted, the full-sphere RMS of this fitted field has the fixed metric

```
A_sphere^2 = (2/3)|delta_g|^2
             + (1/5)||delta_S_E||_F^2 + (1/5)||delta_S_B||_F^2.
```

This follows from uniform-sphere second/fourth moments and the distinct harmonic sectors. It is an analytic summary of the fitted field, not the observed sample's sky weighting or a replacement for FULL13. Its uncertainty must use the joint covariance; no direction is treated as defined when its amplitude vanishes or the relevant eigenvalues are degenerate. This optional summary is not a new physical F or Q law.

| Component | Prospective status and allowed meaning |
|---|---|
| x | Additional tagged-observable FULL13 contrast carrier, if identifiable; no intrinsic spacetime tensor claim |
| F | Existing downstream functional remains unchanged. No existing F implementation was inspected or rebound here. Any consumer must use its already specified functional on the full carrier; otherwise F evaluation remains UNBOUND/NOT_EXECUTED |
| Pi | At most the explicitly labelled Gaussian working sampling law induced by C0; no population-calibrated probability, MIO posterior, or independent empirical null |
| Q | No physical MES anchor, source-distance calibration or causal centroid transfer; physical Q remains unavailable |
| G_F | DEPTH_UNAVAILABLE. Metadata strata are not radial depth and cannot create a depth-completed G_F |

Thus the route can strengthen the interpretation of an observable x and the sensitivity of a conditional working calculation. It does not complete the five-component physical bundle or promote local/global identification. Both source-dependent astrophysics and source-dependent processing can produce the same observed association; a common physical field can also look tag-dependent after angular/model misspecification and selection. No such ambiguity is removed by a formally full-rank 13-coordinate fit.

## Bounded future execution proposal, not a dispatch

The next useful action, after the existing intake's final semantic decision, is an outcome-blind support check for the exact M0/M1 definitions. Only if its conditions hold is the corresponding observed fit warranted. This is one proposed analysis unit, not a required gate for unrelated work.

1. Reuse the exact existing 4756-source NPZ and accepted cached property table/wire masks. Verify frozen input identities and exact integer-ID alignment. Bind to the accepted metadata candidate; do not create a new intake or replay successful queries. Initially load IDs, directions, metadata and covariance only; do not read PM values while deciding labels, columns, scaling or support. No acquisition or new catalogue is required.
2. Freeze M0 and M1, the basis/signs/units, retained sample, reference category, rank policy and covariance designation before PM access. Respect existing outcome-dependent upstream selection; do not add clipping, quality cuts, label thresholds, depth assignments, nonlinear covariance tuning or model selection.
3. Use one process and one BLAS thread, at most 2 GiB incremental RAM, 300 seconds wall time, and two observed fits total: M0 and the one M1 sensitivity, each only when identifiable. Stop on the first violated input/domain/rank condition or hard cap and preserve that first failure. These proposed local ceilings never reset or enlarge existing campaign limits. No dense cross-source covariance/projection, pair enumeration, bootstrap, MCMC, ODE/solver call, significance search or ultra request is included.
4. Validate the implementation on deterministic injected vector and each STF coordinate, common/differential spin, known label contrast, exact duplicated-column and zero-exposure designs, tangent-coordinate covariance transformations, and consistent mas-to-microarcsecond conversion. Those checks exercise the estimator and support decisions; they supply no observed physical evidence. Use one fixed synthetic fixture family, not an empirical-null simulation campaign. Any substantive convention or tolerance ambiguity returns to the controller before observed execution.
5. After passing support and numerical implementation checks, read each observed PM input once for the authorized fits. Preserve full coefficients, full joint/contrast covariance, full singular spectrum, estimator cross-covariance for M0/M1, working RSS and the stated interpretation limits. Record execution identity and failures. Store bulky arrays and logs on the external work area; do not write this work into an unrelated or full root filesystem.
6. A separate read-only reviewer must assess the actual implementation, frozen definitions and outcomes before any scoped scientific admission/publication decision. This method note is not that review. No result is permitted to close the original host contrast or change 17/42, 18/42, historical48, one-use/ultra or R9 status. If either design lacks support, preserve that exact result and continue independent authorized branches.

No further separate discriminatory node is justified by merely repeating the same field fit for DSC, every bitmask, every score cut or morphology-transit threshold. Those would multiply related, selection-coupled association checks without providing the missing centroid mechanism, actual covariance or depth. A direct optical-centroid mechanism test would need genuinely new independent information such as epoch astrometry paired with flux/scan information or an externally specified physical response; none is manufactured here.
