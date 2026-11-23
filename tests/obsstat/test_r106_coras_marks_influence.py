"""R106 CORAS mark-score influence helpers: component layout, fold recording, influence and subset statistics."""
import numpy as np
import pytest

from scripts.r105 import cf4_coras_marks as cm
from scripts.r106 import coras_marks_influence as mi


def _r105_masks(n_draws):
    """Independent replica of the tag/mask construction in cf4_coras_marks.score."""
    offsets = np.array(mi.OFFSETS_KMS)
    residuals = [f"residual_{i}.tsv" for i in range(1, n_draws + 1)]
    tags = [("zero", 0.), ("nn", 0.)] + [(name, u) for name in ["mean.tsv", *residuals] for u in offsets]
    name, u = np.array([t[0] for t in tags]), np.array([t[1] for t in tags])
    draw = np.isin(name, residuals)
    masks = dict(zero=name == "zero", nn=name == "nn", coras_mean=(name == "mean.tsv") & (u == 0),
                 coras_mean_offset=name == "mean.tsv", coras_draws=draw & (u == 0), coras_draws_offset=draw)
    for half, subset in enumerate(np.array_split(residuals, 2)):
        masks[f"coras_half{half + 1}_offset"] = np.isin(name, subset)
    return masks


def test_component_layout_matches_r105_masks():
    n = 6
    ours = mi.r105_choice_indices(n)
    for key, mask in _r105_masks(n).items():
        assert np.array_equal(np.flatnonzero(mask), np.sort(ours[key])), key
    assert mi.draw_components([0, 1], (mi.U0,)).tolist() == [9, 14]


def test_recorder_captures_each_fold_once_and_restores():
    original = cm.fold_score
    a, b = np.random.default_rng(1).normal(size=(2, 7, 3)).tolist()
    with mi.recorded_fold_summaries() as rec:
        for summ in (a, b):
            for which in (np.array([0]), np.array([1, 2])):
                cm.fold_score(summ, which)
    assert cm.fold_score is original and len(rec) == 2
    assert np.array_equal(rec[1][1], np.asarray(b))
    with pytest.raises(RuntimeError):
        with mi.recorded_fold_summaries():
            raise RuntimeError
    assert cm.fold_score is original


def _synthetic(n_draws=10, dominant=3, seed=0):
    rng = np.random.default_rng(seed)
    n_comp = mi.N_FIXED + len(mi.OFFSETS_KMS) * (n_draws + 1)
    summaries = []
    for _ in range(4):
        s = rng.normal(scale=0.3, size=(n_comp, 3))
        idx = mi.draw_components([dominant], range(len(mi.OFFSETS_KMS)))
        s[idx, 0] += 6.0  # dominant training weight
        s[idx, 1] += 4.0  # and better held-out likelihood
        summaries.append(s)
    return mi.Scorer(summaries, ["pgc", "pgc", "pgc1", "pgc1"])


def test_scorer_total_is_sum_of_fold_differences():
    sc = _synthetic()
    idx = mi.draw_components(range(10), (mi.U0,))
    direct = [cm.fold_score(s, idx)["logscore"] - cm.fold_score(s, np.array([0]))["logscore"] for s in sc.summaries]
    tot = sc.total(idx)
    assert tot["pgc"] == pytest.approx(direct[0] + direct[1]) and tot["pgc1"] == pytest.approx(direct[2] + direct[3])


def test_variant_report_flags_single_draw_dominance():
    sc = _synthetic()
    seeds = list(range(101, 111))
    offsets = mi.VARIANTS["coras_draws_offset"]
    recorded = {k: {"coras_mean_offset": v} for k, v in sc.total(mi.mean_components(offsets)).items()}
    rngs = {k: np.random.default_rng(v) for k, v in mi.RNG_SEEDS.items()}
    rep = mi.variant_report(sc, recorded, seeds, offsets, "coras_mean_offset", [104], 20, 20, rngs)
    for k in ("pgc", "pgc1"):
        top = rep["top_influence"][k]
        assert top["seed"] == 104 and top["single_draw_rank"] == 1
        assert top["influence"] == pytest.approx(rep["full"][k] - top["score_without"])
        assert len(rep["leave_one_draw_out"]["influence_full_minus_without"][k]) == 10
        assert rep["named_exclusions"]["104"]["score_without"][k] == pytest.approx(top["score_without"])
        assert rep["halves"][k]["fixed_split_r105_seeds"]["half1_seeds"] == [101, 105]
        assert rep["random_subsets"]["by_n"]["n8"][k]["sd"] >= 0
        assert rep["draw_count_convergence"]["converged"][k] is False
    weights = mi.training_weights(sc, 10, offsets, seeds, 104)
    assert all(w["top_draw_seed"] == 104 and w["seed_of_interest_rank"] == 1 for w in weights)
    text = " ".join(mi.variant_statement("coras_draws_offset", rep))
    assert "seed 104" in text and "Not converged" in text
