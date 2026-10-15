"""Local first-velocity-jet (Euclidean 1+3 limit) radial identifiability.

Metric (-,+,+,+) and orientation eps123=+1 assumed. The registered
∇_i v_j gradient here is a local nonrelativistic spatial jet, not a
global curved-spacetime tetrad optical response. No CF4 shear/omega/A/tilt
measurement follows without a correct source/radiation/matter congruence.
"""
from __future__ import annotations
import numpy as np
from .cf4_apparent_kinematic_distribution import stf2_orthonormal

MPC_KM=3.085677581491367e19
C_KM_S=299792.458


class RadialKinematicsError(ValueError):
    pass


def _gradient(g):
    a=np.asarray(g)
    if np.iscomplexobj(a) or a.shape!=(3,3) or not np.isfinite(a).all():
        raise RadialKinematicsError("finite real 3x3 velocity gradient")
    return np.asarray(a,float)


def split_local_velocity_gradient(gradient_kms_mpc):
    """G_ij=∂_i v_j, θ=tr G, σ=sym(G)-(θ/3)I, ω=antisym(G).

    Positive θ describes radial expansion; omega pseudo-vector is
    omega^k=(1/2)eps^{kij}omega_ij with eps123=+1.
    """
    g=_gradient(gradient_kms_mpc)
    expansion=float(np.trace(g))
    s=(g+g.T)*.5 -np.eye(3)*expansion/3.
    w=(g-g.T)*.5
    pseudo=np.array((w[1,2],w[2,0],w[0,1]),float)
    reconstruction=(expansion/3)*np.eye(3)+s+w
    return {
        "Theta_km_s_Mpc":expansion,
        "H_jet_km_s_Mpc":expansion/3,
        "Theta_s_inv":expansion/MPC_KM,
        "sigma_km_s_Mpc":s,
        "omega_tensor_km_s_Mpc":w,
        "omega_pseudovector_km_s_Mpc":pseudo,
        "sigma_s_inv":s/MPC_KM,
        "omega_pseudovector_s_inv":pseudo/MPC_KM,
        "roundtrip_maxabs":float(np.max(abs(reconstruction-g))),
        "claims":"LOCAL_NONRELATIVISTIC_JET_NOT_OBSERVED_COSMOLOGICAL_KINEMATICS",
    }


def radial_velocity_jet(n,gradient):
    n=np.asarray(n)
    if (np.iscomplexobj(n) or n.ndim!=2 or n.shape[1]!=3 or
        not np.isfinite(n).all() or
        not np.allclose(np.sum(n.astype(float)**2,axis=1),1,atol=1e-12)):
        raise RadialKinematicsError("unit sky directions as n×3")
    g=_gradient(gradient)
    return np.einsum("ni,ij,nj->n",n,g,n,optimize=True)


def antisymmetric_basis():
    """ω23,ω31,ω12 are the pseudo-vector components, eps123=+1."""
    b=np.zeros((3,3,3))
    for k,(i,j) in enumerate(((1,2),(2,0),(0,1))):
        b[k,i,j]=1.
        b[k,j,i]=-1.
    return b


def radial_design_rank(n, *, norm_min=1e-12):
    """Pure angular operator (not survey likelihood) STF5 and 3 vorticity modes."""
    a=np.asarray(n,float)
    if (a.ndim!=2 or a.shape[1]!=3 or len(a)<10 or
        not np.isfinite(a).all() or
        not np.allclose(np.sum(a*a,axis=1),1,atol=1e-12)):
        raise RadialKinematicsError("at least 10 complete real unit sight lines")
    T=stf2_orthonormal()
    stf=np.einsum("ni,aij,nj->na",a,T,a,optimize=True)
    vort=np.einsum("ni,aij,nj->na",a,antisymmetric_basis(),a,optimize=True)
    sig=np.linalg.svd(stf,compute_uv=False)
    norm=float(np.linalg.norm(vort))
    if norm>norm_min*np.sqrt(len(a)):
        raise RadialKinematicsError("antisymmetric radial operator lost its nullspace")
    return {
        "n":len(a),
        "source_model":"local Euclidean first velocity gradient; no optical/GR transfer",
        "shear_design":stf,
        "vorticity_design":vort,
        "stf5_singular_values":sig,
        "stf5_rank":int(np.sum(sig>sig[0]*1e-10)),
        "omega_3_mode_rank":0,
        "vorticity_design_frobenius_residual":norm,
        "four_acceleration_rank":"UNDETERMINED_FROM_THIS_OPERATOR",
        "material_relative_tilt_rank":"UNDETERMINED_FROM_THIS_OPERATOR",
    }
