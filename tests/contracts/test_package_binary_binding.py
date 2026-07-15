"""Contracts for fail-closed audit-package binary provenance."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from common.package_binary_binding import (
    verify_package_binary_binding,
    verify_packaged_entry_bytes,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
_BUILDERS = (
    "build_external_audit_package",
    "build_research_only_audit_package",
    "build_research_evaluation_package",
    "build_statistical_formalism_audit_package",
)


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _write_bound_png(root: Path, relative: str, data: bytes) -> Path:
    artifact = root / relative
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(data)
    manifest = artifact.with_suffix(".manifest.json")
    manifest.write_text(
        json.dumps(
            {
                "artifact_path": relative,
                "artifact_sha256": _sha256(data),
            }
        ),
        encoding="utf-8",
    )
    return manifest


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )


def _init_git(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Binary Binding Test")
    _git(root, "config", "user.email", "binary-binding@example.invalid")


def _commit_all(root: Path, message: str = "baseline") -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)


def _load_builder(name: str):
    spec = importlib.util.spec_from_file_location(
        f"binary_binding_{name}",
        REPO_ROOT / "scripts" / f"{name}.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _builder_entry(module, name: str):
    source = Path("figures/current/current.png")
    archive = "audit/figures/current/current.png"
    if name == "build_external_audit_package":
        return module.AuditPackageEntry(source, archive, "figure_payload", "test")
    if name == "build_research_evaluation_package":
        return module.Entry(archive, "figure_payload", source_path=source)
    return module.PackageEntry(
        archive_path=archive,
        group="figure_payload",
        description="test",
        source_path=source,
    )


def test_non_git_root_requires_explicitly_pinned_sidecar(tmp_path: Path):
    data = b"\x89PNG\r\n\x1a\ncurrent"
    manifest = _write_bound_png(tmp_path, "figures/current/current.png", data)

    with pytest.raises(ValueError, match="not independently trusted"):
        verify_package_binary_binding(
            tmp_path,
            "figures/current/current.png",
            content_mode="active_public",
        )

    binding = verify_package_binary_binding(
        tmp_path,
        "figures/current/current.png",
        content_mode="active_public",
        explicit_manifest_path="figures/current/current.manifest.json",
        explicit_manifest_sha256=_sha256(manifest.read_bytes()),
    )

    assert binding == {
        "method": "sidecar_artifact_sha256",
        "sha256": _sha256(data),
        "trusted_source": (
            "reviewed-pin:figures/current/current.manifest.json@"
            + _sha256(manifest.read_bytes())
        ),
    }

    assert verify_packaged_entry_bytes(
        tmp_path,
        "figures/current/current.png",
        data,
        expected_sha256=_sha256(data),
        content_mode="active_public",
        expected_binary_binding=binding,
    ) == data


@pytest.mark.parametrize("builder_name", _BUILDERS)
def test_all_package_builders_record_and_enforce_binary_binding(
    tmp_path: Path,
    builder_name: str,
):
    data = b"\x89PNG\r\n\x1a\ncurrent"
    _write_bound_png(tmp_path, "figures/current/current.png", data)
    _init_git(tmp_path)
    _commit_all(tmp_path)
    module = _load_builder(builder_name)
    entry = _builder_entry(module, builder_name)

    rows = module._entry_rows(tmp_path, (entry,))
    assert rows[0]["binary_binding"]["method"] == "git_head_exact_bytes"
    assert rows[0]["binary_binding"]["sha256"] == rows[0]["sha256"]

    manifest = tmp_path / "figures/current/current.manifest.json"
    changed = data + b"-changed"
    (tmp_path / "figures/current/current.png").write_bytes(changed)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["artifact_sha256"] = _sha256(changed)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    archive_payload = {"archive_entries": rows}
    with pytest.raises(ValueError, match="changed after manifest construction"):
        if builder_name == "build_external_audit_package":
            module.render_readme = lambda _payload: ""
            module.build_zip_bytes(tmp_path, archive_payload)
        else:
            module._build_zip_bytes(tmp_path, archive_payload, (entry,))

    (tmp_path / "figures/current/current.png").write_bytes(changed)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["artifact_sha256"] = "sha256:" + "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest digest mismatch"):
        module._entry_rows(tmp_path, (entry,))


def test_mismatched_sidecar_digest_fails_without_git_fallback(tmp_path: Path):
    data = b"\x89PNG\r\n\x1a\ncurrent"
    _write_bound_png(tmp_path, "figures/current/current.png", data)
    manifest = tmp_path / "figures/current/current.manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["artifact_sha256"] = "sha256:" + "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="manifest digest mismatch"):
        verify_package_binary_binding(
            tmp_path,
            "figures/current/current.png",
            content_mode="active_public",
            explicit_manifest_path="figures/current/current.manifest.json",
            explicit_manifest_sha256=_sha256(manifest.read_bytes()),
        )


def test_binary_symlink_fails_closed(tmp_path: Path):
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"\x89PNG\r\n\x1a\noutside")
    active = tmp_path / "figures/current/current.png"
    active.parent.mkdir(parents=True)
    active.symlink_to(outside)

    with pytest.raises(ValueError, match="symlink"):
        verify_package_binary_binding(
            tmp_path,
            "figures/current/current.png",
            content_mode="active_public",
        )


def test_digest_sidecar_symlink_fails_closed(tmp_path: Path):
    data = b"\x89PNG\r\n\x1a\ncurrent"
    artifact = tmp_path / "figures/current/current.png"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(data)
    outside = tmp_path / "outside.json"
    outside.write_text(
        json.dumps(
            {
                "artifact_path": "figures/current/current.png",
                "artifact_sha256": _sha256(data),
            }
        ),
        encoding="utf-8",
    )
    artifact.with_suffix(".manifest.json").symlink_to(outside)

    with pytest.raises(ValueError, match="symlink"):
        verify_package_binary_binding(
            tmp_path,
            "figures/current/current.png",
            content_mode="active_public",
        )


def test_copied_legacy_png_cannot_be_retyped_active(tmp_path: Path):
    data = b"\x89PNG\r\n\x1a\nlegacy-bytes"
    legacy = tmp_path / "legacy/cf4_p0/figures/original.png"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(data)
    _write_bound_png(tmp_path, "figures/current/copied.png", data)

    with pytest.raises(ValueError, match="duplicates immutable legacy bytes"):
        verify_package_binary_binding(
            tmp_path,
            "figures/current/copied.png",
            content_mode="active_public",
        )


def test_immutable_legacy_binary_remains_hash_bound(tmp_path: Path):
    data = b"%PDF-1.4\nlegacy\n"
    artifact = tmp_path / "legacy/cf4_p0/report.pdf"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(data)
    manifest = tmp_path / "legacy/cf4_p0/report.manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "artifact_path": "legacy/cf4_p0/report.pdf",
                "artifact_sha256": _sha256(data),
            }
        ),
        encoding="utf-8",
    )

    binding = verify_package_binary_binding(
        tmp_path,
        "legacy/cf4_p0/report.pdf",
        content_mode="immutable_historical_evidence",
        explicit_manifest_path="legacy/cf4_p0/report.manifest.json",
        explicit_manifest_sha256=_sha256(manifest.read_bytes()),
    )

    assert binding["method"] == "sidecar_artifact_sha256"
    assert binding["sha256"] == _sha256(data)

    with pytest.raises(ValueError, match="requires immutable_historical_evidence"):
        verify_package_binary_binding(
            tmp_path,
            "legacy/cf4_p0/report.pdf",
            content_mode="active_public",
        )


def test_staged_legacy_copy_cannot_be_blessed_by_mutable_index(tmp_path: Path):
    _init_git(tmp_path)
    data = b"\x89PNG\r\n\x1a\ncommitted-legacy"
    legacy = tmp_path / "legacy/cf4_p0/original.png"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(data)
    _commit_all(tmp_path)

    _write_bound_png(tmp_path, "figures/current/copied.png", data)
    _git(tmp_path, "add", "-A")

    with pytest.raises(ValueError, match="duplicates immutable legacy bytes"):
        verify_package_binary_binding(
            tmp_path,
            "figures/current/copied.png",
            content_mode="active_public",
        )


def test_existing_active_path_replaced_with_legacy_bytes_fails(tmp_path: Path):
    _init_git(tmp_path)
    legacy_data = b"\x89PNG\r\n\x1a\nlegacy"
    current_data = b"\x89PNG\r\n\x1a\ncurrent"
    legacy = tmp_path / "legacy/cf4_p0/original.png"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(legacy_data)
    _write_bound_png(tmp_path, "figures/current/current.png", current_data)
    _commit_all(tmp_path)

    manifest = _write_bound_png(
        tmp_path,
        "figures/current/current.png",
        legacy_data,
    )
    _git(tmp_path, "add", "-A")
    assert _sha256(manifest.read_bytes()).startswith("sha256:")

    with pytest.raises(ValueError, match="duplicates immutable legacy bytes"):
        verify_package_binary_binding(
            tmp_path,
            "figures/current/current.png",
            content_mode="active_public",
        )


def test_co_mutated_binary_and_sidecar_cannot_bless_each_other(tmp_path: Path):
    _init_git(tmp_path)
    _write_bound_png(
        tmp_path,
        "figures/current/current.png",
        b"\x89PNG\r\n\x1a\nbaseline",
    )
    _commit_all(tmp_path)

    _write_bound_png(
        tmp_path,
        "figures/current/current.png",
        b"\x89PNG\r\n\x1a\nco-mutated",
    )
    _git(tmp_path, "add", "-A")

    with pytest.raises(ValueError, match="not independently trusted"):
        verify_package_binary_binding(
            tmp_path,
            "figures/current/current.png",
            content_mode="active_public",
        )


def test_unchanged_head_active_binary_is_legitimate_collision_control(
    tmp_path: Path,
):
    _init_git(tmp_path)
    data = b"\x89PNG\r\n\x1a\npre-existing-shared-bytes"
    legacy = tmp_path / "legacy/cf4_p0/original.png"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(data)
    _write_bound_png(tmp_path, "figures/current/current.png", data)
    _commit_all(tmp_path)

    binding = verify_package_binary_binding(
        tmp_path,
        "figures/current/current.png",
        content_mode="active_public",
    )

    assert binding == {
        "method": "git_head_exact_bytes",
        "sha256": _sha256(data),
        "trusted_source": "git-head:figures/current/current.png",
    }


def test_relocated_immutable_binary_must_be_reachable_from_head(tmp_path: Path):
    _init_git(tmp_path)
    data = b"%PDF-1.4\nfrozen-baseline\n"
    original = tmp_path / "reports/frozen.pdf"
    original.parent.mkdir(parents=True)
    original.write_bytes(data)
    _commit_all(tmp_path)

    relocated = tmp_path / "legacy/cf4_p0/reports/frozen.pdf"
    relocated.parent.mkdir(parents=True)
    original.rename(relocated)
    _git(tmp_path, "add", "-A")

    binding = verify_package_binary_binding(
        tmp_path,
        "legacy/cf4_p0/reports/frozen.pdf",
        content_mode="immutable_historical_evidence",
    )

    assert binding["method"] == "git_head_reachable_binary_blob"
    assert binding["sha256"] == _sha256(data)
    assert binding["trusted_source"].startswith("git-head-blob:")


def test_non_git_binary_without_sidecar_fails_with_documented_fallback(tmp_path: Path):
    artifact = tmp_path / "figures/current/unbound.png"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"\x89PNG\r\n\x1a\nunbound")

    with pytest.raises(ValueError, match="no independent byte binding in HEAD"):
        verify_package_binary_binding(
            tmp_path,
            "figures/current/unbound.png",
            content_mode="active_public",
        )
