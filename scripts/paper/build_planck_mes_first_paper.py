#!/usr/bin/env python3
"""Build the map-free Planck MES six-family analysis and first paper draft.

The builder consumes only the eight committed inputs frozen by
``FAST_TRACK.yaml``.  It never opens sky maps.  All six predeclared feature
families are evaluated with the repository's existing observation-inclusive
leave-one-out finite-rank operator.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr, spearmanr

from obsstat.mes_row_anchor import (
    ResidualDipoleAttribution,
    build_mes_row_anchor_pool,
)
from obsstat.planck_post275_lane import observation_inclusive_max_scan


REPO_ROOT = Path(__file__).resolve().parents[2]
OBSERVED_ROW_ID = "PLANCK-PR3-SMICA-OBSERVED"

ALLOWED_INPUT_PATHS = (
    "docs/generated/pr315_planck_smica_feature_replay.npz",
    "docs/generated/pr315_planck_smica_feature_replay.json",
    "docs/generated/pr315_planck_smica_result.json",
    "docs/generated/pr314_planck_pr3_smica_existing_result.json",
    "docs/generated/planck_mes_morphology/planck_mes_morphology.npz",
    "docs/generated/planck_mes_morphology/planck_mes_morphology_result.json",
    "docs/generated/planck_mes_morphology/planck_mes_morphology_metadata.json",
    "docs/generated/planck_mes_morphology/planck_mes_morphology_replay.json",
)

REQUIRED_ANALYSIS_OUTPUTS = (
    "analysis_summary.json",
    "feature_rank_table.csv",
    "family_ablation_table.csv",
    "family_score_dependence.csv",
    "figure_local_rank_profile.pdf",
    "figure_family_rank_comparison.pdf",
    "figure_global_null_scores.pdf",
    "figure_anchor_dependence.pdf",
)

FORBIDDEN_CLAIM_STRINGS = (
    "unconditional p-value",
    "detection of anisotropy",
    "detection of shear",
    "detection of vorticity",
    "detection of global tilt",
    "mes uncovers a hidden anomaly",
    "significantly different from 133/301",
    "self-anchors add independent information",
    "bianchi family identified",
    "native-solver evidence",
    "publication ready",
    "MES amplitude coordinates",
    "the result is therefore morphology-driven rather than anchor-driven",
)

GENERIC_FEATURE_IDS = (
    "cl_l2",
    "cl_l3",
    "cl_l4",
    "cl_l5",
    "parity_even_over_odd_l2_l5",
    "power_tensor_gap_l2",
    "power_tensor_gap_l3",
    "multipole_l2_absdot",
    "multipole_l3_absdot_0",
    "multipole_l3_absdot_1",
    "multipole_l3_absdot_2",
    "multipole_plane_alignment_max_l2_l3",
)
MORPHOLOGY_FEATURE_IDS = GENERIC_FEATURE_IDS[4:]
MES_FEATURE_IDS = (
    "mes_sigma_anchor",
    "mes_omega_anchor",
    *MORPHOLOGY_FEATURE_IDS,
)


class PaperBuildError(RuntimeError):
    """Raised when a frozen input, analysis invariant, or output drifts."""


@dataclass(frozen=True)
class FamilySpec:
    family_id: str
    feature_ids: tuple[str, ...]
    role: str


FAMILY_SPECS = (
    FamilySpec(
        "GENERIC_12",
        GENERIC_FEATURE_IDS,
        "frozen generic twelve-feature benchmark control",
    ),
    FamilySpec(
        "RAW_REDUCED_10",
        GENERIC_FEATURE_IDS[:2] + MORPHOLOGY_FEATURE_IDS,
        "isolates removal of raw C4 and C5",
    ),
    FamilySpec(
        "EPS_REDUCED_10",
        ("epsilon_2", "epsilon_3", *MORPHOLOGY_FEATURE_IDS),
        "isolates the C_l-to-dimensionless-amplitude transformation",
    ),
    FamilySpec(
        "MES_10",
        MES_FEATURE_IDS,
        "primary typed squared MES-ceiling plus morphology family",
    ),
    FamilySpec(
        "ANCHORS_ONLY_2",
        MES_FEATURE_IDS[:2],
        "measures anchor-only extremeness and dependence",
    ),
    FamilySpec(
        "MORPHOLOGY_ONLY_8",
        MORPHOLOGY_FEATURE_IDS,
        "isolates the irreducible morphology contribution",
    ),
)
FAMILY_IDS = tuple(spec.family_id for spec in FAMILY_SPECS)

MES_SIGMA_TEX = r"\Sigma^2_{\max}"
MES_OMEGA_TEX = r"W^2_{\max}"

FEATURE_LABELS = {
    "cl_l2": r"$C_2$",
    "cl_l3": r"$C_3$",
    "cl_l4": r"$C_4$",
    "cl_l5": r"$C_5$",
    "epsilon_2": r"$\epsilon_2$",
    "epsilon_3": r"$\epsilon_3$",
    "mes_sigma_anchor": rf"${MES_SIGMA_TEX}$",
    "mes_omega_anchor": rf"${MES_OMEGA_TEX}$",
    "parity_even_over_odd_l2_l5": "parity",
    "power_tensor_gap_l2": r"$G_2$",
    "power_tensor_gap_l3": r"$G_3$",
    "multipole_l2_absdot": r"$d_2$",
    "multipole_l3_absdot_0": r"$d_{3,0}$",
    "multipole_l3_absdot_1": r"$d_{3,1}$",
    "multipole_l3_absdot_2": r"$d_{3,2}$",
    "multipole_plane_alignment_max_l2_l3": r"$A_{23}$",
}

REFERENCES_BIB = r"""@article{MaartensEllisStoeger1995,
  author  = {Roy Maartens and George F. R. Ellis and William R. Stoeger},
  title   = {Limits on anisotropy and inhomogeneity from the cosmic background radiation},
  journal = {Physical Review D},
  volume  = {51},
  pages   = {1525--1535},
  year    = {1995},
  doi     = {10.1103/PhysRevD.51.1525},
  eprint  = {astro-ph/9501016},
  archivePrefix = {arXiv}
}

@article{StoegerAraujoGebbie1997,
  author  = {William R. Stoeger and Marcelo E. Araujo and Tim Gebbie},
  title   = {The Limits on Cosmological Anisotropies and Inhomogeneities from COBE Data},
  journal = {The Astrophysical Journal},
  volume  = {476},
  pages   = {435},
  year    = {1997},
  eprint  = {astro-ph/9904346},
  archivePrefix = {arXiv}
}

@article{Planck2018VII,
  author  = {{Planck Collaboration}},
  title   = {Planck 2018 results. VII. Isotropy and Statistics of the CMB},
  journal = {Astronomy \& Astrophysics},
  volume  = {641},
  pages   = {A7},
  year    = {2020},
  doi     = {10.1051/0004-6361/201935201},
  eprint  = {1906.02552},
  archivePrefix = {arXiv}
}

@article{PhipsonSmyth2010,
  author  = {Belinda Phipson and Gordon K. Smyth},
  title   = {Permutation P-values Should Never Be Zero: Calculating Exact P-values When Permutations Are Randomly Drawn},
  journal = {Statistical Applications in Genetics and Molecular Biology},
  volume  = {9},
  number  = {1},
  pages   = {Article 39},
  year    = {2010},
  doi     = {10.2202/1544-6115.1585},
  eprint  = {1603.05766},
  archivePrefix = {arXiv}
}

@misc{BarberRamdas2026,
  author  = {Rina Foygel Barber and Aaditya Ramdas},
  title   = {Monte Carlo testing: non-asymptotic guarantees without joint exchangeability},
  year    = {2026},
  eprint  = {2607.23010},
  archivePrefix = {arXiv},
  primaryClass = {stat.ME}
}

@article{CopiHutererStarkman2004,
  author  = {Craig J. Copi and Dragan Huterer and Glenn D. Starkman},
  title   = {Multipole Vectors---A New Representation of the CMB Sky and Evidence for Statistical Anisotropy or Non-Gaussianity at $2\leq\ell\leq8$},
  journal = {Physical Review D},
  volume  = {70},
  pages   = {043515},
  year    = {2004},
  doi     = {10.1103/PhysRevD.70.043515},
  eprint  = {astro-ph/0310511},
  archivePrefix = {arXiv}
}

@misc{Weeks2004,
  author  = {Jeffrey R. Weeks},
  title   = {Maxwell's Multipole Vectors and the CMB},
  year    = {2004},
  eprint  = {astro-ph/0412231},
  archivePrefix = {arXiv}
}

@article{AluriRalstonWeltman2017,
  author  = {Pavan K. Aluri and John P. Ralston and Amanda Weltman},
  title   = {Alignments of parity even/odd-only multipoles in CMB},
  journal = {Monthly Notices of the Royal Astronomical Society},
  volume  = {472},
  pages   = {2410--2421},
  year    = {2017},
  doi     = {10.1093/mnras/stx2112},
  eprint  = {1703.07070},
  archivePrefix = {arXiv}
}

@article{Planck2018IV,
  author  = {{Planck Collaboration}},
  title   = {Planck 2018 results. IV. Diffuse component separation},
  journal = {Astronomy \& Astrophysics},
  volume  = {641},
  pages   = {A4},
  year    = {2020},
  doi     = {10.1051/0004-6361/201833881},
  eprint  = {1807.06208},
  archivePrefix = {arXiv}
}

@article{HeroldEtAl2025,
  author  = {Laura Herold and Graeme E. Addison and Charles L. Bennett and Hayley C. Nofi and J. L. Weiland},
  title   = {Nearly full-sky low-multipole CMB temperature anisotropy: III. CMB anomalies},
  year    = {2025},
  eprint  = {2509.03720},
  archivePrefix = {arXiv}
}
"""


def _allowed_resolved_paths() -> frozenset[Path]:
    return frozenset((REPO_ROOT / path).resolve() for path in ALLOWED_INPUT_PATHS)


def _guard_input_path(path: Path) -> Path:
    resolved = Path(path).resolve()
    if resolved not in _allowed_resolved_paths():
        raise PaperBuildError(f"path is outside the map-free input whitelist: {path}")
    return resolved


def _read_allowed_json(path: Path) -> dict[str, object]:
    resolved = _guard_input_path(path)
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PaperBuildError(f"invalid committed JSON input: {resolved}") from exc
    if not isinstance(payload, dict):
        raise PaperBuildError(f"committed JSON input must be an object: {resolved}")
    return payload


def _load_allowed_npz(path: Path) -> dict[str, object]:
    resolved = _guard_input_path(path)
    try:
        with np.load(resolved, allow_pickle=False) as package:
            return {key: np.array(package[key], copy=True) for key in package.files}
    except (OSError, ValueError, KeyError) as exc:
        raise PaperBuildError(f"invalid committed NPZ input: {resolved}") from exc


def _sha256_file(path: Path) -> str:
    resolved = _guard_input_path(path)
    digest = hashlib.sha256()
    try:
        with resolved.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PaperBuildError(f"cannot hash committed input: {resolved}") from exc
    return "sha256:" + digest.hexdigest()


def _as_strings(
    value: object, *, label: str, require_unique: bool = True
) -> tuple[str, ...]:
    array = np.asarray(value)
    if array.ndim != 1:
        raise PaperBuildError(f"{label} must be one-dimensional")
    values = tuple(str(item) for item in array.tolist())
    if any(not item for item in values):
        raise PaperBuildError(f"{label} must contain non-empty strings")
    if require_unique and len(set(values)) != len(values):
        raise PaperBuildError(f"{label} must contain unique strings")
    return values


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PaperBuildError(message)


def _rank_payload(value: Fraction, denominator: int) -> dict[str, object]:
    numerator_fraction = value * denominator
    _require(numerator_fraction.denominator == 1, "finite rank denominator drifted")
    numerator = int(numerator_fraction)
    return {
        "numerator": numerator,
        "denominator": denominator,
        "fraction": f"{numerator}/{denominator}",
        "reduced_fraction": str(value),
        "decimal": numerator / denominator,
    }


def _file_identity_table() -> dict[str, dict[str, str]]:
    roles = {
        ALLOWED_INPUT_PATHS[0]: "one observed row plus 300 paired-null generic feature rows",
        ALLOWED_INPUT_PATHS[1]: "generic feature/operator/null metadata",
        ALLOWED_INPUT_PATHS[2]: "corrected generic result",
        ALLOWED_INPUT_PATHS[3]: "frozen generic benchmark control",
        ALLOWED_INPUT_PATHS[4]: "301 by 10 MES morphology rows",
        ALLOWED_INPUT_PATHS[5]: "primary MES finite-rank result",
        ALLOWED_INPUT_PATHS[6]: "MES operator/source/claim metadata",
        ALLOWED_INPUT_PATHS[7]: "exact map-free MES replay receipt",
    }
    return {
        relative: {
            "path": relative,
            "sha256": _sha256_file(REPO_ROOT / relative),
            "role": roles[relative],
        }
        for relative in ALLOWED_INPUT_PATHS
    }


def _load_inputs() -> dict[str, object]:
    generic_npz = _load_allowed_npz(REPO_ROOT / ALLOWED_INPUT_PATHS[0])
    generic_metadata = _read_allowed_json(REPO_ROOT / ALLOWED_INPUT_PATHS[1])
    generic_result = _read_allowed_json(REPO_ROOT / ALLOWED_INPUT_PATHS[2])
    generic_benchmark = _read_allowed_json(REPO_ROOT / ALLOWED_INPUT_PATHS[3])
    mes_npz = _load_allowed_npz(REPO_ROOT / ALLOWED_INPUT_PATHS[4])
    mes_result = _read_allowed_json(REPO_ROOT / ALLOWED_INPUT_PATHS[5])
    mes_metadata = _read_allowed_json(REPO_ROOT / ALLOWED_INPUT_PATHS[6])
    mes_replay = _read_allowed_json(REPO_ROOT / ALLOWED_INPUT_PATHS[7])
    identities = _file_identity_table()

    generic_package_sha = identities[ALLOWED_INPUT_PATHS[0]]["sha256"]
    generic_metadata_sha = identities[ALLOWED_INPUT_PATHS[1]]["sha256"]
    benchmark_sha = identities[ALLOWED_INPUT_PATHS[3]]["sha256"]
    mes_package_sha = identities[ALLOWED_INPUT_PATHS[4]]["sha256"]
    mes_result_sha = identities[ALLOWED_INPUT_PATHS[5]]["sha256"]
    mes_metadata_sha = identities[ALLOWED_INPUT_PATHS[6]]["sha256"]

    feature_package_record = generic_result.get("feature_package")
    _require(isinstance(feature_package_record, dict), "generic feature record missing")
    _require(
        feature_package_record.get("package_sha256") == generic_package_sha,
        "generic feature package identity drifted",
    )
    _require(
        feature_package_record.get("metadata_sha256") == generic_metadata_sha,
        "generic feature metadata identity drifted",
    )
    _require(
        mes_metadata.get("source_feature_package_identity") == generic_package_sha,
        "MES source feature identity drifted",
    )
    _require(
        mes_metadata.get("source_feature_metadata_identity") == generic_metadata_sha,
        "MES source metadata identity drifted",
    )
    _require(mes_metadata.get("package_sha256") == mes_package_sha, "MES package drifted")
    _require(mes_metadata.get("result_sha256") == mes_result_sha, "MES result drifted")
    _require(mes_replay.get("package_sha256") == mes_package_sha, "MES replay package drifted")
    _require(mes_replay.get("result_sha256") == mes_result_sha, "MES replay result drifted")
    _require(
        mes_replay.get("metadata_sha256") == mes_metadata_sha,
        "MES replay metadata drifted",
    )
    _require(
        feature_package_record.get("branch_tail_registry", {})
        .get("benchmark_control", {})
        .get("result_sha256")
        == benchmark_sha,
        "generic benchmark identity drifted",
    )

    try:
        observed = np.asarray(generic_npz["observed_features"], dtype=float)
        nulls = np.asarray(generic_npz["null_features"], dtype=float)
        source_covariance = np.asarray(generic_npz["covariance"], dtype=float)
        null_row_ids = _as_strings(generic_npz["row_ids"], label="generic row_ids")
        source_feature_ids = _as_strings(
            generic_npz["feature_ids"], label="generic feature_ids"
        )
        source_feature_units = _as_strings(
            generic_npz["feature_units"],
            label="generic feature_units",
            require_unique=False,
        )
        source_tails = _as_strings(
            generic_npz["tails"], label="generic tails", require_unique=False
        )
        mes_rows = np.asarray(mes_npz["feature_rows"], dtype=float)
        mes_row_ids = _as_strings(mes_npz["row_ids"], label="MES row_ids")
        mes_feature_ids = _as_strings(mes_npz["feature_ids"], label="MES feature_ids")
        mes_feature_units = _as_strings(
            mes_npz["feature_units"],
            label="MES feature_units",
            require_unique=False,
        )
    except KeyError as exc:
        raise PaperBuildError(f"required map-free array missing: {exc}") from exc

    source_rows = np.vstack((observed, nulls))
    row_ids = (OBSERVED_ROW_ID, *null_row_ids)
    _require(source_rows.shape == (301, 12), "generic row pool must be 301 by 12")
    _require(mes_rows.shape == (301, 10), "MES row pool must be 301 by 10")
    _require(np.all(np.isfinite(source_rows)), "generic rows contain non-finite values")
    _require(np.all(np.isfinite(mes_rows)), "MES rows contain non-finite values")
    _require(source_feature_ids == GENERIC_FEATURE_IDS, "generic feature order drifted")
    _require(mes_feature_ids == MES_FEATURE_IDS, "MES feature order drifted")
    _require(row_ids == mes_row_ids, "generic and MES row order drifted")
    _require(source_tails == ("two-sided",) * 12, "generic tail registry drifted")
    _require(
        source_feature_units == ("microK_CMB^2",) * 4 + ("dimensionless",) * 8,
        "generic feature units drifted",
    )
    _require(
        mes_feature_units == ("dimensionless",) * 10,
        "MES feature units drifted",
    )

    try:
        states = build_mes_row_anchor_pool(
            row_ids=row_ids,
            feature_matrix=source_rows,
            feature_ids=source_feature_ids,
            feature_units=source_feature_units,
            residual_dipole_attribution=(
                ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO
            ),
            source_identity=str(mes_metadata["source_feature_package_identity"]),
            covariance_identity=str(mes_metadata["source_covariance_identity"]),
            operator_identity=str(mes_metadata["source_operator_identity"]),
        )
    except (KeyError, ValueError) as exc:
        raise PaperBuildError("active MES anchor reconstruction failed") from exc
    epsilon_rows = np.asarray(
        [[dict(state.epsilon_l)[2], dict(state.epsilon_l)[3]] for state in states],
        dtype=float,
    )
    active_anchor_rows = np.asarray(
        [
            [state.anchor("sigma").value, state.anchor("omega").value]
            for state in states
        ],
        dtype=float,
    )
    _require(
        np.array_equal(active_anchor_rows, mes_rows[:, :2]),
        "committed MES anchors differ from the active authority",
    )
    _require(
        np.array_equal(source_rows[:, 4:], mes_rows[:, 2:]),
        "generic and MES morphology columns differ",
    )

    return {
        "source_rows": source_rows,
        "source_covariance": source_covariance,
        "source_feature_ids": source_feature_ids,
        "source_feature_units": source_feature_units,
        "epsilon_rows": epsilon_rows,
        "mes_rows": mes_rows,
        "row_ids": row_ids,
        "generic_metadata": generic_metadata,
        "generic_result": generic_result,
        "generic_benchmark": generic_benchmark,
        "mes_result": mes_result,
        "mes_metadata": mes_metadata,
        "mes_replay": mes_replay,
        "input_identities": identities,
    }


def _family_matrices(inputs: Mapping[str, object]) -> dict[str, np.ndarray]:
    source_rows = np.asarray(inputs["source_rows"], dtype=float)
    epsilon_rows = np.asarray(inputs["epsilon_rows"], dtype=float)
    mes_rows = np.asarray(inputs["mes_rows"], dtype=float)
    morphology = source_rows[:, 4:]
    return {
        "GENERIC_12": source_rows,
        "RAW_REDUCED_10": np.column_stack((source_rows[:, :2], morphology)),
        "EPS_REDUCED_10": np.column_stack((epsilon_rows, morphology)),
        "MES_10": mes_rows,
        "ANCHORS_ONLY_2": mes_rows[:, :2],
        "MORPHOLOGY_ONLY_8": morphology,
    }


def _feature_units(feature_ids: Sequence[str]) -> list[str]:
    return ["microK_CMB^2" if item.startswith("cl_l") else "dimensionless" for item in feature_ids]


def _feature_role(feature_id: str) -> str:
    if feature_id.startswith("cl_l"):
        return "RAW_LOW_MULTIPOLE_POWER_COORDINATE"
    if feature_id.startswith("epsilon_"):
        return "DIMENSIONLESS_MULTIPOLE_AMPLITUDE_COORDINATE"
    if feature_id.startswith("mes_"):
        return "ROWWISE_REALIZATION_CONDITIONAL_SQUARED_NORMALIZED_MES_CEILING"
    return "DIMENSIONLESS_IRREDUCIBLE_MORPHOLOGY"


def _analyze_family(spec: FamilySpec, rows: np.ndarray) -> tuple[dict[str, object], np.ndarray]:
    tails = ("two-sided",) * len(spec.feature_ids)
    scan = observation_inclusive_max_scan(rows, tails, observation_index=0)
    reversed_scan = observation_inclusive_max_scan(
        rows[::-1], tails, observation_index=rows.shape[0] - 1
    )
    row_equivariant = (
        reversed_scan.global_p == scan.global_p
        and reversed_scan.local_p == scan.local_p
        and np.allclose(
            np.asarray(reversed_scan.row_max_scores[::-1]),
            np.asarray(scan.row_max_scores),
            rtol=0.0,
            atol=1e-15,
        )
    )
    _require(row_equivariant, f"row permutation equivariance failed for {spec.family_id}")
    local_values = tuple(scan.local_p)
    minimum = min(local_values)
    minimum_ids = [
        feature_id
        for feature_id, value in zip(spec.feature_ids, local_values, strict=True)
        if value == minimum
    ]
    features = []
    for index, (feature_id, value, local_rank) in enumerate(
        zip(spec.feature_ids, rows[0], local_values, strict=True)
    ):
        features.append(
            {
                "index": index,
                "feature_id": feature_id,
                "label": FEATURE_LABELS[feature_id],
                "role": _feature_role(feature_id),
                "unit": _feature_units((feature_id,))[0],
                "observed_value": float(value),
                "local_rank": _rank_payload(local_rank, rows.shape[0]),
                "is_observed_minimum": feature_id in minimum_ids,
            }
        )
    payload = {
        "family_id": spec.family_id,
        "role": spec.role,
        "feature_ids": list(spec.feature_ids),
        "feature_units": _feature_units(spec.feature_ids),
        "tail_policy": list(tails),
        "row_count": rows.shape[0],
        "observation_index": 0,
        "global_rank": _rank_payload(scan.global_p, rows.shape[0]),
        "observed_minimum": {
            "feature_ids": minimum_ids,
            "rank": _rank_payload(minimum, rows.shape[0]),
        },
        "observation_row_score": float(scan.observation_max_score),
        "row_scores": [float(value) for value in scan.row_max_scores],
        "row_permutation_equivariant": True,
        "features": features,
        "comparison_scope": "PAIRED_OPERATOR_SENSITIVITY_ON_ONE_FROZEN_ROW_POOL",
    }
    return payload, np.asarray(scan.row_max_scores, dtype=float)


def _artifact_registry() -> dict[str, dict[str, object]]:
    common = {
        "owner": "OBSSTAT",
        "claim_tier": "C2_DIAGNOSTIC_ONLY",
        "artifact_mode": "DRAFT_NONAUTHORITATIVE",
        "allowed_use": [
            "conditional finite-ensemble rank reporting",
            "paired operator-sensitivity description",
            "map-free draft reproduction",
            "squared normalized MES ceiling-coordinate diagnostics",
        ],
        "transfer_source": "Planck PR3 delivered SMICA products; no native Bianchi transfer",
        "null_status": "EXACT_300_ORDERED_FFP10_SMICA_CMB_PLUS_NOISE_PAIRS",
        "covariance_status": "POOLED_COVARIANCE_DIAGNOSTIC_ONLY_NOT_USED_BY_RANK_SCAN",
        "forbidden_use": [
            "physical shear or vorticity measurement",
            "local versus global source identification",
            "direction or STF construction from scalars",
            "native-solver or Bianchi-family evidence",
        ],
    }
    registry: dict[str, dict[str, object]] = {}
    for filename in REQUIRED_ANALYSIS_OUTPUTS:
        entry = dict(common)
        if filename.endswith(".pdf"):
            entry.update(
                category="DIAGNOSTIC",
                coordinate_system="scalar feature/rank space; no sky direction",
                random_seed="none; deterministic complete-row operator",
            )
        else:
            entry.update(category="DIAGNOSTIC_DATA")
        registry[filename] = entry
    return registry


def compute_analysis() -> dict[str, object]:
    """Compute all six frozen map-free family variants and diagnostics."""

    inputs = _load_inputs()
    matrices = _family_matrices(inputs)
    families: dict[str, dict[str, object]] = {}
    row_scores: dict[str, np.ndarray] = {}
    for spec in FAMILY_SPECS:
        family, scores = _analyze_family(spec, matrices[spec.family_id])
        families[spec.family_id] = family
        row_scores[spec.family_id] = scores

    mes_result = inputs["mes_result"]
    generic_result = inputs["generic_result"]
    generic_benchmark = inputs["generic_benchmark"]
    _require(
        families["MES_10"]["global_rank"]["fraction"] == "98/301",
        "primary MES rank does not replay as 98/301",
    )
    _require(
        families["GENERIC_12"]["global_rank"]["fraction"] == "133/301",
        "generic control does not replay as 133/301",
    )
    _require(
        mes_result.get("global_finite_rank", {}).get("fraction") == "98/301",
        "committed MES result baseline drifted",
    )
    _require(
        generic_result.get("PR315_joint_cutsky_family_rank") == "133/301",
        "committed corrected generic baseline drifted",
    )
    _require(
        generic_benchmark.get("finite_feature_family_p") == "19/43",
        "frozen generic benchmark baseline drifted",
    )
    mes_local = [
        feature["local_rank"]["numerator"]
        for feature in families["MES_10"]["features"]
    ]
    _require(
        mes_local == list(mes_result.get("local_finite_rank_numerators", [])),
        "MES coordinate ranks drifted",
    )

    anchors = matrices["ANCHORS_ONLY_2"]
    pearson = pearsonr(anchors[:, 0], anchors[:, 1])
    spearman = spearmanr(anchors[:, 0], anchors[:, 1])
    correlation_block = np.corrcoef(anchors, rowvar=False)
    anchor_dependence = {
        "scope": "ALL_301_OBSERVATION_PLUS_NULL_ROWS_DESCRIPTIVE_DEPENDENCE",
        "feature_ids": ["mes_sigma_anchor", "mes_omega_anchor"],
        "pearson_r": float(pearson.statistic),
        "spearman_rho": float(spearman.statistic),
        "correlation_block": correlation_block.tolist(),
        "correlation_block_rank": int(np.linalg.matrix_rank(correlation_block)),
        "correlation_block_condition_number": float(np.linalg.cond(correlation_block)),
        "independent_information_gain": False,
        "interpretation": "strong shared same-row dependence; not an information-gain test",
    }

    score_dependence = []
    for left, right in combinations(FAMILY_IDS, 2):
        result = spearmanr(row_scores[left], row_scores[right])
        score_dependence.append(
            {
                "family_a": left,
                "family_b": right,
                "spearman_rho": float(result.statistic),
                "row_count": 301,
                "interpretation": "descriptive paired operator sensitivity",
            }
        )

    operator = generic_result.get("operator_identity", {})
    summary = {
        "format": "PLANCK_MES_FIRST_PAPER_ANALYSIS_V1",
        "status": "DRAFT_NONAUTHORITATIVE",
        "owner": "OBSSTAT",
        "scope": "Planck PR3 SMICA observation plus exact 300 ordered paired FFP10 CMB+noise rows",
        "claim_id": "C-PR135-FINITE-NULL-RANK",
        "claim_status": "CONDITIONAL_DIAGNOSTIC_ONLY",
        "claim_tier": "C2",
        "public_use": False,
        "family_order": list(FAMILY_IDS),
        "row_ids": list(inputs["row_ids"]),
        "families": families,
        "anchor_dependence": anchor_dependence,
        "family_score_dependence": score_dependence,
        "comparison_interpretation": (
            "DESCRIPTIVE_PAIRED_OPERATOR_SENSITIVITY_NOT_INDEPENDENT_TESTS"
        ),
        "generic_control_preserved": True,
        "morphology_minimum_reproduced_without_anchors": (
            families["MORPHOLOGY_ONLY_8"]["observed_minimum"]["feature_ids"]
            == ["multipole_l3_absdot_0"]
            and families["MORPHOLOGY_ONLY_8"]["observed_minimum"]["rank"]["fraction"]
            == "16/301"
        ),
        "statistical_operator": {
            "implementation": "obsstat.planck_post275_lane.observation_inclusive_max_scan",
            "row_count": 301,
            "observation_count": 1,
            "null_count": 300,
            "tail_policy": "two-sided for every frozen coordinate",
            "center": "row-specific leave-one-out median",
            "local_rank": "conservative greater-or-equal observation-inclusive rank",
            "family_reducer": "minimum local rank / maximum negative-log local rank",
            "family_rank": "observation-inclusive pooled rank over all 301 row scores",
            "operator_selection": "no family selected from observed outcomes",
        },
        "mes_coordinate_authority": {
            "active_factory": "common.statistical_foundations.registered_geodesic_mes_anchors",
            "row_operator": "obsstat.mes_row_anchor.build_mes_row_anchor_pool",
            "residual_dipole_attribution": "SAG_OBSERVER_MOTION_EPS1_ZERO",
            "epsilon_formula": "sqrt((2*l+1)*C_l/(4*pi))/T0",
            "sigma_formula_check": "(3/2)*(3*epsilon_2+(3/7)*epsilon_3)^2",
            "omega_formula_check": "(3/2)*((2/15)*epsilon_2)^2",
            "sigma_target_invariant": "sigma_ab_sigma_ab_over_6H2",
            "omega_target_invariant": "omega_ab_omega_ab_over_6H2",
            "coordinate_semantics": "SQUARED_NORMALIZED_ONE_WAY_MES_CEILINGS",
            "conditioning": "REALIZATION_CONDITIONAL_SAME_ROW",
            "shared_data_dependence": True,
            "independent_information_gain": False,
        },
        "corrected_operator": {
            "estimator_id": operator.get("estimator_id"),
            "condition_number": operator.get("condition_number"),
            "singular_floor": operator.get("singular_floor"),
            "basis_dimension": operator.get("basis_dimension"),
            "retained_dimension": operator.get("retained_dimension"),
            "transfer_order": operator.get("transfer_order"),
        },
        "input_artifacts": inputs["input_identities"],
        "artifact_registry": _artifact_registry(),
        "claim_boundaries": {
            "directional_support": "BLOCKED_DIRECTIONAL_SUPPORT",
            "local_global_response": "SINGLE_SHELL_LOCAL_GLOBAL_NONIDENTIFIED",
            "family_identification": "BLOCKED_PRE_NATIVE_ATLAS",
            "covariance_role": "DIAGNOSTIC_ONLY_NOT_USED_BY_RANK_SCAN_OR_LIKELIHOOD",
            "allowed_interpretation": (
                "conditional finite-null result with a morphology-sourced "
                "observation-row minimum and coordinate-family-dependent rank"
            ),
        },
        "primary_interpretation": (
            "The MES family rank is not unusually small in the frozen ensemble; "
            "the observation-row minimum is morphology-driven, while both squared "
            "normalized MES ceilings have rank 74/301. The full family rank remains "
            "coordinate-family dependent."
        ),
        "raw_maps_reopened": False,
        "generating_command": (
            "PYTHONPATH=htt:htt/src:htt/htt python "
            "scripts/paper/build_planck_mes_first_paper.py "
            "--output-dir docs/generated/planck_mes_first_paper "
            "--paper-dir papers/planck_mes_first_observation"
        ),
    }
    _require(summary["morphology_minimum_reproduced_without_anchors"], "morphology attribution failed")
    return summary


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_tables(summary: Mapping[str, object], output_dir: Path) -> None:
    feature_rows = []
    ablation_rows = []
    for family_id in summary["family_order"]:
        family = summary["families"][family_id]
        minimum_ids = set(family["observed_minimum"]["feature_ids"])
        for feature in family["features"]:
            rank = feature["local_rank"]
            feature_rows.append(
                {
                    "family_id": family_id,
                    "feature_index": feature["index"],
                    "feature_id": feature["feature_id"],
                    "feature_role": feature["role"],
                    "unit": feature["unit"],
                    "observed_value": format(feature["observed_value"], ".17g"),
                    "local_rank_numerator": rank["numerator"],
                    "local_rank_denominator": rank["denominator"],
                    "local_rank_fraction": rank["fraction"],
                    "local_rank_decimal": format(rank["decimal"], ".17g"),
                    "is_family_minimum": feature["feature_id"] in minimum_ids,
                }
            )
        global_rank = family["global_rank"]
        minimum = family["observed_minimum"]["rank"]
        ablation_rows.append(
            {
                "family_id": family_id,
                "role": family["role"],
                "feature_count": len(family["feature_ids"]),
                "global_rank_numerator": global_rank["numerator"],
                "global_rank_denominator": global_rank["denominator"],
                "global_rank_fraction": global_rank["fraction"],
                "global_rank_decimal": format(global_rank["decimal"], ".17g"),
                "minimum_feature_ids": "|".join(family["observed_minimum"]["feature_ids"]),
                "minimum_rank_fraction": minimum["fraction"],
                "observation_row_score": format(family["observation_row_score"], ".17g"),
                "row_permutation_equivariant": family["row_permutation_equivariant"],
                "comparison_interpretation": summary["comparison_interpretation"],
            }
        )
    _write_csv(
        output_dir / "feature_rank_table.csv",
        (
            "family_id",
            "feature_index",
            "feature_id",
            "feature_role",
            "unit",
            "observed_value",
            "local_rank_numerator",
            "local_rank_denominator",
            "local_rank_fraction",
            "local_rank_decimal",
            "is_family_minimum",
        ),
        feature_rows,
    )
    _write_csv(
        output_dir / "family_ablation_table.csv",
        (
            "family_id",
            "role",
            "feature_count",
            "global_rank_numerator",
            "global_rank_denominator",
            "global_rank_fraction",
            "global_rank_decimal",
            "minimum_feature_ids",
            "minimum_rank_fraction",
            "observation_row_score",
            "row_permutation_equivariant",
            "comparison_interpretation",
        ),
        ablation_rows,
    )
    _write_csv(
        output_dir / "family_score_dependence.csv",
        (
            "family_a",
            "family_b",
            "spearman_rho",
            "row_count",
            "interpretation",
        ),
        [
            {
                **entry,
                "spearman_rho": format(entry["spearman_rho"], ".17g"),
            }
            for entry in summary["family_score_dependence"]
        ],
    )


_FIXED_PDF_TIME = datetime(2026, 8, 26, tzinfo=timezone.utc)


def _save_figure(fig: plt.Figure, path: Path, *, title: str) -> None:
    fig.savefig(
        path,
        format="pdf",
        bbox_inches="tight",
        metadata={
            "Title": title,
            "Author": "OBSSTAT diagnostic paper builder",
            "Subject": "DRAFT_NONAUTHORITATIVE conditional finite-null diagnostic",
            "Creator": "scripts/paper/build_planck_mes_first_paper.py",
            "CreationDate": _FIXED_PDF_TIME,
            "ModDate": _FIXED_PDF_TIME,
        },
    )
    plt.close(fig)


def _plot_local_rank_profile(summary: Mapping[str, object], path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10.0, 7.2), constrained_layout=True)
    for axis, family_id in zip(axes, ("GENERIC_12", "MES_10"), strict=True):
        family = summary["families"][family_id]
        values = [item["local_rank"]["decimal"] for item in family["features"]]
        labels = [item["label"] for item in family["features"]]
        colors = [
            "#c43c39" if item["is_observed_minimum"] else
            "#3b6fb6" if item["feature_id"].startswith("mes_") else "#777777"
            for item in family["features"]
        ]
        positions = np.arange(len(values))
        axis.bar(positions, values, color=colors, edgecolor="black", linewidth=0.4)
        axis.axhline(0.05, color="#555555", linestyle="--", linewidth=0.9, label="0.05 guide")
        axis.set_xticks(positions, labels, rotation=35, ha="right")
        axis.set_ylim(0.0, 1.0)
        axis.set_ylabel("observation-inclusive local rank")
        axis.set_title(family_id.replace("_", " "))
        axis.legend(loc="upper right", frameon=False)
    _save_figure(fig, path, title="Planck MES local finite-rank profile")


def _plot_family_rank_comparison(summary: Mapping[str, object], path: Path) -> None:
    family_ids = summary["family_order"]
    values = [summary["families"][item]["global_rank"]["decimal"] for item in family_ids]
    fractions = [summary["families"][item]["global_rank"]["fraction"] for item in family_ids]
    fig, axis = plt.subplots(figsize=(10.0, 4.8), constrained_layout=True)
    colors = ["#747474", "#8b8b8b", "#6996c7", "#3b6fb6", "#8c6bb1", "#c47a42"]
    positions = np.arange(len(family_ids))
    bars = axis.bar(positions, values, color=colors, edgecolor="black", linewidth=0.5)
    axis.set_xticks(positions, [item.replace("_", "\n") for item in family_ids])
    axis.set_ylabel("observation-inclusive family rank")
    axis.set_ylim(0.0, max(values) + 0.13)
    axis.set_title("Predeclared paired operator-sensitivity decomposition")
    for bar, label in zip(bars, fractions, strict=True):
        axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.015, label, ha="center", va="bottom", fontsize=9)
    axis.text(
        0.99,
        0.98,
        "Descriptive paired comparison; not independent tests",
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=8.5,
        color="#444444",
    )
    _save_figure(fig, path, title="Planck MES six-family rank comparison")


def _plot_global_null_scores(summary: Mapping[str, object], path: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(12.0, 7.2), constrained_layout=True)
    for axis, family_id in zip(axes.flat, summary["family_order"], strict=True):
        family = summary["families"][family_id]
        scores = np.asarray(family["row_scores"], dtype=float)
        axis.hist(scores[1:], bins=24, color="#9d9d9d", edgecolor="white", linewidth=0.4)
        axis.axvline(scores[0], color="#c43c39", linewidth=1.8, label="SMICA observation")
        axis.set_title(family_id.replace("_", " "), fontsize=10)
        axis.set_xlabel(r"row score $-\log(\min_j p_{ij})$")
        axis.set_ylabel("paired-null rows")
        axis.legend(frameon=False, fontsize=8)
        axis.text(
            0.97,
            0.92,
            family["global_rank"]["fraction"],
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=9,
        )
    _save_figure(fig, path, title="Planck MES finite-null row-score distributions")


def _plot_anchor_dependence(summary: Mapping[str, object], path: Path) -> None:
    inputs = _load_inputs()
    anchors = np.asarray(inputs["mes_rows"], dtype=float)[:, :2]
    dependence = summary["anchor_dependence"]
    x_scale = 1.0e-10
    y_scale = 1.0e-13
    fig, axis = plt.subplots(figsize=(6.6, 5.4), constrained_layout=True)
    axis.scatter(anchors[1:, 0] / x_scale, anchors[1:, 1] / y_scale, s=14, alpha=0.45, color="#777777", label="paired FFP10 rows")
    axis.scatter(anchors[0, 0] / x_scale, anchors[0, 1] / y_scale, s=70, color="#c43c39", edgecolor="black", linewidth=0.6, label="SMICA observation", zorder=3)
    axis.set_xlabel(rf"${MES_SIGMA_TEX}\,/\,10^{{-10}}$")
    axis.set_ylabel(rf"${MES_OMEGA_TEX}\,/\,10^{{-13}}$")
    axis.set_title("Same-row MES-anchor dependence")
    axis.legend(frameon=False)
    axis.text(
        0.03,
        0.97,
        (
            f"Pearson r = {dependence['pearson_r']:.4f}\n"
            f"Spearman rho = {dependence['spearman_rho']:.4f}\n"
            f"correlation rank = {dependence['correlation_block_rank']}\n"
            f"condition = {dependence['correlation_block_condition_number']:.2f}"
        ),
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "#bbbbbb", "alpha": 0.85},
    )
    _save_figure(fig, path, title="Planck MES same-row anchor dependence")


def _write_figures(summary: Mapping[str, object], output_dir: Path) -> None:
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.grid": True,
            "grid.alpha": 0.2,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    _plot_local_rank_profile(summary, output_dir / "figure_local_rank_profile.pdf")
    _plot_family_rank_comparison(summary, output_dir / "figure_family_rank_comparison.pdf")
    _plot_global_null_scores(summary, output_dir / "figure_global_null_scores.pdf")
    _plot_anchor_dependence(summary, output_dir / "figure_anchor_dependence.pdf")


def _tex_escape(value: str) -> str:
    return value.replace("_", r"\_")


def _tex_rank(rank: Mapping[str, object]) -> str:
    return rf"\frac{{{rank['numerator']}}}{{{rank['denominator']}}}"


def _format_observed_value(feature_id: str, value: float) -> str:
    if feature_id in {"mes_sigma_anchor", "mes_omega_anchor", "epsilon_2", "epsilon_3"}:
        return rf"{value:.7e}"
    if feature_id.startswith("cl_l"):
        return rf"{value:.6f}"
    return rf"{value:.6f}"


def render_manuscript(summary: Mapping[str, object]) -> str:
    """Render the complete manuscript using only values in the summary."""

    families = summary["families"]
    mes = families["MES_10"]
    generic = families["GENERIC_12"]
    morphology = families["MORPHOLOGY_ONLY_8"]
    anchors_only = families["ANCHORS_ONLY_2"]
    mes_rank = mes["global_rank"]
    generic_rank = generic["global_rank"]
    mes_min = mes["observed_minimum"]["rank"]
    dependence = summary["anchor_dependence"]
    corrected = summary["corrected_operator"]

    coordinate_rows = []
    for feature in mes["features"]:
        coordinate_rows.append(
            "{} & ${}$ & ${}$ \\\\".format(
                feature["label"],
                _format_observed_value(feature["feature_id"], feature["observed_value"]),
                _tex_rank(feature["local_rank"]),
            )
        )
    family_rows = []
    for family_id in summary["family_order"]:
        family = families[family_id]
        minimum_labels = ", ".join(FEATURE_LABELS[item] for item in family["observed_minimum"]["feature_ids"])
        family_rows.append(
            "{} & {} & ${}$ & {} (${}$) \\\\".format(
                _tex_escape(family_id),
                _tex_escape(family["role"]),
                _tex_rank(family["global_rank"]),
                minimum_labels,
                _tex_rank(family["observed_minimum"]["rank"]),
            )
        )
    dependence_rows = []
    for entry in summary["family_score_dependence"]:
        dependence_rows.append(
            "{} & {} & {:.4f} \\\\".format(
                _tex_escape(entry["family_a"]),
                _tex_escape(entry["family_b"]),
                entry["spearman_rho"],
            )
        )
    registry_rows = []
    for family_id in summary["family_order"]:
        family = families[family_id]
        registry_rows.append(
            r"\item[{}] {}".format(
                _tex_escape(family_id),
                ", ".join(r"\texttt{{{}}}".format(_tex_escape(item)) for item in family["feature_ids"]),
            )
        )

    return rf"""\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{amsmath,amssymb,booktabs,graphicx,hyperref}}
\graphicspath{{{{../../docs/generated/planck_mes_first_paper/}}}}
\hypersetup{{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}}

\title{{Finite-null calibration of MES-anchored low-multipole morphology in Planck PR3}}
\author{{Draft analysis note---nonauthoritative}}
\date{{26 August 2026}}

\begin{{document}}
\maketitle

\begin{{abstract}}
The large-angle cosmic microwave background provides direct constraints on departures from an almost--Friedmann--Lema\^itre--Robertson--Walker geometry, but the Maartens--Ellis--Stoeger (MES) bounds are one-way, premise-dependent ceilings rather than measurements of shear, vorticity, or geometric family. We apply typed geodesic squared normalized MES ceiling coordinates to corrected Planck PR3 SMICA low-multipole features and calibrate them with the same frozen operator on 300 ordered paired FFP10 CMB+noise realizations. The analysis combines two realization-conditional squared normalized MES ceiling coordinates with eight dimensionless irreducible morphology coordinates and uses observation-inclusive leave-one-out finite ranks. The MES-family rank is ${_tex_rank(mes_rank)}\simeq {mes_rank['decimal']:.3f}$, compared with ${_tex_rank(generic_rank)}\simeq {generic_rank['decimal']:.3f}$ for a separately frozen generic twelve-feature benchmark. The smallest coordinate rank is ${_tex_rank(mes_min)}\simeq {mes_min['decimal']:.3f}$ and comes from an octupole multipole-vector coordinate; the two MES ceilings each have rank $74/301\simeq {74/301:.3f}$. The observation-row minimum is morphology-driven rather than anchor-driven. The full family rank nevertheless remains coordinate-family dependent, because adding the two MES ceilings changes the complete-pool row-score distribution. This is a conditional finite-null methods application, not a physical or geometric identification.
\end{{abstract}}

\section{{Introduction and scope}}
The MES programme derives comparatively model-independent one-way bounds on large-scale kinematic departures from CMB multipoles under stated almost-EGS assumptions \cite{{MaartensEllisStoeger1995,StoegerAraujoGebbie1997}}. A small CMB anisotropy can restrict admissible departures under those assumptions, but the converse does not follow: scalar ceilings do not select a geometry or provide posterior evidence for one.

Large-angle CMB studies also face a statistical family-selection problem. Correlated statistics are inspected on one observed sky, while apparent prominence can depend on cleaning, masks, and the chosen statistic family \cite{{Planck2018VII,HeroldEtAl2025}}. We therefore calibrate a predeclared family with an exact complete-pool rank, following the conservative nonzero finite-rank principle \cite{{PhipsonSmyth2010}}, rather than searching post hoc for a preferred anomaly statistic.

Our scope is narrow: construct typed same-row MES coordinates from corrected $C_2$ and $C_3$, combine them with eight frozen morphology coordinates, evaluate all six predeclared family variants, and state the remaining nonidentification boundaries. This draft neither reopens maps nor extends the ensemble after seeing the result.

\section{{Planck PR3 observation and paired FFP10 null ensemble}}
The observation is Planck PR3 SMICA temperature data represented by the committed joint cut-sky low-$\ell$ feature row; SMICA and the PR3 component products are described by Planck Collaboration IV \cite{{Planck2018IV}}. The null pool contains 300 exact ordered pairs of FFP10 SMICA CMB and noise realizations. Every row has the same mask, harmonic convention, beam/pixel commonization, feature order, and numerical operator. The portable generic row is
\[
(C_2,C_3,C_4,C_5,\mathcal P,G_2,G_3,d_2,d_{{3,0}},d_{{3,1}},d_{{3,2}},A_{{23}}).
\]
The primary scope is conditional on this one SMICA row and this fixed pool. Other component-separation products and larger robustness ensembles are outside the present analysis.

\section{{Corrected joint cut-sky low-ell features}}
The corrected estimator fits all real harmonics through $\ell=5$ simultaneously on the weighted cut sky. Monopole and dipole coefficients are nuisance terms in the same fit as the retained $\ell=2,\ldots,5$ modes; only after the masked fit are retained coefficients mapped to the common beam/pixel convention. The registered basis and retained dimensions are {corrected['basis_dimension']} and {corrected['retained_dimension']}, respectively. The condition number is {corrected['condition_number']:.7g}, and the relative singular floor is {corrected['singular_floor']:.6g}. The corrected generic family reproduces the frozen ${_tex_rank(generic_rank)}$ benchmark rank.

\section{{Typed squared normalized MES realization-conditional ceilings}}
For each row,
\[
\epsilon_\ell=\frac{{1}}{{T_0}}\left[\frac{{(2\ell+1)C_\ell}}{{4\pi}}\right]^{{1/2}}.
\]
Under the registered SAG observer-motion branch, the residual cosmological dipole attribution is $\epsilon_1=0$. Define the squared normalized targets
\[
\Sigma^2\equiv\frac{{\sigma_{{ab}}\sigma^{{ab}}}}{{6H^2}},
\qquad
W^2\equiv\frac{{\omega_{{ab}}\omega^{{ab}}}}{{6H^2}}.
\]
The active geodesic MES factory supplies the one-way ceilings
\[
\Sigma^2\leq\Sigma^2_{{\max}}=\frac32\left(3\epsilon_2+\frac37\epsilon_3\right)^2,
\qquad
W^2\leq W^2_{{\max}}=\frac32\left(\frac{{2}}{{15}}\epsilon_2\right)^2.
\]
These squared normalized MES ceiling coordinates are deterministic functions of each row's $C_2$ and $C_3$, share the same data, and are not observed physical shear or vorticity. The MES family is
\[
(\Sigma^2_{{\max}},W^2_{{\max}},\mathcal P,G_2,G_3,d_2,d_{{3,0}},d_{{3,1}},d_{{3,2}},A_{{23}}).
\]

\begin{{table}}[ht]
\centering
\small
\caption{{Premises and normalization of the registered MES ceiling coordinates. These assumptions are part of the interpretation, not conclusions inferred from the data.}}
\begin{{tabular}}{{p{{0.24\linewidth}}p{{0.66\linewidth}}}}
\toprule
Item & Registered premise \\
\midrule
Congruence & geodesic \\
Regime & linear almost-EGS \\
Dipole attribution & SAG observer-motion; residual $\epsilon_1=0$ \\
Conditioning & realization-conditional same-row \\
Shear normalization & $\sigma_{{ab}}\sigma^{{ab}}/(6H^2)$ \\
Vorticity normalization & $\omega_{{ab}}\omega^{{ab}}/(6H^2)$ \\
$C_1/C_2$ status & premise-dependent derivative hierarchy \\
Converse & forbidden; a ceiling coordinate is not a measured invariant \\
\bottomrule
\end{{tabular}}
\label{{tab:mes-premises}}
\end{{table}}

\section{{Observation-inclusive finite-null family statistic}}
Let $X_{{ij}}$ be coordinate $j$ of row $i$ in the complete $N=301$ pool. For every two-sided coordinate, $m_{{ij}}$ is the median after excluding row $i$, and $D_{{ij}}=|X_{{ij}}-m_{{ij}}|$. The local complete-pool rank is
\[
p_{{ij}}=\frac1N\sum_{{k=1}}^N\mathbf 1(D_{{kj}}\ge D_{{ij}}).
\]
With $r_i=\min_j p_{{ij}}$, the family rank for the observation is
\[
p_{{\rm fam}}=\frac1N\sum_{{i=1}}^N\mathbf 1(r_i\le r_{{\rm obs}}).
\]
This operator is equivariant under complete-row permutations, includes the selected row, and treats ties conservatively.

\paragraph{{Calibration premise.}}
Under the null premise that the observed SMICA row and the 300 processed FFP10 rows are jointly exchangeable under the null, the complete row-scoring map is permutation-equivariant. Hence the observation-inclusive family rank is super-uniform, with conservative treatment of ties \cite{{PhipsonSmyth2010,BarberRamdas2026}}. If FFP10 does not faithfully represent the observational null, the reported fractions remain exact empirical ranks relative to the frozen pool, but they do not inherit unconditional Type-I-error calibration. Arithmetic exactness of the finite-pool rank is therefore distinct from scientific fidelity of the null model.

\section{{Results}}
\subsection{{Coordinate-wise ranks}}
\begin{{table}}[ht]
\centering
\caption{{MES-family observed coordinates and finite ranks. The table is diagnostic-only (C2); it does not assign physical sources.}}
\begin{{tabular}}{{lrr}}
\toprule
Coordinate & Observed value & Finite rank \\
\midrule
{chr(10).join(coordinate_rows)}
\bottomrule
\end{{tabular}}
\label{{tab:coordinate-ranks}}
\end{{table}}

The two squared normalized MES ceilings each have rank $74/301$, whereas the smallest coordinate rank is ${_tex_rank(mes_min)}$ from $d_{{3,0}}$. The same $d_{{3,0}}$ minimum and rank occur in the morphology-only family. Thus the observation-row minimum is morphology-driven rather than anchor-driven. This statement concerns the minimum coordinate only, not the complete-pool family-rank distribution.

\begin{{figure}}[ht]
\centering
\includegraphics[width=0.96\linewidth]{{figure_local_rank_profile.pdf}}
\caption{{Observation-inclusive local ranks for the generic and MES families. Red marks the family minimum; blue marks the squared normalized MES ceiling coordinates. This C2 diagnostic shows coordinate ranks only and supplies no directional or geometric identification.}}
\label{{fig:local-ranks}}
\end{{figure}}

\subsection{{Family decomposition and coordinate sensitivity}}
\begin{{table}}[ht]
\centering
\small
\caption{{Six predeclared family variants on the identical 301-row pool. Rank differences are descriptive paired operator sensitivity, not separate tests.}}
\begin{{tabular}}{{p{{0.18\linewidth}}p{{0.38\linewidth}}rr}}
\toprule
Family & Purpose & Global rank & Minimum coordinate \\
\midrule
{chr(10).join(family_rows)}
\bottomrule
\end{{tabular}}
\label{{tab:family-decomposition}}
\end{{table}}

Removing $C_4$ and $C_5$ changes the global rank from ${_tex_rank(generic_rank)}$ to ${_tex_rank(families['RAW_REDUCED_10']['global_rank'])}$. Replacing $(C_2,C_3)$ by $(\epsilon_2,\epsilon_3)$ gives ${_tex_rank(families['EPS_REDUCED_10']['global_rank'])}$, and replacing those amplitudes by the two registered squared normalized MES ceiling coordinates gives ${_tex_rank(mes_rank)}$. The ceilings-only and morphology-only ranks are ${_tex_rank(anchors_only['global_rank'])}$ and ${_tex_rank(morphology['global_rank'])}$. No difference between these fractions is assigned a separate significance.

Across all 301 rows the anchor Pearson correlation is {dependence['pearson_r']:.6f}, and the Spearman correlation is {dependence['spearman_rho']:.6f}. The two-by-two correlation block has numerical rank {dependence['correlation_block_rank']} and condition number {dependence['correlation_block_condition_number']:.3f}. These values quantify strong shared same-row dependence; they do not establish additional information.

\begin{{table}}[ht]
\centering
\scriptsize
\caption{{Spearman dependence of complete-row family scores. These paired descriptive values are not a multiple-testing panel.}}
\begin{{tabular}}{{llr}}
\toprule
Family A & Family B & Spearman $\rho$ \\
\midrule
{chr(10).join(dependence_rows)}
\bottomrule
\end{{tabular}}
\label{{tab:score-dependence}}
\end{{table}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=0.96\linewidth]{{figure_family_rank_comparison.pdf}}
\caption{{Six-family observation-inclusive rank comparison. This C2 diagnostic separates coordinate/family choices; it does not measure a physical effect of MES reparameterization.}}
\label{{fig:family-ranks}}
\end{{figure}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=0.98\linewidth]{{figure_global_null_scores.pdf}}
\caption{{Complete-pool row-score distributions with the SMICA observation marked. The covariance exported by PR-327 is not used in these ranks or histograms.}}
\label{{fig:global-scores}}
\end{{figure}}

\begin{{figure}}[ht]
\centering
\includegraphics[width=0.72\linewidth]{{figure_anchor_dependence.pdf}}
\caption{{Dependence of the two realization-conditional squared normalized MES ceilings across the fixed pool. Their strong association is expected from shared $C_2,C_3$ inputs and does not imply two independent channels.}}
\label{{fig:anchor-dependence}}
\end{{figure}}

\subsection{{Generic-control comparison}}
The MES-family rank ${_tex_rank(mes_rank)}$ and generic-control rank ${_tex_rank(generic_rank)}$ are outputs of two different predeclared coordinate families on the same rows. The decomposition in Table~\ref{{tab:family-decomposition}} shows that the change combines removal of two raw amplitudes with two coordinate transformations. It is therefore inappropriate to attribute the full numerical change to MES physics.

\section{{Interpretation and limitations}}
The primary result is a null result within the frozen finite ensemble: the family rank is not unusually small, and the observation-row minimum coordinate is an octupole morphology statistic rather than either MES ceiling. The full family rank nevertheless remains coordinate-family dependent, because adding the two MES ceilings changes the complete-pool row-score distribution. This supports the operational use and map-free calibration of typed MES ceiling coordinates, while supplying no measurement of physical shear or vorticity.

The main limitations are one SMICA component-separation product, 300 paired CMB+noise rows, realization-conditional same-row anchors, no direction-indexed source field in the portable package, no physical response that separates local and global contributions, and no native-solver morphology atlas. Planck-only local/global separation is nonidentified, and scalar coordinates cannot construct a direction or STF object. The pooled ten-dimensional covariance is a conditioning diagnostic only; it is absent from the rank scan and from any likelihood.

\section{{Conclusion}}
We constructed a typed, row-equivariant finite-null application of geodesic squared normalized MES ceiling coordinates to Planck PR3 low-multipole morphology. Within the frozen SMICA plus 300 paired FFP10 ensemble, the ten-coordinate family rank is ${_tex_rank(mes_rank)}$. Its observation-row minimum is ${_tex_rank(mes_min)}$ and is morphology-driven rather than anchor-driven. The family rank remains coordinate-family dependent: the morphology-only rank is ${_tex_rank(morphology['global_rank'])}$, while adding the two ceilings changes the complete-pool row-score distribution and gives ${_tex_rank(mes_rank)}$. The analysis is a reproducible methodological bridge and conditional null result. It does not identify a physical source, distinguish local from global kinematics, or select a Bianchi geometry.

\appendix
\section{{Exact morphology definitions and conventions}}
The eight morphology coordinates use the same frozen operator on every row. The even-to-odd low-multipole power ratio is
\[
\mathcal P=\frac{{C_2+C_4}}{{C_3+C_5}}.
\]
For each $\ell\in\{{2,3\}}$, let $A^{{(\ell)}}$ be the real symmetric trace-one angular-momentum power tensor, with ordered eigenvalues $\lambda_{{\ell,1}}\leq\lambda_{{\ell,2}}\leq\lambda_{{\ell,3}}$. The registered power-tensor gap is
\[
G_\ell=\lambda_{{\ell,3}}-\lambda_{{\ell,2}}.
\]
This construction follows the angular-momentum power-tensor family of directional statistics \cite{{AluriRalstonWeltman2017}}.

Multipole vectors are extracted from the Majorana polynomial
\[
P_\ell(z)=\sum_{{m=-\ell}}^\ell
\sqrt{{\binom{{2\ell}}{{\ell+m}}}}\,a_{{\ell m}}z^{{\ell+m}},
\]
using orthonormal Condon--Shortley harmonics and $z=e^{{i\phi}}\cot(\theta/2)$. Antipodally paired roots define unoriented axes $\boldsymbol v_{{\ell,i}}$; the stored representative has its largest-absolute Cartesian component positive \cite{{CopiHutererStarkman2004,Weeks2004}}. The quadrupole coordinate is
\[
d_2=\left|\boldsymbol v_{{2,1}}\!\cdot\!\boldsymbol v_{{2,2}}\right|.
\]
For the octupole, the three absolute pairwise products are sorted in ascending order:
\[
(d_{{3,0}},d_{{3,1}},d_{{3,2}})
=\operatorname{{sort}}\left\{{
\left|\boldsymbol v_{{3,i}}\!\cdot\!\boldsymbol v_{{3,j}}\right|:
1\leq i<j\leq3
\right\}}.
\]
Finally, define the normalized quadrupole plane normal $\widehat{{\boldsymbol n}}_2$ from $\boldsymbol v_{{2,1}}\times\boldsymbol v_{{2,2}}$ and the three normalized octupole plane normals $\widehat{{\boldsymbol n}}_{{3,ij}}$ from $\boldsymbol v_{{3,i}}\times\boldsymbol v_{{3,j}}$. The plane-alignment coordinate is
\[
A_{{23}}=\max_{{i<j}}
\left|\widehat{{\boldsymbol n}}_2\!\cdot\!\widehat{{\boldsymbol n}}_{{3,ij}}\right|.
\]
Degenerate coincident axes make the corresponding plane undefined and are rejected by the frozen operator rather than assigned an artificial direction.

\section{{Exact feature and tail registry}}
Every listed coordinate uses a two-sided tail and the same observation-inclusive scan.
\begin{{description}}
{chr(10).join(registry_rows)}
\end{{description}}
The six families were fixed before their decomposition values were computed and are not interpreted as independent hypotheses.

\section{{Map-free replay and data/code availability}}
The paper builder reads the eight committed map-free inputs recorded in \path{{docs/generated/planck_mes_first_paper/analysis_summary.json}}. It generates three CSV tables, four diagnostic PDF figures, and this source draft without opening the raw Planck archive. The raw data remain external for later robustness work. The generated summary records content identities, exact row order, operator semantics, claim ceiling, and figure/table provenance. Recomputed rational ranks require exact equality; floating dependence diagnostics are compared numerically, while PDF container bytes are not scientific acceptance criteria.

\bibliographystyle{{plain}}
\bibliography{{references}}
\end{{document}}
"""


def _assert_claim_firewall(manuscript: str) -> None:
    lowered = manuscript.lower()
    violations = [item for item in FORBIDDEN_CLAIM_STRINGS if item.lower() in lowered]
    if violations:
        raise PaperBuildError("forbidden manuscript claim strings: " + ", ".join(violations))
    if "TO_BE_COMPUTED" in manuscript or "TO_BE_GENERATED" in manuscript:
        raise PaperBuildError("unresolved manuscript marker remains")


def build_planck_mes_first_paper(
    *,
    output_dir: Path,
    paper_dir: Path,
) -> dict[str, object]:
    """Generate the analysis summary, tables, figures, and complete draft."""

    output_dir = Path(output_dir)
    paper_dir = Path(paper_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paper_dir.mkdir(parents=True, exist_ok=True)
    summary = compute_analysis()
    summary_path = output_dir / "analysis_summary.json"
    _write_json(summary_path, summary)
    _write_tables(summary, output_dir)
    _write_figures(summary, output_dir)

    # The manuscript is deliberately rendered from the generated summary file,
    # so numerical prose and tables have one machine-readable source.
    generated_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manuscript = render_manuscript(generated_summary)
    _assert_claim_firewall(manuscript)
    (paper_dir / "main.tex").write_text(manuscript, encoding="utf-8")
    (paper_dir / "references.bib").write_text(REFERENCES_BIB, encoding="utf-8")

    missing = [
        str(output_dir / filename)
        for filename in REQUIRED_ANALYSIS_OUTPUTS
        if not (output_dir / filename).is_file()
        or (output_dir / filename).stat().st_size == 0
    ]
    if missing:
        raise PaperBuildError("required outputs missing: " + ", ".join(missing))
    return generated_summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "docs/generated/planck_mes_first_paper",
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=REPO_ROOT / "papers/planck_mes_first_observation",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = build_planck_mes_first_paper(
        output_dir=args.output_dir,
        paper_dir=args.paper_dir,
    )
    print(
        json.dumps(
            {
                "status": "PASS_MAP_FREE_PLANCK_MES_FIRST_PAPER_DRAFT",
                "MES_10": summary["families"]["MES_10"]["global_rank"]["fraction"],
                "GENERIC_12": summary["families"]["GENERIC_12"]["global_rank"]["fraction"],
                "output_dir": str(args.output_dir),
                "paper_dir": str(args.paper_dir),
                "raw_maps_reopened": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
