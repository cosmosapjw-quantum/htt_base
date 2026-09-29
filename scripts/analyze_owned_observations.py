#!/usr/bin/env python3
"""Bounded, manifest-driven entrypoint for owner-held observational products."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (REPO_ROOT, REPO_ROOT / "htt", REPO_ROOT / "htt" / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from htt.obsstat.owned_data_adapter import bind_owned_products, binding_report, load_matrix
from htt.obsstat.spectral_residual_analysis import (
    SpectralContractError, analyze_residuals, spectrum_from_npz, write_outputs,
)
from htt.obsstat.owned_lowell_analysis import analyze_nside16_map
from htt.obsstat.catalogs.owned_desi_analysis import summarize_desi
from htt.obsstat.owned_cf4_query_analysis import summarize_cf4_queries


def _theory(path: Path, spectrum: str) -> tuple[np.ndarray, np.ndarray, str]:
    key = f"D_{spectrum.upper()}"
    with np.load(path, allow_pickle=False) as arrays:
        if "ell" not in arrays.files or key not in arrays.files:
            raise SpectralContractError(f"theory NPZ lacks ell/{key}")
        return arrays["ell"].copy(), arrays[key].copy(), "Dl"


def run(args: argparse.Namespace) -> dict:
    matrix = load_matrix(args.matrix)
    bindings = bind_owned_products(matrix, repo_root=args.repo_root, external_workdir=args.external_workdir)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    bindings_path = output / "owned_data_bindings.json"
    bindings_path.write_text(json.dumps(binding_report(bindings), indent=2, allow_nan=False) + "\n")
    theory_path = args.theory.resolve()
    analyses, skipped = [], []
    rows_by_id = {row["dataset_id"]: row for row in matrix["datasets"]}
    for binding in bindings:
        if binding.work_packet != "DATA-02" or binding.role_for_analysis != "observed_spectrum_or_release_container":
            continue
        if binding.path_status != "PRESENT_FILE":
            skipped.append({"dataset_id": binding.dataset_id, "reason": binding.path_status})
            continue
        metadata = dict(rows_by_id[binding.dataset_id].get("index_metadata", {}))
        metadata["overlap_family"] = binding.overlap_family
        try:
            observed = spectrum_from_npz(binding.resolved_path, dataset_id=binding.dataset_id, metadata=metadata)
            theory_ell, theory_values, quantity = _theory(theory_path, observed.spectrum)
            result = analyze_residuals(observed, theory_ell, theory_values, theory_quantity=quantity)
            paths = write_outputs(result, output / "spectra")
            analyses.append({"dataset_id": binding.dataset_id, "status": "EXECUTED_DIAGNOSTIC", "outputs": paths,
                             "law_status": result["law_status"]})
        except (OSError, KeyError, ValueError, SpectralContractError) as exc:
            skipped.append({"dataset_id": binding.dataset_id, "reason": f"SCHEMA_OR_ALIGNMENT_BLOCKED: {exc}"})
    lane_status = "EXECUTED" if analyses else "HOLD_INPUT_INCOMPLETE"
    binding_by_id = {binding.dataset_id: binding for binding in bindings}
    branch_outputs: dict[str, list[dict[str, str]]] = {"DATA-03": [], "DATA-04": [], "DATA-05": []}

    mask_binding = binding_by_id.get("planck.temp_mask.nside16")
    if mask_binding is not None and mask_binding.path_status == "PRESENT_FILE":
        with np.load(mask_binding.resolved_path, allow_pickle=False) as mask_arrays:
            mask_key = "mask" if "mask" in mask_arrays.files else None
            mask = mask_arrays[mask_key].copy() if mask_key else None
        if mask is not None:
            for dataset_id in ("planck.commander.nside16", "planck.smica.nside16"):
                binding = binding_by_id.get(dataset_id)
                if binding is None or binding.path_status != "PRESENT_FILE":
                    continue
                with np.load(binding.resolved_path, allow_pickle=False) as arrays:
                    map_key = "I" if "I" in arrays.files else "map" if "map" in arrays.files else None
                    if map_key is None:
                        continue
                    components = [arrays[map_key].copy()]
                    if "Q" in arrays.files and "U" in arrays.files:
                        components.extend([arrays["Q"].copy(), arrays["U"].copy()])
                    stored_unit = str(arrays["unit"].item()) if "unit" in arrays.files else None
                map_metadata = rows_by_id[dataset_id].get("index_metadata", {})
                units = stored_unit or map_metadata.get("unit")
                ordering = str(map_metadata.get("ordering", "")).split()[0]
                result = analyze_nside16_map(np.asarray(components), mask, dataset_id=dataset_id,
                                             units=str(units), ordering=ordering, frame="GALACTIC")
                path = output / f"{dataset_id.replace('.', '_')}_lowell_features.json"
                path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
                branch_outputs["DATA-03"].append({"dataset_id": dataset_id, "output": str(path)})

    for binding in bindings:
        if binding.work_packet == "DATA-04" and binding.path_status == "PRESENT_FILE" and Path(binding.resolved_path).suffix == ".npz":
            with np.load(binding.resolved_path, allow_pickle=False) as arrays:
                payload = {key: arrays[key].copy() for key in arrays.files}
            identity = binding.dataset_id.upper()
            tracer = next((name for name in ("BGS", "LRG", "QSO") if name in identity), "UNKNOWN")
            cap = next((name for name in ("NGC", "SGC") if name in identity), "UNKNOWN")
            result = summarize_desi(payload, dataset_id=binding.dataset_id, tracer=tracer, cap=cap,
                                    z_edges=[0.0, 0.2, 0.4, 0.6, 1.0, 1.5, 3.0])
            path = output / f"{binding.dataset_id.replace('.', '_')}_desi_summary.json"
            path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
            branch_outputs["DATA-04"].append({"dataset_id": binding.dataset_id, "output": str(path)})

    for binding in bindings:
        if binding.work_packet == "DATA-05" and "query_batch" in binding.dataset_id and binding.path_status == "PRESENT_FILE" and Path(binding.resolved_path).suffix == ".npz":
            with np.load(binding.resolved_path, allow_pickle=False) as arrays:
                payload = {key: arrays[key].copy() for key in arrays.files}
            result = summarize_cf4_queries(payload, dataset_id=binding.dataset_id,
                                            depth_edges_mpc_h=[0.0, 50.0, 100.0, 200.0, 500.0])
            path = output / f"{binding.dataset_id.replace('.', '_')}_cf4_depth.json"
            path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
            branch_outputs["DATA-05"].append({"dataset_id": binding.dataset_id, "output": str(path)})
    report = {
        "schema": "htt.owned_observation_analysis_report/v1",
        "matrix_dataset_count": len(bindings),
        "bindings": str(bindings_path),
        "spectral_lane": {"status": lane_status, "executed": analyses, "skipped": skipped},
        "optional_lanes": {
            "DATA-03": "EXECUTED_DIAGNOSTIC" if branch_outputs["DATA-03"] else "IMPLEMENTED_HOLD_INPUT_INCOMPLETE",
            "DATA-04": "EXECUTED_DIAGNOSTIC" if branch_outputs["DATA-04"] else "IMPLEMENTED_HOLD_INPUT_INCOMPLETE",
            "DATA-05": "EXECUTED_DIAGNOSTIC" if branch_outputs["DATA-05"] else "IMPLEMENTED_HOLD_INPUT_INCOMPLETE",
            "DATA-06": "NOT_REQUESTED_NO_COMPLETE_LIKELIHOOD_LAW",
            "DATA-07": "NOT_REQUESTED_NO_PHYSICAL_RESPONSE_OR_JOINT_BODY",
        },
        "branch_outputs": branch_outputs,
        "cross_survey_combination": "NOT_PERFORMED",
        "scientific_claim_promotion": False,
        "claim_ceiling": "diagnostic-only; missing laws and external bytes remain unavailable",
    }
    report_path = output / "owned_data_analysis_report.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    report["report_path"] = str(report_path)
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--matrix", type=Path, required=True, help="handoff ZIP, folder, or DATASET_ANALYSIS_MATRIX.json")
    result.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    result.add_argument("--external-workdir", type=Path)
    result.add_argument("--theory", type=Path, default=REPO_ROOT / "data" / "camb_ref_planck2018.npz")
    result.add_argument("--output", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    report = run(args)
    print(json.dumps({"report": report["report_path"], "spectral_status": report["spectral_lane"]["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
