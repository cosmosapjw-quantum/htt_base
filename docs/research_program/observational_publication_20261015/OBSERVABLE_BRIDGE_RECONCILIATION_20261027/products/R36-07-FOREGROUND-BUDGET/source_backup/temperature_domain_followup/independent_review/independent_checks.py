from pathlib import Path
import json,time,math,hashlib,sys
import numpy as np
import scipy
from scipy.integrate import quad
import mpmath as mp
mp.mp.dps=80
start=time.monotonic(); R=Path(__file__).resolve().parent
h=mp.mpf('6.62607015e-34');k=mp.mpf('1.380649e-23');c=mp.mpf('299792458');ref=mp.mpf('353e9');Tc=mp.mpf('2.7255');ad=h*ref/k
f=lambda x:mp.expm1(x)/x if x else mp.mpf(1)
g=lambda r,u:f(ad*u)/f(ad*r*u)
s=lambda r,beta,u:r**(beta+2)*g(r,u)
fmt=lambda x:mp.nstr(x,55)
# Rest-frame angular average of the Lorentz-transformed bath.
kin=[]
for v in map(mp.mpf,['0','.001','.01','.5','.9','.9999']):
 gam=1/mp.sqrt(1-v*v);dmin=1/(gam*(1+v))
 angular=mp.quad(lambda mu:1/(gam*(1+v*mu))**4,[-1,0,1])/2
 tensor=gam**2*(1+v*v/3)
 assert mp.almosteq(angular,tensor,rel_eps=mp.mpf('1e-70'))
 ratio=dmin*tensor**mp.mpf('.25')
 assert ratio >= dmin*dmin
 if v: assert ratio<1
 kin.append({'v_over_c':fmt(v),'angular_Uprime_over_U':fmt(angular),'tensor_Uprime_over_U':fmt(tensor),'receding_Tobs_K':fmt(Tc*ratio),'conservative_floor_K':fmt(Tc*dmin*dmin)})
# Endpoint bounds are pointwise in frequency; prove/test straddling noncommutation.
y=mp.findroot(lambda y:(y*y+1)**2-8*y,(mp.mpf('1.5'),mp.mpf('1.7')))
u_star=2*mp.log(y)/ad
H=lambda u:(g(mp.mpf('.5'),u)+g(mp.mpf('2'),u))/2
hstar=H(u_star);h0=H(0);hfloor=H(1/Tc)
pointwise_lower=(min(1,g(mp.mpf('.5'),1/Tc))+min(1,g(mp.mpf('2'),1/Tc)))/2
assert 0<u_star<1/Tc and pointwise_lower<=hstar<min(h0,hfloor)
straddle={'frequencies_GHz':['176.5','706'],'positive_effective_weights':['0.5','0.5'],'u_interior_K_inverse':fmt(u_star),'T_interior_K':fmt(1/u_star),'H_at_infinity':fmt(h0),'H_at_floor':fmt(hfloor),'H_at_interior':fmt(hstar),'integrated_pointwise_lower':fmt(pointwise_lower),'conclusion':'Whole-passband endpoint minimum is invalid; candidate pointwise minimum before integration is valid.'}
for r in map(mp.mpf,['.001','0.5','1','2','8']):
 lower=min(1,g(r,1/Tc));upper=max(1,g(r,1/Tc))
 for u in [0,mp.mpf('1e-20'),mp.mpf('.01'),1/Tc]:
  assert lower<=g(r,u)<=upper
# Correlated beta-temperature measures obey source Jensen/Hölder and old TV bounds.
nu_ratios=[mp.mpf('.001'),mp.mpf('.6'),mp.mpf('1.7'),mp.mpf('3')]
source_weights=[mp.mpf('.2'),mp.mpf('.1'),mp.mpf('.3'),mp.mpf('.4')]
base=[w*r**mp.mpf('3.5')*min(1,g(r,1/Tc)) for w,r in zip(source_weights,nu_ratios)]
m=sum(base);tb=sum(w*mp.log(r) for w,r in zip(base,nu_ratios))/m
for delta in map(mp.mpf,['-100','-20','-2','0','2','20','100']):
 for temp in [Tc,mp.mpf(20),mp.mpf('1e8')]:
  actual=sum(w*s(r,delta+mp.mpf('1.5'),1/temp) for w,r in zip(source_weights,nu_ratios))
  assert actual>=m*mp.exp(tb*delta)*(1-mp.mpf('1e-70'))
mu=[mp.mpf('.1'),mp.mpf('.7'),mp.mpf('2.3'),mp.mpf('.4')]
deltas=[mp.mpf('-20'),mp.mpf('3'),mp.mpf('-1'),mp.mpf('12')]
Ts=[Tc,mp.mpf('1000'),mp.mpf('3'),mp.mpf('1e5')]
a=mp.mpf('2');b=mp.mpf('1.3')
Jm=sum(w*mp.exp(-a*d) for w,d in zip(mu,deltas));Jp=sum(w*mp.exp(b*d) for w,d in zip(mu,deltas));M0=sum(mu)
assert M0 <= Jm**(b/(a+b))*Jp**(a/(a+b))
for power in [1,2,4]:
 Mk=sum(w*abs(d)**power for w,d in zip(mu,deltas))
 bound=(power/(mp.e*a))**power*Jm+(power/(mp.e*b))**power*Jp
 assert Mk<=bound
 for lp in [0,1,2,5]:assert sum(w*abs(d)**power/t**lp for w,d,t in zip(mu,deltas,Ts)) <= Tc**(-lp)*Mk
M1=sum(w*abs(d) for w,d in zip(mu,deltas));M2=sum(w*d*d for w,d in zip(mu,deltas));Mt2=sum(w*(t/20-1)**2 for w,t in zip(mu,Ts))
row_actual=[M0,M1,sum(w*abs(t/20-1) for w,t in zip(mu,Ts)),M2/2,sum(w*abs(d*(t/20-1)) for w,d,t in zip(mu,deltas,Ts)),Mt2/2]
row_bounds=[M0,M1,mp.sqrt(M0*Mt2),M2/2,mp.sqrt(M2*Mt2),Mt2/2]
assert all(x<=z for x,z in zip(row_actual,row_bounds))
# Independent full spin-2 E/B atom using finite Wigner-d sums, all 24 real coordinates.
def dy(l,m,n,th):
 pref=mp.sqrt(mp.factorial(l+m)*mp.factorial(l-m)*mp.factorial(l+n)*mp.factorial(l-n))
 val=0
 for z in range(2*l+1):
  args=[l+n-z,z,m-n+z,l-m-z]
  if min(args)<0:continue
  val+=(-1)**(m-n+z)*mp.cos(th/2)**(2*l+n-m-2*z)*mp.sin(th/2)**(m-n+2*z)/mp.fprod(mp.factorial(q) for q in args)
 return pref*val
def Y(l,m,spin,th,ph):return (-1)**spin*mp.sqrt((2*l+1)/(4*mp.pi))*dy(l,m,-spin,th)*mp.exp(1j*m*ph)
P=mp.mpc('.6','.8');th=mp.mpf('1.1');ph=mp.mpf('.7');V=[]
for l in [2,3]:
 EB=[]
 for mval in range(l+1):
  a2=P*mp.conj(Y(l,mval,2,th,ph));an2=mp.conj(P)*mp.conj(Y(l,mval,-2,th,ph))
  EB.append((-(a2+an2)/2,1j*(a2-an2)/2))
 for component in [0,1]:
  assert abs(mp.im(EB[0][component]))<mp.mpf('1e-70')
  V.append(mp.re(EB[0][component]))
  for mval in range(1,l+1):V.extend([mp.sqrt(2)*mp.re(EB[mval][component]),mp.sqrt(2)*mp.im(EB[mval][component])])
assert len(V)==24
norm=mp.sqrt(sum(x*x for x in V));assert mp.almosteq(norm,mp.sqrt(3/mp.pi),rel_eps=mp.mpf('1e-70'))
atom=[]
for T in [mp.mpf('20'),mp.mpf('1e3'),mp.mpf('1e8')]:
 atom.append({'T_K':fmt(T),'norm_U_t':fmt(abs(T/20-1)*norm),'norm_U_tt':fmt((T/20-1)**2*norm/2),'seven_band_spectral_responses':[fmt(s(n/ref,mp.mpf('1.5'),1/T)) for n in map(mp.mpf,['30e9','44e9','70e9','100e9','143e9','217e9','353e9'])]})
# A full 168-dimensional randomized algebra check; not the actual native operator certificate.
rng=np.random.default_rng(364207);A=rng.normal(size=(13,168,2));p=rng.normal(size=(13,2));p/=np.maximum(1,np.linalg.norm(p,axis=1))[:,None];weights=rng.uniform(.01,2,size=13)
Ysum=np.einsum('n,nij,nj->i',weights,A,p);normbound=sum(weights[n]*np.linalg.norm(A[n],2) for n in range(13));assert np.linalg.norm(Ysum)<=normbound
for v in rng.normal(size=(30,168)):
 support=sum(weights[n]*np.linalg.norm(A[n].T@v) for n in range(13));assert abs(v@Ysum)<=support
# Independent one-year erosion arithmetic and the grey bolometric tail constants.
v0=mp.mpf('1e15')*(mp.mpf('1e-23'))**(mp.mpf(1)/3);tau=mp.mpf('365.25')*86400;amax=mp.mpf('1e-5');B=mp.mpf('70000')
Tmax=B/mp.log(v0*tau/amax);assert abs(v0*tau*mp.exp(-B/Tmax)/amax-1)<mp.mpf('1e-70')
sigma=2*mp.pi**5*k**4/(15*h**3*c**2);C3=sigma*c**2/(2*mp.pi*k*ref**2)
Bnu=lambda T:2*h*ref**3/c**2/mp.expm1(ad/T)
for temp in [Tc,mp.mpf(20),mp.mpf('1e5')]:assert (sigma*temp**4/mp.pi)/Bnu(temp)>=C3*temp**3
B2=sum(w*t*t for w,t in zip(mu,Ts));B3=sum(w*t**3 for w,t in zip(mu,Ts));assert B2<=B3**(mp.mpf(2)/3)*M0**(mp.mpf(1)/3)
# Independent adaptive quadrature on the declared frequency-linear DIRBE interpolant.
rows=[]
for line in (R/'replay/source/DIRBE_SYSTEM_SPECTRAL_RESPONSE_TABLE.ASC').read_text().splitlines():
 try:vals=list(map(float,line.split()))
 except ValueError:continue
 if len(vals)==11:rows.append(vals)
arr=np.array(rows);fq=float(c)/(arr[:,0]*1e-6)/1e9;rp=arr[:,10];idx=np.argsort(fq);fq=fq[idx];rp=rp[idx]
integ=np.zeros(3);errors=np.zeros(3)
for lo,hi,rlo,rhi in zip(fq[:-1],fq[1:],rp[:-1],rp[1:]):
 if rlo==0 and rhi==0:continue
 def fn(x,kind):
  rr=rlo+(rhi-rlo)*(x-lo)/(hi-lo);r=x/353
  xx=float(h/k/Tc)*x*1e9;xd=float(ad/Tc)
  gg=(math.expm1(xd)/xd)/(math.expm1(xx)/xx)
  ww=rr*r**3.5*min(1,gg)
  return rr*(float(c)/(240e-6)/1e9)/x if kind==0 else ww if kind==1 else ww*math.log(r)
 for j in range(3):
  val,err=quad(lambda x:fn(x,j),lo,hi,epsabs=1e-13,epsrel=5e-13)
  integ[j]+=val;errors[j]+=err
xd=float(h*ref/(k*Tc));db=2*float(k)*float(ref)**2/float(c)**2*xd**2*math.exp(xd)/math.expm1(xd)**2
mplus=db*integ[1]/integ[0]/1e-20;bplus=integ[2]/integ[1]
candidate=json.loads((R/'replay/temperature_domain_followup/NUMERIC_WITNESSES.json').read_text())['MBB_uniform_passband_lower']
assert abs(mplus/candidate['DIRBE_lower_m_MJy_sr_per_K_CMB353']-1)<1e-12
assert abs(bplus-candidate['b_plus'])<1e-12
out={'status':'PASS_FINITE_INDEPENDENT_CHECKS','mpmath_dps':mp.mp.dps,'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'mpmath':mp.__version__,'kinematic_frame_checks':kin,'straddling_band_falsifier':straddle,'beta_temperature_correlation_and_row_bounds':'PASS','full_spin2_24_real_atom':{'vector':[fmt(x) for x in V],'norm':fmt(norm),'expected_norm':fmt(mp.sqrt(3/mp.pi)),'hot_atom_sequence':atom},'full_168_output_support_and_norm_algebra':'PASS; synthetic operator, not native qualification','survival_one_year_K_80dps':fmt(Tmax),'grey_bolometric_C3_Hz_per_K3':fmt(C3),'grey_bolometric_and_Holder_checks':'PASS','DIRBE_adaptive_quadrature':{'mplus':mplus,'bplus':bplus,'mplus_relative_difference':mplus/candidate['DIRBE_lower_m_MJy_sr_per_K_CMB353']-1,'bplus_difference':bplus-candidate['b_plus'],'integral_error_estimates':errors.tolist(),'qualification':'Floating numerical cross-check, no outward-rounded certified quadrature lower bound'},'elapsed_s':time.monotonic()-start,'acceptance_met':False,'qualified_products':[]}
(R/'INDEPENDENT_CHECKS.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({key:out[key] for key in ['status','survival_one_year_K_80dps','straddling_band_falsifier','DIRBE_adaptive_quadrature','elapsed_s']},indent=2))
