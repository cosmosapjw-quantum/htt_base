"""Projection calibration and declared-domain checks for the new oracle only."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
spec=importlib.util.spec_from_file_location('shear_oracle',Path(__file__).with_name('run.py'))
ray=importlib.util.module_from_spec(spec);spec.loader.exec_module(ray)

class ProjectionTests(unittest.TestCase):
 def test_nonzero_quadrupole_octupole_and_dipole(self):
  e,w=ray.sphere(12);Q=np.array([[.3,.1,.2],[.1,-.1,-.05],[.2,-.05,-.2]])
  v=np.array([.2,-.4,.7]);eye=np.eye(3)
  O=np.einsum('i,j,k->ijk',v,v,v)-(v@v)/5*(np.einsum('i,jk->ijk',v,eye)+np.einsum('j,ik->ijk',v,eye)+np.einsum('k,ij->ijk',v,eye))
  dip=np.array([.1,.2,-.3])
  f=6+e@dip+np.einsum('ni,ij,nj->n',e,Q,e)+np.einsum('ni,nj,nk,ijk->n',e,e,e,O)
  q,o,d=ray.coefficients(e,w,f)
  for actual,expected in [(q,Q),(o,O),(d,dip)]:np.testing.assert_allclose(actual,expected,atol=2e-12,rtol=0)
  reverse=ray.coefficients(-e,w,f)
  for actual,expected in zip(reverse,[Q,-O,-dip]):np.testing.assert_allclose(actual,expected,atol=2e-12,rtol=0)
 def test_full_sky_timelike_domain(self):
  e,_=ray.sphere(8);S=np.diag([1.,-1.,0.])
  for h in [0.,-0.1,1.,1.1]:
   with self.assertRaises(ValueError):ray.propagate(e,S,h,32)

if __name__=='__main__':unittest.main()
