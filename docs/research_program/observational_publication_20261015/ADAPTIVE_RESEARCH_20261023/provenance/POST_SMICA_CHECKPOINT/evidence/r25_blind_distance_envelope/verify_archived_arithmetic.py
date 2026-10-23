"""Blind finite-library certificate. Standard library only; no candidate import.

Each JSON floating scalar is interpreted as its parsed exact binary64 rational.
For d <= 0, reduce x=-d/2**s to [0,1]. The alternating Taylor sums S_181(x)
and S_180(x) enclose exp(-x). Outward integer rounding on a 10**240 grid,
followed by s outward-rounded squarings, encloses exp(d). All arithmetic in
this certificate is integer or fractions.Fraction; no floating exp is used.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import datetime
import hashlib
import json
import math
import platform
import subprocess
import sys
import time

START = time.monotonic()
ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE = ROOT / 'docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023'
OUT = Path('/mnt/extdrive/workdir/htt_open_data/r25_blind_distance_envelope')
EXPECTED_MANIFEST = '735f35ad7b1cf3eab48abd5ded2e52dbceccb813f1caf504b35c9f058c4725fb'
EXPECTED_INPUT = '77439c5b5966f6f0c6a4d4e2819b28b76b7a3c24523e9b08ec9f7e12fd5ca2b8'
GRID = 10**240
TAYLOR_EVEN = 180

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def exact(x):
    assert isinstance(x, float) and math.isfinite(x)
    return F.from_float(x)

def ceil_fraction(x):
    return -((-x.numerator)//x.denominator)

def down(x):
    return F((x.numerator*GRID)//x.denominator, GRID)

def up(x):
    return F(-((-x.numerator*GRID)//x.denominator), GRID)

def exp_interval(d):
    assert d <= 0
    x = -d
    steps = 0
    while x > 1:
        x /= 2
        steps += 1
    term = F(1)
    subtotal = term
    for n in range(1, TAYLOR_EVEN+1):
        term *= -x/n
        subtotal += term
    upper = subtotal
    lower = subtotal + term*(-x)/(TAYLOR_EVEN+1)
    assert 0 < lower <= upper <= 1
    lo, hi = down(lower), up(upper)
    for _ in range(steps):
        lo, hi = down(lo*lo), up(hi*hi)
    assert 0 <= lo <= hi <= 1
    return lo, hi

def sum_intervals(items, divisor=1):
    return sum((a for a,b in items),F(0))/divisor, sum((b for a,b in items),F(0))/divisor

def fixed_string(integer, digits):
    sign = '-' if integer < 0 else ''
    raw = str(abs(integer)).zfill(digits+1)
    return sign + raw[:-digits] + '.' + raw[-digits:]

def endpoint(x, direction, digits=40):
    scaled = x*10**digits
    integer = scaled.numerator//scaled.denominator if direction=='lower' else ceil_fraction(scaled)
    return fixed_string(integer,digits)

def interval_json(bounds):
    lo,hi = bounds
    assert lo <= hi
    return {'lower_decimal':endpoint(lo,'lower'), 'upper_decimal':endpoint(hi,'upper'),
            'lower_rational':[str(lo.numerator),str(lo.denominator)],
            'upper_rational':[str(hi.numerator),str(hi.denominator)]}

manifest_path = BASE/'distance_conditional_evidence/MANIFEST.json'
input_path = BASE/'R25-DISTANCE-CONDITIONAL-EVIDENCE_INPUT.json'
result_path = BASE/'distance_conditional_evidence/RESULT.json'
manifest = json.loads(manifest_path.read_text())
inp = json.loads(input_path.read_text())
result = json.loads(result_path.read_text())
assert sha(manifest_path)==EXPECTED_MANIFEST
assert sha(input_path)==EXPECTED_INPUT
assert sha(result_path)==manifest['products_sha256']['RESULT.json']
assert manifest['input_identity']==result['input_identity']=='sha256:'+EXPECTED_INPUT
assert result['formula']=={
    'numerator':'logsumexp(eight saved training-fixed conditional block log densities)-log(8)',
    'denominator':'maximum of four conditional Gaussian null ML log densities per fold',
    'aggregate':'logsumexp(five fold log E)-log(5)'}
assert len(result['components'])==40
assert len(result['null_fits'])==20
assert [f['fold'] for f in result['folds']]==list(range(5))
assert Counter(c['fold'] for c in result['components'])=={j:8 for j in range(5)}
assert Counter(c['fold'] for c in result['null_fits'])=={j:4 for j in range(5)}
fold_reports=[]
maxima=[]
equal_means=[]
stored_logE_intervals=[]
stored_logq_ratio_intervals=[]
common_component_intervals={}
for fold in result['folds']:
    j=fold['fold']
    comps=[c for c in result['components'] if c['fold']==j]
    nulls=[c for c in result['null_fits'] if c['fold']==j]
    assert len({(c['scenario'],c['model']) for c in comps})==8
    assert fold['n']==result['cohort']['fold_sizes'][j]
    assert all(c['n']==fold['n'] for c in comps+nulls)
    assert fold['max_null_logdensity']==max(c['ellstar'] for c in nulls)
    denominator=exact(fold['max_null_logdensity'])
    candidates=[]
    details=[]
    for c in comps:
        logq=exact(c['log_density'])
        d=logq-denominator
        iv=exp_interval(d)
        candidates.append(iv)
        key=(c['scenario'],c['model'])
        common_component_intervals.setdefault(key,[]).append(iv)
        details.append({'scenario':c['scenario'],'model':c['model'],
            'log_density_binary64_hex':c['log_density'].hex(),
            'denominator_log_binary64_hex':fold['max_null_logdensity'].hex(),
            'exact_log_difference':[str(d.numerator),str(d.denominator)],
            'ratio_interval':interval_json(iv)})
    imax=max(range(8),key=lambda k:exact(comps[k]['log_density']))
    max_iv=candidates[imax]
    equal_iv=sum_intervals(candidates,8)
    coarse_iv=sum_intervals(candidates)
    # Positive omitted components make max strictly below eight times equal.
    assert max_iv[1]<coarse_iv[0]
    maxima.append(max_iv)
    equal_means.append(equal_iv)
    stored_logE_intervals.append(exp_interval(exact(fold['logE'])))
    stored_logq_ratio_intervals.append(exp_interval(exact(fold['logq'])-denominator))
    fold_reports.append({'fold':j,'n':fold['n'],'max_component':{
        'scenario':comps[imax]['scenario'],'model':comps[imax]['model']},
        'max_ratio':interval_json(max_iv),'exact_equal_mixture_ratio':interval_json(equal_iv),
        'eight_times_exact_equal_mixture_ratio':interval_json(coarse_iv),
        'components':details})

tight=sum_intervals(maxima,5)
equal=sum_intervals(equal_means,5)
coarse=tuple(8*x for x in equal)
stored_logE_average=sum_intervals(stored_logE_intervals,5)
stored_logq_average=sum_intervals(stored_logq_ratio_intervals,5)
stored_summary=exact(result['E_arithmetic_fold_average'])
assert tight[1]<coarse[0]<F(1)
assert tight[1]<F(1,1000)
# Exact global component averaging provides a tighter bound if weights are
# constrained to be identical in all folds; included only as an extra check.
common_means={k:sum_intervals(v,5) for k,v in common_component_intervals.items()}
common_key=max(common_means,key=lambda k:common_means[k][0])
assert all(common_means[common_key][0]>v[1] for k,v in common_means.items() if k!=common_key)

status=subprocess.check_output(['git','status','--short','--branch'],cwd=ROOT,text=True)
(OUT/'git_status_observed.txt').write_text(status)
report={
 'review_id':'R25_DISTANCE_FINITE_LIBRARY_BLIND_ARITHMETIC',
 'component_verdict':'PASS_FINITE_ARCHIVED_SCALAR_ARITHMETIC_ONLY',
 'original_scientific_admission':'HOLD',
 'original_frozen_fit_cap':'20; violation >=21 inherited from controller task and unchanged; no fits performed by this review',
 'independence':'No candidate compute import or execution; no author blocker research or prior review verdict inspected; standard-library independent derivation',
 'requested_runtime':{'model':'gpt-6-astra','reasoning_effort':'xhigh'},
 'observed_runtime':'UNKNOWN',
 'source_seals':{str(p.relative_to(ROOT)):sha(p) for p in [manifest_path,input_path,result_path]},
 'source_identity_checks':'PASS supplied manifest/input identities and manifest-bound RESULT identity; full scalar fold counts and denominator field maxima checked',
 'statement':'For every fold j=0..4, q_jk=exp(archived component log_density), D_j=exp(archived max_null_logdensity), w_jk>=0 and sum_k w_jk=1: sum_k w_jk q_jk/D_j <= max_k q_jk/D_j <= sum_k q_jk/D_j = 8 q_equal,j/D_j. The fixed 1/5 fold average obeys the average of those bounds. The maximum over arbitrary independent fold weight vectors equals the average of fold component maxima.',
 'proof':'A convex combination of nonnegative values is at most their maximum. A maximum is at most their sum. Each q_equal,j is defined as the exact arithmetic mean of the eight reconstructed positive values. Summing inequalities with fixed nonnegative weight 1/5 preserves order. Choosing a vertex weight at each fold maximum attains the tight upper bound; no optimization or new fit is needed.',
 'arithmetic_semantics':'JSON floats parsed to IEEE binary64 and then exact rationals using as_integer_ratio via Fraction.from_float. Subtraction is exact rational subtraction, not floating subtraction. Stored logq, logE, E are rounded summaries, not exact identities for the reconstructed component mixture.',
 'certificate_method':{'grid_decimal_places':240,'taylor_upper_degree':180,'taylor_lower_degree':181,
   'method':'For d<=0, x=-d/2^s in [0,1]. Alternating-series remainder implies S181(x)<=exp(-x)<=S180(x). Exact rational evaluation; endpoints floor/ceil to grid 10^-240. s monotone squarings with outward floor/ceil preserve enclosure. Summation/division are exact rational operations. Final displayed decimals independently rounded outwards to 40 decimal places.',
   'rigor_scope':'Finite arithmetic conditional on the archived binary64 scalar values; Python integer/Fraction correctness trusted. No CAS_4AXIS claim and no certification of the fitted log-density values.'},
 'aggregates':{
   'tight_arbitrary_per_fold_convex_reweighting_maximum':interval_json(tight),
   'exact_reconstructed_equal_mixture_average':interval_json(equal),
   'eight_times_exact_equal_mixture_average':interval_json(coarse),
   'average_exp_archived_fold_logE':interval_json(stored_logE_average),
   'average_exp_exact_difference_archived_logq_and_logD':interval_json(stored_logq_average),
   'archived_E_arithmetic_fold_average_exact_binary64':{'hex':result['E_arithmetic_fold_average'].hex(),'rational':[str(stored_summary.numerator),str(stored_summary.denominator)]},
   'exact_reconstructed_equal_minus_archived_E_summary':interval_json((equal[0]-stored_summary,equal[1]-stored_summary)),
   'common_weights_across_all_folds_maximum':interval_json(common_means[common_key]),
   'common_weights_maximizing_component':{'scenario':common_key[0],'model':common_key[1]},
   'strict_comparisons':['tight bound < 0.001','tight bound < eight times exact equal mixture average < 1']},
 'folds':fold_reports,
 'caveats':[
   'This closes pure convex reweighting of these eight archived components with these fixed five fold denominators and fixed equal fold aggregation at the observed archived inputs.',
   'Normalization of component density functions is inherited from the input contract, not independently established by evaluating scalar log densities; normalization is not needed for the pointwise inequality.',
   'Data-dependent per-fold weights satisfy the pointwise bound but do not thereby yield a normalized training-only density or valid e-value.',
   'No optimization, new fit, old training rerun, raw-data access, downloads, or candidate module import/execution occurred.',
   'Underlying fitted component logs and fitted denominator logs are treated as supplied numbers; their numerical accuracy, optimizer certification, selected-source law and conditional null domination are not established.',
   'No calibrated inference, e-validity, physical tensor conclusion, native solver result, Bianchi identification, original acceptance recovery, or global scientific admission follows.',
   'Full tensor coefficients, covariance cross blocks and 40 component carriers remain inherited in the sealed RESULT; scalar evidence is a decision summary only.',
   'The original frozen 20-fit cap violation >=21 and historical HOLD remain unchanged. This separate arithmetic verification does not rename or reset that task.'
 ],
 'execution':{'command':'PYTHONDONTWRITEBYTECODE=1 python3 -B /mnt/extdrive/workdir/htt_open_data/r25_blind_distance_envelope/verify_archived_arithmetic.py',
   'python':sys.version,'implementation':platform.python_implementation(),'executable':sys.executable,
   'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
   'git_branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
   'git_origin':subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip(),
   'source_script_sha256':sha(Path(__file__)),
   'elapsed_seconds':time.monotonic()-START,
   'write_scope':str(OUT)}}
report_path=OUT/'DISTANCE_FINITE_LIBRARY_REVIEW.json'
report_path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'report':str(report_path),'report_sha256':sha(report_path),
 'verdict':report['component_verdict'],
 'aggregates':{k:({a:b for a,b in v.items() if 'rational' not in a} if isinstance(v,dict) else v) for k,v in report['aggregates'].items()},
 'elapsed_seconds':report['execution']['elapsed_seconds']},indent=2))
