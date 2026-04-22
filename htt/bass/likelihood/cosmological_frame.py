"""FB-7.4 cosmological-frame likelihood.

The probability density function implemented here is evaluated in the
Bianchi rest frame only.  Observer-motion marginalisation is explicitly
out of scope for FB-7 and must be layered on later via
``bass.likelihood.observer_frame_adapter`` in FB-8.  No observer boost
parameters are accepted by this class.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

import numpy as np

_OBSERVER_FRAME_KEYS = frozenset(
    {
        "observer_boost",
        "beta_obs",
        "v_hat_obs",
        "observer_frame",
        "boost_vector",
        "boost_prior",
    }
)
_SPECTRUM_KEYS = ("TT", "EE", "TE", "BB")
_SMALL_FLOAT = 1.0e-30


def _normalise_axis(vector: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    arr = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(arr))
    if not np.isfinite(norm) or norm <= _SMALL_FLOAT:
        arr = np.asarray(fallback, dtype=float)
        norm = float(np.linalg.norm(arr))
    return arr / max(norm, _SMALL_FLOAT)


def _axis_from_angles(longitude_deg: float, latitude_deg: float) -> np.ndarray:
    lon = np.radians(float(longitude_deg))
    lat = np.radians(float(latitude_deg))
    return np.array(
        [
            np.cos(lat) * np.cos(lon),
            np.cos(lat) * np.sin(lon),
            np.sin(lat),
        ],
        dtype=float,
    )


def _as_mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


class CosmologicalFrameLikelihood:
    """Direction-dependent likelihood in the cosmological frame only.

    Scope pin: this output is **cosmological-frame only**. FB-8 composes
    the observer-frame layer on top via
    ``bass.likelihood.observer_frame_adapter``; this class must not
    silently absorb observer-frame boost parameters.
    """

    def __init__(
        self,
        *,
        htt_decomposition: Mapping[str, object],
        tier: Literal["low_ell", "hybrid", "full"] = "low_ell",
    ) -> None:
        if tier not in {"low_ell", "hybrid", "full"}:
            raise ValueError("tier must be one of 'low_ell', 'hybrid', 'full'")
        if "resolved_axis" not in htt_decomposition:
            raise KeyError("htt_decomposition must include 'resolved_axis'")

        directional_covariance = htt_decomposition.get("directional_covariance", {})
        ell = directional_covariance.get("ell")
        if ell is None:
            ell = np.arange(
                max(
                    (
                        len(np.asarray(htt_decomposition.get("spectra_reference", {}).get(key, [])))
                        for key in _SPECTRUM_KEYS
                    ),
                    default=0,
                ),
                dtype=int,
            )
        self.ell = np.asarray(ell, dtype=int)
        self.tier = tier
        self.htt_decomposition = htt_decomposition
        self.resolved_axis = _normalise_axis(
            np.asarray(htt_decomposition["resolved_axis"], dtype=float),
            np.array([0.0, 0.0, 1.0]),
        )
        self.axis_precision = float(htt_decomposition.get("axis_precision", 4.0))
        self.effective_amplitude = float(htt_decomposition.get("effective_amplitude", 0.0))
        self.beta_gate_pass = bool(htt_decomposition.get("beta_gate_pass", True))
        self.anisotropy_tensor = np.asarray(
            htt_decomposition.get("anisotropy_tensor", np.zeros((3, 3))),
            dtype=float,
        )
        self.anisotropy_tensor = 0.5 * (self.anisotropy_tensor + self.anisotropy_tensor.T)
        spectra_reference = htt_decomposition.get("spectra_reference", {})
        self.spectra_reference = {
            key: np.asarray(spectra_reference.get(key, np.zeros(self.ell.size)), dtype=float)
            for key in _SPECTRUM_KEYS
        }
        tier_max_ell = {"low_ell": 12, "hybrid": 20, "full": np.inf}[tier]
        if self.ell.size:
            self.ell_mask = (self.ell >= 2) & (self.ell <= tier_max_ell)
        else:
            self.ell_mask = np.zeros(0, dtype=bool)
        self.noise_fraction = {"low_ell": 0.08, "hybrid": 0.06, "full": 0.04}[tier]
        self.harmonic_support = tuple(htt_decomposition.get("harmonic_support", ()))
        self.alm_reference = _as_mapping(htt_decomposition.get("alm_reference"))
        self.alm_reference_packed = _as_mapping(
            htt_decomposition.get("alm_reference_packed")
        )
        harmonic_covariance = _as_mapping(htt_decomposition.get("harmonic_covariance"))
        self.harmonic_gaussian_ready = False
        self._joint_covariance = None
        self._joint_covariance_inv = None
        self._harmonic_size = 0
        if (
            harmonic_covariance is not None
            and self.alm_reference is not None
            and "dense_blocks" in harmonic_covariance
        ):
            blocks = _as_mapping(harmonic_covariance["dense_blocks"])
            if blocks is not None:
                tt = np.asarray(blocks.get("TT", np.zeros((0, 0))), dtype=float)
                ee = np.asarray(blocks.get("EE", np.zeros((0, 0))), dtype=float)
                te = np.asarray(blocks.get("TE", np.zeros((0, 0))), dtype=float)
                bb = np.asarray(blocks.get("BB", np.zeros((0, 0))), dtype=float)
                size = int(tt.shape[0])
                if (
                    tt.shape == (size, size)
                    and ee.shape == (size, size)
                    and te.shape == (size, size)
                    and bb.shape == (size, size)
                ):
                    scale = max(
                        float(np.max(np.abs(np.diag(tt)))) if size else 0.0,
                        float(np.max(np.abs(np.diag(ee)))) if size else 0.0,
                        float(np.max(np.abs(np.diag(bb)))) if size else 0.0,
                        1.0e-12,
                    )
                    regularization = 1.0e-9 * scale
                    zero = np.zeros_like(tt)
                    joint = np.block(
                        [
                            [tt, te, zero],
                            [te.T, ee, zero],
                            [zero, zero, bb],
                        ]
                    )
                    joint = 0.5 * (joint + joint.T)
                    joint += regularization * np.eye(joint.shape[0], dtype=float)
                    self._joint_covariance = joint
                    self._joint_covariance_inv = np.linalg.inv(joint)
                    self._harmonic_size = size
                    self.harmonic_gaussian_ready = bool(size > 0)

    def _reject_observer_frame_params(self, params: Mapping[str, object]) -> None:
        overlap = _OBSERVER_FRAME_KEYS.intersection(params)
        if overlap:
            keys = ", ".join(sorted(overlap))
            raise ValueError(
                "CosmologicalFrameLikelihood is cosmological-frame only; "
                f"observer-motion keys [{keys}] must be handled by "
                "bass.likelihood.observer_frame_adapter in FB-8."
            )

    def _axis_from_params(self, params: Mapping[str, object]) -> np.ndarray:
        if "axis_vector" in params:
            return _normalise_axis(np.asarray(params["axis_vector"], dtype=float), self.resolved_axis)
        if "preferred_axis" in params:
            return _normalise_axis(
                np.asarray(params["preferred_axis"], dtype=float), self.resolved_axis
            )
        lon_key = "axis_l_deg" if "axis_l_deg" in params else "lon_deg" if "lon_deg" in params else "l_deg"
        lat_key = "axis_b_deg" if "axis_b_deg" in params else "lat_deg" if "lat_deg" in params else "b_deg"
        if lon_key in params and lat_key in params:
            return _normalise_axis(
                _axis_from_angles(float(params[lon_key]), float(params[lat_key])),
                self.resolved_axis,
            )
        return self.resolved_axis.copy()

    def _spectral_log_prob(self, params: Mapping[str, object]) -> float:
        if self.ell_mask.size == 0:
            return 0.0
        logp = 0.0
        for key in _SPECTRUM_KEYS:
            ref = np.asarray(self.spectra_reference[key], dtype=float)
            model_key = f"spectra_{key}"
            model = np.asarray(params.get(model_key, ref), dtype=float)
            n = min(ref.size, model.size, self.ell_mask.size)
            if n == 0:
                continue
            mask = self.ell_mask[:n]
            if not np.any(mask):
                continue
            ref_sel = ref[:n][mask]
            model_sel = model[:n][mask]
            sigma = self.noise_fraction * np.maximum(np.abs(ref_sel), 1.0e-6)
            residual = model_sel - ref_sel
            logp += -0.5 * float(np.sum((residual / sigma) ** 2))
        return logp

    def _harmonic_vector(self, params: Mapping[str, object]) -> np.ndarray:
        assert self.alm_reference is not None
        size = self._harmonic_size
        vectors: list[np.ndarray] = []
        for key, fallback_name in (("alm_T", "T"), ("alm_E", "E"), ("alm_B", "B")):
            fallback = np.asarray(self.alm_reference[fallback_name], dtype=float)
            values = np.asarray(params.get(key, fallback), dtype=float)
            if values.shape != (size,):
                raise ValueError(
                    f"{key} must have shape ({size},), got {values.shape}"
                )
            vectors.append(values)
        return np.concatenate(vectors)

    def _harmonic_log_prob(self, params: Mapping[str, object]) -> float:
        assert self._joint_covariance_inv is not None
        assert self.alm_reference is not None
        reference = np.concatenate(
            [
                np.asarray(self.alm_reference["T"], dtype=float),
                np.asarray(self.alm_reference["E"], dtype=float),
                np.asarray(self.alm_reference["B"], dtype=float),
            ]
        )
        model = self._harmonic_vector(params)
        residual = model - reference
        quad = float(residual @ self._joint_covariance_inv @ residual)
        return -0.5 * quad

    def log_prob(self, params: Mapping[str, object]) -> float:
        """Evaluate the cosmological-frame log-likelihood."""
        self._reject_observer_frame_params(params)
        if self.harmonic_gaussian_ready:
            return float(self._harmonic_log_prob(params))
        axis = self._axis_from_params(params)
        amplitude = float(params.get("amplitude", params.get("anisotropy_amplitude", self.effective_amplitude)))

        alignment = float(np.clip(np.dot(axis, self.resolved_axis), -1.0, 1.0))
        angular_term = self.axis_precision * alignment
        quadratic_term = float(axis @ self.anisotropy_tensor @ axis)
        amp_sigma = max(0.05, 0.35 * max(self.effective_amplitude, 0.05))
        amplitude_term = -0.5 * ((amplitude - self.effective_amplitude) / amp_sigma) ** 2
        if not self.beta_gate_pass:
            amplitude_term -= 12.0 * amplitude * amplitude
        spectral_term = self._spectral_log_prob(params)
        return float(angular_term + quadratic_term + amplitude_term + spectral_term)

    def directional_surface(
        self,
        *,
        amplitude: float | None = None,
        n_longitude: int = 121,
        n_latitude: int = 61,
    ) -> dict[str, np.ndarray]:
        """Evaluate ``log_prob`` on a longitude/latitude grid.

        The surface is still cosmological-frame only; observer-motion
        marginalisation remains the FB-8 adapter's responsibility.
        """
        lon = np.linspace(0.0, 360.0, int(n_longitude))
        lat = np.linspace(-90.0, 90.0, int(n_latitude))
        log_prob = np.zeros((lat.size, lon.size), dtype=float)
        for ilat, lat_deg in enumerate(lat):
            for ilon, lon_deg in enumerate(lon):
                params = {"axis_l_deg": lon_deg, "axis_b_deg": lat_deg}
                if amplitude is not None:
                    params["amplitude"] = float(amplitude)
                log_prob[ilat, ilon] = self.log_prob(params)
        return {
            "longitude_deg": lon,
            "latitude_deg": lat,
            "log_prob": log_prob,
        }
