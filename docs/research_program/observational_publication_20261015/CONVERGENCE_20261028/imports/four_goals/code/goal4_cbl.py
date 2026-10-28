"""Finite optical/CBL algebra and opacity envelopes; no solver or ODE.
Run: OPENBLAS_NUM_THREADS=1 python code/goal4_cbl.py
"""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import logm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

WROOT=Path(__file__).resolve().parents[1]
I=np.eye(2,dtype=complex);s1=np.array([[0,1],[1,0]],complex);s2=np.array([[0,-1j],[1j,0]]);s3=np.diag([1.,-1.]).astype(complex)
A=1j*s2/9;Bg=1j*s3/5
comm=lambda X,Y:X@Y-Y@X
jordan=lambda X,Y:(X@Y+Y@X)/2

def covjets(X,Xp,Xpp,con=A,conp=None):
    if conp is None:conp=np.zeros((2,2),complex)
    return Xp+comm(con,X),Xpp+comm(conp,X)+2*comm(con,Xp)+comm(con,comm(con,X))

def mcbl(X,Xp,Xpp,H,Hp,con=A,conp=None):
    v,a=covjets(X,Xp,Xpp,con,conp)
    return I+H*H*(jordan(X,a)-v@v)+H*Hp*jordan(X,v)

zg=np.linspace(.05,1.5,201);identity_residual=0.;gauge_residual=0.;noncomm=0.;mineig=1e9
for zz in zg:
    W=(2+zz/4)*I+zz*s1/7+(.2+zz*zz/11)*s3
    Wp=I/4+s1/7+2*zz*s3/11;Wpp=2*s3/11
    d=zz+zz*zz/5;dp=1+2*zz/5;dpp=.4;H=1+zz/3;Hp=1/3
    D=d*W;Dp=dp*W+d*Wp;Dpp=dpp*W+2*dp*Wp+d*Wpp
    cv=1+H*H*(d*dpp-dp*dp)+H*Hp*d*dp
    DW,D2W=covjets(W,Wp,Wpp)
    lhs=mcbl(D,Dp,Dpp,H,Hp)
    rhs=I+(cv-1)*(W@W)+d*d*(H*H*(jordan(W,D2W)-DW@DW)+H*Hp*jordan(W,DW))
    identity_residual=max(identity_residual,np.linalg.norm(lhs-rhs))
    noncomm=max(noncomm,np.linalg.norm(comm(W,DW)))
    mineig=min(mineig,np.linalg.eigvalsh(W).min())
    U=np.diag([np.exp(1j*zz/5),np.exp(-1j*zz/5)]);Ud=U.conj().T
    Dg=U@D@Ud;Dgp=U@(Dp+comm(Bg,D))@Ud
    Dgpp=U@(Dpp+2*comm(Bg,Dp)+comm(Bg,comm(Bg,D)))@Ud
    Ag=U@A@Ud-Bg;Agp=U@comm(Bg,A)@Ud
    cg=mcbl(Dg,Dgp,Dgpp,H,Hp,Ag,Agp)
    gauge_residual=max(gauge_residual,np.linalg.norm(cg-U@lhs@Ud))
assert identity_residual<1e-12 and gauge_residual<1e-12

# Calibrated positive source/effect tomography in an orthonormal Hermitian basis.
paulis=[np.eye(2),np.array(s1,dtype=complex),np.array(s2,dtype=complex),np.array(s3,dtype=complex)]
E=[p/np.sqrt(2) for p in paulis]
states=[paulis[0]/2]+[(paulis[0]+p)/2 for p in paulis[1:]]
M=np.array([[np.trace(R@a).real*np.trace(b@L).real for a in E for b in E] for R in states for L in states])
K=np.diag([1/3,1/5]);Ac=np.array([[np.trace(a@K@b@K.T).real for b in E] for a in E])
y=M@Ac.ravel();rec=np.linalg.solve(M,y).reshape(4,4)
err=np.linalg.norm(rec-Ac)
Q=K.T@K;lam=np.linalg.eigvalsh(Q);distance_upper=1/np.sqrt(lam[-1]);tmin=.1;distance_lower=np.sqrt(tmin/lam[0])
Xi=lambda Q:logm(Q)-np.trace(logm(Q))*np.eye(2)/2
xi_scaling_error=np.linalg.norm(Xi(Q)-Xi(.4*Q))
vec=K.ravel(order='F');J=np.outer(vec,vec.conj())
rank_filter=int(np.linalg.matrix_rank(J));rank_depol=int(np.linalg.matrix_rank(np.eye(4)/2))
gamma=.3;K0=np.diag([1.,np.sqrt(1-gamma)]);K1=np.array([[0,np.sqrt(gamma)],[0,0]])
Qin=K0.T@K0+K1.T@K1;Qout=K0@K0.T+K1@K1.T

# Fixed flat de Sitter geometry, d=z and H=c=1. Tau(0)=0 except
# the explicitly labelled constant calibration example.
grid=np.linspace(0,1.5,301)
tau=.2*grid;dr=grid*np.exp(tau/2)
Cr=1-np.exp(tau)
corrected=1+np.exp(-tau)*(Cr-1)
assert np.max(abs(corrected))<1e-14
# A pointwise outer set from 0<=tau<=0.3, |tau'|<=0.25,
# |tau''|<=0.02, H'=0. Box extrema are conservative, not assumed
# simultaneously attained by a common C2 opacity function.
tau_upper=.3;B=dr**2*.02/2
xlo=Cr-1-B;xhi=Cr-1+B;tl=np.exp(-tau_upper);th=1.
corners=np.stack([tl*xlo,tl*xhi,th*xlo,th*xhi])
lo=1+corners.min(axis=0);hi=1+corners.max(axis=0)
assert np.all(lo<=1e-14) and np.all(hi>=-1e-14)
# Lower-derivative curvature estimator under unknown first opacity derivative.
# kappa=(H^2 d'^2/c^2-1)/d^2, physical curvature units inverse length^2.
drp=np.exp(tau/2)*(1+.1*grid)
mask=grid>0
kappa_naive=np.zeros_like(grid);kappa_corrected=np.zeros_like(grid)
kappa_naive[mask]=(drp[mask]**2-1)/dr[mask]**2
kappa_corrected[mask]=((drp[mask]-.1*dr[mask])**2-np.exp(tau[mask]))/dr[mask]**2
assert np.max(abs(kappa_corrected[mask]))<1e-10

fig,ax=plt.subplots(1,3,figsize=(14,4),layout='constrained')
ax[0].plot(grid,Cr,label=r'Observed $C[d_r]$, $\tau=0.2z$')
ax[0].axhline(1-1.1**2,ls=':',color='tab:purple',label=r'Constant calibration $d_r=1.1d$')
ax[0].plot(grid,corrected,color='black',label='Opacity-corrected geometry')
ax[0].set(xlabel='Redshift z',ylabel='CBL residual',title='Flat geometry can have a nonzero flux residual');ax[0].legend(fontsize=8)
ax[1].fill_between(grid,lo,hi,alpha=.25,label='Declared opacity-derivative outer set')
ax[1].plot(grid,Cr,color='tab:orange',label='Naive residual');ax[1].axhline(0,color='black',ls='--',label='True geometric residual')
ax[1].set(xlabel='Redshift z',ylabel='Compatible geometric C',title='Report a set before assigning a geometric cause');ax[1].legend(fontsize=8)
ax[2].plot(grid[mask],kappa_naive[mask],label='Uncorrected curvature estimator')
ax[2].plot(grid[mask],kappa_corrected[mask],color='black',label='Corrected (zero)')
ax[2].set(xlabel='Redshift z',ylabel=r'$\kappa$ in $(H_0/c)^2$',title='First-derivative alternative; avoid the vertex',ylim=(-.05,2));ax[2].legend(fontsize=8)
fig.suptitle('Goal 4: finite optical-response checks on an analytic flat de Sitter control',fontsize=13)
for ext in ['png','pdf']:fig.savefig(WROOT/f'figures/goal4_cbl_opacity.{ext}',dpi=170)
out={'scope':'New finite algebra/quadrature-free matrix checks and synthetic opacity calculation; no observed data, solver or ODE.',
 'matrix_jordan_numeric_residual':float(identity_residual),'covariant_gauge_numeric_residual':float(gauge_residual),'noncommutator_max_F':float(noncomm),'min_W_eigenvalue':float(mineig),
 'tomography_design_rank':int(np.linalg.matrix_rank(M)),'tomography_design_condition':float(np.linalg.cond(M)),'tomography_reconstruction_F_error':float(err),'distance_identified_interval_with_TNI':[0,float(distance_upper)],'distance_identified_interval_with_TNI_lower_open':True,'distance_interval_with_transmission_lower_0p1':[float(distance_lower),float(distance_upper)],
 'grey_scaling_Xi_residual':float(xi_scaling_error),'filter_Choi_rank':rank_filter,'filter_is_unitary':False,'depolarizing_Choi_rank':rank_depol,'amplitude_damping_Astar_I':Qin.tolist(),'amplitude_damping_A_I':Qout.tolist(),
 'linear_opacity_at_z1p5':float(tau[-1]),'naive_CBL_at_z1p5':float(Cr[-1]),'constant_calibration_CBL':1-1.1**2,'corrected_CBL_max_residual':float(np.max(abs(corrected))),'opacity_outer_interval_at_z1p5':[float(lo[-1]),float(hi[-1])],'corrected_curvature_max_residual':float(np.max(abs(kappa_corrected[mask])))}
(WROOT/'lanes/GOAL4_CHECKS.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
