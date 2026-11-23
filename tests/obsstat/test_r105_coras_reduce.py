"""Independent CORAS H02 projection, paired-seed comparison and input-integrity checks."""
from pathlib import Path
import tempfile
import unittest

import numpy as np
from numpy.testing import assert_allclose

from scripts.r105 import coras_reduce as core


class TestCorasReduction(unittest.TestCase):
    def test_projected_covariance_equals_dense_transform(self):
        rng=np.random.default_rng(173)
        raw=rng.normal(size=(8,5)); w=rng.normal(size=(36,5))
        mean=w@rng.normal(size=5); nn=rng.normal(size=36); obs=rng.normal(size=36)
        m=np.eye(36)*2.5
        out=core.summarized(mean,raw@w.T,nn,obs,m)
        c=w@np.cov(raw,rowvar=False,ddof=1)@w.T
        assert_allclose(out["sample_covariance_36x36"],c,atol=3e-14)
        assert_allclose(out["measurement_plus_sample_cov_quadratic_minus_coras"],
                        (obs-mean)@np.linalg.inv(m+c)@(obs-mean),rtol=3e-14)
        self.assertEqual(out["residual_sample_rank"],5)
        self.assertEqual(out["split_by_sorted_seed"]["half_counts"],[4,4])

    def test_seed_comparison_is_intersection_only(self):
        a=dict(mean=np.array([1.,2.]),draws={0:np.array([99,99]),1:np.array([1,2]),2:np.array([3,4])})
        b=dict(mean=np.array([3.,4.]),draws={1:np.array([1,2]),2:np.array([3,4]),3:np.array([111,23])})
        r=core.compare_mesh(a,b)
        self.assertEqual(r["common_seeds"],[1,2])
        self.assertEqual(r["paired_residual_rms_norm"],0.)

    def test_ids_exact_ints_and_order_finite(self):
        ids=np.array([9007199254740993,9007199254740992],dtype='<i8')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"residual_1.tsv"
            p.write_text("# id value\n9007199254740993 0.2\n9007199254740992 -1.1\n")
            assert_allclose(core.read_radial(p,ids),[.2,-1.1])
            for a in ("9007199254740992 0.2\n9007199254740993 -1.1\n",
                      "9007199254740993.0 0.2\n9007199254740992 -1.1\n",
                      "9007199254740993 nan\n9007199254740992 -1.1\n"):
                p.write_text(a)
                with self.assertRaises(ValueError):
                    core.read_radial(p,ids)

    def test_zero_variance_split_and_minimum_draw(self):
        z=np.zeros((5,4))
        self.assertIsNone(core.split_diagnostic(z)["symmetric_relative_frobenius"])
        self.assertEqual(core.split_diagnostic(z[:2])["status"],"need_at_least_four_draws")

    def test_manifest_and_output_binding_and_partial_draw_rejection(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            ids=np.array([21,31])
            rays=np.array([[1.,0.,0.],[0.,0.,1.]])
            geo=dict(ids=ids, ng=rays,radius=np.array([1.,2.]),weights=np.ones((36,2)),
                     nn=np.zeros(36),observed=np.ones(36),measurement_cov=np.eye(36))
            (p/"sites.tsv").write_text("21 1 1.5707963267948966 0\n31 2 0 0\n")
            (p/"mean.tsv").write_text("21 1\n31 0\n")
            (p/"residual_1.tsv").write_text("21 -1\n31 -2\n")
            (p/"residual_2.tsv").write_text("21 2\n31 3\n")
            cfg=dict(radial=24,ell=4,fft=16,smoothing_Mpch=15.,growth_fsigma8=.405,
                     external_bulk_galactic_kms=[95,-172,28])
            rec=dict(first=1,last=2,groups=2,config=cfg, donor_commit="45ab25635aa32869ce207511d556ea257ab8a591",
                     source_sha256="a"*64,binary_sha256="b"*64,sites_sha256=core._sha(p/"sites.tsv"),
                     input_sha256={k:"c"*64 for k in ("data/2MRS_group_member_catalog.dat","data/CosmicEmu_spectrum_Planck18.dat")},
                     output_sha256={f.name:core._sha(f) for f in p.glob("*.tsv") if f.name!="sites.tsv"})
            (p/"run.json").write_text(json.dumps(rec))
            out=core.run([p],geo)["configs"][0]
            self.assertEqual(out["n_draws"],2)
            self.assertEqual(out["covariance_rank"],1)
            assert_allclose(out["sample_covariance_36x36"],32.)
            with self.assertRaisesRegex(ValueError,"duplicate seed"):
                core.run([p,p],geo)
            (p/"residual_1.tsv").write_text("21 -10\n31 -2\n")
            with self.assertRaisesRegex(ValueError,"residual SHA"):
                core.run([p],geo)
            (p/"residual_2.tsv").unlink()
            with self.assertRaisesRegex(ValueError,"incomplete"):
                core.run([p],geo)
