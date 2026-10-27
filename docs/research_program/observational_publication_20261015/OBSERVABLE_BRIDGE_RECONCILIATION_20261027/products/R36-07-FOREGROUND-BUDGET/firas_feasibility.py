"""Consume actual Pass4 LOWF tables for bounded-source feasibility diagnostics.

This tests source geometry and data semantics.  It intentionally makes no beam
lower-envelope, LOS support, or full-sky intensity certificate.
"""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
from astropy.io import fits
from scipy.spatial import cKDTree
import healpy as hp

ROOT=Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_budget_actual')
SOURCE=ROOT/'source'
SKY=SOURCE/'FIRAS_DESTRIPED_SKY_SPECTRA_LOWF.FITS'
CV=SOURCE/'FIRAS_C_VECTOR_LOWF.FITS'
COV=SOURCE/'FIRAS_COVARIANCE_MATRIX_LOWF.FITS'
MODEL=SOURCE/'FIRAS_MODEL_ERRORS_LOWF.FITS'
BEAM=SOURCE/'firas_beam_radial_profile.txt'
S7=Path('/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/run/COMMON_SUPPORT_S7.npz')

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

with fits.open(SKY,memmap=True) as h:
 header=h[0].header
 nfreq=int(header['NUM_FREQ']);zero=float(header['NU_ZERO']);delta=float(header['DELTA_NU'])
 lon=np.asarray(h[1].data['GAL_LON'],float);lat=np.asarray(h[1].data['GAL_LAT'],float)
 pixel=np.asarray(h[1].data['PIXEL'],int)
 weight=np.asarray(h[1].data['WEIGHT'],float)
 spectrum=np.asarray(h[1].data['SPECTRUM'],float)
with fits.open(CV,memmap=True) as h: c=np.asarray(h[1].data['C_VECTOR'][0],float)
with fits.open(COV,memmap=True) as h: cov=np.asarray(h[1].data['ROW_COVR'],float)
with fits.open(MODEL,memmap=True) as h: model_rows=len(h[1].data)
beam_profile=np.loadtxt(BEAM)
if nfreq!=43 or spectrum.shape!=(6067,182) or cov.shape!=(43,182):raise RuntimeError('FIRAS_VALID_FREQUENCY_OR_SHAPE')
if not np.all(spectrum[:,nfreq:]==0):raise RuntimeError('FIRAS_TRAILING_DATA_CHANGED')
if not np.all(weight>0):raise RuntimeError('FIRAS_NONPOSITIVE_WEIGHT')
if c[:nfreq].shape!=(43,) or not np.isfinite(c[:nfreq]).all() or not np.isfinite(cov[:,:nfreq]).all():
 raise RuntimeError('FIRAS_C_VECTOR_OR_COVARIANCE_INVALID')
with np.load(S7,allow_pickle=False) as z:ring=np.asarray(z['retained_ring64'],int)
theta,phi=hp.pix2ang(64,ring,nest=False)
target=np.column_stack((np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi),np.cos(theta)))
src_theta=np.deg2rad(90-lat);src_phi=np.deg2rad(lon)
source=np.column_stack((np.sin(src_theta)*np.cos(src_phi),np.sin(src_theta)*np.sin(src_phi),np.cos(src_theta)))
distance,index=cKDTree(source).query(target)
angle=2*np.arcsin(np.minimum(1,distance/2))*180/np.pi
freq=zero+delta*np.arange(nfreq)
with (ROOT/'FIRAS_VALID43_TABLE.csv').open('w',newline='') as f:
 writer=csv.writer(f)
 writer.writerow(('bin_zero_based','nominal_frequency_GHz','measured_min_MJy_sr',
                  'measured_median_MJy_sr','measured_max_MJy_sr',
                  'negative_rows','C_vector_MJy_sr','covariance_diagonal_MJy_sr_squared'))
 for i,nu in enumerate(freq):
  vals=spectrum[:,i]
  writer.writerow((i,float(nu),float(vals.min()),float(np.median(vals)),float(vals.max()),
                   int(np.sum(vals<0)),float(c[i]),float(cov[i,i])))
out={
 'source_files':{str(p):{'sha256':digest(p),'bytes':p.stat().st_size} for p in (SKY,CV,COV,MODEL,BEAM)},
 'FIRAS':'Pass4 LOWF measured absolute sky spectra, MJy/sr; not a positive foreground-component upper certificate',
 'rows':len(pixel),'positive_weight_rows':int(np.sum(weight>0)),'pixel_id_minmax':[int(pixel.min()),int(pixel.max())],
 'valid_frequency_count_from_NUM_FREQ':nfreq,'stored_spectrum_columns':spectrum.shape[1],
 'trailing_zero_columns_are_padding':int(spectrum.shape[1]-nfreq),
 'frequency_GHz_first_last':[float(freq[0]),float(freq[-1])],
 'spectrum_valid43_minmax_MJy_per_sr':[float(spectrum[:,:nfreq].min()),float(spectrum[:,:nfreq].max())],
 'valid43_negative_sample_count':int(np.sum(spectrum[:,:nfreq]<0)),
 'C_vector_interpretation':'FIRAS explanatory supplement calls C vector square root of a diagonal covariance component, MJy/sr; exact relation to separately released covariance matrix is unresolved here',
 'C_vector_diagonal_relative_max':float(np.max(np.abs(np.diag(cov[:,:nfreq])-c[:nfreq]**2)/np.maximum(c[:nfreq]**2,1e-30))),
 'C_vector_vs_released_covariance_status':'OBSERVED_BYTE_NUMERICAL_DIFFERENCE; NO_EQUIVALENCE_ACCEPTANCE_GATE; NOT_USED_FOR_PHYSICAL_RADIUS',
 'model_selection_rows':model_rows,
 'S7_ring_center_count':len(ring),
 'nearest_FIRAS_centre_angle_deg_quantiles':[float(v) for v in np.quantile(angle,[0,.5,.9,.99,1])],
 'S7_ring_centres_more_than_3p5_deg_from_nearest_FIRAS_centre':int(np.sum(angle>3.5)),
 'instantaneous_Moon_beam_profile_max_radius_deg':float(beam_profile[-1,0]),
 'coverage_status':'CENTRE_DISTANCE_DIAGNOSTIC_ONLY; scan-elongated FIRAS beam lower response unknown; no unbounded physical sector inferred from nearest-centre distance',
 'positive_domination_certified_S7_sectors':[],
 'positive_domination_uncertain_S7_sector_count':len(ring),
 'physical_unbounded_sector_count':'UNKNOWN_WITHOUT_RESPONSE_LOWER_CERTIFICATE',
 'positive_dual_certificate':'NOT_EVALUABLE: calibrated full-sky absolute functional or target-kernel-dominating nonnegative aggregate response, with beam/spectral lower bounds, absent',
 'physical_LOS_domain':'NOT_BOUNDED_BY_THESE_DATA',
 'radius_upper':'NOT_ESTABLISHED',
}
(ROOT/'FIRAS_FEASIBILITY.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
np.savez_compressed(ROOT/'FIRAS_COVERAGE_DIAGNOSTIC.npz',s7_ring64=ring,nearest_centre_deg=angle,
                    nearest_source_row=index,frequencies_valid43_GHz=freq)
print(json.dumps({'rows':len(pixel),'valid_freq':nfreq,'nearest_max_deg':angle.max(),
                  'gt3p5':int(np.sum(angle>3.5))}))
