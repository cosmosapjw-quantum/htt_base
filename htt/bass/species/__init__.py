"""bass.species (LB-1) — five-species background evolution (γ, ν, b, c, Λ).

Public entry points
-------------------

Physical constants bundle:
    ``SpeciesConstants``, ``default_constants``

Shared FLRW η-grid table:
    ``FLRWBackgroundTable``, ``build_flrw_background_table``

Abstract base + canonical ordering:
    ``SpeciesBackground``, ``SpeciesLabel``, ``SpeciesSnapshot``,
    ``CANONICAL_ORDER``

Concrete species classes:
    ``PhotonBackground``, ``NeutrinoBackground``,
    ``BaryonBackground``, ``CDMBackground``, ``LambdaBackground``

Registry + factory:
    ``SpeciesBackgroundRegistry``, ``SpeciesBackgroundRegistry.from_planck2018``

See ``docs/lowell_bianchi/01_species_background_spec.md`` for the full
design. See ``docs/lowell_bianchi/00_conventions.md`` for units,
signature, SSOT, and the external-code policy enforced by
``bass.validation.test_external_code_policy`` (LB-0).
"""
from bass.species.background_table import (
    FLRWBackgroundTable,
    build_flrw_background_table,
)
from bass.species.baryon import BaryonBackground
from bass.species.base import (
    CANONICAL_ORDER,
    SpeciesBackground,
    SpeciesLabel,
    SpeciesSnapshot,
)
from bass.species.cdm import CDMBackground
from bass.species.constants import SpeciesConstants, default_constants
from bass.species.lambda_ import LambdaBackground
from bass.species.neutrino import NeutrinoBackground
from bass.species.photon import PhotonBackground
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import (
    TiltedSpeciesBackground,
    V_HAT_E_DEFAULT,
    V_HAT_NORM_TOL,
)


__all__ = [
    # constants + builder
    "SpeciesConstants",
    "default_constants",
    "FLRWBackgroundTable",
    "build_flrw_background_table",
    # base
    "SpeciesBackground",
    "SpeciesLabel",
    "SpeciesSnapshot",
    "CANONICAL_ORDER",
    # concrete species
    "PhotonBackground",
    "NeutrinoBackground",
    "BaryonBackground",
    "CDMBackground",
    "LambdaBackground",
    # registry
    "SpeciesBackgroundRegistry",
    # FB-3.1 tilt wrapper
    "TiltedSpeciesBackground",
    "V_HAT_E_DEFAULT",
    "V_HAT_NORM_TOL",
]
