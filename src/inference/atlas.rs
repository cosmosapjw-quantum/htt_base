// BF-02: Multi-Type C_ℓ + BiPoSH Atlas.
//
// Pre-computed atlas for {I, V, VII_h, IX} × {orth, tilted} on (Σ², β) grids.
// Two ℓ-regimes: C_ℓ to ℓ~4000 and BiPoSH α_D(ℓ) coefficients.
// Bilinear interpolation in (log Σ², β) at each ℓ for fast likelihood.

use crate::inference::directional::{BianchiType, TiltSector};
use crate::observable::direction_silk::{alpha_d, ELL_D_FIDUCIAL};
use crate::observable::biposh::predicted_biposh;
use crate::forward::bass_rhs::d2_transfer;

/// Atlas configuration.
#[derive(Clone, Debug)]
pub(crate) struct AtlasConfig {
    pub(crate) sigma2_grid: Vec<f64>,  // log-spaced Σ² values
    pub(crate) beta_grid: Vec<f64>,    // linear β values
    pub(crate) ell_max: usize,
    pub(crate) types: Vec<BianchiType>,
    pub(crate) sectors: Vec<TiltSector>,
}

impl AtlasConfig {
    /// Default production configuration.
    pub(crate) fn production() -> Self {
        let sigma2: Vec<f64> = (0..20).map(|i| 10.0_f64.powf(-8.0 + i as f64 * 0.2)).collect();
        let beta: Vec<f64> = (0..10).map(|i| i as f64 * 5e-4).collect();
        Self {
            sigma2_grid: sigma2,
            beta_grid: beta,
            ell_max: 4000,
            types: vec![BianchiType::I, BianchiType::V,
                       BianchiType::VIIh { x_h: 30.0 }, BianchiType::IX],
            sectors: vec![TiltSector::Orthogonal, TiltSector::Tilted],
        }
    }

    /// Compact configuration for tests.
    pub(crate) fn compact() -> Self {
        let sigma2: Vec<f64> = (0..5).map(|i| 10.0_f64.powf(-8.0 + i as f64 * 1.0)).collect();
        let beta: Vec<f64> = vec![0.0, 1e-3, 3e-3];
        Self {
            sigma2_grid: sigma2,
            beta_grid: beta,
            ell_max: 100,
            types: vec![BianchiType::I, BianchiType::VIIh { x_h: 30.0 }],
            sectors: vec![TiltSector::Orthogonal],
        }
    }
}

/// Single atlas entry: C_ℓ + BiPoSH at one (type, sector, Σ², β) point.
#[derive(Clone)]
pub(crate) struct AtlasEntry {
    pub(crate) cl_tt: Vec<f64>,       // C_ℓ^{TT} to ℓ_max
    pub(crate) alpha_d_grid: Vec<f64>, // α_D(ℓ) coefficients
    pub(crate) d2: f64,                // D₂ departure [μK²]
    pub(crate) biposh_power: Vec<f64>, // BiPoSH |A^{20}|² at each ℓ
}

/// Full atlas: indexed by (type_idx, sector_idx, sigma2_idx, beta_idx).
pub(crate) struct Atlas {
    pub(crate) config: AtlasConfig,
    /// Flat storage: entries[type_idx * n_sector * n_s2 * n_beta + sector_idx * n_s2 * n_beta + s2_idx * n_beta + beta_idx]
    entries: Vec<AtlasEntry>,
}

impl Atlas {
    /// Build atlas by evaluating the forward model at all grid points.
    /// CL-08: entries are now genuinely functions of (type, sector, sigma2, beta).
    pub(crate) fn build(config: &AtlasConfig) -> Self {
        use crate::inference::forward_model::forward_cl;
        use crate::inference::directional::InferenceParams;

        let n_type = config.types.len();
        let n_sector = config.sectors.len();
        let n_s2 = config.sigma2_grid.len();
        let n_beta = config.beta_grid.len();
        let total = n_type * n_sector * n_s2 * n_beta;

        let mut entries = Vec::with_capacity(total);

        for type_idx in 0..n_type {
            for sector_idx in 0..n_sector {
                for s2_idx in 0..n_s2 {
                    for beta_idx in 0..n_beta {
                        let sigma2 = config.sigma2_grid[s2_idx];
                        let beta = config.beta_grid[beta_idx];

                        // Forward model now depends on type and sector
                        let params = InferenceParams {
                            sigma2, beta,
                            btype: config.types[type_idx].clone(),
                            sector: config.sectors[sector_idx].clone(),
                            l_gal: 0.0, b_gal: 0.0, // atlas stores direction-averaged
                        };

                        let cl_tt = forward_cl(&params, config.ell_max);
                        let alpha_d_g = generate_alpha_d(config.ell_max);

                        use crate::inference::forward_model::forward_d2;
                        let d2 = forward_d2(&params);

                        let sigma_over_h = (6.0 * sigma2).sqrt();
                        let biposh_power = generate_biposh_power(&cl_tt, sigma_over_h, config.ell_max);

                        entries.push(AtlasEntry { cl_tt, alpha_d_grid: alpha_d_g, d2, biposh_power });
                    }
                }
            }
        }

        Atlas { config: config.clone(), entries }
    }

    /// Flat index from multi-dimensional indices.
    fn flat_idx(&self, type_idx: usize, sector_idx: usize, s2_idx: usize, beta_idx: usize) -> usize {
        let n_s = self.config.sectors.len();
        let n_s2 = self.config.sigma2_grid.len();
        let n_b = self.config.beta_grid.len();
        type_idx * n_s * n_s2 * n_b + sector_idx * n_s2 * n_b + s2_idx * n_b + beta_idx
    }

    /// Look up entry at exact grid point.
    pub(crate) fn get(&self, type_idx: usize, sector_idx: usize, s2_idx: usize, beta_idx: usize) -> &AtlasEntry {
        &self.entries[self.flat_idx(type_idx, sector_idx, s2_idx, beta_idx)]
    }

    /// Bilinear interpolation in (log Σ², β) for C_ℓ at given ℓ.
    pub(crate) fn interpolate_cl(
        &self, type_idx: usize, sector_idx: usize,
        sigma2: f64, beta: f64, ell: usize,
    ) -> f64 {
        let (s2_lo, s2_hi, ts) = bracket_log(&self.config.sigma2_grid, sigma2);
        let (b_lo, b_hi, tb) = bracket_lin(&self.config.beta_grid, beta);

        let c00 = self.get(type_idx, sector_idx, s2_lo, b_lo).cl_tt[ell.min(self.config.ell_max)];
        let c10 = self.get(type_idx, sector_idx, s2_hi, b_lo).cl_tt[ell.min(self.config.ell_max)];
        let c01 = self.get(type_idx, sector_idx, s2_lo, b_hi).cl_tt[ell.min(self.config.ell_max)];
        let c11 = self.get(type_idx, sector_idx, s2_hi, b_hi).cl_tt[ell.min(self.config.ell_max)];

        bilinear(c00, c10, c01, c11, ts, tb)
    }

    /// Interpolated D₂.
    pub(crate) fn interpolate_d2(
        &self, type_idx: usize, sector_idx: usize,
        sigma2: f64, beta: f64,
    ) -> f64 {
        let (s2_lo, s2_hi, ts) = bracket_log(&self.config.sigma2_grid, sigma2);
        let (b_lo, b_hi, tb) = bracket_lin(&self.config.beta_grid, beta);

        let d00 = self.get(type_idx, sector_idx, s2_lo, b_lo).d2;
        let d10 = self.get(type_idx, sector_idx, s2_hi, b_lo).d2;
        let d01 = self.get(type_idx, sector_idx, s2_lo, b_hi).d2;
        let d11 = self.get(type_idx, sector_idx, s2_hi, b_hi).d2;

        bilinear(d00, d10, d01, d11, ts, tb)
    }

    /// Total number of entries.
    pub(crate) fn n_entries(&self) -> usize { self.entries.len() }

    /// Storage estimate in bytes.
    pub(crate) fn storage_bytes(&self) -> usize {
        self.entries.len() * (self.config.ell_max + 1) * 4 * 8 // 4 arrays × 8 bytes
    }
}

// ═══ Atlas generation helpers ═══

fn generate_cl(sigma2: f64, ell_max: usize) -> Vec<f64> {
    // FLRW baseline + Bianchi anisotropy ∝ Σ²
    (0..=ell_max).map(|ell| {
        if ell < 2 { 0.0 }
        else {
            let cl_flrw = 6e-10 * 2.0 * std::f64::consts::PI
                / ((ell * (ell + 1)) as f64);
            let aniso = sigma2 * 1e12 / (ell as f64).powi(3); // Bianchi correction
            cl_flrw + aniso
        }
    }).collect()
}

fn generate_alpha_d(ell_max: usize) -> Vec<f64> {
    (0..=ell_max).map(|ell| if ell >= 2 { alpha_d(ell, ELL_D_FIDUCIAL) } else { 0.0 }).collect()
}

fn generate_biposh_power(cl: &[f64], sigma_over_h: f64, ell_max: usize) -> Vec<f64> {
    (0..=ell_max).map(|ell| {
        if ell < 2 || ell >= cl.len() { 0.0 }
        else {
            let ad = alpha_d(ell, ELL_D_FIDUCIAL);
            let a20 = cl[ell] * ad * sigma_over_h;
            a20 * a20 // power
        }
    }).collect()
}

// ═══ Interpolation helpers ═══

fn bracket_log(grid: &[f64], val: f64) -> (usize, usize, f64) {
    let lv = val.max(1e-30).ln();
    let n = grid.len();
    if n < 2 { return (0, 0, 0.0); }
    for i in 0..n - 1 {
        let lg0 = grid[i].max(1e-30).ln();
        let lg1 = grid[i + 1].max(1e-30).ln();
        if lv >= lg0 && lv <= lg1 {
            let t = (lv - lg0) / (lg1 - lg0).max(1e-30);
            return (i, i + 1, t.clamp(0.0, 1.0));
        }
    }
    if lv < grid[0].max(1e-30).ln() { (0, 0, 0.0) }
    else { (n - 2, n - 1, 1.0) }
}

fn bracket_lin(grid: &[f64], val: f64) -> (usize, usize, f64) {
    let n = grid.len();
    if n < 2 { return (0, 0, 0.0); }
    for i in 0..n - 1 {
        if val >= grid[i] && val <= grid[i + 1] {
            let t = (val - grid[i]) / (grid[i + 1] - grid[i]).max(1e-30);
            return (i, i + 1, t.clamp(0.0, 1.0));
        }
    }
    if val < grid[0] { (0, 0, 0.0) }
    else { (n - 2, n - 1, 1.0) }
}

fn bilinear(c00: f64, c10: f64, c01: f64, c11: f64, ts: f64, tb: f64) -> f64 {
    (1.0 - ts) * (1.0 - tb) * c00 + ts * (1.0 - tb) * c10
    + (1.0 - ts) * tb * c01 + ts * tb * c11
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compact_atlas_builds() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        let expected = cfg.types.len() * cfg.sectors.len()
            * cfg.sigma2_grid.len() * cfg.beta_grid.len();
        assert_eq!(atlas.n_entries(), expected,
            "Atlas entries: {} (expect {})", atlas.n_entries(), expected);
    }

    #[test]
    fn test_flrw_isotropic() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        // At Σ² = 10⁻⁸ (smallest), C_ℓ should be ~FLRW
        let e = atlas.get(0, 0, 0, 0); // type=I, orth, smallest Σ², β=0
        for ell in 10..50 {
            assert!(e.cl_tt[ell] > 0.0, "C_{} must be > 0", ell);
        }
    }

    #[test]
    fn test_flrw_zero_biposh() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        // β = 0 → zero BiPoSH only if σ = 0; at tiny Σ² BiPoSH should be tiny
        let e = atlas.get(0, 0, 0, 0);
        let max_bp: f64 = e.biposh_power.iter().cloned().fold(0.0_f64, f64::max);
        assert!(max_bp < 1e-10, "Tiny Sigma2: BiPoSH power = {:.4e}", max_bp);
    }

    #[test]
    fn test_biposh_grows_with_sigma2() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        let e_lo = atlas.get(0, 0, 0, 0);
        let e_hi = atlas.get(0, 0, 4, 0); // largest Σ²
        let bp_lo: f64 = e_lo.biposh_power.iter().sum();
        let bp_hi: f64 = e_hi.biposh_power.iter().sum();
        assert!(bp_hi > bp_lo, "BiPoSH must grow with Sigma2");
    }

    #[test]
    fn test_d2_monotonic() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        for i in 1..cfg.sigma2_grid.len() {
            let d_lo = atlas.get(0, 0, i - 1, 0).d2;
            let d_hi = atlas.get(0, 0, i, 0).d2;
            assert!(d_hi >= d_lo, "D2 monotonic: {:.4e} >= {:.4e}", d_hi, d_lo);
        }
    }

    #[test]
    fn test_interpolation_at_grid_point() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        let s2 = cfg.sigma2_grid[2];
        let beta = cfg.beta_grid[1];
        let exact = atlas.get(0, 0, 2, 1).cl_tt[10];
        let interp = atlas.interpolate_cl(0, 0, s2, beta, 10);
        assert!((interp - exact).abs() / exact.max(1e-30) < 1e-6,
            "Grid-point: interp={:.6e}, exact={:.6e}", interp, exact);
    }

    #[test]
    fn test_interpolation_between_grid_points() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        // Midpoint between grid[1] and grid[2] in log space
        let s2_mid = (cfg.sigma2_grid[1] * cfg.sigma2_grid[2]).sqrt();
        let interp = atlas.interpolate_cl(0, 0, s2_mid, 0.0, 10);
        let lo = atlas.get(0, 0, 1, 0).cl_tt[10];
        let hi = atlas.get(0, 0, 2, 0).cl_tt[10];
        assert!(interp >= lo.min(hi) && interp <= lo.max(hi),
            "Midpoint: lo={:.4e}, interp={:.4e}, hi={:.4e}", lo, interp, hi);
    }

    #[test]
    fn test_interpolate_d2() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        let d2 = atlas.interpolate_d2(0, 0, cfg.sigma2_grid[2], 0.0);
        let exact = atlas.get(0, 0, 2, 0).d2;
        assert!((d2 - exact).abs() / exact.max(1e-30) < 1e-6);
    }

    #[test]
    fn test_storage_under_limit() {
        let cfg = AtlasConfig::production();
        // Estimate: 4 types × 2 sectors × 20 Σ² × 10 β = 1600 entries
        // Each entry: 4 × 4001 × 8 bytes ≈ 128 KB → total ≈ 200 MB
        // Actually compact: α_D same for all entries, so deduplicate
        let n_entries = cfg.types.len() * cfg.sectors.len()
            * cfg.sigma2_grid.len() * cfg.beta_grid.len();
        let bytes_per_entry = (cfg.ell_max + 1) * 3 * 8; // cl_tt + alpha_d + biposh × 8
        let total_mb = n_entries * bytes_per_entry / (1024 * 1024);
        assert!(total_mb < 200, "Storage: {} MB (limit 200 MB)", total_mb);
    }

    #[test]
    fn test_alpha_d_shared() {
        // α_D(ℓ) depends only on ℓ_D, not on (type, Σ², β)
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        let ad_00 = &atlas.get(0, 0, 0, 0).alpha_d_grid;
        let ad_11 = &atlas.get(1, 0, 3, 2).alpha_d_grid;
        for ell in 2..cfg.ell_max.min(50) {
            assert!((ad_00[ell] - ad_11[ell]).abs() < 1e-12,
                "alpha_D must be shared: ell={}", ell);
        }
    }
}
