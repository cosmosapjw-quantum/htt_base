"""Fixed-design Gaussian inference with diagonal + low-rank covariance.

Research implementation: O(n * small_width) storage, no observation-square
matrix or inverse. Distances, selection, templates and covariance must be fixed
independently of the fitted data for the stated exact Gaussian sampling law.
Numerical rank remains a scale-dependent numerical decision, not a certificate.
"""
from dataclasses import dataclass
import numpy as np
from statistics import NormalDist
import hashlib
import json
from common.bulkflow_covariance import SamplingCovariance, as_sampling_covariance


def _finite(value, name, ndim=None):
    x = np.asarray(value, dtype=float)
    if (ndim is not None and x.ndim != ndim) or not np.all(np.isfinite(x)):
        raise ValueError(f"{name} must be finite with ndim={ndim}")
    return x


def _computed_finite(value, name):
    if not np.all(np.isfinite(value)):
        raise ArithmeticError(f"{name} exceeds finite numerical domain; rescale inputs")
    return value


def _rank_svd(a, rtol, reference=0.):
    _computed_finite(a, "whitened design")
    u, s, vt = np.linalg.svd(a, full_matrices=False)
    scale = float(s[0]) if s.size else 0.
    # The absolute floor prevents roundoff in a removed nuisance mode from
    # becoming a new signal when the whole residual design is nearly zero.
    tol = max(rtol * scale, max(a.shape, default=1) * np.finfo(float).eps * reference)
    keep = s > tol
    return u[:, keep], s[keep], vt[keep], tol, s


@dataclass(frozen=True)
class JointCompression:
    """Exact sufficient quadratic statistics for a fixed mean-template family.

    Values are floating-point approximations to exact algebraic identities.
    Nuisance parameters have been profiled over an unrestricted linear space.
    logdet and n are useful for fixed-C Gaussian profile log-likelihoods, not
    for comparing nuisance models by marginal evidence.
    """
    gram: np.ndarray
    score: np.ndarray
    y_precision_y: float
    logdet: float
    n: int
    nuisance_rank: int
    identity: str
    branch: str

    def __post_init__(self):
        for name in ("gram", "score"):
            array = np.array(getattr(self, name), copy=True)
            array.flags.writeable = False
            object.__setattr__(self, name, array)

    def _amplitude(self, value):
        value = _finite(value, "amplitude", 1)
        if value.shape != self.score.shape:
            raise ValueError("amplitude has wrong length")
        return value

    def quadratic(self, amplitude):
        """Profile residual chi-square; cancellation can affect tiny results."""
        a = self._amplitude(amplitude)
        with np.errstate(over="ignore", invalid="ignore"):
            q = float(self.y_precision_y - 2*a@self.score + a@self.gram@a)
        _computed_finite(q, "compressed quadratic")
        floor = 64*np.finfo(float).eps * max(1., abs(self.y_precision_y),
                                             abs(2*a@self.score), abs(a@self.gram@a))
        if q < -floor:
            raise ArithmeticError("negative quadratic beyond roundoff; check scaling")
        return max(q, 0.)

    def deviance_difference(self, amplitude, reference):
        """-2 log[L_profile(a)/L_profile(reference)]; fixed C,N,F only."""
        a, b = self._amplitude(amplitude), self._amplitude(reference)
        with np.errstate(over="ignore", invalid="ignore"):
            value = float((a-b) @ (self.gram @ (a+b) - 2*self.score))
        return _computed_finite(value, "deviance difference")

    def profile_log_likelihood(self, amplitude):
        if self.branch != "free_nuisance_profile":
            raise ValueError("use marginal_log_likelihood for proper Gaussian nuisance")
        return _computed_finite(-.5*(self.quadratic(amplitude)+self.logdet+self.n*np.log(2*np.pi)), "log likelihood")

    def marginal_log_likelihood(self, amplitude):
        """Normalized density after integrating the declared proper nuisance prior."""
        if self.branch != "proper_gaussian_marginal":
            raise ValueError("free nuisance profile is not marginal evidence")
        return _computed_finite(-.5*(self.quadratic(amplitude)+self.logdet+self.n*np.log(2*np.pi)), "log likelihood")

    def require_identity(self, identity):
        if identity != self.identity:
            raise ValueError("compression identity mismatch; rebuild fixed statistics")


class StructuredLinearModel:
    """y=F a+N eta+b+epsilon with known structured C and fixed F,N.

    Free deterministic nuisance eta is eliminated in whitened space. A proper
    Gaussian nuisance prior instead contributes a covariance factor; do not
    remove that same nuisance twice. Coefficient units affect numerical rank.
    """
    def __init__(self, F, covariance, nuisance=None, rank_rtol=None, *,
                 observation_order_id, selection_id, observation_unit, coefficient_units, nuisance_units=()):
        F = _finite(F, "F", 2)
        F = F.copy()
        covariance = as_sampling_covariance(covariance)
        covariance = (SamplingCovariance(dense=covariance.dense.copy()) if covariance.dense is not None
                      else SamplingCovariance(diagonal=covariance.diagonal.copy(), low_rank=covariance.low_rank.copy()))
        n, self.p = F.shape
        if n != covariance.size or not self.p:
            raise ValueError("F needs covariance.size rows and at least one column")
        self.covariance_operator = covariance
        self.n = n
        self.rank_rtol = max(F.shape)*np.finfo(float).eps if rank_rtol is None else rank_rtol
        if not np.isfinite(self.rank_rtol) or not 0 <= self.rank_rtol < 1:
            raise ValueError("rank_rtol must lie in [0,1)")
        N = np.empty((n, 0)) if nuisance is None else _finite(nuisance, "nuisance", 2)
        if N.shape[0] != n:
            raise ValueError("nuisance rows must match F")
        if any(not isinstance(x, str) or not x.strip() for x in
               (observation_order_id, selection_id, observation_unit)):
            raise ValueError("explicit observation order, selection identity and unit are required")
        coefficient_units = tuple(coefficient_units)
        if len(coefficient_units) != self.p or any(not isinstance(x, str) or not x.strip() for x in coefficient_units):
            raise ValueError("one explicit unit per signal coefficient is required")
        nuisance_units = tuple(nuisance_units)
        if len(nuisance_units) != N.shape[1] or any(not isinstance(x, str) or not x.strip() for x in nuisance_units):
            raise ValueError("one explicit unit per free nuisance coefficient is required")
        self.branch = "free_nuisance_profile"
        self.metadata = dict(observation_order_id=observation_order_id, selection_id=selection_id,
                             observation_unit=observation_unit, coefficient_units=coefficient_units, nuisance_units=nuisance_units,
                             rank_rtol=float(self.rank_rtol), covariance_fixed=True, design_fixed=True,
                             nuisance_fixed=True, selection_fixed=True)
        digest = hashlib.sha256(json.dumps(self.metadata, sort_keys=True).encode())
        for array in (F, N, covariance.dense if covariance.dense is not None else covariance.diagonal,
                      np.empty((0, 0)) if covariance.dense is not None else covariance.low_rank):
            digest.update(str(array.shape).encode()); digest.update(np.ascontiguousarray(array).tobytes())
        self.identity = digest.hexdigest()
        for array in (covariance.dense, covariance.diagonal, covariance.low_rank):
            if array is not None:
                array.flags.writeable = False
        wn = covariance.whiten(N)
        self._un, _, _, self.nuisance_tolerance, self.nuisance_singular_values = _rank_svd(
            wn, self.rank_rtol)
        self.nuisance_rank = self._un.shape[1]
        wf = covariance.whiten(F)
        self._a = self._project(wf)
        reference = float(np.linalg.norm(wf, 2))
        self._us, self.singular_values, self._vt, self.rank_tolerance, self.all_singular_values = _rank_svd(
            self._a, self.rank_rtol, reference)
        self.rank = self.singular_values.size
        self.residual_dof = n-self.nuisance_rank-self.rank
        self.row_projector = self._vt.T @ self._vt
        scaled_v = self._vt.T/self.singular_values if self.rank else np.empty((self.p, 0))
        self.covariance = scaled_v @ scaled_v.T
        with np.errstate(over="ignore", invalid="ignore"):
            self.gram = self._a.T @ self._a
        _computed_finite(self.gram, "design Gram")
        _computed_finite(self.covariance, "coefficient covariance")
        for array in (self._un, self._a, self._us, self._vt, self.singular_values,
                      self.all_singular_values, self.nuisance_singular_values,
                      self.row_projector, self.covariance, self.gram):
            array.flags.writeable = False
        self.condition_retained = (float(self.singular_values[0]/self.singular_values[-1])
                                   if self.rank else None)

    def _project(self, value):
        return value-self._un @ (self._un.T @ value)

    def _data(self, y):
        y = _finite(y, "y", 1)
        if y.shape != (self.n,):
            raise ValueError("y length must equal n")
        return _computed_finite(self._project(self.covariance_operator.whiten(y-getattr(self, "_prior_offset", 0.))), "whitened data")

    def fit(self, y):
        """Minimum Euclidean-norm representative on the retained row space."""
        z = self._data(y)
        estimate = self._vt.T @ ((self._us.T @ z)/self.singular_values)
        residual = z-self._us @ (self._us.T @ z)
        _computed_finite(estimate, "coefficient estimate")
        with np.errstate(over="ignore", invalid="ignore"):
            residual_chi_square = float(residual @ residual)
        _computed_finite(residual_chi_square, "fit residual norm")
        return {"estimate": estimate, "covariance": self.covariance.copy(),
                "rank": int(self.rank), "nuisance_rank": self.nuisance_rank,
                "residual_dof": self.residual_dof,
                "residual_chi_square": residual_chi_square}

    def compress(self, y):
        z = self._data(y)
        with np.errstate(over="ignore", invalid="ignore"):
            score = self._a.T @ z
            q = float(z@z)
        _computed_finite(score, "compressed score")
        _computed_finite(q, "compressed data norm")
        return JointCompression(self.gram.copy(), score, q,
                                self.covariance_operator.logdet(), self.n, self.nuisance_rank, self.identity, self.branch)

    def influence(self, contrast, atol=0., rtol=1e-9):
        """n-vector ell such that g.T a_hat = ell.T y; rejects lost contrasts."""
        if not np.isfinite(atol) or not np.isfinite(rtol) or atol < 0 or rtol < 0:
            raise ValueError("estimability tolerances must be finite and nonnegative")
        g = _finite(contrast, "contrast", 1)
        if g.shape != (self.p,):
            raise ValueError("contrast length must equal p")
        if np.linalg.norm(g-self.row_projector@g) > atol+rtol*np.linalg.norm(g):
            raise ValueError("contrast is not identifiable at the retained numerical rank")
        weights = self._us @ ((self._vt @ g)/self.singular_values)
        return _computed_finite(self.covariance_operator.whiten_transpose(self._project(weights)), "contrast influence")

    def scalar_interval(self, y, contrast, alpha=.05, box=None, envelope=None, radius=1.):
        """Conservative fixed-contrast Gaussian interval plus deterministic bias.

        Box and ellipsoidal envelope add as a Minkowski sum if both provided.
        No data-selected contrast or estimated-C coverage is claimed.
        """
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must lie in (0,1)")
        ell = self.influence(contrast)
        y = _finite(y, "y", 1)
        if y.shape != ell.shape:
            raise ValueError("y length must equal n")
        variance = float(ell @ self.covariance_operator.matmat(ell))
        bias = 0.
        if box is not None:
            bounds = _finite(box, "box", 1)
            if bounds.shape != ell.shape or np.any(bounds < 0):
                raise ValueError("box must be nonnegative with length n")
            bias += float(np.abs(ell) @ bounds)
        if envelope is not None:
            E = _finite(envelope, "envelope", 2)
            if E.shape[0] != self.n or not np.isfinite(radius) or radius < 0:
                raise ValueError("envelope must have n rows and nonnegative finite radius")
            bias += float(radius*np.linalg.norm(E.T@ell))
        _computed_finite(variance, "contrast variance")
        _computed_finite(bias, "bias bound")
        se = np.sqrt(max(variance, 0.))
        center = float(ell@(y-getattr(self, "_prior_offset", 0.)))
        half = float(NormalDist().inv_cdf(1-alpha/2)*se+bias)
        _computed_finite([center, half, center-half, center+half], "contrast interval")
        return {"center": center, "standard_error": float(se), "variance": variance,
                "bias_bound": bias, "lower": center-half, "upper": center+half,
                "alpha": alpha}

    @property
    def storage_bytes(self):
        arrays = (self._un, self._a, self._us, self._vt, self.singular_values,
                  self.all_singular_values, self.nuisance_singular_values,
                  self.row_projector, self.covariance, self.gram)
        return (self.covariance_operator.storage_bytes + sum(a.nbytes for a in arrays)
                + getattr(self, "_prior_offset", np.empty(0)).nbytes)

    @classmethod
    def gaussian_marginal(cls, F, covariance, nuisance, prior_covariance, *, prior_mean=None, **contract):
        """Integrate eta~N(prior_mean,S); no free projection of the same modes.

        S must be SPD and fixed. This is a conditional normalized likelihood
        in signal amplitudes, not evidence integrated over their prior.
        """
        N = _finite(nuisance, "nuisance", 2)
        S = _finite(prior_covariance, "prior_covariance", 2)
        if S.shape != (N.shape[1], N.shape[1]) or not np.allclose(S, S.T, rtol=0, atol=0):
            raise ValueError("prior covariance must be square and symmetric for nuisance columns")
        try:
            root = np.linalg.cholesky(S)
        except np.linalg.LinAlgError as exc:
            raise ValueError("proper Gaussian prior covariance must be positive definite") from exc
        mean = np.zeros(N.shape[1]) if prior_mean is None else _finite(prior_mean, "prior_mean", 1)
        if mean.shape != (N.shape[1],):
            raise ValueError("prior mean length must equal nuisance columns")
        C = as_sampling_covariance(covariance)
        factor = N @ root
        if N.shape[0] != C.size:
            raise ValueError("nuisance rows must match covariance")
        effective = (SamplingCovariance(dense=C.dense + factor @ factor.T) if C.dense is not None
                     else SamplingCovariance(diagonal=C.diagonal, low_rank=np.column_stack((C.low_rank, factor))))
        nuisance_units = tuple(contract.pop("nuisance_units", ()))
        if len(nuisance_units) != N.shape[1] or any(not isinstance(x, str) or not x.strip() for x in nuisance_units):
            raise ValueError("one explicit unit per Gaussian nuisance coefficient is required")
        model = cls(F, effective, **contract)
        model.metadata.update(gaussian_nuisance_units=nuisance_units,
                              prior_covariance_units="pairwise products of nuisance units")
        model.branch = "proper_gaussian_marginal"
        model._prior_offset = N @ mean
        model._prior_offset.flags.writeable = False
        model.identity = hashlib.sha256((model.identity + model.branch + json.dumps(nuisance_units)).encode() + model._prior_offset.tobytes()).hexdigest()
        return model
