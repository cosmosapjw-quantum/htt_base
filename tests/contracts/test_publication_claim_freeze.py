import importlib.util
import json
from pathlib import Path
import subprocess

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/check_publication_claim_freeze.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("publication_claim_freeze", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://publication_claim_freeze.md",
        expected_artifact_path="docs/generated/publication_claim_freeze.md",
    ) == ()

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
    assert assertions["pdf_claim_lint_passed"] is True
    assert assertions["manuscript_blockers_recorded"] is True
    assert assertions["no_forbidden_claim_language"] is True
    assert assertions["no_c5_c6_family_id_claim"] is True
    assert payload["failed_gates"] == []

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
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--dry-run",
            "--freeze-output",
            str(freeze_output),
            "--matrix-output",
            str(matrix_output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
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
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--freeze-output",
            str(freeze_output),
            "--matrix-output",
            str(matrix_output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert write.returncode == 0, write.stderr
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
    assert f"Missing refs | {blockers['missing_refs']}" in freeze_text
    assert f"Quarantined refs | {blockers['quarantined_refs']}" in freeze_text
    _assert_no_forbidden_language(freeze_text + "\n" + matrix_text)

    fresh = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--check",
            "--freeze-output",
            str(freeze_output),
            "--matrix-output",
            str(matrix_output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert fresh.returncode == 0, fresh.stderr
    assert "up-to-date" in fresh.stdout

    matrix_output.write_text(matrix_text + "\n", encoding="utf-8")
    stale = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--check",
            "--freeze-output",
            str(freeze_output),
            "--matrix-output",
            str(matrix_output),
        ],
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
