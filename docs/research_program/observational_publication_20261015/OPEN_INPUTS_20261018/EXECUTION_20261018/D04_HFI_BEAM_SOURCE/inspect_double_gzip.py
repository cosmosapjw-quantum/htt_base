"""Approved two-layer format amendment; original strict tar/FITS parser preserved."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import resource
import signal
import sys
import time

import inspect_source as original

PRIOR_BYTES = 1536
PRIOR_SECONDS = 1.563056
SOURCE_SHA = "187755434816addc045f13a4efd8515bb86b83531adc0eb7586412d9cfca4994"


class SharedMeter:
    """Reserve requested output so nested reads cannot overspend the same cap."""
    def __init__(self, cap=1024**3, prior=PRIOR_BYTES, seconds=120 - PRIOR_SECONDS):
        self.cap, self.count, self.reserved = cap, prior, 0
        self.seconds, self.started = seconds, time.monotonic()
        self.layers = {"outer_gzip_decoded": 0, "inner_gzip_decoded": 0}

    def reserve(self, size):
        if time.monotonic() - self.started >= self.seconds:
            raise original.IntakeStop("remaining cumulative inspection wall-time limit")
        if size < 0 or self.count + self.reserved + size > self.cap:
            raise original.IntakeStop("shared two-layer cumulative decompressed-byte limit")
        self.reserved += size


class MeteredStream:
    def __init__(self, stream, meter, layer):
        self.stream, self.meter, self.layer = stream, meter, layer

    def read(self, size=-1):
        self.meter.reserve(size)
        try:
            data = self.stream.read(size)
            self.meter.count += len(data)
            self.meter.layers[self.layer] += len(data)
            return data
        finally:
            self.meter.reserved -= size


class PrefixStream:
    """Return already-metered lookahead without re-decoding or skipping it."""
    def __init__(self, prefix, rest):
        self.prefix, self.rest = prefix, rest

    def read(self, size):
        first, self.prefix = self.prefix[:size], self.prefix[size:]
        return first + self.rest.read(size - len(first)) if len(first) < size else first


def inspect_two_layers(compressed, meter=None, limits=None):
    meter = SharedMeter(prior=0) if meter is None else meter
    limits = original.Limits(seconds=meter.seconds) if limits is None else limits
    result = {"coverage": "INTAKE_INCOMPLETE", "members": [], "obstruction": None,
              "resources": {}}
    try:
        outer_gzip = gzip.GzipFile(fileobj=compressed, mode="rb")
        outer = MeteredStream(outer_gzip, meter, "outer_gzip_decoded")
        # Only the exactly evidenced second layer is accepted. No recursion.
        outer_prefix = outer.read(2)
        if outer_prefix != b"\x1f\x8b":
            raise original.IntakeStop("observed double-gzip source amendment does not match outer decoded signature")
        inner_gzip = gzip.GzipFile(fileobj=PrefixStream(outer_prefix, outer), mode="rb")
        inner = MeteredStream(inner_gzip, meter, "inner_gzip_decoded")
        prefix = inner.read(512)
        if prefix.startswith((b"\x1f\x8b", b"PK\x03\x04", b"BZh")):
            raise original.IntakeStop("third compression layer rejected; no recursive decoding")
        if len(prefix) != 512:
            raise original.IntakeStop("inner stream lacks complete initial tar header")
        result = original.inspect_stream(PrefixStream(prefix, inner), limits)
        if result["coverage"] == "COMPLETE_PERMITTED_METADATA_INSPECTION":
            # Reading both EOFs checks both gzip trailers/CRCs. Close alone
            # would not establish trailer validity after a partial read.
            if inner.read(1):
                raise original.IntakeStop("unexpected inner content after confirmed tar/gzip EOF")
            if outer.read(1):
                raise original.IntakeStop("unconsumed content after inner gzip EOF")
            result["gzip_trailers"] = "BOTH_LAYERS_EOF_CRC_VALIDATED"
    except Exception as exc:
        result["coverage"] = "INTAKE_INCOMPLETE"
        result["obstruction"] = {"type": type(exc).__name__, "message": str(exc),
                                 "uninspected": "unreached active/later tar members and unvalidated remaining gzip content"}
    result["two_layer_resources"] = {
        "prior_decoded_bytes": meter.count - sum(meter.layers.values()),
        **meter.layers, "cumulative_decompressed_bytes_all_layers": meter.count,
        "inspection_elapsed_seconds": time.monotonic() - meter.started,
        "cumulative_byte_limit": meter.cap,
        "remaining_wall_allowance_seconds_at_start": meter.seconds,
        "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    return result


def main():
    started = time.monotonic()
    base = Path(__file__).resolve().parent
    output = base / "SOURCE_INDEX_DOUBLE_GZIP.json"
    if output.exists():
        raise FileExistsError("preserve existing continuation result; no replay")
    def timeout(signum, frame):
        raise original.IntakeStop("remaining 118.436944-second inspection wall alarm")
    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, 120 - PRIOR_SECONDS)
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    threads = int(next(line.split()[1] for line in Path("/proc/self/status").read_text().splitlines()
                       if line.startswith("Threads:")))
    if threads > 2:
        raise original.IntakeStop("process threads exceed two")
    old_index = json.loads((base / "SOURCE_INDEX.json").read_text())
    source = Path(old_index["source"]["path"])
    if original.sha256(source) != SOURCE_SHA or source.stat().st_size != 86556876:
        raise original.IntakeStop("frozen source identity drift")
    prior_metadata_files = ["SOURCE_INDEX.json", "PREFIX_DIAGNOSTIC.json", "ASSESSMENT.md", "FORMAT_DIAGNOSIS.md"]
    # Conservative UTF-8 envelope-byte charge includes the retained raw
    # metadata, hex/escaped copies and explanatory text from prior stages.
    prior_metadata = sum((base / name).stat().st_size for name in prior_metadata_files)
    remaining_seconds = 120 - PRIOR_SECONDS - (time.monotonic() - started)
    meter = SharedMeter(prior=PRIOR_BYTES, seconds=remaining_seconds)
    limits = original.Limits(seconds=remaining_seconds, metadata=16 * 1024**2 - prior_metadata)
    with source.open("rb") as compressed:
        result = inspect_two_layers(compressed, meter, limits)
    result.update({"owner": "obsstat", "scope": "source qualification only",
                   "claim_tier": "C0", "transfer_source": "none", "non_claim_bearing": True,
                   "source": old_index["source"],
                   "format_amendment": "Exactly two evidenced gzip layers; original strict tar/FITS parser unchanged",
                   "prior_evidence_sha256": {name: original.sha256(base / name) for name in prior_metadata_files},
                   "limits": {**asdict(limits), "memory_bytes": 512 * 1024**2, "threads": 2,
                              "shared_all_layer_decompressed_bytes": 1024**3},
                   "execution": {"time_utc": datetime.now(timezone.utc).isoformat(),
                                 "interpreter": sys.executable, "astropy": original.astropy_version,
                                 "argv": sys.argv, "requested_model": "gpt-6.1-sol/high",
                                 "observed_runtime": "UNKNOWN", "process_threads_observed": threads,
                                 "prior_wall_charge_seconds": PRIOR_SECONDS,
                                 "continuation_elapsed_seconds": time.monotonic() - started,
                                 "cumulative_wall_charge_seconds": PRIOR_SECONDS + time.monotonic() - started,
                                 "prior_retained_metadata_envelope_bytes_conservative": prior_metadata},
                   "caveats": ["No numerical FITS array/column data interpreted",
                               "Source qualification only; scientific response law still requires independent assessment"]})
    with output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({"coverage": result["coverage"], "obstruction": result["obstruction"],
                      "members": len(result["members"]), "resources": result["two_layer_resources"],
                      "execution": result["execution"]}, indent=2))
    return 0 if result["coverage"] == "COMPLETE_PERMITTED_METADATA_INSPECTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
