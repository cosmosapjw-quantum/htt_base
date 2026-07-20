"""PR-179 raw-CF4 catalogue-fit directional cosmography.

The module extracts one prospectively frozen group-level statistic and
calibrates it with a position-preserving selection/systematics null.  The
reported ``H_cat`` and ``q_cat`` quantities are coefficients of the truncated
catalogue relation defined in the PR-179 spec.  They are not physical fields,
cosmological-anisotropy measurements, peculiar-flow reconstructions, or HTT
likelihood products.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.stats import beta as beta_distribution

from obsstat.catalogs.cf4_raw import Cf4RawGroupCatalog
from obsstat.finite_ensemble import rank_certificate

__all__ = [
    "DirectionalCosmographyConfig",
    "DirectionalCosmographyError",
    "analyze_directional_cosmography",
    "assign_group_folds",
    "canonical_json_sha256",
    "prepare_directional_catalogue",
]


METHOD_FAMILIES = ("CAL", "SN", "FP", "TF", "SBF", "MIXED_OTHER")
NULL_METHOD_FAMILIES = ("FP", "TF", "OTHER")
TARGET_NAMES = ("H_x", "H_y", "H_z", "q_x", "q_y", "q_z")


class DirectionalCosmographyError(ValueError):
    """Raised when a frozen PR-179 numerical contract fails closed."""


def canonical_json_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _array_sha256(value: np.ndarray, dtype: str) -> str:
    array = np.ascontiguousarray(np.asarray(value, dtype=dtype))
    return hashlib.sha256(array.tobytes()).hexdigest()


@dataclass(frozen=True)
class DirectionalCosmographyConfig:
    """Frozen numerical choices; production uses the PR-179 defaults."""

    c_km_s: float = 299792.458
    z_min: float = 0.01
    z_max: float = 0.10
    peculiar_velocity_floor_km_s: float = 300.0
    systematic_floor_mag: float = 0.05
    folds: int = 5
    fold_nside: int = 2
    stratum_nside: int = 1
    selection_nside: int = 4
    redshift_bin_edges: tuple[float, ...] = (0.01, 0.025, 0.05, 0.075, 0.10)
    minimum_stratum_groups: int = 8
    minimum_overall_supported_fraction: float = 0.90
    minimum_broad_method_supported_fraction: float = 0.80
    max_condition_number: float = 1.0e4
    minimum_information_h: float = 0.10
    minimum_information_q: float = 0.10
    minimum_information_q_cubic: float = 0.05
    max_hq_canonical_correlation: float = 0.95
    null_draws: int = 19999
    null_batch_size: int = 64
    seed_entropy: tuple[int, int] = (20260720, 179)
    alpha: float = 0.05
    confidence_level: float = 0.95

    def __post_init__(self) -> None:
        if not (0.0 < self.z_min < self.z_max):
            raise DirectionalCosmographyError("invalid frozen redshift domain")
        if self.folds != 5:
            raise DirectionalCosmographyError("PR-179 requires exactly five folds")
        if self.null_draws < 1 or self.null_batch_size < 1:
            raise DirectionalCosmographyError("null budget and batch size must be positive")
        if len(self.redshift_bin_edges) != 5:
            raise DirectionalCosmographyError("PR-179 requires four frozen redshift bins")
        if tuple(sorted(self.redshift_bin_edges)) != self.redshift_bin_edges:
            raise DirectionalCosmographyError("redshift-bin edges must be increasing")
        if self.redshift_bin_edges[0] != self.z_min or self.redshift_bin_edges[-1] != self.z_max:
            raise DirectionalCosmographyError("redshift bins must span the frozen domain")
        if not 0.0 < self.alpha < 1.0:
            raise DirectionalCosmographyError("alpha must lie in (0,1)")

    def to_dict(self) -> dict[str, object]:
        return {
            key: (list(value) if isinstance(value, tuple) else value)
            for key, value in self.__dict__.items()
        }


@dataclass(frozen=True)
class PreparedDirectionalCatalogue:
    group_id: np.ndarray
    z: np.ndarray
    y: np.ndarray
    e_dmzp: np.ndarray
    sigma: np.ndarray
    direction: np.ndarray
    method_family: np.ndarray
    null_method_family: np.ndarray
    fold: np.ndarray
    nside1_pixel: np.ndarray
    nside4_pixel: np.ndarray
    depth_bin: np.ndarray
    stratum_code: np.ndarray
    selected_row_sha256: str
    design_sha256: str
    support_report: Mapping[str, object]

    @property
    def n(self) -> int:
        return int(self.group_id.size)


@dataclass(frozen=True)
class _FoldModel:
    fold_id: int
    train: np.ndarray
    test: np.ndarray
    reduced_train: np.ndarray
    reduced_test: np.ndarray
    target_train: np.ndarray
    target_test: np.ndarray
    reduced_operator: np.ndarray
    full_operator_h: np.ndarray
    full_operator_joint: np.ndarray
    nuisance_names: tuple[str, ...]


def _healpix_pixels(ra_deg: np.ndarray, dec_deg: np.ndarray, nside: int) -> np.ndarray:
    try:
        import healpy as hp
    except ImportError as exc:  # pragma: no cover - production dependency gate
        raise DirectionalCosmographyError("healpy is required for frozen HEALPix support") from exc
    theta = np.deg2rad(90.0 - np.asarray(dec_deg, dtype=float))
    phi = np.deg2rad(np.asarray(ra_deg, dtype=float))
    return np.asarray(hp.ang2pix(nside, theta, phi, nest=True), dtype=np.int64)


def assign_group_folds(
    cluster_pixel: np.ndarray,
    method_family: np.ndarray,
    *,
    folds: int = 5,
) -> np.ndarray:
    """Count-balance complete (pixel,method) clusters deterministically."""

    pixels = np.asarray(cluster_pixel, dtype=np.int64)
    families = np.asarray(method_family).astype("U16")
    if pixels.ndim != 1 or families.shape != pixels.shape:
        raise DirectionalCosmographyError("fold cluster arrays must be one-dimensional")
    keys = [(int(pixel), str(family)) for pixel, family in zip(pixels, families)]
    members: dict[tuple[int, str], list[int]] = {}
    for index, key in enumerate(keys):
        members.setdefault(key, []).append(index)
    ordered = sorted(members, key=lambda key: (-len(members[key]), key[0], key[1]))
    loads = [0] * folds
    assignment: dict[tuple[int, str], int] = {}
    for key in ordered:
        fold = min(range(folds), key=lambda value: (loads[value], value))
        assignment[key] = fold
        loads[fold] += len(members[key])
    result = np.asarray([assignment[key] for key in keys], dtype=np.int64)
    for key, indices in members.items():
        if len(set(result[indices].tolist())) != 1:
            raise DirectionalCosmographyError(f"dependency cluster split: {key!r}")
    return result


def _depth_bins(z: np.ndarray, edges: Sequence[float]) -> np.ndarray:
    bins = np.searchsorted(np.asarray(edges, dtype=float), z, side="right") - 1
    bins = np.where(z == edges[-1], len(edges) - 2, bins)
    if np.any((bins < 0) | (bins >= len(edges) - 1)):
        raise DirectionalCosmographyError("row escaped frozen redshift bins")
    return np.asarray(bins, dtype=np.int64)


def _stratum_codes(
    fold: np.ndarray,
    sky: np.ndarray,
    family: np.ndarray,
    depth: np.ndarray,
) -> np.ndarray:
    family_code = np.asarray([NULL_METHOD_FAMILIES.index(str(value)) for value in family],
                             dtype=np.int64)
    raw = np.column_stack((fold, sky, family_code, depth)).astype("<i8", copy=False)
    _, codes = np.unique(raw, axis=0, return_inverse=True)
    return np.asarray(codes, dtype=np.int64)


def prepare_directional_catalogue(
    catalogue: Cf4RawGroupCatalog,
    config: DirectionalCosmographyConfig,
) -> PreparedDirectionalCatalogue:
    """Build the outcome-independent domain, folds, and null support."""

    primary = catalogue.primary_domain_mask(
        c_km_s=config.c_km_s,
        z_min=config.z_min,
        z_max=config.z_max,
    )
    if not np.any(primary):
        raise DirectionalCosmographyError("no groups satisfy the frozen domain")
    ids = catalogue.group_id[primary]
    z = catalogue.vcmb_km_s[primary] / config.c_km_s
    dmzp = catalogue.dmzp[primary]
    e_dmzp = catalogue.e_dmzp[primary]
    ra = catalogue.ra_deg[primary]
    dec = catalogue.dec_deg[primary]
    family = catalogue.method_family[primary]
    null_family = np.where(
        np.isin(family, np.asarray(("FP", "TF"))), family, "OTHER"
    ).astype("U16")
    radians_ra, radians_dec = np.deg2rad(ra), np.deg2rad(dec)
    direction = np.column_stack((
        np.cos(radians_dec) * np.cos(radians_ra),
        np.cos(radians_dec) * np.sin(radians_ra),
        np.sin(radians_dec),
    ))
    y = dmzp - 25.0 - 5.0 * np.log10(config.c_km_s * z)
    sigma = np.sqrt(
        np.square(e_dmzp)
        + np.square(5.0 * config.peculiar_velocity_floor_km_s
                    / (math.log(10.0) * catalogue.vcmb_km_s[primary]))
        + config.systematic_floor_mag ** 2
    )
    nside2 = _healpix_pixels(ra, dec, config.fold_nside)
    fold = assign_group_folds(nside2, family, folds=config.folds)
    nside1 = _healpix_pixels(ra, dec, config.stratum_nside)
    nside4 = _healpix_pixels(ra, dec, config.selection_nside)
    depth = _depth_bins(z, config.redshift_bin_edges)
    strata = _stratum_codes(fold, nside1, null_family, depth)
    counts = np.bincount(strata)
    supported = counts[strata] >= config.minimum_stratum_groups
    overall_fraction = float(np.mean(supported))
    unsupported_strata: list[dict[str, object]] = []
    for code in sorted(set(strata.tolist())):
        indices = np.flatnonzero(strata == code)
        if indices.size >= config.minimum_stratum_groups:
            continue
        first = int(indices[0])
        unsupported_strata.append({
            "fold": int(fold[first]),
            "nside1_pixel": int(nside1[first]),
            "broad_method_family": str(null_family[first]),
            "depth_bin": int(depth[first]),
            "group_count": int(indices.size),
            "group_id_sha256": _array_sha256(ids[indices], "<i8"),
        })
    unsupported_strata.sort(key=lambda row: (
        row["fold"], row["nside1_pixel"], row["broad_method_family"], row["depth_bin"]
    ))

    cell_method_rows: list[dict[str, object]] = []
    for pixel in sorted(set(nside1.tolist())):
        for label in METHOD_FAMILIES:
            mask = (nside1 == pixel) & (family == label)
            if not np.any(mask):
                continue
            fraction = float(np.mean(supported[mask]))
            ok = fraction >= config.minimum_broad_method_supported_fraction
            cell_method_rows.append({
                "nside1_pixel": int(pixel),
                "method_family": label,
                "groups": int(np.count_nonzero(mask)),
                "supported_fraction": fraction,
                "descriptive_80_percent_flag": bool(ok),
            })
    broad_method_rows: list[dict[str, object]] = []
    broad_method_ok = True
    for label in NULL_METHOD_FAMILIES:
        mask = null_family == label
        fraction = float(np.mean(supported[mask]))
        ok = fraction >= config.minimum_broad_method_supported_fraction
        broad_method_ok &= ok
        broad_method_rows.append({
            "broad_method_family": label,
            "groups": int(np.count_nonzero(mask)),
            "supported_fraction": fraction,
            "pass": bool(ok),
        })
    support_ok = (
        overall_fraction >= config.minimum_overall_supported_fraction
        and broad_method_ok
    )
    support_report = {
        "primary_domain_groups": int(ids.size),
        "supported_groups": int(np.count_nonzero(supported)),
        "unsupported_groups": int(np.count_nonzero(~supported)),
        "supported_fraction": overall_fraction,
        "minimum_stratum_groups": config.minimum_stratum_groups,
        "minimum_overall_supported_fraction": config.minimum_overall_supported_fraction,
        "minimum_broad_method_supported_fraction": config.minimum_broad_method_supported_fraction,
        "n_strata": int(counts.size),
        "n_supported_strata": int(np.count_nonzero(counts >= config.minimum_stratum_groups)),
        "cell_method": cell_method_rows,
        "broad_method": broad_method_rows,
        "unsupported_strata": unsupported_strata,
        "unsupported_strata_sha256": canonical_json_sha256(unsupported_strata),
        "null_support_certifiable": bool(support_ok),
    }
    # Inferential scoring uses only prospectively supported strata.  The
    # support thresholds are evaluated against the complete frozen domain.
    keep = supported
    selected_hash = catalogue.selected_row_sha256(primary)
    arrays_for_hash = {
        "primary_selected_row_sha256": selected_hash,
        "inferential_ids": _array_sha256(ids[keep], "<i8"),
        "fold": _array_sha256(fold[keep], "<i8"),
        "stratum": _array_sha256(strata[keep], "<i8"),
        "direction": _array_sha256(direction[keep], "<f8"),
        "z": _array_sha256(z[keep], "<f8"),
        "sigma": _array_sha256(sigma[keep], "<f8"),
        "e_dmzp": _array_sha256(e_dmzp[keep], "<f8"),
        "method_family": hashlib.sha256(
            "\n".join(family[keep].tolist()).encode("utf-8")
        ).hexdigest(),
        "null_method_family": hashlib.sha256(
            "\n".join(null_family[keep].tolist()).encode("utf-8")
        ).hexdigest(),
    }
    return PreparedDirectionalCatalogue(
        group_id=ids[keep],
        z=z[keep],
        y=y[keep],
        e_dmzp=e_dmzp[keep],
        sigma=sigma[keep],
        direction=direction[keep],
        method_family=family[keep],
        null_method_family=null_family[keep],
        fold=fold[keep],
        nside1_pixel=nside1[keep],
        nside4_pixel=nside4[keep],
        depth_bin=depth[keep],
        stratum_code=strata[keep],
        selected_row_sha256=_array_sha256(ids[keep], "<i8"),
        design_sha256=canonical_json_sha256(arrays_for_hash),
        support_report=support_report,
    )


def _weighted_rank(matrix: np.ndarray, weight: np.ndarray) -> tuple[int, float]:
    weighted = np.asarray(matrix, dtype=float) * np.sqrt(weight)[:, None]
    singular = np.linalg.svd(weighted, compute_uv=False)
    if singular.size == 0 or singular[0] == 0.0:
        return 0, 0.0
    tolerance = (100.0 * np.finfo(float).eps * max(weighted.shape) * singular[0])
    return int(np.count_nonzero(singular > tolerance)), float(tolerance)


def _prune_exact_aliases(
    matrix: np.ndarray,
    names: Sequence[str],
    weight: np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...]]:
    kept_columns: list[np.ndarray] = []
    kept_names: list[str] = []
    previous_rank = 0
    for column, name in zip(matrix.T, names):
        if name != "intercept" and float(np.ptp(column)) == 0.0:
            continue
        trial = np.column_stack((*kept_columns, column)) if kept_columns else column[:, None]
        rank, _ = _weighted_rank(trial, weight)
        if rank > previous_rank:
            kept_columns.append(column)
            kept_names.append(str(name))
            previous_rank = rank
    if not kept_columns:
        raise DirectionalCosmographyError("all nuisance columns were aliased")
    return np.column_stack(kept_columns), tuple(kept_names)


def _selection_density(
    pixels_train: np.ndarray,
    depth_train: np.ndarray,
    pixels_all: np.ndarray,
    depth_all: np.ndarray,
) -> np.ndarray:
    counts: dict[tuple[int, int], int] = {}
    for pixel, depth in zip(pixels_train.tolist(), depth_train.tolist()):
        key = (int(pixel), int(depth))
        counts[key] = counts.get(key, 0) + 1
    return np.asarray([
        math.log1p(counts.get((int(pixel), int(depth)), 0))
        for pixel, depth in zip(pixels_all.tolist(), depth_all.tolist())
    ], dtype=float)


def _base_design(
    data: PreparedDirectionalCatalogue,
    train: np.ndarray,
    all_rows: np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...]]:
    z = data.z[all_rows]
    # This nuisance is the prospectively frozen *reported* e_DMzp column.
    # The larger ``sigma`` array remains exclusively the WLS/studentization
    # scale and must not replace the published-error covariate.
    log_error = np.log(data.e_dmzp[all_rows])
    train_log = np.log(data.e_dmzp[train])
    log_center = float(np.mean(train_log))
    log_scale = float(np.std(train_log, ddof=0))
    if not math.isfinite(log_scale) or log_scale <= 0.0:
        raise DirectionalCosmographyError("reported-error nuisance has zero scale")
    density = _selection_density(
        data.nside4_pixel[train],
        data.depth_bin[train],
        data.nside4_pixel[all_rows],
        data.depth_bin[all_rows],
    )
    density_train = _selection_density(
        data.nside4_pixel[train],
        data.depth_bin[train],
        data.nside4_pixel[train],
        data.depth_bin[train],
    )
    density_center = float(np.mean(density_train))
    density_scale = float(np.std(density_train, ddof=0))
    if not math.isfinite(density_scale) or density_scale <= 0.0:
        density_scale = 1.0

    columns: list[np.ndarray] = [np.ones(len(all_rows)), z, np.square(z),
                                 (log_error - log_center) / log_scale]
    names = ["intercept", "z", "z_squared", "centered_log_e_DMzp"]
    for label in METHOD_FAMILIES[:-1]:
        indicator = (data.method_family[all_rows] == label).astype(float)
        columns.append(indicator)
        names.append(f"method_{label}")
    for label in METHOD_FAMILIES[:-1]:
        indicator = (data.method_family[all_rows] == label).astype(float)
        columns.append(indicator * z)
        names.append(f"method_{label}_by_z")
    columns.append((density - density_center) / density_scale)
    names.append("train_only_Nside4_depth_density")
    return np.column_stack(columns), tuple(names)


def _wls_operator(design: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    weight_sqrt = 1.0 / np.asarray(sigma, dtype=float)
    weighted = design * weight_sqrt[:, None]
    singular = np.linalg.svd(weighted, compute_uv=False)
    if singular.size == 0 or singular[-1] <= (
        100.0 * np.finfo(float).eps * max(weighted.shape) * singular[0]
    ):
        raise DirectionalCosmographyError("weighted design is rank deficient")
    return np.linalg.pinv(weighted, rcond=100.0 * np.finfo(float).eps) * weight_sqrt[None, :]


def _build_fold_models(data: PreparedDirectionalCatalogue) -> list[_FoldModel]:
    target = np.column_stack((data.direction, data.z[:, None] * data.direction))
    models: list[_FoldModel] = []
    all_rows = np.arange(data.n, dtype=np.int64)
    for fold_id in range(5):
        train = all_rows[data.fold != fold_id]
        test = all_rows[data.fold == fold_id]
        if train.size == 0 or test.size == 0:
            raise DirectionalCosmographyError("empty cross-fit fold")
        base_all, names_all = _base_design(data, train, all_rows)
        base_train, names = _prune_exact_aliases(
            base_all[train], names_all, 1.0 / np.square(data.sigma[train])
        )
        selected = [names_all.index(name) for name in names]
        base_test = base_all[test][:, selected]
        target_train, target_test = target[train], target[test]
        reduced_operator = _wls_operator(base_train, data.sigma[train])
        full_h = np.column_stack((base_train, target_train[:, :3]))
        full_joint = np.column_stack((base_train, target_train))
        models.append(_FoldModel(
            fold_id=fold_id,
            train=train,
            test=test,
            reduced_train=base_train,
            reduced_test=base_test,
            target_train=target_train,
            target_test=target_test,
            reduced_operator=reduced_operator,
            full_operator_h=_wls_operator(full_h, data.sigma[train]),
            full_operator_joint=_wls_operator(full_joint, data.sigma[train]),
            nuisance_names=names,
        ))
    return models


def _weighted_residualize(
    target: np.ndarray,
    nuisance: np.ndarray,
    weight: np.ndarray,
) -> np.ndarray:
    sqrt_weight = np.sqrt(weight)
    operator = np.linalg.pinv(
        nuisance * sqrt_weight[:, None],
        rcond=100.0 * np.finfo(float).eps,
    ) * sqrt_weight[None, :]
    return target - nuisance @ (operator @ target)


def _minimum_information_ratio(
    raw: np.ndarray,
    residual: np.ndarray,
    weight: np.ndarray,
) -> float:
    raw_gram = raw.T @ (weight[:, None] * raw)
    residual_gram = residual.T @ (weight[:, None] * residual)
    raw_min = float(np.linalg.eigvalsh(raw_gram)[0])
    residual_min = float(np.linalg.eigvalsh(residual_gram)[0])
    if raw_min <= 0.0:
        return 0.0
    return max(0.0, min(1.0, residual_min / raw_min))


def _canonical_correlation(left: np.ndarray, right: np.ndarray, weight: np.ndarray) -> float:
    sqrt_weight = np.sqrt(weight)[:, None]
    left_w, right_w = left * sqrt_weight, right * sqrt_weight
    q_left, _ = np.linalg.qr(left_w, mode="reduced")
    q_right, _ = np.linalg.qr(right_w, mode="reduced")
    singular = np.linalg.svd(q_left.T @ q_right, compute_uv=False)
    return float(singular[0]) if singular.size else 1.0


def _response_identifiability(
    data: PreparedDirectionalCatalogue,
    models: Sequence[_FoldModel],
    config: DirectionalCosmographyConfig,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    h_all, q_all = True, True
    for model in models:
        weight = 1.0 / np.square(data.sigma[model.train])
        target = model.target_train.copy()
        norms = np.sqrt(np.sum(weight[:, None] * np.square(target), axis=0))
        if np.any(~np.isfinite(norms)) or np.any(norms <= 0.0):
            raise DirectionalCosmographyError("zero target response norm")
        target /= norms
        h_raw, q_raw = target[:, :3], target[:, 3:]
        h_res = _weighted_residualize(h_raw, model.reduced_train, weight)
        q_res = _weighted_residualize(q_raw, model.reduced_train, weight)
        q_cond = _weighted_residualize(
            q_raw, np.column_stack((model.reduced_train, h_raw)), weight
        )
        cubic = np.square(data.z[model.train])[:, None] * data.direction[model.train]
        cubic_norm = np.sqrt(np.sum(weight[:, None] * np.square(cubic), axis=0))
        cubic = cubic / cubic_norm
        q_cubic = _weighted_residualize(
            q_raw,
            np.column_stack((model.reduced_train, h_raw, cubic)),
            weight,
        )
        cubic_cond = _weighted_residualize(
            cubic, np.column_stack((model.reduced_train, h_raw)), weight
        )
        h_rank, _ = _weighted_rank(h_res, weight)
        q_rank, _ = _weighted_rank(q_cond, weight)
        h_singular = np.linalg.svd(
            h_res * np.sqrt(weight)[:, None], compute_uv=False
        )
        h_condition = (
            float(h_singular[0] / h_singular[-1])
            if h_singular[-1] > 0.0 else math.inf
        )
        combined = np.column_stack((h_res, q_cond))
        q_singular = np.linalg.svd(
            combined * np.sqrt(weight)[:, None], compute_uv=False
        )
        q_condition = (
            float(q_singular[0] / q_singular[-1])
            if q_singular[-1] > 0.0 else math.inf
        )
        info_h = _minimum_information_ratio(h_raw, h_res, weight)
        info_q = _minimum_information_ratio(q_raw, q_cond, weight)
        info_q_cubic = _minimum_information_ratio(q_raw, q_cubic, weight)
        correlation = _canonical_correlation(h_res, q_res, weight)
        cubic_correlation = _canonical_correlation(q_cond, cubic_cond, weight)
        h_pass = (
            h_rank == 3
            and h_condition <= config.max_condition_number
            and info_h >= config.minimum_information_h
        )
        q_pass = (
            q_rank == 3
            and q_condition <= config.max_condition_number
            and info_q >= config.minimum_information_q
            and info_q_cubic >= config.minimum_information_q_cubic
            and correlation < config.max_hq_canonical_correlation
            and cubic_correlation < config.max_hq_canonical_correlation
        )
        h_all &= h_pass
        q_all &= q_pass
        rows.append({
            "fold": model.fold_id,
            "h_rank": h_rank,
            "q_conditional_rank": q_rank,
            "h_condition_number": h_condition,
            "q_conditional_condition_number": q_condition,
            "retained_information_h": info_h,
            "retained_information_q": info_q,
            "retained_information_q_directional_cubic": info_q_cubic,
            "h_q_canonical_correlation": correlation,
            "q_directional_cubic_canonical_correlation": cubic_correlation,
            "h_pass": bool(h_pass),
            "q_pass": bool(q_pass),
        })
    branch = "JOINT_H_Q" if h_all and q_all else ("H_ONLY" if h_all else "NONE")
    return {
        "evaluated_from_design_only": True,
        "folds": rows,
        "h_pass_all_folds": bool(h_all),
        "q_pass_all_folds": bool(q_all),
        "analysis_branch": branch,
        "q_withheld": branch != "JOINT_H_Q",
        "thresholds": {
            "max_condition_number": config.max_condition_number,
            "minimum_information_h": config.minimum_information_h,
            "minimum_information_q": config.minimum_information_q,
            "minimum_information_q_cubic": config.minimum_information_q_cubic,
            "max_hq_canonical_correlation": config.max_hq_canonical_correlation,
        },
    }


def _score_batch(
    values: np.ndarray,
    data: PreparedDirectionalCatalogue,
    models: Sequence[_FoldModel],
    branch: str,
) -> tuple[np.ndarray, np.ndarray]:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim == 1:
        matrix = matrix[:, None]
    if matrix.shape[0] != data.n:
        raise DirectionalCosmographyError("score batch row mismatch")
    scores = np.zeros(matrix.shape[1], dtype=float)
    contributions = np.zeros((5, matrix.shape[1]), dtype=float)
    for model in models:
        train_y, test_y = matrix[model.train], matrix[model.test]
        beta_reduced = model.reduced_operator @ train_y
        reduced_prediction = model.reduced_test @ beta_reduced
        if branch == "H_ONLY":
            operator = model.full_operator_h
            full_design_test = np.column_stack((model.reduced_test, model.target_test[:, :3]))
        elif branch == "JOINT_H_Q":
            operator = model.full_operator_joint
            full_design_test = np.column_stack((model.reduced_test, model.target_test))
        else:
            raise DirectionalCosmographyError("no identifiable scoring branch")
        beta_full = operator @ train_y
        full_prediction = full_design_test @ beta_full
        weight = 1.0 / np.square(data.sigma[model.test])[:, None]
        improvement = np.sum(
            weight * (np.square(test_y - reduced_prediction)
                      - np.square(test_y - full_prediction)),
            axis=0,
        )
        contributions[model.fold_id] = improvement
        scores += improvement
    return scores, contributions


def _oof_reduced_prediction(
    data: PreparedDirectionalCatalogue,
    models: Sequence[_FoldModel],
) -> np.ndarray:
    prediction = np.empty(data.n, dtype=float)
    for model in models:
        beta = model.reduced_operator @ data.y[model.train]
        prediction[model.test] = model.reduced_test @ beta
    if np.any(~np.isfinite(prediction)):
        raise DirectionalCosmographyError("non-finite out-of-fold reduced prediction")
    return prediction


def _full_design_and_operator(
    data: PreparedDirectionalCatalogue,
    branch: str,
    subset: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...], np.ndarray]:
    all_rows = np.arange(data.n, dtype=np.int64)
    use = all_rows if subset is None else all_rows[np.asarray(subset, dtype=bool)]
    if use.size < 20:
        raise DirectionalCosmographyError("deletion leaves insufficient groups")
    base_all, names_all = _base_design(data, use, all_rows)
    base_use, names = _prune_exact_aliases(
        base_all[use], names_all, 1.0 / np.square(data.sigma[use])
    )
    selected_columns = [names_all.index(name) for name in names]
    base_all = base_all[:, selected_columns]
    target = data.direction if branch == "H_ONLY" else np.column_stack(
        (data.direction, data.z[:, None] * data.direction)
    )
    design_use = np.column_stack((base_all[use], target[use]))
    operator_use = _wls_operator(design_use, data.sigma[use])
    target_rows = np.arange(len(names), design_use.shape[1], dtype=np.int64)
    embedded = np.zeros((target_rows.size, data.n), dtype=float)
    embedded[:, use] = operator_use[target_rows]
    return base_all, target, names, embedded


def _deletion_response_receipt(
    data: PreparedDirectionalCatalogue,
    branch: str,
    keep: np.ndarray,
    config: DirectionalCosmographyConfig,
) -> dict[str, object]:
    all_rows = np.arange(data.n, dtype=np.int64)
    use = all_rows[np.asarray(keep, dtype=bool)]
    base_all, names_all = _base_design(data, use, all_rows)
    base_use, names = _prune_exact_aliases(
        base_all[use], names_all, 1.0 / np.square(data.sigma[use])
    )
    selected = [names_all.index(name) for name in names]
    base_use = base_all[use][:, selected]
    target = np.column_stack((
        data.direction[use], data.z[use, None] * data.direction[use]
    ))
    weight = 1.0 / np.square(data.sigma[use])
    norms = np.sqrt(np.sum(weight[:, None] * np.square(target), axis=0))
    if np.any(norms <= 0.0) or np.any(~np.isfinite(norms)):
        raise DirectionalCosmographyError("deletion target response has zero norm")
    target /= norms
    h_raw, q_raw = target[:, :3], target[:, 3:]
    h_res = _weighted_residualize(h_raw, base_use, weight)
    h_rank, _ = _weighted_rank(h_res, weight)
    h_singular = np.linalg.svd(h_res * np.sqrt(weight)[:, None], compute_uv=False)
    h_condition = (
        float(h_singular[0] / h_singular[-1])
        if h_singular.size and h_singular[-1] > 0.0 else math.inf
    )
    h_information = _minimum_information_ratio(h_raw, h_res, weight)
    h_pass = (
        h_rank == 3
        and h_condition <= config.max_condition_number
        and h_information >= config.minimum_information_h
    )
    receipt: dict[str, object] = {
        "groups": int(use.size),
        "h_rank": h_rank,
        "h_condition_number": h_condition,
        "retained_information_h": h_information,
        "h_pass": bool(h_pass),
        "pass": bool(h_pass),
    }
    if branch == "JOINT_H_Q":
        q_cond = _weighted_residualize(
            q_raw, np.column_stack((base_use, h_raw)), weight
        )
        q_rank, _ = _weighted_rank(q_cond, weight)
        joint = np.column_stack((h_res, q_cond))
        singular = np.linalg.svd(joint * np.sqrt(weight)[:, None], compute_uv=False)
        q_condition = (
            float(singular[0] / singular[-1]) if singular[-1] > 0.0 else math.inf
        )
        q_information = _minimum_information_ratio(q_raw, q_cond, weight)
        q_pass = (
            q_rank == 3
            and q_condition <= config.max_condition_number
            and q_information >= config.minimum_information_q
        )
        receipt.update({
            "q_conditional_rank": q_rank,
            "q_conditional_condition_number": q_condition,
            "retained_information_q": q_information,
            "q_pass": bool(q_pass),
            "pass": bool(h_pass and q_pass),
        })
    return receipt


def _deletion_operators(
    data: PreparedDirectionalCatalogue,
    branch: str,
    config: DirectionalCosmographyConfig,
) -> tuple[
    np.ndarray,
    np.ndarray,
    list[tuple[str, np.ndarray, dict[str, object]]],
    list[dict[str, object]],
    int,
    tuple[str, ...],
]:
    base, target, names, full_operator = _full_design_and_operator(data, branch)
    weight = 1.0 / np.square(data.sigma)
    residual_target = _weighted_residualize(target, base, weight)
    metric = residual_target.T @ (weight[:, None] * residual_target)
    specifications: list[tuple[str, np.ndarray]] = []
    for label in METHOD_FAMILIES:
        keep = data.method_family != label
        if np.count_nonzero(~keep) == 0:
            continue
        specifications.append((f"leave_method_{label}", keep))
    for pixel in sorted(set(data.nside1_pixel.tolist())):
        keep = data.nside1_pixel != pixel
        specifications.append((f"leave_nside1_{pixel}", keep))
    midpoint = 0.05
    for label, keep in (("low_depth_only", data.z <= midpoint),
                        ("high_depth_only", data.z > midpoint)):
        specifications.append((label, keep))
    cases: list[tuple[str, np.ndarray, dict[str, object]]] = []
    failures: list[dict[str, object]] = []
    for label, keep in specifications:
        try:
            response = _deletion_response_receipt(data, branch, keep, config)
            if response["pass"] is not True:
                failures.append({
                    "case": label,
                    "status": "FAILED_RESPONSE_GATE",
                    "response": response,
                })
                continue
            operator = _full_design_and_operator(data, branch, keep)[3]
            cases.append((label, operator, response))
        except DirectionalCosmographyError as exc:
            failures.append({
                "case": label,
                "status": "FIT_OR_RANK_FAILURE",
                "error": str(exc),
            })
    return full_operator, metric, cases, failures, len(specifications), names


def _metric_distance(delta: np.ndarray, metric: np.ndarray) -> np.ndarray:
    # delta has (parameter,batch)
    squared = np.einsum("ib,ij,jb->b", delta, metric, delta, optimize=True)
    return np.sqrt(np.maximum(0.0, squared))


def _coefficient_summary(vector: np.ndarray, branch: str) -> dict[str, object]:
    factor_h = -math.log(10.0) / 5.0
    h = factor_h * np.asarray(vector[:3], dtype=float)
    h_amp = float(np.linalg.norm(h))

    def axis(value: np.ndarray) -> dict[str, float] | None:
        amplitude = float(np.linalg.norm(value))
        if amplitude == 0.0:
            return None
        unit = value / amplitude
        ra = math.degrees(math.atan2(float(unit[1]), float(unit[0]))) % 360.0
        dec = math.degrees(math.asin(float(np.clip(unit[2], -1.0, 1.0))))
        return {"ra_deg": ra, "dec_deg": dec}

    payload: dict[str, object] = {
        "H_cat_log_dipole_vector": h.tolist(),
        "H_cat_log_dipole_amplitude": h_amp,
        "H_cat_positive_axis_J2000": axis(h),
    }
    if branch == "JOINT_H_Q":
        q = (-2.0 * math.log(10.0) / 5.0) * np.asarray(vector[3:6], dtype=float)
        payload.update({
            "q_cat_dipole_vector": q.tolist(),
            "q_cat_dipole_amplitude": float(np.linalg.norm(q)),
            "q_cat_positive_axis_J2000": axis(q),
        })
    else:
        payload.update({
            "q_cat_dipole_vector": None,
            "q_cat_dipole_amplitude": None,
            "q_cat_positive_axis_J2000": None,
            "q_withheld_reason": "prospective_response_identifiability_gate_failed",
        })
    return payload


def _clopper_pearson_plus_one_interval(
    exceedance: int,
    draws: int,
    confidence: float,
) -> tuple[float, float]:
    alpha = 1.0 - confidence
    lower_binomial = 0.0 if exceedance == 0 else float(
        beta_distribution.ppf(alpha / 2.0, exceedance, draws - exceedance + 1)
    )
    upper_binomial = 1.0 if exceedance == draws else float(
        beta_distribution.ppf(1.0 - alpha / 2.0, exceedance + 1, draws - exceedance)
    )
    return (
        (1.0 + draws * lower_binomial) / (draws + 1.0),
        (1.0 + draws * upper_binomial) / (draws + 1.0),
    )


def _run_complete_null(
    data: PreparedDirectionalCatalogue,
    models: Sequence[_FoldModel],
    branch: str,
    config: DirectionalCosmographyConfig,
) -> dict[str, object]:
    observed_scores, fold_contributions = _score_batch(data.y, data, models, branch)
    observed_score = float(observed_scores[0])
    reduced_oof = _oof_reduced_prediction(data, models)
    studentized = (data.y - reduced_oof) / data.sigma
    strata = [np.flatnonzero(data.stratum_code == code)
              for code in sorted(set(data.stratum_code.tolist()))]
    if any(index.size < config.minimum_stratum_groups for index in strata):
        raise DirectionalCosmographyError("unsupported stratum entered null generator")

    (
        full_operator,
        metric,
        deletion_cases,
        deletion_failures,
        expected_deletion_cases,
        nuisance_names,
    ) = _deletion_operators(data, branch, config)
    observed_beta = full_operator @ data.y
    observed_deletions: list[dict[str, object]] = []
    observed_stability = 0.0
    for label, operator, response_receipt in deletion_cases:
        beta = operator @ data.y
        distance = float(_metric_distance((beta - observed_beta)[:, None], metric)[0])
        observed_stability = max(observed_stability, distance)
        denominator = float(np.linalg.norm(beta) * np.linalg.norm(observed_beta))
        cosine = None if denominator == 0.0 else float(np.dot(beta, observed_beta) / denominator)
        observed_deletions.append({
            "case": label,
            "target_coefficients": beta.tolist(),
            "metric_discrepancy": distance,
            "cosine_to_full": cosine,
            "response_gate": response_receipt,
        })
    observed_deletions.extend(deletion_failures)

    rng = np.random.Generator(
        np.random.PCG64DXSM(np.random.SeedSequence(config.seed_entropy))
    )
    null_scores = np.empty(config.null_draws, dtype=float)
    null_stability = np.empty(config.null_draws, dtype=float)
    null_h_amplitude = np.empty(config.null_draws, dtype=float)
    null_q_amplitude = (np.empty(config.null_draws, dtype=float)
                        if branch == "JOINT_H_Q" else None)
    stream_hasher = hashlib.sha256()
    offset = 0
    while offset < config.null_draws:
        width = min(config.null_batch_size, config.null_draws - offset)
        permuted = np.empty((data.n, width), dtype=float)
        permutation_indices = np.empty((data.n, width), dtype=np.int64)
        for indices in strata:
            ordering = np.argsort(rng.random((indices.size, width)), axis=0,
                                  kind="stable")
            chosen = indices[ordering]
            permutation_indices[indices] = chosen
            permuted[indices] = studentized[chosen]
        stream_hasher.update(np.asarray(permutation_indices, dtype="<i8").tobytes())
        values = reduced_oof[:, None] + data.sigma[:, None] * permuted
        scores, _ = _score_batch(values, data, models, branch)
        null_scores[offset:offset + width] = scores
        beta_full = full_operator @ values
        maxima = np.zeros(width, dtype=float)
        for _, operator, _ in deletion_cases:
            beta_delete = operator @ values
            maxima = np.maximum(maxima, _metric_distance(beta_delete - beta_full, metric))
        null_stability[offset:offset + width] = maxima
        null_h_amplitude[offset:offset + width] = (
            math.log(10.0) / 5.0 * np.linalg.norm(beta_full[:3], axis=0)
        )
        if null_q_amplitude is not None:
            null_q_amplitude[offset:offset + width] = (
                2.0 * math.log(10.0) / 5.0 * np.linalg.norm(beta_full[3:6], axis=0)
            )
        offset += width

    exceedance = int(np.count_nonzero(null_scores >= observed_score))
    interval = _clopper_pearson_plus_one_interval(
        exceedance, config.null_draws, config.confidence_level
    )
    mc_se = math.sqrt(
        max(0.0, (exceedance / config.null_draws)
            * (1.0 - exceedance / config.null_draws) / config.null_draws)
    )
    certificate = rank_certificate(
        n_null=config.null_draws,
        exceedance_count=exceedance,
        uncertainty_interval=interval,
        boundary=config.alpha,
        direction="below",
        confidence_level=config.confidence_level,
        uncertainty_method="iid_permutation_clopper_pearson_plus_one_rank",
        mc_se=mc_se,
    )
    stability_reference = float(np.quantile(null_stability, 0.95, method="higher"))
    fold_values = fold_contributions[:, 0]
    positive_total = float(np.sum(np.maximum(fold_values, 0.0)))
    fold_nonnegative = int(np.count_nonzero(fold_values >= 0.0))
    fold_dominance = (
        0.0 if positive_total == 0.0
        else float(np.max(np.maximum(fold_values, 0.0)) / positive_total)
    )
    stability_pass = (
        not deletion_failures
        and len(deletion_cases) == expected_deletion_cases
        and fold_nonnegative >= 4
        and fold_dominance <= 0.5
        and observed_stability <= stability_reference
    )
    coefficient = _coefficient_summary(observed_beta, branch)
    coefficient["matched_null_95_reference_envelope"] = {
        "H_cat_log_dipole_amplitude": float(
            np.quantile(null_h_amplitude, 0.95, method="higher")
        ),
        "q_cat_dipole_amplitude": (
            None if null_q_amplitude is None
            else float(np.quantile(null_q_amplitude, 0.95, method="higher"))
        ),
        "interpretation": "matched-null conditional reference; not a cosmological confidence limit",
    }
    return {
        "observed_score": observed_score,
        "fold_contributions": fold_values.tolist(),
        "null_scores": null_scores.tolist(),
        "null_scores_sha256": _array_sha256(null_scores, "<f8"),
        "null_stability_scores_sha256": _array_sha256(null_stability, "<f8"),
        "permutation_stream_sha256": stream_hasher.hexdigest(),
        "exceedance_count": exceedance,
        "rank_certificate": certificate,
        "coefficient_summary": coefficient,
        "target_coefficients": observed_beta.tolist(),
        "stability": {
            "per_fold_nonnegative_count": fold_nonnegative,
            "positive_improvement_max_fraction": fold_dominance,
            "observed_max_deletion_discrepancy": observed_stability,
            "matched_null_95_max_deletion_discrepancy": stability_reference,
            "pass": bool(stability_pass),
            "expected_cases": expected_deletion_cases,
            "evaluated_cases": len(deletion_cases),
            "failed_cases": len(deletion_failures),
            "deletions": observed_deletions,
        },
        "lineage": {
            "complete": True,
            "draws": config.null_draws,
            "rng": "NumPy PCG64DXSM",
            "seed_sequence_entropy": list(config.seed_entropy),
            "unique_replicate_ids": f"00000..{config.null_draws - 1:05d}",
            "same_rows_positions_velocities_errors_methods_folds": True,
            "per_replicate_nuisance_and_target_refit": True,
            "nuisance_names_by_fold": [list(model.nuisance_names) for model in models],
        },
    }


def _terminal(
    response: Mapping[str, object],
    support: Mapping[str, object],
    null: Mapping[str, object] | None,
    config: DirectionalCosmographyConfig,
) -> tuple[str, str]:
    if not bool(support["null_support_certifiable"]):
        return (
            "DESCRIPTIVE_ONLY_NULL_NOT_CERTIFIABLE",
            "Matched-null stratum support failed the frozen catalogue thresholds.",
        )
    branch = str(response["analysis_branch"])
    if branch == "NONE":
        return (
            "NON_INFORMATIVE_RESPONSE_OVERLAP",
            "The H_cat response failed a prospective rank/information gate.",
        )
    if null is None:
        raise DirectionalCosmographyError("eligible analysis is missing null output")
    if branch == "H_ONLY":
        return (
            "H_ONLY_SELECTION_SYSTEMATICS_CONDITIONAL",
            "The prospective q_cat response gate failed while H_cat passed; q_cat is withheld and the H-only matched-null comparison is supporting conditional evidence.",
        )
    if not bool(null["stability"]["pass"]):  # type: ignore[index]
        return (
            "NON_INFORMATIVE_SELECTION_SYSTEMATICS_DOMINATED",
            "A frozen fold/deletion stability falsifier failed.",
        )
    certificate = null["rank_certificate"]  # type: ignore[index]
    guard_lower, guard_upper = certificate["guard_interval"]
    prefix = "H-only; q_cat withheld. " if branch == "H_ONLY" else ""
    if guard_upper < config.alpha:
        return (
            "CATALOGUE_SELECTION_SYSTEMATICS_CONDITIONAL_DIRECTIONAL_RESIDUAL",
            prefix + "The frozen upper-tail statistic lies below the matched-null alpha guard; catalogue residual only.",
        )
    if guard_lower >= config.alpha:
        return (
            "MATCHED_NULL_CONTAINS_DIRECTIONAL_STATISTIC",
            prefix + "The matched selection/systematics null contains the frozen statistic.",
        )
    return (
        "NUMERICALLY_UNRESOLVED_AT_FROZEN_MC_BUDGET",
        prefix + "The finite-rank guard straddles the frozen alpha boundary.",
    )


def _supporting_matched_null_disposition(
    null: Mapping[str, object] | None,
    config: DirectionalCosmographyConfig,
) -> str | None:
    if null is None:
        return None
    if not bool(null["stability"]["pass"]):  # type: ignore[index]
        return "NON_INFORMATIVE_SELECTION_SYSTEMATICS_DOMINATED"
    guard_lower, guard_upper = null["rank_certificate"]["guard_interval"]  # type: ignore[index]
    if guard_upper < config.alpha:
        return "CATALOGUE_SELECTION_SYSTEMATICS_CONDITIONAL_DIRECTIONAL_RESIDUAL"
    if guard_lower >= config.alpha:
        return "MATCHED_NULL_CONTAINS_DIRECTIONAL_STATISTIC"
    return "NUMERICALLY_UNRESOLVED_AT_FROZEN_MC_BUDGET"


def analyze_directional_cosmography(
    catalogue: Cf4RawGroupCatalog,
    config: DirectionalCosmographyConfig | None = None,
) -> dict[str, object]:
    """Run the complete frozen PR-179 data and matched-null analysis."""

    config = DirectionalCosmographyConfig() if config is None else config
    data = prepare_directional_catalogue(catalogue, config)
    models = _build_fold_models(data)
    response = _response_identifiability(data, models, config)
    null: dict[str, object] | None = None
    if bool(data.support_report["null_support_certifiable"]) and response["analysis_branch"] != "NONE":
        null = _run_complete_null(
            data, models, str(response["analysis_branch"]), config
        )
    terminal, reason = _terminal(response, data.support_report, null, config)
    supporting_disposition = _supporting_matched_null_disposition(null, config)
    family_counts = {
        label: int(np.count_nonzero(data.method_family == label))
        for label in METHOD_FAMILIES
    }
    fold_counts = {
        str(fold): int(np.count_nonzero(data.fold == fold)) for fold in range(5)
    }
    raw_receipt = {
        "schema": "htt.pr179.raw_catalogue_receipt.v1",
        "authenticated_total_groups": catalogue.row_count,
        "inferential_groups": data.n,
        "selected_row_sha256": data.selected_row_sha256,
        "design_sha256": data.design_sha256,
        "row_id_sha256": catalogue.row_id_sha256,
        "source_hashes": dict(catalogue.source_hashes),
        "accessed_columns": {
            table: list(columns)
            for table, columns in sorted(catalogue.accessed_columns.items())
        },
        "method_family_counts": family_counts,
        "fold_counts": fold_counts,
        "domain": {
            "z_min_inclusive": config.z_min,
            "z_max_inclusive": config.z_max,
            "velocity": "table3 Vcmb, published CMB-frame systemic velocity",
            "distance": "table4 DMzp/e_DMzp",
            "coordinate": "table3 J2000 RAdeg/DEdeg",
        },
        "column_firewall": {
            "runtime_value_access_receipt_complete": True,
            "reconstruction_columns_used": False,
            "cosmology_corrected_columns_used": False,
            "cartesian_columns_used": False,
            "Dist_used": False,
            "P0_estimator_reused": False,
            "cosmological_monopole_modelled_or_subtracted": False,
        },
        "support": data.support_report,
    }
    result: dict[str, object] = {
        "schema": "htt.pr179.directional_cosmography_result.v1",
        "terminal": terminal,
        "terminal_reason": reason,
        "analysis_branch": response["analysis_branch"],
        "q_cat_withheld": response["q_withheld"],
        "supporting_h_only_matched_null_disposition": (
            supporting_disposition if response["analysis_branch"] == "H_ONLY" else None
        ),
        "selection_systematics_conditional": True,
        "not_cosmological_anisotropy": True,
        "response_identifiability": response,
        "observed_score": None if null is None else null["observed_score"],
        "rank_certificate": None if null is None else null["rank_certificate"],
        "coefficient_summary": None if null is None else null["coefficient_summary"],
        "stability_status": None if null is None else null["stability"]["pass"],  # type: ignore[index]
        "allowed_use": "internal selection/systematics-conditional raw-catalogue statistic only",
        "forbidden_use": [
            "cosmological anisotropy or isotropy claim",
            "directional Hubble constant or cosmic-acceleration measurement",
            "peculiar-flow or causal attribution",
            "CF4 P0 resolution",
            "HTT evidence or posterior",
            "geometry family transfer or native-solver claim",
        ],
    }
    return {
        "config": config.to_dict(),
        "config_sha256": canonical_json_sha256(config.to_dict()),
        "raw_catalogue_receipt": raw_receipt,
        "response_identifiability": response,
        "matched_null": null,
        "result": result,
    }
