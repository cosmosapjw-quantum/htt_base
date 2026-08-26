from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.paper import build_planck_mes_first_paper as builder


EXPECTED_FAMILIES = (
    "GENERIC_12",
    "RAW_REDUCED_10",
    "EPS_REDUCED_10",
    "MES_10",
    "ANCHORS_ONLY_2",
    "MORPHOLOGY_ONLY_8",
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, object]:
    return builder.compute_analysis()


@pytest.fixture(scope="module")
def built_package(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    root = tmp_path_factory.mktemp("planck_mes_first_paper")
    output_dir = root / "generated"
    paper_dir = root / "paper"
    result = builder.build_planck_mes_first_paper(
        output_dir=output_dir,
        paper_dir=paper_dir,
    )
    return {
        "result": result,
        "output_dir": output_dir,
        "paper_dir": paper_dir,
    }


def test_primary_mes_rank_replays_as_98_of_301(
    analysis: dict[str, object],
) -> None:
    mes = analysis["families"]["MES_10"]
    assert mes["global_rank"] == {
        "numerator": 98,
        "denominator": 301,
        "fraction": "98/301",
        "reduced_fraction": "14/43",
        "decimal": pytest.approx(98 / 301),
    }


def test_generic_control_replays_as_133_of_301(
    analysis: dict[str, object],
) -> None:
    generic = analysis["families"]["GENERIC_12"]
    assert generic["global_rank"]["numerator"] == 133
    assert generic["global_rank"]["denominator"] == 301
    assert generic["global_rank"]["fraction"] == "133/301"
    assert generic["global_rank"]["reduced_fraction"] == "19/43"
    assert analysis["generic_control_preserved"] is True


def test_all_six_predeclared_families_are_present_and_row_equivariant(
    analysis: dict[str, object],
) -> None:
    assert tuple(analysis["family_order"]) == EXPECTED_FAMILIES
    assert tuple(analysis["families"]) == EXPECTED_FAMILIES
    assert analysis["statistical_operator"]["row_count"] == 301
    for family_id in EXPECTED_FAMILIES:
        family = analysis["families"][family_id]
        assert family["row_permutation_equivariant"] is True
        assert family["tail_policy"] == ["two-sided"] * len(
            family["feature_ids"]
        )


def test_rank_shift_decomposition_is_not_silently_omitted(
    analysis: dict[str, object],
) -> None:
    numerators = {
        family_id: analysis["families"][family_id]["global_rank"]["numerator"]
        for family_id in EXPECTED_FAMILIES
    }
    assert numerators == {
        "GENERIC_12": 133,
        "RAW_REDUCED_10": 110,
        "EPS_REDUCED_10": 109,
        "MES_10": 98,
        "ANCHORS_ONLY_2": 78,
        "MORPHOLOGY_ONLY_8": 88,
    }
    assert (
        analysis["comparison_interpretation"]
        == "DESCRIPTIVE_PAIRED_OPERATOR_SENSITIVITY_NOT_INDEPENDENT_TESTS"
    )


def test_anchor_and_minimum_feature_attribution_is_correct(
    analysis: dict[str, object],
) -> None:
    mes = analysis["families"]["MES_10"]
    local = {
        row["feature_id"]: row["local_rank"]["numerator"]
        for row in mes["features"]
    }
    assert local["mes_sigma_anchor"] == 74
    assert local["mes_omega_anchor"] == 74
    assert local["multipole_l3_absdot_0"] == 16
    assert mes["observed_minimum"]["feature_ids"] == [
        "multipole_l3_absdot_0"
    ]
    assert mes["observed_minimum"]["rank"]["fraction"] == "16/301"
    morphology = analysis["families"]["MORPHOLOGY_ONLY_8"]
    assert morphology["observed_minimum"]["feature_ids"] == [
        "multipole_l3_absdot_0"
    ]
    assert analysis["anchor_dependence"]["correlation_block_rank"] == 2
    assert analysis["anchor_dependence"]["pearson_r"] == pytest.approx(
        0.9948739660934142
    )
    assert analysis["anchor_dependence"]["spearman_rho"] == pytest.approx(
        0.993738311588304
    )


def test_builder_never_opens_raw_map_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[Path] = []
    original_json = builder._read_allowed_json
    original_npz = builder._load_allowed_npz

    def traced_json(path: Path) -> dict[str, object]:
        seen.append(Path(path).resolve())
        return original_json(path)

    def traced_npz(path: Path) -> dict[str, object]:
        seen.append(Path(path).resolve())
        return original_npz(path)

    monkeypatch.setattr(builder, "_read_allowed_json", traced_json)
    monkeypatch.setattr(builder, "_load_allowed_npz", traced_npz)
    builder.build_planck_mes_first_paper(
        output_dir=tmp_path / "generated",
        paper_dir=tmp_path / "paper",
    )
    expected = {
        (builder.REPO_ROOT / relative).resolve()
        for relative in builder.ALLOWED_INPUT_PATHS
    }
    assert set(seen) == expected
    assert all("/raw/" not in path.as_posix() for path in seen)
    with pytest.raises(builder.PaperBuildError, match="map-free input whitelist"):
        builder._read_allowed_json(
            Path("/mnt/sn850x2t/htt_base_e2e/workdir/raw/forbidden.json")
        )


def test_manuscript_numbers_are_loaded_from_analysis_summary(
    analysis: dict[str, object],
) -> None:
    altered = deepcopy(analysis)
    altered["families"]["MES_10"]["global_rank"].update(
        numerator=97,
        fraction="97/301",
        reduced_fraction="97/301",
        decimal=97 / 301,
    )
    altered["families"]["GENERIC_12"]["global_rank"].update(
        numerator=132,
        fraction="132/301",
        reduced_fraction="132/301",
        decimal=132 / 301,
    )
    manuscript = builder.render_manuscript(altered)
    assert r"\frac{97}{301}" in manuscript
    assert r"\frac{132}{301}" in manuscript
    assert r"\frac{98}{301}" not in manuscript
    assert r"\frac{133}{301}" not in manuscript


def test_forbidden_claims_are_absent(
    built_package: dict[str, object],
) -> None:
    manuscript = (built_package["paper_dir"] / "main.tex").read_text(
        encoding="utf-8"
    )
    references = (built_package["paper_dir"] / "references.bib").read_text(
        encoding="utf-8"
    )
    lowered = manuscript.lower()
    for forbidden in builder.FORBIDDEN_CLAIM_STRINGS:
        assert forbidden.lower() not in lowered
    assert "TO_BE_COMPUTED" not in manuscript
    assert "TO_BE_GENERATED" not in manuscript
    assert builder.MES_SIGMA_TEX == r"\Sigma^2_{\max}"
    assert builder.MES_OMEGA_TEX == r"W^2_{\max}"
    assert r"\Sigma^2_{\max}" in manuscript
    assert r"W^2_{\max}" in manuscript
    assert r"\Sigma_{2,\max}" not in manuscript
    assert r"W_{2,\max}" not in manuscript
    assert "squared normalized MES ceiling coordinates" in manuscript
    assert "jointly exchangeable under the null" in manuscript
    assert "super-uniform" in manuscript
    assert "exact empirical ranks relative to the frozen pool" in manuscript
    assert "unconditional Type-I-error calibration" in manuscript
    assert r"\mathcal P=\frac{C_2+C_4}{C_3+C_5}" in manuscript
    assert r"G_\ell=\lambda_{\ell,3}-\lambda_{\ell,2}" in manuscript
    assert (
        r"d_2=\left|\boldsymbol v_{2,1}\!\cdot\!\boldsymbol v_{2,2}\right|"
        in manuscript
    )
    assert "Majorana polynomial" in manuscript
    assert "SAG observer-motion" in manuscript
    assert "premise-dependent derivative hierarchy" in manuscript
    assert (
        "The observation-row minimum is morphology-driven rather than "
        "anchor-driven."
    ) in manuscript
    assert (
        "The full family rank nevertheless remains coordinate-family dependent"
        in manuscript
    )
    assert (
        "The result is therefore morphology-driven rather than anchor-driven"
        not in manuscript
    )
    assert "nonidentified" in manuscript
    for citation_key in (
        "BarberRamdas2026",
        "CopiHutererStarkman2004",
        "Weeks2004",
        "AluriRalstonWeltman2017",
        "Planck2018IV",
    ):
        assert f"{{{citation_key}," in references


def test_required_tables_figures_and_summary_are_generated(
    built_package: dict[str, object],
) -> None:
    output_dir = built_package["output_dir"]
    paper_dir = built_package["paper_dir"]
    for filename in builder.REQUIRED_ANALYSIS_OUTPUTS:
        path = output_dir / filename
        assert path.is_file() and path.stat().st_size > 0
        if path.suffix == ".pdf":
            assert path.read_bytes().startswith(b"%PDF")
    summary = json.loads(
        (output_dir / "analysis_summary.json").read_text(encoding="utf-8")
    )
    assert tuple(summary["family_order"]) == EXPECTED_FAMILIES
    assert (paper_dir / "main.tex").is_file()
    assert (paper_dir / "references.bib").is_file()
