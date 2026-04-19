"""FB-5.7 skeleton — k × type regression matrix contract.

This module deliberately ships no physics during the FB-META-5
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the perturbation-sector
cross-type regression matrix is wired to the Planck/CAMB fixtures.
"""
from __future__ import annotations


def run_k_type_regression_matrix(
    *,
    type_labels: tuple[str, ...],
    k_values: tuple[float, ...],
    ell_max: int,
) -> dict[str, object]:
    """Future FB-5.7 regression matrix for ``k × type`` perturbation cases.

    Contract only: this surface is reserved for the future regression
    runner that evaluates the perturbation-sector matrix across selected
    Bianchi types and comoving wavenumbers against the established
    Planck/CAMB fixture oracles.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5``.
    - ``bass/integration/test_lowell_bianchi.py`` (existing Planck/CAMB
      regression anchor and fixture policy).
    - Planck Collaboration 2018 VI, arXiv:1807.06209 (cosmological-
      parameter anchor for the Planck-era regression oracle).
    - ``# TODO: citation needed`` exact `Dl_TT` / Table 2 locator from
      the verified Planck paper if the future regression needs a direct
      table-level citation.
    """
    raise NotImplementedError(
        "FB-5.7 skeleton only: k-by-type perturbation regression matrix "
        "is not implemented."
    )
