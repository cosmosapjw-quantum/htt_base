# Adversarial Research Audit Prompt: HTT/Bianchi Manuscript

You are an external adversarial reviewer. Audit only the research formalization and results: physics, mathematics, statistics, inference design, claim tiers, figure interpretation, and manuscript logic. Do not review programming style, code architecture, packaging, tests as software, or implementation aesthetics.

## Inputs

Use this archive only. The compiled PDF is intentionally absent.

Read in this order:
1. `research_audit_source/docs/manuscript/main.tex`
2. chapter files included by `main.tex`
3. `research_audit_source/docs/generated/manuscript_plot_list_index.md`
4. `research_audit_source/docs/generated/result_pack_A.md`
5. `research_audit_source/docs/generated/result_pack_B.md`
6. `research_audit_source/docs/generated/result_pack_C.md`
7. `research_audit_source/docs/generated/transfer_sensitivity_report.md`
8. figure manifests for figures you cite
9. code samples only if manifests/prose are insufficient to understand a figure

## Hard Boundaries

- No native low-ell Bianchi Boltzmann solver output is available in this manuscript.
- External/AniCLASS/legacy transfer outputs are transfer-conditional, not native.
- MIO diagnostics/certificates are not posterior odds, truth certificates, or HTT evidence terms.
- HTT owns model-dependent likelihoods, evidence, PPC, LOOCV, null competition, and posterior pushforward.
- OBSSTAT owns observable feature extraction only.
- Scalar `x`, `Q`, `Pi`, `F`, `G_F`, direction coherence, low-ell residuals, or morphology axes do not identify a Bianchi family.
- Bianchi family-ID and geometry-detection claims are blocked unless a native low-ell morphology atlas, matched nulls, masks, covariance, and family-equivalence gates are present.

## Token Discipline

Return findings only. Do not summarize chapters. Do not quote long passages. Cite `path:line` or figure manifest path. If a section is acceptable, write one short sentence. Prefer tables with concise issue text.

## Required Output

Use exactly these sections:

1. `Verdict`: PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. `Minimal Defensible Claim`: one paragraph, conservative.
3. `Fatal Blockers`: only blockers that invalidate the current main claim.
4. `Major Findings`: table with columns `Severity | Location | Problem | Why It Matters | Required Fix`.
5. `Physics/Math Audit`: table with `Item | Status | Issue | Required Fix`.
6. `Statistics/Inference Audit`: table with `Item | Status | Issue | Required Fix`.
7. `Figure/Result Audit`: list only figures/tables whose interpretation is wrong, under-supported, or overclaimed.
8. `Claim-Tier Corrections`: exact wording to downgrade or remove.
9. `Additional Analyses Required`: analyses needed before stronger claims are allowed.
10. `Claims That Are Safe`: bullet list of claims allowed under current evidence.

## Adversarial Checks

### A. Physics and mathematical formalization
- Are frame conventions explicit and consistent: normal frame, matter frame, CMB frame, local boost frame, geometry frame?
- Are units, signs, and dimensions correct for shear, vorticity, tilt rapidity, curvature, `x_C`, `Q`, `Pi`, `F`, and `G_F`?
- Do FLRW, no-tilt, local-boost-only, global-tilt-only, zero-denominator, and rank-deficient limits behave correctly?
- Is `x_C = Sigma^2 - W^2 + Omega_tilt + Omega_k_aniso` treated as a signed comparator coordinate rather than an invariant anisotropy magnitude?
- Is MES use derived under stated assumptions, or merely asserted?
- Are deterministic template effects separated from anisotropic covariance effects?

### B. Transfer and solver provenance
- Wherever a value depends on external/AniCLASS/legacy transfer, is the transfer dependence explicit?
- Does any caption/table imply native BASS/native solver validation?
- Are family labels used only as provenance/equivalence-class labels, not as identified geometry?
- Are future-native adapter/schema discussions clearly non-result surfaces?

### C. Statistical inference and evidence
- Are likelihood factors, priors, channel independence/correlation assumptions, and Occam penalties justified?
- Are Bayes factors robust to channel ablation, prior changes, covariance assumptions, and look-elsewhere effects?
- Are PPC, LOOCV, null competition, and matched-mask/covariance gates present where evidence claims require them?
- Are local boost, global tilt, and survey/systematic alternatives separated?
- Are DESI, CF4, Planck, high-l, and lensing figures descriptive unless calibrated nulls/covariance are bound?
- Are bootstrap/jackknife intervals presented only as diagnostics, not p-values or posteriors?

### D. Observational-data plot interpretation
- Planck low-l residuals: do not accept sigma-bar residuals as full-covariance, cosmic-variance, mask-coupled p-values.
- Planck spectra/lensing: check theory/reference transfer labeling.
- DESI footprint/weights: check sky support and selection-systematics caveats.
- CF4 velocity/density/depth: check volume-coordinate caveats and avoid angular sky-fraction overclaim.
- Long-run jackknife/bootstrap: verify no evidence, p-value, or posterior language is inferred.

### E. Legacy and conditioned figures
- Treat conditioned legacy appendix figures as hypothesis-conditioned diagnostics only.
- Do not allow legacy evidence bars, posterior triangles, pairwise matrices, direction plots, or sensitivity plots to become current production evidence unless current null/PPC/LOOCV/mask/covariance gates are present.
- Check whether legacy material conflicts with current claim boundaries in main chapters.

### F. Manuscript structure and rhetoric
- Identify places where strong rhetoric outruns evidence.
- Flag any manual/status-number claims that should be generated-source claims.
- Flag any result that is visually persuasive but not mathematically/statistically supported.
- Distinguish: proved, derived, implemented, generated, smoke-tested, validated, transfer-conditional, diagnostic-only, proposed, speculative.

## Rejection Triggers

Reject or mark not ready if any of these are used as current results:
- an identified Bianchi family.
- a detected Bianchi geometry.
- native validation claimed for external-transfer output.
- MIO diagnostics promoted into model-weight, likelihood-ratio, or adjudication status.
- Scalar diagnostics alone used as geometry/family evidence.
- Evidence claim lacking required null/covariance/prior/PPC/LOOCV support.
