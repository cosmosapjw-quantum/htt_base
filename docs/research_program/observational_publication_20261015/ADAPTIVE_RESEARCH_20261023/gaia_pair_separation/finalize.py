"""Seal saved candidate after all numerical command timers have closed."""

import hashlib
import json
from pathlib import Path
import re

from compute import HERE, sha256


RAW = Path("/mnt/extdrive/workdir/htt_open_data/r25_gaia_pair_separation/raw")
RUNS = ["test_01", "test_02", "production_01", "whitening_probe_01", "package_01", "package_02", "typed_01"]


def main():
    measurements = {}
    for name in RUNS:
        kind, ordinal = name.rsplit("_", 1)
        s = (RAW / f"{kind}_time_{ordinal}.txt").read_text()
        m = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (\S+)", s)
        parts = [float(x) for x in m.group(1).split(":")]
        measurements[name] = {
            "elapsed_seconds":sum(x * 60**i for i, x in enumerate(reversed(parts))),
            "max_rss_bytes":1024*int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", s).group(1)),
            "exit_status":int(re.search(r"Exit status: (\d+)", s).group(1)),
        }
    assert [measurements[x]["exit_status"] for x in RUNS] == [1, 0, 0, 0, 1, 0, 0]
    cumulative = sum(x["elapsed_seconds"] for x in measurements.values())
    maximum_rss = max(x["max_rss_bytes"] for x in measurements.values())
    assert cumulative < 300 and maximum_rss < 1073741824
    candidate_files = ["compute.py", "test_compute.py", "package.py", "finalize.py",
                       "RESULT.json", "arrays.npz", "figure.png", "REPORT.md"]
    candidate_hashes = {p:sha256(HERE / p) for p in candidate_files}
    candidate = "sha256:"+hashlib.sha256(json.dumps(candidate_hashes, sort_keys=True,
                                  separators=(",", ":")).encode()).hexdigest()
    receipt = json.loads((HERE / "RAW_RECEIPT.json").read_text())
    receipt["outcome"] = "success"
    receipt["candidate_identity"] = candidate
    receipt["attempts"] = [x for x in receipt["attempts"] if x["kind"] not in {"saved_carrier_packaging", "saved_carrier_typed_profile"}] + [
        {"kind":"saved_carrier_packaging", "ordinal":1, "status":"FAIL_ENOSPC", "elapsed_seconds":measurements["package_01"]["elapsed_seconds"],
         "reason":"root filesystem filled during compressed carrier write; retained first stderr, removed only incomplete owned array"},
        {"kind":"saved_carrier_packaging", "ordinal":2, "status":"PASS", "elapsed_seconds":measurements["package_02"]["elapsed_seconds"],
         "reason":"compressed from saved external raw carrier; no production pair traversal"},
        {"kind":"saved_carrier_typed_profile", "ordinal":1, "status":"PASS", "elapsed_seconds":measurements["typed_01"]["elapsed_seconds"],
         "reason":"materialized response tensors from saved d and STF basis; no production pair traversal"},
    ]
    receipt["numeric_command_metrics"] = measurements
    receipt["cumulative_numeric_elapsed_seconds"] = cumulative
    receipt["maximum_numeric_rss_bytes"] = maximum_rss
    receipt["raw_files"] = {p.name:sha256(p) for p in sorted(RAW.iterdir()) if p.is_file()}
    receipt.pop("raw_files_before_packaging", None)
    (HERE / "RAW_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    manifest = json.loads((HERE / "MANIFEST.json").read_text())
    manifest["candidate_identity"] = candidate
    manifest["file_hashes"] = {p:sha256(HERE / p) for p in candidate_files + ["RAW_RECEIPT.json"]}
    manifest["cumulative_numeric_elapsed_seconds"] = cumulative
    manifest["maximum_numeric_rss_bytes"] = maximum_rss
    (HERE / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    ret = json.loads((HERE / "RETURN.json").read_text())
    ret["outcome"] = "success"
    ret["candidate_identity"] = candidate
    ret["actual_numeric_elapsed_seconds"] = cumulative
    ret["actual_numeric_max_rss_bytes"] = maximum_rss
    ret["manifest_sha256"] = sha256(HERE / "MANIFEST.json")
    ret.pop("actual_numeric_elapsed_seconds_before_packaging", None)
    (HERE / "RETURN.json").write_text(json.dumps(ret, indent=2) + "\n")
    print(json.dumps({"candidate_identity":candidate, "numeric_seconds":cumulative,
                      "max_rss_bytes":maximum_rss, "manifest_sha256":ret["manifest_sha256"]}))


if __name__ == "__main__":
    main()
