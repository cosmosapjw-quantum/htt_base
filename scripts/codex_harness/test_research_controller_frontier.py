"""Append/reopening counterexamples; production state is read only and deep copied."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import test_research_controller as base
from test_research_controller import POLICY, PROFILES, task
_candidate_spec = importlib.util.spec_from_file_location(
    'r26_actual_review_candidate', Path(__file__).resolve().parent / 'research_controller.py')
rc = importlib.util.module_from_spec(_candidate_spec)
_candidate_spec.loader.exec_module(rc)
base.rc = rc


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
        routes = [spec("R1"), spec("R2"), spec("USE", {"any": [leaf("R1"), leaf("R2")]})]
        # Alternative scientific methods can supply the same product; aliases cannot.
        for row, method in zip(routes, ("linear nuisance marginalization", "calibration profile likelihood",
                                        "consume a reviewed confidence bundle")):
            row["semantic_delta"]["after"]["method"] = method
        self.append(state, routes)
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


class MinimalLifecycleRepairTests(unittest.TestCase):
    setUp = FrontierTests.setUp
    state = FrontierTests.state
    launch = FrontierTests.launch
    result = FrontierTests.result
    issue = FrontierTests.issue
    semantic_file = FrontierTests.semantic_file
    """Tiny metadata fixtures for the three frozen R29 lifecycle defects."""
    def test_save_two_hop_alias_and_new_file(self):
        root = Path(self.tmp.name)
        target = root / "durable" / "STATE.json"
        rc.save(target, {"generation": 1})
        middle, alias = root / "middle", root / "alias"
        middle.symlink_to(target)
        alias.symlink_to(middle)
        rc.save(alias, {"generation": 2})
        self.assertTrue(alias.is_symlink())
        self.assertTrue(middle.is_symlink())
        self.assertEqual(json.loads(target.read_text()), {"generation": 2})
        self.assertEqual(list(target.parent.glob(".controller-*")), [])

    def cli(self, path, *args):
        result = base.subprocess.run([base.sys.executable, "-B", str(Path(rc.__file__)),
            "--state", str(path), *args], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_cli_pins_two_hop_target_and_result_sidecar(self):
        root = Path(self.tmp.name)
        target = root / "durable" / "STATE.json"
        campaign = root / "campaign.json"
        campaign.write_text(json.dumps({"campaign_id": "alias-fixture", "tasks": [task("A")]}))
        self.cli(target, "init", "--campaign", str(campaign), "--authorization", "metadata only")
        middle, alias = root / "middle", root / "alias"
        middle.symlink_to(target)
        alias.symlink_to(middle)
        args = [part for model, effort in sorted(PROFILES)
                for part in ("--available-profile", model + "/" + effort)]
        packet = self.cli(alias, "next", *args)
        self.cli(alias, "ack", "--packet-id", packet["packet_id"], "--agent-id", "fixture-author")
        raw = root / "raw.json"; raw.write_text('{"metadata":"actual fixture result"}')
        result = {"packet_id": packet["packet_id"], "task_id": "A", "agent_id": "fixture-author",
                  "input_identity": "input-v1", "raw_receipt": str(raw), "outcome": "success",
                  "candidate_identity": "fixture-candidate", "validation_evidence": ["fixture control"]}
        result_path = root / "result.json"; result_path.write_text(json.dumps(result))
        self.cli(alias, "record", "--result", str(result_path))
        self.assertTrue(alias.is_symlink()); self.assertTrue(middle.is_symlink())
        self.assertTrue((target.parent / "STATE.json.results" / (rc.digest(result) + ".json")).is_file())
        self.assertFalse((root / "alias.results").exists())
        self.assertEqual(json.loads(target.read_text())["tasks"]["A"]["phase"], "review")
        self.assertEqual(self.cli(alias, "summary"), self.cli(target, "summary"))

    def test_prohibited_and_exhausted_ordinary_transport_atomic(self):
        for reason, prohibited in (("owner prohibits retry", True), ("exhausted monthly quota", False)):
            state = self.state([task("A", approved_repair_id=None)])
            packet = rc.next_packet(state, POLICY, PROFILES)
            evidence = self.semantic_file({"refused": reason})
            rc.launch_failed(state, packet["packet_id"], evidence, "transport", reason, prohibited)
            self.assertTrue(state["tasks"]["A"]["hold"]["retry_prohibited"])
            evidence = self.semantic_file(delta("prelaunch_transport", packet_id=packet["packet_id"],
                before={"transport": "refused"}, after={"transport": "available"}))
            old = copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError):
                rc.resume(state, "A", evidence, "input-v1")
            self.assertEqual(state, old)

    def initial_failure_fixture(self, plan):
        state = self.state([task("A", approved_repair_id=None)])
        state["tasks"]["A"]["accounting"] = {"seconds": 17.25, "tokens": 13}
        state["ultra_repairs"]["historical-used"] = {"task_id": "OLD"}
        state["ultra_pending"]["historical-pending"] = {"task_id": "OLD"}
        author = self.launch(state)
        self.result(state, author, "blocker", candidate_identity=None,
                    issue=self.issue(**{"class": "code"}))
        research = self.launch(state)
        self.result(state, research, repair_plan=plan, candidate_identity=None)
        repair = rc.next_packet(state, POLICY, PROFILES)
        agent = state["packets"][author["packet_id"]]["agent_id"]
        source = state["tasks"]["A"]["history"][0]
        data = {"status": "dispatched", "native_tool": "collaboration.followup_task", "task_id": "A",
                "agent_id": agent, "phase": "repair", "packet_id": repair["packet_id"],
                "input_identity": "input-v1", "repair_plan_identity": rc.digest(plan),
                "base_packet_id": author["packet_id"], "base_candidate_identity": None,
                "base_raw_receipt": copy.deepcopy(source["receipt"]),
                "requested": repair["route"]["requested"],
                "transport_selected": repair["route"]["transport_selected"]}
        host = Path(self.tmp.name) / "host.json"
        host.write_text(json.dumps({"dispatch_accepted": True, **{k:data[k] for k in
            ("native_tool", "agent_id", "packet_id", "task_id", "input_identity")}}))
        data.update(host_call_receipt=str(host), host_call_receipt_sha256=rc._receipt(str(host))["sha256"])
        evidence = Path(self.tmp.name) / "followup.json"; evidence.write_text(json.dumps(data))
        return state, author, repair, agent, evidence, data

    def test_initial_failure_structured_and_string_plan_review(self):
        for plan in ({"repair": "correct initial control"}, "correct initial control"):
            state, author, repair, agent, evidence, data = self.initial_failure_fixture(plan)
            if isinstance(plan, str):
                data.pop("base_candidate_identity")
                evidence.write_text(json.dumps(data))
            old = copy.deepcopy(state)
            rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
            for field in ("campaign", "campaign_identity", "ultra_repairs", "ultra_pending", "turn"):
                self.assertEqual(state[field], old[field])
            for field in ("history", "authors", "contributors", "failures", "accounting", "attempt"):
                self.assertEqual(state["tasks"]["A"][field], old["tasks"]["A"][field])
            self.assertEqual(state["packets"][repair["packet_id"]]["observed_runtime"], "UNKNOWN")
            after_ack = copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError):
                rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
            self.assertEqual(state, after_ack)
            result = {"packet_id": repair["packet_id"], "task_id": "A", "agent_id": agent,
                "input_identity": "input-v1", "base_packet_id": author["packet_id"],
                "base_candidate_identity": None, "base_raw_receipt": data["base_raw_receipt"],
                "outcome": "success", "candidate_identity": "actual-new-candidate",
                "validation_evidence": ["new control passed"]}
            raw = Path(self.tmp.name) / "new-outcome.json"; raw.write_text(json.dumps(result))
            result["raw_receipt"] = str(raw)
            for change in ({"candidate_identity": None}, {"base_packet_id": "wrong"},
                           {"base_raw_receipt": {}}, {"raw_receipt": data["base_raw_receipt"]["path"]}):
                with self.assertRaises(rc.ControllerError): rc.record(state, {**result, **change}, POLICY)
                self.assertEqual(state, after_ack)
            rc.record(state, result, POLICY)
            after_record = copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError): rc.record(state, result, POLICY)
            self.assertEqual(state, after_record)
            review = rc.next_packet(state, POLICY, PROFILES)
            with self.assertRaises(rc.ControllerError): rc.acknowledge(state, review["packet_id"], agent)
            rc.acknowledge(state, review["packet_id"], "fresh-independent-reviewer")
            self.result(state, review, acceptance_met=True, candidate_identity="actual-new-candidate")
            self.assertEqual(state["tasks"]["A"]["state"], "completed")

    def test_initial_failure_followup_rejects_mutations_atomically(self):
        changes = ("plan", "receipt", "input", "agent", "route", "unknown", "unacknowledged",
                   "environment", "nonsubstantive", "source-candidate", "task-candidate", "packet-candidate",
                   "prior-success", "not-latest", "not-dispatched", "fake-base-candidate", "source-input",
                   "source-agent", "source-packet", "raw-drift", "host-not-accepted", "host-hash", "research-candidate")
        for change in changes:
            state, author, repair, agent, evidence, data = self.initial_failure_fixture({"repair": "control"})
            t = state["tasks"]["A"]; source = t["history"][0]
            if change == "plan": data["repair_plan_identity"] = "wrong"
            if change == "receipt": data["base_raw_receipt"] = {**data["base_raw_receipt"], "sha256": "wrong"}
            if change == "input": data["input_identity"] = "wrong"
            if change == "agent": data["agent_id"] = "wrong"
            if change == "route": state["packets"][author["packet_id"]]["route"]["requested"] = {"model": "wrong"}
            if change == "unknown": t["history"].pop(0)
            if change == "unacknowledged": state["packets"][author["packet_id"]]["launch_performed"] = False
            if change == "environment": source["result"]["issue"]["class"] = "environment"
            if change == "nonsubstantive": source["result"]["issue"]["substantive"] = False
            if change == "source-candidate": source["result"]["candidate_identity"] = "fake"
            if change == "task-candidate": t["candidate_identity"] = "fake"
            if change == "packet-candidate": state["packets"][repair["packet_id"]]["candidate_identity"] = "fake"
            if change == "research-candidate": t["history"][1]["result"]["candidate_identity"] = "fake-success"
            if change == "prior-success": t["history"].insert(0, {**copy.deepcopy(source), "result": {
                **source["result"], "outcome": "success", "candidate_identity": "old-success"}})
            if change == "not-latest": t["history"].append({**copy.deepcopy(source), "packet_id": "newer-author"})
            if change == "not-dispatched": data["status"] = "returned"
            if change == "fake-base-candidate": data["base_candidate_identity"] = "NO_CANDIDATE"
            if change == "source-input": source["result"]["input_identity"] = "wrong"
            if change == "source-agent": source["result"]["agent_id"] = "wrong"
            if change == "source-packet": source["result"]["packet_id"] = "wrong"
            if change == "raw-drift": Path(data["base_raw_receipt"]["path"]).write_text("changed raw bytes")
            if change == "host-hash": data["host_call_receipt_sha256"] = "wrong"
            if change == "host-not-accepted":
                host = Path(data["host_call_receipt"])
                host.write_text(json.dumps({**json.loads(host.read_text()), "dispatch_accepted": False}))
                data["host_call_receipt_sha256"] = rc._receipt(str(host))["sha256"]
            evidence.write_text(json.dumps(data)); old = copy.deepcopy(state)
            with self.subTest(change=change), self.assertRaises(rc.ControllerError):
                rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
            self.assertEqual(state, old)

    def test_successful_base_dispatched_followup_unchanged(self):
        state, author, repair, agent, evidence, data = FrontierTests.followup_fixture(self)
        data.update(status="dispatched", requested=repair["route"]["requested"],
                    transport_selected=repair["route"]["transport_selected"])
        host = Path(self.tmp.name) / "host-dispatch.json"
        host.write_text(json.dumps({"dispatch_accepted": True, **{k:data[k] for k in
            ("native_tool", "agent_id", "packet_id", "task_id", "input_identity")}}))
        data.update(host_call_receipt=str(host), host_call_receipt_sha256=rc._receipt(str(host))["sha256"])
        evidence.write_text(json.dumps(data))
        rc.acknowledge(state, repair["packet_id"], agent, followup_evidence=str(evidence))
        continuation = state["packets"][repair["packet_id"]]["continuation"]
        self.assertEqual(continuation["base_candidate_identity"], "candidate-v1")
        self.assertNotIn("base_raw_receipt", continuation)

    def test_empty_or_wrong_plan_rejected_at_record(self):
        for plan in (" ", {}, [], ["repair"], True, 7):
            state = self.state([task("A", approved_repair_id=None)])
            self.result(state, self.launch(state), "blocker", candidate_identity=None, issue=self.issue())
            research = self.launch(state); old = copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError): self.result(state, research, repair_plan=plan)
            self.assertEqual(state, old)


class ConcurrentReviewTests(unittest.TestCase):
    """Host-only fixture transitions; no real acquisition or review is launched."""
    setUp = base.ControllerTests.setUp
    state = base.ControllerTests.state
    launch = base.ControllerTests.launch
    def result(self, state, packet, outcome="success", **kwargs):
        if "candidate_identity" not in kwargs:
            if packet["phase"] == "review":
                kwargs["candidate_identity"] = state["tasks"][packet["task_id"]]["candidate_identity"]
            elif packet["phase"] == "execute" and packet["task_id"] in {"CANDIDATE", "SECOND"}:
                import hashlib
                artifact = Path(state["tasks"][packet["task_id"]]["spec"]["owned_paths"][0]) / 'CANDIDATE.json'
                kwargs["candidate_identity"] = 'sha256:' + hashlib.sha256(artifact.read_bytes()).hexdigest()
                kwargs.setdefault("qualified_products", [str(artifact)])
        return base.ControllerTests.result(self, state, packet, outcome, **kwargs)
    issue = base.ControllerTests.issue

    def fixture(self, state=None, second=True):
        root = Path(self.tmp.name)
        source = root / 'frozen.csv'
        source.write_text('frozen input\n')
        contract = root / 'INPUT.json'
        contract.write_text(json.dumps({'input_sources': [{'path': str(source)}]}))
        rows = []
        for key, kind in [('CANDIDATE', 'numeric'), ('SECOND', 'numeric'),
                          ('Z-ACQUIRE', 'input'), ('SMICA', 'numeric')]:
            if key == 'SECOND' and not second:
                continue
            owned = root / key
            owned.mkdir(exist_ok=True)
            (owned / 'CANDIDATE.json').write_text(json.dumps({'value': 1, 'method': key}))
            row = task(key, kind=kind, owned_paths=[str(owned)], input_sources=[str(contract)])
            rows.append(row)
        if state is None:
            state = self.state(rows)
        else:
            for row in rows:
                row.update(contract_origin='new_conditional_research', promotes_original_acceptance=False,
                           approved_repair_id=None, requires={'all': []},
                           semantic_delta=delta(after={'method': 'fixture bounded method for ' + row['id']}))
            rc.append_frontier(state, {'frontier_id': 'concurrent-review-fixture', 'tasks': rows}, 'fixture owner')
        state['tasks']['SMICA']['last_turn'] = 10000
        self.result(state, self.launch(state))
        if second:
            self.result(state, self.launch(state))
        acquisition = self.launch(state)
        self.assertEqual(acquisition['task_id'], 'Z-ACQUIRE')
        self.assertEqual(acquisition['phase'], 'acquisition')
        return state, acquisition

    def plan(self, state):
        packet = rc.next_packet(state, POLICY, PROFILES, review_only=True)
        self.assertEqual(packet.get('task_id'), 'CANDIDATE')
        self.assertEqual(packet['phase'], 'review')
        return packet

    def test_explicit_plan_replay_ack_poll_and_no_second_review(self):
        state, acquisition = self.fixture()
        owner = copy.deepcopy(state['tasks']['Z-ACQUIRE'])
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES))
        packet = self.plan(state)
        self.assertTrue(packet['review_only'])
        self.assertEqual(packet, rc.next_packet(state, POLICY, PROFILES, review_only=True))
        self.assertEqual(packet, rc.next_packet(state, POLICY, PROFILES))
        rc.acknowledge(state, packet['packet_id'], 'fresh-read-only-reviewer')
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES, review_only=True))
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES))
        self.assertEqual(state['tasks']['Z-ACQUIRE'], owner)
        self.assertEqual(state['packets'][acquisition['packet_id']]['observed_runtime'], 'UNKNOWN')

    def test_unknown_missing_and_overlapping_declared_scopes_wait(self):
        for change in ('missing-input', 'missing-owned', 'overlap-owned', 'nested-input', 'symlink-input'):
            with self.subTest(change=change):
                state, _ = self.fixture(second=False)
                spec = state['tasks']['CANDIDATE']['spec']
                if change == 'missing-input':
                    spec['input_sources'] = [str(Path(self.tmp.name) / 'absent-input')]
                elif change == 'missing-owned':
                    state['tasks']['Z-ACQUIRE']['spec']['owned_paths'] = []
                elif change == 'overlap-owned':
                    state['tasks']['Z-ACQUIRE']['spec']['owned_paths'] = spec['owned_paths']
                else:
                    target = Path(state['tasks']['Z-ACQUIRE']['spec']['owned_paths'][0]) / 'being-written.csv'
                    target.write_text('partial acquisition')
                    if change == 'symlink-input':
                        link = Path(self.tmp.name) / 'input-link.csv'
                        link.symlink_to(target)
                        spec['input_sources'] = [str(link)]
                    else:
                        Path(spec['input_sources'][0]).write_text(json.dumps({'sources': [{'path': str(target)}]}))
                before = copy.deepcopy(state)
                self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES, review_only=True))
                self.assertEqual(state, before)

    def test_running_writer_or_planned_discovery_prevents_review(self):
        for other in ('execute', 'repair', 'acquisition', 'research', 'escalation', 'discovery'):
            with self.subTest(other=other):
                state, _ = self.fixture(second=False)
                if other == 'discovery':
                    rc.enable_adaptive(state, 'fixture owner')
                    state['adaptive']['packets']['pending'] = {'state': 'planned'}
                else:
                    state['tasks']['SMICA'].update(state='running', phase=other)
                before = copy.deepcopy(state)
                self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES, review_only=True))
                self.assertEqual(state, before)

    def test_no_review_means_no_writer_and_no_discovery(self):
        owned = Path(self.tmp.name) / 'acquisition-only'
        owned.mkdir()
        state = self.state([task('ACQUIRE', kind='input', owned_paths=[str(owned)]), task('SMICA')])
        state['tasks']['SMICA']['last_turn'] = 10000
        self.launch(state)
        rc.enable_adaptive(state, 'fixture owner')
        before = copy.deepcopy(state)
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES, review_only=True))
        self.assertEqual(state, before)
        self.assertFalse(state['adaptive']['packets'])

    def test_ack_rechecks_candidate_inputs_dependencies_owner_and_freshness_atomically(self):
        for change in ('candidate', 'input', 'contract-bytes', 'owner-paths', 'new-writer',
                       'dependency', 'author', 'reused', 'route', 'replacement-acquisition'):
            with self.subTest(change=change):
                state, acquisition = self.fixture(second=False)
                packet = self.plan(state)
                agent = 'fresh-read-only-reviewer'
                if change == 'candidate':
                    state['tasks']['CANDIDATE']['candidate_identity'] = 'changed candidate'
                elif change == 'input':
                    state['tasks']['CANDIDATE']['spec']['input_identity'] = 'changed input'
                elif change == 'contract-bytes':
                    Path(state['tasks']['CANDIDATE']['spec']['input_sources'][0]).write_text('{"changed":true}')
                elif change == 'owner-paths':
                    state['tasks']['Z-ACQUIRE']['spec']['owned_paths'] = state['tasks']['CANDIDATE']['spec']['owned_paths']
                elif change == 'new-writer':
                    self.result(state, acquisition, candidate_identity='acquired-v1')
                    state['tasks']['SMICA'].update(state='running', phase='execute')
                elif change == 'replacement-acquisition':
                    replacement = copy.deepcopy(state['packets'][acquisition['packet_id']])
                    replacement['packet_id'] = 'different-acquisition-packet'
                    state['packets'][replacement['packet_id']] = replacement
                    state['tasks']['Z-ACQUIRE']['packet_id'] = replacement['packet_id']
                elif change == 'dependency':
                    state['tasks']['CANDIDATE']['spec']['requires'] = {'all': [{'task_id': 'SMICA', 'evidence': 'completed'}]}
                elif change == 'author':
                    agent = state['tasks']['CANDIDATE']['authors'][0]
                elif change == 'reused':
                    agent = state['packets'][acquisition['packet_id']]['agent_id']
                else:
                    state['packets'][packet['packet_id']]['route']['route'] = 'general_code'
                before = copy.deepcopy(state)
                with self.assertRaises(rc.ControllerError):
                    rc.acknowledge(state, packet['packet_id'], agent)
                self.assertEqual(state, before)

    def test_result_orders_preserve_other_owner_and_writer_free_ack(self):
        for acquisition_first in (True, False):
            with self.subTest(acquisition_first=acquisition_first):
                state, acquisition = self.fixture(second=False)
                packet = self.plan(state)
                if acquisition_first:
                    self.result(state, acquisition, candidate_identity='acquired-v1')
                    owner = copy.deepcopy(state['tasks']['Z-ACQUIRE'])
                    rc.acknowledge(state, packet['packet_id'], 'fresh-reviewer-after-acquisition')
                    self.result(state, packet, acceptance_met=True)
                    self.assertEqual(state['tasks']['Z-ACQUIRE'], owner)
                else:
                    rc.acknowledge(state, packet['packet_id'], 'fresh-reviewer-during-acquisition')
                    owner = copy.deepcopy(state['tasks']['Z-ACQUIRE'])
                    self.result(state, packet, acceptance_met=True)
                    self.assertEqual(state['tasks']['Z-ACQUIRE'], owner)
                    reviewed = copy.deepcopy(state['tasks']['CANDIDATE'])
                    self.result(state, acquisition, candidate_identity='acquired-v1')
                    self.assertEqual(state['tasks']['CANDIDATE'], reviewed)
                self.assertEqual(state['tasks']['CANDIDATE']['state'], 'completed')
                self.assertEqual(state['tasks']['Z-ACQUIRE']['phase'], 'review')

    def test_review_refusal_or_failure_preserves_acquisition_and_holds_repair(self):
        for refused in (True, False):
            with self.subTest(refused=refused):
                state, _ = self.fixture(second=False)
                packet = self.plan(state)
                owner = copy.deepcopy(state['tasks']['Z-ACQUIRE'])
                if refused:
                    receipt = Path(self.tmp.name) / 'review-refusal.json'
                    receipt.write_text('{"native_refusal":"temporary"}')
                    rc.launch_failed(state, packet['packet_id'], str(receipt), 'transport', 'temporary refusal')
                else:
                    rc.acknowledge(state, packet['packet_id'], 'fresh-failing-reviewer')
                    self.result(state, packet, 'blocker', issue=self.issue(), repair_plan='Concrete deterministic closeout')
                    self.assertEqual(state['tasks']['CANDIDATE']['phase'], 'repair')
                self.assertEqual(state['tasks']['Z-ACQUIRE'], owner)
                self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES))
                self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES, review_only=True))

    def test_unsupported_review_transport_does_not_mutate_or_issue_writer(self):
        state, _ = self.fixture(second=False)
        before = copy.deepcopy(state)
        result = rc.next_packet(state, POLICY, {('gpt-6-sol', 'high')}, review_only=True)
        self.assertNotIn('spawn_args', result)
        self.assertEqual(state, before)

    def test_review_only_cli_reserves_only_read_only_candidate(self):
        import subprocess
        import sys
        state, _ = self.fixture(second=False)
        checkpoint = Path(self.tmp.name) / 'STATE.json'
        policy = Path(self.tmp.name) / 'POLICY.json'
        checkpoint.write_text(json.dumps(state))
        policy.write_text(json.dumps(POLICY))
        command = [sys.executable, str(Path(rc.__file__)), '--state', str(checkpoint),
                   '--policy', str(policy), 'next', '--review-only',
                   '--available-profile', 'gpt-6-astra/xhigh']
        result = subprocess.run(command, text=True, capture_output=True, check=True, timeout=15)
        packet = json.loads(result.stdout)
        self.assertEqual(packet['phase'], 'review')
        self.assertTrue(packet['review_only'])
        self.assertFalse(packet['launch_performed'])
        after = json.loads(checkpoint.read_text())
        self.assertEqual(state['tasks']['Z-ACQUIRE'], after['tasks']['Z-ACQUIRE'])

    def test_scoped_62_baseline_preserves_old_campaign_packets_and_accounting(self):
        path = Path(__file__).resolve().parents[2] / '.agent-harness/runtime/r23-continuous/r25/STATE_BEFORE.json'
        if not path.is_file():
            self.skipTest('owner frozen 62-task snapshot unavailable')
        state = json.loads(path.read_text())
        before = copy.deepcopy(state)
        self.assertEqual(len(state['tasks']), 62)
        state, _ = self.fixture(state, second=False)
        packet = self.plan(state)
        rc.acknowledge(state, packet['packet_id'], 'fresh-frozen-baseline-reviewer')
        self.result(state, packet, acceptance_met=True)
        for field in ('campaign', 'campaign_identity', 'ultra_repairs', 'ultra_pending'):
            self.assertEqual(state[field], before[field])
        for key, value in before['tasks'].items():
            self.assertEqual(state['tasks'][key], value)
        for key, value in before['packets'].items():
            self.assertEqual(state['packets'][key], value)

    def test_declared_nested_contract_acquisition_overlap_waits(self):
        state, _ = self.fixture(second=False)
        contract = Path(state['tasks']['CANDIDATE']['spec']['input_sources'][0])
        child = contract.parent / 'CHILD.json'
        acquired = Path(state['tasks']['Z-ACQUIRE']['spec']['owned_paths'][0]) / 'data.csv'
        acquired.write_text('in-progress acquisition')
        contract.write_text(json.dumps({'input_sources': [str(child)]}))
        child.write_text(json.dumps({'input_sources': [{'path': str(acquired)}]}))
        before = copy.deepcopy(state)
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES, review_only=True))
        self.assertEqual(state, before)

    def test_nested_contract_mutations_reject_ack_even_when_new_path_is_disjoint(self):
        for overlap in (True, False):
            with self.subTest(overlap=overlap):
                state, _ = self.fixture(second=False)
                contract = Path(state['tasks']['CANDIDATE']['spec']['input_sources'][0])
                child = contract.parent / 'CHILD.json'
                safe = contract.parent / 'frozen.csv'
                contract.write_text(json.dumps({'input_sources': [str(child)]}))
                child.write_text(json.dumps({'input_sources': [str(safe)]}))
                packet = self.plan(state)
                destination = (Path(state['tasks']['Z-ACQUIRE']['spec']['owned_paths'][0]) / 'data.csv'
                               if overlap else contract.parent / 'different-safe-input.csv')
                destination.write_text('changed child dependency')
                child.write_text(json.dumps({'input_sources': [str(destination)]}))
                before = copy.deepcopy(state)
                with self.assertRaises(rc.ControllerError):
                    rc.acknowledge(state, packet['packet_id'], 'fresh-nested-contract-reviewer')
                self.assertEqual(state, before)

    def test_candidate_bytes_are_bound_not_only_candidate_identity_label(self):
        state, _ = self.fixture(second=False)
        state['tasks']['CANDIDATE']['candidate_products'] = ['CANDIDATE.json']
        artifact = Path(state['tasks']['CANDIDATE']['spec']['owned_paths'][0]) / 'CANDIDATE.json'
        packet = self.plan(state)
        artifact.write_text('{"value":999}')
        before = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError):
            rc.acknowledge(state, packet['packet_id'], 'fresh-artifact-reviewer')
        self.assertEqual(state, before)

    def test_unmatched_candidate_identity_waits_without_state_mutation(self):
        state, _ = self.fixture(second=False)
        state['tasks']['CANDIDATE']['candidate_identity'] = 'sha256:' + '0' * 64
        before = copy.deepcopy(state)
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES, review_only=True))
        self.assertEqual(state, before)

    def test_manifest_identity_binds_product_bytes_at_plan_and_ack(self):
        import hashlib
        for stale_before_plan in (True, False):
            with self.subTest(stale_before_plan=stale_before_plan):
                state, _ = self.fixture(second=False)
                task_row = state['tasks']['CANDIDATE']
                directory = Path(task_row['spec']['owned_paths'][0])
                artifact = directory / 'CANDIDATE.json'
                manifest = directory / 'MANIFEST.json'
                manifest.write_text(json.dumps({'task_id': 'CANDIDATE', 'input_identity': 'input-v1',
                    'products_sha256': {'CANDIDATE.json': hashlib.sha256(artifact.read_bytes()).hexdigest()}}))
                task_row['candidate_identity'] = 'sha256:' + hashlib.sha256(manifest.read_bytes()).hexdigest()
                task_row['candidate_products'] = []
                if stale_before_plan:
                    artifact.write_text('{"value":999}')
                    before = copy.deepcopy(state)
                    self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES, review_only=True))
                    self.assertEqual(state, before)
                else:
                    packet = self.plan(state)
                    artifact.write_text('{"value":999}')
                    before = copy.deepcopy(state)
                    with self.assertRaises(rc.ControllerError):
                        rc.acknowledge(state, packet['packet_id'], 'fresh-manifest-reviewer')
                    self.assertEqual(state, before)

    def manifest_fixture(self, inventory="files", as_list=False):
        import hashlib
        as_list = as_list or inventory == "inventory"
        state, acquisition = self.fixture(second=False)
        row = state["tasks"]["CANDIDATE"]
        directory = Path(row["spec"]["owned_paths"][0])
        artifact = directory / "compute.py"
        artifact.write_text("frozen implementation\n")
        declaration = {"sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                       "size_bytes": artifact.stat().st_size}
        entries = [{"path": artifact.name, **declaration}] if as_list else {artifact.name: declaration}
        manifest = directory / "MANIFEST.json"
        manifest.write_text(json.dumps({"task_id": "CANDIDATE", "input_identity": "input-v1",
                                        inventory: entries}))
        row.update(candidate_identity="sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest(),
                   candidate_products=[])
        return state, acquisition, artifact, manifest

    def test_all_manifest_inventory_forms_unchanged_plan_ack_record(self):
        for inventory, as_list in (("files", False), ("files", True),
                                   ("products_sha256", False), ("products", False),
                                   ("inventory", True)):
            with self.subTest(inventory=inventory, as_list=as_list):
                state, _, artifact, _ = self.manifest_fixture(inventory, as_list)
                packet = self.plan(state)
                self.assertIn(str(artifact), packet["review_context"]["scope"]["candidate_seals"])
                rc.acknowledge(state, packet["packet_id"], "actual-independent-reviewer")
                self.result(state, packet, acceptance_met=True)
                self.assertEqual(state["tasks"]["CANDIDATE"]["state"], "completed")

    def test_all_manifest_inventories_mutation_or_removal_before_ack_rejects_atomically(self):
        for inventory in ("files", "products_sha256", "products", "inventory"):
            for remove in (False, True):
                with self.subTest(inventory=inventory, remove=remove):
                    state, _, artifact, _ = self.manifest_fixture(inventory)
                    packet = self.plan(state)
                    if remove:
                        artifact.unlink()
                    else:
                        artifact.write_text("changed implementation\n")
                    before = copy.deepcopy(state)
                    self.assertNotIn("spawn_args", rc.next_packet(state, POLICY, PROFILES, review_only=True))
                    self.assertEqual(state, before)
                    with self.assertRaises(rc.ControllerError):
                        rc.acknowledge(state, packet["packet_id"], "actual-independent-reviewer")
                    self.assertEqual(state, before)

    def test_all_manifest_inventories_mutation_after_ack_rejects_outcome_atomically(self):
        for inventory in ("files", "products_sha256", "products", "inventory"):
            for outcome in ("success", "blocker"):
                with self.subTest(inventory=inventory, outcome=outcome):
                    state, _, artifact, _ = self.manifest_fixture(inventory)
                    packet = self.plan(state)
                    rc.acknowledge(state, packet["packet_id"], "actual-independent-reviewer")
                    artifact.write_text("changed after actual review ACK\n")
                    before = copy.deepcopy(state)
                    with self.assertRaises(rc.ControllerError):
                        self.result(state, packet, outcome, acceptance_met=True, issue=self.issue())
                    self.assertEqual(state, before)
                    self.assertEqual(state["tasks"]["CANDIDATE"]["state"], "running")

    def test_missing_malformed_candidate_or_changed_input_after_ack_rejects_outcome(self):
        for change in ("remove", "malformed_manifest", "input"):
            with self.subTest(change=change):
                state, _, artifact, manifest = self.manifest_fixture()
                packet = self.plan(state)
                rc.acknowledge(state, packet["packet_id"], "actual-independent-reviewer")
                if change == "remove":
                    artifact.unlink()
                elif change == "malformed_manifest":
                    manifest.write_text("{malformed")
                else:
                    Path(state["tasks"]["CANDIDATE"]["spec"]["input_sources"][0]).write_text("{}")
                before = copy.deepcopy(state)
                with self.assertRaises(rc.ControllerError):
                    self.result(state, packet, acceptance_met=True)
                self.assertEqual(state, before)

    def test_mixed_manifest_inventories_bind_every_file_and_reject_conflicts(self):
        import hashlib
        for conflict in (False, True):
            state, _, artifact, manifest = self.manifest_fixture()
            document = json.loads(manifest.read_text())
            other = artifact.with_name("RESULT.txt")
            other.write_text("independent result bytes\n")
            document["products_sha256"] = {other.name: hashlib.sha256(other.read_bytes()).hexdigest()}
            document["products"] = {artifact.name: {"sha256": "0" * 64 if conflict else
                hashlib.sha256(artifact.read_bytes()).hexdigest()}}
            manifest.write_text(json.dumps(document))
            state["tasks"]["CANDIDATE"]["candidate_identity"] = "sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest()
            if conflict:
                before = copy.deepcopy(state)
                self.assertNotIn("spawn_args", rc.next_packet(state, POLICY, PROFILES, review_only=True))
                self.assertEqual(state, before)
            else:
                packet = self.plan(state)
                seals = packet["review_context"]["scope"]["candidate_seals"]
                self.assertTrue({str(artifact), str(other)} <= seals.keys())
                # files and products must remain bound even when products_sha256 is present.
                artifact.write_text("changed first inventory\n")
                before = copy.deepcopy(state)
                with self.assertRaises(rc.ControllerError):
                    rc.acknowledge(state, packet["packet_id"], "actual-independent-reviewer")
                self.assertEqual(state, before)

    def test_malformed_present_inventory_cannot_hide_behind_another_valid_inventory(self):
        import hashlib
        for malformed in (None, "not-an-inventory", [{"sha256": "0" * 64}], {"compute.py": {"bytes": 1}}):
            state, _, artifact, manifest = self.manifest_fixture("products_sha256")
            document = json.loads(manifest.read_text())
            document["files"] = malformed
            manifest.write_text(json.dumps(document))
            state["tasks"]["CANDIDATE"]["candidate_identity"] = "sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest()
            before = copy.deepcopy(state)
            self.assertNotIn("spawn_args", rc.next_packet(state, POLICY, PROFILES, review_only=True))
            self.assertEqual(state, before)

    def test_conflicting_embedded_path_or_size_declarations_rejects(self):
        import hashlib
        for conflict in ("path", "size_bytes", "bytes"):
            state, _, artifact, manifest = self.manifest_fixture()
            document = json.loads(manifest.read_text())
            if conflict == "path":
                other = artifact.with_name("DIFFERENT.txt")
                other.write_text("different declared product")
                document["files"][artifact.name]["path"] = other.name
            else:
                document["files"][artifact.name][conflict] = artifact.stat().st_size + 1
            manifest.write_text(json.dumps(document))
            state["tasks"]["CANDIDATE"]["candidate_identity"] = "sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest()
            before = copy.deepcopy(state)
            self.assertNotIn("spawn_args", rc.next_packet(state, POLICY, PROFILES, review_only=True))
            self.assertEqual(state, before)

    def test_ordinary_review_retains_existing_record_semantics(self):
        state, _, artifact, _ = self.manifest_fixture()
        state["tasks"]["Z-ACQUIRE"]["state"] = "completed"  # Fixture writer slot is free.
        packet = rc.next_packet(state, POLICY, PROFILES)
        self.assertEqual(packet["phase"], "review")
        self.assertFalse(packet.get("review_only"))
        rc.acknowledge(state, packet["packet_id"], "actual-independent-reviewer")
        artifact.write_text("ordinary review compatibility fixture\n")
        self.result(state, packet, acceptance_met=True)
        self.assertEqual(state["tasks"]["CANDIDATE"]["state"], "completed")

    def test_nested_contract_traversal_bound_waits_without_prose_scans(self):
        state, _ = self.fixture(second=False)
        contract = Path(state['tasks']['CANDIDATE']['spec']['input_sources'][0])
        current = contract
        for index in range(18):
            child = contract.parent / ('nested-' + str(index) + '.json')
            current.write_text(json.dumps({'input_sources': [str(child)]}))
            current = child
        current.write_text('{"description":"prose is not a filesystem declaration"}')
        before = copy.deepcopy(state)
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES, review_only=True))
        self.assertEqual(state, before)

    def test_live_auxiliary_and_distance_have_provable_candidate_bindings(self):
        path = Path(__file__).resolve().parents[2] / '.agent-harness/runtime/r23-continuous/STATE.json'
        if not path.is_file():
            self.skipTest('owner live checkpoint unavailable')
        raw = path.read_bytes()
        state = json.loads(raw)
        owners = {key: copy.deepcopy(value) for key, value in state['tasks'].items() if value['state'] == 'running'}
        for key in ('R25-DISTANCE-AUXILIARY-OVERLAP', 'R25-DISTANCE-CONDITIONAL-EVIDENCE'):
            if state['tasks'].get(key, {}).get('state') != 'ready' or state['tasks'][key]['phase'] != 'review':
                self.skipTest('live independent review inventory transitioned')
            context = rc._review_context(state, key)
            self.assertIsNotNone(context, key)
            self.assertTrue(context['scope']['candidate_seals'])
            self.assertTrue(context['scope']['source_contracts'])
        for key, value in owners.items():
            self.assertEqual(state['tasks'][key], value)
        self.assertEqual(path.read_bytes(), raw)

    def test_actual_live_copy_exposes_safe_ready_review_without_touching_live_bytes(self):
        path = Path(__file__).resolve().parents[2] / '.agent-harness/runtime/r23-continuous/STATE.json'
        if not path.is_file():
            self.skipTest('owner live snapshot unavailable')
        raw = path.read_bytes()
        state = json.loads(raw)
        running = {key: value for key, value in state['tasks'].items() if value['state'] == 'running'}
        if len(running) != 1 or next(iter(running.values()))['phase'] != 'acquisition':
            self.skipTest('live acquisition already transitioned')
        eligible = [key for key in rc.summary(state)['ready'] if state['tasks'][key]['phase'] == 'review'
                    and rc._review_context(state, key) is not None]
        if not eligible:
            self.skipTest('live ready review inventory already transitioned')
        before = copy.deepcopy(state)
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES))
        packet = rc.next_packet(state, POLICY, PROFILES, review_only=True)
        self.assertIn(packet['task_id'], eligible)
        self.assertEqual(packet['phase'], 'review')
        for key in running:
            self.assertEqual(state['tasks'][key], before['tasks'][key])
        self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__": unittest.main()

# R26 source-closure controls use disposable state and never schedule live STATE.
def _r26_review_state(tmp_path, document, owner=None):
    import hashlib
    contract = tmp_path / 'INPUT.json'
    contract.write_text(json.dumps(document))
    candidate = tmp_path / 'candidate.bin'
    candidate.write_bytes(b'candidate review fixture')
    state = {'tasks': {'C': {'phase': 'review', 'state': 'ready',
        'candidate_identity': 'sha256:' + hashlib.sha256(candidate.read_bytes()).hexdigest(),
        'candidate_products': [], 'spec': {'input_identity': 'fixture-input',
        'input_sources': [str(contract)], 'owned_paths': [str(candidate)], 'requires': {'all': []}}}},
        'packets': {}}
    if owner is not None:
        state['tasks']['A'] = {'phase': 'acquisition', 'state': 'running',
            'packet_id': 'owner', 'spec': {'input_identity': 'owner-input', 'owned_paths': [str(owner)]}}
        state['packets']['owner'] = {'launch_performed': True, 'agent_id': 'acquisition-agent',
            'task_id': 'A', 'phase': 'acquisition', 'input_identity': 'owner-input'}
    return state, contract, candidate


def test_r26_remote_references_and_mixed_records(tmp_path):
    state, _, _ = _r26_review_state(tmp_path, {'sources': [
        'https://example.invalid/paper', {'url': 'https://example.invalid/data', 'scope': 'reference'}]})
    before = copy.deepcopy(state)
    context = rc._review_context(state, 'C')
    assert context is not None and state == before
    assert len(context['scope']['source_seals']) == 1
    local = tmp_path / 'local.dat'; local.write_bytes(b'source')
    for group in ('sources', 'inputs'):
        state, _, _ = _r26_review_state(tmp_path, {group: [{'url': 'https://example.invalid/data',
            'source_files': [{'path': str(local)}]}]})
        before = copy.deepcopy(state)
        assert rc._review_context(state, 'C') is None and state == before


def test_r26_source_leaf_sha_size_alias_and_mutation(tmp_path):
    import hashlib
    leaf = tmp_path / 'leaf.dat'; leaf.write_bytes(b'old data')
    alias = tmp_path / 'alias.dat'; alias.symlink_to(leaf)
    record = {'path': str(alias), 'resolved_path': str(leaf), 'sha256': hashlib.sha256(leaf.read_bytes()).hexdigest(),
              'bytes': leaf.stat().st_size, 'size_bytes': leaf.stat().st_size}
    state, _, _ = _r26_review_state(tmp_path, {'inputs': [record]})
    context = rc._review_context(state, 'C')
    assert context and context['scope']['source_aliases'][str(alias)] == str(leaf)
    assert context['scope']['source_seals'][str(leaf)]['sha256'] == record['sha256']
    leaf.write_bytes(b'new data')
    before = copy.deepcopy(state)
    assert rc._review_context(state, 'C') is None and state == before
    leaf.write_bytes(b'old data')
    other = tmp_path / 'other.dat'; other.write_bytes(leaf.read_bytes())
    alias.unlink(); alias.symlink_to(other)
    assert rc._review_context(state, 'C') is None and state == before


def test_r26_nested_and_manifest_overlap_before_source_hash(tmp_path, monkeypatch):
    import hashlib
    leaf = tmp_path / 'claimed.dat'; leaf.write_bytes(b'claimed')
    row = {'path': str(leaf), 'sha256': hashlib.sha256(leaf.read_bytes()).hexdigest(), 'bytes': leaf.stat().st_size}
    for document in ({'input_identity_binding': {'source_files': [row]}},
                     {'files': {leaf.name: {'sha256': row['sha256'], 'bytes': row['bytes']}}},
                     {'source_hashes': {leaf.name: row['sha256']}},
                     {'external_raw_carrier': str(leaf), 'external_raw_carrier_sha256': row['sha256']}):
        state, _, _ = _r26_review_state(tmp_path, document, owner=leaf)
        before = copy.deepcopy(state)
        original_open = Path.open
        def guarded_open(path, *args, **kwargs):
            if path.resolve() == leaf:
                raise AssertionError('overlapping source was read before rejection')
            return original_open(path, *args, **kwargs)
        with monkeypatch.context() as patcher:
            patcher.setattr(Path, 'open', guarded_open)
            assert rc._review_context(state, 'C') is None
        assert state == before


def test_r26_oversized_json_contract_rejected_and_candidate_bound(tmp_path):
    giant = tmp_path / 'metadata.json'; giant.write_text(json.dumps({'description': 'x' * (1024 * 1024)}))
    state, _, candidate = _r26_review_state(tmp_path, {'input_sources': [str(giant)]})
    before = copy.deepcopy(state)
    assert rc._review_context(state, 'C') is None and state == before
    giant.unlink()
    state, _, candidate = _r26_review_state(tmp_path, {})
    assert rc._review_context(state, 'C') is not None
    candidate.write_bytes(b'changed candidate')
    assert rc._review_context(state, 'C') is None


def test_r26_actual_tag_and_toy_quotient_frozen_closures_read_only():
    import hashlib
    source = Path('/mnt/extdrive/workdir/htt_open_data/r26_blind_actual_review_slot_contract/STATE_SNAPSHOT.json')
    state = json.loads(source.read_text())
    before = copy.deepcopy(state)
    root = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
    tag = rc._review_context(state, 'R25-GAIA-RELEASE-TAG-ASSOCIATION', repository_root=root)
    assert tag is not None and state == before
    assert len(tag['scope']['source_seals']) >= 37
    property_table = '/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_properties_20261023/products/property_table.json'
    assert tag['scope']['source_seals'][property_table] == {'sha256':
        '76d523bb28a1176fa3e81139b6581f3fa176ae4745129f8ec5c9dd995d207c4e', 'size_bytes': 4643777}
    qid = 'R25-GAIA-SOURCE-QUOTIENT-CERTIFICATE'
    toy = Path('/mnt/extdrive/workdir/htt_open_data/r26_blind_actual_review_slot_contract/fixtures/actual_quotient_closure/candidate.bin')
    projection = copy.deepcopy(state)
    row = projection['tasks'][qid]
    row.update(phase='review', state='ready', candidate_identity='sha256:' + hashlib.sha256(toy.read_bytes()).hexdigest())
    row['spec']['owned_paths'] = [str(toy)]
    context = rc._review_context(projection, qid, repository_root=root)
    assert context is not None
    assert '/mnt/extdrive/workdir/htt_open_data/r25_gaia_pair_separation/packaged/arrays.npz' in context['scope']['source_seals']
    assert state == before


def test_r26_typed_future_large_data_requires_identity_bound_root(tmp_path):
    import hashlib
    leaf = tmp_path / 'future_data.json'
    leaf.write_text(json.dumps({'data': 'x' * (1024 * 1024)}))
    record = {'path': str(leaf), 'role': 'data',
              'sha256': hashlib.sha256(leaf.read_bytes()).hexdigest(), 'size_bytes': leaf.stat().st_size}
    state, contract, _ = _r26_review_state(tmp_path, {'input_sources': [record]})
    assert rc._review_context(state, 'C') is None
    state['tasks']['C']['spec']['input_identity'] = 'sha256:' + hashlib.sha256(contract.read_bytes()).hexdigest()
    context = rc._review_context(state, 'C')
    assert context is not None and str(leaf) in context['scope']['source_seals']
    packet = {'task_id': 'C', 'review_context': context, 'candidate_identity': context['scope']['candidate_identity'],
              'input_identity': context['scope']['input_identity']}
    leaf.write_text(json.dumps({'data': 'y' * (1024 * 1024)}))
    before = copy.deepcopy(state)
    assert not rc._review_context_matches(state, packet)
    assert state == before


def test_r26_source_seal_64mib_cap_and_duplicate_conflict(tmp_path):
    import hashlib
    leaf = tmp_path / 'large.bin'
    with leaf.open('wb') as stream:
        stream.truncate(64 * 1024 * 1024 + 1)
    state, _, _ = _r26_review_state(tmp_path, {'inputs': [str(leaf)]})
    before = copy.deepcopy(state)
    assert rc._review_context(state, 'C') is None and state == before
    leaf.write_bytes(b'duplicate source')
    good = hashlib.sha256(leaf.read_bytes()).hexdigest()
    state, _, _ = _r26_review_state(tmp_path, {'inputs': [
        {'path': str(leaf), 'sha256': good}, {'path': str(leaf), 'sha256': '0' * 64}]})
    assert rc._review_context(state, 'C') is None


def test_r26_source_manifest_list_and_embedded_path_conflict(tmp_path):
    import hashlib
    leaf = tmp_path / 'leaf.dat'; leaf.write_bytes(b'manifest input')
    sha = hashlib.sha256(leaf.read_bytes()).hexdigest()
    state, _, _ = _r26_review_state(tmp_path, {'files': [{'path': leaf.name, 'sha256': sha,
                                                         'size_bytes': leaf.stat().st_size}]})
    context = rc._review_context(state, 'C')
    assert context and str(leaf) in context['scope']['source_seals']
    other = tmp_path / 'other.dat'; other.write_bytes(leaf.read_bytes())
    state, _, _ = _r26_review_state(tmp_path, {'files': {leaf.name: {'path': other.name,
                                                                      'sha256': sha}}})
    before = copy.deepcopy(state)
    assert rc._review_context(state, 'C') is None and state == before


def test_r26_same_bytes_symlink_retarget_changes_context(tmp_path):
    leaf = tmp_path / 'leaf.dat'; leaf.write_bytes(b'identical bytes')
    other = tmp_path / 'other.dat'; other.write_bytes(leaf.read_bytes())
    alias = tmp_path / 'alias.dat'; alias.symlink_to(leaf)
    state, _, _ = _r26_review_state(tmp_path, {'inputs': [str(alias)]})
    old = rc._review_context(state, 'C')
    assert old
    packet = {'task_id': 'C', 'review_context': old, 'candidate_identity': old['scope']['candidate_identity'],
              'input_identity': old['scope']['input_identity']}
    alias.unlink(); alias.symlink_to(other)
    assert not rc._review_context_matches(state, packet)


def test_r26_inventory_form_size_conflict_overlap_and_replay(tmp_path, monkeypatch):
    import hashlib
    bundle = tmp_path / 'bundle'; bundle.mkdir()
    product = bundle / 'RESULT.json'; product.write_bytes(b'{"value":1}')
    item = {'path': product.name, 'sha256': hashlib.sha256(product.read_bytes()).hexdigest(),
            'size_bytes': product.stat().st_size}
    manifest = bundle / 'MANIFEST.json'
    manifest.write_text(json.dumps({'task_id': 'C', 'input_identity': 'fixture-input', 'inventory': [item]}))
    state, _, _ = _r26_review_state(tmp_path, {})
    state['tasks']['C']['spec']['owned_paths'] = [str(bundle)]
    state['tasks']['C']['candidate_identity'] = 'sha256:' + hashlib.sha256(manifest.read_bytes()).hexdigest()
    context = rc._review_context(state, 'C')
    assert context and str(product) in context['scope']['candidate_seals']
    packet = {'task_id': 'C', 'review_context': context,
              'candidate_identity': context['scope']['candidate_identity'],
              'input_identity': context['scope']['input_identity']}
    product.write_bytes(b'{"value":2}')
    before = copy.deepcopy(state)
    assert not rc._review_context_matches(state, packet) and state == before
    product.write_bytes(b'{"value":1}')
    for alteration in ({'size_bytes': item['size_bytes'] + 1}, {'sha256': '0' * 64},
                       {'path': 'absent.json'}):
        bad = {**item, **alteration}
        manifest.write_text(json.dumps({'task_id': 'C', 'input_identity': 'fixture-input', 'inventory': [bad]}))
        state['tasks']['C']['candidate_identity'] = 'sha256:' + hashlib.sha256(manifest.read_bytes()).hexdigest()
        old = copy.deepcopy(state)
        assert rc._review_context(state, 'C') is None and state == old
    manifest.write_text(json.dumps({'task_id': 'C', 'input_identity': 'fixture-input',
                                    'files': {product.name: {'sha256': '0' * 64}}, 'inventory': [item]}))
    state['tasks']['C']['candidate_identity'] = 'sha256:' + hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert rc._review_context(state, 'C') is None
    # Reject an acquisition-owned product before opening it.
    manifest.write_text(json.dumps({'task_id': 'C', 'input_identity': 'fixture-input', 'inventory': [item]}))
    state['tasks']['C']['candidate_identity'] = 'sha256:' + hashlib.sha256(manifest.read_bytes()).hexdigest()
    state['tasks']['A'] = {'phase': 'acquisition', 'state': 'running', 'packet_id': 'owner',
                          'spec': {'input_identity': 'owner-input', 'owned_paths': [str(product)]}}
    state['packets']['owner'] = {'launch_performed': True, 'agent_id': 'author', 'task_id': 'A',
                                 'phase': 'acquisition', 'input_identity': 'owner-input'}
    original_open = Path.open
    def protected_open(path, *args, **kwargs):
        if path.resolve() == product:
            raise AssertionError('acquisition-owned product opened')
        return original_open(path, *args, **kwargs)
    with monkeypatch.context() as patcher:
        patcher.setattr(Path, 'open', protected_open)
        assert rc._review_context(state, 'C') is None


def test_r26_explicit_contract_and_manifest_roles_parse_nonjson(tmp_path):
    import hashlib
    leaf = tmp_path / 'nested.dat'; leaf.write_bytes(b'nested input')
    for role in ('contract', 'manifest'):
        metadata = tmp_path / (role + '.dat')
        metadata.write_text(json.dumps({'inputs': [{'path': str(leaf),
                        'sha256': hashlib.sha256(leaf.read_bytes()).hexdigest()}]}))
        record = {'path': str(metadata), 'role': role,
                  'sha256': hashlib.sha256(metadata.read_bytes()).hexdigest(), 'bytes': metadata.stat().st_size}
        state, _, _ = _r26_review_state(tmp_path, {'inputs': [record]})
        context = rc._review_context(state, 'C')
        assert context and str(leaf) in context['scope']['source_seals']
        state, _, _ = _r26_review_state(tmp_path, {'inputs': [record]}, owner=leaf)
        before = copy.deepcopy(state)
        assert rc._review_context(state, 'C') is None and state == before


def test_r26_inventory_mapping_alias_race_refuses(tmp_path, monkeypatch):
    import hashlib
    leaf = tmp_path / 'leaf.dat'; leaf.write_bytes(b'same bytes')
    owned = tmp_path / 'owned.dat'; owned.write_bytes(leaf.read_bytes())
    alias = tmp_path / 'alias.dat'; alias.symlink_to(leaf)
    state, _, _ = _r26_review_state(tmp_path, {'files': {str(alias): {
        'path': str(leaf), 'sha256': hashlib.sha256(leaf.read_bytes()).hexdigest()}}}, owner=owned)
    original_open = Path.open
    hit = []
    def retarget(path, *args, **kwargs):
        if path == leaf and not hit:
            hit.append(True)
            alias.unlink(); alias.symlink_to(owned)
        return original_open(path, *args, **kwargs)
    before = copy.deepcopy(state)
    with monkeypatch.context() as patcher:
        patcher.setattr(Path, 'open', retarget)
        assert rc._review_context(state, 'C') is None
    assert hit and state == before


def test_r26_inventory_alias_pair_remains_equal_through_completed_proof(tmp_path, monkeypatch):
    import hashlib
    target_a = tmp_path / 'target_a.dat'; target_a.write_bytes(b'identical bytes')
    target_b = tmp_path / 'target_b.dat'; target_b.write_bytes(target_a.read_bytes())
    key = tmp_path / 'mapping_key.dat'; key.symlink_to(target_a)
    embedded = tmp_path / 'embedded_path.dat'; embedded.symlink_to(target_a)
    record = {'path': str(embedded), 'sha256': hashlib.sha256(target_a.read_bytes()).hexdigest(),
              'size_bytes': target_a.stat().st_size}
    state, _, _ = _r26_review_state(tmp_path, {'files': {str(key): record}})
    before = copy.deepcopy(state)
    stable = rc._review_context(state, 'C')
    assert stable is not None and state == before
    assert stable['scope']['source_aliases'][str(key)] == str(target_a)
    assert stable['scope']['source_aliases'][str(embedded)] == str(target_a)

    original_open = Path.open
    hit = []
    def retarget_embedded_while_key_is_hashed(path, *args, **kwargs):
        if path == target_a and not hit:
            hit.append(True)
            embedded.unlink(); embedded.symlink_to(target_b)
        return original_open(path, *args, **kwargs)
    with monkeypatch.context() as patcher:
        patcher.setattr(Path, 'open', retarget_embedded_while_key_is_hashed)
        assert rc._review_context(state, 'C') is None
    assert hit and state == before
    assert key.resolve() == target_a and embedded.resolve() == target_b


def test_r26_owned_scope_counts_toward_256_limit(tmp_path):
    paths = []
    for index in range(255):
        leaf = tmp_path / f'leaf_{index}.dat'; leaf.write_bytes(b'')
        paths.append(str(leaf))
    state, _, _ = _r26_review_state(tmp_path, {'inputs': paths})
    before = copy.deepcopy(state)
    assert rc._review_context(state, 'C') is None and state == before


def test_r26_actual_tag_and_quotient_inventory_complete_on_copied_state():
    import importlib.util
    p = Path('/mnt/extdrive/workdir/htt_open_data/r26_blind_review_slot_source/STATE_SNAPSHOT.json')
    state = json.loads(p.read_text()); original = copy.deepcopy(state)
    for row in state['tasks'].values():
        if row['state'] == 'running' and row['phase'] != 'acquisition':
            row['state'] = 'held'  # In-memory scheduling fixture only.
    root = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
    tag = rc._review_context(state, 'R25-GAIA-RELEASE-TAG-ASSOCIATION', repository_root=root)
    quotient = rc._review_context(state, 'R25-GAIA-SOURCE-QUOTIENT-CERTIFICATE', repository_root=root)
    assert tag and quotient
    assert len(tag['scope']['candidate_seals']) == 26
    assert len(quotient['scope']['candidate_seals']) == 11
    qmanifest = Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_quotient_certificate/MANIFEST.json')
    inventory = json.loads(qmanifest.read_text())['inventory']
    for item in inventory:
        member = str((qmanifest.parent / item['path']).resolve())
        assert quotient['scope']['candidate_seals'][member] == item['sha256']
    assert original['tasks']['R25-GAIA-SOURCE-QUOTIENT-CERTIFICATE']['candidate_identity'] == state['tasks']['R25-GAIA-SOURCE-QUOTIENT-CERTIFICATE']['candidate_identity']


def test_r26_typed_data_cannot_hide_contract_and_malformed_reference_refuses(tmp_path):
    import hashlib
    nested = tmp_path / 'nested.dat'; nested.write_bytes(b'nested')
    data = tmp_path / 'typed_data.json'; data.write_text(json.dumps({'inputs': [str(nested)]}))
    record = {'path': str(data), 'role': 'data',
              'sha256': hashlib.sha256(data.read_bytes()).hexdigest(), 'bytes': data.stat().st_size}
    state, root, _ = _r26_review_state(tmp_path, {'input_sources': [record]})
    state['tasks']['C']['spec']['input_identity'] = 'sha256:' + hashlib.sha256(root.read_bytes()).hexdigest()
    before = copy.deepcopy(state)
    assert rc._review_context(state, 'C') is None and state == before
    state, _, _ = _r26_review_state(tmp_path, {'sources': ['https://']})
    assert rc._review_context(state, 'C') is None


class SameTaskRepairInputTests(FrontierTests):
    """Disposable controller fixtures; no canonical STATE/ledger or native payload writes."""
    def fixture(self):
        root = Path('/mnt/extdrive/workdir/htt_open_data/r26_full7_memory_repair_execution/preimages')
        if not root.is_dir():
            self.skipTest('bounded full7 repair baseline unavailable')
        self.n = 0
        def write(value, name=None):
            self.n += 1
            p = Path(self.tmp.name) / (name or ('document-' + str(self.n) + '.json'))
            p.write_text(json.dumps(value))
            return rc._receipt(str(p))
        before = json.loads((root/'INPUT_BEFORE.json').read_text())
        parent = json.loads((root/'PACKET_BEFORE.json').read_text())
        state = self.state([task('R25-PR3-FREQUENCY-TENSOR-CROSSPREDICTION',
            input_identity='sha256:' + rc._receipt(str(root/'INPUT_BEFORE.json'))['sha256'])])
        state['campaign_identity'] = before['controller_campaign_identity']
        t = state['tasks']['R25-PR3-FREQUENCY-TENSOR-CROSSPREDICTION']
        t['phase'] = 'research'
        packet = self.launch(state)
        state['packets'][parent['packet_id']] = parent
        raw = json.loads((root/'RAW_BEFORE.json').read_text())
        # Freeze the historical ledger read in this fixture; live execution has advanced.
        from unittest.mock import patch
        original_read_bytes = Path.read_bytes
        historical_raw = (root/'RAW_BEFORE.json').read_bytes()
        ledger_path = Path('/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/run/RAW_RECEIPT.json')
        def fixture_read_bytes(path):
            return historical_raw if path == ledger_path else original_read_bytes(path)
        ledger_read = patch.object(Path, 'read_bytes', fixture_read_bytes)
        ledger_read.start(); self.addCleanup(ledger_read.stop)
        t['history'].append({'packet_id':parent['packet_id'], 'phase':'execute',
            'receipt':rc._receipt(str(root/'RAW_BEFORE.json')), 'result':{'outcome':'blocker'}})
        t['failures'] = [{'class':'numeric','original':'over-cap'}]
        t['issue'] = {'original':'memory'}
        t['ultra_used'] = ['old-repair']
        state['ultra_repairs'] = {'old-repair':{'retained':True}}
        t['accounting'] = {'seconds':123}
        result = {'packet_id':packet['packet_id'], 'task_id':packet['task_id'],
            'agent_id':state['packets'][packet['packet_id']]['agent_id'],
            'input_identity':packet['input_identity'], 'outcome':'success',
            'repair_plan':'One bounded same-task memory lifetime repair',
            'raw_receipt':str(root/'CONTROL_BEFORE.json')}
        contributors = [{'agent_id':'fixture-'+role,'role':role,'requested_runtime':'fixture-request',
            'observed_runtime':'UNKNOWN','raw_receipt':write({'fixture':role})}
            for role in ['controller_patch','numerical_source']]
        after = copy.deepcopy(before)
        # Parent/preimages remain historical; candidate seals describe current sources.
        for row in after['input_sources']:
            name = Path(row['path']).name
            if row.get('role') == 'code' and name in after['source_sha256']:
                current = rc._receipt(row['path'])
                row.update(sha256=current['sha256'],bytes=Path(row['path']).stat().st_size)
                after['source_sha256'][name] = current['sha256']
        after.update(schema='htt.full7_native_input/2',ack_path=str(Path(self.tmp.name)/'new-ACK.json'),
                     source_contributors=before['source_contributors']+contributors)
        output = '/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/run'
        contract = rc._receipt('/mnt/extdrive/workdir/htt_open_data/r26_full7_memory_repair_contract/REPAIR_CONTRACT.md')
        result_ref = write(result)
        before_ref = rc._receipt('/mnt/extdrive/workdir/htt_open_data/r26_full7_frozen_input/FROZEN_FULL7_INPUT.json')
        raw_ref = rc._receipt(str(root/'RAW_BEFORE.json'))
        lineage = {'schema':'htt.full7_memory_repair_lineage/1','repair_id':'R26-FULL7-MEMORY-LIFETIME-01',
            'repair_contract':contract,'research_result':result_ref,'parent_input':before_ref,
            'parent_ack':rc._receipt(before['ack_path']),
            'parent_packet':json.loads((root/'ACK_BEFORE.json').read_text())['controller_packet_receipt'],
            'parent_raw_receipt':raw_ref,'source_preimages':{name:rc._receipt(str(root/name))
                for name in before['source_sha256']},
            'checkpoint_seals':{name:rc._receipt(output+'/'+name) for name in
                ['VALID_'+k+'.npz' for k in raw['products']]+['COMMON_SUPPORT_S7.npz']},
            'historical_controls':rc._receipt(str(root/'CONTROL_BEFORE.json')),
            'affected_controls':[write({'fixture':True,'status':'FINISHED','exit_code':0,
                'child_reaped':True,'elapsed_seconds':0.01,'ru_maxrss_bytes':1024})],
            'output_directory':output,'ledger_path':output+'/RAW_RECEIPT.json','max_resumed_numerical_attempts':1}
        after['repair_lineage'] = lineage
        after_ref = write(after)
        diff = write({'fixture':'diff'})
        review = {'decision':'APPROVE_ONE_BOUNDED_SAME_TASK_MEMORY_REPAIR','scientific_admission':'HOLD',
            'before_input':before_ref,'after_input':after_ref,'repair_contract':contract,'raw_before':raw_ref,
            'preserved_scientific_fields':True,'preserved_caps':True,'unresolved_blocking_findings':[],
            'source_sha256':after['source_sha256'],'affected_controls':lineage['affected_controls'],
            'reviewer_id':'fixture-independent-reviewer','independent_of':t['contributors']+[v['agent_id'] for v in contributors],
            'requested_runtime':'fixture-request','observed_runtime':'UNKNOWN',
            'diffs':{'controller_patch':diff,'numerical_source':diff},'controller_patch':diff,
            'controller_source':rc._receipt(str(Path(rc.__file__).resolve())),
            'controller_tests':rc._receipt(str(Path(__file__).resolve()))}
        tr = {'schema':'htt.repair_input_transition/1','kind':'full7_memory_lifetime_same_science',
            'campaign':state['campaign_identity'],'task_id':result['task_id'],
            'research_packet_id':packet['packet_id'],'research_result':result_ref,'repair_contract':contract,
            'before_input':before_ref,'after_input':after_ref,'raw_before':raw_ref,
            'source_review':write(review),'preparation_contributors':contributors}
        return state,result,tr,write,after,review

    def test_repair_input_integrated_preserves_and_exposes_lineage(self):
        state,result,tr,write,after,review = self.fixture()
        old = copy.deepcopy(state); key = result['task_id']
        ref = write(tr)
        rc.record(state,result,POLICY,ref['path'])
        t, prior = state['tasks'][key], old['tasks'][key]
        for field in ('failures','attempt','ultra_used','accounting','issue'):
            self.assertEqual(t[field],prior[field])
        for field in ('campaign','campaign_identity','turn','ultra_pending','ultra_repairs'):
            self.assertEqual(state[field],old[field])
        self.assertEqual(t['history'][:-1],prior['history'])
        self.assertEqual(state['packets'],old['packets'])
        self.assertEqual(t['spec_history'],[prior['spec']])
        self.assertEqual((t['phase'],t['state']),('repair','ready'))
        packet = rc.next_packet(state,POLICY,PROFILES)
        self.assertEqual(packet['repair_input_transition']['sha256'],ref['sha256'])
        assignment = json.loads(packet['spawn_args']['message'].split('Assignment:\n')[1])
        self.assertEqual(assignment['repair_input_transition'],packet['repair_input_transition'])
        snapshot = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError): rc.record(state,result,POLICY,ref['path'])
        self.assertEqual(state,snapshot)

    def test_repair_input_rejections_atomic(self):
        state,result,tr,write,after,review = self.fixture()
        cases = []
        for field in ('products','support','operator_identity','decoder','prior_product_charges_seconds'):
            bad = copy.deepcopy(after); bad[field] = {'drift':True}
            altered = copy.deepcopy(tr); altered['after_input'] = write(bad); cases.append(altered)
        for field in ('campaign','task_id','research_packet_id','kind'):
            altered = copy.deepcopy(tr); altered[field] = 'stale'; cases.append(altered)
        altered = copy.deepcopy(tr); altered['raw_before']['sha256'] = '0'*64; cases.append(altered)
        bad = copy.deepcopy(review); bad['reviewer_id'] = tr['preparation_contributors'][0]['agent_id']
        altered = copy.deepcopy(tr); altered['source_review'] = write(bad); cases.append(altered)
        bad = copy.deepcopy(review); bad['scientific_admission'] = 'PASS'
        altered = copy.deepcopy(tr); altered['source_review'] = write(bad); cases.append(altered)
        for altered in cases:
            prior = copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError): rc.record(state,result,POLICY,write(altered)['path'])
            self.assertEqual(state,prior)
        for field,value in [('state','planned'),('phase','execute')]:
            bad_state = copy.deepcopy(state); bad_state['tasks'][result['task_id']][field] = value
            prior = copy.deepcopy(bad_state)
            with self.assertRaises(rc.ControllerError): rc.record(bad_state,result,POLICY,write(tr)['path'])
            self.assertEqual(bad_state,prior)


class SavedLawTestRepairTests(FrontierTests):
    """Disposable actual-schema chain, no science or live state execution."""
    def fixture(self):
        from unittest.mock import patch
        original = Path('/mnt/extdrive/workdir/htt_open_data/r26_s04_selected_law_consumer')
        root = Path(self.tmp.name)
        binding = patch.object(rc, '_SAVED_LAW_DIRECTORY', str(root)); binding.start()
        self.addCleanup(binding.stop)
        count = [0]
        def write(value, name=None):
            count[0] += 1
            p = root / (name or ('document-' + str(count[0]) + '.json'))
            p.write_text(json.dumps(value)); return rc._receipt(str(p))
        def code(name, text):
            path = root / name; path.write_text(text)
            return {**rc._receipt(str(path)), 'bytes':path.stat().st_size, 'ast':'PASS'}
        test = 'class AnalyticContractTests:\n def test_correlated_prediction_includes_training_uncertainty(self):\n  self.assertGreater(float(Z@Ginv@Z.T),0.)\n'
        before = json.loads((original/'FROZEN_INPUT.json').read_text())
        before['source_code'] = {n:code(n, test if n == 'test_consume.py' else '# unchanged\n')
                                 for n in before['source_code']}
        preimages = {}
        for n,row in before['source_code'].items():
            p = root / ('preimage-' + n); p.write_bytes(Path(row['path']).read_bytes())
            preimages[n] = rc._receipt(str(p))
        before_ref = write(before, 'FROZEN_INPUT.json')
        key = before['task_id']
        inventory = [{**{k:v for k,v in row.items() if k != 'ast'}, 'role':'code'}
                     for row in before['source_code'].values()]
        inventory += [{**before_ref,'bytes':Path(before_ref['path']).stat().st_size,'role':'contract'},
                      {'path':'retained-data','role':'data','sha256':'a'*64,'bytes':3}]
        state = self.state([task(key,input_identity='sha256:'+before_ref['sha256'],input_sources=inventory)])
        t = state['tasks'][key]; t['phase'] = 'research'
        packet = self.launch(state)
        parent = json.loads((original/'ACKNOWLEDGED_EXECUTION_PACKET.json').read_text())
        parent.update(campaign=state['campaign_identity'],input_identity=t['spec']['input_identity'])
        parent_ref = write(parent,'ACKNOWLEDGED_EXECUTION_PACKET.json')
        state['packets'][parent['packet_id']] = parent
        ack = json.loads((original/'CONTROLLER_ACK.json').read_text())
        ack.update(input_identity=t['spec']['input_identity'],acknowledged_packet=parent_ref)
        ack_ref = write(ack,'CONTROLLER_ACK.json')
        log = root/'focused_tests.stderr.log'; log.write_text('original failed test\n')
        log_ref = rc._receipt(str(log))
        raw = json.loads((original/'RUN_ACCOUNTING.json').read_text())
        raw.update(controller_ack_file=ack_ref['path'],controller_ack_sha256=ack_ref['sha256'])
        raw['started_commands'][0].update(stderr=log_ref['path'],stderr_sha256=log_ref['sha256'])
        raw_ref = write(raw,'RUN_ACCOUNTING.json')
        outcome = json.loads((original/'CONTROLLER_OUTCOME.json').read_text())
        outcome.update(input_identity=t['spec']['input_identity'],raw_receipt=raw_ref['path'],
            raw_receipt_sha256=raw_ref['sha256'],first_failure_log=log_ref['path'],
            first_failure_log_sha256=log_ref['sha256'])
        outcome_ref = write(outcome,'CONTROLLER_OUTCOME.json')
        t['history'].append({'packet_id':parent['packet_id'],'phase':'execute','receipt':raw_ref,
                              'result':{'outcome':'blocker'}})
        t['failures'] = [{'class':'numeric','original':'singleton'}]
        t['accounting'] = {'seconds':2.9794867201708257}
        result = {'packet_id':packet['packet_id'],'task_id':key,'agent_id':state['packets'][packet['packet_id']]['agent_id'],
            'input_identity':packet['input_identity'],'outcome':'success','repair_plan':'single test expression',
            'raw_receipt':raw_ref['path']}
        result_ref = write(result)
        contract = write({'fixture':'contract'})
        contributors = [{'agent_id':'fixture-'+role,'role':role,'requested_runtime':'fixture',
            'observed_runtime':'UNKNOWN','raw_receipt':write({'fixture':role})}
            for role in ('controller_patch','numerical_source')]
        after = copy.deepcopy(before); after['schema'] = 'htt.saved_selected_law_frozen_input/2'
        after['source_code']['test_consume.py'] = code('test_consume.py',test.replace('float(Z@Ginv@Z.T)','(Z@Ginv@Z.T).item()'))
        after['source_code']['run_continuation.py'] = code('run_continuation.py','# new driver\n')
        after['repair_lineage'] = {'schema':'htt.saved_law_testfix_lineage/1',
            'repair_id':'R26-SAVED-LAW-SINGLETON-01','repair_contract':contract,'research_result':result_ref,
            'parent_input':before_ref,'parent_ack':ack_ref,'parent_packet':parent_ref,'parent_raw_receipt':raw_ref,
            'parent_outcome':outcome_ref,'failure_log':log_ref,'source_preimages':preimages,
            'ack_path':str(root/'testfix_v1'/'NEW_ACK.json'),'output_directory':str(root),
            'ledger_path':str(root/'RUN_ACCOUNTING_TESTFIX.json'),'inherited_seconds_cap':90,
            'prior_charged_seconds':2.9794867201708257,'inherited_rss_bytes_max':2147483648,
            'max_resumed_numerical_attempts':1}
        expected = {k:after['repair_lineage'][k]['sha256'] for k in rc._SAVED_LAW_PARENT_SHA256}
        parent_binding = patch.object(rc, '_SAVED_LAW_PARENT_SHA256', expected)
        parent_binding.start(); self.addCleanup(parent_binding.stop)
        after_ref = write(after, 'FROZEN_INPUT_TESTFIX.json')
        diff = write({'fixture':'diff'})
        review = {'decision':'APPROVE_ONE_BOUNDED_SAME_TASK_TEST_REPAIR','scientific_admission':'HOLD',
            'before_input':before_ref,'after_input':after_ref,'repair_contract':contract,'raw_before':raw_ref,
            'preserved_scientific_fields':True,'preserved_caps':True,'unresolved_blocking_findings':[],
            'source_code':after['source_code'],'reviewer_id':'independent','contract_author_id':'contract-author',
            'independent_of':t['authors']+t['contributors']+[r['agent_id'] for r in contributors]+['contract-author'],
            'requested_runtime':'fixture','observed_runtime':'UNKNOWN',
            'diffs':{'controller_patch':diff,'numerical_source':diff},'controller_patch':diff,
            'controller_source':rc._receipt(str(Path(rc.__file__).resolve())),
            'controller_tests':rc._receipt(str(Path(__file__).resolve()))}
        tr = {'schema':'htt.repair_input_transition/1','kind':'saved_law_singleton_test_same_science',
            'campaign':state['campaign_identity'],'task_id':key,'research_packet_id':packet['packet_id'],
            'research_result':result_ref,'repair_contract':contract,'before_input':before_ref,'after_input':after_ref,
            'raw_before':raw_ref,'source_review':write(review),'preparation_contributors':contributors}
        return state,result,tr,write,after,review

    def test_saved_law_atomic_binding_preserves_and_exposes(self):
        state,result,tr,write,after,review = self.fixture(); old = copy.deepcopy(state)
        ref = write(tr); rc.record(state,result,POLICY,ref['path'])
        t = state['tasks'][result['task_id']]; prior = old['tasks'][result['task_id']]
        for k in ('failures','accounting','attempt','ultra_used'):
            self.assertEqual(t.get(k),prior.get(k))
        self.assertEqual(t['spec_history'],[prior['spec']])
        self.assertEqual(t['history'][:-1],prior['history'])
        self.assertEqual(state['packets'],old['packets'])
        self.assertEqual(t['spec']['input_sources'][-2],prior['spec']['input_sources'][-1])
        self.assertEqual(len(t['spec']['input_sources']),len(prior['spec']['input_sources'])+1)
        packet = rc.next_packet(state,POLICY,PROFILES)
        self.assertEqual(packet['input_identity'],'sha256:'+tr['after_input']['sha256'])
        self.assertEqual(packet['repair_input_transition']['sha256'],ref['sha256'])
        snapshot = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError): rc.record(state,result,POLICY,ref['path'])
        self.assertEqual(state,snapshot)

    def test_saved_law_mutations_rejected_atomically(self):
        state,result,tr,write,after,review = self.fixture()
        cases = []
        for k in ('source_inputs','claim_ceiling','bounds'):
            bad = copy.deepcopy(after); bad[k] = {'changed':True}
            altered = copy.deepcopy(tr); altered['after_input'] = write(bad); cases.append(altered)
        for name in ('consume.py','plot.py','run_capped.py'):
            bad = copy.deepcopy(after); bad['source_code'][name]['bytes'] += 1
            altered = copy.deepcopy(tr); altered['after_input'] = write(bad); cases.append(altered)
        for change in ('preimage','cap'):
            bad = copy.deepcopy(after)
            if change == 'preimage': bad['repair_lineage']['source_preimages'].pop('test_consume.py')
            else: bad['repair_lineage']['inherited_seconds_cap'] = 91
            altered = copy.deepcopy(tr); altered['after_input'] = write(bad); cases.append(altered)
        for k in ('kind','campaign','research_packet_id'):
            altered = copy.deepcopy(tr); altered[k] = 'stale'; cases.append(altered)
        for k,v in (('decision','FAIL'),('reviewer_id',tr['preparation_contributors'][0]['agent_id']),
                    ('reviewer_id','contract-author')):
            bad = copy.deepcopy(review); bad[k] = v
            altered = copy.deepcopy(tr); altered['source_review'] = write(bad); cases.append(altered)
        for altered in cases:
            prior = copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError): rc.record(state,result,POLICY,write(altered)['path'])
            self.assertEqual(state,prior)
        # Even a newly sealed extra test edit fails before review or state mutation.
        path = Path(after['source_code']['test_consume.py']['path']); path.write_text(path.read_text()+'# extra edit\n')
        after['source_code']['test_consume.py'].update(rc._receipt(str(path)),bytes=path.stat().st_size)
        tr['after_input'] = write(after); prior = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError): rc.record(state,result,POLICY,write(tr)['path'])
        self.assertEqual(state,prior)

    def test_saved_law_stale_ack_result_and_unresolved_child_rejected(self):
        state,result,tr,write,after,review = self.fixture()
        cases = []
        for change in ('ack','parent','raw','outcome','future_ack','future_ledger'):
            bad = copy.deepcopy(after)
            field = {'ack':'parent_ack','parent':'parent_packet','raw':'parent_raw_receipt',
                     'outcome':'parent_outcome'}.get(change)
            if field:
                row = json.loads(Path(bad['repair_lineage'][field]['path']).read_text())
                row['input_identity'] = 'sha256:'+'0'*64
                bad['repair_lineage'][field] = write(row)
            else:
                bad['repair_lineage']['ack_path' if change == 'future_ack' else 'ledger_path'] = tr['before_input']['path']
            altered = copy.deepcopy(tr); altered['after_input'] = write(bad); cases.append(altered)
        altered = copy.deepcopy(tr); altered['research_result'] = write({**result,'agent_id':'fabricated'})
        cases.append(altered)
        for altered in cases:
            prior = copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError): rc.record(state,result,POLICY,write(altered)['path'])
            self.assertEqual(state,prior)
        bad = copy.deepcopy(state)
        bad['packets']['unresolved'] = {**bad['packets'][result['packet_id']], 'packet_id':'unresolved'}
        prior = copy.deepcopy(bad)
        with self.assertRaises(rc.ControllerError): rc.record(bad,result,POLICY,write(tr)['path'])
        self.assertEqual(bad,prior)


class CF4FixtureRepairTests(unittest.TestCase):
    """Disposable source/receipt chains; never execute the scientific modules."""
    setUp = base.ControllerTests.setUp
    state = base.ControllerTests.state
    launch = base.ControllerTests.launch

    def fixture(self):
        from unittest.mock import patch
        original = Path(rc._CF4_DIRECTORY)
        root = Path(self.tmp.name)
        count = [0]
        def write(value, name=None):
            count[0] += 1
            path = root/(name or ('document-'+str(count[0])+'.json'))
            path.write_text(json.dumps(value))
            return rc._receipt(str(path))
        def seal(name):
            return rc._receipt(str(root/name))
        before = json.loads((original/'FROZEN_INPUT.json').read_text())
        (root/'FROZEN_INPUT.json').write_bytes((original/'FROZEN_INPUT.json').read_bytes())
        before_ref = seal('FROZEN_INPUT.json')
        key = rc._CF4_TASK
        names = ('consume.py','plot.py','driver.py','test_consume.py')
        for name in names:
            (root/name).write_bytes((original/name).read_bytes())
        # This copied source is inspected as AST only, without importing science.
        (root/'test_consume_repair.py').write_bytes((original/'test_consume_repair.py').read_bytes())
        (root/'run_continuation.py').write_text('# disposable controller fixture; never executed\n')
        source = [{**seal(n),'size_bytes':(root/n).stat().st_size}
                  for n in (*names,'test_consume_repair.py','run_continuation.py')]
        inventory = [{**seal(n),'bytes':(root/n).stat().st_size,'role':'code'} for n in names]
        inventory += [{**before_ref,'role':'contract','bytes':(root/'FROZEN_INPUT.json').stat().st_size}]
        state = self.state([task(key,input_identity='sha256:'+before_ref['sha256'],input_sources=inventory)])
        t = state['tasks'][key]; t['phase'] = 'research'
        packet = self.launch(state)
        ack = json.loads((original/'ACTUAL_ACK_EXECUTE.json').read_text())
        append_ref = write(json.loads((original/'ACTUAL_CONTROLLER_APPEND.json').read_text()),
                           'ACTUAL_CONTROLLER_APPEND.json')
        ack['controller_append_sha256'] = append_ref['sha256']
        ack_ref = write(ack,'ACTUAL_ACK_EXECUTE.json')
        parent = {'packet_id':ack['packet_id'],'task_id':key,'input_identity':ack['input_identity'],
                  'launch_performed':True,'agent_id':ack['agent_id']}
        state['packets'][parent['packet_id']] = parent
        (root/'tests.stderr').write_bytes((original/'tests.stderr').read_bytes())
        log_ref = seal('tests.stderr')
        (root/'EXECUTION.jsonl').write_bytes((original/'EXECUTION.jsonl').read_bytes())
        raw = json.loads((original/'RUN_RECEIPT.json').read_text())
        raw.update(ack_sha256=ack_ref['sha256'],controller_append_sha256=append_ref['sha256'])
        raw_ref = write(raw,'RUN_RECEIPT.json')
        outcome = json.loads((original/'EXECUTOR_RESULT.json').read_text())
        outcome['raw_receipt'] = raw_ref['path']
        outcome['test_summary'].update(stderr=log_ref['path'],stderr_sha256=log_ref['sha256'])
        write(outcome,'EXECUTOR_RESULT.json')
        t['history'].append({'packet_id':parent['packet_id'],'phase':'execute','receipt':raw_ref,
                              'result':{'outcome':'blocker'}})
        t['failures'] = [{'original':'two fixtures'}]
        t['accounting'] = {'seconds':64.38265966903418}
        result = {'packet_id':packet['packet_id'],'task_id':key,
            'agent_id':state['packets'][packet['packet_id']]['agent_id'],
            'input_identity':packet['input_identity'],'outcome':'success','repair_plan':'fixture bodies only',
            'raw_receipt':raw_ref['path']}
        result_ref = write(result)
        contract = rc._receipt('/mnt/extdrive/workdir/htt_open_data/r26_cf4_final_group_fixture_research/CONTRACT.md')
        lineage = {'task_id':key,'transition_kind':'cf4_final_group_fixture_same_science',
            'old_input':before_ref,'research_contract':contract,'research_result':result_ref,
            'old_evidence':{n:seal(n) for n in ('ACTUAL_ACK_EXECUTE.json','ACTUAL_CONTROLLER_APPEND.json',
                'EXECUTION.jsonl','RUN_RECEIPT.json','EXECUTOR_RESULT.json','tests.stderr')},
            'inherited_accounting':{'cap_seconds':600,'cumulative_seconds':64.38265966903418,
                'future_invocation_seconds_cap':120,'future_scientific_invocations_max':1,
                'rss_cap_bytes':2147483648,'threads':1},
            'original_code':{n:seal(n) for n in names},
            'allowed_repaired_test_methods':sorted(rc._CF4_ALLOWED_METHODS),
            **{k:str(root/'repair_run'/n) for k,n in (
                ('future_ack_path','ACTUAL_ACKNOWLEDGED_REPAIR_PACKET.json'),
                ('future_execution_ledger_path','EXECUTION.jsonl'),('future_run_receipt_path','RUN_RECEIPT.json'))}}
        lineage['future_source_review_path'] = '/mnt/extdrive/workdir/htt_open_data/r26_cf4_fixture_source_review/REVIEW.json'
        after = {**before,'schema':'htt.r26.cf4_final_group_frozen_input/2',
                 'source_code':source,'repair_lineage':lineage}
        after_ref = write(after,'FROZEN_INPUT_REPAIR.json')
        contributors = [{'agent_id':'fixture-'+role,'role':role,'requested_runtime':'fixture',
            'observed_runtime':'UNKNOWN','raw_receipt':write({'fixture':role})}
            for role in ('controller_patch','numerical_source')]
        diff = write({'fixture':'diff'})
        review = {'decision':'APPROVE_ONE_BOUNDED_SAME_TASK_FIXTURE_REPAIR','scientific_admission':'HOLD',
            'before_input':before_ref,'after_input':after_ref,'repair_contract':contract,'raw_before':raw_ref,
            'preserved_scientific_fields':True,'preserved_caps':True,'unresolved_blocking_findings':[],
            'source_code':source,'reviewer_id':'independent','contract_author_id':result['agent_id'],
            'independent_of':t['authors']+t['contributors']+[r['agent_id'] for r in contributors]+[result['agent_id']],
            'requested_runtime':'fixture','observed_runtime':'UNKNOWN',
            'diffs':{'controller_patch':diff,'numerical_source':diff},'controller_patch':diff,
            'controller_source':rc._receipt(str(Path(rc.__file__).resolve())),
            'controller_tests':rc._receipt(str(Path(__file__).resolve()))}
        review_ref = write(review)
        lineage['future_source_review_path'] = review_ref['path']
        after_ref = write(after,'FROZEN_INPUT_REPAIR.json')
        review['after_input'] = after_ref
        review_ref = write(review, Path(review_ref['path']).name)
        tr = {'schema':'htt.repair_input_transition/1','kind':'cf4_final_group_fixture_same_science',
            'campaign':state['campaign_identity'],'task_id':key,'research_packet_id':packet['packet_id'],
            'research_result':result_ref,'repair_contract':contract,'before_input':before_ref,
            'after_input':after_ref,'raw_before':raw_ref,'source_review':review_ref,
            'preparation_contributors':contributors}
        expected = {n:seal(n)['sha256'] for n in rc._CF4_OLD_SHA256 if (root/n).is_file()}
        for name,value in (('_CF4_DIRECTORY',str(root)),('_CF4_OLD_SHA256',expected),
                           ('_CF4_RESEARCH_PACKET',packet['packet_id']),('_CF4_SOURCE_REVIEW_PATH',review_ref['path'])):
            binding = patch.object(rc,name,value); binding.start(); self.addCleanup(binding.stop)
        return state,result,tr,write,after,review

    def test_cf4_atomic_binding_retains_old_code_and_accounting(self):
        state,result,tr,write,after,review = self.fixture(); old = copy.deepcopy(state)
        ref = write(tr); rc.record(state,result,POLICY,ref['path'])
        t = state['tasks'][result['task_id']]; prior = old['tasks'][result['task_id']]
        for key in ('failures','accounting','attempt','ultra_used'):
            self.assertEqual(t.get(key),prior.get(key))
        self.assertEqual(state['packets'],old['packets'])
        self.assertEqual(t['spec_history'],[prior['spec']])
        self.assertEqual(t['spec']['input_sources'][:4],prior['spec']['input_sources'][:4])
        self.assertEqual(len(t['spec']['input_sources']),len(prior['spec']['input_sources'])+2)
        self.assertEqual(t['repair_input_transition']['parent_ack'],after['repair_lineage']['old_evidence']['ACTUAL_ACK_EXECUTE.json'])
        snapshot = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError): rc.record(state,result,POLICY,ref['path'])
        self.assertEqual(state,snapshot)
        packet = rc.next_packet(state,POLICY,PROFILES)
        self.assertEqual(packet['input_identity'],'sha256:'+tr['after_input']['sha256'])

    def test_cf4_invalid_transitions_leave_state_unchanged(self):
        state,result,tr,write,after,review = self.fixture()
        cases = []
        for key in ('kind','campaign','research_packet_id','task_id'):
            bad = copy.deepcopy(tr); bad[key] = 'stale'; cases.append(bad)
        bad = copy.deepcopy(tr); bad['research_result'] = write({**result,'outcome':'unknown'}); cases.append(bad)
        for field,value in (('source_inputs',[]),('claim_ceiling','changed'),('limits',{})):
            bad = copy.deepcopy(after); bad[field] = value
            altered = copy.deepcopy(tr); altered['after_input'] = write(bad); cases.append(altered)
        for field,value in (('cap_seconds',601),('cumulative_seconds',0),('threads',2),
                            ('rss_cap_bytes',2147483649),('future_invocation_seconds_cap',121)):
            bad = copy.deepcopy(after); bad['repair_lineage']['inherited_accounting'][field] = value
            altered = copy.deepcopy(tr); altered['after_input'] = write(bad); cases.append(altered)
        for field in ('future_ack_path','future_execution_ledger_path','future_run_receipt_path'):
            bad = copy.deepcopy(after); bad['repair_lineage'][field] = tr['before_input']['path']
            altered = copy.deepcopy(tr); altered['after_input'] = write(bad); cases.append(altered)
        for field in ('ACTUAL_ACK_EXECUTE.json','RUN_RECEIPT.json','EXECUTOR_RESULT.json'):
            bad = copy.deepcopy(after); bad['repair_lineage']['old_evidence'][field]['sha256'] = '0'*64
            altered = copy.deepcopy(tr); altered['after_input'] = write(bad); cases.append(altered)
        bad = copy.deepcopy(review); bad['reviewer_id'] = tr['preparation_contributors'][0]['agent_id']
        altered = copy.deepcopy(tr); altered['source_review'] = write(bad); cases.append(altered)
        for altered in cases:
            if altered['after_input'] != tr['after_input']:
                document = json.loads(Path(altered['after_input']['path']).read_text())
                altered['after_input'] = write(document, 'FROZEN_INPUT_REPAIR.json')
                bound_review = {**review,'after_input':altered['after_input'],
                                'source_code':document['source_code']}
                altered['source_review'] = write(bound_review, Path(tr['source_review']['path']).name)
            else:
                write(after, 'FROZEN_INPUT_REPAIR.json')
                if altered['source_review'] != tr['source_review']:
                    bad_review = json.loads(Path(altered['source_review']['path']).read_text())
                    altered['source_review'] = write(bad_review, Path(tr['source_review']['path']).name)
                if altered['source_review'] == tr['source_review']:
                    write(review, Path(tr['source_review']['path']).name)
            snapshot = copy.deepcopy(state)
            with self.assertRaises(rc.ControllerError): rc.record(state,result,POLICY,write(altered)['path'])
            self.assertEqual(state,snapshot)
        # Even correctly resealed edits outside the allowed two bodies are rejected.
        path = Path(rc._CF4_DIRECTORY)/'test_consume_repair.py'
        path.write_text(path.read_text().replace('len(METHODS), 6','len(METHODS), 5'))
        with self.assertRaisesRegex(rc.ControllerError,'extra CF4 test AST edit'):
            rc._cf4_test_ast((path.parent/'test_consume.py').read_bytes(),path.read_bytes())

    def test_cf4_resealed_extra_ast_or_original_code_drift_rejected_atomically(self):
        state,result,tr,write,after,review = self.fixture()
        root = Path(rc._CF4_DIRECTORY)
        repaired = root/'test_consume_repair.py'
        repaired.write_text(repaired.read_text().replace('len(METHODS), 6','len(METHODS), 5'))
        for row in after['source_code']:
            if row['path'] == str(repaired):
                row.update(rc._receipt(str(repaired)),size_bytes=repaired.stat().st_size)
        tr['after_input'] = write(after,'FROZEN_INPUT_REPAIR.json')
        snapshot = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError,'extra CF4 test AST edit'):
            rc.record(state,result,POLICY,write(tr)['path'])
        self.assertEqual(state,snapshot)
        repaired.write_bytes((root/'test_consume.py').read_bytes())
        consumer = root/'consume.py'; consumer.write_text(consumer.read_text()+'# drift\n')
        for row in after['source_code']:
            if row['path'] in {str(consumer),str(repaired)}:
                path = Path(row['path']); row.update(rc._receipt(str(path)),size_bytes=path.stat().st_size)
        tr['after_input'] = write(after,'FROZEN_INPUT_REPAIR.json')
        with self.assertRaisesRegex(rc.ControllerError,'CF4 original code changed'):
            rc.record(state,result,POLICY,write(tr)['path'])
        self.assertEqual(state,snapshot)

    def test_cf4_concurrent_packet_or_higher_debit_rejected(self):
        state,result,tr,write,after,review = self.fixture()
        ref = write(tr)
        for reason in ('concurrent','higher_debit'):
            bad = copy.deepcopy(state)
            if reason == 'concurrent':
                bad['packets']['unresolved'] = {**bad['packets'][result['packet_id']],
                                                'packet_id':'unresolved'}
            else:
                bad['tasks'][result['task_id']]['accounting']['seconds'] = 65
            snapshot = copy.deepcopy(bad)
            with self.assertRaises(rc.ControllerError): rc.record(bad,result,POLICY,ref['path'])
            self.assertEqual(bad,snapshot)


class CF4SourceLayoutRepairTests(unittest.TestCase):
    """Copied metadata and source only; no actual task dispatch or science imports."""
    setUp = base.ControllerTests.setUp
    state = base.ControllerTests.state
    launch = base.ControllerTests.launch

    def fixture(self):
        from unittest.mock import patch
        original = Path(rc._CF4_DIRECTORY); root = Path(self.tmp.name)
        def write(value, name):
            path = root/name; path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(value)); return rc._receipt(str(path))
        def seal(name): return rc._receipt(str(root/name))
        def relocated(value):
            return json.loads(json.dumps(value).replace(str(original),str(root)))
        for name in rc._CF4_LAYOUT_PREIMAGES:
            target = root/name; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((original/name).read_bytes())
        before = relocated(json.loads((original/'FROZEN_INPUT_REPAIR.json').read_text()))
        before_ref = write(before,'FROZEN_INPUT_REPAIR.json')
        after = relocated(json.loads((original/'FROZEN_INPUT_SOURCE_LAYOUT.json').read_text()))
        lineage = after['source_layout_lineage']; lineage['before_input'] = before_ref
        for row in after['source_layout_code']:
            relative = Path(row['path']).relative_to(root)
            target = root/relative; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((original/relative).read_bytes())
        parent_name = 'repair_run/ACTUAL_CONTROLLER_REPAIR_PACKET.json'
        parent = relocated(json.loads((original/parent_name).read_text()))
        parent['input_identity'] = 'sha256:'+before_ref['sha256']
        parent_ref = write(parent,parent_name)
        ack_name = 'repair_run/ACTUAL_ACKNOWLEDGED_REPAIR_PACKET.json'
        ack = relocated(json.loads((original/ack_name).read_text()))
        ack.update(input_identity=parent['input_identity'],actual_acknowledged_packet=parent_ref)
        ack_ref = write(ack,ack_name)
        raw_name = 'repair_run/RUN_RECEIPT.json'
        raw = json.loads((original/raw_name).read_text()); raw['ack_sha256'] = ack_ref['sha256']
        raw_ref = write(raw,raw_name)
        lineage['failed_parent_evidence'] = {n:seal(n) for n in lineage['failed_parent_evidence']}
        lineage['predecessor_transition'] = seal('ACTUAL_FIXTURE_INPUT_TRANSITION.json')
        key = rc._CF4_TASK
        inventory = [{'path':r['path'],'sha256':r['sha256'],'bytes':r['size_bytes'],'role':'code'}
                     for r in before['source_code']]
        inventory.append({**before_ref,'bytes':(root/'FROZEN_INPUT_REPAIR.json').stat().st_size,'role':'contract'})
        state = self.state([task(key,input_identity=parent['input_identity'],input_sources=inventory)])
        t = state['tasks'][key]; t['phase'] = 'research'; packet = self.launch(state)
        state['packets'][parent['packet_id']] = parent
        t['history'].append({'packet_id':parent['packet_id'],'phase':'repair','receipt':raw_ref})
        t['repair_input_transition'] = {**lineage['predecessor_transition'],'parent_input':{'retained':'old'}}
        t['accounting'] = {'seconds':75.37988796900027}; t['failures'] = [{'retained':'old failures'}]
        result = {'packet_id':packet['packet_id'],'task_id':key,
            'agent_id':state['packets'][packet['packet_id']]['agent_id'],'input_identity':parent['input_identity'],
            'outcome':'success','repair_plan':'parser source extent repair only','raw_receipt':raw_ref['path']}
        result_ref = write(result,'RESEARCH_RESULT.json'); lineage['research_result_future_path'] = result_ref['path']
        review_path = str(root/'REVIEW.json'); lineage['future_source_review_path'] = review_path
        after_ref = write(after,'FROZEN_INPUT_SOURCE_LAYOUT.json')
        contributors = [{'agent_id':'fixture-'+role,'role':role,'requested_runtime':'fixture',
            'observed_runtime':'UNKNOWN','raw_receipt':write({'role':role},role+'.json')}
            for role in ('controller_patch','numerical_source')]
        diff = write({'fixture':'diff'},'diff.json')
        review = {'decision':'APPROVE_ONE_BOUNDED_SAME_TASK_SOURCE_LAYOUT_REPAIR','scientific_admission':'HOLD',
            'before_input':before_ref,'after_input':after_ref,'repair_contract':lineage['source_layout_contract'],
            'raw_before':raw_ref,'preserved_scientific_fields':True,'preserved_caps':True,
            'unresolved_blocking_findings':[],'source_layout_code':after['source_layout_code'],
            'contract_author_id':result['agent_id'],'reviewer_id':'independent',
            'independent_of':t['authors']+t['contributors']+[r['agent_id'] for r in contributors]+[result['agent_id']],
            'requested_runtime':'fixture','observed_runtime':'UNKNOWN',
            'diffs':{'controller_patch':diff,'numerical_source':diff},
            'controller_source':rc._receipt(str(Path(rc.__file__).resolve())),
            'controller_tests':rc._receipt(str(Path(__file__).resolve()))}
        review_ref = write(review,'REVIEW.json')
        tr = {'schema':'htt.repair_input_transition/1','kind':'cf4_source_layout_same_science',
            'campaign':state['campaign_identity'],'task_id':key,'research_packet_id':packet['packet_id'],
            'research_result':result_ref,'repair_contract':lineage['source_layout_contract'],
            'before_input':before_ref,'after_input':after_ref,'raw_before':raw_ref,'source_review':review_ref,
            'preparation_contributors':contributors}
        expected = {n:seal(n)['sha256'] for n in rc._CF4_LAYOUT_PREIMAGES}
        for name,value in (('_CF4_DIRECTORY',str(root)),('_CF4_LAYOUT_PREIMAGES',expected),
                           ('_CF4_LAYOUT_REVIEW_PATH',review_path)):
            binding = patch.object(rc,name,value); binding.start(); self.addCleanup(binding.stop)
        return state,result,tr,write,after,review

    def test_source_layout_atomic_sequential_binding_and_replay_rejection(self):
        state,result,tr,write,after,review = self.fixture(); old = copy.deepcopy(state)
        ref = write(tr,'TRANSITION.json'); rc.record(state,result,POLICY,ref['path'])
        t = state['tasks'][result['task_id']]; prior = old['tasks'][result['task_id']]
        self.assertEqual(t['repair_input_transition_history'],[prior['repair_input_transition']])
        self.assertEqual(t['spec_history'],[prior['spec']])
        for key in ('failures','accounting','attempt','ultra_used'):
            self.assertEqual(t.get(key),prior.get(key))
        self.assertEqual(t['spec']['input_sources'][:6],prior['spec']['input_sources'][:6])
        self.assertEqual(len(t['spec']['input_sources']),len(prior['spec']['input_sources'])+4)
        snapshot = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError): rc.record(state,result,POLICY,ref['path'])
        self.assertEqual(state,snapshot)

    def test_source_layout_invalid_metadata_rejected_without_state_mutation(self):
        state,result,tr,write,after,review = self.fixture()
        for change in ('old_lineage','debit','cap','predecessor','future_path','reviewer','packet','prior_transition','concurrent','unknown_research','stale_failure'):
            bad = copy.deepcopy(after); altered = copy.deepcopy(tr); current = copy.deepcopy(state)
            reviewed = copy.deepcopy(review)
            if change == 'old_lineage': bad['repair_lineage']['task_id'] = 'changed'
            if change == 'debit': bad['source_layout_lineage']['inherited_accounting']['cumulative_seconds'] = 75
            if change == 'cap': bad['source_layout_lineage']['inherited_accounting']['cap_seconds'] = 601
            if change == 'predecessor': bad['source_layout_lineage']['predecessor_transition']['sha256'] = '0'*64
            if change == 'future_path': bad['source_layout_lineage']['future_ack_path'] = tr['before_input']['path']
            if change == 'reviewer': reviewed['reviewer_id'] = result['agent_id']
            if change == 'packet': altered['research_packet_id'] = 'stale'
            if change == 'prior_transition': current['tasks'][result['task_id']]['repair_input_transition']['sha256'] = '0'*64
            supplied_result = copy.deepcopy(result)
            if change == 'unknown_research': supplied_result['outcome'] = 'unknown'
            if change == 'stale_failure': altered['raw_before'] = tr['before_input']
            if change == 'concurrent': current['packets']['unresolved'] = {**current['packets'][result['packet_id']], 'packet_id':'unresolved'}
            altered['after_input'] = write(bad,'FROZEN_INPUT_SOURCE_LAYOUT.json')
            reviewed['after_input'] = altered['after_input']; altered['source_review'] = write(reviewed,'REVIEW.json')
            snapshot = copy.deepcopy(current)
            with self.assertRaises(rc.ControllerError): rc.record(current,supplied_result,POLICY,write(altered,'TRANSITION.json')['path'])
            self.assertEqual(current,snapshot)

    def test_source_layout_extra_science_ast_and_changed_math_test_rejected(self):
        state,result,tr,write,after,review = self.fixture()
        root = Path(rc._CF4_DIRECTORY); parser = root/'source_layout/consume.py'
        parser.write_text(parser.read_text()+'\nOTHER_SCIENCE = 1\n')
        for row in after['source_layout_code']:
            if row['path'] == str(parser): row.update(rc._receipt(str(parser)),size_bytes=parser.stat().st_size)
        tr['after_input'] = write(after,'FROZEN_INPUT_SOURCE_LAYOUT.json'); snapshot = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError,'CF4 change outside parser body'):
            rc.record(state,result,POLICY,write(tr,'TRANSITION.json')['path'])
        self.assertEqual(state,snapshot)
        parser.write_bytes((root/'consume.py').read_bytes())
        tests = root/'source_layout/test_consume_repair.py'; tests.write_text(tests.read_text()+'# drift\n')
        for row in after['source_layout_code']:
            if row['path'] in (str(parser),str(tests)):
                p = Path(row['path']); row.update(rc._receipt(str(p)),size_bytes=p.stat().st_size)
        tr['after_input'] = write(after,'FROZEN_INPUT_SOURCE_LAYOUT.json')
        with self.assertRaisesRegex(rc.ControllerError,'CF4 layout eight mathematical tests changed'):
            rc.record(state,result,POLICY,write(tr,'TRANSITION.json')['path'])
        self.assertEqual(state,snapshot)
