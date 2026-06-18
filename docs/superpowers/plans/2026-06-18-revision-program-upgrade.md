# Revision Program Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the external-audit repair plan into a novelty-preserving research revision program that turns the manuscript into a claim-tiered framework, conditional-mapping, diagnostic-analysis, and forecast paper without promoting unsupported native-solver or family-identification claims.

**Architecture:** Treat `HTT_Bianchi_revision_program.zip` and `htt_revision_upgrade_package_2026-06-17.zip` as external design inputs, not as publication artifacts. Reuse the repo's existing `common.contracts.ArtifactMode` and `AllowedUse` lanes, add source inventories and crosswalks, then stage the new experiments through manifest-backed repo scripts before manuscript promotion. All physics claims remain routed through claim-tier, transfer-provenance, null/covariance, and MIO/HTT ownership gates.

**Tech Stack:** LaTeX under `docs/manuscript`, Python 3 through `venv/bin/python`, repo-local packages under `htt/src`, `htt/mio`, and `htt/htt/htt`, generated reports under `docs/generated`, figures under `figures/current` or `figures/observed_current`, pytest contract tests, and web-verified bibliography entries.

---

## Evidence Read

- Repo contract and handoff surfaces:
  - `AGENTS.md`
  - `.agents/skills/*/SKILL.md` inventory
  - `.codex/agents/*.toml` inventory
  - `docs/codex_handoff/pr_backlog.yaml`
  - `docs/codex_handoff/pr_status.yaml`
- Existing plan to extend:
  - `docs/superpowers/plans/2026-06-18-external-audit-research-revision.md`
- Newly arrived package:
  - `HTT_Bianchi_revision_program.zip`
  - Key files: `00_STRATEGIC_OVERVIEW.md`, `01_NOVELTY_LEDGER.md`, `02_REFRAME_AND_REORG.md`, `03_UPGRADE_PLAN.md`, `04_EXPERIMENT_PROGRAM.md`, `05_DEFENSE_DOSSIER.md`, `06_LITERATURE_POSITIONING.md`, `code/*.py`
  - Smoke command:
    ```bash
    rm -rf /tmp/htt_revision_program_analysis
    mkdir -p /tmp/htt_revision_program_analysis
    unzip -q /home/cosmosapjw/Dropbox/bianchi/htt_base/HTT_Bianchi_revision_program.zip -d /tmp/htt_revision_program_analysis
    cd /tmp/htt_revision_program_analysis/revision_program/code
    /home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python run_all.py
    ```
  - Result: all six scaffold scripts exited 0; outputs are explicitly synthetic/analytic scaffolds with production hooks.
- Previously arrived upgrade package:
  - `htt_revision_upgrade_package_2026-06-17.zip`
  - Key files: `docs/02_novelty_preserving_reframe.md`, `docs/03_claim_lanes_artifact_promotion_model.md`, `docs/04_additional_numerical_experiments.md`, `docs/06_statistical_upgrade_plan.md`, `docs/10_pr_dag_revision.md`, `machine_readable/pr_dag_revision.yaml`
  - Smoke command:
    ```bash
    rm -rf /tmp/htt_revision_upgrade_package_analysis
    mkdir -p /tmp/htt_revision_upgrade_package_analysis
    unzip -q /home/cosmosapjw/Dropbox/bianchi/htt_base/htt_revision_upgrade_package_2026-06-17.zip -d /tmp/htt_revision_upgrade_package_analysis
    PYTHONPATH=/tmp/htt_revision_upgrade_package_analysis/htt_revision_upgrade_package_2026-06-17/src \
      /home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python \
      -m pytest /tmp/htt_revision_upgrade_package_analysis/htt_revision_upgrade_package_2026-06-17/tests/test_framework.py -q
    ```
  - Result: `7 passed`.
- Web CRAG snapshot for literature positioning:
  - Secrest et al., `arXiv:2505.23526`, published as Rev. Mod. Phys. cosmic dipole colloquium.
  - Böhme et al., PRL 135, 201001, radio source count dipole.
  - Whitford, Howlett, Davis, MNRAS 526, 3051, CosmicFlows-4 bulk-flow estimator uncertainty caveats.
  - `arXiv:2106.05284`, survey method for velocity and intrinsic anisotropy separation.
  - Nilsson, Uggla, Wainwright, Lim, `astro-ph/9904252`, almost-isotropic CMB does not imply almost-isotropic universe.
  - `arXiv:2510.23769`, CatWISE2020 clustering and cosmic dipole anomaly.
  - `arXiv:2511.00822`, CatWISE2020 quasar dipole reassessment.
  - `arXiv:2512.03867`, tilted anisotropic universes competitor/constraint paper.

## Scope Check

This is an upgrade plan, not a direct manuscript patch. It extends the conservative repair plan rather than replacing it:

- Conservative repair remains in `docs/superpowers/plans/2026-06-18-external-audit-research-revision.md`.
- This plan adds the novelty ledger, claim-lane crosswalk, package provenance, experiment staging, literature CRAG, defense dossier, and revised DAG.
- The incoming scaffold figures and numbers are not manuscript evidence until regenerated from repo-local scripts with manifests.
- No task implements a native low-ell solver, no task labels external transfer as native, and no task promotes family identification.

## File Structure

- Create `docs/audits/revision_program_2026-06-18/package_inventory.json`
  - Hash and list the two incoming package zips and their internal files.
- Create `docs/audits/revision_program_2026-06-18/package_inventory.md`
  - Human-readable evidence inventory and smoke-test summary.
- Create `docs/generated/revision_plan_crosswalk.md`
  - Maps prior repair tasks, new novelty items N1-N7, experiments E1-E8, and proposed PR-R000-PR-R062.
- Create `docs/generated/revision_novelty_ledger.md`
  - Repo-local, claim-tiered novelty ledger using allowed phrases.
- Create `docs/generated/revision_claim_lanes.md`
  - Concrete promotion rules using existing `ArtifactMode` and `AllowedUse`.
- Create `docs/generated/revision_literature_crag.md`
  - Web-verified citation and competitor-positioning checklist.
- Create `docs/generated/revision_defense_dossier.md`
  - Referee objection matrix derived from the new package, rewritten in repo claim language.
- Create `docs/codex_handoff/pr_dag_revision.yaml`
  - Supplemental R-DAG candidate that references existing completed PR DAG without overwriting `docs/codex_handoff/pr_status.yaml`.
- Create `scripts/inventory_revision_program_packages.py`
  - Produces package inventory JSON/MD and guards against silently changed input zips.
- Create `scripts/generate_revision_research_program.py`
  - Produces novelty ledger, claim-lane report, crosswalk, literature CRAG, and defense dossier.
- Create `tests/contracts/test_revision_program_inventory.py`
  - Verifies package hashes, smoke-test metadata, and source labels.
- Create `tests/contracts/test_revision_research_program.py`
  - Verifies claim lanes, novelty ledger tiers, no native/family promotion, and R-DAG integrity.
- Modify `scripts/check_publication_claim_freeze.py`
  - Adds public claim rows for revised safe claims only after generated ledgers exist.
- Modify `scripts/build_research_only_audit_package.py`
  - Includes the new research-program reports, not the full external toy packages.
- Modify manuscript later, after generated artifacts exist:
  - `docs/manuscript/ch01_introduction.tex`
  - `docs/manuscript/ch02_dipole_anomaly.tex`
  - `docs/manuscript/ch03_framework.tex`
  - `docs/manuscript/ch07_results.tex`
  - `docs/manuscript/ch08_robustness.tex`
  - `docs/manuscript/ch09_discussion.tex`
  - `docs/manuscript/ch10_future.tex`
  - `docs/manuscript/main.tex`
  - `docs/manuscript/references.bib`

## Adversarial Role Notes

- Code cartographer steelman: reuse existing `ArtifactMode`, `AllowedUse`, `status_snapshot`, figure manifests, and manuscript-audit scripts because the repo already contains a mature promotion layer. Attack: vendoring the incoming `htt_revision_framework` would duplicate `common.contracts` and create a second source of truth.
- Harness engineer steelman: first add inventory and generator tests before touching manuscript text. Attack: editing chapters before source JSON/manifests creates another unverifiable report state.
- Physics/statistics auditor steelman: N1, N2, N3, N6, and N7 can preserve novelty without detection language if each is assigned exact, supported, conditional, or forecast status. Attack: any single-number Bayes-factor headline without prior-floor, sigma-beta, covariance, null, PPC, and LOOCV status is still a rejection trigger.
- Claim-gate reviewer steelman: a diagnostic-only plot can be meaningful if its lane forbids evidence, p-values, posterior odds, native transfer, geometry, and family use. Attack: "diagnostic-only" must not become a dumping ground for hidden evidence claims.
- Regression tester steelman: package smoke results and repo tests should be recorded separately. Attack: external package tests passing do not validate repo integration.

### Task 1: Package Inventory and Smoke-Test Ledger

**Files:**
- Create: `scripts/inventory_revision_program_packages.py`
- Create: `tests/contracts/test_revision_program_inventory.py`
- Create generated: `docs/audits/revision_program_2026-06-18/package_inventory.json`
- Create generated: `docs/audits/revision_program_2026-06-18/package_inventory.md`

- [ ] **Step 1: Write the failing inventory test**

Create `tests/contracts/test_revision_program_inventory.py`:

```python
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JSON_OUT = ROOT / "docs/audits/revision_program_2026-06-18/package_inventory.json"
MD_OUT = ROOT / "docs/audits/revision_program_2026-06-18/package_inventory.md"


def test_revision_package_inventory_check_mode_passes():
    result = subprocess.run(
        [
            "venv/bin/python",
            "scripts/inventory_revision_program_packages.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_revision_package_inventory_records_sources_and_smoke_results():
    payload = json.loads(JSON_OUT.read_text())
    assert payload["schema_version"] == "htt.revision_program_inventory.v1"
    assert payload["owner"] == "COMMON"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert set(payload["packages"]) == {
        "HTT_Bianchi_revision_program.zip",
        "htt_revision_upgrade_package_2026-06-17.zip",
    }
    for package in payload["packages"].values():
        assert package["sha256"]
        assert package["entries"]
        assert package["source_role"] == "external_revision_input"
    assert payload["smoke_tests"]["revision_program_run_all"]["status"] == "passed"
    assert payload["smoke_tests"]["upgrade_package_pytest"]["status"] == "passed"
    assert "synthetic/analytic scaffold" in payload["caveats"]
    assert "not publication evidence" in payload["caveats"]
    text = MD_OUT.read_text()
    assert "HTT_Bianchi_revision_program.zip" in text
    assert "htt_revision_upgrade_package_2026-06-17.zip" in text
    assert "not publication evidence" in text
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_revision_program_inventory.py -q
```

Expected: fails because `scripts/inventory_revision_program_packages.py` and generated inventory files do not exist.

- [ ] **Step 3: Implement the package inventory script**

Create `scripts/inventory_revision_program_packages.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/audits/revision_program_2026-06-18"
JSON_OUT = OUT_DIR / "package_inventory.json"
MD_OUT = OUT_DIR / "package_inventory.md"
PACKAGES = (
    "HTT_Bianchi_revision_program.zip",
    "htt_revision_upgrade_package_2026-06-17.zip",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def zip_entries(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        return sorted(archive.namelist())


def build_payload() -> dict:
    packages: dict[str, dict] = {}
    for name in PACKAGES:
        path = ROOT / name
        if not path.exists():
            raise FileNotFoundError(path)
        packages[name] = {
            "path": name,
            "sha256": sha256(path),
            "entries": zip_entries(path),
            "source_role": "external_revision_input",
        }
    return {
        "schema_version": "htt.revision_program_inventory.v1",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "packages": packages,
        "smoke_tests": {
            "revision_program_run_all": {
                "command": "venv/bin/python run_all.py in extracted revision_program/code",
                "status": "passed",
            },
            "upgrade_package_pytest": {
                "command": "PYTHONPATH=<extracted>/src venv/bin/python -m pytest tests/test_framework.py -q",
                "status": "passed",
            },
        },
        "caveats": [
            "synthetic/analytic scaffold",
            "not publication evidence",
            "adapt concepts into repo-local generators before manuscript promotion",
        ],
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Revision Program Package Inventory",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        "generating_command: `venv/bin/python scripts/inventory_revision_program_packages.py --write`",
        "",
        "## Packages",
        "",
        "| Package | SHA256 | Entries | Role |",
        "| --- | --- | ---: | --- |",
    ]
    for name, package in payload["packages"].items():
        lines.append(
            f"| `{name}` | `{package['sha256']}` | {len(package['entries'])} | {package['source_role']} |"
        )
    lines.extend(
        [
            "",
            "## Smoke Tests",
            "",
            "| Check | Status | Command |",
            "| --- | --- | --- |",
        ]
    )
    for name, check in payload["smoke_tests"].items():
        lines.append(f"| `{name}` | `{check['status']}` | `{check['command']}` |")
    lines.extend(["", "## Caveats", ""])
    for caveat in payload["caveats"]:
        lines.append(f"- {caveat}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload()
    text = render_markdown(payload)
    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        JSON_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        MD_OUT.write_text(text)
        return 0
    if args.check:
        expected_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        missing = [str(path) for path in (JSON_OUT, MD_OUT) if not path.exists()]
        if missing:
            print("missing generated inventory: " + ", ".join(missing), file=sys.stderr)
            return 1
        if JSON_OUT.read_text() != expected_json:
            print("package_inventory.json is stale; run with --write", file=sys.stderr)
            return 1
        if MD_OUT.read_text() != text:
            print("package_inventory.md is stale; run with --write", file=sys.stderr)
            return 1
        return 0
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Generate the inventory**

Run:

```bash
venv/bin/python scripts/inventory_revision_program_packages.py --write
```

Expected: writes JSON and Markdown inventory under `docs/audits/revision_program_2026-06-18/`.

- [ ] **Step 5: Verify inventory tests pass**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_revision_program_inventory.py -q
```

Expected: `2 passed`.

- [ ] **Step 6: Commit**

Run:

```bash
git add scripts/inventory_revision_program_packages.py tests/contracts/test_revision_program_inventory.py docs/audits/revision_program_2026-06-18/package_inventory.json docs/audits/revision_program_2026-06-18/package_inventory.md
git commit -m "REV-R001: inventory revision program inputs"
```

### Task 2: Novelty Ledger, Claim Lanes, Defense Dossier, and Crosswalk Generator

**Files:**
- Create: `scripts/generate_revision_research_program.py`
- Create: `tests/contracts/test_revision_research_program.py`
- Create generated: `docs/generated/revision_plan_crosswalk.md`
- Create generated: `docs/generated/revision_novelty_ledger.md`
- Create generated: `docs/generated/revision_claim_lanes.md`
- Create generated: `docs/generated/revision_literature_crag.md`
- Create generated: `docs/generated/revision_defense_dossier.md`
- Create generated: `docs/codex_handoff/pr_dag_revision.yaml`

- [ ] **Step 1: Write the failing research-program test**

Create `tests/contracts/test_revision_research_program.py`:

```python
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATED = [
    ROOT / "docs/generated/revision_plan_crosswalk.md",
    ROOT / "docs/generated/revision_novelty_ledger.md",
    ROOT / "docs/generated/revision_claim_lanes.md",
    ROOT / "docs/generated/revision_literature_crag.md",
    ROOT / "docs/generated/revision_defense_dossier.md",
    ROOT / "docs/codex_handoff/pr_dag_revision.yaml",
]


def read_all_generated_text() -> str:
    return "\n".join(path.read_text() for path in GENERATED if path.exists())


def test_revision_research_program_check_mode_passes():
    result = subprocess.run(
        [
            "venv/bin/python",
            "scripts/generate_revision_research_program.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_revision_research_program_contains_required_reframe_objects():
    text = read_all_generated_text()
    for token in [
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "N6",
        "N7",
        "E1",
        "E2",
        "E3",
        "E4",
        "E5",
        "E6",
        "E7",
        "E8",
        "PR-R000",
        "PR-R062",
    ]:
        assert token in text
    assert "external/proxy transfer is not native transfer" in text
    assert "family identification remains blocked" in text
    assert "paper_main_validated" in text
    assert "diagnostic_only/external_audit_conditioned/external_audit" in text


def test_revision_research_program_avoids_forbidden_promotion():
    text = read_all_generated_text().lower()
    forbidden_patterns = [
        r"native solver result",
        r"family identified",
        r"geometry detected",
        r"truth certificate",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, text), pattern
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_revision_research_program.py -q
```

Expected: fails because the generator and generated files do not exist.

- [ ] **Step 3: Implement the generator with embedded controlled content**

Create `scripts/generate_revision_research_program.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {
    "crosswalk": ROOT / "docs/generated/revision_plan_crosswalk.md",
    "novelty": ROOT / "docs/generated/revision_novelty_ledger.md",
    "lanes": ROOT / "docs/generated/revision_claim_lanes.md",
    "literature": ROOT / "docs/generated/revision_literature_crag.md",
    "defense": ROOT / "docs/generated/revision_defense_dossier.md",
    "dag": ROOT / "docs/codex_handoff/pr_dag_revision.yaml",
}

NOVELTY = [
    ("N1", "exact", "Signed comparator coordinate for shear, vorticity, tilt, and anisotropic curvature."),
    ("N2", "supported", "Matter-sector departure framing addresses the almost-EGS loophole."),
    ("N3", "conditional", "Dipole-conditioned mapping to observational equivalence classes; family identification remains blocked."),
    ("N4", "supported", "Species-resolved effective-temperature closure with explicit representation caveats."),
    ("N5", "exact", "Claim-tiered provenance methodology for contested-anomaly reporting."),
    ("N6", "supported", "Per-channel occupancy vector with channel-matched denominators."),
    ("N7", "forecast", "Tomographic local-boost versus global-tilt separation forecast."),
]

EXPERIMENTS = [
    ("E1", "Prior floor and ceiling sensitivity surface plus fractional/intrinsic Bayes factor."),
    ("E2", "Bulk-flow sigma-beta uncertainty band plus look-elsewhere correction."),
    ("E3", "Per-channel occupancy vector across model rows."),
    ("E4", "Deterministic quadrupole template likelihood versus stochastic covariance treatment."),
    ("E5", "Tomographic degeneracy-breaking forecast for local boost and global tilt."),
    ("E6", "Posterior-predictive and LOOCV adequacy checks for any evidence-grade HTT wording."),
    ("E7", "Cross-survey covariance model for shared clustering-dipole uncertainty."),
    ("E8", "Native low-ell morphology atlas roadmap only; no implementation in this repo state."),
]

PR_ROWS = [
    ("PR-R000", "Promotion-model audit over existing ArtifactMode and AllowedUse", []),
    ("PR-R001", "Status snapshot lane propagation", ["PR-R000"]),
    ("PR-R002", "Figure manifest lane and forbidden-use fields", ["PR-R000"]),
    ("PR-R003", "PDF-level claim lint integration", ["PR-R001"]),
    ("PR-R010", "Prior support sensitivity surface", ["PR-R002"]),
    ("PR-R011", "Bulk-flow uncertainty propagation band", ["PR-R002"]),
    ("PR-R012", "Rule-of-three FPR intervals", ["PR-R002"]),
    ("PR-R013", "MES algebraic ceiling versus observational-bound calibration", ["PR-R002"]),
    ("PR-R020", "Per-channel occupancy vector", ["PR-R000"]),
    ("PR-R021", "Certified filling status and invalid-sector handling", ["PR-R020"]),
    ("PR-R022", "Depth-gap G_F epsilon floor and uncertainty kind", ["PR-R021"]),
    ("PR-R023", "Component filling anatomy", ["PR-R021"]),
    ("PR-R030", "Local/global response-rank audit", ["PR-R002"]),
    ("PR-R031", "Local boost-only G_F null", ["PR-R022", "PR-R030"]),
    ("PR-R032", "Global-tilt injection recovery", ["PR-R022", "PR-R030"]),
    ("PR-R033", "Survey-axis and selection-response nulls", ["PR-R031"]),
    ("PR-R034", "Cross-survey covariance model", ["PR-R033"]),
    ("PR-R040", "Deterministic-template likelihood branch", ["PR-R002"]),
    ("PR-R041", "Stochastic covariance likelihood branch", ["PR-R002"]),
    ("PR-R042", "Template-versus-covariance sensitivity report", ["PR-R040", "PR-R041"]),
    ("PR-R043", "Scalar equivalence-class graph with family identification blocked", ["PR-R020", "PR-R042"]),
    ("PR-R050", "Posterior-predictive checks", ["PR-R034", "PR-R042"]),
    ("PR-R051", "LOOCV held-out probe test", ["PR-R034"]),
    ("PR-R052", "Prior covariance null sensitivity dashboard", ["PR-R010", "PR-R011", "PR-R012", "PR-R034"]),
    ("PR-R053", "Manuscript strong-evidence wording replacement", ["PR-R003", "PR-R052"]),
    ("PR-R060", "Regenerate figure suite with manifests and source JSON", ["PR-R052", "PR-R053"]),
    ("PR-R061", "Build reviewer packet", ["PR-R060"]),
    ("PR-R062", "Independent CoVe run and final response table", ["PR-R061"]),
]


def metadata(title: str) -> list[str]:
    return [
        f"# {title}",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        "caveats:",
        "- external/proxy transfer is not native transfer",
        "- family identification remains blocked until native morphology atlas support exists",
        "- scaffold package outputs are not publication evidence",
        "",
    ]


def render_novelty() -> str:
    lines = metadata("Revision Novelty Ledger")
    lines.extend(["| ID | Tier | Safe statement |", "| --- | --- | --- |"])
    for ident, tier, statement in NOVELTY:
        lines.append(f"| {ident} | {tier} | {statement} |")
    lines.extend(["", "Promotion rule: exact and supported claims can enter framework text; conditional claims require premise boxes; forecast claims require forecast labels."])
    return "\n".join(lines) + "\n"


def render_lanes() -> str:
    lines = metadata("Revision Claim Lanes")
    lines.extend(
        [
            "| Lane | Allowed use | Forbidden use |",
            "| --- | --- | --- |",
            "| `blocked/governance_diagnostic/internal_only` | gate failure reports | evidence, posterior odds, paper claims |",
            "| `diagnostic_only/external_audit_conditioned/external_audit` | external audit diagnostics | paper-main inference or family use |",
            "| `diagnostic_only/paper_appendix_conditioned/paper_appendix` | caveated diagnostic plots | validated evidence wording |",
            "| `conditional/paper_appendix_conditioned/paper_appendix` | transfer-conditional summaries | native or geometry wording |",
            "| `conditional/paper_main_candidate/paper_main` | caveat-box framework or forecast figures | claim without premise/null/covariance status |",
            "| `validated/paper_main_validated/paper_main` | future native-validated results | unavailable in current repo state |",
            "",
            "Caption rule: every promoted figure states claim lane, transfer source, null status, and forbidden-use sentence.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_crosswalk() -> str:
    lines = metadata("Revision Plan Crosswalk")
    lines.extend(["## Relation To Existing Plan", ""])
    lines.append("The conservative repair plan clears external-audit rejection triggers. This upgrade adds novelty preservation, experiment staging, literature CRAG, and a supplemental R-DAG.")
    lines.extend(["", "## Novelty To Experiment Map", "", "| Novelty | Experiments | Manuscript home |", "| --- | --- | --- |"])
    rows = {
        "N1": ("E3", "Chapter 3 framework and Chapter 7 occupancy repair"),
        "N2": ("literature CRAG", "Introduction and discussion"),
        "N3": ("E2,E7,E8 roadmap", "Dipole anomaly and results caveat boxes"),
        "N4": ("Gaunt and closure correction from conservative plan", "Chapter 5"),
        "N5": ("claim lanes and audit package", "Methods and appendices"),
        "N6": ("E3", "Results and appendix table"),
        "N7": ("E5", "Future and forecast results"),
    }
    for novelty, (experiments, home) in rows.items():
        lines.append(f"| {novelty} | {experiments} | {home} |")
    lines.extend(["", "## Experiment List", ""])
    for ident, description in EXPERIMENTS:
        lines.append(f"- {ident}: {description}")
    lines.extend(["", "## Supplemental PR Slice", ""])
    for ident, title, depends in PR_ROWS:
        dep_text = ", ".join(depends) if depends else "none"
        lines.append(f"- {ident}: {title}; depends: {dep_text}")
    return "\n".join(lines) + "\n"


def render_literature() -> str:
    lines = metadata("Revision Literature CRAG")
    lines.extend(
        [
            "| Source | Use in revision | Status |",
            "| --- | --- | --- |",
            "| `arXiv:2505.23526` / Rev. Mod. Phys. dipole colloquium | cosmic dipole anomaly context | web-verified |",
            "| PRL 135, 201001 | independent radio source-count dipole context | web-verified |",
            "| MNRAS 526, 3051 | CF4 bulk-flow uncertainty caveat | web-verified |",
            "| `arXiv:2106.05284` | survey/tomographic separation motivation | web-verified |",
            "| `astro-ph/9904252` | almost-EGS loophole support | web-verified |",
            "| `arXiv:2510.23769` | CatWISE clustering systematic context | web-verified |",
            "| `arXiv:2511.00822` | CatWISE reassessment context | web-verified |",
            "| `arXiv:2512.03867` | tilted anisotropic universe competitor/constraint | web-verified |",
            "",
            "CRAG rule: every current-literature claim must be checked against the latest arXiv/journal version before manuscript citation is updated.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_defense() -> str:
    lines = metadata("Revision Defense Dossier")
    rows = [
        ("O1", "Bayes factor restates dipole significance", "Concede and report it as conditional, prior-sensitive, sigma-beta-sensitive forward-model output."),
        ("O2", "Evidence prior floor dominates", "Generate E1 surface and quote ranges plus fractional/intrinsic Bayes factor."),
        ("O3", "FPR zero is not a rate estimate", "Use rule-of-three interval and matched-mask/full-covariance roadmap."),
        ("O4", "Deterministic quadrupole is not five random modes", "Add E4 template likelihood branch and delta-log-likelihood sensitivity."),
        ("O5", "Tilted-anisotropic competitor constrains amplitude explanations", "Engage as motivation for conditional mapping rather than detection framing."),
        ("O6", "CMB isotropy bounds already exist", "Use almost-EGS loophole distinction and maintain CMB-null consistency."),
        ("O7", "Signed scalar is algebraic", "State exact algebra and defend comparator-explicit signed packaging."),
        ("O8", "Governance is not physics", "Tie governance to reproducible contested-anomaly inference and claim provenance."),
        ("O9", "Dipole premise may be systematic", "Make premise conditional and updateable; keep premise-independent framework claims separate."),
        ("O10", "Local boost and global tilt are degenerate", "Promote E5 as forecasted decision requirement, not current discrimination proof."),
        ("O11", "Gaunt coefficient mismatch", "Apply conservative-plan correction and lock with CoVe check."),
        ("O12", "Closure contribution fraction overworded", "Rewrite as contribution fraction, not accuracy claim."),
        ("O13", "No native Boltzmann solve", "Disclose external/proxy transfer and keep native roadmap separate."),
    ]
    lines.extend(["| ID | Steelman objection | Repo-safe response |", "| --- | --- | --- |"])
    for ident, objection, response in rows:
        lines.append(f"| {ident} | {objection} | {response} |")
    return "\n".join(lines) + "\n"


def render_dag() -> str:
    lines = ["prs:"]
    for ident, title, depends in PR_ROWS:
        dep_text = ", ".join(depends)
        lines.append(f"  - id: {ident}")
        lines.append(f"    title: {title!r}")
        lines.append(f"    depends: [{dep_text}]")
        lines.append("    status: proposed")
    return "\n".join(lines) + "\n"


RENDERERS = {
    "crosswalk": render_crosswalk,
    "novelty": render_novelty,
    "lanes": render_lanes,
    "literature": render_literature,
    "defense": render_defense,
    "dag": render_dag,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    expected = {key: renderer() for key, renderer in RENDERERS.items()}
    if args.write:
        for key, text in expected.items():
            OUTPUTS[key].parent.mkdir(parents=True, exist_ok=True)
            OUTPUTS[key].write_text(text)
        return 0
    if args.check:
        for key, text in expected.items():
            path = OUTPUTS[key]
            if not path.exists():
                print(f"missing generated file: {path}", file=sys.stderr)
                return 1
            if path.read_text() != text:
                print(f"stale generated file: {path}", file=sys.stderr)
                return 1
        return 0
    for key, text in expected.items():
        print(f"===== {OUTPUTS[key]} =====")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Generate the research program reports**

Run:

```bash
venv/bin/python scripts/generate_revision_research_program.py --write
```

Expected: writes all five generated Markdown reports and `docs/codex_handoff/pr_dag_revision.yaml`.

- [ ] **Step 5: Run research-program tests**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_revision_research_program.py -q
```

Expected: `3 passed`.

- [ ] **Step 6: Run semantic guard over generated reports**

Run:

```bash
venv/bin/python -m common.semantic_guards.no_overclaim \
  docs/generated/revision_plan_crosswalk.md \
  docs/generated/revision_novelty_ledger.md \
  docs/generated/revision_claim_lanes.md \
  docs/generated/revision_literature_crag.md \
  docs/generated/revision_defense_dossier.md
```

Expected: no native/family/geometry overclaim findings.

- [ ] **Step 7: Commit**

Run:

```bash
git add scripts/generate_revision_research_program.py tests/contracts/test_revision_research_program.py docs/generated/revision_plan_crosswalk.md docs/generated/revision_novelty_ledger.md docs/generated/revision_claim_lanes.md docs/generated/revision_literature_crag.md docs/generated/revision_defense_dossier.md docs/codex_handoff/pr_dag_revision.yaml
git commit -m "REV-R002: add revision research program"
```

### Task 3: Promote Artifact Lanes Through Figure Manifests and Audit Packages

**Files:**
- Modify: `htt/src/common/artifact_manifest.py`
- Modify: `scripts/build_research_only_audit_package.py`
- Modify: `tests/contracts/test_audit_package_generator.py`
- Modify: `tests/contracts/test_current_manuscript_figures.py`

- [ ] **Step 1: Add a failing figure-manifest lane assertion**

Append this test to `tests/contracts/test_current_manuscript_figures.py`:

```python
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_current_manifested_figures_carry_claim_lane_fields():
    manifest_paths = sorted((ROOT / "figures/current").glob("*.manifest.json"))
    assert manifest_paths, "expected current figure manifests"
    for manifest_path in manifest_paths:
        payload = json.loads(manifest_path.read_text())
        assert payload["claim_tier"] in {
            "blocked",
            "diagnostic_only",
            "exploratory",
            "conditional",
            "validated",
        }
        assert payload["artifact_mode"] in {
            "governance_diagnostic",
            "internal_exploratory",
            "external_audit_conditioned",
            "paper_appendix_conditioned",
            "paper_main_candidate",
            "paper_main_validated",
        }
        assert payload["allowed_use"] in {
            "internal_only",
            "external_audit",
            "paper_appendix",
            "paper_main",
        }
        assert payload.get("caption_policy"), manifest_path
        assert any("family" in item.lower() for item in payload["caption_policy"])
```

- [ ] **Step 2: Run the failing lane assertion**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_current_manuscript_figures.py::test_current_manifested_figures_carry_claim_lane_fields -q
```

Expected: fails on any legacy manifest missing `artifact_mode`, `allowed_use`, or `caption_policy`.

- [ ] **Step 3: Patch figure generators to write lane fields**

Update `scripts/make_current_manuscript_figures.py`, `scripts/make_observed_data_manuscript_figures.py`, and `scripts/curate_current_manuscript_figures.py` so every manifest uses this payload fragment:

```python
lane_payload = {
    "claim_tier": "diagnostic_only",
    "artifact_mode": "paper_appendix_conditioned",
    "allowed_use": "paper_appendix",
    "caption_policy": [
        "External/proxy transfer is not native transfer.",
        "This figure is not evidence for geometry or family identification.",
        "Use requires the caveats and source JSON linked in this manifest.",
    ],
    "promotion_blockers": [
        "native_morphology_atlas_absent",
        "matched_mask_full_covariance_status_not_validated",
    ],
}
manifest.update(lane_payload)
```

- [ ] **Step 4: Regenerate current figure manifests**

Run:

```bash
venv/bin/python scripts/make_current_manuscript_figures.py
venv/bin/python scripts/make_observed_data_manuscript_figures.py
venv/bin/python scripts/curate_current_manuscript_figures.py
```

Expected: existing figure PNGs and manifests are regenerated with lane fields and no missing source JSON references.

- [ ] **Step 5: Include revision reports in research-only audit package**

Modify `scripts/build_research_only_audit_package.py` so the included file list contains:

```python
REVISION_PROGRAM_FILES = (
    "docs/audits/revision_program_2026-06-18/package_inventory.json",
    "docs/audits/revision_program_2026-06-18/package_inventory.md",
    "docs/generated/revision_plan_crosswalk.md",
    "docs/generated/revision_novelty_ledger.md",
    "docs/generated/revision_claim_lanes.md",
    "docs/generated/revision_literature_crag.md",
    "docs/generated/revision_defense_dossier.md",
    "docs/codex_handoff/pr_dag_revision.yaml",
)
```

Append `REVISION_PROGRAM_FILES` to the existing manifest input list, and reject missing files with a clear error.

- [ ] **Step 6: Run package and figure tests**

Run:

```bash
venv/bin/python -m pytest \
  tests/contracts/test_current_manuscript_figures.py::test_current_manifested_figures_carry_claim_lane_fields \
  tests/contracts/test_audit_package_generator.py \
  -q
venv/bin/python scripts/build_research_only_audit_package.py --check
```

Expected: tests pass and package check succeeds.

- [ ] **Step 7: Commit**

Run:

```bash
git add scripts/make_current_manuscript_figures.py scripts/make_observed_data_manuscript_figures.py scripts/curate_current_manuscript_figures.py scripts/build_research_only_audit_package.py tests/contracts/test_current_manuscript_figures.py tests/contracts/test_audit_package_generator.py figures/current docs/generated/research_only_external_audit_package_manifest.json docs/generated/research_only_external_audit_package.zip
git commit -m "REV-R003: propagate revision claim lanes"
```

### Task 4: Stage Conservative P0/P1 Experiment Assets From Repo Inputs

**Files:**
- Create: `scripts/generate_revision_experiment_assets.py`
- Create: `tests/contracts/test_revision_experiment_assets.py`
- Create generated: `docs/generated/revision_experiment_assets.json`
- Create generated: `docs/generated/revision_experiment_assets.md`
- Create figures and manifests:
  - `figures/current/fig_revision_prior_support_surface.png`
  - `figures/current/fig_revision_sigma_beta_band.png`
  - `figures/current/fig_revision_rule_of_three_fpr.png`
  - `figures/current/fig_revision_per_channel_occupancy.png`
  - `figures/current/fig_revision_tomographic_forecast.png`

- [ ] **Step 1: Write failing experiment-asset tests**

Create `tests/contracts/test_revision_experiment_assets.py`:

```python
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSET_JSON = ROOT / "docs/generated/revision_experiment_assets.json"


def test_revision_experiment_assets_check_mode_passes():
    result = subprocess.run(
        [
            "venv/bin/python",
            "scripts/generate_revision_experiment_assets.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_revision_experiment_assets_are_lane_limited():
    payload = json.loads(ASSET_JSON.read_text())
    assert payload["schema_version"] == "htt.revision_experiment_assets.v1"
    assert payload["owner"] == "COMMON"
    assert payload["claim_tier"] == "diagnostic_only"
    expected = {
        "E1_prior_support_surface",
        "E2_sigma_beta_band",
        "E3_per_channel_occupancy",
        "E5_tomographic_forecast",
        "FPR_rule_of_three",
    }
    assert set(payload["assets"]) == expected
    for asset in payload["assets"].values():
        assert asset["artifact_mode"] in {
            "external_audit_conditioned",
            "paper_appendix_conditioned",
            "paper_main_candidate",
        }
        assert asset["allowed_use"] in {"external_audit", "paper_appendix", "paper_main"}
        assert "not native transfer" in " ".join(asset["caveats"])
        assert "not family identification" in " ".join(asset["caveats"])
        assert Path(ROOT / asset["figure_path"]).exists()
        assert Path(ROOT / asset["manifest_path"]).exists()
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_revision_experiment_assets.py -q
```

Expected: fails because the generator and outputs do not exist.

- [ ] **Step 3: Implement the generator with deterministic toy-to-repo transition labels**

Create `scripts/generate_revision_experiment_assets.py` that:

1. Loads current repo-generated observational inventories when present:
   - `docs/generated/observational_data_inventory.json`
   - `docs/generated/observed_longrun_analysis.json`
   - `docs/generated/current_science_plot_payload.json`
2. Generates deterministic diagnostic arrays for E1, E2, E3, FPR, and E5 using the same formulas as the incoming scaffold only when production inputs are absent.
3. Marks each asset with `input_mode`:
   - `repo_observed_input` when repo observed data is consumed.
   - `analytic_scaffold` when the package formula is used.
4. Writes JSON, Markdown, PNG, and manifest files.

Use this manifest fragment for every asset:

```python
manifest = {
    "owner": "COMMON",
    "implementation_scope": "common",
    "claim_tier": asset_claim_tier,
    "artifact_mode": asset_mode,
    "allowed_use": asset_allowed_use,
    "transfer_source": "external/proxy_or_none",
    "sky_support_status": asset_sky_status,
    "null_mock_status": asset_null_status,
    "config_hash": config_hash,
    "input_hashes": input_hashes,
    "generating_command": "venv/bin/python scripts/generate_revision_experiment_assets.py --write",
    "caveats": [
        "not native transfer",
        "not family identification",
        "does not promote geometry or family claims",
        "paper-main use requires the lane recorded in this manifest",
    ],
}
```

- [ ] **Step 4: Generate the experiment assets**

Run:

```bash
venv/bin/python scripts/generate_revision_experiment_assets.py --write
```

Expected: writes five PNGs, five manifests, JSON, and Markdown report.

- [ ] **Step 5: Run experiment tests and visual manifest audit**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_revision_experiment_assets.py -q
venv/bin/python scripts/audit_manuscript_figures.py --dry-run
```

Expected: experiment tests pass; figure audit sees manifests for the new assets if they are referenced.

- [ ] **Step 6: Commit**

Run:

```bash
git add scripts/generate_revision_experiment_assets.py tests/contracts/test_revision_experiment_assets.py docs/generated/revision_experiment_assets.json docs/generated/revision_experiment_assets.md figures/current/fig_revision_*.png figures/current/fig_revision_*.manifest.json
git commit -m "REV-R010: add revision diagnostic assets"
```

### Task 5: Manuscript Reframe After Generated Assets Exist

**Files:**
- Modify: `docs/manuscript/ch01_introduction.tex`
- Modify: `docs/manuscript/ch02_dipole_anomaly.tex`
- Modify: `docs/manuscript/ch03_framework.tex`
- Modify: `docs/manuscript/ch07_results.tex`
- Modify: `docs/manuscript/ch08_robustness.tex`
- Modify: `docs/manuscript/ch09_discussion.tex`
- Modify: `docs/manuscript/ch10_future.tex`
- Modify: `docs/manuscript/generated/current_figures_results.tex`
- Modify: `docs/manuscript/references.bib`

- [ ] **Step 1: Add manuscript regression test for revised framing**

Append to `tests/contracts/test_publication_claim_freeze.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_manuscript_uses_revision_program_framing():
    combined = "\n".join(
        path.read_text()
        for path in [
            ROOT / "docs/manuscript/ch01_introduction.tex",
            ROOT / "docs/manuscript/ch02_dipole_anomaly.tex",
            ROOT / "docs/manuscript/ch07_results.tex",
            ROOT / "docs/manuscript/ch09_discussion.tex",
            ROOT / "docs/manuscript/ch10_future.tex",
        ]
    )
    assert "claim-tiered framework" in combined
    assert "transfer-conditional" in combined
    assert "conditional on the dipole premise" in combined
    assert "family identification remains blocked" in combined
    assert "tomographic" in combined
    assert "prior-support sensitivity" in combined
```

- [ ] **Step 2: Run the failing manuscript framing test**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_publication_claim_freeze.py::test_manuscript_uses_revision_program_framing -q
```

Expected: fails until the revised language is added.

- [ ] **Step 3: Update the abstract/introduction around safe novelty**

Patch `docs/manuscript/ch01_introduction.tex` to state:

```tex
This report is a claim-tiered framework paper, not a native-solver
detection paper.  It introduces a signed comparator coordinate for
FLRW departure, separates MIO diagnostics from HTT likelihoods,
and uses current matter-dipole inputs only as a transfer-conditional
and dipole-conditional demonstration layer.  Because almost-isotropic
CMB temperature fields do not by themselves close every matter-sector
departure loophole, the framework is designed to state what current
data can quantify, what remains conditional, and what future
tomographic or native-morphology information would be needed to
promote a claim.
```

- [ ] **Step 4: Update the dipole chapter with current-literature CRAG**

Patch `docs/manuscript/ch02_dipole_anomaly.tex` so the literature paragraph cites:

```tex
The matter-dipole premise is actively contested.  We therefore treat
CatWISE, radio, and bulk-flow inputs as conditional probes rather than
settled evidence for anisotropic geometry.  Recent reassessments of
CatWISE clustering and mask coupling, current radio-source-count
analyses, and tilted-anisotropic model constraints are discussed as
premise and systematics controls.  This framing makes the likelihood
layer updateable: replacing or down-weighting a survey changes the
conditional HTT evidence surface without changing the exact
claim-tier and provenance machinery.
```

- [ ] **Step 5: Update results around prior, sigma-beta, occupancy, and forecast**

Patch `docs/manuscript/ch07_results.tex` to add a generated-assets subsection:

```tex
\subsection{Revision diagnostic assets}
\label{sec:revision-diagnostic-assets}

Figures~\ref{fig:revision-prior-support-surface}
through~\ref{fig:revision-tomographic-forecast} are generated
from the revision-program asset script and carry claim-lane
manifests.  They are not native-transfer evidence and do not
identify a Bianchi family.  Their role is to expose which parts of
the current conditional preference are prior-support, bulk-flow
uncertainty, null-calibration, occupancy-denominator, or
local/global-degeneracy questions.
```

Add figure references only after `scripts/generate_revision_experiment_assets.py --write` has produced PNGs and manifests.

- [ ] **Step 6: Update future-work chapter around native solver boundary**

Patch `docs/manuscript/ch10_future.tex` to state:

```tex
The native low-ell morphology atlas remains the boundary between
scalar compatibility diagnostics and family-level morphology claims.
The current repository can define adapter schemas, artifact lanes,
null/covariance gates, and tomographic forecasts, but it does not
produce native low-ell transfer functions or morphology-atlas
comparisons.  Future promotion requires native atlas entries,
matched masks, full covariance, external nulls, and family-equivalence
tests.
```

- [ ] **Step 7: Add bibliography entries from web CRAG**

Add BibTeX entries to `docs/manuscript/references.bib` for:

```bibtex
@article{Secrest2025CosmicDipoleColloquium,
  title = {Colloquium: The Cosmic Dipole Anomaly},
  author = {Secrest, Nathan J. and von Hausegger, Sebastian and Rameez, Mohamed and Mohayaee, Roya and Sarkar, Subir},
  journal = {Reviews of Modern Physics},
  year = {2025},
  eprint = {2505.23526},
  archivePrefix = {arXiv},
  primaryClass = {astro-ph.CO}
}

@article{Nilsson1999AlmostIsotropic,
  title = {An Almost Isotropic Cosmic Microwave Temperature Does Not Imply an Almost Isotropic Universe},
  author = {Nilsson, U. S. and Uggla, C. and Wainwright, J. and Lim, W. C.},
  journal = {The Astrophysical Journal Letters},
  year = {1999},
  eprint = {astro-ph/9904252},
  archivePrefix = {arXiv}
}

@article{Whitford2023CF4Estimators,
  title = {Evaluating bulk flow estimators for CosmicFlows-4 measurements},
  author = {Whitford, A. M. and Howlett, C. and Davis, T. M.},
  journal = {Monthly Notices of the Royal Astronomical Society},
  volume = {526},
  pages = {3051},
  year = {2023},
  eprint = {2306.11269},
  archivePrefix = {arXiv},
  primaryClass = {astro-ph.CO}
}

@article{Nadolny2021VelocityAnisotropyTest,
  title = {A new way to test the Cosmological Principle: measuring our peculiar velocity and the large scale anisotropy independently},
  author = {Nadolny, Tobias and Durrer, Ruth and Kunz, Martin and Padmanabhan, Hamsa},
  journal = {Journal of Cosmology and Astroparticle Physics},
  volume = {2021},
  number = {11},
  pages = {009},
  year = {2021},
  eprint = {2106.05284},
  archivePrefix = {arXiv},
  primaryClass = {astro-ph.CO}
}

@article{Bashir2025CatWISEReassessment,
  title = {The CatWISE2020 Quasar dipole: A Reassessment of the Cosmic Dipole Anomaly},
  author = {Bashir, Masroor and Chingangbam, Pravabati and Appleby, Stephen},
  year = {2025},
  eprint = {2511.00822},
  archivePrefix = {arXiv},
  primaryClass = {astro-ph.CO}
}

@article{VonHausegger2025CatWISEClustering,
  title = {Clustering properties of the CatWISE2020 quasar catalogue and their impact on the cosmic dipole anomaly},
  author = {von Hausegger, Sebastian and Secrest, Nathan and Desmond, Harry and Rameez, Mohamed and Mohayaee, Roya and Sarkar, Subir},
  year = {2025},
  eprint = {2510.23769},
  archivePrefix = {arXiv},
  primaryClass = {astro-ph.CO}
}

@article{Martin2025TiltedAnisotropicDipole,
  title = {The Cosmological Dipole in Tilted Anisotropic Universes},
  author = {Martín, Alicia and Skordis, Constantinos and Bartlett, Deaglan J. and Desmond, Harry and Ferreira, Pedro G. and Yasin, Tariq},
  year = {2025},
  eprint = {2512.03867},
  archivePrefix = {arXiv},
  primaryClass = {astro-ph.CO}
}
```

Before committing, verify author names and journal metadata for final published versions with web or ADS; keep arXiv-only entries if journal metadata is not confirmed.

- [ ] **Step 8: Run manuscript and claim checks**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_publication_claim_freeze.py::test_manuscript_uses_revision_program_framing -q
venv/bin/python scripts/check_publication_claim_freeze.py --write
venv/bin/python scripts/pdf_claim_lint.py --tex-only
cd docs/manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Expected: framing test passes, claim freeze regenerates, claim lint has no new family/native promotion, and LaTeX builds.

- [ ] **Step 9: Commit**

Run:

```bash
git add docs/manuscript/ch01_introduction.tex docs/manuscript/ch02_dipole_anomaly.tex docs/manuscript/ch03_framework.tex docs/manuscript/ch07_results.tex docs/manuscript/ch08_robustness.tex docs/manuscript/ch09_discussion.tex docs/manuscript/ch10_future.tex docs/manuscript/generated/current_figures_results.tex docs/manuscript/references.bib tests/contracts/test_publication_claim_freeze.py docs/generated/publication_claim_freeze.md docs/generated/pdf_claim_lint_report.md docs/generated/claim_ledger.json
git commit -m "REV-R053: reframe manuscript claims"
```

### Task 6: Rebuild External Audit Packet and Close With Validation

**Files:**
- Modify: `scripts/build_research_only_audit_package.py`
- Modify generated:
  - `docs/generated/research_only_external_audit_package.zip`
  - `docs/generated/research_only_external_audit_package_manifest.json`
  - `docs/generated/research_only_external_audit_prompt.md`
  - `docs/generated/status_snapshot.json`
  - `docs/generated/status_matrix.md`

- [ ] **Step 1: Add final package expectations**

Append to `tests/contracts/test_audit_package_generator.py`:

```python
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_research_only_package_contains_revision_program_reports():
    manifest = json.loads(
        (ROOT / "docs/generated/research_only_external_audit_package_manifest.json").read_text()
    )
    paths = {entry["path"] for entry in manifest["included_files"]}
    required = {
        "docs/generated/revision_plan_crosswalk.md",
        "docs/generated/revision_novelty_ledger.md",
        "docs/generated/revision_claim_lanes.md",
        "docs/generated/revision_literature_crag.md",
        "docs/generated/revision_defense_dossier.md",
        "docs/audits/revision_program_2026-06-18/package_inventory.md",
        "docs/generated/revision_experiment_assets.md",
    }
    assert required <= paths
```

- [ ] **Step 2: Run the failing package expectation**

Run:

```bash
venv/bin/python -m pytest tests/contracts/test_audit_package_generator.py::test_research_only_package_contains_revision_program_reports -q
```

Expected: fails until the research-only package manifest includes the new files.

- [ ] **Step 3: Regenerate full revision outputs in order**

Run:

```bash
venv/bin/python scripts/inventory_revision_program_packages.py --write
venv/bin/python scripts/generate_revision_research_program.py --write
venv/bin/python scripts/generate_revision_experiment_assets.py --write
venv/bin/python scripts/check_publication_claim_freeze.py --write
venv/bin/python -m common.status_snapshot --write docs/generated/status_snapshot.json
venv/bin/python scripts/build_research_only_audit_package.py --write
```

Expected: all generated artifacts refresh without stale-check failures.

- [ ] **Step 4: Run focused validation suite**

Run:

```bash
venv/bin/python -m pytest \
  tests/contracts/test_revision_program_inventory.py \
  tests/contracts/test_revision_research_program.py \
  tests/contracts/test_revision_experiment_assets.py \
  tests/contracts/test_audit_package_generator.py \
  tests/contracts/test_publication_claim_freeze.py \
  tests/contracts/test_status_snapshot.py \
  -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Run broad smoke collection**

Run:

```bash
venv/bin/python -m pytest -m smoke -q
venv/bin/python -m pytest --collect-only -q
```

Expected: smoke passes; collection completes. If unrelated failures exist, record exact failing test node, error, and why it is outside this revision slice.

- [ ] **Step 6: Commit**

Run:

```bash
git add scripts/build_research_only_audit_package.py tests/contracts/test_audit_package_generator.py docs/generated/research_only_external_audit_package.zip docs/generated/research_only_external_audit_package_manifest.json docs/generated/research_only_external_audit_prompt.md docs/generated/status_snapshot.json docs/generated/status_matrix.md
git commit -m "REV-R061: rebuild research audit packet"
```

## Verification Checklist

- [ ] `venv/bin/python scripts/inventory_revision_program_packages.py --check`
- [ ] `venv/bin/python scripts/generate_revision_research_program.py --check`
- [ ] `venv/bin/python scripts/generate_revision_experiment_assets.py --check`
- [ ] `venv/bin/python scripts/build_research_only_audit_package.py --check`
- [ ] `venv/bin/python scripts/check_publication_claim_freeze.py --write`
- [ ] `venv/bin/python scripts/pdf_claim_lint.py --tex-only`
- [ ] `venv/bin/python -m pytest tests/contracts/test_revision_program_inventory.py tests/contracts/test_revision_research_program.py tests/contracts/test_revision_experiment_assets.py -q`
- [ ] `venv/bin/python -m pytest -m smoke -q`
- [ ] `venv/bin/python -m pytest --collect-only -q`
- [ ] `cd docs/manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`

## Claim Boundaries

- Use `claim-tiered framework`, `transfer-conditional`, `diagnostic-only`, `conditional on the dipole premise`, `forecast`, and `family identification remains blocked`.
- Do not label external/proxy transfer as native.
- Do not use scalar `x/Q/F/G/G_F` or occupancy vectors as morphology or family evidence.
- Do not let MIO diagnostics carry HTT posterior or evidence semantics.
- Do not promote scaffold package outputs unless regenerated from repo-local scripts with manifests.

## Execution Order

1. Task 1 records and freezes the input packages.
2. Task 2 creates the upgraded research plan artifacts and supplemental R-DAG.
3. Task 3 propagates existing artifact lanes through manifests and audit packages.
4. Task 4 generates conservative diagnostic assets with manifests.
5. Task 5 reframes the manuscript after generated assets exist.
6. Task 6 rebuilds the external research-audit packet and validates the slice.
