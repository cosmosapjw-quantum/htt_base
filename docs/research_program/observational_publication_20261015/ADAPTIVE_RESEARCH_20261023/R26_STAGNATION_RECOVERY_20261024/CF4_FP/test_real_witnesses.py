#!/usr/bin/env python3
"""Independent 100-digit Decimal checks on strongest real bound witnesses."""
import json
from decimal import Decimal as D, localcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent


def token_box(s, multiplier):
    x = D(s)
    places = len(s.split(".", 1)[1]) if "." in s else 0
    delta = D(1).scaleb(-places)*multiplier
    return x-delta, x+delta


def check():
    result = json.loads((HERE / "RESULT.json").read_text())
    all_witnesses = json.loads((HERE / "WITNESSES.json").read_text())["precision"]
    checked = []
    with localcontext() as ctx:
        ctx.prec = 100
        for name, all_groups in all_witnesses.items():
            width = D("0.5") if name == "ROUND_TO_NEAREST_LAST_PRINTED_PLACE" else D(1)
            summary = result["rounding_conventions"][name]
            active = {str(summary["all_group_max_lower_group"]), str(summary["all_group_min_upper_group"])}
            for group in active:
                r = all_groups[group]
                source = {x["pgc"]: x for x in r["table2_rows"]}
                means = {}
                for extremum in ("lower", "upper"):
                    numer = den = D(0)
                    for choice in r[f"{extremum}_extremizing_weights"]:
                        row = source[choice["pgc"]]
                        mlo, mhi = token_box(row["dm"], width)
                        slo, shi = token_box(row["err"], width)
                        m = mlo if extremum == "lower" else mhi
                        s = slo if choice["endpoint"] == "weight_high" else shi
                        w = 1/(s*s)
                        numer += w*m
                        den += w
                    mean = numer/den
                    means[extremum] = mean
                    assert D(r["modulus_interval"]["lower"]) <= mean <= D(r["modulus_interval"]["upper"])
                tlo, thi = token_box(r["table3_row"]["dm"], width)
                assert D(r["offset_interval"]["lower"]) <= tlo-means["upper"]
                assert D(r["offset_interval"]["upper"]) >= thi-means["lower"]
                qlo_sum = qhi_sum = D(0)
                for row in r["table2_rows"]:
                    slo, shi = token_box(row["err"], width)
                    qlo_sum += 1/(slo*slo)
                    qhi_sum += 1/(shi*shi)
                qlo = 1/qlo_sum.sqrt()
                qhi = 1/qhi_sum.sqrt()
                assert D(r["q_interval"]["lower"]) <= qlo <= qhi <= D(r["q_interval"]["upper"])
                checked.append({"convention": name, "group": int(group), "rows": len(source)})
    assert len(checked) == 4
    print(json.dumps({"status": "PASS_INDEPENDENT_100_DIGIT_REAL_WITNESSES", "checks": checked}))


if __name__ == "__main__":
    check()
