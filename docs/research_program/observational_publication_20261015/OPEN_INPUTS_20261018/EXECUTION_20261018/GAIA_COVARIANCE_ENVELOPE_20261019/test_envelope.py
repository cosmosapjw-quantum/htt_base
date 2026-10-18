"""Finite algebra/parser controls only; no observational mocks or raw-file reads."""
import base64
import io
import json
import unittest
import warnings

import numpy as np
from astropy.io.votable import parse_single_table

import envelope as e


def row_array(n=1):
    rows = np.zeros(n, dtype=e.DTYPE)
    for i in range(n):
        rows['source_id'][i] = -1234567890123+i
        rows['ra'][i], rows['dec'][i] = 123.25+i, -45.5
        rows['pmra'][i], rows['pmdec'][i] = -3.5, 2.75
        rows['pmra_error'][i], rows['pmdec_error'][i] = .125, .25
        rows['pmra_pmdec_corr'][i] = -.375
        rows['astrometric_params_solved'][i] = -31
    return rows


def fixture(rows, encoded=None, trailer=''):
    fields = ''.join('<FIELD name="%s" datatype="%s"%s/>' % (name, typ,
                      '' if unit is None else ' unit="'+unit+'"')
                     for name, typ, unit in zip(e.NAMES, e.TYPES, e.UNITS))
    payload = base64.b64encode(rows.tobytes()).decode() if encoded is None else encoded
    return (f'<?xml version="1.0"?><VOTABLE xmlns="{e.NS}" version="1.4">'
            '<RESOURCE type="results"><INFO name="QUERY_STATUS" value="OK"/>'
            '<TABLE name="result_1792320789985">'+fields+
            '<DATA><BINARY2><STREAM encoding="base64">'+payload+
            '</STREAM></BINARY2></DATA></TABLE>'+trailer+'</RESOURCE></VOTABLE>').encode()


def parse(data, sizes=None, batch=25000):
    collected = []
    reader = e.FrozenReader(lambda rows: collected.append(rows.copy()), batch_rows=batch)
    if sizes is None:
        reader.feed(data)
    else:
        at = 0
        for size in sizes:
            reader.feed(data[at:at+size]); at += size
        reader.feed(data[at:])
    reader.feed(b'', final=True)
    for batch_rows in collected:
        assert batch_rows.dtype == e.DTYPE
        assert batch_rows.dtype.itemsize == 88
    return reader, np.concatenate(collected, dtype=e.DTYPE, casting='no') if collected else np.zeros(0, dtype=e.DTYPE)


class ParserControls(unittest.TestCase):
    def test_all_sixteen_null_bits_against_astropy(self):
        for j in range(16):
            with self.subTest(j=j):
                rows = row_array()
                rows['mask'][0, j//8] |= 1 << (7-j%8)
                # Nonzero null payload remains present; all later fields must align.
                data = fixture(rows)
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    reference = parse_single_table(io.BytesIO(data)).array
                for k, name in enumerate(e.NAMES):
                    self.assertEqual(bool(reference.mask[name][0]), j == k)
                    if j != k:
                        self.assertEqual(reference.data[name][0], rows[name][0])
                if j < 8:
                    with self.assertRaisesRegex(ValueError, 'Required source field NULL'):
                        parse(data)
                else:
                    reader, got = parse(data)
                    self.assertEqual(reader.optional_null[j-8], 1)
                    self.assertEqual(got.tobytes(), rows.tobytes())

    def test_endian_and_signed(self):
        rows = row_array(3)
        _, got = parse(fixture(rows))
        self.assertEqual(got.tobytes(), rows.tobytes())
        self.assertEqual(int(got['source_id'][0]), -1234567890123)
        self.assertEqual(int(got['astrometric_params_solved'][0]), -31)
        self.assertEqual(float(got['pmra_pmdec_corr'][0]), -.375)

    def test_every_single_boundary_and_single_byte_chunks(self):
        rows = row_array(2)
        data = fixture(rows)
        for split in range(len(data)+1):
            _, got = parse(data, [split], batch=1)
            self.assertEqual(got.tobytes(), rows.tobytes())
        _, got = parse(data, [1]*len(data), batch=1)
        self.assertEqual(got.tobytes(), rows.tobytes())

    def test_three_padding_cases_and_xml_whitespace(self):
        for n in (1, 2, 3):
            rows = row_array(n)
            encoded = base64.b64encode(rows.tobytes()).decode()
            encoded = ' \n\t\r'.join(encoded[i:i+7] for i in range(0, len(encoded), 7))
            _, got = parse(fixture(rows, encoded), [1]*10000, batch=1)
            self.assertEqual(got.tobytes(), rows.tobytes())

    def test_optional_nonfinite_remains_unknown_and_direction_no_new_cut(self):
        rows = row_array()
        rows['ruwe'] = np.nan
        rows['ra'] = 361  # D05 imposed finite validity only, no new domain cut.
        reader, got = parse(fixture(rows))
        self.assertEqual(reader.optional_nonfinite[-1], 1)
        self.assertTrue(np.isnan(got['ruwe'][0]))

    def test_rejects_malformed_and_incomplete(self):
        rows = row_array()
        good = fixture(rows)
        encoded = base64.b64encode(rows.tobytes()).decode()
        bad = [good[:-1], good[:-40], fixture(rows, encoded[:-1]),
               fixture(rows, base64.b64encode(rows.tobytes()[:-1]).decode()),
               fixture(rows, encoded+'AAAA'), fixture(rows, encoded+'='),
               fixture(rows, '!'+encoded[1:]), fixture(rows, encoded+'\v'),
               good.replace(b'encoding="base64"', b'encoding="base64" href="elsewhere"'),
               good.replace(b'name="ra" datatype="double"', b'name="wrong" datatype="double"'),
               good.replace(b'name="ra" datatype="double"', b'name="ra" datatype="double" arraysize="1"'),
               good.replace(b'<DATA>', b'<VALUES null="x"/><DATA>'),
               good.replace(b'value="OK"', b'value="ERROR"'),
               good.replace(b'<BINARY2>', b'<BINARY>').replace(b'</BINARY2>', b'</BINARY>'),
               good.replace(b'<INFO name="QUERY_STATUS" value="OK"/>', b''),
               good.replace(b'version="1.4"', b'version="1.3"')]
        for status in ('ERROR', 'OVERFLOW'):
            bad.append(fixture(rows, trailer=f'<INFO name="QUERY_STATUS" value="{status}"/>'))
        for data in bad:
            with self.subTest(data=data[-100:]):
                with self.assertRaises((ValueError, e.expat.ExpatError)):
                    parse(data)

    def test_required_invalid_not_dropped(self):
        for name, value in [('ra', np.nan), ('dec', np.inf), ('pmra', np.nan),
                            ('pmdec', np.inf), ('pmra_error', 0), ('pmdec_error', -1),
                            ('pmra_pmdec_corr', 1), ('pmra_pmdec_corr', np.nan)]:
            rows = row_array(); rows[name] = value
            with self.assertRaises(ValueError):
                parse(fixture(rows))


class KernelControls(unittest.TestCase):
    def assertE(self, a, b):
        self.assertLessEqual(e.normalized_error(a, np.asarray(b)), 1e-12)

    def test_frozen_cached_mapping(self):
        _, _, _, _, controls = e.load_inputs()
        self.assertTrue(all(v <= 1e-12 for v in controls.values()))

    def test_exact_zero_and_one_source(self):
        zero = e.variance_kernel(np.zeros((2, 2, 3)), [2, 2], [3, 3], [1/6, 1/6])
        self.assertTrue(np.array_equal(zero, np.zeros((2, 3))))
        c = np.array([[4., 1.], [1., 9.]])
        ell = np.array([1., -2.])
        t = (ell @ c)[None, :, None]
        s2 = e.variance_kernel(t, [2], [3], [1/6])
        self.assertE(s2, [[36]])
        self.assertE(np.sum(np.sqrt(s2), axis=0)**2, [36])
        # Attaining decomposition and zero-weight residual avoid division by zero.
        a = c @ ell / 6
        self.assertE(ell @ a, 6)
        self.assertGreaterEqual(np.linalg.eigvalsh(c-np.outer(a, a)).min(), -1e-12)

    def test_two_sources_attainment_and_transformations(self):
        t = np.array([[[1.], [0.]], [[-2.], [0.]]])
        s2 = e.variance_kernel(t, [1, 1], [1, 1], [0, 0])
        self.assertE(s2.sum(axis=0), [5])
        self.assertE(np.sqrt(s2).sum(axis=0)**2, [9])
        cross = np.diag([-1., 0.])
        joint = np.block([[np.eye(2), cross], [cross, np.eye(2)]])
        ell = np.array([1., 0., -2., 0.])
        self.assertE(ell @ joint @ ell, 9)
        self.assertGreaterEqual(np.linalg.eigvalsh(joint).min(), 0)
        self.assertE(e.variance_kernel(-t, [1, 1], [1, 1], [0, 0]), s2)
        self.assertE(e.variance_kernel(t[::-1], [1, 1], [1, 1], [0, 0])[::-1], s2)
        self.assertE(e.variance_kernel(t[:, ::-1], [1, 1], [1, 1], [0, 0]), s2)

    def test_stable_direct_unit_and_batch_parity(self):
        sa, sd, rho = np.array([2., 4., .1]), np.array([3., .7, 5.]), np.array([.2, -.8, .99])
        t = np.arange(18, dtype=float).reshape(3, 2, 3)/7-1
        s2 = e.variance_kernel(t, sa, sd, rho)
        direct = []
        for i in range(3):
            c = np.array([[sa[i]**2, rho[i]*sa[i]*sd[i]], [rho[i]*sa[i]*sd[i], sd[i]**2]])
            ell = np.linalg.solve(c, t[i])
            direct.append(np.diag(ell.T @ c @ ell))
        self.assertE(s2, np.array(direct))
        self.assertE(e.variance_kernel(t[:, ::-1], sd, sa, rho), s2)
        # With fixed ell, C -> u^2 C and t=ell C -> u^2 t gives s^2 -> u^2 s^2.
        self.assertE(e.variance_kernel(t*1e6, sa*1000, sd*1000, rho), s2*1e6)
        parts = [e.variance_kernel(t[i:i+1], sa[i:i+1], sd[i:i+1], rho[i:i+1]) for i in range(3)]
        self.assertE(sum(np.sum(p, axis=0, dtype=np.longdouble) for p in parts), np.sum(s2, axis=0, dtype=np.longdouble))
        self.assertE(sum(np.sum(np.sqrt(p), axis=0, dtype=np.longdouble) for p in parts), np.sum(np.sqrt(s2), axis=0, dtype=np.longdouble))
        # Float32 multiplication before promotion is detectably different.
        value = np.array([.1234567], dtype=np.float32)
        self.assertFalse(np.array_equal(value.astype(float)*1000, (value*1000).astype(float)))

    def test_invalid_kernel(self):
        for sa, sd, rho in [(0, 1, 0), (1, -1, 0), (1, 1, 1), (1, 1, np.nan)]:
            with self.assertRaises(ValueError):
                e.variance_kernel(np.ones((1, 2, 1)), [sa], [sd], [rho])
        with self.assertRaises(ValueError):
            e.variance_kernel(np.full((1, 2, 1), np.inf), [1], [1], [0])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    if outcome.wasSuccessful():
        with (e.HERE / 'CONTROLS.json').open('x') as out:
            json.dump(dict(status='PASS', tests=outcome.testsRun, code_sha256=e.digest(e.__file__),
                           test_sha256=e.digest(__file__), contract_sha256=e.CONTRACT_SHA,
                           parser='All 16 MSB-first null flags independently compared with Astropy tiny fixtures; every short-fixture split',
                           finite_tolerance='E<=1e-12; zero kernel exact', observational_mock_generation=False), out, indent=2)
    raise SystemExit(not outcome.wasSuccessful())
