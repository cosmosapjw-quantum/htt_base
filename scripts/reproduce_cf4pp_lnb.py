#!/usr/bin/env python3
"""Bind or quarantine the legacy CF4++ lnB sensitivity number.

This is a provenance search only.  It scans repo-local canonical JSON payloads
for a CF4++ lnB record with explicit config/input hashes.  It does not rerun
inference or synthesize a missing legacy value.
"""
from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = REPO_ROOT / "docs/generated/cf4pp_lnb_provenance_report.json"
OUT_MD = REPO_ROOT / "docs/generated/cf4pp_lnb_provenance_report.md"
DEFAULT_SOURCE_JSON = (
    "docs/generated/current_science_plot_payload.json",
    "docs/generated/revision_experiment_assets.json",
    "docs/generated/expanded_manuscript_figure_suite.json",
    "docs/generated/current_manuscript_figure_curation.json",
    "docs/generated/observed_longrun_analysis.json",
    "docs/generated/observational_data_inventory.json",
    "docs/audits/external_research_inputs_2026-06-20/input_inventory.json",
    "figures/conditioned_legacy/root__fig_cf4pp_sensitivity.manifest.json",
    "htt/workspace/results/mio_directional_coherence.json",
    "htt/workspace/results/integrated_pipeline_results.json",
    "htt/workspace/data/obs_defaults.json",
    "dl_pipeline/assets/obs_meta/INDEX.json",
)
TARGET_LABELS = ("cf4++", "cf4pp")
TARGET_LNB = 44.0
TARGET_TOL = 0.05
GENERATING_COMMAND = "venv/bin/python scripts/reproduce_cf4pp_lnb.py --write"
ALLOWED_BOUND_CLAIM_TIERS = frozenset(
    {
        "diagnostic_only",
        "transfer_conditional",
    }
)
ALLOWED_BOUND_TRANSFER_SOURCES = frozenset(
    {
        "legacy_external_transfer_or_unbound",
        "legacy_external_proxy",
        "external_transfer",
        "AniCLASS_external",
        "empirical_proxy",
    }
)
ACCEPTANCE_REQUIREMENTS = (
    "cf4pp_identity",
    "target_lnb_value",
    "bound_config_hash",
    "nonempty_input_hashes",
    "generating_command",
    "allowed_claim_tier",
    "allowed_transfer_source",
)


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _jsonable(value: object) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_jsonable(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("non-finite float is not reportable")
        return value
    if isinstance(value, (int, bool)) or value is None:
        return value
    return str(value)


def _source_files(paths: Sequence[Path] | None = None) -> list[Path]:
    if paths:
        candidates = [path if path.is_absolute() else REPO_ROOT / path for path in paths]
    else:
        candidates = [REPO_ROOT / path for path in DEFAULT_SOURCE_JSON]
    return sorted({path.resolve() for path in candidates if path.is_file()})


def _load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _normalise(text: object) -> str:
    return str(text).strip().lower().replace("_", "")


def _mapping_mentions_cf4pp(mapping: Mapping[str, object]) -> bool:
    haystack = " ".join(
        str(item)
        for key, value in mapping.items()
        for item in (key, value)
        if not isinstance(value, (Mapping, list, tuple))
    ).lower()
    return any(label in haystack.replace("_", "") for label in TARGET_LABELS)


def _lnb_values(mapping: Mapping[str, object]) -> list[float]:
    values: list[float] = []
    for key, value in mapping.items():
        key_norm = _normalise(key)
        if "lnb" not in key_norm and "logbayes" not in key_norm:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            values.append(number)
    return values


def _as_string_list(value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        text = str(value).strip()
        return [text] if text else []
    if isinstance(value, Sequence):
        result = [str(item).strip() for item in value]
        return [item for item in result if item]
    return []


def _record_provenance(
    mapping: Mapping[str, object],
) -> tuple[str | None, list[str], str | None, str | None]:
    config_hash = mapping.get("config_hash")
    input_hashes = mapping.get("input_hashes")
    command = mapping.get("generating_command")
    claim_tier = mapping.get("claim_tier")
    if isinstance(config_hash, str) and config_hash.strip():
        return (
            config_hash.strip(),
            _as_string_list(input_hashes),
            str(command).strip() if command else None,
            str(claim_tier).strip() if claim_tier else None,
        )
    return (
        None,
        _as_string_list(input_hashes),
        str(command).strip() if command else None,
        str(claim_tier).strip() if claim_tier else None,
    )


def _transfer_source(mapping: Mapping[str, object]) -> str | None:
    value = mapping.get("transfer_source")
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _rejection_reasons(record: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not any(abs(value - TARGET_LNB) <= TARGET_TOL for value in record["lnB_values"]):
        reasons.append("target_lnb_absent")
    if not record.get("config_hash") or not record.get("input_hashes"):
        reasons.append("missing_bound_config_or_input_hashes")
    if not record.get("generating_command"):
        reasons.append("missing_generating_command")
    if not record.get("claim_tier"):
        reasons.append("missing_claim_tier")
    elif record["claim_tier"] not in ALLOWED_BOUND_CLAIM_TIERS:
        reasons.append("unsupported_claim_tier")
    if not record.get("transfer_source"):
        reasons.append("missing_transfer_source")
    elif record["transfer_source"] not in ALLOWED_BOUND_TRANSFER_SOURCES:
        reasons.append("unsupported_transfer_source")
    return reasons


def _find_records(
    value: object,
    *,
    source_path: Path,
    pointer: str = "",
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(value, Mapping):
        if _mapping_mentions_cf4pp(value):
            lnb_values = _lnb_values(value)
            config_hash, input_hashes, command, claim_tier = _record_provenance(value)
            transfer_source = _transfer_source(value)
            record = {
                "source_path": _repo_relative(source_path),
                "pointer": pointer or "/",
                "lnB_values": lnb_values,
                "config_hash": config_hash,
                "input_hashes": input_hashes,
                "generating_command": command,
                "claim_tier": claim_tier,
                "transfer_source": transfer_source,
            }
            record["rejection_reasons"] = _rejection_reasons(record)
            record["has_bound_provenance"] = not record["rejection_reasons"]
            records.append(
                record
            )
        for key, item in value.items():
            records.extend(
                _find_records(
                    item,
                    source_path=source_path,
                    pointer=f"{pointer}/{key}",
                )
            )
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            records.extend(
                _find_records(
                    item,
                    source_path=source_path,
                    pointer=f"{pointer}/{index}",
                )
            )
    return records


def _source_hashes(files: Iterable[Path]) -> list[str]:
    return [f"{_repo_relative(path)}={_sha256_file(path)}" for path in files]


def build_report(source_json: Sequence[Path] | None = None) -> dict[str, Any]:
    json_files = _source_files(source_json)
    source_hashes = _source_hashes(json_files)
    source_records: list[dict[str, Any]] = []
    for path in json_files:
        payload = _load_json(path)
        if payload is None:
            continue
        source_records.extend(_find_records(payload, source_path=path))

    bound_records = [
        record
        for record in source_records
        if record["has_bound_provenance"]
        and any(abs(value - TARGET_LNB) <= TARGET_TOL for value in record["lnB_values"])
    ]
    config_hash = _sha256_text(
        json.dumps(
            {
                "script": "scripts/reproduce_cf4pp_lnb.py",
                "source_json": [_repo_relative(path) for path in json_files],
                "target_labels": TARGET_LABELS,
                "target_lnb": TARGET_LNB,
                "target_tolerance": TARGET_TOL,
                "acceptance_requirements": ACCEPTANCE_REQUIREMENTS,
                "allowed_bound_claim_tiers": sorted(ALLOWED_BOUND_CLAIM_TIERS),
                "allowed_bound_transfer_sources": sorted(ALLOWED_BOUND_TRANSFER_SOURCES),
                "source_hashes": source_hashes,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )

    if bound_records:
        selected = bound_records[0]
        status = "reproduced_with_bound_inputs"
        claim_tier = "transfer_conditional"
        lnb_cf4pp = next(
            value
            for value in selected["lnB_values"]
            if abs(value - TARGET_LNB) <= TARGET_TOL
        )
        bound_result_config_hash = selected["config_hash"]
        bound_result_input_hashes = selected["input_hashes"]
        caveats = [
            "transfer-conditional legacy sensitivity only",
            "not native transfer",
            "not a family or geometry claim",
            "not used as evidence without matched null/PPC/LOOCV status",
        ]
    else:
        selected = None
        status = "quarantined_untraceable"
        claim_tier = "blocked"
        lnb_cf4pp = None
        bound_result_config_hash = None
        bound_result_input_hashes = []
        caveats = [
            "not used in manuscript headline",
            "dedicated rerun required",
            "canonical JSON search did not bind the CF4++ lnB value",
            "not native transfer",
            "not a family or geometry claim",
        ]

    return {
        "schema_version": "htt.cf4pp_lnb_provenance.v1",
        "owner": "HTT",
        "implementation_scope": "cf4pp_lnb_provenance_gate",
        "claim_tier": claim_tier,
        "transfer_source": "legacy_external_transfer_or_unbound",
        "status": status,
        "target": "CF4++ legacy lnB sensitivity value",
        "lnB_cf4pp": lnb_cf4pp,
        "config_hash": config_hash,
        "bound_result_config_hash": bound_result_config_hash,
        "input_hashes": source_hashes,
        "bound_result_input_hashes": bound_result_input_hashes,
        "accepted_source": selected,
        "source_search": source_records,
        "rejected_candidates": [
            record for record in source_records if record["rejection_reasons"]
        ],
        "source_file_count": len(json_files),
        "source_json": [_repo_relative(path) for path in json_files],
        "acceptance_requirements": list(ACCEPTANCE_REQUIREMENTS),
        "allowed_bound_claim_tiers": sorted(ALLOWED_BOUND_CLAIM_TIERS),
        "allowed_bound_transfer_sources": sorted(ALLOWED_BOUND_TRANSFER_SOURCES),
        "sky_support_status": "not_directional",
        "covariance_status": "not_bound_for_cf4pp_legacy_sensitivity",
        "null_mock_status": "not_bound",
        "caveats": caveats,
        "generating_command": GENERATING_COMMAND,
        "git_commit_or_worktree_state": "pending_rev_r077_commit",
        "external_context": [
            "https://academic.oup.com/mnras/article/527/2/3788/7419869",
            "https://academic.oup.com/mnras/article/526/2/3051/7296158",
            "https://edd.ifa.hawaii.edu/describe_columns.php?table=kcf4allvel",
        ],
    }


def render_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# CF4++ lnB Provenance Report",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        f"transfer_source: {payload['transfer_source']}",
        f"status: {payload['status']}",
        f"config_hash: {payload['config_hash']}",
        f"input_hash_count: {len(payload['input_hashes'])}",
        f"sky_support_status: {payload['sky_support_status']}",
        f"covariance_status: {payload['covariance_status']}",
        f"null_mock_status: {payload['null_mock_status']}",
        "generating_command: `venv/bin/python scripts/reproduce_cf4pp_lnb.py --write`",
        f"git_commit_or_worktree_state: {payload['git_commit_or_worktree_state']}",
        "",
        "input_hashes:",
        *[f"- {item}" for item in payload["input_hashes"]],
        "",
        "## Decision",
        "",
    ]
    if payload["status"] == "reproduced_with_bound_inputs":
        lines.append(
            "The CF4++ legacy sensitivity value is bound to a repo-local JSON "
            "record with config and input hashes. It remains transfer-conditional."
        )
    else:
        lines.append(
            "The CF4++ legacy sensitivity value is quarantined: repo-local "
            "canonical JSON payloads did not bind it to config and input hashes."
        )
    lines.extend(
        [
            "",
            "## Accepted Source",
            "",
            (
                "- none"
                if payload["accepted_source"] is None
                else f"- `{payload['accepted_source']['source_path']}` "
                f"{payload['accepted_source']['pointer']}"
            ),
            "",
            "## Rejected Candidates",
            "",
            *[
                f"- `{record['source_path']}` {record['pointer']}: "
                f"{', '.join(record['rejection_reasons'])}"
                for record in payload["rejected_candidates"]
            ],
            "",
            "## Manuscript Action",
            "",
            (
                "The CF4++ row may remain only as a labeled, transfer-conditional "
                "sensitivity row with bound provenance."
                if payload["status"] == "reproduced_with_bound_inputs"
                else "Remove the +44/+105.8 values from headline/result prose and "
                "keep CF4++/Watkins rows as unbound, quarantined sensitivity "
                "entries pending a dedicated rerun."
            ),
            "",
            "## Caveats",
            "",
            *[f"- {item}" for item in payload["caveats"]],
            "",
            "## Search Summary",
            "",
            f"- canonical JSON files scanned: {payload['source_file_count']}",
            f"- CF4++ candidate records: {len(payload['source_search'])}",
            f"- bound input hashes for target value: {len(payload['bound_result_input_hashes'])}",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_outputs(payload: Mapping[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")


def _read_expected(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def check_outputs(payload: Mapping[str, Any]) -> list[str]:
    expected_json = json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n"
    expected_md = render_markdown(payload)
    mismatches: list[str] = []
    if _read_expected(OUT_JSON) != expected_json:
        mismatches.append(_repo_relative(OUT_JSON))
    if _read_expected(OUT_MD) != expected_md:
        mismatches.append(_repo_relative(OUT_MD))
    return mismatches


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-json",
        action="append",
        type=Path,
        default=None,
        help="Override source JSON list; may be passed multiple times.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write report files")
    mode.add_argument("--check", action="store_true", help="verify reports are current")
    mode.add_argument("--json", action="store_true", help="print report JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.source_json and not args.json:
        print("--source-json is only allowed with --json", file=sys.stderr)
        return 2
    payload = build_report(args.source_json)
    if args.write:
        _write_outputs(payload)
        print(f"wrote {_repo_relative(OUT_JSON)}")
        print(f"wrote {_repo_relative(OUT_MD)}")
        return 0
    if args.check:
        mismatches = check_outputs(payload)
        if mismatches:
            print("stale CF4++ provenance report:", ", ".join(mismatches), file=sys.stderr)
            return 1
        print("OK: CF4++ lnB provenance report is current")
        return 0
    print(json.dumps(_jsonable(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
