"""Tilted physical HYREC-2 recombination and reionization rate & Jacobian coupling (N3).

Separates the four distinct physical appearances of baryon tilt and metric expansion:
1. Proper baryon reaction clock: dt_n / d tau_b = Gamma_b => dN / d tau_b = Gamma_b * H_n.
2. Baryon rest-frame target density: n_{H,rest} = N_H / (Gamma_b * a^3).
3. Directional Sobolev Ly-alpha escape rate averaged over Gauss-Legendre S^2:
     K(n_hat) = (1/3) Theta_b + sigma_{b,ab} n_hat^a n_hat^b,
     tau_S(n_hat) = 3 A_{Ly-alpha} lambda_alpha^3 n_{1s} / (8 pi K(n_hat)),
     P_esc(tau_S) = (1 - exp(-tau_S)) / tau_S.
4. Matter expansion cooling Theta_b / 3 + Compton heating/cooling dT_m / dtau_b.

NEVER substitutes H -> Gamma * H globally across reaction clocks, Sobolev optical depth,
density Dilution, and cooling. Uses exact SHA-256 verified recovered HyRec-2 atomic
tables (`Alpha_inf.dat`, `R_inf.dat`, `fit_swift.dat`, `two_photon_tables.dat`).
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from typing import Literal, Sequence

import numpy as np
from scipy.integrate import solve_ivp

from bass.background.geometry import pstf_rank2
from bass.recombination.clocked_chemistry import ChemistryHistory, ChemistryTangent, evolve_clocked_chemistry
from bass.recombination.reionization import C_LIGHT, SIGMA_T, ReionizationParameters
from bass.transport.general_bianchi_transfer import gl_sphere_grid

__all__ = [
    "HYREC_EXPECTED_SHA256",
    "HyRecAtomicTables",
    "TiltedHyrecHistory",
    "TiltedRecombinationChannels",
    "channel_expansion_from_tilted_kinematics",
    "compare_against_forbidden_global_gamma_H",
    "hyrec_emla_rhs_and_jacobian",
    "integrate_tilted_recombination",
    "load_hyrec_atomic_tables",
    "to_clocked_chemistry_inputs",
]

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ATOMIC_DIR = ROOT / "data/external/r101_legacy_recovery/hyrec_atomic"

HYREC_EXPECTED_SHA256: dict[str, str] = {
    "Alpha_inf.dat": "357101049c9382e90e5e1e896961407d3b465b61b78de9750b852c05ea4d1023",
    "R_inf.dat": "ce914f4b552ba55ba00f7916f36b0986f19adfdb638e5aefae91f7b2d05a8112",
    "fit_swift.dat": "46a644d7d2633b8f13080f9062df9b72a2e5adfa956d70d32ad1d7f4ec0a4641",
    "two_photon_tables.dat": "93d23871e21c40f5b72a6ef9acf3eb7be054735c8aee9401e455736c1d9d8cf9",
}

# Physical constants (CGS / eV matching HYREC-2 EMLA2s2p + CMB Boltzmann conventions)
EI_EV = 13.598286071938324
E_HE1_EV = 24.5873888
KBOLTZ_EV_PER_K = 8.617343e-5
LAMBDA_2S1S = 8.2206
A_LYA_S = 6.2649e8
SAHA_FACT_CGS = 3.016103031869581e21
LYA_FACT_CGS = 4.662899067555897e15
SIGMA_T_CGS = 6.6524587321e-25
A_RAD_CGS = 7.5657e-15
ME_CGS = 9.1093837015e-28
C_CGS = 2.99792458e10
G_CGS = 6.67430e-8
M_PROTON_G = 1.67262192369e-24
MPC_CM = 3.0856775814913673e24

HYREC_NTR = 100
HYREC_NTM = 40
HYREC_TR_MIN_EV = 0.004
HYREC_TR_MAX_EV = 0.4
HYREC_TM_TR_MIN = 0.1


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _cubic4(frac: float) -> np.ndarray:
    return np.array(
        [
            frac * (frac - 1.0) * (2.0 - frac) / 6.0,
            (1.0 + frac) * (1.0 - frac) * (2.0 - frac) / 2.0,
            (1.0 + frac) * frac * (2.0 - frac) / 2.0,
            (1.0 + frac) * frac * (frac - 1.0) / 6.0,
        ],
        dtype=np.float64,
    )


@dataclass(frozen=True)
class HyRecAtomicTables:
    """Validated HYREC-2 EMLA effective cascade and SWIFT fit tables."""

    log_alpha_cgs: np.ndarray  # shape (100, 40, 4): [tm<=tr 2s, 2p, tm>tr 2s, 2p]
    log_r2p2s: np.ndarray  # shape (100,)
    swift_tr_k: np.ndarray  # shape (265,)
    swift_delta: np.ndarray  # shape (265, 4): [delta0, d_obh2, d_yp, d_tcmb]
    two_photon_raw: np.ndarray
    sha256_manifest: dict[str, str]
    dlog_tr: float = math.log(HYREC_TR_MAX_EV / HYREC_TR_MIN_EV) / (HYREC_NTR - 1)
    dtm_tr: float = (1.0 - HYREC_TM_TR_MIN) / (HYREC_NTM - 1)

    def interpolate_rates(self, tr_ev: float, tm_ev: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """Return (alpha[2s,2p], dalpha[2s,2p], beta[2s,2p], R_{2p->2s}) in CGS."""
        ratio = tm_ev / max(tr_ev, 1e-30)
        ioff = 2 if ratio > 1.0 else 0
        if ratio > 1.0:
            ratio = 1.0 / ratio
        ratio = min(max(ratio, HYREC_TM_TR_MIN), 1.0)
        tr_c = min(max(tr_ev, HYREC_TR_MIN_EV), HYREC_TR_MAX_EV)

        itrf = (math.log(tr_c) - math.log(HYREC_TR_MIN_EV)) / self.dlog_tr
        itr = int(min(max(int(math.floor(itrf)), 1), HYREC_NTR - 3))
        c_tr = _cubic4(itrf - itr)

        itmf = (ratio - HYREC_TM_TR_MIN) / self.dtm_tr
        itm = int(min(max(int(math.floor(itmf)), 1), HYREC_NTM - 3))
        c_tm = _cubic4(itmf - itm)

        alpha_eq = np.empty(2, dtype=np.float64)
        alpha = np.empty(2, dtype=np.float64)
        beta = np.empty(2, dtype=np.float64)
        saha_coeff = SAHA_FACT_CGS * (tr_c ** 1.5) * math.exp(-0.25 * EI_EV / tr_c)

        sl_tr = slice(itr - 1, itr + 3)
        sl_tm = slice(itm - 1, itm + 3)
        for l_idx in range(2):
            a_eq_l = math.exp(float(c_tr @ self.log_alpha_cgs[sl_tr, -1, l_idx]))
            alpha_eq[l_idx] = a_eq_l
            beta[l_idx] = a_eq_l * saha_coeff / (2 * l_idx + 1)
            alpha[l_idx] = math.exp(float(c_tr @ self.log_alpha_cgs[sl_tr, sl_tm, l_idx + ioff] @ c_tm))

        dalpha = alpha - alpha_eq
        r2p2s = math.exp(float(c_tr @ self.log_r2p2s[sl_tr]))
        return alpha, dalpha, beta, r2p2s

    def swift_correction(
        self,
        tr_k: float,
        *,
        omega_bh2: float = 0.02242,
        y_he: float = 0.245,
        t_cmb0: float = 2.7255,
    ) -> float:
        """Linearly interpolate SWIFT relative Lyman-alpha escape factor delta(T_r)."""
        if tr_k <= self.swift_tr_k[0] or tr_k >= self.swift_tr_k[-1]:
            return 0.0
        idx = int(np.searchsorted(self.swift_tr_k, tr_k)) - 1
        t0 = float(self.swift_tr_k[idx])
        t1 = float(self.swift_tr_k[idx + 1])
        w = (tr_k - t0) / max(t1 - t0, 1e-30)
        row = (1.0 - w) * self.swift_delta[idx] + w * self.swift_delta[idx + 1]
        # Perturbations around SWIFT Planck fiducial (0.02242, 0.245, 2.7255)
        delta = (
            float(row[0])
            + float(row[1]) * (omega_bh2 - 0.02242)
            + float(row[2]) * (y_he - 0.245)
            + float(row[3]) * (t_cmb0 - 2.7255)
        )
        return delta


def load_hyrec_atomic_tables(
    atomic_dir: Path | str = DEFAULT_ATOMIC_DIR,
    *,
    verify_sha256: bool = True,
) -> HyRecAtomicTables:
    """Load and SHA-256 verify recovered HYREC-2 atomic tables."""
    base = Path(atomic_dir)
    manifest: dict[str, str] = {}
    for fname, expected in HYREC_EXPECTED_SHA256.items():
        fpath = base / fname
        if not fpath.is_file():
            raise FileNotFoundError(f"missing recovered HYREC atomic file: {fpath}")
        digest = _sha256_file(fpath)
        if verify_sha256 and digest != expected:
            raise ValueError(f"SHA-256 mismatch for {fname}: got {digest}, expected {expected}")
        manifest[fname] = digest

    alpha_raw = np.loadtxt(base / "Alpha_inf.dat", dtype=np.float64)
    if alpha_raw.shape != (HYREC_NTR * HYREC_NTM, 4):
        raise ValueError(f"unexpected Alpha_inf.dat shape {alpha_raw.shape}")
    log_alpha = np.log(np.maximum(alpha_raw.reshape(HYREC_NTR, HYREC_NTM, 4), 1e-300))

    r_raw = np.loadtxt(base / "R_inf.dat", dtype=np.float64)
    if r_raw.shape != (HYREC_NTR,):
        raise ValueError(f"unexpected R_inf.dat shape {r_raw.shape}")
    log_r = np.log(np.maximum(r_raw, 1e-300))

    swift_raw = np.loadtxt(base / "fit_swift.dat", dtype=np.float64)
    if swift_raw.ndim != 2 or swift_raw.shape[1] != 5 or np.any(np.diff(swift_raw[:, 0]) <= 0.0):
        raise ValueError("fit_swift.dat must have increasing T_r[K] and 5 columns")

    two_photon_raw = np.loadtxt(base / "two_photon_tables.dat", dtype=np.float64)
    return HyRecAtomicTables(
        log_alpha_cgs=log_alpha,
        log_r2p2s=log_r,
        swift_tr_k=swift_raw[:, 0].copy(),
        swift_delta=swift_raw[:, 1:5].copy(),
        two_photon_raw=two_photon_raw,
        sha256_manifest=manifest,
    )


@dataclass(frozen=True)
class TiltedRecombinationChannels:
    """Four explicitly separated physical kinematic channels for recombination & cooling.

    Attributes:
        reaction_clock_rate_s: dN / d tau_b = Gamma_b * H_n [s^-1].
        proper_hydrogen_density_cm3: baryon rest-frame density n_{H,rest} = N_H / (Gamma_b a^3) [cm^-3].
        lya_escape_expansion_s: effective isotropic/anisotropic Sobolev expansion H_esc [s^-1].
        matter_expansion_rate_s: isotropic baryon velocity-divergence rate Theta_b / 3 [s^-1].
        gamma_baryon: Lorentz factor 1 / sqrt(1 - |v_b|^2) >= 1.
        tr_baryon_k: radiation temperature seen in baryon rest frame [K].
    """

    reaction_clock_rate_s: float
    proper_hydrogen_density_cm3: float
    lya_escape_expansion_s: float
    matter_expansion_rate_s: float
    gamma_baryon: float = 1.0
    tr_baryon_k: float = 2.7255

    def __post_init__(self) -> None:
        if self.reaction_clock_rate_s <= 0.0 or not math.isfinite(self.reaction_clock_rate_s):
            raise ValueError("reaction_clock_rate_s must be finite and positive")
        if self.proper_hydrogen_density_cm3 <= 0.0 or not math.isfinite(self.proper_hydrogen_density_cm3):
            raise ValueError("proper_hydrogen_density_cm3 must be finite and positive")
        if self.lya_escape_expansion_s <= 0.0 or not math.isfinite(self.lya_escape_expansion_s):
            raise ValueError("lya_escape_expansion_s must be finite and positive")
        if not math.isfinite(self.matter_expansion_rate_s):
            raise ValueError("matter_expansion_rate_s must be finite")
        if self.gamma_baryon < 1.0 or not math.isfinite(self.gamma_baryon):
            raise ValueError("gamma_baryon must be >= 1.0")
        if self.tr_baryon_k <= 0.0 or not math.isfinite(self.tr_baryon_k):
            raise ValueError("tr_baryon_k must be positive")


def _sobolev_p_esc(tau_s: float) -> float:
    if tau_s < 1e-6:
        return 1.0 - 0.5 * tau_s + (tau_s * tau_s) / 6.0
    if tau_s > 500.0:
        return 1.0 / tau_s
    return -math.expm1(-tau_s) / tau_s


def channel_expansion_from_tilted_kinematics(
    H_n_s: float,
    v_b: Sequence[float] | np.ndarray,
    sigma_b_s: np.ndarray | None,
    theta_b_s: float | None,
    n_H_normal_cm3: float,
    x_1s: float,
    tr_normal_k: float,
    *,
    n_gl_theta: int = 8,
    baryon_radiation_temp_mode: Literal["normal", "rest_monopole"] = "normal",
) -> TiltedRecombinationChannels:
    """Build the four separate physical channels from tilted baryon kinematics and shear.

    For anisotropic baryon shear ``sigma_b_s`` (trace-free 3x3 in s^-1), computes the
    exact optical escape expansion ``H_esc`` satisfying:
      P_esc(tau_0 / (1 + sigma_{nn}/(Theta_b/3)))_S2 == P_esc(tau_0 * H_iso / H_esc).
    To leading O(sigma^2), <P_esc(n)> = P_esc(H_b) + quadratic shear corrections (zero O(sigma)).
    """
    vb = np.asarray(v_b, dtype=np.float64)
    if vb.shape != (3,) or not np.all(np.isfinite(vb)):
        raise ValueError("v_b must be finite (3,)")
    b2 = float(vb @ vb)
    if b2 >= 1.0:
        raise ValueError("|v_b| must be < 1")
    gamma = 1.0 / math.sqrt(1.0 - b2)
    clock = gamma * float(H_n_s)
    n_h_rest = float(n_H_normal_cm3) / gamma
    h_iso_b = float(H_n_s) if theta_b_s is None else float(theta_b_s) / 3.0

    # In the tilted baryon frame, isotropic dipole modulation gives <T> = Gamma T_n in photon bath
    if baryon_radiation_temp_mode == "normal":
        tr_b = float(tr_normal_k)
    elif baryon_radiation_temp_mode == "rest_monopole":
        # Boltzmann blackbody energy density rho' = Gamma^2 (1 + b^2/3) rho => T_eff = [Gamma^2(1+b^2/3)]^(1/4) T_n
        tr_b = float(tr_normal_k) * (gamma * gamma * (1.0 + b2 / 3.0)) ** 0.25
    else:
        raise ValueError(f"unknown baryon_radiation_temp_mode {baryon_radiation_temp_mode!r}")

    if sigma_b_s is None or float(np.max(np.abs(sigma_b_s))) == 0.0:
        h_esc = h_iso_b
    else:
        sig = pstf_rank2(np.asarray(sigma_b_s, dtype=np.float64))
        _, _, n_grid, w_grid = gl_sphere_grid(int(n_gl_theta))
        n_vec = n_grid.reshape(-1, 3)
        w_norm = w_grid.reshape(-1) / (4.0 * math.pi)
        # Line-of-sight velocity gradient K(n) = Theta_b/3 + sigma_{ab} n^a n^b
        k_dir = h_iso_b + np.einsum("ni,ij,nj->n", n_vec, sig, n_vec)
        k_dir = np.maximum(k_dir, 1e-30 * abs(h_iso_b))
        n1s_rest = max(n_h_rest * max(float(x_1s), 1e-12), 1e-30)
        # Dimensionless Sobolev optical depth: tau_S(n) = (A_LyA * n_{1s}) / (LYA_FACT * K(n))
        # where LYA_FACT = 8*pi/(3*lambda_alpha^3) [cm^-3] and A_LyA = 6.2649e8 [s^-1].
        num = (A_LYA_S * n1s_rest) / LYA_FACT_CGS
        tau_dir = num / k_dir
        p_avg = 0.0
        for wj, tj in zip(w_norm, tau_dir):
            p_avg += float(wj) * _sobolev_p_esc(float(tj))
        # In optically thick regime P_esc = 1/tau_S = H_esc / (n_{1s} * LYA_FACT), invert cleanly via tau_eff:
        if p_avg < 1e-6:
            tau_eff = 1.0 / max(p_avg, 1e-300)
        else:
            # Solve (1 - exp(-tau)) / tau = p_avg monotonically by Newton
            tau_eff = min(1.0 / max(p_avg, 1e-300), num / h_iso_b)
            tau_eff = max(tau_eff, 1e-8)
            for _ in range(12):
                ex = math.exp(-tau_eff)
                val = (1.0 - ex) / tau_eff - p_avg
                deriv = (tau_eff * ex - (1.0 - ex)) / (tau_eff * tau_eff)
                if abs(deriv) < 1e-300:
                    break
                tau_eff = max(1e-12, tau_eff - val / deriv)
        h_esc = num / tau_eff

    return TiltedRecombinationChannels(
        reaction_clock_rate_s=clock,
        proper_hydrogen_density_cm3=n_h_rest,
        lya_escape_expansion_s=h_esc,
        matter_expansion_rate_s=h_iso_b,
        gamma_baryon=gamma,
        tr_baryon_k=tr_b,
    )


def _helium_saha_xe(n_h_cm3: float, tr_ev: float, f_he: float) -> float:
    """Saha equilibrium electron contribution f_He * x_HeII(z) for singly-ionized Helium."""
    if f_he <= 0.0:
        return 0.0
    x_exp = -E_HE1_EV / max(tr_ev, 1e-30)
    if x_exp < -700.0:
        return 0.0
    s_he = 4.0 * SAHA_FACT_CGS * (tr_ev ** 1.5) * math.exp(x_exp) / max(n_h_cm3, 1e-30)
    if s_he > 1e12:
        return f_he
    # Solve (x_HII + f_He * y) * y / (1 - y) = s_he approximated cleanly with x_HII ~ 1 during HeII->HeI
    # Exact quadratic for f_He y^2 + (1 + s_he) y - s_he = 0
    disc = (1.0 + s_he) ** 2 + 4.0 * f_he * s_he
    y_he = (2.0 * s_he) / ((1.0 + s_he) + math.sqrt(disc))
    return f_he * y_he


def hyrec_emla_rhs_and_jacobian(
    x_hii: float,
    tm_k: float,
    channels: TiltedRecombinationChannels,
    tables: HyRecAtomicTables,
    *,
    f_he: float,
    omega_bh2: float = 0.02242,
    y_he: float = 0.245,
    t_cmb0: float = 2.7255,
    x_he_ion: float | None = None,
    use_swift: bool = True,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Compute d(x_HII, T_m)/dN, 2x2 state Jacobian, and sensitivities to the 4 channels.

    Returns:
        rhs: array ``[dx_HII/dN, dT_m/dN]``.
        jac: 2x2 Jacobian ``d(rhs)/d(x_HII, T_m)``.
        channel_tangents: dict mapping each channel name to length-2 partial derivative
          ``d(rhs)/d(channel_value)``.
    """
    n_h = channels.proper_hydrogen_density_cm3
    clock = channels.reaction_clock_rate_s
    h_esc = channels.lya_escape_expansion_s
    h_mat = channels.matter_expansion_rate_s
    tr_k = channels.tr_baryon_k

    x_he = _helium_saha_xe(n_h, KBOLTZ_EV_PER_K * tr_k, f_he) if x_he_ion is None else float(x_he_ion)
    swift_delta = tables.swift_correction(tr_k, omega_bh2=omega_bh2, y_he=y_he, t_cmb0=t_cmb0) if use_swift else 0.0

    def _eval_rhs(xh: float, tm: float, cl: float, nh: float, hesc: float, hmat: float) -> np.ndarray:
        xh_c = min(max(xh, 1e-12), 1.0 - 1e-12)
        xe = xh + x_he
        tr_ev = KBOLTZ_EV_PER_K * tr_k
        tm_ev = KBOLTZ_EV_PER_K * max(tm, 1e-6)
        alpha, dalpha, beta, r2p2s = tables.interpolate_rates(tr_ev, tm_ev)

        r_lya = LYA_FACT_CGS * hesc / (nh * (1.0 - xh_c))
        if swift_delta != 0.0:
            r_lya /= max(1.0 + swift_delta, 1e-12)

        gs = beta[0] + 3.0 * r2p2s + LAMBDA_2S1S
        gp = beta[1] + r2p2s + r_lya
        den_s = gs - 3.0 * r2p2s * r2p2s / gp
        den_p = gp - 3.0 * r2p2s * r2p2s / gs
        if abs(den_s) < 1e-300 or abs(den_p) < 1e-300:
            dx = 0.0
        else:
            c2s = (LAMBDA_2S1S + 3.0 * r2p2s * r_lya / gp) / den_s
            c2p = (r_lya + r2p2s * LAMBDA_2S1S / gs) / den_p
            s_exp = -EI_EV / tr_ev
            s_h = 0.0 if s_exp < -700.0 else SAHA_FACT_CGS * (tr_ev ** 1.5) * math.exp(s_exp) / nh
            dxe2 = xe * xh - s_h * (1.0 - xh)
            num_s = s_h * (1.0 - xh) * dalpha[0] + alpha[0] * dxe2
            num_p = s_h * (1.0 - xh) * dalpha[1] + alpha[1] * dxe2
            dx = -(nh / cl) * (num_s * c2s + num_p * c2p)

        gamma_c = 8.0 * SIGMA_T_CGS * A_RAD_CGS * (tr_k ** 4) / (3.0 * ME_CGS * C_CGS)
        compton = (gamma_c / cl) * (xe / max(1.0 + f_he + xe, 1e-30)) * (tr_k - tm)
        dtm = -2.0 * (hmat / cl) * tm + compton
        return np.array([dx, dtm], dtype=np.float64)

    base = _eval_rhs(x_hii, tm_k, clock, n_h, h_esc, h_mat)

    jac = np.zeros((2, 2), dtype=np.float64)
    hx = max(1e-7 * max(abs(x_hii), 1e-4), 1e-10)
    xp = min(x_hii + hx, 1.0 - 1e-13)
    xm = max(x_hii - hx, 1e-13)
    jac[:, 0] = (_eval_rhs(xp, tm_k, clock, n_h, h_esc, h_mat) - _eval_rhs(xm, tm_k, clock, n_h, h_esc, h_mat)) / max(xp - xm, 1e-15)

    ht = max(1e-6 * max(abs(tm_k), 1.0), 1e-6)
    jac[:, 1] = (_eval_rhs(x_hii, tm_k + ht, clock, n_h, h_esc, h_mat) - _eval_rhs(x_hii, max(tm_k - ht, 1e-6), clock, n_h, h_esc, h_mat)) / (
        tm_k + ht - max(tm_k - ht, 1e-6)
    )

    tangents: dict[str, np.ndarray] = {}
    # Exact analytical partials wrt clock and h_mat (exact scaling 1/clock and linear in h_mat)
    tangents["reaction_clock_rate_s"] = -base / clock
    tangents["matter_expansion_rate_s"] = np.array([0.0, -2.0 * tm_k / clock], dtype=np.float64)
    # Centered FD for n_h and h_esc (incorporates nonlinear C_{2s}, C_{2p} and Saha dependencies)
    dn = 1e-6 * n_h
    tangents["proper_hydrogen_density_cm3"] = (
        _eval_rhs(x_hii, tm_k, clock, n_h + dn, h_esc, h_mat) - _eval_rhs(x_hii, tm_k, clock, n_h - dn, h_esc, h_mat)
    ) / (2.0 * dn)
    de = 1e-6 * h_esc
    tangents["lya_escape_expansion_s"] = (
        _eval_rhs(x_hii, tm_k, clock, n_h, h_esc + de, h_mat) - _eval_rhs(x_hii, tm_k, clock, n_h, h_esc - de, h_mat)
    ) / (2.0 * de)

    return base, jac, tangents


@dataclass(frozen=True)
class TiltedHyrecHistory:
    """Integrated recombination + optional reionization history with four-channel separation."""

    z_grid: np.ndarray  # ascending or evaluation order
    N_grid: np.ndarray
    x_HII: np.ndarray
    x_e: np.ndarray
    T_m_K: np.ndarray
    H_n_s: np.ndarray
    gamma_baryon: np.ndarray
    tau_dot_conformal_Mpc: np.ndarray
    opacity_per_efold: np.ndarray
    kappa: np.ndarray
    visibility: np.ndarray
    channel_mode: str
    tables_sha256: dict[str, str]


def _default_reion_xe(z: np.ndarray, f_he: float, params: ReionizationParameters) -> np.ndarray:
    """Smooth tanh reionization floor identical in form to bass.recombination.reionization."""
    zp1 = 1.0 + z
    arg_h = (zp1 ** 1.5 - (1.0 + params.z_reion_H) ** 1.5) / (1.5 * math.sqrt(1.0 + params.z_reion_H) * params.delta_z_H)
    f_h = (1.0 + f_he) * 0.5 * (1.0 - np.tanh(np.clip(arg_h, -40.0, 40.0)))
    if not params.include_HeII:
        return f_h
    arg_he2 = (zp1 ** 1.5 - (1.0 + params.z_reion_HeII) ** 1.5) / (
        1.5 * math.sqrt(1.0 + params.z_reion_HeII) * params.delta_z_HeII
    )
    f_he2 = f_he * 0.5 * (1.0 - np.tanh(np.clip(arg_he2, -40.0, 40.0)))
    return f_h + f_he2


def integrate_tilted_recombination(
    z_eval: Sequence[float] | np.ndarray,
    *,
    h: float = 0.6735837,
    t_cmb0: float = 2.72548,
    omega_b: float = 0.0494142797907188,
    omega_m: float = 0.313841,
    omega_r: float = 9.220339e-5,
    omega_lambda: float = 0.686067,
    y_he: float = 0.245,
    n_h0_m3: float | None = None,
    H_n_fn=None,
    v_b_fn=None,
    sigma_b_fn=None,
    theta_b_fn=None,
    tables: HyRecAtomicTables | None = None,
    reionization: ReionizationParameters | None = None,
    mode: Literal["tilted_physical", "forbidden_global_gamma_H"] = "tilted_physical",
    baryon_radiation_temp_mode: Literal["normal", "rest_monopole"] = "normal",
    rtol: float = 1e-9,
    atol: float = 1e-12,
) -> TiltedHyrecHistory:
    """Integrate coupled HYREC-2 (x_HII, T_m) along N = -ln(1+z) over arbitrary z_eval.

    Uses Radau with analytic/table Jacobian across the recombination epoch, supporting
    arbitrarily prescribed background expansion ``H_n_fn(N)``, baryon tilt ``v_b_fn(N)``,
    and baryon shear/expansion ``sigma_b_fn(N), theta_b_fn(N)``.
    """
    tbl = load_hyrec_atomic_tables() if tables is None else tables
    zs = np.asarray(z_eval, dtype=np.float64)
    if zs.ndim != 1 or np.any(zs < 0.0) or not np.all(np.isfinite(zs)):
        raise ValueError("z_eval must be a finite non-negative 1D array")
    # Sort descending in z (ascending in e-fold N = -ln(1+z)) for causal forward time evolution
    sort_order = np.argsort(-zs, kind="mergesort")
    z_desc = zs[sort_order]
    N_asc = -np.log1p(z_desc)

    h0_s = float(h) * 100.0 * 1e5 / MPC_CM  # 100 km/s/Mpc = 1e7 cm/s/Mpc; h*1e7/MPC_CM
    rho_crit_cgs = 3.0 * h0_s * h0_s / (8.0 * math.pi * G_CGS)
    if n_h0_m3 is None:
        n_h0_cm3 = (1.0 - float(y_he)) * float(omega_b) * rho_crit_cgs / M_PROTON_G
        n_h0_m3_val = n_h0_cm3 * 1e6
    else:
        n_h0_m3_val = float(n_h0_m3)
        n_h0_cm3 = n_h0_m3_val * 1e-6

    omega_bh2 = float(omega_b) * float(h) * float(h)
    f_he = float(y_he) / (4.0 * (1.0 - float(y_he)))

    def _H_normal(N_val: float) -> float:
        if H_n_fn is not None:
            return float(H_n_fn(float(N_val)))
        a = math.exp(float(N_val))
        return h0_s * math.sqrt(max(float(omega_r) / (a ** 4) + float(omega_m) / (a ** 3) + float(omega_lambda), 1e-30))

    def _channels_at(N_val: float, x_hii: float) -> TiltedRecombinationChannels:
        z_v = math.exp(-float(N_val)) - 1.0
        a = math.exp(float(N_val))
        H_n = _H_normal(N_val)
        n_h_norm = n_h0_cm3 / (a ** 3)
        tr_norm = float(t_cmb0) * (1.0 + z_v)
        vb = np.zeros(3, dtype=np.float64) if v_b_fn is None else np.asarray(v_b_fn(float(N_val)), dtype=np.float64)
        sig = None if sigma_b_fn is None else np.asarray(sigma_b_fn(float(N_val)), dtype=np.float64)
        th = None if theta_b_fn is None else float(theta_b_fn(float(N_val)))
        ch = channel_expansion_from_tilted_kinematics(
            H_n, vb, sig, th, n_h_norm, max(1.0 - x_hii, 1e-12), tr_norm,
            baryon_radiation_temp_mode=baryon_radiation_temp_mode,
        )
        if mode == "tilted_physical":
            return ch
        if mode == "forbidden_global_gamma_H":
            # Anti-pattern control: keeps n_H unboosted and overwrites ALL expansion rates with Gamma*H_n
            return TiltedRecombinationChannels(
                reaction_clock_rate_s=ch.reaction_clock_rate_s,
                proper_hydrogen_density_cm3=n_h_norm,
                lya_escape_expansion_s=ch.reaction_clock_rate_s,
                matter_expansion_rate_s=ch.reaction_clock_rate_s,
                gamma_baryon=ch.gamma_baryon,
                tr_baryon_k=ch.tr_baryon_k,
            )
        raise ValueError(f"unknown channel mode {mode!r}")

    z_start = max(1650.0, float(z_desc[0]) + 50.0)
    N_start = -math.log1p(z_start)
    # Initialize in Hydrogen Saha equilibrium at z_start
    n_h_i = n_h0_cm3 * ((1.0 + z_start) ** 3)
    tr_ev_i = KBOLTZ_EV_PER_K * float(t_cmb0) * (1.0 + z_start)
    s_i = SAHA_FACT_CGS * (tr_ev_i ** 1.5) * math.exp(-EI_EV / tr_ev_i) / n_h_i
    x_hii_0 = 1.0 if s_i > 1e10 else 0.5 * (-s_i + math.sqrt(s_i * s_i + 4.0 * s_i))
    y0 = np.array([x_hii_0, float(t_cmb0) * (1.0 + z_start)], dtype=np.float64)

    def ode_rhs(N_val: float, y: np.ndarray) -> np.ndarray:
        ch = _channels_at(N_val, float(y[0]))
        rhs_vec, _, _ = hyrec_emla_rhs_and_jacobian(
            float(y[0]), float(y[1]), ch, tbl, f_he=f_he, omega_bh2=omega_bh2, y_he=float(y_he), t_cmb0=float(t_cmb0)
        )
        return rhs_vec

    def ode_jac(N_val: float, y: np.ndarray) -> np.ndarray:
        ch = _channels_at(N_val, float(y[0]))
        _, jac_mat, _ = hyrec_emla_rhs_and_jacobian(
            float(y[0]), float(y[1]), ch, tbl, f_he=f_he, omega_bh2=omega_bh2, y_he=float(y_he), t_cmb0=float(t_cmb0)
        )
        return jac_mat

    sol = solve_ivp(
        ode_rhs,
        (N_start, float(N_asc[-1])),
        y0,
        method="Radau",
        jac=ode_jac,
        t_eval=N_asc,
        rtol=float(rtol),
        atol=float(atol),
    )
    if not sol.success:
        raise RuntimeError(f"HYREC tilted recombination Radau solver failed: {sol.message}")

    x_hii_asc = np.clip(sol.y[0], 0.0, 1.0)
    tm_asc = np.maximum(sol.y[1], 1e-6)
    x_he_asc = np.array(
        [_helium_saha_xe(_channels_at(Nv, float(xh)).proper_hydrogen_density_cm3, KBOLTZ_EV_PER_K * float(t_cmb0) * (1.0 + zv), f_he) for Nv, zv, xh in zip(N_asc, z_desc, x_hii_asc)],
        dtype=np.float64,
    )
    xe_asc = x_hii_asc + x_he_asc
    if reionization is not None:
        xe_re = _default_reion_xe(z_desc, f_he, reionization)
        # Apply tanh reionization only at z < z_reion + 6 * delta_z so early epoch stays untouched
        z_cut = reionization.z_reion_H + 8.0 * reionization.delta_z_H
        xe_asc = np.where(z_desc < z_cut, np.maximum(xe_asc, xe_re), xe_asc)

    H_n_arr = np.array([_H_normal(Nv) for Nv in N_asc], dtype=np.float64)
    gam_arr = np.array([_channels_at(Nv, float(xh)).gamma_baryon for Nv, xh in zip(N_asc, x_hii_asc)], dtype=np.float64)
    n_h_rest_arr = np.array([_channels_at(Nv, float(xh)).proper_hydrogen_density_cm3 for Nv, xh in zip(N_asc, x_hii_asc)], dtype=np.float64)

    # Proper Thomson opacity per e-fold d tau_0 / dN along normal frame: Gamma_b^-1 n_{e,rest} sigma_T c / H_n
    # Wait: in rest_time tau_0 = int sigma_T c n_{e,rest} dt_n = int (sigma_T c N_H/(Gamma a^3) xe / H_n) dN;
    # at normal frame: d tau / dN = n_e_normal * sigma_T * c / H_n = n_{H,rest}*Gamma * xe * sigma_T * c / H_n!
    # Conformal d tau / d chi [Mpc^-1] in normal frame uses n_e_normal * sigma_T * a * MPC_M:
    mpc_m = MPC_CM / 100.0
    n_e_normal_m3 = (n_h_rest_arr * 1e6) * gam_arr * xe_asc
    tau_dot_mpc = n_e_normal_m3 * SIGMA_T / (1.0 + z_desc) * mpc_m
    op_per_efold = n_e_normal_m3 * SIGMA_T * C_LIGHT / np.maximum(H_n_arr, 1e-300)

    # Forward optical depth from observer (z_desc[-1]) integrated upward via trapezoid rule on op_per_efold dN
    kappa_asc = np.zeros_like(N_asc)
    for k in range(len(N_asc) - 2, -1, -1):
        dN = float(N_asc[k + 1] - N_asc[k])
        kappa_asc[k] = kappa_asc[k + 1] + 0.5 * (op_per_efold[k] + op_per_efold[k + 1]) * dN
    vis_asc = op_per_efold * np.exp(-kappa_asc)

    # Restore exact requested z_eval ordering
    inv_perm = np.empty_like(sort_order)
    inv_perm[sort_order] = np.arange(len(zs))
    return TiltedHyrecHistory(
        z_grid=z_desc[inv_perm],
        N_grid=N_asc[inv_perm],
        x_HII=x_hii_asc[inv_perm],
        x_e=xe_asc[inv_perm],
        T_m_K=tm_asc[inv_perm],
        H_n_s=H_n_arr[inv_perm],
        gamma_baryon=gam_arr[inv_perm],
        tau_dot_conformal_Mpc=tau_dot_mpc[inv_perm],
        opacity_per_efold=op_per_efold[inv_perm],
        kappa=kappa_asc[inv_perm],
        visibility=vis_asc[inv_perm],
        channel_mode=mode,
        tables_sha256=dict(tbl.sha256_manifest),
    )


def compare_against_forbidden_global_gamma_H(
    z_eval: Sequence[float] | np.ndarray,
    *,
    beta_const: Sequence[float] | np.ndarray,
    **kwargs,
) -> dict[str, object]:
    """Compare physical 4-channel recombination vs forbidden global H -> Gamma * H."""
    b = np.asarray(beta_const, dtype=np.float64)
    v_fn = lambda _N: b
    phys = integrate_tilted_recombination(z_eval, v_b_fn=v_fn, mode="tilted_physical", **kwargs)
    forb = integrate_tilted_recombination(z_eval, v_b_fn=v_fn, mode="forbidden_global_gamma_H", **kwargs)
    flrw = integrate_tilted_recombination(z_eval, v_b_fn=None, mode="tilted_physical", **kwargs)
    rel_phys_vs_forb = np.abs(phys.x_e - forb.x_e) / np.maximum(phys.x_e, 1e-12)
    rel_phys_vs_flrw = np.abs(phys.x_e - flrw.x_e) / np.maximum(flrw.x_e, 1e-12)
    return {
        "beta_norm": float(np.linalg.norm(b)),
        "gamma": 1.0 / math.sqrt(1.0 - float(b @ b)),
        "max_abs_xe_diff_phys_vs_forbidden": float(np.max(np.abs(phys.x_e - forb.x_e))),
        "max_rel_xe_diff_phys_vs_forbidden": float(np.max(rel_phys_vs_forb)),
        "max_rel_xe_diff_phys_vs_flrw": float(np.max(rel_phys_vs_flrw)),
        "max_abs_Tm_diff_K_phys_vs_forbidden": float(np.max(np.abs(phys.T_m_K - forb.T_m_K))),
    }


def to_clocked_chemistry_inputs(
    z_edges: Sequence[float] | np.ndarray,
    hist: TiltedHyrecHistory,
    tables: HyRecAtomicTables,
    *,
    beta_by_cell: np.ndarray,
    photon_direction_by_cell: np.ndarray,
    comoving_hydrogen_m3: float,
    y_he: float = 0.245,
) -> ChemistryHistory:
    """Adapt linearized HYREC-2 rates around a trajectory into clocked_chemistry cells."""
    z_e = np.asarray(z_edges, dtype=np.float64)
    N_edges = -np.log1p(z_e)
    if np.any(np.diff(N_edges) <= 0.0):
        raise ValueError("z_edges must be strictly decreasing so N_edges strictly increase")
    n_cells = len(N_edges) - 1
    N_mid = 0.5 * (N_edges[:-1] + N_edges[1:])
    # Interpolate baseline x_HII, T_m, H_n on ascending N_grid
    order = np.argsort(hist.N_grid)
    Ng = hist.N_grid[order]
    xh_mid = np.interp(N_mid, Ng, hist.x_HII[order])
    tm_mid = np.interp(N_mid, Ng, hist.T_m_K[order])
    hn_mid = np.interp(N_mid, Ng, hist.H_n_s[order])

    # Build 2-state [neutral, ionized] generator per cell reproducing instantaneous HYREC rates
    gens = np.zeros((n_cells, 2, 2), dtype=np.float64)
    f_he = float(y_he) / (4.0 * (1.0 - float(y_he)))
    for j in range(n_cells):
        z_m = math.expm1(-float(N_mid[j]))
        vb_j = np.asarray(beta_by_cell[j], dtype=np.float64)
        gamma_j = 1.0 / math.sqrt(1.0 - float(vb_j @ vb_j))
        nh_rest = (comoving_hydrogen_m3 * 1e-6) / (gamma_j * math.exp(3.0 * float(N_mid[j])))
        tr_k = 2.72548 * (1.0 + z_m)
        tr_ev = KBOLTZ_EV_PER_K * tr_k
        tm_ev = KBOLTZ_EV_PER_K * tm_mid[j]
        alpha, _, beta, r2p2s = tables.interpolate_rates(tr_ev, tm_ev)
        r_lya = LYA_FACT_CGS * float(hn_mid[j]) / (nh_rest * max(1.0 - xh_mid[j], 1e-12))
        gs = beta[0] + 3.0 * r2p2s + LAMBDA_2S1S
        gp = beta[1] + r2p2s + r_lya
        c2s = (LAMBDA_2S1S + 3.0 * r2p2s * r_lya / gp) / (gs - 3.0 * r2p2s * r2p2s / gp)
        c2p = (r_lya + r2p2s * LAMBDA_2S1S / gs) / (gp - 3.0 * r2p2s * r2p2s / gs)
        r_rec = nh_rest * max(xh_mid[j], 1e-12) * (alpha[0] * c2s + alpha[1] * c2p)
        s_h = SAHA_FACT_CGS * (tr_ev ** 1.5) * math.exp(-EI_EV / tr_ev) / nh_rest
        r_ion = nh_rest * s_h * (alpha[0] * c2s + alpha[1] * c2p)
        gens[j] = np.array([[-r_ion, r_rec], [r_ion, -r_rec]], dtype=np.float64)

    x0_start = float(np.interp(N_edges[0], Ng, hist.x_HII[order]))
    x0_start = min(max(x0_start, 0.0), 1.0)
    return evolve_clocked_chemistry(
        N_edges=N_edges,
        initial_population=np.array([1.0 - x0_start, x0_start], dtype=np.float64),
        electron_yield=np.array([0.0, 1.0 + f_he * 1e-12], dtype=np.float64),
        proper_generators_s=gens,
        hubble_normal_s=hn_mid,
        beta=beta_by_cell,
        photon_direction=photon_direction_by_cell,
        comoving_hydrogen_m3=comoving_hydrogen_m3,
        tangent=ChemistryTangent(),
    )
