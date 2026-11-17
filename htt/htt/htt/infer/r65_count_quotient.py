"""Conditional count likelihood for the identified NVSS transverse carrier.

The statistical experiment is a pixel-centre log-intensity model, not the
all-orders Lorentz transformation of an extended-source catalogue. Conditioning
on every HEALPix ring count removes an arbitrary multiplicative ring response.
The exact exponential-family sufficient statistic is retained. Gaussian five
views are explicitly local approximations to this one likelihood.
"""
from __future__ import annotations

from dataclasses import dataclass
from copy import copy

import numpy as np
from scipy import linalg, stats


def angular_features(vectors, quadrupole=False):
    """Return (nx,ny[, STF xx-yy,xy,xz,yz]) in the ICRS frame.

    The four STF matrices have Frobenius norm one. The fifth, axisymmetric
    matrix diag(-1,-1,2)/sqrt(6), and nz are ring-constant and are omitted.
    """
    v = np.asarray(vectors, dtype=float)
    if v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all():
        raise ValueError("vectors must be finite (n,3)")
    if not np.allclose(np.sum(v * v, axis=1), 1, rtol=0, atol=2e-12):
        raise ValueError("directions must be unit vectors")
    x, y, z = v.T
    columns = [x, y]
    if quadrupole:
        columns.extend([(x*x-y*y)/np.sqrt(2), np.sqrt(2)*x*y,
                        np.sqrt(2)*x*z, np.sqrt(2)*y*z])
    return np.column_stack(columns)


@dataclass
class RingLikelihood:
    counts: np.ndarray
    features: np.ndarray
    groups: np.ndarray
    exposure: np.ndarray | None = None

    def __post_init__(self):
        self.counts = np.asarray(self.counts, dtype=float)
        self.features = np.asarray(self.features, dtype=float)
        raw_groups = np.asarray(self.groups)
        n = self.counts.size
        if (self.counts.ndim != 1 or self.features.ndim != 2 or
                self.features.shape[0] != n or self.features.shape[1] == 0 or
                raw_groups.shape != (n,) or n == 0):
            raise ValueError("need nonempty counts(n), features(n,p), groups(n)")
        if (not np.isfinite(self.counts).all() or np.any(self.counts < 0) or
                np.any(self.counts != np.floor(self.counts)) or
                not np.isfinite(self.features).all()):
            raise ValueError("counts must be nonnegative integers and features finite")
        if not np.issubdtype(raw_groups.dtype, np.integer):
            raise ValueError("group labels must be integers")
        self.group_labels, self.groups = np.unique(raw_groups, return_inverse=True)
        self.n_groups = len(self.group_labels)
        self.exposure = (np.ones(n) if self.exposure is None else
                         np.asarray(self.exposure, dtype=float))
        if (self.exposure.shape != (n,) or not np.isfinite(self.exposure).all() or
                np.any(self.exposure <= 0)):
            raise ValueError("retain only cells with finite positive exposure")
        self.totals = np.bincount(self.groups, weights=self.counts,
                                  minlength=self.n_groups)
        if self.totals.sum() == 0:
            raise ValueError("at least one observed count is required")
        self.sufficient = self.features.T @ self.counts
        self.log_exposure = np.log(self.exposure)
        self.log_partition0 = self._partition(np.zeros(n))[0]
        order = np.argsort(self.groups, kind='stable')
        self.group_indices = np.split(order, np.flatnonzero(np.diff(self.groups[order]))+1)

    def _partition(self, eta):
        logw = self.log_exposure + eta
        shift = np.full(self.n_groups, -np.inf)
        np.maximum.at(shift, self.groups, logw)
        w = np.exp(logw-shift[self.groups])
        sums = np.bincount(self.groups, weights=w, minlength=self.n_groups)
        return shift+np.log(sums), w/sums[self.groups]

    def evaluate(self, theta):
        theta = np.asarray(theta, dtype=float)
        if theta.shape != (self.features.shape[1],) or not np.isfinite(theta).all():
            raise ValueError("parameter shape or finiteness error")
        eta = self.features @ theta
        logz, prob = self._partition(eta)
        mu = self.totals[self.groups]*prob
        ll = float(self.sufficient @ theta - self.totals @ (logz-self.log_partition0))
        score = self.sufficient-self.features.T @ mu
        means = np.column_stack([
            np.bincount(self.groups, weights=prob*self.features[:, j],
                        minlength=self.n_groups)
            for j in range(self.features.shape[1])])
        fisher = self.features.T @ (mu[:, None]*self.features)
        fisher -= means.T @ (self.totals[:, None]*means)
        fisher = .5*(fisher+fisher.T)
        return ll, score, fisher, mu

    def probabilities(self, theta):
        return self._partition(self.features @ np.asarray(theta, dtype=float))[1]

    def simulate(self, theta, rng):
        """Exact conditional multinomial draw; no LSS/multiplicity is simulated."""
        p = self.probabilities(theta)
        y = np.zeros(self.counts.size, dtype=int)
        for r, total in enumerate(self.totals.astype(int)):
            at = self.group_indices[r]
            if total:
                y[at] = rng.multinomial(total, p[at]/p[at].sum())
        result = copy(self)
        result.counts = y.astype(float)
        result.sufficient = self.features.T@result.counts
        # Every ring total is fixed by construction, and all partition data
        # are immutable shared arrays. This avoids rebuilding identical sky
        # geometry for each conditional draw.
        return result

    def carrier(self):
        """Numbers alone are insufficient without this experiment's partitions."""
        return {"score_statistic": self.sufficient, "ring_totals": self.totals,
                "group_labels": self.group_labels,
                "partition_contract": "features, exposure and group map must be retained",
                "law": "independent ring multinomials conditional on observed totals"}


def fit_joint(experiments, maps=None, offsets=None, start=None, *, max_iter=80):
    """Maximize sum_b ell_b(M_b theta + offset_b), with exact derivatives."""
    experiments = list(experiments)
    if not experiments:
        raise ValueError("at least one experiment is required")
    if maps is None:
        if len(experiments) != 1:
            raise ValueError("multiple experiments require explicit parameter maps")
        maps = [np.eye(experiments[0].features.shape[1])]
    maps = [np.asarray(m, dtype=float) for m in maps]
    if len(maps) != len(experiments) or maps[0].ndim != 2:
        raise ValueError("one matrix map is required per experiment")
    q = maps[0].shape[1]
    if q == 0:
        raise ValueError("at least one fitted parameter is required")
    offsets = ([np.zeros(e.features.shape[1]) for e in experiments] if offsets is None
               else [np.asarray(o, dtype=float) for o in offsets])
    if len(offsets) != len(experiments):
        raise ValueError("one offset is required per experiment")
    for e, m, o in zip(experiments, maps, offsets):
        if (m.shape != (e.features.shape[1], q) or o.shape != (e.features.shape[1],) or
                not np.isfinite(m).all() or not np.isfinite(o).all()):
            raise ValueError("invalid parameter map or offset")
    theta = np.zeros(q) if start is None else np.asarray(start, dtype=float).copy()
    if theta.shape != (q,) or not np.isfinite(theta).all():
        raise ValueError("invalid starting point")

    def evaluate(t):
        vals = [e.evaluate(m@t+o) for e, m, o in zip(experiments, maps, offsets)]
        return (sum(v[0] for v in vals),
                sum((m.T@v[1] for m, v in zip(maps, vals)), np.zeros(q)),
                sum((m.T@v[2]@m for m, v in zip(maps, vals)), np.zeros((q, q))), vals)

    converged = False
    for iteration in range(max_iter):
        ll, score, fisher, vals = evaluate(theta)
        eig = np.linalg.eigvalsh(fisher)
        if eig[-1] <= 0 or eig[0] <= 1e-11*eig[-1]:
            raise ValueError("parameter map is not identifiable in this conditional experiment")
        step = linalg.solve(fisher, score, assume_a='pos')
        decrement = float(score@step)
        if decrement < 1e-14 or np.max(np.abs(step)) < 2e-11:
            converged = True
            break
        fraction = 1.0
        for _ in range(35):
            candidate = theta+fraction*step
            llnew = evaluate(candidate)[0]
            if llnew >= ll-2e-9:
                theta = candidate
                break
            fraction *= .5
        else:
            raise RuntimeError("Newton line search did not converge")
        if np.max(np.abs(theta)) > 50:
            raise RuntimeError("possible separated/unbounded conditional fit")
    if not converged:
        raise RuntimeError("conditional fit did not converge within the declared limit")
    ll, score, fisher, vals = evaluate(theta)
    cov = linalg.inv(fisher)
    pearson = 0.0
    cells = rings = 0
    for e, v in zip(experiments, vals):
        positive = v[3] > 0
        pearson += float(np.sum((e.counts[positive]-v[3][positive])**2/v[3][positive]))
        cells += int(positive.sum())
        rings += int(np.count_nonzero(e.totals))
    dof = cells-rings-q
    return {"estimate": theta, "covariance": .5*(cov+cov.T),
            "precision": fisher, "log_likelihood_relative_zero": float(ll),
            "score_at_maximum": score, "iterations": iteration+1, "rank": q,
            "eigenvalues": np.linalg.eigvalsh(fisher),
            "pearson": pearson, "pearson_dof": dof,
            "overdispersion_diagnostic": pearson/dof if dof > 0 else None,
            "per_experiment_estimates": [m@theta+o for m, o in zip(maps, offsets)],
            "law": "conditional pixel-centre loglinear multinomial",
            "covariance_role": "inverse observed information; asymptotic conditional covariance",
            "physical_LSS_calibrated": False}


def shared_maps(n_bins, n_features, responses=None, *, fixed_dipole=None):
    """Common two-vector with independent per-bin quadrupoles, or fixed dipoles."""
    if n_bins < 1 or n_features < 2:
        raise ValueError("need bins and two dipole features")
    k = np.ones(n_bins) if responses is None else np.asarray(responses, dtype=float)
    if k.shape != (n_bins,) or not np.isfinite(k).all():
        raise ValueError("one finite response per bin")
    nuisance = n_features-2
    fixed = fixed_dipole is not None
    q = n_bins*nuisance + (0 if fixed else 2)
    if q == 0:
        raise ValueError("fixed dipoles without nuisance should be evaluated directly")
    if fixed:
        fixed_dipole = np.asarray(fixed_dipole, dtype=float)
        if fixed_dipole.shape != (2,) or not np.isfinite(fixed_dipole).all():
            raise ValueError("fixed dipole must be a finite two-vector")
    maps, offsets = [], []
    for b in range(n_bins):
        m = np.zeros((n_features, q))
        o = np.zeros(n_features)
        if fixed:
            o[:2] = k[b]*fixed_dipole
        else:
            m[:2, :2] = k[b]*np.eye(2)
        first = (0 if fixed else 2)+b*nuisance
        m[2:, first:first+nuisance] = np.eye(nuisance)
        maps.append(m)
        offsets.append(o)
    return maps, offsets


def nested_lr(full_loglike, restricted_loglike, dof):
    stat = 2*(full_loglike-restricted_loglike)
    if stat < -1e-6 or dof < 1:
        raise ValueError("the supplied nested fit has an invalid likelihood ordering")
    stat = max(0., float(stat))
    return {"statistic": stat, "dof": int(dof),
            "asymptotic_conditional_p": float(stats.chi2.sf(stat, dof)),
            "calibration": "Wilks approximation under the stated conditional count law"}


def flux_path_transform(n_bins, dimension=2):
    """Keep level0 and successive signed contrasts; no flux-to-time relabeling."""
    if n_bins < 1 or dimension < 1:
        raise ValueError("positive dimensions required")
    t = np.eye(n_bins)
    for b in range(1, n_bins):
        t[b, b-1] = -1
    return np.kron(t, np.eye(dimension))


def finite_bin_response(bin_counts, boundary_log_density, alpha):
    """Conditional unresolved peak-proxy response; NOT a measured radio SED.

    boundary_log_density[j] estimates S_j n(S_j) for all lower boundaries;
    the final boundary is infinity with zero density. The population and same
    angular support must match. Entries are counts per unit log peak intensity.
    """
    counts = np.asarray(bin_counts, dtype=float)
    density = np.asarray(boundary_log_density, dtype=float)
    if (counts.ndim != 1 or density.shape != (len(counts)+1,) or
            not np.isfinite(counts).all() or np.any(counts <= 0) or
            not np.isfinite(density).all() or np.any(density < 0) or
            not np.isfinite(alpha)):
        raise ValueError("invalid counts, boundary densities or spectral index")
    return 2+(1+alpha)*(density[:-1]-density[1:])/counts


def gaussian_five_views(y, covariance, reference=None):
    """Five linked views of a retained signed Gaussian approximation.

    The covariance and frame survive every path transformation. These are
    pushforwards of one experiment, never multiplied as independent evidence.
    """
    y = np.asarray(y, dtype=float)
    c = np.asarray(covariance, dtype=float)
    if y.ndim != 1 or len(y) % 2 or c.shape != (len(y), len(y)):
        raise ValueError("need one two-vector per bin and the full covariance")
    if not np.isfinite(y).all() or not np.isfinite(c).all() or not np.allclose(c, c.T):
        raise ValueError("carrier must be finite with symmetric covariance")
    ref = np.zeros_like(y) if reference is None else np.asarray(reference, dtype=float)
    if ref.shape != y.shape or not np.isfinite(ref).all():
        raise ValueError("reference shape or finiteness error")
    chol = linalg.cholesky(c, lower=True)
    residual = y-ref
    w = linalg.solve_triangular(chol, residual, lower=True)
    wald = float(w@w)
    radius = float(np.sqrt(stats.chi2.ppf(.95, len(y))))
    t = flux_path_transform(len(y)//2)
    support_radius = radius*np.sqrt(np.diag(c))
    return {
        "x": {"signed_levels": y, "full_covariance": c, "frame": "ICRS xy",
              "units": "dimensionless log-intensity dipole", "reference": ref},
        "Q": {"gauge": np.sqrt(wald)/radius, "rank": len(y),
              "anchor": "95% statistical coefficient-noise ellipsoid, not physical MES"},
        "Pi": {"wald": wald, "conditional_gaussian_tail": float(stats.chi2.sf(wald, len(y))),
               "law": "local fixed-covariance Gaussian approximation, not posterior probability"},
        "F": {"coordinate_support_lower": y-support_radius,
              "coordinate_support_upper": y+support_radius,
              "antipodal_utilization_positive": (y+support_radius)/support_radius,
              "antipodal_utilization_negative": (-y+support_radius)/support_radius,
              "region": "one simultaneous 95% Gaussian ellipsoid; all directions available from x"},
        "G_F": {"transform": t, "signed_path": t@y, "full_path_covariance": t@c@t.T,
                "path_coordinate": "ordered disjoint peak-intensity bins, not redshift or time",
                "level_retained": True},
        "exact_likelihood": "use ring sufficient statistic and retained partitions",
        "independent_factors": False,
    }
