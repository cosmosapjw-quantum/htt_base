#!/usr/bin/env python3
"""Portable source-manifest and test runner for PR-278."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "docs/research_program/post_pr275/tier_a_adjudication"
SOURCE_JSON = OUTPUT_DIR / "source_manifest.json"
SOURCE_MD = OUTPUT_DIR / "source_manifest.md"
PANEL_JSON = OUTPUT_DIR / "panel_receipt.json"
LEDGER_JSON = OUTPUT_DIR / "adjudication_ledger.json"
LEDGER_MD = OUTPUT_DIR / "adjudication_ledger.md"
EXPECTED_MANIFEST_CONTENT_SHA256 = (
    "8db86f88a29ff31a8d75697e62f03582cc805453d2519c262780833d24830ecf"
)
EXPECTED_SOURCE_JSON_SHA256 = (
    "0b7eb908da0e92e282ae2470e50ae584cd5f8c00c82c5b1f52f1664145e68a13"
)
EXPECTED_SOURCE_MD_SHA256 = (
    "bc0864ba9f657b3b7ad6d4cd130af402a1fed264ae838337c6d0f2a9e7b1c824"
)
EXPECTED_PANEL_JSON_SHA256 = (
    "b7839be6ecf6b0fcdd81f9cbbcff03fc08058d20f2c62b94588602c8ae966f04"
)
EXPECTED_LEDGER_JSON_SHA256 = (
    "82707a95ff8d351da9c4212a8df50395e05bb7d9ec5e64546afebb837ea8e758"
)
EXPECTED_LEDGER_MD_SHA256 = (
    "fe9bb600dbc64ac6314b1267b5082bfdf0184b4b1fa827fbc459700e957a9202"
)


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    source_paths = [str(ROOT / "htt/src"), str(ROOT / "htt")]
    existing = environment.get("PYTHONPATH")
    if existing:
        source_paths.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(source_paths)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["MPLBACKEND"] = "Agg"
    return environment


def _source_payload() -> dict[str, object]:
    source = ROOT / "htt/src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    package = ROOT / "htt"
    if str(package) not in sys.path:
        sys.path.insert(0, str(package))
    from common.tier_a_lane_adjudication import build_source_manifest

    return build_source_manifest(ROOT)


def _ledger_builders() -> tuple[
    Callable[[Path], dict[str, object]],
    Callable[[Path], dict[str, object]],
]:
    source = ROOT / "htt/src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    package = ROOT / "htt"
    if str(package) not in sys.path:
        sys.path.insert(0, str(package))
    from common.tier_a_adjudication_ledger import (
        build_adjudication_ledger,
        build_panel_receipt_from_run,
    )

    return build_panel_receipt_from_run, build_adjudication_ledger


def _source_bytes(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _source_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    assert isinstance(summary, dict)
    lines = [
        "# PR-278 Tier-A adjudication source manifest",
        "",
        "This is a receipt inventory and review queue, not a capability or publication grant.",
        "",
        "## Exact counts",
        "",
        f"- family rows: {summary['family_rows']}",
        f"- author-side candidates: {summary['source_candidates']}",
        f"- reviewable now: {summary['reviewable_families']}",
        f"- non-terminal candidate holds: {summary['source_candidate_holds']}",
        f"- event-gated families: {summary['event_gated_families']}",
        f"- dual-axis rows: {summary['dual_axis_rows']}",
        f"- exact dual-axis terminal-receipt crosswalks: {summary['dual_axis_exact_crosswalks']}",
        f"- dual-axis INCONCLUSIVE dispositions: {summary['dual_axis_inconclusive']}",
        f"- CF4 P0 rescues: {summary['cf4_p0_rescue_count']}",
        "",
        "## Family queue",
        "",
        "| Family | Source status | Reviewable | Pre-disposition | Blocker |",
        "|---|---|---:|---|---|",
    ]
    family_units = payload["family_units"]
    assert isinstance(family_units, list)
    for row in family_units:
        assert isinstance(row, dict)
        blocker = row.get("event_gate") or ", ".join(row["missing_terminal_cards"]) or "none"
        lines.append(
            f"| {row['unit_id']} | {row['source_unlock_status']} | "
            f"{'yes' if row['reviewable_now'] else 'no'} | "
            f"{row['pre_adjudication_disposition']} | {blocker} |"
        )
    lines += [
        "",
        "## Dual-axis negative mapping result",
        "",
        (
            "All 62 registered rows retain individual `INCONCLUSIVE` dispositions "
            "because no exact terminal-receipt crosswalk exists. Semantic "
            "similarity is not a crosswalk."
        ),
        "",
        (
            "Final aggregation remains PR-157. "
            "`capability_effect=NONE_PENDING_PR157`, `public_use=false`, and the "
            "claim ceiling remains `diagnostic_only`."
        ),
        "",
    ]
    return "\n".join(lines)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _verify_frozen_source() -> int:
    if (
        not SOURCE_JSON.is_file()
        or SOURCE_JSON.is_symlink()
        or not SOURCE_MD.is_file()
        or SOURCE_MD.is_symlink()
    ):
        print(json.dumps({"ok": False, "mode": "verify-frozen-source"}))
        return 1
    json_bytes = SOURCE_JSON.read_bytes()
    markdown_bytes = SOURCE_MD.read_bytes()
    try:
        payload = json.loads(json_bytes)
    except json.JSONDecodeError:
        print(json.dumps({"ok": False, "mode": "verify-frozen-source"}))
        return 1
    if not isinstance(payload, dict):
        print(json.dumps({"ok": False, "mode": "verify-frozen-source"}))
        return 1
    recorded = payload.pop("manifest_content_sha256", None)
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    ok = (
        recorded == EXPECTED_MANIFEST_CONTENT_SHA256
        and _sha256(canonical) == EXPECTED_MANIFEST_CONTENT_SHA256
        and _sha256(json_bytes) == EXPECTED_SOURCE_JSON_SHA256
        and _sha256(markdown_bytes) == EXPECTED_SOURCE_MD_SHA256
    )
    print(json.dumps({"ok": ok, "mode": "verify-frozen-source"}, sort_keys=True))
    return 0 if ok else 1


def _ledger_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    assert isinstance(summary, dict)
    lines = [
        "# PR-278 Tier-A per-lane adjudication ledger",
        "",
        (
            "This ledger is diagnostic-only receipt disposition for later PR-157 "
            "aggregation. It issues no claim capability and enables no public use."
        ),
        "",
        "## Exact disposition counts",
        "",
        f"- family GRANT: {summary['family_GRANT']}",
        f"- family HOLD: {summary['family_HOLD']}",
        f"- family INCONCLUSIVE: {summary['family_INCONCLUSIVE']}",
        f"- family DOWNGRADE: {summary['family_DOWNGRADE']}",
        f"- dual-axis INCONCLUSIVE: {summary['dual_axis_INCONCLUSIVE']}",
        f"- exact dual-axis crosswalks: {summary['exact_dual_axis_terminal_receipt_crosswalks']}",
        f"- CF4 P0 rescues: {summary['cf4_p0_rescue_count']}",
        "",
        "## Family dispositions",
        "",
        "| Family | Verdict | Origin | Gate or rationale |",
        "|---|---|---|---|",
    ]
    family_rows = payload["family_dispositions"]
    assert isinstance(family_rows, list)
    for row in family_rows:
        assert isinstance(row, dict)
        rationale = str(row["rationale"]).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {row['unit_id']} | {row['verdict']} | "
            f"{row['disposition_origin']} | {rationale} |"
        )
    lines += [
        "",
        "## Dual-axis dispositions",
        "",
        (
            "All 62 rows remain individually `INCONCLUSIVE`: no exact registered "
            "terminal-receipt crosswalk exists, and semantic similarity is not a "
            "substitute."
        ),
        "",
        "| Row | Verdict |",
        "|---|---|",
    ]
    dual_rows = payload["dual_axis_dispositions"]
    assert isinstance(dual_rows, list)
    for row in dual_rows:
        assert isinstance(row, dict)
        lines.append(f"| {row['unit_id']} | {row['verdict']} |")
    lines += [
        "",
        (
            "PR-157 remains the final aggregator. "
            "`capability_effect=NONE_PENDING_PR157`, `public_use=false`, and "
            "`claim_ceiling=diagnostic_only`."
        ),
        "",
    ]
    return "\n".join(lines)


def _write_or_check_panel(*, write: bool) -> int:
    build_panel, _ = _ledger_builders()
    payload = build_panel(ROOT)
    expected = _source_bytes(payload)
    if write:
        PANEL_JSON.write_bytes(expected)
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "write-panel",
                    "receipt_content_sha256": payload["receipt_content_sha256"],
                },
                sort_keys=True,
            )
        )
        return 0
    ok = (
        PANEL_JSON.is_file()
        and not PANEL_JSON.is_symlink()
        and PANEL_JSON.read_bytes() == expected
    )
    print(json.dumps({"ok": ok, "mode": "check-panel"}, sort_keys=True))
    return 0 if ok else 1


def _write_or_check_ledger(*, write: bool, report_mode: str | None = None) -> int:
    _, build_ledger = _ledger_builders()
    payload = build_ledger(ROOT)
    expected_json = _source_bytes(payload)
    expected_md = _ledger_markdown(payload).encode("utf-8")
    if write:
        LEDGER_JSON.write_bytes(expected_json)
        LEDGER_MD.write_bytes(expected_md)
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "write-ledger",
                    "ledger_content_sha256": payload["ledger_content_sha256"],
                },
                sort_keys=True,
            )
        )
        return 0
    ok = (
        LEDGER_JSON.is_file()
        and not LEDGER_JSON.is_symlink()
        and LEDGER_JSON.read_bytes() == expected_json
        and LEDGER_MD.is_file()
        and not LEDGER_MD.is_symlink()
        and LEDGER_MD.read_bytes() == expected_md
    )
    print(
        json.dumps(
            {"ok": ok, "mode": report_mode or "check-ledger"}, sort_keys=True
        )
    )
    return 0 if ok else 1


def _verify_panel_receipt() -> int:
    ok = PANEL_JSON.is_file() and not PANEL_JSON.is_symlink()
    if ok:
        data = PANEL_JSON.read_bytes()
        ok = _sha256(data) == EXPECTED_PANEL_JSON_SHA256
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            ok = False
            payload = {}
        if isinstance(payload, dict):
            recorded = payload.pop("receipt_content_sha256", None)
            canonical = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
            ok = ok and recorded == _sha256(canonical)
        else:
            ok = False
    print(json.dumps({"ok": ok, "mode": "verify-panel"}, sort_keys=True))
    return 0 if ok else 1


def _verify_adjudication_ledger() -> int:
    if (
        not LEDGER_JSON.is_file()
        or LEDGER_JSON.is_symlink()
        or not LEDGER_MD.is_file()
        or LEDGER_MD.is_symlink()
        or _sha256(LEDGER_JSON.read_bytes()) != EXPECTED_LEDGER_JSON_SHA256
        or _sha256(LEDGER_MD.read_bytes()) != EXPECTED_LEDGER_MD_SHA256
    ):
        print(json.dumps({"ok": False, "mode": "verify-ledger"}, sort_keys=True))
        return 1
    return _write_or_check_ledger(write=False, report_mode="verify-ledger")


def _write_or_check(*, write: bool) -> int:
    payload = _source_payload()
    expected_json = _source_bytes(payload)
    expected_md = _source_markdown(payload).encode("utf-8")
    if write:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        SOURCE_JSON.write_bytes(expected_json)
        SOURCE_MD.write_bytes(expected_md)
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "write-source",
                    "manifest_content_sha256": payload["manifest_content_sha256"],
                },
                sort_keys=True,
            )
        )
        return 0
    ok = (
        SOURCE_JSON.is_file()
        and not SOURCE_JSON.is_symlink()
        and SOURCE_JSON.read_bytes() == expected_json
        and SOURCE_MD.is_file()
        and not SOURCE_MD.is_symlink()
        and SOURCE_MD.read_bytes() == expected_md
    )
    print(json.dumps({"ok": ok, "mode": "check-source"}, sort_keys=True))
    return 0 if ok else 1


def _run(arguments: list[str]) -> int:
    return subprocess.run(
        arguments,
        cwd=ROOT,
        env=_environment(),
        check=False,
    ).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=(
            "write-source",
            "check-source",
            "verify-frozen-source",
            "write-panel",
            "check-panel",
            "verify-panel",
            "write-ledger",
            "check-ledger",
            "verify-ledger",
            "probe",
            "focused",
            "collect",
            "smoke",
        ),
    )
    args = parser.parse_args(argv)
    if args.mode == "write-source":
        return _write_or_check(write=True)
    if args.mode == "check-source":
        return _write_or_check(write=False)
    if args.mode == "verify-frozen-source":
        return _verify_frozen_source()
    if args.mode == "write-panel":
        return _write_or_check_panel(write=True)
    if args.mode == "check-panel":
        return _write_or_check_panel(write=False)
    if args.mode == "verify-panel":
        return _verify_panel_receipt()
    if args.mode == "write-ledger":
        return _write_or_check_ledger(write=True)
    if args.mode == "check-ledger":
        return _write_or_check_ledger(write=False)
    if args.mode == "verify-ledger":
        return _verify_adjudication_ledger()
    if args.mode == "probe":
        return _run(
            [
                sys.executable,
                "-B",
                "-c",
                (
                    "from pathlib import Path; import common, bass, htt; "
                    "root=Path.cwd().resolve(); "
                    "paths=[Path(module.__file__).resolve() for module in "
                    "(common, bass, htt)]; "
                    "assert all(path.is_relative_to(root) for path in paths); "
                    "print('source-layout-ok')"
                ),
            ]
        )
    common = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
    ]
    if args.mode == "focused":
        return _run(
            common
            + [
                "tests/contracts/test_tier_a_lane_adjudication.py",
                "tests/contracts/test_claim_capability_engine.py",
                "tests/contracts/test_research_remediation_state.py",
                "tests/pr_cards/test_claim_adjudication.py",
            ]
        )
    if args.mode == "collect":
        return _run(common + ["--collect-only"])
    return _run(common + ["-m", "smoke"])


if __name__ == "__main__":
    raise SystemExit(main())
