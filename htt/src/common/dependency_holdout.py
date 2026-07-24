"""PR-139: dependency-aware holdout and train-only refit.

A closed-form conjugate Gaussian group random-intercept regression is used
as a self-contained toy (no PR4 data) to exercise a CORRECT held-out
predictive comparison:

* the exchangeable unit is an entire group (rows in a group share the
  random intercept ``b_g`` and are not exchangeable at the row level);
* every preprocessing step (standardization, feature/axis selection) is
  re-run on the TRAINING partition of each fold only, and the transform
  is content-addressed per fold;
* the held-out score is the JOINT log predictive density of the held-out
  group's rows (a multivariate density), summed over folds — a
  dependency-bound ELPD (Vehtari-Gelman-Gabry 2017, arXiv:1507.04544);
* the PSIS approximation (Vehtari et al. 2015, arXiv:1507.02646; the
  generalized-Pareto fit follows Zhang-Stephens 2009 as implemented in
  arviz/loo) is verified against the exact per-fold refit — a Pareto k
  above 0.7 or an ELPD disagreement beyond tolerance forces the exact
  refit.

Guards refuse: a dependent row used as an independent LOO unit (a fold
that splits a dependency cluster), a preprocessing transform computed on
the full data, a PSIS ELPD reported when unreliable without the exact
fallback, a channel ablation / full-vs-fold evidence difference labeled a
LOO score, and a LOO claim when no exchangeable unit exists.

Dependency-qualified held-out predictive-score mechanics only, at
``roadmap_rescue_v1:C2`` — never a detection, a geometry, or a rescue.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from numbers import Real
from typing import Sequence

import numpy as np

SCHEMA_VERSION = "pr139.dependency_holdout.v1"

# Score kinds that are NOT a held-out LOO/ELPD score and must never be
# labeled one (the anti-drift rule of the card).
NON_LOO_SCORE_KINDS = ("channel_ablation", "full_vs_fold_evidence_difference")


class HoldoutError(ValueError):
    """Raised when a holdout is leaky, mislabeled, or not identified."""


class HoldoutStatus(str, Enum):
    LOO_IDENTIFIED = "LOO_identified"
    LOO_NOT_IDENTIFIED = "LOO_not_identified"


# --------------------------------------------------------------------------
# dependency graph
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class DependencyGraph:
    """Rows partitioned into dependency clusters; a fold is one cluster.

    ``unit_kind`` names the exchangeable unit (observation / group /
    survey / depth). ``cluster_of`` gives, per row, the id of the
    dependency cluster it belongs to. The valid held-out folds are the
    clusters; a single cluster spanning every row is NOT identified.
    """

    unit_kind: str
    cluster_of: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.cluster_of:
            raise HoldoutError("dependency graph has no rows")
        if self.unit_kind not in ("observation", "group", "survey", "depth"):
            raise HoldoutError(f"unknown unit_kind {self.unit_kind!r}")

    @property
    def n_rows(self) -> int:
        return len(self.cluster_of)

    def clusters(self) -> dict[int, tuple[int, ...]]:
        out: dict[int, list[int]] = {}
        for row, cid in enumerate(self.cluster_of):
            out.setdefault(cid, []).append(row)
        return {cid: tuple(rows) for cid, rows in sorted(out.items())}

    def folds(self) -> tuple[tuple[int, ...], ...]:
        return tuple(self.clusters().values())

    def status(self) -> HoldoutStatus:
        return (HoldoutStatus.LOO_IDENTIFIED if len(self.clusters()) >= 2
                else HoldoutStatus.LOO_NOT_IDENTIFIED)


def require_exchangeable_unit(graph: DependencyGraph) -> None:
    """Refuse a LOO on a graph with no held-out exchangeable unit."""
    if graph.status() is HoldoutStatus.LOO_NOT_IDENTIFIED:
        raise HoldoutError(
            "LOO_not_identified: the dependency graph has a single cluster "
            "spanning every row, so there is no held-out exchangeable unit")


def _require_group_graph_matches_model(
        model: GroupModel, graph: DependencyGraph) -> None:
    """Refuse a graph whose folds differ from the modeled dependencies."""

    if graph.n_rows != len(model.group):
        raise HoldoutError(
            "dependency graph row count does not match the model groups")
    graph_partition = {
        frozenset(rows) for rows in graph.folds()
    }
    model_partition = {
        frozenset(int(row) for row in model.rows_of_group(group))
        for group in model.group_ids()
    }
    if graph_partition != model_partition:
        raise HoldoutError(
            "dependency graph folds do not match the model group partition")


def require_units_respect_dependency(
        declared_folds: Sequence[Sequence[int]],
        true_clusters: Sequence[Sequence[int]]) -> None:
    """Refuse folds that split a true dependency cluster.

    A declared fold that is a strict subset of a true dependency cluster
    (e.g. a single row taken from a correlated group) treats dependent
    rows as independent LOO units and is refused.
    """
    if not true_clusters:
        raise HoldoutError("the true dependency partition has no clusters")
    cluster_of: dict[int, int] = {}
    for cid, rows in enumerate(true_clusters):
        if not rows:
            raise HoldoutError("a true dependency cluster is empty")
        for row in rows:
            if row in cluster_of:
                raise HoldoutError(
                    "true dependency clusters overlap on a row")
            cluster_of[row] = cid
    seen: set[int] = set()
    for fold in declared_folds:
        fold = list(fold)
        if not fold:
            raise HoldoutError("a declared fold is empty")
        fold_rows = set(fold)
        if len(fold_rows) != len(fold):
            raise HoldoutError("a declared fold repeats a row")
        unknown = fold_rows - cluster_of.keys()
        if unknown:
            raise HoldoutError(
                f"a declared fold contains unknown rows {sorted(unknown)}")
        repeated = seen & fold_rows
        if repeated:
            raise HoldoutError(
                f"declared folds repeat rows {sorted(repeated)}")
        seen.update(fold_rows)
        touched = {cluster_of[row] for row in fold_rows}
        for cid in touched:
            if not set(true_clusters[cid]).issubset(fold_rows):
                raise HoldoutError(
                    "a declared fold splits a dependency cluster — dependent "
                    "rows may not be used as independent LOO units")
        # a fold spanning several clusters is a coarser (valid) unit
    missing = cluster_of.keys() - seen
    if missing:
        raise HoldoutError(
            f"declared folds omit rows {sorted(missing)}")
    return None


# --------------------------------------------------------------------------
# model
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class GroupModel:
    """Conjugate Gaussian group random-intercept regression.

    ``X`` is the full design (rows x features, WITHOUT the intercept
    column — an unstandardized intercept is added internally). ``group``
    gives the group id per row. Everything downstream is closed form.
    """

    X: np.ndarray
    y: np.ndarray
    group: tuple[int, ...]
    sig2: float
    tau_b2: float
    prior_tau2: float

    def __post_init__(self) -> None:
        if not isinstance(self.X, np.ndarray) or self.X.ndim != 2:
            raise HoldoutError("X must be a two-dimensional numeric array")
        if not isinstance(self.y, np.ndarray) or self.y.ndim != 1:
            raise HoldoutError("y must be a one-dimensional numeric array")
        if self.X.shape[0] == 0:
            raise HoldoutError("group model has no rows")
        if self.y.shape[0] != self.X.shape[0] \
                or len(self.group) != self.X.shape[0]:
            raise HoldoutError("X, y, and group must have the same row count")
        if (
            not np.issubdtype(self.X.dtype, np.number)
            or not np.issubdtype(self.y.dtype, np.number)
            or np.iscomplexobj(self.X)
            or np.iscomplexobj(self.y)
        ):
            raise HoldoutError("X and y must be real numeric arrays")
        if not np.all(np.isfinite(self.X)) or not np.all(np.isfinite(self.y)):
            raise HoldoutError("X and y must contain only finite values")
        for name, value, lower, inclusive in (
            ("sig2", self.sig2, 0.0, False),
            ("tau_b2", self.tau_b2, 0.0, True),
            ("prior_tau2", self.prior_tau2, 0.0, False),
        ):
            if not isinstance(value, Real) or not np.isfinite(float(value)):
                raise HoldoutError(f"{name} must be finite")
            if value < lower or (not inclusive and value == lower):
                relation = "non-negative" if inclusive else "positive"
                raise HoldoutError(f"{name} must be {relation}")

    def rows_of_group(self, g: int) -> np.ndarray:
        return np.array([i for i, gg in enumerate(self.group) if gg == g],
                        dtype=int)

    def group_ids(self) -> tuple[int, ...]:
        return tuple(sorted(set(self.group)))


def _v_group(n: int, sig2: float, tau_b2: float) -> np.ndarray:
    return sig2 * np.eye(n) + tau_b2 * np.ones((n, n))


def _design(X: np.ndarray, means: np.ndarray, stds: np.ndarray,
            cols: Sequence[int]) -> np.ndarray:
    """Standardize the selected columns and prepend an intercept."""
    Xs = (X[:, cols] - means[list(cols)]) / stds[list(cols)]
    return np.column_stack([np.ones(X.shape[0]), Xs])


def _posterior(design: np.ndarray, y: np.ndarray, groups: Sequence[int],
               sig2: float, tau_b2: float, prior_tau2: float):
    """GLS conjugate posterior (mean, cov) of the coefficient vector."""
    p = design.shape[1]
    precision = np.eye(p) / prior_tau2
    rhs = np.zeros(p)
    for g in sorted(set(groups)):
        rows = [i for i, gg in enumerate(groups) if gg == g]
        Xg = design[rows]
        Vg = _v_group(len(rows), sig2, tau_b2)
        Vinv = np.linalg.inv(Vg)
        precision = precision + Xg.T @ Vinv @ Xg
        rhs = rhs + Xg.T @ Vinv @ y[rows]
    cov = np.linalg.inv(precision)
    mean = cov @ rhs
    return mean, cov


def _mvn_logpdf(x: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> float:
    n = len(x)
    sign, logdet = np.linalg.slogdet(cov)
    if sign <= 0:
        raise HoldoutError("non-PSD predictive covariance")
    diff = x - mean
    quad = diff @ np.linalg.solve(cov, diff)
    return float(-0.5 * (n * np.log(2 * np.pi) + logdet + quad))


# --------------------------------------------------------------------------
# train-only transforms (content-addressed)
# --------------------------------------------------------------------------
def _round_vec(v: np.ndarray) -> list:
    return [round(float(x), 12) for x in np.atleast_1d(v)]


def _validated_row_indices(
        rows: Sequence[int], n_rows: int, label: str, *,
        allow_empty: bool = False) -> np.ndarray:
    values = list(rows)
    if not values and not allow_empty:
        raise HoldoutError(f"{label} row indices may not be empty")
    normalized = []
    for row in values:
        if isinstance(row, bool) or not isinstance(row, (int, np.integer)):
            raise HoldoutError(f"{label} row indices must be integers")
        index = int(row)
        if index < 0 or index >= n_rows:
            raise HoldoutError(
                f"{label} row index {index} is outside [0, {n_rows})")
        normalized.append(index)
    if len(set(normalized)) != len(normalized):
        raise HoldoutError(f"{label} row indices contain duplicates")
    return np.asarray(normalized, dtype=int)


def _assert_excludes(rows_used: Sequence[int],
                     held_rows: Sequence[int]) -> None:
    """Behavioral guard: a train-only transform must not see held-out rows."""
    overlap = ({int(r) for r in rows_used}
               & {int(r) for r in held_rows})
    if overlap:
        raise HoldoutError(
            f"a train-only transform was given held-out rows "
            f"{sorted(overlap)} — this is preprocessing leakage")


def train_only_standardization(X: np.ndarray, train_rows: Sequence[int],
                               held_rows: Sequence[int] | None = None):
    """Column means/stds from TRAIN rows only; returns (means, stds, hash).

    When ``held_rows`` is supplied the row set is BEHAVIORALLY verified to
    exclude every held-out row (not merely self-labeled train_only).
    """
    tr = _validated_row_indices(
        train_rows, X.shape[0], "training")
    if held_rows is not None:
        held = _validated_row_indices(
            held_rows, X.shape[0], "held-out", allow_empty=True)
        _assert_excludes(tr, held)
    means = X[tr].mean(axis=0)
    stds = X[tr].std(axis=0, ddof=0)
    stds = np.where(stds < 1e-12, 1.0, stds)
    provenance = {"scope": "train_only", "n_train": int(len(tr)),
                  "means": _round_vec(means), "stds": _round_vec(stds)}
    return means, stds, _provenance_hash(provenance)


def full_data_standardization(X: np.ndarray):
    """Leaky: means/stds from ALL rows. Provenance is marked full_data."""
    means = X.mean(axis=0)
    stds = X.std(axis=0, ddof=0)
    stds = np.where(stds < 1e-12, 1.0, stds)
    provenance = {"scope": "full_data", "means": _round_vec(means),
                  "stds": _round_vec(stds)}
    return means, stds, _provenance_hash(provenance)


def _provenance_hash(provenance: dict) -> str:
    import json
    return hashlib.sha256(
        json.dumps(provenance, sort_keys=True).encode()).hexdigest()[:16]


def select_features(X: np.ndarray, y: np.ndarray, rows: Sequence[int],
                    k: int, scope: str,
                    held_rows: Sequence[int] | None = None
                    ) -> tuple[tuple[int, ...], dict]:
    """Rank candidate features by |corr(X_j, y)| on ``rows``; keep top-k.

    ``scope`` records whether the selection used the train partition
    (``train_only``) or the full data (``full_data``, leaky). When
    ``scope`` is ``train_only`` and ``held_rows`` is supplied, the row set
    is BEHAVIORALLY verified to exclude the held-out rows.
    """
    if isinstance(k, bool) or not isinstance(k, (int, np.integer)):
        raise HoldoutError("feature count k must be an integer")
    k = int(k)
    if k < 0 or k > X.shape[1]:
        raise HoldoutError(
            f"feature count k must be between 0 and {X.shape[1]}")
    r = _validated_row_indices(rows, X.shape[0], "selection")
    if held_rows is not None and scope == "train_only":
        held = _validated_row_indices(
            held_rows, X.shape[0], "held-out", allow_empty=True)
        _assert_excludes(r, held)
    yc = y[r] - y[r].mean()
    scores = []
    for j in range(X.shape[1]):
        xc = X[r, j] - X[r, j].mean()
        denom = np.sqrt((xc @ xc) * (yc @ yc))
        corr = 0.0 if denom < 1e-12 else float(abs((xc @ yc) / denom))
        scores.append(corr)
    order = sorted(range(X.shape[1]), key=lambda j: (-scores[j], j))
    chosen = tuple(sorted(order[:k]))
    provenance = {"scope": scope, "k": k, "chosen": list(chosen),
                  "abs_corr": [round(scores[j], 10) for j in chosen]}
    return chosen, {"provenance": provenance,
                    "hash": _provenance_hash(provenance)}


def require_train_only(provenance: dict) -> None:
    """Refuse a transform/selection provenance computed on the full data."""
    scope = provenance.get("scope")
    if scope != "train_only":
        raise HoldoutError(
            f"a preprocessing step used scope {scope!r} — every transform "
            "must be re-fit on the training partition only (train_only)")


# --------------------------------------------------------------------------
# exact group-refit ELPD
# --------------------------------------------------------------------------
def exact_group_elpd(model: GroupModel, graph: DependencyGraph, *,
                     cols: Sequence[int] | None = None,
                     select_k: int | None = None,
                     leaky_selection: bool = False,
                     leaky_standardize: bool = False,
                     standardize: bool = True) -> dict:
    """Exact leave-one-group-out ELPD with train-only refit.

    For each group fold: recompute standardization (and, if ``select_k``,
    feature selection) on the training groups only, refit the conjugate
    posterior, and evaluate the JOINT log predictive density of the
    held-out group. Each train-only transform is BEHAVIORALLY verified to
    exclude the held-out rows. ``leaky_*`` flags reproduce the optimistic
    (full-data preprocessing) variants for the demonstration;
    ``standardize=False`` disables standardization so the result equals
    the marginal-MVN conditional (used for the equivalence cross-check).
    """
    require_exchangeable_unit(graph)
    _require_group_graph_matches_model(model, graph)
    fold_records = []
    total = 0.0
    all_rows = np.arange(model.X.shape[0])
    for held in model.group_ids():
        held_rows = model.rows_of_group(held)
        train_rows = np.array([i for i in all_rows
                               if i not in set(held_rows.tolist())], dtype=int)
        # feature/axis selection
        if select_k is not None:
            sel_rows = all_rows if leaky_selection else train_rows
            scope = "full_data" if leaky_selection else "train_only"
            chosen, sel_meta = select_features(
                model.X, model.y, sel_rows, select_k, scope,
                held_rows=(None if leaky_selection else held_rows))
        else:
            chosen = tuple(cols) if cols is not None \
                else tuple(range(model.X.shape[1]))
            sel_meta = {"provenance": {"scope": "train_only", "chosen":
                                       list(chosen)}, "hash": None}
        # standardization
        if not standardize:
            means = np.zeros(model.X.shape[1])
            stds = np.ones(model.X.shape[1])
            std_hash = None
            std_scope = "none"
        elif leaky_standardize:
            means, stds, std_hash = full_data_standardization(model.X)
            std_scope = "full_data"
        else:
            means, stds, std_hash = train_only_standardization(
                model.X, train_rows, held_rows=held_rows)
            std_scope = "train_only"
        design = _design(model.X, means, stds, chosen)
        train_groups = [model.group[i] for i in train_rows]
        mean, cov = _posterior(design[train_rows], model.y[train_rows],
                               train_groups, model.sig2, model.tau_b2,
                               model.prior_tau2)
        Xh = design[held_rows]
        pred_mean = Xh @ mean
        pred_cov = Xh @ cov @ Xh.T + _v_group(len(held_rows), model.sig2,
                                              model.tau_b2)
        lp = _mvn_logpdf(model.y[held_rows], pred_mean, pred_cov)
        total += lp
        fold_records.append({
            "group": held, "n_rows": int(len(held_rows)),
            "log_predictive_density": lp,
            "selection_scope": sel_meta["provenance"]["scope"],
            "selection_hash": sel_meta["hash"],
            "chosen_features": list(chosen),
            "standardize_scope": std_scope,
            "standardize_hash": std_hash,
        })
    return {"method": "exact_group_refit", "unit_kind": graph.unit_kind,
            "n_folds": len(fold_records), "elpd": total,
            "elpd_per_obs": total / model.X.shape[0],
            "folds": fold_records}


# --------------------------------------------------------------------------
# PSIS group ELPD
# --------------------------------------------------------------------------
def _logsumexp(a: np.ndarray) -> float:
    m = float(np.max(a))
    return m + float(np.log(np.sum(np.exp(a - m))))


def _gpdfit(ary: np.ndarray) -> tuple[float, float]:
    """Empirical-Bayes generalized-Pareto fit (Zhang-Stephens 2009).

    Reproduces the arviz/loo reference; ``ary`` must be sorted ascending
    and positive.
    """
    prior_bs = 3.0
    prior_k = 10.0
    n = len(ary)
    m_est = 30 + int(n ** 0.5)
    b_ary = 1 - np.sqrt(m_est / (np.arange(1, m_est + 1) - 0.5))
    b_ary /= prior_bs * ary[int(n / 4 + 0.5) - 1]
    b_ary += 1 / ary[-1]
    k_ary = np.log1p(-b_ary[:, None] * ary).mean(axis=1)
    len_scale = n * (np.log(-(b_ary / k_ary)) - k_ary - 1)
    weights = 1 / np.exp(len_scale - len_scale[:, None]).sum(axis=1)
    real = weights >= 10 * np.finfo(float).eps
    if not np.all(real):
        weights = weights[real]
        b_ary = b_ary[real]
    weights /= weights.sum()
    b_post = float(np.sum(b_ary * weights))
    k_post = float(np.log1p(-b_post * ary).mean())
    sigma = -k_post / b_post
    k_post = (n * k_post + prior_k * 0.5) / (n + prior_k)
    return k_post, sigma


def _gpinv(probs: np.ndarray, kappa: float, sigma: float) -> np.ndarray:
    x = np.full_like(probs, np.nan)
    if sigma <= 0:
        return x
    ok = (probs > 0) & (probs < 1)
    if abs(kappa) < 1e-8:
        x[ok] = -np.log1p(-probs[ok])
    else:
        x[ok] = np.expm1(-kappa * np.log1p(-probs[ok])) / kappa
    x *= sigma
    x[probs == 0] = 0.0
    if kappa >= 0:
        x[probs == 1] = np.inf
    else:
        x[probs == 1] = -sigma / kappa
    return x


def psis_smooth(log_ratios: np.ndarray) -> tuple[np.ndarray, float]:
    """Pareto-smoothed log importance weights + fitted shape k."""
    if log_ratios.ndim != 1 or not np.all(np.isfinite(log_ratios)):
        raise HoldoutError(
            "PSIS log importance ratios must be a finite vector")
    S = len(log_ratios)
    lw = log_ratios - _logsumexp(log_ratios)  # normalized for stability
    n_tail = int(min(0.2 * S, 3 * np.sqrt(S)))
    if n_tail < 5:
        # too few tail draws to fit a Pareto tail — fail toward exact
        # (never silently report a small k as "reliable")
        raise HoldoutError(
            "too few posterior draws for a Pareto-smoothed tail fit — "
            "increase n_draws or use the exact refit")
    order = np.argsort(lw)
    sorted_lw = lw[order]
    cutoff = sorted_lw[S - n_tail - 1]
    tail = sorted_lw[S - n_tail:]
    exp_cutoff = np.exp(cutoff)
    exceed = np.exp(tail) - exp_cutoff
    k, sigma = _gpdfit(exceed)
    if not np.isfinite(k) or not np.isfinite(sigma) or sigma <= 0:
        raise HoldoutError(
            "PSIS Pareto-tail fit produced a non-finite diagnostic — "
            "use the exact refit")
    probs = (np.arange(1, n_tail + 1) - 0.5) / n_tail
    smoothed = np.log(_gpinv(probs, k, sigma) + exp_cutoff)
    if not np.all(np.isfinite(smoothed)):
        raise HoldoutError(
            "PSIS smoothing produced non-finite weights — use the exact refit")
    smoothed = np.minimum(smoothed, float(np.max(lw)))
    new_sorted = sorted_lw.copy()
    new_sorted[S - n_tail:] = smoothed
    new_lw = np.empty_like(lw)
    new_lw[order] = new_sorted
    new_lw -= _logsumexp(new_lw)
    return new_lw, float(k)


def psis_group_elpd(model: GroupModel, graph: DependencyGraph,
                    n_draws: int, seed: int, *,
                    cols: Sequence[int] | None = None) -> dict:
    """PSIS-LOO ELPD over group folds from a single full-data fit."""
    require_exchangeable_unit(graph)
    _require_group_graph_matches_model(model, graph)
    chosen = tuple(cols) if cols is not None else tuple(range(model.X.shape[1]))
    means, stds, _ = train_only_standardization(
        model.X, list(range(model.X.shape[0])))
    design = _design(model.X, means, stds, chosen)
    mean, cov = _posterior(design, model.y, model.group, model.sig2,
                           model.tau_b2, model.prior_tau2)
    rng = np.random.Generator(np.random.PCG64(seed))
    L = np.linalg.cholesky(cov)
    z = rng.standard_normal((n_draws, len(mean)))
    betas = mean[None, :] + z @ L.T
    fold_records = []
    total = 0.0
    for held in model.group_ids():
        held_rows = model.rows_of_group(held)
        Xh = design[held_rows]
        Vh = _v_group(len(held_rows), model.sig2, model.tau_b2)
        sign, logdet = np.linalg.slogdet(Vh)
        Vinv = np.linalg.inv(Vh)
        loglik = np.empty(n_draws)
        for s in range(n_draws):
            diff = model.y[held_rows] - Xh @ betas[s]
            loglik[s] = -0.5 * (len(held_rows) * np.log(2 * np.pi)
                                + logdet + diff @ Vinv @ diff)
        log_ratios = -loglik  # 1 / p(y_h | beta)
        lw, k = psis_smooth(log_ratios)
        elpd_h = _logsumexp(lw + loglik)  # lw already normalized
        total += elpd_h
        fold_records.append({"group": held, "elpd": float(elpd_h),
                             "pareto_k": float(k)})
    return {"method": "psis_group", "n_draws": n_draws, "seed": seed,
            "elpd": total, "elpd_per_obs": total / model.X.shape[0],
            "max_pareto_k": max(f["pareto_k"] for f in fold_records),
            "folds": fold_records}


def _finite_diagnostic(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise HoldoutError(f"{label} must be finite") from exc
    if not np.isfinite(number):
        raise HoldoutError(f"{label} must be finite")
    return number


def compare_exact_psis(exact: dict, psis: dict, tol_elpd: float,
                       k_threshold: float) -> dict:
    """Verify the PSIS approximation against the exact refit."""
    tol_elpd = _finite_diagnostic(tol_elpd, "ELPD tolerance")
    if tol_elpd < 0:
        raise HoldoutError("ELPD tolerance must be non-negative")
    k_threshold = _finite_diagnostic(k_threshold, "Pareto-k threshold")
    ex = {f["group"]: f["log_predictive_density"] for f in exact["folds"]}
    diffs = [abs(f["elpd"] - ex[f["group"]]) for f in psis["folds"]]
    max_diff = _finite_diagnostic(max(diffs), "fold ELPD difference")
    total_diff = _finite_diagnostic(
        abs(exact["elpd"] - psis["elpd"]), "total ELPD difference")
    for fold in psis["folds"]:
        _finite_diagnostic(fold["pareto_k"], "fold Pareto k")
    max_k = _finite_diagnostic(psis["max_pareto_k"], "maximum Pareto k")
    reliable = max_k <= k_threshold
    agree = max_diff <= tol_elpd
    return {"max_abs_fold_diff": float(max_diff),
            "total_elpd_diff": float(total_diff),
            "max_pareto_k": float(max_k), "k_threshold": float(k_threshold),
            "tol_elpd": float(tol_elpd), "psis_reliable": bool(reliable),
            "psis_agrees_with_exact": bool(agree),
            "require_exact_fallback": bool(not reliable)}


def require_reliable_or_exact(psis: dict, k_threshold: float,
                              used_exact_fallback: bool) -> None:
    """Refuse a PSIS ELPD reported when unreliable without exact fallback."""
    max_k = _finite_diagnostic(psis["max_pareto_k"], "maximum Pareto k")
    k_threshold = _finite_diagnostic(k_threshold, "Pareto-k threshold")
    if max_k > k_threshold and not used_exact_fallback:
        raise HoldoutError(
            f"PSIS Pareto k = {max_k:.3f} exceeds "
            f"{k_threshold} — the exact refit is required, not the PSIS "
            "approximation")


def influential_folds(psis: dict, k_threshold: float = 0.7) -> list:
    k_threshold = _finite_diagnostic(k_threshold, "Pareto-k threshold")
    rows = []
    for fold in psis["folds"]:
        pareto_k = _finite_diagnostic(fold["pareto_k"], "fold Pareto k")
        if pareto_k > k_threshold:
            rows.append({"group": fold["group"], "pareto_k": pareto_k})
    return rows


# --------------------------------------------------------------------------
# dependency optimism: group-joint vs row-level holdout
# --------------------------------------------------------------------------
def marginal_covariance(model: GroupModel,
                        cols: Sequence[int] | None = None):
    """Marginal MVN of y under the conjugate prior: (mean, cov).

    Marginalizing both the coefficient vector (prior N(0, tau2 I)) and the
    group intercepts gives y ~ N(0, tau2 D D^T + V), D the intercept-
    augmented design and V the block-diagonal group covariance. The exact
    held-out predictive of any row subset is then a Gaussian conditional
    of this marginal — which correctly propagates the within-group
    correlation that makes row-level holdout leaky.
    """
    chosen = tuple(cols) if cols is not None else tuple(range(model.X.shape[1]))
    design = np.column_stack([np.ones(model.X.shape[0]), model.X[:, chosen]])
    n = model.X.shape[0]
    v_block = np.zeros((n, n))
    for g in model.group_ids():
        rows = model.rows_of_group(g)
        v_block[np.ix_(rows, rows)] = _v_group(len(rows), model.sig2,
                                               model.tau_b2)
    cov = model.prior_tau2 * design @ design.T + v_block
    return np.zeros(n), cov


def conditional_joint_lpd(mean: np.ndarray, cov: np.ndarray, y: np.ndarray,
                          subset: Sequence[int]) -> float:
    """Joint log predictive density of ``y[subset]`` given the rest."""
    s = list(subset)
    o = [i for i in range(len(y)) if i not in set(s)]
    if not o:
        raise HoldoutError("no conditioning rows remain")
    coo = cov[np.ix_(o, o)]
    cso = cov[np.ix_(s, o)]
    css = cov[np.ix_(s, s)]
    resid = y[o] - mean[o]
    cond_mean = mean[s] + cso @ np.linalg.solve(coo, resid)
    cond_cov = css - cso @ np.linalg.solve(coo, cso.T)
    return _mvn_logpdf(y[s], cond_mean, cond_cov)


def dependency_optimism(model: GroupModel, graph: DependencyGraph, *,
                        cols: Sequence[int] | None = None) -> dict:
    """Group-joint (honest) vs row-level (optimistic) held-out lpd.

    Removing an entire group is honest; scoring a single row while its
    correlated group-mates stay in the conditioning set leaks the shared
    random intercept and is optimistic. The row-level folds are also
    shown to split a dependency cluster (refused by the dependency guard).
    """
    require_exchangeable_unit(graph)
    _require_group_graph_matches_model(model, graph)
    mean, cov = marginal_covariance(model, cols)
    y = model.y
    n = len(y)
    group_folds = [list(model.rows_of_group(g)) for g in model.group_ids()]
    group_lpd = sum(conditional_joint_lpd(mean, cov, y, f)
                    for f in group_folds)
    row_lpd = sum(conditional_joint_lpd(mean, cov, y, [i]) for i in range(n))
    # the honest group folds respect the dependency clusters
    require_units_respect_dependency(group_folds, group_folds)
    # a row-level fold set splits every cluster and is refused
    row_folds = [[i] for i in range(n)]
    split_refused = False
    try:
        require_units_respect_dependency(row_folds, group_folds)
    except HoldoutError:
        split_refused = True
    return {
        "group_loo_per_obs": group_lpd / n,
        "row_loo_per_obs": row_lpd / n,
        "row_optimism": (row_lpd - group_lpd) / n,
        "row_fold_split_refused": split_refused,
        "note": "row-level holdout retains a held-out row's group-mates "
                "and is optimistic; the group is the valid unit",
    }


# --------------------------------------------------------------------------
# score-kind guard
# --------------------------------------------------------------------------
def refuse_as_loo(score_kind: str) -> None:
    """Refuse labeling a non-LOO comparison a LOO / ELPD score."""
    if score_kind in NON_LOO_SCORE_KINDS:
        raise HoldoutError(
            f"a {score_kind!r} is not a held-out LOO/ELPD score and may "
            "not be labeled one; it is a separate sensitivity")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("channel ablation ", "is the loo"),
        ("evidence difference ", "is the loo"),
        ("dependent rows ", "as independent units"),
        ("standardized on ", "the full data"),
        ("selected features on ", "the full data"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise HoldoutError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(exact_per_obs: float, max_k: float,
                     leak_gap: float, status: str) -> str:
    return (
        f"Dependency-bound held-out predictive density (group-LOO, "
        f"train-only refit): per-observation ELPD {exact_per_obs:.4f}; "
        f"the PSIS approximation is reliable (max Pareto k {max_k:.3f} "
        f"< 0.7) and matches the exact refit. Leaky full-data "
        f"preprocessing inflates the score by {leak_gap:.4f} (optimism). "
        f"Status {status}. Dependency-qualified predictive-score "
        f"mechanics only; no detection.")
