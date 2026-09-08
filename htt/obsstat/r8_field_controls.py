"""Source-specific released velocity-field controls, without an uncertainty law.

Coordinates are Galactic Cartesian Mpc/h; velocities are Galactic Cartesian
CMB-frame km/s. Invalid query rows survive with a reason and missing prediction.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
import numpy as np


@dataclass(frozen=True)
class GridField:
    product_id: str
    components: tuple
    origin_hmpc: float
    spacing_hmpc: float
    radius_hmpc: float | None
    metadata: dict

    def __post_init__(self):
        shapes=[np.shape(a) for a in self.components]
        if len(shapes)!=3 or len(set(shapes))!=1 or len(shapes[0])!=3 or min(shapes[0])<2:
            raise ValueError('three matching rectangular Cartesian components required')
        if any(np.asarray(a).dtype.kind!='f' for a in self.components):
            raise ValueError('real floating velocity components required')
        if not np.isfinite(self.origin_hmpc) or not np.isfinite(self.spacing_hmpc) or self.spacing_hmpc<=0:
            raise ValueError('finite origin and positive spacing required')
        if self.radius_hmpc is not None and (not np.isfinite(self.radius_hmpc) or self.radius_hmpc<=0):
            raise ValueError('positive finite support radius required')
        for key,value in {'coordinate_frame':'GALACTIC_CARTESIAN','velocity_frame':'CMB','units':'km/s'}.items():
            if self.metadata.get(key)!=value:raise ValueError(f'explicit {key}={value} required')


@dataclass(frozen=True)
class FieldSamples:
    product_id: str
    sample_ids: tuple[str,...]
    velocity_km_s: np.ndarray
    radial_km_s: np.ndarray
    status: np.ndarray

    @property
    def available(self):return self.status=='AVAILABLE_CONTROL'

    def rows(self):
        return [{'sample_id':s,'status':str(self.status[i]),
                 'velocity_km_s':self.velocity_km_s[i].tolist() if self.available[i] else None,
                 'radial_km_s':float(self.radial_km_s[i]) if self.available[i] else None}
                for i,s in enumerate(self.sample_ids)]


def galactic_positions(longitude, latitude, radius, *, units, h=None):
    l,b,r=map(lambda a:np.asarray(a,dtype=float),(longitude,latitude,radius))
    if l.ndim!=1 or b.shape!=l.shape or r.shape!=l.shape:
        raise ValueError('matching one-dimensional coordinates required')
    if not all(np.isfinite(a).all() for a in (l,b,r)) or np.any(abs(b)>90) or np.any(r<=0):
        raise ValueError('finite sky positions and positive radius required')
    if units=='Mpc':
        if h is None or not np.isfinite(h) or h<=0:raise ValueError('explicit positive h for physical Mpc')
        r=r*h
    elif units!='Mpc/h' or h is not None:raise ValueError('use Mpc/h directly or Mpc with explicit h')
    l,b=np.deg2rad(l),np.deg2rad(b)
    n=np.column_stack((np.cos(b)*np.cos(l),np.cos(b)*np.sin(l),np.sin(b)))
    return r[:,None]*n,n


def sample_field(field, sample_ids, positions_hmpc, directions) -> FieldSamples:
    ids=tuple(map(str,sample_ids));p=np.asarray(positions_hmpc,dtype=float);n=np.asarray(directions,dtype=float)
    if len(set(ids))!=len(ids) or p.shape!=(len(ids),3) or n.shape!=p.shape:
        raise ValueError('unique ordered IDs and matching Cartesian rows required')
    count=len(ids);status=np.full(count,'INVALID_QUERY',dtype='<U48')
    velocity=np.full((count,3),np.nan);radial=np.full(count,np.nan)
    good=np.isfinite(p).all(axis=1)&np.isfinite(n).all(axis=1)&(abs(np.linalg.norm(n,axis=1)-1)<1e-12)
    shape=np.array(np.shape(field.components[0]));u=np.zeros_like(p)
    u[good]=(p[good]-field.origin_hmpc)/field.spacing_hmpc
    inside=good & np.all((u>=0)&(u<=shape-1),axis=1)
    status[good & ~inside]='OUTSIDE_GRID'
    if field.radius_hmpc is not None:
        radial_ok=np.linalg.norm(p,axis=1)<=field.radius_hmpc
        status[inside & ~radial_ok]='OUTSIDE_RELEASED_SPHERE';inside &= radial_ok
    rows=np.flatnonzero(inside)
    low=np.minimum(np.floor(u[rows]).astype(int),shape-2);weight=u[rows]-low
    values=np.zeros((len(rows),3));valid=np.ones(len(rows),dtype=bool)
    status[rows]='AVAILABLE_CONTROL'
    for offsets in product((0,1),repeat=3):
        ix=low+np.array(offsets)
        if field.radius_hmpc is not None:
            corner=field.origin_hmpc+field.spacing_hmpc*ix
            allowed=np.linalg.norm(corner,axis=1)<=field.radius_hmpc
            status[rows[valid & ~allowed]]='INTERPOLATION_CORNERS_OUTSIDE_SUPPORT'
            valid &= allowed
        corner_values=np.column_stack([a[tuple(ix.T)] for a in field.components])
        finite=np.isfinite(corner_values).all(axis=1)
        status[rows[valid & ~finite]]='NONFINITE_SUPPORT_CORNER';valid &= finite
        w=np.prod(np.where(np.array(offsets),weight,1-weight),axis=1)
        values += w[:,None]*np.where(np.isfinite(corner_values),corner_values,0.)
    # The finite internal accumulator never escapes for an invalid support row.
    velocity[rows[valid]]=values[valid]
    radial[rows[valid]]=np.einsum('ij,ij->i',velocity[rows[valid]],n[rows[valid]])
    return FieldSamples(field.product_id,ids,velocity,radial,status)


def load_carrick(directory):
    directory=Path(directory);v=np.load(directory/'twompp_velocity.npy',mmap_mode='r',allow_pickle=False)
    if v.shape!=(3,257,257,257):raise ValueError('Carrick released cube shape mismatch')
    readme=(directory/'twompp_README.txt').read_text()
    if not all(s in readme for s in ['Galactic Cartesian','-200 to 200','beta* = 0.43','Vext']):
        raise ValueError('Carrick release coordinate/normalization source changed')
    return GridField('carrick_2mpp',tuple(v),-200.,400/256.,200.,{
        'coordinate_frame':'GALACTIC_CARTESIAN','velocity_frame':'CMB','units':'km/s',
        'release':'Carrick et al. 2015 v1.0','source':str(directory/'twompp_velocity.npy'),
        'axis_order':'components,X,Y,Z per released numpy cube indices; no transpose',
        'smoothing_hmpc':4.,'external_bulk':'already added by release; do not add again',
        'uncertainty_law':None})


def load_coras(path):
    path=Path(path)
    with path.open() as stream:
        header=stream.readline().strip()
    if header!='# vX[km/s]\tvY[km/s]\tvZ[km/s]':raise ValueError('CORAS velocity source header changed')
    # Parse the original rows: a cached ndarray is not used as a substitute source.
    v=np.loadtxt(path,dtype=np.float64)
    if v.shape!=(201**3,3):raise ValueError('CORAS released original row count changed')
    v=v.reshape(201,201,201,3)
    return GridField('coras_zCMB',tuple(v[:,:,:,i] for i in range(3)),-200.,2.,200.,{
        'coordinate_frame':'GALACTIC_CARTESIAN','velocity_frame':'CMB','units':'km/s',
        'release':'CORAS public reconstructed zCMB grid','source':str(path),
        'axis_order':'row=(i*201+j)*201+k; i=X,j=Y,k=Z',
        'source_documentation':'https://github.com/rlilow/CORAS#reconstructed-fields-on-a-grid',
        'smoothing_hmpc':5.,'uncertainty_law':None,
        'support':'r>200 Mpc/h zero-padded source excluded, including interpolation corners'})


def load_lilow(directory):
    from .jwst_distance_consistency import PR319_2MRS_NEURAL_FIELD_CONTRACT
    directory=Path(directory)
    fields=tuple(np.load(directory/f'{axis}Velocity.npy',mmap_mode='r',allow_pickle=False) for axis in 'xyz')
    if any(f.shape!=(128,128,128) for f in fields):raise ValueError('PR319 neural field shape mismatch')
    return GridField('lilow_2mrs',fields,-63.5*3.125,3.125,200.,{
        **PR319_2MRS_NEURAL_FIELD_CONTRACT,'coordinate_frame':'GALACTIC_CARTESIAN',
        'velocity_frame':'CMB','units':'km/s','source':str(directory),
        'uncertainty_law':None,'source_byte_binding':'caller binds PR319 selected members'})
