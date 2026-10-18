"""Angular candidate matching of actual Cepheid host fields and CF4 galaxies."""
import numpy as np
import pytest
from obsstat.htt_shoes_cf4_astrometric_join import (
   unit_sky,centroid_sky,nearest_catalogue_source,
   parse_shoes_cepheid_table_line, AstrometricJoinError)


def test_wraparound_host_centroid_stays_near_ra_zero():
    x=centroid_sky([(359.99,12.),(.01,12.),(0.,12.)])
    assert abs(x[0])<.02 or x[0]>359.98
    assert x[1]==pytest.approx(12.,abs=.001)


def test_spherical_nearest_candidate_with_second_nearest_rejection():
    sky=np.array([[45.,33.],[46.,34.],[51.,37.]])
    v=nearest_catalogue_source([(45.0005,33.0003)],sky,cut_arcmin=4)
    assert v['status']=='POSITION_CANDIDATE'
    assert v['first_distance_arcmin']<.05
    assert v['nearest_index']==0
    v2=nearest_catalogue_source([(45.0005,33.0003)],
        np.array([[45.0002,33.0003],[45.0006,33.0004]]),
        cut_arcmin=4)
    assert v2['status']=='AMBIGUOUS_WITHIN_CUT'
    v3=nearest_catalogue_source([(45.0005,33.0003)],
        np.array([[55.,39.],[56.,40.]]),cut_arcmin=4)
    assert v3['status']=='NO_MATCH_WITHIN_CUT'


def test_parser_ignores_latex_headers_and_preserves_source_positions():
    line='N4258 & 184.74149 & 47.303103 & 5 & 33.72 & 0.92 & 0.04 & 24.52 \\\\'
    assert parse_shoes_cepheid_table_line(line)==('N4258',184.74149,47.303103)
    assert parse_shoes_cepheid_table_line(r'\colhead{Field}& RA & DEC') is None


def test_sky_unit_real_frame_finite():
    x=unit_sky([(0,0),(90,0),(180,0)])
    np.testing.assert_allclose(x,[[1,0,0],[0,1,0],[-1,0,0]],atol=1e-14)
    with pytest.raises(AstrometricJoinError):
        unit_sky([(1,102)])
    with pytest.raises(AstrometricJoinError):
        centroid_sky([])
