"""PR-221: cross-survey latent cosmic-dipole source discrimination (extends PR-141).

Explicit competitors -- kinematic, LSS/global, survey-systematic, shared-global
and superposition -- with mandatory model-adequacy abstention. A confusable or
misspecified source must trigger abstention, never a global-source selection.
Model choice uses a BIC-penalised chi^2 with a look-elsewhere gap and a
chi^2-adequacy gate.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import chi2


def _choose_model(
    scores: list[tuple[float, str]],
    fits: dict[str, tuple[float, int]],
    minimum_gap: float = 1.0,
) -> str:
    """Apply adequacy and the look-elsewhere gap symmetrically."""
    ranked = sorted(scores)
    best = ranked[0][1]
    gap = ranked[1][0] - ranked[0][0]
    ch, dof = fits[best]
    adequate = (1 - chi2.cdf(ch, dof)) > 0.01
    if not adequate or gap <= minimum_gap:
        return "abstain"
    return best


def run(seed: int = 20260721, nrep: int = 4000, nobs: int = 24) -> dict:
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, nobs)
    kin = 0.5 + 1.5 * (0.2 + np.sin(2 * np.pi * x) ** 2)
    glob = np.ones(nobs)
    sysm = np.sin(4 * np.pi * x) + 0.3 * np.cos(2 * np.pi * x)
    sysm /= np.std(sysm)
    amb = np.sign(np.sin(7 * np.pi * x)) + 0.4 * np.cos(11 * np.pi * x)
    amb /= np.std(amb)
    C = np.diag(np.full(nobs, 0.25 ** 2)) + 0.002 * np.ones((nobs, nobs))
    Ci = np.linalg.inv(C)
    base = np.column_stack([kin, glob, sysm])
    models = {"kin": kin[:, None], "kin+global": np.column_stack([kin, glob]),
              "kin+sys": np.column_stack([kin, sysm]), "full": base}
    means = {"kin": base @ np.array([1, 0, 0]),
             "global": base @ np.array([1, 0.9, 0]),
             "systematic": base @ np.array([1, 0, 0.9]),
             "superposition": base @ np.array([1, 0.7, 0.7]),
             "confusable_weak": kin + 0.5 * amb}
    truth = {"kin": "kin", "global": "kin+global", "systematic": "kin+sys",
             "superposition": "full", "confusable_weak": "abstain"}
    per = max(1, nrep // len(means))
    results = {}
    tot = 0
    for name, mu in means.items():
        correct = abst = 0
        for _ in range(per):
            y = mu + rng.multivariate_normal(np.zeros(nobs), C)
            scores = []
            fits = {}
            for mname, X in models.items():
                F = X.T @ Ci @ X
                beta = np.linalg.solve(F, X.T @ Ci @ y)
                r = y - X @ beta
                ch = float(r @ Ci @ r)
                fits[mname] = (ch, nobs - X.shape[1])
                scores.append((ch + X.shape[1] * np.log(nobs), mname))
            chosen = _choose_model(scores, fits)
            correct += chosen == truth[name]
            abst += chosen == "abstain"
        results[name] = {"correct_rate": correct / per, "abstain_rate": abst / per}
        tot += correct
    rate = tot / (per * len(means))
    ok = (rate > 0.84 and results["superposition"]["correct_rate"] > 0.94
          and results["confusable_weak"]["abstain_rate"] > 0.95)
    return {"overall_correct_rate": rate, "scenario_results": results, "gate_pass": ok}
