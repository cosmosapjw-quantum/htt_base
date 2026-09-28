"""R3 low-speed FLRW depth kernels with explicit frame and expansion domain."""
from dataclasses import dataclass
import numpy as np
from scipy.integrate import quad
from common.r7_contracts import finite_array,content_id,NumericalUnresolved


@dataclass(frozen=True)
class ResponseBlock:
    matrix: np.ndarray
    parameter_labels: tuple[str,...]
    units: str
    observer_kernel: np.ndarray
    source_kernel: np.ndarray
    response_id: str
    domain: dict
    numerical_error: np.ndarray


def depth_response(z,directions,background,frame_policy) -> ResponseBlock:
    redshift=finite_array(z,ndim=1);n=finite_array(directions,shape=(len(redshift),3))
    if np.any(redshift<=0) or not np.allclose(np.linalg.norm(n,axis=1),1.,atol=1e-12,rtol=0): raise ValueError("positive redshift and unit sight lines required")
    if background.get("spatial_curvature")!=0: raise ValueError("T9 kernels require flat FLRW")
    if frame_policy.get("redshift")!="OBSERVED" or frame_policy.get("direction")!="OUTWARD" or frame_policy.get("velocity_units")!="v/c":
        raise ValueError("T9 observer/source frame convention is explicit")
    beta_bound=float(frame_policy["maximum_velocity_frame_shift"])
    if beta_bound<0 or np.any(beta_bound/redshift>frame_policy.get("maximum_shift_over_z",.01)):
        raise ValueError("small velocity/frame shifts compared with z required")
    h=background["H"];hz=np.array([h(float(v)) for v in redshift])
    if not np.all(np.isfinite(hz)) or np.any(hz<=0): raise ValueError("positive expansion history")
    def reciprocal(x):
        value=float(h(x))
        if not np.isfinite(value) or value<=0: raise ValueError("positive expansion along entire ray")
        return 1/value
    integrals=np.array([quad(reciprocal,0,float(v),epsabs=1e-13,epsrel=1e-11) for v in redshift])
    if np.any(integrals[:,0]<=integrals[:,1]): raise NumericalUnresolved("depth integral denominator unresolved")
    fo=(1+redshift)/(hz*integrals[:,0]);fg=(1+redshift)*(1-fo)
    matrix=(5/np.log(10))*np.column_stack((n*fo[:,None],n*fg[:,None]))
    return ResponseBlock(matrix,("beta_observer_x","beta_observer_y","beta_observer_z","K_source_x","K_source_y","K_source_z"),
        "mag per dimensionless velocity",fo,fg,content_id({"z":redshift,"directions":n,"background":background["source_id"],"frame":frame_policy}),
        {"model":"FLAT_FLRW_LOW_SPEED_R3","background_id":background["source_id"],"maximum_velocity_frame_shift":beta_bound,
         "approximation":"first order in velocity, fixed observed redshift"},integrals[:,1])
