"""Small independent source-class falsifiers and optional future repair.

These are analytic model examples, not measured foreground budgets.

For a positive pure-power-law emitter measure mu at nu0, let delta=beta-beta0,
t_minus=log(nu_minus/nu0)<0<t_plus=log(nu_plus/nu0), and
J_plusminus=integral exp(t_plusminus*delta) dmu. The baseline spectral factors
must be divided out of a qualified intensity upper constraint to bound J.
For k>=1 and x>=0, max x^k exp(-a*x)=(k/(e*a))^k. Applying this to positive
and negative delta separately proves, on the whole real line,
 integral |delta|^k dmu <= (k/(e*abs(t_minus)))^k J_minus
                           +(k/(e*t_plus))^k J_plus.
For k=0, integral dmu <= J_minus+J_plus. Signed/complex polarization moments
are bounded by these positive moments when |dnu|<=dmu. Factorial moments
divide this upper bound by k!. Compact beta support is sufficient, not
necessary. A pair of qualified absolute source functionals on either side
of 30 GHz could provide this weaker route. It still assumes a supported
power-law source model and matching spatial/spectral response domination.

By contrast, no such temperature-tail bound follows solely from a finite
collection of normalized modified blackbodies if arbitrarily large T is
admitted. At fixed reference amplitude at nu0, B_nu(T)/B_nu0(T) tends to
(nu/nu0)^2 as T tends to infinity. All finitely many intensities stay finite
but the R32 second moment ((T-20)/20)^2/2 diverges. This mathematical limit
does not describe viable hot dust; a justified physical ceiling or tail
moment bound excludes it and remains a scientifically meaningful input.
"""
import json
import math
from pathlib import Path
import numpy as np

OUT=Path(__file__).resolve().parent
nu0=30.0
tminus=math.log(.408/nu0)
tplus=math.log(68.020812/nu0)
delta=np.linspace(-100,100,20001)
rows=[]
for k in (0,1,2,3):
    if k==0:
        left=right=1.
    else:
        left=(k/(math.e*abs(tminus)))**k
        right=(k/(math.e*tplus))**k
    lhs=np.abs(delta)**k
    rhs=left*np.exp(tminus*delta)+right*np.exp(tplus*delta)
    assert np.all(lhs<=rhs*(1+1e-14))
    rows.append({'order':k,'J_below_multiplier':left,'J_above_multiplier':right,
                 'grid_min_slack':float((rhs-lhs).min())})

nu=np.array([68.020812,100.,143.,217.,353.,639.395616])*1e9
ref=353e9;h=6.62607015e-34;kb=1.380649e-23
dust=[]
for T in (20.,100.,1000.,1e6):
    response=(nu/ref)**(1.5+3)*np.expm1(h*ref/(kb*T))/np.expm1(h*nu/(kb*T))
    dust.append({'T_K':T,'response_ratio_fixed_reference_intensity':response.tolist(),
                 'factorial_second_t_moment_per_reference_amplitude':((T-20.)/20.)**2/2.})

obj={'status':'UNQUALIFIED_ANALYTIC_MODEL_EXAMPLES_ONLY','whole_domain_proof':__doc__,
     'bracket_GHz':[.408,30.,68.020812],
     'synchrotron_positive_moment_envelope':rows,
     'MBB_temperature_tail_example':dust,
     'limits':['No Haslam data acquired or calibrated; source paper alone supplies no admitted upper confidence set.',
               'FIRAS sky and spectral response domination still missing.',
               'The pure power law must be justified across the bracket; curvature or low-frequency absorption cannot be ignored.',
               'Source-subtracted or inpainted maps require bounds on removed intensity; use a retained total-power product if available.',
               'This is a possible new acquisition/model repair; it does not alter current candidate acceptance.']}
(OUT/'WEAKER_PATH.json').write_text(json.dumps(obj,indent=2)+'\n')
print(json.dumps({'analytic_envelope_grid_checks':'PASS','dust_highT_moment_growth':dust[-1]['factorial_second_t_moment_per_reference_amplitude'],'physical_calibration':False}))
