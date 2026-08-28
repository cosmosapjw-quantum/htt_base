"""PR-186: the single active vorticity normalization and its ceiling.

Registered convention (frame-consistent with the parent constraint and the
live comparator/MES code):

    W^2 := omega_ab omega^ab / (6 H^2) = omega_a omega^a / (3 H^2),

using the exact tensor/vector identity omega_ab omega^ab = 2 omega_a omega^a
for the spatial antisymmetric vorticity 2-form and its dual vector. With
Theta = 3H, sqrt(omega_ab omega^ab)/Theta <= B implies W^2 <= 3 B^2 / 2.

The v5/v10 display W^2 = omega_a omega^a / H^2 is exactly 3x the registered
value; this module proves the identity two independent ways and scans the
active sources for the 3x-wrong pattern.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

# Active-source allowlist: files that legitimately QUOTE the wrong pattern to
# document/correct it, plus build artifacts that are not active sources.
_ALLOWLIST_SUBSTRINGS = (
    "egs3_parent_identity.py",       # the correction authority (records the 3x slip)
    "parent_identity_seal.json",     # its seal (records v5_document_convention)
    "/build/lib/",                   # stale build copies, not active sources
    "w2_convention.py",              # this module (documents the pattern)
    "run_pr186_w2_convention.py",    # its runner
    "test_pr_186_",                  # its tests
    "pr186_result_card.json",        # its card (quotes the before/after display)
    "docs/research_program/strengthening/",  # strengthening specs (document patterns)
    "htt_post_v10_strengthening_plan_20260721/",  # the external audit package
    "legacy/",                       # frozen historical
    "docs/PR_DELTAS/",               # immutable deltas
    "CHANGELOG.md",                  # immutable historical record
    "docs/V5_",                      # v5-era historical derivation notes
    "docs/ver2_upgrade/",            # historical
)

# Matches W^2 = omega_a omega^a / H^2 (the 3x-wrong form), in LaTeX or text,
# but NOT the correct /(3H^2) or /(6H^2) forms.
_BAD_PATTERNS = (
    re.compile(r"\\omega_a\s*\\omega\^a\}?\s*\{?\s*H\^2\s*\}?"),
    re.compile(r"omega_a\s*omega\^a\s*/\s*H\^2"),
)
_CORRECT_GUARD = re.compile(r"3\s*\*?\s*H\^2|6\s*\*?\s*H\^2|3H\^2|6H\^2")

_TEXT_SUFFIXES = {".py", ".tex", ".md", ".json", ".yaml", ".yml", ".txt"}


def vorticity_tensor_vector_identity(n: int = 100_000, seed: int = 20260721) -> dict:
    """Numerical lineage: omega_ab omega^ab == 2 omega_a omega^a.

    Random spatial antisymmetric 3x3 tensors in an orthonormal frame; the dual
    vector is omega_a = (1/2) eps_abc omega^bc.
    """
    rng = np.random.default_rng(seed)
    eps = np.zeros((3, 3, 3))
    for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        eps[i, j, k] = 1.0
        eps[i, k, j] = -1.0
    max_err = 0.0
    for _ in range(n):
        a = rng.normal(size=(3, 3))
        omega = a - a.T  # antisymmetric
        tensor_norm = float(np.einsum("ab,ab->", omega, omega))
        vec = 0.5 * np.einsum("abc,bc->a", eps, omega)
        vec_norm = float(vec @ vec)
        max_err = max(max_err, abs(tensor_norm - 2.0 * vec_norm))
    return {
        "lineage": "numerical_random_antisymmetric_tensor",
        "n_samples": n,
        "identity": "omega_ab omega^ab == 2 omega_a omega^a",
        "max_abs_error": max_err,
        "ok": max_err < 1e-12,
    }


def ceiling_conversion_symbolic() -> dict:
    """Symbolic lineage: W^2 = omega_ab omega^ab/(6H^2) and the 3/2 ceiling."""
    import sympy as sp

    H, B, wa2 = sp.symbols("H B wa2", positive=True)  # wa2 = omega_a omega^a
    Theta = 3 * H
    # omega_ab omega^ab = 2 * wa2 (proven above), W^2 registered:
    w_ab_sq = 2 * wa2
    W2_registered = sp.simplify(w_ab_sq / (6 * H**2))
    W2_vec_form = sp.simplify(wa2 / (3 * H**2))
    identity_ok = sp.simplify(W2_registered - W2_vec_form) == 0
    # v5/v10 wrong display:
    W2_wrong = wa2 / H**2
    ratio_wrong_over_right = sp.simplify(W2_wrong / W2_registered)
    # ceiling: sqrt(w_ab_sq)/Theta <= B  =>  w_ab_sq <= B^2 Theta^2 = 9 B^2 H^2
    w_ab_sq_max = (B * Theta) ** 2
    W2_max = sp.simplify(w_ab_sq_max / (6 * H**2))
    ceiling_ok = sp.simplify(W2_max - sp.Rational(3, 2) * B**2) == 0
    return {
        "lineage": "symbolic_sympy",
        "W2_registered": str(W2_registered),
        "W2_vector_form": str(W2_vec_form),
        "tensor_vector_forms_equal": bool(identity_ok),
        "wrong_over_right_ratio": str(ratio_wrong_over_right),
        "ceiling_W2_max": str(W2_max),
        "ceiling_is_three_halves_Bsq": bool(ceiling_ok),
        "ok": bool(identity_ok and ceiling_ok and ratio_wrong_over_right == 3),
    }


def _is_allowlisted(rel: str) -> bool:
    return any(sub in rel for sub in _ALLOWLIST_SUBSTRINGS)


def scan_active_sources(repo: Path) -> dict:
    """Scan active repo sources for the 3x-wrong vorticity display pattern."""
    hits = []
    for path in repo.rglob("*"):
        if not path.is_file() or path.suffix not in _TEXT_SUFFIXES:
            continue
        rel = str(path.relative_to(repo))
        if _is_allowlisted(rel) or rel.startswith((".git/", "venv/", "node_modules/")):
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for ln_no, line in enumerate(text.splitlines(), start=1):
            for pat in _BAD_PATTERNS:
                if pat.search(line) and not _CORRECT_GUARD.search(line):
                    hits.append({"file": rel, "line": ln_no, "text": line.strip()[:120]})
    return {
        "active_bad_pattern_hits": hits,
        "n_hits": len(hits),
        "clean": len(hits) == 0,
    }
