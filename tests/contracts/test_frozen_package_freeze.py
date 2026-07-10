"""Contract: byte-freeze of the shipped external-audit packages (REV-R179).

Adversarial-audit finding (freeze-battery lane, 2026-07-11): the v6 builder's
``--check`` has been structurally RED since the v7 cycle -- the builder
re-enumerates the LIVE tree (source index, evidence hashes), so any file
added by a later cycle makes in-memory regeneration differ from the frozen
package. That redness says "the live tree moved on", NOT "the frozen package
changed". The actual freeze guarantee is carried by git: every shipped
package directory is tracked and must show NO modifications to tracked
files. This test pins that guarantee directly and documents the expected-red
status of the v6 --check.

(The v9 package is the LIVE HEAD and is deliberately absent here; its
byte-stability is covered by test_external_audit_report_v9.py.)
"""
from pathlib import Path
import subprocess
import unittest

REPO = Path(__file__).resolve().parents[2]

FROZEN_PACKAGES = [
    "external_audit_research_report_20260707_v5",
    "external_audit_research_report_20260708_v6",
    "external_audit_research_report_20260709_v6_1",
    "external_audit_research_report_20260710_v7",
    "external_audit_research_report_20260710_v8",
]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                          text=True, check=True).stdout


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
