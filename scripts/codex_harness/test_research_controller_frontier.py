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

    def followup_fixture(self, kind="numeric"):
        state = self.state([task("A", approved_repair_id=None, kind=kind)])
        author = self.launch(state)
        self.result(state, author)
        review = self.launch(state)
        self.result(state, review, "blocker", issue=self.issue(), repair_plan="Fix exact row and compare reference")
        repair = rc.next_packet(state, POLICY, PROFILES)
        agent = state["packets"][author["packet_id"]]["agent_id"]
        data = {"native_tool": "collaboration.followup_task", "task_id": "A", "agent_id": agent,
                "phase": "repair", "packet_id": repair["packet_id"], "input_identity": "input-v1",
                "repair_plan_identity": rc.digest(state["tasks"]["A"]["repair_plan"]),
                "base_packet_id": author["packet_id"], "base_candidate_identity": "candidate-v1",
                "candidate_identity": "candidate-v2"}
        raw = Path(self.tmp.name) / "followup-raw.json"
        raw.write_text(json.dumps(data))
        data.update(raw_receipt=str(raw), raw_receipt_sha256=rc._receipt(str(raw))["sha256"])
        evidence = Path(self.tmp.name) / "followup.json"
        evidence.write_text(json.dumps(data))
        return state, author, repair, agent, evidence, data

    def test_same_task_author_followup_and_fresh_independent_review(self):
        state, author, repair, agent, evidence, data = self.followup_fixture()
        old = copy.deepcopy(state)
        rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
        packet = state["packets"][repair["packet_id"]]
        self.assertEqual(packet["native_tool"], "collaboration.followup_task")
        self.assertEqual(packet["observed_runtime"], "UNKNOWN")
        self.assertEqual(packet["continuation"]["evidence"], rc._receipt(str(evidence)))
        self.assertEqual(state["events"][-1]["type"], "followup_acknowledged")
        for key in ("authors", "contributors", "ultra_used"):
            self.assertEqual(state["tasks"]["A"][key], old["tasks"]["A"][key])
        for key in ("campaign", "campaign_identity", "ultra_repairs", "ultra_pending", "turn"):
            self.assertEqual(state[key], old[key])
        for key in old["packets"]:
            if key != repair["packet_id"]:
                self.assertEqual(state["packets"][key], old["packets"][key])
        result = {"packet_id": repair["packet_id"], "task_id": "A", "agent_id": agent,
                  "input_identity": "input-v1", "raw_receipt": data["raw_receipt"], "outcome": "success",
                  "candidate_identity": "candidate-v2", "validation_evidence": ["reference agrees"]}
        for change in ({"candidate_identity": "candidate-v1"}, {"raw_receipt": str(evidence)}):
            snapshot = copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError):
                rc.record(state, {**result, **change}, POLICY)
            self.assertEqual(state, snapshot)
        rc.record(state, result, POLICY)
        review = rc.next_packet(state, POLICY, PROFILES)
        with self.assertRaises(rc.ControllerError):
            rc.acknowledge(state, review["packet_id"], agent, followup_evidence=str(evidence))
        rc.acknowledge(state, review["packet_id"], "fresh-independent-reviewer")
        self.result(state, review, acceptance_met=True, candidate_identity="candidate-v2")
        self.assertEqual(state["tasks"]["A"]["state"], "completed")

    def test_theory_execute_readonly_author_cannot_retarget_repair_profile(self):
        state, author, repair, agent, evidence, data = self.followup_fixture(kind="theory")
        self.assertEqual(author["route"]["route"], "review_or_research")
        self.assertEqual(author["route"]["transport_selected"],
                         {"model": "gpt-6-astra", "effort": "xhigh"})
        self.assertEqual(repair["route"]["route"], "subagent_specialist")
        self.assertEqual(repair["route"]["transport_selected"],
                         {"model": "gpt-6-sol", "effort": "high"})
        self.assertEqual(state["tasks"]["A"]["targeted_repairs"][0]["repair_plan"],
                         state["tasks"]["A"]["repair_plan"])
        snapshot = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, "implementation route/profile"):
            rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
        self.assertEqual(state, snapshot)

    def test_followup_cannot_change_requested_or_transport_profile_or_readonly_role(self):
        for mutation in ("requested", "transport_selected", "subagent_routine", "orchestrator"):
            state, author, repair, agent, evidence, data = self.followup_fixture()
            original = state["packets"][author["packet_id"]]["route"]
            if mutation in {"requested", "transport_selected"}:
                original[mutation] = {"model": "gpt-6.1-sol", "effort": "medium"}
            else:
                original["route"] = mutation
            snapshot = copy.deepcopy(state)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(
                    rc.ControllerError, "implementation route/profile"):
                rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
            self.assertEqual(state, snapshot)

    def test_followup_rejects_missing_stale_and_unbound_evidence_atomically(self):
        state, author, repair, agent, evidence, data = self.followup_fixture()
        old = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError):
            rc.acknowledge(state, repair["packet_id"], agent)
        self.assertEqual(state, old)
        for change in ({}, {"task_id": "other"}, {"agent_id": "other"}, {"phase": "execute"},
                       {"packet_id": author["packet_id"]}, {"input_identity": "stale-input"},
                       {"repair_plan_identity": "stale"}, {"base_candidate_identity": "stale"},
                       {"base_packet_id": "unknown"}, {"base_packet_id": {}}, {"raw_receipt": None},
                       {"candidate_identity": "candidate-v1"},
                       {"candidate_identity": ""}, {"raw_receipt_sha256": "wrong"},
                       {"native_tool": "collaboration.spawn_agent"}):
            value = {**data, **change} if change else {}
            evidence.write_text(json.dumps(value))
            with self.subTest(change=change), self.assertRaises(rc.ControllerError):
                rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
            self.assertEqual(state, old)
        # A correctly hashed receipt still has to contain matching input/candidate identities.
        raw = Path(data["raw_receipt"])
        for change in ({"input_identity": "stale"}, {"candidate_identity": "stale"}):
            raw.write_text(json.dumps({**data, **change}))
            evidence.write_text(json.dumps({**data, "raw_receipt_sha256": rc._receipt(str(raw))["sha256"]}))
            with self.assertRaises(rc.ControllerError):
                rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
            self.assertEqual(state, old)

    def test_followup_rejects_other_task_roles_and_unknown_outcomes(self):
        for mutation in ("other-task", "review", "escalation", "unknown", "no-plan", "execute",
                         "acquisition", "research", "new-thread"):
            state, author, repair, agent, evidence, data = self.followup_fixture()
            old_packet = state["packets"][author["packet_id"]]
            if mutation == "other-task":
                old_packet["task_id"] = "OTHER"
            elif mutation in {"review", "escalation"}:
                old_packet["phase"] = mutation
            elif mutation == "unknown":
                state["tasks"]["A"]["history"] = [e for e in state["tasks"]["A"]["history"]
                                                     if e["packet_id"] != author["packet_id"]]
            elif mutation == "no-plan":
                state["tasks"]["A"]["repair_plan"] = " "
            elif mutation == "new-thread":
                agent = "fresh-thread"
            else:
                state["tasks"]["A"]["phase"] = mutation
                state["packets"][repair["packet_id"]]["phase"] = mutation
            snapshot = copy.deepcopy(state)
            with self.subTest(mutation=mutation), self.assertRaises(rc.ControllerError):
                rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
            self.assertEqual(state, snapshot)

    def test_real_checkpoint_followup_preserves_historical_48_and_accounting(self):
        path = Path(__file__).resolve().parents[2] / ".agent-harness/runtime/r23-continuous/STATE.json"
        if not path.is_file():
            self.skipTest("owner production checkpoint unavailable")
        raw = path.read_bytes()
        state = json.loads(raw)
        if "R24-BOOST-ACCELERATION" not in state["tasks"]:
            self.skipTest("current followup frontier unavailable")
        t = state["tasks"]["R24-BOOST-ACCELERATION"]
        if t["phase"] != "repair" or t["state"] not in {"ready", "planned"}:
            self.skipTest("production repair already acknowledged")
        if t["state"] == "ready":
            # Other live branches can be running. Plan only in a disposable view,
            # then test acknowledgement against the full copied checkpoint.
            planning = copy.deepcopy(state)
            for key, other in planning["tasks"].items():
                if key != "R24-BOOST-ACCELERATION" and other["state"] != "completed":
                    other["state"] = "held"
            packet = rc.next_packet(planning, POLICY, PROFILES)
            self.assertEqual(packet["task_id"], "R24-BOOST-ACCELERATION")
            t = state["tasks"]["R24-BOOST-ACCELERATION"] = planning["tasks"]["R24-BOOST-ACCELERATION"]
            state["packets"][packet["packet_id"]] = planning["packets"][packet["packet_id"]]
        else:
            packet = state["packets"][t["packet_id"]]
        source = next(e for e in t["history"] if e["phase"] == "execute")
        agent = source["result"]["agent_id"]
        data = {"native_tool": "collaboration.followup_task", "task_id": packet["task_id"],
                "agent_id": agent, "phase": "repair", "packet_id": packet["packet_id"],
                "input_identity": packet["input_identity"], "repair_plan_identity": rc.digest(t["repair_plan"]),
                "base_packet_id": source["packet_id"], "base_candidate_identity": t["candidate_identity"],
                "candidate_identity": "fixture-new-candidate"}
        receipt = Path(__file__).resolve().parents[2] / (
            "docs/research_program/observational_publication_20261015/"
            "METHOD_EXECUTION_20261023/boost_acceleration/REPAIR_RAW_RECEIPT.json")
        if not receipt.is_file():
            self.skipTest("actual author repair receipt unavailable")
        data["candidate_identity"] = json.loads(receipt.read_text())["candidate_identity"]
        data.update(raw_receipt=str(receipt), raw_receipt_sha256=rc._receipt(str(receipt))["sha256"])
        evidence = self.semantic_file(data)
        old = copy.deepcopy(state)
        rc.acknowledge(state, packet["packet_id"], agent, followup_evidence=evidence)
        historical = list(old["tasks"])[:48]
        self.assertEqual({k: state["tasks"][k] for k in historical}, {k: old["tasks"][k] for k in historical})
        for key in ("campaign", "campaign_identity", "ultra_repairs", "ultra_pending", "turn"):
            self.assertEqual(state[key], old[key])
        for key in old["packets"]:
            if key != packet["packet_id"]:
                self.assertEqual(state["packets"][key], old["packets"][key])
        self.assertEqual(path.read_bytes(), raw)

    def test_acknowledged_unknown_not_replayed(self):
        state=self.state([task("A")]); p=self.launch(state)
        state["tasks"]["A"]["state"]="held" # Interrupted host with no recorded result.
        for kind in ("method","prelaunch_transport"):
            evidence=self.semantic_file(delta(kind,packet_id=p["packet_id"]))
            old=copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError):rc.resume(state,"A",evidence,"input-v1")
            self.assertEqual(state,old)


if __name__ == "__main__": unittest.main()
