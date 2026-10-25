#!/usr/bin/env python3
"""Exact finite-box CF4 FP pooling check under the frozen R26 contract."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction as F
from math import isqrt
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
CONTRACT = OUT.parent / "r26_sdss_genealogy_independent_review"
BIND = CONTRACT / "SOURCE_BINDINGS.json"
PRECISION_DIGITS = 55
CONVENTIONS = {
    "ROUND_TO_NEAREST_LAST_PRINTED_PLACE": F(1, 2),
    "ONE_LAST_PLACE_OUTER": F(1),
}


def frac(token: str) -> F:
    return F(token.strip())


def quantum(token: str) -> F:
    token = token.strip()
    n = len(token.split(".", 1)[1]) if "." in token else 0
    return F(1, 10**n)


def interval(token: str, width: F) -> tuple[F, F]:
    x = frac(token)
    d = quantum(token) * width
    return x - d, x + d


def finite_box(rows: list[dict], width: F):
    """Exact rational extrema from all sorted endpoint-weight breakpoints."""
    z = []
    for r in rows:
        ml, mh = interval(r["dm"], width)
        sl, sh = interval(r["err"], width)
        if sl <= 0:
            raise ValueError(f"DOMAIN_UNCERTAIN PGC={r['pgc']} e_DMfp={r['err']}")
        z.append((r["pgc"], ml, mh, 1 / sh**2, 1 / sl**2))

    def extrema(values_idx: int, descending: bool):
        ordered = sorted(z, key=lambda row: ((-row[values_idx]) if descending else row[values_idx], row[0]))
        values = [r[values_idx] for r in ordered]
        lows = [r[3] for r in ordered]
        highs = [r[4] for r in ordered]
        numerator = sum((v*w for v, w in zip(values, lows)), F())
        denominator = sum(lows, F())
        best = None
        best_k = 0
        for k in range(len(ordered) + 1):
            candidate = numerator / denominator
            if best is None or (candidate > best if descending else candidate < best):
                best, best_k = candidate, k
            if k < len(ordered):
                delta = highs[k] - lows[k]
                numerator += values[k] * delta
                denominator += delta
        witness = [{"pgc": r[0], "endpoint": "weight_high" if i < best_k else "weight_low"}
                   for i, r in enumerate(ordered)]
        return best, witness

    lower, lower_weights = extrema(1, False)
    upper, upper_weights = extrema(2, True)
    sum_low = sum((r[3] for r in z), F())
    sum_high = sum((r[4] for r in z), F())
    nominal_weights = [1 / frac(r["err"])**2 for r in rows]
    nominal = sum((frac(r["dm"]) * w for r, w in zip(rows, nominal_weights)), F()) / sum(nominal_weights)
    return {
        "lower": lower, "upper": upper,
        "q_lower": sqrt_bounds_inverse_weight(sum_high)[0],
        "q_upper": sqrt_bounds_inverse_weight(sum_low)[1],
        "nominal": nominal,
        "lower_weights": lower_weights, "upper_weights": upper_weights,
        "convex_hull": (min(r[1] for r in z), max(r[2] for r in z)),
    }


def sqrt_bounds_inverse_weight(weight: F) -> tuple[F, F]:
    """Certified decimal grid enclosure of sqrt(1/weight), integer only."""
    scale = 10**PRECISION_DIGITS
    numerator = weight.denominator * scale * scale
    denominator = weight.numerator
    floor = isqrt(numerator // denominator)
    lo = F(floor, scale)
    exact = floor * floor * denominator == numerator
    hi = lo if exact else F(floor + 1, scale)
    return lo, hi


def decimal_out(x: F, direction: str, places: int = 45) -> str:
    scale = 10**places
    a = x.numerator * scale // x.denominator
    if direction == "up" and F(a, scale) < x:
        a += 1
    sign = "-" if a < 0 else ""
    digits = str(abs(a)).zfill(places + 1)
    return sign + digits[:-places] + "." + digits[-places:]


def exact_pair(x: F) -> dict:
    return {"numerator": str(x.numerator), "denominator": str(x.denominator),
            "decimal_lower": decimal_out(x, "down"), "decimal_upper": decimal_out(x, "up")}


def endpoint_pair(lo: F, hi: F) -> dict:
    return {"lower": decimal_out(lo, "down"), "upper": decimal_out(hi, "up")}


def quantile(sorted_values: list[F], q: F) -> F:
    v = (len(sorted_values)-1)*q
    lo = v.numerator // v.denominator
    f = v - lo
    return sorted_values[lo]*(1-f) + sorted_values[min(lo+1, len(sorted_values)-1)]*f


def binding_receipt() -> dict:
    bound = json.loads(BIND.read_text())
    receipt = []
    for b in bound:
        p = Path(b["path"])
        stat = p.stat()
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if stat.st_size != b["bytes"] or digest != b["sha256"]:
            raise ValueError(f"SOURCE_IDENTITY_MISMATCH {p}")
        receipt.append({"path": str(p), "bytes": stat.st_size, "sha256": digest})
    prior_bind = OUT.parent / "r26_sdss_v110_source_intake" / "SOURCE_IDENTITIES.json"
    budget = next(x for x in json.loads(prior_bind.read_text()) if Path(x["path"]).name == "SCIENTIFIC_BUDGET.jsonl")
    if hashlib.sha256(Path(budget["path"]).read_bytes()).hexdigest() != budget["sha256"]:
        raise ValueError("HISTORICAL_BUDGET_IDENTITY_MISMATCH")
    return {"binding_path": str(BIND), "binding_sha256": hashlib.sha256(BIND.read_bytes()).hexdigest(),
            "source_intake_identity_path": str(prior_bind),
            "original_science_budget": {"path": budget["path"], "bytes": budget["bytes"], "sha256": budget["sha256"],
                                        "last_completed_cumulative_s": 41.02750632702373, "cap_s": 600},
            "verified": receipt}


def raw_rows(path: Path, parse):
    offset = 0
    with path.open("rb") as f:
        for line_no, binary in enumerate(f, 1):
            s = binary.decode("ascii").rstrip("\r\n")
            yield parse(s, line_no, offset)
            offset += len(binary)


def parse2(s: str, line_no: int, offset: int) -> dict:
    return {"pgc": int(s[0:7]), "group": int(s[8:15]), "dm": s[65:71].strip(),
            "err": s[72:76].strip(), "line": line_no, "byte_offset_zero_based": offset,
            "raw": s}


def parse3(s: str, line_no: int, offset: int) -> dict:
    return {"group": int(s[0:7]), "count": s[113:116].strip(), "dm": s[117:123].strip(),
            "err": s[124:129].strip(), "line": line_no, "byte_offset_zero_based": offset,
            "raw": s}


def witness(group: int, rows: list[dict], target: dict | None, z: dict | None = None) -> dict:
    o = {"group": group, "table2_rows": rows, "table3_row": target}
    if z:
        o["modulus_interval"] = endpoint_pair(z["lower"], z["upper"])
        o["q_interval"] = endpoint_pair(z["q_lower"], z["q_upper"])
        o["nominal"] = exact_pair(z["nominal"])
        o["lower_extremizing_weights"] = z["lower_weights"]
        o["upper_extremizing_weights"] = z["upper_weights"]
    return o


def run():
    receipt = binding_receipt()
    mapping = {Path(x["path"]).name: Path(x["path"]) for x in receipt["verified"]}
    # Raw source PGC tokens define membership; no archived author join code is imported.
    sdss_ids = set()
    sdss_rows = 0
    with mapping["SDSS_PV_public.dat"].open("r", encoding="ascii") as f:
        next(f)
        for line in f:
            sdss_rows += 1
            sdss_ids.add(int(line.split(None, 1)[0]))
    assert sdss_rows == len(sdss_ids) == 34059
    table2 = {}
    grouped = defaultdict(list)
    for r in raw_rows(mapping["table2.dat"], parse2):
        if r["pgc"] in table2:
            raise ValueError(f"DUPLICATE_TABLE2_PGC {r['pgc']}")
        table2[r["pgc"]] = r
        if bool(r["dm"]) != bool(r["err"]):
            raise ValueError(f"INCOMPLETE_TABLE2_FP_PAIR PGC={r['pgc']}")
        if r["dm"]:
            grouped[r["group"]].append(r)
    table3 = {}
    for r in raw_rows(mapping["table3.dat"], parse3):
        if r["group"] in table3:
            raise ValueError(f"DUPLICATE_TABLE3_GROUP {r['group']}")
        table3[r["group"]] = r
    npz = np.load(mapping["selected_source_observables.npz"])
    selected = {int(x) for x in npz["group_id"]}
    cohort = sorted({table2[x]["group"] for x in sdss_ids & table2.keys() if table2[x]["group"] in selected})
    if len(cohort) != 22653:
        raise ValueError(f"COHORT_COUNT_MISMATCH observed={len(cohort)} expected=22653")
    receipt.update({"source_fields": {"table2": "PGC1:7 1PGC9:15 DMfp66:71 e_DMfp73:76",
                                      "table3": "1PGC1:7 o_DMfp114:116 DMfp118:123 e_DMfp125:129"},
                    "cohort_definition": "selected group_id with >=1 raw SDSS PGC joined to table2",
                    "cohort_groups": len(cohort), "SDSS_PGC_rows": sdss_rows,
                    "PGC20919_stage_example": {"table2": {k: table2[20919][k] for k in ("pgc", "group", "dm", "err", "line", "byte_offset_zero_based")},
                                               "table3": {k: table3[20919][k] for k in ("group", "count", "dm", "err", "line", "byte_offset_zero_based")},
                                               "DMav": table3[20919]["raw"][15:21].strip(), "DMzp": table3[20919]["raw"][8:14].strip()}})
    (OUT / "SOURCE_BINDING_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")

    structure = []
    tally = Counter()
    records = {name: [] for name in CONVENTIONS}
    excluded = {name: [] for name in CONVENTIONS}
    nominal_residuals = []
    non_sdss_example = None
    for group in cohort:
        rows = grouped.get(group, [])
        t = table3.get(group)
        n_sdss = sum(r["pgc"] in sdss_ids for r in rows)
        n_other = len(rows)-n_sdss
        tally["all_FP_contributors"] += len(rows)
        tally["SDSS_FP_contributors"] += n_sdss
        tally["other_FP_contributors"] += n_other
        tally["groups_with_other_FP_contributors"] += n_other > 0
        tally["ALL_GALAXY_IDS_IN_SDSS"] += n_other == 0
        if not t or not t["count"] or not t["dm"] or not t["err"]:
            reason = "MISSING_TABLE3_FP_FIELDS"
        elif int(t["count"]) != len(rows):
            reason = "TABLE3_FP_COUNT_MISMATCH"
        else:
            reason = None
        if reason:
            structure.append({"group": group, "reason": reason, "observed_contributors": len(rows),
                              "table3_o_DMfp": t["count"] if t else None, "witness": witness(group, rows, t)})
            for name in CONVENTIONS:
                excluded[name].append({"group": group, "reason": reason})
            continue
        tally["structurally_qualified"] += 1
        if n_other and non_sdss_example is None:
            non_sdss_example = group
        for name, width in CONVENTIONS.items():
            try:
                z = finite_box(rows, width)
                tlo, thi = interval(t["dm"], width)
                elo, ehi = interval(t["err"], width)
            except (ValueError, ZeroDivisionError) as exc:
                excluded[name].append({"group": group, "reason": "DOMAIN_UNCERTAIN", "detail": str(exc)})
                continue
            qgap = max(z["q_lower"]-ehi, elo-z["q_upper"], F())
            rec = {"group": group, "n_fp": len(rows), "n_sdss": n_sdss, "n_other": n_other,
                   "all_galaxy_ids_in_sdss": n_other == 0,
                   "lower": z["lower"], "upper": z["upper"],
                   "q_lower": z["q_lower"], "q_upper": z["q_upper"],
                   "target_lo": tlo, "target_hi": thi, "target_error_lo": elo, "target_error_hi": ehi,
                   "offset_lo": tlo-z["upper"], "offset_hi": thi-z["lower"],
                   "q_gap": qgap, "nominal": z["nominal"]}
            records[name].append(rec)
            if name == "ROUND_TO_NEAREST_LAST_PRINTED_PLACE":
                nominal_residuals.append(z["nominal"]-frac(t["dm"]))

    result = {"scope": "all table2 FP contributors in retained SDSS-linked CF4 groups",
              "requested_runtime": "gpt-6-sol/high", "observed_runtime": "UNKNOWN",
              "source_binding_receipt": "SOURCE_BINDING_RECEIPT.json",
              "structure": {"cohort_count": len(cohort), **dict(tally),
                            "witness_count": len(structure), "witnesses": [{k: v for k, v in x.items() if k != "witness"} for x in structure]},
              "rounding_conventions": {}, "simultaneous_modulus_error_feasibility": "NOT_ESTABLISHED",
              "quoted_error_law": "NOT_ESTABLISHED", "missing_subsource_genealogy": "FP accepted-subsource purity and weights unknown",
              "H02": "HOLD_UNCHANGED", "scientific_admission": "HOLD",
              "native_solver_or_ODE": "NOT_USED", "physical_Q_denominator_Pi": "NOT_ADMITTED",
              "offset_scope": "structurally_qualified_groups_only",
              "all_cohort_reproduction": "UNESTABLISHED_IF_ANY_STRUCTURAL_EXCLUSION",
              "non_sdss_witness_group": non_sdss_example}
    witnesses = {"structural": structure, "precision": {}}
    if nominal_residuals:
        residuals = sorted(nominal_residuals)
        result["nominal_modulus_minus_table3_quantiles"] = {str(q): exact_pair(quantile(residuals, q))
                                                           for q in (F(), F(1,20), F(1,2), F(19,20), F(1))}
    for name, recs in records.items():
        inc = [r["group"] for r in recs]
        s = {"precision_rule": str(CONVENTIONS[name]) + " lexical quantum",
             "included_group_ids": inc, "excluded_group_ids_with_reasons": excluded[name],
             "included_count": len(inc), "excluded_count": len(excluded[name]),
             "error_pooling_disjoint_group_ids": [r["group"] for r in recs if r["q_gap"] > 0],
             "error_pooling_disjoint_count": sum(r["q_gap"] > 0 for r in recs),
             "marginal_projection_only": True}
        if recs:
            lo = max(recs, key=lambda r: (r["offset_lo"], -r["group"]))
            hi = min(recs, key=lambda r: (r["offset_hi"], r["group"]))
            s["all_group_offset_bounds"] = endpoint_pair(lo["offset_lo"], hi["offset_hi"])
            s["all_group_max_lower_group"] = lo["group"]
            s["all_group_min_upper_group"] = hi["group"]
            s["all_group_gap_if_empty"] = exact_pair(lo["offset_lo"]-hi["offset_hi"]) if lo["offset_lo"] > hi["offset_hi"] else None
            singleton = [r for r in recs if r["n_fp"] == 1]
            s["singleton_group_count"] = len(singleton)
            if singleton:
                sl = max(singleton, key=lambda r: (r["offset_lo"], -r["group"]))
                sh = min(singleton, key=lambda r: (r["offset_hi"], r["group"]))
                s["singleton_offset_bounds"] = endpoint_pair(sl["offset_lo"], sh["offset_hi"])
                s["singleton_max_lower_group"] = sl["group"]
                s["singleton_min_upper_group"] = sh["group"]
                s["singleton_gap_if_empty"] = exact_pair(sl["offset_lo"]-sh["offset_hi"]) if sl["offset_lo"] > sh["offset_hi"] else None
            # Two strongest real witnesses are the active offset bounds; preserve raw rows and exact extremizing choices.
            chosen = {lo["group"], hi["group"]}
            if non_sdss_example:
                chosen.add(non_sdss_example)
            qbad = max(recs, key=lambda r: r["q_gap"])
            if qbad["q_gap"] > 0:
                chosen.add(qbad["group"])
            witnesses["precision"][name] = {}
            for g in sorted(chosen):
                r = next(r for r in recs if r["group"] == g)
                z = finite_box(grouped[g], CONVENTIONS[name])
                w = witness(g, grouped[g], table3[g], z)
                w.update({"offset_interval": endpoint_pair(r["offset_lo"], r["offset_hi"]),
                          "error_target_interval": endpoint_pair(r["target_error_lo"], r["target_error_hi"]),
                          "error_gap": exact_pair(r["q_gap"]), "sdss_contributors": r["n_sdss"],
                          "other_contributors": r["n_other"]})
                witnesses["precision"][name][str(g)] = w
        result["rounding_conventions"][name] = s
    if structure or any(excluded.values()):
        result["status"] = "STRUCTURAL/NUMERICAL_HOLD"
    elif any(s["all_group_gap_if_empty"] is not None or s["error_pooling_disjoint_count"] > 0
             for s in result["rounding_conventions"].values()):
        result["status"] = "POOLING_INCOMPATIBLE_WITH_ROUNDING_WITNESS"
    else:
        result["status"] = "POOLING_OUTER_COMPATIBLE"
    (OUT / "WITNESSES.json").write_text(json.dumps(witnesses, indent=2) + "\n")
    (OUT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "cohort": len(cohort), "structure_witnesses": len(structure),
                      "summary": {k: {x: v for x, v in s.items() if x in ("included_count", "excluded_count", "error_pooling_disjoint_count", "all_group_max_lower_group", "all_group_min_upper_group", "all_group_gap_if_empty", "singleton_group_count")}
                                  for k, s in result["rounding_conventions"].items()}}, indent=2))


if __name__ == "__main__":
    run()
