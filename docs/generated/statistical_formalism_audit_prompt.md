# Adversarial Audit Prompt: x_C/Q/Pi/F/G_F Statistical Formalism

You are an external hostile reviewer. Audit only the statistical and physical formalization of `x_C`, `Q`, `Pi`, `F`, and `G_F`, plus the manuscript/result figures that use them. Do not review software style, packaging aesthetics, CI design, or general code quality.

## Inputs

Read in this order:
1. `READINESS_CHECKLIST.md`
2. `statistical_formalism_audit/docs/manuscript/main.tex`
3. generated LaTeX snippets under `statistical_formalism_audit/docs/manuscript/generated/`
4. `statistical_formalism_audit/docs/generated/current_science_plot_payload.json`
5. `statistical_formalism_audit/docs/generated/result_pack_A.md`
6. `statistical_formalism_audit/docs/generated/result_pack_B.md`
7. `statistical_formalism_audit/docs/generated/result_pack_C.md`
8. VER2 departure/MIO generated reports under `statistical_formalism_audit/docs/ver2_upgrade/generated/`
9. figure manifests under `statistical_formalism_audit/figures/`
10. formalism code/tests only when prose or manifests are insufficient.

## Hard Boundaries

- No native low-ell Bianchi solver result is present.
- External/legacy transfer-dependent results are transfer-conditional.
- MIO diagnostics are not posterior odds, evidence, or truth certificates.
- HTT owns model-dependent likelihood, evidence, PPC, LOOCV, and posterior pushforward.
- `x_C`, `Q`, `Pi`, `F`, `G_F`, direction coherence, residual vectors, or low-ell summaries cannot identify Bianchi family or geometry.

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

### x_C
- Verify sign convention in `x_C = Sigma^2 - W^2 + Omega_tilt + Omega_k_aniso`.
- Check whether `x_C` is ever described as invariant magnitude or geometry evidence.
- Check FLRW, no-tilt, local-boost-only, global-tilt-only, and negative-coordinate limits.

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
- Verify depth-bin metadata, reference/comparison bins, denominator split, null status, and calibration caveats.
- Reject `G_F` as global-tilt evidence unless local/systematic null competition and matched calibration are present.

### MIO/HTT separation
- Check MIO report cards do not create evidence, posterior odds, model ranking, or truth certificates.
- Check HTT posterior pushforward does not merge MIO certificates as evidence.
- Check result packs keep diagnostic status distinct from production readiness labels.

### Figures
- For each included figure, inspect its manifest before judging the caption.
- Treat conditioned legacy figures as prior-context diagnostics only.
- Reject any visual inference that is not supported by manifest claim tier, null status, covariance status, and transfer provenance.

## Rejection Triggers

Reject if any current claim says or implies:
- Bianchi geometry detected.
- Bianchi family identified.
- external transfer validated as native.
- MIO posterior/evidence/truth certificate.
- scalar formalism values alone imply geometry, family, or native-solver validation.
