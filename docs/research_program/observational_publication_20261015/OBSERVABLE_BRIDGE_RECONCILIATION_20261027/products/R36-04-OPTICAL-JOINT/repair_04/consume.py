#!/usr/bin/env python3
"""Reproduce source-bound conditional optical response tables and figures."""
from pathlib import Path
import csv
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from optical_joint import (B3, KAPPA, boost_chart, boost_dipole, invert_boost,
                           joint_budget, joint_test, lift_matrix, m_matrix,
                           raw_to_target, residual_covariance, stf3)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
OBS = HERE.parents[2]
P6 = ROOT / 'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025'
SOURCE = P6 / 'evidence/research/latest_results.json'
MANIFEST = OBS / 'EVIDENCE_MANIFEST.json'
EXPECTED = '83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def directions(count=96):
    i = np.arange(count)
    z = 1 - 2 * (i + .5) / count
    phi = i * np.pi * (3 - np.sqrt(5))
    r = np.sqrt(1 - z*z)
    return np.column_stack((r*np.cos(phi), r*np.sin(phi), z))


def run():
    if sha(MANIFEST) != EXPECTED:
        raise RuntimeError('frozen source manifest identity changed')
    data = json.loads(SOURCE.read_text())
    q = data['cf4_calibration_quotient']
    s = np.asarray(q['apparent_tensor_dimensionless'], float)
    b = np.asarray(q['apparent_b_dimensionless'], float)
    if not np.isclose(np.linalg.norm(s), 0.03265680189321492, rtol=0, atol=1e-14):
        raise RuntimeError('corrected dimensionless P6 statistic changed')
    if not np.isclose(np.linalg.norm(b), np.linalg.norm(s), rtol=0, atol=1e-14):
        raise RuntimeError('P6 basis is inconsistent')
    l = lift_matrix(s)
    m = m_matrix(s)
    if not np.allclose(l.T @ l, m, rtol=2e-14, atol=1e-18):
        raise RuntimeError('retained M identity fails')
    n = directions()
    d = np.array([.012, -.009, .006])  # declared synthetic coefficient
    weights = 1 + .4 * n[:, 2]
    # Correlated source-level covariance is a deterministic *design* control.
    u = np.linspace(-1, 1, len(n))
    source_c = 1e-8 * (np.eye(len(n)) + .2 * np.outer(u, u))
    response = raw_to_target(n, s, d, weights, source_c)
    c10 = response['summary_covariance']
    c7 = residual_covariance(c10, s)
    if np.linalg.norm(c10[:3, 3:]) == 0:
        raise RuntimeError('synthetic shared-source cross covariance was discarded')
    # The design's linear response is K[-kappa V/(1+q)]; verify by central perturbation.
    step = 1e-6
    plus = raw_to_target(n, s, d + np.array([step, 0, 0]), weights)['summary']
    minus = raw_to_target(n, s, d - np.array([step, 0, 0]), weights)['summary']
    if not np.allclose((plus-minus)/(2*step), response['jacobian_d_S'][:, 0], rtol=2e-7, atol=1e-9):
        raise RuntimeError('raw-to-target response derivative fails')
    # Exact L_S image plus perpendicular signal: both components consume one B=1.
    proj = l @ np.linalg.solve(m, l.T)
    u7 = np.eye(7)[:, 0]
    perp = (np.eye(7)-proj) @ u7
    perp /= np.linalg.norm(perp)
    pdir = l @ np.array([1., 0., 0.])
    pdir /= np.linalg.norm(pdir)
    o_counter = KAPPA*l @ d + .8*(perp+pdir)
    counter = joint_test(o_counter, s, d, 1.0)
    if counter['compatible'] or not np.isclose(counter['score'], np.sqrt(1.28), atol=2e-13):
        raise RuntimeError('0.8/0.8 shared-budget falsifier failed')
    profiled = joint_test(o_counter, s, d, 1.0, e_d=.8/(KAPPA*np.linalg.norm(l[:, 0])))
    zero = joint_test(np.zeros(7), np.zeros((3,3)), d, 0)
    repaired_interior = joint_test(np.zeros(7), np.diag([.001,-.001,0]),
                                   np.array([.001,0,0]), 1e-8, e_d=.002, d_max=.01)
    underflow_zero = joint_test(np.r_[1e-200,np.zeros(6)], np.zeros((3,3)),
                                 np.zeros(3), 0)
    underflow_nonzero = joint_test(np.r_[1e-200,np.zeros(6)],
                                    np.diag([1e-200,-1e-200,0]), np.zeros(3), 0)
    if not repaired_interior['compatible'] or repaired_interior['residual_norm'] != 0:
        raise RuntimeError('reviewed interior witness false rejection persists')
    if underflow_zero['compatible'] or underflow_nonzero['compatible'] or underflow_nonzero['branch'] != 'INVERTIBLE_S':
        raise RuntimeError('reviewed underflow false acceptance persists')
    narrow_s=np.diag([.001,-.001,0.])
    narrow_k=KAPPA*lift_matrix(narrow_s)
    rf1=joint_test(narrow_k@np.array([.0100005,0,0]),narrow_s,
                   np.array([.01,0,0]),5.606717652542515e-10,e_d=1e-6,d_max=.1)
    rf2=joint_test(narrow_k@np.array([.0001000000009,0,0]),narrow_s,
                   np.zeros(3),1.0092091825422658e-15,e_d=.1,d_max=.0001)
    if not rf1['compatible'] or rf1['certified_upper_bound']>rf1['budget']:
        raise RuntimeError('RF1 feasible witness false rejection persists')
    if rf2['compatible'] or rf2['certified_lower_bound']<=rf2['budget']:
        raise RuntimeError('RF2 physical boundary false acceptance persists')
    ncf_center=np.array([.125,1e-60,0.])
    ncf_empty=joint_test(narrow_k@ncf_center,narrow_s,ncf_center,
                         1e-7,e_d=0,d_max=.125)
    ncf_tangent=joint_test(np.zeros(7),narrow_s,np.array([.25,0,0]),
                           .001,e_d=.125,d_max=.125)
    ncf_sqrt3=joint_test(np.r_[1.,1.,1.,np.zeros(4)],np.zeros((3,3)),
                         np.zeros(3),2)
    if ncf_empty['compatible'] or not ncf_empty['physical_set_empty']:
        raise RuntimeError('NCF1 exact direct singleton was falsely accepted')
    if not ncf_tangent['compatible'] or ncf_tangent['profiled_d']!=[.125,0,0]:
        raise RuntimeError('NCF3 representable tangent witness lost')
    if not ncf_sqrt3['certified_upper_bound']>np.sqrt(3):
        raise RuntimeError('NCF2 upper endpoint was not rounded outward')
    epf_center=np.array([np.nextafter(.25,0.),0.,0.])
    epf_zero=joint_test(np.zeros(7),np.zeros((3,3)),epf_center,.001,
                        e_d=.125,d_max=.125)
    epf_shear=joint_test(np.zeros(7),narrow_s,epf_center,.001,
                         e_d=.125,d_max=.125)
    epf_exterior=joint_test(np.zeros(7),narrow_s,
                            np.array([np.nextafter(.25,np.inf),0.,0.]),
                            .001,e_d=.125,d_max=.125)
    if not epf_zero['compatible'] or not epf_shear['compatible'] or not epf_exterior['physical_set_empty']:
        raise RuntimeError('EPF1 near-tangent closed-ball construction failed')
    # Source-level finite-z ratio has O(z) magnitude change.
    a1 = np.einsum('ijk,ni,nj,nk->n', B3[0], n, n, n)
    zvals = np.array([.02, .01, .005])
    shifts = []
    base_y = response['raw_magnitude']
    for z in zvals:
        perturb = KAPPA*np.log1p(z*a1)
        shifts.append(float(np.linalg.norm(response['estimator'][3:] @ perturb)))
    ratio = [shifts[i]/shifts[i+1] for i in range(2)]
    if not all(1.85 < x < 2.15 for x in ratio):
        raise RuntimeError('finite-z magnitude order not linear')
    beta = np.array([.003, -.002, .001])
    db = boost_dipole(s, beta)
    if not np.allclose(invert_boost(s, db), beta, rtol=1e-13, atol=1e-15):
        raise RuntimeError('moving-observer inverse failed')
    gamma = 1.004
    chart = boost_chart(np.array([0., .01]), np.array([0., 1.]), gamma)
    if not np.isclose(chart['d_l_star_tilde'][1], gamma*chart['d_l_star'][1]):
        raise RuntimeError('corrected chart boost rule failed')
    if not np.isclose(chart['z_tilde'][0], 1/gamma-1):
        raise RuntimeError('vertex redshift shift was lost')
    # H7 coefficients are reported symbolically; no unsupported physical radii.
    budget_unit = joint_budget(.1, 0, 0, 0, 0, 1)
    table = [
        ('P6 apparent dimensionless S norm', float(np.linalg.norm(s)), 'saved corrected P6 sufficient statistic'),
        ('min singular value of L_S', float(np.linalg.svd(l)[1][-1]), 'dimensionless inverse conditioning'),
        ('max singular value of L_S', float(np.linalg.svd(l)[1][0]), 'dimensionless response'),
        ('min eigenvalue M_S', float(np.linalg.eigvalsh(m)[0]), 'dimensionless squared response'),
        ('synthetic raw direct dipole norm', float(np.linalg.norm(response['summary'][:3])), 'finite selected magnitude estimator only'),
        ('synthetic raw octupole norm', float(np.linalg.norm(response['summary'][3:])), 'finite selected magnitude estimator only'),
        ('synthetic direct/octupole cross-cov norm', float(np.linalg.norm(c10[:3,3:])), 'declared design covariance'),
        ('synthetic joint residual covariance trace', float(np.trace(c7)), 'declared design covariance'),
        ('0.8/0.8 separate component', .8, 'unit mathematical budget'),
        ('0.8/0.8 joint score', counter['score'], 'rejects shared unit ball'),
        ('reviewed feasible witness residual norm', repaired_interior['residual_norm'], 'profiled direct dipole, norm-bound certified'),
        ('RF1 narrow-ball upper bound',rf1['certified_upper_bound'],'feasible witness, declared budget 5.606717652542515e-10'),
        ('RF2 physical-boundary lower bound',rf2['certified_lower_bound'],'valid rejection, declared budget 1.0092091825422658e-15'),
        ('NCF1 exact-ball verdict',int(ncf_empty['physical_set_empty']),'singleton center has positive 1e-120 squared excess'),
        ('NCF3 tangent witness coordinate',ncf_tangent['profiled_d'][0],'exact representable intersection singleton'),
        ('NCF2 sqrt3 lower bound',ncf_sqrt3['certified_lower_bound'],'directed downward, seven-component fixed objective'),
        ('NCF2 sqrt3 upper bound',ncf_sqrt3['certified_upper_bound'],'directed upward, seven-component fixed objective'),
        ('EPF1 one-ulp overlap shear residual upper',epf_shear['certified_upper_bound'],'verified original-ball witness, B=.001'),
        ('EPF1 adjacent exterior verdict',int(epf_exterior['physical_set_empty']),'exact binary64 squared-ball emptiness'),
        ('reviewed S=0 tiny nonzero residual norm', underflow_zero['residual_norm'], 'zero budget rejects'),
        ('reviewed S nonzero tiny residual norm', underflow_nonzero['residual_norm'], 'invertible branch, zero budget rejects'),
        ('synthetic finite-z shift z=0.02', shifts[0], 'source-level selected estimator'),
        ('synthetic finite-z shift z=0.01', shifts[1], 'source-level selected estimator'),
        ('synthetic finite-z shift z=0.005', shifts[2], 'source-level selected estimator'),
    ]
    with (HERE/'TABLE.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['quantity', 'value', 'scope'])
        writer.writerows(table)
    plt.rcParams.update({'font.size': 10, 'pdf.fonttype': 42})
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4), layout='constrained')
    ax[0].bar(['perpendicular','parallel','joint'], [.8,.8,counter['score']], color=['#488bb1','#d28b55','#6a4c93'])
    ax[0].axhline(1, color='black', linewidth=1, linestyle='--')
    ax[0].set_ylabel('Score / one declared unit budget')
    ax[0].set_title('Exact seven-component split')
    ax[1].imshow(response['jacobian_d_S'], cmap='coolwarm', aspect='auto')
    ax[1].set_xlabel('Input d (3) and S (5)')
    ax[1].set_ylabel('Raw-fit direct d (3) and STF3 O (7)')
    ax[1].set_title('Selected-source response Jacobian')
    fig.savefig(HERE/'JOINT_RESPONSE.pdf')
    fig.savefig(HERE/'JOINT_RESPONSE.svg')
    plt.close(fig)
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4), layout='constrained')
    ax[0].imshow(c10, cmap='viridis', aspect='equal')
    ax[0].axhline(2.5, color='white', linewidth=.8)
    ax[0].axvline(2.5, color='white', linewidth=.8)
    ax[0].set_title('Full synthetic direct/STF3 covariance')
    ax[1].loglog(zvals, shifts, 'o-', label='selected STF3 magnitude shift')
    ax[1].loglog(zvals, shifts[-1]*zvals/zvals[-1], '--', label='linear reference')
    ax[1].set_xlabel('Finite redshift z')
    ax[1].set_ylabel('STF3 shift (mag)')
    ax[1].legend()
    fig.savefig(HERE/'SOURCE_AND_FINITE_Z.pdf')
    fig.savefig(HERE/'SOURCE_AND_FINITE_Z.svg')
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.2,4.4),layout='constrained')
    for x,(label,case,color) in enumerate([('RF1 feasible',rf1,'#488bb1'),('RF2 excluded',rf2,'#d28b55'),
                                           ('NCF3 tangent',ncf_tangent,'#6a4c93'),('NCF2 fixed',ncf_sqrt3,'#367c60')]):
        budget=case['budget']
        ax.vlines(x,case['certified_lower_bound']/budget,
                  case['certified_upper_bound']/budget,color=color,linewidth=5)
        ax.scatter([x],[case['certified_lower_bound']/budget],marker='_',s=140,color=color)
        ax.scatter([x],[case['certified_upper_bound']/budget],marker='_',s=140,color=color)
    ax.axhline(1,color='black',linestyle='--',linewidth=1,label='unchanged budget')
    ax.set_xticks([0,1,2,3],['RF1 feasible','RF2 excluded','NCF3 tangent','NCF2 fixed'])
    ax.set_ylabel('Certified residual interval / declared budget')
    ax.set_yscale('symlog',linthresh=.1)
    ax.set_ylim(-.05,3)
    ax.legend()
    ax.set_title('Original-ball witness and seven-component bound')
    fig.savefig(HERE/'NORM_BOUND_DECISION.pdf')
    fig.savefig(HERE/'NORM_BOUND_DECISION.svg')
    plt.close(fig)
    result = {
        'packet_id': 'a3c0cf3a91f1e9e9b42655aae9d807b977a9b429f41740a6b5a19a505156def8',
        'base_packet_id': 'b5bac779afef84c0ac243fe864feb7624de29c25e3d50b09837a0fa5fa078ebd',
        'base_candidate_identity': 'sha256:ec4421a423a87889cc268c65d551a772846ca93298b028d08143201ec824137b',
        'repair_plan_identity': 'OWNER_AUTHORIZED_IN_NEXT_033',
        'task_id': 'R36-04-OPTICAL-JOINT', 'agent_id': '/root/rc_9441945b45b2b786',
        'requested_runtime': {'model': 'gpt-6-sol', 'reasoning_effort': 'high'},
        'observed_runtime': 'UNKNOWN',
        'owner': 'common optical response; obsstat feature extraction',
        'scope': 'solver-free source-level optical joint response and conditional CF4 sufficient-statistic consumer',
        'transfer_source': 'none; saved apparent CF4 proxy is not native transfer',
        'sky_support_status': 'synthetic selected 96-direction design; no CF4 same-event sky qualification',
        'null_mock_status': 'no empirical null or coverage law',
        'covariance_status': 'full joint covariance exercised on synthetic source law; actual CF4 direct/octupole joint covariance unavailable',
        'claim_tier': 'C0_CONDITIONAL_METHOD',
        'acceptance_met': False, 'candidate_status': 'PROPOSED_PENDING_INDEPENDENT_REVIEW',
        'qualified_products': ['optical_joint_response'],
        'input_identity': 'sha256:' + EXPECTED,
        'source': {'manifest_sha256': sha(MANIFEST), 'p6_saved_results_sha256': sha(SOURCE),
                   'p6_tensor_norm': q['tensor_frobenius_norm'],
                   'p6_working_covariance_scope': q['working_covariance_scope']},
        'numerical_tolerances': {'source_tensor_atol': 1e-14, 'M_identity_rtol': 2e-14,
                                 'jacobian_central_difference_rtol': 2e-7,
                                 'joint_score_atol': 2e-13,
                                 'source': 'double precision saved P6 data and finite difference step 1e-6; no physical acceptance radius'},
        'counterexample': counter, 'direct_uncertainty_profile_example': profiled,
        'reviewed_numeric_repair_controls': {'interior_feasible_witness':repaired_interior,
                                              'S_zero_underflow_rejection':underflow_zero,
                                              'S_nonzero_underflow_rejection':underflow_nonzero},
        'norm_bound_repair_controls': {'RF1_feasible_narrow_ball':rf1,
                                       'RF2_excluded_physical_boundary':rf2,
                                       'RF3_large_residual': 'TYPED_NUMERIC_RANGE_IN_TEST'},
        'exact_set_and_directed_certificate_controls': {'NCF1_empty_singleton':ncf_empty,
            'NCF2_sqrt3_fixed_objective':ncf_sqrt3,'NCF3_representable_tangent':ncf_tangent,
            'NCF2_rational_endpoint_oracles':'IN_FOCUSED_TESTS'},
        'available_witness_controls': {'EPF1_zero_response':epf_zero,
            'EPF1_nonzero_response':epf_shear,'EPF1_adjacent_exterior':epf_exterior},
        'S_zero_example': zero, 'uncertain_S_coefficient': float(KAPPA*np.sqrt(3/5)),
        'H7_example_angular_only_epsilon_0p1': budget_unit,
        'finite_z_example': {'z': zvals.tolist(), 'STF3_norm': shifts, 'doubling_ratios': ratio},
        'synthetic_source_design': {'rows': len(n), 'rank': 16, 'weights': '1+0.4 n_z',
                                    'raw_covariance': '1e-8 (I+0.2 uu^T), u=linspace(-1,1,96); mathematical control only',
                                    'full_signed_summary': response['summary'].tolist(),
                                    'jacobian_d_S': response['jacobian_d_S'].tolist(),
                                    'summary_covariance': c10.tolist(), 'residual_covariance': c7.tolist()},
        'moving_observer_example': {'beta_synthetic': beta.tolist(), 'd_boost': db.tolist(),
                                    'gamma_synthetic': gamma, 'shifted_vertex_z': float(chart['vertex_z_tilde'])},
        'undefined_sectors': {'CF4_direct_dipole_physical_referent': 'UNKNOWN',
                              'CF4_direct_octupole_joint_covariance': 'UNAVAILABLE',
                              'physical_Bz_Bsel_eS_eO': 'UNAVAILABLE',
                              'x_Q_F_Pi_G': 'UNDEFINED_WITHOUT_OWNER_SPECIFIC_INPUTS'},
        'scientific_interpretation': 'A conditional joint response can reject a declared shared error class; the saved CF4 tensor is an apparent dimensionless input, not evidence of acceleration, boost, shear, or a Bianchi family.'}
    (HERE/'RESULT.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result


if __name__ == '__main__':
    r = run()
    print(json.dumps({'status': r['candidate_status'], 'counterexample_score': r['counterexample']['score'],
                      'P6_norm': r['source']['p6_tensor_norm']}))
