"""Compact exact-profile controls. Execute once only after controller ACK."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

import smica_implicit_reader as implicit
import project_smica
import run_smica


class ExactFormatControls(unittest.TestCase):
    def setUp(self):
        from astropy.io import fits
        self.fits = fits
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def fixture(self, nside=16, explicit=False):
        fits = self.fits
        count = 12 * nside * nside
        index = np.arange(count, dtype=np.float64)
        q = (np.sin(index * .17) + np.cos(index * .019)).astype("f4") * 1e-5
        u = (np.sin(index * .131) - np.cos(index * .031)).astype("f4") * 1e-5
        data = [np.zeros(count, dtype="f4"), q, u,
                np.ones(count, dtype="f4"), np.ones(count, dtype="f4"),
                np.zeros(count, dtype="f4"), -q, -u,
                np.ones(count, dtype="f4"), np.ones(count, dtype="f4")]
        names = [c["TTYPE"] for c in implicit._sealed_json(implicit.CONTRACT, implicit.CONTRACT_SHA)
                 ["production_header_profile"]["columns"]]
        units = ["K_CMB", "K_CMB", "K_CMB", "", "", "K_CMB", "K_CMB", "K_CMB", "", ""]
        cols = [fits.Column(name=name, format="1E", unit=unit, array=values)
                for name, unit, values in zip(names, units, data)]
        table = fits.BinTableHDU.from_columns(cols)
        table.header.update(NSIDE=nside, ORDERING="NESTED", COORDSYS="GALACTIC",
                            POLCCONV="COSMO", PIXTYPE="HEALPIX", METHOD="SMICA",
                            **{"AST-COMP": "CMB", "BAD_DATA": -1.6375e30})
        for number in (4, 5, 9, 10):
            table.header[f"TUNIT{number}"] = ""
        if explicit:
            table.header.update(FIRSTPIX=0, LASTPIX=count - 1,
                                INDXSCHM="IMPLICIT", OBJECT="FULLSKY")
        path = Path(self.temp.name) / f"map_{len(list(Path(self.temp.name).glob('*.fits')))}.fits"
        fits.HDUList([fits.PrimaryHDU(), table]).writeto(path)
        product = {"path": str(path), "size_bytes": path.stat().st_size,
                   "hdu_index": 1, "nside": nside, "q_field": "Q_STOKES",
                   "u_field": "U_STOKES", "tform": "1E", "unit_raw": "K_CMB",
                   "pol_keyword": "POLCCONV", "bad_data_keyword": "BAD_DATA",
                   "rehash_on_execution": False}
        return product, q, u

    def profile(self, product):
        profile = implicit._sealed_json(implicit.CONTRACT, implicit.CONTRACT_SHA)["production_header_profile"].copy()
        fd = os.open(product["path"], os.O_RDONLY)
        try:
            primary, n, _ = implicit._header_at(fd, 0)
            _, map_n, _ = implicit._header_at(fd, n + implicit._data_bytes(primary))
        finally:
            os.close(fd)
        profile.update(NSIDE=product["nside"], NAXIS2=12 * product["nside"] ** 2,
                       data_offset_bytes=n + map_n)
        st = Path(product["path"]).stat()
        return profile, implicit._file_identity(st)

    def reader(self, product, support, chunk_rows=397, reverse=False, parent_nside=8):
        profile, identity = self.profile(product)
        yield from implicit._selected_chunks(product, support, chunk_rows,
                                             reverse, parent_nside,
                                             fixture_profile=profile,
                                             fixture_identity=identity)

    def test_implicit_rows_equal_explicit_reference_and_24_stf(self):
        from streamed_reader import selected_chunks as strict
        from streamed_operator import project_pass, bound_math, REPO
        implicit_product, q, u = self.fixture()
        explicit_product, _, _ = self.fixture(explicit=True)
        support = np.zeros(12 * 8 * 8, dtype=bool)
        support[::3] = True
        a = list(self.reader(implicit_product, support))
        b = list(strict(explicit_product, support, chunk_rows=397, parent_nside=8))
        self.assertEqual(len(a), len(b))
        for got, ref in zip(a, b):
            for g, r in zip(got, ref):
                self.assertTrue(np.array_equal(g, r))
        adapter = lambda *args, **kwargs: self.reader(*args, **kwargs)
        c, tensors, _ = project_smica.project_with_reader(
            implicit_product, support, parent_nside=8, reader=adapter)
        ref = project_pass(explicit_product, support, chunk_rows=131072,
                           parent_nside=8, reader=strict)["canonical24"]
        tolerance = 1e-12 + 1e-9 * np.abs(ref)
        self.assertTrue(np.all(np.abs(c - ref) <= tolerance))
        for got, expected in zip(tensors, bound_math().decode_stf(ref, REPO)):
            self.assertTrue(np.all(np.abs(got - expected) <= 1e-12 + 1e-9 * np.abs(expected)))
        self.assertTrue(np.any(q < 0) and np.any(u < 0))

    def test_product_identity_and_negative_header_profiles(self):
        product, _, _ = self.fixture()
        support = np.ones(12 * 8 * 8, dtype=bool)
        with self.assertRaisesRegex(RuntimeError, "UNQUALIFIED_PRODUCT"):
            next(implicit.selected_chunks(product, support, parent_nside=8))
        cases = [
            {"NAXIS2": 12 * 16 * 16 - 1}, {"NSIDE": 64},
            {"INDXSCHM": "EXPLICIT"}, {"OBJECT": "PARTIAL"},
            {"FIRSTPIX": 1}, {"LASTPIX": 12 * 16 * 16 - 2},
            {"ORDERING": "RING"}, {"COORDSYS": "ECLIPTIC"},
            {"POLCCONV": "IAU"}, {"TSCAL2": 2.0},
            {"TZERO2": 1.0}, {"TDIM2": "(1)"},
            {"THEAP": 0}, {"ZTABLE": True}, {"ZIMAGE": True},
            {"TTYPE2": "Q_STOKES_INP"}, {"TTYPE3": "PIXEL"},
        ]
        for changes in cases:
            case, _, _ = self.fixture()
            with self.fits.open(case["path"], mode="update") as hdus:
                for key, value in changes.items():
                    hdus[1].header[key] = value
            case["size_bytes"] = Path(case["path"]).stat().st_size
            with self.subTest(changes=changes):
                with self.assertRaises(RuntimeError):
                    list(self.reader(case, support))
        wrong, _, _ = self.fixture()
        profile, identity = self.profile(wrong)
        with self.assertRaisesRegex(RuntimeError, "QUALIFIED_SOURCE_STAT_DRIFT"):
            list(implicit._selected_chunks(wrong, support, 397, False, 8,
                                           fixture_profile=profile,
                                           fixture_identity=(0,) + identity[1:]))
        with mock.patch.object(implicit, "CONTRACT_SHA", "0" * 64):
            with self.assertRaisesRegex(RuntimeError, "IMMUTABLE_SMALL_SOURCE_DRIFT"):
                list(implicit.selected_chunks(product, support, parent_nside=8))

    def test_short_read_selected_bad_nonfinite_and_near_unseen(self):
        product, _, _ = self.fixture()
        support = np.ones(12 * 8 * 8, dtype=bool)
        profile, identity = self.profile(product)
        real_pread = os.pread
        with mock.patch.object(implicit.os, "pread", side_effect=lambda fd, n, at: b"short" if n > 2880 else real_pread(fd, n, at)):
            with self.assertRaisesRegex(RuntimeError, "SHORT_FITS_ROW_READ_NO_RETRY"):
                list(implicit._selected_chunks(product, support, 397, False, 8,
                                               fixture_profile=profile, fixture_identity=identity))
        for value, status in ((np.float32(-1.6375e30), "INVALID"),
                              (np.float32(np.nan), "INVALID"),
                              (np.nextafter(np.float32(-1.6375e30), np.float32(0)), "NEAR_UNSEEN")):
            case, _, _ = self.fixture()
            with self.fits.open(case["path"], mode="update") as hdus:
                hdus[1].data["Q_STOKES"][0] = value
            case["size_bytes"] = Path(case["path"]).stat().st_size
            with self.subTest(status=status):
                with self.assertRaisesRegex(implicit.OperatorDomainHold, status):
                    list(self.reader(case, support))

    def test_started_failure_and_source_drift_preserve_account_base(self):
        base = {key: 100.0 for key in run_smica.ALL}
        base["SMICA"] = 297.8989226810652
        ledger = {"baseline_charged_seconds": base.copy(),
                  "delta_charged_seconds": {key: 0.0 for key in run_smica.ALL},
                  "cumulative_charged_seconds": base.copy(), "charges": []}
        marker = {"status": "FAILED", "elapsed_seconds": 2.5,
                  "native_bound_seconds": 300.0, "attempt_id": "mock-first-failure"}
        with mock.patch.object(run_smica, "persist"):
            run_smica.settle_native(ledger, marker)
            with self.assertRaisesRegex(RuntimeError, "DUPLICATE_ATTEMPT_DEBIT"):
                run_smica.settle_native(ledger, marker)
        self.assertEqual(ledger["baseline_charged_seconds"], base)
        self.assertEqual(ledger["cumulative_charged_seconds"]["SMICA"], base["SMICA"] + 2.5)
        self.assertEqual(len(ledger["charges"]), 1)
        source = Path(self.temp.name) / "sealed.json"
        source.write_text('{"before":true}')
        prior = project_smica.sha(source)
        source.write_text('{"after":true}')
        with self.assertRaisesRegex(RuntimeError, "SOURCE_OR_INPUT_SEAL_DRIFT"):
            project_smica.sealed(source, prior)
        self.assertEqual(ledger["baseline_charged_seconds"], base)
        self.assertEqual(len(ledger["charges"]), 1)

    def test_existing_started_receipt_blocks_second_launch(self):
        private_run = Path(self.temp.name) / "run"
        private_run.mkdir()
        (private_run / "RAW_RECEIPT.json").write_text('{"stage":"NATIVE_STARTED"}')
        with (mock.patch.object(run_smica, "RUN", private_run),
              mock.patch.object(run_smica.child_source, "validate_go") as go):
            with self.assertRaisesRegex(RuntimeError, "ONE_USE_RAW_RECEIPT_EXISTS_NO_RELAUNCH"):
                run_smica.run(SimpleNamespace())
            go.assert_not_called()


if __name__ == "__main__":
    unittest.main()
