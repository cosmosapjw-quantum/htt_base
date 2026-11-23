"""Draw-level influence and Monte Carlo spread of the 6dFGSv CORAS mark scores (CF4_MARKS128).

scripts/r105/cf4_coras_marks.score runs unchanged.  Its per-fold sufficient
statistics (log J_train, log J_test, log D_test for every mixture component) are
recorded where they enter cf4_coras_marks.fold_score.  Every subset score below is
cf4_coras_marks.fold_score on a component subset, minus the zero-flow score, summed
over the five group folds of each catalogue key.

Component layout fixed by score(): [zero, nn, mean.tsv x offsets, residual_s x offsets
for each seed], offsets (-300, -100, 0, 100, 300) km/s.  The layout is checked by
reproducing every recorded R105 choice, fold by fold, and the recorded sums in the
CF4_MARKS128 output; an optional 8-draw run is checked against the first eight draws.

For each coras_draws* score (u=0 draws and offset-marginalised draws) this reports:
leave-one-draw-out influence, the score without the most influential draw and
without named seeds, single-draw scores, random-subset Monte Carlo mean/SD versus n
(with and without the most influential draw), the SD over random disjoint halves next
to the fixed R105 half split, and training-weight concentration per fold.

Claim class: Monte Carlo convergence in the number of CORAS draws of a conditional
predictive score (fixed CF3-calibrated growth and bulk, fitted selection per fold).
No physical attribution and no calibrated p.  Draws named for exclusion are
diagnostics only: the reported score keeps every draw.
"""
from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import scipy

from scripts.r105 import cf4_coras_marks as cm
from scripts.r105 import coras_reduce as cr
from scripts.r106.coras_stability import analysis_command, quantiles, sha256_file, write_json

SCHEMA = "htt.r106.cf4_marks_influence/1"
OFFSETS_KMS = (-300., -100., 0., 100., 300.)
U0 = OFFSETS_KMS.index(0.)
N_FIXED = 2  # zero-flow and 2MRS NeuralNet components precede the CORAS blocks
VARIANTS = {"coras_draws": (U0,), "coras_draws_offset": tuple(range(len(OFFSETS_KMS)))}
MEAN_CHOICE = {"coras_draws": "coras_mean", "coras_draws_offset": "coras_mean_offset"}
SUBSET_SIZES = (8, 16, 32, 64, 96)
SUBSET_SIZES_WITHOUT_TOP = (8, 32, 64)
CONVERGENCE_TOLERANCE_NATS = 0.5
RNG_SEEDS = dict(subsets=10611, subsets_without_top=10612, disjoint_halves=10613)


@contextmanager
def recorded_fold_summaries():
    """Record the (components, 3) array of every fold as cf4_coras_marks.score passes it to fold_score."""
    records = []
    original = cm.fold_score

    def recorder(summaries, which):
        if not records or records[-1][0] is not summaries:
            records.append((summaries, np.array(summaries, dtype=float)))
        return original(summaries, which)

    cm.fold_score = recorder
    try:
        yield records
    finally:
        cm.fold_score = original


def draw_components(positions, offsets, n_offsets=len(OFFSETS_KMS)):
    """Component indices of the residual draws at 0-based positions, for the given offset positions."""
    return np.array([N_FIXED + n_offsets * (1 + i) + o for i in positions for o in offsets], dtype=int)


def mean_components(offsets):
    return np.array([N_FIXED + o for o in offsets], dtype=int)


class Scorer:
    """Sum over folds of fold_score(subset) - fold_score(zero) per catalogue key."""

    def __init__(self, summaries, keys):
        self.summaries = [np.asarray(s, float) for s in summaries]
        self.keys = list(keys)
        self.zero = [cm.fold_score(s, np.array([0]))["logscore"] for s in self.summaries]

    def per_fold(self, idx):
        return [cm.fold_score(s, idx)["logscore"] - z for s, z in zip(self.summaries, self.zero)]

    def total(self, idx):
        out = {}
        for k, v in zip(self.keys, self.per_fold(idx)):
            out[k] = out.get(k, 0.) + v
        return out


def r105_choice_indices(n_draws):
    """Component subsets of the recorded R105 choices (cf4_coras_marks.score), as index arrays."""
    every = range(len(OFFSETS_KMS))
    choices = {"zero": np.array([0]), "nn": np.array([1]), "coras_mean": mean_components((U0,)),
               "coras_mean_offset": mean_components(every),
               "coras_draws": draw_components(range(n_draws), (U0,)),
               "coras_draws_offset": draw_components(range(n_draws), every)}
    if n_draws >= 4:
        for h, part in enumerate(np.array_split(np.arange(n_draws), 2)):
            choices[f"coras_half{h + 1}_offset"] = draw_components(part, every)
    return choices


def verify_layout(scorer, result, n_draws, tol=1e-9):
    """Every recorded R105 per-fold choice must be reproduced from the recorded summaries."""
    worst = 0.
    choices = r105_choice_indices(n_draws)
    rows = [r for k in result["folds"] for r in result["folds"][k]]
    if len(rows) != len(scorer.summaries):
        raise ValueError("recorded fold summaries do not match the R105 folds")
    for name, idx in choices.items():
        for row, v in zip(rows, scorer.per_fold(idx)):
            worst = max(worst, abs(v - row["shared_minus_zero"][name]))
    if worst > tol:
        raise ValueError(f"component layout not reproduced (max |diff| {worst:.3g})")
    return worst


def summary(values):
    v = np.asarray(values, float)
    q = quantiles(v)
    return dict(mean=float(v.mean()), sd=float(v.std(ddof=1)) if len(v) > 1 else 0., q05=q[0], q50=q[1], q95=q[2])


def subset_mc(scorer, pool, sizes, offsets, reps, rng, reference=None):
    """Random subsets without replacement from pool; optional per-key reference gives the fraction at or below it."""
    out = {}
    for n in (m for m in sizes if m < len(pool)):
        vals = {}
        for _ in range(reps):
            t = scorer.total(draw_components(rng.choice(pool, n, replace=False), offsets))
            for k, v in t.items():
                vals.setdefault(k, []).append(v)
        out[f"n{n}"] = {k: dict(**summary(v), **({} if reference is None else
                                                 {"fraction_le_first8_score": float(np.mean(np.asarray(v) <= reference[k]))}))
                        for k, v in vals.items()}
    return out


def training_weights(scorer, n_draws, offsets, seeds, seed_of_interest):
    """Per-fold effective components and per-draw training weight (summed over offsets) of the full mixture."""
    idx = draw_components(range(n_draws), offsets)
    rows = []
    for k, s in zip(scorer.keys, scorer.summaries):
        lt = s[idx, 0]
        logw = lt - np.logaddexp.reduce(lt)
        w = np.exp(logw).reshape(n_draws, len(offsets)).sum(1)
        order = np.argsort(-w)
        pos = seeds.index(seed_of_interest)
        rows.append(dict(key=k, effective_training_components=float(np.exp(-np.logaddexp.reduce(2 * logw))),
                         top_draw_seed=seeds[int(order[0])], top_draw_weight=float(w[order[0]]),
                         second_draw_weight=float(w[order[1]]), seed_of_interest_weight=float(w[pos]),
                         seed_of_interest_rank=int(np.flatnonzero(order == pos)[0]) + 1))
    return rows


def variant_report(scorer, recorded, seeds, offsets, mean_name, named, reps, halves_reps, rngs):
    n = len(seeds)
    keys = sorted(set(scorer.keys), key=scorer.keys.index)
    everything = list(range(n))
    full = scorer.total(draw_components(everything, offsets))
    mean_score = {k: recorded[k][mean_name] for k in keys}
    loo = {k: [] for k in keys}
    for i in everything:
        t = scorer.total(draw_components([j for j in everything if j != i], offsets))
        for k in keys:
            loo[k].append(full[k] - t[k])
    single = {k: [] for k in keys}
    for i in everything:
        t = scorer.total(draw_components([i], offsets))
        for k in keys:
            single[k].append(t[k])
    top = {}
    for k in keys:
        i = int(np.argmax(loo[k]))
        without = full[k] - loo[k][i]
        excess = full[k] - mean_score[k]
        top[k] = dict(seed=seeds[i], seed_position=i, influence=float(loo[k][i]), score_without=float(without),
                      score_alone=float(single[k][i]),
                      single_draw_rank=int(np.flatnonzero(np.argsort(-np.asarray(single[k])) == i)[0]) + 1,
                      excess_over_mean_choice=float(excess),
                      fraction_of_excess_carried=float(loo[k][i] / excess) if excess > 0 else None,
                      next_largest_influence=float(np.sort(loo[k])[-2]),
                      next_largest_abs_influence=float(np.max(np.abs(np.delete(np.asarray(loo[k]), i)))),
                      next_largest_abs_influence_seed=seeds[int(np.argmax(np.abs(np.where(np.arange(len(loo[k])) == i, 0.0, np.asarray(loo[k])))))])
    named_out = {}
    for s in named:
        if s not in seeds:
            raise ValueError(f"named seed {s} not in the run")
        i = seeds.index(s)
        rest = [j for j in everything if j != i]
        named_out[str(s)] = dict(
            score_without=scorer.total(draw_components(rest, offsets)),
            score_alone=scorer.total(draw_components([i], offsets)),
            single_draw_rank={k: int(np.flatnonzero(np.argsort(-np.asarray(single[k])) == i)[0]) + 1 for k in keys},
            leave_one_out_influence={k: float(loo[k][i]) for k in keys})
    first8 = scorer.total(draw_components(range(min(8, n)), offsets))
    top_seed_by_key = {k: top[k]["seed"] for k in keys}
    pool_ex = {k: np.array([j for j in everything if seeds[j] != top_seed_by_key[k]]) for k in keys}
    mc = subset_mc(scorer, np.arange(n), SUBSET_SIZES, offsets, reps, rngs["subsets"], reference=first8)
    mc_ex = {}
    for k in keys:
        sub = subset_mc(scorer, pool_ex[k], SUBSET_SIZES_WITHOUT_TOP, offsets, reps, rngs["subsets_without_top"])
        mc_ex[k] = {size: v[k] for size, v in sub.items()}
        mc_ex[k][f"n{n - 1}_all_remaining"] = top[k]["score_without"]
    a, b = np.array_split(np.arange(n), 2)
    fixed = {h: scorer.total(draw_components(part, offsets)) for h, part in (("half1", a), ("half2", b))}
    diffs, halfscores = {k: [] for k in keys}, {k: [] for k in keys}
    rng = rngs["disjoint_halves"]
    for _ in range(halves_reps):
        p = rng.permutation(n)
        x = scorer.total(draw_components(p[: n // 2], offsets))
        y = scorer.total(draw_components(p[n // 2:], offsets))
        for k in keys:
            diffs[k].append(x[k] - y[k])
            halfscores[k].extend((x[k], y[k]))
    halves = {}
    for k in keys:
        d = np.asarray(diffs[k])
        obs = fixed["half1"][k] - fixed["half2"][k]
        pos = top[k]["seed_position"]
        moved_a = [j for j in a if j != pos] if pos in a else [*a, pos]
        moved_b = [j for j in b if j != pos] if pos in b else [*b, pos]
        halves[k] = dict(fixed_split_r105_seeds=dict(half1_seeds=[seeds[a[0]], seeds[a[-1]]],
                                               half2_seeds=[seeds[b[0]], seeds[b[-1]]],
                                               half1=fixed["half1"][k], half2=fixed["half2"][k], difference=obs,
                                               top_draw_seed=top[k]["seed"], top_draw_in_half=1 if pos in a else 2,
                                               half1_with_top_draw_moved=scorer.total(draw_components(moved_a, offsets))[k],
                                               half2_with_top_draw_moved=scorer.total(draw_components(moved_b, offsets))[k]),
                         random_disjoint_halves=dict(reps=halves_reps, half_score=summary(halfscores[k]),
                                                     difference_sd=float(d.std(ddof=1)),
                                                     abs_difference_q50_q95=[float(v) for v in np.quantile(np.abs(d), [.5, .95])],
                                                     fraction_abs_difference_ge_fixed=float(np.mean(np.abs(d) >= abs(obs)))))
    max_abs_influence = {k: float(np.max(np.abs(loo[k]))) for k in keys}
    converged = {k: bool(halves[k]["random_disjoint_halves"]["difference_sd"] < CONVERGENCE_TOLERANCE_NATS
                         and max_abs_influence[k] < CONVERGENCE_TOLERANCE_NATS) for k in keys}
    return dict(
        n_draws=n, full=full, mean_choice=mean_name, mean_choice_score=mean_score, first8=first8,
        leave_one_draw_out=dict(influence_full_minus_without={k: [float(v) for v in loo[k]] for k in keys},
                                top5={k: [[seeds[int(i)], float(loo[k][i])] for i in np.argsort(-np.asarray(loo[k]))[:5]]
                                      for k in keys},
                                max_abs_influence=max_abs_influence),
        top_influence=top, named_exclusions=named_out,
        single_draw={k: dict(**summary(single[k]), max=float(np.max(single[k])),
                             max_seed=seeds[int(np.argmax(single[k]))]) for k in keys},
        random_subsets=dict(reps=reps, by_n=mc),
        random_subsets_without_top_influence_draw={k: dict(seed_removed=top_seed_by_key[k], reps=reps, by_n=mc_ex[k])
                                                   for k in keys},
        halves=halves,
        draw_count_convergence=dict(tolerance_nats=CONVERGENCE_TOLERANCE_NATS,
                                    criterion="random-disjoint-half difference SD and max |leave-one-out influence| "
                                              "both below tolerance",
                                    converged=converged))


def variant_statement(name, rep):
    lines = []
    for k, t in rep["top_influence"].items():
        frac = t["fraction_of_excess_carried"]
        dominated = frac is not None and frac >= 0.5
        h = rep["halves"][k]
        n8 = rep["random_subsets"]["by_n"].get("n8", {}).get(k)
        line = (f"{name} [{k}]: {rep['n_draws']}-draw score {rep['full'][k]:.2f} versus {rep['mean_choice']} "
                f"{rep['mean_choice_score'][k]:.2f} and first-8 {rep['first8'][k]:.2f}"
                + (f" (at the {n8['fraction_le_first8_score']:.0%} point of random 8-draw subsets, mean {n8['mean']:.2f}, "
                   f"SD {n8['sd']:.2f})" if n8 else "") +
                f". Largest leave-one-out influence: seed {t['seed']} ({t['influence']:.2f} nats; largest |influence| of the "
                f"other draws {t['next_largest_abs_influence']:.3g}, seed {t['next_largest_abs_influence_seed']}); without it {t['score_without']:.2f}; alone {t['score_alone']:.2f} "
                f"(single-draw rank {t['single_draw_rank']}). ")
        if dominated:
            line += (f"Seed {t['seed']} carries {frac:.0%} of the excess over {rep['mean_choice']}: the {rep['n_draws']}-draw "
                     f"value is dominated by one draw. ")
            if t["seed_position"] >= 8:
                line += (f"First-8 to {rep['n_draws']} change {rep['full'][k] - rep['first8'][k]:+.2f}, of which "
                         f"{t['score_without'] - rep['first8'][k]:+.2f} remains without seed {t['seed']}: not a "
                         "realization-count gain. ")
        else:
            trend = ", ".join(f"{size}: {v[k]['mean']:.2f}" for size, v in rep["random_subsets"]["by_n"].items())
            line += ("No single draw carries most of the excess; the change with n follows the random-subset trend "
                     f"(subset means {trend}). ")
        fx = h["fixed_split_r105_seeds"]
        line += (f"Fixed seed halves {fx['half1_seeds'][0]}-{fx['half1_seeds'][1]}/{fx['half2_seeds'][0]}-"
                 f"{fx['half2_seeds'][1]}: {fx['half1']:.2f}/{fx['half2']:.2f}; moving seed {fx['top_draw_seed']} to the "
                 f"other half gives {fx['half1_with_top_draw_moved']:.2f}/{fx['half2_with_top_draw_moved']:.2f}. Random "
                 f"disjoint halves differ with SD {h['random_disjoint_halves']['difference_sd']:.2f} nats. ")
        line += ("Not converged in the number of draws." if not rep["draw_count_convergence"]["converged"][k]
                 else "Within the declared draw-count tolerance.")
        lines.append(line)
    return lines


def residual_rms(directory, seeds):
    """RMS of each residual draw over the 6dFGSv sites (km/s), digest-checked against run.json."""
    geom = cm.site_geometry()[0]
    rec, *_ = cr.metadata(directory, geom)
    out = []
    for s in seeds:
        f = directory / f"residual_{s}.tsv"
        if cr._sha(f) != rec["output_sha256"][f.name]:
            raise ValueError(f"field hash mismatch: {f}")
        out.append(float(np.sqrt(np.mean(cr.read_radial(f, geom["ids"]) ** 2))))
    return out


def first8_check(run, run8, marks8, scorer, seeds):
    """The 8-draw run must hold the same field bytes as the first eight draws here and reproduce its scores."""
    rec = json.loads((run / "run.json").read_text())["output_sha256"]
    rec8 = json.loads((run8 / "run.json").read_text())["output_sha256"]
    same = all(rec.get(k) == v for k, v in rec8.items())
    m8 = json.loads(marks8.read_text())
    n8 = len(m8["seed_ids"])
    if m8["seed_ids"] != seeds[:n8]:
        raise ValueError("8-draw run seeds are not the first seeds of the main run")
    worst = 0.
    for name, idx in r105_choice_indices(n8).items():
        t = scorer.total(idx)
        for k in t:
            worst = max(worst, abs(t[k] - m8["sum_heldout_shared_minus_zero"][k][name]))
    return dict(run8_run_json_sha256=cr._sha(run8 / "run.json"), marks8_sha256=sha256_file(marks8),
                field_bytes_identical_to_first_draws=same, n_draws=n8, max_abs_score_difference=worst,
                reproduced=bool(same and worst < 1e-9))


REVIEW_CORRECTIONS = [
    dict(id="F1", change="New output. Every coras_draws* score in CF4_MARKS128 gets leave-one-draw-out influence, the "
                         "score without the most influential draw and without named seeds, single-draw scores, a "
                         "random-subset Monte Carlo mean/SD versus n (with and without the most influential draw) and "
                         "the SD over random disjoint halves next to the fixed R105 half split; the u=0 and offset "
                         "scores are judged separately; statements are generated from these numbers."),
]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", type=Path, required=True, help="CORAS 6dFGSv field run (marks128)")
    p.add_argument("--reference", type=Path, required=True, help="R105 CF4_FIELD_HOLDOUT.json")
    p.add_argument("--marks", type=Path, required=True, help="recorded cf4_coras_marks output for --run")
    p.add_argument("--run8", type=Path, help="8-draw field run to check against the first draws")
    p.add_argument("--marks8", type=Path, help="recorded cf4_coras_marks output for --run8")
    p.add_argument("--exclude-seed", type=int, nargs="*", default=[], help="named seeds for diagnostic exclusion")
    p.add_argument("--reps", type=int, default=400)
    p.add_argument("--halves-reps", type=int, default=1000)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--supersede", action="store_true")
    a = p.parse_args(argv)
    with recorded_fold_summaries() as records:
        result = cm.score(a.run, a.reference)
    seeds = list(result["seed_ids"])
    keys = [k for k in result["folds"] for _ in result["folds"][k]]
    scorer = Scorer([r[1] for r in records], keys)
    n = len(seeds)
    if scorer.summaries[0].shape[0] != N_FIXED + len(OFFSETS_KMS) * (n + 1):
        raise ValueError("unexpected number of mixture components")
    worst_fold = verify_layout(scorer, result, n)
    recorded = json.loads(a.marks.read_text())
    if recorded["coras_run_sha256"] != result["coras_run_sha256"] or recorded["seed_ids"] != seeds:
        raise ValueError("--marks was not produced from --run")
    worst_sum = max(abs(result["sum_heldout_shared_minus_zero"][k][c] - recorded["sum_heldout_shared_minus_zero"][k][c])
                    for k in recorded["sum_heldout_shared_minus_zero"] for c in recorded["sum_heldout_shared_minus_zero"][k])
    if worst_sum > 1e-9:
        raise ValueError(f"rescored sums differ from --marks ({worst_sum:.3g})")
    sums = result["sum_heldout_shared_minus_zero"]
    variants = {}
    for name, offsets in VARIANTS.items():
        rngs = {k: np.random.default_rng(v) for k, v in RNG_SEEDS.items()}
        variants[name] = variant_report(scorer, sums, seeds, offsets, MEAN_CHOICE[name], a.exclude_seed,
                                        a.reps, a.halves_reps, rngs)
        variants[name]["statement"] = variant_statement(name, variants[name])
    top_seeds = sorted({t["seed"] for v in variants.values() for t in v["top_influence"].values()} | set(a.exclude_seed))
    rms = residual_rms(a.run, seeds)
    order = np.argsort(np.argsort(-np.asarray(rms)))
    rms_out = dict(median_kms=float(np.median(rms)), min_kms=float(np.min(rms)), max_kms=float(np.max(rms)),
                   seeds={str(s): dict(rms_kms=rms[seeds.index(s)], rank_descending=int(order[seeds.index(s)]) + 1)
                          for s in top_seeds})
    weights = {}
    for name, offsets in VARIANTS.items():
        focus = variants[name]["top_influence"][keys[0]]["seed"]
        weights[name] = dict(seed_of_interest=focus, folds=training_weights(scorer, n, offsets, seeds, focus))
    out = dict(schema=SCHEMA,
               inputs=dict(run=dict(directory=str(a.run.resolve()), run_json_sha256=cr._sha(a.run / "run.json"),
                                    seed_range=[seeds[0], seeds[-1]], n_draws=n,
                                    mean_sha256=result["mean_sha256"]),
                           reference=dict(path=str(a.reference), sha256=sha256_file(a.reference)),
                           marks=dict(path=str(a.marks.resolve()), sha256=sha256_file(a.marks)),
                           nn_sha256=result["nn_sha256"], catalogue=result["catalogue"], runs_config=result["runs_config"]),
               reproduction=dict(max_abs_per_fold_difference=worst_fold, max_abs_sum_difference_vs_marks=worst_sum,
                                 recorded_sums=sums),
               component_layout=dict(fixed=["zero", "nn"], offsets_kms=list(OFFSETS_KMS),
                                     blocks=["mean.tsv", *(f"residual_{s}.tsv" for s in seeds)]),
               variants=variants, training_weight_concentration=weights, residual_rms_6dfgsv_sites=rms_out,
               claim_class="Monte Carlo convergence in the number of CORAS draws of a conditional predictive score; "
                           "no physical attribution",
               scope=result["scope"], physical_Pi=None, calibrated_p=None,
               note="Seeds named or removed here are diagnostics; the reported score keeps every draw. More draws, "
                    "not exclusion, are the remedy for a non-converged mixture.")
    if a.run8 is not None and a.marks8 is not None:
        out["first8_check"] = first8_check(a.run, a.run8, a.marks8, scorer, seeds)
    root = Path(__file__).resolve().parents[2]
    out["provenance"] = dict(
        script=str(Path(__file__).resolve().relative_to(root)), script_sha256=sha256_file(Path(__file__).resolve()),
        dependency_sha256={str(Path(m.__file__).resolve().relative_to(root)): sha256_file(m.__file__)
                           for m in (cm, cr, sys.modules["scripts.r106.coras_stability"])},
        command=analysis_command(sys.orig_argv if argv is None else ["scripts.r106.coras_marks_influence.main", *map(str, argv)]),
        numpy=np.__version__, scipy=scipy.__version__, rng_seeds=RNG_SEEDS,
        reps=dict(subsets=a.reps, disjoint_halves=a.halves_reps))
    out["review_corrections"] = REVIEW_CORRECTIONS
    status, digest = write_json(a.output, out, supersede=a.supersede)
    print(f"{a.output}: {status} sha256={digest}", flush=True)


if __name__ == "__main__":
    main()
