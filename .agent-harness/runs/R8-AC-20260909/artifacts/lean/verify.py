#!/usr/bin/env python3
"""Recompile fresh Lean proofs and emit honest, scoped CAS evidence; no installs."""
from pathlib import Path
import datetime, hashlib, json, os, re, subprocess, sys, time
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
LEAN = Path('/home/cosmosapjw/.elan/toolchains/leanprover--lean4---v4.31.0/bin/lean')
PACKAGES = Path('/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages')
CONTRACT = ROOT / '.agent-harness/runs/R8-AC-20260909/CAS_CONTRACT.json'
PIN = '5ff7f84db01b6871f74f7c60b5c36430a4cae93735466e277bd9c4019ab22723'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    start = time.monotonic()
    if sha(CONTRACT) != PIN:
        print(json.dumps({'status':'ERROR','checks':{},'domain_assumption_diff':['contract identity changed'],'counterexample':None}))
        return 3
    src = HERE/'R8.lean'
    source = src.read_text()
    if re.search(r'\b(sorry|axiom|admit)\b', source):
        raise RuntimeError('Unproved declaration or placeholder in Lean source')
    if (ROOT/'formal/lean-toolchain').read_text().strip() != 'leanprover/lean4:v4.31.0':
        raise RuntimeError('Repository Lean pin changed')
    if (PACKAGES/'mathlib/lean-toolchain').read_text().strip() != 'leanprover/lean4:v4.31.0':
        raise RuntimeError('Mathlib toolchain mismatch')
    rev = subprocess.check_output(['git','-C',str(PACKAGES/'mathlib'),'rev-parse','HEAD'],text=True).strip()
    if rev != 'fabf563a7c95a166b8d7b6efca11c8b4dc9d911f':
        raise RuntimeError('Shared mathlib source revision changed')
    env = os.environ.copy()
    env['LEAN_PATH'] = ':'.join(str(p/'.lake/build/lib/lean') for p in sorted(PACKAGES.iterdir()) if p.is_dir())
    command = [str(LEAN), '-o', str(HERE/'R8.olean'), str(src)]
    run = subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,timeout=150)
    transcript = run.stdout+run.stderr
    (HERE/'build.log').write_text(transcript)
    version = subprocess.check_output([str(LEAN),'--version'],text=True).strip()
    built = run.returncode == 0 and 'sorryAx' not in transcript
    result = {
      'axis':'lean', 'status':'INCONCLUSIVE' if built else 'ERROR',
      'contract_sha256':PIN,'checks':{
        'O1_weighted_lower_and_scaling':None,
        'O2_quaternion_rotation_and_chart_derivative':None,
        'O3_interval_inclusive_counts':True if built else None,
        'J2_rational_factor_support':True if built else None,
        'J2_gaussian_marginal_counterexample':None},
      'domain_assumption_diff':[
        {'obligation':'O1_weighted_lower_and_scaling','kind':'unresolved_scope',
         'detail':'Generic common-index weighted spectral combination is compiled under the permitted component bounds. Exact norm multiplicities and sqrt scaling are compiled. Tensor representation, spectra and feasible identity rotation are not assembled into a Lean theorem asserting both exact orbit minimum fixtures.'},
        {'obligation':'O2_quaternion_rotation_and_chart_derivative','kind':'unresolved_scope',
         'detail':'Quaternion Gram/determinant identities and actual coordinate HasDerivAt formulas, projection numerator identity, derivative squared bound and sqrt(3)<=7/4 compile. Four-chart global coverage and cell spherical-length/rotation-radius theorem are not assembled; no generic radius PASS.'},
        {'obligation':'J2_gaussian_marginal_counterexample','kind':'unresolved_scope',
         'detail':'Only sign-mixture pointwise support identity compiles. No measure-theoretic construction establishes its Gaussian marginals and nonguassian joint law.'}],
      'counterexample':None,'mathematical_counterexample_found':False,
      'subchecks':{
        'generic_common_rotation_weighted_lower':built,
        'exact_scaling_norm_multiplicities':built,
        'positive_scale_sqrt_identity':built,
        'generic_homogeneous_quaternion_gram_and_determinant':built,
        'normalized_chart_actual_directional_coordinate_derivative':built,
        'normalized_chart_derivative_projection_and_squared_bound':built,
        'sqrt_three_rational_radius_majorant':built,
        'generic_inclusive_interval_count_and_ratio_bounds':built,
        'exact_301_1000_reject_nonreject_thresholds':built,
        'tie_and_wide_interval_fixtures':built,
        'rational_rank_one_full_rank_left_inverse_covariance_and_support':built,
        'sign_mixture_pointwise_identity_only':built},
      'assumptions':['Real nonnegative component spectral bounds for every same rotation index (Hoffman-Wielandt/Mirsky prerequisites permitted by contract).','Positive q0,o0,M and chart squared denominator; m>0 and m^2<=s.','Deterministic inclusive score intervals enclose their exact fixed scores.'],
      'scope':'Fresh conditional real algebra/calculus and exact rational/finite-set proofs. No probability-law, physical or implementation admission.',
      'build':{'command':command,'cwd':str(ROOT),'env':{'LEAN_PATH':env['LEAN_PATH']},'returncode':run.returncode,'version':version,'mathlib_revision':rev,'elapsed_seconds':time.monotonic()-start,'source_sha256':sha(src),'transcript':'build.log','transcript_sha256':sha(HERE/'build.log'),'compiled_object_sha256':sha(HERE/'R8.olean') if built else None},
      'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (HERE/'build_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return 2 if built else 3
if __name__ == '__main__': sys.exit(main())
