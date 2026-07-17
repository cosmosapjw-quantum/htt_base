"""Contract: byte-freeze of the shipped external-audit packages (REV-R179).

Adversarial-audit finding (freeze-battery lane, 2026-07-11): the v6 builder's
``--check`` has been structurally RED since the v7 cycle -- the builder
re-enumerates the LIVE tree (source index, evidence hashes), so any file
added by a later cycle makes in-memory regeneration differ from the frozen
package. That redness says "the live tree moved on", NOT "the frozen package
changed".

Byte authority (PR-124 preflight, 2026-07-17): the fixed-hash ledger
``docs/research_program/long_horizon_rescue/cf4_p0_legacy_package_hashes.json``
plus the off-repo backup bundle recorded in ``docs/git_history/README.md``.
The ``legacy/`` tree was untracked from git and the pre-PR-119 baseline
snapshots were stripped from history for GitHub pushability, so git is no
longer an immutability authority for the quarantined packages; this test now
verifies on-disk bytes against the ledger only. ``EXPECTED_BASELINE_COMMIT``
is retained as a historical identifier -- it resolves through the committed
commit map ``docs/git_history/commit_map_20260717.tsv`` and the backup bundle.

(PR-120 moved the value-bearing v6--v9 snapshots under the typed
``legacy/cf4_p0`` root.  Their bytes remain frozen against the ledger's fixed
root digests; neither the mutable index nor a regenerated quarantine
inventory is an immutability authority.)
"""
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import unittest

REPO = Path(__file__).resolve().parents[2]

FROZEN_PACKAGES = [
    "external_audit_research_report_20260707_v5",
]
QUARANTINED_PACKAGES = (
    "external_audit_research_report_20260708_v6",
    "external_audit_research_report_20260709_v6_1",
    "external_audit_research_report_20260710_v7",
    "external_audit_research_report_20260710_v8",
    "external_audit_research_report_20260711_v9",
)
LEGACY_ROOT = Path("legacy/cf4_p0/packages/external_reports")
FIXED_HASH_LEDGER = Path(
    "docs/research_program/long_horizon_rescue/cf4_p0_legacy_package_hashes.json"
)
EXPECTED_BASELINE_COMMIT = "e6da3670043596efdcd93f9ba5e631e1462146c7"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                          text=True, check=True).stdout


def _root_sha256(rows: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for relative, data in sorted(rows):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(data).digest())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _filesystem_root_rows(root: Path) -> list[tuple[str, bytes]]:
    rows: list[tuple[str, bytes]] = []
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise AssertionError(f"frozen package contains a symlink: {path}")
        if stat.S_ISREG(info.st_mode):
            rows.append((path.relative_to(root).as_posix(), path.read_bytes()))
        elif not stat.S_ISDIR(info.st_mode):
            raise AssertionError(f"frozen package contains a special file: {path}")
    return rows


class FrozenPackageFreeze(unittest.TestCase):
    def test_every_frozen_package_is_tracked_and_unmodified(self):
        for pkg in FROZEN_PACKAGES:
            with self.subTest(package=pkg):
                self.assertTrue((REPO / pkg).is_dir(), f"{pkg} missing")
                tracked = _git("ls-files", pkg).splitlines()
                self.assertGreater(len(tracked), 0,
                                   f"{pkg} has no git-tracked files")
                dirty = [ln for ln in
                         _git("status", "--porcelain", pkg).splitlines()
                         if not ln.startswith("??")]
                self.assertEqual(dirty, [],
                                 f"{pkg} tracked files modified: {dirty}")

    def test_v5_builder_still_has_no_check_flag_guard(self):
        # the v5 builder must NEVER be run (no --check; running it would
        # overwrite the frozen package) -- pin that it still lacks --check
        text = (REPO / "scripts/build_external_audit_report_v5.py").read_text()
        self.assertNotIn("--check", text)

    def test_cf4_descendant_reports_are_legacy_only_and_fixed_hash_bound(self):
        ledger_path = REPO / FIXED_HASH_LEDGER
        self.assertTrue(ledger_path.is_file())
        self.assertFalse(ledger_path.is_symlink())
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        self.assertEqual(ledger["schema_version"], "1.0.0")
        self.assertEqual(ledger["baseline_commit"], EXPECTED_BASELINE_COMMIT)
        self.assertEqual(
            ledger["root_digest_contract"],
            "sha256 over sorted UTF-8 relative_path + NUL + raw SHA-256 digest + NUL",
        )
        self.assertEqual(
            {row["baseline_path"] for row in ledger["package_roots"]},
            set(QUARANTINED_PACKAGES),
        )

        for row in ledger["package_roots"]:
            package = row["baseline_path"]
            with self.subTest(package=package):
                self.assertFalse((REPO / package).exists())
                legacy = REPO / row["legacy_path"]
                self.assertEqual(legacy, REPO / LEGACY_ROOT / package)
                self.assertTrue(legacy.is_dir())
                self.assertFalse(legacy.is_symlink())

                legacy_rows = _filesystem_root_rows(legacy)
                self.assertEqual(len(legacy_rows), row["file_count"])
                self.assertEqual(_root_sha256(legacy_rows), row["root_sha256"])

        for row in ledger["root_artifacts"]:
            artifact = row["baseline_path"]
            with self.subTest(artifact=artifact):
                self.assertFalse((REPO / artifact).exists())
                legacy = REPO / row["legacy_path"]
                self.assertEqual(legacy.parent, REPO / LEGACY_ROOT)
                self.assertTrue(legacy.is_file())
                self.assertFalse(legacy.is_symlink())
                legacy_bytes = legacy.read_bytes()
                self.assertEqual(len(legacy_bytes), row["size_bytes"])
                self.assertEqual(
                    "sha256:" + hashlib.sha256(legacy_bytes).hexdigest(),
                    row["sha256"],
                )
