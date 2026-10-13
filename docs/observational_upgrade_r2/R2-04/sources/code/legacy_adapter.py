"""Explicit-contract adapters around immutable HTT legacy formula bytes.

No legacy likelihood, data defaults, cached evidence or physical detection is
implicitly imported. Bounds are conditional on the supplied proof scope and on
the epsilon convention matching that scope. NumPy is the only new dependency.
"""
from __future__ import annotations

import builtins
from dataclasses import dataclass, asdict
import hashlib
from pathlib import Path
from types import ModuleType
import numpy as np


@dataclass(frozen=True)
class AnalysisContract:
    contract_id: str
    congruence: str
    comparator_id: str
    proof_scope_id: str
    measure_id: str
    multipole_definition: str = "sqrt((2ell+1)*C_ell/(4*pi))/T0"

    def __post_init__(self):
        if any(not isinstance(x, str) or not x.strip() for x in asdict(self).values()):
            raise ValueError("Every physical/provenance contract field is required")


def multipole_rms(power, ell, *, power_kind: str, power_unit: str, T0_K: float):
    """Harmonic RMS epsilon, NOT an undocumented PSTF multipole norm.

    D_ell = ell(ell+1) C_ell/(2*pi). Units are explicit; all inputs must
    be nonnegative finite powers with integer ell >= 1 and T0_K > 0.
    """
    power, ell = np.broadcast_arrays(np.asarray(power, float), np.asarray(ell, float))
    if (not np.isfinite(T0_K) or T0_K <= 0 or np.any(~np.isfinite(power))
            or np.any(power < 0) or np.any(~np.isfinite(ell))
            or np.any(ell < 1) or np.any(ell != np.floor(ell))):
        raise ValueError("Invalid spectrum, ell, or temperature")
    if power_kind not in {"C_ell", "D_ell"} or power_unit not in {"K2", "uK2"}:
        raise ValueError("Declare C_ell/D_ell and K2/uK2 explicitly")
    cl = power * (1e-12 if power_unit == "uK2" else 1.0)
    if power_kind == "D_ell":
        cl = cl * 2 * np.pi / (ell * (ell + 1))
    return np.sqrt((2 * ell + 1) * cl / (4 * np.pi)) / T0_K


class LegacyAdapter:
    """Load bounds.py and its ssot dependency without editing either source.

    An import hook is local to the bounds module; sys.path/sys.modules are not
    modified. All observation-sensitive function arguments are supplied below.
    This loads trusted user-supplied Python, not a sandbox for arbitrary code.
    """
    def __init__(self, legacy_root, contract: AnalysisContract, expected_hashes=None):
        self.root = Path(legacy_root).resolve()
        self.contract = contract
        self.hashes = {}
        modules = {}
        for name in ("ssot", "bounds"):
            path = self.root / "htt" / (name + ".py")
            source = path.read_bytes()
            self.hashes[str(path.relative_to(self.root))] = hashlib.sha256(source).hexdigest()
            if expected_hashes is not None:
                if expected_hashes.get(str(path.relative_to(self.root))) != self.hashes[str(path.relative_to(self.root))]:
                    raise ValueError("Legacy source hash mismatch: " + str(path))
            module = ModuleType("_htt_legacy_" + name)
            module.__file__ = str(path)
            native_import = builtins.__import__
            def local_import(import_name, globals=None, locals=None, fromlist=(), level=0):
                if level == 0 and import_name == "ssot":
                    return modules["ssot"]
                return native_import(import_name, globals, locals, fromlist, level)
            module.__dict__["__builtins__"] = dict(vars(builtins), __import__=local_import)
            exec(compile(source, str(path), "exec"), module.__dict__)
            modules[name] = module
        self.bounds = modules["bounds"]

    def bounds_from_epsilon(self, eps1, eps2, eps3, *, frame_correction: bool):
        """Evaluate actual legacy bound functions, never their data defaults.

        The returned Sigma2 ceiling is a SHEAR ceiling. It must not silently
        become a total signed-defect ceiling with tilt/curvature/vorticity.
        """
        e1, e2, e3 = np.broadcast_arrays(*[np.asarray(x, float) for x in (eps1, eps2, eps3)])
        if any(np.any(~np.isfinite(x)) or np.any(x < 0) for x in (e1, e2, e3)):
            raise ValueError("Multipole bounds require finite nonnegative epsilon")
        bs = self.bounds.B_sigma_corrected(e1, e2, e3) if frame_correction else self.bounds.B_sigma(e1, e2, e3)
        return {"B_sigma": bs, "B_omega": self.bounds.B_omega(e1, e2, e3),
                "B_accel": self.bounds.B_accel(e1, e2, e3),
                "Sigma2_shear_ceiling": 1.5 * bs**2,
                "frame_correction": frame_correction,
                "contract": asdict(self.contract), "source_sha256": self.hashes.copy()}

    def departure_pushforward(self, *, Sigma2, W2, Omega_tilt, curvature_delta,
                             weights, x_ceiling, identifiable, q_thresholds=(0.1,)):
        """Signed x and partial-observable Q/Pi, preserving unknown mass.

        x_ceiling is caller-supplied and scope-specific. No missing component is
        replaced by zero. identifiable is a per-sample physical/response flag.
        Strict threshold event Q > q* retains exact boundary mass explicitly.
        Bounds are for the declared normalized input measure (e.g. posterior),
        never automatically for the cosmological population or frequentist law.
        """
        inputs = [np.asarray(a, float) for a in
            (Sigma2, W2, Omega_tilt, curvature_delta, weights, x_ceiling)]
        if any(a.ndim > 1 for a in inputs) or np.asarray(identifiable).ndim > 1:
            raise ValueError("Posterior inputs must be scalars or one-dimensional samples")
        arr = np.broadcast_arrays(*inputs)
        s, w, t, k, weight, ceiling = [a.reshape(-1) for a in arr]
        known = np.broadcast_to(np.asarray(identifiable, bool), arr[0].shape).reshape(-1)
        if len(weight) == 0 or np.any(~np.isfinite(weight)) or np.any(weight < 0) or weight.max() <= 0:
            raise ValueError("Weights must be finite, nonnegative, and have positive total")
        if np.any((s < 0) & np.isfinite(s)) or np.any((w < 0) & np.isfinite(w)):
            raise ValueError("Sigma2 and W2 are squared quantities")
        # Scaling first avoids overflow for finite but very large weights.
        scaled_weight = weight / weight.max()
        p = scaled_weight / scaled_weight.sum()
        raw_x = self.bounds.x_defect(s, Omega_tilt=t, Omega_k_aniso=k, W2=w)
        x_known = known & np.isfinite(s) & np.isfinite(w) & np.isfinite(t) & np.isfinite(k) & np.isfinite(raw_x)
        x = np.where(x_known, raw_x, np.nan)
        q_known = x_known & np.isfinite(ceiling) & (ceiling > 0)
        q = np.full_like(x, np.nan)
        q[q_known] = x[q_known] / ceiling[q_known]
        q_known &= np.isfinite(q)
        q[~q_known] = np.nan
        unknown_mass = float(p[~q_known].sum())
        thresholds = np.asarray(q_thresholds, float).reshape(-1)
        if np.any(~np.isfinite(thresholds)):
            raise ValueError("Thresholds must be finite")
        pi = []
        for threshold in thresholds:
            lower = float(p[q_known & (q > threshold)].sum())
            boundary = float(p[q_known & (q == threshold)].sum())
            pi.append({"threshold": float(threshold), "event": "Q > threshold",
                       "lower": lower, "upper": min(1.0, lower + unknown_mass),
                       "known_boundary_mass": boundary})
        return {"x": x, "Q": q, "normalized_weights": p,
                "x_known_mass": float(p[x_known].sum()),
                "Q_known_mass": float(p[q_known].sum()),
                "Q_unknown_mass": unknown_mass, "Pi_intervals": pi,
                "contract": asdict(self.contract), "source_sha256": self.hashes.copy()}
