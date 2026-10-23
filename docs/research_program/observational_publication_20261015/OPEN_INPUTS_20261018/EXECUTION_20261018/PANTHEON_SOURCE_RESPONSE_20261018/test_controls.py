"""Synthetic falsifiers only; these do not qualify physical calibration."""
import gzip
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np
import campaign as c


def tokens():
    values={name:'1.0000' for name in c.TRUTH}
    values.update(CID='0007',IDSURVEY='1',SIM_LIBID='2',SIM_NGEN_LIBID='1',
                  SIM_TYPE_INDEX='1',SIM_TEMPLATE_INDEX='0',SIM_ZFLAG='1',
                  x1='3',c='.3',x1ERR='2',cERR='.5',SIM_x1='1.0000',SIM_c='.1000',
                  SIM_AV='.1000',SIM_RV='2.0000',SIM_ZCMB='.0200',
                  COV_x1_c='.2',ERRFLAG_FIT='0',CUTFLAG_SNANA='3')
    return values


def candidate(t=None):
    t=t or tokens()
    values={head:np.float32(t[fit]) for fit,head in c.TRUTH.items()}
    for name in ('SIM_TYPE_INDEX','SIM_TEMPLATE_INDEX','SIM_REDSHIFT_FLAG'):
        values[name]=np.int32(values[name])
    values.update(RA=21.34523,DEC=34.02502,SIM_RA=float(np.float32(21.34523)),SIM_DEC=float(np.float32(34.02502)))
    return {'values':values,'dtypes':{n:np.asarray(v).dtype for n,v in values.items()},'path':'generated', 'row_index':0}


class Controls(unittest.TestCase):
    def test_reordered_columns_literal_cid(self):
        with tempfile.TemporaryDirectory(prefix='pantheon-control-') as tmp:
            path=Path(tmp)/'fixture.gz'
            with gzip.open(path,'wt') as f:f.write('VARNAMES: c CID x1\nSN: .4 0007 2\n')
            names,rows=c.parse_fitres(path)
            self.assertEqual(names,['c','CID','x1'])
            self.assertEqual(rows[0][1],{'c':'.4','CID':'0007','x1':'2'})

    def test_duplicate_cid_across_surveys_truth_disambiguates(self):
        t=tokens();wrong=candidate();wrong['values']['SIM_AV']=np.float32(.8)
        self.assertEqual(c.choose_candidate(t,[wrong,candidate()])[0],'UNIQUE_TRUTH_MATCH')
        # Literal CID alone would collide; source truth must reject the wrong survey candidate.
        self.assertEqual(c.choose_candidate(t,[wrong])[0],'TRUTH_DISAGREEMENT')

    def test_ambiguous_and_zero_candidates(self):
        self.assertEqual(c.choose_candidate(tokens(),[])[0],'ZERO_CANDIDATE')
        self.assertEqual(c.choose_candidate(tokens(),[candidate(),candidate()])[0],'MULTIPLE_AGREEING')

    def test_altered_truth_and_missing_binding(self):
        for field in c.TRUTH.values():
            wrong=candidate();wrong['values'][field]+=100
            self.assertEqual(c.choose_candidate(tokens(),[wrong])[0],'TRUTH_DISAGREEMENT',field)
        wrong=candidate();del wrong['values']['SIM_SALT2gammaDM']
        self.assertEqual(c.choose_candidate(tokens(),[wrong])[0],'MISSING_TRUTH_BINDING')

    def test_serialization_and_dtype_ulp(self):
        # Bounds use token's last decimal digit, not a relative percent margin.
        self.assertTrue(c.truth_agrees('1.230',np.float64(1.2305),np.dtype('f8')))
        self.assertFalse(c.truth_agrees('1.230',np.float64(1.23050000001),np.dtype('f8')))
        one=np.float32(1)
        step=np.nextafter(one,np.float32(math.inf))
        self.assertTrue(c.truth_agrees('1.000000000',step,np.dtype('f4')))
        self.assertFalse(c.truth_agrees('1.000000000',np.nextafter(step,np.float32(math.inf)),np.dtype('f4')))
        self.assertTrue(c.truth_agrees('1.230e-3',np.float32(.0012304),np.dtype('f4')))
        self.assertFalse(c.truth_agrees('1.230e-3',np.float32(.0012306),np.dtype('f4')))
        self.assertFalse(c.truth_agrees('1.1',np.int32(1),np.dtype('i4')))

    def test_invalid_rv_errors_flags_keep_reasons(self):
        for field,val in [('SIM_RV','0'),('SIM_AV','-.1'),('x1ERR','0'),('cERR','-1'),('c','nan'),('ERRFLAG_FIT','1'),('CUTFLAG_SNANA','1')]:
            t=tokens();t[field]=val;r,reasons=c.response(t)
            self.assertFalse(r['eligible'],field);self.assertTrue(reasons)

    def test_singular_covariance_retains_raw(self):
        t=tokens();t['COV_x1_c']='1'
        r,_=c.response(t)
        self.assertTrue(r['eligible']);self.assertIn('rc',r)
        self.assertNotIn('q_working',r)
        self.assertEqual(r['quadratic_status'],'UNEVALUABLE_CORRELATION')
        t['COV_x1_c']=str(1-5e-11)
        self.assertNotIn('q_working',c.response(t)[0])

    def test_analytic_quadratic_oracle(self):
        r,_=c.response(tokens())
        rx=2.;rc=.15
        covariance=np.array([[4.,.2],[.2,.25]])
        expected=float(np.array([rx,rc]) @ np.linalg.inv(covariance) @ np.array([rx,rc]))
        self.assertAlmostEqual(r['q_working'],expected,places=13)

    def test_zero_dust(self):
        t=tokens();t['SIM_AV']='0'
        r,_=c.response(t);self.assertEqual(r['rc'],r['rc0'])

    def test_direction_source_cast_and_historical_rejection(self):
        h=candidate()
        self.assertEqual(c.direction(h,'STRICT_STORAGE_ULP')[0],'SOURCE_COORDINATE_DISAGREEMENT')
        self.assertEqual(c.direction(h,'SNANA_FLOAT32_PROMOTED_TO_FITS_FLOAT64')[0],'QUALIFIED_NATIVE_RELEASED')
        h['values']['SIM_RA']=float(np.nextafter(np.float32(h['values']['SIM_RA']),np.float32(math.inf)))
        self.assertEqual(c.direction(h,'SNANA_FLOAT32_PROMOTED_TO_FITS_FLOAT64')[0],'SOURCE_COORDINATE_DISAGREEMENT')
        # Even a double-only perturbation hidden by a reverse float32 cast fails.
        h=candidate();h['values']['SIM_RA']=np.nextafter(h['values']['SIM_RA'],math.inf)
        self.assertEqual(c.direction(h,'SNANA_FLOAT32_PROMOTED_TO_FITS_FLOAT64')[0],'SOURCE_COORDINATE_DISAGREEMENT')
        h=candidate();h['values']['RA']=-9
        self.assertEqual(c.direction(h,'SNANA_FLOAT32_PROMOTED_TO_FITS_FLOAT64')[0],'SENTINEL_OR_RANGE')


if __name__=='__main__':unittest.main(verbosity=2)
