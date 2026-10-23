"""Small real-byte acquisition lifecycle fixtures; never touch production state/processes."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import research_controller as rc
from test_research_controller import POLICY, PROFILES, task


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = rc.initialize({"campaign_id": "checkpoint-fixture", "tasks": [
            task("ACQUIRE", kind="input", approved_repair_id=None), task("SMICA")]}, "actual fixture authorization")
        self.packet = rc.next_packet(self.state, POLICY, PROFILES)
        self.assertEqual(self.packet["task_id"], "ACQUIRE")
        rc.acknowledge(self.state, self.packet["packet_id"], "actual-acquisition-agent")
        self.paths = {}
        for name, value in {"source.py": "actual source version", "attempt.json": '{"elapsed":2,"bytes":7}',
                            "raw.txt": "actual source/process raw observation", "complete.bin": "done",
                            "partial.bin": "partial"}.items():
            p = self.root/name
            p.write_text(value)
            self.paths[name] = p
        self.worker, self.host = self.documents()

    def seal(self, path):
        path = Path(path)
        b = path.read_bytes()
        return {"path": str(path.resolve()), "sha256": hashlib.sha256(b).hexdigest(), "size_bytes": len(b)}

    def write(self, name, value):
        path = self.root/name
        path.write_text(json.dumps(value))
        return str(path)

    def documents(self, sequence=1, state=None, task_id="ACQUIRE"):
        state = self.state if state is None else state
        binding = rc.acquisition_binding(state, task_id, sequence)
        source = str(self.paths["source.py"])
        def product(name, identifier):
            return {**self.seal(self.paths[name]), "product_id": identifier,
                    "source_release": "real-release-v1", "source_refs": [source]}
        snapshot = {"sources": [self.seal(source)], "processes": [
            {"pid": 100, "start_identity": "boot:actual-start-ticks-10", "parent_pid": 1,
             "session_id": "actual-session", "command": ["python", source], "cwd": str(self.root),
             "role": "launcher", "state": "exited", "exit_code": 0, "source_refs": [source]}],
            "queued_writers": [], "future_launchers": [], "attempt_receipts": [self.seal(self.paths["attempt.json"])],
            "completed_products": [product("complete.bin", "completed")],
            "partial_products": [{**product("partial.bin", "partial"), "offset": self.paths["partial.bin"].stat().st_size}],
            "accounting": {"attempts": 1, "wall_seconds": 2, "received_bytes": 7}}
        worker = {"binding": binding, "handoff_complete": True, "inventory_complete": True,
                  "snapshot": snapshot, "raw_evidence": [self.seal(self.paths["raw.txt"])]}
        worker_path = self.write(f"worker-{sequence}.json", worker)
        observation = {"binding": binding, "observer": "actual-independent-host", "inventory_complete": True,
                       "processes": snapshot["processes"], "queued_writers": [], "future_launchers": []}
        obs_path = self.write(f"observations-{sequence}.json", observation)
        host = {"binding": binding, "worker_receipt": rc._receipt(worker_path),
                "snapshot_identity": rc.digest(snapshot), "inventory_complete": True,
                "quiescence_observed": True, "observer": "actual-independent-host",
                "process_observation": self.seal(obs_path), "raw_evidence": [self.seal(self.paths["raw.txt"])]}
        return worker_path, self.write(f"host-{sequence}.json", host)

    def rewrite(self, path, edit):
        value = json.loads(Path(path).read_text())
        edit(value)
        Path(path).write_text(json.dumps(value))

    def reject(self, call):
        before = copy.deepcopy(self.state)
        with self.assertRaises((rc.ControllerError, ValueError, KeyError, OSError)):
            call()
        self.assertEqual(self.state, before)

    def checkpoint(self):
        return rc.checkpoint_acquisition(self.state, "ACQUIRE", self.worker, self.host)

    def plan(self, row):
        source = self.root/"cooperative.py"
        source.write_text("reviewed cooperative source")
        b = row["binding"]
        review = {"verdict": "SCOPED_PASS", "reviewer": "independent-source-reviewer",
                  "task_id": b["task_id"], "packet_id": b["packet_id"], "input_identity": b["input_identity"],
                  "source_hashes": {str(source): self.seal(source)["sha256"]}}
        review_path = self.write("source-review.json", review)
        return self.write("resume-plan.json", {"binding": b, "checkpoint_identity": row["checkpoint_identity"],
                          "sources": [self.seal(source)], "review_receipt": self.seal(review_path)})

    def prepare(self):
        row = self.checkpoint()
        plan = self.plan(row)
        return rc.prepare_acquisition_resume(self.state, "ACQUIRE", row["checkpoint_identity"], plan)

    def dispatch(self, reservation):
        doc = {"binding": reservation["binding"], "checkpoint_identity": reservation["checkpoint_identity"],
               "reservation_identity": reservation["reservation_identity"], "agent_id": reservation["agent_id"],
               "native_tool": "collaboration.followup_task", "accepted": True,
               "requested": reservation["route"]["requested"],
               "transport_selected": reservation["route"]["transport_selected"]}
        raw = self.write("native-call.json", doc)
        return self.write("dispatch.json", {**doc, "tool_receipt": self.seal(raw)})

    def test_missing_actual_handoff_and_host_observation_waits(self):
        before = copy.deepcopy(self.state)
        self.assertEqual(rc.next_packet(self.state, POLICY, PROFILES)["status"], "AWAITING_NATIVE_OUTCOME")
        self.assertEqual(self.state, before)
        self.rewrite(self.worker, lambda v:v.update(handoff_complete=False))
        self.reject(self.checkpoint)

    def test_active_dormant_or_queued_future_rejects_atomically(self):
        original = Path(self.worker).read_bytes()
        for field, value in (("state", "running"), ("state", "stopped"), ("start_identity", "")):
            with self.subTest(field=field, value=value):
                Path(self.worker).write_bytes(original)
                self.rewrite(self.worker, lambda v:v["snapshot"]["processes"][0].update({field:value}))
                self.reject(self.checkpoint)
        for key in ("queued_writers", "future_launchers"):
            Path(self.worker).write_bytes(original)
            self.rewrite(self.worker, lambda v:v["snapshot"].update({key:["actual queued writer"]}))
            self.reject(self.checkpoint)

    def test_wrong_task_packet_agent_input_and_sequence_rejected(self):
        original = Path(self.worker).read_bytes()
        for field in ("task_id", "packet_id", "input_identity", "agent_id", "task_spec_identity", "packet_identity"):
            with self.subTest(field=field):
                Path(self.worker).write_bytes(original)
                self.rewrite(self.worker, lambda v:v["binding"].update({field:"wrong"}))
                self.reject(self.checkpoint)
        Path(self.worker).write_bytes(original)
        self.worker, self.host = self.documents(sequence=2)
        self.reject(self.checkpoint)

    def test_missing_or_changed_source_attempt_product_and_raw_evidence_rejected(self):
        for name in self.paths:
            with self.subTest(name=name):
                path = self.paths[name]
                old = path.read_bytes()
                path.write_bytes(old+b"changed")
                self.reject(self.checkpoint)
                path.write_bytes(old)

    def test_host_identity_inventory_and_pid_start_mismatch_rejected(self):
        original = Path(self.host).read_bytes()
        for field,value in (("quiescence_observed",False),("inventory_complete",False),
                            ("observer","actual-acquisition-agent"),("snapshot_identity","wrong")):
            Path(self.host).write_bytes(original)
            self.rewrite(self.host, lambda v:v.update({field:value}))
            self.reject(self.checkpoint)
        Path(self.host).write_bytes(original)
        obs=json.loads(Path(self.host).read_text())["process_observation"]["path"]
        self.rewrite(obs,lambda v:v["processes"][0].update(start_identity="PID reused"))
        self.reject(self.checkpoint)

    def test_partial_offset_mismatch_and_stale_host_receipt_rejected(self):
        self.rewrite(self.worker,lambda v:v["snapshot"]["partial_products"][0].update(offset=6))
        self.reject(self.checkpoint)
        self.worker,self.host=self.documents()
        self.rewrite(self.worker,lambda v:v.update(extra_actual_record="late uncorroborated record"))
        self.reject(self.checkpoint)

    def test_checkpoint_enables_existing_ready_consumer_and_duplicate_is_noop(self):
        old=copy.deepcopy(self.state); fingerprint=rc.adaptive_fingerprint(self.state)
        row=self.checkpoint(); checkpointed=copy.deepcopy(self.state)
        self.assertEqual(self.checkpoint(),row);self.assertEqual(self.state,checkpointed)
        self.assertEqual(rc.adaptive_fingerprint(self.state),fingerprint)
        for key in ("campaign","campaign_identity","packets","turn","events","ultra_repairs","ultra_pending"):
            self.assertEqual(self.state[key],old[key])
        t=copy.deepcopy(self.state["tasks"]["ACQUIRE"]);t["state"]="running"
        self.assertEqual(t,old["tasks"]["ACQUIRE"])
        self.assertEqual(rc.next_packet(self.state,POLICY,PROFILES)["task_id"],"SMICA")

    def test_stale_partial_after_checkpoint_rejects_next_and_prepare(self):
        row=self.checkpoint();plan=self.plan(row)
        self.paths["partial.bin"].write_text("changed")
        self.reject(lambda:rc.next_packet(self.state,POLICY,PROFILES))
        self.reject(lambda:rc.prepare_acquisition_resume(self.state,"ACQUIRE",row["checkpoint_identity"],plan))

    def test_prepare_before_checkpoint_or_while_other_packet_owns_slot_rejected(self):
        self.reject(lambda:rc.prepare_acquisition_resume(self.state,"ACQUIRE","none","missing"))
        row=self.checkpoint();plan=self.plan(row)
        rc.next_packet(self.state,POLICY,PROFILES)
        self.reject(lambda:rc.prepare_acquisition_resume(self.state,"ACQUIRE",row["checkpoint_identity"],plan))

    def test_reservation_unknown_blocks_normal_review_discovery_and_duplicate(self):
        reservation=self.prepare();saved=copy.deepcopy(self.state)
        row=self.state["acquisition_lifecycle"]["ACQUIRE"][-1]
        self.assertEqual(rc.prepare_acquisition_resume(self.state,"ACQUIRE",row["checkpoint_identity"],row["resume"]["plan"]["plan_receipt"]["path"]),reservation)
        for review_only in (False,True):
            self.assertEqual(rc.next_packet(self.state,POLICY,PROFILES,review_only=review_only)["status"],"AWAITING_NATIVE_OUTCOME")
        self.assertEqual(self.state,saved)
        self.reject(lambda:rc.acknowledge(self.state,self.packet["packet_id"],"another-agent"))

    def test_wrong_resume_profile_agent_checkpoint_and_unaccepted_raw_call_rejected(self):
        reservation=self.prepare();dispatch=self.dispatch(reservation);original=Path(dispatch).read_bytes()
        for field,value in (("accepted",False),("agent_id","other"),("checkpoint_identity","old"),
                            ("requested",{"model":"gpt-6-astra","effort":"ultra"})):
            Path(dispatch).write_bytes(original);self.rewrite(dispatch,lambda v:v.update({field:value}))
            self.reject(lambda:rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch))
        Path(dispatch).write_bytes(original)
        self.rewrite(self.root/"native-call.json",lambda v:v.update(accepted=False))
        self.reject(lambda:rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch))

    def test_unreviewed_or_changed_resume_sources_rejected(self):
        row=self.checkpoint();plan=self.plan(row)
        self.rewrite(self.root/"source-review.json",lambda v:v.update(verdict="HOLD"))
        self.reject(lambda:rc.prepare_acquisition_resume(self.state,"ACQUIRE",row["checkpoint_identity"],plan))
        plan=self.plan(row);self.root.joinpath("cooperative.py").write_text("changed")
        self.reject(lambda:rc.prepare_acquisition_resume(self.state,"ACQUIRE",row["checkpoint_identity"],plan))

    def test_same_agent_roundtrip_preserves_science_fingerprint_accounting_original_packet(self):
        old=copy.deepcopy(self.state);fingerprint=rc.adaptive_fingerprint(self.state)
        reservation=self.prepare();dispatch=self.dispatch(reservation)
        rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch)
        resumed=copy.deepcopy(self.state)
        rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch)
        self.assertEqual(self.state,resumed)
        self.assertEqual(rc.adaptive_fingerprint(self.state),fingerprint)
        for key,value in old.items():self.assertEqual(self.state[key],value)
        self.assertEqual(rc.next_packet(self.state,POLICY,PROFILES)["status"],"AWAITING_NATIVE_OUTCOME")
        self.checkpoint() # Duplicate prior checkpoint cannot re-yield running acquisition.
        self.assertEqual(self.state["tasks"]["ACQUIRE"]["state"],"running")
        raw=self.write("actual-final-result.json",{"actual":"final result after resumed acquisition"})
        rc.record(self.state,{"task_id":"ACQUIRE","packet_id":self.packet["packet_id"],
            "input_identity":"input-v1","agent_id":"actual-acquisition-agent","raw_receipt":raw,
            "outcome":"success","candidate_identity":"actual-candidate","validation_evidence":["actual fixture validation"]},POLICY)
        self.assertEqual(self.state["tasks"]["ACQUIRE"]["phase"],"review")

    def test_second_checkpoint_preserves_cumulative_attempts_and_completed_products(self):
        reservation=self.prepare();dispatch=self.dispatch(reservation)
        rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch)
        self.worker,self.host=self.documents(sequence=2)
        # Matching cumulative records are legal; no new attempt is invented by lifecycle.
        row=self.checkpoint();self.assertEqual(row["binding"]["sequence"],2)
        self.assertEqual(self.state["tasks"]["ACQUIRE"]["attempt"],1)

    def test_cumulative_reset_and_lost_completed_or_partial_reject_with_fresh_corroboration(self):
        reservation=self.prepare();dispatch=self.dispatch(reservation)
        rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch)
        for change in (lambda s:s["accounting"].update(attempts=0),
                       lambda s:s.update(completed_products=[]),
                       lambda s:s.update(partial_products=[]),
                       lambda s:s.update(attempt_receipts=[self.seal(self.paths["raw.txt"])])):
            self.worker,self.host=self.documents(sequence=2)
            self.rewrite(self.worker,lambda w:change(w["snapshot"]))
            worker=json.loads(Path(self.worker).read_text());host=json.loads(Path(self.host).read_text())
            host.update(worker_receipt=rc._receipt(self.worker),snapshot_identity=rc.digest(worker["snapshot"]))
            Path(self.host).write_text(json.dumps(host))
            self.reject(self.checkpoint)

    def test_stale_sources_or_receipts_after_reservation_reject_ack_without_releasing_writer(self):
        reservation=self.prepare();dispatch=self.dispatch(reservation)
        self.root.joinpath("cooperative.py").write_text("stale source after reservation")
        self.reject(lambda:rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch))
        self.assertEqual(self.state["tasks"]["ACQUIRE"]["state"],"resume_pending")

    def test_coherent_checkpoint_document_replacement_rejected_by_next_prepare_and_ack(self):
        row=self.checkpoint();plan=self.plan(row)
        self.paths["partial.bin"].write_text("CHANGED")
        self.worker,self.host=self.documents()
        self.reject(lambda:rc.next_packet(self.state,POLICY,PROFILES))
        self.reject(lambda:rc.prepare_acquisition_resume(self.state,"ACQUIRE",row["checkpoint_identity"],plan))

    def test_stale_checkpoint_between_consumer_plan_and_ordinary_ack_rejected(self):
        self.checkpoint();packet=rc.next_packet(self.state,POLICY,PROFILES)
        self.paths["partial.bin"].write_text("changed after consumer plan")
        self.reject(lambda:rc.acknowledge(self.state,packet["packet_id"],"actual-independent-consumer"))

    def test_coherent_plan_review_and_source_replacement_after_reservation_rejected(self):
        reservation=self.prepare();row=self.state["acquisition_lifecycle"]["ACQUIRE"][-1]
        newsource=self.root/"replacement.py";newsource.write_text("reviewed but different source")
        review={"verdict":"SCOPED_PASS","reviewer":"independent-source-reviewer",
                "task_id":row["binding"]["task_id"],"packet_id":row["binding"]["packet_id"],
                "input_identity":row["binding"]["input_identity"],
                "source_hashes":{str(newsource):self.seal(newsource)["sha256"]}}
        reviewpath=self.write("new-review.json",review)
        Path(reservation["plan"]["plan_receipt"]["path"]).write_text(json.dumps({
            "binding":row["binding"],"checkpoint_identity":row["checkpoint_identity"],
            "sources":[self.seal(newsource)],"review_receipt":self.seal(reviewpath)}))
        dispatch=self.dispatch(reservation)
        self.reject(lambda:rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch))

    def test_same_size_and_growing_prefix_overwrites_rejected_but_actual_append_allowed(self):
        reservation=self.prepare();dispatch=self.dispatch(reservation)
        rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch)
        for body in ("CHANGED","CHANGED-longer-than-original"):
            self.paths["partial.bin"].write_text(body)
            self.worker,self.host=self.documents(sequence=2)
            self.reject(self.checkpoint)
        self.paths["partial.bin"].write_text("partial-real-new-validated-bytes")
        self.worker,self.host=self.documents(sequence=2)
        self.assertEqual(self.checkpoint()["binding"]["sequence"],2)

    def test_partial_source_release_change_rejected_even_with_retained_bytes(self):
        reservation=self.prepare();dispatch=self.dispatch(reservation)
        rc.acknowledge_acquisition_resume(self.state,"ACQUIRE",reservation["reservation_identity"],dispatch)
        self.worker,self.host=self.documents(sequence=2)
        self.rewrite(self.worker,lambda w:w["snapshot"]["partial_products"][0].update(source_release="different scientific release"))
        worker=json.loads(Path(self.worker).read_text());host=json.loads(Path(self.host).read_text())
        host.update(worker_receipt=rc._receipt(self.worker),snapshot_identity=rc.digest(worker["snapshot"]))
        Path(self.host).write_text(json.dumps(host));self.reject(self.checkpoint)

    def test_independent_discovery_remains_available_excluding_checkpointed_acquisition(self):
        self.state["tasks"]["SMICA"].update(state="held",hold={"reason":"actual independent method question"})
        rc.enable_adaptive(self.state,"actual independent research authorization")
        self.worker,self.host=self.documents()
        fingerprint=rc.adaptive_fingerprint(self.state);self.checkpoint()
        packet=rc.next_packet(self.state,POLICY,PROFILES)
        self.assertEqual(packet["phase"],"discovery")
        self.assertEqual(packet["eligible_branches"],["SMICA"])
        self.assertEqual(rc.adaptive_fingerprint(self.state),fingerprint)
        self.assertEqual(rc.next_packet(self.state,POLICY,PROFILES),packet)

    def test_no_discovery_allowance_from_lifecycle_without_scientific_delta(self):
        self.state["tasks"]["SMICA"]["state"]="completed"
        rc.enable_adaptive(self.state,"actual fixture authorization")
        self.worker,self.host=self.documents()
        fingerprint=rc.adaptive_fingerprint(self.state);self.checkpoint()
        self.assertNotIn("packet_id",rc.next_packet(self.state,POLICY,PROFILES))
        self.assertEqual(self.state["adaptive"]["packets"],{})
        self.assertEqual(rc.adaptive_fingerprint(self.state),fingerprint)

    def test_copied_live_state_preserves_baseline62_and_selects_actual_smica_after_release(self):
        repo=Path(__file__).resolve().parents[2]
        path=repo/".agent-harness/runtime/r23-continuous/STATE.json"
        baseline=repo/".agent-harness/runtime/r23-continuous/r25/STATE_BEFORE.json"
        if not path.exists() or not baseline.exists():self.skipTest("read-only live fixture unavailable")
        raw=path.read_bytes();live=json.loads(raw);before=copy.deepcopy(live)
        key="R25-PR3-FREQUENCY-ACQUIRE"
        if live["tasks"][key]["state"]!="running":self.skipTest("live acquisition is no longer running")
        self.assertEqual(rc.next_packet(live,POLICY,PROFILES)["status"],"AWAITING_NATIVE_OUTCOME")
        worker,host=self.documents(state=live,task_id=key)
        fingerprint=rc.adaptive_fingerprint(live)
        rc.checkpoint_acquisition(live,key,worker,host)
        self.assertEqual(rc.adaptive_fingerprint(live),fingerprint)
        for field in ("campaign","campaign_identity","packets","ultra_repairs","ultra_pending"):
            self.assertEqual(live[field],before[field])
        baseline=json.loads(baseline.read_text())
        for oldkey in baseline["tasks"]:self.assertEqual(live["tasks"][oldkey],before["tasks"][oldkey])
        packet=rc.next_packet(live,POLICY,PROFILES)
        self.assertEqual(packet["task_id"],"R25-SMICA-SPECTRAL-NULLSPACE")
        self.assertEqual(packet["input_identity"],before["tasks"][packet["task_id"]]["spec"]["input_identity"])
        self.assertEqual(path.read_bytes(),raw)


if __name__=="__main__":
    unittest.main()
