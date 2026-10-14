import importlib.util
from pathlib import Path
import numpy as np
from astropy.io import fits

path=Path(__file__).resolve().parents[2]/'scripts/run_reboot_cosmos_selection.py'
spec=importlib.util.spec_from_file_location('cosmos_reader',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_raw_window_big_endian_logical_and_chunk_boundaries(tmp_path):
    p=tmp_path/'fixture.fits'
    h=fits.BinTableHDU.from_columns([fits.Column(name='id',format='K',array=np.arange(5)),fits.Column(name='value',format='D',array=np.arange(5)+.3),fits.Column(name='flag',format='L',array=[0,1,0,1,0])])
    h.writeto(p)
    with fits.open(p,memmap=True) as hdus:spec=m.table_spec(hdus[1])
    values=m.read_window(p,spec,1,4,['id','value','flag'])
    np.testing.assert_array_equal(values['id'],[1,2,3]);np.testing.assert_allclose(values['value'],[1.3,2.3,3.3]);np.testing.assert_array_equal(values['flag'],[True,False,True])
