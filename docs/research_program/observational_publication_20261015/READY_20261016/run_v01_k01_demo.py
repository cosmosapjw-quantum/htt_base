"""Deterministic manufacturing to check V01/K01 invariants, not observations."""
import json
import numpy as np
from publication_frame_kinematics import C_SI, source_frame_packet, radial_operator,STF,antisymmetric_from_pseudovector
from build_ready_ledgers import canonical
from pathlib import Path

def run():
  b_o=[369.82e3/C_SI,0,0];b_m=[0,200e3/C_SI,0]
  p=source_frame_packet(b_o,b_m,[150,20,-80]);p['input_kind']='MANUFACTURED_FRAME_VELOCITIES_NOT_MEASURED_GLOBAL_TILT'
  theta=np.linspace(0,1,160);phi=2*np.pi*((np.arange(160)*0.61803398875)%1);n=np.stack([np.sqrt(1-(2*theta-1)**2)*np.cos(phi),np.sqrt(1-(2*theta-1)**2)*np.sin(phi),2*theta-1],axis=-1)
  ns=n/np.linalg.norm(n,axis=1,keepdims=True)
  A=radial_operator(ns);S=STF([[1.,.2,.4],[.2,-.3,-.1],[.4,-.1,.6]])
  null=np.stack([A@antisymmetric_from_pseudovector(e).reshape(9) for e in np.eye(3)],axis=1)
  sig=np.linalg.svd(A,compute_uv=False)
  return {'schema':'htt.sixpaper.V01_K01_manufactured/1','V01':p,'K01':{'source_unit':'s^-1 spatial gradient, dimensionless sky direction','radial_design_shape':list(A.shape),'generic_rank':int(np.sum(sig>1e-10)),'three_vorticity_column_null_max':float(np.max(abs(null))),'independent_omega_a_information_from_radial_gradient':'NONE','finite_actual_optical_transfer':'NOT_CALCULATED'},'classification':'MATHEMATICAL_DERIVATION_NUMERIC_SANITY'}

if __name__=='__main__':
 d=run();Path(__file__).with_name('V01_K01_MANUFACTURED_RESULT.json').write_text(canonical(d));print(json.dumps({'rapidity_MO':d['V01']['rapidity_MO_invariant'],'radial_rank':d['K01']['generic_rank'],'antisymmetric_null':d['K01']['three_vorticity_column_null_max']},indent=2))
