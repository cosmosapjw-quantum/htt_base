"""Read a pinned source fixture with ast.literal_eval; never import upstream code."""
import argparse
import ast
import csv
import hashlib
import io
import json
from pathlib import Path

SOURCE_SHA256 = "3580ef81c7860c63f476bfb2c03b02120b5e34da9573885aef28f456d53c2440"
SOURCE_URL = "https://github.com/NumCosmo/NumCosmo/blob/91ecab49a0b3c48846fd128cd8ada8c7ca6e0620/tests/python/conftest.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("pinned fixture identity mismatch")
    matches = []
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(x, ast.Name) and x.id == "EDD_CF4_SNIA_EXCERPT"
            for x in node.targets
        ):
            matches.append(ast.literal_eval(node.value))
    if len(matches) != 1 or not isinstance(matches[0], str):
        raise ValueError("expected exactly one literal fixture")
    rows = list(csv.reader(io.StringIO(matches[0]), delimiter="|"))
    if len(rows) != 11 or any(len(x) != 45 for x in rows):
        raise ValueError("expected five header lines and six 45-column records")
    columns = rows[1]
    if len(set(columns)) != 45:
        raise ValueError("duplicate columns")
    records = [dict(zip(columns, row)) for row in rows[5:]]
    pgcs = [int(r["pgc"]) for r in records]
    if len(set(pgcs)) != 6:
        raise ValueError("non-unique excerpt PGC")
    args.outdir.mkdir(parents=True, exist_ok=True)
    target = args.outdir / "six_contributor_identities.csv"
    with target.open("w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["source_record_1based", "PGC", "SNIa_literal", "group_1PGC"])
        for i, record in enumerate(records, 1):
            writer.writerow([i, record["pgc"], record["SNIa"], record["1PGC"]])
    result = {
        "owner": "obsstat",
        "status": "DIAGNOSTIC_ONLY",
        "claim_tier": "C0",
        "scope": "six source-claimed EDD records in public NumCosmo test fixture; not a full EDD export",
        "transfer_source": "none",
        "source_url": SOURCE_URL,
        "source_sha256": SOURCE_SHA256,
        "source_claimed_export_date": "2026-10-17",
        "header_lines": 5,
        "record_count": len(records),
        "field_count": len(columns),
        "PGCs": pgcs,
        "derived_identity_csv_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "schema": [
            {"name": name, "format": fmt, "unit": unit, "description": description}
            for name, fmt, unit, description in zip(columns, rows[2], rows[3], rows[4])
        ],
        "caveats": [
            "Source fixture labels itself as the first six rows of an EDD export; live EDD was not queried.",
            "No entire-catalogue contributor completeness, row independence, selection law or covariance inferred.",
            "No upstream Python, notebook or serialized .gvar object executed or loaded.",
        ],
    }
    (args.outdir / "excerpt_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"records": len(records), "fields": len(columns), "PGCs": pgcs}))


if __name__ == "__main__":
    main()
