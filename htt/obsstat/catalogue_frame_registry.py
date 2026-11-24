"""Catalogue frame registry on top of ``publication_frame_kinematics`` (R108 SQ-FRAME).

Purpose
-------
One record per catalogue release used in R98-R106: position frame, epoch/equinox,
redshift frame(s) and the velocity reference that connects them, each with a
locator (ReadMe line, VOTable FIELD, TAP_SCHEMA row, FITS header card or paper
section). Frame changes are allowed only through a registered
:class:`VelocityReference`; the transformation methods accept a registry key and
never a raw velocity ("no unmeasured beta"), and every transformation also names
the release whose data it transforms (required keyword ``release_id``). The pair
is checked by :meth:`FrameRegistry.conversion_reference`:

* the release must be registered with ``conversion_status = "registered"``. A
  release whose redshift frame is stated but whose conversion velocity is not
  stated in the release or a cited paper carries ``"beta_not_stated"``; a release
  with no velocity frame carries ``"not_applicable"``. Every transformation that
  names either raises :class:`UnmeasuredBetaError`;
* the key must be one of the release's own velocity references, or the own
  reference of another registered release (e.g. the Planck 2018 solar dipole
  applied to CF4 heliocentric redshifts) whose input frame is a frame the data
  release states: the moving frame for ``*_to_rest`` and the rest frame for
  ``*_to_moving``.

What the registry does not check: a reference is admitted with a status in
``_ALLOWED_STATUS`` and a locator string of at least 8 characters; the content of
the locator is not verified.

Conventions
-----------
* Local tetrad (-,+,+,+), units of c; ``beta`` is the velocity of the *moving*
  frame (e.g. the solar-system barycentre) measured in the *rest* frame (e.g.
  the CMB frame), Galactic Cartesian components (x to l=0,b=0; z to b=90 deg).
* Velocity composition is ``publication_frame_kinematics.relative_beta``
  (canonical unrotated boost). The inverse of the boost by ``beta`` is the boost
  by ``-beta`` (a single pure boost has no Wigner rotation).
* Photon direction ``n`` points from the observer to the source. For a frame S
  moving with ``beta`` relative to rest frame C and ``n_S`` measured in S::

      1 + z_C = (1 + z_S) / (gamma (1 - beta . n_S))
      n_C = [n_S + (gamma - 1)(n_S . bhat) bhat - gamma beta] / (gamma (1 - beta . n_S))

  To first order ``c z_C = c z_S + c beta . n_S`` (heliocentric to CMB when S is
  the barycentre and C the CMB frame).

This module holds no measured numbers except the published Planck 2018 solar
dipole (with locator). Release-recovered velocities are loaded from the JSON
written by ``scripts/r108/frame_registry_build.py``.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal, Mapping

import numpy as np

from . import publication_frame_kinematics as pfk

__all__ = [
    "C_KM_S",
    "UnmeasuredBetaError",
    "VelocityReference",
    "CatalogueRelease",
    "FrameRegistry",
    "planck2018_solar_dipole_reference",
    "galactic_unit_vector",
]

C_KM_S = 299792.458

ConversionStatus = Literal["published", "recovered_from_release", "measured_repository_estimate"]
#: published: quoted in a paper or release with a locator; recovered_from_release: reproduced from the
#: release's own two-frame columns; measured_repository_estimate: a repository estimator output on a
#: release (locator = file path + SHA-256). Anything else (assumed, fiducial, default) is refused.
_ALLOWED_STATUS = ("published", "recovered_from_release", "measured_repository_estimate")


class UnmeasuredBetaError(KeyError):
    """Raised when a frame change would need a velocity that is not registered."""


def galactic_unit_vector(l_deg: float, b_deg: float) -> np.ndarray:
    l, b = math.radians(float(l_deg)), math.radians(float(b_deg))
    if not (math.isfinite(l) and math.isfinite(b)) or abs(b) > math.pi / 2 + 1e-15:
        raise ValueError("finite Galactic (l, b) required")
    return np.array([math.cos(b) * math.cos(l), math.cos(b) * math.sin(l), math.sin(b)])


def _vec3(value, name: str) -> np.ndarray:
    v = np.asarray(value, dtype=np.float64)
    if v.shape != (3,) or not np.isfinite(v).all():
        raise ValueError(f"{name} must be a finite 3-vector")
    return v


@dataclass(frozen=True)
class VelocityReference:
    """A measured or release-recovered frame velocity with its locator.

    ``beta_galactic`` is the velocity of ``moving_frame`` in ``rest_frame`` (units
    of c, Galactic Cartesian). ``covariance_galactic`` is optional (3x3, units of
    c^2); ``None`` means the release states no uncertainty.
    """

    key: str
    moving_frame: str
    rest_frame: str
    beta_galactic: tuple[float, float, float]
    status: ConversionStatus
    locator: str
    covariance_galactic: tuple[tuple[float, float, float], ...] | None = None
    formula: str = "exact_relativistic"
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.key or not isinstance(self.key, str):
            raise ValueError("velocity reference key required")
        if self.status not in _ALLOWED_STATUS:
            raise UnmeasuredBetaError(
                f"{self.key}: status {self.status!r} is not a measured beta; allowed {_ALLOWED_STATUS}")
        if not isinstance(self.locator, str) or len(self.locator.strip()) < 8:
            raise UnmeasuredBetaError(f"{self.key}: a locator is required for every beta")
        b = _vec3(self.beta_galactic, "beta_galactic")
        if float(b @ b) >= 1.0:
            raise ValueError("superluminal beta")
        object.__setattr__(self, "beta_galactic", tuple(float(x) for x in b))
        if self.covariance_galactic is not None:
            c = np.asarray(self.covariance_galactic, dtype=np.float64)
            if c.shape != (3, 3) or not np.isfinite(c).all() or np.max(abs(c - c.T)) > 1e-12 * max(1e-300, np.max(abs(c))):
                raise ValueError("covariance must be finite symmetric 3x3")
            if np.linalg.eigvalsh(c).min() < -1e-12 * max(1e-300, np.max(abs(c))):
                raise ValueError("covariance must be positive semidefinite")
            object.__setattr__(self, "covariance_galactic", tuple(tuple(float(x) for x in row) for row in c))
        if self.formula not in ("exact_relativistic", "linear_cz_sum"):
            raise ValueError("formula must be exact_relativistic or linear_cz_sum")

    @property
    def beta(self) -> np.ndarray:
        return np.array(self.beta_galactic, dtype=np.float64)

    def to_dict(self) -> dict:
        return {
            "key": self.key, "moving_frame": self.moving_frame, "rest_frame": self.rest_frame,
            "beta_galactic": list(self.beta_galactic), "status": self.status, "locator": self.locator,
            "covariance_galactic": None if self.covariance_galactic is None else [list(r) for r in self.covariance_galactic],
            "formula": self.formula, "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: Mapping) -> "VelocityReference":
        cov = d.get("covariance_galactic")
        return cls(key=d["key"], moving_frame=d["moving_frame"], rest_frame=d["rest_frame"],
                   beta_galactic=tuple(d["beta_galactic"]), status=d["status"], locator=d["locator"],
                   covariance_galactic=None if cov is None else tuple(tuple(r) for r in cov),
                   formula=d.get("formula", "exact_relativistic"), notes=d.get("notes", ""))


@dataclass(frozen=True)
class CatalogueRelease:
    """Frame identity of one catalogue release.

    ``locators`` maps each field name (``position_frame``, ``epoch``,
    ``redshift_frames``, ``velocity_reference``) to a locator string.
    ``conversion_status`` is ``"registered"`` when every conversion the release
    needs is a registered velocity, ``"not_applicable"`` when the release has no
    redshift/velocity frame to convert, and ``"beta_not_stated"`` otherwise.
    """

    release_id: str
    name: str
    position_frame: str
    epoch: str
    equinox: str
    redshift_frames: tuple[str, ...]
    velocity_reference_keys: tuple[str, ...]
    conversion_status: Literal["registered", "not_applicable", "beta_not_stated"]
    locators: tuple[tuple[str, str], ...]
    notes: str = ""

    def __post_init__(self) -> None:
        if self.conversion_status not in ("registered", "not_applicable", "beta_not_stated"):
            raise ValueError("unknown conversion_status")
        if self.conversion_status == "registered" and not self.velocity_reference_keys:
            raise ValueError(f"{self.release_id}: registered conversion needs velocity reference keys")
        if self.conversion_status != "registered" and self.velocity_reference_keys:
            raise ValueError(f"{self.release_id}: velocity keys given but status {self.conversion_status}")
        loc = dict(self.locators)
        for fld in ("position_frame", "epoch", "redshift_frames"):
            if not loc.get(fld):
                raise ValueError(f"{self.release_id}: locator for {fld} required")
        if self.velocity_reference_keys and not loc.get("velocity_reference"):
            raise ValueError(f"{self.release_id}: locator for velocity_reference required")

    def to_dict(self) -> dict:
        return {"release_id": self.release_id, "name": self.name, "position_frame": self.position_frame,
                "epoch": self.epoch, "equinox": self.equinox, "redshift_frames": list(self.redshift_frames),
                "velocity_reference_keys": list(self.velocity_reference_keys),
                "conversion_status": self.conversion_status, "locators": dict(self.locators), "notes": self.notes}

    @classmethod
    def from_dict(cls, d: Mapping) -> "CatalogueRelease":
        return cls(release_id=d["release_id"], name=d["name"], position_frame=d["position_frame"],
                   epoch=d["epoch"], equinox=d["equinox"], redshift_frames=tuple(d["redshift_frames"]),
                   velocity_reference_keys=tuple(d["velocity_reference_keys"]),
                   conversion_status=d["conversion_status"], locators=tuple(sorted(d["locators"].items())),
                   notes=d.get("notes", ""))


def planck2018_solar_dipole_reference(t0_k: float = 2.72548) -> VelocityReference:
    """Published Planck 2018 solar dipole as a frame velocity (barycentre in CMB frame).

    Planck Collaboration 2020, A&A 641, A1 (Planck 2018 results I), Sect. 5.1/Table 3:
    amplitude 3362.08 +- 0.99 uK, (l, b) = (264.021 +- 0.011, 48.253 +- 0.005) deg;
    T0 = 2.72548 +- 0.00057 K (Fixsen 2009, ApJ 707, 916). beta = A / T0 to first order.
    The same constants are in htt/htt/htt/infer/physical_dipole.py (A_REF_MICROK, L_DEG, B_DEG).
    Covariance: Gaussian propagation of the quoted amplitude, l, b and T0 errors (independent);
    an error proxy, not the Planck likelihood.
    """
    amp, sa = 3362.08e-6, 0.99e-6
    l, b = 264.021, 48.253
    sl, sb = math.radians(0.011), math.radians(0.005)
    st0 = 0.00057
    beta = amp / t0_k
    n = galactic_unit_vector(l, b)
    lr, br = math.radians(l), math.radians(b)
    dn_dl = np.array([-math.cos(br) * math.sin(lr), math.cos(br) * math.cos(lr), 0.0])
    dn_db = np.array([-math.sin(br) * math.cos(lr), -math.sin(br) * math.sin(lr), math.cos(br)])
    J = np.column_stack((n / t0_k, beta * dn_dl, beta * dn_db, -beta * n / t0_k))
    cov = J @ np.diag([sa ** 2, sl ** 2, sb ** 2, st0 ** 2]) @ J.T
    return VelocityReference(
        key="planck2018_solar_dipole", moving_frame="solar_system_barycentre", rest_frame="CMB",
        beta_galactic=tuple(beta * n), status="published",
        locator=("Planck 2018 results I, A&A 641, A1 (2020), Sect. 5.1 Table 3 (3362.08+-0.99 uK, "
                 "l=264.021+-0.011, b=48.253+-0.005); T0 Fixsen 2009 ApJ 707 916; "
                 "repo constants htt/htt/htt/infer/physical_dipole.py"),
        covariance_galactic=tuple(tuple(r) for r in cov), formula="exact_relativistic",
        notes="beta = A/T0 (first-order kinematic dipole); 369.82 km/s",
    )


@dataclass
class FrameRegistry:
    """Registry of releases and the only velocities allowed for frame changes."""

    references: dict[str, VelocityReference] = field(default_factory=dict)
    releases: dict[str, CatalogueRelease] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    # -- construction ---------------------------------------------------
    def register_reference(self, ref: VelocityReference) -> None:
        if not isinstance(ref, VelocityReference):
            raise TypeError("only VelocityReference objects can be registered")
        if ref.key in self.references and self.references[ref.key] != ref:
            raise ValueError(f"conflicting velocity reference {ref.key}")
        self.references[ref.key] = ref

    def register_release(self, rel: CatalogueRelease) -> None:
        if not isinstance(rel, CatalogueRelease):
            raise TypeError("only CatalogueRelease objects can be registered")
        for k in rel.velocity_reference_keys:
            if k not in self.references:
                raise UnmeasuredBetaError(f"{rel.release_id}: velocity reference {k!r} is not registered")
        self.releases[rel.release_id] = rel

    def validate(self) -> None:
        for key, ref in self.references.items():
            if key != ref.key:
                raise ValueError("reference key mismatch")
        for rel in self.releases.values():
            for k in rel.velocity_reference_keys:
                if k not in self.references:
                    raise UnmeasuredBetaError(f"{rel.release_id}: velocity reference {k!r} is not registered")

    # -- access (keys only: no raw beta) ---------------------------------
    def _ref(self, key) -> VelocityReference:
        if not isinstance(key, str):
            raise TypeError("frame transformations take a registry key, never a raw velocity")
        try:
            return self.references[key]
        except KeyError:
            raise UnmeasuredBetaError(f"velocity reference {key!r} is not registered") from None

    def release_reference(self, release_id: str, key: str) -> VelocityReference:
        """The release's own velocity reference ``key`` (registered releases only)."""
        rel = self._release(release_id)
        if rel.conversion_status != "registered":
            raise UnmeasuredBetaError(
                f"{release_id}: conversion_status={rel.conversion_status}; no measured beta for a frame change")
        if key not in rel.velocity_reference_keys:
            raise UnmeasuredBetaError(f"{release_id}: {key!r} is not a velocity reference of this release")
        return self._ref(key)

    def _release(self, release_id) -> CatalogueRelease:
        if not isinstance(release_id, str):
            raise TypeError("release_id must be a registered release id string")
        rel = self.releases.get(release_id)
        if rel is None:
            raise UnmeasuredBetaError(f"unknown release {release_id!r}; register it before transforming its data")
        return rel

    def stated_frames(self, release_id: str) -> frozenset[str]:
        """Frames in which a registered release states its velocities (from its own references)."""
        rel = self._release(release_id)
        return frozenset(f for k in rel.velocity_reference_keys
                         for f in (self.references[k].moving_frame, self.references[k].rest_frame))

    def conversion_reference(self, release_id: str, key: str,
                             direction: Literal["to_rest", "to_moving"]) -> VelocityReference:
        """Reference ``key`` for a frame change of data from release ``release_id``.

        Raises :class:`UnmeasuredBetaError` unless the release is ``registered`` and
        ``key`` is either one of its own references or the own reference of another
        registered release whose input frame (moving frame for ``to_rest``, rest frame
        for ``to_moving``) is one of :meth:`stated_frames` of the data release.
        """
        ref = self._ref(key)
        if direction not in ("to_rest", "to_moving"):
            raise ValueError("direction must be 'to_rest' or 'to_moving'")
        rel = self._release(release_id)
        if rel.conversion_status != "registered":
            raise UnmeasuredBetaError(
                f"{release_id}: conversion_status={rel.conversion_status}; no frame change of its data is allowed")
        if key in rel.velocity_reference_keys:
            return self.release_reference(release_id, key)
        suppliers = sorted(r.release_id for r in self.releases.values()
                           if r.conversion_status == "registered" and key in r.velocity_reference_keys)
        if not suppliers:
            raise UnmeasuredBetaError(f"{key!r} is not the stated velocity reference of any registered release")
        frame_in = ref.moving_frame if direction == "to_rest" else ref.rest_frame
        own = self.stated_frames(release_id)
        if frame_in not in own:
            raise UnmeasuredBetaError(
                f"{release_id}: {key!r} ({direction}) needs data in {frame_in!r}; the release states {sorted(own)}")
        return ref

    def beta(self, key: str) -> np.ndarray:
        return self._ref(key).beta

    # -- velocities (publication_frame_kinematics boosts) ----------------
    def velocity_to_moving(self, key: str, beta_object_in_rest, *, release_id: str) -> np.ndarray:
        """Object velocity seen from the moving frame (canonical boost by +beta)."""
        if not isinstance(key, str):
            raise TypeError("frame transformations take a registry key, never a raw velocity")
        ref = self.conversion_reference(release_id, key, "to_moving")
        return pfk.relative_beta(_vec3(beta_object_in_rest, "object beta"), ref.beta)

    def velocity_to_rest(self, key: str, beta_object_in_moving, *, release_id: str) -> np.ndarray:
        """Inverse of :meth:`velocity_to_moving` (canonical boost by -beta)."""
        if not isinstance(key, str):
            raise TypeError("frame transformations take a registry key, never a raw velocity")
        ref = self.conversion_reference(release_id, key, "to_rest")
        return pfk.relative_beta(_vec3(beta_object_in_moving, "object beta"), -ref.beta)

    # -- photons: redshift and aberration --------------------------------
    @staticmethod
    def _unit(n) -> np.ndarray:
        n = np.asarray(n, dtype=np.float64)
        if n.ndim == 1:
            n = n[None, :]
        if n.ndim != 2 or n.shape[1] != 3 or not np.isfinite(n).all():
            raise ValueError("directions must be finite N-by-3")
        if np.max(abs(np.linalg.norm(n, axis=1) - 1.0)) > 1e-10:
            raise ValueError("unit directions required")
        return n

    def _photon(self, ref: VelocityReference, z, n, sign: float, formula: str | None = None):
        b = sign * ref.beta
        n = self._unit(n)
        z = np.asarray(z, dtype=np.float64)
        if z.shape not in ((), (len(n),)) or not np.isfinite(z).all() or np.any(z <= -1.0):
            raise ValueError("redshifts must be finite and > -1, one per direction")
        g = pfk.gamma(b)
        bn = n @ b
        form = ref.formula if formula is None else formula
        if form == "linear_cz_sum":
            z_out = z + bn
            n_out = n.copy()
        else:
            z_out = (1.0 + z) / (g * (1.0 - bn)) - 1.0
            bb = float(np.linalg.norm(b))
            bhat = b / bb if bb > 0 else np.zeros(3)
            n_out = (n + ((g - 1.0) * (n @ bhat))[:, None] * bhat[None, :] - g * b[None, :]) / (g * (1.0 - bn))[:, None]
        return z_out, n_out

    def photon_to_rest(self, key: str, z_moving, n_moving, formula: str | None = None, *, release_id: str):
        """(z, n) measured in the moving frame -> rest frame (e.g. heliocentric -> CMB).

        ``formula`` defaults to the convention the reference records (the release's own
        conversion); ``"exact_relativistic"`` forces the exact transform with the same beta.
        ``release_id`` names the release whose (z, n) are transformed (see :meth:`conversion_reference`).
        """
        if not isinstance(key, str):
            raise TypeError("frame transformations take a registry key, never a raw velocity")
        if formula not in (None, "exact_relativistic", "linear_cz_sum"):
            raise ValueError("formula must be None, exact_relativistic or linear_cz_sum")
        ref = self.conversion_reference(release_id, key, "to_rest")
        return self._photon(ref, z_moving, n_moving, +1.0, formula)

    def photon_to_moving(self, key: str, z_rest, n_rest, formula: str | None = None, *, release_id: str):
        """Inverse of :meth:`photon_to_rest` (boost by -beta) for the same ``formula``."""
        if not isinstance(key, str):
            raise TypeError("frame transformations take a registry key, never a raw velocity")
        ref = self.conversion_reference(release_id, key, "to_moving")
        form = ref.formula if formula is None else formula
        if form not in ("exact_relativistic", "linear_cz_sum"):
            raise ValueError("formula must be None, exact_relativistic or linear_cz_sum")
        if form == "linear_cz_sum":
            n = self._unit(n_rest)
            return np.asarray(z_rest, dtype=np.float64) - n @ ref.beta, n.copy()
        return self._photon(ref, z_rest, n_rest, -1.0, "exact_relativistic")

    # -- (de)serialisation ------------------------------------------------
    def to_dict(self) -> dict:
        return {"references": {k: r.to_dict() for k, r in sorted(self.references.items())},
                "releases": {k: r.to_dict() for k, r in sorted(self.releases.items())}}

    @classmethod
    def from_dict(cls, d: Mapping) -> "FrameRegistry":
        reg = cls()
        for r in d.get("references", {}).values():
            reg.register_reference(VelocityReference.from_dict(r))
        for r in d.get("releases", {}).values():
            reg.register_release(CatalogueRelease.from_dict(r))
        return reg

    @classmethod
    def from_json(cls, path: str | Path) -> "FrameRegistry":
        payload = json.loads(Path(path).read_text())
        return cls.from_dict(payload["registry"] if "registry" in payload else payload)

    def releases_with_conversions(self) -> Iterable[tuple[str, str]]:
        for rid, rel in sorted(self.releases.items()):
            for k in rel.velocity_reference_keys:
                yield rid, k
