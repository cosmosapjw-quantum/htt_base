#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {
    "crosswalk": ROOT / "docs/generated/revision_plan_crosswalk.md",
    "novelty": ROOT / "docs/generated/revision_novelty_ledger.md",
    "lanes": ROOT / "docs/generated/revision_claim_lanes.md",
    "literature": ROOT / "docs/generated/revision_literature_crag.md",
    "defense": ROOT / "docs/generated/revision_defense_dossier.md",
    "dag": ROOT / "docs/codex_handoff/pr_dag_revision.yaml",
}

CAVEATS = [
    "external/proxy transfer is not native transfer",
    "family identification remains blocked until native morphology atlas support exists",
    "scaffold package outputs are not publication evidence",
]

NOVELTY = [
    (
        "N1",
        "exact",
        "Signed comparator coordinate for shear, vorticity, tilt, and anisotropic curvature.",
        "C1/C2 algebraic framework wording only.",
    ),
    (
        "N2",
        "supported",
        "Matter-sector departure framing addresses the almost-EGS loophole without detection language.",
        "Literature-positioned framework claim.",
    ),
    (
        "N3",
        "conditional",
        "Dipole-conditioned mapping to observational equivalence classes; family identification remains blocked.",
        "Requires premise and transfer caveat boxes.",
    ),
    (
        "N4",
        "supported",
        "Species-resolved effective-temperature closure with explicit representation caveats.",
        "Legacy TSC/Teff material remains reproducibility support.",
    ),
    (
        "N5",
        "exact",
        "Claim-tiered provenance methodology for contested-anomaly reporting.",
        "COMMON owns metadata and artifact promotion rules.",
    ),
    (
        "N6",
        "supported",
        "Per-channel occupancy vector with channel-matched denominators.",
        "Diagnostic-only MIO-style scalar packaging.",
    ),
    (
        "N7",
        "forecast",
        "Tomographic local-boost versus global-tilt separation forecast.",
        "Future experiment design, not current discrimination proof.",
    ),
]

EXPERIMENTS = [
    (
        "E1",
        "Prior floor and ceiling sensitivity surface plus fractional/intrinsic Bayes factor.",
        "HTT",
        "conditional candidate only after prior/null/PPC status exists.",
    ),
    (
        "E2",
        "Bulk-flow sigma-beta uncertainty band plus look-elsewhere correction.",
        "HTT",
        "conditional on external/proxy transfer provenance.",
    ),
    (
        "E3",
        "Per-channel occupancy vector across model rows.",
        "MIO",
        "diagnostic_only; no posterior or truth language.",
    ),
    (
        "E4",
        "Deterministic quadrupole template likelihood versus stochastic covariance treatment.",
        "HTT",
        "requires matched covariance/null status before evidence wording.",
    ),
    (
        "E5",
        "Tomographic degeneracy-breaking forecast for local boost and global tilt.",
        "HTT/obsstat",
        "forecast lane only.",
    ),
    (
        "E6",
        "Posterior-predictive and LOOCV adequacy checks for any evidence-grade HTT wording.",
        "HTT",
        "blocks promotion until passed.",
    ),
    (
        "E7",
        "Cross-survey covariance model for shared clustering-dipole uncertainty.",
        "obsstat/HTT",
        "conditional on covariance implementation.",
    ),
    (
        "E8",
        "Native low-ell morphology atlas roadmap only; no implementation in this repo state.",
        "BASS_native",
        "specified future interface; no native-transfer claim.",
    ),
]

PR_ROWS = [
    ("PR-R000", "Promotion-model audit over existing ArtifactMode and AllowedUse", []),
    ("PR-R001", "Status snapshot lane propagation", ["PR-R000"]),
    ("PR-R002", "Figure manifest lane and forbidden-use fields", ["PR-R000"]),
    ("PR-R003", "PDF-level claim lint integration", ["PR-R001"]),
    ("PR-R004", "Revision claim freeze rows for safe framework wording", ["PR-R001", "PR-R003"]),
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
    lines = [
        f"# {title}",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        "caveats:",
    ]
    lines.extend(f"- {caveat}" for caveat in CAVEATS)
    lines.extend(["", ""])
    return lines


def render_novelty() -> str:
    lines = metadata("Revision Novelty Ledger")
    lines.extend(
        [
            "| ID | Tier | Safe statement | Promotion guard |",
            "| --- | --- | --- | --- |",
        ]
    )
    for ident, tier, statement, guard in NOVELTY:
        lines.append(f"| {ident} | {tier} | {statement} | {guard} |")
    lines.extend(
        [
            "",
            "Tier vocabulary: exact/supported/conditional/forecast.",
            "Promotion rule: exact and supported claims can enter framework text; conditional claims require premise boxes; forecast claims require forecast labels.",
            "",
        ]
    )
    return "\n".join(lines)


def render_lanes() -> str:
    lines = metadata("Revision Claim Lanes")
    lines.extend(
        [
            "| Lane | Allowed use | Forbidden use |",
            "| --- | --- | --- |",
            "| `blocked/governance_diagnostic/internal_only` | gate failure reports | evidence, odds-based inference claims, paper claims |",
            "| `diagnostic_only/external_audit_conditioned/external_audit` | external audit diagnostics | paper-main inference or family use |",
            "| `diagnostic_only/paper_appendix_conditioned/paper_appendix` | caveated diagnostic plots | validated evidence wording |",
            "| `conditional/paper_appendix_conditioned/paper_appendix` | transfer-conditional summaries | native or geometry wording |",
            "| `conditional/paper_main_candidate/paper_main` | caveat-box framework or forecast figures | claim without premise/null/covariance status |",
            "| `validated/paper_main_validated/paper_main` | future native-validated results | unavailable in current repo state |",
            "",
            "Caption rule: every promoted figure states claim lane, transfer source, null status, and forbidden-use sentence.",
            "Supplemental DAG rule: `docs/codex_handoff/pr_dag_revision.yaml` is proposed only and must not overwrite `docs/codex_handoff/pr_status.yaml`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_crosswalk() -> str:
    lines = metadata("Revision Plan Crosswalk")
    lines.extend(["## Relation To Existing Plan", ""])
    lines.append(
        "The conservative repair plan clears external-audit rejection triggers. This upgrade adds novelty preservation, experiment staging, literature CRAG, and a supplemental R-DAG."
    )
    lines.extend(
        [
            "",
            "## Novelty To Experiment Map",
            "",
            "| Novelty | Experiments | Manuscript home |",
            "| --- | --- | --- |",
        ]
    )
    rows = [
        ("N1", "E3", "Chapter 3 framework and Chapter 7 occupancy repair"),
        ("N2", "literature CRAG", "Introduction and discussion"),
        ("N3", "E2,E7,E8 roadmap", "Dipole anomaly and results caveat boxes"),
        ("N4", "conservative-plan closure correction", "Chapter 5"),
        ("N5", "claim lanes and audit package", "Methods and appendices"),
        ("N6", "E3", "Results and appendix table"),
        ("N7", "E5", "Future and forecast results"),
    ]
    for novelty, experiments, home in rows:
        lines.append(f"| {novelty} | {experiments} | {home} |")

    lines.extend(["", "## Experiment List", ""])
    for ident, description, owner, guard in EXPERIMENTS:
        lines.append(f"- {ident}: {description} Owner: {owner}. Guard: {guard}")

    lines.extend(["", "## Supplemental PR Slice", ""])
    for ident, title, depends in PR_ROWS:
        dep_text = ", ".join(depends) if depends else "none"
        lines.append(f"- {ident}: {title}; depends: {dep_text}; status: proposed")

    lines.extend(["", "Supplemental row count: 29 proposed PR rows spanning PR-R000 through PR-R062.", ""])
    return "\n".join(lines)


def render_literature() -> str:
    lines = metadata("Revision Literature CRAG")
    lines.extend(
        [
            "| Source | Use in revision | Status |",
            "| --- | --- | --- |",
            "| `arXiv:2505.23526` / Rev. Mod. Phys. dipole colloquium | cosmic dipole anomaly context | recorded CRAG snapshot; refresh before citation edit |",
            "| PRL 135, 201001 | independent radio source-count dipole context | recorded CRAG snapshot; refresh before citation edit |",
            "| MNRAS 526, 3051 | CF4 bulk-flow uncertainty caveat | recorded CRAG snapshot; refresh before citation edit |",
            "| `arXiv:2106.05284` | survey/tomographic separation motivation | recorded CRAG snapshot; refresh before citation edit |",
            "| `astro-ph/9904252` | almost-EGS loophole support | recorded CRAG snapshot; refresh before citation edit |",
            "| `arXiv:2510.23769` | CatWISE clustering systematic context | recorded CRAG snapshot; refresh before citation edit |",
            "| `arXiv:2511.00822` | CatWISE reassessment context | recorded CRAG snapshot; refresh before citation edit |",
            "| `arXiv:2512.03867` | tilted anisotropic universe competitor/constraint | recorded CRAG snapshot; refresh before citation edit |",
            "",
            "CRAG rule: every current-literature claim must be checked against the latest arXiv/journal version before manuscript citation is updated.",
            "",
        ]
    )
    return "\n".join(lines)


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
    lines.append("")
    return "\n".join(lines)


def render_dag() -> str:
    lines = [
        "schema_version: htt.pr_dag_revision.v1",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        "status_surface: proposed_only",
        "does_not_overwrite: docs/codex_handoff/pr_status.yaml",
        "caveats:",
    ]
    lines.extend(f"  - {json.dumps(caveat)}" for caveat in CAVEATS)
    lines.append("prs:")
    for ident, title, depends in PR_ROWS:
        lines.append(f"  - id: {json.dumps(ident)}")
        lines.append(f"    title: {json.dumps(title)}")
        lines.append(f"    depends: {json.dumps(depends)}")
        lines.append('    status: "proposed"')
    lines.append("")
    return "\n".join(lines)


RENDERERS = {
    "crosswalk": render_crosswalk,
    "novelty": render_novelty,
    "lanes": render_lanes,
    "literature": render_literature,
    "defense": render_defense,
    "dag": render_dag,
}


def expected_outputs() -> dict[str, str]:
    return {key: RENDERERS[key]() for key in OUTPUTS}


def write_outputs(outputs: dict[str, str]) -> None:
    for key, text in outputs.items():
        path = OUTPUTS[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def check_outputs(outputs: dict[str, str]) -> int:
    for key, text in outputs.items():
        path = OUTPUTS[key]
        if not path.exists():
            print(f"missing generated file: {path}", file=sys.stderr)
            return 1
        if path.read_text() != text:
            print(f"stale generated file: {path}", file=sys.stderr)
            return 1
    return 0


def print_report(outputs: dict[str, str]) -> None:
    for key, text in outputs.items():
        print(f"===== {OUTPUTS[key].relative_to(ROOT)} =====")
        print(text, end="")
        if not text.endswith("\n"):
            print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")

    outputs = expected_outputs()
    if args.write:
        write_outputs(outputs)
        return 0
    if args.check:
        return check_outputs(outputs)
    print_report(outputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
