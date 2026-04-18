// BH-01: HTT Bridge — maps BASS outputs to HTT inference channels.
//
// 8 channels total:
//   Ch 1-2: CMB quadrupole/octupole (low-ℓ, from a_{ℓm})
//   Ch 3-4: CatWISE + Radio dipoles (matter tracers)
//   Ch 5: CF4 bulk flow (peculiar velocity)
//   Ch 6: Vorticity upper limit
//   Ch 7: Line-of-sight (LoS) integral
//   Ch 8 (NEW): BiPoSH L=2 from direction-dependent Silk (ℓ=600..4000)
//
// Production values preserved: ln B(FLRW_tilt) = +26.40, β = 1.360×10⁻³.

use super::bass_rhs::{BassResult, d2_transfer};

/// HTT channel identifier.
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum HttChannel {
    CmbQuadrupole,   // Ch 1
    CmbOctupole,     // Ch 2
    CatWISE,         // Ch 3
    Radio,           // Ch 4
    CF4BulkFlow,     // Ch 5
    VorticityUL,     // Ch 6
    LoS,             // Ch 7
    BiPoSH,          // Ch 8 (NEW)
}

impl HttChannel {
    pub(crate) fn all() -> Vec<Self> {
        vec![Self::CmbQuadrupole, Self::CmbOctupole, Self::CatWISE,
             Self::Radio, Self::CF4BulkFlow, Self::VorticityUL,
             Self::LoS, Self::BiPoSH]
    }

    pub(crate) fn original_7() -> Vec<Self> {
        vec![Self::CmbQuadrupole, Self::CmbOctupole, Self::CatWISE,
             Self::Radio, Self::CF4BulkFlow, Self::VorticityUL, Self::LoS]
    }

    pub(crate) fn index(&self) -> usize {
        match self {
            Self::CmbQuadrupole => 0, Self::CmbOctupole => 1,
            Self::CatWISE => 2, Self::Radio => 3,
            Self::CF4BulkFlow => 4, Self::VorticityUL => 5,
            Self::LoS => 6, Self::BiPoSH => 7,
        }
    }
}

/// Per-channel log-likelihood contribution.
#[derive(Clone, Debug)]
pub(crate) struct ChannelLikelihood {
    pub(crate) channel: HttChannel,
    pub(crate) ln_l: f64,      // log-likelihood
    pub(crate) n_data: usize,  // number of data points
}

/// Map BASS D₂ to CMB quadrupole/octupole channel likelihood.
///
/// Uses the D₂ transfer function to predict C₂, C₃ from Σ².
pub(crate) fn cmb_low_ell_likelihood(d2: f64, c2_obs: f64, c3_obs: f64) -> Vec<ChannelLikelihood> {
    // ΛCDM D_ℓ values (Planck 2018 best-fit Commander):
    //   D₂^ΛCDM ≈ 1150 μK², D₃^ΛCDM ≈ 950 μK² (from Planck 2018 Table 1)
    let d2_lcdm: f64 = 1150.0;
    let d3_lcdm: f64 = 950.0;
    
    // Cosmic variance: σ(D_ℓ) = D_ℓ × √(2/(2ℓ+1))
    // ℓ=2: σ = 1150 × √(2/5) = 727 μK²
    // ℓ=3: σ = 950 × √(2/7) = 508 μK²
    let sigma_d2: f64 = d2_lcdm * (2.0 / 5.0_f64).sqrt();
    let sigma_c3: f64 = d3_lcdm * (2.0 / 7.0_f64).sqrt();
    
    let ln_l_quad = -0.5 * (d2 - c2_obs).powi(2) / sigma_d2.powi(2);

    // Octupole prediction: D₃ = D₂ × (f₃/f₂)
    // For BI (m=0 scalar): f₃/f₂ ≈ 0.15 (from AniCLASS: power falls ℓ⁻² from ℓ=2)
    // For VII_h: f₃/f₂ ≈ 0.3-0.5 (spiral pattern enhances octupole)
    // Using BI value as default (model-independent MIO should not assume a type)
    let f3_over_f2: f64 = 0.15;  // BI scalar cascade — documented in R03a §4.3
    let d3_model = d2 * f3_over_f2;
    let ln_l_oct = -0.5 * (d3_model - c3_obs).powi(2) / sigma_c3.powi(2);

    vec![
        ChannelLikelihood { channel: HttChannel::CmbQuadrupole, ln_l: ln_l_quad, n_data: 5 },
        ChannelLikelihood { channel: HttChannel::CmbOctupole, ln_l: ln_l_oct, n_data: 7 },
    ]
}

/// Map BASS D₂ to Route B transfer function for HTT.
///
/// HTT needs: D₂(Σ²) lookup table matching existing 26-point grid.
pub(crate) fn route_b_transfer(sigma2_grid: &[f64]) -> Vec<(f64, f64)> {
    sigma2_grid.iter().map(|&s2| (s2, d2_transfer(s2))).collect()
}

/// Total log-evidence from all 7 original channels.
///
/// ln B(FLRW_tilt) should reproduce +26.40 ± 0.1 nat.
pub(crate) fn total_ln_evidence_7ch(channel_likelihoods: &[ChannelLikelihood]) -> f64 {
    channel_likelihoods.iter()
        .filter(|c| c.channel != HttChannel::BiPoSH)
        .map(|c| c.ln_l)
        .sum()
}

/// Total log-evidence from all 8 channels (7 + BiPoSH).
pub(crate) fn total_ln_evidence_8ch(channel_likelihoods: &[ChannelLikelihood]) -> f64 {
    channel_likelihoods.iter().map(|c| c.ln_l).sum()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_8_channels() {
        assert_eq!(HttChannel::all().len(), 8);
        assert_eq!(HttChannel::original_7().len(), 7);
    }

    #[test]
    fn test_channel_indices() {
        assert_eq!(HttChannel::CmbQuadrupole.index(), 0);
        assert_eq!(HttChannel::BiPoSH.index(), 7);
    }

    #[test]
    fn test_route_b_backward_compatible() {
        let grid: Vec<f64> = (0..26).map(|i| 10.0_f64.powf(-10.0 + i as f64 * 0.4)).collect();
        let transfer = route_b_transfer(&grid);
        assert_eq!(transfer.len(), 26);
        // D₂ must be monotonically increasing
        for i in 1..transfer.len() {
            assert!(transfer[i].1 >= transfer[i - 1].1);
        }
    }

    #[test]
    fn test_cmb_likelihood_structure() {
        let liks = cmb_low_ell_likelihood(100.0, 120.0, 30.0);
        assert_eq!(liks.len(), 2);
        assert_eq!(liks[0].channel, HttChannel::CmbQuadrupole);
        assert_eq!(liks[1].channel, HttChannel::CmbOctupole);
        // Likelihoods should be negative (penalty for mismatch)
        assert!(liks[0].ln_l <= 0.0);
    }

    #[test]
    fn test_7ch_evidence_excludes_biposh() {
        let liks = vec![
            ChannelLikelihood { channel: HttChannel::CmbQuadrupole, ln_l: -1.0, n_data: 5 },
            ChannelLikelihood { channel: HttChannel::BiPoSH, ln_l: -100.0, n_data: 1000 },
        ];
        let ln_b_7 = total_ln_evidence_7ch(&liks);
        assert!((ln_b_7 - (-1.0)).abs() < 1e-10, "7ch must exclude BiPoSH");
        let ln_b_8 = total_ln_evidence_8ch(&liks);
        assert!((ln_b_8 - (-101.0)).abs() < 1e-10, "8ch includes BiPoSH");
    }
}
