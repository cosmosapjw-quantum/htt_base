"""Finite driver fixtures only; run via --tests after parent authorization.

No released source rows, source archive or original D07 campaign is read.
"""
import io
import json
from pathlib import Path
import tempfile
import tarfile
import unittest

import numpy as np

from run_source_analysis import (CONTRACT_SHA256, REQUIRED, extract_selected, first_mock_controls, fit_mock,
                                ledger_state, read_mock, sha256, validate_approval)


class SourceDriverFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mapping = dict(zip(REQUIRED, (0, 1, 2, 4, 6, 32, 33, 34)))
        self.approval = {"status": "APPROVED_FOR_STAGE2", "approval_reference": "FINITE_FIXTURE_ONLY",
                         "column_count": 36, "header_lines": 1, "delimiter": "whitespace",
                         "field_indices": self.mapping}

    def source(self, rows):
        path = self.root / "finite_rows.txt"
        path.write_text("# finite fixture\n" + "\n".join(" ".join(row) for row in rows) + "\n")
        return path

    def row(self, z="0.06", cen="0", sd="0.03", measured="0.01"):
        row = ["0"] * 36
        for key, value in {"ID": "000000019", "RA": "40", "Dec": "-20", "z_obs": z,
                           "cen_flag": cen, "logdist_true": ".005", "logdist": measured,
                           "logdist_err": sd}.items():
            row[self.mapping[key]] = value
        return row

    def test_exact_redshift_endpoints_only(self):
        rows, total = read_mock(self.source([self.row(z=z) for z in (".00999", ".01", ".1", ".10001")]), self.approval)
        self.assertEqual(total, 4)
        np.testing.assert_array_equal(rows["z_obs"], [.01, .1])

    def test_invalid_rows_rejected_even_outside_z_cut(self):
        for changes in ({"sd": "0"}, {"sd": "-1"}, {"sd": "nan"}, {"cen": ".5"},
                        {"cen": "2"}, {"measured": "inf"}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    read_mock(self.source([self.row(z=".2", **changes), self.row()]), self.approval)

    def test_no_blank_or_wrong_length_row_deletion(self):
        for bad in ([], self.row()[:-1]):
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                read_mock(self.source([bad, self.row()]), self.approval)

    def test_approved_column_mapping_is_used(self):
        row = self.row()
        row[1], row[2] = row[2], row[1]
        changed = dict(self.approval, field_indices=dict(self.mapping, RA=2, Dec=1))
        rows, _ = read_mock(self.source([row]), changed)
        np.testing.assert_array_equal(rows["RA"], [40])
        np.testing.assert_array_equal(rows["Dec"], [-20])

    def test_no_approval_or_binding_drift(self):
        selected, header = self.root / "selected.json", self.root / "header.json"
        selected.write_text("{}")
        header.write_text("{}")
        good = dict(self.approval, contract_sha256=CONTRACT_SHA256,
                    selected_members_sha256=sha256(selected), actual_header_sha256=sha256(header),
                    archive_sha256="a" * 64)
        validate_approval(good, selected, header, {"sha256": "a" * 64})
        for key, value in (("status", "PENDING"), ("actual_header_sha256", "b" * 64),
                           ("approval_reference", ""), ("column_count", 35)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_approval(dict(good, **{key: value}), selected, header, {"sha256": "a" * 64})

    def test_shared_budget_incomplete_and_invalid_units_fail_closed(self):
        start = {"event": "START", "run_id": "fixture"}
        end = {"event": "END", "run_id": "fixture", "elapsed_s": 1.25}
        _, used = ledger_state(io.StringIO(json.dumps(start) + "\n" + json.dumps(end)))
        self.assertEqual(used, 1.25)
        for rows in ([start], [end], [start, dict(end, elapsed_s=-1)], [start, end, end]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                ledger_state(io.StringIO("\n".join(json.dumps(row) for row in rows)))

    def test_first_mock_control_path_with_finite_fixture(self):
        rng = np.random.default_rng(20261018)
        rows = {"RA": rng.uniform(0, 360, 300), "Dec": np.rad2deg(np.arcsin(rng.uniform(-1, 1, 300))),
                "z_obs": rng.uniform(.01, .1, 300), "logdist_true": rng.normal(0, .01, 300),
                "logdist": rng.normal(0, .03, 300), "logdist_err": rng.uniform(.02, .06, 300)}
        controls = first_mock_controls(rows, fit_mock(rows))
        self.assertEqual(controls["atol_mag"], 1e-10)
        self.assertEqual(controls["rtol"], 1e-8)

    def finite_archive(self, bad=None):
        selected = self.root / "selected"
        selected.mkdir()
        entries = [{"name": f"nested/R19{box:03d}.0_err_corr", "size": 2, "box": box, "observer": 0}
                   for box in range(64)]
        first = selected / "R19000.0_err_corr"
        first.write_bytes(b"0\n")
        archive = self.root / "mocks.tar.gz"
        with tarfile.open(archive, "w:gz") as stream:
            if bad is not None:
                info = tarfile.TarInfo(bad)
                if bad == "link":
                    info.type = tarfile.SYMTYPE
                    info.linkname = "elsewhere"
                stream.addfile(info)
            for entry in entries:
                info = tarfile.TarInfo(entry["name"])
                info.size = entry["size"]
                stream.addfile(info, io.BytesIO(b"0\n"))
        return {"members": entries}, {"member": entries[0], "member_path": str(first),
                                      "member_sha256": sha256(first)}, archive.stat()

    def test_extract_reuses_qualified_first_and_preserves_rerun_gate(self):
        selection, header, stat = self.finite_archive()
        paths = extract_selected(self.root, selection, header, stat)
        self.assertEqual(len(paths), 64)
        self.assertEqual(paths[selection["members"][0]["name"]]["path"], header["member_path"])
        self.assertEqual(len(list((self.root / "analysis_selected").glob("*_err_corr"))), 63)
        with self.assertRaisesRegex(ValueError, "prior extraction"):
            extract_selected(self.root, selection, header, stat)

    def test_traversal_and_symlink_archive_entries_fail_before_extraction(self):
        # Separate fixture roots preserve the first failure of each attack.
        for bad in ("../escape", "/absolute", "link"):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as directory:
                previous, self.root = self.root, Path(directory)
                try:
                    selection, header, stat = self.finite_archive(bad)
                    with self.assertRaises(ValueError):
                        extract_selected(self.root, selection, header, stat)
                    self.assertTrue((self.root / "analysis_selected" / "FIRST_FAILURE.txt").exists())
                finally:
                    self.root = previous

    def test_extract_cap_is_cumulative_and_checked_before_opening_archive(self):
        entries = [{"name": f"R19{box:03d}.0_err_corr", "size": 2 * 1024**3 // 64 + 1}
                   for box in range(64)]
        with self.assertRaisesRegex(ValueError, "frozen limits"):
            extract_selected(self.root, {"members": entries}, {}, None)


if __name__ == "__main__":
    unittest.main()
