"""Contract: consolidated open-items ledger (REV-R180).

The ledger is the single dev-tier ranking of every unfinished research item
and every external-audit item answered only by registration. Contracts:

1. builder --check is byte-stable (regeneration == disk);
2. every ticket yaml on disk is represented (open or closed section);
3. ranking is a contiguous 1..N ordering with executability drawn from the
   declared vocabulary, 'now' items strictly before 'decision_only' before
   'blocked';
4. the ledger is dev-tier and never rendered into any report: the v9 report
   builder must not reference it.
"""
from pathlib import Path
import json
import subprocess
import sys
import unittest

REPO = Path(__file__).resolve().parents[2]
LEDGER_JSON = REPO / "docs/generated/open_items_ledger.json"
LEDGER_MD = REPO / "docs/research_program/OPEN_ITEMS_LEDGER.md"
TICKET_DIR = REPO / "docs/research_program/egs3/tickets"
ORDER = {"now": 0, "decision_only": 1, "blocked": 2}


class OpenItemsLedgerContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(LEDGER_JSON.read_text())

    def test_builder_check_byte_stable(self):
        run = subprocess.run(
            [sys.executable, "scripts/build_open_items_ledger.py", "--check"],
            cwd=REPO, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_every_ticket_represented(self):
        cited = {row["ticket"]
                 for row in (self.payload["open_items"]
                             + self.payload["closed_or_held_tickets"])
                 if row.get("ticket")}
        on_disk = {p.name for p in TICKET_DIR.glob("*.yaml")}
        self.assertEqual(on_disk - cited, set())
        self.assertEqual(cited - on_disk, set())

    def test_ranking_contiguous_and_ordered_by_executability(self):
        rows = self.payload["open_items"]
        self.assertEqual([r["rank"] for r in rows],
                         list(range(1, len(rows) + 1)))
        vocab = set(self.payload["executability_vocabulary"])
        keys = [r["executability"] for r in rows]
        self.assertTrue(set(keys) <= vocab)
        self.assertEqual(keys, sorted(keys, key=ORDER.__getitem__))

    def test_dev_tier_and_not_rendered_in_report(self):
        self.assertTrue(self.payload["not_a_report_artifact"])
        self.assertEqual(self.payload["tier"], "DEV")
        builder = (REPO / "scripts/build_external_audit_report_v9.py")
        self.assertNotIn("open_items_ledger", builder.read_text())
        self.assertIn("never rendered into any report",
                      LEDGER_MD.read_text())
