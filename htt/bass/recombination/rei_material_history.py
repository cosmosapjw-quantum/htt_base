"""Read published non-tilted REI material trajectories in its own density, clock and geometry."""
from __future__ import annotations

import gzip
import hashlib
from pathlib import Path

import numpy as np

from bass.recombination.opacity_history import OpticalCells
from bass.recombination.reionization import C_LIGHT, SIGMA_T

REI_COMMIT = "56dc609ea9b801c88d3364aed3eee140b3a20d46"
SAMPLE_PATH = ("research/rei_igm_sync_20261116/approximation_validity/incremental_fifth/"
               "results_five/fifth_abundances.csv.gz")
SAMPLE_SHA = "7aea66ecbc033e66619dc10c410161346d3f065e54c30448b4690064b74351a9"
FULL_SHA = "fb9c0821b4180bed9f65d807ddb0e8b39a6e6a35567e8f0235f611512b3c75f6"
FIVE_CASE_PATH = SAMPLE_PATH.rsplit("/", 1)[0] + "/five_case_abundances.csv.gz"
FIVE_CASE_SHA = "f4bc0046d79faf2cd13ae7ed78135503306c7d76c11580e4601a757c407bc83d"
CASE_Q = {"ZERO": 0.0, "SHEAR_HALF_PLUS": .005, "SHEAR_HALF_MINUS": -.005,
          "SHEAR_PLUS": .01, "SHEAR_MINUS": -.01}
SOURCES = {FIVE_CASE_SHA: (1001, "five_case_inspection_sample"), SAMPLE_SHA: (1001, "published_inspection_sample"),
           FULL_SHA: (312238, "full_native_normalized_history")}
MPC_CM = 3.0856775814913673e24
HELIUM_RATIO = 0.2454 / (4 * (1 - 0.2454))


def _expansion(a, q_ref=.01):
    # REI's registered axisymmetric, stress-free, non-tilted q_ref branch.
    omega_r, omega_m = 9.2e-5, 0.315
    h0 = 67.4e5 / MPC_CM
    def flrw2(scale):
        return h0**2 * (omega_r / scale**4 + omega_m / scale**3 + 1 - omega_r - omega_m)
    ref = 1 / 21
    return np.sqrt(flrw2(a) + q_ref**2 * flrw2(ref) * (ref / a)**6)


class ReiMaterialHistory:
    """Authenticated finite donor; z means mean scale-factor redshift, never ray redshift.

    The archives describe the registered finite conditional model family. The public inspection
    table is sampled, so its finite integration has an additional sampling error.
    """
    def __init__(self, path, case="SHEAR_PLUS"):
        path = Path(path)
        with path.open("rb") as stream:
            self.sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
        if self.sha256 not in SOURCES:
            raise ValueError("unrecognized REI material-history SHA-256")
        nrows, self.sampling = SOURCES[self.sha256]
        if case not in CASE_Q or (self.sha256 != FIVE_CASE_SHA and case != "SHEAR_PLUS"):
            raise ValueError("requested REI case unavailable in this material file")
        self.case, self.q_ref = case, CASE_Q[case]
        fields = ("a", "zbar", "time_s", "x_HI", "x_HII", "x_HeI", "x_HeII", "x_HeIII",
                  "xe_per_H", "temperature_K", "nH_proper_cm3", "ne_proper_cm3")
        with gzip.open(path, "rt") as stream:
            header = stream.readline().strip().split(",")
            if "b" in header:
                fields += ("b",)
            source = stream
            if self.sha256 == FIVE_CASE_SHA:
                # Case is the first field, q_ref is the second, as locked by the file SHA.
                if header[:2] != ["case", "q_ref"]:
                    raise ValueError("REI case columns changed")
                source = (line for line in stream if line.startswith(case + ","))
            data = np.loadtxt(source, delimiter=",", usecols=[header.index(k) for k in fields])
        if data.shape != (nrows, len(fields)) or not np.isfinite(data).all():
            raise ValueError("REI columns or population invalid")
        a, z, self.t, h1, h2, he1, he2, he3, xe, temp, nh, ne = data.T[:12]
        self.b = data[:, 12] if len(fields) > 12 else None
        if (np.any(np.diff(a) <= 0) or np.any(np.diff(self.t) <= 0)
                or not np.allclose(z[[0,-1]], [20,4], atol=1e-12, rtol=0)
                or not np.allclose((1 + z) * a, 1, rtol=1e-12)):
            raise ValueError("unexpected mean redshift or proper-time support")
        fractions = data[:, 3:8]
        if (np.any(fractions < -1e-14) or np.any(fractions > 1+1e-14)
                or not np.allclose(h1 + h2, 1, atol=5e-13, rtol=0)
                or not np.allclose(he1 + he2 + he3, 1, atol=5e-13, rtol=0)):
            raise ValueError("nonconserving REI material state")
        self.charge_error = float(np.max(np.abs(xe - (h2 + HELIUM_RATIO * (he2 + 2 * he3)))))
        # Published inspection columns were resampled separately by the donor.
        # Its product nH*xe differs from its interpolated ne at order 1e-9.
        self.relative_density_error = float(np.max(np.abs(nh * xe / ne - 1)))
        density_rtol = 1e-8 if self.sha256 in (SAMPLE_SHA, FIVE_CASE_SHA) else 5e-13
        if (self.charge_error > 5e-13 or np.any(temp <= 0) or np.any(nh <= 0)
                or self.relative_density_error > density_rtol):
            raise ValueError("inconsistent REI thermodynamic state or charge")
        self.nh0 = float(nh[0] * a[0]**3)
        if not np.allclose(nh * a**3, self.nh0, rtol=density_rtol, atol=0):
            raise ValueError("donor proper H density violates conserved nucleus current")
        if self.b is not None:
            self.b.setflags(write=False)
        self.z = z
        self.N = -np.log1p(z)
        self.material = np.stack((h2, he2, he3, temp))
        self.ne = ne
        self.q = self._rate(a, h2 + HELIUM_RATIO * (he2 + 2 * he3))
        self.xe_nodes = h2 + HELIUM_RATIO * (he2 + 2 * he3)
        for array in (self.z, self.N, self.t, self.material, self.ne, self.q, self.xe_nodes):
            array.setflags(write=False)

    def _rate(self, a, xe):
        return C_LIGHT * SIGMA_T * 1e6 * (self.nh0 / a**3) * xe / _expansion(a, self.q_ref)

    def rate(self, N):
        n = np.asarray(N, dtype=float)
        if not np.isfinite(n).all() or np.any(n < self.N[0]) or np.any(n > self.N[-1]):
            raise ValueError("query outside finite REI history")
        return self._rate(np.exp(n), np.interp(n, self.N, self.xe_nodes))

    def cells(self, edges):
        """Integrate positive material charge and its analytic donor clock, split at every knot."""
        e = np.asarray(edges, dtype=float)
        if (e.ndim != 1 or len(e) < 2 or not np.isfinite(e).all() or np.any(np.diff(e) <= 0)
                or e[0] < self.N[0] or e[-1] > self.N[-1]):
            raise ValueError("invalid edges for REI opacity support")
        cuts = np.union1d(e, self.N[(self.N > e[0]) & (self.N < e[-1])])
        h = np.diff(cuts) / 2
        mid = cuts[:-1] + h
        offset = np.sqrt(3 / 5) * h
        depth = h * (5 * self.rate(mid - offset) + 8 * self.rate(mid) + 5 * self.rate(mid + offset)) / 9
        dtau = np.add.reduceat(depth, np.searchsorted(cuts, e[:-1]))
        tau = np.r_[np.cumsum(dtau[::-1])[::-1], 0.]
        return OpticalCells(dtau, tau, np.exp(-tau[1:]) * (-np.expm1(-dtau)))

    def observer_rays(self, observer_z_mean=4.0):
        """Trace finite-interval normal-observer rays in the archived LRS-I metric."""
        from bass.recombination.rei_observer_rays import ReiObserverRays
        if self.b is None:
            raise ValueError("directional rays require a material history with archived metric b")
        return ReiObserverRays(self, observer_z_mean)

    def evaluate(self, z_eval):
        """Evaluate source densities and exact sampled-opacity cell integrals on a finite window.

        Interpolate fractions linearly in N; integrate the corresponding physical opacity
        over each source piece with 3-point Gauss quadrature. Preserve the unobserved z<4 gap.
        """
        from bass.recombination.tilted_hyrec import TiltedHyrecHistory

        z = np.asarray(z_eval, dtype=float)
        if (z.ndim != 1 or z.size < 2 or not np.isfinite(z).all()
                or np.any(z < self.z[-1]) or np.any(z > self.z[0]) or len(np.unique(z)) != len(z)):
            raise ValueError("require unique evaluation redshifts inside the finite REI interval [4, 20]")
        N = -np.log1p(z)
        h2, he2, he3, temp = [np.interp(N, self.N, y) for y in self.material]
        xe = h2 + HELIUM_RATIO * (he2 + 2 * he3)
        a = 1 / (1 + z)
        H = _expansion(a, self.q_ref)
        q = self.rate(N)
        order = np.argsort(N)
        kappa = np.empty_like(z)
        kappa[order] = self.cells(N[order]).tau_to_observer
        # The same interpolated rate determines conformal opacity: dτ/dχ = (a H / c)dτ/dN.
        tau_dot_mpc = q * a * H * (MPC_CM / 100) / C_LIGHT
        return TiltedHyrecHistory(
            z_grid=z.copy(), N_grid=N, x_HII=h2, x_e=xe, T_m_K=temp, H_n_s=H,
            gamma_baryon=np.ones_like(z), tau_dot_conformal_Mpc=tau_dot_mpc, opacity_per_efold=q,
            kappa=kappa, visibility=q*np.exp(-kappa), channel_mode=f"prescribed_non_tilted_REI_{self.case}",
            tables_sha256={"rei_native_material": self.sha256}, rei_opacity_source=self,
        )
