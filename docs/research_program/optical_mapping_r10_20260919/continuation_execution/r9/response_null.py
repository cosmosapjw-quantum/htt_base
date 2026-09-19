#!/usr/bin/env python3
"""Use immutable saved survey response, without new mocks or a noise law."""
from pathlib import Path
import argparse,hashlib,io,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
DONOR='870bd67af159993ccde4ede9923424a475c01375'
PREFIX='docs/research_program/tensor_joint_r9/revision2/'

def main(output):
 paths=[PREFIX+'multidepth/observed_initial/observed.json',PREFIX+'selected_law/final/rows_and_coefficients.npz',PREFIX+'selected_law/final/result.json','htt/obsstat/sdss_pv_depth.py']
 # The first three are the consumed saved numerical inputs. The extractor is
 # source context; no raw-catalogue or mock rerun is performed here.
 blobs={p:subprocess.check_output(['git','show',f'{DONOR}:{p}'],cwd=ROOT) for p in paths}
 observed=json.loads(blobs[paths[0]]);z=np.load(io.BytesIO(blobs[paths[1]]),allow_pickle=False);cal=json.loads(blobs[paths[2]])
 R=np.array(observed['response']);H=np.array(observed['H']);T=np.array(observed['T']);Y=np.array(observed['Y'])
 assert R.shape==(36,36) and H.shape==(27,36) and T.shape==(36,36)
 c=np.tile(np.r_[1.,np.zeros(8)],4);b=R@c;A=np.column_stack((R,b));v=np.r_[-c,1.]
 # Parameter theta comprises additive eta angular coefficients per shell,
 # followed by a free common zero point. Units are dex throughout.
 theta0=np.r_[np.linalg.solve(R,Y),0.];shift=cal['descriptive_offset_dex'];theta1=theta0+shift*v
 errors={'response_null':float(np.max(abs(A@v))),'same_observation':float(np.max(abs(A@theta1-A@theta0))),'baseline_fits_saved_Y':float(np.max(abs(A@theta0-Y))),'common_monopole_response':float(np.max(abs(b-c))),'contrast_removes_offset':float(np.max(abs(H@b))),'saved_offset_transport':float(np.max(abs(z['y_after']-z['y_before']-shift*b))),'saved_contrast_transport':float(np.max(abs(z['r_after']-z['r_before']-shift*(H@b)))),'saved_anchored_transport':float(np.max(abs(z['anchored_after']-z['anchored_before']-shift*(T@b))))}
 assert max(errors.values())<1e-11
 ranks={name:int(np.linalg.matrix_rank(x,tol=1e-10)) for name,x in [('R',R),('A',A),('H_R',H@R),('T_R',T@R)]}
 assert ranks=={'R':36,'A':36,'H_R':27,'T_R':36}
 # Anchor keeps sensitivity to a pure zero-point change; it cannot separate
 # that change from an opposite shift in all four unconstrained monopoles.
 assert abs((T@b)[0]-1)<1e-11 and np.max(abs((T@b)[1:]))<1e-11
 target=np.r_[np.tile(np.r_[.25,np.zeros(8)],4),0.]
 assert abs(target@v+1)<1e-14
 singular=np.linalg.svd(A,compute_uv=False)
 result={'status':'ACTUAL_SAVED_RESPONSE_NULL_DIRECTION','owner':'HTT nuisance identifiability / obsstat saved response','claim_tier':'DIAGNOSTIC_ONLY','donor':DONOR,'source_hashes':{p:hashlib.sha256(data).hexdigest() for p,data in blobs.items()},'method':'finite matrix nullspace on saved SDSS in_mask cumulative-depth response, unit-weight SVD additive logdistance angular fields','ranks':ranks,'singular_values_A_36_nonzero':singular.tolist(),'nullity_A':1,'null_vector_37':v.tolist(),'offset_column':b.tolist(),'theta0':theta0.tolist(),'theta1':theta1.tolist(),'step_dex':shift,'unsupported_target':'mean of four free shell monopoles with unknown common additive zero point','target_on_null':float(target@v),'anchor_offset_response':(T@b).tolist(),'residuals':errors,'counts':observed['counts'],'selected_observation_law':'UNAVAILABLE','physical_boost_tilt_response':'UNAVAILABLE','CF4_selected_law':'UNAVAILABLE_NOT_SUBSTITUTED_BY_CF3_SDSS','joint_noise_law':'UNAVAILABLE','confidence_or_rejection':'NOT_COMPUTED','alpha_spent':0,'new_mock_calls':0,'scope':'Conditional additive eta mean-response identifiability only. A changed nuisance/physical model requires its own bound response. This does not prove full observation-law equivalence.'}
 output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'status':result['status'],'ranks':ranks,'max_residual':max(errors.values()),'alpha_spent':0}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
