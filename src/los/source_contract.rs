//! SourceComponents — decomposed LoS source for the C_ℓ pipeline.
//!
//! Each k-mode's LoS source is split into physically distinct terms.
//! The `total` field is the sum used in the actual LoS integration;
//! the individual fields enable per-component diagnostics.
//!
//! ## Naming convention
//!
//! The late-time metric source is named `late_metric`, NOT `isw`.
//! In the current production path this field is NONZERO: it stores the
//! effective late metric contribution used by the line-of-sight integral
//! (currently analytic Zone-A late ISW plus the ACC-01 metric term in the
//! sync/Poisson branch). The neutral name keeps the code honest while the
//! exact convention is still being audited.

/// Decomposed LoS source for a single k-mode.
#[derive(Clone, Debug)]
pub(crate) struct SourceComponents {
    /// Conformal time/distance grid [Mpc].
    pub(crate) eta: Vec<f64>,
    /// g(η) × (Θ₀ − Φ_P + Π/4): Sachs-Wolfe term.
    pub(crate) sw: Vec<f64>,
    /// −ġ × v_b / k: Doppler (IBP form, kept for diagnostics).
    pub(crate) doppler: Vec<f64>,
    /// g × v_b / k: Doppler (pre-IBP form, for j'_ℓ integration).
    /// R-NORM-02: This is physically exact and numerically stable.
    pub(crate) doppler_preibp: Vec<f64>,
    /// e^{−τ}(...) late-metric source. Neutral naming is intentional: the
    /// precise convention mapping is still under audit, but this channel is
    /// physically the late-time metric/Weyl contribution used in production.
    pub(crate) late_metric: Vec<f64>,
    /// sw + late_metric (monopole channel, integrated with j_ℓ).
    /// Note: doppler is NOT in total — it uses j'_ℓ via doppler_preibp.
    pub(crate) total: Vec<f64>,
}

impl SourceComponents {
    /// Build from individual components.  Panics if lengths mismatch.
    pub(crate) fn new(
        eta: Vec<f64>,
        sw: Vec<f64>,
        doppler: Vec<f64>,
        late_metric: Vec<f64>,
    ) -> Self {
        let n = eta.len();
        assert_eq!(sw.len(), n);
        assert_eq!(doppler.len(), n);
        assert_eq!(late_metric.len(), n);
        // R-NORM-02: total = sw + late_metric (monopole channel, j_ℓ).
        // Doppler uses j'_ℓ channel via doppler_preibp.
        // For backward compatibility, old IBP doppler is kept in `doppler`.
        let total: Vec<f64> = (0..n)
            .map(|i| sw[i] + late_metric[i])
            .collect();
        let doppler_preibp = vec![0.0; n]; // filled by caller if using pre-IBP
        Self { eta, sw, doppler, doppler_preibp, late_metric, total }
    }

    /// Build with pre-IBP Doppler (R-NORM-02 Method 2).
    pub(crate) fn new_with_preibp(
        eta: Vec<f64>,
        sw: Vec<f64>,
        doppler_ibp: Vec<f64>,
        doppler_preibp: Vec<f64>,
        late_metric: Vec<f64>,
    ) -> Self {
        let n = eta.len();
        assert_eq!(sw.len(), n);
        assert_eq!(doppler_ibp.len(), n);
        assert_eq!(doppler_preibp.len(), n);
        assert_eq!(late_metric.len(), n);
        let total: Vec<f64> = (0..n)
            .map(|i| sw[i] + late_metric[i])
            .collect();
        Self { eta, sw, doppler: doppler_ibp, doppler_preibp, late_metric, total }
    }

    /// Identity check: |total − (sw+late_metric)| < eps at every point.
    #[cfg(test)]
    pub(crate) fn verify_identity(&self, eps: f64) -> bool {
        self.total.iter().enumerate().all(|(i, &t)| {
            let sum = self.sw[i] + self.late_metric[i];
            (t - sum).abs() < eps
        })
    }

    /// Apply a multiplicative window to ALL fields simultaneously.
    pub(crate) fn apply_window_all(&mut self, window_fn: impl Fn(usize) -> bool) {
        for i in 0..self.eta.len() {
            if !window_fn(i) {
                self.sw[i] = 0.0;
                self.doppler[i] = 0.0;
                self.doppler_preibp[i] = 0.0;
                self.late_metric[i] = 0.0;
                self.total[i] = 0.0;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_source_components_identity() {
        let n = 100;
        let eta: Vec<f64> = (0..n).map(|i| i as f64 * 0.1).collect();
        let sw: Vec<f64> = (0..n).map(|i| 0.3 * (i as f64 * 0.01).sin()).collect();
        let doppler: Vec<f64> = (0..n).map(|i| 0.1 * (i as f64 * 0.02).cos()).collect();
        let late_metric = vec![0.0; n]; // zero in current convention

        let comps = SourceComponents::new(eta, sw, doppler, late_metric);
        assert!(comps.verify_identity(1e-15), "Identity check failed");
    }

    #[test]
    fn test_no_isw_in_module() {
        // Meta-test: the word "isw" must not appear as a field name.
        // This is enforced by code review; this test documents the contract.
        let comps = SourceComponents::new(
            vec![0.0], vec![0.0], vec![0.0], vec![0.0],
        );
        // late_metric field exists, isw does not (compile-time guarantee).
        assert_eq!(comps.late_metric.len(), 1);
    }
}
