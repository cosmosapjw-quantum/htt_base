import pytest,numpy as np
from pathlib import Path
import s02_partial_cf4 as s
ROOT=Path(__file__).resolve().parent.parent/'source'
# Direct archive is pinned to the pre-existing verified local backup path.
A=ROOT/'h03_archive.zip'
S=ROOT/'h03/htt_six_paper_h03/inputs/selected_source_observables.npz'

def test_source_digest():
 theta,cov=s.read_h03(A,S);assert theta.shape==(4,9) and cov.shape==(36,36)
 with pytest.raises(ValueError,match='digest'):s.read_h03(S,A)

def test_one_joint_draw_36d():
 th,cov=s.read_h03(A,S);x=s.joint_draw(th,cov);assert x.shape==(2048,4,9)
 assert np.allclose(x.mean(axis=0),th,rtol=0,atol=2e-13)

def test_physical_missing_preserved():
 th,c=s.read_h03(A,S);x=s.joint_draw(th,c);p=s.paired_partial_measure(x)
 for src in ('Q','F','G_F'):
  q=p.exceedance(src,(0.,.25,.5,1.));assert q['unknown_mass']==pytest.approx(1)
  assert all(v==pytest.approx(0) for v in q['lower']) and all(v==pytest.approx(1) for v in q['upper'])

def test_strict_tie_and_weight():
 from publication_functionals import PartialMeasure,PartialDraw
 H='c'*64
 p=PartialMeasure((PartialDraw('a',.2,'c',H,q=.5,missing_reasons={'F':'domain_uncertified','G_F':'domain_uncertified'}),
 PartialDraw('b',.8,'c',H,missing_reasons={'Q':'unmeasured_defined','F':'domain_uncertified','G_F':'domain_uncertified'})))
 v=p.exceedance('Q',(.49,.5,.51));assert v['lower']==pytest.approx((.2,0,0));assert v['upper']==pytest.approx((1,.8,.8))

def test_same_source_working_correlation():
 th,cov=s.read_h03(A,S);q=s.working_functional(s.joint_draw(th,cov));assert q.shape==(2048,4)
 assert not np.allclose(np.corrcoef(q,rowvar=False),np.eye(4),atol=.01)
