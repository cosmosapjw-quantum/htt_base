from __future__ import annotations

import hashlib
import json
import stat
import subprocess
from pathlib import Path

from common.artifact_manifest import validate_manifest_payload


ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "harness_templates/vendor/physmath-gpt56/3.1.0"
RECEIPT = ROOT / "docs/audits/harness_intake_20260714/receipt.json"
CLEANUP_BASE = "0864b00948143d9b19d4983e50fcd2d905f4a5d3"
GENERIC_SKILLS = {
    "adversarial-review",
    "claim-source-audit",
    "evidence-acquisition",
    "hypothesis-space",
    "independent-diff-review",
    "numerical-validation",
    "physics-math-validation",
    "research-closeout",
    "research-code-task",
    "research-contract",
    "reproducibility-closeout",
    "scientific-validation",
    "verification-design",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _historical_receipt() -> dict:
    """Load the retired intake receipt from its immutable Git authority."""
    relative = RECEIPT.relative_to(ROOT).as_posix()
    completed = subprocess.run(
        ["git", "show", f"{CLEANUP_BASE}:{relative}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def _tree_hash(root: Path) -> tuple[int, int, str]:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        rel = path.relative_to(root).as_posix().encode()
        digest.update(rel + b"\0" + _sha256(path).encode() + b"\n")
    return len(files), sum(path.stat().st_size for path in files), digest.hexdigest()


def test_receipt_matches_immutable_vendor_trees() -> None:
    receipt = _historical_receipt()
    assert receipt["schema_version"] == "htt.physmath_harness_receipt.v1"
    for archive in receipt["archives"]:
        name = "coding" if "coding" in archive["name"] else "research"
        count, size, tree_hash = _tree_hash(VENDOR / name)
        assert (count, size, tree_hash) == (
            archive["file_count"],
            archive["uncompressed_bytes"],
            archive["vendor_tree_sha256"],
        )
        manifest = json.loads((VENDOR / name / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["version"] == "3.1.0"
        assert manifest["name"] == archive["name"].removesuffix(".zip")


def test_all_vendor_members_are_versioned() -> None:
    completed = subprocess.run(
        ["git", "ls-files", "--", str(VENDOR.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    tracked = {line for line in completed.stdout.splitlines() if line}
    worktree = {
        path.relative_to(ROOT).as_posix()
        for path in VENDOR.rglob("*")
        if path.is_file()
    }
    assert tracked == worktree

    attributes = subprocess.run(
        ["git", "check-attr", "text", "--", *sorted(worktree)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert attributes.stdout.splitlines()
    assert all(line.endswith(": text: unset") for line in attributes.stdout.splitlines())


def test_vendor_has_only_expected_executables_and_safe_paths() -> None:
    expected = {
        "coding/tools/init_harness.py",
        "coding/tools/validate_harness.py",
        "research/tools/init_workspace.py",
        "research/tools/validate_workspace.py",
    }
    executable: set[str] = set()
    for path in VENDOR.rglob("*"):
        assert not path.is_symlink()
        assert ".." not in path.relative_to(VENDOR).parts
        if path.is_file() and path.stat().st_mode & stat.S_IXUSR:
            executable.add(path.relative_to(VENDOR).as_posix())
        assert path.suffix not in {".pyc", ".pyo"}
    assert executable == expected


def test_root_controls_and_adapter_preserve_repo_authority() -> None:
    receipt = _historical_receipt()
    for rel, expected in receipt["root_control_hashes"].items():
        assert len(expected) == 64
        int(expected, 16)
        assert (ROOT / rel).is_file()
        for mode in ("coding", "research"):
            upstream = VENDOR / mode / rel
            if upstream.is_file():
                assert _sha256(ROOT / rel) != _sha256(upstream)

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Codex operating contract" in agents
    assert "Do not implement or simulate the future external low-ell" in agents
    assert "Use `$htt-physmath-audit` for evidence-locked multi-axis hostile audits" in agents
    assert "`$htt-physics-math-audit` alone does not route a complete multi-axis audit" in agents

    active = {path.parent.name for path in (ROOT / ".agents/skills").glob("*/SKILL.md")}
    assert not (GENERIC_SKILLS & active)
    adapter = (ROOT / ".agents/skills/htt-physmath-audit/SKILL.md").read_text(encoding="utf-8")
    assert "TODO" not in adapter
    for phrase in [
        "HTT owns posterior/evidence/PPC/LOOCV",
        "MIO owns diagnostic-only certificates",
        "public_use=false",
        "ClaimTier.EXPLORATORY",
        "ArtifactMode.INTERNAL_EXPLORATORY",
        "AllowedUse.INTERNAL_ONLY",
        "BundleKind.COMMON_CONTRACT",
        "Scalar, directional, or external-transfer-only evidence cannot",
        "Bianchi geometry or family",
        "native adapter remains schema-only and fail-closed",
    ]:
        assert phrase in adapter


def test_receipt_is_explicitly_non_scientific() -> None:
    metadata = _historical_receipt()["artifact_metadata"]
    assert validate_manifest_payload(
        metadata,
        manifest_path=RECEIPT,
        expected_artifact_path="docs/audits/harness_intake_20260714/receipt.json",
    ) == ()
    assert metadata["owner"] == "COMMON"
    assert metadata["implementation_scope"] == "common"
    assert metadata["bundle_kind"] == "common_contract"
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["artifact_mode"] == "governance_diagnostic"
    assert metadata["allowed_use"] == "external_audit"
    assert metadata["transfer_source"] == "none"
    assert metadata["sky_support_status"] == "not_directional"
    assert metadata["null_mock_status"] == "not_statistical"
