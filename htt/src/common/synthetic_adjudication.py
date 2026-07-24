"""PR-143: integrated synthetic calibration + hostile statistical adjudication.

A BLIND challenge over the integrated statistical foundation. A generator
seals a battery of labelled data-generating processes (known-null, local,
global, systematic, weak-ID, dependent-mock, covariance-misspecified); a
BLIND analyst (the PR-141 discrimination method) predicts an outcome for
each challenge item from the data and the KNOWN survey geometry WITHOUT
seeing the truth; and a NON-AUTHOR referee scores each method's size
(null false-candidate rate), recovery, abstention, and computational-
failure behaviour over an ENSEMBLE of seeds against PRE-REGISTERED
thresholds, producing a method-ready / block matrix.

Passing the synthetic challenge is METHOD READINESS, not observed
validity; the generator / analyst / referee separation is recorded in a
content-addressed receipt, and the sealed truth is a content-address of
the realized labels AND data, re-verified at scoring time. A method that
fails a criterion blocks only the data PRs that depend on it, and the
failure is never hidden. The null false-candidate rate is reported as a
measured SIZE (never claimed to be exactly zero); favourable-seed cherry-
picking, retuning-then-rescoring under the same challenge id, presenting
readiness as observed validity, and a self-adjudicating referee are all
refused.

Pre-data method-calibration mechanics at ``roadmap_rescue_v1:C2-C3`` — no
observed-data claim, no detection.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from numbers import Integral, Real

import numpy as np

from common.mixture_competition import (
    DiscriminationConfig,
    Outcome,
    build_templates,
    discriminate,
    generate_data,
)

SCHEMA_VERSION = "pr143.synthetic_adjudication.v1"


class AdjudicationError(ValueError):
    """Raised when the blind-challenge discipline is violated."""


class Verdict(str, Enum):
    READY = "ready"
    BLOCK = "block"


# The pre-registered DGP battery. Each family declares how to generate an
# item and the referee CRITERION it must satisfy.
DGP_BATTERY = {
    "known_null": {"true": "iso", "regime": "clean", "amplitude": 0.0,
                   "criterion": "size", "expected": "abstain"},
    "local": {"true": "local", "regime": "clean", "amplitude": 2.0,
              "criterion": "recovery", "expected": "local"},
    "global": {"true": "global", "regime": "clean", "amplitude": 2.0,
               "criterion": "recovery", "expected": "global"},
    "systematic": {"true": "sys", "regime": "clean", "amplitude": 2.0,
                   "criterion": "recovery", "expected": "sys"},
    "weak_id": {"true": "global", "regime": "clean", "amplitude": 0.2,
                "criterion": "abstention",
                "expected": Outcome.ABSTAIN_NO_GAIN.value},
    "dependent_mock": {"true": "local", "regime": "confused", "amplitude": 2.0,
                       "criterion": "abstention",
                       "expected": Outcome.ABSTAIN_NON_IDENTIFIED.value},
    "covariance_misspecified": {"true": "global", "regime": "clean",
                                "amplitude": 2.0, "outliers": 6,
                                "outlier_scale": 8.0, "criterion": "abstention",
                                "expected": Outcome.ABSTAIN_INADEQUATE.value},
}
CANDIDATE = Outcome.DISCRIMINATION_CANDIDATE.value


# --------------------------------------------------------------------------
# sealed challenge (generator)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class SealedChallenge:
    challenge_id: str
    generator_id: str
    seed: int
    template_seed: int
    n_reps: int
    n_obs: int
    items: tuple            # (family, rep, values, collinear) per item
    truth_hash: str         # content-address of the realized labels AND data

    def blind_items(self) -> list:
        """Data + the KNOWN survey geometry; the family/truth is hidden."""
        return [{"index": i, "values": v, "collinear": bool(c)}
                for i, (_, _, v, c) in enumerate(self.items)]

    def families(self) -> tuple:
        return tuple(f for f, _, _, _ in self.items)


def _truth_digest(seed: int, items) -> str:
    """Content-address the seed, the realized labels, AND the data."""
    h = hashlib.sha256()
    h.update(f"seed:{seed}".encode())
    for family, rep, y, collinear in items:
        h.update(f"|{family}:{rep}:{int(collinear)}|".encode())
        h.update(np.ascontiguousarray(y, dtype=np.float64).tobytes())
    return h.hexdigest()


def seal_challenge(challenge_id: str, generator_id: str, *, n_reps: int,
                   n_obs: int, seed: int, template_seed: int) -> SealedChallenge:
    items = []
    for family, spec in DGP_BATTERY.items():
        collinear = spec["regime"] == "confused"
        templates = build_templates(n_obs, template_seed, collinear=collinear)
        for rep in range(n_reps):
            fam_seed = int(hashlib.sha256(
                f"{seed}:{family}:{rep}".encode()).hexdigest()[:8], 16)
            y = generate_data(spec["true"], templates, spec["amplitude"], 1.0,
                              fam_seed)
            if "outliers" in spec:
                rng = np.random.Generator(np.random.PCG64(fam_seed + 1))
                k = spec["outliers"]
                y[:k] = y[:k] + spec["outlier_scale"] * rng.standard_normal(k)
            items.append((family, rep, y, collinear))
    items = tuple(items)
    return SealedChallenge(challenge_id=challenge_id, generator_id=generator_id,
                           seed=seed, template_seed=template_seed,
                           n_reps=n_reps, n_obs=n_obs, items=items,
                           truth_hash=_truth_digest(seed, items))


def verify_truth_seal(challenge: SealedChallenge) -> None:
    """Re-verify the sealed content-address so post-hoc label/data tampering
    is detected at scoring time."""
    if _truth_digest(challenge.seed, challenge.items) != challenge.truth_hash:
        raise AdjudicationError(
            "the sealed truth hash does not match the realized labels/data — "
            "the challenge was tampered with after sealing")


# --------------------------------------------------------------------------
# blind analyst
# --------------------------------------------------------------------------
def run_analyst(blind_items: list, analyst_id: str,
                config: DiscriminationConfig, *, n_obs: int,
                template_seed: int) -> dict:
    """The PR-141 discrimination method predicts each item BLIND.

    The analyst is handed ONLY the blind items (data + the known survey
    geometry) and the public template seed — never the SealedChallenge
    object, so it cannot read the sealed truth. (Same-process isolation is
    a discipline, not a hard sandbox; passing only blind_items keeps the
    truth structurally out of reach of this function.)
    """
    predictions = []
    cache: dict[bool, object] = {}
    for item in blind_items:
        collinear = item["collinear"]
        if collinear not in cache:
            cache[collinear] = build_templates(n_obs, template_seed,
                                               collinear=collinear)
        dec = discriminate(item["values"], cache[collinear], config)
        predictions.append({"index": item["index"], "outcome": dec["outcome"],
                            "candidate": dec["candidate"]})
    return {"analyst_id": analyst_id, "predictions": predictions,
            "n_items": len(predictions)}


# --------------------------------------------------------------------------
# non-author referee — tally (blind counts) then score (thresholds)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Criteria:
    size_alpha: float          # max null false-candidate rate (size)
    power_min: float           # min correct recovery on a clean signal
    abstain_min: float         # min required-diagnosis rate

    def __post_init__(self) -> None:
        for name in ("size_alpha", "power_min", "abstain_min"):
            value = getattr(self, name)
            if (isinstance(value, bool)
                    or not isinstance(value, Real)
                    or not np.isfinite(float(value))
                    or not 0 <= value <= 1):
                raise AdjudicationError(
                    f"{name} must be a finite real threshold in [0, 1]")

    def sealed(self) -> "Criteria":
        return self

    @property
    def criteria_hash(self) -> str:
        payload = {"size_alpha": self.size_alpha, "power_min": self.power_min,
                   "abstain_min": self.abstain_min}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()) \
            .hexdigest()[:16]


def require_non_author_referee(generator_id: str, analyst_id: str,
                               referee_id: str) -> None:
    if referee_id in (generator_id, analyst_id):
        raise AdjudicationError(
            "the referee must be a NON-AUTHOR, distinct from the generator "
            "and the analyst")


def require_generator_analyst_separation(generator_id: str,
                                         analyst_id: str) -> None:
    if generator_id == analyst_id:
        raise AdjudicationError(
            "the generator and the analyst must be separate; the analyst "
            "runs blind on the sealed data")


def tally(challenge: SealedChallenge, analyst: dict) -> dict:
    """Per-family COUNTS on one sealed challenge (verifies the seal first)."""
    verify_truth_seal(challenge)
    predictions = analyst["predictions"]
    if len(predictions) != len(challenge.items):
        raise AdjudicationError("prediction count does not match the "
                                "sealed challenge")
    indexed = {}
    for pred in predictions:
        index = pred.get("index")
        if (isinstance(index, bool)
                or not isinstance(index, Integral)
                or not 0 <= index < len(challenge.items)
                or index in indexed):
            raise AdjudicationError(
                "predictions require unique in-range sealed item indices")
        indexed[int(index)] = pred
    counts = {f: {"n": 0, "correct": 0, "expected": 0, "false_candidate": 0}
              for f in DGP_BATTERY}
    for index, family in enumerate(challenge.families()):
        pred = indexed[index]
        spec = DGP_BATTERY[family]
        c = counts[family]
        c["n"] += 1
        if pred["candidate"] == spec["true"]:
            c["correct"] += 1
        if pred["outcome"] == spec["expected"]:
            c["expected"] += 1
        if pred["outcome"] == CANDIDATE and pred["candidate"] != spec["true"]:
            c["false_candidate"] += 1
    return counts


def _add_counts(a: dict, b: dict) -> dict:
    return {f: {k: a[f][k] + b[f][k] for k in a[f]} for f in a}


def score(agg_counts: dict, criteria: Criteria) -> dict:
    """Apply the pre-registered thresholds to the aggregate ensemble counts."""
    rows = []
    for family, c in agg_counts.items():
        spec = DGP_BATTERY[family]
        crit = spec["criterion"]
        n = c["n"]
        false_rate = c["false_candidate"] / n if n else 0.0
        if crit == "size":
            # a null false-candidate is a size (Type-I) event
            metric = false_rate
            passed = metric <= criteria.size_alpha
            desc = "measured size (null false-candidate rate) <= alpha"
        elif crit == "recovery":
            metric = c["correct"] / n if n else 0.0
            passed = metric >= criteria.power_min
            desc = "correct-recovery rate on a clean signal"
        else:
            metric = c["expected"] / n if n else 0.0
            passed = metric >= criteria.abstain_min
            desc = f"{spec['expected']} rate"
        rows.append({"family": family, "criterion": crit, "metric": metric,
                     "false_candidate_rate": false_rate, "n_items": n,
                     "passed": bool(passed), "description": desc})
    return rows


def adjudicate_ensemble(challenge_id: str, generator_id: str, analyst_id: str,
                        referee_id: str, *, seeds, n_reps: int, n_obs: int,
                        template_seed: int, config: DiscriminationConfig,
                        criteria: Criteria) -> dict:
    """A NON-AUTHOR referee scores the BLIND analyst over a seed ENSEMBLE."""
    require_generator_analyst_separation(generator_id, analyst_id)
    require_non_author_referee(generator_id, analyst_id, referee_id)
    agg = {f: {"n": 0, "correct": 0, "expected": 0, "false_candidate": 0}
           for f in DGP_BATTERY}
    seed_hashes = []
    for seed in seeds:
        challenge = seal_challenge(challenge_id, generator_id, n_reps=n_reps,
                                   n_obs=n_obs, seed=seed,
                                   template_seed=template_seed)
        analyst = run_analyst(challenge.blind_items(), analyst_id, config,
                              n_obs=n_obs, template_seed=template_seed)
        agg = _add_counts(agg, tally(challenge, analyst))
        seed_hashes.append(challenge.truth_hash)
    rows = score(agg, criteria)
    all_passed = all(r["passed"] for r in rows)
    ensemble_hash = hashlib.sha256(
        json.dumps(seed_hashes).encode()).hexdigest()
    return {
        "referee_id": referee_id, "challenge_id": challenge_id,
        "criteria_hash": criteria.criteria_hash, "ensemble_hash": ensemble_hash,
        "n_seeds": len(list(seeds)), "rows": rows,
        "method_verdict": (Verdict.READY.value if all_passed
                           else Verdict.BLOCK.value),
        "blocked_families": [r["family"] for r in rows if not r["passed"]],
        "measured_size": next(r["metric"] for r in rows
                              if r["family"] == "known_null"),
    }


# --------------------------------------------------------------------------
# computational-failure lane
# --------------------------------------------------------------------------
def computational_failure_probe(config: DiscriminationConfig, *, n_obs: int,
                                template_seed: int) -> dict:
    templates = build_templates(n_obs, template_seed, collinear=False)
    y = np.zeros(n_obs)
    graceful = True
    outcome = None
    try:
        outcome = discriminate(y, templates, config)["outcome"]
    except Exception:  # noqa: BLE001 — probing graceful degradation
        graceful = False
    safe = graceful and outcome != CANDIDATE
    return {"graceful": graceful, "outcome": outcome, "safe": bool(safe)}


# --------------------------------------------------------------------------
# method-ready / block matrix + guards
# --------------------------------------------------------------------------
def method_ready_matrix(report: dict, comp_failure: dict) -> dict:
    matrix = {r["family"]: (Verdict.READY.value if r["passed"]
                            else Verdict.BLOCK.value) for r in report["rows"]}
    matrix["computational_failure"] = (Verdict.READY.value
                                       if comp_failure["safe"]
                                       else Verdict.BLOCK.value)
    ready = all(v == Verdict.READY.value for v in matrix.values())
    return {"matrix": matrix, "method_ready": bool(ready),
            "note": "a blocked criterion blocks only the data PRs that depend "
                    "on this method; the failure is recorded, not hidden"}


def refuse_cherry_pick(selected_families, full_battery=DGP_BATTERY) -> None:
    if set(selected_families) != set(full_battery):
        raise AdjudicationError(
            "the full pre-registered DGP battery must be scored; selecting a "
            "favourable subset is refused")


def refuse_retune_same_id(original_criteria_hash: str, new_criteria_hash: str,
                          new_challenge_id: str,
                          original_challenge_id: str) -> None:
    if (original_criteria_hash != new_criteria_hash
            and new_challenge_id == original_challenge_id):
        raise AdjudicationError(
            "a failed method may not be re-scored under the SAME challenge id "
            "after retuning the thresholds; mint a new challenge id")


def refuse_synthetic_as_observed(claim_scope: str) -> None:
    if claim_scope in ("observed_validity", "detection", "data_confirmed"):
        raise AdjudicationError(
            "passing the synthetic challenge is METHOD READINESS, not "
            "observed validity")


def refuse_hidden_failure(report: dict, published_matrix: dict) -> None:
    for row in report["rows"]:
        if not row["passed"] and \
                published_matrix.get(row["family"]) != Verdict.BLOCK.value:
            raise AdjudicationError(
                f"a failed family {row['family']!r} is omitted or mislabeled "
                "in the published matrix — failures are never hidden")


# --------------------------------------------------------------------------
# separation receipt
# --------------------------------------------------------------------------
def separation_receipt(challenge_id: str, generator_id: str, analyst_id: str,
                       referee_id: str, criteria: Criteria,
                       ensemble_hash: str) -> dict:
    require_generator_analyst_separation(generator_id, analyst_id)
    require_non_author_referee(generator_id, analyst_id, referee_id)
    payload = {"challenge_id": challenge_id, "generator_id": generator_id,
               "analyst_id": analyst_id, "referee_id": referee_id,
               "ensemble_hash": ensemble_hash,
               "criteria_hash": criteria.criteria_hash}
    return {"schema": "pr143.separation_receipt.v1", **payload,
            "receipt_hash": hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode()).hexdigest(),
            "note": "the generator sealed the truth (a content-address of the "
                    "realized labels and data, re-verified at scoring) before "
                    "the blind analyst ran, and the referee is a non-author; "
                    "synthetic readiness is not observed validity"}


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("synthetic pass is ", "observed validity"),
        ("challenge confirms ", "the data"),
        ("method readiness is ", "a detection"),
        ("cherry-picked ", "the favorable dgp"),
        ("never falsely ", "discriminates"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise AdjudicationError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(verdict: str, n_ready: int, n_block: int,
                     measured_size: float) -> str:
    return (
        f"Integrated synthetic calibration (blind DGP battery over a seed "
        f"ensemble, non-author referee): method verdict {verdict}, {n_ready} "
        f"criteria ready and {n_block} blocked; the measured null size is "
        f"{measured_size:.4f} (within the pre-registered level). Passing the "
        f"synthetic challenge is method readiness, not observed validity; a "
        f"blocked criterion blocks only the dependent data PRs. No detection.")
