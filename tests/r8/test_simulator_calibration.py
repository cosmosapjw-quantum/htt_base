import numpy as np
import pytest
from htt.infer.r8_simulator_calibration import ToyLocationLaw,AbsoluteResidual,candidate_rank

def test_same_procedure_inclusive_ties_domain_and_no_dropped_rows():
    law=ToyLocationLaw('student5',0.)
    result=candidate_rank(law,0.,199,81007,AbsoluteResidual())
    assert result.pvalue==1 and len(result.row_scores)==200
    assert candidate_rank(law,2.,199,81007,AbsoluteResidual()).status=='UNRESOLVED_DOMAIN'
    with pytest.raises(ValueError):candidate_rank(law,0.,0,1,AbsoluteResidual())
    with pytest.raises(ValueError):candidate_rank(law,0.,199,1,lambda rows,x:np.zeros(199))

def test_known_selected_sampler_never_retains_failed_proposals():
    law=ToyLocationLaw('selected_normal',0.)
    sample=law.sample(0.,20000,np.random.default_rng(123))
    assert sample.mean()>.4 and sample.shape==(20000,)
    # Selected |Z| is exactly half-normal by s(z)+s(-z)=1.
    assert np.mean(np.abs(sample))==pytest.approx(np.sqrt(2/np.pi),abs=.02)
    with pytest.raises(ValueError):ToyLocationLaw('fitted_unknown',0.)
