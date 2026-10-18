"""Plot actual same-sky processed-feature values, never sampling uncertainty."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    source = HERE/"results/L02_ACTUAL_STATISTICS.json"
    result = json.loads(source.read_text())
    rows = result["field_rows"]
    products = [r["product"] for r in rows if r["field"] == "T"]
    labels = [p.replace("SMICA_", "S:").replace("NILC_", "N:").replace("_FULL", "F").replace("FULL", "F") for p in products]
    panels = [
        ("quadrupole_shape", "Signed tr(q³)\nreflection: T/E even; B odd", None),
        ("octupole_concentration", "Octupole concentration λmax(A)\nO(3) invariant", (0., .65)),
        ("QO_contraction", "tr(q²A)\nO(3) invariant", (0., .55)),
        ("chirality", "Normalized triple product h\nreflection: T/E odd; B even", (-.33, .33)),
        ("joint_axis_overlap_squared", "Principal Q²/O axes: squared overlap\nO(3) invariant; headless axes", (0., 1.)),
        ("O3_fixed_axis_squared_cosines", "Octupole axis: Galactic z squared cosine\nfixed-axis orientation; not invariant", (0., 1.)),
    ]
    fig, axs = plt.subplots(2, 3, figsize=(13.5, 8.), sharex=True)
    styles = {"T": ("#111111", "o", -.16), "E": ("#0072B2", "s", 0.), "B": ("#D55E00", "^", .16)}
    for ax, (key, title, limits) in zip(axs.ravel(), panels):
        for field, (color, marker, offset) in styles.items():
            chosen = [r for r in rows if r["field"] == field]
            values = []
            for row in chosen:
                v = row["SO3_signed"].get(key, row["orientation"].get(key))
                if key == "O3_fixed_axis_squared_cosines" and v is not None:
                    v = v[2]
                values.append(np.nan if v is None else v)
            ax.scatter([products.index(r["product"])+offset for r in chosen], values,
                       color=color, marker=marker, label=field, s=32)
        ax.set_title(title, fontsize=10)
        ax.set_xticks(range(len(products)), labels, rotation=55, ha="right", fontsize=8)
        ax.grid(axis="y", color="0.88", lw=.6)
        if limits:
            ax.set_ylim(limits)
    axs[0, 0].legend(title="Field", ncol=3, fontsize=8)
    fig.suptitle("L02: ell 2/3 tensors from the original Planck common-support estimator", fontsize=13)
    fig.text(.5, .015, "One physical sky · product alternatives are correlated · original cut-sky fits · no calibrated significance", ha="center", fontsize=10)
    fig.tight_layout(rect=(0., .065, 1., .96))
    for extension in ("png", "pdf"):
        path = HERE/f"results/L02_actual_shape_and_orientation.{extension}"
        if path.exists():
            raise FileExistsError(f"create-only plot exists: {path}")
        fig.savefig(path, dpi=180)
    plt.close(fig)
    path = HERE/"results/L02_feature_vectors.csv"
    if path.exists():
        raise FileExistsError("create-only table exists")
    with path.open("w", newline="") as f:
        fields = ["product", "field", "sky_id", "C2_microK2", "C3_microK2"]
        fields += list(rows[0]["SO3_signed"])+["joint_axis_overlap_squared"]
        fields += [f"{ell}_axis_{axis}_squared_cosine" for ell in ("Q2", "O3") for axis in ("x", "y", "z")]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            record = {k: row[k] for k in fields[:5]}
            record.update(row["SO3_signed"])
            record["joint_axis_overlap_squared"] = row["orientation"]["joint_axis_overlap_squared"]
            for ell in ("Q2", "O3"):
                values = row["orientation"][f"{ell}_fixed_axis_squared_cosines"]
                for index, axis in enumerate(("x", "y", "z")):
                    record[f"{ell}_axis_{axis}_squared_cosine"] = None if values is None else values[index]
            writer.writerow(record)
    print("Wrote PNG/PDF and 25-row feature table from L02_ACTUAL_STATISTICS.json")


if __name__ == "__main__":
    main()
