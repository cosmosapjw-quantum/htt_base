# Audit VER2 Research Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the latest external research audits into a fail-closed, claim-tiered revision DAG that downclaims unsafe current results and then hardens the physical/statistical analysis before any stronger public claim is attempted.

**Architecture:** This is a supplemental `REV-R088+` research-hardening DAG, not a canonical `PR-*` completion update. The stricter `audit_ver2.md` verdict controls when it conflicts with `RESEARCH_AUDIT_REPORT.md`: positive Bayes-factor, global-tilt, scalar occupancy, and family/morphology readings are blocked until the required generative, null, covariance, prior, PPC, LOOCV, and native-atlas gates exist. The work is split into immediate manuscript/result downclaim PRs, then math/formalism repair PRs, then statistical hardening PRs, then refreshed external-audit packaging.

**Tech Stack:** Python 3, pytest, NumPy/SciPy where already used, LaTeX/latexmk, repo-local HTT/MIO/OBSSTAT/BASS contracts, generated manifests and markdown result packs.

---

## Evidence Read

- `AGENTS.md`: no native low-ell solver implementation, no pre-native family-ID, MIO/HTT separation, no figure without manifest.
- `.agents/skills/htt-revision-planner/SKILL.md`, `htt-claim-firewall`, `htt-claim-provenance-ledger`, `htt-dag-orchestrator`, `htt-reviewer-mode-pre-submission`, `htt-statistical-hardening`.
- `docs/codex_handoff/pr_backlog.yaml` and `docs/codex_handoff/pr_status.yaml`: canonical DAG is complete; use supplemental REV IDs.
- `RESEARCH_AUDIT_REPORT.md`: near-pass, asks for discovery wording removal, Pi/F harmonization, manual status count generation, matched-null forecast caveat.
- `audit_ver2.md`: reject/not-ready; controls the plan because it identifies fatal blockers around source identification, frame consistency, denominator admissibility, prior/error sensitivity, central chi-square misuse, shared survey covariance, PPC failure, and audit package source structure.
- Current source scan: strong or stale wording remains in `docs/manuscript/ch01_introduction.tex`, `ch02_dipole_anomaly.tex`, `ch07_results.tex`, `ch08_robustness.tex`, `ch09_discussion.tex`, and `ch10_future.tex`.
- Current harness scan: relevant implementation surfaces exist in `scripts/pdf_claim_lint.py`, `scripts/audit_manuscript_figures.py`, `scripts/make_current_manuscript_figures.py`, `scripts/result_packs/generate_pack_B_local_global.py`, `scripts/result_packs/generate_pack_C_mio_certificates.py`, `htt/mio/formalism/channel_occupancy_vector.py`, `htt/htt/htt/nulls/*`, `htt/htt/htt/infer/*`, `htt/src/common/bulkflow_likelihood.py`, and `htt/obsstat/catalogs/*`.
- Web CRAG: arXiv `0803.4089` supports prior sensitivity in Bayesian evidence; arXiv `1502.01593`/Planck 2015 reports no physical Bianchi VII_h evidence; arXiv `2306.11269` supports CF4 estimator/systematic uncertainty concern; arXiv `2511.00822` supports CatWISE mask/clustering/selection reassessment.

## Role Divergence And Convergence

- Code cartographer steelman: reuse existing fail-closed contracts (`channel_matched_occupancy`, CF4 schema, spectroscopic data-random contracts, local/survey nulls) before adding new abstractions. Attack: manuscript/result packs currently advertise stronger interpretations than these contracts allow.
- Harness engineer steelman: start with tests that fail on exact unsafe phrases and stale manual status counts. Attack: another disclaimer-only patch is insufficient unless lints prevent regression.
- Physics/statistics auditor steelman: the strict audit is right to block source identification and scalar occupancy. Attack: quick manuscript downclaims must not be treated as mathematical repair; frame and denominator repairs need separate PRs.
- Claim-gate reviewer steelman: downgrade first, then harden. Attack: leaving positive `lnB` headlines or `conditional` global-tilt ceiling in result packs will make the next audit fail even if prose caveats improve.
- Regression tester steelman: focused contract tests plus PDF/figure/package gates are enough per PR. Attack: broad `make_current_manuscript_figures.py --check` is currently stale and should be repaired before final packaging.

## Supplemental DAG

Topological order:

`REV-R088 -> REV-R089 -> REV-R090 -> REV-R091 -> REV-R092 -> checkpoint -> REV-R093 -> REV-R094 -> REV-R095 -> REV-R096 -> REV-R097 -> checkpoint -> REV-R098 -> REV-R099 -> REV-R100 -> REV-R101`

Checkpoint after `REV-R092` and `REV-R097` using:

```bash
venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5
```

Record the canonical DAG remains complete and the supplemental REV slice percentage separately.

---

### Task 1: REV-R088 Archive Re-Audit Inputs And Build Response Matrix

**Files:**
- Move/archive source: `audit_ver2.md`, `RESEARCH_AUDIT_REPORT.md`
- Create: `docs/audits/external_research_inputs_2026-06-20_reaudit/ARCHIVE_MANIFEST.md`
- Create: `docs/audits/external_research_inputs_2026-06-20_reaudit/input_inventory.md`
- Create: `docs/generated/audit_ver2_response_matrix.md`
- Create: `docs/generated/audit_ver2_response_matrix.json`
- Create: `docs/PR_DELTAS/rev-r088.md`
- Test: `tests/contracts/test_audit_ver2_response_matrix.py`

- [ ] **Step 1: Write the failing intake test**

```python
def test_audit_ver2_matrix_prioritizes_strict_audit():
    import json
    from pathlib import Path

    matrix = json.loads(Path("docs/generated/audit_ver2_response_matrix.json").read_text())
    assert matrix["schema_version"] == "htt.audit_ver2_response_matrix.v1"
    assert matrix["strict_audit_controls_conflicts"] is True
    assert matrix["canonical_dag_status"] == "unchanged_complete"
    blockers = {row["blocker_id"]: row for row in matrix["blockers"]}
    assert {"F1", "F2", "F3", "F4"} <= set(blockers)
    assert blockers["F1"]["required_policy"] == "positive_lnb_reclassified_as_amplitude_fit"
    assert blockers["F2"]["required_policy"] == "normal_frame_vorticity_zero_until_threading_identity"
    assert blockers["F3"]["required_policy"] == "scalar_qf_proxy_until_channel_matched_or_joint_ceiling"
    assert blockers["F4"]["required_policy"] == "no_single_jeffreys_label_without_prior_error_surface"
    assert all(row["next_rev_id"].startswith("REV-R") for row in matrix["blockers"])
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_audit_ver2_response_matrix.py -q
```

Expected: fail because the matrix files do not exist.

- [ ] **Step 3: Implement intake artifacts**

Archive both root reports into the audit folder, compute sha256 hashes, and create a response matrix with these categories:

- `fatal_blocker`: F1-F4 from `audit_ver2.md`.
- `major_required_fix`: central/noncentral likelihood split, PPC failure, shared covariance, Saadeh/vorticity portability, contamination null, CF4 error model, flat comparator wording, G_F toy status, result-pack gate split, PDF lint strength, archive source structure.
- `near_pass_quick_fix`: discovery wording, Pi namespace split, F disambiguation, manual counts, matched-null forecast wording.
- `safe_claim`: keep only the strict audit safe-claim list, not the near-pass positive evidence summary.

- [ ] **Step 4: Validate and commit**

Run:

```bash
venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_audit_ver2_response_matrix.py -q
venv/bin/python -B scripts/check_claim_language.py --dry-run docs/generated/audit_ver2_response_matrix.md docs/PR_DELTAS/rev-r088.md
git add docs/audits/external_research_inputs_2026-06-20_reaudit docs/generated/audit_ver2_response_matrix.* docs/PR_DELTAS/rev-r088.md tests/contracts/test_audit_ver2_response_matrix.py
git commit -m "REV-R088: archive strict research reaudit"
```

---

### Task 2: REV-R089 Emergency Claim Downshift In Manuscript And PDF Lint

**Files:**
- Modify: `scripts/pdf_claim_lint.py`
- Modify: `docs/manuscript/ch01_introduction.tex`
- Modify: `docs/manuscript/ch02_dipole_anomaly.tex`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch08_robustness.tex`
- Modify: `docs/manuscript/ch09_discussion.tex`
- Modify: `docs/manuscript/ch10_future.tex`
- Modify/regenerate: `docs/generated/pdf_claim_lint_report.md`
- Modify/regenerate: `docs/generated/manuscript_audit_repair_matrix.md`
- Create: `docs/PR_DELTAS/rev-r089.md`
- Test: `tests/contracts/test_audit_ver2_claim_firewall.py`

- [ ] **Step 1: Write the failing claim-firewall tests**

```python
from pathlib import Path

MANUSCRIPT = "\n".join(path.read_text(encoding="utf-8") for path in Path("docs/manuscript").glob("ch*.tex"))

def test_strict_audit_reclassified_positive_evidence_language():
    lowered = MANUSCRIPT.lower()
    forbidden_fragments = [
        "odds exceeding",
        "one-sixteenth of the mes-allowed anisotropy budget",
        "property of the data, not a model failure",
        "comparator is the most conservative",
        "conditional evidence for global tilt",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in lowered
    assert "premise-conditioned amplitude fit" in lowered
    assert "single-\\beta likelihood or covariance model fails" in lowered
    assert "fiducial comparator" in lowered

def test_pi_and_f_are_namespace_disambiguated():
    text = MANUSCRIPT
    assert "\\Pi_{\\rm HTT}" in text
    assert "\\Pi_{\\rm MIO}" in text
    assert "legacy budget-normalised score" in text
    assert "class-conditioned filling" in text

def test_neutrino_result_is_derived_not_discovered():
    lowered = MANUSCRIPT.lower()
    assert "solver discovers" not in lowered
    assert "discovery that neutrinos" not in lowered
    assert "derived result" in lowered
    assert "transfer-conditional" in lowered
```

- [ ] **Step 2: Extend PDF lint**

Add failure patterns for `odds exceeding`, `combined significance now exceeds`, `property of the data, not a model failure`, `most conservative choice`, and `one-sixteenth of the MES-allowed anisotropy budget`. Add a high-strength numeric context rule: a large `ln B` mention paired with `global tilt`, `decisive`, `evidence`, `odds`, or `support` fails unless the context explicitly says it is an admitted-amplitude or premise-conditioned fit and not a source-identification claim.

- [ ] **Step 3: Patch manuscript wording**

Use these replacements:

- `combined significance now exceeds ...` -> `several heterogeneous published amplitude anomalies are treated here as conditional inputs; their common physical origin is not established`.
- `data support a tilt-like degree of freedom` -> `configured likelihood admits a nonzero beta-like amplitude under selected priors and transfer prescription`.
- `odds exceeding ...` -> remove; replace with prior/error-sensitive likelihood-ratio wording.
- `F approx 6.3%` or `F=0.093` -> state whether it is class-conditioned filling or legacy budget-normalised score.
- PPC `property of the data` -> model inadequacy gate for the single-beta likelihood or covariance model.
- `CMB carries zero tilt information` -> configured scalar `D_2/D_3` likelihood gives no positive support for the shared beta-like parameter.
- `flat comparator is most conservative` -> flat is fiducial; comparator envelope is the result.
- `solver discovers` / `discovery that neutrinos` -> derived, transfer-conditional result.

- [ ] **Step 4: Rebuild and validate**

Run:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=docs/generated/manuscript_pdf docs/manuscript/main.tex
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py --check
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_audit_ver2_claim_firewall.py tests/contracts/test_pdf_claim_lint.py tests/contracts/test_manuscript_rearchitecture.py
```

- [ ] **Step 5: Commit**

```bash
git add scripts/pdf_claim_lint.py docs/manuscript docs/generated/pdf_claim_lint_report.md docs/generated/manuscript_audit_repair_matrix.md docs/PR_DELTAS/rev-r089.md tests/contracts/test_audit_ver2_claim_firewall.py tests/contracts/test_pdf_claim_lint.py
git commit -m "REV-R089: downshift strict audit claims"
```

---

### Task 3: REV-R090 Replace Manual Manuscript Counts With Generated Source

**Files:**
- Modify: `scripts/audit_manuscript_figures.py`
- Modify/create generator if needed: `scripts/generate_manuscript_status_snippets.py`
- Modify/regenerate: `docs/manuscript/generated/ver2_artifact_export_policy.tex`
- Modify/regenerate: `docs/manuscript/generated/ver2_figure_manifest_status.tex`
- Modify/regenerate: `docs/manuscript/generated/ver2_status_snapshot.tex`
- Modify/regenerate: `docs/manuscript/generated/ver2_titlepage_status.tex`
- Modify: `docs/manuscript/ch01_introduction.tex`
- Modify: `docs/manuscript/ch07_results.tex`
- Create: `docs/PR_DELTAS/rev-r090.md`
- Test: `tests/contracts/test_generated_status_counts.py`

- [ ] **Step 1: Write failing tests**

```python
from scripts.audit_manuscript_figures import build_manuscript_figure_audit

def test_no_manual_status_numbers_remain():
    audit = build_manuscript_figure_audit(".", manuscript_root="docs/manuscript")
    manual = [issue for issue in audit.text_issues if issue.issue_type == "manual_status_number"]
    assert manual == []

def test_status_snippets_carry_source_hashes():
    for rel in [
        "docs/manuscript/generated/ver2_figure_manifest_status.tex",
        "docs/manuscript/generated/ver2_status_snapshot.tex",
        "docs/manuscript/generated/ver2_titlepage_status.tex",
    ]:
        text = open(rel, encoding="utf-8").read()
        assert "generated from" in text.lower()
        assert "sha256:" in text
```

- [ ] **Step 2: Implement generated status snippets**

Derive counts from `docs/generated/status_snapshot.json`, `docs/generated/current_manuscript_figure_curation.json`, and figure manifest inventory rather than hardcoding prose numbers. Replace prose count sentences with `\input{generated/...}` snippets or generated macros.

- [ ] **Step 3: Validate**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/audit_manuscript_figures.py --dry-run
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_generated_status_counts.py tests/contracts/test_manuscript_figure_audit.py
```

- [ ] **Step 4: Commit**

```bash
git add scripts/audit_manuscript_figures.py scripts/generate_manuscript_status_snippets.py docs/manuscript docs/generated/manuscript_figure_inventory.md docs/PR_DELTAS/rev-r090.md tests/contracts/test_generated_status_counts.py
git commit -m "REV-R090: generate manuscript status counts"
```

---

### Task 4: REV-R091 Split Report-Generation Gates From Science Gates

**Files:**
- Modify: `scripts/result_packs/generate_pack_B_local_global.py`
- Modify: `scripts/result_packs/generate_pack_C_mio_certificates.py`
- Modify/regenerate: `docs/generated/result_pack_B.md`
- Modify/regenerate: `docs/generated/result_pack_C.md`
- Create: `docs/PR_DELTAS/rev-r091.md`
- Test: `tests/result_packs/test_pack_B.py`
- Test: `tests/result_packs/test_pack_C.py`

- [ ] **Step 1: Write failing gate tests**

```python
def test_pack_b_observed_inference_is_blocked_until_observed_payloads_exist():
    from importlib.util import spec_from_file_location, module_from_spec
    from pathlib import Path
    spec = spec_from_file_location("pack_b", "scripts/result_packs/generate_pack_B_local_global.py")
    module = module_from_spec(spec); spec.loader.exec_module(module)
    payload = module.build_result_pack_payload(repo_root=Path("."), generating_command="pytest", worktree_state="test")
    assert payload["observed_inference_status"] == "blocked_observed_inference"
    assert payload["global_tilt_claim_tier_ceiling"] == "blocked"
    assert payload["synthetic_design_ceiling"] == "conditional"

def test_pack_c_separates_report_and_science_gates():
    from importlib.util import spec_from_file_location, module_from_spec
    from pathlib import Path
    spec = spec_from_file_location("pack_c", "scripts/result_packs/generate_pack_C_mio_certificates.py")
    module = module_from_spec(spec); spec.loader.exec_module(module)
    payload = module.build_result_pack_payload(repo_root=Path("."), generating_command="pytest", worktree_state="test")
    assert payload["report_gates"]["markdown_rendered"] == "pass"
    assert payload["science_gates"]["covariance_null_complete"] in {"fail", "not_bound"}
    assert payload["science_gates"]["model_ranking_allowed"] == "forbidden"
```

- [ ] **Step 2: Implement gate split**

Pack B must state:

- `observed_inference_status: blocked_observed_inference`
- `global_tilt_claim_tier_ceiling: blocked`
- `synthetic_design_ceiling: conditional`
- local/global wording allowed only for synthetic design unless observed covariance/null/rank/PPC/LOOCV payloads are bound.

Pack C must export `report_gates` separately from `science_gates`; a clean report render does not imply clean science gates.

- [ ] **Step 3: Validate and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/result_packs/generate_pack_B_local_global.py
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/result_packs/generate_pack_C_mio_certificates.py
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/result_packs/test_pack_B.py tests/result_packs/test_pack_C.py
git add scripts/result_packs docs/generated/result_pack_B.md docs/generated/result_pack_C.md tests/result_packs docs/PR_DELTAS/rev-r091.md
git commit -m "REV-R091: split report and science gates"
```

---

### Task 5: REV-R092 Correct Figure Lanes And Repair Current-Figure Check Mode

**Files:**
- Modify: `scripts/make_current_manuscript_figures.py`
- Modify/regenerate: `docs/generated/current_science_plot_payload.json`
- Modify/regenerate: `docs/generated/current_manuscript_plot_list.md`
- Modify/regenerate: `figures/current/*.manifest.json`
- Modify/regenerate: `docs/manuscript/generated/current_figures_*.tex`
- Create: `docs/PR_DELTAS/rev-r092.md`
- Test: `tests/contracts/test_current_manuscript_figures.py`

- [ ] **Step 1: Write failing lane tests**

```python
import json
from pathlib import Path

def test_audit_ver2_figure_lane_downgrades():
    manifests = {p.name: json.loads(p.read_text()) for p in Path("figures/current").glob("*.manifest.json")}
    assert manifests["fig_revision_tomographic_forecast.manifest.json"]["allowed_use"] in {
        "paper_appendix_blocked_degeneracy",
        "methods_negative_result",
    }
    assert "near_degeneracy" in " ".join(manifests["fig_revision_tomographic_forecast.manifest.json"]["caveats"]).lower()
    assert manifests["fig_revision_prior_support_surface.manifest.json"]["artifact_mode"] == "display_only_prior_sensitivity_schematic"
    assert manifests["fig_revision_sigma_beta_band.manifest.json"]["artifact_mode"] == "display_only_error_budget_schematic"
    assert manifests["fig_revision_per_channel_occupancy.manifest.json"]["allowed_use"] != "paper_main"
    assert "physical occupancy" not in json.dumps(manifests).lower()
```

- [ ] **Step 2: Fix check-mode drift**

Run `scripts/make_current_manuscript_figures.py --check`, inspect stale outputs, regenerate with the normal mode, then make check mode pass. Do not retune figures to look better; keep negative/degenerecy results visible.

- [ ] **Step 3: Validate and checkpoint**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/make_current_manuscript_figures.py
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/make_current_manuscript_figures.py --check
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_current_manuscript_figures.py
venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5
```

- [ ] **Step 4: Commit**

```bash
git add scripts/make_current_manuscript_figures.py docs/generated/current_science_plot_payload.json docs/generated/current_manuscript_plot_list.md docs/manuscript/generated/current_figures_*.tex figures/current docs/PR_DELTAS/rev-r092.md
git commit -m "REV-R092: downgrade audited figure lanes"
```

---

### Task 6: REV-R093 Formalize Normal-Frame Versus Threading Vorticity

**Files:**
- Modify: `htt/bass/hierarchy/frame_contracts.py`
- Modify: `htt/bass/background/constraints.py`
- Modify: `docs/manuscript/ch03_framework.tex`
- Modify: `docs/manuscript/ch04_bianchi_bounds.tex`
- Create: `tests/bass/test_frame_vorticity_identity.py`
- Create: `docs/generated/frame_vorticity_repair_note.md`
- Create: `docs/PR_DELTAS/rev-r093.md`

- [ ] **Step 1: Write failing frame tests**

```python
def test_normal_frame_identity_forbids_vorticity_term():
    from bass.hierarchy.frame_contracts import FrameIdentityScope
    normal = FrameIdentityScope.normal_frame_slicing()
    assert normal.vorticity_term_allowed is False
    assert normal.geometry_ricci_substitution_allowed is True

def test_threading_identity_blocks_without_full_boost_terms():
    from bass.hierarchy.frame_contracts import FrameIdentityScope
    threading = FrameIdentityScope.threading_candidate(full_boost_terms_bound=False)
    assert threading.claim_tier == "blocked"
    assert "full_boost_terms_missing" in threading.blocked_reasons
```

- [ ] **Step 2: Implement frame contract**

Add a small immutable contract that distinguishes:

- hypersurface-normal Bianchi slicing: intrinsic group-orbit Ricci allowed, `W_std=0`, vorticity sector absent;
- matter/threading candidate: vorticity may be discussed only if full boost, flux, anisotropic stress, and constraint terms are bound; otherwise blocked.

- [ ] **Step 3: Patch manuscript**

Remove current VII_h vorticity decomposition as a current result unless the new threading contract allows it. Place any legacy vorticity rows in a blocked appendix with explicit frame caveat.

- [ ] **Step 4: Validate and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/bass/test_frame_vorticity_identity.py
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run htt/bass/hierarchy/frame_contracts.py docs/generated/frame_vorticity_repair_note.md docs/manuscript/ch03_framework.tex docs/manuscript/ch04_bianchi_bounds.tex
git add htt/bass/hierarchy/frame_contracts.py htt/bass/background/constraints.py tests/bass/test_frame_vorticity_identity.py docs/manuscript/ch03_framework.tex docs/manuscript/ch04_bianchi_bounds.tex docs/generated/frame_vorticity_repair_note.md docs/PR_DELTAS/rev-r093.md
git commit -m "REV-R093: split frame vorticity identities"
```

---

### Task 7: REV-R094 Promote Channel-Matched Occupancy And Block Scalar Q/F Occupancy

**Files:**
- Modify: `htt/mio/formalism/channel_occupancy_vector.py`
- Modify: `scripts/make_current_manuscript_figures.py`
- Modify: `docs/manuscript/ch03_framework.tex`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch09_discussion.tex`
- Modify/regenerate: `docs/generated/current_science_plot_payload.json`
- Create: `docs/generated/channel_occupancy_repair_report.md`
- Create: `docs/PR_DELTAS/rev-r094.md`
- Test: `tests/mio/test_channel_occupancy_vector.py`
- Test: `tests/contracts/test_audit_ver2_claim_firewall.py`

- [ ] **Step 1: Extend occupancy tests**

```python
def test_scalar_proxy_rows_cannot_use_occupancy_language():
    from mio.formalism.channel_occupancy_vector import classify_occupancy_language
    result = classify_occupancy_language(
        numerator_channel="tilt",
        denominator_channel="shear",
        requested_phrase="physical occupancy",
    )
    assert result["allowed"] is False
    assert result["status"] == "proxy_score_only"
    assert "channel_mismatch" in result["blocked_reasons"]
```

- [ ] **Step 2: Implement language classifier and report integration**

Keep existing `channel_matched_occupancy` strict. Add an explicit classifier for scalar proxy rows so manuscript and figure code can call it. In generated payloads, rename scalar `Q/F` displays as `proxy_score_only` unless numerator and denominator channels match or a joint admissible ceiling proof is attached.

- [ ] **Step 3: Validate and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/mio/test_channel_occupancy_vector.py tests/contracts/test_audit_ver2_claim_firewall.py
git add htt/mio/formalism/channel_occupancy_vector.py scripts/make_current_manuscript_figures.py docs/manuscript docs/generated/channel_occupancy_repair_report.md docs/generated/current_science_plot_payload.json docs/PR_DELTAS/rev-r094.md tests/mio/test_channel_occupancy_vector.py
git commit -m "REV-R094: block scalar occupancy overclaim"
```

---

### Task 8: REV-R095 Bind Amplitude-Matched Contamination Null As A Negative Result

**Files:**
- Create: `htt/htt/htt/infer/amplitude_matched_contamination.py`
- Create: `tests/htt/test_amplitude_matched_contamination.py`
- Modify: `scripts/result_packs/generate_pack_B_local_global.py`
- Modify/regenerate: `docs/generated/result_pack_B.md`
- Create: `docs/generated/amplitude_matched_contamination_report.json`
- Create: `docs/generated/amplitude_matched_contamination_report.md`
- Create: `docs/PR_DELTAS/rev-r095.md`

- [ ] **Step 1: Write failing negative-result tests**

```python
def test_high_contamination_fpr_blocks_source_identification():
    from htt.infer.amplitude_matched_contamination import contamination_fpr_report
    report = contamination_fpr_report(
        n_trials=100,
        n_false_positive=95,
        trigger="lnB_gt_5",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = report.as_payload()
    assert payload["claim_tier"] == "blocked"
    assert payload["source_identification_status"] == "failed"
    assert payload["false_positive_rate"]["raw"] == 0.95
    assert payload["false_positive_rate"]["wilson_95"][0] > 0.85
    assert payload["headline_bayes_factor_allowed"] is False
```

- [ ] **Step 2: Implement report**

Use exact binomial/Wilson intervals. This PR does not run new long mocks; it binds the externally audited 95/100 negative result as a current source-identification blocker and makes Result Pack B consume it.

- [ ] **Step 3: Validate and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_amplitude_matched_contamination.py tests/result_packs/test_pack_B.py
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/result_packs/generate_pack_B_local_global.py
git add htt/htt/htt/infer/amplitude_matched_contamination.py tests/htt/test_amplitude_matched_contamination.py scripts/result_packs/generate_pack_B_local_global.py docs/generated/amplitude_matched_contamination_report.* docs/generated/result_pack_B.md docs/PR_DELTAS/rev-r095.md
git commit -m "REV-R095: bind contamination null blocker"
```

---

### Task 9: REV-R096 Replace Proxy Prior Surfaces With Prior/Error Gate Records

**Files:**
- Create: `htt/htt/htt/infer/prior_error_sensitivity.py`
- Create: `tests/htt/test_prior_error_sensitivity.py`
- Modify: `scripts/make_current_manuscript_figures.py`
- Modify/regenerate: `figures/current/fig_revision_prior_support_surface.*`
- Modify/regenerate: `figures/current/fig_revision_sigma_beta_band.*`
- Create: `docs/generated/prior_error_sensitivity_report.json`
- Create: `docs/generated/prior_error_sensitivity_report.md`
- Create: `docs/PR_DELTAS/rev-r096.md`

- [ ] **Step 1: Write failing sensitivity tests**

```python
def test_sign_flip_blocks_single_evidence_label():
    from htt.infer.prior_error_sensitivity import summarize_prior_error_grid
    report = summarize_prior_error_grid(
        rows=[
            {"prior_floor": 1e-12, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": 26.0},
            {"prior_floor": 1e-6, "ceiling": 1.0, "sigma_beta": 2.7e-4, "lnB": -39.1},
        ],
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = report.as_payload()
    assert payload["single_jeffreys_label_allowed"] is False
    assert payload["sign_flip_detected"] is True
    assert payload["claim_tier"] == "blocked"
```

- [ ] **Step 2: Implement sensitivity summary**

Report robust range, sign flips, boundary mass placeholder status, KL placeholder status, and whether current rows are actual marginal likelihoods or display proxies. Figure manifests must say display-only if actual evidence runs are absent.

- [ ] **Step 3: Validate and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_prior_error_sensitivity.py tests/contracts/test_current_manuscript_figures.py
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/make_current_manuscript_figures.py --check
git add htt/htt/htt/infer/prior_error_sensitivity.py tests/htt/test_prior_error_sensitivity.py scripts/make_current_manuscript_figures.py docs/generated/prior_error_sensitivity_report.* figures/current docs/generated/current_science_plot_payload.json docs/PR_DELTAS/rev-r096.md
git commit -m "REV-R096: gate prior error sensitivity"
```

---

### Task 10: REV-R097 Add Joint Survey Hierarchical Likelihood Contract

**Files:**
- Create: `htt/htt/htt/infer/joint_survey_hierarchy.py`
- Create: `tests/htt/test_joint_survey_hierarchy.py`
- Modify: `htt/obsstat/catalogs/cf4.py`
- Modify: `htt/obsstat/catalogs/spectroscopic_dipole.py`
- Create: `docs/generated/joint_survey_hierarchy_design.md`
- Create: `docs/PR_DELTAS/rev-r097.md`

- [ ] **Step 1: Write failing contract tests**

```python
def test_joint_hierarchy_blocks_without_cross_probe_covariance():
    from htt.infer.joint_survey_hierarchy import build_joint_hierarchy_contract
    contract = build_joint_hierarchy_contract(
        probes=("CatWISE", "radio", "CF4"),
        covariance_status="not_bound",
        nuisance_status="survey_nuisance_not_bound",
        heldout_status="not_run",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = contract.as_payload()
    assert payload["claim_tier"] == "blocked"
    assert payload["conditional_independence_product_allowed"] is False
    assert "cross_probe_covariance_not_bound" in payload["blocked_reasons"]
```

- [ ] **Step 2: Implement schema-only hierarchy gate**

This is not a full observed-data inference PR. It defines the minimum fields required before CatWISE/radio/CF4 amplitudes can be multiplied or compared as a shared source model: cross-probe covariance, mask/selection function metadata, calibration nuisance terms, shared LSS covariance, and held-out predictive status.

- [ ] **Step 3: Validate, checkpoint, and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_joint_survey_hierarchy.py tests/htt/test_cf4_likelihood.py tests/obsstat/test_spectroscopic_dipole.py
venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5
git add htt/htt/htt/infer/joint_survey_hierarchy.py tests/htt/test_joint_survey_hierarchy.py htt/obsstat/catalogs docs/generated/joint_survey_hierarchy_design.md docs/PR_DELTAS/rev-r097.md
git commit -m "REV-R097: add joint survey hierarchy gate"
```

---

### Task 11: REV-R098 Treat PPC Failure And LOOCV Absence As Evidence Blockers

**Files:**
- Create/modify: `htt/htt/htt/infer/predictive_adequacy.py`
- Create: `tests/htt/test_predictive_adequacy.py`
- Modify: `scripts/result_packs/generate_pack_B_local_global.py`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch08_robustness.tex`
- Modify/regenerate: `docs/generated/result_pack_B.md`
- Create: `docs/generated/predictive_adequacy_report.json`
- Create: `docs/generated/predictive_adequacy_report.md`
- Create: `docs/PR_DELTAS/rev-r098.md`

- [ ] **Step 1: Write failing adequacy tests**

```python
def test_ppc_failure_blocks_channel_evidence():
    from htt.infer.predictive_adequacy import adequacy_gate
    gate = adequacy_gate(
        ppc_p_value=0.012,
        ppc_threshold=0.05,
        loocv_status="not_run",
        config_hash="sha256:" + "a" * 64,
        input_hashes=("sha256:" + "b" * 64,),
        generating_command="pytest",
        worktree_state="test",
    )
    payload = gate.as_payload()
    assert payload["adequacy_status"] == "failed"
    assert payload["evidence_claim_allowed"] is False
    assert "ppc_failure" in payload["blocked_reasons"]
    assert "loocv_not_run" in payload["blocked_reasons"]
```

- [ ] **Step 2: Implement adequacy gate**

Result Pack B and manuscript robustness sections must say channel (b) fails the registered PPC criterion unless a later model comparison fixes it. Add required next models: single beta, survey-specific amplitudes, mixture/outlier, and systematic-response.

- [ ] **Step 3: Validate and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_predictive_adequacy.py tests/result_packs/test_pack_B.py
git add htt/htt/htt/infer/predictive_adequacy.py tests/htt/test_predictive_adequacy.py scripts/result_packs/generate_pack_B_local_global.py docs/manuscript/ch07_results.tex docs/manuscript/ch08_robustness.tex docs/generated/predictive_adequacy_report.* docs/generated/result_pack_B.md docs/PR_DELTAS/rev-r098.md
git commit -m "REV-R098: block failed predictive adequacy"
```

---

### Task 12: REV-R099 Split Low-Ell Mean-Template And Covariance Likelihood Branches

**Files:**
- Create: `htt/obsstat/lowell_likelihood_branches.py`
- Create: `tests/obsstat/test_lowell_likelihood_branches.py`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch09_discussion.tex`
- Create: `docs/generated/lowell_likelihood_branch_report.md`
- Create: `docs/PR_DELTAS/rev-r099.md`

- [ ] **Step 1: Write failing branch tests**

```python
def test_central_chi_square_not_allowed_for_deterministic_template():
    from obsstat.lowell_likelihood_branches import classify_lowell_likelihood
    result = classify_lowell_likelihood(
        statistic="D2_D3_scalar",
        bianchi_role="deterministic_mean_template",
        orientation_status="not_marginalized",
        covariance_status="not_bound",
    )
    assert result["allowed"] is False
    assert "noncentral_or_harmonic_orientation_required" in result["blocked_reasons"]

def test_covariance_branch_requires_full_covariance():
    from obsstat.lowell_likelihood_branches import classify_lowell_likelihood
    result = classify_lowell_likelihood(
        statistic="BiPoSH_or_covariance",
        bianchi_role="stochastic_covariance",
        orientation_status="not_applicable",
        covariance_status="diagonal_only",
    )
    assert result["allowed"] is False
    assert "full_covariance_not_bound" in result["blocked_reasons"]
```

- [ ] **Step 2: Implement branch classifier**

Mean-template branch requires harmonic-space template and orientation marginalization or a noncentral statistic. Covariance/BiPoSH branch requires full anisotropic covariance. Central scalar chi-square is not enough for either branch.

- [ ] **Step 3: Validate and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_lowell_likelihood_branches.py
git add htt/obsstat/lowell_likelihood_branches.py tests/obsstat/test_lowell_likelihood_branches.py docs/manuscript/ch07_results.tex docs/manuscript/ch09_discussion.tex docs/generated/lowell_likelihood_branch_report.md docs/PR_DELTAS/rev-r099.md
git commit -m "REV-R099: split low-ell likelihood branches"
```

---

### Task 13: REV-R100 Reclassify G_F Evolution As Registered Model Or Blocked Toy

**Files:**
- Modify: `htt/mio/formalism/isotropy_gap.py`
- Modify: `scripts/make_current_manuscript_figures.py`
- Modify/regenerate: `docs/generated/gf_matched_null_forecast_report.json`
- Modify/regenerate: `docs/generated/gf_matched_null_forecast_report.md`
- Modify: `docs/manuscript/ch08_robustness.tex`
- Modify: `docs/manuscript/ch10_future.tex`
- Create: `tests/mio/test_gf_evolution_gate.py`
- Create: `docs/PR_DELTAS/rev-r100.md`

- [ ] **Step 1: Write failing G_F gate tests**

```python
def test_toy_gf_evolution_is_not_local_global_discriminator():
    from mio.formalism.isotropy_gap import classify_gf_evolution_model
    gate = classify_gf_evolution_model(
        model_kind="toy_beta_z_law",
        selection_covariance_status="not_bound",
        boltzmann_or_gr_status="not_bound",
    )
    assert gate["claim_tier"] == "blocked"
    assert gate["local_global_discriminator_allowed"] is False
    assert "toy_evolution_law" in gate["blocked_reasons"]
```

- [ ] **Step 2: Implement gate**

G_F curves may be shown as registered phenomenological models only if evolution equation, redshift-bin covariance, and selection transfer status are explicit. Otherwise they remain blocked toy curves.

- [ ] **Step 3: Validate and commit**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/mio/test_gf_evolution_gate.py tests/contracts/test_current_manuscript_figures.py
git add htt/mio/formalism/isotropy_gap.py scripts/make_current_manuscript_figures.py docs/generated/gf_matched_null_forecast_report.* docs/manuscript/ch08_robustness.tex docs/manuscript/ch10_future.tex tests/mio/test_gf_evolution_gate.py docs/PR_DELTAS/rev-r100.md
git commit -m "REV-R100: gate G_F evolution claims"
```

---

### Task 14: REV-R101 Rebuild Manuscript, Source-Complete Audit Package, And Freeze Next-Audit Prompt

**Files:**
- Modify: `scripts/build_research_only_audit_package.py`
- Modify: `docs/generated/research_only_external_audit_prompt.md`
- Modify/regenerate: `docs/generated/research_only_external_audit_package.zip`
- Modify/regenerate: `docs/generated/research_only_external_audit_package_manifest.json`
- Modify/regenerate: `docs/generated/manuscript_pdf/htt_base_research_report.pdf`
- Modify/regenerate: `docs/generated/manuscript_pdf/htt_base_research_report.manifest.json`
- Create: `docs/generated/audit_ver2_completion_report.md`
- Create: `docs/PR_DELTAS/rev-r101.md`
- Test: `tests/contracts/test_research_only_audit_package.py`
- Test: `tests/contracts/test_audit_ver2_claim_firewall.py`

- [ ] **Step 1: Write final package tests**

```python
def test_research_only_package_includes_line_stable_tex_and_reaudit_matrix():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("pkg", "scripts/build_research_only_audit_package.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    payload, _ = module.build_payload(
        repo_root=Path("."),
        output_zip=Path("docs/generated/research_only_external_audit_package.zip"),
        output_manifest=Path("docs/generated/research_only_external_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/research_only_external_audit_prompt.md"),
        generating_command="pytest",
        worktree_state="test",
    )
    paths = {entry["archive_path"] for entry in payload["archive_entries"]}
    assert "research_audit_source/docs/manuscript/main.tex" in paths
    assert "research_audit_source/docs/generated/audit_ver2_response_matrix.md" in paths
    assert "research_audit_source/docs/generated/audit_ver2_completion_report.md" in paths
    assert not any(path.lower().endswith(".pdf") for path in paths)
```

- [ ] **Step 2: Rebuild final artifacts**

Run:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=docs/generated/manuscript_pdf docs/manuscript/main.tex
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/audit_manuscript_figures.py
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py
```

- [ ] **Step 3: Final validation**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/pdf_claim_lint.py --check
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/audit_manuscript_figures.py --dry-run
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py --check
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q \
  tests/contracts/test_audit_ver2_response_matrix.py \
  tests/contracts/test_audit_ver2_claim_firewall.py \
  tests/contracts/test_current_manuscript_figures.py \
  tests/contracts/test_research_only_audit_package.py \
  tests/result_packs/test_pack_B.py \
  tests/result_packs/test_pack_C.py \
  tests/htt/test_amplitude_matched_contamination.py \
  tests/htt/test_prior_error_sensitivity.py \
  tests/htt/test_joint_survey_hierarchy.py \
  tests/htt/test_predictive_adequacy.py \
  tests/obsstat/test_lowell_likelihood_branches.py \
  tests/mio/test_gf_evolution_gate.py
```

- [ ] **Step 4: Commit**

```bash
git add scripts/build_research_only_audit_package.py docs/generated/research_only_external_audit_* docs/generated/manuscript_pdf docs/generated/audit_ver2_completion_report.md docs/PR_DELTAS/rev-r101.md tests/contracts/test_research_only_audit_package.py
git commit -m "REV-R101: refresh strict reaudit package"
```

---

## Kill Switches

- If a patch requires native low-ell morphology atlas outputs, stop and mark the corresponding task blocked until the external solver arrives.
- If a positive `lnB` statement is needed to preserve historical context, it must be in a legacy/conditioned appendix with explicit prior/error/null/PPC/LOOCV caveats and no source-identification wording.
- If scalar `x`, `Q`, `Pi`, `F`, or `G_F` is used as geometry or family evidence, fail the PR.
- If MIO diagnostics are consumed as HTT likelihood/evidence input, fail the PR.
- If audit-package checks would include PDFs or broad code snapshots, fail the package PR.
- If a check fails because forbidden exact strings appear in tests/prompts, rephrase or split the literal rather than weakening the scanner.

## Final Acceptance Criteria

- The strict audit blockers F1-F4 are represented in generated response/completion reports with explicit status.
- Current manuscript no longer presents positive Bayes-factor values as global-tilt evidence or source identification.
- Current manuscript treats the amplitude-matched contamination null as a blocking negative result.
- Normal-frame vorticity and threading/matter-frame vorticity are separated.
- Scalar Q/F occupancy language is replaced by channel-matched vector occupancy or proxy-score language.
- Result packs separate report-generation gates from science gates.
- Figure manifests reflect display-only, negative-result, appendix-only, or blocked lanes as appropriate.
- PDF claim lint fails high-strength numeric evidence language.
- Research-only audit package contains line-stable TeX source, generated matrices, figure payloads/manifests/source JSON, and no PDFs.
