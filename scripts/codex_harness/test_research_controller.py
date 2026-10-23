"""Behavior tests for durable routing; no native execution is simulated as observed."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
# A selected-input fixture can exercise the patch without cloning the project.
INPUTS = HERE.parents[2] / "inputs"
ROUTER_DIR = HERE if (HERE / "native_routing.py").exists() else INPUTS / "scripts/codex_harness"
sys.path.insert(0, str(ROUTER_DIR))
sys.path.insert(0, str(HERE))
import native_routing
import research_controller as rc

POLICY = native_routing.load_policy(ROUTER_DIR.parents[1] / "docs/harness/NATIVE_ROUTING_POLICY_V1.json")
PROFILES = {(v["requested"]["model"], v["requested"]["effort"]) for v in POLICY["routes"].values()}


def task(key, deps=(), **kwargs):
    return {"id": key, "depends_on": list(deps), "goal": "Finite frozen calculation " + key,
            "acceptance": "Exact reference and unchanged source assumptions", "input_identity": "input-v1",
            "kind": "numeric", "approved_repair_id": "repair-1", **kwargs}


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.counter = 0

    def state(self, tasks=None):
        return rc.initialize({"campaign_id": "test", "approved_scientific_repairs": ["repair-1", "repair-2"],
                              "tasks": tasks or [task("A"), task("B", ["A"])]},
                             "Owner authorizes campaign and bounded scientific repair")

    def launch(self, s, profiles=PROFILES):
        p = rc.next_packet(s, POLICY, profiles)
        self.counter += 1
        rc.acknowledge(s, p["packet_id"], "native-agent-" + str(self.counter))
        return p

    def result(self, s, p, outcome="success", **kwargs):
        self.counter += 1
        path = Path(self.tmp.name) / ("receipt-" + str(self.counter))
        path.write_text("unique actual outcome receipt " + str(self.counter))
        r = {"packet_id": p["packet_id"], "task_id": p["task_id"],
             "agent_id": s["packets"][p["packet_id"]]["agent_id"], "input_identity": p["input_identity"],
             "raw_receipt": str(path), "outcome": outcome,
             "candidate_identity": "candidate-v1", "validation_evidence": ["dense reference agrees"], **kwargs}
        if r.get("issue", {}).get("true_external"):
            r["issue"].setdefault("external_payload", {"required": ["exact physical all-m T/E/B atlas"],
                "source_or_owner": "source release custodian", "exhaustion_receipt": str(path)})
        rc.record(s, r, POLICY)
        return r

    def issue(self, **kwargs):
        if kwargs.get("true_external") and "class" not in kwargs:
            kwargs["class"] = "input"
        return {"class": "numeric", "question": "Is covariance SPD under exact source convention?",
                "exact_missing_or_defect": "Negative Schur eigenvalue at source row 31",
                "input_identity": "input-v1", "substantive": True, **kwargs}

    def finish(self, s):
        p = self.launch(s)
        self.result(s, p)
        review = self.launch(s)
        self.assertEqual(review["phase"], "review")
        self.result(s, review, acceptance_met=True)

    def test_dependent_blocker_escalation_repair_independent_review_continue(self):
        s = self.state()
        p = self.launch(s)
        self.result(s, p, "blocker", issue=self.issue(high_consequence=True, risk="Biases physical inference"))
        escalation = self.launch(s)
        self.assertEqual(escalation["route"]["requested"], {"model": "gpt-6-astra", "effort": "ultra"})
        self.result(s, escalation, repair_plan="Factor source covariance and compare dense Schur reference")
        repair = self.launch(s)
        self.assertEqual(repair["phase"], "repair")
        self.result(s, repair)
        review = self.launch(s)
        self.result(s, review, acceptance_met=True)
        self.assertEqual(rc.summary(s)["ready"], ["B"])
        self.finish(s)
        self.assertEqual(rc.summary(s)["status"], "CAMPAIGN_ACCEPTANCES_REVIEWED")
        self.assertEqual(s["tasks"]["A"]["ultra_used"], ["repair-1"])

    def test_two_preserved_substantive_failures_trigger_ultra(self):
        s = self.state([task("A")])
        self.result(s, self.launch(s), "blocker", issue=self.issue())
        self.assertEqual(s["tasks"]["A"]["phase"], "research")
        self.result(s, self.launch(s), "blocker", issue=self.issue())
        self.assertEqual(s["tasks"]["A"]["phase"], "escalation")
        self.assertEqual(len(s["tasks"]["A"]["failures"]), 2)

    def test_once_per_approved_repair_then_hold_and_resume_requires_new_evidence(self):
        s = self.state([task("A")])
        self.result(s, self.launch(s), "blocker", issue=self.issue(high_consequence=True, risk="Wrong uncertainty"))
        self.result(s, self.launch(s), repair_plan="Repair exact factorization")
        result = self.result(s, self.launch(s), "blocker", issue=self.issue())
        self.assertEqual(s["tasks"]["A"]["state"], "held")
        with self.assertRaises(rc.ControllerError):
            rc.resume(s, "A", result["raw_receipt"], "input-v1", "repair-1")
        semantic = Path(self.tmp.name) / "new-input.json"
        semantic.write_text(json.dumps({"kind": "input", "before": {"release": "v1"},
            "after": {"release": "v2 with corrected covariance"},
            "scope": "source covariance", "discriminator": "recompute Schur residual"}))
        rc.resume(s, "A", str(semantic), "input-v2", "repair-2")
        self.assertEqual(s["tasks"]["A"]["state"], "ready")
        self.assertEqual(len(s["tasks"]["A"]["history"]), 3)

    def test_external_missing_is_acquisition_opportunity_not_terminal(self):
        s = self.state([task("A", kind="input", external_missing=["public table"]), task("B")])
        p = self.launch(s)
        self.assertEqual(p["phase"], "acquisition")
        self.result(s, p, "blocker", issue=self.issue(**{"class": "input", "true_external": True}))
        self.assertEqual(rc.next_packet(s, POLICY, PROFILES)["task_id"], "B")
        self.assertEqual(s["tasks"]["A"]["ultra_used"], [])

    def test_environment_permission_and_prohibition_hold_without_ultra(self):
        for classification in ("environment", "permission", "input"):
            with self.subTest(classification=classification):
                s = self.state([task("A")])
                self.result(s, self.launch(s), "blocker", issue=self.issue(
                    **{"class": classification, "true_external": classification == "input",
                       "high_consequence": True, "risk": "quota blocked"}))
                self.assertEqual(s["tasks"]["A"]["state"], "held")
                self.assertEqual(s["tasks"]["A"]["ultra_used"], [])

    def test_empty_ready_and_unresolved_plan_or_running_never_success(self):
        s = self.state([task("A"), task("B", ["A"])])
        p = rc.next_packet(s, POLICY, PROFILES)
        self.assertEqual(rc.summary(s)["status"], "AWAITING_NATIVE_OUTCOME")
        self.assertEqual(rc.next_packet(s, POLICY, PROFILES), p)
        rc.acknowledge(s, p["packet_id"], "actual-agent")
        self.assertEqual(rc.next_packet(s, POLICY, PROFILES)["status"], "AWAITING_NATIVE_OUTCOME")
        self.result(s, p, "blocker", issue=self.issue(true_external=True))
        self.assertEqual(rc.summary(s)["ready"], [])
        self.assertEqual(rc.summary(s)["status"], "HOLD_UNRESOLVED_BRANCHES")

    def test_stale_input_packet_agent_and_review_candidate_rejected(self):
        s = self.state([task("A")])
        p = self.launch(s)
        with self.assertRaises(rc.ControllerError):
            self.result(s, p, input_identity="old-input")
        with self.assertRaises(rc.ControllerError):
            self.result(s, p, agent_id="invented")
        self.result(s, p)
        review = self.launch(s)
        with self.assertRaises(rc.ControllerError):
            self.result(s, review, candidate_identity="stale", acceptance_met=True)
        self.result(s, review, acceptance_met=True)
        with self.assertRaises(rc.ControllerError):
            self.result(s, p)

    def test_unlaunched_result_and_author_as_reviewer_rejected(self):
        s = self.state([task("A")])
        p = rc.next_packet(s, POLICY, PROFILES)
        with self.assertRaises(rc.ControllerError):
            rc.record(s, {"packet_id": p["packet_id"]}, POLICY)
        rc.acknowledge(s, p["packet_id"], "author")
        self.result(s, p)
        review = rc.next_packet(s, POLICY, PROFILES)
        with self.assertRaises(rc.ControllerError):
            rc.acknowledge(s, review["packet_id"], "author")

    def test_exact_catalog_only_and_other_ready_not_starved(self):
        s = self.state([task("A", kind="theory"), task("B")])
        profiles = {("gpt-6-sol", "high")}
        p = rc.next_packet(s, POLICY, profiles)
        self.assertEqual(p["task_id"], "B")
        s = self.state([task("A", kind="theory")])
        out = rc.next_packet(s, POLICY, {("gpt-6-astra", "high")})
        self.assertEqual(out["status"], "HOLD_TRANSPORT_UNAVAILABLE")
        self.assertEqual(s["tasks"]["A"]["state"], "ready")
        self.assertFalse(out["unavailable"][0]["route"]["launch_performed"])

    def test_fairness_new_ready_work_precedes_repeated_branch(self):
        s = self.state([task("A"), task("B")])
        self.result(s, self.launch(s), "blocker", issue=self.issue())
        self.assertEqual(rc.next_packet(s, POLICY, PROFILES)["task_id"], "B")

    def test_invalid_dag_and_count_only_reuse_rejected(self):
        for rows in ([task("A", ["missing"])], [task("A", ["B"]), task("B", ["A"])],
                     [task("A"), task("A")], [task("A", initial_state="completed")]):
            with self.subTest(rows=rows), self.assertRaises(rc.ControllerError):
                self.state(rows)

    def test_original_science_contract_checked_and_scoped_completion_separate(self):
        dag = {"nodes": [{"id": "original", "depends_on": [], "acceptance": "native atlas", "state": "blocked_input"}]}
        plan = {"all_original_nodes": copy.deepcopy(dag["nodes"])}
        campaign = {"campaign_id": "subset", "tasks": [task("A")]}
        bound = rc.bind_original_contracts(campaign, dag, plan)
        s = rc.initialize(bound, "current authorization")
        self.finish(s)
        self.assertEqual(s["campaign"]["original_science_contract"]["nodes"][0]["state"], "blocked_input")
        plan["all_original_nodes"][0]["acceptance"] = "toy atlas"
        with self.assertRaises(rc.ControllerError):
            rc.bind_original_contracts(campaign, dag, plan)

    def test_checkpoint_roundtrip_keeps_packets_outcomes_and_unknown_observation(self):
        s = self.state([task("A")])
        p = self.launch(s)
        self.result(s, p)
        path = Path(self.tmp.name) / "state.json"
        rc.save(path, s)
        resumed = json.loads(path.read_text())
        self.assertEqual(resumed, s)
        self.assertEqual(resumed["packets"][p["packet_id"]]["observed_runtime"], "UNKNOWN")
        self.assertEqual(rc.next_packet(resumed, POLICY, PROFILES)["phase"], "review")

    def test_planned_review_replay_returns_current_packet_not_old_author_packet(self):
        s = self.state([task("A")])
        author = self.launch(s)
        self.result(s, author)
        review = rc.next_packet(s, POLICY, PROFILES)
        self.assertNotEqual(review["packet_id"], author["packet_id"])
        self.assertEqual(rc.next_packet(s, POLICY, PROFILES), review)

    def test_shared_repair_id_has_campaign_wide_ultra_budget(self):
        s = self.state([task("A"), task("B")])
        self.result(s, self.launch(s), "blocker", issue=self.issue(high_consequence=True, risk="Scientific admission"))
        # Fairness selects B before A's escalation. Same repair identity cannot reserve ultra twice.
        b = self.launch(s)
        self.assertEqual(b["task_id"], "B")
        self.result(s, b, "blocker", issue=self.issue(high_consequence=True, risk="Scientific admission"))
        self.assertEqual(s["tasks"]["B"]["phase"], "research")
        self.assertEqual(len(s["ultra_repairs"]), 0)
        self.assertEqual(len(s["ultra_pending"]), 1)

    def test_unavailable_ultra_is_only_reserved_until_actual_ack(self):
        s = self.state([task("A")])
        self.result(s, self.launch(s), "blocker", issue=self.issue(high_consequence=True, risk="Scientific admission"))
        out = rc.next_packet(s, POLICY, set())
        self.assertEqual(out["status"], "HOLD_TRANSPORT_UNAVAILABLE")
        self.assertEqual(s["ultra_repairs"], {})
        self.assertEqual(s["tasks"]["A"]["ultra_used"], [])
        p = rc.next_packet(s, POLICY, PROFILES)
        self.assertEqual(s["ultra_repairs"], {})
        rc.acknowledge(s, p["packet_id"], "actual-ultra-agent")
        self.assertEqual(s["ultra_repairs"]["repair-1"]["agent_id"], "actual-ultra-agent")

    def test_external_bool_cannot_bypass_scientific_escalation(self):
        s = self.state([task("A")])
        p = self.launch(s)
        with self.assertRaises(rc.ControllerError):
            self.result(s, p, "blocker", issue=self.issue(**{"class": "numeric", "true_external": True}))
        self.assertEqual(s["tasks"]["A"]["state"], "running")
        self.assertEqual(s["tasks"]["A"]["failures"], [])

    def test_prelaunch_quota_refusal_continues_other_ready_without_ultra_consumption(self):
        s = self.state([task("A"), task("B")])
        raw = self.result(s, self.launch(s), "blocker", issue=self.issue(high_consequence=True, risk="Scientific admission"))
        # Execute independent B; fairness then returns A before B's review.
        b = self.launch(s)
        self.assertEqual(b["task_id"], "B")
        self.result(s, b)
        p = rc.next_packet(s, POLICY, PROFILES)
        self.assertEqual(p["phase"], "escalation")
        rc.launch_failed(s, p["packet_id"], raw["raw_receipt"], "environment", "Provider monthly native launch quota")
        self.assertEqual(s["ultra_repairs"], {})
        self.assertEqual(s["ultra_pending"], {})
        self.assertFalse(s["packets"][p["packet_id"]]["launch_performed"])
        self.assertEqual(rc.next_packet(s, POLICY, PROFILES)["task_id"], "B")

    def test_implementation_route_cannot_inject_ultra_without_blocker(self):
        with self.assertRaises(rc.ControllerError):
            self.state([task("A", implementation_route="blocker_escalation")])

    def test_research_contributor_is_explicitly_excluded_from_reviewer(self):
        s = self.state([task("A")])
        self.result(s, self.launch(s), "blocker", issue=self.issue())
        research = self.launch(s)
        research_agent = s["packets"][research["packet_id"]]["agent_id"]
        self.result(s, research, repair_plan="bounded repair")
        self.result(s, self.launch(s))
        review = rc.next_packet(s, POLICY, PROFILES)
        self.assertIn(research_agent, s["tasks"]["A"]["contributors"])
        with self.assertRaises(rc.ControllerError):
            rc.acknowledge(s, review["packet_id"], research_agent)

    def test_declared_prior_advisor_and_parent_are_excluded_from_review(self):
        s = self.state([task("A", contributors=["prior-astra-advisor", "parent-author", "prior-astra-advisor"])])
        self.assertEqual(s["tasks"]["A"]["contributors"], ["prior-astra-advisor", "parent-author"])
        self.result(s, self.launch(s))
        review = rc.next_packet(s, POLICY, PROFILES)
        for contributor in ("prior-astra-advisor", "parent-author"):
            with self.subTest(contributor=contributor), self.assertRaises(rc.ControllerError):
                rc.acknowledge(s, review["packet_id"], contributor)

    def test_invalid_declared_contributor_identity_rejected(self):
        for contributors in ("parent", [""], [None]):
            with self.subTest(contributors=contributors), self.assertRaises(rc.ControllerError):
                self.state([task("A", contributors=contributors)])

    def test_reviewer_plan_drives_one_targeted_repair_fresh_review_and_next(self):
        s = self.state()
        self.result(s, self.launch(s))
        review = self.launch(s)
        self.result(s, review, "blocker", issue=self.issue(), repair_plan="Whiten covariance relatively; test unit scaling and tiny contrast")
        self.assertEqual(s["tasks"]["A"]["phase"], "repair")
        self.assertEqual(len(s["tasks"]["A"]["targeted_repairs"]), 1)
        repair = self.launch(s)
        with self.assertRaises(rc.ControllerError):
            self.result(s, repair, candidate_identity="candidate-v1")
        self.result(s, repair, candidate_identity="candidate-v2")
        closeout = self.launch(s)
        self.assertEqual(closeout["phase"], "review")
        with self.assertRaises(rc.ControllerError):
            self.result(s, closeout, candidate_identity="candidate-v1", acceptance_met=True)
        self.result(s, closeout, candidate_identity="candidate-v2", acceptance_met=True)
        self.assertEqual(rc.next_packet(s, POLICY, PROFILES)["task_id"], "B")

    def test_explicit_deterministic_counterexample_repair_after_consumed_ultra(self):
        s = self.state()
        self.result(s, self.launch(s))
        self.result(s, self.launch(s), "blocker", issue=self.issue(high_consequence=True, risk="False estimability"))
        ultra = self.launch(s)
        self.assertEqual(ultra["phase"], "escalation")
        self.result(s, ultra, repair_plan="Use relative covariance whitening and contrast normalization")
        self.result(s, self.launch(s), candidate_identity="candidate-v2")
        review = self.launch(s)
        issue = self.issue(exact_missing_or_defect="K/s underflows before original-K zero check; tiny nonestimable contrast accepted")
        self.result(s, review, "blocker", candidate_identity="candidate-v2", issue=issue,
                    repair_plan="Check original K for zero before division; classify scaled contrast without underflow")
        self.assertEqual(s["tasks"]["A"]["phase"], "repair")
        self.assertEqual(len(s["ultra_repairs"]), 1)
        repair = self.launch(s)
        with self.assertRaises(rc.ControllerError):
            self.result(s, repair, candidate_identity="candidate-v2")
        self.result(s, repair, candidate_identity="candidate-v3")
        final_review = self.launch(s)
        with self.assertRaises(rc.ControllerError):
            self.result(s, final_review, candidate_identity="candidate-v2", acceptance_met=True)
        self.result(s, final_review, candidate_identity="candidate-v3", acceptance_met=True)
        self.assertEqual(rc.next_packet(s, POLICY, PROFILES)["task_id"], "B")
        self.assertEqual(len(s["ultra_repairs"]), 1)

    def test_review_without_precise_plan_does_not_skip_research(self):
        for plan in (None, "", "   "):
            with self.subTest(plan=plan):
                s = self.state([task("A")])
                self.result(s, self.launch(s))
                review = self.launch(s)
                self.result(s, review, "blocker", issue=self.issue(), repair_plan=plan)
                self.assertEqual(s["tasks"]["A"]["phase"], "research")

    def test_review_repair_plan_cannot_skip_high_consequence_escalation(self):
        s = self.state([task("A")])
        self.result(s, self.launch(s))
        self.result(s, self.launch(s), "blocker", issue=self.issue(high_consequence=True, risk="Physical inference changes"),
                    repair_plan="Concrete plan still requires eligible ultra diagnosis")
        self.assertEqual(s["tasks"]["A"]["phase"], "escalation")

    def test_targeted_review_repair_cannot_loop_on_new_candidate(self):
        s = self.state([task("A", approved_repair_id=None)])
        self.result(s, self.launch(s))
        self.result(s, self.launch(s), "blocker", issue=self.issue(), repair_plan="First bounded repair")
        self.result(s, self.launch(s), candidate_identity="candidate-v2")
        self.result(s, self.launch(s), "blocker", candidate_identity="candidate-v2", issue=self.issue(), repair_plan="Repeat proposed closeout")
        self.assertEqual(s["tasks"]["A"]["phase"], "research")
        self.assertEqual(len(s["tasks"]["A"]["targeted_repairs"]), 1)

    def test_prompt_history_is_bounded_refs_without_losing_durable_outcomes(self):
        s = self.state([task("A")])
        huge = "OLD_LARGE_RESULT_SENTINEL" + "x" * 200000
        self.result(s, self.launch(s), diagnostic_payload=huge)
        self.result(s, self.launch(s), "blocker", issue=self.issue(), repair_plan="Current exact whitening repair")
        self.result(s, self.launch(s), candidate_identity="candidate-v2")
        history = copy.deepcopy(s["tasks"]["A"]["history"])
        current_issue = copy.deepcopy(s["tasks"]["A"]["issue"])
        packet = rc.next_packet(s, POLICY, PROFILES)
        prompt = packet["spawn_args"]["message"]
        self.assertNotIn("OLD_LARGE_RESULT_SENTINEL", prompt)
        assignment = json.loads(prompt.split("Assignment:\n", 1)[1])
        self.assertEqual(len(assignment["history_refs"]), 2)
        self.assertEqual(assignment["history_total"], 3)
        self.assertEqual(assignment["issue"], current_issue)
        self.assertEqual(assignment["repair_plan"], "Current exact whitening repair")
        self.assertEqual(set(assignment["history_refs"][0]),
                         {"phase", "packet_id", "receipt", "outcome", "candidate_identity"})
        self.assertEqual(s["tasks"]["A"]["history"], history)
        self.assertEqual(history[0]["result"]["diagnostic_payload"], huge)
        self.assertEqual(rc.summary(s)["status"], "AWAITING_NATIVE_OUTCOME")

    def test_missing_input_alone_and_unknown_runtime_do_not_escalate(self):
        s = self.state([task("A", kind="input")])
        self.result(s, self.launch(s), "blocker", issue=self.issue(**{"class": "input", "substantive": False}))
        self.assertEqual(s["tasks"]["A"]["phase"], "research")
        self.result(s, self.launch(s), "blocker", issue=self.issue(**{"class": "input", "substantive": False}))
        self.assertEqual(s["tasks"]["A"]["state"], "held")
        self.assertEqual(s["ultra_repairs"], {})

    def test_cli_checkpoints_launch_outcome_and_content_addressed_result(self):
        campaign = Path(self.tmp.name) / "campaign.json"
        campaign.write_text(json.dumps({"campaign_id": "cli", "tasks": [task("A")]}))
        state = Path(self.tmp.name) / "state.json"
        import os
        env = {**os.environ, "PYTHONPATH": str(ROUTER_DIR)}
        command = [sys.executable, str(HERE / "research_controller.py"), "--state", str(state),
                   "--policy", str(ROUTER_DIR.parents[1] / "docs/harness/NATIVE_ROUTING_POLICY_V1.json")]
        def run(*args):
            result = subprocess.run(command + list(args), env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        run("init", "--campaign", str(campaign), "--authorization", "Current owner instruction")
        packet = run("next", "--available-profile", "gpt-6-sol/high")
        self.assertFalse(packet["launch_performed"])
        run("ack", "--packet-id", packet["packet_id"], "--agent-id", "actual-native-id")
        receipt = Path(self.tmp.name) / "native-result.txt"
        receipt.write_text("Actual worker receipt fixture, finite reference agreed")
        result_path = Path(self.tmp.name) / "result.json"
        result_path.write_text(json.dumps({"packet_id": packet["packet_id"], "task_id": "A",
            "agent_id": "actual-native-id", "input_identity": "input-v1", "outcome": "success",
            "raw_receipt": str(receipt), "candidate_identity": "sha256:candidate",
            "validation_evidence": ["finite reference agreed"]}))
        run("record", "--result", str(result_path))
        self.assertEqual(run("summary")["states"]["A"], "ready")
        results = list((state.parent / (state.name + ".results")).glob("*.json"))
        self.assertEqual(len(results), 1)
        self.assertEqual(json.loads(results[0].read_text()), json.loads(result_path.read_text()))


if __name__ == "__main__":
    unittest.main()
