"""Exact dyadic small-matrix correction audit, no author code imported."""
import time, json, sys, resource, os
from pathlib import Path
from fractions import Fraction as Q
import numpy as np
start=time.monotonic(); ROOT=Path('/mnt/extdrive/workdir/htt_open_data/r26_gaia_quotient_blind_review'); checks=[]
def dy(a):
 a=np.asarray(a); pairs=[float(x).as_integer_ratio() for x in a.flat]; den=max(d for n,d in pairs)
 return np.array([n*(den//d) for n,d in pairs],dtype=object).reshape(a.shape),den
def fmul(a,b):return a[0]@b[0],a[1]*b[1]
def fx(a):return [[Q(int(x),a[1]) for x in row] for row in a[0]]
def check(name,ok,**detail):
 o={'name':name,'pass':bool(ok),**detail};checks.append(o);print(json.dumps(o,default=str),flush=True)
 if not ok:raise AssertionError(name)
try:
 src=np.load('/mnt/extdrive/workdir/htt_open_data/r25_gaia_pair_separation/packaged/arrays.npz',allow_pickle=False)
 ss=np.load('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_quotient_certificate/INTERVALS.npz',allow_pickle=False)
 W=dy(src['W']); cd=dy(src['Cd'].reshape(117,117)); sym=(cd[0]+cd[0].T,2*cd[1])
 old=fx(fmul(fmul(W,sym),(W[0].T,W[1])))
 base=ss['S_star_center']; br=ss['S_star_radius']; cc=ss['S_star_minus_W_symCd_WT_center']; cr=ss['S_star_minus_W_symCd_WT_radius']
 violations=[]; worst=0.
 for i in range(88):
  for j in range(88):
   need=abs(Q.from_float(float(base[i,j]))-old[i][j]-Q.from_float(float(cc[i,j])))+Q.from_float(float(br[i,j]))
   r=Q.from_float(float(cr[i,j])); worst=max(worst,float(need/r))
   if need>r:violations.append((i,j,str(need-r)))
 check('exact_all_7744_symCd_correction_enclosure',not violations,worst_radius_fraction=worst,violations=violations[:10],target='S_star-W*((Cd+Cd.T)/2 exact)*W.T')
 for name,sourcekey,outkey in [('design','D','A_star'),('observed','d','z_star')]:
  shape=(117,13) if name=='design' else (117,1)
  val=fx(fmul(W,dy(src[sourcekey].reshape(shape))))
  c=ss[outkey+'_center'];r=ss[outkey+'_radius']; key='A_star_minus_WD' if name=='design' else 'z_star_minus_Wd'
  pc=ss[key+'_center'];pr=ss[key+'_radius'];bad=[];worst=0.
  for i,row in enumerate(val):
   for j,x in enumerate(row):
    need=abs(Q.from_float(float(c[i,j]))-x-Q.from_float(float(pc[i,j])))+Q.from_float(float(r[i,j])); rr=Q.from_float(float(pr[i,j]));worst=max(worst,float(need/rr))
    if need>rr:bad.append((i,j))
  check('exact_'+name+'_saved_response_correction_enclosure',not bad,worst_radius_fraction=worst,violations=bad)
 # Exact F-center*y and its radius, using integer contractions (88 by 9512).
 fc=dy(ss['F_center']);fr=dy(ss['F_radius']);y=dy(src['y'].reshape(9512,1))
 fcy=fx(fmul(fc,y));fry=fx(fmul(fr,(abs(y[0]),y[1])))
 zc=ss['z_star_center'];zr=ss['z_star_radius'];pc=ss['z_star_minus_WHy_center'];pr=ss['z_star_minus_WHy_radius'];bad=[];worst=0.
 for i in range(88):
  need=abs(Q.from_float(float(zc[i,0]))-fcy[i][0]-Q.from_float(float(pc[i,0])))+Q.from_float(float(zr[i,0]))+fry[i][0]
  rr=Q.from_float(float(pr[i,0]));worst=max(worst,float(need/rr))
  if need>rr:bad.append(i)
 check('exact_interval_source_pushforward_correction_enclosure',not bad,worst_radius_fraction=worst,violations=bad,target='z_star-W H y using saved proved F enclosure')
 # Exact sampled source contractions bound input-ball uncertainty without float sums.
 # Sampling is a falsifier; full enclosure proof remains the reviewed algorithm.
 fc=ss['Fstar_center'];fr=ss['Fstar_radius'];X=src['X'].reshape(9512,13); yy=src['y'].reshape(9512)
 for i,j in [(0,0),(43,6),(87,12)]:
  cv=sum((Q.from_float(float(fc[i,k]))*Q.from_float(float(X[k,j])) for k in range(9512)),Q())
  rv=sum((Q.from_float(float(fr[i,k]))*abs(Q.from_float(float(X[k,j]))) for k in range(9512)),Q())
  need=abs(cv-Q.from_float(float(ss['A_star_center'][i,j])))+rv
  check('sample_exact_design_contraction_'+str(i)+'_'+str(j),need<=Q.from_float(float(ss['A_star_radius'][i,j])))
 for i in [0,43,87]:
  cv=sum((Q.from_float(float(fc[i,k]))*Q.from_float(float(yy[k])) for k in range(9512)),Q())
  rv=sum((Q.from_float(float(fr[i,k]))*abs(Q.from_float(float(yy[k]))) for k in range(9512)),Q())
  need=abs(cv-Q.from_float(float(ss['z_star_center'][i,0])))+rv
  check('sample_exact_observation_contraction_'+str(i),need<=Q.from_float(float(ss['z_star_radius'][i,0])))
 status='PASS'
except BaseException as e:
 status='FAIL';error=repr(e);print('FIRST_FAILURE',error,flush=True)
finally:
 (ROOT/'raw'/'correction_checks.json').write_text(json.dumps({'status':status,'checks':checks,'elapsed_seconds':time.monotonic()-start,'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'pid':os.getpid(),'error':locals().get('error')},indent=2)+'\n')
 sys.exit(0 if status=='PASS' else 1)
