"""Append/reopening counterexamples; production state is read only and deep copied."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import test_research_controller as base
from test_research_controller import POLICY, PROFILES, task
import research_controller as rc


def delta(kind="method", **kwargs):
    return {"kind": kind, "before": {"method": "retained-summary"},
            "after": {"method": "matched-cohort nuisance comparison"},
            "scope": "conditional distance", "discriminator": "compare residual projection", **kwargs}


def spec(key, requires=None):
    return task(key, contract_origin="new_conditional_research", promotes_original_acceptance=False,
                approved_repair_id=None, owned_paths=["fixture/"+key], input_sources=["fixture-release"],
                requires=requires or {"all": []}, semantic_delta=delta())


class FrontierTests(unittest.TestCase):
    setUp = base.ControllerTests.setUp
    state = base.ControllerTests.state
    launch = base.ControllerTests.launch
    result = base.ControllerTests.result
    issue = base.ControllerTests.issue
    def semantic_file(self, value):
        path = Path(self.tmp.name) / "semantic.json"
        path.write_text(json.dumps(value))
        return str(path)

    def append(self, state, rows):
        rc.append_frontier(state, {"frontier_id": "new-methods", "tasks": rows}, "owner authorized")

    def test_real_state_copy_preserves_original_objects_and_accounting(self):
        path = Path(__file__).resolve().parents[2] / ".agent-harness/runtime/r23-continuous/STATE.json"
        if not path.is_file():
            self.skipTest("owner production checkpoint unavailable")
        raw = path.read_bytes()
        state = json.loads(raw)
        old = copy.deepcopy(state)
        self.append(state, [spec("R24-TEST")])
        for field in ("campaign", "campaign_identity", "packets", "ultra_repairs", "ultra_pending", "turn"):
            self.assertEqual(state[field], old[field])
        self.assertEqual({k:state["tasks"][k] for k in old["tasks"]}, old["tasks"])
        self.assertEqual(path.read_bytes(), raw)
        self.assertIn("R24-TEST", rc.summary(state)["ready"])

    def test_alternative_qualified_products_not_counterexample_completion(self):
        state = self.state([task("OLD")])
        leaf = lambda name: {"task_id":name,"evidence":"qualified","product":"confidence_bundle"}
        self.append(state,[spec("R1"),spec("R2"),spec("USE",{"any":[leaf("R1"),leaf("R2")]})])
        state["tasks"]["R1"].update(state="completed")
        state["tasks"]["R2"].update(state="held")
        self.assertNotIn("USE",rc.summary(state)["ready"])
        state["tasks"]["R1"]["qualified_products"]=["confidence_bundle"]
        self.assertIn("USE",rc.summary(state)["ready"])

    def test_actual_candidate_review_qualification_unlocks_typed_consumer(self):
        state = self.state([task("A")])
        obligation = {"all": [{"any": [
            {"task_id": "A", "evidence": "qualified", "product": "confidence_bundle"}]}]}
        self.append(state, [spec("USE", obligation)])
        packet = self.launch(state)
        self.result(state, packet, qualified_products=["confidence_bundle"])
        self.assertNotIn("USE", rc.summary(state)["ready"])
        review = self.launch(state)
        self.result(state, review, acceptance_met=True, qualified_products=["confidence_bundle"])
        self.assertIn("USE", rc.summary(state)["ready"])

    def test_transport_restores_without_any_repair_or_changed_input(self):
        state = self.state([task("A", approved_repair_id=None)])
        packet = rc.next_packet(state, POLICY, PROFILES)
        evidence = self.semantic_file({"refusal": "temporary native transport"})
        rc.launch_failed(state, packet["packet_id"], evidence, "transport", "temporary")
        evidence = self.semantic_file(delta("prelaunch_transport", packet_id=packet["packet_id"],
            before={"transport": "refused"}, after={"transport": "available"}))
        rc.resume(state, "A", evidence, "input-v1")
        retry = rc.next_packet(state, POLICY, PROFILES)
        self.assertEqual(retry["phase"], "execute")
        self.assertEqual(state["ultra_repairs"], {})
        self.assertEqual(state["ultra_pending"], {})

    def test_resume_evidence_reaches_next_worker(self):
        state = self.state([task("A")])
        state["tasks"]["A"]["state"] = "held"
        value = delta()
        evidence = self.semantic_file(value)
        rc.resume(state, "A", evidence, "input-v1")
        packet = rc.next_packet(state, POLICY, PROFILES)
        active = packet["resume_evidence"]
        self.assertEqual(active["semantic_delta"], value)
        self.assertEqual(active["receipt"]["path"], str(Path(evidence).resolve()))
        assignment = json.loads(packet["spawn_args"]["message"].split("Assignment:\n", 1)[1])
        self.assertEqual(assignment["resume_evidence"], active)

    def test_scientific_resume_survives_prelaunch_transport_restore(self):
        state = self.state([task("A")])
        state["tasks"]["A"]["state"] = "held"
        method = delta()
        method_path = self.semantic_file(method)
        rc.resume(state, "A", method_path, "input-v1")
        scientific = copy.deepcopy(state["tasks"]["A"]["resume_evidence"])
        packet = rc.next_packet(state, POLICY, PROFILES)
        refusal = Path(self.tmp.name) / "refusal.txt"
        refusal.write_text("actual fixture native prelaunch refusal")
        rc.launch_failed(state, packet["packet_id"], str(refusal), "transport", "temporary")
        transport = delta("prelaunch_transport", packet_id=packet["packet_id"],
            before={"transport": "refused"}, after={"transport": "available"})
        transport_path = Path(self.tmp.name) / "restored.json"
        transport_path.write_text(json.dumps(transport))
        rc.resume(state, "A", str(transport_path), "input-v1")
        retry = rc.next_packet(state, POLICY, PROFILES)
        self.assertEqual(retry["phase"], "research")
        self.assertEqual(retry["scientific_resume"], scientific)
        self.assertEqual(retry["transport_resume"]["semantic_delta"], transport)
        assignment = json.loads(retry["spawn_args"]["message"].split("Assignment:\n", 1)[1])
        self.assertEqual(assignment["scientific_resume"], scientific)
        self.assertEqual(assignment["transport_resume"], retry["transport_resume"])

    def test_metadata_renamed_exhausted_resume_rejected(self):
        state = self.state([task("A")])
        state["tasks"]["A"]["state"] = "held"
        value = delta()
        evidence = self.semantic_file(value)
        rc.resume(state, "A", evidence, "input-v1")
        packet = self.launch(state)
        self.result(state, packet, "blocker", issue=self.issue())
        self.assertEqual(state["tasks"]["A"]["state"], "held")
        value.update(label="renamed attempt", identity="new hash label", metadata={"label": "new"})
        value["after"]["sha256"] = "new-seal"
        evidence = self.semantic_file(value)
        old = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError):
            rc.resume(state, "A", evidence, "input-v1")
        self.assertEqual(state, old)

    def test_appended_packet_identity_binds_frontier_and_task_spec(self):
        old = self.state([task("OLD")])
        old["tasks"]["OLD"]["state"] = "held"
        first = copy.deepcopy(old)
        second = copy.deepcopy(old)
        self.append(first, [spec("NEW")])
        changed = spec("NEW")
        changed["semantic_delta"]["after"]["method"] = "different physical nuisance comparison"
        self.append(second, [changed])
        p = rc.next_packet(first, POLICY, PROFILES)
        q = rc.next_packet(second, POLICY, PROFILES)
        self.assertNotEqual(p["packet_id"], q["packet_id"])
        self.assertEqual(p["task_spec_identity"], rc.digest(first["tasks"]["NEW"]["spec"]))
        self.assertEqual(p["frontier_identity"], first["frontiers"][0]["identity"])
        # Old planned packets are returned exactly, never retroactively rebound.
        retained = copy.deepcopy(p)
        self.assertEqual(rc.next_packet(first, POLICY, PROFILES), retained)

    def test_invalid_append_is_atomic(self):
        for rows in ([spec("X",{"all":[{"task_id":"missing","evidence":"completed"}]})],
                     [spec("X",{"any":[{"task_id":"Y","evidence":"completed"}]}),
                      spec("Y",{"all":[{"task_id":"X","evidence":"completed"}]})],
                     [spec("OLD")], [spec("X",{"any":[]})]):
            state=self.state([task("OLD")]); old=copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError): self.append(state,rows)
            self.assertEqual(state,old)

    def test_review_must_qualify_candidate_products(self):
        state=self.state([task("A")]); p=self.launch(state)
        self.result(state,p,qualified_products=["confidence_bundle"])
        review=self.launch(state)
        self.result(state,review,acceptance_met=True)
        self.assertEqual(state["tasks"]["A"]["qualified_products"],[])
        state=self.state([task("A")]); p=self.launch(state); self.result(state,p)
        review=self.launch(state); old=copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError):
            self.result(state,review,acceptance_met=True,qualified_products=["confidence_bundle"])
        self.assertEqual(state,old)

    def test_label_hash_only_and_same_unused_repair_rejected(self):
        state=self.state([task("A")]); state["tasks"]["A"]["state"]="held"
        evidence=self.semantic_file(delta(before={"identity":"old"},after={"identity":"new"}))
        with self.assertRaises(rc.ControllerError): rc.resume(state,"A",evidence,"new")
        evidence=self.semantic_file(delta())
        with self.assertRaises(rc.ControllerError): rc.resume(state,"A",evidence,"input-v1","repair-1")
        rc.resume(state,"A",evidence,"input-v1")
        self.assertEqual(state["tasks"]["A"]["phase"],"research")

    def test_transport_restores_exact_unused_ultra_and_preserves_phase(self):
        state=self.state([task("A")]); p=self.launch(state)
        self.result(state,p,"blocker",issue=self.issue(high_consequence=True,risk="wrong result"))
        p=rc.next_packet(state,POLICY,PROFILES)
        refusal=self.semantic_file({"refusal":"temporary native transport"})
        rc.launch_failed(state,p["packet_id"],refusal,"transport","native temporary refusal")
        old=copy.deepcopy(state)
        evidence=self.semantic_file(delta("prelaunch_transport",packet_id=p["packet_id"],
            before={"transport":"refused"},after={"transport":"available"}))
        rc.resume(state,"A",evidence,"input-v1")
        self.assertEqual(state["tasks"]["A"]["phase"],"escalation")
        self.assertEqual(state["ultra_repairs"],old["ultra_repairs"])
        retry=rc.next_packet(state,POLICY,PROFILES)
        self.assertNotEqual(retry["packet_id"],p["packet_id"])
        self.assertEqual(retry["phase"],p["phase"])
        rc.acknowledge(state,retry["packet_id"],"new-agent")
        self.assertEqual(len(state["ultra_repairs"]),1)

    def test_acknowledged_unknown_not_replayed(self):
        state=self.state([task("A")]); p=self.launch(state)
        state["tasks"]["A"]["state"]="held" # Interrupted host with no recorded result.
        for kind in ("method","prelaunch_transport"):
            evidence=self.semantic_file(delta(kind,packet_id=p["packet_id"]))
            old=copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError):rc.resume(state,"A",evidence,"input-v1")
            self.assertEqual(state,old)


if __name__ == "__main__": unittest.main()
