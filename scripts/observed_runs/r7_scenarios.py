"""Declared analytical scenarios used by the R7 methods figures."""
import math
from fractions import Fraction as F
import numpy as np
from scipy.special import eval_legendre
from scipy.stats import chi2
from common.r7_contracts import AcceptanceResult,RadiationJet
from common.r7_radiation_jet import kinematics_from_radiation_jet
from htt.infer.r7_confidence import PhysicalDomain,PhysicalRegion,project_joint_region
from htt.infer.r7_mes_region import AffineRatioFunctional,affine_box_gf_bound


def high_source_regions():
    # y=theta+h+e; e~N(0,1). Fixed illustrative observations y=1,z=.25.
    # H3: h~N(0,1), z=h+nu, nu~N(0,.25), all primitive errors independent.
    # Project the full two-dimensional joint acceptance ellipsoid, not a Wilks fit.
    y=1.;z=.25;c1=chi2.ppf(.95,1);c2=chi2.ppf(.95,2)
    center=y-z/1.25;width=np.sqrt(1.2*(c2-z*z/1.25))
    return {'scope':'Declared scalar Gaussian scenarios, illustrative fixed y=1,z=.25; no observed sky',
        'H0':{'region':None,'status':'UNBOUNDED','law':'unrestricted deterministic h; quotient rank zero'},
        'H1':{'region':[y-1-np.sqrt(c1),y+1+np.sqrt(c1)],'law':'|h|<=1; union over known-noise 95% acceptance'},
        'H2':{'region':[y-np.sqrt(2*c1),y+np.sqrt(2*c1)],'law':'h~N(0,1) marginalized'},
        'H3':{'region':[center-width,center+width],'law':'joint y,z Gaussian covariance [[2,1],[1,1.25]], rank-two 95% ellipsoid projection'}}


def finite_mask_scenario():
    # Axial continuum polynomial quadrature for a single source Y_70. y includes
    # all ell0..5; only m=0 cross terms survive by azimuthal orthogonality.
    # Gauss-Legendre order32 integrates these polynomial entries through degree18.
    mu,weight=np.polynomial.legendre.leggauss(32);y=np.column_stack([np.sqrt((2*l+1)/(4*np.pi))*eval_legendre(l,mu) for l in range(6)])
    p=eval_legendre(7,mu);dp=7*(eval_legendre(6,mu)-mu*p)/(1-mu*mu)
    g=np.sqrt(15/(4*np.pi))*(mu*p-(1-mu*mu)*dp)
    m0=(1+mu)**2/4;E=y.T@((2*np.pi*weight*m0)[:,None]*y);A=y.T@(2*np.pi*weight*m0*g)
    full=y.T@(2*np.pi*weight*g)
    if np.linalg.norm(full)>1e-12:raise ValueError('full sky forbidden cross coupling failed')
    t=np.geomspace(1e-5,.05,40);f=t/3;singular=[];cost=[]
    for v in t:
        k=(-v*np.linalg.solve(np.eye(6)-v*E,A))[2:]
        singular.append(np.linalg.norm(k));cost.append(1/np.linalg.norm(k)**2)
    # Loose rigorous analytic supremum: |P7|<=1, |P7'|<=28 on [-1,1].
    sup_g=29*np.sqrt(15/(4*np.pi));cL=4*np.pi*np.sqrt(36/(4*np.pi))*sup_g
    bounds=cL*f/(1-36*f)
    return {'scope':'Continuum axial soft mask m=t(1+mu)^2/4, Y70 first-order thermal generator; ell0..5 fitted,2..5 retained',
        'mask_fraction':f,'singular_value':singular,'unit_displacement_minimum_cost':cost,'T5_norm_bound':bounds,
        'quadrature_order':32,'polynomial_degree_ceiling':18,'full_sky_cross_residual':float(np.linalg.norm(full)),
        'status':'NUMERICAL_CONTINUUM_POLYNOMIAL_ORACLE; binary64 quadrature has no certified roundoff enclosure',
        'cost_direction':'unit displacement along this one-column image; other directions have infinite cost'}


def mes_scenarios():
    values=np.linspace(-.5,.5,51);q=np.diag([1e-5,-1e-5,0.]);theta=3.;tbar=2.7255
    norms=[]
    for amplitude in values:
        jet=RadiationJet(theta,tbar,'OUTWARD','SCENARIO_FRAME','FIXED_SKY_VARYING_JET',q=q,q_dot=amplitude*q,
            tbar_dot=0.,grad_d=np.zeros((3,3)),div_o=np.zeros((3,3)),curl_d=np.zeros((3,3)),
            curl_d_dot=np.zeros((3,3)),curl_div_q=np.zeros((3,3)))
        state=kinematics_from_radiation_jet(jet);norms.append(np.linalg.norm(state.shear))
    domain=PhysicalDomain('DECLARED_BOX',('x',),lambda t,e:True,((-1.,1.),),([0.],))
    region=PhysicalRegion(None,domain,None,lambda t,e:AcceptanceResult(True,0.,1,1.,abs(t[0])<.2,'RESOLVED'),.95,'fixture',('SCENARIO',))
    gf=AffineRatioFunctional('signed_GF',F(-1),F(2),(F(1),),(F(1),))
    projection=project_joint_region(region,gf,affine_box_gf_bound)
    return {'scope':'Same observed Q, independently varied supplied q_dot; first-order geodesic collisionless scenario only',
        'rate_parameter_per_s':values,'normalized_shear_norm':norms,'Theta_per_s':theta,'temperature_K':tbar,
        'same_state_GF':projection,'GF_description':'(-1+x)/(2+x); accepted |x|<.2, box outer relaxation [-1,1], feasible witness x=0'}
