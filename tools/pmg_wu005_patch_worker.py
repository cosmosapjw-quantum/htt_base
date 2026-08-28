#!/usr/bin/env python3
"""Apply the bounded PMG-WU-005 attended-path carrier threading patch."""

from pathlib import Path


PATH = Path("scripts/observed_runs/run_planck_pr3.py")


def require_one(lines: list[str], value: str, *, start: int = 0, end: int | None = None) -> int:
    stop = len(lines) if end is None else end
    hits = [index for index in range(start, stop) if lines[index] == value]
    if len(hits) != 1:
        raise SystemExit(f"expected one scoped anchor, found {len(hits)}: {value}")
    return hits[0]


def function_bounds(lines: list[str], start_marker: str, end_marker: str) -> tuple[int, int]:
    start = require_one(lines, start_marker)
    end = require_one(lines, end_marker, start=start + 1)
    return start, end


def main() -> None:
    lines = PATH.read_text().splitlines()

    import_anchor = (
        "from obsstat.covariance_replay import "
        "validate_sample_covariance_replay  # noqa: E402"
    )
    import_marker = "from obsstat.planck_irrep_carrier import (  # noqa: E402"
    if import_marker not in lines:
        index = require_one(lines, import_anchor) + 1
        lines[index:index] = [
            import_marker,
            "    OBSERVATION_ROW_ID,",
            "    replay_planck_irrep_carrier,",
            "    scalar_feature_closure_report,",
            "    write_planck_irrep_carrier,",
            ")",
            "from obsstat.planck_paired300_carrier_execution import (  # noqa: E402",
            "    carrier_vector_from_alm,",
            ")",
        ]

    helper_marker = "def _component_features_from_real_carrier("
    if helper_marker not in lines:
        _, helper_insert = function_bounds(
            lines,
            "def _process_ffp10_component(",
            "def _mark_observed_data_open_attempt() -> None:",
        )
        helpers = [
            "",
            "",
            helper_marker,
            "    carrier: np.ndarray,",
            ") -> np.ndarray:",
            "    \"\"\"Project one frozen 32-real carrier back to the twelve features.\"\"\"",
            "",
            "    vector = np.asarray(carrier, dtype=np.float64)",
            "    if vector.shape != (JOINT_CUTSKY_RETAINED_DIMENSION,):",
            "        raise PlanckWorkerError(\"real carrier dimension drifted\")",
            "    alm = real_vector_to_alm(vector, lmin=LMIN, lmax=LMAX)",
            "    vectors2 = extract_multipole_vectors(alm, ell=2, lmax=LMAX)",
            "    vectors3 = extract_multipole_vectors(alm, ell=3, lmax=LMAX)",
            "    return component_features_from_vectors(",
            "        alm, vectors2=vectors2, vectors3=vectors3, lmax=LMAX",
            "    )",
            "",
            "",
            "def _process_ffp10_component_with_carrier(",
            "    path: Path,",
            "    *,",
            "    array_name: str,",
            "    row_ids: tuple[str, ...],",
            "    component: str,",
            "    context: Mapping[str, object],",
            "    chunk_rows: int = 32,",
            ") -> tuple[np.ndarray, np.ndarray]:",
            "    \"\"\"Process each compact null row once and preserve the same-fit carrier.\"\"\"",
            "",
            "    try:",
            "        with np.load(path, allow_pickle=False, mmap_mode=\"r\") as bundle:",
            "            maps = np.asarray(bundle[array_name])",
            "            if maps.ndim != 2 or maps.shape[0] != len(row_ids):",
            "                raise PlanckWorkerError(\"FFP10 same-sky map pairing is incomplete\")",
            "            features: list[np.ndarray] = []",
            "            carriers: list[np.ndarray] = []",
            "            for start in range(0, len(row_ids), chunk_rows):",
            "                chunk = maps[start : start + chunk_rows]",
            "                if not np.all(np.isfinite(chunk)):",
            "                    raise PlanckWorkerError(\"FFP10 map stack contains nonfinite values\")",
            "                for pixel_map in chunk:",
            "                    value, _, alm = _process_map(",
            "                        np.asarray(pixel_map, dtype=float),",
            "                        component=component,",
            "                        context=context,",
            "                    )",
            "                    features.append(value)",
            "                    carriers.append(carrier_vector_from_alm(alm))",
            "    except (KeyError, OSError, ValueError) as exc:",
            "        raise PlanckWorkerError(\"FFP10 bundle is not a safe numeric NPZ\") from exc",
            "    feature_matrix = np.asarray(features, dtype=np.float64)",
            "    carrier_matrix = np.asarray(carriers, dtype=np.float64)",
            "    if feature_matrix.shape != (len(row_ids), 12):",
            "        raise PlanckWorkerError(\"FFP10 feature matrix shape drifted\")",
            "    if carrier_matrix.shape != (",
            "        len(row_ids), JOINT_CUTSKY_RETAINED_DIMENSION",
            "    ):",
            "        raise PlanckWorkerError(\"FFP10 carrier matrix shape drifted\")",
            "    return feature_matrix, carrier_matrix",
        ]
        lines[helper_insert:helper_insert] = helpers

    run_start, run_end = function_bounds(
        lines,
        "def run_pr315_joint_cutsky_attended(",
        "def export_pr315_portable_evidence(",
    )
    old_start = "        null_features = _process_ffp10_component("
    start = require_one(lines, old_start, start=run_start, end=run_end)
    close = start
    while close < run_end and lines[close] != "        )":
        close += 1
    if close >= run_end:
        raise SystemExit("null-processing call did not close")
    close += 1
    observed_block = [
        "        observed_features, _, _ = _process_map(",
        "            observed_map, component=\"SMICA\", context=context",
        "        )",
    ]
    if lines[close : close + len(observed_block)] != observed_block:
        raise SystemExit("attended observation-processing block drifted")
    lines[start : close + len(observed_block)] = [
        "        null_features, null_carrier = (",
        "            _process_ffp10_component_with_carrier(",
        "                components[\"null\"],",
        "                array_name=\"smica_maps\",",
        "                row_ids=row_ids,",
        "                component=\"SMICA\",",
        "                context=context,",
        "            )",
        "        )",
        "        observed_features, _, observed_alm = _process_map(",
        "            observed_map, component=\"SMICA\", context=context",
        "        )",
        "        observed_carrier = carrier_vector_from_alm(observed_alm)",
    ]

    run_start, run_end = function_bounds(
        lines,
        "def run_pr315_joint_cutsky_attended(",
        "def export_pr315_portable_evidence(",
    )
    replay_start = require_one(
        lines,
        "        portable_replay = replay_pr315_feature_package(",
        start=run_start,
        end=run_end,
    )
    replay_close = replay_start
    while replay_close < run_end and lines[replay_close] != "        )":
        replay_close += 1
    if replay_close >= run_end:
        raise SystemExit("feature replay call did not close")
    replay_close += 1
    carrier_marker = "        carrier_package = output_dir / \"paired300_irrep_carrier.npz\""
    if carrier_marker not in lines[run_start:run_end]:
        carrier_block = [
            "        observed_projected = _component_features_from_real_carrier(",
            "            observed_carrier",
            "        )",
            "        null_projected = np.asarray(",
            "            [",
            "                _component_features_from_real_carrier(row)",
            "                for row in null_carrier",
            "            ],",
            "            dtype=np.float64,",
            "        )",
            "        scalar_closure = scalar_feature_closure_report(",
            "            observed_expected=observed_features,",
            "            observed_projected=observed_projected,",
            "            null_expected=null_features,",
            "            null_projected=null_projected,",
            "        )",
            "        _write_json(output_dir / \"scalar_closure.json\", scalar_closure)",
            carrier_marker,
            "        carrier_metadata = output_dir / \"paired300_irrep_carrier.json\"",
            "        transfer_identity = {",
            "            \"source_beam_sha256\": _array_digest(",
            "                np.asarray(context[\"source_beams\"][\"SMICA\"])",
            "            ),",
            "            \"source_pixel_window_sha256\": _array_digest(",
            "                np.asarray(context[\"source_pixels\"][\"SMICA\"])",
            "            ),",
            "            \"target_beam_sha256\": _array_digest(",
            "                np.asarray(context[\"target_beam\"])",
            "            ),",
            "            \"target_pixel_window_sha256\": _array_digest(",
            "                np.asarray(context[\"target_pixel\"])",
            "            ),",
            "        }",
            "        carrier_receipt = write_planck_irrep_carrier(",
            "            package_path=carrier_package,",
            "            metadata_path=carrier_metadata,",
            "            observed_real_alm=observed_carrier,",
            "            null_real_alm=null_carrier,",
            "            row_ids=(OBSERVATION_ROW_ID, *row_ids),",
            "            null_ordered_row_ids_sha256=SMICA_EXISTING_INVENTORY_ID,",
            "            operator_identity=observation_operator,",
            "            transfer_identity=transfer_identity,",
            "            source_manifest_sha256=str(",
            "                acceptance[\"raw_input_manifest_sha256\"]",
            "            ),",
            "            scalar_feature_package_sha256=str(",
            "                package_receipt[\"package_sha256\"]",
            "            ),",
            "        )",
            "        carrier_replay = replay_planck_irrep_carrier(",
            "            package_path=carrier_package,",
            "            metadata_path=carrier_metadata,",
            "        )",
        ]
        lines[replay_close:replay_close] = carrier_block

    run_start, run_end = function_bounds(
        lines,
        "def run_pr315_joint_cutsky_attended(",
        "def export_pr315_portable_evidence(",
    )
    result_anchor = require_one(
        lines,
        "            \"feature_package\": package_receipt,",
        start=run_start,
        end=run_end,
    )
    if "            \"irrep_carrier\": carrier_receipt," not in lines[run_start:run_end]:
        lines[result_anchor + 1 : result_anchor + 1] = [
            "            \"irrep_carrier\": carrier_receipt,",
            "            \"irrep_carrier_replay\": carrier_replay,",
            "            \"scalar_closure\": scalar_closure,",
        ]

    run_start, run_end = function_bounds(
        lines,
        "def run_pr315_joint_cutsky_attended(",
        "def export_pr315_portable_evidence(",
    )
    terminal_anchor = require_one(
        lines,
        "                \"feature_package_sha256\": package_receipt[\"package_sha256\"],",
        start=run_start,
        end=run_end,
    )
    if "                \"irrep_carrier_replay\": \"MATCH\"," not in lines[run_start:run_end]:
        lines[terminal_anchor + 1 : terminal_anchor + 1] = [
            "                \"irrep_carrier_package_sha256\": carrier_receipt[",
            "                    \"package_sha256\"",
            "                ],",
            "                \"irrep_carrier_replay\": \"MATCH\",",
            "                \"scalar_closure\": scalar_closure[\"state\"],",
        ]

    PATH.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
