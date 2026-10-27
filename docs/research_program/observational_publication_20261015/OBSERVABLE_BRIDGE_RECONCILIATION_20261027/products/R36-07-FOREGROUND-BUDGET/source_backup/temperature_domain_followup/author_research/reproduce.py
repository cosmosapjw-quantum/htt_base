"""Small analytical witnesses only; no native maps/noise or frozen files changed."""
from pathlib import Path
import json,math,hashlib,time
import numpy as np
from scipy.special import logsumexp
from numpy.polynomial.legendre import leggauss
R=Path(__file__).resolve().parent;P=R.parent;start=time.monotonic()
h=6.62607015e-34;k=1.380649e-23;c=299792458.;Tc=2.7255;ref=353e9

def f(x):return np.expm1(x)/x

def g(nu,T):return f(h*ref/(k*T))/f(h*nu/(k*T))

def db(nu):
 x=h*nu/(k*Tc)
 return 2*k*nu**2/c**2*x*x*np.exp(x)/np.expm1(x)**2

kin=[]
for v in [0.,.001,.01,.5,.9,.9999]:
 gamma=1/math.sqrt(1-v*v);dmin=1/(gamma*(1+v))
 rest_ratio=(gamma*gamma*(1+v*v/3))**.25
 kin.append({'speed_over_c':v,'gamma':gamma,'grey_equilibrium_Trest_over_local_CMB':rest_ratio,
             'receding_grey_Tobs_K':Tc*dmin*rest_ratio,'general_bounded_speed_floor_K':Tc*dmin*dmin})
 assert Tc*dmin*rest_ratio+1e-14>=Tc*dmin*dmin

# Reuse cached DIRBE response only; not the old producer's code.
rows=[]
for line in (P/'source/DIRBE_SYSTEM_SPECTRAL_RESPONSE_TABLE.ASC').read_text().splitlines():
 try:a=[float(z) for z in line.split()]
 except ValueError:continue
 if len(a)==11:rows.append(a)
a=np.array(rows);nu=c/(a[:,0]*1e-6);resp=a[:,10];ix=np.argsort(nu);nu=nu[ix];resp=resp[ix]
x,w=leggauss(16);left,right=nu[:-1],nu[1:];half=(right-left)/2;mid=(left+right)/2
nq=(mid[:,None]+half[:,None]*x).ravel();rq=((resp[:-1,None]+resp[1:,None])/2+(resp[1:,None]-resp[:-1,None])/2*x).ravel();wq=(half[:,None]*np.broadcast_to(w,(len(half),len(w)))).ravel();keep=rq>0;nq=nq[keep];rq=rq[keep];wq=wq[keep]
N=float(np.sum(wq*rq*(c/(240e-6))/nq))
# beta0=1.5, normalized MBB = r^(beta+2)*g(r,u).
minimum=np.minimum(1.,g(nq,Tc));maximum=np.maximum(1.,g(nq,Tc))
weights=wq*rq*(nq/ref)**3.5*minimum
mplus=db(ref)*np.sum(weights)/N
prob=weights/weights.sum();b=float(prob@np.log(nq/ref));aminus=math.log(ref/.408e9)
mlow=db(ref)*(.408e9/ref)**3.5 # g_min=1 below reference
checks=[]
for temp in [Tc,3.,20.,100.,1e4,1e8]:
 gg=g(nq,temp)
 assert np.all(gg>=minimum*(1-1e-13)) and np.all(gg<=maximum*(1+1e-13))
 for delta in [-20.,-2.,0.,2.,20.]:
  log_actual=logsumexp(np.log(wq*rq/N)+3.5*np.log(nq/ref)+np.log(gg)+delta*np.log(nq/ref))+math.log(db(ref))
  log_lower=math.log(mplus)+b*delta
  assert log_actual>=log_lower-1e-12
 checks.append({'T_K':temp,'DIRBE_baseline_response_MJy_sr_per_K_CMB353':float(db(ref)*np.sum(wq*rq*(nq/ref)**3.5*gg)/N/1e-20),
                'original_t':(temp-20)/20,'original_tt_over_2':((temp-20)/20)**2/2,
                'inverse_u_K_inverse':1/temp,'normalized_inverse_coordinate_20u':20/temp})
# A fixed complex sky atom produces a full rank-two 24-vector kernel, with
# norm sqrt(3/pi) per unit complex amplitude (prior independently checked).
full=[{'T_K':row['T_K'],'norm_U_t_for_unit_complex_atom':math.sqrt(3/math.pi)*abs(row['original_t']),
       'norm_U_tt_for_unit_complex_atom':math.sqrt(3/math.pi)*row['original_tt_over_2']} for row in checks]

# Local slope interpolation: exact geometric frequency combination cancels beta.
# Conservative global constant for all T>=Tc; no numerical maximization used.
interp=[]
nuL=.408e9;nuH=c/(240e-6)
for freq in [30.,44.,70.,100.,143.,217.,353.]:
 nt=freq*1e9;theta=math.log(nuH/nt)/math.log(nuH/nuL)
 # Planck ratio bounds B_nu between RJ_nu*T*exp(-hnu/kTfloor) and RJ_nu*T.
 logbound=(theta*h*nuL+(1-theta)*h*nuH)/(k*Tc)
 vals=[]
 for temp in [Tc,3.,20.,100.,1e4,1e8]:
  lp=lambda n:3*math.log(n)-math.log(math.expm1(h*n/(k*temp)))
  logC=lp(nt)-theta*lp(nuL)-(1-theta)*lp(nuH)
  assert logC<=logbound+1e-12
  vals.append({'T_K':temp,'log_exact_Planck_interpolation_factor':logC})
 interp.append({'frequency_GHz':freq,'theta_low':theta,'conservative_all_T_log_factor_upper':logbound,'samples':vals})

# Source-grounded representative refractory-grain conditional class.
v0=1e15*(1e-23)**(1/3);a_max=1e-5;B=7e4
survival=[]
for seconds in [10.,86400.,365.25*86400,1e6*365.25*86400]:
 temp=B/math.log(v0*seconds/a_max)
 eroded=v0*seconds*math.exp(-B/temp)
 assert abs(eroded/a_max-1)<1e-13
 survival.append({'constant_rest_temperature_duration_s':seconds,'a_initial_max_cm':a_max,'limiting_temperature_K':temp,
                  'status':'CONDITIONAL_RATE_MODEL_VALUE; not a universal grain ceiling or certified parameter interval'})
# Sublimation residence control alone cannot bound T moments: hot dwell=1/N,
# T=N gives bounded loss <=v0/N but integral T^2 dt=N diverges.
spikes=[]
for n in [1e4,1e6,1e8]:
 spikes.append({'T_K':n,'dwell_s':1/n,'eroded_radius_cm':v0/n*math.exp(-B/n),'integral_T_squared_dt_K2_s':n})
# Choose an additional arbitrary scale so every listed pulse survives a_max.
scale=a_max/(2*v0)
for item in spikes:
 item['dwell_s']*=scale;item['eroded_radius_cm']*=scale;item['integral_T_squared_dt_K2_s']*=scale
 assert item['eroded_radius_cm']<a_max

prior=json.loads((P/'NUMERIC_RESEARCH.json').read_text())
ZL=prior['source_stats']['lambda_haslam408_nofilt.fits']['equal_area_integral_K_RJ_sr']*2*k*(.408e9)**2/c**2
ZH=prior['source_stats']['DIRBE_BAND10_AAM_P3B.FITS']['sum_with_uniform_nominal_pixel_areas_MJy']*1e-20
jm=ZL/mlow;jp=ZH/mplus
mass=jm**(b/(aminus+b))*jp**(aminus/(aminus+b))

out={'task_id':'R36-07-FOREGROUND-BUDGET','followup':'temperature_domain_followup','status':'CONDITIONAL_THEORY_WITNESSES_ONLY','kinematic_floor':kin,
     'passive_temperature_floor_K':Tc,'bounded_u_domain_K_inverse':[0,1/Tc],
     'MBB_uniform_passband_lower':{'beta0':1.5,'a_minus':aminus,'b_plus':b,'Haslam_nominal_m_SI_per_K_CMB353':mlow,'DIRBE_lower_m_MJy_sr_per_K_CMB353':mplus/1e-20,
       'proof':'g=f(h ref u/k)/f(h nu u/k), f(x)=expm1(x)/x, monotone in u with sign(ref-nu); extrema are T_floor and infinity; Jensen after uniform lower response.',
       'numeric_checks':checks},
     'idealized_source_sum_sensitivity':{'Jminus_K_CMB353_sr':jm,'Jplus_K_CMB353_sr':jp,'M0_upper_K_CMB353_sr':mass,
       'qualification':'NOT_PHYSICAL_CALIBRATION; assumes raw sums exact true fluxes, kappa=1, nominal Haslam, same pure MBB across source bands'},
     'full_24_vector_temperature_counterexample':full,'monochromatic_interpolation_factor':interp,
     'conditional_survival_model':{'citation':'Waxman and Draine 2000, equations 10-12','attempt_frequency_per_s':1e15,'atomic_number_density_cm_minus3':1e23,'binding_B_over_k_K':B,'v0_cm_s':v0,'examples':survival},
     'transient_survival_without_T2_bound':spikes,
     'assertions':'ALL_PASS','elapsed_s':time.monotonic()-start,'acceptance_met':False,'qualified_products':[]}
(R/'NUMERIC_WITNESSES.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'assertions':out['assertions'],'DIRBE_mplus':mplus/1e-20,'b_plus':b,'one_year_survival_ceiling_K':survival[2]['limiting_temperature_K'],'elapsed_s':out['elapsed_s']}))
