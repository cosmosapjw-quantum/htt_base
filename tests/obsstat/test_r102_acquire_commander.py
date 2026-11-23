"""Unit tests for R102 bounded chunked-FITS Commander noise intake."""
from __future__ import annotations

from email.message import Message
import hashlib
from pathlib import Path
import pytest

from scripts.r98 import acquisition_preflight as r98_acq
from scripts.r102 import acquire_commander_pair as r102_acq


class _FakeResp:
    def __init__(self, status: int, headers: list[tuple[str, str]], body: bytes):
        self.status = status
        msg = Message()
        for k, v in headers:
            msg.add_header(k, v)
        self.headers = msg
        self._body = body
        self._pos = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            part = self._body[self._pos :]
            self._pos = len(self._body)
            return part
        part = self._body[self._pos : self._pos + n]
        self._pos += len(part)
        return part


def _ok_headers(filename: str, *, chunked: bool = True, cl: int | None = None) -> list[tuple[str, str]]:
    h = [
        ("Content-Type", "image/fits"),
        ("Content-Disposition", f'inline; filename="{filename}"'),
    ]
    if chunked:
        h.append(("Transfer-Encoding", "chunked"))
    if cl is not None:
        h.append(("Content-Length", str(cl)))
    return h


def test_chunked_exact_length_succeeds_and_validates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b"SIMPLE  =                    T" + b"\x00" * 994
    expected_len = len(payload)
    monkeypatch.setattr(
        r102_acq,
        "archive_job",
        lambda pid: {"id": pid, "url": f"https://pla.esac.esa.int/{pid}", "bytes": expected_len},
    )

    def _fake_validator(path: Path, job: dict) -> dict:
        raw = path.read_bytes()
        assert len(raw) == job["bytes"]
        return {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "channels": {"INTENSITY": {"pixels": 16, "finite": 16}},
        }

    rec = r102_acq.acquire_commander_noise(
        destination=tmp_path,
        max_bytes=expected_len,
        opener=lambda req, timeout=120: _FakeResp(
            200, _ok_headers(r102_acq.COMMANDER_NOISE_ID, chunked=True), payload
        ),
        payload_validator=_fake_validator,
    )
    target = tmp_path / r102_acq.COMMANDER_NOISE_ID
    assert target.is_file()
    assert rec["downloaded"] is True
    assert rec["bytes"] == expected_len
    assert rec["sha256"] == hashlib.sha256(payload).hexdigest()
    assert rec["status"] == "FETCHED_CHUNKED_FITS_VERIFIED_EXACT_BYTES"
    assert rec["commander_null_qualified"] is False


def test_oversized_and_truncated_chunked_streams_abort_without_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_len = 64
    monkeypatch.setattr(
        r102_acq,
        "archive_job",
        lambda pid: {"id": pid, "url": f"https://pla.esac.esa.int/{pid}", "bytes": expected_len},
    )

    with pytest.raises(ValueError, match="exceeded expected size"):
        r102_acq.acquire_commander_noise(
            destination=tmp_path,
            max_bytes=expected_len,
            opener=lambda req, timeout=120: _FakeResp(
                200, _ok_headers(r102_acq.COMMANDER_NOISE_ID, chunked=True), b"A" * 80
            ),
            payload_validator=lambda p, j: {},
        )
    assert not (tmp_path / r102_acq.COMMANDER_NOISE_ID).exists()

    with pytest.raises(ValueError, match="truncated"):
        r102_acq.acquire_commander_noise(
            destination=tmp_path,
            max_bytes=expected_len,
            opener=lambda req, timeout=120: _FakeResp(
                200, _ok_headers(r102_acq.COMMANDER_NOISE_ID, chunked=True), b"A" * 32
            ),
            payload_validator=lambda p, j: {},
        )
    assert not (tmp_path / r102_acq.COMMANDER_NOISE_ID).exists()


def test_header_guards_and_existing_no_clobber(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    expected_len = 32
    monkeypatch.setattr(
        r102_acq,
        "archive_job",
        lambda pid: {"id": pid, "url": f"https://pla.esac.esa.int/{pid}", "bytes": expected_len},
    )

    # Reject HTML error page
    with pytest.raises(ValueError, match="Content-Type"):
        r102_acq.acquire_commander_noise(
            destination=tmp_path,
            max_bytes=expected_len,
            opener=lambda req, timeout=120: _FakeResp(
                200, [("Content-Type", "text/html"), ("Transfer-Encoding", "chunked")], b"<html>"
            ),
            payload_validator=lambda p, j: {},
        )

    # Reject wrong filename in Content-Disposition
    with pytest.raises(ValueError, match="Content-Disposition"):
        r102_acq.acquire_commander_noise(
            destination=tmp_path,
            max_bytes=expected_len,
            opener=lambda req, timeout=120: _FakeResp(
                200, _ok_headers("other_file.fits", chunked=True), b"X" * expected_len
            ),
            payload_validator=lambda p, j: {},
        )

    # Preserve pre-existing file with conflicting size without replacement
    target = tmp_path / r102_acq.COMMANDER_NOISE_ID
    wrong_sized = b"WRONG_SIZE"
    target.write_bytes(wrong_sized)
    with pytest.raises(FileExistsError, match="preserved conflicting product"):
        r102_acq.acquire_commander_noise(
            destination=tmp_path,
            max_bytes=expected_len,
            opener=lambda req, timeout=120: (_ for _ in ()).throw(AssertionError("should not download")),
            payload_validator=lambda p, j: {},
        )
    assert target.read_bytes() == wrong_sized

    # Reuse existing exact-sized validated file without network transfer
    original = b"ORIGINAL_BYTES_" + b"0" * (expected_len - 15)
    target.write_bytes(original)

    def _fake_val(path: Path, job: dict) -> dict:
        return {"bytes": expected_len, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    reused = r102_acq.acquire_commander_noise(
        destination=tmp_path,
        max_bytes=expected_len,
        opener=lambda req, timeout=120: (_ for _ in ()).throw(AssertionError("should not download")),
        payload_validator=_fake_val,
    )
    assert reused["downloaded"] is False
    assert reused["transferred_bytes"] == 0
    assert reused["sha256"] == hashlib.sha256(original).hexdigest()

    # Preserve differing concurrent arrival without replacement
    target.unlink()
    incoming = b"INCOMING_BYTES_" + b"1" * (expected_len - 15)

    def _racy_opener(req, timeout=120):
        target.write_bytes(original)
        return _FakeResp(200, _ok_headers(r102_acq.COMMANDER_NOISE_ID, chunked=True), incoming)

    with pytest.raises(FileExistsError, match="concurrent differing product preserved"):
        r102_acq.acquire_commander_noise(
            destination=tmp_path,
            max_bytes=expected_len,
            opener=_racy_opener,
            payload_validator=_fake_val,
        )
    assert target.read_bytes() == original
