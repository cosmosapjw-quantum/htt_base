from source_conditioned_readiness import run

def test_source_window_values():
 d=run();assert len(d['P1_S02']['H_eff_working_km_s_Mpc'])==4
 assert abs(d['P1_S02']['H_eff_working_km_s_Mpc'][0]-75.16799577028824)<1e-10

def test_S02_physics_blocked_even_with_CF4():
 d=run();assert d['P1_S02']['physical_Q_Pi_F_status']=='INPUT_BLOCKED'
 assert d['P1_S02']['physical_x_C_defined_on_this_sample'] is False

def test_L01_spectral_not_frobenius():
 d=run()['P2_L01'];assert abs(d['K_T_spectral_norm']-2.4328695605629203)<1e-12
 assert d['K_T_frobenius_norm']>d['K_T_spectral_norm']

def test_same_sky_and_missing_pol():
 d=run()['P2_L01'];assert d['independent_cosmic_sky_count']==1
 assert d['SMICA_noSZ_FULL_polarized_source']=='ABSENT_NOT_ZERO'
 assert d['native_P_sky_mask_spin2_ell6_8_response']=='UNVERIFIED'
