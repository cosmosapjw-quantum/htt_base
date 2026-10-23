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
                                   ("products_sha256", False), ("products", False)):
            with self.subTest(inventory=inventory, as_list=as_list):
                state, _, artifact, _ = self.manifest_fixture(inventory, as_list)
                packet = self.plan(state)
                self.assertIn(str(artifact), packet["review_context"]["scope"]["candidate_seals"])
                rc.acknowledge(state, packet["packet_id"], "actual-independent-reviewer")
                self.result(state, packet, acceptance_met=True)
                self.assertEqual(state["tasks"]["CANDIDATE"]["state"], "completed")

    def test_all_manifest_inventories_mutation_or_removal_before_ack_rejects_atomically(self):
        for inventory in ("files", "products_sha256", "products"):
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
        for inventory in ("files", "products_sha256", "products"):
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
