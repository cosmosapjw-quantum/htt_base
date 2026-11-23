"""Execute finite moving-projection identities and numerical convergence."""
from __future__ import annotations
import json
import numpy as np
from scipy.linalg import expm
from bass.kinetic.moving_projection import projection_blocks, integrate_split, memory_kernel, initial_hidden_force


def run():
    def rotating(s):
        v=np.array([[np.cos(s)],[np.sin(s)]]);dv=np.array([[-np.sin(s)],[np.cos(s)]])
        return projection_blocks(np.zeros((2,2)),v,dv)
    grid=np.linspace(0,2.1,51)
    errors=[]
    for tolerance in [1e-6,1e-9,1e-12]:
        aa,qq,xx=integrate_split(grid,[1.,0.],rotating,rtol=tolerance,atol=tolerance/100)
        errors.append({'rtol':tolerance,'resolved_error':float(np.max(abs(aa[0]-np.cos(grid)))),
                       'reconstruction_error':float(np.max(abs(xx-np.array([[1.],[0.]]))))})
    kernel=memory_kernel(1.7,.2,rotating)
    force=initial_hidden_force(1.7,0.,[0.,1.],rotating)
    a=np.array([[0,1j],[1j,1j]])
    def phase(s):return projection_blocks(a,np.array([[1.],[0.]]),np.zeros((2,1)))
    _,_,x=integrate_split([0.,1.],[1.,0.],phase,rtol=1e-12,atol=1e-14)
    return {'scope':'finite declared linear evolution; moving basis/weight; no fitted-family dynamics assumed',
            'rotating_kernel_error':float(abs(kernel.item()+1)),
            'initial_hidden_force_error':float(abs(force.item()-1)),
            'complex_phase_error':float(np.max(abs(x[:,-1]-expm(a)@np.array([1.,0.])))),
            'tolerance_convergence':errors,'physical_Pi':None,'physical_GF':None}


if __name__=='__main__':print(json.dumps(run(),indent=2,allow_nan=False))
