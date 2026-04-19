"""FB-7.5 skeleton — Planck-2018 FLRW-limit validation contract.

This module deliberately ships no FLRW-limit validation physics during
the FB-META-7 rotation. The public surface below is a contract
placeholder only and must raise ``NotImplementedError`` until the full
FB-7 stack can be checked against the Planck-2018 CAMB fixture in the
FLRW limit.
"""
from __future__ import annotations

from pathlib import Path


def validate_planck2018_flrw_limit_match(
    *,
    camb_fixture_path: Path,
    planck_likelihood_arxiv: str = "1907.12875",
    planck_parameters_arxiv: str = "1807.06209",
) -> dict[str, object]:
    """Future FB-7.5 FLRW-limit validator for the full Planck-era stack.

    Contract only: this surface is reserved for the future validator
    that checks the FB-7 LOS + spectrum + HTT + cosmological-frame
    likelihood stack against the shipped CAMB Planck-2018 fixture in the
    FLRW limit.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7``.
    - ``data/camb_ref_planck2018.npz`` (shipped CAMB FLRW-limit oracle).
    - ``docs/dossier/A13_00_FLRW.md`` (local Planck-era FLRW baseline
      summary).
    - Planck Collaboration 2018 V, arXiv:1907.12875 (likelihood paper).
    - Planck Collaboration 2018 VI, arXiv:1807.06209 (base-ΛCDM
      parameter baseline carried by the fixture).
    """
    raise NotImplementedError(
        "FB-7.5 skeleton only: Planck-2018 FLRW-limit validation is not "
        "implemented."
    )
