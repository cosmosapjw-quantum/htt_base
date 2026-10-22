"""Whole-DAG binding tests against the selected source contracts and finite fixtures."""
import copy
import json
from pathlib import Path
import sys
import os
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = HERE.parents[2] / "inputs"
SOURCE = ROOT if (ROOT / "docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json").exists() else INPUTS
ROUTER = HERE if (HERE / "native_routing.py").exists() else SOURCE / "scripts/codex_harness"
sys.path.insert(0, str(ROUTER))
sys.path.insert(0, str(HERE))
import build_research_campaign as builder
import research_controller as rc
from native_routing import load_policy


def frontier():
    return {"campaign_id": "new-source-bound-hypothesis", "approved_scientific_repairs": ["new-repair"],
            "actions": [{"id": "R23-new", "depends_on": [], "goal": "Test the newly authored hypothesis",
                         "acceptance": "Frozen finite calculation plus fresh independent review",
                         "input_identity": "source-v2", "kind": "numeric", "owned_paths": ["new/result.json"],
                         "approved_repair_id": "new-repair", "enables_nodes": ["B02"]}]}


class WholeCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        program = SOURCE / "docs/research_program/observational_publication_20261015"
        cls.dag = json.loads((program / "PUBLICATION_DAG.json").read_text())
        cls.plan = json.loads((program / "OPEN_INPUTS_20261018/CONTINUATION_TASKS.json").read_text())
        cls.policy = load_policy(SOURCE / "docs/harness/NATIVE_ROUTING_POLICY_V1.json")

    def build(self, dag=None, plan=None, authored=None):
        return builder.build_campaign(dag or self.dag, plan or self.plan, authored or frontier())

    def test_all_42_original_contracts_and_18_source_bound_reuses(self):
        campaign = self.build()
        originals = {t["id"]: t for t in campaign["tasks"] if t["contract_origin"] == "original_science"}
        self.assertEqual(len(originals), 42)
        completed = [t for t in originals.values() if t["initial_state"] == "completed"]
        self.assertEqual(len(completed), 18)
        for source in self.dag["nodes"]:
            task = originals[source["id"]]
            self.assertEqual(task["acceptance"], source["acceptance"])
            self.assertEqual(task["original_depends_on"], source["depends_on"])
            self.assertEqual(task["external_missing"], source["external_missing"])
            if source["state"] == "completed_scoped":
                self.assertEqual(task["reuse_evidence"]["existing_evidence"], source["existing_evidence"])
                self.assertTrue(task["reuse_evidence"]["node_identity"])
        self.assertEqual(campaign["original_science_contract"], self.dag)

    def test_first_next_prioritizes_new_hypothesis_not_known_blocked_original(self):
        state = builder.initialize_whole_campaign(self.build(), "current owner authorization")
        packet = rc.next_packet(state, self.policy, {("gpt-6-sol", "high")})
        self.assertEqual(packet["task_id"], "R23-new")
        self.assertFalse(packet["launch_performed"])
        self.assertEqual(rc.summary(state)["original_science"]["source_completed_scoped"], 18)
        self.assertEqual(rc.summary(state)["original_science"]["total"], 42)

    def test_authored_priority_survives_reverse_lexicographic_action_ids(self):
        authored = frontier()
        first = authored["actions"][0]
        first["id"] = "R23-Q"
        second = copy.deepcopy(first)
        second["id"] = "R23-ATLAS"
        authored["actions"] = [first, second]
        state = builder.initialize_whole_campaign(self.build(authored=authored), "current authorization")
        self.assertLess(state["tasks"]["R23-Q"]["last_turn"], state["tasks"]["R23-ATLAS"]["last_turn"])
        packet = rc.next_packet(state, self.policy, {("gpt-6-sol", "high")})
        self.assertEqual(packet["task_id"], "R23-Q")

    def test_enabling_action_gates_original_but_not_scoped_acceptance_promotion(self):
        campaign = self.build()
        tasks = {t["id"]: t for t in campaign["tasks"]}
        self.assertIn("R23-new", tasks["B02"]["depends_on"])
        self.assertEqual(tasks["B02"]["original_depends_on"], ["B01"])
        state = builder.initialize_whole_campaign(campaign, "current authorization")
        self.assertNotIn("B02", rc.summary(state)["ready"])
        # A reviewed enabling result merely exposes the unchanged original obligation.
        state["tasks"]["R23-new"]["state"] = "completed"
        self.assertIn("B02", rc.summary(state)["ready"])
        self.assertEqual(state["tasks"]["B02"]["state"], "ready")
        self.assertEqual(state["tasks"]["B02"]["phase"], "acquisition")
        self.assertEqual(rc.summary(state)["original_science"]["source_completed_scoped"], 18)

    def test_pending_external_original_is_input_resolution_not_automatic_hold(self):
        state = builder.initialize_whole_campaign(self.build(), "current authorization")
        for key in ("K03", "L03", "H02"):
            self.assertEqual(state["tasks"][key]["state"], "ready")
            self.assertEqual(state["tasks"][key]["phase"], "acquisition")
            self.assertTrue(state["tasks"][key]["spec"]["input_routes"])

    def test_completed_reuse_missing_evidence_or_disagreeing_plan_rejected(self):
        dag = copy.deepcopy(self.dag)
        dag["nodes"][0]["existing_evidence"] = []
        with self.assertRaises(rc.ControllerError):
            self.build(dag=dag)
        plan = copy.deepcopy(self.plan)
        plan["all_original_nodes"][0]["intake_state"] = "pending"
        with self.assertRaises(rc.ControllerError):
            self.build(plan=plan)

    def test_frozen_campaign_replay_or_reopening_completed_original_rejected(self):
        authored = frontier()
        authored["actions"][0]["id"] = self.plan["frontier_actions"][0]["id"]
        with self.assertRaises(rc.ControllerError):
            self.build(authored=authored)
        authored = frontier()
        authored["actions"][0]["enables_nodes"] = ["E0"]
        with self.assertRaises(rc.ControllerError):
            self.build(authored=authored)

    def test_enabled_edge_cycle_and_unknown_node_rejected(self):
        authored = frontier()
        authored["actions"][0]["depends_on"] = ["B02"]
        with self.assertRaises(rc.ControllerError):
            self.build(authored=authored)
        authored = frontier()
        authored["actions"][0]["enables_nodes"] = ["unknown"]
        with self.assertRaises(rc.ControllerError):
            self.build(authored=authored)

    def test_acceptance_drift_cannot_be_hidden_by_frontier(self):
        dag = copy.deepcopy(self.dag)
        dag["nodes"][0]["acceptance"] = "weakened gate"
        with self.assertRaises(rc.ControllerError):
            self.build(dag=dag)

    def test_original_repair_authorization_is_explicit_and_validated(self):
        authored = frontier()
        authored["original_node_repairs"] = {"B02": "new-repair"}
        tasks = {t["id"]: t for t in self.build(authored=authored)["tasks"]}
        self.assertEqual(tasks["B02"]["approved_repair_id"], "new-repair")
        authored["original_node_repairs"]["B02"] = "unapproved"
        with self.assertRaises(rc.ControllerError):
            self.build(authored=authored)

    def test_single_command_initializes_whole_dag_and_emits_first_native_packet(self):
        program = SOURCE / "docs/research_program/observational_publication_20261015"
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            authored = tmp / "frontier.json"
            authored.write_text(json.dumps(frontier()))
            args = [sys.executable, str(HERE / "build_research_campaign.py"),
                    "--dag", str(program / "PUBLICATION_DAG.json"),
                    "--plan", str(program / "OPEN_INPUTS_20261018/CONTINUATION_TASKS.json"),
                    "--frontier", str(authored), "--output", str(tmp / "campaign.json"),
                    "--state", str(tmp / "state.json"), "--authorization", "Current user scientific campaign instruction",
                    "--next", "--available-profile", "gpt-6-sol/high",
                    "--policy", str(SOURCE / "docs/harness/NATIVE_ROUTING_POLICY_V1.json")]
            proc = subprocess.run(args, env={**os.environ, "PYTHONPATH": str(ROUTER)}, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            packet = json.loads(proc.stdout)
            self.assertEqual(packet["task_id"], "R23-new")
            state = json.loads((tmp / "state.json").read_text())
            self.assertEqual(len(state["tasks"]), 43)
            self.assertEqual(sum(t["state"] == "completed" for t in state["tasks"].values()), 18)
            self.assertEqual(state["tasks"]["R23-new"]["state"], "planned")
            self.assertFalse(packet["launch_performed"])


if __name__ == "__main__":
    unittest.main()
