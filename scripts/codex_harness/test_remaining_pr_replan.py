"""Audit regressions against the real DAG and mirror validators (no stubs)."""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.codex_harness import validate_remaining_pr_replan as validator


def _crosswalk(monkeypatch, tmp_path: Path, mutate) -> None:
    with validator.CROSSWALK.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    mutate(rows)
    path = tmp_path / "crosswalk.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    monkeypatch.setattr(validator, "CROSSWALK", path)


def test_current_repository_passes() -> None:
    result = validator.validate()
    assert result["baseline_crosswalk_cards"] == 55
    assert result["planning_families"] == 11


def test_rejects_completed_baseline_substitution(monkeypatch, tmp_path) -> None:
    def substitute(rows):
        row = next(r for r in rows if r["original_id"] == "PR-204")
        row.update(original_id="PR-000", canonical_status="completed", successor_nodes="PR-000")

    _crosswalk(monkeypatch, tmp_path, substitute)
    with pytest.raises(ValueError, match="frozen baseline identity mismatch"):
        validator.validate()


def test_rejects_duplicate_planning_family(monkeypatch, tmp_path) -> None:
    def duplicate(rows):
        rows.append(next(r.copy() for r in rows if r["record_type"] == "planning_family"))

    _crosswalk(monkeypatch, tmp_path, duplicate)
    with pytest.raises(ValueError, match="duplicate planning.family"):
        validator.validate()


def test_rejects_missing_baseline_card(monkeypatch, tmp_path) -> None:
    _crosswalk(monkeypatch, tmp_path, lambda rows: rows.remove(
        next(r for r in rows if r["original_id"] == "PR-190")
    ))
    with pytest.raises(ValueError):
        validator.validate()


def test_rejects_duplicate_canonical_card(monkeypatch, tmp_path) -> None:
    _crosswalk(monkeypatch, tmp_path, lambda rows: rows.append(
        next(r.copy() for r in rows if r["record_type"] == "canonical_card")
    ))
    with pytest.raises(ValueError, match="duplicate canonical"):
        validator.validate()


def test_baseline_record_matches_historical_commit() -> None:
    # The regression oracle reads the historical Git object, never the crosswalk.
    commit = "85e261f49c9df9389946eef74d80c1ccd0509816"
    path = "docs/codex_handoff/pr_status.yaml"
    raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=validator.REPO)
    status = validator._status_map(yaml.safe_load(raw))
    expected = {key for key, state in status.items() if state != "completed"}
    record = validator.FROZEN_BASELINE
    assert record["commit"] == commit
    assert record["status_path"] == path
    assert record["status_blob"] == subprocess.check_output(
        ["git", "hash-object", "--stdin"], input=raw, cwd=validator.REPO
    ).decode().strip()
    assert len(record["ids"]) == len(set(record["ids"])) == 55
    assert set(record["ids"]) == expected


def test_baseline_order_is_not_identity(monkeypatch, tmp_path) -> None:
    _crosswalk(monkeypatch, tmp_path, lambda rows: rows.reverse())
    assert validator.validate()["baseline_crosswalk_cards"] == 55


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-p", "no:cacheprovider", "-q", __file__]))
