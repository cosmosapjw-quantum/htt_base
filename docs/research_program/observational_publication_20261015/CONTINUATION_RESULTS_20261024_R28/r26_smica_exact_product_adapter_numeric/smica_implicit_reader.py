"""Exact PR3 SMICA full-map implicit-row adapter for the sealed spin-2 operator.

The row=p interpretation is qualified for one file identity and one header
profile. It is not a generic HEALPix missing-card fallback.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np


CONTRACT = Path("/mnt/extdrive/workdir/htt_open_data/r26_seven_frequency_consumption_framing/SMICA_contract/CONTRACT.json")
CONTRACT_SHA = "38bcd5ec436826c85b9507cf30cd0ae51c2899bcee8644a6db383c7f7fe28ff0"
QUALIFICATION = Path("/mnt/extdrive/workdir/htt_open_data/r26_full7_blind_source_contract/SMICA_PRODUCT_QUALIFICATION.json")
QUALIFICATION_SHA = "12641693664c5188733d5093e0b9c61b3776736a3e311f24dd12148bec3c8c3f"
SOURCE_KNOWLEDGE = Path("/mnt/extdrive/workdir/htt_open_data/r26_seven_frequency_consumption_framing/SMICA_contract/SOURCE_KNOWLEDGE.json")
SOURCE_KNOWLEDGE_SHA = "2d0dcfe98ab58a62fdca85f5c8efe85e65128223f6c9914bdfa845c1eb121f30"
MAX_ROWS = 131072
ROW_WIDTH = 40
NEAR_UNSEEN = -1.6375e30
NEAR_UNSEEN_RADIUS = 1e-7 * 1.6375e30


class OperatorDomainHold(RuntimeError):
    """A selected source sample is outside the unchanged operator domain."""


def _sealed_json(path: Path, digest: str):
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != digest:
        raise RuntimeError("IMMUTABLE_SMALL_SOURCE_DRIFT " + str(path))
    return json.loads(body)


def _file_identity(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)


def _parse_card(card: bytes):
    try:
        line = card.decode("ascii")
    except UnicodeDecodeError as exc:
        raise RuntimeError("NON_ASCII_FITS_HEADER") from exc
    key = line[:8].strip()
    if line[8:10] != "= ":
        return key, None
    raw = line[10:].lstrip()
    if raw.startswith("'"):
        value = []
        pos = 1
        while pos < len(raw):
            if raw[pos] == "'":
                if pos + 1 < len(raw) and raw[pos + 1] == "'":
                    value.append("'")
                    pos += 2
                    continue
                return key, "".join(value).rstrip()
            value.append(raw[pos])
            pos += 1
        raise RuntimeError("UNTERMINATED_FITS_STRING")
    token = raw.split("/", 1)[0].strip()
    if token in ("T", "F"):
        return key, token == "T"
    try:
        return key, int(token)
    except ValueError:
        try:
            return key, float(token.replace("D", "E"))
        except ValueError as exc:
            raise RuntimeError("UNSUPPORTED_FITS_CARD_VALUE " + key) from exc


def _header_at(fd: int, offset: int):
    cards = {}
    blocks = []
    while len(blocks) < 64:
        block = os.pread(fd, 2880, offset + 2880 * len(blocks))
        if len(block) != 2880:
            raise RuntimeError("SHORT_FITS_HEADER_READ_NO_RETRY")
        blocks.append(block)
        for pos in range(0, 2880, 80):
            key, value = _parse_card(block[pos:pos + 80])
            if key == "END":
                raw = b"".join(blocks)
                return cards, len(raw), hashlib.sha256(raw).hexdigest()
            if value is not None:
                if key in cards:
                    raise RuntimeError("DUPLICATE_FITS_CARD " + key)
                cards[key] = value
    raise RuntimeError("FITS_HEADER_LIMIT")


def _data_bytes(cards):
    axes = int(cards.get("NAXIS", -1))
    if axes < 0 or axes > 4:
        raise RuntimeError("FITS_AXIS_LAYOUT")
    size = 0 if axes == 0 else abs(int(cards["BITPIX"])) // 8
    for axis in range(1, axes + 1):
        size *= int(cards[f"NAXIS{axis}"])
    return (size + int(cards.get("PCOUNT", 0))) * int(cards.get("GCOUNT", 1))


def _profile_header(fd: int, size: int, profile, expected_header_sha=None):
    primary, primary_len, _ = _header_at(fd, 0)
    map_at = primary_len + ((_data_bytes(primary) + 2879) // 2880) * 2880
    cards, map_len, header_sha = _header_at(fd, map_at)
    data_offset = map_at + map_len
    if expected_header_sha is not None and header_sha != expected_header_sha:
        raise RuntimeError("EXACT_MAP_HEADER_SHA_DRIFT")
    if data_offset != profile["data_offset_bytes"]:
        raise RuntimeError("EXACT_MAP_DATA_OFFSET_DRIFT")
    for key, expected in profile.items():
        if key in ("columns", "data_offset_bytes", "expected_body_identity",
                   "missing_required_by_exact_profile", "unsupported_cards"):
            continue
        if cards.get(key) != expected:
            raise RuntimeError("EXACT_MAP_PROFILE_DRIFT " + key)
    for key in profile["missing_required_by_exact_profile"]:
        if key in cards:
            raise RuntimeError("EXACT_IMPLICIT_CARD_NOW_PRESENT " + key)
    for key in ("THEAP", "ZIMAGE", "ZTABLE"):
        if key in cards:
            raise RuntimeError("UNSUPPORTED_FITS_HEAP_OR_COMPRESSION " + key)
    for number, column in enumerate(profile["columns"], 1):
        for kind, expected in column.items():
            key = f"{kind}{number}"
            observed = cards.get(key, "ABSENT")
            if observed != expected:
                raise RuntimeError("EXACT_COLUMN_PROFILE_DRIFT " + key)
    if any(key.startswith(("TSCAL", "TZERO", "TDIM")) for key in cards):
        raise RuntimeError("UNSUPPORTED_FITS_COLUMN_SCALING_OR_DIMENSION")
    if any(cards.get(f"TTYPE{i}", "").upper() in ("PIXEL", "PIX", "IPIX")
           for i in range(1, int(cards["TFIELDS"]) + 1)):
        raise RuntimeError("EXPLICIT_PIXEL_COLUMN")
    if cards["NAXIS2"] != 12 * cards["NSIDE"] ** 2:
        raise RuntimeError("FULL_SKY_ROW_COUNT")
    if data_offset + _data_bytes(cards) > size:
        raise RuntimeError("FITS_DATA_TRUNCATED")
    if cards["NAXIS1"] != ROW_WIDTH or cards["NAXIS1"] > 64:
        raise RuntimeError("ROW_WIDTH_BOUND")
    if "BAD_DATA" not in cards:
        raise RuntimeError("MISSING_BAD_DATA")
    return cards, data_offset, header_sha


def _production_binding(product):
    contract = _sealed_json(CONTRACT, CONTRACT_SHA)
    knowledge = _sealed_json(SOURCE_KNOWLEDGE, SOURCE_KNOWLEDGE_SHA)
    qualified = _sealed_json(QUALIFICATION, QUALIFICATION_SHA)
    if product != contract["production_source"]:
        raise RuntimeError("UNQUALIFIED_PRODUCT_OR_SELECTION")
    if contract["production_header_profile"]["expected_body_identity"] != product["sha256"]:
        raise RuntimeError("EXACT_PROFILE_BODY_IDENTITY_DRIFT")
    if (qualified.get("decision") != "QUALIFIED_FOR_FULL7_NATIVE"
            or qualified.get("qualification_id") != product["qualified_source_identity"]
            or qualified.get("product", {}).get("sha256") != product["sha256"]
            or knowledge.get("status") != "CONDITIONALLY_JUSTIFIED_EXACT_PRODUCT_COMPATIBILITY"
            or knowledge["source_identity"]["product"] != product
            or contract["source_profile_id"] != "PR3-SMICA-R3.00-FULL-60952C-IMPLICIT-ROW-V1"):
        raise RuntimeError("EXACT_PRODUCT_QUALIFICATION_DRIFT")
    st = qualified["verified_file_stat"]
    identity = (st["device"], st["inode"], st["size_bytes"], st["mtime_ns"])
    return contract["production_header_profile"], identity, knowledge["source_identity"]["map_header_sha256"]


@contextlib.contextmanager
def _open_rows(product, *, fixture_profile=None, fixture_identity=None):
    if fixture_profile is None:
        profile, identity, expected_header_sha = _production_binding(product)
    else:
        if fixture_identity is None:
            raise RuntimeError("FIXTURE_IDENTITY_REQUIRED")
        profile, identity, expected_header_sha = fixture_profile, fixture_identity, None
    if product.get("rehash_on_execution"):
        raise RuntimeError("UNPLANNED_FULL_NATIVE_REHASH")
    path = Path(product["path"])
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(fd)
        if _file_identity(before) != identity or before.st_size != product["size_bytes"]:
            raise RuntimeError("QUALIFIED_SOURCE_STAT_DRIFT")
        cards, offset, header_sha = _profile_header(fd, before.st_size, profile, expected_header_sha)
        bad = np.float32(cards["BAD_DATA"])
        if not np.isfinite(bad):
            raise RuntimeError("INVALID_DECLARED_SENTINEL")
        yield fd, offset, bad, header_sha
    finally:
        prior = sys.exc_info()[1]
        try:
            changed = _file_identity(os.fstat(fd)) != identity
        finally:
            os.close(fd)
        if changed:
            if prior is None:
                raise RuntimeError("SOURCE_STAT_CHANGED_DURING_READ")
            prior.add_note("SOURCE_STAT_CHANGED_DURING_READ")


def _selected_chunks(product, support_nest, chunk_rows, reverse, parent_nside,
                     *, fixture_profile=None, fixture_identity=None):
    nside = int(product["nside"])
    if (not isinstance(chunk_rows, int) or chunk_rows < 1 or chunk_rows > MAX_ROWS
            or nside < parent_nside or nside % parent_nside):
        raise RuntimeError("CHUNK_OR_PARENT_NSIDE")
    support = np.asarray(support_nest, dtype=bool)
    if support.shape != (12 * parent_nside * parent_nside,):
        raise RuntimeError("SAVED_SUPPORT_SHAPE")
    children = (nside // parent_nside) ** 2
    total = 12 * nside * nside
    starts = range(0, total, chunk_rows)
    if reverse:
        starts = reversed(starts)
    with _open_rows(product, fixture_profile=fixture_profile,
                    fixture_identity=fixture_identity) as (fd, offset, bad, _):
        for lo in starts:
            count = min(chunk_rows, total - lo)
            raw = os.pread(fd, count * ROW_WIDTH, offset + lo * ROW_WIDTH)
            if len(raw) != count * ROW_WIDTH:
                raise RuntimeError("SHORT_FITS_ROW_READ_NO_RETRY")
            nested = np.arange(lo, lo + count, dtype=np.int64)
            selected = support[nested // children]
            if not np.any(selected):
                continue
            q_view = np.ndarray((count,), dtype=">f4", buffer=raw,
                                offset=4, strides=(ROW_WIDTH,))
            u_view = np.ndarray((count,), dtype=">f4", buffer=raw,
                                offset=8, strides=(ROW_WIDTH,))
            q_native, u_native = q_view[selected], u_view[selected]
            if (not np.isfinite(q_native).all() or not np.isfinite(u_native).all()
                    or np.any(q_native == bad) or np.any(u_native == bad)):
                raise OperatorDomainHold("S7_SELECTED_INVALID_NATIVE_CHILD")
            q, u = q_native.astype(np.float64), u_native.astype(np.float64)
            if (np.any(np.abs(q - NEAR_UNSEEN) < NEAR_UNSEEN_RADIUS)
                    or np.any(np.abs(u - NEAR_UNSEEN) < NEAR_UNSEEN_RADIUS)):
                raise OperatorDomainHold("HOLD_NEAR_UNSEEN_OPERATOR_DOMAIN")
            yield nested[selected], q, u


def selected_chunks(product, support_nest, chunk_rows=MAX_ROWS, reverse=False,
                    parent_nside=64):
    """Stream only the qualified production source on an unchanged support."""
    yield from _selected_chunks(product, support_nest, chunk_rows, reverse, parent_nside)
