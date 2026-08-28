"""Contract for retiring pre-current publication and audit surfaces."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = "0864b00948143d9b19d4983e50fcd2d905f4a5d3"

REMOVED_ROOTS = (
    "figures",
    "docs/manuscript",
    "docs/code_capability_audit",
    "docs/superpowers/plans",
    "external_audit_research_report_20260707_v5",
    "external_audit_research_report_20260721_v10",
    "external_audit_research_report_20260722_v11",
)

REMOVED_FILES = (
    "00_start_full_dag_automation_prompt.md",
    "10_re_review_v8_ko.md",
    "PRE_MANUSCRIPT_STAGE2B5_v0_9_1.pdf",
    "docs/P1_main.pdf",
    "docs/P2_main.pdf",
    "docs/P3_main.pdf",
    "docs/P4_main.pdf",
    "docs/P5_main.pdf",
    "docs/stat_audit.txt",
    "external_audit_research_report_20260707_v5.zip",
    "external_audit_research_report_20260721_v10.zip",
    "external_audit_research_report_20260722_v11.zip",
    "external_audit_research_report_v5.pdf",
    "external_audit_research_report_v10.pdf",
    "external_audit_research_report_v11.pdf",
    "fix.md",
    "htt_base_research_evaluation_prompt.md",
    "htt_base_research_evaluation_package_manifest.json",
    "v5_residual_harmonic_algebraic_audit.md",
    "v5_residual_harmonic_algebraic_audit_round2.md",
    "v5_residual_harmonic_algebraic_audit_round3.md",
    "v5_residual_harmonic_algebraic_audit_round4.md",
    "v5_residual_harmonic_algebraic_audit_round5.md",
)

REMOVED_DEDICATED_CODE = (
    "scripts/audit_manuscript_figures.py",
    "scripts/audits/jcap_prd_20260714.py",
    "scripts/build_expanded_manuscript_figure_suite.py",
    "scripts/build_external_audit_package.py",
    "scripts/build_external_audit_report_v5.py",
    "scripts/build_external_audit_report_v6.py",
    "scripts/build_external_audit_report_v7.py",
    "scripts/build_external_audit_report_v8.py",
    "scripts/build_external_audit_report_v9.py",
    "scripts/build_external_audit_report_v10.py",
    "scripts/build_external_audit_report_v11.py",
    "scripts/build_final_report_audit_package.py",
    "scripts/build_pr04_research_audit_package.py",
    "scripts/build_research_evaluation_package.py",
    "scripts/build_research_only_audit_package.py",
    "scripts/build_statistical_formalism_audit_package.py",
    "scripts/build_v6_compact_data_analysis.py",
    "scripts/build_v6_no_download_research_cards.py",
    "scripts/build_v7_external_audit_synthesis.py",
    "scripts/build_v7_paper_a_revision_packet.py",
    "scripts/codex_harness/build_claim_evidence_graph.py",
    "scripts/codex_harness/quarantine_cf4_p0_consumers.py",
    "scripts/codex_harness/run_pr179_directional_cosmography.py",
    "scripts/codex_harness/run_pr122_source_only.sh",
    "scripts/check_publication_claim_freeze.py",
    "scripts/curate_current_manuscript_figures.py",
    "scripts/curate_figure_lanes.py",
    "scripts/generate_manuscript_status_snippets.py",
    "scripts/generate_theorem_extension_assets.py",
    "scripts/inventory_external_research_inputs.py",
    "scripts/inventory_revision_program_packages.py",
    "scripts/build_open_items_ledger.py",
    "scripts/make_additional_figures.py",
    "scripts/make_blocker_discharge_figures.py",
    "scripts/make_current_manuscript_figures.py",
    "scripts/make_data_proxy_coordinates_figure.py",
    "scripts/make_manuscript_figures.py",
    "scripts/make_more_figures.py",
    "scripts/make_obsdata_r195_r198_figures.py",
    "scripts/make_observed_data_manuscript_figures.py",
    "scripts/make_paper_figures.py",
    "scripts/make_parallel_track_figures.py",
    "scripts/make_physics_gallery.py",
    "scripts/make_pr04_paper_figures.py",
    "scripts/make_preliminary_figures.py",
    "scripts/make_report_data_analysis_figures.py",
    "scripts/make_third_wave_figures.py",
    "scripts/make_v6_no_download_figures.py",
    "scripts/pdf_claim_lint.py",
    "scripts/reproduce_cf4pp_lnb.py",
    "scripts/v10_report_data_figures.py",
    "tests/contracts/test_audit_package_generator.py",
    "tests/contracts/test_audit_ver2_claim_firewall.py",
    "tests/contracts/test_audit_ver2_response_matrix.py",
    "tests/contracts/test_blocker_discharge_figure.py",
    "tests/contracts/test_current_manuscript_figures.py",
    "tests/contracts/test_expanded_manuscript_figure_suite.py",
    "tests/contracts/test_external_audit_report_v9.py",
    "tests/contracts/test_external_audit_report_v10.py",
    "tests/contracts/test_external_audit_report_v11.py",
    "tests/contracts/test_external_research_input_inventory.py",
    "tests/contracts/test_final_report_audit_package.py",
    "tests/contracts/test_formalism_figure_labels.py",
    "tests/contracts/test_generated_status_counts.py",
    "tests/contracts/test_code_capability_audit_package.py",
    "tests/contracts/test_jcap_prd_adversarial_audit.py",
    "tests/contracts/test_manuscript_audit_repair_matrix.py",
    "tests/contracts/test_manuscript_cf4_quarantine.py",
    "tests/contracts/test_manuscript_figure_audit.py",
    "tests/contracts/test_manuscript_rearchitecture.py",
    "tests/contracts/test_obsdata_figures.py",
    "tests/contracts/test_observed_data_figures.py",
    "tests/contracts/test_pdf_claim_lint.py",
    "tests/contracts/test_pr04_research_audit_package.py",
    "tests/contracts/test_publication_claim_freeze.py",
    "tests/contracts/test_cf4pp_lnb_provenance.py",
    "tests/contracts/test_report_data_figure_lanes.py",
    "tests/contracts/test_research_evaluation_package.py",
    "tests/contracts/test_research_only_audit_package.py",
    "tests/contracts/test_revision_experiment_assets.py",
    "tests/contracts/test_revision_program_inventory.py",
    "tests/contracts/test_open_items_ledger.py",
    "tests/contracts/test_theorem_extension_assets.py",
    "tests/contracts/test_statistical_formalism_audit_package.py",
    "tests/contracts/test_v6_no_download_figure_pack.py",
    "tests/contracts/test_v6_no_download_research_cards.py",
    "tests/contracts/test_v7_paper_a_hardening.py",
    "htt/bass/observer/test_fb87_docs_gallery_skeleton.py",
    "htt/bass/inference/test_fb117_docs_gallery_skeleton.py",
    "htt/bass/species/test_fb96_docs_gallery_skeleton.py",
    "tests/obsstat/test_cf4_raw_catalog.py",
    "scripts/build_code_capability_audit_package.py",
    "tests/pr_cards/test_pr_122_claim_addressed_evidence_graph_content_addressed.py",
    "tests/pr_cards/test_pr_179_reconstruction_independent_directional_cosmograp.py",
)

AUDIT_EVIDENCE_PREFIXES = (
    "docs/audits/mes_primary_sources/",
    "docs/audits/pr124_d2_authority/",
    "docs/audits/pr170_primary_sources/",
    "docs/audits/pr171_primary_sources/",
    "docs/audits/pr176_primary_sources/",
)

PRESERVED_CURRENT_FILES = (
    "papers/planck_mes_first_observation/main.tex",
    "docs/generated/planck_mes_first_paper/analysis_summary.json",
    "docs/generated/planck_mes_coordinate_audit/result.json",
    "docs/generated/planck_mes_irrep_formalism/wu002_terminal.json",
    "docs/generated/planck_mes_irrep_inventory/terminal.json",
    "docs/generated/planck_mes_morphology/planck_mes_morphology.npz",
    "docs/generated/pr314_planck_pr3_smica_existing_result.json",
    "docs/generated/pr315_planck_smica_feature_replay.npz",
    "docs/generated/pr124_cas_adjudication.json",
    "docs/generated/pr124_d2_authority_receipt.json",
    "docs/generated/pr124_lineage_receipt.json",
    "docs/generated/pr124_theorem_inventory.json",
)

PR124_MES_AUTHORITY_FILES = frozenset(
    {
        "docs/generated/pr124_cas_adjudication.json",
        "docs/generated/pr124_d2_authority_receipt.json",
        "docs/generated/pr124_lineage_receipt.json",
        "docs/generated/pr124_theorem_inventory.json",
    }
)

CURRENT_DAG_AUTHORITY_FILES = frozenset(
    {"docs/generated/pr167_pre_intake_semantic_receipt.json"}
)

LEDGER = "docs/research_program/long_horizon_rescue/cf4_p0_legacy_package_hashes.json"


def _git(*args: str, text: bool = True) -> str | bytes:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=text,
    ).stdout


def _tracked(prefix: str) -> list[str]:
    return _git("ls-files", prefix).splitlines()


def _keep_generated(path: str) -> bool:
    name = path.split("/")[2]
    return (
        path in PR124_MES_AUTHORITY_FILES
        or path in CURRENT_DAG_AUTHORITY_FILES
        or name.startswith(
            (
                "mes_",
                "mesb_",
                "planck_",
                "pr122_mes_",
                "pr124_mes_",
                "pr306_planck_",
                "pr314_planck_",
                "pr315_planck_",
                "pr321_hsc_sacc_",
            )
        )
        or path.startswith(
            "docs/generated/pr124_cas/CAS_CONTRACT_PR124_MES_"
        )
        or any(
            path.startswith(f"docs/generated/pr{number}_")
            for number in range(254, 259)
        )
    )


def test_legacy_publication_surfaces_are_absent() -> None:
    for relative in (
        *REMOVED_ROOTS,
        *REMOVED_FILES,
        *REMOVED_DEDICATED_CODE,
    ):
        assert not (ROOT / relative).exists(), relative


def test_only_registered_primary_receipts_remain_under_audits() -> None:
    survivors = _tracked("docs/audits")
    assert survivors
    assert all(path.startswith(AUDIT_EVIDENCE_PREFIXES) for path in survivors)


def test_generated_tree_contains_only_current_mes_planck_allowlist() -> None:
    survivors = _tracked("docs/generated")
    assert survivors
    rejected = [path for path in survivors if not _keep_generated(path)]
    assert rejected == []


def test_current_planck_mes_artifacts_remain_and_legacy_is_recoverable() -> None:
    for relative in PRESERVED_CURRENT_FILES:
        assert (ROOT / relative).is_file(), relative

    for relative in CURRENT_DAG_AUTHORITY_FILES:
        assert (ROOT / relative).read_bytes() == _git(
            "show", f"{BASE}:{relative}", text=False
        )

    for relative in (
        "PRE_MANUSCRIPT_STAGE2B5_v0_9_1.pdf",
        "figures/parallel_track/README.md",
        "docs/manuscript/main.tex",
    ):
        _git("cat-file", "-e", f"{BASE}:{relative}")

    current_ledger = (ROOT / LEDGER).read_bytes()
    base_ledger = _git("show", f"{BASE}:{LEDGER}", text=False)
    assert current_ledger == base_ledger
