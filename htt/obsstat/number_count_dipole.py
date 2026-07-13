"""Number-count dipole projection + in-house LambdaCDM clustering mocks (REV-R198).

The rev-r193 EXT-DESI lane measured the window-corrected DESI DR1 BGS number-count
dipole D = 3 <delta n_hat>_R but could only report it as a diagnostic: at BGS
depths the dipole MIXES the local large-scale-structure (clustering) dipole with
the kinematic dipole, and its significance needed release-matched mocks. This
module supplies the in-house physical mock (the rev-r197 pattern applied to the
DESI dipole):

1. The exact ell=1 angular-power projection of the observed dN/dz,
       C_ell = (2/pi) int dk k^2 P(k) W_ell(k)^2 ,
       W_ell(k) = int dz phi(z) b D(z) j_ell(k chi(z)) ,
   gives the LambdaCDM clustering dipole cosmic variance (chi, D from the
   fiducial cosmology; phi = normalised dN/dz; b the linear bias).
2. Gaussian-random-field sky maps with those C_ell, masked to the real BGS
   footprint and Poisson-sampled at the random-encoded selection, are pushed
   through the IDENTICAL dipole estimator -> the LambdaCDM null distribution of
   |D|, folding in the clustering cosmic variance + shot noise + mask coupling.
3. The analytic shot-noise floor Var_shot(D) separates the shot-noise from the
   clustering contribution.

Model-independent kinematic descriptor; a consistency test of the observed
dipole against LambdaCDM clustering, NOT a clean kinematic signal (BGS is low-z);
no anisotropy, geometry, family, or observer-frame claim.
"""
from __future__ import annotations

import numpy as np

C_KMS = 299792.458


def _trapz(y, x, axis=-1):
    f = np.trapz if hasattr(np, "trapz") else np.trapezoid
    return f(y, x, axis=axis)


def comoving_distance_hmpc(z, om):
    """Comoving distance chi(z) in Mpc/h (flat LambdaCDM, fiducial Omega_m)."""
    zg = np.linspace(0.0, float(z), 256)
    e = np.sqrt(om * (1.0 + zg) ** 3 + (1.0 - om))
    return (C_KMS / 100.0) * _trapz(1.0 / e, zg)


def growth_factor(z, om):
    """Unnormalised linear growth D(z) (flat LambdaCDM)."""
    a = np.linspace(1e-4, 1.0 / (1.0 + float(z)), 400)
    ez = np.sqrt(om * (1.0 + z) ** 3 + (1.0 - om))
    integ = _trapz(1.0 / (a * np.sqrt(om / a ** 3 + (1.0 - om))) ** 3, a)
    return 2.5 * om * ez * integ


def angular_power_projection(phi_z, z_grid, pk, om, h, bias, lmax, *,
                             kmin=2e-4, kmax=0.5, nk=600):
    """C_ell (ell=1..lmax) from the exact projection of dN/dz phi_z over z_grid."""
    from scipy.special import spherical_jn
    z_grid = np.asarray(z_grid, float)
    phi = np.asarray(phi_z, float)
    phi = phi / _trapz(phi, z_grid)
    chi = np.array([comoving_distance_hmpc(z, om) for z in z_grid])
    d0 = growth_factor(0.0, om)
    dz = np.array([growth_factor(z, om) / d0 for z in z_grid])
    wz = phi * bias * dz
    k = np.geomspace(kmin, kmax, nk)
    pkv = pk(k)
    Cl = np.zeros(lmax + 1)
    for ell in range(1, lmax + 1):
        jl = spherical_jn(ell, np.outer(k, chi))            # (nk, nz)
        Wl = _trapz(jl * wz[None, :], z_grid, axis=1)
        Cl[ell] = (2.0 / np.pi) * _trapz(k ** 2 * pkv * Wl ** 2, k)
    return Cl, chi


def synfast_seeded(Cl, nside, rng, lmax):
    """Deterministic GRF map from C_ell using an explicit RNG (byte-stable)."""
    import healpy as hp
    size = hp.Alm.getsize(lmax)
    alm = np.zeros(size, complex)
    for ell in range(1, lmax + 1):
        s = np.sqrt(max(Cl[ell], 0.0))
        alm[hp.Alm.getidx(lmax, ell, 0)] = rng.standard_normal() * s
        for m in range(1, ell + 1):
            re = rng.standard_normal() * s / np.sqrt(2.0)
            im = rng.standard_normal() * s / np.sqrt(2.0)
            alm[hp.Alm.getidx(lmax, ell, m)] = re + 1j * im
    return hp.alm2map(alm, nside, lmax=lmax, verbose=False) \
        if "verbose" in hp.alm2map.__code__.co_varnames \
        else hp.alm2map(alm, nside, lmax=lmax)


def dipole_from_delta(delta_per_cap, Rp_per_cap, vec):
    """D = 3 <delta n_hat>_R over the (masked) caps."""
    num = np.zeros(3)
    den = 0.0
    for cap in delta_per_cap:
        Rp = Rp_per_cap[cap]
        mask = Rp > 0
        w = Rp * delta_per_cap[cap]
        num += (w[mask][None, :] * vec[:, mask]).sum(axis=1)
        den += Rp[mask].sum()
    return 3.0 * num / den


def shot_noise_sigma(Rp_per_cap, alpha_per_cap, vec):
    """Analytic per-component shot-noise sigma of D (Var(delta_pix)=1/(alpha Rp))."""
    var_num = np.zeros(3)
    den = 0.0
    for cap in Rp_per_cap:
        Rp = Rp_per_cap[cap]
        a = alpha_per_cap[cap]
        mask = Rp > 0
        var_num += ((Rp[mask] / a)[None, :] * vec[:, mask] ** 2).sum(axis=1)
        den += Rp[mask].sum()
    return 3.0 * np.sqrt(var_num) / den


def mock_dipole_amplitudes(Cl, Rp_per_cap, alpha_per_cap, vec, nside, n_mock,
                           seed, lmax):
    """|D| for n_mock LambdaCDM clustering + Poisson-shot mocks on the footprint."""
    rng = np.random.default_rng(seed)
    npix = vec.shape[1]
    amps = np.empty(n_mock)
    for i in range(n_mock):
        dmap = synfast_seeded(Cl, nside, rng, lmax)
        delta = {}
        for cap in Rp_per_cap:
            Rp = Rp_per_cap[cap]
            a = alpha_per_cap[cap]
            mask = Rp > 0
            lam = np.clip(a * Rp * (1.0 + dmap), 0.0, None)
            counts = rng.poisson(lam)
            dd = np.zeros(npix)
            dd[mask] = (counts[mask] - a * Rp[mask]) / (a * Rp[mask])
            delta[cap] = dd
        amps[i] = float(np.linalg.norm(dipole_from_delta(delta, Rp_per_cap, vec)))
    return amps
