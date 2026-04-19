"""FB-11.1 skeleton — documented prior contracts for inference.

This module reserves the public prior-construction surface for the
future inference driver without emitting any numerical prior samples
during the FB-META-11 skeleton rotation.

References
----------
- `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
  §2.
- `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`
  §5 (FB-11 table).
- Planck Collaboration 2018 VI, `arXiv:1807.06209` (parameter-set and
  prior-range anchor).
- Kosowsky & Kahniashvili 2011, `arXiv:1007.4539` (observer-motion
  anchor for the dipole-scale prior).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


_LogPdf = Callable[[np.ndarray], np.ndarray]
_SampleFn = Callable[[np.random.Generator, int], np.ndarray]


@dataclass(frozen=True)
class Prior:
    """Future FB-11.1 prior carrier.

    Contract only: the future implementation couples each named prior to
    a vectorized `log_pdf` and a seeded sampling rule. The actual
    distributions are deferred until the non-skeleton FB-11.1 work.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - Planck Collaboration 2018 VI, `arXiv:1807.06209`.
    """

    name: str
    domain: tuple[float, float] | None
    log_pdf: _LogPdf
    sample: _SampleFn


def prior_rapidity(label: str, *, sigma: float) -> Prior:
    """Reserve the truncated rapidity-prior constructor.

    Contract only: this future constructor covers both cosmological
    tilt rapidity and observer-boost rapidity. The sign of the motion
    remains encoded in the direction vector rather than a signed scalar.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`
      §1 and §5.
    """
    raise NotImplementedError(
        "FB-11.1 skeleton only: prior_rapidity is reserved for the "
        "future truncated rapidity prior implementation."
    )


def prior_direction() -> Prior:
    """Reserve the isotropic `S^2` direction prior.

    Contract only: this future constructor covers both `v_hat_cosmo`
    and `v_hat_obs` while keeping those vectors on separate typed
    ownership surfaces.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - `docs/lowell_bianchi/00_conventions.md` §13.
    """
    raise NotImplementedError(
        "FB-11.1 skeleton only: prior_direction is reserved for the "
        "future isotropic directional prior implementation."
    )


def prior_Sigma_mnu() -> Prior:
    """Reserve the `Sigma_mnu` prior constructor.

    Contract only: the future implementation will expose the
    `Sigma_mnu >= 0` prior promised by the FB-11 SDD. Planck 2018 VI
    Table 2 is the parameter-range anchor, while the exact half-Gaussian
    placeholder shape remains a local FB-11 SDD choice to be verified in
    the actual-work session rather than fabricated here.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - Planck Collaboration 2018 VI, `arXiv:1807.06209`, Table 2.
    - `docs/audits/AUDIT_PHASE_FB_META11_2026-04-20.md` §FB-11.1.
    """
    raise NotImplementedError(
        "FB-11.1 skeleton only: prior_Sigma_mnu is reserved for the "
        "future massive-neutrino prior implementation."
    )


def prior_observer_boost() -> Prior:
    """Reserve the measured-dipole observer-boost prior.

    Contract only: this future constructor represents the observer-speed
    prior centred on the CMB-dipole scale. The implementation is
    deferred so the skeleton can pin the source anchor without claiming
    a completed numeric fit.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - Kosowsky & Kahniashvili 2011, `arXiv:1007.4539`, §IV.
    """
    raise NotImplementedError(
        "FB-11.1 skeleton only: prior_observer_boost is reserved for "
        "the future dipole-informed observer prior implementation."
    )


def prior_structure_constants(bianchi_type: str) -> Prior:
    """Reserve the per-type structure-constant prior surface.

    Contract only: admissible ranges remain delegated to
    `bass.background.bianchi_types` and the future implementation must
    map the chosen Bianchi type to the documented scale prior.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`
      §5.
    """
    raise NotImplementedError(
        "FB-11.1 skeleton only: prior_structure_constants is reserved "
        "for the future per-type structure prior implementation."
    )
