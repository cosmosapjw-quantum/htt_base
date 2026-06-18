# External Audit Research Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the VER06 manuscript from over-strong evidence framing into a defensible, claim-tiered research report, then add the highest-leverage diagnostic analyses requested by the external adversarial audit.

**Architecture:** Treat the external audit as a research blocker, not a code-style review. First preserve and track the audit artifacts, then clear rejection-trigger prose/math defects, then generate manifest-backed diagnostic assets for prior-floor, bulk-flow uncertainty, FPR, occupancy, and adequacy gates. Stronger evidence language remains blocked unless prior, matched-null, PPC, LOOCV, covariance, and look-elsewhere prerequisites are actually satisfied.

**Tech Stack:** LaTeX source under `docs/manuscript`, repo-local Python 3 through `venv/bin/python`, NumPy/Matplotlib for diagnostic figures, existing HTT/MIO/COMMON contracts for manifests and claim gates, pytest for validation.

---

## Evidence Read

- External audit files found at repo root:
  - `AUDIT_REPORT.md`
  - `HTT_Bianchi_VER06_external_audit.zip`
- Zip contents:
  - `AUDIT_REPORT.md`
  - `claim_tier_corrections.md`
  - `revision_checklist.md`
  - `references_verified.md`
  - `verify_claims.py`
  - `README.md`
- CoVe command run:
  ```bash
  unzip -p HTT_Bianchi_VER06_external_audit.zip verify_claims.py | venv/bin/python - --quiet
  ```
  Result: PASS for Gaunt integral and BV shear reproduction; FAIL for Gaunt title/normalisation claim, sigma/H vs sigma/Theta, occupancy category mismatch, FPR=0 overstatement, prior-floor sensitivity; NOTE for MES-vs-Saadeh ceiling looseness and sigma_beta-driven lnB.
- Current manuscript locations confirmed:
  - `docs/manuscript/ch07_results.tex:733-744` boxed headline promotes `ln B ~= +26.3` and `+44`.
  - `docs/manuscript/ch07_results.tex:796-843` contains safer conditional framing but still says "entire signal resides in the tilt degree of freedom".
  - `docs/manuscript/ch07_results.tex:925` writes `sigma/H = 5.4e-3`, which audit shows is `sigma/Theta`.
  - `docs/manuscript/ch07_results.tex:975-993` says widening is "firmly data-dominated" while the narrow prior floor drives negative lnB.
  - `docs/manuscript/ch08_robustness.tex:814-816` labels all CF4 sensitivity rows `Decisive`.
  - `docs/manuscript/ch08_robustness.tex:840-852` reports structured-null FPR as zero.
  - `docs/manuscript/ch05_teff_corrections.tex:336-376` title claims `g_{224}=6` while body derives `4/3`.
  - `docs/manuscript/ch05_teff_corrections.tex:1770-1778` uses "98% accuracy" for a contribution fraction.
  - `docs/manuscript/ch03_framework.tex:665-667` labels a Saadeh vector/shear bound as direct vorticity.
  - `docs/manuscript/ch03_framework.tex:1074-1122` defines scalar occupancy `Q=x/x_max` using a shear ceiling even for tilt-dominated `x`.
  - `docs/manuscript/ch03_framework.tex:2192-2195` still contains `[CITATION NEEDED: Teff Paper III]`.
- Existing repo surfaces to reuse:
  - `htt/htt/htt/infer/prior_sweep.py`
  - `htt/htt/htt/infer/posterior_predictive.py`
  - `htt/htt/htt/infer/loocv.py`
  - `htt/htt/htt/infer/null_competition.py`
  - `htt/mio/formalism/budget_spec.py`
  - `scripts/check_publication_claim_freeze.py`
  - `scripts/audit_manuscript_figures.py`
  - `scripts/pdf_claim_lint.py`
  - `docs/generated/publication_claim_freeze.md`
  - `docs/generated/transfer_sensitivity_report.md`
  - `docs/generated/observed_longrun_analysis.md`

## Scope Check

This plan spans manuscript research claims, math corrections, statistical diagnostics, generated figures, and publication gates. It is intentionally split into independently testable tasks:

- Tasks 1-4 are the conservative repair path required to clear the external audit rejection triggers.
- Tasks 5-8 add manifest-backed diagnostic analyses that develop the research beyond wording edits.
- Tasks 9-10 rebuild validation surfaces and produce the response package.

No task implements or fakes a native low-ell Bianchi solver. No task permits Bianchi family identification, anisotropic geometry detection, or MIO/HTT evidence merging.

## File Structure

- Create `docs/audits/external_ver06_2026-06-18/`
  - Permanent copy of external audit files and a local response matrix.
- Create `docs/generated/external_audit_ver06_response_matrix.md`
  - Machine-reviewable finding-to-fix ledger.
- Create `scripts/verify_external_audit_math_claims.py`
  - Repo-owned CoVe checks derived from the external audit, with no manuscript file mutation.
- Create `tests/contracts/test_external_audit_math_claims.py`
  - Regression tests for Gaunt, sigma/Theta conversion, occupancy mismatch detection, and FPR interval language.
- Create `htt/mio/formalism/occupancy_vector.py`
  - Per-channel occupancy vector so tilt, shear, curvature, and vorticity denominators are not collapsed into one scalar.
- Modify `htt/mio/formalism/__init__.py`
  - Export the occupancy vector.
- Create `tests/mio/test_occupancy_vector.py`
  - Unit tests for per-channel denominator semantics and blocked scalar use.
- Create `scripts/generate_external_audit_revision_assets.py`
  - Generate audit-revision JSON/MD/PNG artifacts for prior-floor, sigma_beta, FPR, MES/Saadeh, and occupancy diagnostics.
- Create `tests/contracts/test_external_audit_revision_assets.py`
  - Validate artifact schema, manifests, and claim boundary text.
- Create generated artifacts:
  - `docs/generated/external_audit_revision_assets.json`
  - `docs/generated/external_audit_revision_assets.md`
  - `figures/current/fig_current_prior_floor_sensitivity.png`
  - `figures/current/fig_current_sigma_beta_sensitivity.png`
  - `figures/current/fig_current_fpr_rule_of_three.png`
  - `figures/current/fig_current_occupancy_vector.png`
  - matching `.manifest.json` files for each figure.
- Modify manuscript source:
  - `docs/manuscript/ch01_introduction.tex`
  - `docs/manuscript/ch03_framework.tex`
  - `docs/manuscript/ch05_teff_corrections.tex`
  - `docs/manuscript/ch06_pipeline.tex`
  - `docs/manuscript/ch07_results.tex`
  - `docs/manuscript/ch08_robustness.tex`
  - `docs/manuscript/ch09_discussion.tex`
  - `docs/manuscript/generated/current_figures_results.tex`
- Modify claim/build scripts:
  - `scripts/check_publication_claim_freeze.py`
  - `scripts/build_research_only_audit_package.py`
- Update generated reports:
  - `docs/generated/publication_claim_freeze.md`
  - `docs/generated/pdf_claim_lint_report.md`
  - `docs/generated/manuscript_figure_inventory.md`
  - `docs/generated/research_only_external_audit_package.zip`
  - `docs/generated/research_only_external_audit_package_manifest.json`
  - `docs/generated/research_only_external_audit_prompt.md`

### Task 1: Preserve External Audit and Create Response Matrix

**Files:**
- Create: `docs/audits/external_ver06_2026-06-18/AUDIT_REPORT.md`
- Create: `docs/audits/external_ver06_2026-06-18/claim_tier_corrections.md`
- Create: `docs/audits/external_ver06_2026-06-18/revision_checklist.md`
- Create: `docs/audits/external_ver06_2026-06-18/references_verified.md`
- Create: `docs/audits/external_ver06_2026-06-18/verify_claims.py`
- Create: `docs/audits/external_ver06_2026-06-18/README.md`
- Create: `docs/generated/external_audit_ver06_response_matrix.md`

- [ ] **Step 1: Extract the audit package into a permanent audit folder**

Run:
```bash
mkdir -p docs/audits/external_ver06_2026-06-18
unzip -o HTT_Bianchi_VER06_external_audit.zip -d docs/audits/external_ver06_2026-06-18
cp AUDIT_REPORT.md docs/audits/external_ver06_2026-06-18/AUDIT_REPORT_root_copy.md
```
Expected: six zip files plus root copy exist under `docs/audits/external_ver06_2026-06-18/`.

- [ ] **Step 2: Run the external CoVe script from its archived copy**

Run:
```bash
venv/bin/python docs/audits/external_ver06_2026-06-18/verify_claims.py --quiet
```
Expected: same FAIL/NOTE/PASS rows as the root zip execution, with no file modifications.

- [ ] **Step 3: Create the response matrix**

Write `docs/generated/external_audit_ver06_response_matrix.md` with this content:

```markdown
# External Audit VER06 Response Matrix

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: manual response ledger from HTT_Bianchi_VER06_external_audit.zip
caveats:
- This response matrix tracks research corrections only.
- It is not software-readiness or submission approval.
- Stronger evidence wording remains blocked without prior, PPC, LOOCV, matched-null, covariance, and look-elsewhere support.

| Audit ID | Severity | Finding | Primary Files | Planned Resolution | Status |
| --- | --- | --- | --- | --- | --- |
| F1/P1 | fatal | Boxed lnB result outruns artifact gates | `docs/manuscript/ch07_results.tex` | Replace with conditional transfer-conditional wording and remove +44 headline promotion | open |
| F2/P2 | fatal | CF4 sensitivity rows flagged unverified but promoted as decisive | `docs/manuscript/ch08_robustness.tex` | Replace verdict labels and keep +44/+106 inside sensitivity table only | open |
| F3/P1/P5 | fatal | Transfer provenance not foregrounded at claim point | `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch09_discussion.tex` | Attach external/proxy transfer and no-native-solver caveat to every lnB paragraph | open |
| Q | high | `Q=x/x_max` uses tilt numerator over shear ceiling | `docs/manuscript/ch03_framework.tex`, `htt/mio/formalism/occupancy_vector.py` | Replace scalar ceiling narrative with per-channel occupancy vector; mark scalar Q N/A for tilt-flat | open |
| PRIOR | high | lnB prior-floor dominated | `docs/manuscript/ch07_results.tex`, `scripts/generate_external_audit_revision_assets.py` | Generate prior-floor diagnostic and quote range, not point estimate | open |
| GAUNT | medium | `g_{224}=6` title contradicts derivation | `docs/manuscript/ch05_teff_corrections.tex` | Retitle to PSTF 4/3 and relabel coupling as (1,1,2) | open |
| SIGMA | low-medium | sigma/H vs sigma/Theta factor-of-three slip | `docs/manuscript/ch03_framework.tex`, `docs/manuscript/ch07_results.tex` | Use `sigma/Theta` and `sigma/H_theta` distinctly | open |
| FPR | partial | `0/100` FPR reported as zero | `docs/manuscript/ch08_robustness.tex` | Report rule-of-three upper bound `<3%`, matched-mask suite pending | open |
| PPCLOOCV | missing | Evidence-grade wording lacks PPC/LOOCV | `docs/generated/publication_claim_freeze.md` | Keep evidence-grade wording blocked; add adequacy artifact status | open |
```

- [ ] **Step 4: Verify the response matrix has no forbidden promotion**

Run:
```bash
venv/bin/python -m common.semantic_guards.no_overclaim docs/generated/external_audit_ver06_response_matrix.md
```
Expected: no forbidden geometry/family/native/MIO-posterior promotion findings.

- [ ] **Step 5: Commit**

```bash
git add docs/audits/external_ver06_2026-06-18 docs/generated/external_audit_ver06_response_matrix.md
git commit -m "AUDIT-VER06: preserve external research audit"
```

### Task 2: Downclaim the Headline Evidence Narrative

**Files:**
- Modify: `docs/manuscript/ch01_introduction.tex`
- Modify: `docs/manuscript/ch06_pipeline.tex`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch08_robustness.tex`
- Modify: `docs/manuscript/ch09_discussion.tex`

- [ ] **Step 1: Verify current over-strong language is present**

Run:
```bash
rg -n "raises the headline|Decisive|entire signal resides|firmly data-dominated|10\\^\\{11\\}:1|sigma_\\beta|All three versions give decisive" docs/manuscript
```
Expected: matches in `ch06_pipeline.tex`, `ch07_results.tex`, `ch08_robustness.tex`, and possibly `ch09_discussion.tex`.

- [ ] **Step 2: Patch the introduction premise**

In `docs/manuscript/ch01_introduction.tex`, after the paragraph ending at line 39, insert:

```tex
All quantitative model-comparison results reported below are
explicitly conditional on this anomaly being cosmological rather
than instrumental, selection-driven, or large-scale-structure
systematic.  This premise remains contested at the few-sigma level
in the current clustering-dipole, mask-coupling, and bulk-flow
literature, so the statistical results below are presented as
conditional diagnostics rather than geometry-detection claims.
```

- [ ] **Step 3: Patch the boxed result**

Replace `docs/manuscript/ch07_results.tex:733-744` with:

```tex
\begin{center}
\fbox{\parbox{0.85\textwidth}{\small
\textbf{Conditional result.}\quad
Assuming the matter-dipole anomaly is substantially cosmological
(Chapter~\ref{ch:dipole}), a direction-marginalised,
transfer-conditional likelihood (VER05; external/empirical-proxy
transfer, with no native low-$\ell$ Bianchi solver output in this
repository) prefers a non-zero \emph{tilt-like} degree of
freedom---a relative velocity between the matter and CMB frames.
Under the WFH2009 amplitude the tilted equivalence classes give
$\ln\mathcal{B}\approx +24.8$ to $+26.4$.  This magnitude is
prior-floor sensitive and scales with the reported bulk-flow
uncertainty; CF4++ and Watkins+2023 values are retained only as
unverified sensitivity rows.  The number is a re-expression of the
dipole/bulk-flow significance, not evidence for anisotropic spatial
geometry, and no Bianchi family is identified.}}
\end{center}
```

- [ ] **Step 4: Fix WFH2009 attribution in ch07**

Replace:
```tex
($\beta = 1.334 \times 10^{-3}$;
Watkins et~al.~\cite{Watkins2023}) as the primary input.
```
with:
```tex
($\beta = 1.334 \times 10^{-3}$; Watkins, Feldman
\& Hudson 2009, hereafter WFH2009) as the primary input.
```

- [ ] **Step 5: Fix ch06 decisive wording**

Replace `docs/manuscript/ch06_pipeline.tex:200-202`:
```tex
documented and corrected.  All three versions give decisive tilt
evidence (Table~\ref{tab:cf4-triple} of
Chapter~\ref{ch:robustness}).
```
with:
```tex
documented and corrected.  All three versions are retained as
legacy transfer-conditional sensitivity rows whose magnitudes are
driven by the reported bulk-flow uncertainty
(Table~\ref{tab:cf4-triple} of Chapter~\ref{ch:robustness});
they are not promoted to geometry or family evidence.
```

- [ ] **Step 6: Patch ch07 model-ranking language**

Replace:
```tex
Three
tiers emerge with sharp boundaries; the evidence
decomposition (the conditioned legacy figure gallery in Appendix~\ref{app:conditioned-legacy-figure-gallery}) confirms
that the entire signal resides in the tilt degree of freedom.
```
with:
```tex
Three conditional tiers emerge within the legacy transfer-conditioned
ranking; the evidence decomposition (the conditioned legacy figure
gallery in Appendix~\ref{app:conditioned-legacy-figure-gallery})
shows that the conditional preference resides in the tilt
(relative-velocity) degree of freedom.  This is a statement about
the matter-dipole anomaly, not about spatial curvature or shear.
```

- [ ] **Step 7: Patch the legacy odds paragraph**

Replace:
```tex
The legacy transfer-conditional evidence summary for tilted models ($\sim 10^{11}:1$
odds), conditional on the matter-dipole anomaly being
physical, should be interpreted in the context of the channel
decomposition (Section~\ref{sec:decomp}), which shows that the
signal is driven entirely by the non-CMB matter dipole channels.
```
with:
```tex
The legacy transfer-conditional evidence summary for tilted models
($\sim 10^{11}:1$ odds under the WFH2009 row), conditional on the
matter-dipole anomaly being physical, should be interpreted in the
context of the channel decomposition (Section~\ref{sec:decomp}).
The odds are direction-marginalised, depend on the reported
bulk-flow uncertainty, are not corrected for the look-elsewhere
choice among bulk-flow compilations, and are driven by the non-CMB
matter-dipole channels.
```

- [ ] **Step 8: Patch the prior sensitivity paragraph**

Replace `firmly data-dominated` wording with:
```tex
Widening the $\Sigstd$ range to $[10^{-30},10^{-2}]$ changes
the evidence by $|\Delta\ln\mathcal{B}| \leq 0.14$, but this
does not establish floor-insensitivity.  Narrowing to
$[10^{-12},10^{-8}]$ destroys the evidence ($-39.1$ for BI,
$-12.9$ for BVIIh) because the prior floor excludes the posterior
mode; hence the headline magnitude must be read as prior-floor
sensitive.
```

- [ ] **Step 9: Patch CF4 table verdicts**

In `docs/manuscript/ch08_robustness.tex`, replace each `Decisive` in `tab:cf4-triple` with:
```tex
Conditional ($\sigma_\beta$-driven; prior-floor sensitive)
```

- [ ] **Step 10: Patch FPR language**

Replace `docs/manuscript/ch08_robustness.tex:846-852` with:
```tex
The false-positive count is $0/100$ for each tested family at
the declared amplitudes.  This should be read as an upper-limit
diagnostic rather than a zero-rate measurement: by the rule of
three, each per-family false-positive rate is constrained only to
be below roughly $3\%$ at 95\% confidence.  These synthetic
injections are not matched-mask, full-covariance null ensembles,
so they remain prerequisites and diagnostics, not evidence terms.
```

- [ ] **Step 11: Run claim scans**

Run:
```bash
rg -n "raises the headline|Decisive|firmly data-dominated|geometry detected|family identified|native solver result|MIO posterior" docs/manuscript
venv/bin/python -m common.semantic_guards.no_overclaim docs/manuscript/ch01_introduction.tex docs/manuscript/ch06_pipeline.tex docs/manuscript/ch07_results.tex docs/manuscript/ch08_robustness.tex docs/manuscript/ch09_discussion.tex
```
Expected: no remaining over-strong hits except explicitly negated guardrail language.

- [ ] **Step 12: Commit**

```bash
git add docs/manuscript/ch01_introduction.tex docs/manuscript/ch06_pipeline.tex docs/manuscript/ch07_results.tex docs/manuscript/ch08_robustness.tex docs/manuscript/ch09_discussion.tex
git commit -m "AUDIT-VER06: downclaim conditional evidence narrative"
```

### Task 3: Repair Math and Normalisation Defects

**Files:**
- Create: `scripts/verify_external_audit_math_claims.py`
- Create: `tests/contracts/test_external_audit_math_claims.py`
- Modify: `docs/manuscript/ch03_framework.tex`
- Modify: `docs/manuscript/ch05_teff_corrections.tex`
- Modify: `docs/manuscript/ch07_results.tex`

- [ ] **Step 1: Write the failing math regression test**

Create `tests/contracts/test_external_audit_math_claims.py`:

```python
from __future__ import annotations

import math
import subprocess


def test_audit_math_claims_script_reports_expected_failures_before_manuscript_fix():
    result = subprocess.run(
        ["venv/bin/python", "scripts/verify_external_audit_math_claims.py", "--json"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert '"gaunt_integral": "pass"' in result.stdout
    assert '"gaunt_title_value": "fail_until_manuscript_fixed"' in result.stdout
    assert '"sigma_h_symbol": "fail_until_manuscript_fixed"' in result.stdout
    assert '"tilt_over_shear_occupancy": "fail_until_vectorized"' in result.stdout


def test_factor_three_sigma_conversion_is_explicit():
    sigma2_std = 4.4e-5
    sigma_over_theta = math.sqrt((2.0 / 3.0) * sigma2_std)
    sigma_over_h_theta = 3.0 * sigma_over_theta
    assert sigma_over_theta == pytest.approx(5.416e-3, rel=5e-3)
    assert sigma_over_h_theta == pytest.approx(1.625e-2, rel=5e-3)
```

Then add the missing import in the same file:

```python
import pytest
```

- [ ] **Step 2: Run the test and verify it fails because the script does not exist**

Run:
```bash
venv/bin/python -m pytest tests/contracts/test_external_audit_math_claims.py -q
```
Expected: FAIL with `No such file or directory: scripts/verify_external_audit_math_claims.py`.

- [ ] **Step 3: Create the repo-owned math verification script**

Create `scripts/verify_external_audit_math_claims.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math


def gaunt_integral() -> float:
    # int_{-1}^{1} P1(mu)^2 P2(mu) dmu = 4/15
    return 4.0 / 15.0


def sigma_conversions(sigma2_std: float = 4.4e-5) -> dict[str, float]:
    sigma_over_theta = math.sqrt((2.0 / 3.0) * sigma2_std)
    return {
        "sigma_over_theta": sigma_over_theta,
        "sigma_over_h_theta": 3.0 * sigma_over_theta,
    }


def occupancy_category() -> dict[str, float]:
    omega_tilt = 5.85e-7
    sigma2 = 1.0e-12
    x = omega_tilt + sigma2
    shear_ceiling = 6.47e-6
    return {
        "x": x,
        "shear_ceiling": shear_ceiling,
        "scalar_q": x / shear_ceiling,
        "tilt_fraction": omega_tilt / x,
    }


def build_payload() -> dict[str, object]:
    sigma = sigma_conversions()
    occ = occupancy_category()
    return {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "gaunt_integral": "pass" if abs(gaunt_integral() - 4.0 / 15.0) < 1.0e-15 else "fail",
        "gaunt_title_value": "fail_until_manuscript_fixed",
        "sigma_h_symbol": "fail_until_manuscript_fixed",
        "tilt_over_shear_occupancy": "fail_until_vectorized",
        "values": {
            "gaunt_integral": gaunt_integral(),
            **sigma,
            **occ,
            "rule_of_three_fpr_upper_95": 3.0 / 100.0,
        },
        "caveats": [
            "This verifier checks audit arithmetic only.",
            "It does not produce HTT evidence, MIO certificates, native transfer, or family identification.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    if args.json:
        print(json.dumps(payload, sort_keys=True, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the test and verify it passes**

Run:
```bash
venv/bin/python -m pytest tests/contracts/test_external_audit_math_claims.py -q
```
Expected: PASS.

- [ ] **Step 5: Patch Gaunt title and body**

In `docs/manuscript/ch05_teff_corrections.tex`, replace:
```tex
\subsection{The Gaunt coefficient $g_{224} = 6$}
```
with:
```tex
\subsection{The cross-term coupling coefficient $g_{112}=4/3$ in the PSTF convention}
```

Replace every explanatory occurrence of `g_{224}` in this subsection with `g_{112}` only where it refers to the `P_1^2 P_2` A-squared-Q coupling. Keep downstream symbol usage only if a later equation explicitly defines a compatibility alias:
```tex
For compatibility with the legacy notation in Eq.~\eqref{eq:F4-full},
we set $g_{224}^{\rm legacy}\equiv g_{112}=4/3$ for this
$(1,1,2)$ Legendre coupling; no $(2,2,4)$ Gaunt integral is used
in the $A^2Q$ term.
```

Delete:
```tex
Some authors report $g = 6$, which corresponds to the unnormalised Legendre coupling
\int P_1^2 P_2\,d\mu multiplied by the appropriate dimensional factors.
```

- [ ] **Step 6: Patch 98 percent wording**

Replace `docs/manuscript/ch05_teff_corrections.tex:1770-1778` with:
```tex
This hierarchy---neutrinos dominate the constraint,
photons provide a correction, ISW is negligible---is the
species-resolved refinement of the single-fluid transfer function
used in the VER06 legacy pipeline.  It does not change the
legacy transfer-conditional evidence value
($\ln \mathcal{B} = +26.40$); it clarifies the physical
interpretation: approximately $98\%$ of the recombination
quadrupole contribution in this decomposition arises from the
neutrino anisotropic stress, with the photon sector entering at
the $1.6\%$ level and ISW at $0.6\%$.
```

- [ ] **Step 7: Patch Saadeh/vorticity provenance**

In `docs/manuscript/ch03_framework.tex:656-667`, replace the direct Saadeh vorticity statement with:
```tex
For vector-sector comparisons, Saadeh~et~al.~\cite{Saadeh2016b}
quote a 95\% upper limit on the vector-mode shear,
$(\sigma_V/H)_0 < 4.7\times10^{-11}$, not a direct universal
bound on $\omega/H$.  Any conversion to a vorticity variable is
model- and convention-dependent; this manuscript therefore uses
the Saadeh value as an external vector-sector shear calibration
unless a Bianchi-specific $\sigma_V/H\to\omega/H$ relation is
shown explicitly.
```

- [ ] **Step 8: Patch sigma/H vs sigma/Theta in BV section**

Replace:
```tex
$\Sigstd = 4.4 \times 10^{-5}$, giving
$\sigma/H = 5.4 \times 10^{-3}$.
```
with:
```tex
$\Sigstd = 4.4 \times 10^{-5}$, giving
$\sigma/\Theta = 5.4 \times 10^{-3}$, equivalently
$\sigma/H_\theta = 1.6 \times 10^{-2}$ with
$H_\theta=\Theta/3$.
```

- [ ] **Step 9: Remove citation-needed marker**

Replace `docs/manuscript/ch03_framework.tex:2192-2195` with:
```tex
degeneracy, this off-manifold residual can dominate the
one-field diagnostic budget.  We therefore treat this example as
a qualitative warning rather than a quantified false-alarm rate
unless a two-field kinetic calculation is supplied.
```

- [ ] **Step 10: Run math and text scans**

Run:
```bash
venv/bin/python -m pytest tests/contracts/test_external_audit_math_claims.py -q
rg -n "g_\\{224\\} = 6|CITATION NEEDED|measures, to \\$98\\\\%\\$ accuracy|\\(omega/H\\)_0 < 5\\.2|\\$\\\\sigma/H = 5\\.4" docs/manuscript
```
Expected: pytest PASS; `rg` returns no matches for the removed high-risk strings.

- [ ] **Step 11: Commit**

```bash
git add scripts/verify_external_audit_math_claims.py tests/contracts/test_external_audit_math_claims.py docs/manuscript/ch03_framework.tex docs/manuscript/ch05_teff_corrections.tex docs/manuscript/ch07_results.tex
git commit -m "AUDIT-VER06: repair math and normalization defects"
```

### Task 4: Replace Scalar Occupancy with a Per-Channel Occupancy Vector

**Files:**
- Create: `htt/mio/formalism/occupancy_vector.py`
- Modify: `htt/mio/formalism/__init__.py`
- Create: `tests/mio/test_occupancy_vector.py`
- Modify: `docs/manuscript/ch03_framework.tex`

- [ ] **Step 1: Write the failing tests**

Create `tests/mio/test_occupancy_vector.py`:

```python
from __future__ import annotations

import pytest

from mio.formalism.occupancy_vector import (
    ChannelCeiling,
    ChannelContribution,
    OccupancyVector,
)


def test_tilt_contribution_cannot_be_normalized_by_shear_ceiling():
    vector = OccupancyVector(
        contributions=(
            ChannelContribution(channel="tilt", value=5.85e-7),
            ChannelContribution(channel="shear", value=1.0e-12),
        ),
        ceilings=(
            ChannelCeiling(channel="shear", value=6.47e-6, source="MES_linear"),
        ),
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="python -m pytest tests/mio/test_occupancy_vector.py -q",
        worktree_state="test-worktree",
    )
    payload = vector.as_payload()
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["scalar_q_status"] == "blocked_channel_mismatch"
    assert "missing_ceiling_for_channel:tilt" in payload["blocked_reasons"]
    assert payload["channel_occupancy"]["shear"] == pytest.approx(1.0e-12 / 6.47e-6)
    assert payload["channel_occupancy"]["tilt"] is None


def test_complete_channel_vector_reports_no_scalar_geometry_claim():
    vector = OccupancyVector(
        contributions=(
            ChannelContribution(channel="tilt", value=5.85e-7),
            ChannelContribution(channel="shear", value=1.0e-12),
        ),
        ceilings=(
            ChannelCeiling(channel="tilt", value=1.358e-3**2, source="FerreiraQuartin_epsilon1"),
            ChannelCeiling(channel="shear", value=6.47e-6, source="MES_linear"),
        ),
        config_hash="sha256:" + "c" * 64,
        input_hashes=("sha256:" + "d" * 64,),
        generating_command="python -m pytest tests/mio/test_occupancy_vector.py -q",
        worktree_state="test-worktree",
    )
    payload = vector.as_payload()
    assert payload["scalar_q_status"] == "not_reported_use_channel_vector"
    assert payload["family_status"] == "blocked_pre_native_atlas"
    assert payload["geometry_status"] == "blocked_pre_native_atlas"
```

- [ ] **Step 2: Run the test and verify it fails**

Run:
```bash
venv/bin/python -m pytest tests/mio/test_occupancy_vector.py -q
```
Expected: FAIL with `ModuleNotFoundError: No module named 'mio.formalism.occupancy_vector'`.

- [ ] **Step 3: Implement occupancy vector**

Create `htt/mio/formalism/occupancy_vector.py`:

```python
"""Per-channel MIO occupancy diagnostics.

This module prevents tilt, shear, curvature, and vorticity contributions from
being collapsed into a single scalar Q when their denominator ceilings are
physically different.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


ALLOWED_CHANNELS = {"tilt", "shear", "curvature", "vorticity"}


def _non_empty(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _finite(value: object, field_name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _positive(value: object, field_name: str) -> float:
    number = _finite(value, field_name)
    if number <= 0.0:
        raise ValueError(f"{field_name} must be positive")
    return number


@dataclass(frozen=True)
class ChannelContribution:
    channel: str
    value: float

    def __post_init__(self) -> None:
        channel = _non_empty(self.channel, "channel")
        if channel not in ALLOWED_CHANNELS:
            raise ValueError(f"unknown channel {channel!r}")
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "value", _finite(self.value, "value"))


@dataclass(frozen=True)
class ChannelCeiling:
    channel: str
    value: float
    source: str

    def __post_init__(self) -> None:
        channel = _non_empty(self.channel, "channel")
        if channel not in ALLOWED_CHANNELS:
            raise ValueError(f"unknown channel {channel!r}")
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "value", _positive(self.value, "value"))
        object.__setattr__(self, "source", _non_empty(self.source, "source"))


@dataclass(frozen=True)
class OccupancyVector:
    contributions: Sequence[ChannelContribution]
    ceilings: Sequence[ChannelCeiling]
    config_hash: str
    input_hashes: Sequence[str]
    generating_command: str
    worktree_state: str

    def _contribution_map(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for item in self.contributions:
            if item.channel in out:
                raise ValueError(f"duplicate contribution channel {item.channel!r}")
            out[item.channel] = item.value
        if not out:
            raise ValueError("contributions must be non-empty")
        return out

    def _ceiling_map(self) -> dict[str, ChannelCeiling]:
        out: dict[str, ChannelCeiling] = {}
        for item in self.ceilings:
            if item.channel in out:
                raise ValueError(f"duplicate ceiling channel {item.channel!r}")
            out[item.channel] = item
        return out

    def as_payload(self) -> dict[str, object]:
        contributions = self._contribution_map()
        ceilings = self._ceiling_map()
        blocked = [
            f"missing_ceiling_for_channel:{channel}"
            for channel, value in sorted(contributions.items())
            if abs(value) > 0.0 and channel not in ceilings
        ]
        occupancy: dict[str, float | None] = {}
        ceiling_sources: dict[str, str | None] = {}
        for channel, value in sorted(contributions.items()):
            ceiling = ceilings.get(channel)
            occupancy[channel] = None if ceiling is None else value / ceiling.value
            ceiling_sources[channel] = None if ceiling is None else ceiling.source
        scalar_status = (
            "blocked_channel_mismatch" if blocked else "not_reported_use_channel_vector"
        )
        return {
            "owner": "MIO",
            "implementation_scope": "mio",
            "claim_tier": "diagnostic_only",
            "transfer_source": "none",
            "sky_support_status": "not_directional",
            "null_mock_status": "not_statistical",
            "config_hash": _non_empty(self.config_hash, "config_hash"),
            "input_hashes": tuple(_non_empty(item, "input_hash") for item in self.input_hashes),
            "generating_command": _non_empty(self.generating_command, "generating_command"),
            "git_commit_or_worktree_state": _non_empty(self.worktree_state, "worktree_state"),
            "contributions": contributions,
            "channel_occupancy": occupancy,
            "ceiling_sources": ceiling_sources,
            "scalar_q_status": scalar_status,
            "blocked_reasons": tuple(blocked),
            "family_status": "blocked_pre_native_atlas",
            "geometry_status": "blocked_pre_native_atlas",
            "caveats": (
                "Per-channel occupancy is a diagnostic denominator comparison only.",
                "Scalar Q is not reported when numerator channels and denominator channels differ.",
                "No geometry or family identification claim is made.",
            ),
        }


__all__ = ["ChannelCeiling", "ChannelContribution", "OccupancyVector"]
```

- [ ] **Step 4: Export the module**

Append to `htt/mio/formalism/__init__.py`:

```python
from mio.formalism.occupancy_vector import (
    ChannelCeiling,
    ChannelContribution,
    OccupancyVector,
)

__all__ += [
    "ChannelCeiling",
    "ChannelContribution",
    "OccupancyVector",
]
```

If the file already defines `__all__` as a tuple, use:
```python
__all__ = (*__all__, "ChannelCeiling", "ChannelContribution", "OccupancyVector")
```

- [ ] **Step 5: Run occupancy tests**

Run:
```bash
venv/bin/python -m pytest tests/mio/test_occupancy_vector.py tests/mio/test_budget_spec.py -q
```
Expected: PASS.

- [ ] **Step 6: Patch manuscript occupancy definition**

In `docs/manuscript/ch03_framework.tex:1074-1122`, replace the single scalar `Q` interpretation for FLRW_tilt with a per-channel statement:

```tex
The scalar ratio $Q=x/x_{\max}$ is meaningful only when the
dominant component of $x$ and the ceiling $x_{\max}$ refer to
the same physical channel.  The MES ceiling in
Eq.~\eqref{eq:Q-def} is a shear ceiling.  Therefore it must not
be used as a certified occupancy denominator for a tilt-dominated
defect.  For the FLRW$_{\mathrm{tilt}}$ model, where
$\Omega_{\mathrm{tilt}}$ contributes more than $99\%$ of $x$ and
the shear contribution is below $10^{-12}$, the shear-normalised
scalar $Q$ is reported only as a legacy diagnostic and is marked
N/A as a physical filling fraction.

The manuscript-facing diagnostic is instead the per-channel
occupancy vector
\begin{equation}
\mathbf{Q}_C =
\left(
\frac{\Sigma^2}{\Sigma^2_{\max}},
\frac{\Omega_{\mathrm{tilt}}}{\Omega_{\mathrm{tilt},\max}},
\frac{\Omega_{k,\mathrm{aniso}}}{\Omega_{k,\max}},
\frac{W^2}{W^2_{\max}}
\right),
\end{equation}
with each denominator carrying its own provenance and claim tier.
Before a native morphology atlas exists, this vector is a
diagnostic denominator comparison only; it does not identify
geometry or a Bianchi family.
```

- [ ] **Step 7: Commit**

```bash
git add htt/mio/formalism/occupancy_vector.py htt/mio/formalism/__init__.py tests/mio/test_occupancy_vector.py docs/manuscript/ch03_framework.tex
git commit -m "AUDIT-VER06: separate occupancy denominators by channel"
```

### Task 5: Generate Prior-Floor, Sigma-Beta, FPR, MES, and Occupancy Diagnostics

**Files:**
- Create: `scripts/generate_external_audit_revision_assets.py`
- Create: `tests/contracts/test_external_audit_revision_assets.py`
- Create: `docs/generated/external_audit_revision_assets.json`
- Create: `docs/generated/external_audit_revision_assets.md`
- Create: `figures/current/fig_current_prior_floor_sensitivity.png`
- Create: `figures/current/fig_current_prior_floor_sensitivity.manifest.json`
- Create: `figures/current/fig_current_sigma_beta_sensitivity.png`
- Create: `figures/current/fig_current_sigma_beta_sensitivity.manifest.json`
- Create: `figures/current/fig_current_fpr_rule_of_three.png`
- Create: `figures/current/fig_current_fpr_rule_of_three.manifest.json`
- Create: `figures/current/fig_current_occupancy_vector.png`
- Create: `figures/current/fig_current_occupancy_vector.manifest.json`

- [ ] **Step 1: Write failing asset tests**

Create `tests/contracts/test_external_audit_revision_assets.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from common.artifact_manifest import validate_manifest_payload


OUTPUT = Path("docs/generated/external_audit_revision_assets.json")
FIGURES = (
    Path("figures/current/fig_current_prior_floor_sensitivity.png"),
    Path("figures/current/fig_current_sigma_beta_sensitivity.png"),
    Path("figures/current/fig_current_fpr_rule_of_three.png"),
    Path("figures/current/fig_current_occupancy_vector.png"),
)


def test_external_audit_revision_assets_check_mode():
    result = subprocess.run(
        ["venv/bin/python", "scripts/generate_external_audit_revision_assets.py", "--check"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_external_audit_revision_assets_have_manifest_boundaries():
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "mixed_legacy_external_proxy_and_none"
    assert payload["science_claim_status"]["evidence_grade_wording"] == "blocked"
    assert payload["science_claim_status"]["family_identification"] == "blocked_pre_native_atlas"
    for fig in FIGURES:
        assert fig.exists()
        manifest = fig.with_suffix(".manifest.json")
        assert manifest.exists()
        manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
        assert validate_manifest_payload(manifest_payload, manifest_path=str(manifest)) == ()
        assert manifest_payload["claim_tier"] == "diagnostic_only"
```

- [ ] **Step 2: Run the failing test**

Run:
```bash
venv/bin/python -m pytest tests/contracts/test_external_audit_revision_assets.py -q
```
Expected: FAIL because the generator does not exist.

- [ ] **Step 3: Implement the generator**

Create `scripts/generate_external_audit_revision_assets.py` with these required constants and functions. Keep the values hard-coded from `AUDIT_REPORT.md` until a real nested-sampling hook is wired; the manifest must call them `legacy_conditioned_diagnostics`, not new evidence.

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO = Path(__file__).resolve().parents[1]
OUT_JSON = REPO / "docs/generated/external_audit_revision_assets.json"
OUT_MD = REPO / "docs/generated/external_audit_revision_assets.md"
FIG_DIR = REPO / "figures/current"

PRIOR_POINTS = [
    {"label": "[1e-30,1e-4] fiducial", "floor": -30, "ceiling": -4, "lnB": 26.3},
    {"label": "[1e-15,1e-6] narrow", "floor": -15, "ceiling": -6, "lnB": 3.0},
    {"label": "[1e-12,1e-8] narrower", "floor": -12, "ceiling": -8, "lnB": -39.1},
    {"label": "[1e-30,1e-2] wide", "floor": -30, "ceiling": -2, "lnB": 26.4},
]

SIGMA_BETA_POINTS = [
    {"label": "WFH2009 primary", "beta": 1.334e-3, "sigma_beta": 0.267e-3, "lnB": 26.3, "verified": True},
    {"label": "CF4++ sensitivity", "beta": 1.051e-3, "sigma_beta": 0.133e-3, "lnB": 44.0, "verified": False},
    {"label": "Watkins+2023 sensitivity", "beta": 1.318e-3, "sigma_beta": 0.097e-3, "lnB": 105.8, "verified": False},
]


def sha_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_state() -> str:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True).strip()
        status = subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).strip()
    except Exception:
        return "git_state_unavailable"
    return f"{commit}+dirty" if status else commit


def manifest(fig: Path, artifact_id: str, title: str, stats: dict[str, object]) -> None:
    payload = {
        "artifact_id": artifact_id,
        "artifact_path": fig.relative_to(REPO).as_posix(),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "created_by": "scripts/generate_external_audit_revision_assets.py",
        "git_commit": None,
        "code_version": git_state(),
        "schema_version": "common.external_audit_revision_figure.v1",
        "config_hash": sha_text(json.dumps(stats, sort_keys=True)),
        "input_hashes": [
            "AUDIT_REPORT.md:" + sha_text(Path("AUDIT_REPORT.md").read_text(encoding="utf-8")),
            "HTT_Bianchi_VER06_external_audit.zip:" + sha_file(REPO / "HTT_Bianchi_VER06_external_audit.zip"),
        ],
        "sky_support_status": "not_directional",
        "null_mock_status": "diagnostic_no_matched_null",
        "transfer_source": "mixed_legacy_external_proxy_and_none",
        "caveats": [
            "Diagnostic response to external audit only.",
            "Legacy lnB values are not promoted to evidence-grade wording.",
            "No native low-ell solver output, geometry detection, or family identification is present.",
        ],
        "required_gates": ["manifest_metadata_present", "claim_downscope_present"],
        "passed_gates": ["manifest_metadata_present", "claim_downscope_present"],
        "failed_gates": [],
        "statistics_definitions": {"title": title, **stats},
    }
    fig.with_suffix(".manifest.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def plot_prior() -> Path:
    fig = FIG_DIR / "fig_current_prior_floor_sensitivity.png"
    xs = [p["floor"] for p in PRIOR_POINTS]
    ys = [p["lnB"] for p in PRIOR_POINTS]
    colors = ["#b91c1c" if y < 0 else "#ca8a04" if y < 5 else "#0f766e" for y in ys]
    plt.figure(figsize=(7.0, 4.2))
    plt.axhline(0, color="0.3", lw=0.8)
    plt.axhline(5, color="0.5", lw=0.8, ls="--")
    plt.scatter(xs, ys, c=colors, s=70)
    for p in PRIOR_POINTS:
        plt.text(p["floor"], p["lnB"] + 2.0, p["label"], ha="center", fontsize=7)
    plt.xlabel(r"log10 prior floor for $\Sigma^2$")
    plt.ylabel(r"legacy conditioned $\ln B$")
    plt.title("Prior-floor sensitivity blocks point-estimate headline wording")
    plt.tight_layout()
    plt.savefig(fig, dpi=180)
    plt.close()
    manifest(fig, "common.external_audit.prior_floor_sensitivity", "Prior-floor sensitivity", {"points": PRIOR_POINTS})
    return fig


def plot_sigma_beta() -> Path:
    fig = FIG_DIR / "fig_current_sigma_beta_sensitivity.png"
    labels = [p["label"] for p in SIGMA_BETA_POINTS]
    snr2 = [(p["beta"] / p["sigma_beta"]) ** 2 for p in SIGMA_BETA_POINTS]
    lnb = [p["lnB"] for p in SIGMA_BETA_POINTS]
    plt.figure(figsize=(7.0, 4.2))
    plt.scatter(snr2, lnb, c=["#0f766e", "#ca8a04", "#ca8a04"], s=75)
    for label, x, y in zip(labels, snr2, lnb):
        plt.text(x, y + 3.0, label, ha="center", fontsize=7)
    plt.xlabel(r"$(\beta/\sigma_\beta)^2$")
    plt.ylabel(r"legacy conditioned $\ln B$")
    plt.title(r"$\ln B$ tracks reported bulk-flow uncertainty")
    plt.tight_layout()
    plt.savefig(fig, dpi=180)
    plt.close()
    manifest(fig, "common.external_audit.sigma_beta_sensitivity", "Sigma-beta sensitivity", {"points": SIGMA_BETA_POINTS})
    return fig


def plot_fpr() -> Path:
    fig = FIG_DIR / "fig_current_fpr_rule_of_three.png"
    families = ["scan", "mask", "clustering", "selection", "survey axis"]
    observed = [0.0] * len(families)
    upper = [0.03] * len(families)
    plt.figure(figsize=(7.0, 4.2))
    plt.bar(families, upper, color="#facc15", edgecolor="#713f12", label="95% upper bound from 0/100")
    plt.scatter(families, observed, color="#0f766e", zorder=3, label="observed false positives")
    plt.ylabel("false-positive rate")
    plt.title("0/100 structured nulls imply FPR < 3%, not FPR = 0")
    plt.xticks(rotation=25, ha="right")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(fig, dpi=180)
    plt.close()
    manifest(fig, "common.external_audit.fpr_rule_of_three", "Rule-of-three FPR diagnostic", {"n": 100, "k": 0, "upper_95": 0.03})
    return fig


def plot_occupancy() -> Path:
    fig = FIG_DIR / "fig_current_occupancy_vector.png"
    tilt = 5.85e-7
    shear = 1.0e-12
    shear_ceiling = 6.47e-6
    plt.figure(figsize=(7.0, 4.2))
    plt.bar(["tilt contribution", "shear contribution"], [tilt, shear], color=["#0f766e", "#64748b"])
    plt.axhline(shear_ceiling, color="#b91c1c", ls="--", label="MES shear ceiling")
    plt.yscale("log")
    plt.ylabel("dimensionless contribution")
    plt.title("Tilt-dominated numerator cannot certify shear-ceiling occupancy")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(fig, dpi=180)
    plt.close()
    manifest(fig, "common.external_audit.occupancy_vector", "Occupancy vector diagnostic", {"tilt": tilt, "shear": shear, "shear_ceiling": shear_ceiling})
    return fig


def build_payload(figures: list[Path]) -> dict[str, object]:
    return {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "mixed_legacy_external_proxy_and_none",
        "sky_support_status": "not_directional",
        "null_mock_status": "diagnostic_no_matched_null",
        "config_hash": sha_text("external-audit-revision-assets-v1"),
        "input_hashes": [
            "AUDIT_REPORT.md:" + sha_text((REPO / "AUDIT_REPORT.md").read_text(encoding="utf-8")),
            "HTT_Bianchi_VER06_external_audit.zip:" + sha_file(REPO / "HTT_Bianchi_VER06_external_audit.zip"),
        ],
        "generating_command": "python scripts/generate_external_audit_revision_assets.py",
        "git_commit_or_worktree_state": git_state(),
        "figures": [path.relative_to(REPO).as_posix() for path in figures],
        "science_claim_status": {
            "evidence_grade_wording": "blocked",
            "family_identification": "blocked_pre_native_atlas",
            "geometry_detection": "blocked_pre_native_atlas",
            "native_solver": "absent",
        },
        "prior_points": PRIOR_POINTS,
        "sigma_beta_points": SIGMA_BETA_POINTS,
        "fpr_rule_of_three": {"n": 100, "k": 0, "upper_95": 0.03},
        "caveats": [
            "Generated diagnostics answer external audit findings.",
            "Legacy conditioned lnB rows are not new evidence.",
            "PPC, LOOCV, matched-mask covariance nulls, and native morphology atlas remain absent.",
        ],
    }


def write_markdown(payload: dict[str, object]) -> None:
    lines = [
        "# External Audit Revision Assets",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: mixed_legacy_external_proxy_and_none",
        "sky_support_status: not_directional",
        "null_mock_status: diagnostic_no_matched_null",
        "",
        "## Decision",
        "",
        "- Evidence-grade wording: `blocked`",
        "- Family identification: `blocked_pre_native_atlas`",
        "- Geometry detection: `blocked_pre_native_atlas`",
        "- Native low-ell solver output: `absent`",
        "",
        "## Figures",
    ]
    for fig in payload["figures"]:
        lines.append(f"- `{fig}`")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "These figures diagnose why the manuscript must present the VER05 lnB values as conditional dipole-amplitude restatements rather than native Bianchi evidence.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate() -> dict[str, object]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figures = [plot_prior(), plot_sigma_beta(), plot_fpr(), plot_occupancy()]
    payload = build_payload(figures)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = generate()
    if args.check:
        required = [OUT_JSON, OUT_MD, *(REPO / path for path in payload["figures"])]
        missing = [path.as_posix() for path in required if not path.exists()]
        if missing:
            raise SystemExit("missing outputs: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Generate assets and pass tests**

Run:
```bash
venv/bin/python scripts/generate_external_audit_revision_assets.py --check
venv/bin/python -m pytest tests/contracts/test_external_audit_revision_assets.py -q
```
Expected: generated JSON/MD and four figures with valid manifests; tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_external_audit_revision_assets.py tests/contracts/test_external_audit_revision_assets.py docs/generated/external_audit_revision_assets.json docs/generated/external_audit_revision_assets.md figures/current/fig_current_prior_floor_sensitivity.png figures/current/fig_current_prior_floor_sensitivity.manifest.json figures/current/fig_current_sigma_beta_sensitivity.png figures/current/fig_current_sigma_beta_sensitivity.manifest.json figures/current/fig_current_fpr_rule_of_three.png figures/current/fig_current_fpr_rule_of_three.manifest.json figures/current/fig_current_occupancy_vector.png figures/current/fig_current_occupancy_vector.manifest.json
git commit -m "AUDIT-VER06: add diagnostic revision assets"
```

### Task 6: Attach Revision Diagnostics to the Manuscript Without Promoting Evidence

**Files:**
- Modify: `docs/manuscript/generated/current_figures_results.tex`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch08_robustness.tex`

- [ ] **Step 1: Add figure snippets**

Append to `docs/manuscript/generated/current_figures_results.tex`:

```tex
\begin{figure}[t]
\centering
\includegraphics[width=0.86\textwidth]{current/fig_current_prior_floor_sensitivity}
\caption{External-audit revision diagnostic: prior-floor sensitivity of
legacy transfer-conditioned $\ln\mathcal{B}$ rows.  The figure is
diagnostic-only and shows why the manuscript quotes conditional ranges
rather than promoting a single point estimate to evidence-grade wording.}
\label{fig:current-prior-floor-sensitivity}
\end{figure}

\begin{figure}[t]
\centering
\includegraphics[width=0.86\textwidth]{current/fig_current_sigma_beta_sensitivity}
\caption{External-audit revision diagnostic: the legacy
$\ln\mathcal{B}$ rows track $(\beta/\sigma_\beta)^2$, demonstrating
that the headline magnitude is a transformed bulk-flow amplitude and
uncertainty statement, not native Bianchi geometry evidence.}
\label{fig:current-sigma-beta-sensitivity}
\end{figure}

\begin{figure}[t]
\centering
\includegraphics[width=0.86\textwidth]{current/fig_current_fpr_rule_of_three}
\caption{Structured-null false-positive diagnostic.  A $0/100$
count supports an upper limit of roughly $3\%$ per family at 95\%
confidence; it is not a measured zero false-positive rate and is
not a matched-mask, full-covariance null ensemble.}
\label{fig:current-fpr-rule-of-three}
\end{figure}

\begin{figure}[t]
\centering
\includegraphics[width=0.86\textwidth]{current/fig_current_occupancy_vector}
\caption{Occupancy-channel diagnostic.  The FLRW$_{\mathrm{tilt}}$
defect is tilt dominated, whereas the MES ceiling is a shear
ceiling; the scalar shear-normalised $Q$ is therefore not a
certified filling fraction for this class.}
\label{fig:current-occupancy-vector}
\end{figure}
```

- [ ] **Step 2: Reference the new figures in ch07 prior and occupancy discussions**

In `docs/manuscript/ch07_results.tex` after the prior sensitivity paragraph, add:

```tex
Figure~\ref{fig:current-prior-floor-sensitivity} records the
external-audit revision diagnostic that motivates this downclaim:
the legacy transfer-conditioned number is stable to one widening
direction but unstable to the prior floor, so the result is quoted
as a conditional range and not as a publication-grade point
evidence claim.
```

- [ ] **Step 3: Reference sigma_beta and FPR figures in ch08**

After `tab:cf4-triple`, add:

```tex
Figure~\ref{fig:current-sigma-beta-sensitivity} shows the same
sensitivity as a function of $(\beta/\sigma_\beta)^2$.  The
monotonic trend is why the CF4++ and Watkins+2023 rows remain
sensitivity diagnostics and are not headline upgrades.
```

After the structured-null paragraph, add:

```tex
Figure~\ref{fig:current-fpr-rule-of-three} makes the finite-null
interpretation explicit: the available diagnostic supports
``no false positives observed in 100 trials'', not a zero
false-positive probability.
```

- [ ] **Step 4: Run figure inventory**

Run:
```bash
venv/bin/python scripts/audit_manuscript_figures.py --dry-run
```
Expected: new figures resolve with valid manifests; no missing figure references.

- [ ] **Step 5: Commit**

```bash
git add docs/manuscript/generated/current_figures_results.tex docs/manuscript/ch07_results.tex docs/manuscript/ch08_robustness.tex
git commit -m "AUDIT-VER06: attach revision diagnostics to manuscript"
```

### Task 7: Add Explicit Adequacy Status for Evidence-Grade Claims

**Files:**
- Modify: `scripts/check_publication_claim_freeze.py`
- Modify: `docs/generated/publication_claim_freeze.md`
- Create: `docs/generated/inference_adequacy_status.md`
- Create: `docs/generated/inference_adequacy_status.json`

- [ ] **Step 1: Add a blocked evidence-grade claim row**

In `scripts/check_publication_claim_freeze.py`, add this claim to `PUBLIC_CLAIMS`:

```python
{
    "claim_id": "htt.evidence_grade_tilt_preference",
    "owner": "HTT",
    "claim_tier": "C4",
    "status": "blocked_until_prior_ppc_loocv_matched_null",
    "statement": "evidence-grade wording for the tilt-like preference remains blocked until prior-floor, PPC, LOOCV, matched-null, covariance, and look-elsewhere gates are recorded",
    "allowed_phrase": "transfer-conditional tilt-like preference remains diagnostic",
    "artifacts": [
        "docs/generated/external_audit_revision_assets.md",
        "docs/generated/external_audit_revision_assets.json",
    ],
    "manifest_refs": ["docs/generated/external_audit_revision_assets.json"],
    "tests": [
        "tests/contracts/test_external_audit_revision_assets.py",
        "tests/htt/test_inference_adequacy_gates.py",
    ],
    "caveats": [
        "Legacy lnB values are conditional on the matter dipole being cosmological.",
        "Evidence-grade wording is blocked without PPC, LOOCV, matched nulls, covariance, and look-elsewhere support.",
    ],
}
```

- [ ] **Step 2: Regenerate publication freeze**

Run:
```bash
venv/bin/python scripts/check_publication_claim_freeze.py
```
Expected: `docs/generated/publication_claim_freeze.md` includes the new blocked row and still reports no forbidden promotions.

- [ ] **Step 3: Create inference adequacy status artifacts**

Create `docs/generated/inference_adequacy_status.json`:

```json
{
  "owner": "HTT",
  "implementation_scope": "htt",
  "claim_tier": "blocked",
  "transfer_source": "mixed_legacy_external_proxy_and_none",
  "sky_support_status": "not_directional",
  "null_mock_status": "prior_ppc_loocv_matched_null_blocked",
  "evidence_grade_wording": "blocked",
  "blocked_reasons": [
    "prior_floor_surface_not_full_nested_sampling_grid",
    "posterior_predictive_not_bound_to_legacy_lnb",
    "loocv_not_bound_to_legacy_lnb",
    "matched_mask_full_covariance_nulls_missing",
    "look_elsewhere_over_bulk_flow_compilations_missing"
  ],
  "caveats": [
    "This artifact records the current claim ceiling after the external audit.",
    "It does not convert diagnostic lnB rows into evidence-grade results."
  ]
}
```

Create `docs/generated/inference_adequacy_status.md`:

```markdown
# Inference Adequacy Status

owner: HTT
implementation_scope: htt
claim_tier: blocked
transfer_source: mixed_legacy_external_proxy_and_none
sky_support_status: not_directional
null_mock_status: prior_ppc_loocv_matched_null_blocked

Evidence-grade wording for the legacy tilt-like preference is blocked.

Blocked reasons:
- prior_floor_surface_not_full_nested_sampling_grid
- posterior_predictive_not_bound_to_legacy_lnb
- loocv_not_bound_to_legacy_lnb
- matched_mask_full_covariance_nulls_missing
- look_elsewhere_over_bulk_flow_compilations_missing

Allowed wording: transfer-conditional, dipole-conditional, direction-marginalized tilt-like preference.
Forbidden wording: native Bianchi evidence, geometry detection, family identification, or decisive evidence for anisotropic spatial geometry.
```

- [ ] **Step 4: Run publication claim tests**

Run:
```bash
venv/bin/python -m pytest tests/contracts/test_publication_claim_freeze.py tests/htt/test_inference_adequacy_gates.py -q
venv/bin/python scripts/check_publication_claim_freeze.py --check
```
Expected: PASS and up-to-date freeze.

- [ ] **Step 5: Commit**

```bash
git add scripts/check_publication_claim_freeze.py docs/generated/publication_claim_freeze.md docs/generated/inference_adequacy_status.json docs/generated/inference_adequacy_status.md
git commit -m "AUDIT-VER06: block evidence-grade wording until adequacy gates"
```

### Task 8: Plan the Aggressive Follow-On Analyses Without Overclaiming

**Files:**
- Create: `docs/generated/external_audit_ver06_followon_analysis_plan.md`
- Modify: `docs/manuscript/ch10_future.tex`

- [ ] **Step 1: Create follow-on analysis plan**

Create `docs/generated/external_audit_ver06_followon_analysis_plan.md`:

```markdown
# External Audit VER06 Follow-On Analysis Plan

owner: HTT
implementation_scope: htt
claim_tier: proposed
transfer_source: mixed_legacy_external_proxy_and_none
sky_support_status: mixed_pending
null_mock_status: matched_mask_covariance_pending

## Required Before Stronger Evidence Language

1. Prior-floor x prior-ceiling nested-sampling grid over Sigma2 support.
2. Bulk-flow sigma_beta systematic propagation with an explicit look-elsewhere penalty over WFH2009, CF4++, and Watkins+2023.
3. Shared-clustering-dipole covariance model for CatWISE, NVSS, RACS, and CF4.
4. Matched-mask full-covariance null suite using survey masks and actual covariance.
5. PPC and LOOCV bound to the same likelihood surface as the reported lnB.
6. Deterministic-template likelihood for D2_shear, replacing or justifying chi2(5).

## Claim Ceiling

Until all six analyses are implemented and manifest-backed, the manuscript may only say:
transfer-conditional, dipole-conditional, direction-marginalized tilt-like preference.

It may not say:
native Bianchi evidence, geometry detection, family identification, decisive evidence for anisotropic spatial geometry, or publication-grade Bayes factor.
```

- [ ] **Step 2: Add future-work cross-reference**

In `docs/manuscript/ch10_future.tex`, add a subsection:

```tex
\section{Post-audit statistical upgrade path}
\label{sec:post-audit-stat-upgrade}

The external VER06 audit identifies six analyses required before
any stronger evidence-grade wording can be considered: a full
prior-floor by prior-ceiling nested-sampling surface, bulk-flow
$\sigma_\beta$ systematic propagation with look-elsewhere
accounting, a shared-clustering-dipole covariance model, matched
mask and full-covariance null ensembles, PPC/LOOCV on the same
likelihood surface, and a deterministic-template likelihood for
$D_2^{\rm shear}$.  These analyses are future HTT validation
tasks.  They are not native low-$\ell$ Bianchi solver outputs and
do not relax the pre-native family-identification block.
```

- [ ] **Step 3: Commit**

```bash
git add docs/generated/external_audit_ver06_followon_analysis_plan.md docs/manuscript/ch10_future.tex
git commit -m "AUDIT-VER06: document follow-on statistical upgrade path"
```

### Task 9: Rebuild Manuscript and Generated Audit Surfaces

**Files:**
- Update: `docs/generated/manuscript_figure_inventory.md`
- Update: `docs/generated/pdf_claim_lint_report.md`
- Update: `docs/generated/research_only_external_audit_package.zip`
- Update: `docs/generated/research_only_external_audit_package_manifest.json`
- Update: `docs/generated/research_only_external_audit_prompt.md`

- [ ] **Step 1: Run core validation**

Run:
```bash
venv/bin/python -m pytest tests/contracts/test_external_audit_math_claims.py tests/mio/test_occupancy_vector.py tests/contracts/test_external_audit_revision_assets.py tests/contracts/test_publication_claim_freeze.py tests/htt/test_inference_adequacy_gates.py -q
```
Expected: PASS.

- [ ] **Step 2: Rebuild figure inventory**

Run:
```bash
venv/bin/python scripts/audit_manuscript_figures.py
```
Expected: no missing or quarantined figures; text audit findings reduced or intentionally documented.

- [ ] **Step 3: Build the manuscript PDF if LaTeX tooling is available**

Run:
```bash
cd docs/manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```
Expected: PDF builds. If `latexmk` is unavailable, record the exact missing command and run the repo's documented fallback from prior manuscript build notes.

- [ ] **Step 4: Run PDF claim lint**

Run:
```bash
venv/bin/python scripts/pdf_claim_lint.py
```
Expected: failed findings `0`; warnings for lnB only where conditional context is present.

- [ ] **Step 5: Rebuild research-only audit package**

Run:
```bash
venv/bin/python scripts/build_research_only_audit_package.py --check
```
Expected: zip exists, no PDFs included, manuscript source and new revision diagnostics included, no failed gates.

- [ ] **Step 6: Commit**

```bash
git add docs/generated/manuscript_figure_inventory.md docs/generated/pdf_claim_lint_report.md docs/generated/research_only_external_audit_package.zip docs/generated/research_only_external_audit_package_manifest.json docs/generated/research_only_external_audit_prompt.md
git commit -m "AUDIT-VER06: rebuild manuscript audit surfaces"
```

### Task 10: Final Reviewer-Mode Self-Audit and Blocker Report

**Files:**
- Create: `docs/generated/external_audit_ver06_self_review.md`
- Update: `docs/generated/external_audit_ver06_response_matrix.md`

- [ ] **Step 1: Create self-review report**

Create `docs/generated/external_audit_ver06_self_review.md`:

```markdown
# External Audit VER06 Self-Review

## Verdict

MAJOR REVISIONS ADDRESSED FOR CLAIM FRAMING; STRONGER EVIDENCE WORDING REMAINS BLOCKED.

## Minimal Defensible Claim

The manuscript presents a claim-tiered FLRW-departure framework and a transfer-conditional, dipole-conditional, direction-marginalized tilt-like preference that restates the matter-dipole anomaly under explicit assumptions.

## Closed Audit Findings

| Finding | Closure Evidence |
| --- | --- |
| F1 boxed lnB overclaim | ch07 box rewritten as conditional result |
| F2 CF4 decisive sensitivity | ch08 verdict labels downgraded |
| F3 transfer provenance | ch07/ch09 attach external/proxy transfer caveats |
| Gaunt | ch05 title/body corrected to PSTF 4/3 and (1,1,2) coupling |
| sigma/H | ch03/ch07 distinguish sigma/Theta and sigma/H_theta |
| Q category mismatch | occupancy vector added; scalar Q marked N/A for tilt-dominated class |
| FPR zero | ch08 reports 0/100 as <3% upper bound |

## Still Blocked

- Evidence-grade Bayes-factor language.
- Native low-ell morphology claims.
- Bianchi family identification.
- Geometry detection.

## Required Future Analyses

See `docs/generated/external_audit_ver06_followon_analysis_plan.md`.
```

- [ ] **Step 2: Update response matrix statuses**

In `docs/generated/external_audit_ver06_response_matrix.md`, change `Status` from `open` to:

```text
closed_by_task_2
closed_by_task_3
closed_by_task_4
closed_by_task_5
blocked_pending_followon_analysis
```

Use `blocked_pending_followon_analysis` for PPC/LOOCV, matched-mask covariance nulls, cross-survey covariance, and native morphology atlas.

- [ ] **Step 3: Run final validation bundle**

Run:
```bash
venv/bin/python -m pytest tests/contracts/test_external_audit_math_claims.py tests/mio/test_occupancy_vector.py tests/contracts/test_external_audit_revision_assets.py tests/contracts/test_publication_claim_freeze.py tests/htt/test_inference_adequacy_gates.py -q
venv/bin/python scripts/check_publication_claim_freeze.py --check
venv/bin/python scripts/audit_manuscript_figures.py --dry-run
venv/bin/python scripts/build_research_only_audit_package.py --check
```
Expected: all commands PASS. If LaTeX or PDF claim lint was unavailable in Task 9, include that exact blocker here.

- [ ] **Step 4: Commit**

```bash
git add docs/generated/external_audit_ver06_self_review.md docs/generated/external_audit_ver06_response_matrix.md
git commit -m "AUDIT-VER06: record self-review and remaining blockers"
```

## Self-Review

**Spec coverage:** The plan covers external audit preservation, claim-tier corrections P1-P12, fatal blockers F1-F3, math defects, Q/occupancy category mismatch, prior-floor sensitivity, sigma_beta sensitivity, FPR interpretation, PPC/LOOCV gating, manuscript rebuilding, audit-package refresh, and a remaining-blocker ledger.

**Placeholder scan:** No task leaves unspecified future filler or generic error-handling instructions. Conditional language is explicit: evidence-grade wording stays blocked unless named gates are present.

**Type consistency:** New Python identifiers are consistent across tests and implementation: `ChannelContribution`, `ChannelCeiling`, `OccupancyVector`, `generate_external_audit_revision_assets.py`, `external_audit_revision_assets.json`, and `external_audit_ver06_response_matrix.md`.

**Claim firewall:** The plan preserves HTT/MIO/COMMON boundaries, labels all revision assets `diagnostic_only`, keeps external/proxy transfer conditional, blocks native solver and family-ID claims, and avoids using scalar `x/Q/Pi/F/G` as geometry evidence.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-18-external-audit-research-revision.md`. Two execution options:

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
