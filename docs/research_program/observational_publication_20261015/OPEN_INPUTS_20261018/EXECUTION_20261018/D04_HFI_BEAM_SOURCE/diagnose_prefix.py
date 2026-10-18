"""One approved <=10 s prefix diagnostic, never a metadata inspection replay."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import zlib


def main():
    started = time.monotonic()
    def timeout(signum, frame):
        raise TimeoutError("10-second prefix diagnostic limit")
    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, 10)
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    base = Path(__file__).resolve().parent
    source = Path("/mnt/extdrive/workdir/htt_open_data/planck/PR3/beams/HFI_RIMO_BEAMS_R3.01.tar.gz")
    expected = "187755434816addc045f13a4efd8515bb86b83531adc0eb7586412d9cfca4994"
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            digest.update(block)
    if digest.hexdigest() != expected or source.stat().st_size != 86556876:
        raise ValueError("frozen source identity mismatch")
    threads = int(next(line.split()[1] for line in Path("/proc/self/status").read_text().splitlines()
                       if line.startswith("Threads:")))
    if threads > 2:
        raise ValueError("observed process threads exceed two")
    decoded = 0
    with gzip.open(source, "rb") as outer:
        prefix = outer.read(512)
        decoded += len(prefix)
        nested_gzip = prefix.startswith(b"\x1f\x8b")
        inner_prefix = None
        if nested_gzip:
            decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
            inner_prefix = decoder.decompress(prefix, 512)
            decoded += len(inner_prefix)
            # Only a directly observed nested-gzip signature permits this one
            # bounded inner prefix. Charge outer and inner decoded bytes.
            while len(inner_prefix) < 512 and not decoder.eof:
                if decoded >= 4096:
                    break
                chunk = outer.read(1)
                decoded += len(chunk)
                if not chunk:
                    break
                extra = decoder.decompress(chunk, min(512 - len(inner_prefix), 4096 - decoded))
                inner_prefix += extra
                decoded += len(extra)
    if len(prefix) != 512 or decoded > 4096:
        raise ValueError("prefix truncated or decoded diagnostic allowance exceeded")
    checksum_field = prefix[148:156]
    try:
        stored = int(checksum_field.strip(b"\0 "), 8)
    except ValueError:
        stored = None
    normalized = prefix[:148] + b" " * 8 + prefix[156:]
    unsigned = sum(normalized)
    signed = sum(byte if byte < 128 else byte - 256 for byte in normalized)
    result = {
        "determination": "INTAKE_INCOMPLETE",
        "scope": "approved bounded format diagnostic only; no full inspection replay",
        "source": {"path": str(source), "bytes": source.stat().st_size, "sha256": expected},
        "original_source_index_sha256": hashlib.sha256((base / "SOURCE_INDEX.json").read_bytes()).hexdigest(),
        "outer_gzip_decoded_prefix": {"offset": 0, "bytes": len(prefix),
                                      "hex": prefix.hex(), "escaped_bytes_repr": repr(prefix)},
        "tar": {"checksum_field_offset": 148, "checksum_field_hex": checksum_field.hex(),
                "stored_octal_value_or_null": stored, "calculated_unsigned": unsigned,
                "calculated_signed": signed, "unsigned_matches": stored == unsigned,
                "signed_matches": stored == signed,
                "magic_offset": 257, "magic_hex": prefix[257:263].hex(),
                "version_offset": 263, "version_hex": prefix[263:265].hex(),
                "type_offset": 156, "type_hex": prefix[156:157].hex()},
        "signatures": {"fits_simple_at_zero": prefix.startswith(b"SIMPLE  ="),
                       "fits_xtension_at_zero": prefix.startswith(b"XTENSION="),
                       "nested_gzip_at_zero": nested_gzip,
                       "zip_at_zero": prefix.startswith(b"PK\x03\x04")},
        "inner_prefix_if_nested_gzip": None if inner_prefix is None else {
            "bytes": len(inner_prefix), "hex": inner_prefix.hex(), "escaped_bytes_repr": repr(inner_prefix)},
        "resources": {"new_decoded_bytes_all_layers_including_replayed": decoded,
                      "prior_failed_decoded_bytes": 512, "cumulative_decoded_bytes": decoded + 512,
                      "elapsed_seconds": time.monotonic() - started,
                      "prior_wall_seconds_conservative": 0.788,
                      "cumulative_wall_seconds_conservative": 0.788 + time.monotonic() - started,
                      "new_decoded_byte_allowance": 4096, "diagnostic_wall_limit_seconds": 10,
                      "inspection_total_wall_limit_seconds": 120,
                      "process_threads_observed": threads,
                      "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      "memory_address_space_limit_bytes": 512 * 1024**2},
        "execution": {"interpreter": sys.executable, "argv": sys.argv,
                      "requested_model": "gpt-6.1-sol/high", "observed_runtime": "UNKNOWN",
                      "parent_pid": os.getppid()},
        "caveat": "No FITS array/column values or full archive metadata inspected; independent framing remains required."
    }
    with (base / "PREFIX_DIAGNOSTIC.json").open("x") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
