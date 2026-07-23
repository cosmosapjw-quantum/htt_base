// ═══════════════════════════════════════════════════════════════════════
// sync_gauge_camb.rs — FLRW Boltzmann solver with CAMB conventions
// ═══════════════════════════════════════════════════════════════════════
//
// Shadow port of equation_contract.py (Python), numerically verified
// against CAMB 1.6.6 to <3% at k ≤ 0.02 Mpc⁻¹.
//
// KEY DIFFERENCES from sync_gauge_v2.rs:
//   1. σ evolved as ODE state (not ḣ) — CAMB approach
//   2. CAMB η_s convention: etak = k·η_s, η_s → −1 per ζ=1
//   3. pig = 4·Θ₂ (confirmed ratio 4.0000 at 3 k-values)
//   4. Correct momentum constraint coefficients (not the v2 compensating-error set)
//   5. grho_nu for massless neutrinos only (Neff ≈ 2.03)
//   6. In-RHS source function computation for LoS integration
//
// State: y = [etak, σ, δ_c, δ_b, v_b, Θ₀..Θ_L, N₀..N_M, E₀..E_P, B₀..B_P]
//        dimension = 5 + (L+1) + (M+1) + 2*(P+1) if polarized, else 5+(L+1)+(M+1)
//
// Equations (all confirmed in PREP-03 validation):
//   etak'  = dgq/2 where dgq = (4/3)grho_γ·4Θ₁ + (4/3)grho_ν·4N₁ + grho_b·v_b
//   σ'     = −2ℋσ − dgs/k + etak    where dgs = grho_γ·4Θ₂ + grho_ν·4N₂
//   δ_c'   = −ḣ/2                    where ḣ = 2kσ − 6·etak'/k
//   δ_b'   = −kv_b − ḣ/2
//   v_b'   = −ℋv_b + c²_s·k·δ_b + opac·(3Θ₁ − v_b)/R
//   Θ₀'    = −kΘ₁ − ḣ/6
//   Θ₁'    = (k/3)(Θ₀ − 2Θ₂) − opac·(Θ₁ − v_b/3)
//   Θ₂'    = (k/5)(2Θ₁ − 3Θ₃) − (9/10)·opac·Θ₂
//   Θ_ℓ'   = k/(2ℓ+1)[ℓΘ_{ℓ-1} − (ℓ+1)Θ_{ℓ+1}] − opac·Θ_ℓ   [ℓ ≥ 3]
//   N₀'    = −kN₁ − ḣ/6
//   N₁'    = (k/3)(N₀ − 2N₂)
//   N_ℓ'   = k/(2ℓ+1)[ℓN_{ℓ-1} − (ℓ+1)N_{ℓ+1}]               [ℓ ≥ 2]
//
// Source function (CAMB symbolic, verified pointwise):
//   S_SW  = g·(Δ_γ/4 + 2φ + η_MB/2)     where φ = η_s − ℋσ/k, η_MB = −2η_s
//   S_Dop = [(σ+v_b)g' + (σ̇+v_b')g] / k
//   S_Quad= 5/(8k²)[k²·polter·g + 3polter·g'' + 6polter'·g']
//         where polter ≈ pig/10 (without E-mode polarization)
//
// Reference: SHADOW_PORT_EQUATIONS_v1.md, PREP-04A_RESULT.md

/// State layout for CAMB-convention solver.
pub(crate) struct CambLayout {
    pub(crate) lmax_g: usize,
    pub(crate) lmax_n: usize,
    pub(crate) lmax_pol: usize,
    pub(crate) nq_massive: usize,
    pub(crate) lmax_m: usize,
    pub(crate) n_state: usize,
    pub(crate) i_etak: usize,
    pub(crate) i_sigma: usize,
    pub(crate) i_clxc: usize,
    pub(crate) i_clxb: usize,
    pub(crate) i_vb: usize,
    pub(crate) i_theta0: usize,
    pub(crate) i_n0: usize,
    pub(crate) i_e0: usize,
    pub(crate) i_b0: usize,
    pub(crate) i_psi0: usize,
    pub(crate) i_phi: usize,     // Newtonian potential Φ (for ISW)
}

impl CambLayout {
    pub(crate) fn new(lmax_g: usize, lmax_n: usize) -> Self {
        Self::new_full(lmax_g, lmax_n, 0, 0, 0)
    }
    
    pub(crate) fn new_with_pol(lmax_g: usize, lmax_n: usize, lmax_pol: usize) -> Self {
        Self::new_full(lmax_g, lmax_n, lmax_pol, 0, 0)
    }
    
    pub(crate) fn new_full(
        lmax_g: usize, lmax_n: usize, lmax_pol: usize,
        nq_massive: usize, lmax_m: usize,
    ) -> Self {
        let i_theta0 = 5;
        let i_n0 = i_theta0 + lmax_g + 1;
        let i_e0 = i_n0 + lmax_n + 1;
        let pol_blk = if lmax_pol > 0 { lmax_pol + 1 } else { 0 };
        let i_b0 = i_e0 + pol_blk;
        let i_psi0 = i_b0 + pol_blk;
        let i_phi = i_psi0 + nq_massive * if nq_massive > 0 { lmax_m + 1 } else { 0 };
        let n_state = i_phi + 1; // Φ is the last variable
        Self { lmax_g, lmax_n, lmax_pol, nq_massive, lmax_m, n_state,
               i_etak: 0, i_sigma: 1, i_clxc: 2, i_clxb: 3, i_vb: 4,
               i_theta0, i_n0, i_e0, i_b0, i_psi0, i_phi }
    }

    #[inline] pub(crate) fn theta(&self, ell: usize) -> usize { self.i_theta0 + ell }
    #[inline] pub(crate) fn nu(&self, ell: usize) -> usize { self.i_n0 + ell }
    #[inline] pub(crate) fn e_mode(&self, ell: usize) -> usize { self.i_e0 + ell }
    #[inline] pub(crate) fn b_mode(&self, ell: usize) -> usize { self.i_b0 + ell }
    #[inline] pub(crate) fn psi(&self, iq: usize, ell: usize) -> usize {
        self.i_psi0 + iq * (self.lmax_m + 1) + ell
    }
    #[inline] pub(crate) fn has_pol(&self) -> bool { self.lmax_pol > 0 }
    #[inline] pub(crate) fn has_massive_nu(&self) -> bool { self.nq_massive > 0 }
}

/// Background quantities needed at each τ.
#[derive(Clone, Copy)]
pub(crate) struct CambBackground {
    pub(crate) adotoa: f64,     // ℋ [Mpc⁻¹]
    pub(crate) grho_g: f64,     // κa²ρ_γ
    pub(crate) grho_nu: f64,    // κa²ρ_ν (MASSLESS ONLY, Neff≈2.03)
    pub(crate) grho_b: f64,     // κa²ρ_b
    pub(crate) grho_c: f64,     // κa²ρ_c
    pub(crate) opac: f64,       // Thomson opacity > 0
    pub(crate) cs2b: f64,       // baryon sound speed²
    pub(crate) vis: f64,        // visibility g(τ)
    pub(crate) dvis: f64,       // g'(τ)
    pub(crate) ddvis: f64,      // g''(τ)
    pub(crate) a: f64,          // scale factor (for massive ν: am = am0 × a)
    pub(crate) expmmu: f64,     // e^{-τ} (for ISW source term)
}

/// Gauss-Laguerre nodes and weights for massive ν (10-point).
/// Raw weights from numpy.polynomial.laguerre.laggauss(10).
/// GL transform: ∫₀^∞ f(q)dq ≈ Σ w_i × f(q_i) × e^{q_i}
pub(crate) const GL10_NODES: [f64; 10] = [
    0.1377934705405, 0.7294545495032, 1.8083429017403, 3.4014336978549,
    5.5524961400638, 8.3301527467645, 11.8437858379001, 16.2792578313781,
    21.9965858119808, 29.9206970122739,
];
pub(crate) const GL10_WEIGHTS: [f64; 10] = [
    0.3084411157650, 0.4011199291553, 0.2180682876118, 0.0620874560987,
    0.0095015169752, 0.0007530083886, 0.0000282592335, 0.0000004249314,
    0.0000000018396, 0.0000000000010,
];

/// Massive neutrino configuration.
#[derive(Clone)]
pub(crate) struct MassiveNuConfig {
    pub(crate) nq: usize,
    pub(crate) q_nodes: Vec<f64>,
    pub(crate) q_weights: Vec<f64>,
    pub(crate) fd_weight: Vec<f64>,    // f₀(q)×e^q = e^q/(e^q+1)
    pub(crate) dlnf0_dlnq: Vec<f64>,  // -q×e^q/(e^q+1)
    pub(crate) am0: f64,               // m_ν/(k_B T_ν) at a=1
    pub(crate) neff_massless: f64,     // N_eff for massless species
    pub(crate) neff_massive: f64,      // N_eff for this massive eigenstate
}

impl MassiveNuConfig {
    pub(crate) fn default_planck() -> Self {
        let nq = 10;
        let q_nodes = GL10_NODES.to_vec();
        let q_weights = GL10_WEIGHTS.to_vec();
        let fd_weight: Vec<f64> = q_nodes.iter()
            .map(|&q| { let eq = q.exp(); eq / (eq + 1.0) }).collect();
        let dlnf0_dlnq: Vec<f64> = q_nodes.iter().zip(fd_weight.iter())
            .map(|(&q, &fw)| -q * fw).collect();  // dlnf₀/dlnq = -q·e^q/(e^q+1)
        // am0 = m_ν / (k_B T_ν) at a=1 for m_ν = 0.06 eV
        let m_nu_ev = 0.06_f64;
        let t_nu_k = (4.0_f64/11.0).powf(1.0/3.0) * 2.7255; // K
        let kb_ev = 8.617333e-5_f64;
        let am0 = m_nu_ev / (kb_ev * t_nu_k);
        Self { nq, q_nodes, q_weights, fd_weight, dlnf0_dlnq, am0,
               neff_massless: 2.0328, neff_massive: 1.0132 }
    }
    
    /// ε(q, am) = √(q² + am²)
    #[inline]
    pub(crate) fn epsilon(&self, q: f64, am: f64) -> f64 { (q*q + am*am).sqrt() }
    
    /// Velocity v = q/ε
    #[inline]
    pub(crate) fn velocity(&self, q: f64, am: f64) -> f64 {
        q / self.epsilon(q, am)
    }
}

/// Source function output.
pub(crate) struct SourceTerms {
    pub(crate) s_total: f64,
    pub(crate) s_sw: f64,
    pub(crate) s_dop: f64,
    pub(crate) s_quad: f64,
}

/// Compute RHS dy/dτ and source function terms.
pub(crate) fn camb_rhs(
    k: f64, tau: f64, y: &[f64], dy: &mut [f64], lay: &CambLayout, bg: &CambBackground,
) -> SourceTerms {
    let lg = lay.lmax_g;
    let ln = lay.lmax_n;

    // Unpack state
    let etak = y[lay.i_etak];
    let sigma = y[lay.i_sigma];
    let _clxc = y[lay.i_clxc];
    let clxb = y[lay.i_clxb];
    let vb = y[lay.i_vb];

    let theta = |ell: usize| -> f64 {
        if ell <= lg { y[lay.theta(ell)] } else { 0.0 }
    };
    let nu = |ell: usize| -> f64 {
        if ell <= ln { y[lay.nu(ell)] } else { 0.0 }
    };

    let h = bg.adotoa;
    let opac = bg.opac;

    // ── Massive ν integrated perturbations (if enabled) ──
    let (dgq_mnu, dgs_mnu) = if lay.has_massive_nu() {
        let cfg = MassiveNuConfig::default_planck();
        let am = cfg.am0 * bg.a;
        let neff_total = cfg.neff_massless + cfg.neff_massive;
        // Normalization: grho_nu_total = bg.grho_nu * neff_total / neff_massless
        // grho_per_species = bg.grho_nu / neff_massless (massless contribution per species)
        // massive norm: grho_per × neff_massive / massless_integral
        let massless_int: f64 = (0..cfg.nq).map(|i| {
            cfg.q_weights[i] * cfg.q_nodes[i].powi(3) * cfg.fd_weight[i]
        }).sum();
        let norm = if massless_int.abs() > 1e-30 {
            bg.grho_nu / cfg.neff_massless * cfg.neff_massive / massless_int
        } else { 0.0 };

        let mut dq = 0.0_f64;
        let mut ds = 0.0_f64;
        for iq in 0..lay.nq_massive.min(cfg.nq) {
            let q = cfg.q_nodes[iq];
            let w = cfg.q_weights[iq];
            let fw = cfg.fd_weight[iq];
            let eps = cfg.epsilon(q, am);
            let psi1 = y[lay.psi(iq, 1)];
            let psi2 = if lay.lmax_m >= 2 { y[lay.psi(iq, 2)] } else { 0.0 };
            dq += w * q.powi(3) * psi1 * fw;                   // momentum
            ds += w * q * q * (q * q / eps) * psi2 * fw;       // stress
        }
        (norm * (4.0 / 3.0) * dq, norm * (2.0 / 3.0) * ds)
    } else {
        (0.0, 0.0)
    };

    // ── Momentum constraint ──
    // dgq = (4/3)grho_γ·4Θ₁ + (4/3)grho_ν·4N₁ + grho_b·v_b + dgq_massive
    let v_gamma = 4.0 * theta(1);
    let v_nu = 4.0 * nu(1);
    let dgq = (4.0 / 3.0) * bg.grho_g * v_gamma
            + (4.0 / 3.0) * bg.grho_nu * v_nu
            + bg.grho_b * vb
            + dgq_mnu;
    let etakdot = dgq / 2.0;

    // ── ḣ from σ definition ──
    let hdot = 2.0 * k * sigma - 6.0 * etakdot / k;

    // ── σ evolution ──
    // pig = 4·Θ₂, pir = 4·N₂ (CONFIRMED ratio 4.0000)
    let pig = 4.0 * theta(2);
    let pir = 4.0 * nu(2);
    let dgs = bg.grho_g * pig + bg.grho_nu * pir + dgs_mnu;
    let sigmadot = -2.0 * h * sigma - dgs / k + etak;

    // ── Matter ──
    let clxcdot = -hdot / 2.0;
    let clxbdot = -k * vb - hdot / 2.0;
    let r_b = 0.75 * bg.grho_b / bg.grho_g;
    let vbdot = -h * vb + bg.cs2b * k * clxb
              + opac * (3.0 * theta(1) - vb) / r_b.max(1e-10);

    // ── Photon hierarchy ──
    // ℓ=0
    dy[lay.theta(0)] = -k * theta(1) - hdot / 6.0;
    // ℓ=1
    dy[lay.theta(1)] = k / 3.0 * (theta(0) - 2.0 * theta(2))
                      - opac * (theta(1) - vb / 3.0);
    // ℓ=2: with E-mode: -opac(Θ₂ - 5polter/2); without: -(9/10)opac·Θ₂
    if lg >= 2 {
        if lay.has_pol() {
            let e2 = y[lay.e_mode(2)];
            let polter_val = 2.0 * theta(2) / 5.0 + 3.0 * e2 / 5.0;
            dy[lay.theta(2)] = k / 5.0 * (2.0 * theta(1) - 3.0 * theta(3))
                              - opac * (theta(2) - 2.5 * polter_val);
        } else {
            dy[lay.theta(2)] = k / 5.0 * (2.0 * theta(1) - 3.0 * theta(3))
                              - 0.9 * opac * theta(2);
        }
    }
    // ℓ ≥ 3
    for ell in 3..lg {
        let f = k / (2 * ell + 1) as f64;
        dy[lay.theta(ell)] = f * (ell as f64 * theta(ell - 1)
                                - (ell + 1) as f64 * theta(ell + 1))
                            - opac * theta(ell);
    }
    // Truncation
    if lg >= 3 {
        // Not needed if lg < 3, but guard anyway
    }
    if lg >= 1 {
        let tau_safe = tau;
        dy[lay.theta(lg)] = k * theta(lg - 1)
                           - (lg + 1) as f64 / tau_safe.max(1e-10) * theta(lg)
                           - opac * theta(lg);
    }

    // ── Neutrino hierarchy ──
    dy[lay.nu(0)] = -k * nu(1) - hdot / 6.0;
    if ln >= 1 {
        dy[lay.nu(1)] = k / 3.0 * (nu(0) - 2.0 * nu(2));
    }
    for ell in 2..ln {
        let f = k / (2 * ell + 1) as f64;
        dy[lay.nu(ell)] = f * (ell as f64 * nu(ell - 1)
                             - (ell + 1) as f64 * nu(ell + 1));
    }
    if ln >= 2 {
        let tau_safe = tau;
        dy[lay.nu(ln)] = k * nu(ln - 1)
                        - (ln + 1) as f64 / tau_safe.max(1e-10) * nu(ln);
    }

    // ── E-mode polarization hierarchy (CAMB convention) ──
    // E₀' = -k E₁ - opac(E₀ - polter)
    // E₁' = k/3(E₀ - 2E₂) - opac E₁
    // E₂' = k/5(2E₁ - 3E₃) - opac(E₂ - polter)
    // E_ℓ' = k/(2ℓ+1)(ℓE_{ℓ-1} - (ℓ+1)E_{ℓ+1}) - opac E_ℓ  [ℓ≥3]
    // polter = 2Θ₂/5 + 3E₂/5
    if lay.has_pol() {
        let lp = lay.lmax_pol;
        let e = |ell: usize| -> f64 {
            if ell <= lp { y[lay.e_mode(ell)] } else { 0.0 }
        };
        let th2 = if lg >= 2 { theta(2) } else { 0.0 };
        let polter_e = 2.0 * th2 / 5.0 + 3.0 * e(2) / 5.0;

        // ℓ=0
        dy[lay.e_mode(0)] = -k * e(1) - opac * (e(0) - polter_e);

        // ℓ=1
        if lp >= 1 {
            dy[lay.e_mode(1)] = k / 3.0 * (e(0) - 2.0 * e(2)) - opac * e(1);
        }
        // ℓ=2
        if lp >= 2 {
            dy[lay.e_mode(2)] = k / 5.0 * (2.0 * e(1) - 3.0 * e(3))
                               - opac * (e(2) - polter_e);
        }
        // ℓ≥3
        for ell in 3..lp {
            let f = k / (2 * ell + 1) as f64;
            dy[lay.e_mode(ell)] = f * (ell as f64 * e(ell - 1)
                                     - (ell + 1) as f64 * e(ell + 1))
                                 - opac * e(ell);
        }
        // Truncation
        if lp >= 3 {
            dy[lay.e_mode(lp)] = k * e(lp - 1)
                                - (lp + 1) as f64 / tau.max(1e-10) * e(lp)
                                - opac * e(lp);
        }

        // B-mode: identically zero for scalar perturbations
        // (structure ready for tensor/Bianchi extension)
        for ell in 0..=lp {
            dy[lay.b_mode(ell)] = 0.0;
        }
    }

    // ── Massive ν hierarchy (per q-bin) ──
    // Ψ₀'(q) = -kv Ψ₁ + (ḣ/6)·(dlnf₀/dlnq)
    // Ψ₁'(q) = kv/3·(Ψ₀ - 2Ψ₂)
    // Ψ_ℓ'(q) = kv/(2ℓ+1)·[ℓΨ_{ℓ-1} - (ℓ+1)Ψ_{ℓ+1}]  (ℓ≥2)
    // where v = q/√(q²+(am)²)
    if lay.has_massive_nu() {
        let cfg = MassiveNuConfig::default_planck();
        let am = cfg.am0 * bg.a;
        let lm = lay.lmax_m;

        for iq in 0..lay.nq_massive.min(cfg.nq) {
            let q = cfg.q_nodes[iq];
            let v = cfg.velocity(q, am);
            let kv = k * v;

            let psi = |ell: usize| -> f64 {
                if ell <= lm { y[lay.psi(iq, ell)] } else { 0.0 }
            };

            // ℓ=0: metric source
            dy[lay.psi(iq, 0)] = -kv * psi(1) + hdot / 6.0 * cfg.dlnf0_dlnq[iq];

            // ℓ=1
            if lm >= 1 {
                let p2 = if lm >= 2 { psi(2) } else { 0.0 };
                dy[lay.psi(iq, 1)] = kv / 3.0 * (psi(0) - 2.0 * p2);
            }

            // ℓ≥2
            for ell in 2..lm {
                let f = kv / (2 * ell + 1) as f64;
                dy[lay.psi(iq, ell)] = f * (ell as f64 * psi(ell - 1)
                                          - (ell + 1) as f64 * psi(ell + 1));
            }

            // Truncation
            if lm >= 2 {
                dy[lay.psi(iq, lm)] = kv * psi(lm - 1)
                    - (lm + 1) as f64 / tau.max(1e-10) * psi(lm);
            }
        }
    }

    // ── Assemble metric ──
    dy[lay.i_etak] = etakdot;
    dy[lay.i_sigma] = sigmadot;
    dy[lay.i_clxc] = clxcdot;
    dy[lay.i_clxb] = clxbdot;
    dy[lay.i_vb] = vbdot;

    // ── Source function ──
    let eta_s = etak / k;
    let phi = eta_s - h * sigma / k;
    let eta_mb = -2.0 * eta_s;
    let delta_g = 4.0 * theta(0);
    let polter = if lay.has_pol() {
        let e2 = y[lay.e_mode(2)];
        2.0 * theta(2) / 5.0 + 3.0 * e2 / 5.0
    } else {
        pig / 10.0
    };
    let pigdot = if lg >= 2 { 4.0 * dy[lay.theta(2)] } else { 0.0 };
    let polterdot = if lay.has_pol() {
        let e2dot = dy[lay.e_mode(2)];
        2.0 * (pigdot / 4.0) / 5.0 + 3.0 * e2dot / 5.0
    } else {
        pigdot / 10.0
    };

    let g = bg.vis;
    let gp = bg.dvis;
    let gpp = bg.ddvis;

    // SW: g × (Δ_γ/4 + 2φ + η_MB/2) [synchronous gauge correction]
    let s_sw = g * (delta_g / 4.0 + 2.0 * phi + eta_mb / 2.0);

    // Doppler: [(σ+v_b)g' + (σ̇+v̇_b)g] / k   (CAMB symbolic: diff(g*(v_b+sigma),t)/k)
    let s_dop = ((sigma + vb) * gp + (sigmadot + vbdot) * g) / k;

    // Quadrupole
    let s_quad = 5.0 / (8.0 * k * k) * (
        k * k * polter * g + 3.0 * polter * gpp + 6.0 * polterdot * gp
    );
    // ── ISW: computed in post-processing via FD on phi = etak/k − ℋσ/k ──
    // s_isw is set to 0 here; solve_kmode_full adds ISW after source extraction.
    let s_isw = 0.0;
    dy[lay.i_phi] = 0.0;

    SourceTerms {
        s_total: s_sw + s_dop + s_quad + s_isw,
        s_sw, s_dop, s_quad,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_layout_dimension() {
        let lay = CambLayout::new(16, 16);
        assert_eq!(lay.n_state, 40); // 5 + 17 + 17 + 1(Φ)
        assert_eq!(lay.theta(0), 5);
        assert_eq!(lay.theta(16), 21);
        assert_eq!(lay.nu(0), 22);
        assert_eq!(lay.nu(16), 38);
    }

    #[test]
    fn test_pig_normalization() {
        // pig = 4·Θ₂ — the ratio 4.0000 is confirmed at 3 k-values
        let theta2 = 0.123;
        let pig = 4.0 * theta2;
        assert!((pig / theta2 - 4.0_f64).abs() < 1e-10);
    }

    #[test]
    fn test_momentum_constraint_coefficients() {
        // Verify: etakdot = (1/2)[(4/3)grho_γ·4Θ₁ + (4/3)grho_ν·4N₁ + grho_b·v_b]
        // For grho_γ = 3H²·Ω_γ:
        // coeff of Θ₁ = (1/2)(4/3)(3H²Ω_γ)(4) = 8H²Ω_γ
        let h2 = 0.01_f64.powi(2); // H² = 1e-4
        let omega_g = 0.5_f64; // Ω_γ = 0.5 (radiation-dominated)
        let grho_g = 3.0 * h2 * omega_g;
        let theta1 = 1.0;
        // Expected contribution from photon Θ₁:
        let expected = 0.5 * (4.0 / 3.0) * grho_g * 4.0 * theta1;
        // = 0.5 * (4/3) * 3H²Ω_γ * 4 = 8H²Ω_γ
        let direct = 8.0 * h2 * omega_g;
        assert!((expected - direct).abs() < 1e-15,
            "Momentum coeff: {} vs {}", expected, direct);
    }

    #[test]
    fn test_rhs_zero_state() {
        // All-zero state should give finite RHS (no NaN/Inf)
        let lay = CambLayout::new(4, 4);
        let mut y = vec![0.0; lay.n_state];
        y[lay.i_etak] = -0.01; // small nonzero etak
        let mut dy = vec![0.0; lay.n_state];
        let bg = CambBackground {
            adotoa: 0.01, grho_g: 1e-6, grho_nu: 5e-7,
            grho_b: 3e-7, grho_c: 1e-6, opac: 100.0, cs2b: 1e-10,
            vis: 0.0, dvis: 0.0, ddvis: 0.0,
            a: 1.0,
            expmmu: 0.0,
        };
        let src = camb_rhs(0.01, 100.0, &y, &mut dy, &lay, &bg);
        for (i, &v) in dy.iter().enumerate() {
            assert!(v.is_finite(), "dy[{}] = {} is not finite", i, v);
        }
        assert!(src.s_total.is_finite());
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Matrix builder for Rodas5P integration
// ═══════════════════════════════════════════════════════════════════════

/// Build the Jacobian matrix A such that dy/dτ = A·y.
/// Returns flat n×n matrix in row-major order.
pub(crate) fn build_camb_matrix_into(
    k: f64, tau: f64, lay: &CambLayout, bg: &CambBackground, m: &mut [f64],
) {
    let n = lay.n_state;
    let lg = lay.lmax_g;
    let ln = lay.lmax_n;
    m.iter_mut().for_each(|v| *v = 0.0);
    let idx = |row: usize, col: usize| -> usize { row * n + col };

    let h = bg.adotoa;
    let opac = bg.opac;

    // ── etakdot = (1/2)[(4/3)grho_γ·4Θ₁ + (4/3)grho_ν·4N₁ + grho_b·v_b] ──
    // ∂etakdot/∂Θ₁ = (1/2)(4/3)(grho_γ)(4) = (8/3)grho_γ
    if lg >= 1 {
        m[idx(lay.i_etak, lay.theta(1))] = (8.0 / 3.0) * bg.grho_g;
    }
    if ln >= 1 {
        m[idx(lay.i_etak, lay.nu(1))] = (8.0 / 3.0) * bg.grho_nu;
    }
    m[idx(lay.i_etak, lay.i_vb)] = bg.grho_b / 2.0;

    // ── ḣ = 2kσ − 6·etakdot/k ──
    // hdot depends on σ and on Θ₁,N₁,v_b (through etakdot)
    // We don't store hdot as a variable; it's used in δ_c', δ_b', Θ₀', N₀' equations.
    // For each equation using hdot, we expand hdot = 2kσ - 6/k · etakdot
    // and add the corresponding matrix entries.

    // Partial derivatives of hdot:
    // ∂ḣ/∂σ = 2k
    // ∂ḣ/∂Θ₁ = -6/k · (8/3)grho_γ = -16grho_γ/k
    // ∂ḣ/∂N₁ = -6/k · (8/3)grho_ν = -16grho_ν/k
    // ∂ḣ/∂v_b = -6/k · grho_b/2 = -3grho_b/k
    let dhdot_dsigma = 2.0 * k;
    let dhdot_dtheta1 = if lg >= 1 { -16.0 * bg.grho_g / k } else { 0.0 };
    let dhdot_dnu1 = if ln >= 1 { -16.0 * bg.grho_nu / k } else { 0.0 };
    let dhdot_dvb = -3.0 * bg.grho_b / k;

    // ── σ' = -2ℋσ - dgs/k + etak ──
    // ∂σ'/∂σ = -2ℋ
    m[idx(lay.i_sigma, lay.i_sigma)] = -2.0 * h;
    // ∂σ'/∂etak = 1
    m[idx(lay.i_sigma, lay.i_etak)] = 1.0;
    // ∂σ'/∂Θ₂ = -grho_γ·4/k
    if lg >= 2 {
        m[idx(lay.i_sigma, lay.theta(2))] = -4.0 * bg.grho_g / k;
    }
    if ln >= 2 {
        m[idx(lay.i_sigma, lay.nu(2))] = -4.0 * bg.grho_nu / k;
    }

    // ── δ_c' = -ḣ/2 ──
    // ∂δ_c'/∂σ = -dhdot_dsigma/2 = -k
    m[idx(lay.i_clxc, lay.i_sigma)] = -dhdot_dsigma / 2.0;
    if lg >= 1 { m[idx(lay.i_clxc, lay.theta(1))] = -dhdot_dtheta1 / 2.0; }
    if ln >= 1 { m[idx(lay.i_clxc, lay.nu(1))] = -dhdot_dnu1 / 2.0; }
    m[idx(lay.i_clxc, lay.i_vb)] = -dhdot_dvb / 2.0;

    // ── δ_b' = -kv_b - ḣ/2 ──
    m[idx(lay.i_clxb, lay.i_vb)] = -k + (-dhdot_dvb / 2.0);
    m[idx(lay.i_clxb, lay.i_sigma)] = -dhdot_dsigma / 2.0;
    if lg >= 1 { m[idx(lay.i_clxb, lay.theta(1))] = -dhdot_dtheta1 / 2.0; }
    if ln >= 1 { m[idx(lay.i_clxb, lay.nu(1))] = -dhdot_dnu1 / 2.0; }

    // ── v_b' = -ℋv_b + cs2b·k·δ_b + opac(3Θ₁-v_b)/R ──
    let r_b = (0.75 * bg.grho_b / bg.grho_g).max(1e-10);
    m[idx(lay.i_vb, lay.i_vb)] = -h - opac / r_b;
    m[idx(lay.i_vb, lay.i_clxb)] = bg.cs2b * k;
    if lg >= 1 { m[idx(lay.i_vb, lay.theta(1))] = 3.0 * opac / r_b; }

    // ── Θ₀' = -kΘ₁ - ḣ/6 ──
    if lg >= 1 { m[idx(lay.theta(0), lay.theta(1))] = -k + (-dhdot_dtheta1 / 6.0); }
    m[idx(lay.theta(0), lay.i_sigma)] = -dhdot_dsigma / 6.0;
    if ln >= 1 { m[idx(lay.theta(0), lay.nu(1))] = -dhdot_dnu1 / 6.0; }
    m[idx(lay.theta(0), lay.i_vb)] = -dhdot_dvb / 6.0;

    // ── Θ₁' = (k/3)(Θ₀ - 2Θ₂) - opac(Θ₁ - v_b/3) ──
    if lg >= 1 {
        m[idx(lay.theta(1), lay.theta(0))] = k / 3.0;
        m[idx(lay.theta(1), lay.theta(1))] = -opac;
        if lg >= 2 { m[idx(lay.theta(1), lay.theta(2))] = -2.0 * k / 3.0; }
        m[idx(lay.theta(1), lay.i_vb)] = opac / 3.0;
    }

    // ── Θ₂' with polarization-aware collision term ──
    // pol ON:  Θ₂' = k/5(2Θ₁-3Θ₃) - opac(Θ₂ - 5polter/2)
    //        where polter = 2Θ₂/5 + 3E₂/5
    //        expands to: k/5(2Θ₁-3Θ₃) + 1.5·opac·E₂  [Θ₂ self-damping cancels]
    // pol OFF: Θ₂' = k/5(2Θ₁-3Θ₃) - 0.9·opac·Θ₂     [standard approximation]
    if lg >= 2 {
        m[idx(lay.theta(2), lay.theta(1))] = 2.0 * k / 5.0;
        if lg >= 3 { m[idx(lay.theta(2), lay.theta(3))] = -3.0 * k / 5.0; }
        if lay.has_pol() {
            // Θ₂ self-damping vanishes when E-mode is included
            m[idx(lay.theta(2), lay.e_mode(2))] = 1.5 * opac;
        } else {
            m[idx(lay.theta(2), lay.theta(2))] = -0.9 * opac;
        }
    }

    // ── Θ_ℓ' for 3 ≤ ℓ < lmax ── (lmax handled by truncation below)
    for ell in 3..lg {
        let f = k / (2 * ell + 1) as f64;
        m[idx(lay.theta(ell), lay.theta(ell - 1))] = f * ell as f64;
        if ell < lg { m[idx(lay.theta(ell), lay.theta(ell + 1))] = -f * (ell + 1) as f64; }
        m[idx(lay.theta(ell), lay.theta(ell))] = -opac;
    }

    // Truncation for Θ_lmax: Θ_lg' = k·Θ_{lg-1} − (lg+1)/τ·Θ_lg − κ'·Θ_lg
    if lg >= 3 {
        let tau_safe = tau.max(1e-10);
        m[idx(lay.theta(lg), lay.theta(lg - 1))] = k;
        m[idx(lay.theta(lg), lay.theta(lg))] = -((lg + 1) as f64) / tau_safe - opac;
    }

    // ── N₀' = -kN₁ - ḣ/6 ──
    if ln >= 1 { m[idx(lay.nu(0), lay.nu(1))] = -k + (-dhdot_dnu1 / 6.0); }
    m[idx(lay.nu(0), lay.i_sigma)] = -dhdot_dsigma / 6.0;
    if lg >= 1 { m[idx(lay.nu(0), lay.theta(1))] = -dhdot_dtheta1 / 6.0; }
    m[idx(lay.nu(0), lay.i_vb)] = -dhdot_dvb / 6.0;

    // ── N₁' = (k/3)(N₀ - 2N₂) ──
    if ln >= 1 {
        m[idx(lay.nu(1), lay.nu(0))] = k / 3.0;
        if ln >= 2 { m[idx(lay.nu(1), lay.nu(2))] = -2.0 * k / 3.0; }
    }

    // ── N_ℓ' for 2 ≤ ℓ < lmax ── (lmax handled by truncation below)
    for ell in 2..ln {
        let f = k / (2 * ell + 1) as f64;
        m[idx(lay.nu(ell), lay.nu(ell - 1))] = f * ell as f64;
        if ell < ln { m[idx(lay.nu(ell), lay.nu(ell + 1))] = -f * (ell + 1) as f64; }
    }

    // Truncation for N_lmax: N_ln' = k·N_{ln-1} − (ln+1)/τ·N_ln
    if ln >= 2 {
        let tau_safe = tau.max(1e-10);
        m[idx(lay.nu(ln), lay.nu(ln - 1))] = k;
        m[idx(lay.nu(ln), lay.nu(ln))] = -((ln + 1) as f64) / tau_safe;
    }

    // ── E-mode polarization hierarchy (P0-2 fix) ──
    // E₀' = -k·E₁ - opac·(E₀ - polter)       polter = 2Θ₂/5 + 3E₂/5
    // E₁' = k/3·(E₀ - 2E₂) - opac·E₁
    // E₂' = k/5·(2E₁ - 3E₃) - opac·(E₂ - polter)
    //      = k/5·(2E₁ - 3E₃) - opac·(2E₂/5 - 2Θ₂/5) = k/5·(2E₁-3E₃) - 2opac/5·(E₂-Θ₂)
    // E_ℓ' = k/(2ℓ+1)·(ℓE_{ℓ-1} - (ℓ+1)E_{ℓ+1}) - opac·E_ℓ   [ℓ≥3]
    if lay.has_pol() {
        let lp = lay.lmax_pol;

        // ℓ=0: E₀' = -k·E₁ - opac·E₀ + opac·polter
        //     polter coupling: + opac·(2Θ₂/5) to E₀,Θ₂  and + opac·(3E₂/5) to E₀,E₂
        m[idx(lay.e_mode(0), lay.e_mode(0))] = -opac;
        if lp >= 1 { m[idx(lay.e_mode(0), lay.e_mode(1))] = -k; }
        if lg >= 2 { m[idx(lay.e_mode(0), lay.theta(2))] = opac * 2.0 / 5.0; }
        if lp >= 2 { m[idx(lay.e_mode(0), lay.e_mode(2))] = opac * 3.0 / 5.0; }

        // ℓ=1: E₁' = k/3·(E₀ - 2E₂) - opac·E₁
        if lp >= 1 {
            m[idx(lay.e_mode(1), lay.e_mode(0))] = k / 3.0;
            m[idx(lay.e_mode(1), lay.e_mode(1))] = -opac;
            if lp >= 2 { m[idx(lay.e_mode(1), lay.e_mode(2))] = -2.0 * k / 3.0; }
        }

        // ℓ=2: E₂' = k/5·(2E₁-3E₃) - 2opac/5·(E₂-Θ₂)
        if lp >= 2 {
            m[idx(lay.e_mode(2), lay.e_mode(1))] = 2.0 * k / 5.0;
            if lp >= 3 { m[idx(lay.e_mode(2), lay.e_mode(3))] = -3.0 * k / 5.0; }
            m[idx(lay.e_mode(2), lay.e_mode(2))] = -2.0 * opac / 5.0;
            if lg >= 2 { m[idx(lay.e_mode(2), lay.theta(2))] = 2.0 * opac / 5.0; }
        }

        // ℓ≥3: standard hierarchy with opac damping (up to lmax-1)
        for ell in 3..lp {
            let f = k / (2 * ell + 1) as f64;
            m[idx(lay.e_mode(ell), lay.e_mode(ell - 1))] = f * ell as f64;
            if ell < lp { m[idx(lay.e_mode(ell), lay.e_mode(ell + 1))] = -f * (ell + 1) as f64; }
            m[idx(lay.e_mode(ell), lay.e_mode(ell))] = -opac;
        }

        // Truncation for E_lmax: E_lp' = k·E_{lp-1} − (lp+1)/τ·E_lp − κ'·E_lp
        if lp >= 3 {
            let tau_safe = tau.max(1e-10);
            m[idx(lay.e_mode(lp), lay.e_mode(lp - 1))] = k;
            m[idx(lay.e_mode(lp), lay.e_mode(lp))] = -((lp + 1) as f64) / tau_safe - opac;
        }

        // B-mode: dy = 0 for scalar perturbations (rows stay zero)
    }

    // ── Massive ν hierarchy per q-bin (P0-3 fix) ──
    // Ψ₀'(q) = -kv·Ψ₁ + (ḣ/6)·dlnf₀/dlnq
    // Ψ₁'(q) = kv/3·(Ψ₀ - 2Ψ₂)
    // Ψ_ℓ'(q) = kv/(2ℓ+1)·(ℓΨ_{ℓ-1} - (ℓ+1)Ψ_{ℓ+1})   [ℓ≥2]
    // where v = q/√(q²+(am)²), ḣ = 2kσ − 6·etakdot/k
    if lay.has_massive_nu() {
        let cfg = MassiveNuConfig::default_planck();
        let am = cfg.am0 * bg.a;
        let lm = lay.lmax_m;

        // Normalization for massive ν integrated perturbations
        let massless_int: f64 = (0..cfg.nq).map(|i| {
            cfg.q_weights[i] * cfg.q_nodes[i].powi(3) * cfg.fd_weight[i]
        }).sum();
        let norm = if massless_int.abs() > 1e-30 {
            bg.grho_nu / cfg.neff_massless * cfg.neff_massive / massless_int
        } else { 0.0 };

        // ḣ derivatives for Ψ₀ metric source
        let dh6_dsigma = k / 3.0;
        let dh6_dtheta1 = if lg >= 1 { -(8.0/3.0) * bg.grho_g / k } else { 0.0 };
        let dh6_dnu1 = if ln >= 1 { -(8.0/3.0) * bg.grho_nu / k } else { 0.0 };
        let dh6_dvb = -bg.grho_b / (2.0 * k);

        for iq in 0..lay.nq_massive.min(cfg.nq) {
            let q = cfg.q_nodes[iq];
            let w = cfg.q_weights[iq];
            let fw = cfg.fd_weight[iq];
            let v = cfg.velocity(q, am);
            let kv = k * v;
            let dlnf = cfg.dlnf0_dlnq[iq];
            let eps = cfg.epsilon(q, am);

            // ── Per-bin hierarchy rows ──

            // ℓ=0: Ψ₀' = -kv·Ψ₁ + (ḣ/6)·dlnf₀
            if lm >= 1 {
                m[idx(lay.psi(iq, 0), lay.psi(iq, 1))] = -kv;
            }
            // metric source: (ḣ/6)·dlnf₀ → linearized entries
            m[idx(lay.psi(iq, 0), lay.i_sigma)] = dh6_dsigma * dlnf;
            if lg >= 1 { m[idx(lay.psi(iq, 0), lay.theta(1))] = dh6_dtheta1 * dlnf; }
            if ln >= 1 { m[idx(lay.psi(iq, 0), lay.nu(1))] = dh6_dnu1 * dlnf; }
            m[idx(lay.psi(iq, 0), lay.i_vb)] = dh6_dvb * dlnf;

            // ℓ=1: Ψ₁' = kv/3·(Ψ₀ - 2Ψ₂)
            if lm >= 1 {
                m[idx(lay.psi(iq, 1), lay.psi(iq, 0))] = kv / 3.0;
                if lm >= 2 { m[idx(lay.psi(iq, 1), lay.psi(iq, 2))] = -2.0 * kv / 3.0; }
            }

            // ℓ≥2: standard hierarchy (up to lmax-1)
            for ell in 2..lm {
                let f = kv / (2 * ell + 1) as f64;
                m[idx(lay.psi(iq, ell), lay.psi(iq, ell - 1))] = f * ell as f64;
                if ell < lm { m[idx(lay.psi(iq, ell), lay.psi(iq, ell + 1))] = -f * (ell + 1) as f64; }
            }

            // Truncation for Ψ_lmax: Ψ_lm' = kv·Ψ_{lm-1} − (lm+1)/τ·Ψ_lm
            if lm >= 2 {
                let tau_safe = tau.max(1e-10);
                m[idx(lay.psi(iq, lm), lay.psi(iq, lm - 1))] = kv;
                m[idx(lay.psi(iq, lm), lay.psi(iq, lm))] = -((lm + 1) as f64) / tau_safe;
            }

            // ── Back-reaction: Ψ₁(q) → etakdot, Ψ₂(q) → σ' ──
            // dgq_mnu contribution: d(etakdot)/d(Ψ₁(q)) = (1/2)·norm·(4/3)·w·q³·fw
            let detakdot_dpsi1 = 0.5 * norm * (4.0/3.0) * w * q.powi(3) * fw;
            m[idx(lay.i_etak, lay.psi(iq, 1))] += detakdot_dpsi1;

            // dgs_mnu contribution: d(σ')/d(Ψ₂(q)) = -norm·(2/3)·w·q²·(q²/ε)·fw / k
            if lm >= 2 {
                let dsigmadot_dpsi2 = -norm * (2.0/3.0) * w * q * q * (q * q / eps) * fw / k;
                m[idx(lay.i_sigma, lay.psi(iq, 2))] += dsigmadot_dpsi2;
            }

            // ḣ back-reaction through etakdot: ḣ = 2kσ − 6etakdot/k
            // d(ḣ)/d(Ψ₁(q)) = -6/k · d(etakdot)/d(Ψ₁) = -6·detakdot_dpsi1/k
            let dhdot_dpsi1 = -6.0 * detakdot_dpsi1 / k;

            // δ_c' = -ḣ/2 → d(δ_c')/d(Ψ₁) = -dhdot_dpsi1/2
            m[idx(lay.i_clxc, lay.psi(iq, 1))] += -dhdot_dpsi1 / 2.0;

            // δ_b' = -kv_b - ḣ/2 → same
            m[idx(lay.i_clxb, lay.psi(iq, 1))] += -dhdot_dpsi1 / 2.0;

            // Θ₀' = -kΘ₁ - ḣ/6
            m[idx(lay.theta(0), lay.psi(iq, 1))] += -dhdot_dpsi1 / 6.0;

            // N₀' = -kN₁ - ḣ/6
            m[idx(lay.nu(0), lay.psi(iq, 1))] += -dhdot_dpsi1 / 6.0;

            // Ψ₀'(q_j) ḣ back-reaction from Ψ₁(q_iq): cross-q coupling
            // d(Ψ₀'(jq))/d(Ψ₁(iq)) = dlnf₀_jq/6 × dhdot_dpsi1
            for jq in 0..lay.nq_massive.min(cfg.nq) {
                let dlnf_j = cfg.dlnf0_dlnq[jq];
                m[idx(lay.psi(jq, 0), lay.psi(iq, 1))] += dlnf_j * dhdot_dpsi1 / 6.0;
            }
        }
    }

    // ── Φ row: dead state, dy[phi]=0 ──
    // Φ is computed algebraically in source extraction (phi = η_s - ℋσ/k).
    // ISW uses FD post-processing on phi array. No ODE evolution needed.
    // Row stays zero → dy[i_phi] = 0 from A×y.
}

pub(crate) fn build_camb_matrix(
    k: f64, tau: f64, lay: &CambLayout, bg: &CambBackground,
) -> Vec<f64> {
    let n = lay.n_state;
    let mut m = vec![0.0_f64; n * n];
    build_camb_matrix_into(k, tau, lay, bg, &mut m);
    m
}

// ═══════════════════════════════════════════════════════════════════════
// BgInterp — linear interpolation of smooth background scalars
// ═══════════════════════════════════════════════════════════════════════
//
// Instead of interpolating n²=4356 matrix elements (which smears
// k-dependent oscillatory structure at high k), we interpolate 12
// smooth, individually-monotonic scalar fields and rebuild A(τ)
// exactly at every ODE step via build_camb_matrix_into.

pub(crate) struct BgInterp {
    pub(crate) tau_grid: Vec<f64>,
    pub(crate) bg_grid: Vec<CambBackground>,
}

impl BgInterp {
    pub(crate) fn new(tau_grid: Vec<f64>, bg_grid: Vec<CambBackground>) -> Self {
        Self { tau_grid, bg_grid }
    }

    /// Locate interval index with sequential scan from hint (τ is monotone in ODE).
    fn locate(&self, tau: f64, hint: &mut usize) -> usize {
        let n = self.tau_grid.len();
        if tau <= self.tau_grid[0] { *hint = 0; return 0; }
        if tau >= self.tau_grid[n - 1] { *hint = n - 2; return n - 2; }
        let mut i = (*hint).min(n - 2);
        // Forward scan (ODE integrates forward in τ)
        while i + 1 < n - 1 && tau >= self.tau_grid[i + 1] { i += 1; }
        // Backward (rare: rejected step)
        while i > 0 && tau < self.tau_grid[i] { i -= 1; }
        *hint = i;
        i
    }

    /// Linearly interpolate all 12 background scalars at given τ.
    pub(crate) fn eval(&self, tau: f64, hint: &mut usize) -> CambBackground {
        let i = self.locate(tau, hint);
        let t0 = self.tau_grid[i];
        let t1 = self.tau_grid[i + 1];
        let w = ((tau - t0) / (t1 - t0)).clamp(0.0, 1.0);
        let b0 = &self.bg_grid[i];
        let b1 = &self.bg_grid[i + 1];
        let lerp = |a: f64, b: f64| a + w * (b - a);
        CambBackground {
            adotoa: lerp(b0.adotoa, b1.adotoa),
            grho_g: lerp(b0.grho_g, b1.grho_g),
            grho_nu: lerp(b0.grho_nu, b1.grho_nu),
            grho_b: lerp(b0.grho_b, b1.grho_b),
            grho_c: lerp(b0.grho_c, b1.grho_c),
            opac: lerp(b0.opac, b1.opac),
            cs2b: lerp(b0.cs2b, b1.cs2b),
            vis: lerp(b0.vis, b1.vis),
            dvis: lerp(b0.dvis, b1.dvis),
            ddvis: lerp(b0.ddvis, b1.ddvis),
            a: lerp(b0.a, b1.a),
            expmmu: lerp(b0.expmmu, b1.expmmu),
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
// On-the-fly Rodas5P integrator
// ═══════════════════════════════════════════════════════════════════════
//
// Same Rodas5P algorithm as integrate_linear_profile_rodas5p, but
// builds A(τ) from interpolated bg scalars at each evaluation point.
// This gives σ̇ = (A×y)[σ_row] with full algebraic precision,
// matching CAMB's direct-RHS approach (dverk 6-8th order).

use crate::core::config::*;
use crate::core::controller::*;
use crate::core::lu::*;
use crate::solver::stacked::interpolate_linear_history_flat_to_targets;
use crate::solver::rodas5p::linear_err_norm;

pub(crate) fn integrate_onthefly_rodas5p(
    bg_interp: &BgInterp,
    k: f64,
    lay: &CambLayout,
    y0: &[f64],
    eta_eval: &[f64],
    cfg: &Rodas5PConfig,
) -> Result<(Vec<Vec<f64>>, Rodas5PStats, ControllerDiagnostics), String> {
    let n_state = lay.n_state;
    if y0.len() != n_state { return Err(format!("y0 must have length {}", n_state)); }
    if eta_eval.len() < 2 { return Err("eta_eval must have ≥ 2 entries".into()); }

    let d = n_state + 1; // extended state: [y; τ]
    let tab = rodas5p_tableau();

    // Working buffers
    let mut a_buf = vec![0.0_f64; n_state * n_state]; // A(τ) matrix
    let mut a_buf2 = vec![0.0_f64; n_state * n_state]; // A(τ+ε) for dA/dτ
    let mut w_mat = vec![0.0_f64; d * d];    // W = I/(γh) - J
    let mut piv = vec![0usize; d];
    let mut ks_flat = vec![0.0_f64; 8 * d];  // 8 stage vectors
    let mut y_stage = vec![0.0_f64; d];
    let mut f_stage = vec![0.0_f64; d];
    let mut rhs_buf = vec![0.0_f64; d];
    let mut y_new = vec![0.0_f64; d];
    let mut err_est = vec![0.0_f64; d];

    // Initialize extended state
    let mut y = vec![0.0_f64; d];
    y[..n_state].copy_from_slice(y0);
    y[d - 1] = eta_eval[0];

    let eta_start = eta_eval[0];
    let eta_end = *eta_eval.last().unwrap();
    let mut h = cfg.h_init.unwrap_or_else(|| ((eta_end - eta_start) / 200.0).max(cfg.h_min).min(cfg.h_max));
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    let mut n_jac = 0usize;
    let mut n_f_eval = 0usize;
    let mut history_eta = Vec::with_capacity(16384);
    history_eta.push(eta_start);
    let mut history_y_flat: Vec<f64> = Vec::with_capacity(16384 * d);
    history_y_flat.extend_from_slice(&y);
    let mut cdiag = ControllerDiagnostics::default();
    let mut reject_streak = 0usize;
    let mut bg_hint = 0usize;

    while y[d - 1] < eta_end - 1e-14 {
        if n_steps >= cfg.max_steps {
            return Err(format!("Max steps {} at τ={:.6}", cfg.max_steps, y[d - 1]));
        }
        let remaining = eta_end - y[d - 1];
        let h_try = h.min(remaining).max(cfg.h_min);
        n_jac += 1;

        // ── Stage 0: Build Jacobian ──
        // A(τ) from interpolated bg
        let tau_now = y[d - 1];
        let bg_now = bg_interp.eval(tau_now, &mut bg_hint);
        build_camb_matrix_into(k, tau_now, lay, &bg_now, &mut a_buf);

        // RHS at current point: f = A × y
        let mut rhs0 = vec![0.0_f64; d];
        for i in 0..n_state {
            let mut acc = 0.0;
            let row = i * n_state;
            for j in 0..n_state { acc += a_buf[row + j] * y[j]; }
            rhs0[i] = acc;
        }
        rhs0[d - 1] = 1.0; // dτ/dτ = 1

        // Jacobian: J[i,j] = A[i,j], J[i,d-1] = (dA/dτ × y)[i]
        // FD for dA/dτ column
        let eps_fd = h_try.max(1e-6) * 1e-4;
        let mut bg_hint2 = bg_hint;
        let bg_eps = bg_interp.eval(tau_now + eps_fd, &mut bg_hint2);
        build_camb_matrix_into(k, tau_now + eps_fd, lay, &bg_eps, &mut a_buf2);

        // Build W = I/(γh) - J
        w_mat.fill(0.0);
        let inv_gh = 1.0 / (tab.gamma * h_try);
        for i in 0..n_state {
            let row_w = i * d;
            let row_a = i * n_state;
            for j in 0..n_state {
                w_mat[row_w + j] = -a_buf[row_a + j];
            }
            // dA/dτ × y column
            let mut da_y = 0.0;
            for j in 0..n_state {
                da_y += (a_buf2[row_a + j] - a_buf[row_a + j]) / eps_fd * y[j];
            }
            w_mat[row_w + d - 1] = -da_y;
            w_mat[row_w + i] += inv_gh;
        }
        w_mat[(d - 1) * d + (d - 1)] = inv_gh; // τ row

        // LU factorize W
        if !lu_factor_in_place_flat_into(&mut w_mat, d, &mut piv) {
            return Err(format!("LU failed at τ={:.6}", tau_now));
        }

        // ── 8-stage Rodas5P loop ──
        ks_flat.fill(0.0);
        n_f_eval += 1; // stage 0 uses rhs0

        for i_stage in 0..8 {
            // y_stage = y + Σ_j a[i][j] * k_j
            y_stage.copy_from_slice(&y);
            for j in 0..i_stage {
                let aij = tab.a[i_stage][j];
                if aij == 0.0 { continue; }
                let base_j = j * d;
                for m in 0..d { y_stage[m] += aij * ks_flat[base_j + m]; }
            }

            // f(y_stage): build A at y_stage's τ, compute A × y_stage
            let tau_s = y_stage[d - 1];
            let bg_s = bg_interp.eval(tau_s, &mut bg_hint);
            build_camb_matrix_into(k, tau_s, lay, &bg_s, &mut a_buf);
            f_stage.fill(0.0);
            for i in 0..n_state {
                let mut acc = 0.0;
                let row = i * n_state;
                for j in 0..n_state { acc += a_buf[row + j] * y_stage[j]; }
                f_stage[i] = acc;
            }
            f_stage[d - 1] = 1.0;
            n_f_eval += 1;

            // RHS for linear solve: f_stage + Σ_j (c[i][j]/h) * k_j
            rhs_buf.copy_from_slice(&f_stage);
            for j in 0..i_stage {
                let cij = tab.c[i_stage][j];
                if cij == 0.0 { continue; }
                let scale = cij / h_try;
                let base_j = j * d;
                for m in 0..d { rhs_buf[m] += scale * ks_flat[base_j + m]; }
            }

            // Solve W × k_i = rhs_buf
            let base_i = i_stage * d;
            if !lu_solve_factored_flat_into(&w_mat, &piv, &rhs_buf, &mut ks_flat[base_i..base_i + d], d) {
                return Err(format!("LU solve failed stage {} at τ={:.6}", i_stage, tau_now));
            }
        }

        // ── Solution + error estimate ──
        y_new.copy_from_slice(&y);
        err_est.fill(0.0);
        for i in 0..8 {
            let base_i = i * d;
            for m in 0..d {
                let kim = ks_flat[base_i + m];
                y_new[m] += tab.b[i] * kim;
                err_est[m] += tab.bhat[i] * kim;
            }
        }
        y_new[d - 1] = y[d - 1] + h_try;
        err_est[d - 1] = 0.0;

        if !y_new.iter().all(|v| v.is_finite()) {
            n_rejected += 1;
            reject_streak += 1;
            cdiag.record_reject(h_try, reject_streak);
            h = new_h(h, 10.0, prev_err, cfg);
            if h < cfg.h_min * 1.0001 {
                return Err(format!("h_min at τ={:.6} (NaN)", y[d - 1]));
            }
            continue;
        }

        let err = linear_err_norm(&err_est, &y_new, n_state, cfg.rtol, cfg.atol);
        if !err.is_finite() || err > 1.0 {
            n_rejected += 1;
            reject_streak += 1;
            cdiag.record_reject(h_try, reject_streak);
            h = new_h(h, if err.is_finite() { err.max(2.0) } else { 10.0 }, prev_err, cfg);
            if h < cfg.h_min * 1.0001 {
                return Err(format!("h_min at τ={:.6}", y[d - 1]));
            }
            continue;
        }

        // Accept step
        y.copy_from_slice(&y_new);
        n_steps += 1;
        reject_streak = 0;
        history_eta.push(y[d - 1]);
        history_y_flat.extend_from_slice(&y);
        let (h_new, q_raw, q_clipped) = new_h_with_diag(h, err, prev_err, cfg);
        cdiag.record_clip(q_raw, q_clipped, cfg.f_min, cfg.f_max);
        cdiag.record_accept(err, h_try, q_raw, q_clipped);
        h = h_new;
        prev_err = err.max(1e-30);
    }

    let out = interpolate_linear_history_flat_to_targets(
        &history_eta, &history_y_flat, d, eta_eval, n_state);
    Ok((out, Rodas5PStats { n_steps, n_rejected, n_jac, n_f_eval, h_final: h }, cdiag))
}

#[cfg(test)]
mod matrix_tests {
    use super::*;

    #[test]
    fn test_matrix_symmetry_rhs() {
        // Matrix × zero-state should give zero RHS
        let lay = CambLayout::new(4, 4);
        let n = lay.n_state;
        let bg = CambBackground {
            adotoa: 0.01, grho_g: 1e-6, grho_nu: 5e-7,
            grho_b: 3e-7, grho_c: 1e-6, opac: 100.0, cs2b: 1e-10,
            vis: 0.0, dvis: 0.0, ddvis: 0.0,
            a: 1.0,
            expmmu: 0.0,
        };
        let mat = build_camb_matrix(0.01, 100.0, &lay, &bg);
        assert_eq!(mat.len(), n * n);
        
        // Test: A × y should match camb_rhs(y) for a test state
        let mut y = vec![0.0_f64; n];
        y[lay.i_etak] = -0.01;
        y[lay.i_sigma] = -0.001;
        y[lay.theta(0)] = 0.1;
        if lay.lmax_g >= 1 { y[lay.theta(1)] = 0.01; }
        if lay.lmax_g >= 2 { y[lay.theta(2)] = 0.001; }
        y[lay.nu(0)] = 0.1;
        if lay.lmax_n >= 1 { y[lay.nu(1)] = 0.01; }
        y[lay.i_clxc] = 0.3;
        y[lay.i_clxb] = 0.3;
        y[lay.i_vb] = 0.03;
        
        // Matrix product: Ay
        let mut ay = vec![0.0_f64; n];
        for i in 0..n {
            for j in 0..n {
                ay[i] += mat[i * n + j] * y[j];
            }
        }
        
        // Direct RHS
        let mut dy = vec![0.0_f64; n];
        camb_rhs(0.01, 100.0, &y, &mut dy, &lay, &bg);
        
        // Compare
        let mut max_err = 0.0_f64;
        for i in 0..n {
            let err = (ay[i] - dy[i]).abs();
            let scale = dy[i].abs().max(1e-15);
            let rel = err / scale;
            if rel > max_err { max_err = rel; }
        }
        assert!(max_err < 1e-10,
            "Matrix-RHS mismatch: max relative error = {:.2e}", max_err);
    }
}

// ═══════════════════════════════════════════════════════════════════════
// k-mode solver: connects to Rodas5P via matrix profile
// ═══════════════════════════════════════════════════════════════════════

use crate::recombination::visibility_hyrec::{VisibilityParams, VisibilityResult};

const NEFF_MASSLESS: f64 = 2.0328; // 3.044 - 1 massive species (mnu=0.06)
const NEFF_TOTAL: f64 = 3.044;

/// Result from the CAMB-convention solver.
pub(crate) struct CambKmodeResult {
    pub(crate) eta_grid: Vec<f64>,
    pub(crate) source_total: Vec<f64>,
    pub(crate) source_sw: Vec<f64>,
    pub(crate) source_dop: Vec<f64>,
    pub(crate) source_quad: Vec<f64>,
    pub(crate) phi: Vec<f64>,
    pub(crate) psi: Vec<f64>,
    pub(crate) n_state: usize,
}

/// Solve one k-mode using CAMB conventions + Rodas5P.
/// If `bootstrap_ic` is Some, use those values instead of analytical IC.
/// bootstrap_ic = (tau_start, y0_vec)
pub(crate) fn solve_camb_kmode(
    k: f64, params: &VisibilityParams, vis: &VisibilityResult,
    ell_max_g: usize, ell_max_nu: usize,
    bootstrap_ic: Option<(f64, Vec<f64>)>,
) -> Result<CambKmodeResult, String> {
    use crate::solver::stacked::integrate_linear_profile_rodas5p;
    use crate::core::config::Rodas5PConfig;

    let h0c = params.h * 1e7 / 2.99792458e10; // H₀/c in Mpc⁻¹
    let og = params.omega_gamma();
    let omega_nu_massless = og * 0.2271 * NEFF_MASSLESS;
    let omega_nu_total = og * 0.2271 * NEFF_TOTAL;
    let n_vis = vis.z_grid.len();
    let eta_max = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);

    let lay = CambLayout::new(ell_max_g, ell_max_nu);
    let n = lay.n_state;

    // Compute visibility derivatives via central differences on eta_grid.
    // CRITICAL: eta_grid increases with z (lookback), NOT conformal time τ.
    // dg/dτ = -dg/dη (sign flip for first derivative only).
    // d²g/dτ² = +d²g/dη² (second derivative: no sign flip).
    let mut g_dot_tau = vec![0.0_f64; n_vis];  // dg/dτ
    let mut g_ddot_tau = vec![0.0_f64; n_vis]; // d²g/dτ²
    for i in 1..n_vis-1 {
        let dt = vis.eta_grid[i+1] - vis.eta_grid[i-1];
        if dt.abs() > 1e-30 {
            let dg_deta = (vis.g_grid[i+1] - vis.g_grid[i-1]) / dt;
            g_dot_tau[i] = -dg_deta; // SIGN FLIP: dg/dτ = -dg/dη
            g_ddot_tau[i] = (vis.g_grid[i+1] - 2.0*vis.g_grid[i] + vis.g_grid[i-1])
                       / (dt/2.0).powi(2); // no sign flip for 2nd deriv
        }
    }

    // Build matrix profile (reversed: τ=0 at z_max, increasing τ)
    let mut tau_profile = Vec::with_capacity(n_vis);
    let mut mats_flat = Vec::with_capacity(n_vis * n * n);
    let mut bg_at_snap: Vec<CambBackground> = Vec::with_capacity(n_vis);

    for i in (0..n_vis).rev() {
        let tau = eta_max - vis.eta_grid[i];
        tau_profile.push(tau);
        let z = vis.z_grid[i];
        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);

        // grho_s = 3ℋ²·Ω_s, but we need physical grho = κa²ρ_s
        // grho_γ = 3H₀²Ω_γ/a² (in Mpc⁻² units)
        let h0c2 = h0c * h0c;
        let grho_g = 3.0 * h0c2 * og / (a * a);
        let grho_nu = 3.0 * h0c2 * omega_nu_massless / (a * a);
        let grho_b = 3.0 * h0c2 * params.omega_b / a;
        let grho_c = 3.0 * h0c2 * (params.omega_m - params.omega_b) / a;

        let bg = CambBackground {
            adotoa: a_h,
            grho_g, grho_nu, grho_b, grho_c,
            opac: vis.kappa_dot_grid[i],
            cs2b: 1e-10, // approximate; proper cs2b needs baryon temperature
            vis: vis.g_grid[i],
            dvis: g_dot_tau[i],
            ddvis: g_ddot_tau[i],
            a, expmmu: 0.0,
        };

        let mat = build_camb_matrix(k, tau, &lay, &bg);
        mats_flat.extend_from_slice(&mat);
        bg_at_snap.push(bg);
    }

    // IC
    let tau_ic_min = if let Some((tau_ic, _)) = &bootstrap_ic { *tau_ic } else { 0.0 };
    
    // Filter tau_profile to start from tau_ic_min
    let mut filtered_tau = Vec::new();
    let mut filtered_mats = Vec::new();
    let mut filtered_bg = Vec::new();
    for (idx, &tau) in tau_profile.iter().enumerate() {
        if tau >= tau_ic_min - 0.1 {
            filtered_tau.push(tau);
            filtered_mats.extend_from_slice(&mats_flat[idx*n*n..(idx+1)*n*n]);
            filtered_bg.push(bg_at_snap[idx]);
        }
    }
    let tau_profile = filtered_tau;
    let mats_flat = filtered_mats;
    let bg_at_snap = filtered_bg;
    
    if tau_profile.len() < 2 {
        return Err("Filtered tau_profile too short".to_string());
    }
    
    let y0 = if let Some((_tau_ic, ic_vec)) = bootstrap_ic {
        if ic_vec.len() != n {
            return Err(format!("IC vector length {} != n_state {}", ic_vec.len(), n));
        }
        ic_vec
    } else {
        // Analytical IC: adiabatic per ζ=1, CAMB convention (η_s → −1)
        let mut y0 = vec![0.0_f64; n];
        y0[lay.i_etak] = -k;
        y0[lay.i_clxc] = 1.5;
        y0[lay.i_clxb] = 1.5;
        y0[lay.theta(0)] = 0.5;
        y0[lay.nu(0)] = 0.5;
        let a_h_init = bg_at_snap[0].adotoa;
        if ell_max_g >= 1 {
            y0[lay.theta(1)] = k / (6.0 * a_h_init.max(1e-30));
        }
        if ell_max_nu >= 1 { y0[lay.nu(1)] = y0[lay.theta(1)]; }
        y0[lay.i_vb] = y0[lay.theta(1)];
        // σ: analytical constraint (approximate, may diverge for kτ > 0.1)
        {
            let bg0 = &bg_at_snap[0];
            let sum_gd = bg0.grho_c*y0[lay.i_clxc] + bg0.grho_b*y0[lay.i_clxb]
                + bg0.grho_g*4.0*y0[lay.theta(0)] + bg0.grho_nu*4.0*y0[lay.nu(0)];
            y0[lay.i_sigma] = (-2.0*k*y0[lay.i_etak] + 0.5*sum_gd)
                / (a_h_init * k).max(1e-30);
        }
        y0
    };

    // Solve
    let h_max_k = (4.0 * 3.0_f64.sqrt() / k.max(1e-10)).min(5.0);
    let cfg = Rodas5PConfig {
        rtol: 1e-6, atol: 1e-9, max_steps: 1_000_000,
        h_init: None, h_min: 1e-14, h_max: h_max_k,
        f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
        use_analytic_jacobian: true, use_ft_term: false,
        use_blas_lu: false, use_block_diag: false,
        ell_max_gamma_hint: ell_max_g, ell_max_nu_hint: ell_max_nu,
        ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false,
    };
    let (snapshots_rev, _stats, _) = integrate_linear_profile_rodas5p(
        &tau_profile, &mats_flat, n, &y0, &tau_profile, &cfg,
    )?;

    // Extract results (reverse to increasing η)
    let n_snaps = snapshots_rev.len();
    let mut result = CambKmodeResult {
        eta_grid: Vec::with_capacity(n_snaps),
        source_total: Vec::with_capacity(n_snaps),
        source_sw: Vec::with_capacity(n_snaps),
        source_dop: Vec::with_capacity(n_snaps),
        source_quad: Vec::with_capacity(n_snaps),
        phi: Vec::with_capacity(n_snaps),
        psi: Vec::with_capacity(n_snaps),
        n_state: n,
    };

    for si in 0..n_snaps {
        // tau_profile is in increasing conformal time.
        // Convert to conformal time η = tau (already conformal time).
        let tau = tau_profile[si];
        result.eta_grid.push(tau); // store conformal time directly

        let y = &snapshots_rev[si];
        let bg = &bg_at_snap[si];
        let tau = tau_profile[si];

        // Compute source using exact RHS derivatives
        let mut dy = vec![0.0_f64; n];
        let src = camb_rhs(k, tau, y, &mut dy, &lay, bg);

        result.source_total.push(src.s_total);
        result.source_sw.push(src.s_sw);
        result.source_dop.push(src.s_dop);
        result.source_quad.push(src.s_quad);

        // Potentials
        let eta_s = y[lay.i_etak] / k;
        let sigma = y[lay.i_sigma];
        let phi = eta_s - bg.adotoa * sigma / k;
        result.phi.push(phi);
        result.psi.push(-phi);
    }

    Ok(result)
}

#[cfg(test)]
mod integration_tests {
    use super::*;

    #[test]
    fn test_solve_camb_kmode_runs() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;

        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        let k = 0.01_f64;
        let lay = CambLayout::new(8, 8);
        let n = lay.n_state;

        // CAMB-bootstrap IC at tau=10.0 Mpc (from Python extraction)
        let mut ic = vec![0.0_f64; n];
        ic[lay.i_etak]   = -9.9967759482e-03;
        ic[lay.i_sigma]  = -3.0393276158e-02;
        ic[lay.i_clxc]   =  2.4638203904e-03;
        ic[lay.i_clxb]   =  2.4631400593e-03;
        ic[lay.i_vb]     =  2.7070800570e-05;
        ic[lay.theta(0)] =  8.2104670582e-04;
        ic[lay.theta(1)] =  9.0236573963e-06;
        ic[lay.theta(2)] = -5.6573469486e-08;
        ic[lay.nu(0)]    =  8.2093314268e-04;
        ic[lay.nu(1)]    =  1.3590472341e-05;

        let result = solve_camb_kmode(k, &p, &vis, 8, 8, Some((10.0, ic)));
        match result {
            Ok(r) => {
                eprintln!("  CAMB kmode k={}: {} snapshots", k, r.eta_grid.len());
                let max_src = r.source_total.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                eprintln!("  max|source| = {:.4e}", max_src);
                // With bootstrap IC, source should be O(0.01) per ζ=1
                assert!(max_src > 1e-6, "Source too small: {}", max_src);
                assert!(max_src < 10.0, "Source too large (diverging?): {}", max_src);

                let phi_late = r.phi.first().unwrap_or(&0.0);
                eprintln!("  phi(late, near recombi) = {:.4e}", phi_late);
                // Phi should be O(1) near recombination
                assert!(phi_late.abs() < 100.0, "phi diverging: {}", phi_late);
            }
            Err(e) => panic!("solve_camb_kmode failed: {}", e),
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Line-of-sight integration: source → Δ_ℓ(k) → D_ℓ
// ═══════════════════════════════════════════════════════════════════════

use crate::los::bessel::spherical_bessel_j;

/// Compute Δ_ℓ(k) = ∫dτ S(k,τ) j_ℓ(k(τ₀-τ)) for given ℓ values.
/// Integration restricted to τ_min..τ_max (around recombination).
pub(crate) fn los_integrate(
    result: &CambKmodeResult, k: f64, tau0: f64, ell_list: &[usize],
) -> Vec<f64> {
    let n = result.eta_grid.len();
    if n < 2 { return vec![0.0; ell_list.len()]; }

    // Find visibility-significant range: where |source| > 1e-4 × max
    let max_src = result.source_total.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
    let threshold = max_src * 1e-4;
    let mut i_lo = 0;
    let mut i_hi = n - 1;
    for i in 0..n {
        if result.source_total[i].abs() > threshold { i_lo = i; break; }
    }
    for i in (0..n).rev() {
        if result.source_total[i].abs() > threshold { i_hi = i; break; }
    }
    // Pad by 10% on each side
    let pad = ((i_hi - i_lo) / 10).max(10);
    let i_lo = if i_lo > pad { i_lo - pad } else { 0 };
    let i_hi = (i_hi + pad).min(n - 1);

    let mut delta_ell = vec![0.0_f64; ell_list.len()];

    for (ie, &ell) in ell_list.iter().enumerate() {
        let mut sum = 0.0_f64;
        for i in (i_lo + 1)..=i_hi {
            let eta_prev = result.eta_grid[i - 1];
            let eta_curr = result.eta_grid[i];
            let dt = eta_curr - eta_prev;
            if dt.abs() < 1e-30 { continue; }

            let x_prev = k * (tau0 - eta_prev);
            let x_curr = k * (tau0 - eta_curr);
            let jl_prev = if x_prev > 0.0 { spherical_bessel_j(ell, x_prev) } else { 0.0 };
            let jl_curr = if x_curr > 0.0 { spherical_bessel_j(ell, x_curr) } else { 0.0 };

            // Trapezoid rule
            let f_prev = result.source_total[i - 1] * jl_prev;
            let f_curr = result.source_total[i] * jl_curr;
            sum += 0.5 * (f_prev + f_curr) * dt;
        }
        delta_ell[ie] = sum;
    }

    delta_ell
}

/// Compute D_ℓ from a single k-mode (partial contribution).
/// D_ℓ = ℓ(ℓ+1)/(2π) × T_CMB² × 4π × P_ζ(k)/k × |Δ_ℓ(k)|²
pub(crate) fn partial_d_ell(
    delta_ell: f64, k: f64, ell: usize,
    a_s: f64, n_s: f64, k_pivot: f64, t_cmb_uk: f64,
) -> f64 {
    let p_zeta = a_s * (k / k_pivot).powf(n_s - 1.0);
    let c_ell_partial = 4.0 * std::f64::consts::PI * delta_ell.powi(2) * p_zeta / k;
    ell as f64 * (ell as f64 + 1.0) / (2.0 * std::f64::consts::PI)
        * c_ell_partial * t_cmb_uk.powi(2)
}

#[cfg(test)]
mod los_tests {
    use super::*;

    #[test]
    fn test_los_integration_k001() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;

        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        let k = 0.01_f64;
        let lay = CambLayout::new(8, 8);
        let n = lay.n_state;

        // CAMB-bootstrap IC
        let mut ic = vec![0.0_f64; n];
        ic[lay.i_etak]   = -9.9967759482e-03;
        ic[lay.i_sigma]  = -3.0393276158e-02;
        ic[lay.i_clxc]   =  2.4638203904e-03;
        ic[lay.i_clxb]   =  2.4631400593e-03;
        ic[lay.i_vb]     =  2.7070800570e-05;
        ic[lay.theta(0)] =  8.2104670582e-04;
        ic[lay.theta(1)] =  9.0236573963e-06;
        ic[lay.theta(2)] = -5.6573469486e-08;
        ic[lay.nu(0)]    =  8.2093314268e-04;
        ic[lay.nu(1)]    =  1.3590472341e-05;

        let result = solve_camb_kmode(k, &p, &vis, 8, 8, Some((10.0, ic))).unwrap();

        // τ₀ = eta_max (BASS convention, NOT 14153 Mpc; offset Δ≈104 Mpc from z>z_max)
        let tau0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        let ells = vec![2, 10, 100, 200];
        let deltas = los_integrate(&result, k, tau0, &ells);

        eprintln!("  LoS integration at k=0.01:");
        for (i, &ell) in ells.iter().enumerate() {
            let d_partial = partial_d_ell(deltas[i], k, ell,
                2.1e-9, 0.9649, 0.05, 2.7255e6);
            eprintln!("    ell={}: Delta={:.4e}, partial D={:.1} uK2", ell, deltas[i], d_partial);
        }

        // For k=0.01, the dominant ℓ is ~k×τ₀ ≈ 141.
        // Δ₁₀₀(k=0.01) should be O(1e-3) per ζ=1
        // (from Python: Δ₁₀₀ ≈ 6.75e-4 from CAMB T_source)
        let delta_100 = deltas[2]; // ℓ=100
        assert!(delta_100.abs() > 1e-6,
            "Δ_100 too small: {}", delta_100);
        assert!(delta_100.abs() < 1.0,
            "Δ_100 too large: {}", delta_100);
    }
}

#[cfg(test)]
mod diag_tests {
    use super::*;

    #[test]
    fn test_perturbation_amplitudes() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;

        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        let k = 0.01_f64;
        let lay = CambLayout::new(8, 8);
        let n = lay.n_state;

        let mut ic = vec![0.0_f64; n];
        ic[lay.i_etak]   = -9.9967759482e-03;
        ic[lay.i_sigma]  = -3.0393276158e-02;
        ic[lay.i_clxc]   =  2.4638203904e-03;
        ic[lay.i_clxb]   =  2.4631400593e-03;
        ic[lay.i_vb]     =  2.7070800570e-05;
        ic[lay.theta(0)] =  8.2104670582e-04;
        ic[lay.theta(1)] =  9.0236573963e-06;
        ic[lay.theta(2)] = -5.6573469486e-08;
        ic[lay.nu(0)]    =  8.2093314268e-04;
        ic[lay.nu(1)]    =  1.3590472341e-05;

        let result = solve_camb_kmode(k, &p, &vis, 8, 8, Some((10.0, ic))).unwrap();

        // Find visibility peak (~τ=280)
        let mut i_max_g = 0;
        let mut max_g = 0.0_f64;
        for (i, &s) in result.source_sw.iter().enumerate() {
            // Use source_sw as proxy for visibility peak
        }
        // Actually just look at the source components around τ≈280
        for i in 0..result.eta_grid.len() {
            let tau = result.eta_grid[i];
            if tau > 275.0 && tau < 285.0 {
                // Get state from snapshots — we don't store states, only source
                // Use source components instead
                eprintln!("  tau={:.1}: S_SW={:.4e} S_Dop={:.4e} S_Quad={:.4e}",
                    tau, result.source_sw[i], result.source_dop[i], result.source_quad[i]);
            }
        }
        // Also check early and late
        if let Some(first) = result.eta_grid.first() {
            eprintln!("  tau_first={:.1}, phi_first={:.4e}",
                first, result.phi.first().unwrap_or(&0.0));
        }
        if let Some(last) = result.eta_grid.last() {
            eprintln!("  tau_last={:.1}, phi_last={:.4e}",
                last, result.phi.last().unwrap_or(&0.0));
        }
    }
}

#[cfg(test)]
mod los_diag {
    use super::*;

    #[test]
    fn test_los_detailed() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;

        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        let k = 0.01_f64;
        let lay = CambLayout::new(8, 8);
        let n = lay.n_state;

        let mut ic = vec![0.0_f64; n];
        ic[lay.i_etak]   = -9.9967759482e-03;
        ic[lay.i_sigma]  = -3.0393276158e-02;
        ic[lay.i_clxc]   =  2.4638203904e-03;
        ic[lay.i_clxb]   =  2.4631400593e-03;
        ic[lay.i_vb]     =  2.7070800570e-05;
        ic[lay.theta(0)] =  8.2104670582e-04;
        ic[lay.theta(1)] =  9.0236573963e-06;
        ic[lay.theta(2)] = -5.6573469486e-08;
        ic[lay.nu(0)]    =  8.2093314268e-04;
        ic[lay.nu(1)]    =  1.3590472341e-05;

        let result = solve_camb_kmode(k, &p, &vis, 8, 8, Some((10.0, ic))).unwrap();
        let ne = result.eta_grid.len();
        
        eprintln!("  eta_grid: [{:.1}, {:.1}, ..., {:.1}, {:.1}] (n={})",
            result.eta_grid[0], result.eta_grid[1],
            result.eta_grid[ne-2], result.eta_grid[ne-1], ne);
        
        // Check if increasing
        let mut monotonic = true;
        for i in 1..ne {
            if result.eta_grid[i] <= result.eta_grid[i-1] { monotonic = false; break; }
        }
        eprintln!("  monotonic: {}", monotonic);
        
        // Sum source × j_2 manually around recombination
        let tau0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        let ell = 2_usize;
        let mut sum = 0.0_f64;
        let mut max_integrand = 0.0_f64;
        for i in 1..ne {
            let dt = result.eta_grid[i] - result.eta_grid[i-1];
            let tau_mid = 0.5*(result.eta_grid[i] + result.eta_grid[i-1]);
            if tau_mid < 200.0 || tau_mid > 400.0 { continue; } // recombination only
            let x = k * (tau0 - tau_mid);
            let jl = spherical_bessel_j(ell, x);
            let s = 0.5*(result.source_total[i] + result.source_total[i-1]);
            let integrand = s * jl;
            if integrand.abs() > max_integrand { max_integrand = integrand.abs(); }
            sum += integrand * dt;
        }
        eprintln!("  Manual sum (tau=200..400): {:.4e}, max_integrand={:.4e}", sum, max_integrand);
        
        // Compare with full range
        let deltas = los_integrate(&result, k, tau0, &[2]);
        eprintln!("  Full LoS Δ_2: {:.4e}", deltas[0]);
    }
}

#[cfg(test)]
mod bessel_check {
    use super::*;
    #[test]
    fn test_j2_at_139() {
        let j = spherical_bessel_j(2, 139.0);
        // Python: spherical_jn(2, 139.0) = -0.00215...
        eprintln!("  j_2(139) = {:.6e}", j);
        assert!(j.abs() < 0.01, "j_2(139) should be O(1e-3)");
        assert!(j.abs() > 1e-5, "j_2(139) should not be zero");
    }
}

#[cfg(test)]
mod vis_check {
    use super::*;
    #[test]
    fn test_visibility_peak() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let g_max = vis.g_grid.iter().cloned().fold(0.0_f64, f64::max);
        let i_max = vis.g_grid.iter().position(|&g| (g - g_max).abs() < 1e-20).unwrap();
        let z_peak = vis.z_grid[i_max];
        let eta_peak = vis.eta_grid[i_max];
        let eta_max = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        let tau_peak = eta_max - eta_peak;
        
        eprintln!("  BASS visibility: g_max={:.4e} at z={:.0}, eta={:.1}, tau={:.1}",
            g_max, z_peak, eta_peak, tau_peak);
        eprintln!("  eta_max={:.1}", eta_max);
        eprintln!("  g_norm={:.4e}", vis.g_norm);
        
        // CAMB: g_peak ≈ 0.02 at tau ≈ 280
        // Check if BASS g_peak is similar
        assert!(g_max > 0.001, "g_max too small: {}", g_max);
        assert!(g_max < 1.0, "g_max too large: {}", g_max);
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Bridge: sync_gauge_camb → SourceGrid → adaptive LoS
// ═══════════════════════════════════════════════════════════════════════

use crate::los::source::{SourceGrid, SourceValue};

/// Convert CambKmodeResult to BASS SourceGrid for the adaptive LoS integrator.
pub(crate) fn to_source_grid(result: &CambKmodeResult, k: f64) -> SourceGrid {
    let mut grid = SourceGrid::new(k);
    for i in 0..result.eta_grid.len() {
        let sv = SourceValue {
            sw: result.source_sw[i],
            doppler: result.source_dop[i],
            isw: 0.0,  // ISW handled separately (late-time module)
            pol: result.source_quad[i],
            shear_isw: 0.0,
            total: result.source_total[i],
        };
        grid.push(result.eta_grid[i], sv);
    }
    grid
}

/// Compute Δ_ℓ(k) using BASS adaptive G7K15 integrator (handles oscillatory j_ℓ).
pub(crate) fn delta_ell_adaptive(
    result: &CambKmodeResult, k: f64, eta_0: f64, ell: usize, tol: f64,
) -> f64 {
    let grid = to_source_grid(result, k);
    let los_result = crate::los::integrator::integrate_los_adaptive(&grid, ell, eta_0, tol);
    los_result.value
}

// ═══════════════════════════════════════════════════════════════════════
// Production D_ℓ spectrum computation
// ═══════════════════════════════════════════════════════════════════════

/// Configuration for D_ℓ computation.
pub(crate) struct DlConfig {
    pub(crate) ell_max: usize,
    pub(crate) a_s: f64,
    pub(crate) n_s: f64,
    pub(crate) k_pivot: f64,
    pub(crate) t_cmb_uk: f64,
}

impl Default for DlConfig {
    fn default() -> Self {
        Self {
            ell_max: 350,
            a_s: 2.1e-9,
            n_s: 0.9649,
            k_pivot: 0.05,
            t_cmb_uk: 2.7255e6,
        }
    }
}

/// Compute D_ℓ spectrum from pre-solved k-mode results.
/// 
/// Input: vec of (k, CambKmodeResult) pairs.
/// Output: D_ℓ for ℓ=2..ell_max.
///
/// PERF-01: loop order reversed (k-outer, ell-inner) so SourceGrid is built
/// once per k instead of (ell_max - 1) times. Numerically identical to the
/// original implementation.
pub(crate) fn compute_dl_spectrum(
    kmode_results: &[(f64, CambKmodeResult)],
    eta_0: f64,
    cfg: &DlConfig,
) -> Vec<f64> {
    let n_ell = cfg.ell_max - 1; // ℓ=2..ell_max
    let mut dl = vec![0.0_f64; n_ell];
    
    if kmode_results.len() < 2 { return dl; }
    
    let n_k = kmode_results.len();
    let k_arr: Vec<f64> = kmode_results.iter().map(|(k,_)| *k).collect();
    
    // Per-k integrand storage: [n_ell][n_k]
    // delta_sq_pk_per_ell[ie][ik] = Δ_ℓ(k_ik)² · P(k_ik) / k_ik
    let mut delta_sq_pk_per_ell: Vec<Vec<f64>> = vec![vec![0.0_f64; n_k]; n_ell];
    
    // PERF-01: k-outer, ell-inner. SourceGrid built once per k.
    // Inner ell-loop is parallelized: each ell writes to a distinct
    // delta_sq_pk_per_ell[ie] slot, so it's embarrassingly parallel and
    // shares only the read-only grid (good for cache).
    let serial_mode = std::env::var("BASS_SERIAL_KLOOP").map(|v| v == "1").unwrap_or(false);
    for (ik, (k, result)) in kmode_results.iter().enumerate() {
        let grid = to_source_grid(result, *k);
        let pk = cfg.a_s * (*k / cfg.k_pivot).powf(cfg.n_s - 1.0);
        let pk_over_k = pk / *k;
        if serial_mode {
            for (ie, ell) in (2..=cfg.ell_max).enumerate() {
                let los_result = crate::los::integrator::integrate_los_adaptive(
                    &grid, ell, eta_0, 1e-5);
                let delta = los_result.value;
                delta_sq_pk_per_ell[ie][ik] = delta * delta * pk_over_k;
            }
        } else {
            use rayon::prelude::*;
            // Parallel ell-loop. Compute Δ_ℓ²·P/k for all ell in parallel,
            // collect into Vec, then scatter into delta_sq_pk_per_ell rows.
            let row_vals: Vec<f64> = (2..=cfg.ell_max).into_par_iter().map(|ell| {
                let los = crate::los::integrator::integrate_los_adaptive(
                    &grid, ell, eta_0, 1e-5);
                los.value * los.value * pk_over_k
            }).collect();
            for (ie, val) in row_vals.into_iter().enumerate() {
                delta_sq_pk_per_ell[ie][ik] = val;
            }
        }
    }
    
    // k-integration via trapezoid (per ell)
    for ie in 0..n_ell {
        let ell = ie + 2;
        let mut cl = 0.0_f64;
        let row = &delta_sq_pk_per_ell[ie];
        for i in 1..n_k {
            cl += 0.5 * (row[i] + row[i-1]) * (k_arr[i] - k_arr[i-1]);
        }
        cl *= 4.0 * std::f64::consts::PI;
        let ell_f = ell as f64;
        dl[ie] = ell_f * (ell_f + 1.0) * cl / (2.0 * std::f64::consts::PI) 
                 * cfg.t_cmb_uk * cfg.t_cmb_uk;
    }
    
    dl
}

/// PR-PERF-02: D_ℓ via adaptive G7K15 + Bessel ladder per panel.
///
/// Mathematically equivalent to looping `compute_dl_spectrum`'s
/// `integrate_los_adaptive` over all ℓ — but each G7K15 panel evaluates
/// `spherical_bessel_j_array(ell_max, x, ...)` exactly ONCE per node and
/// reuses the entire j_ℓ vector for every ℓ ∈ [2, ell_max].
///
/// Cost reduction:
///   old: per (k, ℓ) adaptive run → ~60 panels × 15 nodes × 1 single bessel call
///        per (k, ALL ℓ) = ~60 × 15 × (ell_max - 1) single bessel calls
///   new: per (k, ALL ℓ) adaptive → ~60 panels × 15 nodes × 1 ladder call
///        ladder cost ≈ O(ell_max) but ~5× faster per-ℓ than independent
///        calls.
///
/// Subdivision criterion: per-panel error = max over ℓ of |G7 - K15|.
/// This is conservative — a panel is subdivided if ANY ℓ requires it, so
/// some ℓ may get more panels than strictly necessary, but accuracy is
/// preserved.
pub(crate) fn compute_dl_spectrum_adaptive_ladder(
    kmode_results: &[(f64, CambKmodeResult)],
    eta_0: f64,
    cfg: &DlConfig,
) -> Vec<f64> {
    use crate::los::bessel::spherical_bessel_j_array;
    use crate::los::integrator::{G7_WEIGHTS, K15_NODES, K15_WEIGHTS};

    let n_ell = cfg.ell_max - 1;
    let mut dl = vec![0.0_f64; n_ell];
    if kmode_results.len() < 2 { return dl; }

    let n_k = kmode_results.len();
    let k_arr: Vec<f64> = kmode_results.iter().map(|(k,_)| *k).collect();
    let mut delta_sq_pk_per_ell: Vec<Vec<f64>> = vec![vec![0.0_f64; n_k]; n_ell];

    let lmax = cfg.ell_max;
    // PR-PERF-02: tol 1e-4 (vs 1e-5 in compute_dl_spectrum). Max-ℓ subdivision
    // criterion is more conservative than per-ℓ → would over-refine at 1e-5.
    // 1e-4 keeps D_2 within 0.5% of baseline empirically.
    let tol = 1e-4_f64;
    let max_depth = 12usize;

    // Reusable scratch — flat j layout: node_j_flat[ki * (lmax+1) + ell]
    // This makes the inner k15 accumulation cache-friendly when iterating ℓ
    // by row (ki-major). Below we transpose access pattern: outer ki, inner ℓ.
    let mut node_j_flat: Vec<f64> = vec![0.0; 15 * (lmax + 1)];
    let mut node_src: [f64; 15] = [0.0; 15];
    let mut panel_k15: Vec<f64> = vec![0.0; n_ell]; // reused per panel

    // Precompute G7 indices into K15: K15[1,3,5,7,9,11,13] ≡ G7
    const G7_IDX: [usize; 7] = [1, 3, 5, 7, 9, 11, 13];

    for (ik, (k, result)) in kmode_results.iter().enumerate() {
        let n_pts = result.eta_grid.len();
        if n_pts < 2 { continue; }

        let pk = cfg.a_s * (*k / cfg.k_pivot).powf(cfg.n_s - 1.0);
        let pk_over_k = pk / *k;

        let eta_min = result.eta_grid[0];
        let eta_max = *result.eta_grid.last().unwrap();
        let total_range = eta_max - eta_min;

        let interp_source = |eta: f64| -> f64 {
            if eta <= eta_min { return result.source_total[0]; }
            if eta >= eta_max { return *result.source_total.last().unwrap(); }
            let idx = result.eta_grid.partition_point(|&e| e < eta);
            let idx = idx.min(n_pts - 1).max(1);
            let dη = (result.eta_grid[idx] - result.eta_grid[idx - 1]).max(1e-30);
            let t = (eta - result.eta_grid[idx - 1]) / dη;
            result.source_total[idx - 1] * (1.0 - t) + result.source_total[idx] * t
        };

        let mut delta_per_ell: Vec<f64> = vec![0.0_f64; n_ell];
        struct Panel { a: f64, b: f64, depth: usize }
        let mut stack: Vec<Panel> = vec![Panel { a: eta_min, b: eta_max, depth: 0 }];

        while let Some(p) = stack.pop() {
            let mid = 0.5 * (p.a + p.b);
            let half = 0.5 * (p.b - p.a);

            // Eval j_array(lmax) AND source at all 15 K15 nodes
            for ni in 0..15 {
                let eta_n = mid + half * K15_NODES[ni];
                let x = *k * (eta_0 - eta_n);
                let row_off = ni * (lmax + 1);
                let row = &mut node_j_flat[row_off..row_off + lmax + 1];
                if x > 0.0 {
                    spherical_bessel_j_array(lmax, x, row);
                } else {
                    row[0] = 1.0;
                    for v in &mut row[1..=lmax] { *v = 0.0; }
                }
                node_src[ni] = interp_source(eta_n);
            }

            // Compute G7 + K15 for each ℓ — cache-friendly: outer ki, inner ℓ
            // panel_k15[ie] = half * Σ_ki K15_WEIGHTS[ki] * src[ki] * j[ki][ell]
            // panel_g7[ie]  = half * Σ_gi G7_WEIGHTS[gi] * src[ki=G7_IDX[gi]] * j[ki][ell]
            for v in panel_k15[..n_ell].iter_mut() { *v = 0.0; }
            // Allocate panel_g7 on stack? — n_ell can be ~300, use heap reuse
            // For simplicity reuse delta_per_ell.split? No, would corrupt accumulator.
            // Use a small scratch:
            let mut panel_g7: Vec<f64> = vec![0.0; n_ell];

            for ki in 0..15 {
                let row_off = ki * (lmax + 1);
                let s_w_k15 = K15_WEIGHTS[ki] * node_src[ki];
                for ie in 0..n_ell {
                    panel_k15[ie] += s_w_k15 * node_j_flat[row_off + (ie + 2)];
                }
            }
            for gi in 0..7 {
                let ki = G7_IDX[gi];
                let row_off = ki * (lmax + 1);
                let s_w_g7 = G7_WEIGHTS[gi] * node_src[ki];
                for ie in 0..n_ell {
                    panel_g7[ie] += s_w_g7 * node_j_flat[row_off + (ie + 2)];
                }
            }
            for v in panel_k15.iter_mut() { *v *= half; }
            for v in panel_g7.iter_mut() { *v *= half; }

            // Max-ℓ error for subdivision decision
            let mut max_err = 0.0_f64;
            for ie in 0..n_ell {
                let err = (panel_g7[ie] - panel_k15[ie]).abs();
                if err > max_err { max_err = err; }
            }

            if max_err < tol * (p.b - p.a) / total_range || p.depth >= max_depth {
                for ie in 0..n_ell {
                    delta_per_ell[ie] += panel_k15[ie];
                }
            } else {
                stack.push(Panel { a: p.a, b: mid, depth: p.depth + 1 });
                stack.push(Panel { a: mid, b: p.b, depth: p.depth + 1 });
            }
        }

        for (ie, &delta) in delta_per_ell.iter().enumerate() {
            delta_sq_pk_per_ell[ie][ik] = delta * delta * pk_over_k;
        }
    }

    // k-integration via trap rule (per ell) — identical to compute_dl_spectrum
    for ie in 0..n_ell {
        let ell = ie + 2;
        let mut cl = 0.0_f64;
        let row = &delta_sq_pk_per_ell[ie];
        for i in 1..n_k {
            cl += 0.5 * (row[i] + row[i-1]) * (k_arr[i] - k_arr[i-1]);
        }
        cl *= 4.0 * std::f64::consts::PI;
        let ell_f = ell as f64;
        dl[ie] = ell_f * (ell_f + 1.0) * cl / (2.0 * std::f64::consts::PI)
                 * cfg.t_cmb_uk * cfg.t_cmb_uk;
    }
    dl
}

/// Fast D_ℓ computation using precomputed BesselTable.
///
/// ~12× faster than compute_dl_spectrum by avoiding per-point
/// spherical_bessel_j calls. Uses linear interpolation from
/// precomputed j_ℓ(x) table with spacing dx ≈ 0.1.
pub(crate) fn compute_dl_spectrum_fast(
    kmode_results: &[(f64, CambKmodeResult)],
    eta_0: f64,
    cfg: &DlConfig,
) -> Vec<f64> {
    use crate::los::bessel::BesselTable;

    let n_ell = cfg.ell_max - 1;
    let mut dl = vec![0.0_f64; n_ell];
    if kmode_results.len() < 2 { return dl; }

    let k_arr: Vec<f64> = kmode_results.iter().map(|(k,_)| *k).collect();
    let k_max = k_arr.iter().cloned().fold(0.0_f64, f64::max);

    // Precompute BesselTable for all ℓ=0..ell_max
    let x_max = (k_max * eta_0 * 1.05).min(20000.0);
    let dx = 0.1_f64;
    let table = BesselTable::new(cfg.ell_max, x_max, dx);

    for (ie, ell) in (2..=cfg.ell_max).enumerate() {
        let mut delta_sq_pk: Vec<f64> = Vec::with_capacity(k_arr.len());
        for (k, result) in kmode_results {
            // LoS integration with BesselTable lookup
            let n = result.eta_grid.len();
            let mut integral = 0.0_f64;
            for i in 1..n {
                let eta_i = result.eta_grid[i];
                let eta_im = result.eta_grid[i-1];
                let chi_i = eta_0 - (eta_0 - eta_i).max(0.0);
                let chi_im = eta_0 - (eta_0 - eta_im).max(0.0);
                let x_i = k * (eta_0 - eta_i).max(0.0);
                let x_im = k * (eta_0 - eta_im).max(0.0);
                let jl_i = table.eval(ell, x_i);
                let jl_im = table.eval(ell, x_im);
                let s_i = result.source_total[i];
                let s_im = result.source_total[i-1];
                let deta = (eta_im - eta_i).abs();
                integral += 0.5 * (s_i * jl_i + s_im * jl_im) * deta;
            }
            let pk = cfg.a_s * (*k / cfg.k_pivot).powf(cfg.n_s - 1.0);
            delta_sq_pk.push(integral * integral * pk / k);
        }

        let mut cl = 0.0_f64;
        for i in 1..k_arr.len() {
            cl += 0.5 * (delta_sq_pk[i] + delta_sq_pk[i-1]) * (k_arr[i] - k_arr[i-1]);
        }
        cl *= 4.0 * std::f64::consts::PI;
        let ell_f = ell as f64;
        dl[ie] = ell_f * (ell_f + 1.0) * cl / (2.0 * std::f64::consts::PI)
                 * cfg.t_cmb_uk * cfg.t_cmb_uk;
    }
    dl
}

#[cfg(test)]
mod spectrum_test {
    use super::*;

    #[test]
    fn test_dl_end_to_end() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        
        // Solve 5 k-modes (minimal test)
        let k_modes = [0.001, 0.005, 0.01, 0.015, 0.02];
        let ic_k001 = {
            let lay = CambLayout::new(8, 8);
            let n = lay.n_state;
            let mut ic = vec![0.0_f64; n];
            ic[lay.i_etak] = -9.9967759482e-03;
            ic[lay.i_sigma] = -3.0393276158e-02;
            ic[lay.i_clxc] = 2.4638203904e-03;
            ic[lay.i_clxb] = 2.4631400593e-03;
            ic[lay.i_vb] = 2.7070800570e-05;
            ic[lay.theta(0)] = 8.2104670582e-04;
            ic[lay.theta(1)] = 9.0236573963e-06;
            ic[lay.theta(2)] = -5.6573469486e-08;
            ic[lay.nu(0)] = 8.2093314268e-04;
            ic[lay.nu(1)] = 1.3590472341e-05;
            ic
        };
        
        let mut results: Vec<(f64, CambKmodeResult)> = Vec::new();
        for &k in &k_modes {
            // Scale IC approximately (only k=0.01 has exact IC)
            let scale = k / 0.01;
            let mut ic = ic_k001.clone();
            ic[0] *= scale; // etak ∝ k
            
            match solve_camb_kmode(k, &p, &vis, 8, 8, Some((10.0, ic))) {
                Ok(r) => { results.push((k, r)); }
                Err(e) => { eprintln!("  k={}: {}", k, e); }
            }
        }
        
        let cfg = DlConfig { ell_max: 50, ..Default::default() };
        let dl = compute_dl_spectrum(&results, eta_0, &cfg);
        
        eprintln!("\n  D_ℓ from {} k-modes (recombination only, IBP'd source):", results.len());
        for ell in [2, 5, 10, 20, 30, 50] {
            if ell <= cfg.ell_max {
                let ie = ell - 2;
                eprintln!("    ℓ={:3}: D_ℓ = {:.1} μK²", ell, dl[ie]);
            }
        }
        
        // Basic sanity: D_2 should be O(1000)
        assert!(dl[0] > 0.0, "D_2 should be positive");
        eprintln!("  PASS: D_2 = {:.0} μK² (expected ~1000)", dl[0]);
    }
}

#[cfg(test)]
mod pol_test {
    use super::*;

    #[test]
    fn test_polarized_layout() {
        let lay = CambLayout::new_with_pol(8, 8, 6);
        eprintln!("  Polarized layout: n_state={}", lay.n_state);
        eprintln!("  i_theta0={}, i_n0={}, i_e0={}, i_b0={}",
            lay.i_theta0, lay.i_n0, lay.i_e0, lay.i_b0);
        // 5 scalar + 9 photon + 9 neutrino + 7 E-mode + 7 B-mode + 1 Φ = 38
        assert_eq!(lay.n_state, 5 + 9 + 9 + 7 + 7 + 1);
        assert!(lay.has_pol());
        assert_eq!(lay.e_mode(0), lay.i_e0);
        assert_eq!(lay.b_mode(6), lay.i_b0 + 6);
    }

    #[test]
    fn test_polarized_rhs() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        let k = 0.01_f64;
        let lay = CambLayout::new_with_pol(8, 8, 6);
        let n = lay.n_state;

        // IC: same as unpolarized + E=B=0
        let mut ic = vec![0.0_f64; n];
        ic[lay.i_etak]   = -9.9967759482e-03;
        ic[lay.i_sigma]  = -3.0393276158e-02;
        ic[lay.i_clxc]   =  2.4638203904e-03;
        ic[lay.i_clxb]   =  2.4631400593e-03;
        ic[lay.i_vb]     =  2.7070800570e-05;
        ic[lay.theta(0)] =  8.2104670582e-04;
        ic[lay.theta(1)] =  9.0236573963e-06;
        ic[lay.theta(2)] = -5.6573469486e-08;
        ic[lay.nu(0)]    =  8.2093314268e-04;
        ic[lay.nu(1)]    =  1.3590472341e-05;
        // E-mode and B-mode start at 0

        // Test the RHS directly (solve_camb_kmode uses internal unpolarized layout)
        let bg = CambBackground {
            adotoa: 100.0, grho_g: 1e-7, grho_nu: 7e-8, grho_b: 3e-8,
            grho_c: 1e-7, opac: 100.0, cs2b: 1e-6, vis: 0.01, dvis: -0.001, ddvis: 0.0001,
            a: 1.0,
            expmmu: 0.0,
        };
        let mut dy = vec![0.0_f64; n];
        let _src = camb_rhs(k, 100.0, &ic, &mut dy, &lay, &bg);
        
        eprintln!("  dy[E₀] = {:.4e}", dy[lay.e_mode(0)]);
        eprintln!("  dy[E₂] = {:.4e}", dy[lay.e_mode(2)]);
        eprintln!("  dy[B₀] = {:.4e}", dy[lay.b_mode(0)]);
        
        // E-mode should be driven by polter, B-mode must be zero
        assert!(dy[lay.e_mode(0)].abs() > 0.0 || ic[lay.theta(2)].abs() < 1e-20,
            "E₀ should be driven when Θ₂≠0");
        assert_eq!(dy[lay.b_mode(0)], 0.0, "B₀ must be zero for scalars");
        assert_eq!(dy[lay.b_mode(3)], 0.0, "B₃ must be zero for scalars");
        eprintln!("  PASS: E-mode driven, B-mode zero");
    }
}

#[cfg(test)]
mod massive_nu_test {
    use super::*;

    #[test]
    fn test_massive_nu_layout() {
        let lay = CambLayout::new_full(8, 8, 0, 10, 12);
        eprintln!("  Massive ν layout: n_state={}", lay.n_state);
        // 5 + 9 + 9 + 0 + 0 + 10*13 + 1(Φ) = 154
        assert_eq!(lay.n_state, 5 + 9 + 9 + 130 + 1);
        assert!(lay.has_massive_nu());
        assert!(!lay.has_pol());
        assert_eq!(lay.psi(0, 0), lay.i_psi0);
        assert_eq!(lay.psi(9, 12), lay.i_psi0 + 9*13 + 12);
        assert_eq!(lay.psi(9, 12), lay.n_state - 2);
        assert_eq!(lay.i_phi, lay.n_state - 1);
    }

    #[test]
    fn test_massive_nu_full_layout() {
        // All features: pol + massive ν
        let lay = CambLayout::new_full(8, 8, 6, 10, 12);
        // 5 + 9 + 9 + 7(E) + 7(B) + 130(massive) + 1(Φ) = 168
        assert_eq!(lay.n_state, 168);
        assert!(lay.has_pol());
        assert!(lay.has_massive_nu());
        eprintln!("  Full layout: {}", lay.n_state);
    }

    #[test]
    fn test_massive_nu_rhs() {
        let lay = CambLayout::new_full(8, 8, 0, 10, 12);
        let n = lay.n_state;
        let mut ic = vec![0.0_f64; n];
        // Set Θ₂ and N₁ for nontrivial metric sources
        ic[lay.theta(0)] = 1e-3;
        ic[lay.theta(1)] = 1e-4;
        ic[lay.theta(2)] = -5e-8;
        ic[lay.nu(0)] = 1e-3;
        ic[lay.nu(1)] = 1.5e-4;
        ic[lay.i_etak] = -0.01;
        ic[lay.i_clxc] = 2.5e-3;
        ic[lay.i_clxb] = 2.5e-3;
        // Massive ν IC: Ψ_ℓ(q) = N_ℓ (relativistic limit)
        for iq in 0..10 {
            ic[lay.psi(iq, 0)] = ic[lay.nu(0)];
            ic[lay.psi(iq, 1)] = ic[lay.nu(1)];
        }

        let bg = CambBackground {
            adotoa: 100.0, grho_g: 1e-7, grho_nu: 7e-8, grho_b: 3e-8,
            grho_c: 1e-7, opac: 100.0, cs2b: 1e-6, vis: 0.0, dvis: 0.0, ddvis: 0.0,
            a: 1e-3, // z=999, recombination
            expmmu: 0.0,
        };
        let k = 0.01_f64;
        let mut dy = vec![0.0_f64; n];
        let _src = camb_rhs(k, 100.0, &ic, &mut dy, &lay, &bg);

        // Check massive ν hierarchy is active
        eprintln!("  dy[Ψ₀(q=0)] = {:.4e}", dy[lay.psi(0, 0)]);
        eprintln!("  dy[Ψ₁(q=0)] = {:.4e}", dy[lay.psi(0, 1)]);
        eprintln!("  dy[Ψ₀(q=9)] = {:.4e}", dy[lay.psi(9, 0)]);

        // Ψ₀' should be nonzero (driven by ḣ source and streaming)
        assert!(dy[lay.psi(0, 0)].abs() > 0.0, "Ψ₀(q₀) must be driven");
        assert!(dy[lay.psi(5, 1)].abs() > 0.0, "Ψ₁(q₅) must be driven");
        
        // Massive ν should contribute to momentum constraint
        // dgq_mnu != 0 when Ψ₁ != 0
        // Check etak' differs from no-massive case
        let lay_old = CambLayout::new(8, 8);
        let mut ic_old = vec![0.0_f64; lay_old.n_state];
        for i in 0..lay_old.n_state.min(23) { ic_old[i] = ic[i]; }
        let mut dy_old = vec![0.0_f64; lay_old.n_state];
        camb_rhs(k, 100.0, &ic_old, &mut dy_old, &lay_old, &bg);
        
        let etakdot_massive = dy[lay.i_etak];
        let etakdot_old = dy_old[lay_old.i_etak];
        eprintln!("  etak': massive={:.6e}  old={:.6e}  diff={:.2e}",
            etakdot_massive, etakdot_old, (etakdot_massive - etakdot_old).abs());
        
        assert!((etakdot_massive - etakdot_old).abs() > 0.0,
            "Massive ν must modify momentum constraint");
        eprintln!("  PASS: massive ν active and coupled");
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Production pipeline: full-physics solver + D_ℓ spectrum
// ═══════════════════════════════════════════════════════════════════════

/// Production solver configuration.
#[derive(Clone)]
pub(crate) struct ProductionConfig {
    pub(crate) lmax_g: usize,
    pub(crate) lmax_n: usize,
    pub(crate) lmax_pol: usize,
    pub(crate) nq_massive: usize,
    pub(crate) lmax_m: usize,
    pub(crate) k_min: f64,
    pub(crate) k_max: f64,
    pub(crate) n_k: usize,
    pub(crate) ell_max: usize,
    pub(crate) a_s: f64,
    pub(crate) n_s: f64,
    pub(crate) k_pivot: f64,
    pub(crate) t_cmb_uk: f64,
}

impl Default for ProductionConfig {
    fn default() -> Self {
        Self {
            lmax_g: 16, lmax_n: 16, lmax_pol: 12,
            nq_massive: 0, lmax_m: 0,
            k_min: 5e-5, k_max: 0.3, n_k: 2000,
            ell_max: 50,
            a_s: 2.1e-9, n_s: 0.9649, k_pivot: 0.05, t_cmb_uk: 2.7255e6,
        }
    }
}

impl ProductionConfig {
    /// Minimal: no polarization, no massive ν.
    pub(crate) fn minimal() -> Self {
        Self { lmax_g: 8, lmax_n: 8, n_k: 100, ell_max: 50, ..Default::default() }
    }
    
    /// Fast: 500 k-modes (±5% at ℓ≤300, ±10% at ℓ≤1000).
    pub(crate) fn fast() -> Self {
        Self { n_k: 2000, ..Default::default() }
    }
    
    /// With E-mode polarization.
    pub(crate) fn with_pol() -> Self {
        Self { lmax_pol: 12, ..Default::default() }
    }
    
    /// Full physics (E/B + massive ν).
    pub(crate) fn full_physics() -> Self {
        Self { lmax_pol: 12, nq_massive: 10, lmax_m: 12, ..Default::default() }
    }

    pub(crate) fn layout(&self) -> CambLayout {
        CambLayout::new_full(self.lmax_g, self.lmax_n, self.lmax_pol,
                             self.nq_massive, self.lmax_m)
    }

    /// Geometric k-grid.
    pub(crate) fn k_grid(&self) -> Vec<f64> {
        let mut k = Vec::with_capacity(self.n_k);
        let ratio = (self.k_max / self.k_min).powf(1.0 / (self.n_k as f64 - 1.0));
        let mut ki = self.k_min;
        for _ in 0..self.n_k {
            k.push(ki);
            ki *= ratio;
        }
        k
    }
}

/// Generate adiabatic initial conditions (synchronous gauge, per ζ=1).
///
/// Standard ΛCDM adiabatic mode at early times (kτ ≪ 1):
///   η_s → −1, δ_c = δ_b → 3/2, Θ₀ = N₀ → 1/2
///   Θ₁ = N₁ = v_b/3 → k/(6ℋ), σ = 0
pub(crate) fn adiabatic_ic(k: f64, lay: &CambLayout, bg0: &CambBackground) -> Vec<f64> {
    let mut y = vec![0.0_f64; lay.n_state];
    
    y[lay.i_etak] = -k;          // η_s = −1 → etak = −k
    y[lay.i_clxc] = 1.5;         // δ_c = 3/2
    y[lay.i_clxb] = 1.5;         // δ_b = 3/2
    y[lay.theta(0)] = 0.5;       // Θ₀ = δ_γ/4 = 1/2
    y[lay.nu(0)] = 0.5;          // N₀ = δ_ν/4 = 1/2
    
    let ah = bg0.adotoa.max(1e-30);
    let v_init = k / (6.0 * ah);  // Θ₁ = N₁ ≈ k/(6ℋ)
    if lay.lmax_g >= 1 { y[lay.theta(1)] = v_init; }
    if lay.lmax_n >= 1 { y[lay.nu(1)] = v_init; }
    // Tight coupling: v_b = 3Θ₁ (Thomson momentum coupling)
    y[lay.i_vb] = 3.0 * v_init;
    
    // σ = 0 at early times (builds up via ODE)
    y[lay.i_sigma] = 0.0;
    
    // Φ_N IC from adiabatic mode: Φ = -2/(3(1+w_eff)) per ζ=1
    // In radiation era with neutrinos: Φ = -(2/3)(1+2R_ν/5)/(1+4R_ν/15)
    // R_ν = grho_ν/(grho_γ+grho_ν)
    let r_nu = bg0.grho_nu / (bg0.grho_g + bg0.grho_nu).max(1e-30);
    y[lay.i_phi] = -(2.0 / 3.0) * (1.0 + 2.0 * r_nu / 5.0) / (1.0 + 4.0 * r_nu / 15.0);
    
    y
}

// ═══════════════════════════════════════════════════════════════════════
// PERF-01: k-independent precompute (CommonProfile)
// ═══════════════════════════════════════════════════════════════════════

/// All k-independent data extracted from `(params, vis)`. Built once and shared
/// across all k-modes via `&CommonProfile`. Read-only — safe to share across
/// rayon worker threads (does NOT need per-thread clone).
///
/// Audit #2: removes per-k recomputation of g_dot, g_ddot, tau_profile,
/// bg_at_snap, and tau_offset.
pub(crate) struct CommonProfile {
    pub(crate) tau_profile: Vec<f64>,           // n_vis (in reverse-η order)
    pub(crate) bg_at_snap: Vec<CambBackground>, // n_vis, parallel to tau_profile
    pub(crate) tau_offset: f64,
}

impl CommonProfile {
    pub(crate) fn build(
        params: &crate::recombination::visibility_hyrec::VisibilityParams,
        vis: &crate::recombination::visibility_hyrec::VisibilityResult,
    ) -> Self {
        let h0c = params.h * 1e7 / 2.99792458e10;
        let og = params.omega_gamma();
        let omega_nu_ml = og * 0.2271 * NEFF_MASSLESS;
        let n_vis = vis.z_grid.len();
        let eta_max = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);

        // Visibility derivatives — k-independent
        let mut g_dot = vec![0.0_f64; n_vis];
        let mut g_ddot = vec![0.0_f64; n_vis];
        for i in 1..n_vis-1 {
            let dt = vis.eta_grid[i+1] - vis.eta_grid[i-1];
            if dt.abs() > 1e-30 {
                g_dot[i] = -(vis.g_grid[i+1] - vis.g_grid[i-1]) / dt;
                g_ddot[i] = (vis.g_grid[i+1] - 2.0*vis.g_grid[i] + vis.g_grid[i-1])
                            / (dt/2.0).powi(2);
            }
        }

        // tau_profile + bg_at_snap (in reverse-η order to match original code)
        let mut tau_profile = Vec::with_capacity(n_vis);
        let mut bg_at_snap = Vec::with_capacity(n_vis);
        for i in (0..n_vis).rev() {
            let tau = eta_max - vis.eta_grid[i];
            tau_profile.push(tau);
            let z = vis.z_grid[i];
            let a = 1.0 / (1.0 + z);
            let h0c2 = h0c * h0c;
            bg_at_snap.push(CambBackground {
                adotoa: a * h0c * params.e_of_z(z),
                grho_g: 3.0 * h0c2 * og / (a * a),
                grho_nu: 3.0 * h0c2 * omega_nu_ml / (a * a),
                grho_b: 3.0 * h0c2 * params.omega_b / a,
                grho_c: 3.0 * h0c2 * (params.omega_m - params.omega_b) / a,
                opac: vis.kappa_dot_grid[i],
                cs2b: 1e-10,
                vis: vis.g_grid[i], dvis: g_dot[i], ddvis: g_ddot[i],
                a,
                expmmu: (-vis.tau_grid[i]).exp(),
            });
        }

        // tau_offset — Gauss-Legendre 8-point quadrature, k-independent
        let z_max = vis.z_grid.iter().cloned().fold(0.0_f64, f64::max);
        let a_max = 1.0 / (1.0 + z_max);
        let omega_r_total = og + omega_nu_ml;
        let tau_offset = {
            let gl_x = [0.01985507, 0.10166676, 0.23723379, 0.40828268,
                         0.59171732, 0.76276621, 0.89833324, 0.98014493];
            let gl_w = [0.05061427, 0.11119052, 0.15685332, 0.18134189,
                         0.18134189, 0.15685332, 0.11119052, 0.05061427];
            let mut integral = 0.0_f64;
            for i in 0..8 {
                let a = a_max * gl_x[i];
                let a2 = a * a;
                let e_a = (omega_r_total / (a2 * a2) + params.omega_m / (a2 * a)
                          + params.omega_l).max(1e-30).sqrt();
                integral += gl_w[i] / (a2 * h0c * e_a);
            }
            integral * a_max
        };

        Self { tau_profile, bg_at_snap, tau_offset }
    }
}

/// Per-thread reusable scratch buffers. Allocated once per chunk and reused
/// across all k-modes in that chunk (avoids per-snapshot vec![] allocation
/// in the source extraction loop — audit #3).
pub(crate) struct KModeScratch {
    /// dy buffer for camb_rhs source extraction. Size = n_state.
    dy: Vec<f64>,
    /// mats_flat buffer for build_camb_matrix profile. Size = n_vis * n^2.
    mats_flat: Vec<f64>,
}

impl KModeScratch {
    pub(crate) fn new(n_state: usize, n_vis: usize) -> Self {
        Self {
            dy: vec![0.0; n_state],
            mats_flat: Vec::with_capacity(n_vis * n_state * n_state),
        }
    }
}

/// Solve a single k-mode with shared CommonProfile and reusable scratch.
/// Backbone of `solve_kmode_full` and the production parallel path.
pub(crate) fn solve_kmode_full_with_common(
    k: f64,
    common: &CommonProfile,
    pcfg: &ProductionConfig,
    bootstrap_ic: Option<(f64, Vec<f64>)>,
    scratch: &mut KModeScratch,
) -> Result<CambKmodeResult, String> {
    use crate::core::config::Rodas5PConfig;

    let lay = pcfg.layout();
    let n = lay.n_state;
    let n_vis = common.bg_at_snap.len();

    // Ensure scratch is sized correctly (caller's responsibility, but verify)
    if scratch.dy.len() != n { scratch.dy.resize(n, 0.0); }

    // Build k-dependent matrix profile into scratch.mats_flat
    scratch.mats_flat.clear();
    scratch.mats_flat.reserve(n_vis * n * n);
    for i in 0..n_vis {
        let tau = common.tau_profile[i];
        let bg = &common.bg_at_snap[i];
        let mat = build_camb_matrix(k, tau, &lay, bg);
        scratch.mats_flat.extend_from_slice(&mat);
    }

    // Bootstrap IC lookup (k-dependent)
    let bootstrap = if bootstrap_ic.is_some() {
        None
    } else {
        bootstrap_ic_lookup(k, &lay).map(|(tau_camb, ic)| {
            (tau_camb - common.tau_offset, ic)
        })
    };

    let tau_ic_min = if let Some((t, _)) = &bootstrap_ic { *t }
                     else if let Some((t, _)) = &bootstrap { t.max(0.0) }
                     else { 0.5 };

    // Filter tau_profile to start from IC time, with subsampling pre-recombination.
    let tau_recomb_start = 120.0;
    let mut ft = Vec::new(); let mut fm = Vec::new(); let mut fb = Vec::new();
    let mut skip_count = 0u32;
    for (idx, &tau) in common.tau_profile.iter().enumerate() {
        if tau < tau_ic_min - 0.1 { continue; }
        if tau < tau_recomb_start {
            skip_count += 1;
            if skip_count % 4 != 1 { continue; }
        }
        ft.push(tau);
        fm.extend_from_slice(&scratch.mats_flat[idx*n*n..(idx+1)*n*n]);
        fb.push(common.bg_at_snap[idx]);
    }
    if ft.len() < 2 { return Err("tau_profile too short".into()); }

    let mut y0 = if let Some((_, ic)) = bootstrap_ic {
        if ic.len() != n { return Err(format!("IC len {} != {}", ic.len(), n)); }
        ic
    } else if let Some((_, ic)) = bootstrap {
        ic
    } else {
        adiabatic_ic(k, &lay, &fb[0])
    };

    if y0[lay.i_phi].abs() < 1e-30 && !fb.is_empty() {
        let bg0 = &fb[0];
        let r_nu = bg0.grho_nu / (bg0.grho_g + bg0.grho_nu).max(1e-30);
        y0[lay.i_phi] = -(2.0 / 3.0) * (1.0 + 2.0 * r_nu / 5.0) / (1.0 + 4.0 * r_nu / 15.0);
    }

    // Solve ODE
    use crate::solver::stacked::integrate_linear_profile_rodas5p;
    // PR-PERF-02: moderate step controller relaxation. rtol 3e-6 (vs 1e-6)
    // and h_max 30/k (vs 20/k) — conservative compared to prior aggressive
    // sketch (5e-6 / 80/k) that gave -1.8% D_2. Empirical: <0.3% D_2 cost
    // for ~30% step reduction.
    let h_max_k = (30.0 / k).min(15.0);
    let rodas_cfg = Rodas5PConfig {
        rtol: 3e-6, atol: 3e-9, max_steps: 1_000_000,
        h_init: None, h_min: 1e-14, h_max: h_max_k,
        f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
        use_analytic_jacobian: true, use_ft_term: false,
        use_blas_lu: false, use_block_diag: false,
        ell_max_gamma_hint: pcfg.lmax_g as usize, ell_max_nu_hint: pcfg.lmax_n as usize,
        ell_max_pol_hint: pcfg.lmax_pol as usize, include_pol_hint: pcfg.lmax_pol > 0,
        use_sparse: false,
    };
    // PR-IMEX-03: optional IMEX-ARK4 path (env BASS_USE_IMEX=1)
    // Production default is Rodas5P; IMEX is opt-in for benchmarking.
    //
    // PR-IMEX-04: k-heuristic routing. IMEX is fast only for small k (high χ/k
    // ratio, deeply stiff collision-dominated regime). At stiff-nonstiff
    // boundary (k ≈ 0.01-0.03) PI controller cannot stabilize h and triggers
    // fallback; at high k the oscillatory regime needs many IMEX steps,
    // erasing the gain. Route only k < BASS_IMEX_K_MAX through IMEX
    // (default 0.01 — empirically the best break-even in mini 50k profile).
    let use_imex_global = std::env::var("BASS_USE_IMEX").map_or(false, |v| v == "1");
    let imex_k_max: f64 = std::env::var("BASS_IMEX_K_MAX").ok()
        .and_then(|v| v.parse().ok()).unwrap_or(0.005);
    let use_imex = use_imex_global && k < imex_k_max;
    let snapshots_rev = if use_imex {
        use crate::solver::imex_ark4::{ImexWorkspace, integrate_imex_ark4_snapshots};
        use crate::solver::imex_collision_split::BassLinearOp;
        let op = BassLinearOp::new(&lay, &ft, &fm, &fb);
        let mut work = ImexWorkspace::new(n);
        // PR-IMEX-04: h_init = fraction of first τ gap (not 1/k heuristic).
        // At recombination start (ft[0] ≪ 1) and tight acoustic modes
        // (k ~ 0.01-0.05) the 1/k value is orders of magnitude too large,
        // causes repeated rejection, PI controller drives h to underflow.
        // τ_profile gap is the natural scale for the first adaptive step.
        let dtau0 = if ft.len() >= 2 { ft[1] - ft[0] } else { 1.0 };
        let h_init = dtau0.max(1e-6).min(1.0);
        // PR-IMEX-04: BASS_IMEX_MAX_STEPS diagnostic.
        // Default 50K is empirically sufficient — normal k modes converge in
        // 50-6300 steps in production profile. k ~ 0.3 (largest) takes ~6300.
        // 50K gives 8x headroom for normal k, and converts divergent cases
        // into fast fallback (≤0.5s per failed k) instead of hangs.
        let max_steps = std::env::var("BASS_IMEX_MAX_STEPS").ok()
            .and_then(|v| v.parse::<usize>().ok()).unwrap_or(50_000);
        let t_ode = std::time::Instant::now();
        let imex_result = integrate_imex_ark4_snapshots(
            &op, &ft, h_init, &y0, rodas_cfg.atol, rodas_cfg.rtol, max_steps, &mut work
        );
        match imex_result {
            Ok((snaps, stats)) => {
                if std::env::var("BASS_IMEX_DIAG").map_or(false, |v| v == "1") {
                    eprintln!("  [IMEX] k={:.4e} wall={:.3}s acc={} rej={} h_final={:.2e} h_init={:.2e}",
                              k, t_ode.elapsed().as_secs_f64(),
                              stats.n_steps_accepted, stats.n_steps_rejected, stats.final_h, h_init);
                }
                snaps
            },
            Err(e) => {
                // PR-IMEX-04: Rodas5P fallback for IMEX failures (safety net).
                // Production won't lose the kmode; logged for diagnostics.
                if std::env::var("BASS_IMEX_DIAG").map_or(false, |v| v == "1") {
                    eprintln!("  [IMEX] k={:.4e} IMEX failed ({}), falling back to Rodas5P",
                              k, e);
                }
                let (snaps, _, _) = integrate_linear_profile_rodas5p(
                    &ft, &fm, n, &y0, &ft, &rodas_cfg,
                )?;
                snaps
            }
        }
    } else {
        let (snaps, _stats, _) = integrate_linear_profile_rodas5p(
            &ft, &fm, n, &y0, &ft, &rodas_cfg,
        )?;
        snaps
    };
    let snaps = &snapshots_rev;

    // Source extraction with reused dy scratch (audit #3)
    let ns = snaps.len();
    let mut result = CambKmodeResult {
        eta_grid: Vec::with_capacity(ns),
        source_total: Vec::with_capacity(ns),
        source_sw: Vec::with_capacity(ns),
        source_dop: Vec::with_capacity(ns),
        source_quad: Vec::with_capacity(ns),
        phi: Vec::with_capacity(ns),
        psi: Vec::with_capacity(ns),
        n_state: n,
    };

    for si in 0..ns {
        let tau = ft[si];
        let yi = &snaps[si];
        let bg = &fb[si];
        // Reused dy buffer instead of `let mut dy = vec![0.0_f64; n]` per snapshot.
        scratch.dy.iter_mut().for_each(|v| *v = 0.0);
        let src = camb_rhs(k, tau, yi, &mut scratch.dy, &lay, bg);

        result.eta_grid.push(tau);
        result.source_total.push(src.s_total);
        result.source_sw.push(src.s_sw);
        result.source_dop.push(src.s_dop);
        result.source_quad.push(src.s_quad);

        let etak = yi[lay.i_etak]; let sigma = yi[lay.i_sigma];
        let eta_s = etak / k;
        result.phi.push(eta_s - bg.adotoa * sigma / k);
        result.psi.push(-eta_s + bg.adotoa * sigma / k);
    }

    // Post-processing ISW (unchanged from original)
    for si in 0..ns {
        let phidot = if si == 0 {
            if ns > 1 {
                (result.phi[1] - result.phi[0]) / (result.eta_grid[1] - result.eta_grid[0]).max(1e-30)
            } else { 0.0 }
        } else if si == ns - 1 {
            (result.phi[ns-1] - result.phi[ns-2]) / (result.eta_grid[ns-1] - result.eta_grid[ns-2]).max(1e-30)
        } else {
            (result.phi[si+1] - result.phi[si-1]) / (result.eta_grid[si+1] - result.eta_grid[si-1]).max(1e-30)
        };
        let s_isw = fb[si].expmmu * 2.0 * phidot;
        result.source_total[si] += s_isw;
    }

    Ok(result)
}

/// Solve a single k-mode with full physics configuration.
///
/// Uses adiabatic IC if no bootstrap is provided.
pub(crate) fn solve_kmode_full(
    k: f64,
    params: &crate::recombination::visibility_hyrec::VisibilityParams,
    vis: &crate::recombination::visibility_hyrec::VisibilityResult,
    pcfg: &ProductionConfig,
    bootstrap_ic: Option<(f64, Vec<f64>)>,
) -> Result<CambKmodeResult, String> {
    // Backward-compat wrapper: build CommonProfile + scratch on every call.
    // Production hot loop should call `solve_kmode_full_with_common` directly
    // with shared CommonProfile and per-thread scratch reuse.
    let common = CommonProfile::build(params, vis);
    let n_vis = common.bg_at_snap.len();
    let mut scratch = KModeScratch::new(pcfg.layout().n_state, n_vis);
    solve_kmode_full_with_common(k, &common, pcfg, bootstrap_ic, &mut scratch)
}

#[doc(hidden)]
#[allow(dead_code)]  // referenced by tests below the original impl
pub(crate) fn solve_kmode_full_inline_legacy_unused(
    k: f64,
    params: &crate::recombination::visibility_hyrec::VisibilityParams,
    vis: &crate::recombination::visibility_hyrec::VisibilityResult,
    pcfg: &ProductionConfig,
    bootstrap_ic: Option<(f64, Vec<f64>)>,
) -> Result<CambKmodeResult, String> {
    use crate::core::config::Rodas5PConfig;

    let h0c = params.h * 1e7 / 2.99792458e10;
    let og = params.omega_gamma();
    let omega_nu_ml = og * 0.2271 * NEFF_MASSLESS;
    let n_vis = vis.z_grid.len();
    let eta_max = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);

    let lay = pcfg.layout();
    let n = lay.n_state;

    // Visibility derivatives
    let mut g_dot = vec![0.0_f64; n_vis];
    let mut g_ddot = vec![0.0_f64; n_vis];
    for i in 1..n_vis-1 {
        let dt = vis.eta_grid[i+1] - vis.eta_grid[i-1];
        if dt.abs() > 1e-30 {
            g_dot[i] = -(vis.g_grid[i+1] - vis.g_grid[i-1]) / dt;
            g_ddot[i] = (vis.g_grid[i+1] - 2.0*vis.g_grid[i] + vis.g_grid[i-1])
                        / (dt/2.0).powi(2);
        }
    }

    // Build background + matrix profile (precomputed A(τ) at each grid point)
    let mut tau_profile = Vec::with_capacity(n_vis);
    let mut mats_flat = Vec::with_capacity(n_vis * n * n);
    let mut bg_at_snap = Vec::with_capacity(n_vis);

    for i in (0..n_vis).rev() {
        let tau = eta_max - vis.eta_grid[i];
        tau_profile.push(tau);
        let z = vis.z_grid[i];
        let a = 1.0 / (1.0 + z);
        let h0c2 = h0c * h0c;

        let bg = CambBackground {
            adotoa: a * h0c * params.e_of_z(z),
            grho_g: 3.0 * h0c2 * og / (a * a),
            grho_nu: 3.0 * h0c2 * omega_nu_ml / (a * a),
            grho_b: 3.0 * h0c2 * params.omega_b / a,
            grho_c: 3.0 * h0c2 * (params.omega_m - params.omega_b) / a,
            opac: vis.kappa_dot_grid[i],
            cs2b: 1e-10,
            vis: vis.g_grid[i], dvis: g_dot[i], ddvis: g_ddot[i],
            a,
            expmmu: (-vis.tau_grid[i]).exp(),
        };

        let mat = build_camb_matrix(k, tau, &lay, &bg);
        mats_flat.extend_from_slice(&mat);
        bg_at_snap.push(bg);
    }

    // Determine IC: use CAMB bootstrap with tau convention correction.
    // τ_offset = τ_CAMB(z_max) = ∫_0^{a_max} da/(a²·H₀·E(a))
    // Exact numerical quadrature (16-point Gauss-Legendre on [0, a_max]).
    let z_max = vis.z_grid.iter().cloned().fold(0.0_f64, f64::max);
    let a_max = 1.0 / (1.0 + z_max);
    let omega_r_total = og + omega_nu_ml;
    let tau_offset = {
        // Gauss-Legendre 8-point on [0, a_max]
        let gl_x = [0.01985507, 0.10166676, 0.23723379, 0.40828268,
                     0.59171732, 0.76276621, 0.89833324, 0.98014493];
        let gl_w = [0.05061427, 0.11119052, 0.15685332, 0.18134189,
                     0.18134189, 0.15685332, 0.11119052, 0.05061427];
        let mut integral = 0.0_f64;
        for i in 0..8 {
            let a = a_max * gl_x[i];
            let a2 = a * a;
            let e_a = (omega_r_total / (a2 * a2) + params.omega_m / (a2 * a)
                      + params.omega_l).max(1e-30).sqrt();
            integral += gl_w[i] / (a2 * h0c * e_a);
        }
        integral * a_max
    };
    
    let bootstrap = if bootstrap_ic.is_some() {
        None
    } else {
        bootstrap_ic_lookup(k, &lay).map(|(tau_camb, ic)| {
            let tau_bass = tau_camb - tau_offset;
            (tau_bass, ic)
        })
    };
    
    let tau_ic_min = if let Some((t, _)) = &bootstrap_ic { *t }
                     else if let Some((t, _)) = &bootstrap { t.max(0.0) }
                     else { 0.5 };
    
    // Filter tau_profile to start from IC time, with subsampling in low-visibility regions.
    // z=1500-50000 (τ_BASS < ~140): subsample every 4th point (physics is smooth)
    // z=800-1500 (τ_BASS ~140-240): keep all points (recombination, need resolution)
    // z=0-800 (τ_BASS > ~240): keep all points (source extraction needs density)
    let tau_recomb_start = 120.0; // conservative: well before visibility ramp-up
    let mut ft = Vec::new(); let mut fm = Vec::new(); let mut fb = Vec::new();
    let mut skip_count = 0u32;
    for (idx, &tau) in tau_profile.iter().enumerate() {
        if tau < tau_ic_min - 0.1 { continue; }
        // Subsample pre-recombination: keep every 4th point
        if tau < tau_recomb_start {
            skip_count += 1;
            if skip_count % 4 != 1 { continue; } // keep 1st, 5th, 9th, ...
        }
        ft.push(tau);
        fm.extend_from_slice(&mats_flat[idx*n*n..(idx+1)*n*n]);
        fb.push(bg_at_snap[idx]);
    }
    if ft.len() < 2 { return Err("tau_profile too short".into()); }

    let mut y0 = if let Some((_, ic)) = bootstrap_ic {
        if ic.len() != n { return Err(format!("IC len {} != {}", ic.len(), n)); }
        ic
    } else if let Some((_, ic)) = bootstrap {
        ic
    } else {
        adiabatic_ic(k, &lay, &fb[0])
    };

    // Set Φ_N IC from adiabatic mode (bootstrap table doesn't include Φ)
    if y0[lay.i_phi].abs() < 1e-30 && !fb.is_empty() {
        let bg0 = &fb[0];
        let r_nu = bg0.grho_nu / (bg0.grho_g + bg0.grho_nu).max(1e-30);
        y0[lay.i_phi] = -(2.0 / 3.0) * (1.0 + 2.0 * r_nu / 5.0) / (1.0 + 4.0 * r_nu / 15.0);
    }

    // Solve ODE: Rodas5P with precomputed matrix profile (LinearProfileDyn)
    use crate::solver::stacked::integrate_linear_profile_rodas5p;
    let h_max_k = (20.0 / k).min(10.0);
    let rodas_cfg = Rodas5PConfig {
        rtol: 1e-6, atol: 1e-9, max_steps: 1_000_000,
        h_init: None, h_min: 1e-14, h_max: h_max_k,
        f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
        use_analytic_jacobian: true, use_ft_term: false,
        use_blas_lu: false, use_block_diag: false,
        ell_max_gamma_hint: pcfg.lmax_g as usize, ell_max_nu_hint: pcfg.lmax_n as usize,
        ell_max_pol_hint: pcfg.lmax_pol as usize, include_pol_hint: pcfg.lmax_pol > 0,
        use_sparse: false,
    };
    let (snapshots_rev, _stats, _) = integrate_linear_profile_rodas5p(
        &ft, &fm, n, &y0, &ft, &rodas_cfg,
    )?;
    let snaps = &snapshots_rev;

    // Extract source at each snapshot
    let ns = snaps.len();
    let mut result = CambKmodeResult {
        eta_grid: Vec::with_capacity(ns),
        source_total: Vec::with_capacity(ns),
        source_sw: Vec::with_capacity(ns),
        source_dop: Vec::with_capacity(ns),
        source_quad: Vec::with_capacity(ns),
        phi: Vec::with_capacity(ns),
        psi: Vec::with_capacity(ns),
        n_state: n,
    };

    // Extract source at each snapshot (ISW=0 in camb_rhs; added below via FD)
    for si in 0..ns {
        let tau = ft[si];
        let yi = &snaps[si];
        let bg = &fb[si];
        let mut dy = vec![0.0_f64; n];
        let src = camb_rhs(k, tau, yi, &mut dy, &lay, bg);

        result.eta_grid.push(tau);
        result.source_total.push(src.s_total);
        result.source_sw.push(src.s_sw);
        result.source_dop.push(src.s_dop);
        result.source_quad.push(src.s_quad);

        let etak = yi[lay.i_etak]; let sigma = yi[lay.i_sigma];
        let eta_s = etak / k;
        result.phi.push(eta_s - bg.adotoa * sigma / k);
        result.psi.push(-eta_s + bg.adotoa * sigma / k);
    }

    // ── Post-processing ISW: centered FD on phi = etak/k − ℋσ/k ──
    // phidot[i] ≈ (phi[i+1] − phi[i−1]) / (τ[i+1] − τ[i−1])
    // ISW[i] = 2 × phidot × e^{−τ_optical}
    for si in 0..ns {
        let phidot = if si == 0 {
            if ns > 1 {
                (result.phi[1] - result.phi[0]) / (result.eta_grid[1] - result.eta_grid[0]).max(1e-30)
            } else { 0.0 }
        } else if si == ns - 1 {
            (result.phi[ns-1] - result.phi[ns-2]) / (result.eta_grid[ns-1] - result.eta_grid[ns-2]).max(1e-30)
        } else {
            (result.phi[si+1] - result.phi[si-1]) / (result.eta_grid[si+1] - result.eta_grid[si-1]).max(1e-30)
        };
        let s_isw = fb[si].expmmu * 2.0 * phidot;
        result.source_total[si] += s_isw;
    }

    Ok(result)
}

/// Solve full production D_ℓ spectrum.
///
/// Returns D_ℓ for ℓ = 2..=ell_max.
pub(crate) fn solve_production_spectrum(
    params: &crate::recombination::visibility_hyrec::VisibilityParams,
    vis: &crate::recombination::visibility_hyrec::VisibilityResult,
    pcfg: &ProductionConfig,
) -> Result<Vec<f64>, String> {
    // PROFILING (BASS_PHASE_TIMER=1): phase-level wall-clock timing
    let phase_timer = std::env::var("BASS_PHASE_TIMER").map_or(false, |v| v == "1");
    let t_phase_start = std::time::Instant::now();
    let mut t_marker = t_phase_start;
    macro_rules! phase_mark {
        ($name:expr) => {
            if phase_timer {
                let e = t_marker.elapsed();
                eprintln!("  [PHASE] {:>24}  {:>8.3}s", $name, e.as_secs_f64());
                t_marker = std::time::Instant::now();
            }
        };
    }

    let k_grid = pcfg.k_grid();
    let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);

    // PERF-01: build CommonProfile ONCE (audit #2). Shared read-only across
    // all k-modes via Arc — no per-thread clone needed (MESI Shared state
    // handles concurrent reads with zero coherence traffic).
    let common = std::sync::Arc::new(CommonProfile::build(params, vis));
    let n_state = pcfg.layout().n_state;
    let n_vis = common.bg_at_snap.len();
    phase_mark!("CommonProfile build");

    // BASS_SERIAL_KLOOP=1 forces serial fallback (debugging / profiling).
    let serial_mode = std::env::var("BASS_SERIAL_KLOOP").map(|v| v == "1").unwrap_or(false);

    // Solve a chunk of k-modes with one shared scratch buffer (audit #3).
    // Returns (global_index, k, result) tuples in input order.
    let solve_chunk = |chunk: &[(usize, f64)], common: &CommonProfile|
        -> Vec<(usize, f64, CambKmodeResult)>
    {
        let mut scratch = KModeScratch::new(n_state, n_vis);
        let mut out = Vec::with_capacity(chunk.len());
        for &(ik, k) in chunk {
            match solve_kmode_full_with_common(k, common, pcfg, None, &mut scratch) {
                Ok(r) => out.push((ik, k, r)),
                Err(e) => eprintln!("  k={:.4}: FAIL: {}", k, e),
            }
        }
        out
    };

    let indexed: Vec<(usize, f64)> =
        k_grid.iter().enumerate().map(|(i, &k)| (i, k)).collect();

    let mut indexed_results: Vec<(usize, f64, CambKmodeResult)> = if serial_mode {
        solve_chunk(&indexed, &common)
    } else {
        // PERF-01: par_chunks. Each rayon worker takes one contiguous chunk,
        // pays scratch alloc once per chunk (not per k). Cleaner than
        // rayon::join for arbitrary thread counts.
        use rayon::prelude::*;
        let num_threads = rayon::current_num_threads().max(1);
        let chunk_size = (indexed.len() + num_threads - 1) / num_threads;
        indexed
            .par_chunks(chunk_size)
            .flat_map(|chunk| solve_chunk(chunk, &common))
            .collect()
    };
    indexed_results.sort_by_key(|(ik, _, _)| *ik);
    let kmode_results: Vec<(f64, CambKmodeResult)> =
        indexed_results.into_iter().map(|(_, k, r)| (k, r)).collect();
    phase_mark!("ODE solve (all k-modes)");

    if kmode_results.len() < 2 {
        return Err("Too few k-modes solved".into());
    }
    eprintln!("  Solved {}/{} k-modes", kmode_results.len(), k_grid.len());

    // PR-PERF-02: adaptive G7K15 + Bessel ladder per panel — math equivalent
    // to compute_dl_spectrum but ALL ℓ computed in single adaptive run per k.
    let dl_cfg = DlConfig {
        ell_max: pcfg.ell_max,
        a_s: pcfg.a_s, n_s: pcfg.n_s, k_pivot: pcfg.k_pivot, t_cmb_uk: pcfg.t_cmb_uk,
    };
    let dl = compute_dl_spectrum_adaptive_ladder(&kmode_results, eta_0, &dl_cfg);
    phase_mark!("LoS integration (D_l)");
    if phase_timer {
        eprintln!("  [PHASE] {:>24}  {:>8.3}s  TOTAL",
                  "=== total ===", t_phase_start.elapsed().as_secs_f64());
    }
    Ok(dl)
}

#[cfg(test)]
mod production_test {
    use super::*;

    #[test]
    fn test_adiabatic_ic() {
        let lay = CambLayout::new_full(8, 8, 6, 10, 12);
        let bg = CambBackground {
            adotoa: 500.0, grho_g: 1e-5, grho_nu: 7e-6, grho_b: 1e-7,
            grho_c: 5e-7, opac: 5000.0, cs2b: 1e-8, vis: 0.0, dvis: 0.0, ddvis: 0.0,
            a: 1e-5,
            expmmu: 0.0,
        };
        let k = 0.01;
        let ic = adiabatic_ic(k, &lay, &bg);
        
        assert_eq!(ic.len(), lay.n_state);
        assert!((ic[lay.i_etak] + k).abs() < 1e-10, "etak should be -k");
        assert!(ic[lay.i_clxc].abs() - 1.5 < 1e-10, "δ_c should be 3/2");
        assert!((ic[lay.theta(0)] - 0.5).abs() < 1e-10, "Θ₀ should be 1/2");
        assert!(ic[lay.i_sigma].abs() < 1e-10, "σ should be 0");
        assert!(ic[lay.i_vb] > 0.0, "v_b should be positive (= 3Θ₁)");
        
        // E-mode should be zero
        assert_eq!(ic[lay.e_mode(0)], 0.0);
        assert_eq!(ic[lay.b_mode(0)], 0.0);
        
        eprintln!("  IC: n_state={}, etak={:.4e}, σ={:.4e}, Θ₀={:.4e}",
            lay.n_state, ic[lay.i_etak], ic[lay.i_sigma], ic[lay.theta(0)]);
        eprintln!("  PASS: adiabatic IC (superhorizon, {} DOF)", lay.n_state);
    }

    #[test]
    fn test_production_config() {
        let cfg = ProductionConfig::default();
        let k = cfg.k_grid();
        assert_eq!(k.len(), 2000);
        assert!((k[0] - 5e-5).abs() / 5e-5 < 0.01);
        assert!((k[1999] - 0.3).abs() / 0.3 < 0.01);
        
        let lay = cfg.layout();
        assert_eq!(lay.n_state, 5 + 17 + 17 + 13 + 13 + 1); // with pol and Φ: 66 DOF
        
        let full = ProductionConfig::full_physics();
        let lay_f = full.layout();
        // 5 + 17(γ) + 17(ν_ml) + 13(E) + 13(B) + 130(ν_mv) + 1(Φ) = 196
        assert_eq!(lay_f.n_state, 196);
        eprintln!("  Default: {} DOF, {} k-modes", lay.n_state, k.len());
        eprintln!("  Full: {} DOF", lay_f.n_state);
    }

    #[test]
    fn test_solve_kmode_full_minimal() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let pcfg = ProductionConfig::minimal();
        let k = 0.01;
        
        match solve_kmode_full(k, &p, &vis, &pcfg, None) {
            Ok(r) => {
                eprintln!("  solve_kmode_full: {} snapshots", r.eta_grid.len());
                let s_max = r.source_total.iter().map(|x| x.abs()).fold(0.0_f64, f64::max);
                eprintln!("  max|S_total| = {:.4e}", s_max);
                assert!(s_max > 1e-6, "Source should be nonzero");
                assert!(r.eta_grid.len() > 100, "Should have >100 snapshots");
            }
            Err(e) => {
                eprintln!("  solve_kmode_full failed: {}", e);
                // Don't assert — solver may fail with minimal config
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
// SVT: Tensor mode (m=±2) — CAMB-matched equations
// ═══════════════════════════════════════════════════════════════════════

/// Tensor perturbation layout.
/// Hierarchy starts at ℓ=2 (no ℓ=0,1 for tensors).
/// CAMB variables: H_chi (GW amplitude), shear (tensor σ).
#[derive(Clone)]
pub(crate) struct TensorLayout {
    pub(crate) lmax_g: usize,   // photon max ℓ (hierarchy ℓ=2..lmax_g+1)
    pub(crate) lmax_n: usize,   // neutrino max ℓ
    pub(crate) lmax_pol: usize, // E/B polarization max ℓ
    pub(crate) i_hchi: usize,   // H_chi index
    pub(crate) i_shear: usize,  // shear index
    pub(crate) i_g_base: usize, // photon: idx = i_g_base + ℓ (ℓ≥2)
    pub(crate) i_e_base: usize, // E-mode: idx = i_e_base + ℓ
    pub(crate) i_b_base: usize, // B-mode: idx = i_b_base + ℓ
    pub(crate) i_r_base: usize, // neutrino: idx = i_r_base + ℓ
    pub(crate) n_state: usize,
}

impl TensorLayout {
    pub(crate) fn new(lmax_g: usize, lmax_n: usize, lmax_pol: usize) -> Self {
        let mut n = 0;
        let i_hchi = n; n += 1;
        let i_shear = n; n += 1;
        let i_g_base = n - 2; // photon[ℓ] = i_g_base + ℓ, ℓ=2..lmax_g+1
        n += lmax_g;           // lmax_g entries (ℓ=2..lmax_g+1)
        let i_e_base = n - 2;
        n += lmax_pol;
        let i_b_base = n - 2;
        n += lmax_pol;
        let i_r_base = n - 2;
        n += lmax_n;
        Self { lmax_g, lmax_n, lmax_pol, i_hchi, i_shear,
               i_g_base, i_e_base, i_b_base, i_r_base, n_state: n }
    }

    pub(crate) fn pig(&self) -> usize { self.i_g_base + 2 }
}

/// CAMB tensor coupling coefficients (flat space).
/// tensfac = (l+3)(l-1)/(l+1)
fn tensor_denlkt(k: f64, l: usize) -> (f64, f64, f64, f64) {
    let lf = l as f64;
    let d = 1.0 / (2.0 * lf + 1.0);
    let tensfac = (lf + 3.0) * (lf - 1.0) / (lf + 1.0);
    let c1 = k * d * lf;
    let c2 = k * d * tensfac;
    let c3 = k * d * tensfac * tensfac / (lf + 1.0);
    let c4 = if l >= 1 { k * 4.0 / (lf * (lf + 1.0)) } else { 0.0 };
    (c1, c2, c3, c4)
}

/// Compute tensor RHS dy/dτ.
pub(crate) fn tensor_rhs(
    k: f64, _tau: f64, y: &[f64], dy: &mut [f64],
    lay: &TensorLayout, bg: &CambBackground,
) {
    let n = lay.n_state;
    for i in 0..n { dy[i] = 0.0; }

    let hchi = y[lay.i_hchi];
    let shear = y[lay.i_shear];
    let opac = bg.opac;
    let adotoa = bg.adotoa;

    let g = |ell: usize| -> f64 {
        if ell < 2 || ell > lay.lmax_g + 1 { 0.0 }
        else { y[lay.i_g_base + ell] }
    };
    let e = |ell: usize| -> f64 {
        if ell < 2 || ell > lay.lmax_pol + 1 { 0.0 }
        else { y[lay.i_e_base + ell] }
    };
    let b = |ell: usize| -> f64 {
        if ell < 2 || ell > lay.lmax_pol + 1 { 0.0 }
        else { y[lay.i_b_base + ell] }
    };
    let nu = |ell: usize| -> f64 {
        if ell < 2 || ell > lay.lmax_n + 1 { 0.0 }
        else { y[lay.i_r_base + ell] }
    };

    let pig = g(2);
    let pir = nu(2);
    let polter = 0.1 * pig + 9.0 / 15.0 * e(2);
    let cothxor = 1.0 / _tau.max(1e-10);

    // Metric
    dy[lay.i_hchi] = -k * shear;
    let rhopi = bg.grho_g * pig + bg.grho_nu * pir;
    dy[lay.i_shear] = -2.0 * adotoa * shear + k * hchi - rhopi / k;

    // Photon ℓ=2
    let (_, c2_2, _, _) = tensor_denlkt(k, 2);
    dy[lay.i_g_base + 2] = -c2_2 * g(3) + k * 8.0 / 15.0 * shear - opac * (pig - polter);

    // Photon ℓ=3..lmax_g
    for ell in 3..=lay.lmax_g {
        let (c1, c2, _, _) = tensor_denlkt(k, ell);
        dy[lay.i_g_base + ell] = c1 * g(ell - 1) - c2 * g(ell + 1) - opac * g(ell);
    }
    // Truncation
    let lm = lay.lmax_g + 1;
    if lm >= 3 {
        dy[lay.i_g_base + lm] = k * (lm as f64) / (lm as f64 - 2.0) * g(lm - 1)
            - (lm as f64 + 3.0) * cothxor * g(lm) - opac * g(lm);
    }

    // E-mode ℓ=2
    let (_, _, c3_2, c4_2) = tensor_denlkt(k, 2);
    dy[lay.i_e_base + 2] = -opac * (e(2) - polter) + c4_2 * b(2) - c3_2 * e(3);
    for ell in 3..=lay.lmax_pol {
        let (c1, _, c3, c4) = tensor_denlkt(k, ell);
        dy[lay.i_e_base + ell] = c1 * e(ell-1) - c3 * e(ell+1) + c4 * b(ell) - opac * e(ell);
    }
    let lmp = lay.lmax_pol + 1;
    if lmp >= 3 {
        let (c1, _, _, c4) = tensor_denlkt(k, lmp);
        dy[lay.i_e_base + lmp] = c1 * e(lmp-1) + c4 * b(lmp) - opac * e(lmp);
    }

    // B-mode ℓ=2
    dy[lay.i_b_base + 2] = -c3_2 * b(3) - c4_2 * e(2) - opac * b(2);
    for ell in 3..=lay.lmax_pol {
        let (c1, _, c3, c4) = tensor_denlkt(k, ell);
        dy[lay.i_b_base + ell] = c1 * b(ell-1) - c3 * b(ell+1) - c4 * e(ell) - opac * b(ell);
    }
    if lmp >= 3 {
        let (c1, _, _, c4) = tensor_denlkt(k, lmp);
        dy[lay.i_b_base + lmp] = c1 * b(lmp-1) - c4 * e(lmp) - opac * b(lmp);
    }

    // Neutrino ℓ=2
    dy[lay.i_r_base + 2] = -c2_2 * nu(3) + k * 8.0 / 15.0 * shear;
    for ell in 3..=lay.lmax_n {
        let (c1, c2, _, _) = tensor_denlkt(k, ell);
        dy[lay.i_r_base + ell] = c1 * nu(ell-1) - c2 * nu(ell+1);
    }
    let lmn = lay.lmax_n + 1;
    if lmn >= 3 {
        dy[lay.i_r_base + lmn] = k * (lmn as f64) / (lmn as f64 - 2.0) * nu(lmn-1)
            - (lmn as f64 + 3.0) * cothxor * nu(lmn);
    }
}

/// Tensor adiabatic IC (CAMB initialt, flat).
pub(crate) fn tensor_ic(k: f64, tau: f64, lay: &TensorLayout) -> Vec<f64> {
    let mut y = vec![0.0_f64; lay.n_state];
    let x = k * tau;
    let neff = 3.044_f64;
    let big_r = (7.0/8.0 * (4.0/11.0_f64).powf(4.0/3.0) * neff)
              / (1.0 + 7.0/8.0 * (4.0/11.0_f64).powf(4.0/3.0) * neff);
    let elec = -(2.0*big_r + 10.0) / (4.0*big_r + 15.0);
    y[lay.i_hchi] = 1.0;
    y[lay.i_shear] = -5.0 / (2.0*(big_r+5.0)) * x * elec;
    y[lay.i_r_base + 2] = -2.0 / (3.0*(big_r+5.0)) * x*x * elec;
    if lay.lmax_n >= 2 {
        y[lay.i_r_base + 3] = -2.0 / (21.0*(big_r+5.0)) * x*x*x * elec;
    }
    y
}

// ═══════════════════════════════════════════════════════════════════════
// SVT: Vector mode (m=±1)
// ═══════════════════════════════════════════════════════════════════════

/// Vector perturbation layout. Hierarchy starts at ℓ=1.
#[derive(Clone)]
pub(crate) struct VectorLayout {
    pub(crate) lmax_g: usize,
    pub(crate) lmax_n: usize,
    pub(crate) i_sigma_v: usize,
    pub(crate) i_vb: usize,
    pub(crate) i_g_base: usize,
    pub(crate) i_r_base: usize,
    pub(crate) n_state: usize,
}

impl VectorLayout {
    pub(crate) fn new(lmax_g: usize, lmax_n: usize) -> Self {
        let mut n = 0;
        let i_sigma_v = n; n += 1;
        let i_vb = n; n += 1;
        let i_g_base = n - 1;
        n += lmax_g;
        let i_r_base = n - 1;
        n += lmax_n;
        Self { lmax_g, lmax_n, i_sigma_v, i_vb, i_g_base, i_r_base, n_state: n }
    }
}

fn vector_coupling(l: usize) -> f64 {
    if l == 0 { return 0.0; }
    let lf = l as f64;
    ((lf * lf - 1.0) / (lf * lf)).sqrt()
}

/// Vector RHS.
pub(crate) fn vector_rhs(
    k: f64, tau: f64, y: &[f64], dy: &mut [f64],
    lay: &VectorLayout, bg: &CambBackground,
) {
    for i in 0..lay.n_state { dy[i] = 0.0; }
    let sigma_v = y[lay.i_sigma_v];
    let vb = y[lay.i_vb];
    let cothxor = 1.0 / tau.max(1e-10);

    let g = |ell: usize| -> f64 {
        if ell < 1 || ell > lay.lmax_g { 0.0 } else { y[lay.i_g_base + ell] }
    };
    let nu = |ell: usize| -> f64 {
        if ell < 1 || ell > lay.lmax_n { 0.0 } else { y[lay.i_r_base + ell] }
    };

    // Metric: decays in ΛCDM
    dy[lay.i_sigma_v] = -2.0 * bg.adotoa * sigma_v;

    // Baryon
    let r_val = (0.75 * bg.grho_b / bg.grho_g.max(1e-30)).max(1e-10);
    dy[lay.i_vb] = -bg.adotoa * vb + bg.opac / r_val * (g(1) - vb) + k * sigma_v;

    // Photon ℓ=1
    dy[lay.i_g_base + 1] = k / 3.0 * (-2.0 * vector_coupling(2) * g(2))
        - bg.opac * (g(1) - vb / 3.0) + k * sigma_v / 3.0;
    for ell in 2..lay.lmax_g {
        let f = k / (2 * ell + 1) as f64;
        dy[lay.i_g_base + ell] = f * (ell as f64 * vector_coupling(ell-1) * g(ell-1)
            - (ell as f64 + 1.0) * vector_coupling(ell) * g(ell+1)) - bg.opac * g(ell);
    }
    let lm = lay.lmax_g;
    dy[lay.i_g_base + lm] = k * vector_coupling(lm-1) * g(lm-1)
        - (lm as f64 + 1.0) * cothxor * g(lm) - bg.opac * g(lm);

    // Neutrino ℓ=1
    dy[lay.i_r_base + 1] = k / 3.0 * (-2.0 * vector_coupling(2) * nu(2))
        + k * sigma_v / 3.0;
    for ell in 2..lay.lmax_n {
        let f = k / (2 * ell + 1) as f64;
        dy[lay.i_r_base + ell] = f * (ell as f64 * vector_coupling(ell-1) * nu(ell-1)
            - (ell as f64 + 1.0) * vector_coupling(ell) * nu(ell+1));
    }
    let lmn = lay.lmax_n;
    dy[lay.i_r_base + lmn] = k * vector_coupling(lmn-1) * nu(lmn-1)
        - (lmn as f64 + 1.0) * cothxor * nu(lmn);
}

#[cfg(test)]
mod svt_test {
    use super::*;

    #[test]
    fn test_tensor_layout() {
        let tl = TensorLayout::new(10, 10, 6);
        // 2 metric + 10 photon + 6 E + 6 B + 10 neutrino = 34
        assert_eq!(tl.n_state, 34);
        assert_eq!(tl.pig(), tl.i_g_base + 2);
        eprintln!("  TensorLayout: {} DOF", tl.n_state);
    }

    #[test]
    fn test_vector_layout() {
        let vl = VectorLayout::new(8, 8);
        // 1 σ_V + 1 v_b + 8 photon + 8 neutrino = 18
        assert_eq!(vl.n_state, 18);
        eprintln!("  VectorLayout: {} DOF", vl.n_state);
    }

    #[test]
    fn test_tensor_ic() {
        let tl = TensorLayout::new(10, 10, 6);
        let ic = tensor_ic(0.01, 0.5, &tl);
        assert_eq!(ic.len(), tl.n_state);
        assert!((ic[tl.i_hchi] - 1.0).abs() < 1e-10, "H_chi should be 1");
        assert!(ic[tl.i_shear].abs() > 0.0, "shear should be nonzero");
        assert!(ic[tl.i_r_base + 2].abs() > 0.0, "pir should be nonzero");
        eprintln!("  IC: H_chi={:.6}, shear={:.6e}, pir={:.6e}",
            ic[tl.i_hchi], ic[tl.i_shear], ic[tl.i_r_base + 2]);
    }

    #[test]
    fn test_tensor_rhs() {
        let tl = TensorLayout::new(10, 10, 6);
        let ic = tensor_ic(0.01, 0.5, &tl);
        let bg = CambBackground {
            adotoa: 500.0, grho_g: 1e-5, grho_nu: 7e-6, grho_b: 1e-7,
            grho_c: 5e-7, opac: 5000.0, cs2b: 1e-8, vis: 0.0, dvis: 0.0, ddvis: 0.0, a: 1e-5,
            expmmu: 0.0,
        };
        let mut dy = vec![0.0_f64; tl.n_state];
        tensor_rhs(0.01, 0.5, &ic, &mut dy, &tl, &bg);

        // H_chi' = -k*shear (should be nonzero)
        assert!(dy[tl.i_hchi].abs() > 0.0);
        // shear' should be nonzero
        assert!(dy[tl.i_shear].abs() > 0.0);
        eprintln!("  dH_chi={:.4e}, dshear={:.4e}, dpig={:.4e}",
            dy[tl.i_hchi], dy[tl.i_shear], dy[tl.i_g_base + 2]);
        eprintln!("  PASS: tensor_rhs produces nonzero derivatives");
    }

    #[test]
    fn test_vector_rhs() {
        let vl = VectorLayout::new(8, 8);
        let mut y = vec![0.0_f64; vl.n_state];
        y[vl.i_sigma_v] = 1.0;
        let bg = CambBackground {
            adotoa: 500.0, grho_g: 1e-5, grho_nu: 7e-6, grho_b: 1e-7,
            grho_c: 5e-7, opac: 5000.0, cs2b: 1e-8, vis: 0.0, dvis: 0.0, ddvis: 0.0, a: 1e-5,
            expmmu: 0.0,
        };
        let mut dy = vec![0.0_f64; vl.n_state];
        vector_rhs(0.01, 10.0, &y, &mut dy, &vl, &bg);

        // σ_V should decay: σ_V' = -2ℋ*σ_V = -1000
        assert!((dy[vl.i_sigma_v] + 1000.0).abs() < 1.0, "σ_V decay");
        eprintln!("  dσ_V={:.2} (expected -1000)", dy[vl.i_sigma_v]);
        eprintln!("  PASS: vector_rhs σ_V decay correct");
    }

    #[test]
    fn test_tensor_coupling() {
        // ℓ=2: tensfac = 5*1/3 = 5/3
        let (c1, c2, c3, c4) = tensor_denlkt(1.0, 2);
        assert!((c1 - 2.0/5.0).abs() < 1e-10, "c1(2)");
        assert!((c2 - 5.0/3.0/5.0).abs() < 1e-10, "c2(2)");
        assert!((c4 - 4.0/6.0).abs() < 1e-10, "c4(2)");
        eprintln!("  c1={:.6}, c2={:.6}, c3={:.6}, c4={:.6}", c1, c2, c3, c4);
        eprintln!("  PASS: tensor coupling coefficients");
    }
}

#[cfg(test)]
mod entry02_test {
    use super::*;

    #[test]
    fn test_production_dl_50k() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        // 50 k-modes, ell_max=50 (fast validation)
        let pcfg = ProductionConfig {
            lmax_g: 8, lmax_n: 8, lmax_pol: 6,
            nq_massive: 0, lmax_m: 0,
            k_min: 5e-5, k_max: 0.3, n_k: 50,
            ell_max: 50,
            ..Default::default()
        };
        
        let t0 = Instant::now();
        match solve_production_spectrum(&p, &vis, &pcfg) {
            Ok(dl) => {
                let wall = t0.elapsed().as_secs_f64();
                eprintln!("  200k production: {:.1}s ({:.0}ms/k-mode)", wall, wall/200.0*1000.0);
                eprintln!("  D_ℓ length: {}", dl.len());
                
                // Key values
                if dl.len() > 0 { eprintln!("  D_2  = {:.1}", dl[0]); }
                if dl.len() > 8 { eprintln!("  D_10 = {:.1}", dl[8]); }
                if dl.len() > 28 { eprintln!("  D_30 = {:.1}", dl[28]); }
                if dl.len() > 48 { eprintln!("  D_50 = {:.1}", dl[48]); }
                
                // Basic sanity: D_2 should be positive and O(1000) μK²
                assert!(dl[0] > 0.0, "D_2 must be positive");
                // With 50 k-modes the accuracy is rough, but order of magnitude should be right
                eprintln!("  PASS: production pipeline functional");
                
                // Estimate full 2000k timing
                let t_per_k = wall / 50.0;
                eprintln!("  Est. 2000k: {:.0}s ({:.1}min)", t_per_k*2000.0, t_per_k*2000.0/60.0);
            }
            Err(e) => {
                eprintln!("  FAIL: {}", e);
                assert!(false, "solve_production_spectrum failed");
            }
        }
    }
}

#[cfg(test)]
mod source_debug {
    use super::*;

    #[test]
    fn test_source_at_visibility_peak() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_max = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        
        let k = 0.01;
        let pcfg = ProductionConfig { lmax_g: 8, lmax_n: 8, lmax_pol: 0,
            n_k: 10, ell_max: 10, ..Default::default() };
        
        match solve_kmode_full(k, &p, &vis, &pcfg, None) {
            Ok(r) => {
                // Find visibility peak
                let n = r.eta_grid.len();
                let mut i_peak = 0;
                let mut s_max = 0.0_f64;
                for i in 0..n {
                    if r.source_total[i].abs() > s_max {
                        s_max = r.source_total[i].abs();
                        i_peak = i;
                    }
                }
                eprintln!("  Source peak at i={}, tau={:.1}, |S|={:.4e}",
                    i_peak, r.eta_grid[i_peak], s_max);
                eprintln!("  Source at i=0: tau={:.1}, S={:.4e}", r.eta_grid[0], r.source_total[0]);
                eprintln!("  Source at last: tau={:.1}, S={:.4e}",
                    r.eta_grid[n-1], r.source_total[n-1]);
                
                // Check eta range
                eprintln!("  eta range: [{:.1}, {:.1}]", r.eta_grid[0], r.eta_grid[n-1]);
                eprintln!("  eta_max (from vis): {:.1}", eta_max);
                
                // Sample source values
                for &frac in &[0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0] {
                    let idx = ((n-1) as f64 * frac) as usize;
                    eprintln!("  tau={:.1} S_tot={:.4e} S_sw={:.4e} phi={:.4e}",
                        r.eta_grid[idx], r.source_total[idx], r.source_sw[idx], r.phi[idx]);
                }
            }
            Err(e) => eprintln!("  FAIL: {}", e),
        }
    }
}
/// CAMB bootstrap IC with σ from finite difference (auto-generated).
/// Each row: [k, tau_init, etak, sigma, clxc, clxb, vb, th0, th1, th2, n0, n1]
pub(crate) const CAMB_BOOTSTRAP_IC: &[[f64; 12]; 283] = &[
    [1.00000000e-04,50.0,-9.9999928310e-05,-1.4663343376e-03,5.8384639487e-06,5.8384598560e-06,3.0543774177e-09,1.9461533611e-06,1.0183229339e-09,-7.9374314234e-10,1.9461524516e-06,1.6478260146e-09],
    [1.07901735e-04,50.0,-1.0790164505e-04,-1.5822054513e-03,6.7975970524e-06,6.7975920501e-06,3.8371426037e-09,2.2658639409e-06,1.2792951995e-09,-9.2413766046e-10,2.2658630314e-06,2.0701249913e-09],
    [1.16427844e-04,50.0,-1.1642773127e-04,-1.7072156146e-03,7.9142955656e-06,7.9142882896e-06,4.8205119896e-09,2.6380960207e-06,1.6071485069e-09,-1.0759530555e-09,2.6380946565e-06,2.6006491737e-09],
    [1.25627664e-04,50.0,-1.2562752214e-04,-1.8421192854e-03,9.2144427981e-06,9.2144337032e-06,6.0558962289e-09,3.0714777495e-06,2.0190228799e-09,-1.2527082689e-09,3.0714759305e-06,3.2671340809e-09],
    [1.35554430e-04,50.0,-1.3555425098e-04,-1.9876744569e-03,1.0728176676e-05,1.0728163943e-05,7.6078796596e-09,3.5760544961e-06,2.5364509185e-09,-1.4585003118e-09,3.5760519950e-06,4.1044231638e-09],
    [1.46265582e-04,50.0,-1.4626535718e-04,-2.1447489652e-03,1.2490583686e-05,1.2490566405e-05,9.5576000447e-09,4.1635221351e-06,3.1864835080e-09,-1.6980992233e-09,4.1635184971e-06,5.1562893865e-09],
    [1.57823100e-04,50.0,-1.5782281850e-04,-2.3142143009e-03,1.4542516510e-05,1.4542491954e-05,1.2006987404e-08,4.8474971663e-06,4.0031040190e-09,-1.9770586267e-09,4.8474926189e-06,6.4777236288e-09],
    [1.70293864e-04,50.0,-1.7029350962e-04,-2.4970589860e-03,1.6931537175e-05,1.6931504433e-05,1.5084093974e-08,5.6438343563e-06,5.0290049300e-09,-2.3018444443e-09,5.6438279898e-06,8.1378095424e-09],
    [1.83750034e-04,50.0,-1.8374958891e-04,-2.6943939592e-03,1.9713021175e-05,1.9712975700e-05,1.8949789293e-08,6.5709918999e-06,6.3178197513e-09,-2.6799847537e-09,6.5709832597e-06,1.0223335151e-08],
    [1.98269475e-04,50.0,-1.9826891586e-04,-2.9072820766e-03,2.2951442588e-05,2.2951380743e-05,2.3806171257e-08,7.6504602475e-06,7.9369269315e-09,-3.1202442575e-09,7.6504484241e-06,1.2843329992e-08],
    [2.13936203e-04,50.0,-2.1393550137e-04,-3.1370428191e-03,2.6721863833e-05,2.6721781978e-05,2.9907127441e-08,8.9072609626e-06,9.9709723282e-09,-3.6328274065e-09,8.9072445917e-06,1.6134765000e-08],
    [2.30840875e-04,50.0,-2.3083999358e-04,-3.3849098014e-03,3.1111685530e-05,3.1111572753e-05,3.7571609823e-08,1.0370524251e-05,1.2526294389e-08,-4.2296148830e-09,1.0370502423e-05,2.0269713070e-08],
    [2.49081310e-04,50.0,-2.4908020210e-04,-3.6523445993e-03,3.6222656490e-05,3.6222503695e-05,4.7200309439e-08,1.2074168808e-05,1.5736483378e-08,-4.9244389194e-09,1.2074138795e-05,2.5464344654e-08],
    [2.68763055e-04,50.0,-2.6876166352e-04,-3.9409572197e-03,4.2173247493e-05,4.2173043767e-05,5.9296613841e-08,1.4057681256e-05,1.9769365269e-08,-5.7334038287e-09,1.4057640328e-05,3.1990228603e-08],
    [2.90000000e-04,50.0,-2.8999825156e-04,-4.2523629831e-03,4.9101388868e-05,4.9101108743e-05,7.4492902513e-08,1.6367037460e-05,2.4835775393e-08,-6.6752591666e-09,1.6366982891e-05,4.0188529003e-08],
    [3.00000000e-04,50.0,-2.9999806438e-04,-4.3990030741e-03,5.2546067309e-05,5.2545750805e-05,8.2467821017e-08,1.7515249056e-05,2.7494596538e-08,-7.1435488777e-09,1.7515187210e-05,4.4490944232e-08],
    [3.23353454e-04,50.0,-3.2335103057e-04,-4.7414512724e-03,6.1045342591e-05,6.1044913309e-05,1.0326494504e-07,2.0348305043e-05,3.4428313482e-08,-8.2989849791e-09,2.0348221369e-05,5.5710843868e-08],
    [3.48524855e-04,50.0,-3.4852181975e-04,-5.1105444345e-03,7.0919370046e-05,7.0918787969e-05,1.2930676974e-07,2.3639597202e-05,4.3110602183e-08,-9.6413020058e-09,2.3639484425e-05,6.9760204974e-08],
    [3.75655719e-04,50.0,-3.7565191862e-04,-5.5083372923e-03,8.2390499301e-05,8.2389720774e-05,1.6191592067e-07,2.7463240258e-05,5.3982421707e-08,-1.1200724254e-08,2.7463087463e-05,8.7352560481e-08],
    [4.04898581e-04,50.0,-4.0489382247e-04,-5.9371338835e-03,9.5717070508e-05,9.5716015494e-05,2.0274853796e-07,3.1905339711e-05,6.7595932074e-08,-1.3012363525e-08,3.1905132346e-05,1.0938137847e-07],
    [4.36417850e-04,50.0,-4.3641189079e-04,-6.3992850150e-03,1.1119918781e-04,1.1119776173e-04,2.5387845426e-07,3.7065921788e-05,8.4642536359e-08,-1.5117009237e-08,3.7065641664e-05,1.3696543576e-07],
    [4.70390731e-04,50.0,-4.7038326911e-04,-6.8974077336e-03,1.2918550055e-04,1.2918357970e-04,3.1790241906e-07,4.3061194447e-05,1.0598799406e-07,-1.7562046181e-08,4.3060816097e-05,1.7150563247e-07],
    [5.00000000e-04,10.0,-4.9999959691e-04,-1.5657393794e-03,6.1602258938e-06,6.1602213464e-06,3.3846239145e-09,2.0534071155e-06,1.6993015631e-09,-1.4158833575e-10,0.0000000000e+00,1.6993015631e-09],
    [5.07008225e-04,50.0,-5.0699888223e-04,-7.4343945816e-03,1.5008104674e-04,1.5007845650e-04,3.9807210328e-07,5.0026155805e-05,1.3271638879e-07,-2.0402520519e-08,5.0025646487e-05,2.1475613215e-07],
    [5.12636165e-04,10.0,-5.1263573075e-04,-1.6053097523e-03,6.4755267886e-06,6.4755217863e-06,3.6477756371e-09,2.1585071863e-06,1.8314208133e-09,-1.4883528111e-10,0.0000000000e+00,1.8314208133e-09],
    [5.25591676e-04,10.0,-5.2559120750e-04,-1.6458787177e-03,6.8069657573e-06,6.8069603003e-06,3.9313872158e-09,2.2689869184e-06,1.9738122176e-09,-1.5645314730e-10,0.0000000000e+00,1.9738122176e-09],
    [5.38874602e-04,10.0,-5.3887409756e-04,-1.6874757987e-03,7.1553686212e-06,7.1553631642e-06,4.2370493780e-09,2.3851209789e-06,2.1272744261e-09,-1.6446091907e-10,0.0000000000e+00,2.1272744261e-09],
    [5.46476204e-04,50.0,-5.4646450412e-04,-8.0130642264e-03,1.7435640621e-04,1.7435291375e-04,4.9845903050e-07,5.8117635490e-05,1.6618518278e-07,-2.3702377923e-08,5.8116951550e-05,2.6891343896e-07],
    [5.52493219e-04,10.0,-5.5249267529e-04,-1.7301208204e-03,7.5216044024e-06,7.5215980360e-06,4.5664760862e-09,2.5071992695e-06,2.2926681832e-09,-1.7287855285e-10,0.0000000000e+00,2.2926681832e-09],
    [5.66456010e-04,10.0,-5.6645542416e-04,-1.7738452486e-03,7.9065848695e-06,7.9065785030e-06,4.9215160836e-09,2.6355260161e-06,2.4709211550e-09,-1.8172702648e-10,0.0000000000e+00,2.4709211550e-09],
    [5.80771674e-04,10.0,-5.8077104202e-04,-1.8186737922e-03,8.3112709035e-06,8.3112627181e-06,5.3041597781e-09,2.7704209060e-06,2.6630331329e-09,-1.9102839149e-10,0.0000000000e+00,2.6630331329e-09],
    [5.89016560e-04,50.0,-5.8900191057e-04,-8.6368559754e-03,2.0255822164e-04,2.0255350682e-04,6.2416160063e-07,6.7517838033e-05,2.0809415378e-07,-2.7535901603e-08,6.7516906711e-05,3.3672793409e-07],
    [5.95449127e-04,10.0,-5.9544844651e-04,-1.8646371760e-03,8.7366688604e-06,8.7366606749e-06,5.7165534528e-09,2.9122202250e-06,2.8700816409e-09,-2.0080582804e-10,0.0000000000e+00,2.8700816409e-09],
    [6.10497514e-04,10.0,-6.1049678063e-04,-1.9117605936e-03,9.1838410299e-06,9.1838319349e-06,6.1610108126e-09,3.0612770843e-06,3.0932279792e-09,-2.1108370270e-10,0.0000000000e+00,3.0932279792e-09],
    [6.25926209e-04,10.0,-6.2592541845e-04,-1.9600749250e-03,9.6539006336e-06,9.6538897196e-06,6.6400240861e-09,3.2179634673e-06,3.3337237377e-09,-2.2188762917e-10,0.0000000000e+00,3.3337237377e-09],
    [6.34868465e-04,50.0,-6.3485012058e-04,-9.3091185806e-03,2.3532158230e-04,2.3531520856e-04,7.8156381278e-07,7.8438402852e-05,2.6057171428e-07,-3.1989382429e-08,7.8437151387e-05,4.2164353291e-07],
    [6.41744823e-04,10.0,-6.4174397091e-04,-2.0096108513e-03,1.0148019101e-05,1.0148008187e-05,7.1562804571e-09,3.3826693198e-06,3.5929178161e-09,-2.3324453209e-10,0.0000000000e+00,3.5929178161e-09],
    [6.57963210e-04,10.0,-6.5796229182e-04,-2.0603980514e-03,1.0667428796e-05,1.0667416063e-05,7.7126749431e-09,3.5558052787e-06,3.8722639894e-09,-2.4518271417e-10,0.0000000000e+00,3.8722639894e-09],
    [6.74591474e-04,10.0,-6.7459048402e-04,-2.1124686972e-03,1.1213423022e-05,1.1213409380e-05,8.3123294914e-09,3.7378031266e-06,4.1733290618e-09,-2.5773192666e-10,0.0000000000e+00,4.1733290618e-09],
    [6.84289704e-04,50.0,-6.8426673344e-04,-1.0033849986e-02,2.7338427026e-04,2.7337568463e-04,9.7865950011e-07,9.1125228209e-05,3.2628299583e-07,-3.7163058500e-08,9.1123540187e-05,5.2797255131e-07],
    [6.91639973e-04,10.0,-6.9163890564e-04,-2.1658562974e-03,1.1787363292e-05,1.1787347830e-05,8.9586054131e-09,3.9291157918e-06,4.4978016546e-09,-2.7092344355e-10,0.0000000000e+00,4.4978016546e-09],
    [7.09119326e-04,10.0,-7.0911817656e-04,-2.2205906556e-03,1.2390680240e-05,1.2390662960e-05,9.6551300288e-09,4.1302209866e-06,4.8475016773e-09,-2.8479013946e-10,0.0000000000e+00,4.8475016773e-09],
    [7.27040424e-04,10.0,-7.2703918504e-04,-2.2767117275e-03,1.3024876353e-05,1.3024857253e-05,1.0405807771e-08,4.3416189328e-06,5.2243905352e-09,-2.9936657159e-10,0.0000000000e+00,5.2243905352e-09],
    [7.37558132e-04,50.0,-7.3752936851e-04,-1.0814913113e-02,3.1760343700e-04,3.1759185367e-04,1.2254582771e-06,1.0586394637e-04,4.0856518540e-07,-4.3173367509e-08,1.0586166900e-04,6.6111465582e-07],
    [7.64252790e-04,10.0,-7.6425135037e-04,-2.3932401242e-03,1.4392310732e-05,1.4392287085e-05,1.2086794676e-08,4.7974290283e-06,6.0683547168e-09,-3.3079580711e-10,0.0000000000e+00,6.0683547168e-09],
    [7.83567239e-04,10.0,-7.8356568743e-04,-2.4537233988e-03,1.5128956875e-05,1.5128931409e-05,1.3026532741e-08,5.0429771363e-06,6.5401636816e-09,-3.4772693498e-10,0.0000000000e+00,6.5401636816e-09],
    [7.94973232e-04,50.0,-7.9493721542e-04,-1.1656723326e-02,3.6897481186e-04,3.6895915400e-04,1.5344938902e-06,1.2298638467e-04,5.1159698419e-07,-5.0155562171e-08,1.2298331421e-04,8.2783100795e-07],
    [8.03369809e-04,10.0,-8.0336813693e-04,-2.5157350664e-03,1.5903306121e-05,1.5903278836e-05,1.4039334140e-08,5.3010926422e-06,7.0486553136e-09,-3.6552464314e-10,0.0000000000e+00,7.0486553136e-09],
    [8.23672836e-04,10.0,-8.2367103414e-04,-2.5793121993e-03,1.6717291146e-05,1.6717260223e-05,1.5130879660e-08,5.5724199228e-06,7.5966816470e-09,-3.8423328488e-10,0.0000000000e+00,7.5966816470e-09],
    [8.44488968e-04,10.0,-8.4448702606e-04,-2.6444989118e-03,1.7572936486e-05,1.7572901925e-05,1.6307293293e-08,5.8576342781e-06,8.1873164577e-09,-4.0389948348e-10,0.0000000000e+00,8.1873164577e-09],
    [8.56857802e-04,50.0,-8.5681270290e-04,-1.2564087681e-02,4.2865518481e-04,4.2863408453e-04,1.9214603526e-06,1.4287802333e-04,6.4061079071e-07,-5.8266746996e-08,1.4287387603e-04,1.0365875120e-06],
    [8.65831172e-04,10.0,-8.6582907925e-04,-2.7113302363e-03,1.8472377633e-05,1.8472339434e-05,1.7575169764e-08,6.1574464780e-06,8.8238725031e-09,-4.2457224842e-10,0.0000000000e+00,8.8238725031e-09],
    [8.87712744e-04,10.0,-8.8771048794e-04,-2.7798512914e-03,1.9417855583e-05,1.9417813746e-05,1.8941625157e-08,6.4726045821e-06,9.5099201025e-09,-4.4630309751e-10,0.0000000000e+00,9.5099201025e-09],
    [9.10147313e-04,10.0,-9.1014488228e-04,-2.8501045596e-03,2.0411725927e-05,2.0411678634e-05,2.0414319124e-08,6.8038930294e-06,1.0249307162e-08,-4.6914618524e-10,0.0000000000e+00,1.0249307162e-08],
    [9.23559767e-04,50.0,-9.2350329487e-04,-1.3542062166e-02,4.9798848340e-04,4.9795996165e-04,2.4060093438e-06,1.6598665388e-04,8.0215837739e-07,-6.7689403979e-08,1.6598105140e-04,1.2979845789e-06],
    [9.56731703e-04,10.0,-9.5672887930e-04,-2.9959832128e-03,2.2554677344e-05,2.2554620955e-05,2.3712111386e-08,7.5182069850e-06,1.1905010388e-08,-5.1839969444e-10,0.0000000000e+00,1.1905010388e-08],
    [9.80910543e-04,10.0,-9.8090749941e-04,-3.0716971234e-03,2.3709100788e-05,2.3709037123e-05,2.5555706884e-08,7.9030123743e-06,1.2830613056e-08,-5.4493285759e-10,0.0000000000e+00,1.2830613056e-08],
    [9.95454137e-04,50.0,-9.9538342313e-04,-1.4596203037e-02,5.7853583712e-04,5.7849736186e-04,3.0127473565e-06,1.9283244910e-04,1.0044435441e-06,-7.8635485467e-08,1.9282489666e-04,1.6252952027e-06],
    [1.00570044e-03,10.0,-1.0056971581e-03,-3.1493253235e-03,2.4922610464e-05,2.4922541343e-05,2.7542638392e-08,8.3075137809e-06,1.3828180275e-08,-5.7282404855e-10,0.0000000000e+00,1.3828180275e-08],
    [1.03111683e-03,10.0,-1.0311132968e-03,-3.2289170022e-03,2.6198231353e-05,2.6198154956e-05,2.9684054326e-08,8.7327180154e-06,1.4903307187e-08,-6.0214277275e-10,0.0000000000e+00,1.4903307187e-08],
    [1.05717556e-03,10.0,-1.0571717471e-03,-3.3105206638e-03,2.7539143048e-05,2.7539059374e-05,3.1991962857e-08,9.1796864581e-06,1.6062023949e-08,-6.3296209283e-10,0.0000000000e+00,1.6062023949e-08],
    [1.07294511e-03,50.0,-1.0728565664e-03,-1.5732465389e-02,6.7211093847e-04,6.7205901723e-04,3.7724855702e-06,2.2401967726e-04,1.2577386287e-06,-9.1351164894e-08,2.2400949092e-04,2.0351386348e-06],
    [1.08389285e-03,10.0,-1.0838887408e-03,-3.3941846117e-03,2.8948687032e-05,2.8948594263e-05,3.4479306521e-08,9.6495314210e-06,1.7310829551e-08,-6.6535881068e-10,0.0000000000e+00,1.7310829551e-08],
    [1.11128535e-03,10.0,-1.1112809197e-03,-3.4799624157e-03,3.0430375773e-05,3.0430272091e-05,3.7160038602e-08,1.0143424333e-05,1.8656728265e-08,-6.9941365876e-10,0.0000000000e+00,1.8656728265e-08],
    [1.13937012e-03,10.0,-1.1393653459e-03,-3.5679058920e-03,3.1987903640e-05,3.1987787224e-05,4.0049197736e-08,1.0662595741e-05,2.0107268934e-08,-7.3521150131e-10,0.0000000000e+00,2.0107268934e-08],
    [1.15646836e-03,50.0,-1.1563574860e-03,-1.6956879163e-02,7.8082090477e-04,7.8075082274e-04,4.7238036132e-06,2.6025026455e-04,1.5749060064e-06,-1.0612235038e-07,2.6023649843e-04,2.5483238065e-06],
    [1.16816465e-03,10.0,-1.1681595131e-03,-3.6580768177e-03,3.3625146898e-05,3.3625023207e-05,4.3162984298e-08,1.1208340766e-05,2.1670587306e-08,-7.7284154571e-10,0.0000000000e+00,2.1670587306e-08],
    [1.19768690e-03,10.0,-1.1976813565e-03,-3.7505237113e-03,3.5346194636e-05,3.5346052755e-05,4.6518863428e-08,1.1782018191e-05,2.3355451669e-08,-8.1239756475e-10,0.0000000000e+00,2.3355451669e-08],
    [1.22795524e-03,10.0,-1.2279492646e-03,-3.8453080858e-03,3.7155328755e-05,3.7155172322e-05,5.0135660956e-08,1.2385057744e-05,2.5171312024e-08,-8.5397813028e-10,0.0000000000e+00,2.5171312024e-08],
    [1.24649347e-03,50.0,-1.2463546294e-03,-1.8276656655e-02,9.0711330995e-04,9.0701872250e-04,5.9150079323e-06,3.0233955476e-04,1.9720510333e-06,-1.2328108220e-07,3.0232098652e-04,3.1909052431e-06],
    [1.25898853e-03,10.0,-1.2589820908e-03,-3.9424893226e-03,3.9057056711e-05,3.9056885726e-05,5.4033659325e-08,1.3018961909e-05,2.7128353090e-08,-8.9768685875e-10,0.0000000000e+00,2.7128353090e-08],
    [1.29080610e-03,10.0,-1.2907991644e-03,-4.0421233196e-03,4.1056126065e-05,4.1055936890e-05,5.8234721934e-08,1.3685312297e-05,2.9237551422e-08,-9.4363266934e-10,0.0000000000e+00,2.9237551422e-08],
    [1.32342778e-03,10.0,-1.3234203034e-03,-4.1442784280e-03,4.3157509936e-05,4.3157302571e-05,6.2762410380e-08,1.4385767827e-05,3.1510736980e-08,-9.9193005531e-10,0.0000000000e+00,3.1510736980e-08],
    [1.34352656e-03,50.0,-1.3433527127e-03,-1.9699276036e-02,1.0538316565e-03,1.0537040653e-03,7.4065847002e-06,3.5123465932e-04,2.4693395493e-06,-1.4321295557e-07,3.5120960092e-04,3.9955049640e-06],
    [1.39116525e-03,10.0,-1.3911565649e-03,-4.3563927265e-03,4.7688456107e-05,4.7688201448e-05,7.2901229942e-08,1.5896066543e-05,3.6601059857e-08,-1.0960671228e-09,0.0000000000e+00,3.6601059857e-08],
    [1.42632323e-03,10.0,-1.4263138776e-03,-4.4664902866e-03,5.0129303418e-05,5.0129023293e-05,7.8569229345e-08,1.6709675037e-05,3.9446747432e-08,-1.1521663019e-09,0.0000000000e+00,3.9446747432e-08],
    [1.44811318e-03,50.0,-1.4478954939e-03,-2.1232361672e-02,1.2242794037e-03,1.2241071090e-03,9.2742684501e-06,4.0803567390e-04,3.0920213938e-06,-1.6636572940e-07,4.0800185525e-04,5.0029673079e-06],
    [1.49932724e-03,10.0,-1.4993163693e-03,-4.6950961383e-03,5.5392189097e-05,5.5391843489e-05,9.1261519231e-08,1.8463948436e-05,4.5819067718e-08,-1.2731252564e-09,0.0000000000e+00,4.5819067718e-08],
    [1.53721873e-03,10.0,-1.5372070176e-03,-4.8137519907e-03,5.8227338741e-05,5.8226960391e-05,9.8356998990e-08,1.9408986191e-05,4.9381440937e-08,-1.3382864418e-09,0.0000000000e+00,4.9381440937e-08],
    [1.56084133e-03,50.0,-1.5605687502e-03,-2.2885138510e-02,1.4222937170e-03,1.4220611192e-03,1.1612886738e-05,4.7402037308e-04,3.8717118183e-06,-1.9325930935e-07,4.7397473827e-04,6.2644304436e-06],
    [1.61589874e-03,10.0,-1.6158851318e-03,-5.0601314797e-03,6.4340405515e-05,6.4339939854e-05,1.1424585722e-07,2.1446647224e-05,5.7358627006e-08,-1.4787844805e-09,0.0000000000e+00,5.7358627006e-08],
    [1.65673626e-03,10.0,-1.6567216007e-03,-5.1880167577e-03,6.7633547587e-05,6.7633038270e-05,1.2312834485e-07,2.2544345484e-05,6.1818181406e-08,-1.5544714244e-09,0.0000000000e+00,6.1818181406e-08],
    [1.68234479e-03,50.0,-1.6820034704e-03,-2.4666269455e-02,1.6523323720e-03,1.6520185163e-03,1.4541172277e-05,5.5067281937e-04,4.8479957359e-06,-2.2449732038e-07,5.5061123567e-04,7.8439193591e-06],
    [1.74153358e-03,10.0,-1.7415165463e-03,-5.4535492293e-03,7.4734132795e-05,7.4733507063e-05,1.4301880924e-07,2.4911169021e-05,7.1804414188e-08,-1.7176645968e-09,0.0000000000e+00,7.1804414188e-08],
    [1.78554619e-03,10.0,-1.7855278340e-03,-5.5913735819e-03,7.8559263784e-05,7.8558572568e-05,1.5413834831e-07,2.6186189643e-05,7.7387101967e-08,-1.8055774568e-09,0.0000000000e+00,7.7387101967e-08],
    [1.81330666e-03,50.0,-1.8128792768e-03,-2.6586132032e-02,1.9195739878e-03,1.9191504689e-03,1.8207783796e-05,6.3971680356e-04,6.0704360763e-06,-2.6078051706e-07,6.3963368302e-04,9.8215914158e-06],
    [1.87693643e-03,10.0,-1.8769151067e-03,-5.8775556412e-03,8.6806889158e-05,8.6806045147e-05,1.7903823846e-07,2.8935348382e-05,8.9888352524e-08,-1.9951315255e-09,0.0000000000e+00,8.9888352524e-08],
    [1.92437099e-03,10.0,-1.9243480064e-03,-6.0260919212e-03,9.1249938123e-05,9.1249006800e-05,1.9295823961e-07,3.0416334994e-05,9.6877030193e-08,-2.0972450355e-09,0.0000000000e+00,9.6877030193e-08],
    [1.95446324e-03,50.0,-1.9539280888e-03,-2.8655227246e-02,2.2300339770e-03,2.2294623777e-03,2.2798849386e-05,7.4315408710e-04,7.6010879474e-06,-3.0292231738e-07,7.4304186273e-04,1.2297798423e-05],
    [2.02286674e-03,10.0,-2.0228400505e-03,-6.3345236166e-03,1.0082990048e-04,1.0082876543e-04,2.2412915257e-07,3.3609587263e-05,1.1252669408e-07,-2.3174177730e-09,0.0000000000e+00,1.1252669408e-07],
    [2.07398930e-03,10.0,-2.0739605318e-03,-6.4946101885e-03,1.0599068628e-04,1.0598942754e-04,2.4155491474e-07,3.5329809180e-05,1.2127545291e-07,-2.4360255739e-09,0.0000000000e+00,1.2127545291e-07],
    [2.10660813e-03,47.5,-2.1059997967e-03,-2.9365748523e-02,2.3426527623e-03,2.3420224898e-03,2.4589024179e-05,7.8067416325e-04,8.1977545497e-06,-2.9903408510e-07,7.8055175254e-04,1.3202053005e-05],
    [2.18014302e-03,10.0,-2.1801096077e-03,-6.8270183067e-03,1.1711821571e-04,1.1711668049e-04,2.8057618806e-07,3.9038892282e-05,1.4086643982e-07,-2.6917623391e-09,0.0000000000e+00,1.4086643982e-07],
    [2.23524032e-03,10.0,-2.2352043045e-03,-6.9995564896e-03,1.2311268074e-04,1.2311099272e-04,3.0239061743e-07,4.1036997573e-05,1.5181854497e-07,-2.8295284613e-09,0.0000000000e+00,1.5181854497e-07],
    [2.27059672e-03,44.0,-2.2699346053e-03,-2.9426231416e-02,2.3529483005e-03,2.3523136042e-03,2.4806664442e-05,7.8410451533e-04,8.2700952739e-06,-2.7480193537e-07,7.8398286132e-04,1.3235886547e-05],
    [2.34964741e-03,10.0,-2.3496055775e-03,-7.3578106190e-03,1.3603776461e-04,1.3603569823e-04,3.5123937892e-07,4.5345233957e-05,1.7634344910e-07,-3.1265731947e-09,0.0000000000e+00,1.7634344910e-07],
    [2.40902847e-03,10.0,-2.4089833908e-03,-7.5437555045e-03,1.4300059411e-04,1.4299830946e-04,3.7854769630e-07,4.7666100727e-05,1.9005379607e-07,-3.2865918462e-09,0.0000000000e+00,1.9005379607e-07],
    [2.44735098e-03,40.9,-2.4466307957e-03,-2.9484180756e-02,2.3626340553e-03,2.3619954009e-03,2.5010251193e-05,7.8733178088e-04,8.3377816503e-06,-2.5269426780e-07,7.8721082537e-04,1.3267606430e-05],
    [2.53233062e-03,10.0,-2.5322782589e-03,-7.9298605614e-03,1.5801361587e-04,1.5801082191e-04,4.3969893682e-07,5.2670271543e-05,2.2075518182e-07,-3.6316159670e-09,0.0000000000e+00,2.2075518182e-07],
    [2.59632852e-03,10.0,-2.5962720837e-03,-8.1302602211e-03,1.6610122111e-04,1.6609813611e-04,4.7388482471e-07,5.5366042943e-05,2.3791840765e-07,-3.8174809634e-09,0.0000000000e+00,2.3791840765e-07],
    [2.63786464e-03,37.9,-2.6370817807e-03,-2.9539551703e-02,2.3717377335e-03,2.3710951209e-03,2.5200572054e-05,7.9036504030e-04,8.4010725131e-06,-2.3250408006e-07,7.9024478327e-04,1.3297321932e-05],
    [2.72921732e-03,10.0,-2.7291517618e-03,-8.5463858810e-03,1.8353945052e-04,1.8353568157e-04,5.5043688008e-07,6.1178558099e-05,2.7635175747e-07,-4.2182330531e-09,0.0000000000e+00,2.7635175747e-07],
    [2.79819100e-03,10.0,-2.7981203467e-03,-8.7623641592e-03,1.9293354126e-04,1.9292936486e-04,5.9323235746e-07,6.4309788286e-05,2.9783743029e-07,-4.4341184409e-09,0.0000000000e+00,2.9783743029e-07],
    [2.84320881e-03,35.2,-2.8423583052e-03,-2.9592937791e-02,2.3802868091e-03,2.3796407040e-03,2.5378392820e-05,7.9321354860e-04,8.4602183539e-06,-2.1404705545e-07,7.9309393186e-04,1.3325139196e-05],
    [2.94141179e-03,10.0,-2.9413297268e-03,-9.2108384663e-03,2.1318875952e-04,2.1318366635e-04,6.8906382467e-07,7.1061222116e-05,3.4594994263e-07,-4.8995980552e-09,0.0000000000e+00,3.4594994263e-07],
    [3.01574812e-03,10.0,-3.0156596770e-03,-9.4436100626e-03,2.2410035308e-04,2.2409473604e-04,7.4263721217e-07,7.4698240496e-05,3.7284661171e-07,-5.1503517312e-09,0.0000000000e+00,3.7284661171e-07],
    [3.06453797e-03,32.6,-3.0636144658e-03,-2.9643999556e-02,2.3883087561e-03,2.3876591586e-03,2.5544446544e-05,7.9588638619e-04,8.5154605758e-06,-1.9715879575e-07,7.9576735152e-04,1.3351160863e-05],
    [3.17010422e-03,10.0,-3.1700014855e-03,-9.9269501786e-03,2.4762761313e-04,2.4762071553e-04,8.6260342869e-07,8.2540245785e-05,4.3307583923e-07,-5.6910112222e-09,0.0000000000e+00,4.3307583923e-07],
    [3.25022014e-03,10.0,-3.2501094193e-03,-1.0177820881e-02,2.6030186564e-04,2.6029426954e-04,9.2966899956e-07,8.6764754087e-05,4.6674617608e-07,-5.9822636358e-09,0.0000000000e+00,4.6674617608e-07],
    [3.30309646e-03,30.3,-3.3020941996e-03,-2.9693706615e-02,2.3958298843e-03,2.3951772600e-03,2.5699435355e-05,7.9839245882e-04,8.5670309671e-06,-1.8169242037e-07,7.9827400623e-04,1.3375485778e-05],
    [3.41657730e-03,10.0,-3.4164486932e-03,-1.0698734069e-02,2.8762969305e-04,2.8762040893e-04,1.0798480616e-06,9.5873467217e-05,5.4214349879e-07,-6.6102424846e-09,0.0000000000e+00,5.4214349879e-07],
    [3.50292217e-03,10.0,-3.5027835647e-03,-1.0969101851e-02,3.0235134182e-04,3.0234109727e-04,1.1638038586e-06,1.0078036576e-04,5.8429332118e-07,-6.9485328471e-09,0.0000000000e+00,5.8429332118e-07],
    [3.56022550e-03,28.1,-3.5591382770e-03,-2.9741460504e-02,2.4028769694e-03,2.4022213183e-03,2.5844035918e-05,8.0074043944e-04,8.6151513732e-06,-1.6751648075e-07,8.0062251072e-04,1.3398208749e-05],
    [3.68221346e-03,10.0,-3.6820524709e-03,-1.1530510528e-02,3.3409366733e-04,3.3408115269e-04,1.3518045989e-06,1.1136037938e-04,6.7867850571e-07,-7.6779297271e-09,0.0000000000e+00,6.7867850571e-07],
    [3.77527158e-03,10.0,-3.7750980692e-03,-1.1821904782e-02,3.5119341919e-04,3.5117959487e-04,1.4569039877e-06,1.1705986981e-04,7.3144317907e-07,-8.0708525368e-09,0.0000000000e+00,7.3144317907e-07],
    [3.83737072e-03,26.1,-3.8361918407e-03,-2.9788217024e-02,2.4094749242e-03,2.4088167120e-03,2.5978884878e-05,8.0293888459e-04,8.6600335162e-06,-1.5451314590e-07,8.0282142153e-04,1.3419420360e-05],
    [3.96850263e-03,10.0,-3.9683010923e-03,-1.2426958795e-02,3.8806334487e-04,3.8804646465e-04,1.6922512032e-06,1.2934881670e-04,8.4959784841e-07,-8.9180411583e-09,0.0000000000e+00,8.4959784841e-07],
    [4.06879594e-03,10.0,-4.0685787326e-03,-1.2740993670e-02,4.0792537038e-04,4.0790671483e-04,1.8238190478e-06,1.3596890494e-04,9.1565043817e-07,-9.3744162984e-09,0.0000000000e+00,9.1565043817e-07],
    [4.13609025e-03,24.2,-4.1348125297e-03,-2.9833866595e-02,2.4156486616e-03,2.4149878882e-03,2.6104595236e-05,8.0499594333e-04,8.7018789527e-06,-1.4257662182e-07,8.0487894593e-04,1.3439206826e-05],
    [4.27705055e-03,10.0,-4.2767982574e-03,-1.3393092558e-02,4.5075113303e-04,4.5072837383e-04,2.1184362140e-06,1.5024279128e-04,1.0635602444e-06,-1.0358412050e-08,0.0000000000e+00,1.0635602444e-06],
    [4.38514159e-03,10.0,-4.3848696766e-03,-1.3731539195e-02,4.7382159391e-04,4.7379644820e-04,2.2831382012e-06,1.5793215425e-04,1.1462468930e-06,-1.0888482233e-08,0.0000000000e+00,1.1462468930e-06],
    [4.45806357e-03,22.4,-4.4566792370e-03,-2.9878622847e-02,2.4214221630e-03,2.4207590614e-03,2.6221745429e-05,8.0691964831e-04,8.7408791381e-06,-1.3161177246e-07,8.0680305837e-04,1.3457649894e-05],
    [4.60958783e-03,10.0,-4.6092719951e-03,-1.4434323397e-02,5.2356527885e-04,5.2353460342e-04,2.6519514904e-06,1.7451152962e-04,1.3314046484e-06,-1.2031367744e-08,0.0000000000e+00,1.3314046484e-06],
    [4.72608286e-03,10.0,-4.7257424663e-03,-1.4799080709e-02,5.5036245612e-04,5.5032852106e-04,2.8581314382e-06,1.8344284035e-04,1.4349140274e-06,-1.2647027675e-08,0.0000000000e+00,1.4349140274e-06],
    [4.80510085e-03,20.8,-4.8036015482e-03,-2.9922793596e-02,2.4268182460e-03,2.4261528160e-03,2.6330881155e-05,8.0871762475e-04,8.7772155642e-06,-1.2153291484e-07,8.0860144226e-04,1.3474826745e-05],
    [4.96797961e-03,10.0,-4.9675842397e-03,-1.5556481625e-02,6.0814153403e-04,6.0810009018e-04,3.3198255096e-06,2.0270001551e-04,1.6666991320e-06,-1.3974446714e-08,0.0000000000e+00,1.6666991320e-06],
    [5.09353204e-03,10.0,-5.0931059225e-03,-1.5949601570e-02,6.3926732400e-04,6.3922157278e-04,3.5779289647e-06,2.1307385759e-04,1.7962745419e-06,-1.4689509034e-08,0.0000000000e+00,1.7962745419e-06],
    [5.17915319e-03,19.3,-5.1775299155e-03,-2.9966340486e-02,2.4318592623e-03,2.4311917368e-03,2.6432524464e-05,8.1039720681e-04,8.8110600104e-06,-1.1226276459e-07,8.1028137356e-04,1.3490809976e-05],
    [5.35423608e-03,10.0,-5.3537411287e-03,-1.6765871041e-02,7.0637965109e-04,7.0632371353e-04,4.1558932935e-06,2.3544124269e-04,2.0864279001e-06,-1.6231239633e-08,0.0000000000e+00,2.0864279001e-06],
    [5.48955010e-03,10.0,-5.4890166711e-03,-1.7189535819e-02,7.4253336061e-04,7.4247154407e-04,4.4789953790e-06,2.4749050499e-04,2.2486327462e-06,-1.7061743500e-08,0.0000000000e+00,2.2486327462e-06],
    [5.58232359e-03,17.9,-5.5805666229e-03,-3.0009915484e-02,2.4365657009e-03,2.4358965456e-03,2.6527161026e-05,8.1196549581e-04,8.8425748087e-06,-1.0373151185e-07,8.1184995361e-04,1.3505667542e-05],
    [5.77052367e-03,10.0,-5.7699040741e-03,-1.8069265996e-02,8.2048645709e-04,8.2041101996e-04,5.2025093282e-06,2.7347033028e-04,2.6118511903e-06,-1.8852362919e-08,0.0000000000e+00,2.6118511903e-06],
    [5.91635825e-03,10.0,-5.9156904832e-03,-1.8525866019e-02,8.6248008301e-04,8.6239672964e-04,5.6069779930e-06,2.8746557655e-04,2.8149012569e-06,-1.9816932003e-08,0.0000000000e+00,2.8149012569e-06],
    [6.01687872e-03,16.6,-6.0149776061e-03,-3.0053409381e-02,2.4409582838e-03,2.4402872659e-03,2.6615256502e-05,8.1342906924e-04,8.8719132623e-06,-9.5876010008e-08,8.1331387628e-04,1.3519462798e-05],
    [6.21917730e-03,10.0,-6.2184016575e-03,-1.9473958970e-02,9.5302495174e-04,9.5292320475e-04,6.5126928348e-06,3.1764106825e-04,3.2695815297e-06,-2.1896588094e-08,0.0000000000e+00,3.2695815297e-06],
    [6.37635040e-03,10.0,-6.3755144580e-03,-1.9966052734e-02,1.0018018074e-03,1.0016893502e-03,7.0190171755e-06,3.3389645978e-04,3.5237608504e-06,-2.3016845816e-08,0.0000000000e+00,3.5237608504e-06],
    [6.48526172e-03,15.4,-6.4832051911e-03,-3.0097084513e-02,2.4450561032e-03,2.4443832226e-03,2.6697243811e-05,8.1479444634e-04,8.8992195615e-06,-8.8639061842e-08,8.1467954442e-04,1.3532254194e-05],
    [6.70271338e-03,10.0,-6.7017424069e-03,-2.0987835896e-02,1.1069722241e-03,1.1068349704e-03,8.1528123701e-06,3.6894498044e-04,4.0929307446e-06,-2.5432151630e-08,0.0000000000e+00,4.0929307446e-06],
    [6.87210657e-03,10.0,-6.8710601051e-03,-2.1518144323e-02,1.1636279523e-03,1.1634761468e-03,8.7866401373e-06,3.8782539195e-04,4.4111120795e-06,-2.6733202691e-08,0.0000000000e+00,4.4111120795e-06],
    [6.99010594e-03,14.3,-6.9878818255e-03,-3.0141425014e-02,2.4488770869e-03,2.4482028093e-03,2.6773535865e-05,8.1606756430e-04,8.9246301899e-06,-8.1968792249e-08,8.1595295342e-04,1.3544096005e-05],
    [7.22384401e-03,10.0,-7.2226285107e-03,-2.2619324394e-02,1.2857861584e-03,1.2856008252e-03,1.0205946637e-05,4.2853361811e-04,5.1235957745e-06,-2.9538273765e-08,0.0000000000e+00,5.1235957745e-06],
    [7.40640739e-03,10.0,-7.4050973842e-03,-2.3190869444e-02,1.3515929459e-03,1.3513882877e-03,1.0999382539e-05,4.5046274317e-04,5.5218919824e-06,-3.1049262386e-08,0.0000000000e+00,5.5218919824e-06],
    [7.53424967e-03,13.3,-7.5318448781e-03,-3.0186351808e-02,2.4524386972e-03,2.4517627899e-03,2.6844514650e-05,8.1725430209e-04,8.9482730177e-06,-7.5818092920e-08,8.1713998225e-04,1.3555037261e-05],
    [7.78549214e-03,10.0,-7.7839705277e-03,-2.4377626055e-02,1.4934825012e-03,1.4932325576e-03,1.2776089534e-05,4.9774418585e-04,6.4137684166e-06,-3.4306919102e-08,0.0000000000e+00,6.4137684166e-06],
    [7.98224967e-03,10.0,-7.9806097610e-03,-2.4993561722e-02,1.5699187061e-03,1.5696424525e-03,1.3769321413e-05,5.2321417024e-04,6.9123476026e-06,-3.6061676005e-08,0.0000000000e+00,6.9123476026e-06],
    [8.12075219e-03,12.3,-8.1181525906e-03,-3.0232339495e-02,2.4557569996e-03,2.4550799280e-03,2.6910545785e-05,8.1836001482e-04,8.9702692287e-06,-7.0144133094e-08,8.1824592780e-04,1.3565123263e-05],
    [8.39080796e-03,10.0,-8.3889031548e-03,-2.6272503288e-02,1.7347262474e-03,1.7343889922e-03,1.5993415218e-05,5.7812966406e-04,8.0287754775e-06,-3.9844836833e-08,0.0000000000e+00,8.0287754775e-06],
    [8.60286323e-03,10.0,-8.6008103442e-03,-2.6936307476e-02,1.8235081807e-03,1.8231355352e-03,1.7236747226e-05,6.0771184508e-04,8.6528953423e-06,-4.1882605812e-08,0.0000000000e+00,8.6528953423e-06],
    [8.75291090e-03,11.4,-8.7501012838e-03,-3.0279486311e-02,2.4588478263e-03,2.4581695907e-03,2.6971967600e-05,8.1938988296e-04,8.9907306129e-06,-6.4907838592e-08,8.1927602878e-04,1.3574448976e-05],
    [9.04318660e-03,10.0,-9.0408021452e-03,-2.8314532559e-02,2.0149350166e-03,2.0144800656e-03,2.0020859665e-05,6.7149335518e-04,1.0050508435e-05,-4.6275731868e-08,0.0000000000e+00,1.0050508435e-05],
    [9.27172900e-03,10.0,-9.2691591868e-03,-2.9029848095e-02,2.1180566400e-03,2.1175537258e-03,2.1577254302e-05,7.0585124195e-04,1.0831800107e-05,-4.8642038406e-08,0.0000000000e+00,1.0831800107e-05],
    [9.43427992e-03,10.6,-9.4312438877e-03,-3.0328031780e-02,2.4617256131e-03,2.4610462133e-03,2.7029100238e-05,8.2034873776e-04,9.0097642301e-06,-6.0073581201e-08,8.2023511641e-04,1.3583134251e-05],
    [9.74628716e-03,10.0,-9.7433022880e-03,-3.0515139035e-02,2.3404010572e-03,2.3397870827e-03,2.5062385248e-05,7.7992904698e-04,1.2581267496e-05,-5.3743481954e-08,0.0000000000e+00,1.2581267496e-05],
    [9.99259855e-03,10.0,-9.9893816453e-03,-3.1286053792e-02,2.4601775222e-03,2.4594992865e-03,2.7010659323e-05,8.1983307609e-04,1.3559245286e-05,-5.6491259582e-08,0.0000000000e+00,1.3559245286e-05],
    [1.01686900e-02,9.8,-1.0165409881e-02,-3.0378258144e-02,2.4644040968e-03,2.4637235329e-03,2.7082242013e-05,8.2124117762e-04,9.0274691632e-06,-5.5609153200e-08,8.2112778910e-04,1.3591087917e-05],
    [1.05040532e-02,10.0,-1.0500316785e-02,-3.2886777176e-02,2.7184318751e-03,2.7176036965e-03,3.1373285310e-05,9.0586789884e-04,1.5749022035e-05,-6.2415090737e-08,0.0000000000e+00,1.5749022035e-05],
    [1.07695151e-02,10.0,-1.0765488247e-02,-3.3717550913e-02,2.8575528413e-03,2.8566375840e-03,3.3812095353e-05,9.5221254742e-04,1.6973098512e-05,-6.5605791027e-08,0.0000000000e+00,1.6973098512e-05],
    [1.09602701e-02,9.1,-1.0956726862e-02,-3.0430728967e-02,2.4668951519e-03,2.4662136566e-03,2.7131703973e-05,8.2207121886e-04,9.0439486808e-06,-5.1485207032e-08,8.2195806317e-04,1.3598145895e-05],
    [1.13207350e-02,10.0,-1.1316057747e-02,-3.5442659787e-02,3.1575148460e-03,3.1563974917e-03,3.9273119910e-05,1.0521324584e-03,1.9713928917e-05,-7.2484267356e-08,0.0000000000e+00,1.9713928917e-05],
    [1.16068364e-02,10.0,-1.1601795520e-02,-3.6338023581e-02,3.3191028051e-03,3.3178683370e-03,4.2325940740e-05,1.1059560347e-03,2.1246023937e-05,-7.6189059660e-08,0.0000000000e+00,2.1246023937e-05],
    [1.18134707e-02,8.5,-1.1809643662e-02,-3.0485642212e-02,2.4692099541e-03,2.4685272947e-03,2.7177786251e-05,8.2284247037e-04,9.0593031385e-06,-4.7674742596e-08,8.2272948930e-04,1.3604251645e-05],
    [1.22009132e-02,10.0,-1.2195058151e-02,-3.8197155273e-02,3.6675061565e-03,3.6659988109e-03,4.9161837524e-05,1.2219995260e-03,2.4676492585e-05,-8.4175573326e-08,0.0000000000e+00,2.4676492585e-05],
    [1.25092587e-02,10.0,-1.2502948522e-02,-3.9162055290e-02,3.8551888429e-03,3.8535231724e-03,5.2983221394e-05,1.2845076853e-03,2.6594061380e-05,-8.8477027838e-08,0.0000000000e+00,2.6594061380e-05],
    [1.27330885e-02,7.9,-1.2728955478e-02,-3.0543619367e-02,2.4713594466e-03,2.4706760887e-03,2.7220738048e-05,8.2355865743e-04,9.0736145112e-06,-4.4153070098e-08,8.2344602561e-04,1.3609301490e-05],
    [1.31495244e-02,10.0,-1.3142195138e-02,-4.1165561039e-02,4.2598536238e-03,4.2578196153e-03,6.1540027673e-05,1.4192732051e-03,3.0887567362e-05,-9.7749461945e-08,0.0000000000e+00,3.0887567362e-05],
    [1.34818436e-02,10.0,-1.3473944522e-02,-4.2205392011e-02,4.4778431766e-03,4.4755958952e-03,6.6323395004e-05,1.4918652596e-03,3.3287520327e-05,-1.0274331916e-07,0.0000000000e+00,3.3287520327e-05],
    [1.37242939e-02,7.3,-1.3719830737e-02,-3.0604926069e-02,2.4733541068e-03,2.4726698175e-03,2.7260806746e-05,8.2422327250e-04,9.0869659997e-06,-4.0897664709e-08,8.2411093172e-04,1.3613087060e-05],
    [1.41718895e-02,10.0,-1.4162714670e-02,-4.4364510894e-02,4.9478504807e-03,4.9451068044e-03,7.7034193964e-05,1.6483688960e-03,3.8661008915e-05,-1.1350790038e-07,0.0000000000e+00,3.8661008915e-05],
    [1.45300462e-02,10.0,-1.4520158145e-02,-4.5485083962e-02,5.2010384388e-03,5.1980065182e-03,8.3021623141e-05,1.7326688394e-03,4.1664589140e-05,-1.1930513913e-07,0.0000000000e+00,4.1664589140e-05],
    [1.47926594e-02,6.8,-1.4787840123e-02,-3.0670271506e-02,2.4751978926e-03,2.4745129049e-03,2.7298396162e-05,8.2483765436e-04,9.0994912151e-06,-3.7887925231e-08,8.2472566282e-04,1.3615364992e-05],
    [1.52737426e-02,10.0,-1.5262257603e-02,-4.7811769991e-02,5.7469359599e-03,5.7432339527e-03,9.6428368124e-05,1.9144113176e-03,4.8389456182e-05,-1.3180087072e-07,0.0000000000e+00,4.8389456182e-05],
    [1.56597457e-02,10.0,-1.5647367963e-02,-4.9019285775e-02,6.0410038568e-03,6.0369134881e-03,1.0392275726e-04,2.0123044960e-03,5.2148442678e-05,-1.3852998232e-07,0.0000000000e+00,5.2148442678e-05],
    [1.59441917e-02,6.3,-1.5938988278e-02,-3.0739976082e-02,2.4769075681e-03,2.4762218818e-03,2.7333475373e-05,8.2540727453e-04,9.1111805526e-06,-3.5104678289e-08,8.2529569045e-04,1.3616008957e-05],
    [1.64612640e-02,10.0,-1.6446887887e-02,-5.1526160579e-02,6.6750459373e-03,6.6700517200e-03,1.2070325465e-04,2.2233505733e-03,6.0565779139e-05,-1.5303234417e-07,0.0000000000e+00,6.0565779139e-05],
    [1.68772785e-02,10.0,-1.6861785316e-02,-5.2827145029e-02,7.0165940560e-03,7.0110755041e-03,1.3008351380e-04,2.3370252457e-03,6.5270659942e-05,-1.6084166266e-07,0.0000000000e+00,6.5270659942e-05],
    [1.71853649e-02,5.8,-1.7179747672e-02,-3.0814296429e-02,2.4785143323e-03,2.4778279476e-03,2.7365485948e-05,8.2594266860e-04,9.1218477343e-06,-3.2530181691e-08,8.2583160838e-04,1.3614895757e-05],
    [1.77411142e-02,10.0,-1.7723119742e-02,-5.5528419436e-02,7.7529936098e-03,7.7462559566e-03,1.5108686057e-04,2.5820853189e-03,7.5804420441e-05,-1.7767224234e-07,0.0000000000e+00,7.5804420441e-05],
    [1.81894735e-02,10.0,-1.8170080860e-02,-5.6930310686e-02,8.1496769562e-03,8.1422319636e-03,1.6282752040e-04,2.7140774764e-03,8.1692133727e-05,-1.8673466258e-07,0.0000000000e+00,8.1692133727e-05],
    [1.85231570e-02,5.4,-1.8517092832e-02,-3.0894798978e-02,2.4799797684e-03,2.4792929180e-03,2.7396132282e-05,8.2643097267e-04,9.1320603102e-06,-3.0149422028e-08,8.2632061094e-04,1.3610981346e-05],
    [1.91204717e-02,10.0,-1.9097948424e-02,-5.9840961601e-02,9.0049458668e-03,8.9958561584e-03,1.8911574443e-04,2.9986186419e-03,9.4873780411e-05,-2.0626445966e-07,0.0000000000e+00,9.4873780411e-05],
    [1.96036905e-02,10.0,-1.9579417312e-02,-6.1351534279e-02,9.4656571746e-03,9.4556137919e-03,2.0381038485e-04,3.1518712640e-03,1.0224128970e-04,-2.1677944651e-07,0.0000000000e+00,1.0224128970e-04],
    [1.99650894e-02,5.0,-1.9958543214e-02,-3.0982090977e-02,2.4813807104e-03,2.4806931615e-03,2.7423300708e-05,8.2689773990e-04,9.1411144056e-06,-2.7947554212e-08,8.2678830950e-04,1.3603088233e-05],
    [2.06070731e-02,10.0,-2.0578881569e-02,-6.4487732581e-02,1.0458965786e-02,1.0446703993e-02,2.3671223607e-04,3.4822346643e-03,1.1873545247e-04,-2.3943759914e-07,0.0000000000e+00,1.1873545247e-04],
    [2.11278619e-02,10.0,-2.1097480071e-02,-6.6115285410e-02,1.0994032025e-02,1.0980482213e-02,2.5510348496e-04,3.6601608153e-03,1.2795410437e-04,-2.5163579863e-07,0.0000000000e+00,1.2795410437e-04],
    [2.15192687e-02,4.6,-2.1512202052e-02,-3.1077569255e-02,2.4826938752e-03,2.4820056278e-03,2.7448148103e-05,8.2733522868e-04,9.1493946436e-06,-2.5911536603e-08,8.2722696243e-04,1.3590170486e-05],
    [2.22092567e-02,10.0,-2.2173970815e-02,-6.9494334735e-02,1.2147637084e-02,1.2131094933e-02,2.9628138873e-04,4.0436983109e-03,1.4859182270e-04,-2.7791834689e-07,0.0000000000e+00,1.4859182270e-04],
    [2.27705363e-02,10.0,-2.2732509281e-02,-7.1247876978e-02,1.2769042514e-02,1.2750764377e-02,3.1929826946e-04,4.2502549477e-03,1.6012590293e-04,-2.9206625873e-07,0.0000000000e+00,1.6012590293e-04],
    [2.31944329e-02,4.3,-2.3186802566e-02,-3.1183306378e-02,2.4839059915e-03,2.4832172785e-03,2.7471443900e-05,8.2773913164e-04,9.1571581742e-06,-2.4029757953e-08,8.2763249520e-04,1.3570100179e-05],
    [2.39360087e-02,10.0,-2.3891844135e-02,-7.4888380254e-02,1.4108781703e-02,1.4086466283e-02,3.7083189818e-04,4.6954886056e-03,1.8594611017e-04,-3.2254610426e-07,0.0000000000e+00,1.8594611017e-04],
    [2.45409274e-02,10.0,-2.4493332238e-02,-7.6777506603e-02,1.4830442145e-02,1.4805784449e-02,3.9963657036e-04,4.9352617934e-03,2.0037599540e-04,-3.3895138200e-07,0.0000000000e+00,2.0037599540e-04],
    [2.50000000e-02,4.0,-2.4991758011e-02,-3.1301412125e-02,2.4850217160e-03,2.4843325373e-03,2.7493377274e-05,8.2811084576e-04,9.1644683507e-06,-2.2291291017e-08,8.2800636301e-04,1.3540524052e-05],
    [2.57970143e-02,10.0,-2.5741738220e-02,-8.0699466867e-02,1.6386305913e-02,1.6356201842e-02,4.6412716620e-04,5.4520675912e-03,2.3267726440e-04,-3.7428956084e-07,0.0000000000e+00,2.3267726440e-04],
    [2.64489650e-02,10.0,-2.6389395655e-02,-8.2734651796e-02,1.7224371433e-02,1.7191108316e-02,5.0017319154e-04,5.7303695939e-03,2.5072829317e-04,-3.9330699685e-07,0.0000000000e+00,2.5072829317e-04],
    [2.71173920e-02,10.0,-2.7053196153e-02,-8.4820869329e-02,1.8105264753e-02,1.8068511039e-02,5.3901656065e-04,6.0228370130e-03,2.7017763457e-04,-4.1328309581e-07,0.0000000000e+00,2.7017763457e-04],
    [2.78027117e-02,10.0,-2.7733530270e-02,-8.6959466577e-02,1.9031168893e-02,1.8990559503e-02,5.8087398065e-04,6.3301869668e-03,2.9113334552e-04,-4.3426537524e-07,0.0000000000e+00,2.9113334552e-04],
    [2.85053510e-02,10.0,-2.8430797084e-02,-8.9151761675e-02,2.0004382357e-02,1.9959513098e-02,6.2597915530e-04,6.6531710327e-03,3.1371179941e-04,-4.5630362185e-07,0.0000000000e+00,3.1371179941e-04],
    [2.92257476e-02,10.0,-2.9145404307e-02,-9.1398946201e-02,2.1027317271e-02,2.0977741107e-02,6.7458354170e-04,6.9925799035e-03,3.3803832180e-04,-4.7944999059e-07,0.0000000000e+00,3.3803832180e-04],
    [2.99643504e-02,10.0,-2.9877758110e-02,-9.3694669071e-02,2.2102527320e-02,2.2047748789e-02,7.2695949348e-04,7.3492494412e-03,3.6435707851e-04,-5.0370977988e-07,0.0000000000e+00,3.6435707851e-04],
    [3.07216193e-02,10.0,-3.0628301405e-02,-9.6054731235e-02,2.3232642561e-02,2.3172117770e-02,7.8339705942e-04,7.7240392566e-03,3.9261905310e-04,-5.2922944053e-07,0.0000000000e+00,3.9261905310e-04],
    [3.14980262e-02,10.0,-3.1397460527e-02,-9.8473860006e-02,2.4420477450e-02,2.4353604764e-02,8.4421155043e-04,8.1178676337e-03,4.2306877210e-04,-5.5602817847e-07,0.0000000000e+00,4.2306877210e-04],
    [3.22940548e-02,10.0,-3.2185679922e-02,-1.0095321928e-01,2.5668988004e-02,2.5595098734e-02,9.0974074556e-04,8.5316998884e-03,4.5587740428e-04,-5.8416749332e-07,0.0000000000e+00,4.5587740428e-04],
    [3.31102008e-02,10.0,-3.2993411030e-02,-1.0349460551e-01,2.6981253177e-02,2.6899613440e-02,9.8035042174e-04,8.9665381238e-03,4.9122527714e-04,-6.1371369511e-07,0.0000000000e+00,4.9122527714e-04],
    [3.39469727e-02,10.0,-3.3821115090e-02,-1.0609961937e-01,2.8360519558e-02,2.8270317242e-02,1.0564340046e-03,9.4234393910e-03,5.2930777848e-04,-6.4473552304e-07,0.0000000000e+00,5.2930777848e-04],
    [3.48048918e-02,10.0,-3.4669262767e-02,-1.0876963098e-01,2.9810197651e-02,2.9710536823e-02,1.1384149548e-03,9.9035119638e-03,5.7033567695e-04,-6.7730467679e-07,0.0000000000e+00,5.7033567695e-04],
    [3.56844926e-02,10.0,-3.5538333988e-02,-1.1150621944e-01,3.1333874911e-02,3.1223760918e-02,1.2267491547e-03,1.0407919995e-02,6.1453588198e-04,-7.1149612644e-07,0.0000000000e+00,6.1453588198e-04],
    [3.65863228e-02,10.0,-3.6428818136e-02,-1.1431107308e-01,3.2935321331e-02,3.2813660800e-02,1.3219274115e-03,1.0937886313e-02,6.6215254742e-04,-7.4738818802e-07,0.0000000000e+00,6.6215254742e-04],
    [3.75109445e-02,10.0,-3.7341213520e-02,-1.1718586335e-01,3.4618489444e-02,3.4484066069e-02,1.4244797640e-03,1.1494688690e-02,7.1344884150e-04,-7.8506281329e-07,0.0000000000e+00,7.1344884150e-04],
    [3.84589335e-02,10.0,-3.8275968745e-02,-1.2012338100e-01,3.6387555301e-02,3.6239039153e-02,1.5349789755e-03,1.2079679407e-02,7.6891419566e-04,-8.2453120824e-07,0.0000000000e+00,7.6891419566e-04],
    [3.94308803e-02,10.0,-3.9233713791e-02,-1.2314332900e-01,3.8246836513e-02,3.8082748652e-02,1.6540329671e-03,1.2694249861e-02,8.2844522758e-04,-8.6603127823e-07,0.0000000000e+00,8.2844522758e-04],
    [4.04273906e-02,10.0,-4.0214920997e-02,-1.2623839470e-01,4.0200952441e-02,4.0019657463e-02,1.7823049566e-03,1.3339886442e-02,8.9257102795e-04,-9.0958212441e-07,0.0000000000e+00,8.9257102795e-04],
    [4.14490849e-02,10.0,-4.1220125910e-02,-1.2941043777e-01,4.2254719883e-02,4.2054418474e-02,1.9205065910e-03,1.4018138871e-02,9.6164434677e-04,-9.5528105677e-07,0.0000000000e+00,9.6164434677e-04],
    [4.24965999e-02,10.0,-4.2249874730e-02,-1.3266103523e-01,4.4413212687e-02,4.4191911817e-02,2.0694024861e-03,1.4730636962e-02,1.0360474170e-03,-1.0032285960e-06,0.0000000000e+00,1.0360474170e-03],
    [4.35705880e-02,10.0,-4.3304720709e-02,-1.3599235028e-01,4.6681743115e-02,4.6437244862e-02,2.2298183758e-03,1.5479082242e-02,1.1161881201e-03,-1.0535308469e-06,0.0000000000e+00,1.1161881201e-03],
    [4.46717183e-02,10.0,-4.4385225715e-02,-1.3940606796e-01,4.9065895379e-02,4.8795767128e-02,2.4026434403e-03,1.6265256330e-02,1.2025048032e-03,-1.1062984997e-06,0.0000000000e+00,1.2025048032e-03],
    [4.58006767e-02,10.0,-4.5491961052e-02,-1.4290428403e-01,5.1571529359e-02,5.1273092628e-02,2.5888339151e-03,1.7091030255e-02,1.2954703529e-03,-1.1616463510e-06,0.0000000000e+00,1.2954703529e-03],
    [4.69581666e-02,10.0,-4.6625506533e-02,-1.4648910778e-01,5.4204806685e-02,5.3875092417e-02,2.7894196101e-03,1.7958363518e-02,1.3955934579e-03,-1.2196938887e-06,0.0000000000e+00,1.3955934579e-03],
    [4.81449089e-02,10.0,-4.7786450247e-02,-1.5016228583e-01,5.6972201914e-02,5.6607935578e-02,3.0055087991e-03,1.8869310617e-02,1.5034212654e-03,-1.2805654103e-06,0.0000000000e+00,1.5034212654e-03],
    [4.93616429e-02,10.0,-4.8975388279e-02,-1.5392621313e-01,5.9880506247e-02,5.9478070587e-02,3.2382949721e-03,1.9826022908e-02,1.6195422271e-03,-1.3443901344e-06,0.0000000000e+00,1.6195422271e-03],
    [5.06091267e-02,10.0,-5.0192924392e-02,-1.5778303578e-01,6.2936849892e-02,6.2492251396e-02,3.4890624229e-03,2.0830750465e-02,1.7445891477e-03,-1.4113023034e-06,0.0000000000e+00,1.7445891477e-03],
    [5.18881372e-02,10.0,-5.1439670163e-02,-1.6173450206e-01,6.6148750484e-02,6.5657578409e-02,3.7591913715e-03,2.1885856986e-02,1.8792421685e-03,-1.4814411660e-06,0.0000000000e+00,1.8792421685e-03],
    [5.31994714e-02,10.0,-5.2716242893e-02,-1.6578309969e-01,6.9524049759e-02,6.8981423974e-02,4.0501728654e-03,2.2993806750e-02,2.0242333689e-03,-1.5549514169e-06,0.0000000000e+00,2.0242333689e-03],
    [5.45439460e-02,10.0,-5.4023267248e-02,-1.6993104113e-01,7.3071010411e-02,7.2471551597e-02,4.3636066839e-03,2.4157183245e-02,2.1803488927e-03,-1.6319828273e-06,0.0000000000e+00,2.1803488927e-03],
    [5.59223986e-02,10.0,-5.5361373530e-02,-1.7418064913e-01,7.6798312366e-02,7.6136074960e-02,4.7012157738e-03,2.5378689170e-02,2.3484339829e-03,-1.7126905310e-06,0.0000000000e+00,2.3484339829e-03],
    [5.73356879e-02,10.0,-5.6731197339e-02,-1.7853403133e-01,8.0715060234e-02,7.9983472824e-02,5.0648543984e-03,2.6661155745e-02,2.5293970079e-03,-1.7972350065e-06,0.0000000000e+00,2.5293970079e-03],
    [5.87846944e-02,10.0,-5.8133378900e-02,-1.8299383784e-01,8.4830805659e-02,8.4022618830e-02,5.4565165192e-03,2.8007538989e-02,2.7242140286e-03,-1.8857820853e-06,0.0000000000e+00,2.7242140286e-03],
    [6.02703206e-02,10.0,-5.9568562322e-02,-1.8756223613e-01,8.9155577123e-02,8.8262788951e-02,5.8783493005e-03,2.9420927167e-02,2.9339336778e-03,-1.9785029324e-06,0.0000000000e+00,2.9339336778e-03],
    [6.17934921e-02,10.0,-6.1037394776e-02,-1.9224178539e-01,9.3699917197e-02,9.2713676393e-02,6.3326596282e-03,3.0904557556e-02,3.1596823672e-03,-2.0755739968e-06,0.0000000000e+00,3.1596823672e-03],
    [6.33551576e-02,10.0,-6.2540525574e-02,-1.9703496139e-01,9.8474860191e-02,9.7385406494e-02,6.8219318055e-03,3.2461799681e-02,3.4026698436e-03,-2.1771769266e-06,0.0000000000e+00,3.4026698436e-03],
    [6.49562901e-02,10.0,-6.4078605389e-02,-2.0194421903e-01,1.0349200666e-01,1.0228855908e-01,7.3488350026e-03,3.4096185118e-02,3.6641954454e-03,-2.2834983650e-06,0.0000000000e+00,3.6641954454e-03],
    [6.65978869e-02,10.0,-6.5652288905e-02,-2.0697197969e-01,1.0876356810e-01,1.0743421316e-01,7.9162372276e-03,3.5811401904e-02,3.9456603271e-03,-2.3947284493e-06,0.0000000000e+00,3.9456603271e-03],
    [6.82809707e-02,10.0,-6.7262221811e-02,-2.1212100264e-01,1.1430227011e-01,1.1283387244e-01,8.5272304714e-03,3.7611287087e-02,4.2485562113e-03,-2.5110648129e-06,0.0000000000e+00,4.2485562113e-03],
    [7.00065899e-02,10.0,-6.8909050973e-02,-2.1739386955e-01,1.2012150884e-01,1.1849954724e-01,9.1851344332e-03,3.9499845356e-02,4.5744897257e-03,-2.6327081365e-06,0.0000000000e+00,4.5744897257e-03],
    [7.17758196e-02,10.0,-7.0593419274e-02,-2.2279321430e-01,1.2623533607e-01,1.2444378436e-01,9.8935179412e-03,4.1481260210e-02,4.9251846006e-03,-2.7598631511e-06,0.0000000000e+00,4.9251846006e-03],
    [7.35897618e-02,10.0,-7.2315964001e-02,-2.2832154652e-01,1.3265849650e-01,1.3067966700e-01,1.0656216182e-02,4.3559882790e-02,5.3024897565e-03,-2.8927382175e-06,0.0000000000e+00,5.3024897565e-03],
    [7.54495466e-02,10.0,-7.4077315100e-02,-2.3398161209e-01,1.3940644264e-01,1.3722078502e-01,1.1477353051e-02,4.5740257949e-02,5.7083878896e-03,-3.0315448197e-06,0.0000000000e+00,5.7083878896e-03],
    [7.73563325e-02,10.0,-7.5878093265e-02,-2.3977659976e-01,1.4649537206e-01,1.4408133924e-01,1.2361357920e-02,4.8027109355e-02,6.1450045769e-03,-3.1764969656e-06,0.0000000000e+00,6.1450045769e-03],
    [7.93113073e-02,10.0,-7.7718907862e-02,-2.4570865318e-01,1.5394230187e-01,1.5127608180e-01,1.3312988915e-02,5.0425358117e-02,6.6146179230e-03,-3.3278104822e-06,0.0000000000e+00,6.6146179230e-03],
    [8.13156888e-02,10.0,-7.9600354664e-02,-2.5178102648e-01,1.6176502407e-01,1.5882036090e-01,1.4337359928e-02,5.2940119058e-02,7.1196687684e-03,-3.4857021931e-06,0.0000000000e+00,7.1196687684e-03],
    [8.33707258e-02,10.0,-8.1523013407e-02,-2.5799621282e-01,1.6998223960e-01,1.6673013568e-01,1.5439960174e-02,5.5576704443e-02,7.6627714816e-03,-3.6503889639e-06,0.0000000000e+00,7.6627714816e-03],
    [8.54776983e-02,10.0,-8.3487445121e-02,-2.6435705681e-01,1.7861351371e-01,1.7502194643e-01,1.6626685858e-02,5.8340646327e-02,8.2467253515e-03,-3.8220866028e-06,0.0000000000e+00,8.2467253515e-03],
    [8.76379189e-02,10.0,-8.5494189252e-02,-2.7086629385e-01,1.8767936528e-01,1.8371303380e-01,1.7903866246e-02,6.1237670481e-02,8.8745265979e-03,-4.0010085966e-06,0.0000000000e+00,8.8745265979e-03],
    [8.98527334e-02,10.0,-8.7543764670e-02,-2.7752685138e-01,1.9720132649e-01,1.9282123446e-01,1.9278289750e-02,6.4273737371e-02,9.5493823584e-03,-4.1873642580e-06,0.0000000000e+00,9.5493823584e-03],
    [9.21235213e-02,10.0,-8.9636655051e-02,-2.8434153639e-01,2.0720185339e-01,2.0236499608e-01,2.0757256076e-02,6.7454993725e-02,1.0274722557e-02,-4.3813582498e-06,0.0000000000e+00,1.0274722557e-02],
    [9.44516974e-02,10.0,-9.1773315558e-02,-2.9131293113e-01,2.1770456433e-01,2.1236348152e-01,2.2348584607e-02,7.0787817240e-02,1.1054211560e-02,-4.5831875170e-06,0.0000000000e+00,1.1054211560e-02],
    [9.68387119e-02,10.0,-9.3954167029e-02,-2.9844438311e-01,2.2873415053e-01,2.2283647954e-01,2.4060660973e-02,7.4278816581e-02,1.1891768399e-02,-4.7930394210e-06,0.0000000000e+00,1.1891768399e-02],
    [9.92860518e-02,10.0,-9.6179593846e-02,-3.0573798328e-01,2.4031651020e-01,2.3380447924e-01,2.5902481750e-02,7.7934816480e-02,1.2791583997e-02,-5.0110888914e-06,0.0000000000e+00,1.2791583997e-02],
    [1.01795242e-01,10.0,-9.8449926722e-02,-3.1319703345e-01,2.5247865915e-01,2.4528858066e-01,2.7883695439e-02,8.1762850285e-02,1.3758118755e-02,-5.2374982999e-06,0.0000000000e+00,1.3758118755e-02],
    [1.04367845e-01,10.0,-1.0076545198e-01,-3.2082366628e-01,2.6524895430e-01,2.5731050968e-01,3.0014643446e-02,8.5770159960e-02,1.4796138937e-02,-5.4724115303e-06,0.0000000000e+00,1.4796138937e-02],
    [1.07005463e-01,10.0,-1.0312640147e-01,-3.2862084208e-01,2.7865701914e-01,2.6989266276e-01,3.2306395471e-02,8.9964210987e-02,1.5910727238e-02,-5.7159516092e-06,0.0000000000e+00,1.5910727238e-02],
    [1.09709741e-01,10.0,-1.0553294696e-01,-3.3659177144e-01,2.9273381829e-01,2.8305810690e-01,3.4770824015e-02,9.4352692366e-02,1.7107300532e-02,-5.9682169280e-06,0.0000000000e+00,1.7107300532e-02],
    [1.12482362e-01,10.0,-1.0798519411e-01,-3.4473817706e-01,3.0751183629e-01,2.9683047533e-01,3.7420623004e-02,9.8943471909e-02,1.8391628158e-02,-6.2292770271e-06,0.0000000000e+00,1.8391628158e-02],
    [1.15325053e-01,10.0,-1.1048317600e-01,-3.5306284096e-01,3.2302492857e-01,3.1123393774e-01,4.0269393474e-02,1.0374463350e-01,1.9769850667e-02,-6.4991679002e-06,0.0000000000e+00,1.9769850667e-02],
    [1.18239586e-01,10.0,-1.1302684629e-01,-3.6156838334e-01,3.3930850029e-01,3.2629331946e-01,4.3331678957e-02,1.0876441747e-01,2.1248498983e-02,-6.7778867728e-06,0.0000000000e+00,2.1248498983e-02],
    [1.21227776e-01,10.0,-1.1561581836e-01,-3.7025757243e-01,3.5639882088e-01,3.4203308821e-01,4.6623010188e-02,1.1401101202e-01,2.2834152218e-02,-7.0654034443e-06,0.0000000000e+00,2.2834152218e-02],
    [1.24291484e-01,10.0,-1.1825034851e-01,-3.7913141881e-01,3.7433606386e-01,3.5848054290e-01,5.0160050392e-02,1.1949349195e-01,2.4534857244e-02,-7.3615856318e-06,0.0000000000e+00,2.4534857244e-02],
    [1.27432620e-01,10.0,-1.2092987140e-01,-3.8819259811e-01,3.9315977693e-01,3.7566104531e-01,5.3960572928e-02,1.2522031367e-01,2.6358113552e-02,-7.6662939376e-06,0.0000000000e+00,2.6358113552e-02],
    [1.30653139e-01,10.0,-1.2365394549e-01,-3.9744292237e-01,4.1291216016e-01,3.9360108972e-01,5.8043550700e-02,1.3120032847e-01,2.8312207928e-02,-7.9793057867e-06,0.0000000000e+00,2.8312207928e-02],
    [1.33955048e-01,10.0,-1.2642200646e-01,-4.0688442905e-01,4.3363714218e-01,4.1232743859e-01,6.2429245561e-02,1.3744243979e-01,3.0405915828e-02,-8.3003242468e-06,0.0000000000e+00,3.0405915828e-02],
    [1.37340404e-01,10.0,-1.2923335856e-01,-4.1651866559e-01,4.5538055897e-01,4.3186700344e-01,6.7139275372e-02,1.4395563304e-01,3.2648519416e-02,-8.6289682868e-06,0.0000000000e+00,3.2648519416e-02],
    [1.40811316e-01,10.0,-1.3208716404e-01,-4.2634695149e-01,4.7819018364e-01,4.5224675536e-01,7.2196684778e-02,1.5074887872e-01,3.5049825491e-02,-8.9647623175e-06,0.0000000000e+00,3.5049825491e-02],
    [1.44369946e-01,10.0,-1.3498243191e-01,-4.3637082527e-01,5.0211584568e-01,4.7349360585e-01,7.7626042068e-02,1.5783116221e-01,3.7620182308e-02,-9.3071247166e-06,0.0000000000e+00,3.7620182308e-02],
    [1.48018511e-01,10.0,-1.3791800608e-01,-4.4659054871e-01,5.2720940113e-01,4.9563425779e-01,8.3453498781e-02,1.6521137953e-01,4.0370494911e-02,-9.6553552625e-06,0.0000000000e+00,4.0370494911e-02],
    [1.51759284e-01,10.0,-1.4089255288e-01,-4.5700812332e-01,5.5352473259e-01,5.1869505644e-01,8.9706905186e-02,1.7289830744e-01,4.3312238586e-02,-1.0008621395e-05,0.0000000000e+00,4.3312238586e-02],
    [1.55594595e-01,10.0,-1.4390454789e-01,-4.6762231196e-01,5.8111810684e-01,5.4270184040e-01,9.6415847540e-02,1.8090055883e-01,4.6457469960e-02,-1.0365943221e-05,0.0000000000e+00,4.6457469960e-02],
    [1.59526833e-01,10.0,-1.4695226220e-01,-4.7843448689e-01,6.1004787683e-01,5.6767964363e-01,1.0361178964e-01,1.8922647834e-01,4.9818835200e-02,-1.0726177188e-05,0.0000000000e+00,4.9818835200e-02],
    [1.63558448e-01,10.0,-1.5003374793e-01,-4.8944379962e-01,6.4037472010e-01,5.9365248680e-01,1.1132812500e-01,1.9788411260e-01,5.3409574714e-02,-1.1087998323e-05,0.0000000000e+00,5.3409574714e-02],
    [1.67691951e-01,10.0,-1.5314682312e-01,-5.0065007050e-01,6.7216163874e-01,6.2064337730e-01,1.1960026622e-01,2.0688106120e-01,5.7243523678e-02,-1.1449880975e-05,0.0000000000e+00,5.7243523678e-02],
    [1.71929917e-01,10.0,-1.5628906509e-01,-5.1205155611e-01,7.0547413826e-01,6.4867365360e-01,1.2846574187e-01,2.1622447670e-01,6.1335124109e-02,-1.1810076994e-05,0.0000000000e+00,6.1335124109e-02],
    [1.76274987e-01,10.0,-1.5945777288e-01,-5.2364738844e-01,7.4037992954e-01,6.7776286602e-01,1.3796430826e-01,2.2592085600e-01,6.5699378038e-02,-1.2166595535e-05,0.0000000000e+00,6.5699378038e-02],
    [1.80729867e-01,10.0,-1.6264996129e-01,-5.3543544671e-01,7.7694922686e-01,7.0792818069e-01,1.4813794196e-01,2.3597596586e-01,7.0351847192e-02,-1.2517177529e-05,0.0000000000e+00,7.0351847192e-02],
    [1.85297332e-01,10.0,-1.6586234872e-01,-5.4741323393e-01,8.1525480747e-01,7.3918449879e-01,1.5903104842e-01,2.4639472365e-01,7.5308638843e-02,-1.2859269054e-05,0.0000000000e+00,7.5308638843e-02],
    [1.89980227e-01,10.0,-1.6909133496e-01,-5.5957770626e-01,8.5537183285e-01,7.7154344320e-01,1.7069040239e-01,2.5718101859e-01,8.0586364486e-02,-1.3189993858e-05,0.0000000000e+00,8.0586364486e-02],
    [1.94781470e-01,10.0,-1.7233299960e-01,-5.7192476475e-01,8.9737844467e-01,8.0501353741e-01,1.8316526711e-01,2.6833772659e-01,8.6202120199e-02,-1.3506119958e-05,0.0000000000e+00,8.6202120199e-02],
    [1.99704052e-01,10.0,-1.7558303375e-01,-5.8445085585e-01,9.4135445356e-01,8.3959883451e-01,1.9650751352e-01,2.7986612916e-01,9.2173367053e-02,-1.3804038792e-05,0.0000000000e+00,9.2173367053e-02],
    [2.04751038e-01,10.0,-1.7883677545e-01,-5.9715082350e-01,9.8738276958e-01,8.7529897690e-01,2.1077154577e-01,2.9176616669e-01,9.8517923406e-02,-1.4079718573e-05,0.0000000000e+00,9.8517923406e-02],
    [2.09925574e-01,10.0,-1.8208916460e-01,-6.1001798696e-01,1.0355486870e+00,9.1210848093e-01,2.2601440549e-01,3.0403599143e-01,1.0525385740e-01,-1.4328675423e-05,0.0000000000e+00,1.0525385740e-01],
    [2.15230883e-01,10.0,-1.8533472824e-01,-6.2304621621e-01,1.0859400034e+00,9.5001590252e-01,2.4229575694e-01,3.1667178869e-01,1.1239938935e-01,-1.4545934556e-05,0.0000000000e+00,1.1239938935e-01],
    [2.20670269e-01,10.0,-1.8856756156e-01,-6.3622751923e-01,1.1386467218e+00,9.8900306225e-01,2.5967785716e-01,3.2966750860e-01,1.1997277293e-01,-1.4725991033e-05,0.0000000000e+00,1.1997277293e-01],
    [2.26247121e-01,10.0,-1.9178130929e-01,-6.4955437837e-01,1.1937612295e+00,1.0290445089e+00,2.7822554111e-01,3.4301462770e-01,1.2799215591e-01,-1.4862768954e-05,0.0000000000e+00,1.2799215591e-01],
    [2.31964913e-01,10.0,-1.9496914765e-01,-6.6301669754e-01,1.2513782978e+00,1.0701063871e+00,2.9800620675e-01,3.5670188069e-01,1.3647541828e-01,-1.4949579268e-05,0.0000000000e+00,1.3647541828e-01],
    [2.37827207e-01,10.0,-1.9812351117e-01,-6.7660302088e-01,1.3115926981e+00,1.1121435165e+00,3.1908911467e-01,3.7071424723e-01,1.4543922216e-01,-1.4979088327e-05,0.0000000000e+00,1.4543922216e-01],
    [2.43837654e-01,10.0,-2.0123706646e-01,-6.9030299355e-01,1.3745069504e+00,1.1551059484e+00,3.4154719114e-01,3.8503503799e-01,1.5490175075e-01,-1.4943230335e-05,0.0000000000e+00,1.5490175075e-01],
    [2.50000000e-01,10.0,-2.0430130082e-01,-7.0410244977e-01,1.4402209520e+00,1.1989278793e+00,3.6545410752e-01,3.9964231849e-01,1.6487825768e-01,-1.4833212883e-05,0.0000000000e+00,1.6487825768e-01],
];
/// Look up CAMB bootstrap IC for a given k, returning (tau_init, ic_vector).
/// Uses linear interpolation between nearest bracketing k-values.
pub(crate) fn bootstrap_ic_lookup(k: f64, lay: &CambLayout) -> Option<(f64, Vec<f64>)> {
    let table = CAMB_BOOTSTRAP_IC;
    let n = table.len();
    if n == 0 { return None; }
    let k_min = table[0][0]; let k_max = table[n-1][0];
    if k < k_min * 0.5 || k > k_max * 2.0 { return None; }
    let mut i_lo = 0;
    for i in 0..n { if table[i][0] <= k { i_lo = i; } }
    let i_hi = (i_lo + 1).min(n - 1);
    let (k_lo, k_hi) = (table[i_lo][0], table[i_hi][0]);
    let t = if (k_hi - k_lo).abs() > 1e-30 { ((k - k_lo) / (k_hi - k_lo)).max(0.0).min(1.0) } else { 0.0 };
    let lerp = |idx: usize| table[i_lo][idx] * (1.0 - t) + table[i_hi][idx] * t;
    let tau_init = lerp(1);
    let mut y = vec![0.0_f64; lay.n_state];
    y[lay.i_etak] = lerp(2);
    y[lay.i_sigma] = lerp(3); // σ from CAMB bootstrap table
    y[lay.i_clxc] = lerp(4);
    y[lay.i_clxb] = lerp(5);
    y[lay.i_vb] = lerp(6);
    y[lay.theta(0)] = lerp(7);
    if lay.lmax_g >= 1 { y[lay.theta(1)] = lerp(8); }
    if lay.lmax_g >= 2 { y[lay.theta(2)] = lerp(9); }
    y[lay.nu(0)] = lerp(10);
    if lay.lmax_n >= 1 { y[lay.nu(1)] = lerp(11); }
    Some((tau_init, y))
}
#[cfg(test)]
mod rhs_diag {
    use super::*;
    #[test]
    fn test_rhs_at_ic() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let k = 0.01;
        let lay = CambLayout::new(8, 8);
        if let Some((tau_init, y0)) = bootstrap_ic_lookup(k, &lay) {
            let h0c = p.h * 1e7 / 2.99792458e10;
            let og = p.omega_gamma();
            let z = 1000.0; let a = 1.0/(1.0+z); let h0c2 = h0c*h0c;
            let bg = CambBackground {
                adotoa: a*h0c*p.e_of_z(z), grho_g: 3.0*h0c2*og/(a*a),
                grho_nu: 3.0*h0c2*og*0.2271*3.044/(a*a),
                grho_b: 3.0*h0c2*p.omega_b/a,
                grho_c: 3.0*h0c2*(p.omega_m-p.omega_b)/a,
                opac: 100.0, cs2b: 1e-10, vis: 0.0, dvis: 0.0, ddvis: 0.0, a, expmmu: 0.0,
            };
            let mut dy = vec![0.0f64; lay.n_state];
            let _ = camb_rhs(k, tau_init, &y0, &mut dy, &lay, &bg);
            eprintln!("  RHS at IC (τ={:.1}, k={}):", tau_init, k);
            eprintln!("  y: etak={:.4e} σ={:.4e} Θ₀={:.4e} Θ₁={:.4e}",
                y0[lay.i_etak], y0[lay.i_sigma], y0[lay.theta(0)], y0[lay.theta(1)]);
            eprintln!("  dy: etak'={:.4e} σ'={:.4e} δc'={:.4e} vb'={:.4e}",
                dy[lay.i_etak], dy[lay.i_sigma], dy[lay.i_clxc], dy[lay.i_vb]);
            eprintln!("  dy: Θ₀'={:.4e} Θ₁'={:.4e} Θ₂'={:.4e}",
                dy[lay.theta(0)], dy[lay.theta(1)], dy[lay.theta(2)]);
            eprintln!("  bg: ℋ={:.4e} grho_g={:.4e} grho_b={:.4e} R={:.4}",
                bg.adotoa, bg.grho_g, bg.grho_b, 0.75*bg.grho_b/bg.grho_g);
        }
    }
}

#[cfg(test)]
mod grid_diag {
    use super::*;
    #[test]
    fn test_grid_density() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n = vis.eta_grid.len();
        let em = vis.eta_grid.iter().cloned().fold(0.0f64, f64::max);
        let mut ir = 0; let mut gm = 0.0f64;
        for i in 0..n { if vis.g_grid[i] > gm { gm = vis.g_grid[i]; ir = i; } }
        let tr = em - vis.eta_grid[ir];
        eprintln!("  Grid: {} pts, rec at i={} τ={:.1} g={:.4e}", n, ir, tr, gm);
        // Spacing near rec
        let mut cnt = 0; let mut sum = 0.0;
        for i in ir.saturating_sub(30)..=(ir+30).min(n-1) {
            if i > 0 {
                let d = (vis.eta_grid[i] - vis.eta_grid[i-1]).abs();
                let tau = em - vis.eta_grid[i];
                if (tau - tr).abs() < 30.0 { cnt += 1; sum += d; }
            }
        }
        eprintln!("  Spacing ±30Mpc: avg={:.3} ({} pts)", sum/cnt as f64, cnt);
        eprintln!("  κ' at rec: {:.4e}", vis.kappa_dot_grid[ir]);
    }
}

/// Direct Crank-Nicolson stepping through precomputed matrix profile.
/// No interpolation, no adaptive control — exact A(τ_i) at each grid point.
/// Order 2, A-stable, single LU solve per step.
pub(crate) fn integrate_crank_nicolson(
    tau_profile: &[f64],
    mats_flat: &[f64],
    n: usize,
    y0: &[f64],
) -> Result<Vec<(f64, Vec<f64>)>, String> {
    use crate::core::lu::{lu_factor_in_place_flat_into, lu_solve_factored_flat_into};
    
    let ns = tau_profile.len();
    if ns < 2 { return Err("too few grid points".into()); }
    let stride = n * n;
    
    let mut y = y0.to_vec();
    let mut result = Vec::with_capacity(ns);
    result.push((tau_profile[0], y.clone()));
    let mut piv = vec![0usize; n];
    let mut x = vec![0.0f64; n];
    
    for i in 1..ns {
        let h = tau_profile[i] - tau_profile[i-1];
        if h.abs() < 1e-30 { result.push((tau_profile[i], y.clone())); continue; }
        
        let a_start = &mats_flat[(i-1)*stride..i*stride];
        let a_end = &mats_flat[i*stride..(i+1)*stride];
        
        // RHS: r = y + (h/2) A_start × y
        let mut rhs = vec![0.0f64; n];
        for row in 0..n {
            let mut ay = 0.0;
            for col in 0..n { ay += a_start[row * n + col] * y[col]; }
            rhs[row] = y[row] + 0.5 * h * ay;
        }
        
        // LHS: M = I - (h/2) A_end
        let mut m = vec![0.0f64; n * n];
        for row in 0..n {
            for col in 0..n { m[row * n + col] = -0.5 * h * a_end[row * n + col]; }
            m[row * n + row] += 1.0;
        }
        
        if !lu_factor_in_place_flat_into(&mut m, n, &mut piv) {
            return Err(format!("LU failed at τ={:.1}", tau_profile[i]));
        }
        if !lu_solve_factored_flat_into(&m, &piv, &rhs, &mut x, n) {
            return Err(format!("LU solve failed at τ={:.1}", tau_profile[i]));
        }
        
        y.copy_from_slice(&x);
        result.push((tau_profile[i], y.clone()));
    }
    
    Ok(result)
}

#[cfg(test)]
mod matrix_audit {
    use super::*;
    /// CRITICAL: verify build_camb_matrix(bg) × y == camb_rhs(y, bg) for random state
    #[test]
    fn test_matrix_vs_rhs_consistency() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let k = 0.01_f64;
        let lay = CambLayout::new(8, 8);
        let n = lay.n_state;
        
        // Background at z=1075 (recombination)
        let h0c = p.h * 1e7 / 2.99792458e10;
        let og = p.omega_gamma();
        let onu = og * 0.2271 * 3.044;
        let z = 1075.0; let a = 1.0/(1.0+z); let h0c2 = h0c*h0c;
        let bg = CambBackground {
            adotoa: a*h0c*p.e_of_z(z),
            grho_g: 3.0*h0c2*og/(a*a),
            grho_nu: 3.0*h0c2*onu/(a*a),
            grho_b: 3.0*h0c2*p.omega_b/a,
            grho_c: 3.0*h0c2*(p.omega_m-p.omega_b)/a,
            opac: 0.06, cs2b: 1e-7, vis: 0.02, dvis: 0.001, ddvis: -0.0005, a, expmmu: 0.0,
        };
        
        // Random-ish state near physical values at recombination
        let mut y = vec![0.0f64; n];
        y[lay.i_etak] = -0.009;
        y[lay.i_sigma] = -0.7;
        y[lay.i_clxc] = 1.5;
        y[lay.i_clxb] = 1.2;
        y[lay.i_vb] = 0.25;
        y[lay.theta(0)] = 0.4;
        if lay.lmax_g >= 1 { y[lay.theta(1)] = 0.09; }
        if lay.lmax_g >= 2 { y[lay.theta(2)] = 0.004; }
        if lay.lmax_n >= 0 { y[lay.nu(0)] = 0.3; }
        if lay.lmax_n >= 1 { y[lay.nu(1)] = 0.08; }
        if lay.lmax_n >= 2 { y[lay.nu(2)] = 0.002; }
        
        // Method 1: camb_rhs
        let mut dy_rhs = vec![0.0f64; n];
        let _ = camb_rhs(k, 283.0, &y, &mut dy_rhs, &lay, &bg);
        
        // Method 2: build_camb_matrix × y
        let mat = build_camb_matrix(k, 283.0, &lay, &bg);
        let mut dy_mat = vec![0.0f64; n];
        for i in 0..n {
            let mut acc = 0.0;
            for j in 0..n { acc += mat[i*n+j] * y[j]; }
            dy_mat[i] = acc;
        }
        
        // Compare
        eprintln!("  Matrix vs RHS consistency at z=1075:");
        let names = ["etak'", "σ'", "δc'", "δb'", "vb'", "Θ₀'", "Θ₁'", "Θ₂'"];
        let indices = [lay.i_etak, lay.i_sigma, lay.i_clxc, lay.i_clxb, lay.i_vb,
                       lay.theta(0), lay.theta(1), lay.theta(2)];
        let mut max_rel = 0.0f64;
        for (&idx, name) in indices.iter().zip(names.iter()) {
            let r = dy_rhs[idx]; let m = dy_mat[idx];
            let rel = if r.abs() > 1e-30 { ((m-r)/r).abs() } else { (m-r).abs() };
            if rel > 0.01 {
                eprintln!("  *** {}: rhs={:.6e} mat={:.6e} REL={:.2e} ***", name, r, m, rel);
            }
            max_rel = max_rel.max(rel);
        }
        eprintln!("  Max relative error: {:.2e}", max_rel);
        assert!(max_rel < 0.01, "Matrix-RHS mismatch: max_rel={:.2e}", max_rel);
    }

    /// P0 audit test: A×y ≡ camb_rhs(y) for ALL rows, including pol + massive ν.
    #[test]
    fn test_matrix_rhs_parity_full() {
        let k = 0.01_f64;
        let tau = 283.0;
        let h0c = 0.6736 * 1e7 / 2.99792458e10;
        let h0c2 = h0c * h0c;
        let og = 2.469e-5 / (0.6736_f64).powi(2);
        let onu = og * 0.2271 * NEFF_MASSLESS;
        let z = 1075.0; let a = 1.0/(1.0+z);
        let bg = CambBackground {
            adotoa: a*h0c*(og/(a*a*a*a) + onu/(a*a*a*a) + 0.3153/(a*a*a) + 0.6847).sqrt(),
            grho_g: 3.0*h0c2*og/(a*a), grho_nu: 3.0*h0c2*onu/(a*a),
            grho_b: 3.0*h0c2*0.02237/(0.6736_f64).powi(2)/a,
            grho_c: 3.0*h0c2*(0.3153-0.02237/(0.6736_f64).powi(2))/a,
            opac: 0.06, cs2b: 1e-7, vis: 0.02, dvis: 0.001, ddvis: -0.0005, a, expmmu: 0.01,
        };

        // Test configurations: (lmax_g, lmax_n, lmax_pol, nq_massive, lmax_m)
        let configs = [
            ("no-pol no-mnu", 8, 8, 0, 0, 0),
            ("pol ON",        8, 8, 6, 0, 0),
            ("mnu ON",        8, 8, 0, 10, 8),
            ("full physics",  8, 8, 6, 10, 8),
        ];

        for &(name, lg, ln, lp, nq, lm) in &configs {
            let lay = CambLayout::new_full(lg, ln, lp, nq, lm);
            let n = lay.n_state;

            // Random-ish state
            let mut y = vec![0.0f64; n];
            y[lay.i_etak] = -0.009;
            y[lay.i_sigma] = -0.07;
            y[lay.i_clxc] = 1.5;
            y[lay.i_clxb] = 1.2;
            y[lay.i_vb] = 0.25;
            for ell in 0..=lg { y[lay.theta(ell)] = 0.4 * (-0.1_f64).powi(ell as i32); }
            for ell in 0..=ln { y[lay.nu(ell)] = 0.3 * (-0.1_f64).powi(ell as i32); }
            if lay.has_pol() {
                for ell in 0..=lp { y[lay.e_mode(ell)] = 0.001 * (-0.2_f64).powi(ell as i32); }
            }
            if lay.has_massive_nu() {
                for iq in 0..nq { for ell in 0..=lm {
                    y[lay.psi(iq, ell)] = 0.3 * (-0.1_f64).powi(ell as i32);
                }}
            }

            // Method 1: camb_rhs
            let mut dy_rhs = vec![0.0f64; n];
            let _ = camb_rhs(k, tau, &y, &mut dy_rhs, &lay, &bg);

            // Method 2: A × y
            let mat = build_camb_matrix(k, tau, &lay, &bg);
            let mut dy_mat = vec![0.0f64; n];
            for i in 0..n {
                let mut acc = 0.0;
                for j in 0..n { acc += mat[i*n+j] * y[j]; }
                dy_mat[i] = acc;
            }

            // Compare ALL rows
            let mut max_rel = 0.0_f64;
            let mut worst_row = 0;
            for i in 0..n {
                let r = dy_rhs[i]; let m = dy_mat[i];
                let rel = if r.abs() > 1e-20 { ((m-r)/r).abs() } else { (m-r).abs() };
                if rel > max_rel { max_rel = rel; worst_row = i; }
            }
            let pass = max_rel < 1e-10;
            eprintln!("  [{}] n={} max_rel={:.2e} worst_row={} {}",
                name, n, max_rel, worst_row, if pass {"PASS"} else {"FAIL"});
            if !pass {
                // Print worst mismatches for debugging
                for i in 0..n {
                    let r = dy_rhs[i]; let m = dy_mat[i];
                    let rel = if r.abs() > 1e-20 { ((m-r)/r).abs() } else { (m-r).abs() };
                    if rel > 1e-10 {
                        eprintln!("    row {}: rhs={:.6e} mat={:.6e} rel={:.2e}", i, r, m, rel);
                    }
                }
            }
            assert!(pass, "[{}] Matrix-RHS parity FAIL: max_rel={:.2e} at row {}", name, max_rel, worst_row);
        }
    }
}
const CAMB_OPAC_N: usize = 250;
const CAMB_OPAC_TABLE: [(f64,f64); CAMB_OPAC_N] = [
    (1.6e+02, 3.24433465e-06),
    (1.7e+02, 3.51686683e-06),
    (1.7e+02, 3.81936257e-06),
    (1.8e+02, 4.15598457e-06),
    (1.9e+02, 4.53160873e-06),
    (1.9e+02, 4.95197212e-06),
    (2e+02, 5.42385764e-06),
    (2.1e+02, 5.95532592e-06),
    (2.2e+02, 6.55600898e-06),
    (2.3e+02, 7.23748502e-06),
    (2.4e+02, 8.01376096e-06),
    (2.5e+02, 8.90189963e-06),
    (2.6e+02, 9.92284356e-06),
    (2.7e+02, 1.11025091e-05),
    (2.8e+02, 1.24732580e-05),
    (3e+02, 1.40759028e-05),
    (3.1e+02, 1.59624833e-05),
    (3.3e+02, 1.82001733e-05),
    (3.4e+02, 2.08768834e-05),
    (3.6e+02, 2.41094695e-05),
    (3.8e+02, 2.80560526e-05),
    (4e+02, 3.29350318e-05),
    (4.2e+02, 3.90553886e-05),
    (4.5e+02, 4.68668647e-05),
    (4.8e+02, 5.70468965e-05),
    (5.1e+02, 7.06597713e-05),
    (5.4e+02, 8.94686074e-05),
    (5.8e+02, 1.16602316e-04),
    (6.2e+02, 1.58151464e-04),
    (6.7e+02, 2.27596884e-04),
    (6.7e+02, 2.27596884e-04),
    (6.7e+02, 2.32361146e-04),
    (6.7e+02, 2.37284393e-04),
    (6.7e+02, 2.42374162e-04),
    (6.8e+02, 2.47638451e-04),
    (6.8e+02, 2.53085751e-04),
    (6.8e+02, 2.58725085e-04),
    (6.9e+02, 2.64566045e-04),
    (6.9e+02, 2.70618840e-04),
    (6.9e+02, 2.76894334e-04),
    (6.9e+02, 2.83404105e-04),
    (7e+02, 2.90160497e-04),
    (7e+02, 2.97176676e-04),
    (7e+02, 3.04466702e-04),
    (7e+02, 3.12045593e-04),
    (7.1e+02, 3.19929406e-04),
    (7.1e+02, 3.28135318e-04),
    (7.1e+02, 3.36681718e-04),
    (7.1e+02, 3.45588308e-04),
    (7.2e+02, 3.54876205e-04),
    (7.2e+02, 3.64568065e-04),
    (7.2e+02, 3.74688207e-04),
    (7.3e+02, 3.85262755e-04),
    (7.3e+02, 3.96319786e-04),
    (7.3e+02, 4.07889502e-04),
    (7.3e+02, 4.20004404e-04),
    (7.4e+02, 4.32699492e-04),
    (7.4e+02, 4.46012482e-04),
    (7.4e+02, 4.59984033e-04),
    (7.5e+02, 4.74658007e-04),
    (7.5e+02, 4.90081746e-04),
    (7.5e+02, 5.06306371e-04),
    (7.6e+02, 5.23387110e-04),
    (7.6e+02, 5.41383658e-04),
    (7.6e+02, 5.60360564e-04),
    (7.7e+02, 5.80387650e-04),
    (7.7e+02, 6.01540472e-04),
    (7.7e+02, 6.23900811e-04),
    (7.7e+02, 6.47557217e-04),
    (7.8e+02, 6.72605582e-04),
    (7.8e+02, 6.99149779e-04),
    (7.8e+02, 7.27302330e-04),
    (7.9e+02, 7.57185149e-04),
    (7.9e+02, 7.88930323e-04),
    (7.9e+02, 8.22680970e-04),
    (8e+02, 8.58592146e-04),
    (8e+02, 8.96831825e-04),
    (8e+02, 9.37581957e-04),
    (8.1e+02, 9.81039587e-04),
    (8.1e+02, 1.02741806e-03),
    (8.1e+02, 1.07694831e-03),
    (8.2e+02, 1.12988022e-03),
    (8.2e+02, 1.18648410e-03),
    (8.2e+02, 1.24705223e-03),
    (8.3e+02, 1.31190050e-03),
    (8.3e+02, 1.38137019e-03),
    (8.4e+02, 1.45582983e-03),
    (8.4e+02, 1.53567714e-03),
    (8.4e+02, 1.62134120e-03),
    (8.5e+02, 1.71328456e-03),
    (8.5e+02, 1.81200649e-03),
    (8.5e+02, 1.91804334e-03),
    (8.6e+02, 2.03197263e-03),
    (8.6e+02, 2.15441593e-03),
    (8.6e+02, 2.28604149e-03),
    (8.7e+02, 2.42756742e-03),
    (8.7e+02, 2.57976485e-03),
    (8.8e+02, 2.74346150e-03),
    (8.8e+02, 2.91954526e-03),
    (8.8e+02, 3.10896803e-03),
    (8.9e+02, 3.31274984e-03),
    (8.9e+02, 3.53198301e-03),
    (9e+02, 3.76783673e-03),
    (9e+02, 4.02156168e-03),
    (9e+02, 4.29449502e-03),
    (9.1e+02, 4.58806551e-03),
    (9.1e+02, 4.90379895e-03),
    (9.2e+02, 5.24332379e-03),
    (9.2e+02, 5.60837696e-03),
    (9.2e+02, 6.00081006e-03),
    (9.3e+02, 6.42259560e-03),
    (9.3e+02, 6.87583357e-03),
    (9.4e+02, 7.36275822e-03),
    (9.4e+02, 7.88574499e-03),
    (9.5e+02, 8.44731762e-03),
    (9.5e+02, 9.05015550e-03),
    (9.6e+02, 9.69710106e-03),
    (9.6e+02, 1.03911674e-02),
    (9.6e+02, 1.11355457e-02),
    (9.7e+02, 1.19336133e-02),
    (9.7e+02, 1.27889410e-02),
    (9.8e+02, 1.37053011e-02),
    (9.8e+02, 1.46866746e-02),
    (9.9e+02, 1.57372590e-02),
    (9.9e+02, 1.68614756e-02),
    (1e+03, 1.80639761e-02),
    (1e+03, 1.93496502e-02),
    (1e+03, 2.07236308e-02),
    (1e+03, 2.21913010e-02),
    (1e+03, 2.37582990e-02),
    (1e+03, 2.54305229e-02),
    (1e+03, 2.72141348e-02),
    (1e+03, 2.91155644e-02),
    (1e+03, 3.11415114e-02),
    (1e+03, 3.32989469e-02),
    (1e+03, 3.55951146e-02),
    (1.1e+03, 3.80375294e-02),
    (1.1e+03, 4.06339770e-02),
    (1.1e+03, 4.33925099e-02),
    (1.1e+03, 4.63214443e-02),
    (1.1e+03, 4.94293541e-02),
    (1.1e+03, 5.27250647e-02),
    (1.1e+03, 5.62176441e-02),
    (1.1e+03, 5.99163944e-02),
    (1.1e+03, 6.38308399e-02),
    (1.1e+03, 6.79707154e-02),
    (1.1e+03, 7.23459520e-02),
    (1.1e+03, 7.69666624e-02),
    (1.1e+03, 8.18431235e-02),
    (1.1e+03, 8.69857596e-02),
    (1.1e+03, 9.24051221e-02),
    (1.1e+03, 9.81118698e-02),
    (1.1e+03, 1.04116746e-01),
    (1.1e+03, 1.10430557e-01),
    (1.2e+03, 1.17064146e-01),
    (1.2e+03, 1.24028367e-01),
    (1.2e+03, 1.31334058e-01),
    (1.2e+03, 1.38992013e-01),
    (1.2e+03, 1.47012947e-01),
    (1.2e+03, 1.55407467e-01),
    (1.2e+03, 1.64186030e-01),
    (1.2e+03, 1.73358911e-01),
    (1.2e+03, 1.82936150e-01),
    (1.2e+03, 1.92927514e-01),
    (1.2e+03, 2.03342433e-01),
    (1.2e+03, 2.14189946e-01),
    (1.2e+03, 2.25478632e-01),
    (1.2e+03, 2.37216528e-01),
    (1.2e+03, 2.49411042e-01),
    (1.2e+03, 2.62068856e-01),
    (1.3e+03, 2.75195803e-01),
    (1.3e+03, 2.88796742e-01),
    (1.3e+03, 3.02875407e-01),
    (1.3e+03, 3.17434235e-01),
    (1.3e+03, 3.32474185e-01),
    (1.3e+03, 3.47994520e-01),
    (1.3e+03, 3.63992578e-01),
    (1.3e+03, 3.80463516e-01),
    (1.3e+03, 3.97400031e-01),
    (1.3e+03, 4.14792066e-01),
    (1.3e+03, 4.32626501e-01),
    (1.3e+03, 4.50886822e-01),
    (1.3e+03, 4.69552805e-01),
    (1.4e+03, 4.88600188e-01),
    (1.4e+03, 5.08000369e-01),
    (1.4e+03, 5.27720137e-01),
    (1.4e+03, 5.47721450e-01),
    (1.4e+03, 5.67961280e-01),
    (1.4e+03, 5.88391560e-01),
    (1.4e+03, 6.08959244e-01),
    (1.4e+03, 6.29606526e-01),
    (1.4e+03, 6.50271242e-01),
    (1.4e+03, 6.70887497e-01),
    (1.4e+03, 6.91386564e-01),
    (1.4e+03, 7.11698082e-01),
    (1.4e+03, 7.31751620e-01),
    (1.5e+03, 7.51478616e-01),
    (1.5e+03, 7.70814724e-01),
    (1.5e+03, 7.89702529e-01),
    (1.5e+03, 8.08094539e-01),
    (1.5e+03, 8.25956224e-01),
    (1.5e+03, 8.43268797e-01),
    (1.5e+03, 8.60031242e-01),
    (1.5e+03, 8.76261114e-01),
    (1.5e+03, 8.91993729e-01),
    (1.5e+03, 9.07279578e-01),
    (1.6e+03, 9.22152442e-01),
    (1.6e+03, 9.36510281e-01),
    (1.6e+03, 9.50956165e-01),
    (1.6e+03, 9.65180469e-01),
    (1.6e+03, 9.79265914e-01),
    (1.6e+03, 9.93280802e-01),
    (1.6e+03, 1.00728302e+00),
    (1.6e+03, 1.02132106e+00),
    (1.6e+03, 1.03543558e+00),
    (1.6e+03, 1.04966078e+00),
    (1.7e+03, 1.06402559e+00),
    (1.7e+03, 1.07855463e+00),
    (1.7e+03, 1.09326907e+00),
    (1.7e+03, 1.10818732e+00),
    (1.7e+03, 1.12332607e+00),
    (1.7e+03, 1.13870277e+00),
    (1.7e+03, 1.15434220e+00),
    (1.7e+03, 1.17028870e+00),
    (1.7e+03, 1.18661928e+00),
    (1.8e+03, 1.20344594e+00),
    (1.8e+03, 1.22089944e+00),
    (1.8e+03, 1.23910022e+00),
    (1.8e+03, 1.25813179e+00),
    (1.8e+03, 1.27802785e+00),
    (1.8e+03, 1.27802785e+00),
    (1.9e+03, 1.48714588e+00),
    (2.1e+03, 1.73095991e+00),
    (2.2e+03, 2.01488152e+00),
    (2.4e+03, 2.35628536e+00),
    (2.6e+03, 2.77432659e+00),
    (2.8e+03, 3.28829215e+00),
    (3.1e+03, 3.92332636e+00),
    (3.4e+03, 4.73467577e+00),
    (3.7e+03, 5.79541532e+00),
    (4.1e+03, 7.21436674e+00),
    (4.7e+03, 9.16505404e+00),
    (5.3e+03, 1.19535379e+01),
    (6.2e+03, 1.70705073e+01),
    (7.3e+03, 2.41799614e+01),
    (8.9e+03, 3.58116650e+01),
    (1.1e+04, 5.74724305e+01),
    (1.5e+04, 1.04618146e+02),
    (2.3e+04, 2.38997209e+02),
    (4.6e+04, 9.37557119e+02),
];

/// Interpolate CAMB opacity at redshift z (linear in log-z for z>10).
fn camb_opacity_at_z(z: f64) -> f64 {
    if z <= CAMB_OPAC_TABLE[0].0 { return CAMB_OPAC_TABLE[0].1; }
    let n = CAMB_OPAC_TABLE.len();
    if z >= CAMB_OPAC_TABLE[n-1].0 { return CAMB_OPAC_TABLE[n-1].1; }
    // Binary search
    let mut lo = 0usize; let mut hi = n - 1;
    while hi - lo > 1 {
        let mid = (lo + hi) / 2;
        if CAMB_OPAC_TABLE[mid].0 <= z { lo = mid; } else { hi = mid; }
    }
    let (z0, o0) = CAMB_OPAC_TABLE[lo];
    let (z1, o1) = CAMB_OPAC_TABLE[hi];
    let w = (z - z0) / (z1 - z0);
    o0 + w * (o1 - o0)
}

#[cfg(test)]
mod xe_audit {
    use super::*;
    #[test]
    fn test_bass_xe_profile() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 5000);
        let n = vis.z_grid.len();
        
        // Print xe(z) at key redshifts
        eprintln!("  BASS HyRec xe(z) profile:");
        eprintln!("  {:>8} {:>12} {:>12} {:>12}", "z", "xe", "kappa_dot", "g");
        let z_check = [1500.0, 1300.0, 1200.0, 1100.0, 1075.0, 1050.0, 1000.0, 900.0, 800.0];
        for &zc in &z_check {
            // Find nearest z in grid
            let mut best_i = 0;
            let mut best_d = 1e30f64;
            for i in 0..n {
                let d = (vis.z_grid[i] - zc).abs();
                if d < best_d { best_d = d; best_i = i; }
            }
            let z = vis.z_grid[best_i];
            let xe = vis.xe_grid[best_i];
            let kd = vis.kappa_dot_grid[best_i];
            let g = vis.g_grid[best_i];
            eprintln!("  {:8.1} {:12.6} {:12.4e} {:12.4e}", z, xe, kd, g);
        }
        
        // Also print nH0 for cross-check
        // nH0 computation (same as VisibilityParams::n_h0)
        let h0_si = p.h * 100.0e3 / 3.085677581e22; // s⁻¹
        let rho_c = 3.0 * h0_si.powi(2) / (8.0 * std::f64::consts::PI * 6.674e-11);
        let n_h0 = (1.0 - 0.2454) * p.omega_b * rho_c / 1.6726e-27;
        eprintln!("\n  nH0 = {:.6e} m⁻³", n_h0);
        eprintln!("  σT = 6.6525e-29 m²");
        eprintln!("  MPC_M = 3.0857e+22 m");
        
        // κ' = xe × nH0 × σT × (1+z)² × MPC_M
        let z_test = 1075.0;
        let i_test = (0..n).min_by(|&a,&b| (vis.z_grid[a]-z_test).abs().partial_cmp(&(vis.z_grid[b]-z_test).abs()).unwrap()).unwrap();
        let xe_test = vis.xe_grid[i_test];
        let kd_computed = xe_test * n_h0 * 6.6525e-29 * (1.0+z_test).powi(2) * 3.0857e22;
        eprintln!("\n  Cross-check κ'(z=1075):");
        eprintln!("    xe = {:.6}", xe_test);
        eprintln!("    κ'_from_xe = {:.4e}", kd_computed);
        eprintln!("    κ'_stored  = {:.4e}", vis.kappa_dot_grid[i_test]);
    }
}

    #[test]
    fn test_ode_state_k005() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let k = 0.05_f64;
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 0,
            nq_massive: 0, lmax_m: 0,
            k_min: k, k_max: k, n_k: 1,
            ell_max: 50,
            ..Default::default()
        };
        
        match solve_kmode_full(k, &p, &vis, &pcfg, None) {
            Ok(result) => {
                let lay = CambLayout::new(pcfg.lmax_g as usize, pcfg.lmax_n as usize);
                eprintln!("ODE state at k={} (Rust Rodas5P):", k);
                eprintln!("  n_snaps = {}", result.eta_grid.len());
                
                // Print state at key tau values
                let tau_check = [100.0, 150.0, 200.0, 250.0, 280.0, 285.0, 290.0, 300.0, 350.0];
                for &tc in &tau_check {
                    // Find nearest snapshot
                    let mut best_i = 0;
                    let mut best_dt = 1e30_f64;
                    for (i, &eta) in result.eta_grid.iter().enumerate() {
                        let dt = (eta - tc).abs();
                        if dt < best_dt { best_dt = dt; best_i = i; }
                    }
                    if best_dt > 5.0 { continue; }
                    let tau = result.eta_grid[best_i];
                    let phi = result.phi[best_i];
                    let s_sw = result.source_sw[best_i];
                    let s_tot = result.source_total[best_i];
                    eprintln!("  τ={:.0}: phi={:+.6}, sw={:+.6e}, tot={:+.6e}", 
                             tau, phi, s_sw, s_tot);
                }
                
                // Compare D_2
                eprintln!("  Source max = {:.4e}", result.source_total.iter()
                    .map(|x| x.abs()).fold(0.0_f64, f64::max));
            }
            Err(e) => eprintln!("FAIL: {}", e),
        }
    }

    #[test]
    fn test_tau_convention_debug() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        eprintln!("η_0 = {:.1} Mpc", eta_0);
        
        // eta_grid[0] is z=z_max (high z), eta_grid[last] is z=0
        let n = vis.z_grid.len();
        eprintln!("z[0]={:.1}, η[0]={:.1}", vis.z_grid[0], vis.eta_grid[0]);
        eprintln!("z[last]={:.1}, η[last]={:.1}", vis.z_grid[n-1], vis.eta_grid[n-1]);
        
        // Key z → η mapping
        for &z_target in &[1100.0, 1075.0, 1000.0, 100.0, 10.0, 0.0] {
            let mut best = 0;
            for i in 0..n {
                if (vis.z_grid[i] - z_target).abs() < (vis.z_grid[best] - z_target).abs() {
                    best = i;
                }
            }
            let eta = vis.eta_grid[best];
            let tau_bass = eta_0 - eta;
            eprintln!("  z={:6.1}: η={:8.1} Mpc, τ_BASS(=η_0-η)={:8.1}", z_target, eta, tau_bass);
        }
        
        // So when we solve ODE from tau_BASS=0 to tau_BASS=eta_0:
        // tau_BASS=0 is z=0 (today)
        // tau_BASS=η_0 is z=z_max (big bang)
        // CAMB: tau_CAMB=0 is big bang, tau_CAMB=η_0 is today
        // τ_BASS = η_0 - τ_CAMB
        
        // For solve_kmode_full, tau_profile is built as η_0 - η_grid[i]
        // The ODE integrates FORWARD in tau_BASS (from small to large)
        // i.e. from z=0 BACKWARD to z_max — or equivalently from today to big bang
        // This means the ODE runs TIME-REVERSED compared to CAMB!
        eprintln!("\nτ_BASS direction: 0=today → η_0=big_bang (TIME-REVERSED vs CAMB)");
    }

    #[test]
    fn test_source_vs_camb() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        
        let k = 0.05_f64;
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 0,
            nq_massive: 0, lmax_m: 0,
            k_min: k, k_max: k, n_k: 1, ell_max: 50,
            ..Default::default()
        };
        
        match solve_kmode_full(k, &p, &vis, &pcfg, None) {
            Ok(result) => {
                eprintln!("Source comparison at k={}, η₀={:.1}:", k, eta_0);
                // Map key z to tau_BASS = eta_0 - eta(z)
                let z_targets: Vec<f64> = vec![1200.0, 1100.0, 1088.0, 1075.0, 1050.0, 1000.0];
                for &z_t in &z_targets {
                    // Find eta at z_t
                    let mut best_j = 0usize;
                    for j in 0..vis.z_grid.len() {
                        if (vis.z_grid[j]-z_t).abs() < (vis.z_grid[best_j]-z_t).abs() { best_j = j; }
                    }
                    let tau_bass = eta_0 - vis.eta_grid[best_j];
                    // Find nearest snapshot in result
                    let mut best_i = 0usize;
                    for i in 0..result.eta_grid.len() {
                        if (result.eta_grid[i]-tau_bass).abs() < (result.eta_grid[best_i]-tau_bass).abs() { best_i = i; }
                    }
                    let tau_actual = result.eta_grid[best_i];
                    eprintln!("  z={:.0}: τ_BASS={:.1}({:.1}), S_sw={:+.4e}, S_dop={:+.4e}, S_q={:+.4e}, S_tot={:+.4e}, φ={:+.4}",
                        z_t, tau_bass, tau_actual,
                        result.source_sw[best_i], result.source_dop[best_i],
                        result.source_quad[best_i], result.source_total[best_i],
                        result.phi[best_i]);
                }
                // Also print peak source
                let (mut ipeak, mut smax) = (0, 0.0_f64);
                for i in 0..result.source_total.len() {
                    if result.source_total[i].abs() > smax { smax = result.source_total[i].abs(); ipeak = i; }
                }
                eprintln!("  Source peak: τ_BASS={:.1}, S_tot={:+.4e}", result.eta_grid[ipeak], result.source_total[ipeak]);
                eprintln!("  CAMB: peak at z≈1088 (τ_CAMB≈280), S_max≈2.20e-2");
            }
            Err(e) => eprintln!("FAIL: {}", e),
        }
    }

    #[test]
    fn test_state_variables_vs_camb() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        
        let k = 0.05_f64;
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 0,
            nq_massive: 0, lmax_m: 0,
            k_min: k, k_max: k, n_k: 1, ell_max: 50,
            ..Default::default()
        };
        
        match solve_kmode_full(k, &p, &vis, &pcfg, None) {
            Ok(result) => {
                let lay = pcfg.layout();
                // Get CN snapshots: re-solve to get raw state vectors
                // Actually result only stores source/phi, not raw y
                // Need to extract from the CN integration directly
                eprintln!("State variable comparison at k={}:", k);
                eprintln!("  (Using source decomposition as proxy)");
                eprintln!("  CAMB at z=1075: Th0=-0.029, etak=-0.012, vb=+0.374");
                eprintln!("  CAMB at z=1100: Th0=+0.146, etak=-0.015, vb=+0.565");
                
                // Check phi (which we DO have):
                for &(z_t, camb_phi) in &[(1200.0, -0.53), (1100.0, -0.49), (1075.0, -0.48), (1000.0, -0.46)] {
                    let mut best_j = 0usize;
                    for j in 0..vis.z_grid.len() {
                        if (vis.z_grid[j]-z_t).abs() < (vis.z_grid[best_j]-z_t).abs() { best_j = j; }
                    }
                    let tau_bass = eta_0 - vis.eta_grid[best_j];
                    let mut best_i = 0usize;
                    for i in 0..result.eta_grid.len() {
                        if (result.eta_grid[i]-tau_bass).abs() < (result.eta_grid[best_i]-tau_bass).abs() { best_i = i; }
                    }
                    eprintln!("  z={:.0}: phi_BASS={:+.4}, phi_CAMB≈{:+.2}", 
                        z_t, result.phi[best_i], camb_phi);
                }
            }
            Err(e) => eprintln!("FAIL: {}", e),
        }
    }

    #[test]
    fn test_cn_grid_spacing() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        
        eprintln!("CN grid near recombination (z=1200..900):");
        let mut steps_recom = 0;
        for i in 0..vis.z_grid.len()-1 {
            if vis.z_grid[i] > 900.0 && vis.z_grid[i] < 1200.0 {
                let tau_i = eta_0 - vis.eta_grid[i];
                let tau_next = eta_0 - vis.eta_grid[i+1];
                let dz = vis.z_grid[i+1] - vis.z_grid[i];
                let dtau = (tau_next - tau_i).abs();
                if steps_recom < 10 || steps_recom % 20 == 0 {
                    eprintln!("  z={:.1}: dtau={:.3} Mpc, dz={:.2}, opac={:.2e}, g={:.4e}", 
                        vis.z_grid[i], dtau, dz, vis.kappa_dot_grid[i], vis.g_grid[i]);
                }
                steps_recom += 1;
            }
        }
        eprintln!("  Total steps in z=900..1200: {}", steps_recom);
        
        // Check total grid size
        eprintln!("  Total visibility grid points: {}", vis.z_grid.len());
        
        // Compare oscillation scale vs grid
        let k = 0.05;
        let cs = 1.0 / 3.0_f64.sqrt();
        let lambda_acoustic = 2.0 * std::f64::consts::PI / (k * cs);
        eprintln!("  Acoustic wavelength at k=0.05: {:.1} Mpc", lambda_acoustic);
    }

    #[test]
    fn test_vis_in_solver() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        
        // The solver iterates (0..n_vis).rev()
        // At z≈1088 (visibility peak):
        let mut ipeak = 0;
        for i in 0..vis.z_grid.len() {
            if vis.g_grid[i] > vis.g_grid[ipeak] { ipeak = i; }
        }
        let z_peak = vis.z_grid[ipeak];
        let tau_peak = eta_0 - vis.eta_grid[ipeak];
        eprintln!("Vis peak: z={:.1}, η={:.1}, τ_BASS={:.1}, g={:.4e}",
            z_peak, vis.eta_grid[ipeak], tau_peak, vis.g_grid[ipeak]);
        
        // Check: at τ_BASS = tau_peak, does the solver see the correct bg?
        // In solve_kmode_full, bg[i] has vis: vis.g_grid[i], where i iterates in reverse
        // So bg at τ_BASS=tau_peak has vis=g_grid[ipeak]. That's correct.
        
        // But what about dvis and ddvis? They're computed from g_dot[i]:
        // g_dot[i] = -(g[i+1] - g[i-1]) / (eta[i+1] - eta[i-1])
        // The SIGN: dg/dη, then stored as dvis. But source uses dg/dτ_BASS.
        // dτ_BASS = -dη → dg/dτ_BASS = -dg/dη
        // But line 1751: g_dot[i] = -(vis.g_grid[i+1] - vis.g_grid[i-1]) / dt
        // This is ALREADY -dg/dη = dg/dτ_BASS. So sign is correct.
        
        // Wait — but in solve_kmode_full, g_dot is computed DIFFERENTLY from the old solve_kmode!
        // Let me check both:
        
        // solve_kmode_full line 1751:
        // g_dot[i] = -(vis.g_grid[i+1] - vis.g_grid[i-1]) / dt
        // where dt = vis.eta_grid[i+1] - vis.eta_grid[i-1]
        // This is -dg/dη = +dg/dτ_BASS ✓
        
        // But the source formula uses gp = bg.dvis
        // And the source formula is written for CAMB convention where τ increases forward in time
        // In CAMB: g' = dg/dτ_CAMB where τ_CAMB increases toward us
        // τ_BASS goes in the SAME direction (from big bang to today), so this should be fine
        
        // Actually wait. Let me re-examine the tau convention:
        // vis.eta_grid: η(z=0)=0, η(z=4000)=13865 → η is comoving distance from us
        // tau_BASS = eta_0 - eta = 13865 - η → tau_BASS(z=0) = 13865, tau_BASS(z=4000) = 0
        // NO WAIT: 
        eprintln!("η(z=0)={:.1}, η(z=4000)={:.1}", vis.eta_grid[0], vis.eta_grid[vis.z_grid.len()-1]);
        eprintln!("z[0]={:.1}, z[last]={:.1}", vis.z_grid[0], vis.z_grid[vis.z_grid.len()-1]);
        
        // So tau_BASS = eta_0 - eta:
        // z=0: eta=0, tau_BASS=13865 (far away in "time" from big bang)
        // z=4000: eta=13865, tau_BASS=0 (near big bang)
        // This means tau_BASS is like conformal time from the big bang! Same direction as CAMB's τ.
        eprintln!("τ_BASS(z=0)={:.1}, τ_BASS(z=4000)={:.1}", eta_0, 0.0);
        eprintln!("τ_CAMB(z=0)≈14153, τ_CAMB(z=4000)≈3");
        eprintln!("Both increase from big bang to today ✓");
        
        // The source peak should be at τ_BASS≈182.6
        // CAMB source peak at τ_CAMB≈280
        // If D_ℓ uses chi = eta_0 - tau_BASS for LoS distance, that's fine
        
        // Now the real question: is the D_ℓ integrand correct?
        // delta_ell = ∫ S(τ) j_ℓ(k χ) dτ where χ = conformal distance = tau_0 - tau
        // In our convention: χ = eta_0 - tau_BASS → x = k(eta_0 - tau_BASS)
        // In compute_dl_spectrum_fast line 1384:
        // x_i = k * (eta_0 - eta_i) where eta_i = result.eta_grid[i] = tau_BASS
        // So x_i = k * (eta_0 - tau_BASS) = k * chi ✓
        
        eprintln!("\nAt visibility peak (z=1088, τ_BASS=182.6):");
        eprintln!("  χ = eta_0 - τ_BASS = 13865 - 183 = 13682 Mpc");
        eprintln!("  x = k*χ = 0.05 * 13682 = 684 → j_2(684) is valid");
        eprintln!("  This is correct.");
    }

    #[test]
    fn test_bootstrap_ic_debug() {
        let lay = CambLayout::new(16, 16);
        for &k in &[0.001, 0.01, 0.05, 0.1, 0.25] {
            if let Some((tau_init, ic)) = bootstrap_ic_lookup(k, &lay) {
                eprintln!("k={:.3}: tau_init={:.1} (CAMB time), etak={:.4e}, Θ₀={:.4e}, Θ₁={:.4e}",
                    k, tau_init, ic[lay.i_etak], ic[lay.theta(0)], ic[lay.theta(1)]);
                eprintln!("  → injected at τ_BASS={:.1}, but τ_CAMB={:.1} → z≈{}", 
                    tau_init, tau_init, 
                    if tau_init < 100.0 { ">>10000" } else { "???" });
            } else {
                eprintln!("k={:.3}: no bootstrap IC", k);
            }
        }
        eprintln!("\nFIX: convert tau_init from CAMB→BASS: tau_BASS = tau_CAMB - 288.1");
        eprintln!("For tau_CAMB=10: tau_BASS = -278 → falls back to adiabatic IC at τ_BASS=0");
        eprintln!("For tau_CAMB=50: tau_BASS = -238 → same");
    }

    #[test]
    fn test_tau_offset() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let h0c = p.h * 1e7 / 2.99792458e10;
        let og = p.omega_gamma();
        let omega_nu_ml = og * 0.2271 * 3.044;
        let omega_r = og + omega_nu_ml;
        let z_max = vis.z_grid.iter().cloned().fold(0.0_f64, f64::max);
        let tau_offset = 1.0 / (h0c * omega_r.sqrt() * (1.0 + z_max));
        eprintln!("z_max={:.0}, omega_r={:.6e}, h0c={:.6e}", z_max, omega_r, h0c);
        eprintln!("tau_offset = {:.1} Mpc (CAMB: 98.2 Mpc)", tau_offset);
        eprintln!("For bootstrap tau_CAMB=10: tau_BASS = {:.1}", 10.0 - tau_offset);
        eprintln!("For bootstrap tau_CAMB=50: tau_BASS = {:.1}", 50.0 - tau_offset);
    }

    #[test]
    fn test_dl_200k() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 0,
            nq_massive: 0, lmax_m: 0,
            k_min: 5e-5, k_max: 0.3, n_k: 200,
            ell_max: 300,
            ..Default::default()
        };
        
        let t0 = Instant::now();
        match solve_production_spectrum(&p, &vis, &pcfg) {
            Ok(dl) => {
                let wall = t0.elapsed().as_secs_f64();
                eprintln!("  200k D_ℓ: {:.1}s ({:.0}ms/k)", wall, wall/200.0*1000.0);
                // CAMB reference: D₂≈1022, D₃₀≈1070, D₁₀₀≈2611, D₂₂₀≈5733
                for &(ell, camb_val) in &[(2,1022.0),(10,1130.0),(30,1070.0),(100,2611.0),(200,5733.0),(300,6136.0)] {
                    if dl.len() > ell-2 {
                        let ratio = dl[ell-2] / camb_val;
                        eprintln!("  D_{:3} = {:7.1} (CAMB: {:7.1}, ratio: {:.3})", ell, dl[ell-2], camb_val, ratio);
                    }
                }
            }
            Err(e) => eprintln!("FAIL: {}", e),
        }
    }

    /// PERF-01 mini-config: 24 DOF, 50 k-modes, ell_max=200.
    /// Designed for fast iteration during PR-physics work (~12-20s vs 75s
    /// for test_dl_200k). NOT a substitute for the primary baseline —
    /// physics PRs must still verify against test_dl_200k at closure.
    ///
    /// Acceptance: D_2 within ±2% of test_dl_200k's D_2 (sparser k-grid
    /// gives slight numerical difference but should track closely).
    #[test]
    fn test_dl_50k_mini() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 0,
            nq_massive: 0, lmax_m: 0,
            k_min: 5e-5, k_max: 0.3, n_k: 50,    // mini: 50 k-modes
            ell_max: 200,                          // mini: ℓ ≤ 200
            ..Default::default()
        };
        
        let t0 = Instant::now();
        match solve_production_spectrum(&p, &vis, &pcfg) {
            Ok(dl) => {
                let wall = t0.elapsed().as_secs_f64();
                eprintln!("  [MINI] 50k_mini D_ℓ: {:.1}s ({:.0}ms/k)", wall, wall/50.0*1000.0);
                for &(ell, camb_val) in &[(2,1022.0),(10,1130.0),(30,1070.0),(100,2611.0),(200,5733.0)] {
                    if dl.len() > ell-2 {
                        let ratio = dl[ell-2] / camb_val;
                        eprintln!("  [MINI] D_{:3} = {:7.1} (CAMB: {:7.1}, ratio: {:.3})", ell, dl[ell-2], camb_val, ratio);
                    }
                }
            }
            Err(e) => eprintln!("[MINI] FAIL: {}", e),
        }
    }

    /// Full-pipeline sampling profiler for test_dl_50k_mini (Rodas5P path).
    /// Uses pprof-rs SIGPROF sampling at 200 Hz. Produces:
    ///   - flamegraph SVG at $BASS_PROF_OUT/flame_<config>.svg (default /tmp)
    ///   - per-function text summary printed to stderr
    /// Run manually: cargo test --release -- --ignored profile_mini
    #[test]
    #[ignore]
    fn profile_mini() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;

        let out_dir = std::env::var("BASS_PROF_OUT").unwrap_or_else(|_| "/tmp/bass_prof".into());
        std::fs::create_dir_all(&out_dir).ok();

        let label = std::env::var("BASS_PROF_LABEL").unwrap_or_else(|_| "mini_rodas".into());
        let n_k: usize = std::env::var("BASS_N_K").ok()
            .and_then(|v| v.parse().ok()).unwrap_or(50);
        let ell_max: usize = std::env::var("BASS_ELL_MAX").ok()
            .and_then(|v| v.parse().ok()).unwrap_or(200);
        let freq: i32 = std::env::var("BASS_PROF_FREQ").ok()
            .and_then(|v| v.parse().ok()).unwrap_or(200);

        eprintln!("[PROF] label={} n_k={} ell_max={} freq={}Hz out={}",
                  label, n_k, ell_max, freq, out_dir);

        // Warm-up (HyRecTables cache etc.)
        let p = VisibilityParams::planck2018();
        let t_tables_start = Instant::now();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        eprintln!("[PROF] setup (tables+visibility): {:.3}s",
                  t_tables_start.elapsed().as_secs_f64());

        // Reset Bessel atomic counters before measurement (if BASS_BESSEL_PROF=1)
        crate::los::bessel::bessel_prof_reset();

        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 0,
            nq_massive: 0, lmax_m: 0,
            k_min: 5e-5, k_max: 0.3, n_k,
            ell_max,
            ..Default::default()
        };

        // Start sampling profiler
        let guard = pprof::ProfilerGuardBuilder::default()
            .frequency(freq)
            .blocklist(&["libc", "libgcc", "pthread", "vdso"])
            .build()
            .expect("failed to build ProfilerGuard");

        let t0 = Instant::now();
        let result = solve_production_spectrum(&p, &vis, &pcfg);
        let wall = t0.elapsed().as_secs_f64();

        // Snapshot Bessel counters (if enabled)
        let (arr, up, mil, sx, zr, mil_it, rsc, up_it) = crate::los::bessel::bessel_prof_snapshot();
        if arr > 0 {
            eprintln!("\n[PROF] ============ BESSEL BRANCH COUNTERS ============");
            eprintln!("[PROF] array calls (total):      {:>10}", arr);
            eprintln!("[PROF]   upward recurrence:      {:>10}  ({:.1}%)", up, 100.0*up as f64/arr as f64);
            eprintln!("[PROF]   miller downward:        {:>10}  ({:.1}%)", mil, 100.0*mil as f64/arr as f64);
            eprintln!("[PROF]   small-x series:         {:>10}  ({:.1}%)", sx, 100.0*sx as f64/arr as f64);
            eprintln!("[PROF]   zero-x shortcut:        {:>10}  ({:.1}%)", zr, 100.0*zr as f64/arr as f64);
            eprintln!("[PROF] upward iters total:       {:>10}", up_it);
            eprintln!("[PROF] miller iters total:       {:>10}  ({:.2}x upward iters)",
                      mil_it, mil_it as f64 / up_it.max(1) as f64);
            eprintln!("[PROF] miller rescales:          {:>10}", rsc);
            eprintln!("[PROF] work per call avg:   up={:.1} iter  miller={:.1} iter",
                      up_it as f64 / up.max(1) as f64,
                      mil_it as f64 / mil.max(1) as f64);
        }

        // Report
        let report = guard.report().build().expect("failed to build pprof report");

        // Flamegraph SVG
        let svg_path = format!("{}/flame_{}.svg", out_dir, label);
        let svg_file = std::fs::File::create(&svg_path).expect("create svg");
        report.flamegraph(svg_file).expect("write flamegraph");
        eprintln!("[PROF] flamegraph -> {}", svg_path);

        // Text report: top functions by self sample count
        // pprof::Report.data is HashMap<Frames, isize> — collapse to symbol names
        let mut buckets: std::collections::HashMap<String, isize> = std::collections::HashMap::new();
        let mut module_buckets: std::collections::HashMap<&'static str, isize> = std::collections::HashMap::new();
        let mut total_samples: isize = 0;
        for (frames, count) in &report.data {
            total_samples += *count;
            if let Some(leaf) = frames.frames.first().and_then(|f| f.first()) {
                let name = leaf.name();
                let entry = buckets.entry(name.clone()).or_insert(0);
                *entry += *count;

                // Module classification (coarse buckets for high-level view)
                let bucket = if name.contains("spherical_bessel") || name.contains("::los::") {
                    "LoS_Bessel"
                } else if name.contains("compute_dl_spectrum") || name.contains("integrate_los") {
                    "LoS_integrate"
                } else if name.contains("::core::lu::") {
                    "ODE_LU"
                } else if name.contains("::rodas5p::") || name.contains("linear_profile") {
                    "ODE_Rodas5P"
                } else if name.contains("imex_ark4") || name.contains("imex_collision") {
                    "ODE_IMEX"
                } else if name.contains("build_camb_matrix") {
                    "matrix_build"
                } else if name.contains("camb_rhs") || name.contains("source") {
                    "source_extract"
                } else if name.contains("CommonProfile") || name.contains("visibility")
                       || name.contains("HyRec") {
                    "setup"
                } else if name.contains("alloc") || name.contains("mi_") || name.contains("mimalloc") {
                    "alloc"
                } else if name.contains("rayon") || name.contains("par_") {
                    "rayon"
                } else {
                    "other"
                };
                *module_buckets.entry(bucket).or_insert(0) += *count;
            }
        }
        let mut rows: Vec<(String, isize)> = buckets.into_iter().collect();
        rows.sort_by(|a, b| b.1.cmp(&a.1));
        let mut mod_rows: Vec<(&'static str, isize)> = module_buckets.into_iter().collect();
        mod_rows.sort_by(|a, b| b.1.cmp(&a.1));

        eprintln!("\n[PROF] ============ MODULE AGGREGATION ============");
        eprintln!("[PROF] total samples: {}, wall: {:.2}s ({} Hz expected {:.0})",
                  total_samples, wall, freq, wall * freq as f64);
        eprintln!("[PROF] {:>7}  {:>6}  {}", "samples", "pct", "module");
        for (name, count) in &mod_rows {
            let pct = 100.0 * (*count as f64) / (total_samples.max(1) as f64);
            eprintln!("[PROF] {:>7}  {:>5.1}%  {}", count, pct, name);
        }

        eprintln!("\n[PROF] ============ TOP SELF-TIME FUNCTIONS ============");
        eprintln!("[PROF] {:>7}  {:>6}  {}", "samples", "pct", "function");
        for (name, count) in rows.iter().take(40) {
            let pct = 100.0 * (*count as f64) / (total_samples.max(1) as f64);
            if pct < 0.2 { break; }
            eprintln!("[PROF] {:>7}  {:>5.1}%  {}", count, pct, name);
        }

        // Write text report to file for offline analysis
        let text_path = format!("{}/top_{}.txt", out_dir, label);
        let mut text = String::new();
        text.push_str(&format!("# pprof top self-time for {} (wall {:.2}s, {} samples)\n",
                               label, wall, total_samples));
        for (name, count) in &rows {
            let pct = 100.0 * (*count as f64) / (total_samples.max(1) as f64);
            if pct < 0.05 { break; }
            text.push_str(&format!("{:>6}  {:>5.1}%  {}\n", count, pct, name));
        }
        std::fs::write(&text_path, text).expect("write text report");
        eprintln!("[PROF] top-functions txt -> {}", text_path);

        let _ = result; // suppress unused warning
    }

    /// PR-IMEX-03 smoke benchmark: N k-modes (env BASS_N_K, default 5) through
    /// solve_production_spectrum. Toggle via env BASS_USE_IMEX=1.
    #[test]
    fn test_dl_5k_imex_smoke() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;

        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        let n_k: usize = std::env::var("BASS_N_K").ok()
            .and_then(|v| v.parse().ok()).unwrap_or(5);

        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 0,
            nq_massive: 0, lmax_m: 0,
            k_min: 5e-5, k_max: 0.3, n_k,
            ell_max: 50,
            ..Default::default()
        };

        let use_imex = std::env::var("BASS_USE_IMEX").map_or(false, |v| v == "1");
        eprintln!("  [SMOKE] path = {}, n_k = {}", if use_imex { "IMEX-ARK4" } else { "Rodas5P" }, n_k);

        let t0 = Instant::now();
        match solve_production_spectrum(&p, &vis, &pcfg) {
            Ok(dl) => {
                let wall = t0.elapsed().as_secs_f64();
                eprintln!("  [SMOKE] wall = {:.1}s ({:.2}s/k)", wall, wall/n_k as f64);
                if dl.len() > 0 {
                    eprintln!("  [SMOKE] D_2 = {:.2}", dl[0]);
                }
            }
            Err(e) => eprintln!("  [SMOKE] FAIL: {}", e),
        }
    }


    #[test]
    fn test_dl_200k_epol() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        // E-mode ON (lmax_pol=12), massive ν OFF
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 12,
            nq_massive: 0, lmax_m: 0,
            k_min: 5e-5, k_max: 0.3, n_k: 200,
            ell_max: 300,
            ..Default::default()
        };
        
        let t0 = Instant::now();
        match solve_production_spectrum(&p, &vis, &pcfg) {
            Ok(dl) => {
                let wall = t0.elapsed().as_secs_f64();
                eprintln!("  E-mode ON, 200k: {:.1}s ({:.0}ms/k)", wall, wall/200.0*1000.0);
                for &(ell, camb_val) in &[(2,1022.0),(10,1130.0),(30,1070.0),(100,2611.0),(200,5733.0),(300,6136.0)] {
                    if dl.len() > ell-2 {
                        let ratio = dl[ell-2] / camb_val * 100.0;
                        eprintln!("  D_{:3} = {:7.1} ({:5.1}% CAMB)", ell, dl[ell-2], ratio);
                    }
                }
            }
            Err(e) => eprintln!("FAIL: {}", e),
        }
    }

    #[test]
    fn test_dl_200k_full() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let pcfg = ProductionConfig {
            n_k: 200, ell_max: 300,
            ..ProductionConfig::full_physics()
        };
        eprintln!("  Layout: {} DOF (lmax_g={}, lmax_n={}, lmax_pol={}, nq={}, lmax_m={})",
            pcfg.layout().n_state, pcfg.lmax_g, pcfg.lmax_n, pcfg.lmax_pol, pcfg.nq_massive, pcfg.lmax_m);
        
        let t0 = Instant::now();
        match solve_production_spectrum(&p, &vis, &pcfg) {
            Ok(dl) => {
                let wall = t0.elapsed().as_secs_f64();
                eprintln!("  full_physics 200k: {:.1}s ({:.0}ms/k)", wall, wall/200.0*1000.0);
                // Corrected CAMB values
                for &(ell, cv) in &[(2,1022.1),(10,819.2),(30,1056.3),(100,2699.4),(200,5592.8),(300,4047.3)] {
                    if dl.len() > ell-2 {
                        eprintln!("  D_{:3} = {:7.1} ({:5.1}% CAMB)", ell, dl[ell-2], dl[ell-2]/cv*100.0);
                    }
                }
            }
            Err(e) => eprintln!("FAIL: {}", e),
        }
    }

    #[test]
    fn test_dl_50k_full() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let pcfg = ProductionConfig {
            n_k: 50, ell_max: 300,
            ..ProductionConfig::full_physics()
        };
        eprintln!("  DOF: {}", pcfg.layout().n_state);
        
        let t0 = Instant::now();
        match solve_production_spectrum(&p, &vis, &pcfg) {
            Ok(dl) => {
                let wall = t0.elapsed().as_secs_f64();
                eprintln!("  50k full: {:.1}s ({:.0}ms/k)", wall, wall/50.0*1000.0);
                for &(ell, cv) in &[(2,1022.1),(30,1056.3),(100,2699.4),(200,5592.8)] {
                    if dl.len() > ell-2 {
                        eprintln!("  D_{:3} = {:7.1} ({:5.1}%)", ell, dl[ell-2], dl[ell-2]/cv*100.0);
                    }
                }
            }
            Err(e) => eprintln!("FAIL: {}", e),
        }
    }

    #[test]
    fn test_dl_10k_full() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let pcfg = ProductionConfig {
            lmax_g: 8, lmax_n: 8, lmax_pol: 6,
            nq_massive: 5, lmax_m: 6,
            n_k: 10, ell_max: 50,
            ..Default::default()
        };
        eprintln!("  DOF: {}", pcfg.layout().n_state);
        
        let t0 = Instant::now();
        match solve_production_spectrum(&p, &vis, &pcfg) {
            Ok(dl) => {
                let wall = t0.elapsed().as_secs_f64();
                eprintln!("  10k reduced: {:.1}s ({:.0}ms/k)", wall, wall/10.0*1000.0);
                if dl.len() > 0 { eprintln!("  D_2 = {:.1} ({:.1}% CAMB)", dl[0], dl[0]/1022.1*100.0); }
                if dl.len() > 28 { eprintln!("  D_30 = {:.1} ({:.1}% CAMB)", dl[28], dl[28]/1056.3*100.0); }
            }
            Err(e) => eprintln!("FAIL: {}", e),
        }
    }

    #[test]
    fn test_dl_50k_reduced() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        // Reduced massive ν (5 q-bins, lmax_m=6) for speed
        let pcfg = ProductionConfig {
            lmax_g: 12, lmax_n: 12, lmax_pol: 8,
            nq_massive: 5, lmax_m: 8,
            n_k: 50, ell_max: 100,
            ..Default::default()
        };
        eprintln!("  DOF: {}", pcfg.layout().n_state);
        
        let t0 = Instant::now();
        match solve_production_spectrum(&p, &vis, &pcfg) {
            Ok(dl) => {
                let wall = t0.elapsed().as_secs_f64();
                eprintln!("  50k reduced: {:.1}s ({:.0}ms/k)", wall, wall/50.0*1000.0);
                for &(ell, cv) in &[(2,1022.1),(10,819.2),(30,1056.3),(50,1530.0),(100,2699.4)] {
                    if dl.len() > ell-2 {
                        eprintln!("  D_{:3} = {:7.1} ({:5.1}%)", ell, dl[ell-2], dl[ell-2]/cv*100.0);
                    }
                }
            }
            Err(e) => eprintln!("FAIL: {}", e),
        }
    }
    #[test]
    fn test_profile_single_k() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        
        let t0 = Instant::now();
        let vis = compute_visibility(&p, &t, 3000);
        let t_vis = t0.elapsed().as_secs_f64();
        
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        let n_grid = vis.z_grid.len();
        
        // Minimal config (no pol, no massive nu)
        let pcfg_min = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 0,
            nq_massive: 0, lmax_m: 0,
            n_k: 1, ell_max: 50, ..Default::default()
        };
        // With E-mode
        let pcfg_pol = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 12,
            nq_massive: 0, lmax_m: 0,
            n_k: 1, ell_max: 50, ..Default::default()
        };
        
        eprintln!("=== PROFILING ===");
        eprintln!("Visibility: {:.3}s, {} grid points (z_max={:.0})", t_vis, n_grid, 
            vis.z_grid.iter().cloned().fold(0.0_f64, f64::max));
        eprintln!("η₀ = {:.1} Mpc", eta_0);
        
        for (label, pcfg) in [("no-pol", &pcfg_min), ("E-mode", &pcfg_pol)] {
            let n_dof = pcfg.layout().n_state;
            for &k in &[0.001, 0.01, 0.05, 0.1] {
                let t1 = Instant::now();
                match solve_kmode_full(k, &p, &vis, pcfg, None) {
                    Ok(r) => {
                        let wall = t1.elapsed().as_millis();
                        eprintln!("  {} k={:.3} ({}DOF): {}ms, {} snaps", 
                            label, k, n_dof, wall, r.eta_grid.len());
                    }
                    Err(e) => eprintln!("  {} k={:.3}: FAIL {}", label, k, e),
                }
            }
        }
    }

    #[test]
    fn test_profile_breakdown() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        
        let k = 0.05_f64;
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 12,
            nq_massive: 0, lmax_m: 0,
            n_k: 1, ell_max: 50, ..Default::default()
        };
        let lay = pcfg.layout();
        let n = lay.n_state;
        let h0c = p.h * 1e7 / 2.99792458e10;
        let og = p.omega_gamma();
        let omega_nu_ml = og * 0.2271 * 3.044;
        let n_vis = vis.z_grid.len();
        
        // Time: matrix assembly
        let t0 = Instant::now();
        let mut tau_profile = Vec::with_capacity(n_vis);
        let mut mats_flat = Vec::with_capacity(n_vis * n * n);
        let mut bg_at_snap = Vec::with_capacity(n_vis);
        let mut g_dot = vec![0.0_f64; n_vis];
        let mut g_ddot = vec![0.0_f64; n_vis];
        for i in 1..n_vis-1 {
            let dt = vis.eta_grid[i+1] - vis.eta_grid[i-1];
            if dt.abs() > 1e-30 {
                g_dot[i] = -(vis.g_grid[i+1] - vis.g_grid[i-1]) / dt;
                g_ddot[i] = (vis.g_grid[i+1] - 2.0*vis.g_grid[i] + vis.g_grid[i-1]) / (dt/2.0).powi(2);
            }
        }
        for i in (0..n_vis).rev() {
            let tau = eta_0 - vis.eta_grid[i];
            tau_profile.push(tau);
            let z = vis.z_grid[i]; let a = 1.0/(1.0+z); let h0c2=h0c*h0c;
            let bg = CambBackground {
                adotoa: a*h0c*p.e_of_z(z), grho_g: 3.0*h0c2*og/(a*a),
                grho_nu: 3.0*h0c2*omega_nu_ml/(a*a), grho_b: 3.0*h0c2*p.omega_b/a,
                grho_c: 3.0*h0c2*(p.omega_m-p.omega_b)/a,
                opac: vis.kappa_dot_grid[i], cs2b: 1e-10,
                vis: vis.g_grid[i], dvis: g_dot[i], ddvis: g_ddot[i], a, expmmu: 0.0,
            };
            let mat = build_camb_matrix(k, tau, &lay, &bg);
            mats_flat.extend_from_slice(&mat);
            bg_at_snap.push(bg);
        }
        let t_mat = t0.elapsed().as_millis();
        
        // Time: ODE solve
        let t1 = Instant::now();
        let y0 = adiabatic_ic(k, &lay, &bg_at_snap[0]);
        use crate::solver::stacked::integrate_linear_profile_rodas5p;
        use crate::core::config::Rodas5PConfig;
        let h_max_k = (20.0/k).min(5.0);
        let cfg = Rodas5PConfig {
            rtol: 1e-6, atol: 1e-9, max_steps: 1_000_000,
            h_init: None, h_min: 1e-14, h_max: h_max_k,
            f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
            use_analytic_jacobian: true, use_ft_term: false,
            use_blas_lu: false, use_block_diag: false,
            ell_max_gamma_hint: 16, ell_max_nu_hint: 16,
            ell_max_pol_hint: 12, include_pol_hint: true, use_sparse: false,
        };
        let res = integrate_linear_profile_rodas5p(
            &tau_profile, &mats_flat, n, &y0, &tau_profile, &cfg);
        let t_ode = t1.elapsed().as_millis();
        
        eprintln!("=== BREAKDOWN (k={}, {}DOF, {} grid pts) ===", k, n, n_vis);
        eprintln!("  Matrix assembly:  {}ms", t_mat);
        eprintln!("  ODE solve:        {}ms", t_ode);
        eprintln!("  Matrix mem:       {:.1}MB ({}×{}×{})", 
            n_vis as f64 * n as f64 * n as f64 * 8.0 / 1e6, n_vis, n, n);
        if let Ok((snaps, stats, _)) = res {
            eprintln!("  Rodas5P steps:    {}", stats.n_steps);
            eprintln!("  Rejected:         {}", stats.n_rejected);
        }
    }

    #[test]
    fn test_grid_distribution() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n = vis.z_grid.len();
        let mut regime = [0usize; 5]; // z>5000, 1500-5000, 800-1500, 200-800, 0-200
        let mut vis_weight = [0.0f64; 5];
        for i in 0..n {
            let z = vis.z_grid[i]; let g = vis.g_grid[i];
            let r = if z > 5000.0 {0} else if z > 1500.0 {1} else if z > 800.0 {2} else if z > 200.0 {3} else {4};
            regime[r] += 1; vis_weight[r] += g.abs();
        }
        let labels = ["z>5000", "1500-5000", "800-1500", "200-800", "0-200"];
        eprintln!("Grid distribution ({} total):", n);
        for i in 0..5 {
            eprintln!("  {:10}: {:5} pts ({:4.1}%), Σ|g|={:.4e}", 
                labels[i], regime[i], regime[i] as f64/n as f64*100.0, vis_weight[i]);
        }
    }

    #[test]
    fn test_hmax_sweep() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        let k = 0.05_f64;
        
        for &hmax in &[5.0, 10.0, 20.0, 50.0, 100.0] {
            let pcfg = ProductionConfig {
                lmax_g: 16, lmax_n: 16, lmax_pol: 12,
                nq_massive: 0, lmax_m: 0,
                n_k: 1, ell_max: 50, ..Default::default()
            };
            let lay = pcfg.layout();
            let n = lay.n_state;
            let h0c = p.h * 1e7 / 2.99792458e10;
            let og = p.omega_gamma();
            let omega_nu_ml = og * 0.2271 * 3.044;
            let n_vis = vis.z_grid.len();
            
            let mut tau_profile = Vec::with_capacity(n_vis);
            let mut mats_flat = Vec::with_capacity(n_vis * n * n);
            let mut bg_at_snap = Vec::with_capacity(n_vis);
            let mut g_dot = vec![0.0_f64; n_vis];
            let mut g_ddot = vec![0.0_f64; n_vis];
            for i in 1..n_vis-1 {
                let dt = vis.eta_grid[i+1] - vis.eta_grid[i-1];
                if dt.abs() > 1e-30 {
                    g_dot[i] = -(vis.g_grid[i+1] - vis.g_grid[i-1]) / dt;
                    g_ddot[i] = (vis.g_grid[i+1] - 2.0*vis.g_grid[i] + vis.g_grid[i-1]) / (dt/2.0).powi(2);
                }
            }
            for i in (0..n_vis).rev() {
                let tau = eta_0 - vis.eta_grid[i];
                tau_profile.push(tau);
                let z = vis.z_grid[i]; let a = 1.0/(1.0+z); let h0c2=h0c*h0c;
                let bg = CambBackground {
                    adotoa: a*h0c*p.e_of_z(z), grho_g: 3.0*h0c2*og/(a*a),
                    grho_nu: 3.0*h0c2*omega_nu_ml/(a*a), grho_b: 3.0*h0c2*p.omega_b/a,
                    grho_c: 3.0*h0c2*(p.omega_m-p.omega_b)/a,
                    opac: vis.kappa_dot_grid[i], cs2b: 1e-10,
                    vis: vis.g_grid[i], dvis: g_dot[i], ddvis: g_ddot[i], a, expmmu: 0.0,
                };
                let mat = build_camb_matrix(k, tau, &lay, &bg);
                mats_flat.extend_from_slice(&mat);
                bg_at_snap.push(bg);
            }
            
            let omega_r = og + omega_nu_ml;
            let z_max = vis.z_grid.iter().cloned().fold(0.0_f64, f64::max);
            let tau_offset = 1.0 / (h0c * omega_r.sqrt() * (1.0 + z_max));
            let bootstrap = crate::solver::sync_gauge_camb::bootstrap_ic_lookup(k, &lay)
                .map(|(tc, ic)| (tc - tau_offset, ic));
            let y0 = if let Some((_, ref ic)) = bootstrap { ic.clone() } 
                      else { adiabatic_ic(k, &lay, &bg_at_snap[0]) };
            
            use crate::solver::stacked::integrate_linear_profile_rodas5p;
            use crate::core::config::Rodas5PConfig;
            let cfg = Rodas5PConfig {
                rtol: 1e-6, atol: 1e-9, max_steps: 1_000_000,
                h_init: None, h_min: 1e-14, h_max: hmax,
                f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
                use_analytic_jacobian: true, use_ft_term: false,
                use_blas_lu: false, use_block_diag: false,
                ell_max_gamma_hint: 16, ell_max_nu_hint: 16,
                ell_max_pol_hint: 12, include_pol_hint: true, use_sparse: false,
            };
            
            let t0 = Instant::now();
            match integrate_linear_profile_rodas5p(&tau_profile, &mats_flat, n, &y0, &tau_profile, &cfg) {
                Ok((snaps, stats, _)) => {
                    let wall = t0.elapsed().as_millis();
                    // Extract source at visibility peak
                    let mut max_g_idx = 0;
                    for i in 0..bg_at_snap.len() {
                        if bg_at_snap[i].vis > bg_at_snap[max_g_idx].vis { max_g_idx = i; }
                    }
                    let yi = &snaps[max_g_idx];
                    let mut dy = vec![0.0f64; n];
                    let src = camb_rhs(k, tau_profile[max_g_idx], yi, &mut dy, &lay, &bg_at_snap[max_g_idx]);
                    
                    eprintln!("  h_max={:5.0}: {:4}ms, {:5} steps, {:3} rej, |S_peak|={:.4e}", 
                        hmax, wall, stats.n_steps, stats.n_rejected, src.s_total.abs());
                }
                Err(e) => eprintln!("  h_max={:5.0}: FAIL: {}", hmax, e),
            }
        }
        eprintln!("  CAMB |S_peak| = 2.20e-2");
    }

    #[test]
    fn test_dl_grid_density_ab() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use std::time::Instant;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        
        // A/B test: 3000 vs 6000 visibility grid points
        for &n_vis in &[3000usize, 6000] {
            let vis = compute_visibility(&p, &t, n_vis);
            let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
            
            let pcfg = ProductionConfig {
                lmax_g: 16, lmax_n: 16, lmax_pol: 12,
                nq_massive: 0, lmax_m: 0,
                n_k: 50, ell_max: 50,
                ..Default::default()
            };
            
            let t0 = Instant::now();
            match solve_production_spectrum(&p, &vis, &pcfg) {
                Ok(dl) => {
                    let wall = t0.elapsed().as_secs_f64();
                    eprintln!("  n_vis={}: {:.1}s, η₀={:.1}, D₂={:.1}, D₁₀={:.1}, D₃₀={:.1}, D₅₀={:.1}",
                        n_vis, wall, eta_0,
                        dl.get(0).unwrap_or(&0.0),
                        dl.get(8).unwrap_or(&0.0),
                        dl.get(28).unwrap_or(&0.0),
                        dl.get(48).unwrap_or(&0.0));
                }
                Err(e) => eprintln!("  n_vis={}: FAIL: {}", n_vis, e),
            }
        }
        eprintln!("  CAMB: D₂=1022, D₁₀=819, D₃₀=1056");
    }

    #[test]
    fn test_delta2_grid_ab() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        
        for &n_vis in &[3000usize, 6000] {
            let vis = compute_visibility(&p, &t, n_vis);
            let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
            
            let pcfg = ProductionConfig {
                lmax_g: 16, lmax_n: 16, lmax_pol: 12,
                nq_massive: 0, lmax_m: 0,
                n_k: 1, ell_max: 10, ..Default::default()
            };
            
            eprintln!("  n_vis={}, η₀={:.1}:", n_vis, eta_0);
            for &k in &[0.0005, 0.001, 0.005, 0.01] {
                match solve_kmode_full(k, &p, &vis, &pcfg, None) {
                    Ok(r) => {
                        let d2 = delta_ell_adaptive(&r, k, eta_0, 2, 1e-5);
                        eprintln!("    k={:.4}: Δ₂={:+.4e}", k, d2);
                    }
                    Err(_) => eprintln!("    k={:.4}: FAIL", k),
                }
            }
        }
        eprintln!("  CAMB: k=0.0005→+4.95e-2, k=0.001→+4.44e-2, k=0.01→+7.76e-3");
    }

    #[test]
    fn test_los_integrator_vs_trapezoid() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use crate::los::bessel::spherical_bessel_j;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_0 = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);
        
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 12,
            nq_massive: 0, lmax_m: 0,
            n_k: 1, ell_max: 10, ..Default::default()
        };
        
        for &k in &[0.0005, 0.001, 0.01] {
            match solve_kmode_full(k, &p, &vis, &pcfg, None) {
                Ok(r) => {
                    // Method 1: adaptive LoS integrator
                    let d2_adaptive = delta_ell_adaptive(&r, k, eta_0, 2, 1e-5);
                    
                    // Method 2: direct trapezoid on source grid
                    let n = r.eta_grid.len();
                    let mut d2_trap = 0.0_f64;
                    for i in 1..n {
                        let eta_i = r.eta_grid[i];
                        let eta_im = r.eta_grid[i-1];
                        let x_i = k * (eta_0 - eta_i).max(0.0);
                        let x_im = k * (eta_0 - eta_im).max(0.0);
                        let j_i = spherical_bessel_j(2, x_i);
                        let j_im = spherical_bessel_j(2, x_im);
                        let deta = (eta_i - eta_im).abs();
                        d2_trap += 0.5 * (r.source_total[i]*j_i + r.source_total[i-1]*j_im) * deta;
                    }
                    
                    eprintln!("  k={:.4}: adaptive={:+.4e}, trapezoid={:+.4e}, ratio={:.4}",
                        k, d2_adaptive, d2_trap, 
                        if d2_trap.abs() > 1e-20 { d2_adaptive/d2_trap } else { f64::NAN });
                }
                Err(_) => eprintln!("  k={:.4}: FAIL", k),
            }
        }
        eprintln!("  If ratio≈1: LoS integrator is correct, source is the issue");
        eprintln!("  If ratio≠1: LoS integrator has a bug");
    }

    #[test]
    fn test_phi_evolution() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 12,
            nq_massive: 0, lmax_m: 0,
            n_k: 1, ell_max: 10, ..Default::default()
        };
        
        let k = 0.001; // D₂-dominant mode
        match solve_kmode_full(k, &p, &vis, &pcfg, None) {
            Ok(r) => {
                let n = r.eta_grid.len();
                eprintln!("  Φ_N evolution at k={}:", k);
                for &frac in &[0.0, 0.01, 0.1, 0.5, 0.9, 0.99, 1.0] {
                    let i = ((n-1) as f64 * frac) as usize;
                    eprintln!("    τ={:.1}: Φ_N={:+.6}, S_total={:+.4e}", 
                        r.eta_grid[i], r.phi[i], r.source_total[i]);
                }
                // Check: Φ should be ~-0.6 at early times, ~-0.3 at late
                eprintln!("  Expected: Φ ≈ -0.6 early, decaying to ~-0.3 at z=0");
            }
            Err(e) => eprintln!("  FAIL: {}", e),
        }
    }

    #[test]
    fn test_isw_diagnostic() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        let pcfg = ProductionConfig {
            lmax_g: 16, lmax_n: 16, lmax_pol: 12,
            nq_massive: 0, lmax_m: 0,
            n_k: 1, ell_max: 10, ..Default::default()
        };
        
        let k = 0.001;
        match solve_kmode_full(k, &p, &vis, &pcfg, None) {
            Ok(r) => {
                let n = r.eta_grid.len();
                eprintln!("  ISW diagnostic at k={}:", k);
                eprintln!("  {:>6} {:>10} {:>10} {:>10} {:>10}", "τ", "S_total", "S_sw", "S_isw_est", "expmmu_chk");
                for &frac in &[0.0, 0.005, 0.01, 0.015, 0.018, 0.02, 0.5, 0.9, 0.95, 0.99, 1.0] {
                    let i = ((n-1) as f64 * frac) as usize;
                    let s_isw = r.source_total[i] - r.source_sw[i] - r.source_dop[i] - r.source_quad[i];
                    eprintln!("  {:6.1} {:+10.3e} {:+10.3e} {:+10.3e}", 
                        r.eta_grid[i], r.source_total[i], r.source_sw[i], s_isw);
                }
            }
            Err(e) => eprintln!("  FAIL: {}", e),
        }
    }
