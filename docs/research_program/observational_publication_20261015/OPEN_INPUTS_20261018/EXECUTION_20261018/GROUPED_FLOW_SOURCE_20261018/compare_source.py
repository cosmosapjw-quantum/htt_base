"""Finite source comparison: parse captured means only; never open a 3D grid."""
from __future__ import annotations

import ast
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").exists())
EXTERNAL = Path("/mnt/extdrive/workdir/htt_open_data/cf4/grouped_geometry_source_20261018")
INTAKE_HEAD = "b4a93016afb57a5b115bff4dbfa65bc3d56d4b65"
RADII = [50, 100, 150, 200, 250, 300]
EXPECTED_TABLE = [[-230, 75, -80], [-292, 65, -124], [-245, 77, -91],
                  [-80, 185, -42], [-10, 258, -31], [1, 229, -29]]
SEALED = {
    "SPHERE_PROBE_TRANSCRIPT.txt": "4b0b6c17f5c8e52d1f7f76669cb9db4a084ecc6fdf8182f835ffb9fa1ea8f3f7",
    "giani_main_first13001bytes.jsonpart": "e30081c5b590a48e554cc39af486b388e5fe260bb9ca635de531ce0d9cbf3fa1",
    "giani_main_prefix.headers": "751587e6eacc79b56e0c8d45da2c49dffb9081ab5342f871d1e2610e13038889",
    "courtois_2211.16390v4.html": "d35fd4a0248479f0cad0a2c7db06f6e5ae87f7afc46108fd4c61a80a3ba3db55",
    "courtois_2211.16390v4.headers": "0ddfd4f36e346226ef8192f36310e735470027fe3ffb0d5d862c42490f22fc05",
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sealed_inputs():
    inputs = {}
    for name, expected in SEALED.items():
        path = EXTERNAL / name
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"immutable input identity mismatch: {name}")
        inputs[name] = {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}
    return inputs


class TableParser(HTMLParser):
    """Select Table 1 by identity and use math alttext, avoiding duplicate MathML."""
    def __init__(self):
        super().__init__()
        self.inside = False
        self.math = 0
        self.cell = None
        self.row = None
        self.rows = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "figure" and attrs.get("id") == "S4.T1":
            if self.rows:
                raise ValueError("duplicate Table 1")
            self.inside = True
        if not self.inside:
            return
        if tag == "tr":
            self.row = []
        if tag in {"td", "th"}:
            self.cell = []
        if tag == "math":
            value = attrs.get("alttext", "")
            self.text.append(value)
            if self.cell is not None:
                self.cell.append(value)
            self.math += 1

    def handle_data(self, data):
        if self.inside and not self.math:
            self.text.append(data)
            if self.cell is not None:
                self.cell.append(data)

    def handle_endtag(self, tag):
        if not self.inside:
            return
        if tag == "math":
            self.math -= 1
        elif tag in {"td", "th"} and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == "figure":
            self.inside = False


def parse_table(html):
    parser = TableParser()
    parser.feed(html)
    rows = parser.rows
    if not rows or rows[0][2:] != ["Vx", "Vy", "Vz"]:
        raise ValueError("Table 1 component header missing")
    if rows[1] != ["h{}_{100}^{-1} Mpc"] + ["km s^{-1}"] * 4:
        raise ValueError("Table 1 radius/velocity units changed")
    if "in the cosmic microwave background rest frame" not in " ".join(parser.text):
        raise ValueError("Table 1 CMB frame absent")
    starts = [i for i, row in enumerate(rows) if row[0] == "Grouped CF4"]
    if len(starts) != 1:
        raise ValueError("missing or duplicate Grouped CF4 section")
    selected = rows[starts[0] + 1:starts[0] + 7]
    radii = [int(row[0]) for row in selected]
    vectors = [[int(x) for x in row[2:5]] for row in selected]
    if radii != RADII or vectors != EXPECTED_TABLE:
        raise ValueError("literal grouped Table 1 rows differ from frozen intake")
    return {"source": "https://arxiv.org/html/2211.16390v4#S4.T1",
            "frame": "CMB rest frame", "radius_unit": "h_100^-1 Mpc",
            "velocity_unit": "km/s", "radii": radii,
            "components": ["Vx", "Vy", "Vz"], "vectors": vectors,
            "literal_cells": selected, "norm_error_columns_used": False}


def check_prefix(text):
    # This partial JSON is not executable and is deliberately not loaded as a notebook.
    anchors = ["t = 52.*hdu[0].data", "t_e = 52.*hdu_e[0].data",
               "32. + ((64./1000.)*u)", "32. + ((64./1000.)*v)",
               "32. + ((64./1000.)*w)", "lania_surf_vv = t[:,kk,jj,ii]",
               "lania_surf_vv[2],lania_surf_vv[1],lania_surf_vv[0]"]
    if not all(anchor in text for anchor in anchors):
        raise ValueError("pinned author code anchor absent")
    return {"anchors": anchors, "N": 64, "L_hinv_Mpc": 1000,
            "spacing_hinv_Mpc": 15.625, "index_origin": 32,
            "sample_node_extents_hinv_Mpc": [-500, 484.375],
            "voxel_boundaries": "UNKNOWN", "producer_centering": "UNKNOWN",
            "producer_component_order": "UNKNOWN",
            "author_spatial_lookup": "data[:, iz, iy, ix]",
            "author_component_order": [2, 1, 0], "velocity_factor": 52,
            "scalar_error_factor": 52, "radial_covariance_interpretation": "NOT_QUALIFIED",
            "full_notebook_downloaded_or_executed": False,
            "github_commit": "c9351d81ea224abec0e75ad4ce03d6a0ed6722b0",
            "source": "https://github.com/Leolardo/Laniakea_Backreaction_nb/blob/c9351d81ea224abec0e75ad4ce03d6a0ed6722b0/main.ipynb",
            "prefix_bytes": 13001, "full_notebook_bytes_reported_by_intake": 16369673}


def parse_probe(text):
    records = [ast.literal_eval(line) for line in text.splitlines() if line.startswith("{'box':")]
    expected = {(1000., 32.), (1000., 31.5), (500., 32.), (500., 31.5)}
    seen = set()
    for record in records:
        key = (record["box"], record["origin_index"])
        if key in seen or key not in expected:
            raise ValueError("duplicate or unexpected probe convention")
        seen.add(key)
        means = np.asarray(record["xyz_means"], dtype=float)
        counts = np.asarray(record["counts"])
        if means.shape != (6, 3) or counts.shape != (6,):
            raise ValueError("missing probe radius/component row")
        if not np.isfinite(means).all() or not np.isfinite(counts).all():
            raise ValueError("nonfinite captured probe")
        if not np.all(counts == counts.astype(int)) or np.any(counts <= 0):
            raise ValueError("invalid voxel count")
        # Captured command fixes radius order; the parser does not recompute its grid.
        if not np.all(np.diff(counts) > 0):
            raise ValueError("duplicate or unordered probe radius row")
        recorded = record["max_abs_difference_from_published_rounded_kms"]
        if not np.isclose(np.max(np.abs(means - EXPECTED_TABLE)), recorded, atol=1e-10, rtol=0):
            raise ValueError("captured probe summary inconsistent")
    if seen != expected:
        raise ValueError("missing probe convention")
    return records


def rounding_parity(values, printed):
    """Closed +/-0.5 interval; exact ties are rounding-compatible, not tie-rule proof."""
    values = np.asarray(values, dtype=float)
    printed = np.asarray(printed, dtype=float)
    if values.shape != printed.shape or not np.isfinite(values).all() or not np.isfinite(printed).all():
        raise ValueError("finite matching shapes required")
    return np.abs(values - printed) <= 0.5


def compare(records, table):
    scenarios = []
    for record in records:
        # xyz_means already reverses raw channels. Reversing again is the sole
        # explicit alternative [0,1,2], not a search over component permutations.
        for name, order, means in [
            ("AUTHOR_REVERSED", [2, 1, 0], np.asarray(record["xyz_means"])),
            ("ALTERNATIVE_UNREVERSED", [0, 1, 2], np.asarray(record["xyz_means"])[:, ::-1]),
        ]:
            delta = means - np.asarray(table["vectors"])
            parity = rounding_parity(means, table["vectors"])
            truncated = [record["box"] == 500. and r > 250 for r in RADII]
            source_case = record["box"] == 1000. and record["origin_index"] == 32.
            scenarios.append({"L_hinv_Mpc": record["box"], "index_origin": record["origin_index"],
                              "component_convention": name, "raw_component_order": order,
                              "scope": "AUTHOR_SOURCE_GEOMETRY" if source_case else "ILLUSTRATIVE_ONLY_NOT_OPTIMIZED",
                              "radii": RADII, "counts": record["counts"], "means_kms": means.tolist(),
                              "residuals_kms": delta.tolist(), "component_rounding_parity": parity.tolist(),
                              "row_rounding_parity": parity.all(axis=1).tolist(),
                              "all_six_rows_rounding_parity": bool(parity.all()),
                              "max_abs_residual_kms": float(np.abs(delta).max()),
                              "sphere_truncated_invalid_mask": truncated,
                              "full_sphere_qualification": "NOT_QUALIFIED",
                              "scientific_agreement_test": "NOT_PERFORMED"})
    return {"status": "SOURCE_CONFLICT", "downstream_H02_physical_flow_use": "HOLD",
            "producer64_geometry": "HOLD", "scientific_admission": "HOLD",
            "rounding_rule": "abs(component - printed integer) <= 0.5 km/s; closed ties compatible only",
            "rounding_rule_is_scientific_tolerance": False,
            "spatial_axis_permutation_qualified": False, "fitted_or_selected_convention": None,
            "scenarios": scenarios}


def build_result():
    inputs = sealed_inputs()
    table = parse_table((EXTERNAL / "courtois_2211.16390v4.html").read_text())
    geometry = check_prefix((EXTERNAL / "giani_main_first13001bytes.jsonpart").read_text())
    records = parse_probe((EXTERNAL / "SPHERE_PROBE_TRANSCRIPT.txt").read_text())
    result = compare(records, table)
    result.update({"owner": "obsstat", "scope": "finite external source-convention comparison",
                   "claim_tier": "C0", "claim_status": "DIAGNOSTIC_ONLY", "non_claim_bearing": True,
                   "transfer_source": "none", "inputs": inputs, "table": table, "author_geometry": geometry,
                   "original_42_nodes": "UNCHANGED", "grid_reexecuted": False,
                   "probe_executor_requested": "gpt-6-astra/xhigh", "probe_executor_observed": "UNKNOWN",
                   "probe_launch_time_verification": "NOT_AVAILABLE; captured transcript reused",
                   "probe_recorded_head": INTAKE_HEAD,
                   "probe_recorded_command_exit": 0, "probe_recorded_wall_seconds": 0.989577891,
                   "comparison_executor_requested": "gpt-6.1-sol/high", "comparison_executor_observed": "UNKNOWN",
                   "caveats": ["Producer centering and component order remain UNKNOWN.",
                               "Spherical masks cannot qualify spatial-axis permutation.",
                               "Equal-weight strict-radius captured masks are not a proven producer estimator.",
                               "No origin, scale, weights, or component-order optimization.",
                               "No physical-host query, error propagation, interpolation, likelihood, or solver.",
                               "No independent morphology atlas or physical flow correction qualification."]})
    return result


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def plot(result):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharex=True)
    for j, ax in enumerate(axes):
        ax.axhspan(-0.5, 0.5, color="0.75", label="printed rounding interval")
        for scenario, style in zip(result["scenarios"][:2], ["o-", "s--"]):
            label = "author [2,1,0]" if scenario["raw_component_order"] == [2, 1, 0] else "alternative [0,1,2]"
            ax.plot(RADII, np.asarray(scenario["residuals_kms"])[:, j], style, label=label)
        ax.axhline(0, color="0.4", linewidth=.6)
        ax.set_title(["Vx", "Vy", "Vz"][j])
        ax.set_xlabel(r"Radius [$h_{100}^{-1}$ Mpc]")
        ax.grid(alpha=.2)
    axes[0].set_ylabel("Captured mean - printed Table 1 [km/s]")
    axes[1].legend(fontsize=7)
    fig.suptitle("Grouped CF4 source comparison: L=1000, origin index 32; SOURCE_CONFLICT")
    fig.text(.5, .015, "Diagnostic only. +/-0.5 is table rounding, not a scientific tolerance. No spatial-axis qualification.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .055, 1, .93))
    for extension in ["png", "pdf"]:
        fig.savefig(HERE / f"GROUPED_FLOW_SOURCE.{extension}", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    result = build_result()
    write_json(HERE / "SOURCE_COMPARISON.json", result)
    write_json(HERE / "TABLE1_LITERAL.json", result["table"])
    plot(result)
    print(json.dumps({"status": result["status"], "scenarios": [
        {k: s[k] for k in ["L_hinv_Mpc", "index_origin", "component_convention", "max_abs_residual_kms", "row_rounding_parity", "sphere_truncated_invalid_mask"]}
        for s in result["scenarios"]]}, indent=2))
