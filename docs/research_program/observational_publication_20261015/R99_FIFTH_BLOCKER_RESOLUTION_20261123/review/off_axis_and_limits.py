import numpy as np, platform, scipy
from scipy.integrate import quad_vec
from scipy.optimize import brentq
from bass.transport.finite_redshift_optics import OpticalHistory, finite_redshift_beams
from bass.recombination.reionization import SEC_PER_MPC
from scripts.r99 import gaia_shared_field as ga, cf4_source_law as cf
print(platform.python_version(), np.__version__, scipy.__version__, platform.machine())
N=np.linspace(-1.3,0,81); k=len(N); h=np.array([.86,1.04,1.10]); be=np.array([.02,.03,-.01]); bo=np.array([.03,-.02,.04])
H=lambda h,be:OpticalHistory(N,np.ones(k),np.tile(np.diag(h-1),(k,1,1)),np.zeros((k,3)),np.zeros((k,3,3)),h_reference_si=1/SEC_PER_MPC,emitter_beta=np.tile(be,(k,1)))
sky=np.array([1.,-2.,3.]); sky/=np.linalg.norm(sky); goal=.51
out=finite_redshift_beams(H(h,be),[sky],[goal],n_min=-1.,sky_frame='observed',observer_beta=bo)
def exact_point(n):
    g=1/np.sqrt(1-bo@bo); k0=(g*(1-bo@n)); P=-n + ((g-1)*(-n@bo)/(bo@bo)+g)*bo
    def EP(t): return np.linalg.norm(P*np.exp(-h*t))
    def z(t): return (EP(t)-be@(P*np.exp(-h*t)))/np.sqrt(1-be@be)-1
    te=brentq(lambda t:z(t)-goal,-1.,0.)
    pos=quad_vec(lambda t: np.exp(-2*h*t)*P/EP(t), 0., te,epsabs=1e-13)[0]
    return te,pos,(P*np.exp(-h*te))/EP(te)
t0,x0,pe=exact_point(sky); aa=np.cross(sky,[1,0,0]); aa/=np.linalg.norm(aa); bb=np.cross(sky,aa)
for eps in [1e-4,1e-5]:
    cols=[np.exp(h*t0)*(exact_point(sky*np.cos(eps)+v*np.sin(eps))[1]-exact_point(sky*np.cos(eps)-v*np.sin(eps))[1])/(2*eps) for v in [aa,bb]]
    exact=np.sqrt(abs(pe@np.cross(*cols)))
    err=abs(float(out.angular_distance_mpc[0,0])/exact-1); print('off_axis',eps,exact,err,'event_error',abs(t0-out.emission_N[0,0])); assert err<3e-8
hflat=H(np.ones(3),np.zeros(3))
for zo in [1e-12,1e-15]:
    b=finite_redshift_beams(hflat,[sky],[zo],n_min=-.5,sky_frame='normal')
    print('near_vertex',zo, float(b.redshift[0,0]), float(b.angular_distance_mpc[0,0]),int(b.parity[0,0]))
class D:
    H0=70
    @staticmethod
    def distance_integral(z,order):return z
try: print('zero_sigma',cf.hermite_moments(D,np.array([.01]),np.zeros(1),32))
except ValueError as exc: print('zero_sigma',str(exc))
s=np.array([1.,2.,5.]); print('rank_scale', *[ga.supported_subspace(t*s,t*t*np.diag([1.,2.,0.]))['rank'] for t in [1.,1e-21]])
g=ga.joint_covariance
rng=np.random.default_rng(309); j=rng.normal(size=(3,5,4,2)); v=rng.normal(size=(5,5)); K=v@v.T; J=np.concatenate([a.transpose(1,0,2).reshape(4,10) for a in j],axis=0)
delta=np.max(abs(g(j,K)-J@np.kron(K,np.eye(2))@J.T)); print('joint_maxabs',delta); assert delta < 1e-12
