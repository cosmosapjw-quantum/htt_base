"""Read the retained DESI qiso release, without replacing it with a newer one."""
from pathlib import Path
import hashlib

DESI_QISO_SHA256 = '836a2107c1edfb655f7a5c41701607dd8542efe4dae4309737658829cfe63ba3'


def read_desi_qiso(path):
    # h5py is an optional reader dependency, never an import-time requirement.
    import h5py
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != DESI_QISO_SHA256:
        raise ValueError('retained immutable DESI release input SHA256 mismatch')
    with h5py.File(path) as f:
        group = f['observable/baorecon']; q = group['qiso']
        payload = dict(likelihood_name=f['name'][()].decode(), parameter='qiso',
            observed=q['value'][()].tolist(), covariance=f['covariance/value'][()].tolist(),
            window=f['window/value'][()].tolist(), zeff=float(group.attrs['zeff']),
            DV_over_rd_fid=float(q.attrs['DV_over_rd_fid']))
    return {**payload, 'source_id': 'DESI_DR1_FULLSHAPE_BGS_v1.2:'+digest,
            'source_sha256': digest, 'source_path': str(path), 'source_bytes': path.stat().st_size,
            'alternative': 'syst only; stat alternative and raw catalogue are not independent factors'}
