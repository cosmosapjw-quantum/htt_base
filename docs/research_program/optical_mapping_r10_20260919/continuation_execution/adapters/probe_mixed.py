#!/usr/bin/env python3
"""Source-bound finite rank obstruction; does not grant formal eligibility."""
from pathlib import Path
import argparse,json,hashlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(ROOT/'htt'),str(ROOT/'htt/src')]
from bass.hierarchy.mode_mixing_blocks import assemble_A_mix_block,shear_5vec_to_quadrupole_components

def main(output):
 y=np.zeros(15);y[2]=1 # sole physical ell=0 state; padded m != 0 slots zero
 cols=[]
 for v in np.eye(5):
  matrix=assemble_A_mix_block(sigma_2M=shear_5vec_to_quadrupole_components(v),L_max=2,ell_min=0)
  cols.append((matrix@y)[10:15])
 R=np.array(cols).T
 singular=np.linalg.svd(R,compute_uv=False);rank=int(np.linalg.matrix_rank(R,tol=1e-12))
 assert rank==1
 # Physical ell=2 output spans every STF shear direction. Reconstruct from
 # the module's documented sigma+, sigma-, xy, xz, yz coordinates.
 tensors=[]
 for a,b,c,d,e in np.eye(5):
  tensors.append(np.array([[a+b/np.sqrt(3),c,d],[c,-a+b/np.sqrt(3),e],[d,e,-2*b/np.sqrt(3)]]))
 physical=np.array([-4*S.reshape(-1) for S in tensors]).T
 assert np.linalg.matrix_rank(physical,tol=1e-12)==5
 assert np.max(abs(np.array([np.sum(s*t) for s in tensors for t in tensors]).reshape(5,5)-2*np.eye(5)))<1e-12
 files=['htt/bass/hierarchy/mode_mixing_blocks.py','htt/bass/hierarchy/ver2_native_integrator.py','htt/bass/hierarchy/ver3_layout_protocol.py','htt/bass/los/family_backend_protocol.py']
 r={'status':'NUMERICAL_RANK_OBSTRUCTION','input_order':['sigma+','sigma-','xy','xz','yz'],'output_order':[-2,-1,0,1,2],'source_matrix':R.tolist(),'singular_values':singular.tolist(),'rank':rank,'direct_physical_rank':5,'source_pi0':1,'source_valid_slots':['ell=0,m=0'],'left_or_right_sign_changes_rank':False,'conclusion':'No invertible input/output convention adapter can turn this isotropic-input map into the full physical STF shear map. Formal proof and repair remain unexecuted.','actual_caller':'No tracked production caller of this standalone builder found; runtime ops.A_mix is supplied by ver3_layout_protocol.assemble_mixing_block, a distinct builder.','scope':'this exposed module at pinned bytes, ell_min=0 L_max=2 only','formal_eligible':False,'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
 print(json.dumps({'status':r['status'],'rank':rank,'physical_rank':5}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
