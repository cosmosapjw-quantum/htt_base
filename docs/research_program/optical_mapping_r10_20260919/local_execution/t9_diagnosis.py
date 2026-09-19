#!/usr/bin/env python3
"""Current-consumer comparison against independent kinetic energy integral.
No production mutation. Exit 1 deliberately preserves confirmed mismatch.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,itertools
import numpy as np
from scipy.integrate import quad
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'htt'))
sys.path.insert(0,str(ROOT/'htt/src'))
from bass.hierarchy.terms import T9_shear_down
from bass.hierarchy.packed_operators import apply_T9_shear_down_packed
from bass.hierarchy.pstf_tensor import zero_hierarchy, pstf_from_tensor, unpack_hierarchy, PSTFTensor
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_photon,proper_shear_at_eta
from bass.hierarchy.closure_interface import HardCutClosure
from bass.hierarchy.collision_interface import ZeroCollisionOperator
from bass.hierarchy.mode_mixing_blocks import assemble_A_mix_block

OUT=Path(__file__).resolve().parent

def physics_ratio(estar):
    # d_s F = epsilon (sigma:ee) F', integration needs no T9 coefficient.
    pi0=quad(lambda energy:energy**3*np.exp(-energy/estar),0,np.inf,epsabs=1e-11,epsrel=1e-12)[0]
    derivative=quad(lambda energy:-energy**4/estar*np.exp(-energy/estar),0,np.inf,epsabs=1e-11,epsrel=1e-12)[0]
    return derivative/pi0

def main():
    ratios=[physics_ratio(e) for e in (.5,1.,2.)];assert np.max(np.abs(np.array(ratios)+4))<1e-10
    basis=[np.diag([1.,-1.,0.])/np.sqrt(2),np.diag([1.,1.,-2.])/np.sqrt(6)]
    for i,j in [(0,1),(0,2),(1,2)]:
        a=np.zeros((3,3));a[i,j]=a[j,i]=1/np.sqrt(2);basis.append(a)
    rows=[]
    for a,sigma in itertools.product((1.,2.),basis):
        bg=SimpleNamespace(interp_a=lambda eta:a,interp_Theta=lambda eta:0.)
        tetrad=SimpleNamespace(eta=np.array([0.,1.]),sigma_tensor=np.stack([a*sigma,a*sigma]))
        actual_sigma=proper_shear_at_eta(.5,tetrad,a)
        assert np.max(np.abs(actual_sigma-sigma))<1e-13
        state=zero_hierarchy(2);state.tensors[0]=pstf_from_tensor(np.array(1.))
        # round trip removes any hidden packed monopole normalization.
        assert abs(float(state.tensors[0].to_full_tensor())-1)<1e-14
        rhs=hierarchy_rhs_photon(.5,state.as_flat(),L_max=2,bg_table=bg,tetrad_state=tetrad,closure=HardCutClosure(),collision=ZeroCollisionOperator())
        tensor=unpack_hierarchy(rhs,2).tensors[2].to_full_tensor()
        term=-a*T9_shear_down(2,np.array(1.),sigma)
        packed=-a*PSTFTensor(2,apply_T9_shear_down_packed(2,state.tensors[0].components,sigma)).to_full_tensor()
        expected=a*ratios[1]*sigma
        scale=np.linalg.norm(expected)
        residuals={k:float(np.linalg.norm(v-expected)/scale) for k,v in {'full_term':term,'packed':packed,'public_rhs':tensor}.items()}
        assert max(np.linalg.norm(tensor-term),np.linalg.norm(packed-term))<1e-12
        # Counterfactual output-sign reversal is a diagnostic discriminator only,
        # not an installed candidate repair or proof for the full hierarchy.
        opposite=float(np.linalg.norm(-tensor-expected)/scale)
        assert opposite<1e-10 and residuals['public_rhs']>1
        rows.append({'a':a,'sigma':sigma.tolist(),'reference':expected.tolist(),'public_rhs':tensor.tolist(),'relative_residuals':residuals,'counterfactual_output_sign_residual':opposite,'wrong_sign_rejected':True})
    # Test exactly exposed mixed-mode matrix on isotropic m=0 input. Its CG and
    # 5m storage are not the Cartesian PSTF normalization; do not equate them.
    mix=[]
    y=np.zeros(15);y[2]=1
    for i in range(5):
        m=assemble_A_mix_block(sigma_2M=np.eye(5)[i],L_max=2,ell_min=0)
        mix.append((m@y)[10:15].tolist())
    sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['htt/bass/hierarchy/terms.py','htt/bass/hierarchy/packed_operators.py','htt/bass/hierarchy/hierarchy_rhs.py','htt/bass/hierarchy/mode_mixing_blocks.py','docs/lowell_bianchi/02_multipole_hierarchy_spec.md']}
    result={'diagnosis':'CONFIRMED_MISMATCH_CARTESIAN_PACKED_PUBLIC_RHS','scope':'ell=2 initially isotropic collisionless brightness; five STF basis shears and a=1,2','kinetic_ratios':ratios,'intensity_LHS_coefficient':8/15,'Delta2_over_Delta0':2/15,'rows':rows,'mixed_LHS_outputs':mix,'mixed_physics_normalization':'UNRESOLVED; exposed CG 5m map not identified with direct Cartesian expansion','sources':sources,'FORMAL_T9':'NOT_ADMITTED','production_patch':'NOT_PERFORMED','OP07':'BLOCKED_PENDING_SCOPED_FOUR_AXIS_ADMISSION','source_book_equations':'Unnamed attachment source not sealed; independent kinetic derivation used','affected_consumers':['T9_shear_down','packed T9 generated cache','hierarchy_rhs_photon and shared neutrino path','mode_mixing_blocks pre9 requires separate normalization resolution'],'historical_results':'NOT_REWRITTEN; no blanket retroactive invalidation'}
    (OUT/'t9_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'diagnosis':result['diagnosis'],'cases':len(rows),'actual_over_expected':-1,'normalized_residual':rows[0]['relative_residuals']['public_rhs'],'production_patch':False}))
    return 1
if __name__=='__main__':sys.exit(main())
