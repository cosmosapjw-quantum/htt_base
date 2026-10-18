"""Acceptance-state regressions; run directly without optional repo dependencies."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pubdag", ROOT / "scripts/htt_publication_dag.py")
dag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dag)


class DecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((ROOT / "docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json").read_text())

    def candidate(self):
        doc = copy.deepcopy(self.base)
        byid = {n["id"]: n for n in doc["nodes"]}
        def finish(key):
            n = byid[key]
            for d in n["depends_on"]:
                finish(d)
            n.update(state="completed_scoped", external_missing=[], existing_evidence=["manufactured-test-evidence"])
        finish("S06")
        byid["S06"]["publication_decision"] = {
            "outcome": "HOLD", "submitted": False, "evidence": ["manufactured-readiness-decision.json"]}
        return doc, byid

    def test_historical_snapshot_remains_fourteen(self):
        # The immutable intake packet, not the advancing canonical DAG, is the
        # historical fourteen-node snapshot. Preserve that exact assertion.
        snapshot=json.loads((ROOT / "docs/research_program/observational_publication_20261015/CONTINUATION_20261018/EXECUTION_GOALS.json").read_text())
        self.assertEqual(len(snapshot["nodes"]), 42)
        self.assertEqual(sum(n["basis_state"]=="completed_scoped" for n in snapshot["nodes"]), 14)
        self.assertEqual({n["id"] for n in snapshot["nodes"]}, {n["id"] for n in self.base["nodes"]})

    def test_evidenced_hold_decision_can_finish_without_submission(self):
        doc, byid = self.candidate()
        dag.validate(doc)
        self.assertEqual(byid["S06"]["publication_decision"]["outcome"], "HOLD")

    def test_ready_review_does_not_change_paper_submission_status(self):
        doc, byid = self.candidate()
        byid["S06"]["publication_decision"]["outcome"] = "READY_FOR_OWNER_REVIEW"
        dag.validate(doc)
        self.assertTrue(all(p["publication_status"] == "NOT_READY_TO_SUBMIT" for p in doc["papers"]))

    def test_missing_or_submitted_decision_rejected(self):
        for change in (None, {"outcome":"READY_FOR_OWNER_REVIEW", "submitted":True,"evidence":["x"]},
                       {"outcome":"HOLD", "submitted":False,"evidence":[]}):
            doc, byid = self.candidate()
            byid["S06"]["publication_decision"] = change
            with self.assertRaises(dag.PublicationDAGError):
                dag.validate(doc)

    def test_unfinished_prerequisite_cannot_be_bypassed(self):
        doc, byid = self.candidate()
        byid["S02"]["state"] = "pending"
        with self.assertRaisesRegex(dag.PublicationDAGError, "unfinished prerequisite"):
            dag.validate(doc)


if __name__ == "__main__":
    unittest.main()
