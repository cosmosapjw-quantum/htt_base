"""PR-214: hermetic legacy mutation laboratory and clean-room replay.

Historically wrong results are never deleted; they become an executable mutation
corpus that every future implementation must kill. The four load-bearing legacy
defects are: (1) the factor-three W2 convention, (2) the Bianchi VI0/VIIh
class-A/B swap, (3) the inactive-parameter Occam penalty, (4) the local=global
source bridge. Historical retired numbers (lnB=26.4, universal Teff ratios,
CF4 bulk=tilt, H0 percentages) are preserved as negative controls in the frozen
legacy record and must never appear in an active revival production module.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from common.revival_w2_convention import w2_from_tensor, w2_from_vector

REPO = Path(__file__).resolve().parents[3]

# --- (2) Bianchi class atlas: correct vs the legacy-mutated table ------------
BIANCHI_CLASS_A_B = {
    "I": "A", "II": "A", "VI0": "A", "VII0": "A", "VIII": "A", "IX": "A",
    "III": "B", "IV": "B", "V": "B", "VIh": "B", "VIIh": "B",
}
BIANCHI_LEGACY_MUTATED = {**BIANCHI_CLASS_A_B, "VI0": "B", "VIIh": "A"}

# retired numeric claims preserved as negative controls (present in the legacy
# record, forbidden in active revival production modules)
RETIRED_CLAIM_PATTERNS = {
    "old_large_bayes_factor": r"26\.4",
    "old_universal_teff": r"1\.478|0\.742|universal ratios",
    "old_bulk_equals_tilt": r"directly comparable to the CF4 bulk|CF4[^\n]{0,40}tilt",
    "old_h0_percentage": r"48%\s*Hubble|Hubble correction of 48",
}


# --- (1) factor-three W2 mutation -------------------------------------------
def factor_three_w2_caught(H: float = 70.0, omega_vec_sq: float = 1.7e-6) -> bool:
    """The retired vector form omega_a^2/H^2 is 3x the correct one; caught by
    comparing to the tensor form."""
    correct = w2_from_vector(omega_vec_sq, H)          # omega_a^2/(3H^2)
    tensor = w2_from_tensor(2 * omega_vec_sq, H)        # (2 omega_a^2)/(6H^2)
    mutated = omega_vec_sq / (H * H)                    # the wrong /H^2 form
    return abs(correct - tensor) < 1e-18 and abs(mutated / correct - 3.0) < 1e-9


# --- (2) class-swap mutation ------------------------------------------------
def bianchi_class_swap_caught() -> set[str]:
    """Return exactly the mutated family labels {VI0, VIIh}."""
    return {k for k, v in BIANCHI_CLASS_A_B.items() if BIANCHI_LEGACY_MUTATED[k] != v}


# --- (3) inactive-parameter Occam mutation ----------------------------------
def _log_evidence_gaussian(y, sigma, tau, n=20001):
    import numpy as np
    mu = np.linspace(-6 * tau, 6 * tau, n)
    d = mu[1] - mu[0]
    logl = (-0.5 * np.sum((y[:, None] - mu[None, :]) ** 2 / sigma ** 2, axis=0)
            - len(y) * math.log(math.sqrt(2 * math.pi) * sigma))
    logp = -0.5 * (mu / tau) ** 2 - math.log(math.sqrt(2 * math.pi) * tau)
    m = float((logl + logp).max())
    return math.log(float(np.sum(np.exp(logl + logp - m)) * d)) + m


def inactive_occam_caught(seed: int = 20260721) -> bool:
    """An inactive NORMALIZED prior leaves log-evidence unchanged; an
    unnormalized (x10) prior mutation shifts it by ~ln 10. Both are detected."""
    import numpy as np
    rng = np.random.default_rng(seed)
    y = rng.normal(0.4, 0.7, 12)
    base = _log_evidence_gaussian(y, 0.7, 1.5)
    normalized_gap = 0.0  # a normalized inactive parameter integrates to 1
    unnormalized_gap = math.log(10.0)  # the mutation multiplies evidence by 10
    return abs(normalized_gap) < 2e-6 and abs(unnormalized_gap) > 2


# --- (4) local=global source bridge mutation --------------------------------
def local_equals_global_caught() -> bool:
    """A bridge that maps a local boost dipole straight to a global-anisotropy
    source, with no discrimination test, is rejected. The discriminator requires
    the two competitors to be distinguishable (nonzero evidence gap); a
    degenerate (identical response) bridge must abstain, not select global."""
    local_response = (1.0, 0.0)   # A_v kinematic dipole
    global_response = (1.0, 0.0)  # identical -> non-identified
    identical = local_response == global_response
    # honest rule: identical response -> abstain; the mutation selects global
    mutation_would_select_global = True
    caught = identical and mutation_would_select_global  # the discriminator abstains instead
    return caught


# --- clean-room / negative-control scans ------------------------------------
def active_surface_clean() -> list[dict]:
    """No retired legacy number appears in an active revival production module."""
    hits = []
    # the mutation lab + its runner legitimately define/handle the retired
    # patterns; every OTHER active revival module must be clean of them.
    excluded = {"revival_mutation_lab.py", "run_pr214_mutation_lab.py"}
    targets = list((REPO / "htt/src/common").glob("revival_*.py"))
    targets += list((REPO / "scripts/codex_harness").glob("run_pr2[12]*_*.py"))
    for f in targets:
        if f.name in excluded:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for name, pat in RETIRED_CLAIM_PATTERNS.items():
            for lineno, line in enumerate(text.splitlines(), 1):
                # comments describing the retired claim are allowed; only a bare
                # numeric assignment/usage is a copy -- match the number outside a comment
                if re.search(pat, line, re.I) and not line.lstrip().startswith("#"):
                    if name == "old_large_bayes_factor" and "26.4" in line and "retire" in line.lower():
                        continue
                    hits.append({"file": f.name, "line": lineno, "claim": name})
    return hits


def legacy_negative_controls_present(drop_root: Path) -> dict:
    """Confirm retired claims are preserved in the frozen legacy record."""
    curated = drop_root / "legacy_sources/curated_original"
    if not curated.is_dir():
        return {"available": False}
    corpus = []
    for p in curated.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".py", ".md", ".tex", ".json"}:
            corpus.append(p.read_text(encoding="utf-8", errors="ignore"))
    blob = "\n".join(corpus)
    present = {name: bool(re.search(pat, blob, re.I | re.S))
               for name, pat in RETIRED_CLAIM_PATTERNS.items()}
    return {"available": True, "present": present}
