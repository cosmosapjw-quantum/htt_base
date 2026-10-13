"""Small independent algebra and HDF5 ordering falsifiers for OBS-05."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np

SCRIPT = Path(__file__).resolve().parents[2]/'scripts/obs05_desi_bgs_summary.py'
spec = importlib.util.spec_from_file_location('obs05', SCRIPT)
obs05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obs05)


class SummaryTests(unittest.TestCase):
    def test_placeholder_rejected(self):
        with self.assertRaisesRegex(ValueError, 'physical baseline missing'):
            obs05.validate_physical_baseline(np.zeros(6))

    @unittest.skipUnless(
        importlib.util.find_spec('h5py') is not None,
        'requires optional h5py fixture support',
    )
    def test_edges_not_centroids_and_matrix_permutation(self):
        import h5py
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.h5'
            with h5py.File(path,'w') as f:
                def put(name, labels, entries):
                    g=f.create_group(name)
                    g['labels_values']=np.asarray(labels,dtype='S')
                    for label,ell,edges,s,values in entries:
                        b=g.create_group(label);b['meta/ell']=ell
                        b['s_edges']=edges;b['s']=s;b['value']=values
                # Deliberately different row orders, centroids and theory labels.
                put('observable',['0'],[('0',0,[[2,3],[1,2]],[2.7,1.7],[20,10])])
                put('covariance/observable',['0'],[('0',0,[[1,2],[2,3]],[1.4,2.4],[0,0])])
                put('window/observable',['0'],[('0',0,[[2,3],[1,2]],[2.2,1.2],[0,0])])
                put('window/theory',['2','0'],[('2',2,[[0,1]],[.8],[0]),('0',0,[[0,1]],[.7],[0])])
                f['covariance/value']=[[2,.5],[.5,3]]
                f['window/value']=[[5,6],[7,8]]
            d=obs05.read_summary(path)
            np.testing.assert_equal(d['data'],[10,20])
            np.testing.assert_equal(d['window'],[[8,7],[6,5]])
            np.testing.assert_equal(d['covariance'],[[2,.5],[.5,3]])
            self.assertEqual(d['theory_keys'],[(0,0.,1.),(2,0.,1.)])

    def test_matching_fails_for_wrong_edges(self):
        with self.assertRaises(ValueError):obs05.permutation([(0,0.,1.)],[(0,0.,2.)])

    def test_projection_and_sampling_covariance(self):
        s=np.arange(1,5,dtype=float)*40
        w=np.array([[1,.2,0,0],[0,1,.1,0],[0,0,1,.3],[.1,0,0,1.]])
        c=np.array([[2,.3,0,0],[.3,3,.2,0],[0,.2,4,.1],[0,0,.1,5.]])
        j=np.column_stack([np.ones(4),s/100,(s/100)**2])
        x=w@j; beta=np.array([.2,-.5,.7]); y=x@beta
        result=obs05.diagnostic(dict(data=y,covariance=c,window=w,theory_s=s,
            data_s=s,theory_keys=[(0,float(t),float(t+1)) for t in s]))
        expected=np.linalg.inv(x.T@np.linalg.solve(c,x))
        np.testing.assert_allclose(result['coefficient_estimate'],beta,atol=1e-13)
        np.testing.assert_allclose(result['coefficient_covariance'],expected,rtol=1e-12)
        np.testing.assert_allclose(result['X'],x)
        self.assertEqual(result['rank'],3)
        self.assertLess(result['residual_quadratic_norm'],1e-25)
        template=np.exp(-.5*((s-100)/15)**2)
        np.testing.assert_allclose(result['window_response'][:,0],w@template)
        np.testing.assert_equal(result['window_response'][:,1:],0)

if __name__=='__main__': unittest.main()
