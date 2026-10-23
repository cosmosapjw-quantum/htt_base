"""Offline transport fixtures only. No source GET and no mock science."""
import hashlib
import http.client
from contextlib import nullcontext
import io
import json
from pathlib import Path
import signal
import socket
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import chunked_suffix as c
import resume_acquisition as old


class Response(io.BytesIO):
    def __init__(self, body=b"", status=206, headers=None, url=c.URL):
        super().__init__(body)
        self.status, self.headers, self.url = status, headers or {}, url


def mixed_framing_response(body, status, url, extra_headers=""):
    wire = (f"HTTP/1.1 {status} Fixture\r\nContent-Length: {len(body)}\r\n"
            f"Transfer-Encoding: chunked\r\n{extra_headers}\r\n").encode()
    wire += f"{len(body):x}\r\n".encode()+body+b"\r\n6\r\nhidden\r\n0\r\n\r\n"
    fake_socket = Mock()
    fake_socket.makefile.return_value = io.BytesIO(wire)
    response = http.client.HTTPResponse(fake_socket)
    response.begin()
    response.url = url
    response.read = Mock(wraps=response.read)
    return response


class Offline(unittest.TestCase):
    def setUp(self):
        self.network = patch.object(socket.socket, "connect", side_effect=AssertionError("REAL NETWORK FORBIDDEN"))
        self.network.start()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.network.stop)
        self.root = Path(self.temp.name)

    def fixture(self):
        path = self.root / "part"
        path.write_bytes(b"a"*16)
        return path

    def test_frozen_chunk_math_and_caps(self):
        plans = [c.chunks(i, c.SIZES[i]) for i in (0, 1)]
        self.assertEqual([len(p) for p in plans], [7, 9])
        self.assertEqual(sum(v["body"] for p in plans for v in p), 3893648816)
        self.assertEqual(sum(v["novel"] for p in plans for v in p), 3892600240)
        for index, plan in enumerate(plans):
            retained = c.SIZES[index]
            for v in plan:
                self.assertEqual(v["start"], c.RANGES[index][0]+retained-65536)
                self.assertEqual(v["end"]-v["start"]+1, v["body"])
                self.assertLessEqual(v["body"], 256*1024**2)
                retained += v["novel"]
            self.assertEqual(retained, 4294967296)
        with self.assertRaises(ValueError):
            c.chunks(2, c.SIZES[2])

    def test_strict_headers_status_before_body(self):
        good = {"Content-Range": f"bytes 2-10/{c.TOTAL}", "Content-Length": "9"}
        c.validate_response(206, good, 2, 10)
        cases = [(200, good), (302, good), (206, {}),
                 (206, dict(good, **{"Content-Range": "bytes 2-10/123"})),
                 (206, dict(good, **{"Content-Length": "8"})),
                 (206, dict(good, **{"Content-Encoding": "gzip"}))]
        for status, headers in cases:
            response = Response(b"must not read", status, headers)
            with self.subTest(status=status, headers=headers), self.assertRaises(ValueError):
                c.validate_response(response.status, response.headers, 2, 10)
            self.assertEqual(response.tell(), 0)

    def test_no_redirect_direct_helper_and_host_guard(self):
        handler = old.NoRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "moved", {}, "https://example.com"))
        with self.assertRaises(ValueError):
            old.open_direct(old.urllib.request.Request("http://zenodo.org/unsafe"))
        with self.assertRaises(ValueError):
            old.open_direct(old.urllib.request.Request("https://elsewhere.invalid/a"))

    def test_overlap_checked_before_append(self):
        path = self.fixture()
        chunk = {"retained": 16, "novel": 4, "body": 12}
        for body in (b"b"*8+b"next", b"a"*7):
            with patch.object(c, "OVERLAP", 8), path.open("r+b", buffering=0) as stream:
                with self.assertRaises((ValueError, EOFError)):
                    c.append_chunk(stream, Response(body), chunk, lambda n: None)
            self.assertEqual(path.read_bytes(), b"a"*16)

    def test_short_body_preserves_successful_prefix(self):
        path = self.fixture()
        counts = []
        with patch.object(c, "OVERLAP", 8), path.open("r+b", buffering=0) as stream:
            with self.assertRaisesRegex(EOFError, "SHORT_RESPONSE_BODY"):
                c.append_chunk(stream, Response(b"a"*8+b"ne"), {"retained": 16, "novel": 4, "body": 12}, counts.append)
        self.assertEqual(path.read_bytes(), b"a"*16+b"ne")
        self.assertEqual(sum(counts), 10)

    def test_full_chunk_and_body_accounting(self):
        path = self.fixture()
        counts = []
        with patch.object(c, "OVERLAP", 8), path.open("r+b", buffering=0) as stream:
            self.assertEqual(c.append_chunk(stream, Response(b"a"*8+b"next"),
                                            {"retained": 16, "novel": 4, "body": 12}, counts.append), 4)
        self.assertEqual(path.read_bytes(), b"a"*16+b"next")
        self.assertEqual(sum(counts), 12)

    def test_real_alarm_covers_slow_body_and_preserves_prefix(self):
        class Slow(Response):
            def read(self, n=-1):
                time.sleep(0.2)
                return super().read(n)
        path = self.fixture()
        with patch.object(c, "OVERLAP", 8), path.open("r+b", buffering=0) as stream:
            with self.assertRaises(TimeoutError), c.deadline(0.03):
                c.append_chunk(stream, Slow(b"a"*8+b"next"),
                               {"retained": 16, "novel": 4, "body": 12}, lambda n: None)
        self.assertEqual(path.read_bytes(), b"a"*16)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0], 0)

    def test_signals_preserve_prefix(self):
        class Cancel(Response):
            def read(self, n=-1):
                if self.tell() >= 10:
                    c.interrupted(signal.SIGTERM, None)
                return super().read(min(n, 2))
        path = self.fixture()
        with patch.object(c, "OVERLAP", 8), path.open("r+b", buffering=0) as stream:
            with self.assertRaisesRegex(InterruptedError, "CANCELLED_PRESERVED"):
                c.append_chunk(stream, Cancel(b"a"*8+b"next"),
                               {"retained": 16, "novel": 4, "body": 12}, lambda n: None)
        self.assertEqual(path.read_bytes(), b"a"*16+b"ne")

    def test_account_consumption_duplicate_count_body_caps(self):
        start = {"event": "REQUEST_STARTED", "request_id": "p0c0", "body_bound": c.MAX_BODY}
        c.account(self.root, start)
        with self.assertRaises(ValueError):
            c.account(self.root, start)
        for number in range(1, 16):
            c.account(self.root, dict(start, request_id=str(number), body_bound=1))
        with self.assertRaises(ValueError):
            c.account(self.root, dict(start, request_id="17", body_bound=1))
        c.account(self.root, {"event": "BODY_READ", "bytes": c.BODY_CAP})
        with self.assertRaises(ValueError):
            c.account(self.root, {"event": "BODY_READ", "bytes": 1})
        c.account(self.root, {"event": "METADATA_STARTED"})
        with self.assertRaises(ValueError):
            c.account(self.root, {"event": "METADATA_STARTED"})

    def test_request_reservation_cap_before_network(self):
        with patch.object(c, "BODY_CAP", 10), patch.object(c, "open_direct") as network:
            c.account(self.root, {"event": "REQUEST_STARTED", "request_id": "a", "body_bound": 10})
            with self.assertRaises(ValueError):
                c.account(self.root, {"event": "REQUEST_STARTED", "request_id": "b", "body_bound": 1})
            network.assert_not_called()

    def test_metadata_api_literal_version_and_one_request(self):
        value = {"id": 6824749, "metadata": {"version": "1.1.0"},
                 "files": [{"key": "mocks.tar.gz", "size": c.TOTAL, "checksum": "md5:"+c.MD5}]}
        body = json.dumps(value).encode()
        response = Response(body, 200, {"Content-Length": str(len(body))}, c.API)
        with patch.object(c, "open_direct", return_value=response) as network:
            c.metadata(self.root, time.monotonic()+2)
            self.assertEqual(network.call_count, 1)
            self.assertEqual(network.call_args.args[0].full_url, c.API)
            with self.assertRaises(ValueError):
                c.metadata(self.root, time.monotonic()+2)
            self.assertEqual(network.call_count, 1)
        value["metadata"]["version"] = "v1.1.0"
        with self.assertRaises(ValueError):
            c.validate_metadata(value)

    def test_metadata_oversize_rejected_without_read(self):
        response = Response(b"x", 200, {"Content-Length": str(c.METADATA_CAP+1)}, c.API)
        with patch.object(c, "open_direct", return_value=response):
            with self.assertRaisesRegex(ValueError, "before body"):
                c.metadata(self.root, time.monotonic()+2)
        record = json.loads(c.evidence(self.root, "metadata.failure.json").read_text())
        self.assertEqual(record["body_bytes"], 0)

    def test_complete_part2_is_reused_without_get(self):
        body = b"completed source"
        sha = hashlib.sha256(body).hexdigest()
        a, b = c.RANGES[2]
        receipt = {"status": "VALIDATED", "url": c.URL, "start": a, "end": b,
                   "archive_total": c.TOTAL, "sha256": sha}
        (self.root / f"range.{a}-{b}.json").write_text(json.dumps(receipt))
        expected = {"bytes": len(body), "sha256": sha}
        with patch.object(c, "PART2_SHA", sha), patch.object(c, "RANGES", (*c.RANGES[:2], (a, a+len(body)-1))):
            (self.root / f"range.{a}-{a+len(body)-1}.json").write_text(json.dumps(dict(receipt, end=a+len(body)-1)))
            with patch.object(c, "open_direct") as network:
                c.reuse_complete(self.root, expected, io.BytesIO(body))
                network.assert_not_called()
                with self.assertRaises(ValueError):
                    c.reuse_complete(self.root, expected, io.BytesIO(b"x"*len(body)))

    def test_no_second_phase_and_durable_create_only(self):
        marker = c.evidence(self.root, "started.json")
        c.durable_json(marker, {"status": "FAILED_PRESERVED"})
        with self.assertRaisesRegex(ValueError, "already consumed"):
            c.launch_guards(self.root, self.root / "missing", self.root / "missing", "missing", [])
        with self.assertRaises(FileExistsError):
            c.durable_json(marker, {})

    def test_parent_stops_sibling_and_escalates_only_if_needed(self):
        finished = Mock()
        finished.poll.return_value = 1
        sibling = Mock()
        sibling.poll.return_value = None
        c.stop_children([finished, sibling])
        finished.terminate.assert_not_called()
        sibling.terminate.assert_called_once()
        sibling.wait.assert_called_once_with(timeout=5)

    def test_worker_early_200_failure_has_zero_body_and_no_append(self):
        path = self.fixture()
        preseal = self.root / "snapshot"
        preseal.write_text(json.dumps({"ranges": [{"bytes": 16, "sha256": hashlib.sha256(b"a"*16).hexdigest()}]}))
        response = Response(b"must not read", 200, {})
        chunk = {"retained": 16, "start": 8, "end": 19, "novel": 4, "body": 12}
        with path.open("r+b", buffering=0) as stream, patch.object(c, "chunks", return_value=[chunk]), patch.object(c, "open_direct", return_value=response):
            with self.assertRaisesRegex(ValueError, "HTTP 206"):
                c.worker(self.root, preseal, 0, stream.fileno(), time.monotonic()+2)
        self.assertEqual(path.read_bytes(), b"a"*16)
        failure = json.loads(c.evidence(self.root, "part0.chunk00.failure.json").read_text())
        self.assertEqual(failure["body_bytes"], 0)

    def test_worker_two_sequential_overlap_chunks_and_completion(self):
        path = self.fixture()
        preseal = self.root / "snapshot"
        preseal.write_text(json.dumps({"ranges": [{"bytes": 16, "sha256": hashlib.sha256(b"a"*16).hexdigest()}]}))
        plans = [{"retained": 16, "start": 8, "end": 19, "novel": 4, "body": 12},
                 {"retained": 20, "start": 12, "end": 23, "novel": 4, "body": 12}]
        responses = [Response(b"a"*8+b"next", headers={"Content-Length": "12", "Content-Range": f"bytes 8-19/{c.TOTAL}"}),
                     Response(b"a"*4+b"nextLAST", headers={"Content-Length": "12", "Content-Range": f"bytes 12-23/{c.TOTAL}"})]
        with path.open("r+b", buffering=0) as stream, patch.object(c, "OVERLAP", 8), patch.object(c, "RANGES", ((0, 23), *c.RANGES[1:])), patch.object(c, "chunks", return_value=plans), patch.object(c, "open_direct", side_effect=responses) as network:
            c.worker(self.root, preseal, 0, stream.fileno(), time.monotonic()+2)
            self.assertEqual(network.call_count, 2)
        self.assertEqual(path.read_bytes(), b"a"*16+b"nextLAST")
        receipt = json.loads((self.root / "range.0-23.json").read_text())
        self.assertEqual(receipt["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(c.usage(self.root)["new_bulk_body_bytes_read"], 24)
        self.assertEqual(c.usage(self.root)["cumulative_observed_root_bulk_attempts"], 5)

    def test_controller_metadata_failure_never_starts_bulk(self):
        preseal, approval = self.root / "preseal", self.root / "approval"
        preseal.write_text("{}")
        approval.write_text("approved fixture")
        with patch.object(c, "locked_sources", return_value=nullcontext([])), patch.object(c, "launch_guards", return_value={"source_sha256": {}}), patch.object(c, "metadata", side_effect=EOFError("short metadata fixture")), patch.object(c.subprocess, "Popen") as process:
            with self.assertRaises(EOFError):
                c.launch(self.root, preseal, approval, c.digest(approval))
            process.assert_not_called()
        receipt = json.loads(c.evidence(self.root, "execution.json").read_text())
        self.assertEqual(receipt["status"], "FAILED_PRESERVED")
        self.assertEqual(receipt["usage"]["new_bulk_attempts"], 0)

    def test_controller_worker_failure_stops_sibling_and_no_assembly(self):
        preseal, approval = self.root / "preseal", self.root / "approval"
        preseal.write_text("{}")
        approval.write_text("approved fixture")
        streams = [Mock(), Mock()]
        for stream in streams:
            stream.fileno.return_value = 17
        failed, sibling = Mock(pid=111), Mock(pid=222)
        failed.poll.return_value = 1
        sibling.poll.return_value = None
        with patch.object(c, "locked_sources", return_value=nullcontext(streams)), patch.object(c, "launch_guards", return_value={"source_sha256": {}}), patch.object(c, "metadata"), patch.object(c.subprocess, "Popen", side_effect=[failed, sibling]), patch.object(c, "acquire") as assembly:
            with self.assertRaisesRegex(RuntimeError, "sibling cancelled"):
                c.launch(self.root, preseal, approval, c.digest(approval))
            sibling.terminate.assert_called_once()
            assembly.assert_not_called()
        receipt = json.loads(c.evidence(self.root, "execution.json").read_text())
        self.assertEqual(receipt["status"], "FAILED_PRESERVED")

    def test_mixed_cl_transfer_encoding_metadata_fails_before_body(self):
        value = {"id": 6824749, "metadata": {"version": "1.1.0"},
                 "files": [{"key": "mocks.tar.gz", "size": c.TOTAL, "checksum": "md5:"+c.MD5}]}
        response = mixed_framing_response(json.dumps(value).encode(), 200, c.API)
        self.assertTrue(response.chunked)
        preseal, approval = self.root / "preseal", self.root / "approval"
        preseal.write_text("{}")
        approval.write_text("approved fixture")
        with patch.object(c, "open_direct", return_value=response), patch.object(c, "locked_sources", return_value=nullcontext([])), patch.object(c, "launch_guards", return_value={"source_sha256": {}}), patch.object(c.subprocess, "Popen") as bulk:
            with self.assertRaisesRegex(ValueError, "Transfer-Encoding"):
                c.launch(self.root, preseal, approval, c.digest(approval))
            bulk.assert_not_called()
        response.read.assert_not_called()
        phase = json.loads(c.evidence(self.root, "execution.json").read_text())
        self.assertEqual(phase["status"], "FAILED_PRESERVED")
        self.assertEqual(phase["usage"]["new_bulk_attempts"], 0)
        failure = json.loads(c.evidence(self.root, "metadata.failure.json").read_text())
        self.assertEqual(failure["body_bytes"], 0)
        self.assertEqual(failure["headers"]["Transfer-Encoding"], "chunked")
        self.assertFalse(c.evidence(self.root, "metadata.complete.json").exists())

    def test_mixed_cl_transfer_encoding_bulk_fails_before_append(self):
        path = self.fixture()
        preseal = self.root / "snapshot"
        preseal.write_text(json.dumps({"ranges": [{"bytes": 16, "sha256": hashlib.sha256(b"a"*16).hexdigest()}]}))
        response = mixed_framing_response(b"a"*8+b"next", 206, c.URL,
                                         f"Content-Range: bytes 8-19/{c.TOTAL}\r\n")
        self.assertTrue(response.chunked)
        chunk = {"retained": 16, "start": 8, "end": 19, "novel": 4, "body": 12}
        with path.open("r+b", buffering=0) as stream, patch.object(c, "OVERLAP", 8), patch.object(c, "RANGES", ((0, 19), *c.RANGES[1:])), patch.object(c, "chunks", return_value=[chunk]), patch.object(c, "open_direct", return_value=response):
            with self.assertRaisesRegex(ValueError, "Transfer-Encoding"):
                c.worker(self.root, preseal, 0, stream.fileno(), time.monotonic()+2)
        response.read.assert_not_called()
        self.assertEqual(path.read_bytes(), b"a"*16)
        failure = json.loads(c.evidence(self.root, "part0.chunk00.failure.json").read_text())
        self.assertEqual(failure["body_bytes"], 0)
        self.assertEqual(failure["headers"]["Transfer-Encoding"], "chunked")
        self.assertEqual(failure["status"], "FAILED_PRESERVED")
        self.assertFalse((self.root / "range.0-19.json").exists())

    def test_every_present_transfer_encoding_is_rejected(self):
        c.reject_transfer_encoding({})
        for encoding in ("", "identity", "chunked", "gzip"):
            with self.subTest(encoding=encoding), self.assertRaises(ValueError):
                c.reject_transfer_encoding({"Transfer-Encoding": encoding})


if __name__ == "__main__":
    unittest.main()
