"""Per-family transport kernels.

Import layout:

* ``bass.los.families.base`` — ``LegacyDelegationKernel`` /
  ``NotImplementedKernel`` base classes plus ``FamilyMetadata``.
* ``bass.los.families.type_<family>`` — one module per family. Each
  module defines a concrete kernel class and exposes a singleton
  ``KERNEL`` instance.
* ``KNOWN_FAMILIES`` — mapping ``family -> KERNEL``. All 11 Bianchi
  families (excluding FLRW, which the facade early-returns) are
  represented by concrete kernels that emit family residual packs.
  Publication/readiness promotion is not inferred from registry presence;
  it is decided by the validation layer from residual-pack, IC, and output
  evidence.

Opt-in registration: ``register_all_defaults()`` wires every kernel
into ``bass.transport.exact_transport._TRANSPORT_DISPATCH``. This is
**not** called automatically; callers opt into the dispatch surface they
want to validate.
"""
from __future__ import annotations

from collections.abc import Mapping

from bass.los.families import (
    type_i,
    type_ii,
    type_iii,
    type_iv,
    type_v,
    type_vi_0,
    type_vi_h,
    type_vii_0,
    type_vii_h,
    type_viii,
    type_ix,
)
from bass.los.families.base import (
    FamilyMetadata,
    LegacyDelegationKernel,
    NotImplementedKernel,
    family_metadata_from_registry,
)
from bass.transport.exact_transport import (
    _TRANSPORT_DISPATCH,
    register_family_kernel,
)


__all__ = (
    "FamilyMetadata",
    "LegacyDelegationKernel",
    "NotImplementedKernel",
    "KNOWN_FAMILIES",
    "IMPLEMENTED_FAMILIES",
    "SKELETON_FAMILIES",
    "family_metadata_from_registry",
    "get_family_kernel",
    "is_skeleton",
    "register_all_defaults",
    "unregister_all_defaults",
)


KNOWN_FAMILIES: Mapping[str, object] = {
    "I": type_i.KERNEL,
    "II": type_ii.KERNEL,
    "III": type_iii.KERNEL,
    "IV": type_iv.KERNEL,
    "V": type_v.KERNEL,
    "VI_0": type_vi_0.KERNEL,
    "VI_h": type_vi_h.KERNEL,
    "VII_0": type_vii_0.KERNEL,
    "VII_h": type_vii_h.KERNEL,
    "VIII": type_viii.KERNEL,
    "IX": type_ix.KERNEL,
}


def is_skeleton(family: str) -> bool:
    """True iff ``family``'s kernel still inherits from ``NotImplementedKernel``."""
    kernel = KNOWN_FAMILIES.get(family)
    return isinstance(kernel, NotImplementedKernel)


IMPLEMENTED_FAMILIES: tuple[str, ...] = tuple(
    family for family in KNOWN_FAMILIES if not is_skeleton(family)
)
SKELETON_FAMILIES: tuple[str, ...] = tuple(
    family for family in KNOWN_FAMILIES if is_skeleton(family)
)


def get_family_kernel(family: str) -> object:
    """Return the kernel singleton for ``family``. KeyError on unknown."""
    if family not in KNOWN_FAMILIES:
        raise KeyError(
            f"Unknown Bianchi family '{family}'. Known: {sorted(KNOWN_FAMILIES)}"
        )
    return KNOWN_FAMILIES[family]


def register_all_defaults() -> tuple[str, ...]:
    """Register every ``KNOWN_FAMILIES`` kernel into the transport dispatch.

    Returns the tuple of family names registered. Safe to call multiple
    times: ``register_family_kernel`` is idempotent for the same object.
    """
    registered: list[str] = []
    for family, kernel in KNOWN_FAMILIES.items():
        register_family_kernel(kernel)
        registered.append(family)
    return tuple(registered)


def unregister_all_defaults() -> None:
    """Remove every ``KNOWN_FAMILIES`` kernel from the dispatch.

    Intended for test teardown; in production the registry grows
    monotonically through the session.
    """
    for family, kernel in KNOWN_FAMILIES.items():
        if _TRANSPORT_DISPATCH.get(family) is kernel:
            del _TRANSPORT_DISPATCH[family]
