# R32-06-P4-DESIGN fresh independent assessment

**Decision: SCOPED_PASS for `response_design_note` only.** This is a fresh read-only scientific assessment prepared before the actual formal review packet. Formal packet/ACK and controller qualification remain **PENDING_EXISTING_SCHEDULER_FAIRNESS**. This file is not a dispatch, ACK, task-state mutation, publication permission, four-axis CAS adjudication, or admission of an original42/V03 physical result.

Reviewer: `/root/r35_p4_fresh_independent_review`. Requested route: `gpt-6-astra/xhigh`; observed runtime: **UNKNOWN**. The reviewer did not author the science, retained contract, consumer, or figures, and read no prior independent candidate verdict. The excluded contributors are `/root/rc_2a504af3ea3221e2`, `/root/r35_p4_prescribed_numeric_build`, and `/root/r35_p4_p5_source_contract_intake`.

## Candidate and evidence

Candidate: `docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-06-P4-DESIGN/` in the existing `htt_base` checkout.

- `report/RESULT.json` SHA-256: `fd181ea1cac267317dda86b6f8e9fd374701e01777ae73a7180033cf8ec355ed`.
- Canonical embedded output-manifest SHA-256: `97d4252a9d532532ff114b480629ebcea69078ab2225ff90a37fef19427fdaad`.
- All 50 output entries match their saved SHA-256 and size. All nine retained source entries match their saved SHA-256 and size. The manifest identity is canonical sorted compact JSON, as declared by the candidate.
- Literal contract SHA-256: `cdc26625caf799110f58d101bcde3182134d77aa2e1f8b512112e5ade8aee309`; source-identity JSON SHA-256: `f5640c1ec3c2af4c9c40a9e295de23c2897f89bae84180ebfaa88b0e91d22a12`. All seven current science-file hashes are retained in `raw/identity_check.json`.

I read the seven science files, the complete consumer and TeX conversion code, generated matrix/spectrum/grid/witness/error artifacts, claim map, README, saved raw numerical failure, log, and the actual 17-page PDF. I independently extracted its text and rendered pages 8, 9, 10, 12, 14, and 17 at readable resolution, in addition to inspecting the existing all-page contact sheet. The existing repository/runtime/physics/claim/figure guidance was treated as a constraint, not an approval oracle. Source proof checks included `mathematical_recovery.md` lines 121–148, `NATIVE_INFERENCE_THEOREMS.md` section 6, and `theory_synthesis_20260913/REPORT.md` sections 13–13.1. The retained historical `independent_review.md` was hashed as an input but its verdict/content was not consumed.

No producer, historical CAS, raw survey, ODE, native solver, build, or source-provenance pipeline was rerun. The independent probe script constructs its own rows from the manuscript equations and never imports or executes `report/reproduce.py`.

## Physics/math audit verdict

The finite conditional construction is correct under its stated assumptions. The scalar calibration quotient, parameter scaling, endpoint/history distinction, nullspaces, and deterministic perturbation theorem are mutually consistent. Nothing in this assessment identifies a physical global tilt, Bianchi family, native transfer, observational covariance, posterior, coverage, or original scientific acceptance.

### Assumptions and conventions

The signature, common nonrotating orthonormal frame, signed observer-to-source convention, `c=299792.458 km/s`, `R*=100 Mpc`, `v*=300 km/s`, and `h*=v*/R*` are explicit. The observer term has the correct negative sign for that convention. The five STF matrices are symmetric, traceless and Frobenius-orthonormal; full signed coordinates and a reconstructed 3-by-3 tensor are retained. `m` is a signed rate coefficient, not an inferred positive background H or a usable denominator.

The radial response to the normalized two-mode history and both extra channels are stipulated measurement functionals. Their gains, zero coupling to the scalar nuisance, and common frame are assumptions. `W` is a deterministic positive precision metric. It supplies no empirical covariance or statistical independence. The coefficient box is a finite sensitivity domain; the error illustration uses a separate unit scaled-coordinate ball.

### Equation and definition audit

| Item | Status | Independent evidence |
|---|---|---|
| Common nuisance quotient | PASS | Every saved `J,N,W,P,L,A` agrees with direct equation construction; `P` is idempotent and kills `WN`. |
| Two-radius unisolvence/rank | PASS | Self-contained axis-pair/cross-term proof is valid. Exact rational-basis determinant is `-1327104*(q-1)^4/15625`; this is explicitly an independent unnormalized basis, not a reused normalized determinant. |
| Baseline kernel | PASS | Complete six-dimensional span is common observer/bulk motion plus the three unweighted history coefficients. Nominal analytic and saved SVD projectors agree within 1e-12. |
| Added responses | PASS, conditional | The endpoint acts as identity on the split modes; the second normalized window acts as one third of identity on history modes. Separate ranks are 15, joint rank 18. |
| Equal-radius control | PASS | Exact quotient ranks 8/11/11/14, with complete joint null dimension four. Direct signed dipole and compensated monopole witnesses vanish. |
| Fixed normalization | PASS | One nominal full-design `L` is used for every subdesign and every radius/precision grid. No zero-column normalization or rescaling of weak channels occurs. |
| Identifiable combinations | PASS | Full 18-coordinate right bases, kernel/identified projectors, and `V_r^T L^-1` physical-combination rows are consistent. Thin-SVD list length is not used as nullity. |
| Error theorem | PASS | Full-column-rank pseudoinverse/Weyl proof is correct; deficient theorem is explicitly fixed-operator and controls only the identified projection. |
| Undefined physical sectors | PASS | Vorticity remains NOT_MEASURED; x_C/Q/F/Pi/G_F remain NOT_EVALUABLE_WITH_THIS_RESPONSE. |

## Actual independent numerical outcomes

`independent_probes.py` completed with exit 0. Its 192 numerical residual checks passed; it additionally ran 12 exact rational rank cases, all declared radius and precision grids, all signed witnesses, 64 independent deterministic perturbation fixtures, and the rank-loss boundary probe. NumPy and SymPy versions and all measured residuals are in `raw/probes.json`.

| Design | Rank at q=2 | Nullity | Smallest positive scaled singular value |
|---|---:|---:|---:|
| Baseline | 12 | 6 | 0.10665269388736835 |
| Endpoint | 15 | 3 | 0.09763873653697801 |
| History | 15 | 3 | 0.10180602381390118 |
| Both | 18 | 0 | 0.09393875068420443 |

All nominal relative cutoffs 1e-12, 1e-10, and 1e-8 agree with the analytic ranks. Exact checks at q=1, 2, and 1/2 confirm both the equal-radius exception and the positive-distinct-radius scope. The common quotient and all 18 scaling coordinates agree with the persisted matrices to the declared tolerance. Every saved spectral/grid value agrees with reconstruction. All complete q=1 analytic null spans have the correct dimensions and annihilate the corresponding matrices.

The full-rank saved bound fixture gives actual error 0.1808603122455374 against bound 0.18086031224553567, a 1.7e-15 floating-point excess within the declared 1e-12 absolute allowance. Its effective operator/data vectors and estimator were independently reconstructed. In 64 additional deterministic cases, the largest actual-error/bound ratio was 0.22091921042630283. A perturbation of norm `s_min` along the weakest singular pair reduces the smallest singular value to about 6.21e-17, supporting the explicit loss of certification at that boundary. Neither the manuscript nor JSON assigns zero error to uncertified cases.

As an assumption counterprobe, allowing independent unknown additive offsets for all six added coordinates reduces the joint quotient rank back to 12. The manuscript explicitly warns that changed nuisance coupling requires renewed analysis; it therefore does not hide the calibration assumption responsible for the rank gain.

## Preserved near-equality failure and finite precision

The saved `raw/numerical_second_failure.stderr` reports an analytic/SVD null-projector maximum discrepancy `2.6253829486555184e-12` against `1e-12`. I independently reproduce that exact baseline value at q=1.0001; the history-only case gives `4.249249431306975e-12`. These are basis/subspace numerical errors near a small singular gap. All corresponding analytic kernel response residuals remain within the frozen 1e-12 bound, and all required rank cutoffs still give 12/15/15/18. The baseline smallest positive singular value is about 1.61308e-5 there.

`BUILD_HANDOFF.md` explicitly requires analytic/SVD kernel-projector agreement **at nominal q**. The literal contract requires basis/null residuals and nominal rank cutoffs, and explicitly separates exact rank from threshold dependence near equality. The removed grid projector comparison was an extra condition. Its removal did not change the nominal criterion, the null-residual criterion, the accepted model, or a numerical tolerance. The first failure is retained, not recast as a theorem failure or concealed as an all-grid projector PASS.

Additional reviewer-only gap probes display the expected finite-precision boundary: at requested gap 1e-8, relative cutoff 1e-8 reports rank 14 while tighter cutoffs report 18; at gap 1e-12 all three declared cutoffs report 14 despite the mathematical positive-gap rank 18. A requested gap 1e-16 rounds to exact equality in binary64. These probes support the manuscript's structural-versus-numerical distinction; no uniform binary64 resolvability claim follows.

## Nonblocking finding and bounded cleanup

**P3 / artifact semantic labeling:** `report/reproduce.py`, deficient fixture construction (`e0[0]=.001`), and `report/bound_fixture.json::deficient_projected_error` call an unprojected error vector projected. Its scalar nuisance component is nonzero: `max(abs(P0 e0-e0)) = 7.692307692307693e-5`. The projected norm is `0.0009607689228305228`, below the stored conservative 0.001 norm budget. Applying `P0` changes the estimate by only `2.220446049250313e-16`; the reported deficient identified-error bound remains valid. The theorem itself allows this harmless orthogonal residual through the least-squares pseudoinverse, so this is not a counterexample to the inverse or acceptance result.

A bounded optional cleanup is to name the stored vector `deficient_raw_error`, or explicitly set/store `e0=P0@e0` before the fixture calculation, preserving epsilon=0.001 as its declared upper bound. Regenerate only the dependent fixture/check/result manifest under a new candidate identity if adopted. No change to physical assumptions, theorem, tolerance, matrix, or scientific claim is required. This finding is nonblocking for the finite response-design note; it must not be reported as an exactly quotient-supported stored fixture.

## Manuscript and figures

The actual PDF has 17 pages, all 27 equation numbers, four propositions, three figure captions, every nominal spectrum value, and all eight reported nominal s_min/condition values. Generated placement markers are absent. The final saved TeX log has no overfull boxes, missing characters, or undefined reference/citation messages. Tables and equations are readable; the main numerical table correctly separates finite identified-subspace conditioning from unbounded full-vector gain.

Figure 1 plots positive spectra and states all structural nullities. Figure 2's equal-radius marker is expressly offset for the logarithmic axis, labels rank 14, and states its unbounded full-vector gain; the precision panel uses the frozen coordinates. Figure 3 marks eta/s_min at and above one as uncertified. These figures do not imply confidence levels. The three figures are PDF/vector-text plots; the heatmap and its colorbar in figure 2 are embedded rasters (289-by-299 and 15-by-298 pixels), as is normal for the saved image-based panel, rather than entirely vector primitives. They are readable at the manuscript scale.

## Claim-tier implications, safe claims and remaining boundary

The allowed conclusion is a complete conditional finite response design and its deterministic inverse sensitivity. The original V03 requirement still needs actual endpoint/history kernels, calibration/nuisance coupling, physical common-frame transport and units, and a justified response error/covariance. No physical history provider, native solver, ODE continuation, family identification, x_C/Q/F/Pi/G_F evaluation, posterior, or original42 scientific acceptance is admitted here. The manuscript states those limits correctly and makes no literature priority claim.

No blocking scientific repair is required. The next executable transition is for the existing controller to dispatch its actual formal review packet and bind this assessment to the exact candidate identities, with fresh identity verification. No full numerical or provenance replay is needed if those identities remain unchanged. A changed candidate requires only review of the actual delta and affected evidence. The controller alone records qualification; this preparation leaves qualification and publication untouched.

## Scope and command record

All review writes are confined to `/mnt/extdrive/workdir/htt_open_data/r35_p4_fresh_independent_review/`. Initial read-only `git status`/`git rev-parse HEAD` commands occurred before I recognized the parent instruction's no-Git scope; they changed nothing, and no subsequent Git command was run. No children or STATE changes were made. A memory-registry search found no relevant prior task evidence and was not used in the scientific decision.

Actual numerical/document commands, exit statuses, outputs, rendered pages, probe source and reviewed identities are retained in `raw/` and `raw/commands.json`. An initial document placeholder search also matched the word `displacement`; that diagnostic output is retained as `document_checks_initial.json`, and the final check uses exact template markers. This was a reviewer read-only search correction, not a candidate change.
