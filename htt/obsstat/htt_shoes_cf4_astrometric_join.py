"""Source-position candidate matching, NOT a verified SH0ES-to-CF4 anchor identity.

Inputs are Cepheid STAR positions for SH0ES host field labels and CF4
Cepheid-distance GALAXY positions (both native J2000 equatorial).
A small sky separation is evidence for a candidate, not an anchor
covariance, common Cepheid event, or exact host ID crosswalk.
"""
from __future__ import annotations
import re
import numpy as np
from scipy.spatial import cKDTree


class AstrometricJoinError(ValueError):
    pass


CEPHEID_LINE=re.compile(
    r'^\s*([A-Za-z][A-Za-z0-9.\- ]*)\s*&\s*'
    r'([0-9]{1,3}\.[0-9]+)\s*&\s*'
    r'(-?[0-9]{1,3}\.[0-9]+)\s*&')


def parse_shoes_cepheid_table_line(line):
    if not isinstance(line,str):
        raise AstrometricJoinError('SH0ES table source text expected')
    m=CEPHEID_LINE.match(line)
    if not m:
        return None
    field,ra,dec=m.group(1).strip(),float(m.group(2)),float(m.group(3))
    if not (field and 0<=ra<360 and -90<=dec<=90):
        raise AstrometricJoinError('malformed SH0ES field / astrometric position')
    return field,ra,dec


def unit_sky(radec):
    if np.iscomplexobj(radec):
        raise AstrometricJoinError('real J2000 source positions required')
    z=np.asarray(radec,dtype=float)
    if (z.ndim!=2 or z.shape[1]!=2 or not len(z)
        or not np.isfinite(z).all() or
        np.any((z[:,0]<0)|(z[:,0]>=360)) or
        np.any((z[:,1]<-90)|(z[:,1]>90))):
        raise AstrometricJoinError('finite J2000 [RA,Dec] in degrees required')
    angles=np.deg2rad(z)
    cdec=np.cos(angles[:,1])
    return np.column_stack((cdec*np.cos(angles[:,0]),
                            cdec*np.sin(angles[:,0]),np.sin(angles[:,1])))


def centroid_sky(radec):
    """Spherical normalized chord centroid for many Cepheid star positions."""
    vec=unit_sky(radec).mean(axis=0)
    size=float(np.linalg.norm(vec))
    if size<=1e-8:
        raise AstrometricJoinError('host Cepheid centroid ill-conditioned')
    v=vec/size
    ra=float(np.rad2deg(np.arctan2(v[1],v[0]))%360)
    dec=float(np.rad2deg(np.arcsin(np.clip(v[2],-1,1))))
    return ra,dec


def nearest_catalogue_source(host_cepheid_radec, cf4_galaxy_radec,
                             *,cut_arcmin=4.):
    """Find nearest CF4 Cepheid-measured galaxy, reject ambiguous near ties.

    The angular criterion is a candidate selection, NOT a source identity
    verification. It uses the exact measured source coordinates and does
    not substitute inferred group distance for host association.
    """
    if not np.isfinite(cut_arcmin) or cut_arcmin<=0 or cut_arcmin>=60:
        raise AstrometricJoinError('declared angular cutoff must be in (0,60) arcmin')
    host=centroid_sky(host_cepheid_radec)
    h=unit_sky([host])[0]
    catalog=unit_sky(cf4_galaxy_radec)
    k=min(2,len(catalog))
    dis,ids=cKDTree(catalog).query(h,k=k)
    dist=np.atleast_1d(dis)
    index=np.atleast_1d(ids)
    angle=np.rad2deg(2*np.arcsin(np.clip(dist/2,0,1)))*60
    flag='POSITION_CANDIDATE' if angle[0]<cut_arcmin else 'NO_MATCH_WITHIN_CUT'
    if flag=='POSITION_CANDIDATE' and len(angle)>1 and angle[1]<cut_arcmin:
        flag='AMBIGUOUS_WITHIN_CUT'
    return {
        'status':flag,
        'centroid_RA_J2000_deg':host[0],
        'centroid_DEC_J2000_deg':host[1],
        'nearest_index':int(index[0]),
        'first_distance_arcmin':float(angle[0]),
        'second_distance_arcmin':float(angle[1]) if len(angle)>1 else None,
        'candidate_cut_arcmin':float(cut_arcmin),
        'candidate_host_ID_verification':'NOT_PERFORMED_POSITION_ONLY'
    }
