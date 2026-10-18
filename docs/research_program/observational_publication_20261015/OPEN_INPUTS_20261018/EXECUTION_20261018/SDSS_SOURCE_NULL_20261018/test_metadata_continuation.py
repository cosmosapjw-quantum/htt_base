"""Offline exact-history continuation fixtures; no real process/network launches."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import root_launcher


class MetadataContinuationBoundaries(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        actual = Path("/mnt/extdrive/workdir/htt_open_data/sdss_source_null_20261018")
        attempt = root_launcher.ORIGINAL_ATTEMPT
        for name in ("recovery.single_attempt.started.json",
                     f"recovery.{attempt}.execution.json", f"recovery.{attempt}.metadata.json",
                     f"recovery.{attempt}.metadata.failure.json", f"recovery.{attempt}.metadata.response.json"):
            shutil.copyfile(actual / name, self.root / name)
        prior = Path(__file__).parent / "RECOVERY_PRESEAL_FINAL.json.pre_metadata_phase"
        self.preseal = self.root / "preseal.json"
        shutil.copyfile(prior, self.preseal.with_name(self.preseal.name + ".pre_metadata_phase"))
        self.snapshot = json.loads(prior.read_text())
        self.snapshot["source_sha256"] = {"fixture_code_only": "updated"}
        self.preseal.write_text(json.dumps(self.snapshot))
        self.failure = self.root / f"recovery.{attempt}.execution.json"
        self.metadata = self.root / f"recovery.{attempt}.metadata.json"
        self.approval = self.root / "fixture-approval"
        self.approval.write_text("finite integration fixture; no network")

    def validate(self, **changed):
        args = dict(root=self.root, preseal=self.preseal, snapshot=self.snapshot,
                    prior_failure=self.failure, prior_failure_sha256=root_launcher.PRIOR_FAILURE_SHA256,
                    saved_metadata=self.metadata, saved_metadata_sha256=root_launcher.SAVED_METADATA_SHA256)
        args.update(changed)
        return root_launcher.validate_continuation(**args)

    def call_launch(self):
        return root_launcher.launch(self.root, self.preseal, self.approval, "fixture",
                                    self.failure, root_launcher.PRIOR_FAILURE_SHA256,
                                    self.metadata, root_launcher.SAVED_METADATA_SHA256)

    def test_exact_zero_bulk_history_accepts_without_network(self):
        marker = self.validate()
        self.assertEqual(marker.name, f"recovery.{root_launcher.NAMESPACE}.started.json")
        self.assertFalse(marker.exists())

    def test_generic_wrong_failure_or_hash_rejected_before_network(self):
        for changed in ({"prior_failure_sha256": "0"*64},
                        {"saved_metadata_sha256": "0"*64},
                        {"prior_failure": self.root / "unrelated.json"},
                        {"saved_metadata": self.root / "unrelated.json"}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.validate(**changed)

    def test_changed_noncode_prefix_contract_or_budget_seal_rejected(self):
        for key in ("ranges", "contract_sha256", "scientific_budget_sha256"):
            altered = json.loads(json.dumps(self.snapshot))
            altered[key] = "changed"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "seals changed"):
                self.validate(snapshot=altered)

    def test_altered_original_history_rejected(self):
        original = self.failure.read_text()
        for key, value in (("attempt", "replacement"), ("children", [{"pid": 1}]),
                           ("child_exit_codes", [{"pid": 1, "exit_code": 0}]),
                           ("error", "different failure")):
            record = json.loads(original)
            record[key] = value
            self.failure.write_text(json.dumps(record))
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate()
        self.failure.write_text(original)

    def test_range_or_other_execution_artifacts_block_continuation(self):
        for name in (f"recovery.{root_launcher.ORIGINAL_ATTEMPT}.range0.launch.json",
                     "recovery.other.execution.json", "range.0-4294967295.json"):
            artifact = self.root / name
            artifact.write_text("{}")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "history exists"):
                self.validate()
            artifact.unlink()

    def test_original_marker_and_metadata_failure_must_match(self):
        for name in ("recovery.single_attempt.started.json",
                     f"recovery.{root_launcher.ORIGINAL_ATTEMPT}.metadata.failure.json",
                     f"recovery.{root_launcher.ORIGINAL_ATTEMPT}.metadata.response.json"):
            artifact = self.root / name
            original = artifact.read_bytes()
            artifact.write_text("{}")
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.validate()
            artifact.write_bytes(original)

    def test_second_continuation_rejected_before_network(self):
        self.validate().write_text("{\"phase\":\"already consumed\"}")
        with patch("root_launcher.launch_guards", return_value=(self.snapshot, 7690428705)), \
             patch("root_launcher.verify_metadata", side_effect=AssertionError("network forbidden")) as metadata:
            with self.assertRaisesRegex(ValueError, "already consumed"):
                self.call_launch()
            metadata.assert_not_called()

    def test_metadata_phase_failure_consumes_phase_without_bulk(self):
        with patch("root_launcher.launch_guards", return_value=(self.snapshot, 7690428705)), \
             patch("root_launcher.subprocess.check_output", return_value="fixture-head\n"), \
             patch("root_launcher.verify_metadata", side_effect=OSError("fixture metadata failure")), \
             patch("root_launcher.subprocess.Popen", side_effect=AssertionError("bulk forbidden")) as bulk:
            with self.assertRaisesRegex(OSError, "fixture metadata failure"):
                self.call_launch()
            bulk.assert_not_called()
            with self.assertRaisesRegex(ValueError, "already consumed"):
                self.call_launch()
        result = json.loads((self.root / f"recovery.{root_launcher.NAMESPACE}.execution.json").read_text())
        self.assertEqual(result["children"], [])
        self.assertEqual(result["root_bulk_requests_launched_this_phase"], 0)
        self.assertEqual(result["attempt"], root_launcher.ORIGINAL_ATTEMPT)

    def test_live_previous_controller_blocks_continuation(self):
        exists = Path.exists
        def simulated(path):
            return True if str(path) == "/proc/941715" else exists(path)
        with patch.object(Path, "exists", new=simulated):
            with self.assertRaisesRegex(ValueError, "Prior controller PID exists"):
                self.validate()

    def test_positive_phase_marks_before_metadata_then_three_workers_only(self):
        launched = []
        marker = self.validate()
        original_marker = (self.root / "recovery.single_attempt.started.json").read_bytes()
        original_failure = self.failure.read_bytes()
        def metadata(root, namespace):
            self.assertTrue(marker.exists())
            self.assertEqual(namespace, root_launcher.NAMESPACE)
            self.assertEqual(launched, [])
            return self.metadata
        def start(command, **kwargs):
            index = len(launched)
            self.assertLess(index, 3)
            launched.append(command)
            a, b = root_launcher.RANGES[index]
            (self.root / f"range.{a}-{b}.json").write_text("{\"status\":\"fixture completion\"}")
            class Completed:
                pid = 10000000 + index
                returncode = 0
                def poll(self): return 0
                def wait(self): return 0
            return Completed()
        class Result:
            returncode = 0
        with patch("root_launcher.launch_guards", return_value=(self.snapshot, 7690428705)), \
             patch("root_launcher.subprocess.check_output", return_value="fixture-head\n"), \
             patch("root_launcher.verify_metadata", side_effect=metadata) as official, \
             patch("root_launcher.subprocess.Popen", side_effect=start), \
             patch("root_launcher.subprocess.run", return_value=Result()), \
             patch("root_launcher.acquire") as assemble, \
             patch("root_launcher.shutil.disk_usage", return_value=shutil._ntuple_diskusage(10**12, 0, 10**12)):
            with (self.root / "recovery.controller.lock").open("a") as lock:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.call_launch()
            official.assert_called_once()
            assemble.assert_called_once_with(self.root)
        self.assertEqual(len(launched), 3)
        self.assertTrue(all(root_launcher.NAMESPACE in command for command in launched))
        execution = json.loads((self.root / f"recovery.{root_launcher.NAMESPACE}.execution.json").read_text())
        self.assertEqual(execution["attempt"], root_launcher.ORIGINAL_ATTEMPT)
        self.assertEqual(execution["root_bulk_requests_previously_launched"], 0)
        self.assertEqual(execution["root_bulk_requests_launched_this_phase"], 3)
        self.assertEqual(execution["root_bulk_request_ceiling"], 3)
        self.assertEqual(execution["scientific_execution"], "NOT_STARTED")
        self.assertEqual((self.root / "recovery.single_attempt.started.json").read_bytes(), original_marker)
        self.assertEqual(self.failure.read_bytes(), original_failure)
        with self.assertRaisesRegex(ValueError, "already consumed"):
            self.validate()


if __name__ == "__main__":
    unittest.main()

