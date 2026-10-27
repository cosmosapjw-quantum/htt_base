"""Independent bounded review checks. No author imports; no production writes."""
from pathlib import Path
import json, math, hashlib, time
import mpmath as mp
import numpy as np

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'source'
AUTHOR = Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_positive_envelope_research')
mp.mp.dps = 70
start = time.monotonic()
out = {'precision_decimal_digits': mp.mp.dps, 'author_imports': False}
a = mp.log(mp.mpf(30) / mp.mpf('.408'))

# Integrate the piecewise-linear frequency interpolant analytically, independently
# of the author's 16-point Gaussian quadrature.
rows = []
for line in (SRC / 'DIRBE_SYSTEM_SPECTRAL_RESPONSE_TABLE.ASC').read_text().splitlines():
    try:
        row = [mp.mpf(s) for s in line.split()]
    except (ValueError, TypeError):
        continue
    if len(row) == 11:
        rows.append((mp.mpf(299792458)/(row[0]*mp.mpf('1e-6')), row[10]))
rows.sort()
nu0 = mp.mpf('30e9'); nuc = mp.mpf(299792458)/mp.mpf('240e-6')
den = mp.mpf(0); num = mp.mpf(0)
for (lo, rlo), (hi, rhi) in zip(rows[:-1], rows[1:]):
    if not (rlo or rhi):
        continue
    slope = (rhi-rlo)/(hi-lo); intercept = rlo-slope*lo
    den += slope*(hi-lo)+intercept*mp.log(hi/lo)
    num += slope*(hi*(mp.log(hi/nu0)-1)-lo*(mp.log(lo/nu0)-1))
    num += intercept/2*(mp.log(hi/nu0)**2-mp.log(lo/nu0)**2)
b = num/den
ref = json.loads((AUTHOR/'NUMERIC_RESEARCH.json').read_text())
assert abs(b-mp.mpf(str(ref['DIRBE_passband']['tbar_log_nu_over_30']))) < mp.mpf('1e-13')
assert abs(den*nuc/mp.mpf(str(ref['DIRBE_passband']['normalization_integral_Hz_for_nuIconstant']))-1) < mp.mpf('1e-13')
out['analytic_passband'] = {'tbar':str(b), 'normalization_Hz':str(den*nuc),
    'relative_normalization_error_vs_author':float(abs(den*nuc/mp.mpf(str(ref['DIRBE_passband']['normalization_integral_Hz_for_nuIconstant']))-1))}

constants = []
for k in [1,2,3,4,10,50]:
    for c in [a,b,mp.mpf('.001'),mp.mpf('100')]:
        u=k/c; sharp=(k/(mp.e*c))**k
        assert mp.almosteq(u**k*mp.exp(-c*u),sharp)
        constants.append({'k':k,'c':float(c),'relative_error_at_max':float(abs(u**k*mp.exp(-c*u)/sharp-1))})
out['sharp_one_tail_constants'] = constants

# Logarithmically weighted adversarial mixtures with cancellation and both tails.
atoms = list(map(mp.mpf, ['-110','-5','-1','0','2','5','80']))
masses = list(map(mp.mpf, ['1e-190','0.3','1','2','0.2','1e-9','1e-130']))
phases = [mp.e**(1j*mp.mpf(v)) for v in ['0','1','3.141592653589793','2','4','5','6']]
jm=sum(m*mp.exp(-a*d) for m,d in zip(masses,atoms))
jp=sum(m*mp.exp(b*d) for m,d in zip(masses,atoms))
mom=[sum(m*abs(d)**k for m,d in zip(masses,atoms)) for k in range(5)]
bounds=[jm**(b/(a+b))*jp**(a/(a+b))]+[(k/(mp.e*a))**k*jm+(k/(mp.e*b))**k*jp for k in range(1,5)]
for k in range(5):
    assert mom[k]<=bounds[k]
    cm=abs(sum(m*d**k*p for m,d,p in zip(masses,atoms,phases)))/mp.factorial(k)
    assert cm<=mom[k]/mp.factorial(k)
out['mixture_moment_ratios']=[float(m/c) for m,c in zip(mom,bounds)]
remchecks=[]
for t in [-a, -a+mp.mpf('1e-12'), -a/2, mp.mpf(0), b/2, b-mp.mpf('1e-12'), b]:
    E=jm**((b-t)/(a+b))*jp**((a+t)/(a+b))
    actualE=sum(m*mp.exp(t*d) for m,d in zip(masses,atoms))
    R=sum(m*abs(mp.expm1(t*d)-t*d-(t*d)**2/2) for m,d in zip(masses,atoms))
    tri=E+bounds[0]+abs(t)*bounds[1]+t*t*bounds[2]/2
    assert actualE<=E*(1+mp.mpf('1e-65')) and R<=tri
    row={'t':float(t),'exact_remainder':float(R),'triangle_bound':float(tri)}
    if -a<t<b:
        cub=abs(t)**3/6*((3/(mp.e*(a-max(-t,0))))**3*jm+(3/(mp.e*(b-max(t,0))))**3*jp)
        assert R<=cub*(1+mp.mpf('1e-65'))
        row['cubic_bound']=float(cub)
    remchecks.append(row)
out['endpoint_and_interior_remainders']=remchecks

# The finite-passband Jensen direction holds for all real delta; wide negative
# and positive numerical witnesses supplement, rather than replace, convexity.
for delta in map(mp.mpf,['-1000','-100','-.001','0','.001','100','1000']):
    ts=list(map(mp.mpf,['-4.5','-4.1','3.3','3.7','4.2']))
    ps=list(map(mp.mpf,['.1','.15','.2','.25','.3']))
    tbar=sum(p*t for p,t in zip(ps,ts))
    assert sum(p*mp.exp(delta*t) for p,t in zip(ps,ts))>=mp.exp(delta*tbar)*(1-mp.mpf('1e-65'))
out['Jensen_extreme_delta_checks']=7

# Necessary hypotheses: losing strict bracketing leaves moments uncontrolled;
# outside the bracket even both exponential constraints fail to bound the target.
out['failed_extensions'] = []
for d in [10,100,1000]:
    out['failed_extensions'].append({'d':d,'a_zero_negative_tail_mass':1,'M1':d,
        'log_Jplus':float(-b*d),'outside_t_b_plus_1_log_target':d,
        'outside_witness_log_mass':float(-b*d),'outside_witness_Jplus':1})

def logS(r,x,beta):
    return (beta+3)*mp.log(r)+mp.log(mp.expm1(x))-mp.log(mp.expm1(x*r))
hot=[]
for T in [20,100,10000,100000000]:
    x=mp.mpf('6.62607015e-34')*mp.mpf('353e9')/(mp.mpf('1.380649e-23')*T)
    vals=[mp.exp(logS(r,x,mp.mpf('1.5'))) for r in [mp.mpf('.408')/353,mp.mpf(30)/353,mp.mpf(1),mp.mpf(1855)/353]]
    hot.append({'T':T,'t2_over_2':float(((mp.mpf(T)-20)/20)**2/2),'sample_intensity_ratios':list(map(float,vals))})
out['hot_MBB'] = hot
cold=[]
for x in [100,1000,10000]:
    xx=mp.mpf(x)
    # Scaled integration resolves the narrowing peak. The central interval is
    # contained in the fixed target r in [1/2,3/2] for these x.
    integral=mp.sqrt(xx)*mp.quad(lambda z:mp.exp(logS(1+z/mp.sqrt(xx),xx,xx-3)),[-5,0,5])
    ratio=integral/mp.sqrt(2*mp.pi*xx)
    assert ratio>mp.mpf('.99')
    cold.append({'x':x,'reference_amplitude':x,'central_target_integral_over_nuref':float(integral),
        'ratio_to_sqrt_2pi_x':float(ratio),
        'log_Haslam_response':float(mp.log(xx)+logS(mp.mpf('.408')/353,xx,xx-3)),
        'log_DIRBE_lowedge_response':float(mp.log(xx)+logS(mp.mpf('658.721')/353,xx,xx-3))})
out['cold_MBB_fixed_target_integral']=cold

spatial=[]
for eps in [mp.mpf('.1'),mp.mpf('.001'),mp.mpf('1e-9')]:
    K=mp.matrix([[1-eps,eps],[1-2*eps,2*eps]])
    y=K*mp.matrix([0,1/eps]); kappa=min(K[0,j]+K[1,j] for j in range(2))
    assert y[0]==1 and y[1]==2 and (y[0]+y[1])/kappa>=1/eps
    spatial.append({'epsilon':float(eps),'mass':float(1/eps),'sum_y':float(sum(y)),'kappa':float(kappa),
        'certified_mass_bound':float(sum(y)/kappa)})
out['aggregate_response_counterexample']=spatial
syn=ref['conditional_envelope']['conditional_synch_component_rho_bound_K_CMB']
geo=json.loads(Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_budget_actual/GEOMETRY.json').read_text())
out['units_and_comparison']={'synch_only_conditional_upper_K_CMB':syn,'synch_only_conditional_upper_microK_CMB':syn*1e6,
 'original_algebraic_minimum_K_CMB':geo['rho_min_algebraic_K_CMB'],
 'ratio_for_scale_only':syn/geo['rho_min_algebraic_K_CMB'],
 'full_radius_comparison_admissible':False,'reason':'Missing dust/omitted components and native response remainder bridge; conditional upper bound not a measured norm.'}
out['status']='ALL_BOUNDED_REVIEW_CHECKS_PASSED'
out['elapsed_seconds']=time.monotonic()-start
(ROOT/'INDEPENDENT_CHECKS.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'elapsed_seconds':out['elapsed_seconds'],'analytic_tbar':str(b)}))
