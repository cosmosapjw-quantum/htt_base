"""Behavioral acceptance tests for package routing; no model execution is tested."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "resolve_model.py"
REGISTRY = ROOT / "MODEL_ROUTER.json"


class ModelRouterTests(unittest.TestCase):
    def run_cli(self, *args, env=None):
        completed = subprocess.run([sys.executable, str(SCRIPT), *args],
                                   text=True, capture_output=True, env=env, check=False)
        payload = json.loads(completed.stdout) if completed.stdout.strip() else None
        return completed, payload

    def check_invalid(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(content, encoding="utf-8")
            process, result = self.run_cli("--model", "gpt-6-astra", "--registry", str(path))
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(result["status"], "CONFIG_ERROR")
        self.assertEqual(result["packages"], [])

    def test_all_gpt56_aliases(self):
        aliases = ["GPT-5.6", "5.6", "gpt56", "gpt-5.6-sol", "gpt-5.6-terra",
                   "gpt-5.6-luna", "gpt-5.6-wm", "gpt-5.6-sol-wm",
                   "gpt-5.6-terra-wm", "gpt-5.6-luna-wm"]
        for alias in aliases:
            with self.subTest(alias=alias):
                process, result = self.run_cli("--model", alias)
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertEqual(result["family"], "gpt56")
                self.assertEqual(result["packages"][0]["filename"],
                                 "physmath-research-harness-gpt56-v3.1.0.zip")

    def test_all_gpt6_astra_aliases(self):
        for alias in ["GPT-6 Astra", "6 astra", "gpt6-astra", "gpt-6-astra", "gpt-6-astra-wm"]:
            with self.subTest(alias=alias):
                process, result = self.run_cli("--model", alias)
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertEqual(result["family"], "gpt6-astra")

    def test_case_and_outer_whitespace_normalize(self):
        process, result = self.run_cli("--model", " \tGpT-6-AsTrA-WM\n")
        self.assertEqual(process.returncode, 0)
        self.assertEqual(result["family"], "gpt6-astra")

    def test_unknown_and_future_models_do_not_route(self):
        for label in ["gpt-6", "6", "gpt-7-astra", "gpt-6-astra-next", "gpt-5.7-sol", "foo gpt-6-astra"]:
            with self.subTest(label=label):
                process, result = self.run_cli("--model", label)
                self.assertEqual(process.returncode, 2)
                self.assertEqual(result["status"], "MODEL_UNRESOLVED")
                self.assertIsNone(result["family"])
                self.assertEqual(result["packages"], [])

    def test_missing_label_does_not_inspect_environment(self):
        env = {**os.environ, "OPENAI_MODEL": "gpt-6-astra", "MODEL": "gpt-5.6-sol"}
        process, result = self.run_cli(env=env)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(result["status"], "MODEL_UNRESOLVED")
        self.assertEqual(result["packages"], [])

    def test_explicit_old_harness_overrides_new_model(self):
        process, result = self.run_cli("--model", "gpt-6-astra", "--harness", "gpt56")
        self.assertEqual(process.returncode, 0)
        self.assertEqual(result["family"], "gpt56")
        self.assertEqual(result["selection_basis"], "explicit_user_harness_override")
        self.assertEqual(result["supplied_model_label"], "gpt-6-astra")
        self.assertFalse(result["model_switched"])

    def test_explicit_harness_works_without_known_model(self):
        for args in [("--harness", "gpt6-astra"),
                     ("--model", "unknown", "--harness", "gpt6-astra")]:
            with self.subTest(args=args):
                process, result = self.run_cli(*args)
                self.assertEqual(process.returncode, 0)
                self.assertEqual(result["family"], "gpt6-astra")
                self.assertFalse(result["model_identity_verified"])

    def test_unsupported_override_is_rejected_by_cli(self):
        process, result = self.run_cli("--model", "gpt-6-astra", "--harness", "gpt7")
        self.assertEqual(process.returncode, 2)
        self.assertIsNone(result)
        self.assertIn("invalid choice", process.stderr)

    def test_default_research_does_not_select_coding(self):
        process, result = self.run_cli("--model", "GPT-6 Astra")
        self.assertEqual(process.returncode, 0)
        self.assertEqual([package["task"] for package in result["packages"]], ["research"])
        self.assertEqual(result["packages"][0]["entrypoints"],
                         ["START_HERE.md", "PROJECT_INSTRUCTIONS.md", "prompts/00_integrated_work_run.md"])

    def test_coding_dispatch(self):
        process, result = self.run_cli("--model", "5.6", "--task", "coding")
        self.assertEqual(process.returncode, 0)
        self.assertEqual([package["task"] for package in result["packages"]], ["coding"])
        self.assertEqual(result["packages"][0]["filename"], "physmath-coding-harness-gpt56-v3.1.0.zip")
        self.assertEqual(result["packages"][0]["entrypoints"],
                         ["START_HERE.md", "AGENTS.md", "SCIENTIFIC_CONTRACT.md"])

    def test_both_dispatch_research_then_coding(self):
        process, result = self.run_cli("--model", "6 astra", "--task", "both")
        self.assertEqual(process.returncode, 0)
        self.assertEqual([package["task"] for package in result["packages"]], ["research", "coding"])

    def test_selection_does_not_claim_loaded_executed_or_identity(self):
        process, result = self.run_cli("--model", "gpt-6-astra")
        self.assertEqual(process.returncode, 0)
        self.assertEqual(result["status"], "SELECTED")
        self.assertEqual(result["selection_basis"], "caller_supplied_model_label")
        for field in ["model_identity_verified", "model_switched", "harness_loaded", "harness_executed"]:
            self.assertIs(result[field], False)

    def test_custom_registry_path_is_used(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        registry["families"]["gpt6-astra"]["packages"]["research"]["library_file_id"] = "libfile_test123"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "custom.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            process, result = self.run_cli("--model", "gpt-6-astra", "--registry", str(path))
        self.assertEqual(process.returncode, 0)
        self.assertEqual(result["packages"][0]["library_file_id"], "libfile_test123")

    def test_missing_registry_is_config_error(self):
        with tempfile.TemporaryDirectory() as directory:
            process, result = self.run_cli("--harness", "gpt56", "--registry", str(Path(directory) / "missing.json"))
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(result["status"], "CONFIG_ERROR")
        self.assertEqual(result["packages"], [])

    def test_malformed_json_is_config_error(self):
        self.check_invalid("{invalid")

    def test_duplicate_json_key_is_config_error(self):
        self.check_invalid('{"router_version":1,"router_version":1}')

    def test_wrong_version_or_root_is_config_error(self):
        for content in ['[]', '{"router_version":true}', '{"router_version":2}']:
            with self.subTest(content=content):
                self.check_invalid(content)

    def test_alias_collision_is_config_error(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        registry["families"]["gpt6-astra"]["aliases"].append(" GPT-5.6 ")
        self.check_invalid(json.dumps(registry))

    def test_missing_package_or_inconsistent_path_is_config_error(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        del registry["families"]["gpt56"]["packages"]["coding"]
        self.check_invalid(json.dumps(registry))
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        registry["families"]["gpt56"]["packages"]["coding"]["library_path"] = "/wrong.zip"
        self.check_invalid(json.dumps(registry))


if __name__ == "__main__":
    unittest.main()
