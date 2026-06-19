# External Audit Research Program Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the latest external research audit and proposal files into a staged, claim-firewalled revision program that first repairs the current manuscript, then adds a publishable joint rest-frame/statistical-methods track and a theorem-backed x/F/G/Pi extension track without native-solver or family-identification overclaims.

**Architecture:** Treat the newly uploaded files as external design inputs, not as validated repo artifacts. Preserve them with checksums, clear the immediate manuscript audit findings, then migrate only the useful code and theorem machinery into existing COMMON/OBSSTAT/HTT/MIO/BASS ownership boundaries with manifest-backed artifacts and focused tests. Keep all observational claims gated by raw-data provenance, masks/randoms, matched nulls, covariance, PPC/held-out validation, prior sensitivity, transfer provenance, and claim-tier manifests.

**Tech Stack:** Python 3 via `venv/bin/python`, pytest, existing repo packages under `htt/src`, `htt/htt`, `htt/mio`, `htt/bass`, and `htt/obsstat`, LaTeX under `docs/manuscript`, generated reports under `docs/generated`, figures and manifests under `figures/current`, external audit archives under `docs/audits`, and CRAG-verified references from arXiv/APS/DESI/CF4 sources.

---

## Evidence Read

Repo contract and status:

- `AGENTS.md`
- `.agents/skills/*/SKILL.md` inventory
- `.codex/agents/*.toml` inventory
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/superpowers/plans/2026-06-18-external-audit-research-revision.md`
- `docs/superpowers/plans/2026-06-18-revision-program-upgrade.md`
- `docs/superpowers/plans/2026-06-19-formalism-audit-originality-program.md`

Current repo state at planning time:

- HEAD: `528b64b REV-R073: refresh research audit bundle`
- Existing canonical DAG status: 62/62 completed, no blocked PRs.
- Untracked newest external inputs:
  - `RESEARCH_AUDIT_REPORT.md`
  - `htt_publishable_novel_analysis_program_2026-06-19.zip`
  - `publishable_data_analysis_program.zip`
  - `htt_beyond_mes_egs_theorem_program_2026-06-19.zip`
  - `egs_theorem_program.zip`

External input authority:

| Input | Role | Authority | Integration rule |
| --- | --- | --- | --- |
| `RESEARCH_AUDIT_REPORT.md` | Immediate manuscript and result audit | Highest priority for current report corrections | Must clear before new claims or new figures enter the report |
| `htt_publishable_novel_analysis_program_2026-06-19.zip` | Primary publishable data-analysis program | Canonical for joint rest-frame, prior, rank, finite-mock, and data-adapter DAG | Migrate concepts/code into repo ownership boundaries; do not vendor as a parallel package |
| `htt_beyond_mes_egs_theorem_program_2026-06-19.zip` | Primary theorem-extension program | Canonical for S/G/B/E theorem tracks and kill-switches | Migrate as theorem registry, tests, synthetic theorem figures, and manuscript appendix only |
| `publishable_data_analysis_program.zip` | Compact precursor | Cross-check for theorem/data-analysis seed ideas | Do not duplicate if covered by the large package |
| `egs_theorem_program.zip` | Compact EGS precursor | Cross-check for NT seed ideas | Treat as superseded by the large theorem package |

Web CRAG snapshot:

- von Hausegger and Dalang, "Redshift tomography of the kinematic matter dipole", PRD 111, 123547, confirms redshift selection corrections can be material and even reverse the predicted dipole direction in bins. Source: https://link.aps.org/doi/10.1103/PhysRevD.111.123547
- DESI DR1 official release states DR1 includes spectra for more than 18 million unique targets from May 2021 to June 2022. Source: https://data.desi.lbl.gov/doc/releases/dr1/
- DESI DR1 QSO tomographic dipole work exists as a current arXiv analysis using DESI DR1 QSO data. Source: https://arxiv.org/html/2606.00551v1
- CF4 grouped peculiar-velocity analysis and CF4 data column documentation support the plan's requirement for grouped catalog, distance-variable likelihoods, and release/checksum provenance. Sources: https://academic.oup.com/mnras/article/527/2/3788/7419869 and https://edd.ifa.hawaii.edu/describe_columns.php?table=kcf4allvel

## Claim Firewall

Allowed current public stance:

- claim-tiered observational/statistical framework
- transfer-conditional legacy result
- diagnostic-only MIO certificate
- local/global discrimination candidate
- morphology compatibility only after the native morphology atlas exists
- external-transfer path, never native-result wording

Blocked until future native atlas and validation gates exist:

- Bianchi family identification
- geometry-detection language
- external transfer promoted as native
- MIO certificate promoted to posterior/evidence
- scalar x/Q/Pi/F/G_F promoted to family or geometry evidence
- rest-frame legacy evidence promoted to observed-frame evidence without observer-motion marginalization

## Role Divergence To Run For Each PR

Use these role notes before every implementation PR:

- Code cartographer steelman: reuse current generators, manifest validators, result packs, and artifact lanes. Attack: importing proposal packages wholesale creates duplicate SSoTs and future drift.
- Harness engineer steelman: every new report, figure, theorem bundle, or data-adapter surface needs check mode and pytest coverage. Attack: manuscript edits without generated provenance recreate the audit failure.
- Physics/statistics auditor steelman: the strongest safe path is rest-frame mismatch detection or upper limit with rank/null/held-out validation, not scalar family ranking. Attack: single-number legacy Bayes factors remain prior/support/transfer dominated.
- Claim-gate reviewer steelman: diagnostic figures can be useful if they carry forbidden-use metadata and do not become hidden evidence. Attack: "diagnostic-only" cannot mask posterior, native, or family language.
- Regression tester steelman: run small targeted tests after each PR and full report/audit package checks at checkpoint. Attack: passing external package tests does not prove repo integration.

## Workstream Summary

1. **Immediate audit repair:** fix current manuscript/report issues found by `RESEARCH_AUDIT_REPORT.md`.
2. **Formalism harmonization:** separate HTT posterior exceedance from MIO diagnostic Pi, separate scalar Q from physical filling, add G singularity and denominator kill-switches.
3. **Novel data-analysis program:** stage the joint CMB-CF4-spectroscopic rest-frame consistency track with raw-data manifests, rank audits, nulls, covariance, PPC, and held-out tests.
4. **Theorem-extension program:** integrate S/G/B/E theorem registries, proof obligations, synthetic verification bundles, and appendix material while keeping observational promotion blocked.
5. **Manuscript and audit package refresh:** regenerate plots, result packs, claim ledgers, LaTeX/PDF, and research-only external audit package after gates pass.

## New Post-DAG Revision Slice

The original DAG is complete. Use a new revision slice starting at `REV-R074` and a new research DAG proposal under `docs/codex_handoff/pr_dag_research_program.yaml`. Do not overwrite `docs/codex_handoff/pr_status.yaml` for the completed canonical DAG.

### Task 1: Archive Latest External Inputs And Generate Intake Matrix

**Files:**

- Create: `docs/audits/external_research_inputs_2026-06-20/ARCHIVE_MANIFEST.md`
- Create: `docs/audits/external_research_inputs_2026-06-20/input_inventory.json`
- Create: `docs/audits/external_research_inputs_2026-06-20/input_inventory.md`
- Create: `docs/generated/external_research_input_response_matrix.md`
- Create: `scripts/inventory_external_research_inputs.py`
- Create: `tests/contracts/test_external_research_input_inventory.py`
- Create: `docs/PR_DELTAS/rev-r074.md`

- [ ] **Step 1: Write the failing test**

Create `tests/contracts/test_external_research_input_inventory.py`:

```python
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INV = ROOT / "docs/audits/external_research_inputs_2026-06-20/input_inventory.json"
MD = ROOT / "docs/audits/external_research_inputs_2026-06-20/input_inventory.md"
MATRIX = ROOT / "docs/generated/external_research_input_response_matrix.md"


def test_research_program_inventory_check_mode_passes():
    result = subprocess.run(
        ["venv/bin/python", "scripts/inventory_external_research_inputs.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_research_program_inventory_records_all_latest_inputs():
    payload = json.loads(INV.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "htt.external_research_input_inventory.v1"
    assert payload["owner"] == "COMMON"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["canonical_sources"] == {
        "manuscript_audit": "RESEARCH_AUDIT_REPORT.md",
        "data_analysis_program": "htt_publishable_novel_analysis_program_2026-06-19.zip",
        "theorem_program": "htt_beyond_mes_egs_theorem_program_2026-06-19.zip",
    }
    for name in [
        "RESEARCH_AUDIT_REPORT.md",
        "htt_publishable_novel_analysis_program_2026-06-19.zip",
        "publishable_data_analysis_program.zip",
        "htt_beyond_mes_egs_theorem_program_2026-06-19.zip",
        "egs_theorem_program.zip",
    ]:
        assert name in payload["inputs"]
        assert payload["inputs"][name]["sha256"]
        assert payload["inputs"][name]["source_role"]
    text = MD.read_text(encoding="utf-8") + MATRIX.read_text(encoding="utf-8")
    assert "CF4++ lnB provenance" in text
    assert "Q/F/Pi harmonization" in text
    assert "joint tomographic rest-frame consistency" in text
    assert "theorem promotion DAG" in text
    assert "not native transfer" in text
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_research_program_input_inventory.py -q
```

Expected: FAIL because the script and generated files do not exist.

- [ ] **Step 3: Implement inventory script**

Create `scripts/inventory_external_research_inputs.py` with these responsibilities:

```text
Inputs:
- root files listed in Task 1 test.
Outputs:
- input_inventory.json
- input_inventory.md
- ARCHIVE_MANIFEST.md
- external_research_input_response_matrix.md
Required fields:
- owner=COMMON
- implementation_scope=common
- claim_tier=diagnostic_only
- transfer_source=none
- git_commit_or_worktree_state
- sha256 per input
- zip entry count and selected document list
- source_role and supersession note
```

The script must copy the input files into `docs/audits/external_research_inputs_2026-06-20/` only after checking the root source exists. It must not recursively delete, must reject archive-path symlinks, and must not overwrite outside its own archive directory.

- [ ] **Step 4: Generate the archive**

Run:

```bash
venv/bin/python scripts/inventory_external_research_inputs.py --write
```

Expected: generated inventory records all five inputs and the matrix maps every audit/proposal family to an actionable PR range.

- [ ] **Step 5: Validate claims**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_external_research_input_inventory.py -q
venv/bin/python scripts/check_claim_language.py docs/generated/external_research_input_response_matrix.md
```

Expected: tests pass; claim linter has no production overclaim hits.

- [ ] **Step 6: Commit**

```bash
git add scripts/inventory_external_research_inputs.py tests/contracts/test_external_research_input_inventory.py docs/audits/external_research_inputs_2026-06-20 docs/generated/external_research_input_response_matrix.md docs/PR_DELTAS/rev-r074.md
git commit -m "REV-R074: archive research program audit inputs"
```

### Task 2: Clear Immediate Manuscript Audit Findings

**Files:**

- Modify: `docs/manuscript/ch01_introduction.tex`
- Modify: `docs/manuscript/ch02_dipole_anomaly.tex`
- Modify: `docs/manuscript/ch03_framework.tex`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch08_robustness.tex`
- Modify: `docs/manuscript/ch09_discussion.tex`
- Modify: `docs/generated/pdf_claim_lint_report.md`
- Modify: `docs/generated/publication_claim_freeze.md`
- Create: `docs/generated/manuscript_audit_repair_matrix.md`
- Create: `tests/contracts/test_manuscript_audit_repair_matrix.py`
- Create: `docs/PR_DELTAS/rev-r075.md`

- [ ] **Step 1: Write the repair-matrix test**

Create `tests/contracts/test_manuscript_audit_repair_matrix.py`:

```python
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/generated/manuscript_audit_repair_matrix.md"


def test_manuscript_audit_repair_matrix_exists_and_closes_findings():
    text = MATRIX.read_text(encoding="utf-8")
    for token in [
        "neutrino quadrupole wording",
        "CF4++ lnB provenance",
        "Q/F/Pi harmonization",
        "NO_FLRW_LIMIT rows",
        "sensitivity window wording",
        "observer-frame marginalization pending",
    ]:
        assert token in text
    assert "| closed |" in text
    assert "not native transfer" in text


def test_manuscript_removes_audited_high_risk_phrases():
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in [
            "docs/manuscript/ch07_results.tex",
            "docs/manuscript/ch08_robustness.tex",
            "docs/manuscript/ch09_discussion.tex",
        ]
    )
    blocked = [
        r"the discovery that neutrinos",
        r"98\\% accuracy",
        r"CF4\\+\\+.*ln B\\s*\\approx\\s*\\+44(?!.*pending|.*untraceable|.*quarantined)",
        r"detection window",
        r"detectable against the cosmic-variance floor",
    ]
    for pattern in blocked:
        assert not re.search(pattern, combined, flags=re.IGNORECASE | re.DOTALL), pattern


def test_pdf_claim_lint_still_passes_after_repair():
    result = subprocess.run(
        ["venv/bin/python", "scripts/pdf_claim_lint.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_manuscript_audit_repair_matrix.py -q
```

Expected: FAIL until manuscript wording and matrix exist.

- [ ] **Step 3: Patch current manuscript wording**

Apply these exact research changes:

- `ch09`: replace the neutrino-quadrupole "discovery" wording with "the legacy transfer path indicates that neutrinos account for about 98 percent of the modelled D2 contribution; this is transfer-conditional and not a native-solver result."
- `ch09`: replace "98 percent accuracy" with "about 98 percent contribution fraction in the modelled transfer, with the photon correction kept explicit."
- `ch08` and `ch07`: remove or quarantine untraceable `CF4++ ln B ~= +44` as "pending dedicated rerun from canonical inputs"; do not use it as a headline.
- `ch07`: replace numeric Bayes entries for `NO_FLRW_LIMIT_EXPLICIT` rows with `N/A (no FLRW limit)`.
- `ch07`: replace "detection window" and "detectable" for growing-mode shear forecasts with "sensitivity window".
- `ch01`, `ch03`, `ch07`: reconcile the abstract/headline departure number by naming scenario, EoS, symbol, numerator, denominator, and source payload.
- `ch07` and `ch09`: state observer-frame marginalization is pending for legacy rest-frame numbers.

- [ ] **Step 4: Generate repair matrix**

Create `docs/generated/manuscript_audit_repair_matrix.md` with one row per `RESEARCH_AUDIT_REPORT.md` major/minor finding:

```markdown
# Manuscript Audit Repair Matrix

owner: COMMON
implementation_scope: manuscript
claim_tier: diagnostic_only
transfer_source: mixed_external_proxy_and_none
sky_support_status: mixed
null_mock_status: mixed_blocked_and_not_applicable
generating_command: manual matrix from RESEARCH_AUDIT_REPORT.md
caveats:
- not native transfer
- no family identification
- no geometry-detection claim

| Finding | Files | Resolution | Status |
| --- | --- | --- | --- |
| neutrino quadrupole wording | `docs/manuscript/ch09_discussion.tex` | replaced discovery/accuracy wording with transfer-conditional contribution language | closed |
| CF4++ lnB provenance | `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch08_robustness.tex` | quarantined or removed untraceable headline pending canonical rerun | closed |
| Q/F/Pi harmonization | `docs/manuscript/ch03_framework.tex`, `docs/manuscript/ch07_results.tex` | separated HTT posterior exceedance from MIO diagnostic exceedance; clarified Q/F naming | closed |
| NO_FLRW_LIMIT rows | `docs/manuscript/ch07_results.tex` | replaced forced numeric entries with N/A status | closed |
| sensitivity window wording | `docs/manuscript/ch07_results.tex` | replaced detection wording with sensitivity wording | closed |
| observer-frame marginalization pending | `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch09_discussion.tex` | marked legacy lnB as rest-frame conditional | closed |
```

- [ ] **Step 5: Rebuild and lint**

Run:

```bash
venv/bin/python scripts/pdf_claim_lint.py --check
venv/bin/python -m pytest tests/contracts/test_manuscript_audit_repair_matrix.py tests/contracts/test_publication_claim_freeze.py -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add docs/manuscript docs/generated/manuscript_audit_repair_matrix.md docs/generated/pdf_claim_lint_report.md docs/generated/publication_claim_freeze.md tests/contracts/test_manuscript_audit_repair_matrix.py docs/PR_DELTAS/rev-r075.md
git commit -m "REV-R075: repair manuscript audit findings"
```

### Task 3: Formalize Q/F/Pi/G Semantic Split

**Files:**

- Modify: `htt/mio/formalism/exceedance.py`
- Modify: `htt/mio/formalism/filling_fraction.py`
- Modify: `htt/mio/formalism/normalized_score.py`
- Modify: `scripts/verify_formalism_figure_labels.py`
- Modify: `scripts/make_current_manuscript_figures.py`
- Modify: `docs/manuscript/ch03_framework.tex`
- Create: `htt/htt/htt/infer/posterior_exceedance.py`
- Create: `tests/htt/test_posterior_exceedance.py`
- Modify: `tests/mio/test_exceedance.py`
- Modify: `tests/mio/test_filling_fraction.py`
- Create: `docs/generated/qfpi_semantic_reconciliation.md`
- Create: `docs/PR_DELTAS/rev-r076.md`

- [ ] **Step 1: Write HTT posterior-exceedance tests**

Create `tests/htt/test_posterior_exceedance.py`:

```python
from htt.infer.posterior_exceedance import posterior_exceedance_summary


def test_htt_posterior_exceedance_is_model_conditional_not_mio_pi():
    summary = posterior_exceedance_summary(
        samples=[0.01, 0.05, 0.20, 0.30],
        threshold=0.10,
        model_label="legacy_transfer_conditioned_tilt",
        source_quantity="F_Bayes",
    )
    assert summary["owner"] == "HTT"
    assert summary["quantity_name"] == "P_post"
    assert summary["threshold"] == 0.10
    assert summary["exceedance_probability"] == 0.5
    assert summary["mio_pi_compatible"] is False
    assert "model-conditional posterior exceedance" in summary["definition"]
```

- [ ] **Step 2: Add MIO semantic guards**

Extend MIO tests so diagnostic Pi remains an empirical or registered exceedance curve and cannot use posterior phrasing:

```python
def test_mio_pi_rejects_posterior_language():
    with pytest.raises(ValueError, match="posterior"):
        build_exceedance_curve(
            values=[0.1, 0.2],
            thresholds=[0.15],
            definition="posterior probability P(Q>q|D)",
        )
```

- [ ] **Step 3: Implement `posterior_exceedance_summary`**

Create `htt/htt/htt/infer/posterior_exceedance.py` returning a JSON-serializable dict with:

```text
owner: HTT
quantity_name: P_post
definition: model-conditional posterior exceedance
mio_pi_compatible: false
samples_count
threshold
exceedance_probability
model_label
source_quantity
caveats:
- not a MIO diagnostic Pi
- not a truth probability
- not family or geometry evidence
```

- [ ] **Step 4: Update manuscript and figure-label linter**

Rules:

- MIO `Pi`: empirical/registered exceedance curve, no posterior notation.
- HTT posterior exceedance: use `P_post` or `Pi_HTT` only with explicit distinction; prefer `P_post` in prose.
- MIO `Q`: policy-normalized diagnostic score, not occupancy.
- Certified `F`: allowed only with same-channel numerator and ceiling.
- `G_F`: undefined when both fillings are zero; never auto-fill with one.

- [ ] **Step 5: Validate**

Run:

```bash
venv/bin/python -m pytest tests/htt/test_posterior_exceedance.py tests/mio/test_exceedance.py tests/mio/test_filling_fraction.py tests/contracts/test_formalism_figure_labels.py -q
venv/bin/python scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json
```

Expected: pass, with no Q/F/Pi owner swaps.

- [ ] **Step 6: Commit**

```bash
git add htt/htt/htt/infer/posterior_exceedance.py htt/mio/formalism scripts/verify_formalism_figure_labels.py scripts/make_current_manuscript_figures.py docs/manuscript/ch03_framework.tex docs/generated/qfpi_semantic_reconciliation.md tests/htt/test_posterior_exceedance.py tests/mio docs/PR_DELTAS/rev-r076.md
git commit -m "REV-R076: separate HTT posterior exceedance from MIO diagnostics"
```

### Task 4: Reproduce Or Quarantine CF4++ Headline

**Files:**

- Create: `docs/generated/cf4pp_lnb_provenance_report.md`
- Create: `docs/generated/cf4pp_lnb_provenance_report.json`
- Create: `scripts/reproduce_cf4pp_lnb.py`
- Create: `tests/contracts/test_cf4pp_lnb_provenance.py`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch08_robustness.tex`
- Create: `docs/PR_DELTAS/rev-r077.md`

- [ ] **Step 1: Write provenance test**

Create `tests/contracts/test_cf4pp_lnb_provenance.py`:

```python
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/generated/cf4pp_lnb_provenance_report.json"


def test_cf4pp_lnb_report_check_mode_passes():
    result = subprocess.run(
        ["venv/bin/python", "scripts/reproduce_cf4pp_lnb.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cf4pp_lnb_is_either_reproduced_or_quarantined():
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    assert payload["owner"] == "HTT"
    assert payload["claim_tier"] in {"blocked", "diagnostic_only", "transfer_conditional"}
    assert payload["status"] in {"reproduced_with_bound_inputs", "quarantined_untraceable"}
    if payload["status"] == "reproduced_with_bound_inputs":
        assert payload["config_hash"]
        assert payload["input_hashes"]
        assert payload["lnB_cf4pp"] is not None
    else:
        assert payload["lnB_cf4pp"] is None
        assert "not used in manuscript headline" in payload["caveats"]
```

- [ ] **Step 2: Implement conservative script**

`scripts/reproduce_cf4pp_lnb.py` should first search canonical JSON sources already in repo. If canonical source payloads cannot bind the number, emit:

```json
{
  "owner": "HTT",
  "claim_tier": "blocked",
  "status": "quarantined_untraceable",
  "lnB_cf4pp": null,
  "config_hash": null,
  "input_hashes": [],
  "caveats": ["not used in manuscript headline", "dedicated rerun required"]
}
```

No synthetic rerun is allowed.

- [ ] **Step 3: Patch manuscript based on status**

If reproduced, state exact config/input hashes and keep transfer-conditional status. If quarantined, remove `+44` from headline prose and leave a short provenance note.

- [ ] **Step 4: Validate and commit**

Run:

```bash
venv/bin/python scripts/reproduce_cf4pp_lnb.py --write
venv/bin/python -m pytest tests/contracts/test_cf4pp_lnb_provenance.py -q
venv/bin/python scripts/pdf_claim_lint.py --check
```

Commit:

```bash
git add scripts/reproduce_cf4pp_lnb.py tests/contracts/test_cf4pp_lnb_provenance.py docs/generated/cf4pp_lnb_provenance_report.* docs/manuscript docs/PR_DELTAS/rev-r077.md
git commit -m "REV-R077: bind or quarantine CF4++ legacy evidence"
```

### Task 5: Import Research Program DAG As Proposal, Not Canonical Completion

**Files:**

- Create: `docs/codex_handoff/pr_dag_research_program.yaml`
- Create: `docs/generated/research_program_experiment_registry.yaml`
- Create: `docs/generated/research_program_theorem_registry.yaml`
- Create: `tests/contracts/test_research_program_dag.py`
- Create: `docs/PR_DELTAS/rev-r078.md`

- [ ] **Step 1: Write DAG test**

Create `tests/contracts/test_research_program_dag.py`:

```python
import yaml
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT / "docs/codex_handoff/pr_dag_research_program.yaml"


def test_research_program_dag_has_expected_order_and_blocks_native_family_id():
    payload = yaml.safe_load(DAG.read_text(encoding="utf-8"))
    ids = [row["id"] for row in payload["prs"]]
    for required in [
        "PR-N00",
        "PR-N01",
        "PR-N02",
        "PR-N03",
        "PR-N04",
        "PR-N10",
        "PR-N12",
        "PR-N20",
        "PR-N21",
        "PR-N22",
        "PR-N40",
        "PR-N41",
        "PR-N50",
        "PR-N51",
    ]:
        assert required in ids
    assert payload["policy"]["native_lowell_solver_implementation_allowed"] is False
    assert payload["policy"]["family_identification_claims_blocked_pre_native_atlas"] is True
    blocked = next(row for row in payload["prs"] if row["id"] == "PR-N51")
    assert blocked["status"] == "blocked_until_native_solver"
```

- [ ] **Step 2: Create proposed research DAG**

Use the large package's PR-N list as the source, but adapt ownership:

```yaml
schema_version: htt.research_program_pr_dag.v1
policy:
  native_lowell_solver_implementation_allowed: false
  family_identification_claims_blocked_pre_native_atlas: true
  external_transfer_native_promotion_allowed: false
  mio_htt_evidence_merge_allowed: false
prs:
  - id: PR-N00
    title: Freeze research data, claim, and transfer contracts
    owner: COMMON
    depends: []
    status: proposed
  - id: PR-N01
    title: Install experiment harness and manifest lanes
    owner: COMMON
    depends: [PR-N00]
    status: proposed
  - id: PR-N02
    title: Exact prior and finite-mock calibration
    owner: HTT
    depends: [PR-N01]
    status: proposed
  - id: PR-N03
    title: Nuisance-projected rank and Fisher audits
    owner: HTT
    depends: [PR-N01]
    status: proposed
  - id: PR-N04
    title: Channel-matched occupancy and transfer stability
    owner: MIO
    depends: [PR-N00]
    status: proposed
  - id: PR-N10
    title: CF4 raw group adapter and forward distance likelihood
    owner: OBSSTAT_HTT
    depends: [PR-N01, PR-N03]
    status: proposed
  - id: PR-N12
    title: DESI/BOSS/eBOSS data-random dipole estimator
    owner: OBSSTAT
    depends: [PR-N01, PR-N03]
    status: proposed
  - id: PR-N20
    title: Joint local/global hierarchical model
    owner: HTT
    depends: [PR-N10, PR-N12, PR-N02]
    status: proposed
  - id: PR-N21
    title: Matched nulls, PPC, and held-out validation
    owner: HTT
    depends: [PR-N20]
    status: proposed
  - id: PR-N22
    title: Prior-safe evidence and cross-validation synthesis
    owner: HTT
    depends: [PR-N21]
    status: proposed
  - id: PR-N30
    title: Planck boost/off-diagonal adapter
    owner: OBSSTAT
    depends: [PR-N03]
    status: proposed
  - id: PR-N32
    title: Generic BiPoSH residual and full-covariance MES report
    owner: OBSSTAT_HTT
    depends: [PR-N30, PR-N04]
    status: proposed
  - id: PR-N40
    title: Flagship result pack and theorem-linked manuscript figures
    owner: COMMON
    depends: [PR-N22, PR-N32]
    status: proposed
  - id: PR-N41
    title: External adversarial audit and claim freeze
    owner: COMMON
    depends: [PR-N40]
    status: proposed
  - id: PR-N50
    title: Future native low-ell atlas adapter schema
    owner: BASS
    depends: [PR-N04]
    status: schema_only
  - id: PR-N51
    title: Family equivalence-class gate
    owner: BASS_COMMON
    depends: [PR-N50, PR-N32]
    status: blocked_until_native_solver
```

- [ ] **Step 3: Validate and commit**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_research_program_dag.py -q
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
```

Commit:

```bash
git add docs/codex_handoff/pr_dag_research_program.yaml docs/generated/research_program_experiment_registry.yaml docs/generated/research_program_theorem_registry.yaml tests/contracts/test_research_program_dag.py docs/PR_DELTAS/rev-r078.md
git commit -m "REV-R078: stage research program DAG"
```

### Task 6: Migrate Fast Method Experiments Into Repo Generators

**Files:**

- Modify: `scripts/generate_revision_experiment_assets.py`
- Modify: `tests/contracts/test_revision_experiment_assets.py`
- Create: `htt/htt/htt/infer/finite_mock.py`
- Create: `htt/htt/htt/infer/nuisance_rank.py`
- Create: `htt/htt/htt/infer/fisher_compression.py`
- Create: `htt/mio/formalism/channel_occupancy_vector.py`
- Create: `htt/bass/transfer/evidence_stability.py`
- Create: focused tests:
  - `tests/htt/test_finite_mock.py`
  - `tests/htt/test_nuisance_rank.py`
  - `tests/htt/test_fisher_compression.py`
  - `tests/mio/test_channel_occupancy_vector.py`
  - `tests/bass/test_evidence_stability.py`
- Create: `docs/PR_DELTAS/rev-r079.md`

- [ ] **Step 1: Implement exact finite-mock upper bound**

Function contract:

```python
def zero_trigger_upper_bound(null_count: int, confidence: float = 0.95) -> float:
    """Return one-sided upper FPR bound for zero triggers in N null mocks."""
```

Test:

```python
def test_zero_trigger_bound_for_100_is_not_zero():
    assert zero_trigger_upper_bound(100, 0.95) == pytest.approx(1 - 0.05 ** (1 / 100))
```

- [ ] **Step 2: Implement nuisance-projected rank audit**

Function contract:

```python
def nuisance_projected_rank(target_response, nuisance_response, covariance, tolerance=1e-10):
    """Return rank, singular values, and full-rank status after C^{-1/2} whitening and nuisance projection."""
```

Test proportional local/global responses return rank deficient.

- [ ] **Step 3: Implement Fisher compression audit**

Function contract:

```python
def gaussian_covariance_fisher_full_and_diag(derivatives):
    """Return full and diagonal Fisher matrices for covariance derivative basis at C=I."""
```

Test a purely off-diagonal derivative has positive full information and zero diagonal information.

- [ ] **Step 4: Implement channel occupancy vector**

Function contract:

```python
def channel_matched_occupancy(rows):
    """Return F_i=X_i/U_i rows; reject cross-channel denominator use."""
```

Test cross-channel denominator raises a value error and same-channel rows are in `[0,1]`.

- [ ] **Step 5: Implement evidence stability bound**

Function contract:

```python
def evidence_shift_bound(max_loglike_delta: float) -> dict[str, float]:
    """Return |Delta log Z| <= epsilon certificate."""
```

Test returned upper bound equals epsilon and records transfer-conditional caveats.

- [ ] **Step 6: Regenerate assets and validate**

Run:

```bash
venv/bin/python scripts/generate_revision_experiment_assets.py --write
venv/bin/python -m pytest tests/htt/test_finite_mock.py tests/htt/test_nuisance_rank.py tests/htt/test_fisher_compression.py tests/mio/test_channel_occupancy_vector.py tests/bass/test_evidence_stability.py tests/contracts/test_revision_experiment_assets.py -q
```

- [ ] **Step 7: Commit**

```bash
git add htt/htt/htt/infer htt/mio/formalism htt/bass/transfer scripts/generate_revision_experiment_assets.py tests docs/generated/revision_experiment_assets.* figures/current docs/PR_DELTAS/rev-r079.md
git commit -m "REV-R079: add research method diagnostics"
```

### Task 7: Build Data-Binding Contracts Before Raw Catalog Analysis

**Files:**

- Create: `htt/src/common/data_contracts.py`
- Create: `tests/contracts/test_data_contracts.py`
- Modify: `scripts/inventory_observational_data.py`
- Modify: `docs/generated/observational_data_inventory.json`
- Modify: `docs/generated/observational_data_inventory.md`
- Create: `docs/generated/data_binding_gap_report.md`
- Create: `docs/PR_DELTAS/rev-r080.md`

- [ ] **Step 1: Add data role contracts**

Required dataclasses/enums:

```text
DataRole:
- raw_catalog
- random_catalog
- mask
- mock_catalog
- covariance
- map
- harmonic_product

SurveySupport:
- survey_name
- release
- tracer
- sky_region
- redshift_range
- data_path
- checksum
- random_or_mask_path
- selection_weight_status
- covariance_status
- null_mock_status
- allowed_use
```

- [ ] **Step 2: Enforce raw-data readiness levels**

Levels:

- D0: derived audit payload only, code-path validation and pilot plots.
- D1: raw public catalog plus metadata.
- D2: matched mocks with same support.
- D3: end-to-end simulation.

Test each level validates required fields and rejects missing random catalogs for spectroscopic dipole production.

- [ ] **Step 3: Inventory current repo data**

Run:

```bash
venv/bin/python scripts/inventory_observational_data.py --write
venv/bin/python -m pytest tests/contracts/test_data_contracts.py tests/contracts/test_observed_data_figures.py -q
```

Expected: current observed figures remain diagnostic-only if only D0/D1 surfaces are bound.

- [ ] **Step 4: Commit**

```bash
git add htt/src/common/data_contracts.py scripts/inventory_observational_data.py tests/contracts/test_data_contracts.py docs/generated/observational_data_inventory.* docs/generated/data_binding_gap_report.md docs/PR_DELTAS/rev-r080.md
git commit -m "REV-R080: add observational data binding contracts"
```

### Task 8: CF4 Forward-Likelihood Adapter Track

**Files:**

- Create: `htt/obsstat/catalogs/cf4.py`
- Create: `htt/htt/htt/rest_frame/cf4_likelihood.py`
- Create: `tests/obsstat/test_cf4_catalog_adapter.py`
- Create: `tests/htt/test_cf4_likelihood.py`
- Create: `docs/generated/cf4_forward_likelihood_design.md`
- Create: `docs/PR_DELTAS/rev-r081.md`

- [ ] **Step 1: Implement schema-only adapter first**

CF4 adapter must require:

- object or group identifier
- sky coordinates
- redshift frame
- distance indicator or logdistance variable
- distance uncertainty
- group membership or grouping flag
- method/calibration flag
- release/checksum metadata

It must not treat transformed peculiar velocity as exactly Gaussian unless a manifest explicitly says so.

- [ ] **Step 2: Implement forward likelihood skeleton**

Likelihood input is a distance-like variable:

```text
observed_distance_variable = model_distance_variable(z, local_flow_basis, global_vector, calibration_nuisance) + noise
```

The first PR may support deterministic toy fixtures for tests only, with `claim_tier=diagnostic_only` and no publication result.

- [ ] **Step 3: Validate**

Run:

```bash
venv/bin/python -m pytest tests/obsstat/test_cf4_catalog_adapter.py tests/htt/test_cf4_likelihood.py -q
```

- [ ] **Step 4: Commit**

```bash
git add htt/obsstat/catalogs/cf4.py htt/htt/htt/rest_frame/cf4_likelihood.py tests/obsstat/test_cf4_catalog_adapter.py tests/htt/test_cf4_likelihood.py docs/generated/cf4_forward_likelihood_design.md docs/PR_DELTAS/rev-r081.md
git commit -m "REV-R081: add CF4 forward-likelihood adapter"
```

### Task 9: Spectroscopic Data-Random Dipole Estimator Track

**Files:**

- Create: `htt/obsstat/catalogs/spectroscopic_dipole.py`
- Create: `htt/obsstat/catalogs/redshift_selection.py`
- Create: `tests/obsstat/test_spectroscopic_dipole.py`
- Create: `tests/obsstat/test_redshift_selection.py`
- Create: `docs/generated/spectroscopic_dipole_design.md`
- Create: `docs/PR_DELTAS/rev-r082.md`

- [ ] **Step 1: Implement data-random estimator**

Estimator contract:

```text
dipole = first_moment(data, weights) - alpha * first_moment(randoms, weights)
```

Required checks:

- data and random catalogs share release/tracer/region/bin.
- random catalog exists for production use.
- redshift selection correction status is recorded.
- output is OBSSTAT feature only.

- [ ] **Step 2: Add redshift-selection correction metadata**

Record the von Hausegger-Dalang redshift-selection correction as a required model component for observed-redshift selected bins. This PR can store metadata and toy correction hooks; it must not claim a new observed result.

- [ ] **Step 3: Validate**

Run:

```bash
venv/bin/python -m pytest tests/obsstat/test_spectroscopic_dipole.py tests/obsstat/test_redshift_selection.py -q
```

- [ ] **Step 4: Commit**

```bash
git add htt/obsstat/catalogs/spectroscopic_dipole.py htt/obsstat/catalogs/redshift_selection.py tests/obsstat/test_spectroscopic_dipole.py tests/obsstat/test_redshift_selection.py docs/generated/spectroscopic_dipole_design.md docs/PR_DELTAS/rev-r082.md
git commit -m "REV-R082: add spectroscopic dipole estimator contracts"
```

### Task 10: Joint Rest-Frame Identifiability And Validation Harness

**Files:**

- Create: `htt/htt/htt/rest_frame/joint_model.py`
- Create: `htt/htt/htt/rest_frame/validation.py`
- Create: `htt/htt/htt/rest_frame/cross_survey_covariance.py`
- Create: `tests/htt/test_joint_rest_frame_model.py`
- Create: `tests/htt/test_rest_frame_validation.py`
- Create: `docs/generated/joint_rest_frame_model_design.md`
- Create: `docs/PR_DELTAS/rev-r083.md`

- [ ] **Step 1: Implement response-block object**

Model blocks:

- observer-CMB boost response
- local-flow basis response
- global rest-frame offset response
- survey/systematic nuisance response
- covariance blocks

- [ ] **Step 2: Implement pre-inference rank gate**

Compute:

```text
R_g_perp = P_nuis_perp C^{-1/2} R_g
```

Output:

- singular values
- projected rank
- channel ablation stability
- survey-axis overlap metadata
- claim status: full-rank candidate or rank-deficient no-claim

- [ ] **Step 3: Implement validation summaries**

Validation objects:

- prior support sensitivity surface
- matched null result
- PPC status
- leave-one-probe/bin-out status
- covariance sensitivity status

No evidence-grade output is allowed unless these statuses are all passed.

- [ ] **Step 4: Validate**

Run:

```bash
venv/bin/python -m pytest tests/htt/test_joint_rest_frame_model.py tests/htt/test_rest_frame_validation.py tests/htt/test_nuisance_rank.py -q
```

- [ ] **Step 5: Commit**

```bash
git add htt/htt/htt/rest_frame tests/htt/test_joint_rest_frame_model.py tests/htt/test_rest_frame_validation.py docs/generated/joint_rest_frame_model_design.md docs/PR_DELTAS/rev-r083.md
git commit -m "REV-R083: add joint rest-frame identifiability harness"
```

### Task 11: Integrate Theorem Extension Registry And Synthetic Verification

**Files:**

- Create: `htt/src/common/theorem_registry.py`
- Create: `htt/mio/formalism/dynamic_budget.py`
- Create: `htt/mio/formalism/bound_pushforward.py`
- Create: `htt/bass/kinetic/boltzmann_memory.py`
- Create: `htt/bass/kinetic/tight_coupling_bounds.py`
- Create: `htt/bass/kinetic/visibility_rigidity.py`
- Create: `htt/bass/geometry/egs_rigidity.py`
- Create: `scripts/generate_theorem_extension_assets.py`
- Create: `tests/contracts/test_theorem_registry.py`
- Create: `tests/mio/test_dynamic_budget.py`
- Create: `tests/bass/test_boltzmann_memory_bounds.py`
- Create: `tests/bass/test_egs_rigidity_theorems.py`
- Create: `docs/generated/theorem_extension_registry.json`
- Create: `docs/generated/theorem_extension_registry.md`
- Create: `docs/PR_DELTAS/rev-r084.md`

- [ ] **Step 1: Add theorem registry**

Registry entries must include:

- theorem id
- status: analytic, convention-conditional, program-theorem, observational-blocked
- assumptions
- kill-switches
- allowed use
- forbidden use
- test file
- generated artifact ids

- [ ] **Step 2: Implement P0 theorem primitives**

First migration set:

- S1 angular KL multipole bound
- S3 dynamic comparison budget barrier
- S4 bound-to-Pi domination
- S5 finite-cover bound
- G2 boosted-radiation orbit
- G5 slope degeneracy classification
- B4 visibility cancellation no-go

Use synthetic/manufactured tests only. Do not create observational theorem claims.

- [ ] **Step 3: Encode kill-switches**

Required fail-closed statuses:

- unbounded multipole bridge blocks S2 observational use
- acceleration/temp-gradient block missing blocks FLRW/EGS promotion
- `w` near stiff-fluid singularity blocks G3 inversion
- Bianchi-I assumptions missing blocks G4 exact-flow use
- slope degeneracy blocks slope-only source discrimination
- collision gap nonpositive blocks exponential-forgetting language
- source rank near zero blocks inverse source claim
- line-of-sight sign/phase incoherence blocks source upper bound
- derivative/Weyl diagnostics missing blocks almost-EGS promotion

- [ ] **Step 4: Validate and commit**

Run:

```bash
venv/bin/python scripts/generate_theorem_extension_assets.py --write
venv/bin/python -m pytest tests/contracts/test_theorem_registry.py tests/mio/test_dynamic_budget.py tests/bass/test_boltzmann_memory_bounds.py tests/bass/test_egs_rigidity_theorems.py -q
```

Commit:

```bash
git add htt/src/common/theorem_registry.py htt/mio/formalism htt/bass/kinetic htt/bass/geometry scripts/generate_theorem_extension_assets.py tests docs/generated/theorem_extension_registry.* docs/PR_DELTAS/rev-r084.md
git commit -m "REV-R084: add theorem extension registry"
```

### Task 12: Generate Theorem Figures As Appendix-Only Artifacts

**Files:**

- Modify: `scripts/generate_theorem_extension_assets.py`
- Create: `docs/manuscript/generated/theorem_extension_appendix_figures.tex`
- Create: figures/manifests under `figures/current/`:
  - `fig_theorem_angular_kl_bound.png`
  - `fig_theorem_dynamic_budget_barrier.png`
  - `fig_theorem_boosted_radiation_orbit.png`
  - `fig_theorem_slope_degeneracy.png`
  - `fig_theorem_visibility_cancellation.png`
- Create: `tests/contracts/test_theorem_extension_assets.py`
- Create: `docs/PR_DELTAS/rev-r085.md`

- [ ] **Step 1: Write asset test**

Assert each theorem figure has:

- owner
- theorem id
- claim tier
- artifact mode `paper_appendix_conditioned`
- allowed use `paper_appendix`
- transfer source `none`
- synthetic/manufactured input mode
- forbidden-use sentence
- source JSON and manifest

- [ ] **Step 2: Generate figures**

Run:

```bash
venv/bin/python scripts/generate_theorem_extension_assets.py --write
venv/bin/python -m pytest tests/contracts/test_theorem_extension_assets.py -q
```

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_theorem_extension_assets.py tests/contracts/test_theorem_extension_assets.py figures/current/fig_theorem_* docs/manuscript/generated/theorem_extension_appendix_figures.tex docs/PR_DELTAS/rev-r085.md
git commit -m "REV-R085: generate theorem appendix artifacts"
```

### Task 13: Rewrite Manuscript Architecture Around Safe Strong Results

**Files:**

- Modify: `docs/manuscript/ch01_introduction.tex`
- Modify: `docs/manuscript/ch03_framework.tex`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch08_robustness.tex`
- Modify: `docs/manuscript/ch09_discussion.tex`
- Modify: `docs/manuscript/ch10_future.tex`
- Modify: `docs/manuscript/appendices.tex`
- Modify: `docs/manuscript/main.tex`
- Modify: `docs/manuscript/references.bib`
- Create: `docs/generated/manuscript_rearchitecture_report.md`
- Create: `docs/PR_DELTAS/rev-r086.md`

- [ ] **Step 1: New narrative order**

Use this order:

1. Formal no-go and identifiability: scalar evidence is not a family/geometry test.
2. Current legacy result: transfer-conditional rest-frame tilt-like diagnostic, not headline discovery.
3. New method result: rank/null/prior theorem-backed local/global rest-frame program.
4. Current diagnostic figures: only where manifests allow.
5. Theorem appendix: x/F/G/Pi, EGS/Boltzmann extension, and kill-switches.
6. Future native solver bridge: atlas adapter and family-equivalence gates only.

- [ ] **Step 2: Reposition legacy Bayes factors**

Move legacy lnB discussion into sensitivity/provenance sections. Lead public conclusions with:

- method-level identifiability theorem
- finite-mock calibration rule
- channel-matched occupancy requirement
- data-binding gap report
- rest-frame analysis plan and rank gate

- [ ] **Step 3: Add bibliography entries from CRAG**

Add or verify references for:

- von Hausegger and Dalang 2025 PRD redshift tomography
- DESI DR1 release
- DESI DR1 QSO tomographic dipole preprint if cited as current exploratory literature
- CF4 grouped peculiar-velocity release or reconstruction
- EGS/almost-EGS and Nilsson/Uggla/Wainwright/Lim no-go context

- [ ] **Step 4: Validate**

Run:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=docs/generated/manuscript_pdf docs/manuscript/main.tex
venv/bin/python scripts/pdf_claim_lint.py --check
venv/bin/python scripts/audit_manuscript_figures.py --check
```

- [ ] **Step 5: Commit**

```bash
git add docs/manuscript docs/generated/manuscript_rearchitecture_report.md docs/generated/manuscript_pdf docs/PR_DELTAS/rev-r086.md
git commit -m "REV-R086: reframe manuscript around gated research results"
```

### Task 14: Refresh Research-Only External Audit Package

**Files:**

- Modify: `scripts/build_research_only_audit_package.py`
- Modify: `tests/contracts/test_research_only_audit_package.py`
- Regenerate:
  - `docs/generated/research_only_external_audit_package.zip`
  - `docs/generated/research_only_external_audit_package_manifest.json`
  - `docs/generated/research_only_external_audit_prompt.md`
- Create: `docs/PR_DELTAS/rev-r087.md`

- [ ] **Step 1: Include new required research sources**

The package must include:

- LaTeX sources, not PDF as primary audit input.
- current manuscript generated snippets.
- current figures included by manuscript plus manifests/source JSON.
- `manuscript_audit_repair_matrix.md`
- `qfpi_semantic_reconciliation.md`
- `cf4pp_lnb_provenance_report.*`
- research program DAG/registries.
- theorem extension registry and theorem appendix artifacts.
- minimal code samples needed to understand included plots.

The package must exclude:

- external zip payloads as bulk copies.
- native solver fake outputs.
- unmanifested figure directories.
- unrelated historical PDFs.

- [ ] **Step 2: Validate**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/build_research_only_audit_package.py --check
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_research_only_audit_package.py -q
```

- [ ] **Step 3: Inspect zip entries**

Run:

```bash
python - <<'PY'
from zipfile import ZipFile
from pathlib import Path
zip_path = Path("docs/generated/research_only_external_audit_package.zip")
with ZipFile(zip_path) as zf:
    names = zf.namelist()
print("entries", len(names))
print("pdf_entries", [n for n in names if n.lower().endswith(".pdf")][:10])
for required in [
    "docs/generated/research_only_external_audit_prompt.md",
    "docs/generated/manuscript_audit_repair_matrix.md",
    "docs/generated/qfpi_semantic_reconciliation.md",
    "docs/generated/theorem_extension_registry.md",
]:
    assert required in names, required
PY
```

Expected: entry count prints, `pdf_entries` is empty or limited exactly as the package policy states, and required files are present.

- [ ] **Step 4: Commit**

```bash
git add scripts/build_research_only_audit_package.py tests/contracts/test_research_only_audit_package.py docs/generated/research_only_external_audit_package.zip docs/generated/research_only_external_audit_package_manifest.json docs/generated/research_only_external_audit_prompt.md docs/PR_DELTAS/rev-r087.md
git commit -m "REV-R087: refresh research-only audit package"
```

## Five-PR Checkpoint Rule For This Slice

After REV-R078 and again after REV-R083:

Run:

```bash
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5
venv/bin/python -m pytest --collect-only -q
venv/bin/python -m pytest tests/contracts tests/mio tests/htt tests/obsstat tests/bass -q
```

Record in `docs/generated/progress_checkpoints/` or a new `docs/generated/research_program_checkpoints/`:

- completed revision count
- canonical DAG count remains 62/62
- new research DAG proposed/completed count
- blockers
- claim-tier drift findings
- web CRAG refresh if any literature or data-release fact changed

## Kill Switches

Stop or downscope the affected PR if:

- CF4++ `+44` cannot be bound to canonical config/input hashes: quarantine the number.
- raw CF4/DESI/BOSS/eBOSS data and randoms are absent: keep data analysis at D0/D1 diagnostic or design status.
- response rank is deficient after nuisance projection: publish no-claim/rank-deficient result, not a global-offset claim.
- matched nulls or covariance are missing: no evidence-grade local/global result.
- prior/covariance multiverse changes sign or conclusion: report sensitivity failure.
- leave-one-probe/bin-out validation fails: no detection wording; report prediction failure.
- theorem bridge constants are unbounded or missing: keep theorem as analytic/conditional only.
- G denominator is 0/0 at isotropic fixed point: record undefined, not one.
- line-of-sight source sign/phase coherence is absent: no inverse source bound.
- any manuscript text implies native solver output, family identification, geometry-detection language, MIO diagnostic promotion into inference, or scalar-only geometry promotion.

## Execution Order

1. REV-R074 archive/intake.
2. REV-R075 immediate manuscript repair.
3. REV-R076 Q/F/Pi/G formalism split.
4. REV-R077 CF4++ provenance gate.
5. REV-R078 research DAG/registry proposal.
6. Checkpoint and adversarial self-audit.
7. REV-R079 fast method diagnostics.
8. REV-R080 data-binding contracts.
9. REV-R081 CF4 adapter.
10. REV-R082 spectroscopic estimator.
11. REV-R083 joint rest-frame identifiability harness.
12. Checkpoint and replan if blockers repeat.
13. REV-R084 theorem registry.
14. REV-R085 theorem appendix artifacts.
15. REV-R086 manuscript rearchitecture.
16. REV-R087 research-only audit package refresh.

## Pre-Execution Verification Commands

Before starting implementation, run:

```bash
git status --short
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5
venv/bin/python -m pytest --collect-only -q
```

If collect-only fails, record the exact failure in the active PR delta and continue only with archive/manuscript tasks that do not depend on the failing import path.
