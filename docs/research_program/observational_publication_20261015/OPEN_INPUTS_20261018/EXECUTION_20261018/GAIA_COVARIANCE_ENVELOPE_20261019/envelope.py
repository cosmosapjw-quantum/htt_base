"""Frozen-schema streaming Gaia working-marginal covariance envelope; C0 only."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import xml.parsers.expat as expat

import numpy as np

HERE = Path(__file__).resolve().parent
D05 = HERE.parent / 'D05_GAIA_RADIO'
RAW = Path('/mnt/extdrive/workdir/htt_open_data/gaia/d05_full_20261018/full.vot')
NS = 'http://www.ivoa.net/xml/VOTable/v1.3'
EXPECTED = {
    'observable_vsh.py': '318acb829f163eedda76a136a0edc4d247c17a6893f2faf24681e34fd79822b5',
    'sufficient_statistics.npz': '6d899d4bad30c7f30f6b04ba8381ec623d9d5f6263d464d99d580d38437e2c83',
    'RESULTS.json': '386bfa19ff1f0c24ec836f2e3e471717edf38c3c10da6d119d70548cf062baa0',
}
RAW_SHA = 'e8454190bb3be7d10203ecfe6fe90b34d245fb13b9bb72a155242f85e4271810'
CONTRACT_SHA = 'd0ceb037506d7ac94e4275194544b3572f927f9a865faeeecd00db05453e44ea'
NAMES = ['source_id', 'ra', 'dec', 'pmra', 'pmdec', 'pmra_error', 'pmdec_error',
         'pmra_pmdec_corr', 'ra_pmra_corr', 'ra_pmdec_corr', 'dec_pmra_corr',
         'dec_pmdec_corr', 'parallax', 'parallax_error', 'astrometric_params_solved', 'ruwe']
TYPES = ['long', 'double', 'double', 'double', 'double', 'float', 'float', 'float',
         'float', 'float', 'float', 'float', 'double', 'float', 'short', 'float']
UNITS = [None, 'deg', 'deg', 'mas.yr**-1', 'mas.yr**-1', 'mas.yr**-1', 'mas.yr**-1',
         None, None, None, None, None, 'mas', 'mas', None, None]
FORMATS = ['>i8', '>f8', '>f8', '>f8', '>f8', '>f4', '>f4', '>f4', '>f4', '>f4',
           '>f4', '>f4', '>f8', '>f4', '>i2', '>f4']
DTYPE = np.dtype([('mask', 'u1', (2,))] + list(zip(NAMES, FORMATS)), align=False)
assert DTYPE.itemsize == 88
KEEP = np.array([0, 1, 2, *range(6, 16)])
FRAME = np.array([3, 4, 5])


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def normalized_error(a, b):
    return float(np.max(np.abs(np.asarray(a) - b)) / (1 + np.max(np.abs(b))))


def load_inputs():
    require(digest(HERE / 'CONTRACT.md') == CONTRACT_SHA, 'Frozen contract drift')
    for name, sha in EXPECTED.items():
        require(digest(D05 / name) == sha, 'Frozen D05 input drift: ' + name)
    spec = importlib.util.spec_from_file_location('sealed_d05', D05 / 'observable_vsh.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with np.load(D05 / 'sufficient_statistics.npz', allow_pickle=False) as z:
        normal = z['normal'].copy()  # No RHS loaded or fit executed.
    old = json.loads((D05 / 'RESULTS.json').read_text())
    r = np.eye(16)[KEEP]
    m = np.linalg.solve(normal.T, r.T).T
    b = normal[np.ix_(KEEP, FRAME)] @ np.linalg.inv(normal[np.ix_(FRAME, FRAME)])
    h = normal[np.ix_(KEEP, KEEP)] - b @ normal[np.ix_(FRAME, KEEP)]
    q = r.copy()
    q[:, FRAME] = -b
    cov = m[:, KEEP]
    controls = {
        'MN_equals_R_E': normalized_error(m @ normal, r),
        'Schur_map_E': normalized_error(m, np.linalg.solve(h, q)),
        'saved_quotient_covariance_E': normalized_error(cov, np.array(old['all']['frame_projected']['covariance_uas2yr2'])),
    }
    require(all(v <= 1e-12 for v in controls.values()), 'Cached algebra control failed')
    require(np.all(np.diag(cov) > 0), 'Nonpositive cached variance')
    return module, m, cov, old, controls


def validate_rows(rows):
    mask = np.unpackbits(rows['mask'], axis=1).astype(bool)
    require(not np.any(mask[:, :8]), 'Required source field NULL')
    for name in NAMES[1:8]:
        require(np.all(np.isfinite(rows[name])), 'Required source field nonfinite: ' + name)
    require(np.all(rows['pmra_error'] > 0) and np.all(rows['pmdec_error'] > 0), 'Nonpositive error')
    require(np.all(np.abs(rows['pmra_pmdec_corr']) < 1), 'Invalid correlation')
    return mask


class FrozenReader:
    """One bounded binary buffer; complete XML and raw hash accepted only at EOF."""
    def __init__(self, consume, batch_rows=25000):
        require(1 <= batch_rows <= 25000, 'Batch cap')
        self.consume = consume
        self.batch_rows = batch_rows
        self.stack = []
        self.fields = []
        self.status = []
        self.counts = dict(VOTABLE=0, RESOURCE=0, TABLE=0, DATA=0, BINARY2=0, STREAM=0)
        self.b64 = ''
        self.binary = bytearray()
        self.padded = False
        self.rows = 0
        self.optional_null = np.zeros(8, dtype=np.int64)
        self.optional_nonfinite = np.zeros(8, dtype=np.int64)
        self.parser = expat.ParserCreate(namespace_separator='|')
        self.parser.StartElementHandler = self.start
        self.parser.EndElementHandler = self.end
        self.parser.CharacterDataHandler = self.characters
        self.parser.StartDoctypeDeclHandler = lambda *args: require(False, 'DOCTYPE forbidden')
        self.parser.ExternalEntityRefHandler = lambda *args: 0

    def start(self, full, attrs):
        require(full.startswith(NS + '|'), 'Unexpected XML namespace')
        tag = full.split('|')[-1]
        parent = self.stack[-1] if self.stack else None
        if tag in self.counts:
            self.counts[tag] += 1
            require(self.counts[tag] == 1, 'Duplicate structure: ' + tag)
        if tag == 'VOTABLE':
            require(parent is None and attrs.get('version') == '1.4', 'VOTABLE structure/version')
        elif tag == 'RESOURCE':
            require(parent == 'VOTABLE' and attrs.get('type') == 'results', 'Results RESOURCE')
        elif tag == 'TABLE':
            require(parent == 'RESOURCE' and attrs.get('name') == 'result_1792320789985', 'TABLE identity')
        elif tag == 'FIELD':
            require(parent == 'TABLE' and not self.counts['DATA'], 'FIELD position')
            i = len(self.fields)
            require(i < 16, 'Extra FIELD')
            require((attrs.get('name'), attrs.get('datatype'), attrs.get('unit')) ==
                    (NAMES[i], TYPES[i], UNITS[i]), 'FIELD schema mismatch')
            require('arraysize' not in attrs, 'Array FIELD forbidden')
            self.fields.append(dict(attrs))
        elif tag == 'VALUES':
            require('null' not in attrs, 'VALUES null forbidden')
        elif tag == 'DATA':
            require(parent == 'TABLE' and len(self.fields) == 16, 'DATA structure/schema')
        elif tag == 'BINARY2':
            require(parent == 'DATA', 'BINARY2 structure')
        elif tag == 'STREAM':
            require(parent == 'BINARY2' and attrs.get('encoding') == 'base64' and
                    'href' not in attrs and not any(k.endswith('|href') for k in attrs), 'STREAM schema')
        elif tag in ('BINARY', 'TABLEDATA', 'FITS'):
            require(False, 'Unexpected serialization')
        elif tag == 'INFO' and attrs.get('name') == 'QUERY_STATUS':
            require(parent == 'RESOURCE', 'QUERY_STATUS position')
            self.status.append(attrs.get('value'))
            require(attrs.get('value') == 'OK', 'Non-OK QUERY_STATUS')
        require(parent != 'STREAM', 'Element inside STREAM')
        self.stack.append(tag)

    def end(self, full):
        tag = full.split('|')[-1]
        require(self.stack and self.stack[-1] == tag, 'XML structure')
        if tag == 'STREAM':
            require(not self.b64, 'Partial base64 quantum')
            require(len(self.binary) % 88 == 0, 'Partial final row')
            self.flush(final=True)
        self.stack.pop()

    def characters(self, value):
        if not self.stack or self.stack[-1] != 'STREAM':
            return
        value = value.translate(str.maketrans('', '', ' \t\r\n'))
        if not value:
            return
        require(not self.padded, 'Data after base64 padding')
        self.b64 += value
        n = len(self.b64) // 4 * 4
        if n:
            chunk, self.b64 = self.b64[:n], self.b64[n:]
            decoded = base64.b64decode(chunk, validate=True)
            if '=' in chunk:
                require(base64.b64encode(decoded).decode('ascii') == chunk, 'Invalid/noncanonical padding')
                self.padded = True
                require(not self.b64, 'Data after base64 padding')
            self.binary.extend(decoded)
            self.flush()

    def flush(self, final=False):
        size = self.batch_rows * 88
        while len(self.binary) >= size or (final and self.binary):
            n = min(len(self.binary) // 88, self.batch_rows)
            payload = bytes(self.binary[:n * 88])
            del self.binary[:n * 88]
            rows = np.frombuffer(payload, dtype=DTYPE)
            mask = validate_rows(rows)
            self.optional_null += mask[:, 8:].sum(axis=0)
            for j, name in enumerate(NAMES[8:]):
                self.optional_nonfinite[j] += np.sum(~mask[:, 8+j] & ~np.isfinite(rows[name]))
            self.consume(rows)
            self.rows += n

    def feed(self, value, final=False):
        self.parser.Parse(value, final)
        if final:
            require(not self.stack and all(v == 1 for v in self.counts.values()), 'Missing XML structure')
            require(self.status and all(s == 'OK' for s in self.status), 'Missing/non-OK status')


def variance_kernel(t, sa, sd, rho):
    sa, sd, rho = [np.asarray(x, dtype=np.float64) for x in (sa, sd, rho)]
    require(np.all(np.isfinite(t)) and all(np.all(np.isfinite(x)) for x in (sa, sd, rho)), 'Nonfinite kernel')
    require(np.all(sa > 0) and np.all(sd > 0) and np.all(np.abs(rho) < 1), 'Invalid covariance')
    a, b = t[:, 0, :] / sa[:, None], t[:, 1, :] / sd[:, None]
    s2 = b*b + (a-rho[:, None]*b)**2/(1-rho[:, None]**2)
    require(np.all(np.isfinite(s2)) and np.all(s2 >= 0), 'Invalid variance')
    return s2


class Accumulator:
    def __init__(self, module, m):
        self.module, self.m = module, m
        self.sum_s = np.zeros(13, dtype=np.longdouble)
        self.sum_s2 = np.zeros(13, dtype=np.longdouble)
        self.frame = np.zeros((13, 3), dtype=np.longdouble)
        self.batches = 0

    def __call__(self, rows):
        x = self.module.design(rows['ra'].astype(float), rows['dec'].astype(float))
        t = x @ self.m.T
        # Promote float32 source errors BEFORE the one mas -> microas scale.
        sa = rows['pmra_error'].astype(np.float64) * 1000
        sd = rows['pmdec_error'].astype(np.float64) * 1000
        rho = rows['pmra_pmdec_corr'].astype(np.float64)
        s2 = variance_kernel(t, sa, sd, rho)
        self.sum_s += np.sum(np.sqrt(s2), axis=0, dtype=np.longdouble)
        self.sum_s2 += np.sum(s2, axis=0, dtype=np.longdouble)
        w = self.module.precision(sa, sd, rho)
        ell = np.einsum('nik,nij->njk', t, w)
        f = np.einsum('nik,nij->nkj', ell, x[:, :, FRAME])
        self.frame += np.sum(f, axis=0, dtype=np.longdouble)
        self.batches += 1
        print(json.dumps({'batch': self.batches, 'rows': len(rows)}), flush=True)


def stat_identity(stat):
    return {key: getattr(stat, 'st_' + key) for key in ('dev', 'ino', 'size', 'mtime_ns', 'ctime_ns')}


def actual():
    require((HERE / 'CONTROLS.json').exists(), 'Finite controls not completed')
    finite = json.loads((HERE / 'CONTROLS.json').read_text())
    require(finite['status'] == 'PASS' and finite['code_sha256'] == digest(__file__) and
            finite['test_sha256'] == digest(HERE / 'test_envelope.py'), 'Finite controls identity')
    module, m, cov, old, controls = load_inputs()
    accum = Accumulator(module, m)
    reader = FrozenReader(accum)
    sha = hashlib.sha256()
    with RAW.open('rb') as fd:
        before_fd, before_path = stat_identity(os.fstat(fd.fileno())), stat_identity(RAW.stat())
        require(before_fd == before_path and before_fd['size'] == 192359368, 'Source identity/size before')
        for chunk in iter(lambda: fd.read(65536), b''):
            sha.update(chunk)
            reader.feed(chunk)
        reader.feed(b'', final=True)
        after_fd, after_path = stat_identity(os.fstat(fd.fileno())), stat_identity(RAW.stat())
    require(before_fd == after_fd == after_path, 'Source FD/path identity drift')
    require(sha.hexdigest() == RAW_SHA and reader.rows == 1614173, 'Final raw SHA/count')
    ref = np.asarray(accum.sum_s2, dtype=float)
    vmax = np.asarray(accum.sum_s**2, dtype=float)
    relative = np.abs(ref - np.diag(cov))/np.diag(cov)
    frame_max = float(np.max(np.abs(accum.frame)))
    controls.update(stream_reference_relative_error=relative.tolist(), frame_annihilation_maxabs=frame_max)
    # Preserve computed diagnostics before any post-stream assertion failure.
    partial = dict(rows=reader.rows, v_ref=ref.tolist(), v_max=vmax.tolist(), controls=controls,
                   raw_sha256=sha.hexdigest(), source_before=before_fd, source_after=after_fd)
    with (HERE / 'STREAM_PARTIAL.json').open('x') as out:
        json.dump(partial, out, indent=2, allow_nan=False)
    require(np.all(relative <= 1e-10), 'Actual stream reference relative tolerance')
    require(frame_max <= 1e-10, 'Frame annihilation tolerance')
    require(np.all(np.isfinite(vmax)) and np.all(ref >= 0) and np.all(vmax >= (1-1e-10)*ref) and
            np.all(vmax <= (1+1e-10)*reader.rows*ref), 'Envelope checks')
    labels = old['all']['frame_projected']['coefficient_order']
    result = dict(schema='htt.gaia_working_covariance_envelope/1', owner='obsstat',
        scope='13 fixed frame-quotient coordinates, arbitrary PSD cross-source completions with fixed working 2x2 marginals',
        status='CONDITIONAL_DIAGNOSTIC_COMPUTED_PENDING_INDEPENDENT_REVIEW', claim_tier='C0',
        claim_status='DIAGNOSTIC_ONLY', artifact_mode='CONDITIONAL_RELAXED_COORDINATEWISE_ENVELOPE',
        allowed_use='Floating-point evaluation of analytic coordinatewise working-marginal envelope only',
        transfer_source='none', sky_support_status='Released CRF3 membership and ICRS/J2016.0 directions fixed',
        null_mock_status='NOT_AVAILABLE', covariance_status='Fixed published working marginals; arbitrary relaxed PSD cross-source completion',
        forbidden_uses=['Joint covariance/Loewner bound', 'Coverage or confidence interval', 'Physical error/cosmic curl/vorticity',
                        'Bianchi family identification', 'K03 or original-node admission'],
        caveats=['Maxima need not be jointly attainable', 'Actual source/frame constraint compatibility UNKNOWN',
                 'Selected-source marginal correctness and completeness of systematics unestablished', 'Bias unbounded/unmeasured',
                 'No directed-rounding numerical certificate'],
        source_commit='61fb65008c3a7f269690219e25cde6f8883976e3',
        contract_sha256=CONTRACT_SHA, code_sha256=digest(__file__), test_sha256=digest(HERE / 'test_envelope.py'),
        inputs=EXPECTED, source=dict(path=str(RAW), sha256=sha.hexdigest(), before=before_fd, after=after_fd,
            bytes=before_fd['size'], rows=reader.rows, query_status=reader.status, required_rejected_rows=0,
            optional_null_counts=reader.optional_null.tolist(), optional_unmasked_nonfinite_counts=reader.optional_nonfinite.tolist(),
            member_set_and_uniqueness='Reused identical-byte D05 evidence; not rerun'),
        runtime=dict(requested_model='gpt-6.1-sol', requested_effort='high', observed_model='UNKNOWN', observed_effort='UNKNOWN',
                     python=platform.python_version(), numpy=np.__version__, numerical_threads_cap=2, batch_rows_cap=25000),
        controls=controls, units='microas^2/yr^2', B1_physical='UNKNOWN',
        results=[dict(coordinate=label, v_ref=float(ref[k]), v_max=float(vmax[k]),
                      sigma_ref=float(np.sqrt(ref[k])), sigma_envelope=float(np.sqrt(vmax[k])),
                      variance_ratio=float(vmax[k]/ref[k])) for k, label in enumerate(labels)],
        original_status='17/42; all six NOT_READY_TO_SUBMIT; K03 HOLD unchanged')
    with (HERE / 'RESULTS.json').open('x') as out:
        json.dump(result, out, indent=2, allow_nan=False)
        out.write('\n')
    print(json.dumps({'status': result['status'], 'max_reference_relative': float(relative.max()),
                      'frame_max': frame_max, 'raw_sha256': sha.hexdigest()}), flush=True)


if __name__ == '__main__':
    require(sys.argv[1:] == ['actual'], 'Use actual under bounded_run.py')
    actual()
