"""Matched full-sky numerical-control bridge for PMG-WU-011 Task-7C.

The first-order scalar boost generator couples a full-sky source multipole only
to neighbouring multipoles.  Hence source ell >= 7 has no exact full-sky image
in the retained ell=2..5 carrier.  This module rebuilds the *same* numerical
operator with only the sky mask changed to FULL and uses the resulting replay
floor to anchor the Task-7C numerical image rank.

The control is an engineering calibration object.  It is not a high-ell prior,
an observed-data covariance, a velocity fit, or a scientific terminal.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np

from .planck_pr3_operator import build_joint_cutsky_operator
from .processed_boost_identifiability import (
    _mask_for,
    _output_metric,
    _transfer_arrays,
)
from .processed_boost_nuisance_span import (
    DIRECTION_IDS,
    ExtendedSourceBlockCache,
    Task7CCaseResult,
    Task7COperatorSpec,
    _build_operator,
    contract_directional_tensor,
    direction_registry,
    metric_whiten_directional_matrix,
)
from .processed_boost_operator import ProcessedBoostOperator
from .processed_boost_rank_policy import (
    ControlAnchoredNuisanceGeometry,
    RankDecisionStatus,
    RankPolicy,
    analyse_control_anchored_nuisance_geometry,
    high_source_dimension,
)
from .processed_boost_response import FIT_LMAX, RETAINED_LMIN, ProcessedBoostError


_MATCHED_CONTROL_SCHEMA = "HTT_WU011_TASK7C_MATCHED_FULLSKY_CONTROL_V1"
_MATCHED_DIRECTION_SCHEMA = "HTT_WU011_TASK7C_MATCHED_FULLSKY_DIRECTION_V1"
_MATCHED_ANALYSIS_SCHEMA = "HTT_WU011_TASK7C_MATCHED_CONTROL_ANALYSIS_V1"
_MATCHED_RECEIPT_SCHEMA = "HTT_WU011_TASK7C_MATCHED_CONTROL_RECEIPT_V1"
_EXPECTED_RECEIPT_FILES = (
    "summary.json",
    "rank_sensitivity.csv",
    "control_to_cutsky_operator_ratio.png",
    "survivor_rank_vs_cutoff.png",
)


class MatchedControlError(ProcessedBoostError):
    """Raised when a purported full-sky control is not numerically matched."""


def _sealed_matrix(
    values: object,
    *,
    shape: tuple[int, int],
    label: str,
) -> np.ndarray:
    try:
        matrix = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise MatchedControlError(f"{label} is not a finite matrix") from exc
    if matrix.shape != shape or not np.all(np.isfinite(matrix)):
        raise MatchedControlError(f"{label} is not a finite matrix")
    sealed = np.frombuffer(
        np.ascontiguousarray(matrix, dtype="<f8").tobytes(),
        dtype="<f8",
    ).reshape(shape)
    sealed.setflags(write=False)
    return sealed


def _identity_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise MatchedControlError(f"{label} is absent")
    return value


def _sha_identity(value: object, *, label: str) -> str:
    text = _identity_text(value, label=label)
    prefix, separator, digest = text.partition(":")
    if (
        prefix != "sha256"
        or not separator
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise MatchedControlError(f"{label} is not a sha256 identity")
    return text


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _content_id(role: str, payload: Mapping[str, object], *arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(_canonical_json(payload))
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(b"\0")
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(b"\0")
        digest.update(repr(value.shape).encode("ascii"))
        digest.update(b"\0")
        digest.update(memoryview(value).cast("B"))
    return "sha256:" + digest.hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class MatchedFullSkyDirectionalControl:
    """One full-sky replay-floor matrix at fixed direction and cutoff."""

    direction_id: str
    source_cutoff: int
    high_matrix: np.ndarray
    operator_id: str
    content_id: str

    def __post_init__(self) -> None:
        if self.direction_id not in DIRECTION_IDS:
            raise MatchedControlError("matched-control direction is outside the registry")
        if type(self.source_cutoff) is not int or self.source_cutoff < 7:
            raise MatchedControlError("matched-control source cutoff is outside its domain")
        object.__setattr__(
            self,
            "high_matrix",
            _sealed_matrix(
                self.high_matrix,
                shape=(32, high_source_dimension(self.source_cutoff)),
                label="matched full-sky high-source response",
            ),
        )
        _sha_identity(self.operator_id, label="matched-control operator identity")
        _sha_identity(self.content_id, label="matched-control matrix identity")


@dataclass(frozen=True)
class MatchedFullSkyControlCase:
    """Full-sky replay controls matched to one cut-sky Task-7C case."""

    case_id: str
    source_case_id: str
    source_operator_id: str
    mask_kind: str
    nside: int
    processing_lmax: int
    transfer_kind: str
    source_cutoffs: tuple[int, ...]
    operator_id: str
    directional_controls: tuple[MatchedFullSkyDirectionalControl, ...]
    source_block_build_count: int
    content_id: str

    def __post_init__(self) -> None:
        _identity_text(self.case_id, label="matched-control case ID")
        _identity_text(self.source_case_id, label="source case ID")
        _sha_identity(self.source_operator_id, label="source operator identity")
        _sha_identity(self.operator_id, label="matched-control operator identity")
        _sha_identity(self.content_id, label="matched-control case identity")
        if self.mask_kind != "FULL":
            raise MatchedControlError("matched-control mask must be FULL")
        if type(self.nside) is not int or self.nside <= 0:
            raise MatchedControlError("matched-control nside is invalid")
        if type(self.processing_lmax) is not int or self.processing_lmax < 8:
            raise MatchedControlError("matched-control processing lmax is invalid")
        if (
            not self.source_cutoffs
            or tuple(sorted(set(self.source_cutoffs))) != self.source_cutoffs
            or min(self.source_cutoffs) < 7
        ):
            raise MatchedControlError("matched-control cutoff registry is invalid")
        if self.source_block_build_count != max(self.source_cutoffs) - 6:
            raise MatchedControlError("matched-control source-block count is inconsistent")
        expected = len(DIRECTION_IDS) * len(self.source_cutoffs)
        if len(self.directional_controls) != expected:
            raise MatchedControlError("matched-control directional registry is incomplete")

    def result(
        self,
        direction_id: str,
        source_cutoff: int,
    ) -> MatchedFullSkyDirectionalControl:
        for item in self.directional_controls:
            if item.direction_id == direction_id and item.source_cutoff == source_cutoff:
                return item
        raise MatchedControlError("matched-control directional result is absent")


@dataclass(frozen=True)
class Task7CMatchedControlResult:
    """Control-anchored image quotient with immutable provenance."""

    source_case_id: str
    control_case_id: str
    direction_id: str
    source_cutoff: int
    source_operator_id: str
    control_operator_id: str
    geometry: ControlAnchoredNuisanceGeometry
    content_id: str

    def __post_init__(self) -> None:
        _identity_text(self.source_case_id, label="source case ID")
        _identity_text(self.control_case_id, label="control case ID")
        if self.direction_id not in DIRECTION_IDS:
            raise MatchedControlError("matched-control analysis direction differs")
        if type(self.source_cutoff) is not int or self.source_cutoff < 7:
            raise MatchedControlError("matched-control analysis cutoff differs")
        _sha_identity(self.source_operator_id, label="source operator identity")
        _sha_identity(self.control_operator_id, label="control operator identity")
        if type(self.geometry) is not ControlAnchoredNuisanceGeometry:
            raise MatchedControlError("matched-control geometry type differs")
        _sha_identity(self.content_id, label="matched-control analysis identity")


def analyse_matched_control_matrices(
    low_matrix: object,
    high_matrix: object,
    matched_fullsky_control: object,
    *,
    source_case_id: str,
    control_case_id: str,
    direction_id: str,
    source_cutoff: int,
    source_operator_id: str,
    control_operator_id: str,
    policy: RankPolicy = RankPolicy(),
) -> Task7CMatchedControlResult:
    """Apply the control-anchored rank policy and bind all provenance."""

    source_case = _identity_text(source_case_id, label="source case ID")
    control_case = _identity_text(control_case_id, label="control case ID")
    source_operator = _sha_identity(
        source_operator_id,
        label="source operator identity",
    )
    control_operator = _sha_identity(
        control_operator_id,
        label="control operator identity",
    )
    if direction_id not in DIRECTION_IDS:
        raise MatchedControlError("matched-control direction is outside the registry")
    if type(source_cutoff) is not int or source_cutoff < 7:
        raise MatchedControlError("matched-control source cutoff is outside its domain")

    try:
        geometry = analyse_control_anchored_nuisance_geometry(
            low_matrix,
            high_matrix,
            matched_fullsky_control,
            policy=policy,
        )
    except (ValueError, TypeError) as exc:
        raise MatchedControlError(f"matched-control rank analysis failed: {exc}") from exc

    low = np.asarray(low_matrix, dtype=np.float64)
    high = np.asarray(high_matrix, dtype=np.float64)
    control = np.asarray(matched_fullsky_control, dtype=np.float64)
    payload = {
        "source_case_id": source_case,
        "control_case_id": control_case,
        "direction_id": direction_id,
        "source_cutoff": source_cutoff,
        "source_operator_id": source_operator,
        "control_operator_id": control_operator,
        "rank_status": geometry.rank_status.value,
        "low_rank": geometry.low_rank,
        "high_rank": geometry.high_rank,
        "surviving_rank": geometry.surviving_rank,
        "augmented_rank_increment": geometry.augmented_rank_increment,
        "rank_identity_holds": geometry.rank_identity_holds,
        "containment_witness": geometry.containment_witness,
        "low_threshold_hex": geometry.low_threshold.hex(),
        "high_threshold_hex": geometry.high_threshold.hex(),
        "high_control_operator_norm_hex": geometry.high_control_operator_norm.hex(),
        "policy": {
            "relative_singular_ceiling_hex": policy.relative_singular_ceiling.hex(),
            "control_safety_factor_hex": policy.control_safety_factor.hex(),
            "machine_safety_factor_hex": policy.machine_safety_factor.hex(),
            "ambiguity_factor_hex": policy.ambiguity_factor.hex(),
        },
    }
    content_id = _content_id(
        _MATCHED_ANALYSIS_SCHEMA,
        payload,
        low,
        high,
        control,
    )
    return Task7CMatchedControlResult(
        source_case,
        control_case,
        direction_id,
        source_cutoff,
        source_operator,
        control_operator,
        geometry,
        content_id,
    )


def _build_fullsky_operator(source_spec: Task7COperatorSpec) -> ProcessedBoostOperator:
    mask = _mask_for(source_spec.nside, "FULL")
    joint = build_joint_cutsky_operator(
        mask,
        lmin=0,
        lmax=FIT_LMAX,
        retained_lmin=RETAINED_LMIN,
    )
    source_beam, source_pixel, target_beam, target_pixel = _transfer_arrays(
        source_spec.processing_lmax,
        source_spec.transfer_kind,
    )
    return ProcessedBoostOperator.from_components(
        mask=mask,
        joint_operator=joint,
        processing_lmax=source_spec.processing_lmax,
        source_beam=source_beam,
        source_pixel_window=source_pixel,
        target_beam=target_beam,
        target_pixel_window=target_pixel,
    )


def build_matched_fullsky_control(
    source_spec: Task7COperatorSpec,
) -> MatchedFullSkyControlCase:
    """Rebuild one Task-7C case with only its mask replaced by FULL."""

    if type(source_spec) is not Task7COperatorSpec:
        raise MatchedControlError("matched control requires an exact Task7COperatorSpec")
    if source_spec.mask_kind == "FULL":
        raise MatchedControlError("matched control requires a cut-sky source case")

    source_operator = _build_operator(source_spec)
    control_operator = _build_fullsky_operator(source_spec)
    if source_operator.content_id == control_operator.content_id:
        raise MatchedControlError("matched control did not change the masked estimator")

    cache = ExtendedSourceBlockCache()
    blocks = tuple(
        cache.get(control_operator, source_ell=ell)
        for ell in range(7, max(source_spec.source_cutoffs) + 1)
    )
    output_metric = np.asarray(_output_metric(), dtype=np.float64)
    controls: list[MatchedFullSkyDirectionalControl] = []
    registry = direction_registry()
    for cutoff in source_spec.source_cutoffs:
        active_blocks = tuple(block for block in blocks if block.source_ell <= cutoff)
        for direction_id in DIRECTION_IDS:
            direction = registry[direction_id]
            directional = tuple(
                metric_whiten_directional_matrix(
                    contract_directional_tensor(block.tensor, direction),
                    source_metric_diagonal=block.source_metric_diagonal,
                    output_metric_diagonal=output_metric,
                )
                for block in active_blocks
            )
            high = np.concatenate(directional, axis=1)
            control_id = _content_id(
                _MATCHED_DIRECTION_SCHEMA,
                {
                    "source_case_id": source_spec.case_id,
                    "direction_id": direction_id,
                    "source_cutoff": cutoff,
                    "source_operator_id": source_operator.content_id,
                    "control_operator_id": control_operator.content_id,
                    "block_ids": [block.content_id for block in active_blocks],
                },
                high,
            )
            controls.append(
                MatchedFullSkyDirectionalControl(
                    direction_id,
                    cutoff,
                    high,
                    control_operator.content_id,
                    control_id,
                )
            )

    case_id = f"MATCHED_FULLSKY_FOR_{source_spec.case_id}"
    content_id = _content_id(
        _MATCHED_CONTROL_SCHEMA,
        {
            "case_id": case_id,
            "source_case_id": source_spec.case_id,
            "source_operator_id": source_operator.content_id,
            "mask_kind": "FULL",
            "nside": source_spec.nside,
            "processing_lmax": source_spec.processing_lmax,
            "transfer_kind": source_spec.transfer_kind,
            "source_cutoffs": list(source_spec.source_cutoffs),
            "control_operator_id": control_operator.content_id,
            "directional_control_ids": [item.content_id for item in controls],
            "source_block_build_count": cache.build_count,
        },
    )
    return MatchedFullSkyControlCase(
        case_id,
        source_spec.case_id,
        source_operator.content_id,
        "FULL",
        source_spec.nside,
        source_spec.processing_lmax,
        source_spec.transfer_kind,
        source_spec.source_cutoffs,
        control_operator.content_id,
        tuple(controls),
        cache.build_count,
        content_id,
    )


def _validate_case_pair(
    source_case: Task7CCaseResult,
    control_case: MatchedFullSkyControlCase,
) -> None:
    if type(source_case) is not Task7CCaseResult:
        raise MatchedControlError("matched-control source case has the wrong type")
    if type(control_case) is not MatchedFullSkyControlCase:
        raise MatchedControlError("matched-control case has the wrong type")
    expected = (
        source_case.case_id,
        source_case.operator_id,
        source_case.nside,
        source_case.processing_lmax,
        source_case.transfer_kind,
        source_case.source_cutoffs,
    )
    actual = (
        control_case.source_case_id,
        control_case.source_operator_id,
        control_case.nside,
        control_case.processing_lmax,
        control_case.transfer_kind,
        control_case.source_cutoffs,
    )
    if expected != actual:
        raise MatchedControlError("matched full-sky control does not match source metadata")
    if source_case.mask_kind == "FULL" or control_case.mask_kind != "FULL":
        raise MatchedControlError("matched-control mask roles differ")
    if source_case.operator_id == control_case.operator_id:
        raise MatchedControlError("matched-control operator identity was not separated")


def analyse_task7c_with_matched_fullsky_control(
    source_case: Task7CCaseResult,
    control_case: MatchedFullSkyControlCase,
    *,
    direction_id: str,
    source_cutoff: int,
    policy: RankPolicy = RankPolicy(),
) -> Task7CMatchedControlResult:
    """Analyse one generated cut-sky matrix against its matched full-sky floor."""

    _validate_case_pair(source_case, control_case)
    source = source_case.result(direction_id, source_cutoff)
    control = control_case.result(direction_id, source_cutoff)
    return analyse_matched_control_matrices(
        source.low_matrix,
        source.high_matrix,
        control.high_matrix,
        source_case_id=source_case.case_id,
        control_case_id=control_case.case_id,
        direction_id=direction_id,
        source_cutoff=source_cutoff,
        source_operator_id=source_case.operator_id,
        control_operator_id=control_case.operator_id,
        policy=policy,
    )


def _receipt_rows(
    source_case: Task7CCaseResult,
    control_case: MatchedFullSkyControlCase,
    *,
    control_factors: tuple[float, ...],
) -> tuple[list[dict[str, object]], list[Task7CMatchedControlResult]]:
    _validate_case_pair(source_case, control_case)
    rows: list[dict[str, object]] = []
    analyses: list[Task7CMatchedControlResult] = []
    for cutoff in source_case.source_cutoffs:
        for direction_id in DIRECTION_IDS:
            source = source_case.result(direction_id, cutoff)
            control = control_case.result(direction_id, cutoff)
            control_norm = float(np.linalg.svd(control.high_matrix, compute_uv=False)[0])
            source_norm = float(np.linalg.svd(source.high_matrix, compute_uv=False)[0])

            floor_check = analyse_matched_control_matrices(
                source.low_matrix,
                control.high_matrix,
                control.high_matrix,
                source_case_id=source_case.case_id,
                control_case_id=control_case.case_id,
                direction_id=direction_id,
                source_cutoff=cutoff,
                source_operator_id=source_case.operator_id,
                control_operator_id=control_case.operator_id,
                policy=RankPolicy(control_safety_factor=5.0),
            )
            if (
                floor_check.geometry.rank_status is not RankDecisionStatus.RESOLVED
                or floor_check.geometry.high_rank != 0
                or floor_check.geometry.containment_witness is not False
            ):
                raise MatchedControlError(
                    "matched full-sky replay floor was promoted to a nuisance image"
                )

            for factor in control_factors:
                policy = RankPolicy(control_safety_factor=float(factor))
                result = analyse_task7c_with_matched_fullsky_control(
                    source_case,
                    control_case,
                    direction_id=direction_id,
                    source_cutoff=cutoff,
                    policy=policy,
                )
                analyses.append(result)
                geometry = result.geometry
                rows.append(
                    {
                        "source_case_id": source_case.case_id,
                        "control_case_id": control_case.case_id,
                        "direction_id": direction_id,
                        "source_cutoff": cutoff,
                        "control_safety_factor": float(factor),
                        "rank_status": geometry.rank_status.value,
                        "low_rank": geometry.low_rank,
                        "high_rank": geometry.high_rank,
                        "surviving_rank": (
                            "" if geometry.surviving_rank is None else geometry.surviving_rank
                        ),
                        "augmented_rank_increment": (
                            ""
                            if geometry.augmented_rank_increment is None
                            else geometry.augmented_rank_increment
                        ),
                        "rank_identity_holds": geometry.rank_identity_holds,
                        "containment_witness": geometry.containment_witness,
                        "surviving_frobenius_fraction": (
                            ""
                            if geometry.surviving_frobenius_fraction is None
                            else repr(geometry.surviving_frobenius_fraction)
                        ),
                        "high_threshold": repr(geometry.high_threshold),
                        "control_operator_norm": repr(control_norm),
                        "cutsky_operator_norm": repr(source_norm),
                        "control_to_cutsky_operator_ratio": repr(
                            0.0 if source_norm <= np.finfo(float).tiny else control_norm / source_norm
                        ),
                        "analysis_content_id": result.content_id,
                    }
                )
    return rows, analyses


def write_matched_control_receipt(
    source_case: Task7CCaseResult,
    control_case: MatchedFullSkyControlCase,
    target: str | Path,
    *,
    source_revision: str,
    control_factors: tuple[float, ...] = (2.0, 5.0, 10.0),
) -> dict[str, object]:
    """Write a deterministic, non-terminal matched-control sensitivity receipt."""

    if (
        not isinstance(source_revision, str)
        or len(source_revision) != 40
        or any(character not in "0123456789abcdef" for character in source_revision)
    ):
        raise MatchedControlError("matched-control source revision must be a full Git SHA")
    if (
        not control_factors
        or tuple(sorted(set(control_factors))) != control_factors
        or not all(math.isfinite(value) and value > 1.0 for value in control_factors)
    ):
        raise MatchedControlError("matched-control factor registry is invalid")

    target_path = Path(target)
    if target_path.exists() and any(target_path.iterdir()):
        raise MatchedControlError("matched-control receipt target must be absent or empty")
    target_path.mkdir(parents=True, exist_ok=True)

    rows, analyses = _receipt_rows(
        source_case,
        control_case,
        control_factors=control_factors,
    )
    receipt_id = _content_id(
        _MATCHED_RECEIPT_SCHEMA,
        {
            "source_revision": source_revision,
            "source_case_id": source_case.case_id,
            "source_operator_id": source_case.operator_id,
            "control_case_id": control_case.case_id,
            "control_operator_id": control_case.operator_id,
            "control_content_id": control_case.content_id,
            "control_factors_hex": [float(value).hex() for value in control_factors],
            "analysis_content_ids": [item.content_id for item in analyses],
        },
    )
    summary = {
        "schema": _MATCHED_RECEIPT_SCHEMA,
        "source_revision": source_revision,
        "source_case_id": source_case.case_id,
        "source_operator_id": source_case.operator_id,
        "control_case_id": control_case.case_id,
        "control_operator_id": control_case.operator_id,
        "control_content_id": control_case.content_id,
        "nside": source_case.nside,
        "processing_lmax": source_case.processing_lmax,
        "transfer_kind": source_case.transfer_kind,
        "source_cutoffs": list(source_case.source_cutoffs),
        "directions": list(DIRECTION_IDS),
        "control_safety_factors": list(control_factors),
        "analysis_count": len(analyses),
        "receipt_content_id": receipt_id,
        "status": "PASS_MATCHED_FULLSKY_CONTROL_RECEIPT",
        "scientific_terminal_authorized": False,
        "empirical_beta_fit": False,
        "global_tilt": False,
        "bianchi_attribution": False,
        "claim_promotion": False,
        "merge_authorized": False,
    }
    (target_path / "summary.json").write_bytes(_canonical_json(summary) + b"\n")

    fieldnames = tuple(rows[0])
    with (target_path / "rank_sensitivity.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    nominal = [row for row in rows if row["control_safety_factor"] == 5.0]
    plt.figure(figsize=(7.2, 4.8))
    for direction_id in DIRECTION_IDS:
        selected = [row for row in nominal if row["direction_id"] == direction_id]
        plt.semilogy(
            [int(row["source_cutoff"]) for row in selected],
            [float(row["control_to_cutsky_operator_ratio"]) for row in selected],
            marker="o",
            label=direction_id,
        )
    plt.xlabel("High-source cutoff L")
    plt.ylabel("Matched full-sky / cut-sky operator norm")
    plt.title("Task-7C matched numerical-control scale")
    plt.legend(ncol=2)
    plt.tight_layout()
    plt.savefig(
        target_path / "control_to_cutsky_operator_ratio.png",
        dpi=180,
        metadata={"Software": "htt_base Task-7C matched control"},
    )
    plt.close()

    plt.figure(figsize=(7.2, 4.8))
    for direction_id in DIRECTION_IDS:
        selected = [row for row in nominal if row["direction_id"] == direction_id]
        plt.plot(
            [int(row["source_cutoff"]) for row in selected],
            [
                np.nan if row["surviving_rank"] == "" else int(row["surviving_rank"])
                for row in selected
            ],
            marker="o",
            label=direction_id,
        )
    plt.xlabel("High-source cutoff L")
    plt.ylabel("Control-anchored surviving rank")
    plt.title("Task-7C floor-safe survivor rank (s_ctrl=5)")
    plt.legend(ncol=2)
    plt.tight_layout()
    plt.savefig(
        target_path / "survivor_rank_vs_cutoff.png",
        dpi=180,
        metadata={"Software": "htt_base Task-7C matched control"},
    )
    plt.close()

    manifest_lines = [
        f"{_file_sha256(target_path / filename)}  {filename}"
        for filename in sorted(_EXPECTED_RECEIPT_FILES)
    ]
    manifest_path = target_path / "SHA256SUMS"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="ascii")
    return {
        "status": summary["status"],
        "receipt_content_id": receipt_id,
        "manifest_sha256": _file_sha256(manifest_path),
        "analysis_count": len(analyses),
    }


def verify_matched_control_receipt(target: str | Path) -> dict[str, object]:
    """Verify the companion manifest and non-promotion boundary."""

    target_path = Path(target)
    manifest_path = target_path / "SHA256SUMS"
    if not manifest_path.is_file():
        raise MatchedControlError("matched-control SHA256SUMS is absent")
    entries: dict[str, str] = {}
    for raw_line in manifest_path.read_text(encoding="ascii").splitlines():
        digest, separator, filename = raw_line.partition("  ")
        if not separator or len(digest) != 64 or filename in entries:
            raise MatchedControlError("matched-control manifest syntax is invalid")
        entries[filename] = digest
    if set(entries) != set(_EXPECTED_RECEIPT_FILES):
        raise MatchedControlError("matched-control manifest registry differs")
    for filename, expected in entries.items():
        path = target_path / filename
        if not path.is_file() or _file_sha256(path) != expected:
            raise MatchedControlError(f"matched-control hash mismatch: {filename}")
    summary = json.loads((target_path / "summary.json").read_text(encoding="ascii"))
    if summary.get("schema") != _MATCHED_RECEIPT_SCHEMA:
        raise MatchedControlError("matched-control receipt schema differs")
    if summary.get("status") != "PASS_MATCHED_FULLSKY_CONTROL_RECEIPT":
        raise MatchedControlError("matched-control receipt status differs")
    if summary.get("scientific_terminal_authorized") is not False:
        raise MatchedControlError("matched-control receipt promoted a scientific terminal")
    return {
        "status": summary["status"],
        "source_revision": summary["source_revision"],
        "receipt_content_id": summary["receipt_content_id"],
        "analysis_count": summary["analysis_count"],
        "manifest_entries": len(entries),
        "manifest_sha256": _file_sha256(manifest_path),
    }


__all__ = [
    "MatchedControlError",
    "MatchedFullSkyControlCase",
    "MatchedFullSkyDirectionalControl",
    "Task7CMatchedControlResult",
    "analyse_matched_control_matrices",
    "analyse_task7c_with_matched_fullsky_control",
    "build_matched_fullsky_control",
    "verify_matched_control_receipt",
    "write_matched_control_receipt",
]
