# R29 moving-lens source/theory targeted closeout

Date: 2026-10-24. Reviewer: /root/r29_moving_lens_source_independent_review. Requested model/effort: gpt-6-astra/xhigh. Observed model/effort: UNKNOWN / NOT_INDEPENDENTLY_OBSERVED. This reviewer did not author either candidate.

**Decision: SCOPED_PASS for the single F1/F2 text repair. Scientific decision remains HOLD_SOURCE_SPECIFIC_PHYSICAL_RESPONSE; no new numerical moving-lens packet is justified.**

## Exact binding

- Reviewed revision: /mnt/extdrive/workdir/htt_open_data/r29_nonradial_moving_lens_intake/REPORT_REVISED.md
- Revision SHA256: 0f66033f7f4adc86c214c45ca479e557de1ede447c1b48afedae2752d505ce2d
- Original REPORT.md SHA256, rechecked unchanged: 52c4a64e6013ab9ed9ebec4b19787fd2d09322f49e980e0099f77882610f6126
- Original independent REVIEW.md SHA256, rechecked unchanged: b3d771aadb12e9039396f0c97032239eb18a309ccc05e478d1945784eedd12e7

The actual unified diff and revised text were read. This closeout uses the source evidence already independently inspected in REVIEW.md and SOURCE_AUDIT.json; no new broad literature search or numerical execution occurred.

## Finding closeout

**F1 CLOSED — lines 39–97, 103–105, 129 and 137.** The revision now distinguishes rigid potential translation, its justified scale-separated approximation, the formal R_adv Jacobian, and the missing physical R_phys. Arbitrary E/B coordinates are retained without treating their enumeration as evidence of an unrestricted physical response.

The counterexample was independently checked by differentiating the stated functions: continuity gives delta'=-epsilon V k^3 sin(kx)sin(qy)/kappa; applying the periodic inverse Laplacian gives phi'_v=epsilon V k^3 sin(kx)sin(qy)/(k^2+q^2). The local-advection expression is epsilon V k sin(kx)sin(qy). Their coefficient ratio is k^2/(k^2+q^2), equal to one half at q=k. Density positivity, slow motion, dimensions, fixed kappa, zero-mode/boundary prescription, and the instantaneous scope are now explicit.

The bulk-motion boundary agrees with [Hotinli, Johnson and Meyers 2006.03060v3, Section II](https://arxiv.org/html/2006.03060v3#S2) and [Wayland, Alonso and Coulton 2609.04133v1, Section 2.1](https://arxiv.org/html/2609.04133v1#S2.SS1). The internal-rotation example now uses continuity/Poisson at a snapshot and explicitly excludes a rigid-moving-halo or Bianchi no-go. The ensemble example requires an independently justified fixed linear H and makes no unrestricted R_adv substitution. No remaining F1 scope error was found in these passages.

**F2 CLOSED — lines 105–129.** The revision freezes C, t and the bandpower operator before using w^T LR. For N=t^T A d, h=t^T A t and A=C^{-1}, direct differentiation of N/h gives exactly the displayed data, template and covariance terms. Symmetry/positive-definiteness and nonzero t establish the stated domain. The derivative of the empirical C_{bb'} correctly applies the product rule to both D factors while holding multipole weights and support fixed.

This matches the dependence in [Hotinli et al. 2605.18938v1, Eqs. 23–25](https://arxiv.org/html/2605.18938v1#S3.SS3). Variation of X/selection is handled through delta L. The text also preserves dependence among data, X, t, C and calibration, and limits a derivative kernel to a local first-order statement for nonlinear models. No remaining F2 derivative error was found.

## Limits and next decision

This PASS closes the two identified text findings only. The reviewed response domain, symbolic snapshot check and estimator differential are not an evaluated survey Jacobian, a calibrated physical likelihood, a CAS certificate, or original K03 acceptance.

The public-map/catalogue observations and bounded missing-release statement remain intact. No source-qualified omega/A/beta response with matching covariance, physical calibration and nuisance specification was obtained. Zero cross-mean still does not imply equality of variances or full laws. No signed mode, cross-covariance, physical null law, or (x,F,Pi,Q,G_F) state is manufactured.

Reuse the completed 20261018 result. Do not rerun its scalar contrasts or launch an ACT/DESI map fit from this closeout. Continue other independently READY branches. Reopen this route only with the identified missing payload or a distinctly specified and qualified raw-map experiment. Original K03 HOLD, H04 HOLD, K04's H04 dependency, historical counts/R9 UNKNOWN, and one-use accounting remain unchanged.

No further review ladder is requested for this repaired text. The original report, REVIEW.md and SOURCE_AUDIT.json were preserved. This closeout is the only new file written by the reviewer in this turn.

Signed: /root/r29_moving_lens_source_independent_review; independent source/theory closeout; observed runtime UNKNOWN.

