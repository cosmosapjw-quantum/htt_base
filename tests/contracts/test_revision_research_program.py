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
    chunks = []
    for path in GENERATED:
        assert path.exists(), f"missing generated output: {path}"
        chunks.append(path.read_text())
    return "\n".join(chunks)


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
