import importlib.util
from pathlib import Path
import sys
import unittest
import numpy as np

SCRIPTS=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(SCRIPTS))
SPEC=importlib.util.spec_from_file_location("smica_reboot_pilot",SCRIPTS/"run_smica_reboot_pilot.py")
p=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class PilotProjectionTests(unittest.TestCase):
    def test_cache_identity_is_document_field_not_document_hash(self):
        gate={"cache_hash":"sha256:"+p.EXPECTED_CACHE_SHA256,"cache_reproducibility_green":True}
        p.validate_cache_gate(gate)
        with self.assertRaisesRegex(ValueError,"different cache"):
            p.validate_cache_gate(dict(gate,cache_hash="sha256:wrong"))
        with self.assertRaisesRegex(ValueError,"not green"):
            p.validate_cache_gate(dict(gate,cache_reproducibility_green=False))

    def test_positive_projection_injection(self):
        rng=np.random.default_rng(719)
        design=rng.normal(size=(80,7)); mask=np.ones(80); mask[:12]=0
        selected,operator,meta=p.build_ols_projector(design,mask)
        beta=rng.normal(size=(4,7))
        maps=beta @ design.T
        fitted=p.fit_map_block(maps,selected,operator,count=4,chunk=2)
        np.testing.assert_allclose(fitted,beta,atol=2e-14,rtol=2e-14)
        self.assertLess(meta["operator_design_max_identity_residual"],2e-14)
        reference=np.linalg.lstsq(design[selected],maps[:,selected].T,rcond=None)[0].T
        np.testing.assert_allclose(fitted,reference,atol=2e-14,rtol=2e-14)

    def test_signal_noise_pairing_preserves_linear_fit_and_power_cross_terms(self):
        rng=np.random.default_rng(9)
        design=rng.normal(size=(70,36))
        selected,operator,_=p.build_ols_projector(design,np.ones(70))
        signal=rng.normal(size=(4,70)); noise=rng.normal(size=(4,70))
        separate=p.fit_map_block(signal,selected,operator,4)+p.fit_map_block(noise,selected,operator,4)
        combined=p.fit_map_block(signal+noise,selected,operator,4)
        np.testing.assert_allclose(separate,combined,atol=1e-14,rtol=1e-13)
        ones=np.ones(32)
        np.testing.assert_array_equal(p.lowell_powers(ones),np.ones(4))
        np.testing.assert_array_equal(p.lowell_powers(ones+ones),4*np.ones(4))
        self.assertEqual(len(p.retained_labels()),32)

    def test_duplicate_and_insufficient_ids(self):
        with self.assertRaisesRegex(ValueError,"at least 300"):
            p.validate_realization_ids(np.arange(299),np.arange(300))
        with self.assertRaisesRegex(ValueError,"at least 300"):
            p.validate_realization_ids(np.arange(999),np.arange(299))
        noise=np.arange(300); noise[1]=noise[0]
        with self.assertRaisesRegex(ValueError,"no noise/signal recycling"):
            p.validate_realization_ids(np.arange(999),noise)
        signal=np.arange(999); signal[1]=signal[0]
        with self.assertRaisesRegex(ValueError,"duplicate"):
            p.validate_realization_ids(signal,np.arange(300))
        c,n=p.validate_realization_ids(np.arange(999),np.arange(300))
        self.assertEqual(len(c),300); self.assertEqual(len(n),300)

    def test_invalid_projection_and_maps(self):
        with self.assertRaises(ValueError):
            p.build_ols_projector(np.ones((10,3)),np.ones(10))
        with self.assertRaises(ValueError):
            p.build_ols_projector(np.eye(3),[1,.5,1])
        with self.assertRaises(ValueError):
            p.build_ols_projector(np.eye(3),[1,np.nan,1])
        with self.assertRaises(ValueError):
            p.build_ols_projector(np.eye(3),[1,2,1])
        selected,operator,_=p.build_ols_projector(np.eye(3),np.ones(3))
        with self.assertRaises(ValueError):
            p.fit_map_block(np.zeros((2,3)),selected,operator,3)
        with self.assertRaises(ValueError):
            p.fit_map_block(np.array([[0,np.nan,0]]),selected,operator,1)
        with self.assertRaises(ValueError):
            p.fit_map_block(np.zeros((1,3),complex),selected,operator,1)
        with self.assertRaises(ValueError):
            p.lowell_powers(np.ones(31))


if __name__=="__main__":
    unittest.main()
