# Adversarial Audit Prompt: x_C/Q/Pi/F/G_F Statistical Formalism

You are an external hostile reviewer. Audit only the statistical and physical formalization of `x_C`, `Q`, `Pi`, `F`, and `G_F`, plus preserved manuscript/result surfaces that use them. This is a diagnostic audit bundle, not a current manuscript publication source. Do not review software style, packaging aesthetics, CI design, or general code quality.

## Inputs

Read in this order:
1. `READINESS_CHECKLIST.md`
2. `statistical_formalism_audit/docs/manuscript/main.tex` for the fail-closed quarantine notice
3. historical manuscript chapters `ch01_introduction.tex`, `ch03_framework.tex`, `ch07_results.tex`, and `ch09_discussion.tex`, inspected with `public_use:false` and not compiled
4. generated LaTeX snippets under `statistical_formalism_audit/docs/manuscript/generated/`, especially `formalism_methods_claim_ladder.tex`
5. `statistical_formalism_audit/docs/generated/formalism_audit_originality_response_matrix.md`
6. `FIGURE_LABEL_LINTER_REPORT.md`
7. `statistical_formalism_audit/docs/generated/current_science_plot_payload.json`
8. `statistical_formalism_audit/docs/generated/result_pack_A.md`
9. `statistical_formalism_audit/docs/generated/result_pack_B.md`
10. `statistical_formalism_audit/docs/generated/result_pack_C.md`
11. VER2 departure/MIO generated reports under `statistical_formalism_audit/docs/ver2_upgrade/generated/`
12. figure manifests under `statistical_formalism_audit/figures/`
13. formalism code/tests only when prose or manifests are insufficient.

## Hard Boundaries

- No native low-ell Bianchi solver result is present.
- External/legacy transfer-dependent results are transfer-conditional.
- MIO diagnostics are not posterior odds, evidence, or truth certificates.
- HTT owns model-dependent likelihood, evidence, PPC, LOOCV, and posterior pushforward.
- `x_C`, `Q`, `Pi`, `F`, `G_F`, direction coherence, residual vectors, or low-ell summaries cannot identify Bianchi family or geometry.
- CF4 P0 source quarantine blocks a current manuscript build; retained TeX/Bib sources are immutable historical evidence only.

## Required Verdict

Return exactly these sections:

1. `Verdict`: PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. `Minimal Defensible Claim`: one conservative paragraph.
3. `Fatal Blockers`: only blockers that invalidate the formalism or current manuscript use.
4. `Formalism Findings`: table `Severity | Location | Problem | Required Fix`.
5. `Equation/Definition Audit`: table `Quantity | Status | Issue | Required Fix`.
6. `Statistical Semantics Audit`: table `Item | Status | Issue | Required Fix`.
7. `Figure Interpretation Audit`: only figures whose interpretation overreaches.
8. `Claim-Tier Corrections`: exact wording to replace.
9. `Additional Analyses Required`: analyses needed before stronger claims.
10. `Safe Claims`: bullet list.

## Attack Checklist

### Novelty and substance
- Decide whether the manuscript states a genuine methods contribution or merely renames existing diagnostics.
- Check whether the semantic-firewall machinery has operational consequences: forbidden label tests, figure-label linter gates, manifest lanes, and MIO/HTT ownership separation.
- Reject originality claims that are not backed by explicit package evidence, equations, tests, or generated manifests.

### x_C
- Verify sign convention in `x_C = Sigma^2 - W^2 + Omega_tilt + Omega_k_aniso`.
- Check whether `x_C` is ever described as invariant magnitude or geometry evidence.
- Check FLRW, no-tilt, local-boost-only, global-tilt-only, and negative-coordinate limits.
- Require signed sector components and absolute-magnitude summaries wherever cancellation can hide large terms.

### Cancellation and magnitude reporting
- Check all figures and prose that aggregate `x_C`, `Q`, `F`, or `G_F` for cancellation artifacts.
- Require explicit signed sector components, total magnitude, cancellation ratio, or a stated reason why the quantity is not cancellation-sensitive.
- Reject claims that a small signed aggregate is physically small without a companion magnitude diagnostic.

### Q
- Verify numerator and denominator policy are explicit.
- Check denominator positivity, finite status, and policy compatibility.
- Reject uses where `Q` becomes occupancy, filling fraction, posterior probability, or family evidence.

### Pi
- Verify `Pi` is threshold exceedance only.
- Reject truth-probability, detection-probability, or posterior-odds language unless it is explicitly HTT-owned posterior pushforward with matching caveats.
- Check threshold registration and look-elsewhere metadata.

### F
- Verify `F` is certified occupancy only under sign-clean samples and admissible ceiling.
- Check no clipping hides super-ceiling or negative samples.
- Reject claims that external-transfer denominators certify native filling.

### G_F
- Verify depth-bin metadata, reference/comparison bins, floor-applied-by-bin reporting, raw/effective `F`, denominator split, null status, and calibration caveats.
- Treat matched-null `G_F` reports as forecast-only unless observed matched nulls, PPC, LOOCV, prior sweeps, covariance, and native morphology-atlas gates are all explicitly bound.
- Reject `G_F` as global-tilt evidence unless local/systematic null competition and matched calibration are present.

### MIO/HTT separation
- Check MIO report cards do not create evidence, posterior odds, model ranking, or truth certificates.
- Check HTT posterior pushforward does not merge MIO certificates as evidence.
- Check result packs keep diagnostic status distinct from production readiness labels.
- Check whether semantic-firewall machinery blocks leakage across these lanes in generated outputs, not just in prose.

### Legacy lnB leakage
- Identify any `lnB`, Bayes-factor, evidence-like, or production-readiness language inherited from legacy or VER2 files.
- Accept legacy tokens only when they are explicitly archival, not used as current scientific evidence, and do not enter MIO diagnostic claims.
- Reject any hidden promotion of diagnostic reports into observed-data evidence via legacy readiness language.

### Figures
- For each included figure, inspect its manifest before judging the caption.
- Treat conditioned legacy figures as prior-context diagnostics only.
- Reject any visual inference that is not supported by manifest claim tier, null status, covariance status, and transfer provenance.

## Rejection Triggers

Reject if any current claim says or implies:
- a detected Bianchi geometry.
- an identified Bianchi family.
- external-transfer output is described as native-validated.
- diagnostic-only MIO material is promoted into model-probability, evidence-like, or truth-status language.
- scalar formalism values alone imply geometry, family, or native-solver validation.
