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
import json
from pathlib import Path
import resource
import sys
import tempfile
import time
from typing import Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT / "htt", ROOT / "htt/src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from common.data_identity import (  # noqa: E402
    AdmissionStatus,
    DataIdentityError,
    _regular_beneath,
    _stream_sha256,
    load_lane_registry,
    replay_lane_admission_decision,
)
from obsstat.hsc_kids_current_stack import (  # noqa: E402
    HscKidsCurrentStackError,
    LabelledEBField,
    PseudoClOperator,
    RawSpin2Field,
    SurveyIdentity,
    TomographyBin,
    analyze_joint_response,
    execute_tomography,
    label_eb,
    parallel_transport_axis,
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


class HscKidsWorkerError(RuntimeError):
    """Raised before an HSC/KiDS result when the worker contract drifts."""


def _strict_json(path: Path, *, label: str) -> Mapping[str, object]:
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
        payload = json.loads(
            path.read_bytes(), object_pairs_hook=unique, parse_constant=reject_constant
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HscKidsWorkerError(f"{label} is not strict JSON") from exc
    if not isinstance(payload, Mapping):
        raise HscKidsWorkerError(f"{label} must be a JSON object")
    return payload


def _load_admission(path: Path):
    try:
        registry = load_lane_registry(REGISTRY)
        decision = replay_lane_admission_decision(
            _strict_json(path, label="HSC/KiDS admission"), registry=registry
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


def _admitted_paths(decision, *, data_root: Path) -> dict[str, Path]:
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
    result: dict[str, Path] = {}
    for row in rows:
        component = row.get("component_id")
        relative = row.get("relative_path")
        if component not in records or not isinstance(relative, str):
            raise HscKidsWorkerError("HSC/KiDS component binding identity drifted")
        try:
            path, info = _regular_beneath(data_root, Path(relative), str(component))
            digest = "sha256:" + _stream_sha256(
                path, field_name=str(component), expected_info=info
            )
        except DataIdentityError as exc:
            raise HscKidsWorkerError(f"{component} is not an exact admitted file") from exc
        record = records[str(component)]
        if info.st_size != record.byte_size or digest != record.content_sha256:
            raise HscKidsWorkerError(f"{component} no longer matches admission")
        result[str(component)] = path
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
        weights=product.get("weights"),
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
        )
        for row in bin_rows
    )
    tomography = execute_tomography(labelled, bins=bins)
    operator = PseudoClOperator.build(
        operator_id=mask.get("operator_id"),
        mask_id=mask.get("mask_id"),
        feature_order=tuple(mask.get("feature_order", ())),
        mixing_matrix=mask.get("mixing_matrix"),
        inverse_matrix=mask.get("inverse_matrix"),
    )
    features = operator.apply(tomography.true_features, feature_order=tomography.feature_order)
    operator.pure_mode_oracle()
    return tomography, operator, features


def analyze_documents(
    documents: Mapping[str, Mapping[str, object]], *, observed: bool
) -> dict[str, object]:
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
    axis = _mapping(cross.get("axis_transport"), label="axis transport")
    transported = parallel_transport_axis(
        start=axis.get("start"), end=axis.get("end"), tangent=axis.get("tangent")
    )
    report = analyze_joint_response(
        hsc_features=hsc_features,
        kids_features=kids_features,
        hsc_feature_order=hsc_tomography.feature_order,
        kids_feature_order=kids_tomography.feature_order,
        hsc_covariance=hsc_covariance.get("matrix"),
        kids_covariance=kids_covariance.get("matrix"),
        cross_covariance=cross.get("matrix"),
        nuisance_response=cross.get("nuisance_response"),
        candidate_response=cross.get("candidate_response"),
        observed=observed,
    )
    return {
        **report,
        "survey_releases": {"HSC": hsc_identity.release_id, "KiDS": kids_identity.release_id},
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
            "weights": [1.0, 2.0, 1.5, 0.5],
        }
        bins = [
            {
                "survey_id": survey,
                "bin_index": index,
                "bin_id": f"{prefix}-z{index}",
                "z_min": edges[index],
                "z_max": edges[index + 1],
                "n_z_id": f"{prefix}-nz-{index}",
                "calibration_id": f"{prefix}-cal-{index}",
                "response_id": f"{prefix}-response-{index}",
            }
            for index in range(2)
        ]
        documents[f"{prefix}_n_z"] = {"survey_id": survey, "bins": bins}
        order = tuple(
            f"{survey}:{bins[left]['bin_id']}x{bins[right]['bin_id']}:{mode}"
            for left in range(2)
            for right in range(left, 2)
            for mode in ("EE", "BB")
        )
        orders[survey] = order
        size = len(order)
        mixing = np.eye(size)
        for index in range(size):
            mixing[index, (index + 1) % size] = 0.04
        documents[f"{prefix}_mask"] = {
            "survey_id": survey,
            "operator_id": f"{prefix}-pseudo-cl-v1",
            "mask_id": f"{prefix}-nontrivial-mask-v1",
            "feature_order": list(order),
            "mixing_matrix": mixing.tolist(),
            "inverse_matrix": np.linalg.inv(mixing).tolist(),
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
        calibration_component = (
            "hsc_shear_calibration" if survey == "HSC" else "kids_shear_response"
        )
        rows = 4
        c = 1.0 / np.sqrt(2.0)
        identity = np.eye(rows)
        provider = np.block([[c * identity, c * identity], [-c * identity, c * identity]])
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
        }
    size = len(orders["HSC"])
    x = np.linspace(-1.0, 1.0, 2 * size)
    documents["hsc_kids_cross_covariance"] = {
        "hsc_feature_order": list(orders["HSC"]),
        "kids_feature_order": list(orders["KiDS"]),
        "matrix": (0.08 * np.eye(size)).tolist(),
        "nuisance_response": np.column_stack([np.ones_like(x), x]).tolist(),
        "candidate_response": np.column_stack([np.sin(1.7 * x), np.cos(2.3 * x)]).tolist(),
        "axis_transport": {
            "start": [1.0, 0.0, 0.0],
            "end": [0.0, 1.0, 0.0],
            "tangent": [0.0, 1.0, 0.0],
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
        report = analyze_documents(documents, observed=False)
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
    paths = _admitted_paths(decision, data_root=data_root)
    documents = {
        component: _strict_json(path, label=component) for component, path in paths.items()
    }
    report = analyze_documents(documents, observed=True)
    return {
        **report,
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "ordered_record_ids": [record.record_id for record in decision.records],
        "artifact_metadata": {
            "owner": "OBSSTAT",
            "scope": "HSC/KiDS typed spin-2 operator diagnostic",
            "claim_tier": "diagnostic_only",
            "transfer_source": "none",
            "covariance_status": "FULL_ADMITTED_CROSS_SURVEY_COVARIANCE",
            "null_mock_status": "ADMITTED_SURVEY_PRODUCTS",
            "public_use": False,
            "candidate_commit": os.environ.get("HTT_ATTENDED_CANDIDATE_COMMIT"),
            "candidate_tree": os.environ.get("HTT_ATTENDED_CANDIDATE_TREE"),
        },
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
    parser.add_argument("--rows", choices=tuple(PROFILE_ROWS), default="full")
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.synthetic_profile:
            if args.admission is not None or args.data_root is not None:
                raise HscKidsWorkerError("synthetic profile forbids admission and data root")
            payload = synthetic_profile(rows=args.rows)
        else:
            if args.admission is None or args.data_root is None:
                raise HscKidsWorkerError("admitted run requires admission and data root")
            payload = run_admitted(admission_path=args.admission, data_root=args.data_root)
        _write_json(args.output, payload)
        print(json.dumps(payload, sort_keys=True, allow_nan=False))
        return 0
    except (HscKidsWorkerError, HscKidsCurrentStackError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
