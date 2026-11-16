"""Cobaya Likelihood provider for the R52 joint linear-Gaussian carrier.

Exact same likelihood as r52_joint_identification.joint(): with flat-measure
linear nuisances the theta-dependence of the marginal and the profile agree, so
logL(theta) = theta.t - 1/2 theta.F.theta + const.

Sampling coordinates: theta = m0 + L v (fixed affine map, constant Jacobian; L is a
Cholesky factor of a reference covariance). v has a flat proper prior U(-vmax, vmax)
far outside the posterior, and the declared Gaussian prior on theta is evaluated
inside the likelihood, so the sampled density is exactly L(theta) pi(theta). The
stock Cobaya MCMC kernel is unchanged.
"""
from __future__ import annotations

import numpy as np
from cobaya.likelihood import Likelihood

from htt.htt.infer.r52_joint_identification import THETA_NAMES


class R52JointLikelihood(Likelihood):
    F: list = []
    t: list = []
    m0: list = []
    L: list = []
    prior_sd: list = []

    def initialize(self):
        self._F = np.asarray(self.F, float)
        self._t = np.asarray(self.t, float)
        self._m0 = np.asarray(self.m0, float)
        self._L = np.asarray(self.L, float)
        self._psd = np.asarray(self.prior_sd, float)
        if self._F.shape != (17, 17) or self._t.shape != (17,) or self._L.shape != (17, 17):
            raise ValueError("R52JointLikelihood needs 17x17 F/L and 17-vector t")

    def get_requirements(self):
        return {}

    def theta(self, v: np.ndarray) -> np.ndarray:
        return self._m0 + self._L @ v

    def logp(self, **params_values):
        v = np.array([params_values[f"v_{n}"] for n in THETA_NAMES])
        th = self.theta(v)
        return float(th @ self._t - 0.5 * th @ self._F @ th - 0.5 * np.sum((th / self._psd) ** 2))


def cobaya_info(F, t, m0, L, prior_sd, output: str, seed: int = 52052, vmax: float = 50.0) -> dict:
    names = [f"v_{n}" for n in THETA_NAMES]
    params = {n: {"prior": {"min": -vmax, "max": vmax}, "ref": {"dist": "norm", "loc": 0.0, "scale": 0.5},
                  "proposal": 0.5, "latex": n} for n in names}
    return {
        "likelihood": {"r52_joint": {"external": R52JointLikelihood, "F": np.asarray(F).tolist(), "t": np.asarray(t).tolist(),
                                     "m0": np.asarray(m0).tolist(), "L": np.asarray(L).tolist(),
                                     "prior_sd": np.asarray(prior_sd).tolist(), "input_params": names}},
        "params": params,
        "sampler": {"mcmc": {"covmat": np.eye(17).tolist(), "covmat_params": names,
                             "Rminus1_stop": 0.005, "Rminus1_cl_stop": 0.05, "max_tries": 10000, "seed": seed,
                             "learn_proposal": True}},
        "output": output,
        "force": True,
    }
