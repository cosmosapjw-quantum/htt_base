import numpy as np
import pytest
from common.r7_contracts import ScopeKey
from htt.infer.r7_gaussian_law import JointObservationLaw
from htt.infer.r7_joint_experiment import (compose_joint_law,JointGaussianProvider,analyze_identifiable_combinations,compare_p0_p1)
from htt.infer.r7_depth_response import depth_response


def law(id,y,j,v,c):
    j=np.asarray(j,dtype=float);v=np.asarray(v,dtype=float)
    spec=dict(source_ids=[id],selection_law='fixed',covariance_source='known fixture',mean_definition='linear')
    return JointObservationLaw(ScopeKey(id,id,'COMMON_MODEL',(id,),method_config_id='fixed'),np.array(y),
        tuple(id+str(i) for i in range(len(y))),('theta',),('1',),lambda t,e:j@t+v@e,np.asarray(c,dtype=float),
        spec,'R',lambda t,e:True,jacobian_theta=lambda t,e:j,jacobian_eta=lambda t,e:v)


def test_duplicate_law_adds_no_measurements_and_unknown_cross_law_not_multiplied():
    x=law('x',[0.],[[1.]],[[1.]],[[1.]])
    duplicate=compose_joint_law([x,x],[],None)
    assert duplicate.admitted_laws==(x,) and duplicate.duplicate_measurements==('x0',)
    c=law('c',[0.],[[0.]],[[1.]],[[4.]])
    partition=compose_joint_law([x,c],[],None)
    assert len(partition.admitted_laws)==2 and len(partition.unresolved_cross_links)==1
    with pytest.raises(ValueError,match='evidence'):
        compose_joint_law([x,c],[dict(basis='POSITION_ONLY',evidence='nearby')],None)


def test_joint_calibration_information_one_fifth():
    x=law('x',[0.],[[1.]],[[1.]],[[1.]])
    c=law('c',[0.],[[0.]],[[1.]],[[4.]])
    provider=JointGaussianProvider(np.diag([1.,4.]),('x0','c0'),'independent known errors',('eta',),'FIXED_ETA')
    joint=compose_joint_law([x,c],[],provider).admitted_laws[0]
    old=analyze_identifiable_combinations(x,[0.],[0.],{})
    new=analyze_identifiable_combinations(joint,[0.],[0.],{})
    assert old.rank==0 and old.kernel.shape==(1,1)
    assert new.rank==1 and abs(new.efficient_information[0,0]-.2)<1e-14


def test_singular_exact_constraints_are_not_pseudoinverse_discarded():
    x=law('exact',[1.,0.],[[1.],[0.]],np.empty((2,0)),np.ones((2,2)))
    identification=analyze_identifiable_combinations(x,[1.],[],{})
    assert identification.exact_support_constraints.shape==(1,1)
    assert abs(identification.exact_support_constraints[0,0])>.5


def test_depth_constant_H_and_single_shell_degeneracy_and_domain():
    z=np.array([.1,.2,.3]);n=np.tile([1.,0.,0.],(3,1))
    bg=dict(source_id='constant-H fixture',spatial_curvature=0,H=lambda z:70.)
    frame=dict(redshift='OBSERVED',direction='OUTWARD',velocity_units='v/c',maximum_velocity_frame_shift=1e-5)
    result=depth_response(z,n,bg,frame)
    np.testing.assert_allclose(result.source_kernel,-result.observer_kernel,rtol=1e-14)
    assert np.linalg.matrix_rank(result.matrix)==1
    shell=depth_response(np.full(3,.2),np.eye(3),dict(bg,H=lambda z:70*np.sqrt(.3*(1+z)**3+.7)),frame)
    assert np.linalg.matrix_rank(shell.matrix)==3
    with pytest.raises(ValueError,match='compared'):
        depth_response(z,n,bg,dict(frame,maximum_velocity_frame_shift=.1))


def test_bound_P0_P1_comparison_requires_no_physical_provider():
    x=law('x',[4.],[[1.]],np.empty((1,0)),[[1.]])
    result=compare_p0_p1(x,[0.],[[1.]],'fixed-observation-column',('amplitude',))
    assert not result['p0'].accepted and result['p1'].accepted
    assert result['p1'].rank==1 and result['coefficients'][0]==4.
