import importlib.util
from pathlib import Path
import unittest
import numpy as np

spec=importlib.util.spec_from_file_location('depth_compute',Path(__file__).with_name('compute.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class DepthMomentFixture(unittest.TestCase):
    def test_sources_and_direct_whitened_regression(self):
        inp=c.load_contract()
        model=c.model_module()
        import json
        receipt=json.loads(Path(inp['sources'][2]['path']).read_text())
        rng=np.random.default_rng(31);n=120
        z=np.tile([.3,1.3,2.8],n//3)+rng.uniform(-.1,.1,n)
        a={'source_id':np.arange(n),'ra':rng.uniform(1,359,n),'dec':rng.uniform(-75,75,n),
           'redshift_quaia':z,'pmra_uasyr':rng.normal(0,5,n),'pmdec_uasyr':rng.normal(0,5,n),
           'pmra_error_uasyr':rng.uniform(1,4,n),'pmdec_error_uasyr':rng.uniform(1,4,n),
           'gaia_pmra_pmdec_corr':rng.uniform(-.5,.5,n)}
        for name in c.TEMPLATE_NAMES:a['template_'+name]=rng.normal(size=n)
        A,K,q,counts,peak=c.new_moments(a,receipt,model,chunk=29)
        ref=tuple(np.asarray(receipt[k]) for k in ('reference_center','reference_scale','vector_column_RMS'))
        temp=np.column_stack([a['template_'+name] for name in c.TEMPLATE_NAMES])
        X,bins=model.design(a['ra'],a['dec'],z,temp,ref)
        H=model.dipole(a['ra'],a['dec'])*(z/(1+z))[:,None,None]
        Y=np.column_stack([a['pmra_uasyr'],a['pmdec_uasyr']])
        WX,WY=model.whiten(X,Y,a['pmra_error_uasyr'],a['pmdec_error_uasyr'],a['gaia_pmra_pmdec_corr'])
        WH,_=model.whiten(H,Y,a['pmra_error_uasyr'],a['pmdec_error_uasyr'],a['gaia_pmra_pmdec_corr'])
        np.testing.assert_allclose(A,WH.T@WH,rtol=1e-12,atol=1e-10)
        np.testing.assert_allclose(K,WH.T@WX,rtol=1e-12,atol=1e-10)
        np.testing.assert_allclose(q,WH.T@WY,rtol=1e-12,atol=1e-10)
        np.testing.assert_array_equal(counts,np.bincount(bins,minlength=3))
        # A constant-g six-vector is exactly spanned by old 18 per-bin columns.
        constant=model.dipole(a['ra'],a['dec'])
        summed=sum(X[:,:,6*j:6*j+6] for j in range(3))
        np.testing.assert_allclose(constant,summed,rtol=0,atol=1e-14)

    def test_schur_against_direct_small_regression(self):
        rng=np.random.default_rng(32);m=180
        X=rng.normal(size=(m,102));H=rng.normal(size=(m,6));y=rng.normal(size=m)
        G=X.T@X;b=X.T@y;A=H.T@H;K=H.T@X;q=H.T@y
        out=c.fit(G,b,A,K,q)
        direct=np.linalg.lstsq(np.column_stack([X,H]),y,rcond=None)[0]
        np.testing.assert_allclose(out['theta_uasyr'],direct[-6:],rtol=1e-10,atol=1e-10)
        np.testing.assert_allclose(out['full24_state_uasyr'][:18],direct[:18],rtol=1e-10,atol=1e-10)
        cov=np.linalg.inv(np.column_stack([X,H]).T@np.column_stack([X,H]))
        ix=list(range(18))+list(range(102,108))
        np.testing.assert_allclose(out['full24_cov_uasyr2'],cov[np.ix_(ix,ix)],rtol=1e-10,atol=1e-10)


if __name__=='__main__':unittest.main()
