"""Plot generated conditional quantities; no catalogue fitting or ODE."""
import importlib.util
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('optics', HERE/'theory/verify_two_redshift_null.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
z=np.geomspace(.003,.3,120)
bound=np.array([m.exact_tube(float(x),.0002,.0005) for x in z])
r=json.loads((HERE/'k03/RESULT.json').read_text())
cov=np.array(r['covariance_g_uas2_yr2'])[1:,1:]
e,u=np.linalg.eigh(cov)
t=np.linspace(0,2*np.pi,361)
ellipse=np.array(r['mean_g_uas_yr'])[1:,None]+u@np.diag(np.sqrt(e*r['conditional_95_ellipsoid']['q_threshold']))@np.array([np.cos(t),np.sin(t)])
fig,ax=plt.subplots(1,2,figsize=(10.5,4),layout='constrained')
ax[0].fill_between(z,1000*bound[:,0],1000*bound[:,1],color='#197b8d',alpha=.3)
ax[0].plot(z,1000*bound[:,0],color='#197b8d');ax[0].plot(z,1000*bound[:,1],color='#197b8d')
ax[0].axhline(0,color='black',lw=.7);ax[0].set_xscale('log')
ax[0].set(xlabel='Reference redshift',ylabel='Residual defect (mmag)',title='A. Manufactured finite correction tube')
ax[0].text(.98,.98,'|eta| <= 0.0002\n|kappa| <= 0.5 mmag\nSpecified analytic chi; not measured bounds',ha='right',va='top',transform=ax[0].transAxes,fontsize=8)
ax[1].fill(ellipse[0],ellipse[1],color='#d36c32',alpha=.25)
ax[1].plot(ellipse[0],ellipse[1],color='#d36c32')
ax[1].plot(r['mean_g_uas_yr'][1],r['mean_g_uas_yr'][2],'o',color='#833c17')
ax[1].set(xlabel='ICRS g_y (microarcsec/year)',ylabel='ICRS g_z (microarcsec/year)',title='B. Published observer E1 working summary')
ax[1].set_aspect('equal',adjustable='datalim')
ax[1].text(.02,.02,'Projection of nominal joint 95% ellipsoid\nRounded ICRS covariance only\nNo total-systematics or cosmic coverage',transform=ax[1].transAxes,fontsize=8,va='bottom')
for a in ax:a.grid(alpha=.18)
fig.savefig(HERE/'conditional_results.png',dpi=180)
fig.savefig(HERE/'conditional_results.pdf')
print('Generated conditional_results.png and .pdf')
