"""Exercise runner receipts without running Lean or changing proof evidence."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


RUNNER = Path("docs/research_program/tensor_joint_r9/revision2/depth_formal/law_support/compile.py")
ROOT = Path(__file__).resolve().parents[2]


class LawSupportRunnerTest(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("law_support_runner", ROOT / RUNNER)
        self.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runner)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runner.__file__ = str(self.root / RUNNER)
        self.formal = self.root / "formal"
        (self.formal / "R9Depth").mkdir(parents=True)
        (self.formal / "lean-toolchain").write_text("fixture-toolchain\n")
        self.source = self.formal / "R9Depth/LawSupport.lean"
        self.source.write_text("-- fixture\n#print axioms fixture\n")
        for name in ("BlockBridge", "Covariance"):
            (self.formal / f"R9Depth/{name}.lean").write_text("-- dependency fixture\n")
        self.cache = self.root / "cache"
        (self.cache / "packages/mathlib").mkdir(parents=True)
        (self.cache / "packages/mathlib/lean-toolchain").write_text("fixture-toolchain\n")
        self.output = self.root / "output"

    def invoke(self, effect):
        argv = ["compile.py", "--output", str(self.output), "--cache", str(self.cache)]
        with patch.object(sys, "argv", argv), patch.object(
            self.runner.subprocess, "check_output", return_value=self.runner.PIN + "\n"
        ), patch.object(self.runner.subprocess, "run", side_effect=effect) as run:
            with contextlib.redirect_stdout(io.StringIO()):
                code = self.runner.main()
        return code, json.loads((self.output / "execution.json").read_text()), run.call_count

    def test_timeout_at_each_stage_preserves_partial_output_and_stops(self):
        for failing in range(3):
            with self.subTest(stage=failing):
                self.output = self.root / f"timeout-{failing}"
                responses = [subprocess.CompletedProcess([], 0, f"dep-{i}", "") for i in range(failing)]
                responses.append(subprocess.TimeoutExpired(["lake"], 120, output=b"partial output\n", stderr=b"partial error\n"))
                code, record, count = self.invoke(responses)
                self.assertEqual(code, 1)
                self.assertIsNone(record["exit_code"])
                self.assertTrue(record["timed_out"])
                self.assertEqual(count, failing + 1)
                self.assertIn("partial output\n", record["stdout"])
                self.assertNotIn("b'partial", record["stdout"])
                self.assertIn("partial error\n", record["stderr"])
                self.assertTrue((self.output / "source.lean").is_file())

    def test_missing_compiler_preserves_failure_receipt(self):
        code, record, count = self.invoke(FileNotFoundError("lake not found"))
        self.assertEqual((code, count), (1, 1))
        self.assertEqual(record["launch_error"], "FileNotFoundError: lake not found")
        self.assertIsNone(record["exit_code"])

    def test_success_and_nonzero_dependency_exit(self):
        for exit_code in (0, 3):
            with self.subTest(exit_code=exit_code):
                self.output = self.root / f"exit-{exit_code}"
                code, record, count = self.invoke(lambda *a, **k: subprocess.CompletedProcess(a[0], exit_code, "checked", ""))
                self.assertEqual(code, 0 if exit_code == 0 else 1)
                self.assertEqual(record["exit_code"], exit_code)
                self.assertEqual(count, 3 if exit_code == 0 else 1)

    def test_sorry_axiom_still_fails(self):
        code, record, _ = self.invoke(lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "sorryAx", ""))
        self.assertEqual(code, 1)
        self.assertTrue(record["axiom_check"]["sorryAx_present"])

    def test_changed_source_is_not_reported_as_the_compiled_snapshot(self):
        original = self.source.read_bytes()
        def compiler(*args, **kwargs):
            self.source.write_text("-- changed during compilation\n")
            return subprocess.CompletedProcess(args[0], 0, "checked", "")
        code, record, _ = self.invoke(compiler)
        self.assertEqual(code, 1)
        self.assertTrue(record["source_changed"])
        self.assertEqual(record["source_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual((self.output / "source.lean").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
