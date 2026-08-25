#!/usr/bin/env python3
"""HSC/KiDS typed spin-2 worker and observation-free synthetic profile."""

from __future__ import annotations

import os


THREAD_CONTROLS = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}
for _name, _value in THREAD_CONTROLS.items():
    os.environ[_name] = _value

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import resource
import sys
import tempfile
import time
from typing import BinaryIO, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT / "htt", ROOT / "htt/src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from common.data_identity import (  # noqa: E402
    AdmissionStatus,
    canonical_sha256,
    DataIdentityError,
    _regular_beneath,
    load_lane_registry,
    replay_lane_admission_decision,
)
from obsstat.hsc_kids_current_stack import (  # noqa: E402
    analyze_hsc_released_sacc,
    HscKidsCurrentStackError,
    LabelledEBField,
    PseudoClOperator,
    RawSpin2Field,
    SurveyIdentity,
    TomographyBin,
    analyze_joint_response,
    derive_paired_same_sky_joint_covariance,
    execute_tomography,
    label_eb,
    parallel_transport_axis,
    transported_headless_axis_alignment,
    validate_survey_pair,
)


REGISTRY = ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
REQUIRED_COMPONENTS = (
    "hsc_product",
    "kids_product",
    "hsc_mask",
    "kids_mask",
    "hsc_randoms",
    "kids_randoms",
    "hsc_psf",
    "kids_psf",
    "hsc_n_z",
    "kids_n_z",
    "hsc_shear_calibration",
    "kids_shear_response",
    "hsc_covariance",
    "kids_covariance",
    "hsc_kids_cross_covariance",
)
PROFILE_ROWS = {"1": 1, "8": 8, "32": 32, "128": 128, "full": 256}
PR321_HSC_SACC_SIZE = 22340160
PR321_HSC_SACC_SHA256 = (
    "a28f9e2e088e92d96d2d87083a6eeeac4c0c84c6b48e033bd3d1dc1bf0d8958f"
)


class HscKidsWorkerError(RuntimeError):
    """Raised before an HSC/KiDS result when the worker contract drifts."""


def _strict_json_bytes(raw: bytes, *, label: str) -> Mapping[str, object]:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise HscKidsWorkerError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise HscKidsWorkerError(f"{label} contains non-finite constant {value}")

    try:
        payload = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HscKidsWorkerError(f"{label} is not strict JSON") from exc
    if not isinstance(payload, Mapping):
        raise HscKidsWorkerError(f"{label} must be a JSON object")
    return payload


def _raw_hash(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _array_sha256(value: object) -> str:
    array = np.asarray(value, dtype="<f8", order="C")
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def _legacy_sacc_order_notice(output: str) -> bool:
    return output.splitlines() == [
        "Warning: The FITS format without the 'sacc_ordering' column is deprecated",
        "Assuming data rows are in the correct order as it was before version 1.0.",
    ]


def _load_hsc_sacc(source: BinaryIO) -> Mapping[str, object]:
    try:
        from contextlib import redirect_stdout
        from io import StringIO
        import sacc
    except ImportError as exc:
        raise HscKidsWorkerError(
            "HSC SACC inspection requires the declared local sacc==2.1.2 runtime"
        ) from exc
    if getattr(sacc, "__version__", None) != "2.1.2":
        raise HscKidsWorkerError("HSC SACC loader version must equal 2.1.2")
    try:
        loader_output = StringIO()
        with redirect_stdout(loader_output):
            payload = sacc.Sacc.load_fits(source)
    except Exception as exc:
        raise HscKidsWorkerError("HSC SACC FITS loading failed") from exc
    direct_output = loader_output.getvalue()
    legacy_warning = _legacy_sacc_order_notice(direct_output)
    if direct_output and not legacy_warning:
        raise HscKidsWorkerError("HSC SACC loader emitted unexpected output")
    data_types = tuple(payload.get_data_types())
    if data_types != ("cl_ee",):
        raise HscKidsWorkerError("HSC SACC data-type inventory drifted")
    tracer_order = tuple(payload.tracers)
    tracer_quantities = tuple(payload.tracers[name].quantity for name in tracer_order)
    tracer_z = tuple(
        np.asarray(payload.tracers[name].z, dtype=float) for name in tracer_order
    )
    tracer_nz = tuple(
        np.asarray(payload.tracers[name].nz, dtype=float) for name in tracer_order
    )

    pairs: list[tuple[str, str]] = []
    pair_rows: dict[tuple[str, str], list[object]] = {}
    row_values: list[float] = []
    row_indices_by_pair: dict[tuple[str, str], list[int]] = {}
    for row_index, row in enumerate(payload.data):
        pair = tuple(row.tracers)
        if len(pair) != 2:
            raise HscKidsWorkerError("HSC SACC tracer-pair shape drifted")
        typed_pair = (str(pair[0]), str(pair[1]))
        if typed_pair not in pair_rows:
            pairs.append(typed_pair)
            pair_rows[typed_pair] = []
            row_indices_by_pair[typed_pair] = []
        pair_rows[typed_pair].append(row)
        row_indices_by_pair[typed_pair].append(row_index)
        row_values.append(float(row.value))

    ell_by_pair: list[tuple[float, ...]] = []
    window_shapes: list[tuple[int, int]] = []
    window_column_sums: list[tuple[float, ...]] = []
    pair_selection_indices_match = True
    pair_selection_values_match = True
    covariance_selection_indices_match = True
    dense_covariance = np.asarray(payload.covariance.dense, dtype=float)
    for pair in pairs:
        rows = pair_rows[pair]
        if len(rows) != 17:
            raise HscKidsWorkerError("HSC SACC bandpower block length drifted")
        ell_by_pair.append(tuple(float(row.tags["ell"]) for row in rows))
        first_window = rows[0].tags["window"]
        weights = np.asarray(first_window.weight, dtype=float)
        values = np.asarray(first_window.values, dtype=float)
        if values.shape != (weights.shape[0],):
            raise HscKidsWorkerError("HSC SACC window harmonic support drifted")
        for index, row in enumerate(rows):
            window = row.tags["window"]
            if (
                int(row.tags["window_ind"]) != index
                or not np.array_equal(np.asarray(window.values), values)
                or not np.array_equal(np.asarray(window.weight), weights)
            ):
                raise HscKidsWorkerError("HSC SACC window row binding drifted")
        window_shapes.append(tuple(int(value) for value in weights.shape))
        window_column_sums.append(tuple(float(value) for value in weights.sum(axis=0)))
        stored_indices = np.asarray(row_indices_by_pair[pair], dtype=int)
        api_indices = np.asarray(
            payload.indices(data_type="cl_ee", tracers=pair), dtype=int
        )
        api_values = np.asarray(
            payload.get_mean(data_type="cl_ee", tracers=pair), dtype=float
        )
        stored_values = np.asarray([row.value for row in rows], dtype=float)
        pair_selection_indices_match &= np.array_equal(api_indices, stored_indices)
        pair_selection_values_match &= np.array_equal(api_values, stored_values)
        covariance_selection_indices_match &= np.array_equal(
            dense_covariance[np.ix_(api_indices, api_indices)],
            dense_covariance[np.ix_(stored_indices, stored_indices)],
        )

    payload_mean = np.asarray(payload.mean, dtype=float)
    row_values_array = np.asarray(row_values, dtype=float)
    expected_blocks = [
        list(range(pair_index * 17, (pair_index + 1) * 17))
        for pair_index in range(len(pairs))
    ]
    pair_blocks_contiguous = (
        [row_indices_by_pair[pair] for pair in pairs] == expected_blocks
    )

    return {
        "data_type": data_types[0],
        "tracer_order": tracer_order,
        "tracer_quantities": tracer_quantities,
        "tracer_z": tracer_z,
        "tracer_nz": tracer_nz,
        "tracer_pairs": tuple(pairs),
        "ell_by_pair": tuple(ell_by_pair),
        "window_shapes": tuple(window_shapes),
        "window_column_sums": tuple(window_column_sums),
        "data_vector": payload_mean,
        "covariance": dense_covariance,
        "loader_version": "2.1.2",
        "legacy_stored_order": legacy_warning,
        "legacy_order_crosscheck": {
            "row_values_match_payload_mean": np.array_equal(
                row_values_array, payload_mean
            ),
            "pair_blocks_contiguous": pair_blocks_contiguous,
            "pair_selection_indices_match": bool(pair_selection_indices_match),
            "pair_selection_values_match": bool(pair_selection_values_match),
            "covariance_selection_indices_match": bool(
                covariance_selection_indices_match
            ),
        },
        "observed_payload_validated": True,
    }


def inspect_hsc_sacc(
    *, path: Path, confirmation_sha256: str
) -> dict[str, object]:
    if confirmation_sha256 != PR321_HSC_SACC_SHA256:
        raise HscKidsWorkerError("HSC SACC confirmation identity drifted")
    if not path.is_file() or path.is_symlink():
        raise HscKidsWorkerError("HSC SACC identity requires one regular file")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise HscKidsWorkerError("HSC SACC identity open failed") from exc
    if len(raw) != PR321_HSC_SACC_SIZE:
        raise HscKidsWorkerError("HSC SACC identity byte size drifted")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PR321_HSC_SACC_SHA256:
        raise HscKidsWorkerError("HSC SACC identity SHA-256 drifted")
    inputs = _load_hsc_sacc(BytesIO(raw))
    result = analyze_hsc_released_sacc(**inputs)
    result["input_identity"] = {
        "source_release": "HSC_S19A_Y3",
        "product": "dalal23/hsc_y3_fourier_space_data_vector.sacc",
        "byte_size": PR321_HSC_SACC_SIZE,
        "sha256": digest,
        "data_vector_sha256_float64_le": _array_sha256(inputs["data_vector"]),
        "covariance_sha256_float64_le": _array_sha256(inputs["covariance"]),
    }
    result["generating_procedure"] = "scripts/observed_runs/run_hsc_kids.py"
    result["worker_sha256"] = _file_sha256(Path(__file__))
    return result


def _validate_attended_admission_binding(raw: bytes, decision) -> None:
    record_ids = [record.record_id for record in decision.records]
    if (
        os.environ.get("HTT_ATTENDED_ADMISSION_SHA256") != _raw_hash(raw)
        or os.environ.get("HTT_ATTENDED_ADMISSION_BUNDLE_ID")
        != decision.lane_admission_bundle_id
        or os.environ.get("HTT_ATTENDED_ORDERED_RECORD_IDS_SHA256")
        != canonical_sha256(record_ids)
    ):
        raise HscKidsWorkerError("attended admission acceptance binding drifted")


def _load_admission(path: Path):
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise HscKidsWorkerError("HSC/KiDS admission replay failed") from exc
    try:
        registry = load_lane_registry(REGISTRY)
        decision = replay_lane_admission_decision(
            _strict_json_bytes(raw, label="HSC/KiDS admission"), registry=registry
        )
    except (DataIdentityError, HscKidsWorkerError) as exc:
        raise HscKidsWorkerError(f"HSC/KiDS admission replay failed: {exc}") from exc
    if (
        decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
        or decision.lane_id != "HSC_KIDS"
        or tuple(record.component_id for record in decision.records) != REQUIRED_COMPONENTS
        or decision.lane_admission_bundle_id is None
    ):
        raise HscKidsWorkerError("HSC/KiDS admission is not complete identity admission")
    _validate_attended_admission_binding(raw, decision)
    return decision


def _mark_observed_data_open_attempt() -> None:
    output_text = os.environ.get("HTT_ATTENDED_OUTPUT_DIR", "")
    output = Path(output_text)
    marker = output / "observed_data_opened.json"
    if (
        os.environ.get("HTT_ATTENDED_START_WRITTEN") != "1"
        or not output_text
        or not output.is_absolute()
        or output.is_symlink()
        or not output.is_dir()
        or not (output / "start.json").is_file()
        or os.environ.get("HTT_ATTENDED_DATA_OPEN_MARKER") != str(marker)
        or marker.exists()
        or marker.is_symlink()
    ):
        raise HscKidsWorkerError("attended output/start/data-open binding is invalid")
    _write_json(marker, {"state": "OBSERVED_DATA_OPEN_ATTEMPTED"})


def _admitted_documents(
    decision, *, data_root: Path
) -> dict[str, Mapping[str, object]]:
    if (
        not data_root.is_absolute()
        or data_root.is_symlink()
        or not data_root.is_dir()
        or data_root.resolve() != data_root
    ):
        raise HscKidsWorkerError("data root must be an absolute regular directory")
    bindings = decision.records[0].native_identity_profile.get("component_bindings")
    if not isinstance(bindings, Sequence) or len(bindings) != len(REQUIRED_COMPONENTS):
        raise HscKidsWorkerError("HSC/KiDS native component bindings drifted")
    records = {record.component_id: record for record in decision.records}
    if tuple(records) != REQUIRED_COMPONENTS:
        raise HscKidsWorkerError("HSC/KiDS admitted inventory is incomplete")
    rows = [row for row in bindings if isinstance(row, Mapping)]
    if (
        len(rows) != len(bindings)
        or tuple(row.get("component_id") for row in rows) != REQUIRED_COMPONENTS
    ):
        raise HscKidsWorkerError("HSC/KiDS component binding order drifted")
    result: dict[str, Mapping[str, object]] = {}
    for row in rows:
        component = row.get("component_id")
        relative = row.get("relative_path")
        if component not in records or not isinstance(relative, str):
            raise HscKidsWorkerError("HSC/KiDS component binding identity drifted")
        try:
            path, info = _regular_beneath(data_root, Path(relative), str(component))
            raw = path.read_bytes()
        except DataIdentityError as exc:
            raise HscKidsWorkerError(f"{component} is not an exact admitted file") from exc
        except OSError as exc:
            raise HscKidsWorkerError(f"{component} could not be read") from exc
        record = records[str(component)]
        if (
            info.st_size != record.byte_size
            or len(raw) != record.byte_size
            or _raw_hash(raw) != record.content_sha256
        ):
            raise HscKidsWorkerError(f"{component} no longer matches admission")
        result[str(component)] = _strict_json_bytes(raw, label=str(component))
    return result


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise HscKidsWorkerError(f"{label} must be a mapping")
    return value


def _sequence(value: object, *, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise HscKidsWorkerError(f"{label} must be a sequence")
    return value


def _identity(documents: Mapping[str, Mapping[str, object]], survey: str) -> SurveyIdentity:
    prefix = "hsc" if survey == "HSC" else "kids"
    product = documents[f"{prefix}_product"]
    calibration_component = (
        "hsc_shear_calibration" if survey == "HSC" else "kids_shear_response"
    )
    return SurveyIdentity(
        survey_id=survey,
        release_id=str(product.get("release_id")),
        product_component=f"{prefix}_product",
        mask_component=f"{prefix}_mask",
        randoms_component=f"{prefix}_randoms",
        psf_component=f"{prefix}_psf",
        n_z_component=f"{prefix}_n_z",
        calibration_component=calibration_component,
        covariance_component=f"{prefix}_covariance",
        calibration_role=(
            "multiplicative_shear_calibration"
            if survey == "HSC"
            else "lensfit_shear_response"
        ),
        component_order=str(product.get("component_order")),
        tangent_basis=str(product.get("tangent_basis")),
        spin_convention=str(product.get("spin_convention")),
    )


def _survey_analysis(
    documents: Mapping[str, Mapping[str, object]],
    survey: str,
    identity: SurveyIdentity,
) -> tuple[object, PseudoClOperator, np.ndarray]:
    prefix = "hsc" if survey == "HSC" else "kids"
    product = documents[f"{prefix}_product"]
    mask = documents[f"{prefix}_mask"]
    randoms = documents[f"{prefix}_randoms"]
    psf = documents[f"{prefix}_psf"]
    n_z = documents[f"{prefix}_n_z"]
    calibration = documents[
        "hsc_shear_calibration" if survey == "HSC" else "kids_shear_response"
    ]
    for label, payload in (("mask", mask), ("randoms", randoms), ("PSF", psf), ("n(z)", n_z), ("calibration", calibration)):
        if payload.get("survey_id") != survey:
            raise HscKidsWorkerError(f"{survey} {label} identity was exchanged")
    if randoms.get("status") != "VALIDATED_SELECTION_SUPPORT" or psf.get("status") != "VALIDATED_PSF_SUPPORT":
        raise HscKidsWorkerError(f"{survey} random/PSF support is incomplete")
    gamma1 = np.asarray(product.get("gamma1"), dtype=float)
    gamma2 = np.asarray(product.get("gamma2"), dtype=float)
    additive_gamma1 = np.asarray(psf.get("additive_gamma1"), dtype=float)
    additive_gamma2 = np.asarray(psf.get("additive_gamma2"), dtype=float)
    component_correction = np.asarray(
        calibration.get("component_correction"), dtype=float
    )
    expected_semantics = (
        "HSC_RESPONSIVITY_AND_MULTIPLICATIVE_BIAS_CORRECTION"
        if survey == "HSC"
        else "KIDS_LENSFIT_MULTIPLICATIVE_RESPONSE_CORRECTION"
    )
    if (
        gamma1.ndim != 1
        or gamma1.shape != gamma2.shape
        or additive_gamma1.shape != gamma1.shape
        or additive_gamma2.shape != gamma1.shape
        or component_correction.shape != gamma1.shape
        or not np.all(np.isfinite(additive_gamma1))
        or not np.all(np.isfinite(additive_gamma2))
        or not np.all(np.isfinite(component_correction))
        or np.any(component_correction <= 0.0)
        or calibration.get("correction_semantics") != expected_semantics
    ):
        raise HscKidsWorkerError(f"{survey} PSF/calibration operator is incomplete")
    raw = RawSpin2Field(
        identity=identity,
        gamma1=(gamma1 - additive_gamma1) * component_correction,
        gamma2=(gamma2 - additive_gamma2) * component_correction,
        bin_index=product.get("bin_index"),
        redshift=product.get("redshift"),
        weights=product.get("weights"),
        sky_xy_radians=product.get("sky_xy_radians"),
    )
    labelled: LabelledEBField = label_eb(
        raw,
        provider_matrix=calibration.get("provider_matrix"),
        provider_id=calibration.get("provider_id"),
        output_order=calibration.get("output_order"),
    )
    bin_rows = _sequence(n_z.get("bins"), label=f"{survey} tomography bins")
    bins = tuple(
        TomographyBin(
            survey_id=str(_mapping(row, label="tomography bin").get("survey_id")),
            bin_index=int(row.get("bin_index")),
            bin_id=str(row.get("bin_id")),
            z_min=float(row.get("z_min")),
            z_max=float(row.get("z_max")),
            n_z_id=str(row.get("n_z_id")),
            calibration_id=str(row.get("calibration_id")),
            response_id=str(row.get("response_id")),
            shear_calibration_factor=float(row.get("shear_calibration_factor")),
            response_factor=float(row.get("response_factor")),
        )
        for row in bin_rows
    )
    tomography = execute_tomography(
        labelled,
        bins=bins,
        n_z_weights=n_z.get("row_weights"),
        mask_weights=mask.get("row_weights"),
        flat_sky_wavevector=mask.get("flat_sky_wavevector"),
    )
    operator = PseudoClOperator.build(
        operator_id=mask.get("operator_id"),
        mask_id=mask.get("mask_id"),
        feature_order=tuple(mask.get("feature_order", ())),
        mixing_matrix=mask.get("mixing_matrix"),
        inverse_matrix=mask.get("inverse_matrix"),
        pure_e_pseudo_response=mask.get("pure_e_pseudo_response"),
        pure_b_pseudo_response=mask.get("pure_b_pseudo_response"),
    )
    features = operator.deconvolve(
        tomography.pseudo_features, feature_order=tomography.feature_order
    )
    operator.pure_mode_oracle()
    return tomography, operator, features


def analyze_documents(
    documents: Mapping[str, Mapping[str, object]],
    *,
    execution_mode: str,
    admission_context: Mapping[str, object] | None = None,
) -> dict[str, object]:
    if execution_mode not in {"SYNTHETIC_PROFILE", "ADMITTED_OBSERVED"}:
        raise HscKidsWorkerError("execution mode is not registered")
    observed = execution_mode == "ADMITTED_OBSERVED"
    if observed and (
        not isinstance(admission_context, Mapping)
        or not admission_context.get("lane_admission_bundle_id")
        or not admission_context.get("ordered_record_ids")
    ):
        raise HscKidsWorkerError("observed execution requires admission context")
    if not observed and admission_context is not None:
        raise HscKidsWorkerError("synthetic execution forbids admission context")
    if set(documents) != set(REQUIRED_COMPONENTS):
        raise HscKidsWorkerError("HSC/KiDS fifteen-component bundle is incomplete")
    hsc_identity = _identity(documents, "HSC")
    kids_identity = _identity(documents, "KiDS")
    validate_survey_pair(hsc_identity, kids_identity)
    hsc_tomography, hsc_operator, hsc_features = _survey_analysis(
        documents, "HSC", hsc_identity
    )
    kids_tomography, kids_operator, kids_features = _survey_analysis(
        documents, "KiDS", kids_identity
    )
    hsc_covariance = documents["hsc_covariance"]
    kids_covariance = documents["kids_covariance"]
    cross = documents["hsc_kids_cross_covariance"]
    if tuple(hsc_covariance.get("feature_order", ())) != hsc_tomography.feature_order:
        raise HscKidsWorkerError("HSC covariance feature order drifted")
    if tuple(kids_covariance.get("feature_order", ())) != kids_tomography.feature_order:
        raise HscKidsWorkerError("KiDS covariance feature order drifted")
    if (
        tuple(cross.get("hsc_feature_order", ())) != hsc_tomography.feature_order
        or tuple(cross.get("kids_feature_order", ())) != kids_tomography.feature_order
    ):
        raise HscKidsWorkerError("cross covariance feature order drifted")
    covariance_evidence = None
    covariance_branch = cross.get("covariance_branch")
    if covariance_branch == "PAIRED_SAME_SKY_NULLS":
        if (
            cross.get("hsc_operator_identity") != hsc_operator.operator_id
            or cross.get("kids_operator_identity") != kids_operator.operator_id
        ):
            raise HscKidsWorkerError("paired-null operator identity drifted")
        try:
            covariance_evidence = derive_paired_same_sky_joint_covariance(
                hsc_null_features=cross.get("hsc_null_features"),
                kids_null_features=cross.get("kids_null_features"),
                hsc_feature_order=hsc_tomography.feature_order,
                kids_feature_order=kids_tomography.feature_order,
                hsc_feature_units=tuple(
                    str(value)
                    for value in _sequence(
                        cross.get("hsc_feature_units"), label="HSC feature units"
                    )
                ),
                kids_feature_units=tuple(
                    str(value)
                    for value in _sequence(
                        cross.get("kids_feature_units"), label="KiDS feature units"
                    )
                ),
                hsc_normalization_ids=tuple(
                    str(value)
                    for value in _sequence(
                        cross.get("hsc_normalization_ids"),
                        label="HSC normalization IDs",
                    )
                ),
                kids_normalization_ids=tuple(
                    str(value)
                    for value in _sequence(
                        cross.get("kids_normalization_ids"),
                        label="KiDS normalization IDs",
                    )
                ),
                hsc_realization_ids=tuple(
                    str(value)
                    for value in _sequence(
                        cross.get("hsc_realization_ids"),
                        label="HSC realization IDs",
                    )
                ),
                kids_realization_ids=tuple(
                    str(value)
                    for value in _sequence(
                        cross.get("kids_realization_ids"),
                        label="KiDS realization IDs",
                    )
                ),
                realization_source_identity=str(
                    cross.get("realization_source_identity", "")
                ),
                sky_realization_role=str(cross.get("sky_realization_role", "")),
                overlap_support_identity=str(
                    cross.get("overlap_support_identity", "")
                ),
                hsc_operator_identity=str(cross.get("hsc_operator_identity", "")),
                kids_operator_identity=str(cross.get("kids_operator_identity", "")),
                centering_rule=str(cross.get("centering_rule", "")),
                denominator_rule=str(cross.get("denominator_rule", "")),
            )
        except HscKidsCurrentStackError as exc:
            raise HscKidsWorkerError(
                "paired same-sky covariance evidence is invalid"
            ) from exc
    axis = _mapping(cross.get("axis_transport"), label="axis transport")
    transported = parallel_transport_axis(
        start=axis.get("start"), end=axis.get("end"), tangent=axis.get("tangent")
    )
    alignment = transported_headless_axis_alignment(
        start=axis.get("start"),
        end=axis.get("end"),
        left_tangent=axis.get("tangent"),
        right_tangent=axis.get("comparison_tangent"),
    )
    response_order = tuple(cross.get("response_feature_order", ()))
    report = analyze_joint_response(
        hsc_features=hsc_features,
        kids_features=kids_features,
        hsc_feature_order=hsc_tomography.feature_order,
        kids_feature_order=kids_tomography.feature_order,
        joint_covariance_evidence=covariance_evidence,
        nuisance_response=cross.get("nuisance_response"),
        candidate_response=cross.get("candidate_response"),
        response_feature_order=response_order,
        observed=observed,
    )
    source_releases = {
        "HSC": hsc_identity.release_id,
        "KiDS": kids_identity.release_id,
    }
    artifact_metadata = {
        "owner": "OBSSTAT",
        "scope": "HSC/KiDS typed spin-2 operator diagnostic",
        "artifact_mode": (
            "admitted_observed_operator_diagnostic"
            if observed
            else "synthetic_operator_diagnostic"
        ),
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "source_releases": source_releases,
        "sky_mask_status": "SURVEY_SPECIFIC_MASK_OPERATOR_BOUND",
        "covariance_status": (
            report.get("joint_covariance", {}).get("status")
            if isinstance(report.get("joint_covariance"), Mapping)
            else "CROSS_INFORMATION_ABSENT_ABSTAIN"
        ),
        "null_mock_status": (
            "PAIRED_SAME_SKY_SYNTHETIC_NULLS_BOUND"
            if covariance_evidence is not None and not observed
            else "PAIRED_SAME_SKY_NULLS_BOUND"
            if covariance_evidence is not None
            else "NO_PAIRED_SAME_SKY_NULL_ENSEMBLE_BOUND"
        ),
        "generating_procedure": "scripts/observed_runs/run_hsc_kids.py",
        "allowed_use": "internal_operator_validation",
        "forbidden_uses": [
            "p_value",
            "source_attribution",
            "family_identification",
            "global_claim",
        ],
        "caveats": [
            "joint covariance is derived only from ordered paired same-sky null rows",
            "official HSC/KiDS releases do not provide an admitted joint null ensemble",
            "local structural rank is not global or practical identification",
            "singular covariance or missing cross information requires abstention",
        ],
        "public_use": False,
    }
    return {
        **report,
        "survey_releases": source_releases,
        "operator_family": "TYPED_PSEUDO_CL",
        "pure_mode_oracles": {
            "HSC": hsc_operator.pure_mode_oracle(),
            "KiDS": kids_operator.pure_mode_oracle(),
        },
        "typed_feature_vectors": {
            "HSC": [float(value) for value in hsc_features],
            "KiDS": [float(value) for value in kids_features],
        },
        "transported_headless_axis": [float(value) for value in transported],
        "transported_headless_alignment": alignment,
        "artifact_metadata": artifact_metadata,
    }


def _synthetic_documents() -> dict[str, Mapping[str, object]]:
    documents: dict[str, Mapping[str, object]] = {}
    orders: dict[str, tuple[str, ...]] = {}
    for survey, prefix, release, edges in (
        ("HSC", "hsc", "HSC_S19A_Y3", (0.3, 0.7, 1.2)),
        ("KiDS", "kids", "KIDS_1000_DR4_1", (0.1, 0.5, 0.9)),
    ):
        documents[f"{prefix}_product"] = {
            "release_id": release,
            "component_order": "GAMMA1_THEN_GAMMA2",
            "tangent_basis": "RIGHT_HANDED_NORTH_EAST_SKY",
            "spin_convention": "PASSIVE_EXP_MINUS_2I_PSI",
            "gamma1": [1.0, 0.4, -0.3, 0.2],
            "gamma2": [0.2, -0.5, 0.7, -0.1],
            "bin_index": [0, 0, 1, 1],
            "redshift": [
                edges[0] + 0.1,
                edges[1] - 0.1,
                edges[1] + 0.1,
                edges[2] - 0.1,
            ],
            "weights": [1.0, 2.0, 1.5, 0.5],
            "sky_xy_radians": [[0.0, 0.0], [0.2, 0.1], [0.5, 0.4], [0.8, 0.7]],
        }
        calibration_component = (
            "hsc_shear_calibration" if survey == "HSC" else "kids_shear_response"
        )
        calibration_role = (
            "multiplicative_shear_calibration"
            if survey == "HSC"
            else "lensfit_shear_response"
        )
        bins = [
            {
                "survey_id": survey,
                "bin_index": index,
                "bin_id": f"{prefix}-z{index}",
                "z_min": edges[index],
                "z_max": edges[index + 1],
                "n_z_id": f"{prefix}_n_z:{prefix}-z{index}",
                "calibration_id": f"{calibration_component}:{prefix}-z{index}",
                "response_id": (
                    f"{calibration_component}:{calibration_role}:{prefix}-z{index}"
                ),
                "shear_calibration_factor": (1.01 if index == 0 else 0.98),
                "response_factor": (0.99 if index == 0 else 1.02),
            }
            for index in range(2)
        ]
        documents[f"{prefix}_n_z"] = {
            "survey_id": survey,
            "row_weights": [1.0, 1.2, 0.9, 1.1],
            "bins": bins,
        }
        order = tuple(
            f"{survey}:{bins[left]['bin_id']}x{bins[right]['bin_id']}:k=2,1:{mode}"
            for left in range(2)
            for right in range(left, 2)
            for mode in ("EE", "BB")
        )
        orders[survey] = order
        size = len(order)
        mixing = np.eye(size)
        for index in range(size):
            mixing[index, (index + 1) % size] = 0.04
        pure_e = np.asarray([name.endswith(":EE") for name in order], dtype=float)
        pure_b = np.asarray([name.endswith(":BB") for name in order], dtype=float)
        documents[f"{prefix}_mask"] = {
            "survey_id": survey,
            "operator_id": f"{prefix}-pseudo-cl-v1",
            "mask_id": f"{prefix}-nontrivial-mask-v1",
            "feature_order": list(order),
            "mixing_matrix": mixing.tolist(),
            "inverse_matrix": np.linalg.inv(mixing).tolist(),
            "row_weights": [1.0, 0.8, 0.9, 0.7],
            "flat_sky_wavevector": [2.0, 1.0],
            "pure_e_pseudo_response": (mixing @ pure_e).tolist(),
            "pure_b_pseudo_response": (mixing @ pure_b).tolist(),
        }
        documents[f"{prefix}_randoms"] = {
            "survey_id": survey,
            "status": "VALIDATED_SELECTION_SUPPORT",
        }
        documents[f"{prefix}_psf"] = {
            "survey_id": survey,
            "status": "VALIDATED_PSF_SUPPORT",
            "additive_gamma1": [0.0, 0.0, 0.0, 0.0],
            "additive_gamma2": [0.0, 0.0, 0.0, 0.0],
        }
        rows = 4
        row = np.arange(rows, dtype=float)[:, None]
        mode = np.arange(rows, dtype=float)[None, :]
        nonlocal_basis = np.sqrt(2.0 / rows) * np.cos(
            np.pi * (row + 0.5) * mode / rows
        )
        nonlocal_basis[:, 0] /= np.sqrt(2.0)
        c = 1.0 / np.sqrt(2.0)
        provider = np.block(
            [
                [c * nonlocal_basis, c * nonlocal_basis],
                [-c * nonlocal_basis, c * nonlocal_basis],
            ]
        )
        documents[calibration_component] = {
            "survey_id": survey,
            "provider_id": f"{prefix}-registered-nonlocal-eb-v1",
            "provider_matrix": provider.tolist(),
            "output_order": "E_THEN_B",
            "component_correction": (
                [1.01, 1.01, 1.01, 1.01]
                if survey == "HSC"
                else [0.99, 0.99, 0.99, 0.99]
            ),
            "correction_semantics": (
                "HSC_RESPONSIVITY_AND_MULTIPLICATIVE_BIAS_CORRECTION"
                if survey == "HSC"
                else "KIDS_LENSFIT_MULTIPLICATIVE_RESPONSE_CORRECTION"
            ),
        }
        documents[f"{prefix}_covariance"] = {
            "feature_order": list(order),
            "matrix": (1.8 * np.eye(size) if survey == "HSC" else 1.5 * np.eye(size)).tolist(),
            "role": "SINGLE_SURVEY_REFERENCE_ONLY_NOT_USED_FOR_JOINT_DERIVATION",
        }
    size = len(orders["HSC"])
    x = np.linspace(-1.0, 1.0, 2 * size)
    rng = np.random.default_rng(20260825)
    null_count = 64
    shared = rng.normal(size=(null_count, 4))
    hsc_null = shared @ rng.normal(size=(4, size)) + rng.normal(
        scale=0.35, size=(null_count, size)
    )
    kids_null = shared @ rng.normal(size=(4, size)) + rng.normal(
        scale=0.35, size=(null_count, size)
    )
    realization_ids = [
        f"synthetic-same-sky-{index:03d}" for index in range(null_count)
    ]
    documents["hsc_kids_cross_covariance"] = {
        "hsc_feature_order": list(orders["HSC"]),
        "kids_feature_order": list(orders["KiDS"]),
        "covariance_branch": "PAIRED_SAME_SKY_NULLS",
        "hsc_null_features": hsc_null.tolist(),
        "kids_null_features": kids_null.tolist(),
        "hsc_feature_units": ["dimensionless_shear_squared"] * size,
        "kids_feature_units": ["dimensionless_shear_squared"] * size,
        "hsc_normalization_ids": [
            f"{name}:SYNTHETIC_PSEUDO_CL_V1" for name in orders["HSC"]
        ],
        "kids_normalization_ids": [
            f"{name}:SYNTHETIC_PSEUDO_CL_V1" for name in orders["KiDS"]
        ],
        "hsc_realization_ids": realization_ids,
        "kids_realization_ids": realization_ids,
        "realization_source_identity": "synthetic-paired-same-sky-null-v1",
        "sky_realization_role": "PAIRED_SAME_SKY_COSMIC_REALIZATION",
        "overlap_support_identity": "synthetic-common-overlap-support-v1",
        "hsc_operator_identity": "hsc-pseudo-cl-v1",
        "kids_operator_identity": "kids-pseudo-cl-v1",
        "centering_rule": "JOINT_SAMPLE_MEAN",
        "denominator_rule": "N_MINUS_ONE",
        "nuisance_response": np.column_stack([np.ones_like(x), x]).tolist(),
        "candidate_response": np.column_stack([np.sin(1.7 * x), np.cos(2.3 * x)]).tolist(),
        "response_feature_order": [*orders["HSC"], *orders["KiDS"]],
        "axis_transport": {
            "start": [1.0, 0.0, 0.0],
            "end": [0.0, 1.0, 0.0],
            "tangent": [0.0, 1.0, 0.0],
            "comparison_tangent": [-1.0, 0.0, 0.0],
        },
    }
    return documents


def synthetic_profile(*, rows: str) -> dict[str, object]:
    if rows not in PROFILE_ROWS:
        raise HscKidsWorkerError("synthetic profile row label is not registered")
    started = time.perf_counter()
    report: dict[str, object] | None = None
    documents = _synthetic_documents()
    for _ in range(PROFILE_ROWS[rows]):
        report = analyze_documents(documents, execution_mode="SYNTHETIC_PROFILE")
    assert report is not None
    return {
        **report,
        "row_label": rows,
        "row_count": PROFILE_ROWS[rows],
        "wall_seconds": float(time.perf_counter() - started),
        "max_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
        "thread_controls": THREAD_CONTROLS,
        "observed_statistic_seen": False,
        "observed_science_executed": False,
    }


def run_admitted(*, admission_path: Path, data_root: Path) -> dict[str, object]:
    decision = _load_admission(admission_path)
    _mark_observed_data_open_attempt()
    documents = _admitted_documents(decision, data_root=data_root)
    record_ids = [record.record_id for record in decision.records]
    report = analyze_documents(
        documents,
        execution_mode="ADMITTED_OBSERVED",
        admission_context={
            "lane_admission_bundle_id": decision.lane_admission_bundle_id,
            "ordered_record_ids": record_ids,
        },
    )
    report["artifact_metadata"].update(
        {
            "candidate_commit": os.environ.get("HTT_ATTENDED_CANDIDATE_COMMIT"),
            "candidate_tree": os.environ.get("HTT_ATTENDED_CANDIDATE_TREE"),
            "input_identity": {
                "lane_admission_bundle_id": decision.lane_admission_bundle_id,
                "ordered_record_ids": record_ids,
            },
        }
    )
    return {
        **report,
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "ordered_record_ids": record_ids,
    }


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic-profile", action="store_true")
    mode.add_argument("--run-admitted", action="store_true")
    mode.add_argument("--inspect-hsc-sacc", action="store_true")
    parser.add_argument("--rows", choices=tuple(PROFILE_ROWS), default="full")
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--hsc-sacc", type=Path)
    parser.add_argument("--confirm-input-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.synthetic_profile:
            if any(
                value is not None
                for value in (
                    args.admission,
                    args.data_root,
                    args.hsc_sacc,
                    args.confirm_input_sha256,
                )
            ):
                raise HscKidsWorkerError("synthetic profile forbids admission and data root")
            payload = synthetic_profile(rows=args.rows)
        elif args.run_admitted:
            if args.admission is None or args.data_root is None:
                raise HscKidsWorkerError("admitted run requires admission and data root")
            if args.hsc_sacc is not None or args.confirm_input_sha256 is not None:
                raise HscKidsWorkerError("admitted run forbids HSC-only SACC arguments")
            payload = run_admitted(admission_path=args.admission, data_root=args.data_root)
        else:
            if args.admission is not None or args.data_root is not None:
                raise HscKidsWorkerError("HSC-only SACC inspection forbids admission inputs")
            if args.hsc_sacc is None or args.confirm_input_sha256 is None:
                raise HscKidsWorkerError(
                    "HSC-only SACC inspection requires path and exact confirmation"
                )
            payload = inspect_hsc_sacc(
                path=args.hsc_sacc,
                confirmation_sha256=args.confirm_input_sha256,
            )
        _write_json(args.output, payload)
        print(json.dumps(payload, sort_keys=True, allow_nan=False))
        return 0
    except (HscKidsWorkerError, HscKidsCurrentStackError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
