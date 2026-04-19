"""FB-5.5 skeleton — Class B mode-quantisation contract.

This module deliberately ships no physics during the FB-META-5
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the Class B / Type V mode
quantisation rule is implemented for the perturbation sector.
"""
from __future__ import annotations

from bass.background.bianchi_types import StructureConstants


def quantise_class_b_mode(
    structure: StructureConstants,
    *,
    eigenvalue: float,
    branch: str = "principal",
) -> dict[str, object]:
    """Future FB-5.5 Class B and Type V mode-quantisation helper.

    Contract only: this surface is reserved for the future helper that
    turns a Class B structure-constant set and a continuous eigenvalue
    label into the quantised mode metadata required by the perturbative
    state machine, including the Type V Harrison-style hyperbolic branch.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5``.
    - ``bass/hierarchy/nabla_dispatch.py`` (Type V Harrison-style
      hyperbolic-mode notes and Class B twist offset).
    - ``bass/background/bianchi_types.py`` (Class B `a_twist` and
      `h_parameter` SSOT).
    - ``# TODO: citation needed`` Harrison 1967 original hyperbolic-
      harmonics locator (not arXiv-era; unavailable in the arXiv-only
      channel used for this META phase).
    - ``# TODO: citation needed`` Lyth-Stewart 1990 open-FLRW mode
      locator (same arXiv-only limitation).
    """
    raise NotImplementedError(
        "FB-5.5 skeleton only: Class B mode quantisation is not "
        "implemented."
    )
