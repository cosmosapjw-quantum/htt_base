"""One create-only finite 100 GHz amplitude-beam experiment; no map processing."""
from __future__ import annotations

import os
for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"
import copy
from decimal import Decimal
from fractions import Fraction
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tarfile
import time
import traceback
import unittest

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parents[2]
ROOT = Path("/mnt/extdrive/workdir/htt_open_data/planck/PR3")
CACHE = PROGRAM / "CONTINUATION_20261018/L01_EXECUTION_20261018/results"
SOURCE = HERE.parent / "D04_HFI_BEAM_SOURCE"
PRIOR_BYTES, PRIOR_SECONDS = 206907570, 3.929713791
CAP = 512 * 1024**2
TOL = 1e-10
EXPECTED_HEAD = "008d5bdd8c79d7e61293dc85e8bcbc7b4356848c"
BEAM_SHA = "187755434816addc045f13a4efd8515bb86b83531adc0eb7586412d9cfca4994"
WEIGHTS_SHA = "044ec9bed746ae745ad35a8b6ccf6e603f546083fec328e9c64d866ac9221f93"
MEMBER_SHA = "541378f6c9ab37574aae909519b0f1fe020714a6cea2b8dd1c7fcedb5ffd87df"
JSON_SHA = "bbb250b0288df040cc9273ef8483b91ae8253d5b720f3f22ee817cd846a36205"
NPZ_SHA = "7a462ba827ebe3ef5768552565f323ad2e1a679425be5d077fe8f46b9f0fdec6"
INDEX_SHA = "9f1ade812b50a466efba3750b3b64f1b4bd2be59d7762f2355cc37fd51e24606"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024**2), b""):
            h.update(b)
    return h.hexdigest()


def identity(path, expected):
    digest = sha(path)
    if digest != expected:
        raise ValueError(f"IMMUTABLE_INPUT_IDENTITY: {path}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}


class Meter:
    def __init__(self):
        self.layers = {}
        self.reserved = 0

    @property
    def count(self):
        return sum(self.layers.values())

    def wrap(self, stream, label):
        meter = self
        class Reader:
            def read(self, size=-1):
                if size < 0 or meter.count + meter.reserved + size > CAP:
                    raise RuntimeError("NEW_SHARED_DECODE_CAP")
                meter.reserved += size
                try:
                    b = stream.read(size)
                    meter.layers[label] = meter.layers.get(label, 0) + len(b)
                    return b
                finally:
                    meter.reserved -= size
        return Reader()


def drain(reader):
    while reader.read(65536):
        pass


def read_beams(path, index, meter):
    from astropy.io.fits import Header
    wanted = {index["members"][i-1]["effective_name"]: index["members"][i-1] for i in (14, 22)}
    result = {}
    with path.open("rb") as raw:
        outer_gz = gzip.GzipFile(fileobj=raw)
        outer = meter.wrap(outer_gz, "beam_outer_gzip")
        inner_gz = gzip.GzipFile(fileobj=outer)
        inner = meter.wrap(inner_gz, "beam_inner_gzip")
        with tarfile.open(fileobj=inner, mode="r|") as archive:
            for item in archive:
                if item.name not in wanted:
                    continue
                rec = wanted[item.name]
                if not item.isfile() or item.size != rec["effective_size"]:
                    raise ValueError("FITS_MEMBER_SCHEMA")
                with archive.extractfile(item) as member:
                    raw_headers = member.read(5760)
                    if len(raw_headers) != 5760:
                        raise ValueError("FITS_HEADER_SPAN")
                    hs = [Header.fromstring(raw_headers[i:i+2880].decode("ascii"), sep="")
                          for i in (0, 2880)]
                    for j in (0, 1):
                        cards = [raw_headers[i:i+80].decode("ascii")
                                 for i in range(j*2880, (j+1)*2880, 80)
                                 if raw_headers[i:i+80].strip()]
                        if cards != rec["fits_headers"][j]["cards"]:
                            raise ValueError("FROZEN_FITS_HEADER_DRIFT")
                    split = "100hm1" if rec["ordinal"] == 14 else "100hm2"
                    validate_schema(hs[0], hs[1], split)
                    data = member.read(45*9)
                    if len(data) != 405:
                        raise ValueError("NINE_ROWS_REQUIRED")
                    tokens = [[data[row*45+col*15:row*45+(col+1)*15].decode("ascii")
                               for col in range(3)] for row in range(9)]
                    for row in tokens:
                        for token in row:
                            decimal_fraction(token)
                    result[split] = {"member": item.name, "ordinal": rec["ordinal"],
                                     "rows_0_to_8_T_E_B_literal": tokens}
        # Consume all remaining padding and both trailers; decoded skips count.
        drain(inner)
        drain(outer)
    if set(result) != {"100hm1", "100hm2"}:
        raise ValueError("EXACT_TWO_BEAM_MEMBERS_REQUIRED")
    return result


def validate_schema(primary, table, split):
    expected = {"XTENSION": "TABLE", "NAXIS1": 45, "NAXIS2": 4001,
                "TFIELDS": 3, "MAX-LPOL": 4000, "PCOUNT": 0, "GCOUNT": 1}
    if primary.get("DET1") != split or primary.get("DET2") != split:
        raise ValueError("DETECTOR_SCHEMA")
    if any(table.get(k) != v for k, v in expected.items()):
        raise ValueError("ASCII_TABLE_SCHEMA")
    for col, field in enumerate(("T", "E", "B"), 1):
        if (table.get(f"TTYPE{col}") != field or table.get(f"TFORM{col}") != "E15.7"
                or table.get(f"TBCOL{col}") != 1+15*(col-1)):
            raise ValueError("TEB_FIELD_ORDER_SCHEMA")


def decimal_fraction(token):
    d = Decimal(token.strip())
    if not d.is_finite():
        raise ValueError("NONFINITE_DECIMAL")
    return Fraction(d)


def printed_unit(token):
    d = Decimal(token.strip())
    if not d.is_finite():
        raise ValueError("NONFINITE_DECIMAL")
    return Fraction(10)**d.as_tuple().exponent


def contrast(field, weight, first, second):
    if field not in ("E", "B"):
        raise ValueError("POLARIZATION_FIELD_REQUIRED")
    return decimal_fraction(weight)*(decimal_fraction(first)-decimal_fraction(second))/2


def weights(path, meter):
    retained = {}
    with path.open("rb") as raw:
        gz = gzip.GzipFile(fileobj=raw)
        decoded = meter.wrap(gz, "weights_gzip")
        with tarfile.open(fileobj=decoded, mode="r|") as archive:
            for member in archive:
                if member.name in ("README", "smica_coadd.py", "weights_EB_smica_R3.00.txt"):
                    if not member.isfile() or member.size > 2*1024**2:
                        raise ValueError("WEIGHTS_MEMBER_SCHEMA")
                    retained[member.name] = archive.extractfile(member).read(member.size)
        drain(decoded)
    payload = retained["weights_EB_smica_R3.00.txt"]
    if hashlib.sha256(payload).hexdigest() != MEMBER_SHA:
        raise ValueError("WEIGHTS_MEMBER_IDENTITY")
    rows = [line.split() for line in payload.decode("ascii").splitlines() if line.strip()]
    if len(rows) != 14 or any(len(row) != 4001 for row in rows):
        raise ValueError("POLARIZATION_WEIGHTS_SHAPE")
    # Frozen upstream reshape: (E/B, seven frequencies, ell); 100 GHz index 3.
    source = retained["smica_coadd.py"].decode("ascii")
    readme = retained["README"].decode("ascii")
    if "weights include a beam correction" not in readme:
        raise ValueError("FROZEN_WEIGHT_BEAM_CONVENTION")
    return {"E": rows[3][:9], "B": rows[10][:9]}, {
        "member_sha256": MEMBER_SHA, "source_code_sha256": hashlib.sha256(retained["smica_coadd.py"]).hexdigest(),
        "source_lines": [line for line in source.splitlines() if "reshape" in line or "freq" in line.lower()],
        "shape": [2, 7, 4001], "frequencies_GHz": [30,44,70,100,143,217,353],
        "selected_channel_index": 3, "selected_text_rows": [3,10], "renormalized": False}


def layout(lo, hi):
    return [(ell, field, phase) for ell in range(lo, hi+1) for field in ("E", "B")
            for phase in ["m0"] + [s for m in range(1,ell+1) for s in (f"cos{m}", f"sin{m}")]]


def validate_cache(meta, K):
    import numpy as np
    if (meta.get("schema") != "htt.L01_original_selected_support_finite_response/1"
        or meta["selected_support"]["nside"] != 64
        or meta["selected_support"]["order"] != "RING"
        or meta["selected_support"]["selected_pixels"] != 30021
        or meta["high_response"]["operator_shape"] != [64,90]
        or meta["high_response"]["harmonic_range_low"] != [2,5]
        or meta["high_response"]["harmonic_range_high"] != [6,8]
        or meta["high_response"]["source_basis"] != "real E/B m0 cos/sin per ell, HEALPix Galactic polar frame"
        or K.shape != (64,90) or K.dtype != np.dtype("float64") or not np.isfinite(K).all()):
        raise ValueError("CACHE_SCHEMA_ORDER_OR_FINITE")


def exact_certificate(C, d):
    """Exact binary64 C times exact decimal d; integer ceil sqrt bound."""
    total = sum((sum(Fraction.from_float(float(x))**2 for x in C[:,j])*v*v
                 for j,v in enumerate(d)), Fraction(0))
    scaled = total*10**60
    n = (scaled.numerator+scaled.denominator-1)//scaled.denominator
    m = math.isqrt(n)
    m += m*m < n
    assert Fraction(m*m,10**60) >= total
    return {"S_numerator": str(total.numerator), "S_denominator": str(total.denominator),
            "n_ceil_1e60S": str(n), "m_ceil_sqrt_n": str(m),
            "U_exact_decimal": f"{m//10**30}.{m%10**30:030d}",
            "U_rational": f"{m}/1000000000000000000000000000000"}


def spectral(A, certificate):
    import numpy as np
    scale = float(np.max(np.abs(A))) if A.size else 0.
    if scale == 0:
        return {"spectral_norm": 0., "left_residual": 0., "right_residual": 0., "zero": True}
    M = A/scale
    u,s,vh = np.linalg.svd(M, full_matrices=False)
    left = float(np.linalg.norm(M@vh.T-u*s, ord="fro")/np.linalg.norm(M, ord="fro"))
    right = float(np.linalg.norm(M.T@u-vh.T*s, ord="fro")/np.linalg.norm(M, ord="fro"))
    norm = float(s[0]*scale)
    if max(left,right) > TOL or norm > float(certificate["U_exact_decimal"])*(1+TOL):
        raise ValueError("NORMALIZED_SVD_OR_CERTIFICATE_CONTROL")
    return {"spectral_norm": norm, "left_residual": left, "right_residual": right,
            "zero": False, "normalization_max_abs": scale}


class Controls(unittest.TestCase):
    def test_exact_contrast_controls(self):
        d = contrast("E", "3", "1.5", "1.0")
        self.assertEqual(d, Fraction(3,4))
        self.assertEqual(contrast("E", "3", "1.0", "1.5"), -d)
        self.assertEqual(contrast("B", "0", "1.5", "1.0"), 0)
        self.assertEqual(contrast("B", "3", "1.5", "1.5"), 0)

    def test_wrong_field_and_nonfinite(self):
        for field,w,a,b in (("T","1","1","0"),("E","NaN","1","0"),("B","1","Infinity","0")):
            with self.assertRaises(ValueError): contrast(field,w,a,b)

    def test_schema_and_field_order_rejection(self):
        table = {"XTENSION":"TABLE","NAXIS1":45,"NAXIS2":4001,"TFIELDS":3,
                 "MAX-LPOL":4000,"PCOUNT":0,"GCOUNT":1}
        for j,k in enumerate(("T","E","B"),1):
            table.update({f"TTYPE{j}":k,f"TFORM{j}":"E15.7",f"TBCOL{j}":1+15*(j-1)})
        p = {"DET1":"100hm1","DET2":"100hm1"}
        validate_schema(p,table,"100hm1")
        for key,value in (("TTYPE2","B"),("NAXIS2",4000),("TFORM1","D15.7")):
            with self.assertRaises(ValueError): validate_schema(p,table|{key:value},"100hm1")

    def test_exact_sqrt_and_normalized_nonzero_svd(self):
        import numpy as np
        C = np.array([[1., 0.5],[-0.25,1.]])
        d = [Fraction(1,10**25),Fraction(-2,10**25)]
        cert = exact_certificate(C,d)
        spectral(C*np.array([float(v) for v in d]),cert)
        self.assertGreater(Fraction(cert["U_rational"]),0)
        self.assertEqual(exact_certificate(C,[Fraction(0),Fraction(0)])["U_exact_decimal"],"0.000000000000000000000000000000")


def write_json(path, obj):
    with path.open("x") as f:
        json.dump(obj,f,indent=2,allow_nan=False); f.write("\n")


def run(meter, started):
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    paths = [HERE/name for name in ("RESULT.json","SOURCE_TOKENS.tsv","CONTRAST.png","CONTRAST.pdf","CONTROLS.txt","REPORT.md")]
    if any(p.exists() for p in paths):
        raise FileExistsError("CREATE_ONLY_NO_REPLAY")
    head = subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    if head != EXPECTED_HEAD: raise ValueError("FROZEN_HEAD_DRIFT")
    inputs = [identity(ROOT/"beams/HFI_RIMO_BEAMS_R3.01.tar.gz",BEAM_SHA),
              identity(ROOT/"weights/COM_Code_SMICA-weights-propagation_R3.00.tar.gz",WEIGHTS_SHA),
              identity(CACHE/"ORIGINAL_SELECTED_SUPPORT_RESPONSE.json",JSON_SHA),
              identity(CACHE/"ORIGINAL_SELECTED_SUPPORT_RESPONSE.npz",NPZ_SHA),
              identity(SOURCE/"SOURCE_INDEX_DOUBLE_GZIP.json",INDEX_SHA)]
    meta = json.loads((CACHE/"ORIGINAL_SELECTED_SUPPORT_RESPONSE.json").read_text())
    with np.load(CACHE/"ORIGINAL_SELECTED_SUPPORT_RESPONSE.npz",allow_pickle=False) as z:
        K = z["high6_8_to_low2_5"].copy()
    validate_cache(meta,K)
    with (HERE/"CONTROLS.txt").open("x") as log:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
        tested = unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tested.wasSuccessful(): raise RuntimeError("TARGETED_CONTROLS_FAILED")
    index = json.loads((SOURCE/"SOURCE_INDEX_DOUBLE_GZIP.json").read_text())
    beams = read_beams(Path(inputs[0]["path"]),index,meter)
    w, weight_binding = weights(Path(inputs[1]["path"]),meter)
    low, high = layout(2,5), layout(6,8)
    coefficients = low+high
    rows, d_by_key = [], {}
    for ell in range(9):
        for field,col in (("E",1),("B",2)):
            b1,b2 = [beams[s]["rows_0_to_8_T_E_B_literal"][ell][col] for s in ("100hm1","100hm2")]
            diff = decimal_fraction(b1)-decimal_fraction(b2)
            d = contrast(field,w[field][ell],b1,b2)
            units = printed_unit(b1)+printed_unit(b2)
            flag = "SERIALIZATION_RESOLUTION_LIMITED" if abs(diff)<=units else "RESOLVED_PRINTED_CONTRAST"
            row = {"ell":ell,"field":field,"beam_hm1_literal":b1,"beam_hm2_literal":b2,
                   "weight_100_literal":w[field][ell],"beam_difference_exact":str(diff),
                   "beam_last_printed_units_sum_exact":str(units),"d_exact":str(d),
                   "d_float":float(d),"serialization_status":flag,"used_in_operator":ell>=2}
            rows.append(row)
            d_by_key[ell,field] = d
    d = [d_by_key[ell,field] for ell,field,_ in coefficients]
    C = np.column_stack((np.eye(64),K))
    A = C*np.array([float(v) for v in d])
    b_low = [j for j,(_,f,_) in enumerate(low) if f=="B"]
    e_high = [64+j for j,(_,f,_) in enumerate(high) if f=="E"]
    cert = exact_certificate(C,d)
    leak_cert = exact_certificate(C[np.ix_(b_low,e_high)],[d[j] for j in e_high])
    numeric = spectral(A,cert)
    leakage = spectral(A[np.ix_(b_low,e_high)],leak_cert)
    # Actual-matrix controls, including nonzero synthetic controls above if A=0.
    zero = np.zeros_like(A)
    swapped = C*np.array([float(-v) for v in d])
    assert np.array_equal(swapped,-A)
    assert np.array_equal(C*np.zeros(154),zero)
    for changed in ("order", "field"):
        bad = copy.deepcopy(meta)
        if changed=="order": bad["selected_support"]["order"]="NESTED"
        else: bad["high_response"]["source_basis"]="B/E reversed"
        try: validate_cache(bad,K)
        except ValueError: pass
        else: raise AssertionError("WRONG_CACHE_ORDER_ACCEPTED")
    badK = K.copy(); badK[0,0]=np.nan
    try: validate_cache(meta,badK)
    except ValueError: pass
    else: raise AssertionError("NONFINITE_CACHE_ACCEPTED")
    with (HERE/"SOURCE_TOKENS.tsv").open("x") as f:
        f.write("split\tell\tT_literal\tE_literal\tB_literal\tweight_E100_literal\tweight_B100_literal\n")
        for split in ("100hm1","100hm2"):
            for ell,tokens in enumerate(beams[split]["rows_0_to_8_T_E_B_literal"]):
                f.write("\t".join([split,str(ell),*tokens,w["E"][ell],w["B"][ell]])+"\n")
    fig,ax=plt.subplots(figsize=(7.6,4.5))
    for field,marker in (("E","o"),("B","s")):
        ax.plot(range(2,9),[float(d_by_key[ell,field]) for ell in range(2,9)],marker=marker,label=field)
    ax.axhline(0,color="black",lw=.7); ax.set_xticks(range(2,9))
    ax.set(xlabel=r"Multipole $\ell$",ylabel=r"Signed $d_\ell^X=\frac{1}{2} w_{100,\ell}^X(B_{hm1,\ell}^X-B_{hm2,\ell}^X)$",
           title="Fixed 100 GHz HM amplitude-beam contrast | DIAGNOSTIC / C0")
    if not np.any(A): ax.set_ylim(-1e-12,1e-12); ax.text(.5,.76,"All released E/B beam differences are exactly zero\nin rows 2–8 (published decimal tokens)",transform=ax.transAxes,ha="center")
    ax.legend(); ax.grid(alpha=.2)
    fig.text(.5,.015,"obsstat · fixed weights · cached COARSE support · no physical sky amplitude / uncertainty bound",ha="center",fontsize=8)
    fig.tight_layout(rect=(0,.045,1,1))
    fig.savefig(HERE/"CONTRAST.png",dpi=160); fig.savefig(HERE/"CONTRAST.pdf"); plt.close(fig)
    result = {"schema":"htt.fixed_100GHz_HM_amplitude_beam_coarse/1","owner":"obsstat",
        "scope":"Conditional single-channel common-sky coefficient contribution before final pixel window",
        "status":"DIAGNOSTIC_ONLY","claim_tier":"C0","non_claim_bearing":True,
        "transfer_source":"none","instrument_response_source":"Planck PR3 HFI RIMO R3.01 amplitude B(l); fixed SMICA R3.00 weights",
        "source_identities":inputs,"contract_sha256":sha(HERE/"CONTRACT.md"),"code_sha256":sha(Path(__file__)),
        "observed_head":head,"requested_runtime":"gpt-6.1-sol/high","observed_runtime":"UNKNOWN",
        "execution":{"interpreter":sys.executable,"python":sys.version,"numpy":np.__version__,"matplotlib":matplotlib.__version__,"command":sys.argv},
        "beams":beams,"weights":weight_binding,"source_rows":rows,
        "ordering":{"low":low,"high":high,"basis":meta["high_response"]["source_basis"]},
        "operator":{"formula":"A=[I64 K64x90] diag(d154)","shape":[64,154],"coarse_support":meta["selected_support"],"native_child_response":False},
        "norm":numeric,"high_E_to_low_B":leakage,
        "exact_frobenius_upper_bound":cert,"exact_high_E_to_low_B_upper_bound":leak_cert,
        "certificate_interpretation":"For exact published decimal tokens and cached binary64 K, ||Az||2 <= U||z||2; no physical sky norm or beam uncertainty supplied",
        "controls":{"unittest_count":tested.testsRun,"unittest_success":True,"actual_matrix_swap_zero_cache_order_and_nonfinite":"PASS","relative_tolerance":TOL},
        "plot":{"category":"DIAGNOSTIC","claim_tier":"C0","units":"dimensionless amplitude coefficient gain","normalization":"literal published amplitudes and weights; no renormalization","seed":None,"frame":"HEALPix Galactic polar frame, RING64","allowed_use":"Fixed single-channel conditional coarse gain","forbidden_use":"physical absolute microkelvin contamination; native/exact processed response; family identification","null_status":"NOT_CALIBRATED","covariance_status":"NOT_APPLICABLE_DETERMINISTIC_PUBLISHED_MODEL"},
        "hold":["other channels/LFI UNKNOWN","native-child/exact SMICA processed response","spatial/offdiagonal beams","pixel window","omitted multipoles","physical beam uncertainties/correlations","foregrounds","weight selection","joint signal/noise law","D04/L03/original DAG admission"],
        "resources":{"prior_archive_decoded_bytes":PRIOR_BYTES,"prior_archive_seconds":PRIOR_SECONDS,"new_decoded_layers":meter.layers,"new_decoded_bytes":meter.count,"cumulative_archive_decoded_bytes":PRIOR_BYTES+meter.count,"new_execution_seconds":time.monotonic()-started,"conservative_cumulative_archive_seconds":PRIOR_SECONDS+time.monotonic()-started,"max_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"process_threads":int(next(x.split()[1] for x in Path('/proc/self/status').read_text().splitlines() if x.startswith('Threads:'))),"hard_caps":{"new_seconds":60,"new_decoded_bytes":CAP,"memory_bytes":CAP,"threads":2,"original_archive_bytes":1024**3,"original_archive_seconds":120}}}
    if result["resources"]["process_threads"]>2: raise RuntimeError("THREAD_CAP")
    report = f"""# Fixed 100 GHz HM amplitude-beam numerical result

obsstat; C0; DIAGNOSTIC_ONLY; independent review pending. Requested gpt-6.1-sol/high; observed UNKNOWN. Observed HEAD {head}.

Actual released decimal rows 2–8 give ||A||2={numeric['spectral_norm']:.17g}; high-E→low-B norm={leakage['spectral_norm']:.17g}. Exact rational Frobenius upper bounds are U={cert['U_exact_decimal']} and U_E→B={leak_cert['U_exact_decimal']}. These bound coefficient gain per unit input norm only. Other channels remain UNKNOWN; the physical common response remains HOLD.

The calculation uses amplitude B directly, the fixed published 100 GHz weights, a half split contrast, and C=[I64 K64x90] from the existing 30,021-pixel RING64 cache. It does not apply a second beam to maps/noise or replay a projector/design/injection. Per ell ordering is E then B, each m0/cos/sin; cache metadata and existing basis source were checked before execution. SOURCE_TOKENS.tsv retains literal T/E/B rows 0–8 and selected weights. Rows 0–1 are reported without normalization tests. RESULT.json retains exact differences, last printed decimal units and serialization flags; those flags are not physical rounding or uncertainty intervals.

The integer certificate treats published decimal tokens and cached binary64 K as exact numbers. It sums rational squares S, sets n=ceil(10^60 S), m=ceil_sqrt(n), and U=m 10^-30. Thus U >= ||A||F >= ||A||2. The leakage submatrix is certified separately. Normalized SVD residuals and the independent Frobenius bounds use the frozen 1e-10 controls; exact zero is valid. Four targeted unittest cases plus actual-matrix swap/zero/cache-order/nonfinite controls ran in this same bounded execution; raw outcomes are CONTROLS.txt. No scientific tolerance was changed.

CONTRAST.png/PDF are one signed E/B diagnostic, generated by run_numeric.py from these actual source rows. Units are dimensionless amplitude gain, without weight or beam renormalization; Galactic polar basis, no random seed. Owner obsstat, C0, transfer_source=none (instrumental beam response separately identified), null NOT_CALIBRATED, covariance NOT_APPLICABLE_DETERMINISTIC_PUBLISHED_MODEL. Allowed use is conditional coarse gain. Physical absolute microkelvin contamination, native/exact processed response and family identification are forbidden uses. The displayed zero-scale, if needed, is explicit and carries no uncertainty meaning.

Physical amplitude envelopes, beam uncertainties/correlations, other channels/LFI, spatial/offdiagonal response, final pixel window, omitted multipoles, foregrounds, weight selection and the joint signal/noise law remain missing. D04/L03/original DAG and publication/admission states are unchanged. No network, map/noise replay, native solver, ODE, commit or push was used.

Resource counters and input/code/contract identities are in RESULT.json and EXECUTION_RECEIPT.json. The historical intake remains charged at {PRIOR_BYTES} decoded bytes / {PRIOR_SECONDS} s. Both beam gzip layers, all skipped payloads, weights decompression and CRC-to-EOF bytes count in the new shared meter; unchanged historical receipts are preserved.
"""
    with (HERE/"REPORT.md").open("x") as f: f.write(report)
    write_json(HERE/"RESULT.json",result)
    print(json.dumps({"status":"EXECUTED_PENDING_REVIEW","norm":numeric,"leakage":leakage,"resources":result["resources"]}),flush=True)


def main():
    started=time.monotonic(); meter=Meter()
    if (HERE/"EXECUTION_RECEIPT.json").exists(): raise FileExistsError("NO_REPLAY")
    resource.setrlimit(resource.RLIMIT_AS,(CAP,CAP))
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError("60_SECOND_CUMULATIVE_NEW_EXECUTION_CAP")))
    signal.setitimer(signal.ITIMER_REAL,60)
    status="FAILED"; error=None
    try:
        run(meter,started); status="EXECUTED_PENDING_REVIEW"
    except BaseException as exc:
        error={"type":type(exc).__name__,"message":str(exc)}
        with (HERE/"FIRST_FAILURE.txt").open("x") as f: traceback.print_exc(file=f)
        traceback.print_exc()
    finally:
        elapsed=time.monotonic()-started
        write_json(HERE/"EXECUTION_RECEIPT.json",{"status":status,"error":error,"elapsed_seconds":elapsed,"new_decoded_layers":meter.layers,"new_decoded_bytes":meter.count,"prior_archive_bytes":PRIOR_BYTES,"cumulative_archive_bytes":PRIOR_BYTES+meter.count,"prior_archive_seconds":PRIOR_SECONDS,"conservative_cumulative_archive_seconds":PRIOR_SECONDS+elapsed,"max_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"interpreter":sys.executable,"requested_runtime":"gpt-6.1-sol/high","observed_runtime":"UNKNOWN"})
        signal.setitimer(signal.ITIMER_REAL,0)
    return 0 if status=="EXECUTED_PENDING_REVIEW" else 2


if __name__=="__main__": raise SystemExit(main())
