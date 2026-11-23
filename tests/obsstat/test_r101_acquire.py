"""R101 no-clobber, explicit-selection and per-provider provenance regressions."""
import contextlib
from email.message import Message
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from scripts.r101 import acquire
from scripts.r100.source_intake import compute_digests, download_bounded_product
from scripts.r99.acquisition import validate_product_response


class Response(io.BytesIO):
    def __init__(self, payload, status=200):
        super().__init__(payload)
        self.status = status
        self.read_sizes = []
        self.total_read = 0
        self.headers = {"Content-Length": str(len(payload)), "Content-Type": "application/octet-stream"}

    def read(self, size=-1):
        self.read_sizes.append(size)
        part = super().read(size)
        self.total_read += len(part)
        return part


class AcquisitionTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.dest = Path(self.work.name)
        self.data = b"fixture product"
        self.md5 = hashlib.md5(self.data).hexdigest()
        self.job = {"id": "sdss_randoms_v1_1", "url": "https://example.invalid/fixed.dat",
                    "expected_bytes": len(self.data), "checksum": "md5:" + self.md5}
        self.opener = Mock(side_effect=lambda *args, **kwargs: Response(self.data))

    def get(self, **kwargs):
        job = self.job | kwargs
        return acquire.acquire_one(job, self.dest, len(self.data), fetch=download_bounded_product,
                                   digests=compute_digests, validate_headers=validate_product_response,
                                   opener=self.opener)

    def test_valid_product_reused_without_second_get(self):
        fresh = self.get()
        self.assertEqual(fresh["sha256"], hashlib.sha256(self.data).hexdigest())
        self.assertEqual(fresh["status"], "FETCHED_PROVIDER_MD5_VERIFIED")
        existing = self.get()
        self.assertFalse(existing["downloaded"])
        self.assertEqual(existing["status"], "REUSED_PROVIDER_MD5_VERIFIED")
        self.opener.assert_called_once()

    def test_preserve_differing_existing(self):
        target = self.dest / acquire.FILENAMES[self.job["id"]]
        target.write_bytes(b"wrong same size")
        self.assertEqual(target.stat().st_size, len(self.data))
        with self.assertRaises(FileExistsError):
            self.get()
        self.assertEqual(target.read_bytes(), b"wrong same size")
        self.opener.assert_not_called()

    def test_no_provider_checksum_labels(self):
        r = self.get(checksum=None)
        self.assertEqual(r["status"], "FETCHED_EXACT_LENGTH_LOCAL_DIGEST")
        self.assertFalse(r["provider_checksum_available"])
        r = self.get(checksum=None)
        self.assertEqual(r["status"], "PRESENT_LOCAL_DIGEST_ONLY")
        self.opener.assert_called_once()

    def test_deferred_head_and_checksum_failure(self):
        self.opener.side_effect = lambda *a, **k: Response(b"{}", 202)
        r = self.get(id="lotss_aux_1078")
        self.assertEqual(r["status"], "DEFERRED_HTTP_202")
        self.assertEqual(self.opener.call_args.args[0].get_method(), "HEAD")
        self.opener.assert_called_once()
        self.opener.side_effect = lambda *a, **k: Response(self.data)
        with self.assertRaisesRegex(ValueError, "MD5 mismatch"):
            self.get(checksum="md5:" + "0"*32)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_declared_nine_byte_budget_bounds_read_request(self):
        self.data = b"123456789"
        body = Response(self.data + b"x"*262144)
        body.headers["Content-Length"] = "9"
        self.opener.side_effect = lambda *a, **k: body
        receipt = self.get(expected_bytes=9, checksum="md5:" + hashlib.md5(self.data).hexdigest())
        self.assertEqual(body.read_sizes, [9])
        self.assertEqual(body.total_read, 9)
        self.assertEqual(receipt["bytes"], 9)
        self.assertEqual(Path(receipt["path"]).read_bytes(), self.data)

    def test_long_mismatched_body_and_truncation_do_not_publish(self):
        self.data = b"123456789"
        for payload, msg, reads in [(b"x"*262144, "MD5 mismatch", [9]),
                                    (self.data[:4], "truncated stream", [9, 5])]:
            with self.subTest(length=len(payload)):
                body = Response(payload)
                body.headers["Content-Length"] = "9"
                self.opener.side_effect = lambda *a, **k: body
                with self.assertRaisesRegex(ValueError, msg):
                    self.get(expected_bytes=9, checksum="md5:" + hashlib.md5(self.data).hexdigest())
                self.assertEqual(body.read_sizes, reads)
                self.assertEqual(body.total_read, min(len(payload), 9))
                self.assertEqual(list(self.dest.iterdir()), [])

    def test_ambiguous_or_encoded_framing_is_rejected_before_read(self):
        size = str(len(self.data))
        fields = [[], [("Content-Length", size), ("content-length", "8")],
                  [("Content-Length", size), ("Content-Length", size)],
                  [("Content-Length", size + ", " + size)],
                  [("Content-Length", size), ("Transfer-Encoding", "chunked")],
                  [("Content-Length", size), ("Content-Encoding", "gzip")]]
        for extra in fields:
            with self.subTest(headers=extra):
                body = Response(self.data)
                body.headers = Message()
                body.headers["Content-Type"] = "application/octet-stream"
                for key, value in extra:
                    body.headers[key] = value
                self.opener.side_effect = lambda *a, **k: body
                with self.assertRaises(ValueError):
                    self.get()
                self.assertEqual(body.read_sizes, [])
                self.assertEqual(list(self.dest.iterdir()), [])

    def test_list_and_no_download_plan(self):
        # The checkout's frozen manifest is the canonical source in CI.
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(acquire.main([]), 0)
        self.assertEqual(len(json.loads(out.getvalue())["jobs"]), 6)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            acquire.main(["--ids", "commander_pr3_ffp10_noise_00000", "--max-bytes", "603987840"])
        self.assertEqual(json.loads(out.getvalue())["downloaded_bytes"], 0)
        with self.assertRaisesRegex(ValueError, "budget"):
            acquire.main(["--ids", "commander_pr3_ffp10_noise_00000", "--max-bytes", "1"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            acquire.main(["--execute"])

    def test_filename_guard(self):
        with patch.dict(acquire.FILENAMES, {self.job["id"]: "../escaped"}):
            with self.assertRaisesRegex(ValueError, "basename"):
                self.get()
        self.opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
