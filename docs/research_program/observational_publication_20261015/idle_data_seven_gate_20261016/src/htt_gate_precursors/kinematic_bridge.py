"""V03/K03 algebraic identifiability with explicit observational nuisance subspaces."""
import numpy as np


def history_matrix(q1:float,q2:float,with_local_anchor:bool=False):
    """d_i = beta_O + beta_M0 + <q>_i beta_M1.

    A calibrated independent aberration measurement of beta_O is added only
    in with_local_anchor=True lane. Not a physical global-tilt transfer.
    """
    F=np.array([[1,1,q1],[1,1,q2]],dtype=float)
    if with_local_anchor:
        F=np.vstack((F,[1,0,0]))
    return F


def sky_sample(n:int,seed:int):
    rng=np.random.default_rng(seed);a=rng.normal(size=(n,3))
    return a/np.linalg.norm(a,axis=1)[:,None]


def _unit_response(n):
    """Per direction radial scalar and ideal distance-normalized proper motion.

    For v(r n)=G (r n), radial v/r=n.G.n and tangent v_perp/r=P G n.
    Galaxies additionally have frame spin and apparent glide nuisances;
    quasars have frame terms only (no matter gradient).
    """
    I=np.eye(3);n=np.asarray(n,dtype=float)
    if n.shape!=(3,) or not np.isclose(n@n,1,atol=1e-10):
        raise ValueError('unit direction')
    P=I-n[:,None]@n[None,:]
    A=np.zeros((4,9));frame=np.zeros((4,6))
    for a in range(3):
        for b in range(3):
            G=np.zeros((3,3));G[a,b]=1
            A[0,3*a+b]=n@G@n
            A[1:,3*a+b]=P@G@n
    for a in range(3):
        frame[1:,a]=np.cross(I[a],n)
        frame[1:,3+a]=P@I[a]
    return A,frame


def frame_calibration_design(galaxy_directions,quasar_directions=None):
    G=[];N=[]
    for n in galaxy_directions:
        g,f=_unit_response(n);G.append(g);N.append(f)
    fullG=np.concatenate(G,axis=0);fullN=np.concatenate(N,axis=0)
    if quasar_directions is not None:
        for n in quasar_directions:
            _,f=_unit_response(n)
            # Quasar transverse proper motion only: frame spin/glide,
            # no radial luminosity distance/galaxy velocity-gradient response.
            fullG=np.vstack((fullG,np.zeros((3,9))))
            fullN=np.vstack((fullN,f[1:,:]))
    return np.column_stack((fullG,fullN))


def source_matrix_rank(F,rtol=1e-11):
    ss=np.linalg.svd(F,compute_uv=False)
    if ss.size==0:return 0,ss
    return int(np.count_nonzero(ss>rtol*ss[0])),ss
