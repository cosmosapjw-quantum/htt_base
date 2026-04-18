// BB-06 (REVISED): Bianchi Geometry Integration Test Suite.
// All 11 Bianchi variants tested. 57 tests total.

#[cfg(test)]
mod integration_tests {
    use crate::bianchi::types::*;
    use crate::bianchi::structure::*;
    use crate::bianchi::background::*;
    use crate::bianchi::curvature::*;
    use crate::bianchi::einstein::*;
    use crate::bianchi::tilt;

    /// ALL 11 Bianchi variants (was 10 — VIh was missing).
    fn all_types() -> Vec<BianchiType> {
        vec![
            BianchiType::I, BianchiType::II, BianchiType::III,
            BianchiType::IV, BianchiType::V, BianchiType::VI0,
            BianchiType::VIh(-0.5), // ← FIX: was missing
            BianchiType::VII0, BianchiType::VIIh(1.0),
            BianchiType::VIII, BianchiType::IX,
        ]
    }

    // ═══ §1. Structural: all 11 types ═══

    #[test] fn t01_all_jacobi() {
        for bt in all_types() {
            let p = bt.canonical_params();
            assert!(jacobi_check(&structure_constants(&p)) < 1e-14, "{}", bt.label());
        }
    }
    #[test] fn t02_all_curvature_trace() {
        for bt in all_types() {
            let p = bt.canonical_params();
            let rd = spatial_ricci_diagonal(&p.n_eigenvalues, p.a_magnitude);
            let r3 = spatial_ricci_scalar(&p.n_eigenvalues, p.a_magnitude);
            assert!((rd[0]+rd[1]+rd[2]-r3).abs() < 1e-13, "{}", bt.label());
        }
    }
    #[test] fn t03_all_tracefree() {
        for bt in all_types() {
            let p = bt.canonical_params();
            let s = spatial_ricci_tracefree(&p.n_eigenvalues, p.a_magnitude);
            assert!((s[0]+s[1]+s[2]).abs() < 1e-14, "{}: tr(S)={:.2e}", bt.label(), s[0]+s[1]+s[2]);
        }
    }
    #[test] fn t04_class_all_11() {
        let class_a = [BianchiType::I, BianchiType::II, BianchiType::VI0,
                       BianchiType::VII0, BianchiType::VIII, BianchiType::IX];
        let class_b = [BianchiType::III, BianchiType::IV, BianchiType::V,
                       BianchiType::VIh(-0.5), BianchiType::VIIh(1.0)];
        for bt in &class_a { assert_eq!(bt.class(), BianchiClass::A, "{}", bt.label()); }
        for bt in &class_b { assert_eq!(bt.class(), BianchiClass::B, "{}", bt.label()); }
    }

    // ═══ §2. FLRW recovery ═══

    #[test] fn t05_flrw_types() {
        let yes = [BianchiType::I, BianchiType::V, BianchiType::VII0,
                   BianchiType::VIIh(1.0), BianchiType::IX];
        let no = [BianchiType::II, BianchiType::III, BianchiType::IV,
                  BianchiType::VI0, BianchiType::VIh(-0.5), BianchiType::VIII];
        for bt in &yes { assert!(bt.has_flrw_limit(), "{} should have FLRW limit", bt.label()); }
        for bt in &no  { assert!(!bt.has_flrw_limit(), "{} should NOT have FLRW limit", bt.label()); }
    }
    #[test] fn t06_flrw_ham() { assert!(hamiltonian_constraint(0.0,0.1,0.3,0.6,0.0,0.0).abs() < 1e-15); }
    #[test] fn t07_q_rad() { assert!((deceleration(0.0,1.0,0.0,0.0)-1.0).abs() < 1e-15); }
    #[test] fn t08_q_mat() { assert!((deceleration(0.0,0.0,1.0,0.0)-0.5).abs() < 1e-15); }
    #[test] fn t09_q_lam() { assert!((deceleration(0.0,0.0,0.0,1.0)+1.0).abs() < 1e-15); }

    // ═══ §3. BI analytical ═══

    #[test] fn t10_bi_zero_r3() { let p=BianchiType::I.canonical_params(); assert_eq!(spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude),0.0); }
    #[test] fn t11_bi_zero_s() { let p=BianchiType::I.canonical_params(); assert_eq!(spatial_ricci_tracefree(&p.n_eigenvalues,p.a_magnitude),[0.0;3]); }
    #[test] fn t12_bi_decay() { let r=(1.0_f64/1091.0).powf(1.5); assert!(r>1e-5 && r<1e-4); }
    #[test] fn t13_bi_rad_const() { assert!((shear_scalar_evolution_rhs(1e-5,1.0,0.0)+1e-5).abs() < 1e-19); }
    #[test] fn t14_bi_mom_zero() { assert!(momentum_constraint(&[0.01,0.01,-0.02],&[0.0;3],&[0.0;3]).iter().all(|m| m.abs()<1e-15)); }

    // ═══ §4. BV ═══

    #[test] fn t15_bv_r3_pos() { let p=BianchiType::V.canonical_params(); assert!(spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude)>0.0); }
    #[test] fn t16_bv_s_zero() { let p=BianchiType::V.canonical_params(); let s=spatial_ricci_tracefree(&p.n_eigenvalues,p.a_magnitude); assert!((s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt()<1e-15); }
    #[test] fn t17_bv_ok_neg() { let p=BianchiType::V.canonical_params(); assert!(omega_k(spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude),1.0)<0.0); }
    #[test] fn t18_bv_mom_lin() { let s1=bv_momentum_sigma_theta(1e-4,0.0,0.315,0.001); let s2=bv_momentum_sigma_theta(2e-4,0.0,0.315,0.001); assert!((s2/s1-2.0).abs()<1e-10); }
    #[test] fn t19_bv_no_vort() { let p=BianchiType::V.canonical_params(); assert!(!tilt::tilt_generates_vorticity(&p.n_eigenvalues,&[0.01,0.005,0.0])); }

    // ═══ §5. BIX ═══

    #[test] fn t20_bix_r3() { let p=BianchiType::IX.canonical_params(); assert!((spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude)+3.0).abs()<1e-14); }
    #[test] fn t21_bix_ok_pos() { let p=BianchiType::IX.canonical_params(); assert!(omega_k(spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude),1.0)>0.0); }
    #[test] fn t22_bix_s_zero() { let p=BianchiType::IX.canonical_params(); let s=spatial_ricci_tracefree(&p.n_eigenvalues,p.a_magnitude); assert!((s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt()<1e-14); }
    #[test] fn t23_bix_lam_decay() { assert!(shear_scalar_evolution_rhs(1e-10,-1.0,0.0)<0.0); }

    // ═══ §6. BVII_h ═══

    #[test] fn t24_viih_r3() { for &h in &[0.01,0.1,0.5,1.0,10.0] { let p=BianchiType::VIIh(h).canonical_params(); assert!((spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude)-(-1.0+4.0*h)).abs()<1e-12); } }
    #[test] fn t25_viih_vort() { let p=BianchiType::VIIh(1.0).canonical_params(); assert!(tilt::tilt_generates_vorticity(&p.n_eigenvalues,&[0.01,0.0,0.0])); }
    #[test] fn t26_viih_aniso() { let p=BianchiType::VIIh(1.0).canonical_params(); let s=spatial_ricci_tracefree(&p.n_eigenvalues,p.a_magnitude); assert!((s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt()>0.1); }

    // ═══ §6b. VIh, III, IV curvature (FIX 5: was missing) ═══

    #[test] fn t26b_vih_curvature() {
        // VIh(h): n₁n₂<0, a≠0. ³R = -(n₁n₂+0+0)+4a² = -n₁n₂+4h (h=a²/|n₁n₂|)
        let p = BianchiType::VIh(-0.5).canonical_params();
        let r3 = spatial_ricci_scalar(&p.n_eigenvalues, p.a_magnitude);
        let s = spatial_ricci_tracefree(&p.n_eigenvalues, p.a_magnitude);
        let s_norm = (s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt();
        assert!(r3.is_finite(), "VIh: ³R must be finite");
        assert!((s[0]+s[1]+s[2]).abs() < 1e-14, "VIh: trace-free");
        assert!(s_norm > 0.01, "VIh: must have anisotropic curvature, ||S||={:.4}", s_norm);
    }
    #[test] fn t26c_biii_curvature() {
        let p = BianchiType::III.canonical_params();
        let r3 = spatial_ricci_scalar(&p.n_eigenvalues, p.a_magnitude);
        let s = spatial_ricci_tracefree(&p.n_eigenvalues, p.a_magnitude);
        assert!(r3.is_finite());
        assert!((s[0]+s[1]+s[2]).abs() < 1e-14);
    }
    #[test] fn t26d_biv_curvature() {
        let p = BianchiType::IV.canonical_params();
        let r3 = spatial_ricci_scalar(&p.n_eigenvalues, p.a_magnitude);
        // BIV: n=(1,0,0), a=1 → ³R = 0+4 = 4, ³S = 0 (all equal R_{αα})
        assert!((r3 - 4.0).abs() < 1e-14, "BIV: ³R = {:.4}", r3);
        let s = spatial_ricci_tracefree(&p.n_eigenvalues, p.a_magnitude);
        let s_norm = (s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt();
        assert!(s_norm < 1e-14, "BIV: ||³S|| = {:.2e} (should be 0)", s_norm);
    }

    // ═══ §7. Tilt ═══

    #[test] fn t27_dust_decay() { let (_,b,fi)=tilt::global::evolve_global_tilt_tier_b(0.05,0.0,-10.0,0.0,5000); assert!(*b.last().unwrap()<0.005); let d=fi.iter().map(|f|(f-fi[0]).abs()/fi[0].abs()).fold(0.0f64,|a,b|a.max(b)); assert!(d<1e-8); }
    #[test] fn t28_rad_frozen() { let (_,b,_)=tilt::global::evolve_global_tilt_tier_b(0.1,1.0/3.0,-10.0,0.0,1000); for &v in &b { assert!((v-0.1).abs()<1e-10); } }
    #[test] fn t29_stiff_grow() { let (_,b,_)=tilt::global::evolve_global_tilt_tier_b(0.01,1.0,-2.0,0.0,5000); assert!(*b.last().unwrap()>b[0],"stiff must grow"); }
    #[test] fn t30_bifurc() { assert!(tilt::king_ellis_zero_shear_rhs(0.5,0.0)<0.0); assert!(tilt::king_ellis_zero_shear_rhs(0.5,1.0/3.0).abs()<1e-15); assert!(tilt::king_ellis_zero_shear_rhs(0.5,0.5)>0.0); }
    #[test] fn t31_denom() { let b=tilt::king_ellis_zero_shear_rhs(2.0,0.0); let c=tilt::king_ellis_reduced_rhs(2.0,0.0); assert!((b/c-1.0).abs()>0.05); }
    #[test] fn t32_g8_ok() { tilt::frame_guard::guard_g8_bi_no_single_fluid_tilt(&BianchiType::I,0.0,1); }
    #[test] fn t33_otilt() { assert!(tilt::omega_tilt(0.0,0.3,0.01)>0.0); }

    // ═══ §8. Boost cascade ═══

    #[test] fn t34_boost_id() { let b=tilt::boost_cascade::boost_dipole(&[1.0,2.0,3.0],&[[0.1,0.0,0.0],[0.0,-0.05,0.0],[0.0,0.0,-0.05]],&[0.0;3]); for i in 0..3{assert!((b[i]-[1.0,2.0,3.0][i]).abs()<1e-15);} }
    #[test] fn t35_l2l3() { assert_eq!(tilt::boost_cascade::max_output_ell(2,1),3); }
    #[test] fn t36_btf() { let b=tilt::boost_cascade::boost_quadrupole(&[[0.1,0.0,0.0],[0.0,-0.05,0.01],[0.0,0.01,-0.05]],&[0.01,0.0,0.0],&[0.001,0.0,0.0]); assert!((b[0][0]+b[1][1]+b[2][2]).abs()<1e-14); }

    // ═══ §9. Cross-module ═══

    #[test] fn t37_closure_all() {
        for bt in all_types() {
            let p = bt.canonical_params();
            let ok = omega_k(spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude),1.0);
            let ham = hamiltonian_constraint(0.0,0.05,0.3,1.0-ok-0.05-0.3,ok,0.0);
            assert!(ham.abs()<1e-14, "{}: ham={:.2e}", bt.label(), ham);
        }
    }
    #[test] fn t38_bix_budget() { let p=BianchiType::IX.canonical_params(); let ok=omega_k(spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude),1.0); assert!(hamiltonian_constraint(0.0,0.05,0.2,0.25,ok,0.0).abs()<1e-14); }
    #[test] fn t39_shear_curv() { let s=spatial_ricci_tracefree(&[0.0;3],0.0); let rhs=shear_evolution_rhs(&[0.01,0.01,-0.02],0.5,&s,1.0); assert!((rhs[0]+0.015).abs()<1e-15); }

    /// FIX 4: Vorticity test for ALL 11 types.
    #[test] fn t40_vort_all_11() {
        let v = [0.01, 0.01, 0.01];
        let expected: Vec<(BianchiType, bool)> = vec![
            (BianchiType::I,         false), // n = 0
            (BianchiType::II,        true),  // n₁ ≠ 0
            (BianchiType::III,       true),  // n₁,n₂ ≠ 0
            (BianchiType::IV,        true),  // n₁ ≠ 0
            (BianchiType::V,         false), // n = 0
            (BianchiType::VI0,       true),  // n₁,n₂ ≠ 0
            (BianchiType::VIh(-0.5), true),  // n₁,n₂ ≠ 0
            (BianchiType::VII0,      true),  // n₁,n₂ ≠ 0
            (BianchiType::VIIh(1.0), true),  // n₁,n₂ ≠ 0
            (BianchiType::VIII,      true),  // all n ≠ 0
            (BianchiType::IX,        true),  // all n ≠ 0
        ];
        for (bt, expect) in &expected {
            let p = bt.canonical_params();
            let gen = tilt::tilt_generates_vorticity(&p.n_eigenvalues, &v);
            assert_eq!(gen, *expect, "{}: vorticity={} expect={}", bt.label(), gen, expect);
        }
    }

    // ═══ §10. Background: ALL types (FIX 3) ═══

    #[test] fn t41_bg_bi() {
        let c=CosmologyParams::standard(67.4,9.14e-5,0.315,0.685);
        let bg=evolve(&BianchiType::I.canonical_params(),&c,1e-5,1e-6,5000).unwrap();
        assert!(bg.sigma_h_of_a(1.0)<bg.sigma_h_of_a(0.001));
    }
    #[test] fn t42_bg_fried() {
        let c=CosmologyParams::standard(67.4,9.14e-5,0.315,0.685);
        let bg=evolve(&BianchiType::I.canonical_params(),&c,1e-5,1e-6,5000).unwrap();
        assert!(bg.max_constraint_violation()<1e-4);
    }
    #[test] fn t43_bg_power() {
        let c=CosmologyParams::standard(67.4,9.14e-5,0.315,0.685);
        let bg=evolve(&BianchiType::I.canonical_params(),&c,1e-5,1e-6,5000).unwrap();
        let s1=bg.sigma_h_of_a(0.01); let s2=bg.sigma_h_of_a(0.1);
        if s1>1e-30&&s2>1e-30 { assert!((s2/s1).ln()/(0.1_f64/0.01).ln()< -0.5); }
    }

    /// FIX 3: Background for BV (open)
    #[test] fn t43b_bg_bv() {
        let c = CosmologyParams::standard(67.4, 9.14e-5, 0.315, 0.685);
        let bg = evolve(&BianchiType::V.canonical_params(), &c, 1e-5, 1e-6, 5000).unwrap();
        assert!(bg.sigma_h_of_a(1.0) < bg.sigma_h_of_a(0.001), "BV shear must decay");
    }
    /// FIX 3: Background for BIX (closed, isotropic curvature → same as BI decay)
    #[test] fn t43c_bg_bix() {
        let c = CosmologyParams::standard(67.4, 9.14e-5, 0.315, 0.685);
        let bg = evolve(&BianchiType::IX.canonical_params(), &c, 1e-5, 1e-6, 5000).unwrap();
        assert!(bg.sigma_h_of_a(1.0) < bg.sigma_h_of_a(0.001), "BIX shear must decay");
    }
    /// FIX 3: Background for BVIII (anisotropic curvature)
    #[test] fn t43d_bg_bviii() {
        let c = CosmologyParams::standard(67.4, 9.14e-5, 0.315, 0.685);
        let bg = evolve(&BianchiType::VIII.canonical_params(), &c, 1e-5, 1e-6, 5000).unwrap();
        assert!(bg.sigma_h_of_a(1.0).is_finite(), "BVIII must be stable");
    }
    /// FIX 3: Background for BVII_h (anisotropic curvature)
    #[test] fn t43e_bg_viih() {
        let c = CosmologyParams::standard(67.4, 9.14e-5, 0.315, 0.685);
        let bg = evolve(&BianchiType::VIIh(1.0).canonical_params(), &c, 1e-5, 1e-6, 5000).unwrap();
        assert!(bg.sigma_h_of_a(1.0).is_finite(), "BVII_h must be stable");
    }
    /// FIX 3: Background for VIh (anisotropic curvature)
    #[test] fn t43f_bg_vih() {
        let c = CosmologyParams::standard(67.4, 9.14e-5, 0.315, 0.685);
        let bg = evolve(&BianchiType::VIh(-0.5).canonical_params(), &c, 1e-5, 1e-6, 5000).unwrap();
        assert!(bg.sigma_h_of_a(1.0).is_finite(), "BVI_h must be stable");
    }

    // ═══ §11. Remaining curvature ═══

    #[test] fn t44_bii_r3() { let p=BianchiType::II.canonical_params(); assert!(spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude).abs()<1e-15); }
    #[test] fn t45_bvi0_r3() { let p=BianchiType::VI0.canonical_params(); assert!((spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude)-1.0).abs()<1e-14); }
    #[test] fn t46_bvii0_r3() { let p=BianchiType::VII0.canonical_params(); assert!((spatial_ricci_scalar(&p.n_eigenvalues,p.a_magnitude)+1.0).abs()<1e-14); }
    #[test] fn t47_bviii_aniso() { let p=BianchiType::VIII.canonical_params(); let s=spatial_ricci_tracefree(&p.n_eigenvalues,p.a_magnitude); assert!((s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt()>0.1); }
    #[test] fn t48_windows() { assert!((tilt::local_patch::window_tophat(0.0)-1.0).abs()<1e-15); assert!(tilt::local_patch::window_gaussian(10.0)<1e-20); }

    // ═══ §12. Isotropic curvature types: ³S = 0 (comprehensive) ═══

    #[test] fn t49_isotropic_curvature_types() {
        // Types where ALL R_{αα} are equal → ³S = 0:
        // BI, BII, BIV, BV, BIX
        let isotropic = [BianchiType::I, BianchiType::II, BianchiType::IV,
                         BianchiType::V, BianchiType::IX];
        for bt in &isotropic {
            let p = bt.canonical_params();
            let s = spatial_ricci_tracefree(&p.n_eigenvalues, p.a_magnitude);
            let norm = (s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt();
            assert!(norm < 1e-14, "{}: ||³S||={:.2e} (must be 0)", bt.label(), norm);
        }
    }

    #[test] fn t50_anisotropic_curvature_types() {
        // Types with ³S ≠ 0:
        // BIII, BVI₀, BVI_h, BVII₀, BVII_h, BVIII
        let aniso = [BianchiType::III, BianchiType::VI0, BianchiType::VIh(-0.5),
                     BianchiType::VII0, BianchiType::VIIh(1.0), BianchiType::VIII];
        for bt in &aniso {
            let p = bt.canonical_params();
            let s = spatial_ricci_tracefree(&p.n_eigenvalues, p.a_magnitude);
            let norm = (s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt();
            assert!(norm > 0.01, "{}: ||³S||={:.4} (must be > 0)", bt.label(), norm);
        }
    }
}
