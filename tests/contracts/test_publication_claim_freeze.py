import importlib.util
import json
from pathlib import Path
import subprocess

from common.artifact_manifest import validate_manifest_payload
from common.release_evidence_binding import DEFAULT_RELEASE_EVIDENCE_PIN


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/check_publication_claim_freeze.py"
SOURCE_ONLY_LAUNCHER = REPO_ROOT / "scripts/codex_harness/run_pr122_source_only.sh"
SOURCE_ONLY_TARGET = "scripts/check_publication_claim_freeze.py"
CLAIM_EVIDENCE_INPUTS = {
    "docs/generated/pr122_claim_evidence_graph.json",
    "docs/generated/pr122_claim_closure_report.json",
    "docs/generated/pr122_claim_closure_report.md",
    "docs/generated/pr122_release_receipt.json",
    "docs/generated/pr122_parent_receipt.json",
    "docs/generated/pr122_artifact_manifest.json",
    "docs/generated/pr122_mes_successor_scan.json",
    "docs/generated/pr122_test_execution.json",
}


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "publication_claim_freeze", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cli(*args: str) -> list[str]:
    return [str(SOURCE_ONLY_LAUNCHER), SOURCE_ONLY_TARGET, *args]


def _payload():
    module = _load_module()
    return module.build_publication_claim_freeze_payload(
        repo_root=REPO_ROOT,
        freeze_output=Path("docs/generated/publication_claim_freeze.md"),
        matrix_output=Path("docs/generated/hostile_review_response_matrix.md"),
        generating_command="python scripts/check_publication_claim_freeze.py --dry-run",
        worktree_state="test-worktree",
    )


def _assert_no_forbidden_language(text: str) -> None:
    lowered = text.lower()
    assert ("mio " + "posterior") not in lowered
    assert ("posterior " + "odds") not in lowered
    assert ("truth " + "certificate") not in lowered
    assert ("native " + "solver result") not in lowered
    assert ("family " + "identified") not in lowered
    assert ("geometry " + "detected") not in lowered
    assert ("external transfer " + "validated " + "as native") not in lowered


def test_payload_maps_public_claims_to_artifacts_tests_caveats_and_owner():
    payload = _payload()

    assert payload["owner"] == "COMMON"
    assert payload["implementation_scope"] == "common"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert (
        validate_manifest_payload(
            payload,
            manifest_path="memory://publication_claim_freeze.md",
            expected_artifact_path="docs/generated/publication_claim_freeze.md",
        )
        == ()
    )

    assertions = payload["required_assertions"]
    assert assertions["all_claims_have_owner"] is True
    assert assertions["all_claims_have_artifacts"] is True
    assert assertions["all_claim_artifacts_exist"] is True
    assert assertions["all_claims_have_manifest_refs"] is True
    assert assertions["all_manifest_refs_exist"] is True
    assert assertions["all_claims_have_tests"] is True
    assert assertions["all_claims_have_caveats"] is True
    assert assertions["claim_ledger_included"] is True
    assert assertions["transfer_provenance_included"] is True
    assert assertions["external_audit_package_included"] is True
    assert assertions["pdf_claim_lint_passed"] is False
    assert assertions["manuscript_blockers_recorded"] is True
    assert assertions["no_current_manuscript_pdf_recorded"] is True
    assert assertions["manuscript_source_quarantine_enforced"] is True
    assert assertions["no_forbidden_claim_language"] is True
    assert assertions["no_c5_c6_family_id_claim"] is True
    assert assertions["cf4_p0_quarantine_clean"] is True
    assert assertions["exact_claim_evidence_receipt_consumed"] is True
    assert assertions["claim_release_blocked_by_evidence_graph"] is True
    assert payload["cf4_p0_quarantine"]["ok"] is True
    assert payload["cf4_p0_quarantine"]["issues"] == []
    assert payload["failed_gates"] == ["pdf_claim_lint_passed"]
    assert payload["submission_decision"] == "blocked_cf4_p0_manuscript_quarantine"
    assert payload["manuscript_blockers"]["current_pdf_present"] is False
    assert payload["manuscript_blockers"]["source_quarantine_enforced"] is True

    evidence = payload["claim_evidence_receipt"]
    pin = DEFAULT_RELEASE_EVIDENCE_PIN
    assert evidence["mode"] == "audit_disclosure"
    assert evidence["graph_path"] == pin.graph_path
    assert evidence["graph_file_sha256"] == pin.graph_file_sha256
    assert evidence["graph_ref"] == pin.graph_ref
    assert evidence["receipt_path"] == pin.receipt_path
    assert evidence["receipt_file_sha256"] == pin.receipt_file_sha256
    assert evidence["receipt_id"] == pin.receipt_id
    assert evidence["parent_receipt_id"] == pin.parent_receipt_id
    assert evidence["receipt_version"] == "claim_evidence_receipt_v2"
    assert evidence["closure_path"] == pin.closure_path
    assert evidence["closure_file_sha256"] == pin.closure_file_sha256
    assert evidence["artifact_manifest_file_sha256"] == (
        pin.artifact_manifest_file_sha256
    )
    assert evidence["authority_registry_ref"] == pin.authority_registry_ref
    assert evidence["process_result"] == "PASS"
    assert evidence["evidence_status"] == "BLOCKED"
    assert evidence["scientific_status"] == "OPEN"
    assert evidence["authority_status"] == "REQUIRES_TRUSTED_REGISTRY_VALIDATION"
    assert evidence["claim_release_allowed"] is False
    assert evidence["audit_disclosure_allowed"] is True

    hashed_input_paths = {
        item.partition(":sha256:")[0] for item in payload["input_hashes"]
    }
    assert CLAIM_EVIDENCE_INPUTS <= set(_load_module().DEFAULT_REQUIRED_INPUTS)
    assert CLAIM_EVIDENCE_INPUTS <= hashed_input_paths

    for claim in payload["public_claims"]:
        assert claim["owner"]
        assert claim["artifacts"]
        assert claim["manifest_refs"]
        assert claim["tests"]
        assert claim["caveats"]
    assert not any(
        item.startswith("docs/generated/external_audit_package_manifest.json:")
        for item in payload["input_hashes"]
    )
    _assert_no_forbidden_language(json.dumps(payload["public_claims"], sort_keys=True))


def test_dry_run_does_not_write_reports(tmp_path: Path):
    module = _load_module()
    freeze_output = tmp_path / "freeze.md"
    matrix_output = tmp_path / "matrix.md"

    result = subprocess.run(
        _cli(
            "--dry-run",
            "--freeze-output",
            str(freeze_output),
            "--matrix-output",
            str(matrix_output),
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "DRY-RUN" in result.stdout
    expected = module.build_publication_claim_freeze_payload(
        repo_root=REPO_ROOT,
        freeze_output=freeze_output,
        matrix_output=matrix_output,
        generating_command="python scripts/check_publication_claim_freeze.py --dry-run",
        worktree_state=module._git_state(REPO_ROOT),
    )["submission_decision"]
    assert f"submission_decision={expected}" in result.stdout
    assert "no_c5_c6_family_id_claim=True" in result.stdout
    assert not freeze_output.exists()
    assert not matrix_output.exists()


def test_write_and_check_reports(tmp_path: Path):
    module = _load_module()
    freeze_output = tmp_path / "freeze.md"
    matrix_output = tmp_path / "matrix.md"

    write = subprocess.run(
        _cli(
            "--freeze-output",
            str(freeze_output),
            "--matrix-output",
            str(matrix_output),
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert write.returncode == 1
    assert freeze_output.exists()
    assert matrix_output.exists()
    freeze_text = freeze_output.read_text(encoding="utf-8")
    matrix_text = matrix_output.read_text(encoding="utf-8")
    assert "# Publication Claim Freeze" in freeze_text
    assert "# Hostile Review Response Matrix" in matrix_text
    payload = module.build_publication_claim_freeze_payload(
        repo_root=REPO_ROOT,
        freeze_output=freeze_output,
        matrix_output=matrix_output,
        generating_command="python scripts/check_publication_claim_freeze.py --dry-run",
        worktree_state=module._git_state(REPO_ROOT),
    )
    assert f"Submission decision: `{payload['submission_decision']}`" in freeze_text
    blockers = payload["manuscript_blockers"]
    assert "Current manuscript PDF present | False" in freeze_text
    assert "CF4 P0 source quarantine enforced | True" in freeze_text
    assert "PDF claim lint | blocked, not passed" in freeze_text
    evidence = payload["claim_evidence_receipt"]
    assert (
        f"BLOCKED audit-disclosure evidence receipt: `{evidence['receipt_id']}`"
        in freeze_text
    )
    assert (
        "Claim release from that receipt: `blocked`; audit disclosure only."
        in freeze_text
    )
    assert "| `exact_claim_evidence_receipt_consumed` | `True` |" in freeze_text
    assert "| `claim_release_blocked_by_evidence_graph` | `True` |" in freeze_text
    for path in CLAIM_EVIDENCE_INPUTS:
        assert f"- {path}:sha256:" in freeze_text
        assert f"- {path}:sha256:" in matrix_text
    if blockers["missing_refs"] == 0:
        assert "Missing figure refs" not in freeze_text
    if blockers["quarantined_refs"] == 0:
        assert "Quarantined figure refs" not in freeze_text
    _assert_no_forbidden_language(freeze_text + "\n" + matrix_text)

    fresh = subprocess.run(
        _cli(
            "--check",
            "--freeze-output",
            str(freeze_output),
            "--matrix-output",
            str(matrix_output),
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert fresh.returncode == 1
    assert "up-to-date" in fresh.stdout

    matrix_output.write_text(matrix_text + "\n", encoding="utf-8")
    stale = subprocess.run(
        _cli(
            "--check",
            "--freeze-output",
            str(freeze_output),
            "--matrix-output",
            str(matrix_output),
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert stale.returncode == 1
    assert "stale hostile review response matrix" in stale.stdout


def test_c5_c6_family_identification_fails_before_native_atlas():
    module = _load_module()
    bad_claim = {
        **module.PUBLIC_CLAIMS[0],
        "claim_id": "bad.c6",
        "claim_tier": "C6",
        "statement": "Bianchi geometry " + "detected by the scalar summary",
        "allowed_phrase": "Bianchi family " + "identification",
    }

    payload = module.build_publication_claim_freeze_payload(
        repo_root=REPO_ROOT,
        freeze_output=Path("docs/generated/publication_claim_freeze.md"),
        matrix_output=Path("docs/generated/hostile_review_response_matrix.md"),
        generating_command="python scripts/check_publication_claim_freeze.py --dry-run",
        public_claims=[bad_claim],
        hostile_review_rows=module.HOSTILE_REVIEW_ROWS,
        worktree_state="test-worktree",
    )

    assert payload["required_assertions"]["no_forbidden_claim_language"] is False
    assert payload["required_assertions"]["no_c5_c6_family_id_claim"] is False
    assert "no_forbidden_claim_language" in payload["failed_gates"]
    assert "no_c5_c6_family_id_claim" in payload["failed_gates"]
    assert payload["family_id_violations"][0]["claim_id"] == "bad.c6"


def test_transfer_conditional_c5_morphology_compatibility_can_pass():
    module = _load_module()
    claim = {
        **module.PUBLIC_CLAIMS[0],
        "claim_id": "ok.c5.compatibility",
        "claim_tier": "C5",
        "statement": "transfer-conditional morphology compatibility workflow remains blocked from identification",
        "allowed_phrase": "morphology compatibility candidate",
        "caveats": [
            "Family identification remains blocked.",
            "Transfer source is AniCLASS_external and not native validation.",
        ],
    }

    payload = module.build_publication_claim_freeze_payload(
        repo_root=REPO_ROOT,
        freeze_output=Path("docs/generated/publication_claim_freeze.md"),
        matrix_output=Path("docs/generated/hostile_review_response_matrix.md"),
        generating_command="python scripts/check_publication_claim_freeze.py --dry-run",
        public_claims=[claim],
        hostile_review_rows=module.HOSTILE_REVIEW_ROWS,
        worktree_state="test-worktree",
    )

    assert payload["required_assertions"]["no_forbidden_claim_language"] is True
    assert payload["required_assertions"]["no_c5_c6_family_id_claim"] is True
    assert payload["family_id_violations"] == []


def test_manuscript_uses_revision_program_framing():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            REPO_ROOT / "docs/manuscript/ch01_introduction.tex",
            REPO_ROOT / "docs/manuscript/ch02_dipole_anomaly.tex",
            REPO_ROOT / "docs/manuscript/ch07_results.tex",
            REPO_ROOT / "docs/manuscript/ch09_discussion.tex",
            REPO_ROOT / "docs/manuscript/ch10_future.tex",
        ]
    )
    assert "claim-tiered framework" in combined
    assert "transfer-conditional" in combined
    assert "conditional on the dipole premise" in combined
    assert "family-ID remains blocked" in combined
    assert "tomographic" in combined
    assert "prior-support sensitivity" in combined


def test_missing_required_input_fails_closed(tmp_path: Path):
    module = _load_module()
    missing = "docs/generated/does_not_exist.json"

    try:
        module.build_publication_claim_freeze_payload(
            repo_root=REPO_ROOT,
            freeze_output=tmp_path / "freeze.md",
            matrix_output=tmp_path / "matrix.md",
            generating_command="python scripts/check_publication_claim_freeze.py --dry-run",
            required_inputs=[missing],
            worktree_state="test-worktree",
        )
    except FileNotFoundError as exc:
        assert missing in str(exc)
    else:
        raise AssertionError("missing required input did not fail closed")


def test_manuscript_source_quarantine_is_primitive_and_current_pdf_is_absent():
    module = _load_module()
    source = (REPO_ROOT / module.MANUSCRIPT_SOURCE).read_text(encoding="utf-8")

    assert module._manuscript_source_quarantine_enforced(REPO_ROOT) is True
    assert source.index(
        r"\ifcsname HTTCF4PZeroLegacyReproduction\endcsname"
    ) < source.index("\n" + r"\documentclass")
    assert not (REPO_ROOT / module.CURRENT_MANUSCRIPT_PDF).exists()


def test_stale_cf4_public_claim_mutation_fails_quarantine_gate():
    module = _load_module()
    stale_claim = {
        **module.PUBLIC_CLAIMS[0],
        "claim_id": "stale.cf4.mv.publication",
        "statement": (
            "CF4 MV ideal-window bulk flow |B|(200 h^-1Mpc) = "
            + "40"
            + "5 km/s with LambdaCDM tension "
            + "4.4"
            + "-5.4 sigma"
        ),
        "allowed_phrase": "CF4 " + "40" + "5 km/s bulk-flow result",
    }

    payload = module.build_publication_claim_freeze_payload(
        repo_root=REPO_ROOT,
        freeze_output=Path("docs/generated/publication_claim_freeze.md"),
        matrix_output=Path("docs/generated/hostile_review_response_matrix.md"),
        generating_command="python scripts/check_publication_claim_freeze.py --dry-run",
        public_claims=[stale_claim],
        hostile_review_rows=module.HOSTILE_REVIEW_ROWS,
        worktree_state="test-worktree",
    )

    assert payload["required_assertions"]["cf4_p0_quarantine_clean"] is False
    assert "cf4_p0_quarantine_clean" in payload["failed_gates"]
    assert payload["cf4_p0_quarantine"]["ok"] is False
    assert payload["cf4_p0_quarantine"]["issues"]


def test_blocked_pdf_lint_with_zero_findings_cannot_pass_publication_gate(
    tmp_path: Path,
):
    module = _load_module()
    pdf_path = tmp_path / "docs/generated/manuscript_pdf/htt_base_research_report.pdf"
    report_path = tmp_path / "docs/generated/pdf_claim_lint_report.md"
    pdf_path.parent.mkdir(parents=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"not-a-real-pdf")
    pdf_hash = module._sha256_file(pdf_path)
    report_path.write_text(
        "\n".join(
            [
                "# PDF Claim Lint Report",
                "status: BLOCKED_NO_CURRENT_PDF",
                "claim_lint_passed: false",
                "",
                "## Summary",
                f"- PDF SHA256: `{pdf_hash}`",
                "- Failed findings: `0`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert module._pdf_claim_lint_passed(tmp_path) is False
