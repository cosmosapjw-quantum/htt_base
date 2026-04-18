// BC-07: PSTF Hierarchy Integration Test Suite.
// Comprehensive tests for the full PSTF engine (BC-01 through BC-06).
// 42 tests total (> 35 minimum).

#[cfg(test)]
mod pstf_integration {
    use crate::pstf::tensor;
    use crate::pstf::coupling;
    use crate::pstf::hierarchy::{PSTFHierarchy, Species, HierarchyBackground, spherical_bessel_j};
    use crate::pstf::hierarchy_matrix::{self, HierarchyRegime};
    use crate::pstf::m_decomposition::{self, MmodeHierarchy, cg_kappa_m};
    use crate::collision::thomson;
    use crate::collision::polarisation;
    use crate::collision::baryon_photon;
    use crate::collision::tight_coupling::{self, TCAState, TCABackground};

    fn bg_free(k: f64) -> HierarchyBackground {
        HierarchyBackground { a_h: 0.0, k, sigma_h: 0.0, kappa_dot: 0.0, v_b: 0.0, pol_source: 0.0 }
    }
    fn bg_flrw(k: f64, kd: f64) -> HierarchyBackground {
        HierarchyBackground { a_h: 0.0, k, sigma_h: 0.0, kappa_dot: kd, v_b: 0.0, pol_source: 0.0 }
    }
    fn bg_bianchi(k: f64, sh: f64, ah: f64) -> HierarchyBackground {
        HierarchyBackground { a_h: ah, k, sigma_h: sh, kappa_dot: 0.0, v_b: 0.0, pol_source: 0.0 }
    }
    fn bg_full(k: f64, sh: f64, ah: f64, kd: f64, vb: f64) -> HierarchyBackground {
        HierarchyBackground { a_h: ah, k, sigma_h: sh, kappa_dot: kd, v_b: vb, pol_source: 0.0 }
    }

    // ═══ §1. STF ALGEBRA (BC-01) ═══
    #[test] fn i01_stf_trace_zero() {
        let a=[[1.0,0.5,0.2],[0.5,2.0,0.3],[0.2,0.3,3.0]];
        let p=tensor::stf_project_rank2(&a); assert!(tensor::trace_3x3(&p).abs()<1e-14);
    }
    #[test] fn i02_angular_average_ee() {
        let avg=tensor::angular_average_ee();
        assert!((avg[0][0]-1.0/3.0).abs()<1e-14); assert!(avg[0][1].abs()<1e-14);
    }
    #[test] fn i03_stf_symmetric() {
        let a=[[1.0,0.5,0.2],[0.5,2.0,0.3],[0.2,0.3,3.0]];
        assert!(tensor::is_symmetric_3x3(&tensor::stf_project_rank2(&a),1e-14));
    }
    // ═══ §2. COUPLING COEFFICIENTS (BC-02) ═══
    #[test] fn i04_fs_down_positive() { for l in 1..20{assert!(coupling::free_streaming_down(l)>0.0);} }
    #[test] fn i05_fs_up_positive() { for l in 0..20{assert!(coupling::free_streaming_up(l)>0.0);} }
    #[test] fn i06_shear_down_zero_low() { assert_eq!(coupling::shear_coupling_down(0),0.0); assert_eq!(coupling::shear_coupling_down(1),0.0); }
    #[test] fn i07_cg_m0() { for l in 1..15{let k=cg_kappa_m(l,0);let e=l as f64/((4*l*l-1)as f64).sqrt();assert!((k-e).abs()<1e-14);} }
    #[test] fn i08_cg_vanish() { for l in 1..10{assert!(cg_kappa_m(l,l as i32).abs()<1e-15);} }
    // ═══ §3. FREE-STREAMING → BESSEL (BC-03) ═══
    #[test] fn i09_bessel_exact() { for &x in &[0.1f64,1.0,5.0,10.0,20.0]{assert!((spherical_bessel_j(0,x)-x.sin()/x).abs()<1e-12);} }
    #[test] fn i10_bessel_origin() { assert!((spherical_bessel_j(0,0.0)-1.0).abs()<1e-15); }
    #[test] fn i11_free_stream() {
        let mut h=PSTFHierarchy::new(25,Species::Neutrino,false); h.set_adiabatic_ic(1.0);
        let bg=bg_free(0.05); let (eta,n)=(80.0,40000);
        for _ in 0..n{h.step_rk4(&bg,eta/n as f64);}
        let j0=spherical_bessel_j(0,0.05*eta);
        assert!((h.state[0]-j0).abs()/j0.abs().max(1e-10)<0.05);
    }
    #[test] fn i12_power_cascade() {
        let mut h=PSTFHierarchy::new(25,Species::Neutrino,false); h.set_adiabatic_ic(1.0);
        let bg=bg_free(0.1); for _ in 0..25000{h.step_rk4(&bg,0.002);}
        let low:f64=h.state[0..3].iter().map(|x|x*x).sum();
        let high:f64=h.state[3..10].iter().map(|x|x*x).sum();
        assert!(high>0.01*low,"Power must cascade");
    }
    // ═══ §4. THOMSON COLLISION (BC-04) ═══
    #[test] fn i13_energy_cons() { let f=vec![1.0,0.5,0.2,0.1,0.05]; assert!(thomson::thomson_collision(&f,100.0,0.3,0.5)[0].abs()<1e-14); }
    #[test] fn i14_momentum_cons() { let(f1,vb,kd,r)=(0.02,0.01,80.0,0.5); let c1=-kd*(f1-vb); let cb=baryon_photon::baryon_collision_term(vb,f1,kd,1.0/r); assert!((c1+r*cb).abs()<1e-13); }
    #[test] fn i15_thomson_damp() { let f=vec![0.0,0.0,0.0,0.0,0.0,1.0]; assert!((thomson::thomson_collision(&f,100.0,0.0,0.0)[5]+100.0).abs()<1e-12); }
    #[test] fn i16_emode_src() { let g=vec![0.0,0.0,0.0]; assert!((polarisation::emode_collision(&g,0.1,100.0)[0]-1.0).abs()<1e-12); }
    #[test] fn i17_theta4() { assert_eq!(thomson::THETA4_BRIDGE_COEFFICIENT,6.0); }
    #[test] fn i18_pi_comp() { assert!((polarisation::polarisation_pi(0.1,0.02,0.03)-0.15).abs()<1e-15); }
    // ═══ §5. TCA (BC-05) ═══
    #[test] fn i19_tca_cs0() { assert!((tight_coupling::tca_sound_speed_sq(0.0)-1.0/3.0).abs()<1e-15); }
    #[test] fn i20_tca_cs06() { assert!((tight_coupling::tca_sound_speed_sq(0.6)-1.0/4.8).abs()<1e-15); }
    #[test] fn i21_tca_halfp() {
        let mut s=TCAState{theta0:1.0,v_b:0.0,delta_b:0.0};
        let bg=TCABackground{a_h:0.0,k:0.1,r_ratio:0.0,kappa_dot:1e6,sigma_h:0.0,psi:0.0,phi_dot:0.0};
        let hp=std::f64::consts::PI/(0.1*tight_coupling::tca_sound_speed_sq(0.0).sqrt());
        for _ in 0..10000{tight_coupling::tca_step_rk4(&mut s,&bg,hp/10000.0);}
        assert!((s.theta0+1.0).abs()<0.05);
    }
    #[test] fn i22_slip_flrw() { assert_eq!(tight_coupling::slip_term_f2(0.0,1000.0,100.0),0.0); }
    #[test] fn i23_slip_bi() { let f2=tight_coupling::slip_term_f2(1e-5,1000.0,100.0); assert!((f2-(8.0/15.0)*1e-5*0.1).abs()<1e-20); }
    #[test] fn i24_switch_cts() { let t=TCAState{theta0:0.5,v_b:0.01,delta_b:-0.005}; let f=tight_coupling::switch_to_full(&t,20,0.0,1000.0,100.0); assert!((f[0]-0.5).abs()<1e-15); assert!((f[1]-0.01).abs()<1e-15); for l in 3..=20{assert_eq!(f[l],0.0);} }
    #[test] fn i25_valid_early() { assert!(tight_coupling::tca_is_valid(1e6,100.0,50.0)); }
    #[test] fn i26_invalid_late() { assert!(!tight_coupling::tca_is_valid(10.0,100.0,50.0)); }
    // ═══ §6. m-MODE (BC-06) ═══
    #[test] fn i27_decomp_recon() { let f=vec![1.0,0.5,0.2,0.08,0.03,0.01]; let m=m_decomposition::decompose_axisymmetric(&f,5); let r=m_decomposition::reconstruct_axisymmetric(&m,5); for l in 0..6{assert!((r[l]-f[l]).abs()<1e-15);} }
    #[test] fn i28_only_m0() { let f=vec![1.0,0.5,0.1]; assert_eq!(m_decomposition::active_m_modes(&m_decomposition::decompose_axisymmetric(&f,2),1e-30),vec![0]); }
    #[test] fn i29_total_dof() { assert_eq!(m_decomposition::total_dof(10),121); }
    #[test] fn i30_dim_m2() { assert_eq!(MmodeHierarchy::new(2,10).dim(),9); }
    // ═══ §7. CROSS-MODULE INTEGRATION ═══
    #[test] fn i31_flrw_no_shear() { let mut h=PSTFHierarchy::new(10,Species::Photon,false); h.state[0]=1.0; assert!(h.rhs(&bg_flrw(0.1,0.0))[2].abs()<1e-15); }
    #[test] fn i32_bianchi_shear() { let mut h=PSTFHierarchy::new(10,Species::Photon,true); h.state[0]=1.0; assert!(h.rhs(&bg_bianchi(0.0,0.001,100.0))[2].abs()>1e-6); }
    #[test] fn i33_trunc_conv() {
        let(k,eta,n)=(0.05,40.0,20000usize); let mut v=vec![];
        for &lm in &[10usize,20,30]{let mut h=PSTFHierarchy::new(lm,Species::Neutrino,false); h.set_adiabatic_ic(1.0); for _ in 0..n{h.step_rk4(&bg_free(k),eta/n as f64);} v.push(h.state[0]);}
        assert!((v[1]-v[2]).abs()/v[2].abs().max(1e-10)<0.01);
    }
    #[test] fn i34_tca_full_stable() {
        let t=TCAState{theta0:1.0,v_b:0.0,delta_b:0.0}; let fs=tight_coupling::switch_to_full(&t,20,1e-5,500.0,100.0);
        let mut h=PSTFHierarchy::new(20,Species::Photon,true); h.state=fs;
        for _ in 0..100{h.step_rk4(&bg_full(0.1,1e-5,100.0,50.0,0.0),0.01);}
        assert!(h.state.iter().fold(0.0f64,|a,&v|a.max(v.abs()))<10.0);
    }
    #[test] fn i35_nu_no_thomson() { let mut h=PSTFHierarchy::new(10,Species::Neutrino,false); h.state[3]=1.0; assert!(h.rhs(&bg_flrw(0.0,100.0))[3].abs()<1e-15); }
    #[test] fn i36_photon_thomson() { let mut h=PSTFHierarchy::new(10,Species::Photon,false); h.state[3]=1.0; assert!((h.rhs(&bg_flrw(0.0,100.0))[3]+100.0).abs()<1e-12); }
    #[test] fn i37_cs_recomb() { assert!((baryon_photon::sound_speed(0.6)-1.0/(3.0*1.6f64).sqrt()).abs()<1e-14); }
    #[test] fn i38_r_ratio() { let r=baryon_photon::baryon_photon_ratio(0.049,6.5e-5,1.0/1091.0); assert!(r>0.4&&r<0.8); }
    // ═══ §8. COUPLING MATRIX STRUCTURE ═══
    #[test] fn i39_flrw_tridiag() { assert!(hierarchy_matrix::verify_flrw_tridiagonal(10).0); }
    #[test] fn i40_bi_pentadiag() { assert!(hierarchy_matrix::verify_bianchi_pentadiagonal(10).0); }
    #[test] fn i41_bw_flrw() { assert_eq!(hierarchy_matrix::matrix_bandwidth(10,HierarchyRegime::Flrw),1); }
    #[test] fn i42_bw_bi() { assert_eq!(hierarchy_matrix::matrix_bandwidth(10,HierarchyRegime::BianchiHomogeneous),2); }
}
