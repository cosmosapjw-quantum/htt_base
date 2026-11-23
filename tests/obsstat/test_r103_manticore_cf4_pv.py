"""Analytic grid projection, catalogue-selection, and bounded transfer fixtures."""
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import tempfile
import json
from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

import numpy as np
from numpy.testing import assert_allclose

from scripts.r103 import manticore_cf4_pv as pv


def grid(n):
    xyz = np.indices((n,)*3, dtype=float)
    density = 1.+xyz[0]**2 + 2*xyz[2]
    velocity = [2+xyz[0]-3*xyz[2], -5+xyz[0]+2*xyz[1], 13-3*xyz[1]+5*xyz[2]]
    return {"density":density, **{f"p{i}":v*density for i,v in enumerate(velocity)}}


class TestField(unittest.TestCase):
    def test_axis_interpolation_density_and_observer(self):
        n = np.array([[1.,0.,0.], [0.,-1.,0.], [0.,0.,1.], [1/np.sqrt(2),1/np.sqrt(2),0.], [1.,0.,0.]])
        r = np.array([1.4,1.7,1.2,.91,0.])
        for offset in (0.,-.5):
            stencil = pv.mesh_stencil(n,r,mesh_size=8,box_mpc=8.,offset=offset)
            xyz = 4+offset + r[:,None]*n
            x,y,z = xyz.T
            vel = np.stack((2+x-3*z,-5+x+2*y,13-3*y+5*z),axis=1)
            for relative in (True, False):
                measured = pv.project_field(grid(8),n,stencil,mesh_size=8,observer_relative=relative)
                expected = vel-vel[-1] if relative else vel
                assert_allclose(measured,(expected*n).sum(1),atol=2.e-14)

    def test_boundary_and_inactive_vertices(self):
        n = np.array([[1.,0.,0.]])
        f = grid(8)
        f["density"][5,4,4]=0.
        st = pv.mesh_stencil(n,[0],8,8.)
        self.assertTrue(np.isfinite(pv.project_field(f,n,st,8)).all())
        with self.assertRaisesRegex(ValueError,"undefined"):
            pv.project_field(f,n,pv.mesh_stencil(n,[.1],8,8.),8)
        with self.assertRaisesRegex(ValueError,"out-of-mesh"):
            pv.mesh_stencil(n,[3.1],8,8.)

    def test_fetch_bounds_before_transfer_and_reject_truncation(self):
        class S3:
            count=0
            def head_object(self, **kwargs):
                return {"ContentLength":32,"ETag":'"opaque"'}
            def get_object(self, **kwargs):
                self.count += 1
                assert kwargs['IfMatch'] == '"opaque"'
                return {"Body":BytesIO(b"short"),**self.head_object()}
        conn = S3()
        obj = SimpleNamespace(s3=conn,bucket_name="manticore-local")
        with tempfile.TemporaryDirectory() as t, patch.object(pv,"field_catalog",return_value={0:(obj,"a")}):
            with self.assertRaisesRegex(ValueError,"allowance"):
                pv.fetch_fields(Path(t),[0],31)
            self.assertEqual(conn.count,0)
            with self.assertRaisesRegex(ValueError,"length"):
                pv.fetch_fields(Path(t),[0],32)
            self.assertEqual(list(Path(t).iterdir()),[])

    def test_endpoint_top_vertex(self):
        n = np.array([[1.,0.,0.]])
        f = grid(8)
        result = pv.project_field(f,n,pv.mesh_stencil(n,[3],8,8.),8)
        assert_allclose(result,[2+7-3*4])

    def test_real_hdf5_compressed_covariance_and_draw_identity(self):
        import h5py
        n = np.eye(3)
        weight = np.array([[1.,2.,3.],[2.,0.,-3.]])
        fixture = (np.array([1,2,3]), n, np.array([10.,20.,30.]), weight)
        with tempfile.TemporaryDirectory() as t, patch.object(pv,'geometry',return_value=fixture):
            root = Path(t)
            paths = []
            for idx, sign in enumerate([1,-1]):
                fpath = root/f"manticore_local_{idx:03d}.h5"
                paths.append(str(fpath))
                with h5py.File(fpath, "w") as f:
                    for name, v in zip(("density","p0","p1","p2"),(2.,2.*sign,4.*sign,6.*sign)):
                        f.create_dataset(name, shape=(256,)*3, dtype='f4', fillvalue=v)
                receipt = dict(schema="htt.manticore_local.source/1",index=idx,bucket="manticore-local",
                               key=f"R1024/mcmc_{idx}/velocity_fields/N256/field.h5",etag='"fixture"',
                               bytes=fpath.stat().st_size,sha256=pv.digest(fpath))
                fpath.with_suffix(".source.json").write_text(pv.canonical(receipt)+"\n")
            out = root/"rr.npz"
            pv.main(["reduce","--files",*paths,"--frame","simulation","--output",str(out)])
            score = weight @ np.array([1.,2.,3.])
            with np.load(out) as data:
                assert_allclose(data["b"], np.array([score,-score]))
                assert_allclose(data["posterior_cov"], 2*np.outer(score,score))
                assert_allclose(data["posterior_mean"], 0.)
            with self.assertRaisesRegex(ValueError,"duplicate realization"):
                pv.main(["reduce","--files",paths[0],paths[0],"--frame","simulation","--output",str(root/"dup")])

    def test_fetch_resume_after_partial_batch_and_receipt_recovery(self):
        import h5py
        class S3:
            def __init__(self, bodies):
                self.bodies=bodies
                self.fail_second=True
                self.count=[0,0]
            def key_id(self, key):
                return int(pv.KEY.fullmatch(key).group(1))
            def head_object(self, Bucket, Key):
                i=self.key_id(Key)
                return {"ContentLength":len(self.bodies[i]),"ETag":f'"etag{i}"'}
            def get_object(self,Bucket,Key,IfMatch):
                i=self.key_id(Key)
                self.count[i]+=1
                head=self.head_object(Bucket,Key)
                assert IfMatch==head["ETag"]
                body=b"" if self.fail_second and i==1 else self.bodies[i]
                return dict(head,Body=BytesIO(body))
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            payload=[]
            for i in (0,1):
                with h5py.File(root/"source.h5","w") as f:
                    for name in ("density","p0","p1","p2"):
                        f.create_dataset(name,shape=(256,)*3,dtype="f4",fillvalue=i+1)
                payload.append((root/"source.h5").read_bytes())
            fake=S3(payload)
            cat={i:(SimpleNamespace(s3=fake,bucket_name="manticore-local"),
                    f"R1024/mcmc_{i}/velocity_fields/N256/field.h5") for i in (0,1)}
            store=root/"fetch"
            with patch.object(pv,"field_catalog",return_value=cat), redirect_stdout(StringIO()):
                with self.assertRaisesRegex(ValueError,"body length"):
                    pv.fetch_fields(store,[0,1],sum(map(len,payload)))
                f0=store/"manticore_local_000.h5"
                self.assertEqual(pv.draw_receipt(f0)["index"],0)
                fake.fail_second=False
                pv.fetch_fields(store,[0,1],len(payload[1]))
                self.assertEqual(fake.count,[1,2])
                pv.fetch_fields(store,[0,1],0)
                self.assertEqual(fake.count,[1,2])
                f0.unlink() # simulated interruption after sidecar publication
                pv.fetch_fields(store,[0],len(payload[0]))
                self.assertEqual(fake.count,[2,2])
                rec=pv.draw_receipt(f0)
                f0.with_suffix(".source.json").write_text(pv.canonical(dict(rec,index=1)))
                with self.assertRaisesRegex(ValueError,"release receipt"):
                    pv.draw_receipt(f0)
                f0.with_suffix(".source.json").write_text(pv.canonical(rec))
                f0.write_bytes(payload[1])
                with self.assertRaisesRegex(ValueError,"raw bytes"):
                    pv.draw_receipt(f0)

    def test_atomic_result_publication_preserves_previous_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"result.npz"
            with self.assertRaisesRegex(RuntimeError,"write failed"):
                with pv.staged(out) as f:
                    f.write(b"partial")
                    raise RuntimeError("write failed")
            self.assertEqual(list(Path(t).iterdir()),[])
            for _ in range(2):
                with pv.staged(out) as f:
                    f.write(b"same")
            with self.assertRaises(FileExistsError):
                with pv.staged(out) as f:
                    f.write(b"different")
            self.assertEqual(out.read_bytes(),b"same")
