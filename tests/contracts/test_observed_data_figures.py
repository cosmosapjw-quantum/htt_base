from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_observational_inventory_finds_obs_bundle_and_compact_desi() -> None:
    module = _load_script("inventory_observational_data")
    payload = module.build_inventory(REPO_ROOT, command="test")
    rows = {row["dataset_id"]: row for row in payload["rows"]}

    assert payload["summary"]["present"] > 30
    assert "planck.pr3.tt_full" in rows
    assert rows["planck.pr3.tt_full"]["present"] is True
    assert rows["planck.pr3.tt_full"]["claim_ceiling"] == "diagnostic_only"
    assert "compact.desi.bgs_any_ngc" in rows
    assert rows["compact.desi.bgs_any_ngc"]["schema"]["row_count_hint"] == 4081227
    assert "compact.cf4.query_batch" in rows
    assert rows["compact.cf4.query_batch"]["schema"]["row_count_hint"] == 163760
    assert rows["act.dr6.tt"]["present"] is False
    assert rows["act.dr6.tt"]["claim_ceiling"] == "blocked"


def test_observed_figure_specs_are_claim_gated_and_repo_local() -> None:
    module = _load_script("make_observed_data_manuscript_figures")
    specs = module._figure_specs()

    assert len(specs) >= 10
    names = {spec.file_name for spec in specs}
    assert "fig_observed_desi_footprint_depth.png" in names
    assert "fig_observed_cf4_velocity_density.png" in names
    assert "fig_observed_longrun_jackknife_bootstrap.png" in names
    captions = "\n".join(spec.caption for spec in specs).lower()
    forbidden = [
        "family identified",
        "geometry detected",
        "external transfer validated as native",
        "mio posterior",
        "truth certificate",
        "native low-ell solver output is used",
    ]
    for phrase in forbidden:
        assert phrase not in captions
    combined_claim_text = "\n".join(
        item for spec in specs for item in (spec.caption, *spec.caveats)
    )
    assert "Bianchi family identification" not in combined_claim_text

    for spec in specs:
        assert spec.owner == "OBSSTAT"
        assert spec.implementation_scope == "obsstat"
        assert spec.artifact_id.startswith("obsstat.observed.")
        assert spec.claim_tier == "diagnostic_only"
        assert spec.source_paths
        assert spec.snippet.startswith("observed_figures_")
        for rel_path in spec.source_paths:
            if rel_path.startswith("docs/generated/"):
                continue
            assert (REPO_ROOT / rel_path).exists(), rel_path
