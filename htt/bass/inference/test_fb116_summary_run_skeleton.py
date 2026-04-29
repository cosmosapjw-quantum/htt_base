from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from bass.background.bianchi_types import ALL_BIANCHI_TYPES
from bass.inference.__main__ import main

pytestmark = pytest.mark.slow


def _tmp_config(repo_root: Path, tmp_path: Path) -> Path:
    base = yaml.safe_load((repo_root / "configs/fb11_summary.yaml").read_text(encoding="utf-8"))
    base["outputs"] = {
        "summary_json": str(tmp_path / "fb11_summary_table.json"),
        "summary_markdown": str(tmp_path / "fb11_summary_table.md"),
        "posterior_dir": str(tmp_path / "posteriors"),
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(base, sort_keys=False), encoding="utf-8")
    return path


def test_fb116_summary_config_exists_and_keeps_type_order() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    config = yaml.safe_load((repo_root / "configs/fb11_summary.yaml").read_text(encoding="utf-8"))
    assert tuple(config["models"]["type_labels"]) == tuple(ALL_BIANCHI_TYPES)


def test_fb116_summary_run_is_byte_identical_at_seed_42(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    config_path = _tmp_config(repo_root, tmp_path)
    assert main(["--config", str(config_path), "--seed", "42"]) == 0
    json_path = tmp_path / "fb11_summary_table.json"
    first = json_path.read_bytes()
    assert main(["--config", str(config_path), "--seed", "42"]) == 0
    second = json_path.read_bytes()
    assert first == second


def test_fb116_summary_outputs_exist(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    config_path = _tmp_config(repo_root, tmp_path)
    assert main(["--config", str(config_path), "--seed", "42"]) == 0
    assert (tmp_path / "fb11_summary_table.json").exists()
    assert (tmp_path / "fb11_summary_table.md").exists()
    assert (tmp_path / "bayes_factor_summary.json").exists()


def test_fb116_summary_json_has_one_row_per_bianchi_type(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    config_path = _tmp_config(repo_root, tmp_path)
    assert main(["--config", str(config_path), "--seed", "42"]) == 0
    payload = json.loads((tmp_path / "fb11_summary_table.json").read_text(encoding="utf-8"))
    assert [row["type"] for row in payload["rows"]] == list(ALL_BIANCHI_TYPES)


def test_fb116_summary_truth_ix_gives_positive_ix_ln_b(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    config_path = _tmp_config(repo_root, tmp_path)
    assert main(["--config", str(config_path), "--seed", "42"]) == 0
    payload = json.loads((tmp_path / "fb11_summary_table.json").read_text(encoding="utf-8"))
    ix_row = next(row for row in payload["rows"] if row["type"] == "IX")
    assert ix_row["ln_B"] > 0.0
    assert ix_row["converged"] is True
