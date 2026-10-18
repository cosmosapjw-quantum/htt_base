"""Completed L02 descriptors on the same eight genuine FFP10 pilot rows.

Reuse the L02 kernel read-only. Five component/amplitude variants share eight
IDs, not 40 skies. No null rank, family maximum or physical coverage claim.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
L02 = HERE.parent/"L02_EXECUTION_20261018"
sys.path.insert(0, str(L02))
import statistic_family as family
from source_matched_pilot import identity, validate_pairs

VARIANTS = ("signal_only", "noise_plus_systematics_only", "sum_noise_0.95",
            "sum_noise_1.00", "sum_noise_1.05")


def explicit_field_indices(layout):
    """Bind E/B indexing to the exact archived column identities, not offsets."""
    if len(layout) != 64:
        raise ValueError("SIXTY_FOUR_SPIN_COLUMNS_REQUIRED")
    indices = {"T": np.arange(32)}
    for field in ("E", "B"):
        ix = [i for i, col in enumerate(layout) if col["E_or_B"] == field]
        expected = [{"ell": ell, "m": m, "phase": phase, "E_or_B": field}
                    for ell in range(2, 6) for m in range(ell+1)
                    for phase in (("m0",) if m == 0 else ("cos", "sin"))]
        if [layout[i] for i in ix] != expected:
            raise ValueError("EXPLICIT_SPIN_CHART_NOT_ORIGINAL_L02_CHART")
        indices[field] = np.asarray(ix)+32
    return indices


def variants(coeff):
    c = np.asarray(coeff)
    if c.shape != (8, 2, 96) or not np.isfinite(c).all() or np.iscomplexobj(c):
        raise ValueError("EIGHT_FINITE_PAIRED_TEB_ROWS_REQUIRED")
    return dict(zip(VARIANTS, (c[:, 0], c[:, 1], c[:, 0]+.95*c[:, 1],
                               c[:, 0]+c[:, 1], c[:, 0]+1.05*c[:, 1])))


def apply(coefficients, indices):
    outputs = []
    baseline_rows = []
    for label, rows in variants(coefficients).items():
        for simulation_id, row in enumerate(rows):
            fields, tensors = {}, {}
            for field, ix in indices.items():
                retained = row[ix]*1e6
                q, o = family.tensors_from_real(retained)
                tensors[field] = (q, o)
                fields[field] = {"C2_microK2": float(retained[:5]@retained[:5]/5),
                    "C3_microK2": float(retained[5:12]@retained[5:12]/7),
                    **family.descriptors(q, o, field)}
                if label == "sum_noise_1.00":
                    baseline_rows.append((f"FFP10_{simulation_id:05d}", field, retained))
            cross = {left+right: {"physical_O3_contraction_parity": -1 if "B" in (left, right) else 1,
                                 **family.cross_features(*tensors[left], *tensors[right])}
                     for left, right in (("T", "E"), ("T", "B"), ("E", "B"))}
            outputs.append({"simulation_id": simulation_id, "signal_id": simulation_id,
                "noise_id": simulation_id, "variant": label, "fields": fields,
                "same_row_cross_fields": cross})
    return outputs, baseline_rows


def differences(rows):
    indexed = {(r["simulation_id"], r["variant"]): r for r in rows}
    out = {}
    for field in ("T", "E", "B"):
        out[field] = {}
        for alpha in ("0.95", "1.05"):
            shifts = {}
            for descriptor in family.SHAPE_NAMES:
                values = []
                for i in range(8):
                    base = indexed[i, "sum_noise_1.00"]["fields"][field]["SO3_signed"][descriptor]
                    varied = indexed[i, "sum_noise_"+alpha]["fields"][field]["SO3_signed"][descriptor]
                    values.append(None if base is None or varied is None else varied-base)
                finite = [abs(v) for v in values if v is not None]
                shifts[descriptor] = {"signed_shift_per_id": values,
                    "maximum_absolute_shift": max(finite) if finite else None,
                    "undefined_pair_count": sum(v is None for v in values)}
            overlaps = []
            for i in range(8):
                base = indexed[i, "sum_noise_1.00"]["fields"][field]["orientation"]["joint_axis_overlap_squared"]
                varied = indexed[i, "sum_noise_"+alpha]["fields"][field]["orientation"]["joint_axis_overlap_squared"]
                overlaps.append(None if base is None or varied is None else varied-base)
            finite = [abs(v) for v in overlaps if v is not None]
            shifts["joint_axis_overlap_squared"] = {"signed_shift_per_id": overlaps,
                "maximum_absolute_shift": max(finite) if finite else None,
                "undefined_pair_count": sum(v is None for v in overlaps)}
            out[field][alpha] = shifts
    return out


def plot(rows, shift, directory):
    indexed = {(r["simulation_id"], r["variant"]): r for r in rows}
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.7))
    for column, field in enumerate(("T", "E", "B")):
        ax = axes[0, column]
        for name, label, color in (("signal_only", "CMB", "#2864a5"),
                ("noise_plus_systematics_only", "Noise + systematics", "#dc7b23"),
                ("sum_noise_1.00", "Sum", "#222222")):
            v = [indexed[i, name]["fields"][field]["orientation"]["joint_axis_overlap_squared"] for i in range(8)]
            ax.plot(np.arange(8), [np.nan if x is None else x for x in v], marker="o", ms=3, label=label, color=color)
        ax.set_title(field+" joint quadrupole/octupole axes")
        ax.set_ylim(0, 1)
        ax.set_ylabel("Squared headless-axis overlap")
        ax.set_xlabel("Matched simulation ID")
        ax.set_xticks(np.arange(8))
        if column == 0:
            ax.legend(fontsize=8)
        ax = axes[1, column]
        for descriptor in (*family.SHAPE_NAMES, "joint_axis_overlap_squared"):
            values = shift[field]["1.05"][descriptor]["signed_shift_per_id"]
            ax.plot(np.arange(8), [np.nan if v is None else v for v in values], marker="o", ms=3, label=descriptor)
        ax.axhline(0, color="gray", linewidth=.7)
        ax.set_title(field+" descriptor sensitivity: noise ×1.05")
        ax.set_xlabel("Matched simulation ID")
        ax.set_xticks(np.arange(8))
        ax.set_ylabel("Signed shift from same-row baseline")
        if column == 0:
            ax.legend(fontsize=7)
    fig.suptitle("Fixed L02 family on eight source-matched FFP10 T/E/B rows\nSame-row component/amplitude diagnostics; no null significance or coverage", fontsize=12)
    fig.tight_layout()
    fig.savefig(directory/"L02_ON_EIGHT_PAIR_PILOT.png", dpi=170)
    fig.savefig(directory/"L02_ON_EIGHT_PAIR_PILOT.pdf")
    plt.close(fig)


def main():
    directory = HERE/"results"
    out = directory/"L02_ON_EIGHT_PAIR_PILOT.json"
    if any(p.exists() for p in (out, directory/"L02_ON_EIGHT_PAIR_PILOT.png", directory/"L02_ON_EIGHT_PAIR_PILOT.pdf")):
        raise FileExistsError("CREATE_ONLY_FAMILY_OUTPUT_EXISTS")
    pilot = json.loads((directory/"PILOT.json").read_text())
    path = directory/"PILOT_COEFFICIENTS.npz"
    source = identity(path, pilot["coefficients"]["sha256"])
    archive = family.SOURCE/"retained_common_support_coefficients.npz"
    chart = identity(archive, family.SOURCE_SHA)
    # The same L02 validator checks archive product/chart metadata read-only.
    family.load_source()
    with np.load(archive, allow_pickle=False) as z:
        layout = json.loads(z["column_spin_metadata_json"].item())
    indices = explicit_field_indices(layout)
    with np.load(path, allow_pickle=False) as z:
        validate_pairs(z["signal_ids"], z["noise_ids"])
        rows, baseline = apply(z["component_coefficients_K_CMB"], indices)
    shift = differences(rows)
    result = {"schema": "htt.L03_fixed_L02_family_eight_pairs/1", "owner": "obsstat", "claim_tier": "C0",
        "status": "DIAGNOSTIC_ONLY", "non_claim_bearing": True, "transfer_source": "none",
        "independent_pair_ids": list(range(8)), "independent_pair_count": 8,
        "variant_count": 5, "variant_row_count": len(rows), "field_descriptor_rows": len(rows)*3,
        "same_row_cross_field_pairs": len(rows)*3, "variant_inventory": list(VARIANTS),
        "source": source, "original_column_chart": chart,
        "L02_kernel": identity(L02/"statistic_family.py"),
        "L02_specification": identity(L02/"STATISTIC_FAMILY.md"),
        "generator": identity(__file__), "column_indices_TEB": {k: v.tolist() for k, v in indices.items()},
        "rows": rows, "same_id_noise_amplitude_descriptor_shifts": shift,
        "metamorphic_actual_baseline_rows": family.metamorphic_checks(baseline),
        "null_coverage": "NOT_QUALIFIED", "p_value": None, "family_maximum_or_rank": None,
        "canonical_L03": "HOLD", "canonical_L04": "NOT_COMPLETED", "paper_gate": "NOT_READY_TO_SUBMIT",
        "caveats": ["Five variants and three fields share exactly eight rows; no independent-unit multiplication.",
            "Retrospective descriptive source-conditional use, not preregistration or anomaly significance.",
            "T and polarization supports differ; cross-field features are not physical full-sky spectra.",
            "Unknown zero/degenerate descriptors remain None, never zero-filled.",
            "Native mask/child-average high-mode sensitivity and absent joint split/foreground law persist."]}
    with out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write("\n")
    plot(rows, shift, directory)
    print(json.dumps({"out": str(out), "independent_pair_count": 8, "field_descriptor_rows": len(rows)*3,
                      "metamorphic": result["metamorphic_actual_baseline_rows"],
                      "max_axis_shift_noise_1.05": {f: shift[f]["1.05"]["joint_axis_overlap_squared"]["maximum_absolute_shift"] for f in shift}}, indent=2))


if __name__ == "__main__":
    main()
