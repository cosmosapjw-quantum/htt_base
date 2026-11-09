from __future__ import annotations
import numpy as np
from scripts.r48 import bianchi_fivevar_identifiability_mock as m

def test_class_a_trace_shift_kernel_and_rank_two():
 S=m.stf([.2,-.05,.1,.08,.06]);n=np.array([.3,-.2,.7]);J=m.JA(S)
 for c in (-2.,-.1,0.,1.,3.5): assert np.allclose(m.momentum_A(n,S),m.momentum_A(n+c*np.ones(3),S),atol=1e-14,rtol=0)
 assert np.linalg.matrix_rank(J)==2 and np.linalg.norm(J@np.ones(3))<1e-14
def test_class_b_jacobian_and_local_inverse():
 S=m.stf([.2,-.05,.1,.08,.06]);p=np.array([.7,.4,.2]);J=m.JB(S)
 assert np.linalg.matrix_rank(J)==3 and np.allclose(np.linalg.solve(J,m.momentum_B(p,S)),p,atol=1e-13)
def test_exact_tilt_inversion():
 M=np.array([0.,-.08,.1]);b=m.beta_from_M(M);G=1/np.sqrt(1-b@b)
 assert np.linalg.norm(b)<1 and np.allclose(G**2*b,M,atol=1e-14)
def test_curvature_pair_and_presentation_controls():
 S=m.stf([.2,-.05,.1,.08,.06]);n0=np.array([1.,0,0]);n1=np.array([2.,1,1])
 assert np.allclose(m.momentum_A(n0,S),m.momentum_A(n1,S),atol=1e-14)
 assert np.allclose(np.sort(m.ricci_A(n0)),[-.5,-.5,.5]) and np.allclose(np.sort(m.ricci_A(n1)),[0,0,2])
 assert np.allclose(m.ricci_A([0,0,0]),m.ricci_A([0,2,2])) and np.allclose(m.ricci_B(1,0,0),m.ricci_B(1,2,2))
def test_monte_carlo_five_view_and_information_contract():
 r=m.run_experiment(n_rep=4000,n_post=1500,n_null=256);L=r['likelihood'];H=r['HTT_five_views']
 assert L['kinematic_only_label_information_nats']==0 and abs(L['curvature_oracle_label_information_nats']-.4789)<.03
 assert L['target_kl_loss_full_HTT_with_x_geometry_score_nats']==0
 assert abs(L['target_kl_loss_ablation_no_geometry_carrier_nats']-L['expected_target_posterior_kl_full_data_nats'])<1e-12
 assert L['nuisance_projection']['label_rank_after_parallel_unbounded_calibration_nuisance']==0 and L['randomized_rank_SBC']['p_value']>.01
 assert H['shared_sample_ids']==1500 and H['G_F']['posterior_cross_window_covariance_shape']==[15,15] and min(H['F']['beta_support'])>=0
