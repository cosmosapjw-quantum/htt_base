"""PR-129 NTA3 typed estimator/domain registry + universal-floor
prohibition.

The sqrt(2/5) fractional dispersion is an ESTIMATOR- and DOMAIN-SPECIFIC
statement: for the ideal full-sky noiseless Gaussian quadrupole-power
estimator ``C2_hat = (1/5) sum_m |a_2m|^2``, ``Var(C2_hat)/C2^2 = 2/5``
exactly. It is NOT universal, NOT minimax, NOT a Cramer-Rao statement,
and never supports cannot-do-better readings — the multi-multipole
Fisher quantity is a DIFFERENT registry object and the separation
validator rejects any conflation. This is a corrected supersession of
the original universal claim, not a literal rescue.
roadmap_rescue_v1:C1 estimator-specific mechanics only.

Reality-condition dof accounting (why dof = 5 and not 9): for a real
isotropic Gaussian field, ``a_l0`` is real with variance ``C_l`` and for
``m > 0`` the ``a_lm`` are complex with variance ``C_l/2`` per real
component, while ``a_{l,-m} = (-1)^m a_lm^*`` is determined. The
independent real degrees of freedom are ``1 + 2*l = 2l + 1`` (l = 2:
five), and ``sum_m |a_lm|^2 = a_l0^2 + 2 sum_{m>0} |a_lm|^2`` is
``C_l * chi-square_{2l+1}``. Both the moment derivation and the Monte
Carlo below are built from this Gaussian a_lm structure, not from the
chi-square identity they are checking.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping

SCHEMA_VERSION = "pr129.nta3_estimator_registry.v2"

# The preregistered Monte Carlo tolerance. Pinned HERE as well as in the
# PR-129 spec; the runner refuses to run if the two pins disagree, and
# run_seeded_mc refuses any caller-supplied tolerance that differs from
# this constant — widening requires editing this reviewed module.
PREREGISTERED_TOLERANCE_ABS = 0.004


class Nta3RegistryError(ValueError):
    """Raised on any estimator-registry violation (fail-closed)."""


_REQUIRED_FIELDS = ("estimator_id", "statistic", "sky", "noise", "field",
                    "dof")

# Language that must never attach to the estimator-specific dispersion.
# The negative scan skips this registered prohibition block by sentinel;
# occurrences here DEFINE the ban, they do not assert the claim.
# PR129-PROHIBITION-REGISTRY-BEGIN
_FORBIDDEN_CAPTION_TEXT = (
    "universal floor", "minimax floor", "minimax lower bound",
    "minimax-optimal", "cannot do better", "cannot be beaten",
    "cramer-rao floor", "cramer rao floor", "cramer-rao bound of 0.632",
    "cramer rao bound of 0.632", "no estimator can beat",
    "no estimator does better", "best achievable", "optimal floor",
    "lower bound over all", "bound over all estimators",
)
# PR129-PROHIBITION-REGISTRY-END

# Role markers that forbid a dispersion citation (normalized text).
_FORBIDDEN_DISPERSION_ROLES = (
    "fisher", "cramer-rao", "cramer rao", "minimax", "universal",
    "lower bound over all", "best achievable", "optimal floor",
    "cannot", "no estimator", "does better",
)
_DISPERSION_TOKENS = ("2/5", "0.632")
_DISPERSION_ROLE_TOKENS = ("sampling dispersion", "estimator dispersion",
                           "sampling scatter")


def _normalize(text: str) -> str:
    """Case-fold, strip accents on Cramer, collapse all whitespace runs
    (including inside sqrt(2 / 5)) so paraphrase spacing cannot bypass
    token matching."""
    lowered = text.lower().replace("é", "e")
    collapsed = " ".join(lowered.split())
    return collapsed.replace(" / ", "/").replace("( ", "(").replace(" )",
                                                                    ")")


def alm_real_dof(ell: int) -> int:
    """Independent real Gaussian degrees of freedom in {a_lm} under the
    reality condition a_{l,-m} = (-1)^m a_lm^*: one real a_l0 plus two
    per m = 1..l."""
    if ell < 0:
        raise Nta3RegistryError("ell must be >= 0")
    return 1 + 2 * ell


def moment_dispersion_squared(ell: int) -> Fraction:
    """First-principles Gaussian moment derivation of
    Var(C_l_hat)/C_l^2 for C_l_hat = (1/(2l+1)) sum_m |a_lm|^2,
    term by term — NOT via the chi-square identity.

    a_l0 ~ N(0, C): Var(a_l0^2) = 2 C^2. For m > 0, Re/Im ~ N(0, C/2):
    Var(|a_lm|^2) = 2 * 2 (C/2)^2 = C^2, and |a_lm|^2 enters the m-sum
    with coefficient 2 (reality condition), contributing 4 C^2 each.
    """
    if ell < 0:
        raise Nta3RegistryError("ell must be >= 0")
    var_m0 = Fraction(2)                    # Var(a_l0^2)/C^2
    var_m_positive = Fraction(4)            # 2^2 * Var(|a_lm|^2)/C^2
    total_variance = var_m0 + ell * var_m_positive
    n_terms = Fraction(2 * ell + 1)
    return total_variance / (n_terms * n_terms)


@dataclass(frozen=True)
class EstimatorSpec:
    """One typed estimator registration. Every field explicit."""

    estimator_id: str
    statistic: str
    sky: str
    noise: str
    field: str
    dof: int | None
    dispersion_squared_exact: Fraction | None
    ell: int | None = None

    def __post_init__(self) -> None:
        for name in ("estimator_id", "statistic", "sky", "noise", "field"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise Nta3RegistryError(
                    f"estimator field {name!r} must be non-empty (no "
                    "unspecified estimators)"
                )
        if self.dof is not None and (not isinstance(self.dof, int)
                                     or self.dof < 1):
            raise Nta3RegistryError("dof must be a positive integer or None")
        if self.dispersion_squared_exact is not None:
            if self.ell is None:
                raise Nta3RegistryError(
                    "a registered exact dispersion requires the multipole "
                    "ell so the dof can be structurally derived"
                )
            object.__setattr__(self, "dispersion_squared_exact",
                               Fraction(self.dispersion_squared_exact))

    @classmethod
    def from_payload(cls, payload: Mapping) -> "EstimatorSpec":
        missing = [f for f in _REQUIRED_FIELDS if f not in payload]
        if missing:
            raise Nta3RegistryError(
                f"estimator registration missing fields: {missing}"
            )
        raw_disp = payload.get("dispersion_squared_exact")
        return cls(
            estimator_id=payload["estimator_id"],
            statistic=payload["statistic"],
            sky=payload["sky"],
            noise=payload["noise"],
            field=payload["field"],
            dof=payload["dof"],
            dispersion_squared_exact=(
                None if raw_disp is None else Fraction(str(raw_disp))),
            ell=payload.get("ell"),
        )


def chi_square_dispersion_squared(dof: int) -> Fraction:
    """Closed form: Var(chi2_dof/dof) over the mean squared = 2/dof."""
    if dof < 1:
        raise Nta3RegistryError("dof must be >= 1")
    return Fraction(2, dof)


def verify_quadrupole_dispersion(spec: EstimatorSpec) -> Fraction:
    """Three-way exact check: the registered dispersion must equal the
    chi-square closed form AND the independent Gaussian moment
    derivation, and dof must equal the reality-condition count 2*ell+1
    derived from the registered multipole."""
    if spec.dof is None or spec.dispersion_squared_exact is None \
            or spec.ell is None:
        raise Nta3RegistryError(
            "the quadrupole estimator registration needs dof, ell, and an "
            "exact dispersion"
        )
    structural_dof = alm_real_dof(spec.ell)
    if spec.dof != structural_dof:
        raise Nta3RegistryError(
            f"registered dof {spec.dof} != reality-condition count "
            f"2*ell+1 = {structural_dof} for ell = {spec.ell} (naive "
            "complex-component miscounts are rejected here)"
        )
    closed_form = chi_square_dispersion_squared(spec.dof)
    moment_form = moment_dispersion_squared(spec.ell)
    if closed_form != moment_form:
        raise Nta3RegistryError(
            f"chi-square closed form {closed_form} != Gaussian moment "
            f"derivation {moment_form}"
        )
    if spec.dispersion_squared_exact != closed_form:
        raise Nta3RegistryError(
            f"registered dispersion^2 {spec.dispersion_squared_exact} != "
            f"exact value {closed_form}"
        )
    return closed_form


def run_seeded_mc(spec: EstimatorSpec, *, seed: int, replicates: int,
                  tolerance_abs: float) -> dict:
    """Independent seeded Monte Carlo of the REGISTERED ESTIMATOR: draws
    the Gaussian a_lm under the reality condition and forms
    C_l_hat = (1/(2l+1)) (a_l0^2 + 2 sum_{m>0} |a_lm|^2) directly —
    it does not sample the chi-square identity under test. The tolerance
    MUST equal the module pin (post-hoc widening rejected)."""
    import math

    import numpy as np

    if tolerance_abs != PREREGISTERED_TOLERANCE_ABS:
        raise Nta3RegistryError(
            f"MC tolerance {tolerance_abs} differs from the preregistered "
            f"module pin {PREREGISTERED_TOLERANCE_ABS} — post-hoc "
            "widening is rejected"
        )
    if (
        isinstance(replicates, bool)
        or not isinstance(replicates, int)
        or replicates < 2
    ):
        raise Nta3RegistryError("replicates must be an integer >= 2")
    if spec.dof is None or spec.dispersion_squared_exact is None \
            or spec.ell is None:
        raise Nta3RegistryError("MC needs a fully specified estimator")
    ell = spec.ell
    rng = np.random.Generator(np.random.PCG64(seed))
    c_true = 1.0
    a_l0 = rng.normal(0.0, math.sqrt(c_true), size=replicates)
    total = a_l0 ** 2
    for _m in range(1, ell + 1):
        re = rng.normal(0.0, math.sqrt(c_true / 2.0), size=replicates)
        im = rng.normal(0.0, math.sqrt(c_true / 2.0), size=replicates)
        total = total + 2.0 * (re ** 2 + im ** 2)
    draws = total / (2 * ell + 1)
    sample_ratio = float(np.std(draws, ddof=1) / np.mean(draws))
    target = math.sqrt(float(spec.dispersion_squared_exact))
    deviation = abs(sample_ratio - target)
    if not all(math.isfinite(value) for value in (
        sample_ratio, target, deviation
    )):
        raise Nta3RegistryError(
            "MC produced a non-finite dispersion result — no claim"
        )
    if deviation >= tolerance_abs:
        raise Nta3RegistryError(
            f"MC deviates from the exact dispersion by {deviation:.5f} >= "
            f"{tolerance_abs} under the declared conditions — no claim; "
            "re-examine the analytic form or the implementation"
        )
    return {
        "seed": seed,
        "replicates": replicates,
        "simulation": "gaussian_alm_reality_condition_estimator_draws",
        "ell": ell,
        "sample_sd_over_mean": sample_ratio,
        "exact_target": target,
        "abs_deviation": deviation,
        "tolerance_abs": tolerance_abs,
        "within_tolerance": True,
    }


def validate_separation(claim: Mapping) -> None:
    """Reject any claim conflating the estimator-specific sqrt(2/5) with
    a Fisher/Cramer-Rao/minimax/universal quantity (either direction).
    Matching runs on normalized text (case, accents, whitespace)."""
    cited = _normalize(str(claim.get("cites") or ""))
    role = _normalize(str(claim.get("as") or ""))
    cites_dispersion = any(token in cited for token in _DISPERSION_TOKENS)
    if cites_dispersion:
        for marker in _FORBIDDEN_DISPERSION_ROLES:
            if marker in role:
                raise Nta3RegistryError(
                    "sqrt(2/5) (0.632) is the SINGLE-estimator sampling "
                    "dispersion, never a Fisher/Cramer-Rao/minimax/"
                    f"universal quantity — conflation rejected ({marker!r})"
                )
    if "fisher" in cited and any(token in role
                                 for token in _DISPERSION_ROLE_TOKENS):
        raise Nta3RegistryError(
            "the multi-multipole Fisher quantity is not the single-"
            "estimator sampling dispersion — conflation rejected"
        )


def lint_caption(text: str) -> None:
    """The universal-floor prohibition on generated captions, matched on
    normalized text so accents/spacing cannot bypass it."""
    normalized = _normalize(text)
    for phrase in _FORBIDDEN_CAPTION_TEXT:
        if _normalize(phrase) in normalized:
            raise Nta3RegistryError(
                f"caption attaches forbidden universal-floor language: "
                f"{phrase!r}"
            )


def generate_caption(spec: EstimatorSpec) -> str:
    """Captions derive from the typed registration only, and every
    caption citing the dispersion is routed through the separation
    validator with its registered role before release."""
    if spec.dispersion_squared_exact is not None:
        text = (
            f"[{spec.estimator_id}] Fractional sampling dispersion "
            f"sqrt({spec.dispersion_squared_exact}) of the {spec.sky}, "
            f"{spec.noise}-noise, {spec.field} estimator "
            f"{spec.statistic} (ell = {spec.ell}, reality-condition "
            f"dof = {spec.dof}). Estimator- and domain-specific; a "
            "different estimator or domain carries a different dispersion."
        )
        validate_separation({
            "cites": f"sqrt({spec.dispersion_squared_exact})",
            "as": "single-estimator sampling dispersion",
        })
    else:
        text = (
            f"[{spec.estimator_id}] {spec.statistic} — a distinct "
            "information-theoretic object; never interchangeable with a "
            "single-estimator sampling dispersion."
        )
    lint_caption(text)
    return text
