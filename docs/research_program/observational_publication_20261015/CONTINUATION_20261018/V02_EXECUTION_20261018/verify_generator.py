"""Check saved response against the unchanged analytic first-order source oracle.

This consumes trusted repository Git source at its declared historical identity;
it does not merge or change that source, nor rerun the finite experiments.
"""
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from v02_response import beam_layout, design, sphere_rule

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
COMMIT = 'c2889730d2b5e5b778951f15e8f09afd55bed4e3'
PATH = 'htt/obsstat/processed_boost_theory_bridge.py'


def main():
    target = HERE/'results/V02_ANALYTIC_GENERATOR_CHECK.json'
    if target.exists(): raise FileExistsError('CREATE_ONLY_ANALYTIC_CHECK')
    code = subprocess.check_output(['git', 'show', COMMIT+':'+PATH], cwd=REPO)
    namespace = {'__name__':'historical_analytic_boost_oracle'}
    exec(compile(code, COMMIT+':'+PATH, 'exec'), namespace)
    with np.load(HERE/'results/V02_FINITE_RESPONSE.npz', allow_pickle=False) as z:
        source = z['defined_source_microK'][:, 0]
        beam = z['actual_INT_BEAM']
        transfer = z['transfer_low32_full289']
        finite_difference = z['jacobian_microK_per_beta']
    n, w = sphere_rule(32)
    packet = namespace['real_harmonics_with_gradients'](n, lmax=5)
    pixels = namespace['first_order_sky_generator'](n, packet, source)
    modes = design(n, 16).T@(w[:, None]*pixels)
    analytic = transfer@(beam_layout(beam, 16)[:, None]*modes)
    absolute = float(np.linalg.norm(analytic-finite_difference, 2))
    relative = absolute/np.linalg.norm(analytic, 2)
    beyond6 = float(np.linalg.norm(modes[49:]))
    # First derivative of finite ell<=5 input has no ell>6 component.
    if relative > 1e-7 or beyond6 > 1e-8:
        raise ValueError('ANALYTIC_FIRST_ORDER_GENERATOR_DISAGREES')
    result = {'schema':'htt.V02_analytic_generator_check/1','status':'PASS_FINITE_COUNTERFACTUAL_ORACLE',
              'owner':'obsstat','claim_tier':'C0','non_claim_bearing':True,
              'oracle_source':{'commit':COMMIT,'path':PATH,'sha256':hashlib.sha256(code).hexdigest()},
              'saved_finite_difference_vs_analytic_operator_norm_microK_per_beta':absolute,
              'relative_operator_delta':relative,
              'analytic_mode_norm_above_ell6_microK_per_beta':beyond6,
              'physical_planck_observer_response_qualified':False,
              'new_native_map_processing':False}
    with target.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
