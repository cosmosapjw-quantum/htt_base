"""Recovery contract for retired external-audit packages.

The packages are deliberately absent from the current tree.  Tracked payloads
remain recoverable from the accepted cleanup base; earlier off-tree packages
remain bound by the unchanged fixed-hash ledger.  An optional mounted backup
may be verified, but its absence cannot break an isolated worktree.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import subprocess


REPO = Path(__file__).resolve().parents[2]
CLEANUP_BASE = "0864b00948143d9b19d4983e50fcd2d905f4a5d3"
TRACKED_V5 = "external_audit_research_report_20260707_v5"
LEDGER = Path(
    "docs/research_program/long_horizon_rescue/"
    "cf4_p0_legacy_package_hashes.json"
)
EXPECTED_BASELINE_COMMIT = "e6da3670043596efdcd93f9ba5e631e1462146c7"


def _git(*args: str, text: bool = True) -> str | bytes:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=text,
    ).stdout


def _root_sha256(root: Path) -> tuple[int, str]:
    rows: list[tuple[str, bytes]] = []
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        assert not stat.S_ISLNK(info.st_mode), path
        if stat.S_ISREG(info.st_mode):
            rows.append((path.relative_to(root).as_posix(), path.read_bytes()))
        else:
            assert stat.S_ISDIR(info.st_mode), path
    digest = hashlib.sha256()
    for relative, data in rows:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(data).digest())
        digest.update(b"\0")
    return len(rows), "sha256:" + digest.hexdigest()


def test_tracked_v5_package_is_absent_but_git_recoverable() -> None:
    assert not (REPO / TRACKED_V5).exists()
    _git("cat-file", "-e", f"{CLEANUP_BASE}:{TRACKED_V5}/MANIFEST.json")
    _git(
        "cat-file",
        "-e",
        f"{CLEANUP_BASE}:scripts/build_external_audit_report_v5.py",
    )


def test_fixed_hash_ledger_is_unchanged_and_complete() -> None:
    current = (REPO / LEDGER).read_bytes()
    assert current == _git("show", f"{CLEANUP_BASE}:{LEDGER.as_posix()}", text=False)
    payload = json.loads(current)
    assert payload["schema_version"] == "1.0.0"
    assert payload["baseline_commit"] == EXPECTED_BASELINE_COMMIT
    assert payload["root_digest_contract"] == (
        "sha256 over sorted UTF-8 relative_path + NUL + raw SHA-256 digest + NUL"
    )
    assert payload["package_roots"]
    assert payload["root_artifacts"]


def test_optional_off_tree_backup_matches_ledger_when_mounted() -> None:
    payload = json.loads((REPO / LEDGER).read_text(encoding="utf-8"))
    for row in payload["package_roots"]:
        assert not (REPO / row["baseline_path"]).exists()
        backup = REPO / row["legacy_path"]
        if not backup.exists():
            continue
        assert backup.is_dir() and not backup.is_symlink()
        count, digest = _root_sha256(backup)
        assert count == row["file_count"]
        assert digest == row["root_sha256"]

    for row in payload["root_artifacts"]:
        assert not (REPO / row["baseline_path"]).exists()
        backup = REPO / row["legacy_path"]
        if not backup.exists():
            continue
        assert backup.is_file() and not backup.is_symlink()
        raw = backup.read_bytes()
        assert len(raw) == row["size_bytes"]
        assert "sha256:" + hashlib.sha256(raw).hexdigest() == row["sha256"]
