import importlib.util
from pathlib import Path
from fractions import Fraction
import numpy as np
import pytest

s=importlib.util.spec_from_file_location('cohort',Path(__file__).with_name('cohort.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def test_marked_law_keeps_missing_and_nondetection():
    n=np.array([[116,269],[21,1],[26,3],[191,1]])
    p=n/n.sum()
    assert np.isfinite(m.marked_loglik(n,p))
    assert m.marked_loglik(n,np.ones((4,2))/8)<m.marked_loglik(n,p)
    with pytest.raises(ValueError):m.marked_loglik(n,p*2)


def test_selection_denominator_exact():
    parent=[Fraction(1,4),Fraction(3,4)];selection=[Fraction(4,5),Fraction(1,5)]
    a=sum(p*s for p,s in zip(parent,selection))
    assert a==Fraction(7,20)
    assert [p*s/a for p,s in zip(parent,selection)]==[Fraction(4,7),Fraction(3,7)]


def test_strict_decimal_completion_and_unknown_mass():
    x=np.array([3300,3400,3500])
    assert m.completion(x,5,34,0)==dict(k=1,lower=.2,upper=.6)
    assert m.completion(x,5,34,'-0.01')['k']==2
    assert m.completion(x,5,34,'1')['k']==0
    with pytest.raises(ValueError):m.cents('0.001')


def test_gaussian_cut_normalizer_and_failures():
    assert abs(m.two_cut_normalizer([0,0],np.eye(2),[0,0])-.25)<1e-10
    assert abs(m.two_cut_normalizer([0,0],np.eye(2),[-np.inf,-np.inf])-1)<1e-10
    assert abs(m.two_cut_normalizer([0,0],np.eye(2),[-np.inf,0])-.5)<1e-10
    with pytest.raises(np.linalg.LinAlgError):m.two_cut_normalizer([0,0],[[1,2],[2,1]],[0,0])
    with pytest.raises(ArithmeticError):m.two_cut_normalizer([0,0],np.eye(2),[100,100])


def test_tiny_tail_accuracy_permutation_and_correlated_identity():
    from scipy.stats import norm
    for cuts in ([10,-30],[10,-10],[-30,10]):
        actual=m.two_cut_normalizer([0,0],np.eye(2),cuts)
        assert abs(actual/(norm.sf(cuts[0])*norm.sf(cuts[1]))-1)<1e-12
    for rho in (-.9,-.3,.3,.9):
        cov=np.array([[1,rho],[rho,1]])
        value=m.two_cut_normalizer([0,0],cov,[0,0])
        assert abs(value-(.25+np.arcsin(rho)/(2*np.pi)))<1e-11
        x=m.two_cut_normalizer([0,0],cov,[5,-4])
        y=m.two_cut_normalizer([0,0],cov,[-4,5])
        assert abs(x/y-1)<1e-8
