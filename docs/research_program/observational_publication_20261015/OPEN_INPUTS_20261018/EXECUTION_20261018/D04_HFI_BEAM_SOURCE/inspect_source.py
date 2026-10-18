"""Bounded, read-only tar/FITS metadata intake; never decode array payloads.

The source assessment is a separate scientific decision. This program reports
coverage, literal metadata, and obstructions, not response-law sufficiency.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import resource
import signal
import sys
import tarfile
import time

from astropy import __version__ as astropy_version
from astropy.io.fits import Header


class IntakeStop(Exception):
    """Coverage cannot be established under the declared limits."""


@dataclass(frozen=True)
class Limits:
    seconds: float = 120
    decompressed: int = 1024**3
    metadata: int = 16 * 1024**2
    members: int = 4096
    item: int = 1024**2


class BoundedReader:
    def __init__(self, stream, limits):
        self.stream, self.limits = stream, limits
        self.started = time.monotonic()
        self.count = 0
        self.retained = 0

    def read(self, size):
        if time.monotonic() - self.started >= self.limits.seconds:
            raise IntakeStop("inspection wall-time limit")
        if size < 0 or self.count + size > self.limits.decompressed:
            raise IntakeStop("decompressed-byte limit (including skipped payloads)")
        result = self.stream.read(size)
        self.count += len(result)
        return result

    def exact(self, size):
        result = self.read(size)
        if len(result) != size:
            raise IntakeStop("truncated decompressed stream")
        return result

    def skip(self, size):
        while size:
            chunk = min(size, 65536)
            self.exact(chunk)
            size -= chunk

    def retain(self, text):
        size = len(text.encode("utf-8"))
        if self.retained + size > self.limits.metadata:
            raise IntakeStop("retained decoded metadata limit")
        self.retained += size
        return text


def padded(size, block):
    return ((size + block - 1) // block) * block


def pax_fields(payload):
    """Parse bounded POSIX length-prefixed key/value records."""
    fields, position = {}, 0
    while position < len(payload):
        space = payload.find(b" ", position)
        if space < 0 or not payload[position:space].isdigit():
            raise IntakeStop("invalid PAX record length")
        length = int(payload[position:space])
        if length <= space - position + 1 or position + length > len(payload):
            raise IntakeStop("invalid PAX record span")
        record = payload[space + 1:position + length]
        if not record.endswith(b"\n") or b"=" not in record:
            raise IntakeStop("invalid PAX record")
        key, value = record[:-1].split(b"=", 1)
        fields[key.decode("utf-8")] = value.decode("utf-8")
        position += length
    return fields


def fits_headers(reader, size, first, headers=None):
    remaining = size
    headers = [] if headers is None else headers
    pending = first
    while remaining:
        if remaining < 2880:
            raise IntakeStop("FITS member has incomplete header/block padding")
        start = size - remaining
        blocks = bytearray()
        ended = False
        while not ended:
            if len(blocks) + 2880 > reader.limits.item:
                raise IntakeStop("per-HDU FITS header limit")
            if len(blocks) + 2880 > remaining:
                raise IntakeStop("FITS header exceeds declared member span")
            block = pending if pending is not None else reader.exact(2880)
            pending = None
            if len(block) != 2880:
                raise IntakeStop("short FITS header block")
            if not blocks and block[:8] not in (b"SIMPLE  ", b"XTENSION"):
                raise IntakeStop("unexpected FITS HDU start")
            blocks.extend(block)
            ended = any(block[i:i + 8] == b"END     " for i in range(0, 2880, 80))
        raw = reader.retain(blocks.decode("ascii"))
        header = Header.fromstring(raw, sep="")
        # Astropy's installed Header.data_size owns BITPIX/NAXIS/PCOUNT/GCOUNT,
        # including binary-table heap and random-group sizing. No HDU data access.
        data_size = int(header.data_size)
        if data_size < 0 or any(int(header.get(f"NAXIS{i}", 0)) < 0
                                for i in range(1, int(header.get("NAXIS", 0)) + 1)):
            raise IntakeStop("invalid FITS dimensions/data span")
        span = len(blocks) + padded(data_size, 2880)
        if span > remaining:
            raise IntakeStop("FITS data span exceeds declared member size")
        headers.append({"hdu_ordinal": len(headers), "member_byte_offset": start,
                        "header_bytes": len(blocks), "data_bytes": data_size,
                        "padded_data_bytes_skipped": padded(data_size, 2880),
                        "cards": [raw[i:i + 80] for i in range(0, len(raw), 80)
                                  if raw[i:i + 80].strip()]})
        reader.skip(padded(data_size, 2880))
        remaining -= span
    return headers


def is_document(name):
    name = name.lower()
    return (name.endswith((".txt", ".md", ".rst", ".tex", ".html", ".htm"))
            or any(token in Path(name).name for token in ("readme", "release", "convention")))


def inspect_stream(stream, limits=Limits()):
    reader = BoundedReader(stream, limits)
    result = {"coverage": "INTAKE_INCOMPLETE", "members": [], "obstruction": None}
    local_pax, global_pax, longname, longlink = {}, {}, None, None
    current = None
    try:
        while True:
            offset = reader.count
            block = reader.exact(512)
            if not any(block):
                if any(reader.exact(512)):
                    raise IntakeStop("tar end marker is not two zero blocks")
                # Check gzip CRC/truncation and reject nonzero concatenated tar data.
                while True:
                    if reader.count == limits.decompressed:
                        raise IntakeStop("decompressed cap before confirmed gzip EOF")
                    tail = reader.read(min(65536, limits.decompressed - reader.count))
                    if not tail:
                        break
                    if any(tail):
                        raise IntakeStop("nonzero content after tar end marker")
                result["coverage"] = "COMPLETE_PERMITTED_METADATA_INSPECTION"
                break
            if len(result["members"]) >= limits.members:
                raise IntakeStop("tar member-count limit; next header reached")
            info = tarfile.TarInfo.frombuf(block, "utf-8", "strict")
            current = {"ordinal": len(result["members"]) + 1,
                       "tar_header_decompressed_offset": offset,
                       "literal_name": reader.retain(info.name),
                       "type": info.type.decode("ascii", "backslashreplace"),
                       "declared_size": info.size, "inspection": "PENDING"}
            result["members"].append(current)
            if info.size < 0:
                raise IntakeStop("negative tar size")
            if info.type in (tarfile.XHDTYPE, tarfile.XGLTYPE,
                              tarfile.GNUTYPE_LONGNAME, tarfile.GNUTYPE_LONGLINK):
                if info.size > limits.item:
                    raise IntakeStop("tar extended-header metadata exceeds item limit")
                payload = reader.exact(info.size)
                current["text"] = reader.retain(payload.decode("utf-8"))
                if info.type in (tarfile.XHDTYPE, tarfile.XGLTYPE):
                    fields = pax_fields(payload)
                    if any("sparse" in key.lower() for key in fields):
                        raise IntakeStop("sparse tar extension unsupported")
                    if info.type == tarfile.XGLTYPE:
                        global_pax.update(fields)
                    else:
                        local_pax.update(fields)
                elif info.type == tarfile.GNUTYPE_LONGNAME:
                    longname = payload.rstrip(b"\0").decode("utf-8")
                else:
                    longlink = payload.rstrip(b"\0").decode("utf-8")
                reader.skip(padded(info.size, 512) - info.size)
                current["inspection"] = "TAR_EXTENSION_METADATA"
                continue
            fields = global_pax | local_pax
            local_pax = {}
            name = fields.get("path", longname or info.name)
            size = int(fields.get("size", info.size))
            if size < 0:
                raise IntakeStop("negative effective tar size")
            current["effective_name"] = reader.retain(name)
            current["effective_size"] = size
            current["literal_link_name"] = reader.retain(info.linkname)
            if fields.get("linkpath", longlink):
                current["effective_link_name"] = reader.retain(fields.get("linkpath", longlink))
            longname, longlink = None, None
            if info.type == tarfile.GNUTYPE_SPARSE:
                raise IntakeStop("sparse tar member unsupported")
            if not info.isreg():
                reader.skip(size)
                current["inspection"] = "NONREGULAR_NOT_FOLLOWED"
            else:
                first = reader.exact(min(size, 2880))
                if first[:8] in (b"SIMPLE  ", b"XTENSION"):
                    current["fits_headers"] = []
                    # Assign incrementally to preserve earlier HDUs on obstruction.
                    fits_headers(reader, size, first, current["fits_headers"])
                    current["inspection"] = "ALL_FITS_HDU_HEADERS"
                elif first.startswith((b"\x1f\x8b", b"PK\x03\x04", b"BZh")):
                    raise IntakeStop("nested compressed member requires separate bounded intake")
                elif is_document(name):
                    if size > limits.item:
                        raise IntakeStop("documentation member exceeds per-item limit")
                    content = first + reader.exact(size - len(first))
                    current["text"] = reader.retain(content.decode("utf-8"))
                    current["inspection"] = "DOCUMENT_TEXT"
                else:
                    reader.skip(size - len(first))
                    current["inspection"] = "NON_FITS_NON_DOCUMENT_PAYLOAD_SKIPPED"
                    if name.lower().endswith((".fits", ".fit", ".fts", ".pdf", ".ps")):
                        raise IntakeStop("named FITS/document content has unsupported structure")
            reader.skip(padded(size, 512) - size)
        if local_pax or longname is not None or longlink is not None:
            raise IntakeStop("orphan tar extension at end of stream")
    except Exception as exc:
        result["coverage"] = "INTAKE_INCOMPLETE"
        result["obstruction"] = {"type": type(exc).__name__, "message": str(exc),
                                 "active_member_ordinal": current["ordinal"] if current else None,
                                 "uninspected": "active member remainder and all later archive contents"}
    result["resources"] = {"decompressed_bytes_including_skip": reader.count,
                           "retained_decoded_metadata_bytes": reader.retained,
                           "physical_tar_headers_indexed": len(result["members"]),
                           "inspection_elapsed_seconds": time.monotonic() - reader.started,
                           "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    return result


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fetch-receipt", required=True, type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    # Existing authoritative receipt is required; no download or receipt adoption.
    receipt = json.loads(args.fetch_receipt.read_text())
    actual_size, actual_sha = args.archive.stat().st_size, sha256(args.archive)
    if (actual_size != 86556876 or receipt.get("bytes") != actual_size
            or receipt.get("sha256") != actual_sha
            or Path(receipt["path"]).resolve() != args.archive.resolve()
            or receipt.get("status") not in ("DOWNLOADED", "REUSED")
            or receipt.get("url") != "https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/HFI_RIMO_BEAMS_R3.01.tar.gz"):
        raise IntakeStop("archive identity/official fetch receipt binding mismatch")
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    process_threads = int(next(line.split()[1] for line in Path("/proc/self/status").read_text().splitlines()
                               if line.startswith("Threads:")))
    if process_threads > 2:
        raise IntakeStop("observed process threads exceed two-thread contract")
    def stop_alarm(signum, frame):
        raise IntakeStop("inspection 120-second wall alarm")
    signal.signal(signal.SIGALRM, stop_alarm)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, 120 - (time.monotonic() - started)))
    with gzip.open(args.archive, "rb") as stream:
        result = inspect_stream(stream, Limits(seconds=max(0.001, 120 - (time.monotonic() - started))))
    signal.setitimer(signal.ITIMER_REAL, 0)
    result.update({"owner": "obsstat", "scope": "source qualification only",
                   "claim_tier": "C0", "transfer_source": "none", "non_claim_bearing": True,
                   "source": {"path": str(args.archive), "bytes": actual_size, "sha256": actual_sha,
                              "fetch_receipt_path": str(args.fetch_receipt), "fetch_receipt": receipt,
                              "upstream_checksum": "UNAVAILABLE"},
                   "execution": {"time_utc": datetime.now(timezone.utc).isoformat(),
                                 "interpreter": sys.executable, "astropy": astropy_version,
                                 "argv": sys.argv, "requested_model": "gpt-6.1-sol/high",
                                 "observed_runtime": "UNKNOWN", "process_threads_observed": process_threads,
                                 "total_elapsed_seconds": time.monotonic() - started,
                                 "memory_address_space_limit_bytes": 512 * 1024**2},
                   "caveats": ["No array/column values inspected; numeric validity unchecked",
                               "Source metadata does not admit original scientific nodes",
                               "Separate independent Astra source assessment required"]})
    with args.output.open("x") as out:
        json.dump(result, out, indent=2, ensure_ascii=True)
        out.write("\n")
    print(json.dumps({"coverage": result["coverage"], "obstruction": result["obstruction"],
                      "resources": result["resources"]}, indent=2))
    return 0 if result["coverage"] == "COMPLETE_PERMITTED_METADATA_INSPECTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
