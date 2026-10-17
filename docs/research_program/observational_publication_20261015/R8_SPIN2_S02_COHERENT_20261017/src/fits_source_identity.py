"""Typed Planck PR3 PMASK source audit. Only an immutable qualified source may admit science.

No observational source hash is rewritten or replaced with the observed hash.
Works without astropy/healpy for exact PMASK BINTABLE representation, with bounded RAM.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np

BLOCK = 2880
HEX64 = re.compile(r"[0-9a-fA-F]{64}\Z")


class SourceIdentityError(ValueError):
    """A locked source was not proven byte-identical; contains structured receipt."""

    def __init__(self, receipt):
        self.receipt = receipt
        failures = {k: v["byte_status"] for k, v in receipt.items()
                    if v["byte_status"] != "BYTE_IDENTICAL"}
        super().__init__("native FITS source not admitted: " + json.dumps(failures, sort_keys=True))


def digest_file(path, chunk=4 << 20):
    sha = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(chunk), b""):
            sha.update(part)
    return sha.hexdigest()


def audit_source_files(root, names, expected_sha, expected_size=None):
    """Collect all independent byte observations before raising; never auto-accept drift."""
    base = Path(root) / "planck/PR3/masks"
    result = {}
    for label, filename in names.items():
        f = base / filename
        wanted = expected_sha.get(label)
        entry = {"path": str(f), "expected_sha256": wanted,
                 "expected_digest_wellformed": isinstance(wanted, str) and bool(HEX64.fullmatch(wanted))}
        if not f.is_file() or f.is_symlink():
            entry["byte_status"] = "INPUT_MISSING_OR_SYMLINK"
            result[label] = entry
            continue
        entry["source_size_bytes"] = f.stat().st_size
        entry["observed_sha256"] = digest_file(f)
        if expected_size is not None and entry["source_size_bytes"] != expected_size:
            entry["byte_status"] = "SOURCE_SIZE_MISMATCH"
        elif not entry["expected_digest_wellformed"]:
            entry["byte_status"] = "EXPECTED_DIGEST_MALFORMED"
        elif entry["observed_sha256"].lower() != wanted.lower():
            entry["byte_status"] = "BYTE_SHA_MISMATCH"
        else:
            entry["byte_status"] = "BYTE_IDENTICAL"
        result[label] = entry
    return result


def _value(card):
    if card[8:10] != "= ":
        return None
    raw = card[10:]
    if raw.lstrip().startswith("'"):
        # FITS standard strings may double a quote; this mask contract needs no such value.
        return raw.split("'", 2)[1].strip()
    v = raw.split("/", 1)[0].strip()
    if v in ("T", "F"):
        return v == "T"
    try:
        return int(v)
    except ValueError:
        try:
            return float(v.replace("D", "E"))
        except ValueError:
            return v


def _header(f):
    cards = []
    while True:
        block = f.read(BLOCK)
        if len(block) != BLOCK:
            raise ValueError("TRUNCATED_FITS_HEADER")
        try:
            s = block.decode("ascii")
        except UnicodeError as e:
            raise ValueError("NONASCII_FITS_HEADER") from e
        for i in range(0, BLOCK, 80):
            card = s[i:i+80]
            if card[:8].strip() == "END":
                return {c[:8].strip(): _value(c) for c in cards
                        if c[8:10] == "= "}
            cards.append(card)
        if len(cards) > 100_000:
            raise ValueError("UNBOUNDED_FITS_HEADER")


def _data_size(h):
    if h.get("XTENSION") == "BINTABLE":
        return (int(h["NAXIS1"]) * int(h["NAXIS2"]) + int(h.get("PCOUNT", 0))) * int(h.get("GCOUNT", 1))
    n = int(h.get("NAXIS", 0))
    if n == 0:
        return 0
    dims = 1
    for i in range(1, n+1):
        dims *= int(h[f"NAXIS{i}"])
    return (abs(int(h["BITPIX"])) // 8) * dims


def inspect_planck_pmask(path, nside=2048):
    """Strict narrow Planck PMASK layout: one implicit, Galactic, NESTED float32 map."""
    path = Path(path)
    with path.open("rb") as f:
        primary = _header(f)
        if primary.get("SIMPLE") is not True or primary.get("NAXIS") != 0:
            raise ValueError("PRIMARY_HDU_CONTRACT_MISMATCH")
        ext = _header(f)
        offset = f.tell()
        count = 12 * nside*nside
        required = {
            "XTENSION": "BINTABLE", "BITPIX": 8, "NAXIS": 2, "NAXIS1": 4,
            "NAXIS2": count, "PCOUNT": 0, "GCOUNT": 1, "TFIELDS": 1,
            "PIXTYPE": "HEALPIX", "COORDSYS": "GALACTIC", "ORDERING": "NESTED",
            "NSIDE": nside, "TTYPE1": "PMASK", "TFORM1": "1E",
        }
        bad = {k: {"required": v, "observed": ext.get(k)}
               for k, v in required.items() if ext.get(k) != v}
        if bad:
            raise ValueError("PMASK_LAYOUT_CONTRACT_MISMATCH " + json.dumps(bad, sort_keys=True))
        if ext.get("TUNIT1", "") not in ("", None):
            raise ValueError("PMASK_UNIT_CONTRACT_MISMATCH")
        nbytes = _data_size(ext)
        if offset + ((nbytes + BLOCK-1)//BLOCK)*BLOCK != path.stat().st_size:
            raise ValueError("FITS_LENGTH_HDU_MISMATCH")
    return {"data_offset": offset, "data_bytes": nbytes,
            "count": count, "layout": "PMASK_GALACTIC_NESTED_FLOAT32/1",
            "bad_data": ext.get("BAD_DATA"), "nside": nside}


def semantic_compare_pmask(left, right, nside=2048, chunk_pixels=1 << 18):
    """Exact *decoded PMASK pixel-value* equivalence within a fixed frame/ordering.

    Requires two independently identified files. A different ordering, pixel convention,
    column format or frame is NOT declared unequal without a verified transform.
    Metadata-only reserialization may be equivalent in this declared narrow scope.
    """
    a, b = inspect_planck_pmask(left, nside), inspect_planck_pmask(right, nside)
    out = {"left": str(left), "right": str(right),
           "semantic_scope": "one-field Galactic NESTED PMASK pixel values (not beams/observed Q,U)",
           "structural_status": "SAME_QUALIFIED_LAYOUT", "first_different_pixel": None}
    if a["bad_data"] != b["bad_data"]:
        out["semantic_status"] = "SEMANTIC_CONTRACT_MISMATCH"
        out["reason"] = "BAD_DATA conventions differ"
        return out
    ma = np.memmap(left, dtype=">f4", offset=a["data_offset"], shape=(a["count"],), mode="r")
    mb = np.memmap(right, dtype=">f4", offset=b["data_offset"], shape=(b["count"],), mode="r")
    for start in range(0, a["count"], chunk_pixels):
        aa, bb = np.asarray(ma[start:start+chunk_pixels]), np.asarray(mb[start:start+chunk_pixels])
        if not np.isfinite(aa).all() or not np.isfinite(bb).all() or np.any(aa < 0) or np.any(aa > 1) or np.any(bb < 0) or np.any(bb > 1):
            out["semantic_status"] = "PMASK_VALUES_INVALID"
            out["first_invalid_window"] = start
            return out
        same = (aa == bb)
        if not same.all():
            out["semantic_status"] = "SEMANTIC_DIFFERENT"
            out["first_different_pixel"] = start + int(np.flatnonzero(~same)[0])
            return out
    out["semantic_status"] = "SEMANTIC_EQUIVALENT_PMASK"
    return out


def classify_byte_semantic(byte_status, semantic_status):
    """Byte admission and scientifically justified semantic witness are orthogonal."""
    if byte_status == "BYTE_IDENTICAL":
        return "ORIGINAL_BYTES_ADMITTED"
    if semantic_status == "SEMANTIC_EQUIVALENT_PMASK":
        return "ALTERNATE_BYTES_PMASK_EQUIVALENT__NEW_PROVENANCE_REQUIRED"
    if semantic_status in ("SEMANTIC_DIFFERENT", "PMASK_VALUES_INVALID", "SEMANTIC_CONTRACT_MISMATCH"):
        return "OBSERVATION_OR_CONTRACT_DIFFERENT__BLOCK"
    return "NOT_ADMITTED__SEMANTICS_UNRESOLVED"