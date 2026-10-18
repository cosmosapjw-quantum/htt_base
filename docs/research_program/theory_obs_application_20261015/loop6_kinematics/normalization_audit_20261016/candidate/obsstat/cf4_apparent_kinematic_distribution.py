"""Selection-UNQUALIFIED, actual-source conditional CF4 angular Hubble law.

This is a read-only exploratory WLS distribution of the five tracefree
angular distance-modulus residual coefficients. Its parameter names
explicitly distinguish the apparent Hubble quadrupole from physical
sigma_ab/H, matter/geometry tilt, acceleration and vorticity.

All observations are the official published CF4 group DMzp, e_DMzp,
Vcmb, RA, DEC. The correlations between groups, source/calibration
methods and the sample selection function are NOT public in this raw
group table, so the output MUST NOT be called a physical posterior.
"""
from __future__ import annotations
import numpy as np
from scipy.special import roots_legendre
from scipy.linalg import solve_triangular

C_KMS=299792.458
KAPPA=5/np.log(10)


class Cf4KinematicInputError(ValueError):
    pass


def xyz_from_equatorial(ra_deg,dec_deg):
    if np.iscomplexobj(ra_deg) or np.iscomplexobj(dec_deg):
        raise Cf4KinematicInputError('real J2000 angular sky required')
    ra=np.asarray(ra_deg,float);dec=np.asarray(dec_deg,float)
    if ra.ndim!=1 or ra.shape!=dec.shape or not np.isfinite(ra).all() or not np.isfinite(dec).all() or np.any((ra<0)|(ra>=360)) or np.any(abs(dec)>90):
        raise Cf4KinematicInputError('RA in [0,360), Dec in [-90,90], finite equal arrays')
    a=np.deg2rad(ra); b=np.deg2rad(dec)
    c=np.cos(b)
    return np.column_stack((c*np.cos(a),c*np.sin(a),np.sin(b)))


def stf2_orthonormal():
    """Five Frobenius-orthonormal STF tensors, order xx-yy, xx+yy-2zz, xy,xz,yz."""
    T=np.zeros((5,3,3),float)
    T[0]=np.diag([1,-1,0])/np.sqrt(2)
    T[1]=np.diag([1,1,-2])/np.sqrt(6)
    for k,(i,j) in enumerate(((0,1),(0,2),(1,2)),2):
        T[k,i,j]=T[k,j,i]=1/np.sqrt(2)
    return T


def radial_velocity_gradient(n,grad):
    a=np.asarray(n,float);g=np.asarray(grad,float)
    if a.ndim!=2 or a.shape[1]!=3 or g.shape!=(3,3):
        raise Cf4KinematicInputError('n x3 and velocity gradient 3x3 expected')
    return np.einsum('ni,ij,nj->n',a,g,a,optimize=True)


def luminosity_distance_flat_lcdm(z,H0=74.6,omega_m=.3153,quadrature=20):
    """Dimensionful dL [Mpc] and dimensionless integral I(z), d ln dL/dz.

    CMB-frame Vcmb/c is taken as redshift PROXY, not a native heliocentric
    source redshift. The assumed flat reference cosmographic background
    is NOT fitted. Intercept-free method nuisance absorbs global H scale.
    """
    if np.iscomplexobj(z):
        raise Cf4KinematicInputError('real redshifts expected')
    zz=np.asarray(z,float)
    if (zz.ndim!=1 or len(zz)<1 or not np.isfinite(zz).all()
        or np.any((zz<=0)|(zz>.5)) or H0<=0 or not np.isfinite(H0)
        or not 0<omega_m<1 or not np.isfinite(omega_m)):
        raise Cf4KinematicInputError('physical positive reference z,H0,Omega_m expected')
    nodes,weights=roots_legendre(quadrature)
    t=zz[:,None]*(nodes[None,:]+1)/2
    E=np.sqrt(omega_m*(1+t)**3+1-omega_m)
    I=(zz/2)*np.sum(weights[None,:]/E,axis=1)
    dL=C_KMS/H0*(1+zz)*I
    Eend=np.sqrt(omega_m*(1+zz)**3+1-omega_m)
    logder=1/(1+zz)+1/(I*Eend)
    return dL,I,logder


def model_matrix(z,n,method,*,include_method_slope=True,include_bulk=True,
                 include_angular_dipole=True,omega_m=.3153,H0=74.6):
    """Conditional linearization mu_i-mu_FLRW(z_i)=X beta + noise.

    Angular shear coefficient vector a: H(n)/H0 = 1 + sum_a a_a T_a:n n.
    delta_mu ≈ -(5/ln10)sum_a a_a(T_a:n n), ONLY IF it is true
    directional expansion with no velocity/curvature/selection mixing.

    Independent method offsets & optional method-specific log(z) slopes
    allow strong subset-zero-point/distance-selection flexibility.
    Bulk term is velocity (km/s) whose redshift perturbation scales as
    -(5/ln10)(1+z)(d ln dL/dz)/c n dot b. A redshift independent
    angular dipole is a generic nuisance, NOT a measured 4-acceleration.
    """
    zz=np.asarray(z,float);nn=np.asarray(n,float);ff=np.asarray(method).astype('U32')
    if (zz.ndim!=1 or nn.shape!=(len(zz),3) or ff.shape!=(len(zz),)
        or not np.isfinite(nn).all() or
        not np.allclose(np.sum(nn**2,axis=1),1,atol=2e-13)):
        raise Cf4KinematicInputError('source redshift, unit angles and method labels must align')
    dL,I,loggrad=luminosity_distance_flat_lcdm(zz,omega_m=omega_m,H0=H0)
    methods=sorted(np.unique(ff))
    if len(methods)<1 or any(not m for m in methods):
        raise Cf4KinematicInputError('real source method families required')
    components=[];slices={};start=0
    def register(name,arr):
        nonlocal start
        components.append(arr);slices[name]=slice(start,start+arr.shape[1]);start+=arr.shape[1]
    indicator=(ff[:,None]==np.asarray(methods)[None,:]).astype(float)
    register('method_intercepts',indicator)
    if include_method_slope:
        logz=np.log(zz)
        # subtract within-method weighted-independent centroid to remove
        # intercept/slope near collinearity; weights supplied to estimator.
        centroid=np.asarray([np.mean(logz[ff==j]) for j in methods])
        zfeatures=indicator*(logz[:,None]-centroid[None,:])
        if np.any(np.max(abs(zfeatures),axis=0)<1e-8):
            raise Cf4KinematicInputError('method z-depth slope unavailable')
        register('method_depth_slopes',zfeatures)
    if include_bulk:
        velocity=-KAPPA*((1+zz)*loggrad/C_KMS)[:,None]*nn
        register('bulk',velocity)
    if include_angular_dipole:
        register('angular_dipole',-KAPPA*nn)
    response=np.einsum('ni,tij,nj->nt',nn,stf2_orthonormal(),nn,optimize=True)
    register('shear',-KAPPA*response)
    return {'design':np.column_stack(components),'slices':slices,'methods':methods,
            'reference_mu_mag':25+5*np.log10(dL),
            'redshift_velocity_width_basis_mag_per_kms':KAPPA*((1+zz)*loggrad/C_KMS),
            'source_units':'DMzp/eDMzp mag, Vcmb km/s, H0 km/s/Mpc, bulk km/s; shear is dimensionless',
            'model':'selected source approximate flat LCDM luminosity distance and linear apparent angular Hubble law'}


def weighted_lsq(X,y,sigma,*,max_cond=1e10):
    x=np.asarray(X,float);v=np.asarray(y,float);s=np.asarray(sigma,float)
    if (x.ndim!=2 or v.shape!=(len(x),) or s.shape!=(len(x),)
        or x.shape[1]>=len(x) or not np.isfinite(x).all()
        or not np.isfinite(v).all() or not np.isfinite(s).all()
        or np.any(s<=0)):
        raise Cf4KinematicInputError('finite positive errors, full column WLS expected')
    A=x/s[:,None]; b=v/s
    scales=np.linalg.norm(A,axis=0)
    if np.any(scales<=0) or not np.isfinite(scales).all():
        raise Cf4KinematicInputError('zero source model column')
    U=A/scales
    # QR of normalized columns prevents the km/s vs dimensionless
    # unit difference from spoiling the condition check.
    Q,R=np.linalg.qr(U,mode='reduced')
    evals=np.linalg.svd(R,compute_uv=False)
    cond=float(evals[0]/evals[-1])
    if evals[-1]<=0 or cond>max_cond:
        raise Cf4KinematicInputError(f'weighted source design unidentifiable; normalized cond={cond:g}')
    coeff=solve_triangular(R,Q.T@b,lower=False)/scales
    inverseR=solve_triangular(R,np.eye(R.shape[0]),lower=False)
    cov=(inverseR@inverseR.T)/scales[:,None]/scales[None,:]
    residual=(v-x@coeff)/s
    grad=(U.T@residual)
    return {'beta':coeff,'cov':(cov+cov.T)/2,
       'chisq':float(residual@residual),
       'dof':len(v)-len(coeff),
       'rank':len(coeff),'condition_scaled':cond,
       'qr_orthonormality_residual':float(np.max(abs(Q.T@Q-np.eye(len(R))))),
       'normal_gradient_scaled':float(np.linalg.norm(grad)/(np.linalg.norm(Q.T@b)+1e-300)),
       'fitted_mu_residual':x@coeff,
       'standardized_residual':residual}


def profile_identified_shear_fraction(X,sigma,slices):
    """Fraction of five-direction design energy retained after nuisance projection."""
    idx=slices['shear']
    theta=np.asarray(X,float)[:,idx]/np.asarray(sigma,float)[:,None]
    other=np.r_[np.arange(idx.start),np.arange(idx.stop,X.shape[1])]
    nuisance=np.asarray(X,float)[:,other]/np.asarray(sigma,float)[:,None]
    Q,_=np.linalg.qr(nuisance,mode='reduced')
    residual=theta-Q@(Q.T@theta)
    frac=float(np.sum(residual*residual)/np.sum(theta*theta))
    singular=np.linalg.svd(residual,compute_uv=False)
    return {'relative_stf2_design_energy_after_nuisance':frac,
            'profiled_shear_condition':float(singular[0]/singular[-1])}


def posterior_shear_proxy(mean,cov,sl,*,draws=20000,seed=20261015):
    """Conditional Gaussian image of a five-component *apparent* STF tensor.

    Let A_ij=sum_A a_A T_Aij with Frobenius-orthonormal STF basis. Then
    A_ij A_ij = ||a||_2**2 exactly. If, and ONLY IF, A_ij = sigma_ij/H
    for a single physically qualified observer congruence, the standard
    shear scalar sigma²=sigma_ij sigma_ij/2 gives sigma/H=||a||/sqrt(2),
    sigma/theta=||a||/(3 sqrt(2)) and Sigma²=||a||²/6 (theta=3H).

    This is a conditional numerical normalization, not a GR/CF4 physical
    identification. Earlier source products used ||a|| and ||a||/3 in
    keys named sigma_over_H and sigma_over_theta. Those older bytes are
    historical, not silently reinterpreted or made scientifically physical.
    """
    m=np.asarray(mean,float)[sl];cc=np.asarray(cov,float)[sl,sl]
    if (m.shape!=(5,) or cc.shape!=(5,5)
        or not np.isfinite(m).all() or not np.isfinite(cc).all()
        or not np.allclose(cc,cc.T,rtol=1e-12,atol=1e-14)
        or np.linalg.eigvalsh(cc)[0]<=0
        or isinstance(draws,(bool,np.bool_)) or not isinstance(draws,(int,np.integer))
        or not 1<=draws<=1000000):
        raise Cf4KinematicInputError('finite symmetric positive-definite five-STF covariance, positive finite draws needed')
    rng=np.random.default_rng(seed)
    v=rng.multivariate_normal(m,cc,size=draws)
    coefficient_norm=np.linalg.norm(v,axis=1)
    sigma_over_H=coefficient_norm/np.sqrt(2.)
    sigma_over_theta=sigma_over_H/3.
    hubble_normalized_shear_squared=(coefficient_norm**2)/6.
    scale=np.asarray([.025,.16,.5,.84,.975])
    return {
        'normalization_contract': 'frobenius_orthonormal_stf2: AijAij=sum(a_A²); sigma²=sigma_ij sigma_ij/2; theta=3H',
        'historical_v1_mean_sigma_over_theta_was_coefficient_norm_divided_by_three': True,
        'median_STF_coefficient_frobenius_norm':float(np.median(coefficient_norm)),
        'quantiles_025_16_50_84_975_STF_coefficient_norm':np.quantile(coefficient_norm,scale).tolist(),
        'median_sigma_over_H':float(np.median(sigma_over_H)),
        'quantiles_025_16_50_84_975_sigma_over_H':np.quantile(sigma_over_H,scale).tolist(),
        'mean_sigma_over_theta':float(np.mean(sigma_over_theta)),
        'quantiles_025_16_50_84_975_sigma_over_theta':np.quantile(sigma_over_theta,scale).tolist(),
        'quantiles_025_16_50_84_975_apparent_Sigma2_std':np.quantile(hubble_normalized_shear_squared,scale).tolist(),
        'sampling_scope':'FORMAL_FIXED_SOURCE_GAUSSIAN_CONDITIONAL; SHEAR_NORMALIZATION_IF_A_EQUALS_SIGMA_OVER_H; NOT PHYSICAL SHEAR DISTRIBUTION',
        'n_draws':int(draws)}
