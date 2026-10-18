"""Focused standalone regression for explicit continuation refs; no owner I/O."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROGRAMME = Path(__file__).resolve().parents[2]
SCRIPT = PROGRAMME / "L01_R10_C10_RUNTIME_RECOVERY_20261017/scripts/l01_checkout_guard.py"
spec = importlib.util.spec_from_file_location("continuation_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class CheckoutContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "fixture"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Guard Fixture")
        for relative in guard.REQUIRED:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("print('--spectral-receipt --c8-receipt --attempts')\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.head = self.git("rev-parse", "HEAD")
        self.ref = "origin/research/explicit-continuation-fixture"
        for ref in (guard.EXPECTED_REF, self.ref, "origin/main"):
            self.git("update-ref", "refs/remotes/"+ref, self.head)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              text=True, capture_output=True).stdout.strip()

    def test_default_and_explicit_ref_accept_exact_clean_checkout(self):
        for ref in (guard.EXPECTED_REF, self.ref, "origin/main"):
            result = guard.check_checkout(self.root, ref, smoke=False)
            self.assertEqual(result["head"], self.head)
            self.assertEqual(result["remote_ref"], ref)

    def test_cli_explicit_ref_keeps_import_smoke(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--worktree", str(self.root),
                            "--expected-ref", self.ref], text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(set(json.loads(p.stdout)["smoke"]), {"c8", "c9", "download"})

    def test_explicit_ref_does_not_allow_stale_head_or_tag_shadow(self):
        (self.root / "new.txt").write_text("new\n")
        self.git("add", ".")
        self.git("commit", "-qm", "newer")
        self.git("tag", self.ref)
        with self.assertRaisesRegex(guard.CheckoutError, "STALE_CHECKOUT_HEAD") as exc:
            guard.check_checkout(self.root, self.ref, smoke=False)
        self.assertIn("primary checkout", str(exc.exception))
        self.assertNotIn("fresh", str(exc.exception))

    def test_dirty_checkout_preserved(self):
        notes = self.root / "notes.txt"
        notes.write_text("preserve me\n")
        with self.assertRaisesRegex(guard.CheckoutError, "DIRTY_WORKTREE"):
            guard.check_checkout(self.root, self.ref, smoke=False)
        self.assertEqual(notes.read_text(), "preserve me\n")

    def test_invalid_or_implicit_refs_rejected(self):
        for ref in ("HEAD", "origin/HEAD", "origin/main^", "origin/a..b", "--all", "origin/", 1):
            with self.subTest(ref=ref), self.assertRaisesRegex(guard.CheckoutError, "UNEXPECTED_BRANCH_REF"):
                guard.check_checkout(self.root, ref, smoke=False)

    def test_missing_remote_ref_has_no_head_fallback(self):
        with self.assertRaisesRegex(guard.CheckoutError, "EXPECTED_REMOTE_REF_UNAVAILABLE"):
            guard.check_checkout(self.root, "origin/research/not-fetched", smoke=False)

    def test_top_level_and_committed_missing_file_checks_remain(self):
        with self.assertRaisesRegex(guard.CheckoutError, "NOT_GIT_TOPLEVEL"):
            guard.check_checkout(self.root / "docs", self.ref, smoke=False)
        (self.root / guard.REQUIRED[-1]).unlink()
        self.git("add", "-u")
        self.git("commit", "-qm", "missing required file")
        self.git("update-ref", "refs/remotes/"+self.ref, self.git("rev-parse", "HEAD"))
        with self.assertRaisesRegex(guard.CheckoutError, "INCOMPLETE_STACKED_CHECKOUT"):
            guard.check_checkout(self.root, self.ref, smoke=False)

    def test_git_trust_failure_not_overridden(self):
        # safe.directory is deliberately not edited by the tested implementation.
        from unittest.mock import patch
        failed = subprocess.CompletedProcess([], 128, "", "fatal: detected dubious ownership")
        with patch.object(guard.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(guard.CheckoutError, "GIT_UNAVAILABLE_OR_UNTRUSTED"):
                guard.check_checkout(self.root, self.ref, smoke=False)


if __name__ == "__main__":
    unittest.main()
