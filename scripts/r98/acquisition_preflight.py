"""R98 public-input discovery, existing-file verification and bounded resumable intake.

Metadata only by default. Reuses the R90 exact three-file Quaia allowlist.
No absent upstream covariance is replaced by public catalog repetitions.
Original /mnt/extdrive data are immutable; new files live in local Downloads.
"""
from __future__ import annotations
import argparse, fcntl, hashlib, json, os, re, shutil, time
from email.message import Message
import numpy as np
from astropy.io import fits
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse
from html.parser import HTMLParser
from scripts.r90.download_minimal import ALLOWLIST, RECORD, DEST as OLD_DEST, file_md5
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123"
DEST=Path("/home/cosmosapjw/Downloads/htt_r98_acquisition")
INDEXES={
 "CF4_VIZIER_CATALOG":"https://vizier.cfa.harvard.edu/viz-bin/VizieR?-source=J%2FApJ%2F944%2F94",
 "QUAIA_RELEASE":"https://zenodo.org/api/records/10403370",
 "LOTSS_DR3":"https://lofar-surveys.org/dr3.html",
 "PLANCK_PR3_MAP_MATRIX":"https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html",
 "PLANCK_PR3_ANCILLARY":"https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/",
 "GAIA_CR_F3":"https://gea.esac.esa.int/archive/documentation/GEDR3/Gaia_archive/chap_datamodel/sec_dm_auxiliary_tables/ssec_dm_agn_cross_id.html",
}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(2**20),b""):h.update(b)
 return h.hexdigest()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=="a":
   href=dict(attrs).get("href")
   if href:self.links.append(href)
def fetch_index(key,url,cap=8*2**20):
 req=Request(url,headers={"User-Agent":"htt-r98-scientific-intake/1"})
 with urlopen(req,timeout=25) as response:
  payload=response.read(cap+1)
  if len(payload)>cap:raise ValueError("metadata exceeds bounded request")
  headers=dict(response.headers);final=response.url
  marker={"CF4_VIZIER_CATALOG":b"Cosmicflows-4","GAIA_CR_F3":b"Gaia-CRF3"}.get(key)
  if marker and marker not in payload:raise ValueError("source-specific catalogue marker missing")
 file=DEST/(key+".metadata");file.write_bytes(payload)
 links=[]
 if "html" in headers.get("Content-Type","").lower() or payload.lstrip().startswith(b"<"):
  parser=Links();parser.feed(payload.decode("utf8",errors="replace"))
  links=sorted({urljoin(final,x) for x in parser.links if not x.startswith(("mailto:","javascript:","#"))})
 return {"url":url,"final_url":final,"bytes":len(payload),"sha256":sha(file),"headers":{k:v for k,v in headers.items() if k.lower() in ("etag","last-modified","content-type","content-length")},
         "links":links,"local_path":str(file),"status":"METADATA_RETRIEVED"}

LOTSS_NAME="LoTSS_DR3_v1.0.srl.fits"
LOTSS_URL="https://lofar-surveys.org/public/DR3/catalogues/"+LOTSS_NAME
LOTSS_LOCAL=Path("/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/LoTSS_DR3")/LOTSS_NAME


def lotss_catalog_probe(page):
    if LOTSS_URL not in page.get("links",[]):
        raise ValueError("catalog URL not in observed release-page links")
    page_bytes=Path(page["local_path"]).read_bytes()
    match=re.search(rb"catalogue of ([0-9,]+) radio sources", page_bytes)
    if not match:raise ValueError("release-page source count not located")
    prose_rows=int(match.group(1).replace(b",",b""))
    with fits.open(LOTSS_LOCAL,memmap=True) as hdul:
        ext=hdul[1]
        start,end=ext.fileinfo()["hdrLoc"],ext.fileinfo()["datLoc"]
        local_rows=int(ext.header["NAXIS2"])
        extname=ext.header["EXTNAME"]
    if not 0<start<end<=131072:raise ValueError("unexpected FITS metadata span")
    req=Request(LOTSS_URL,headers={"Accept-Encoding":"identity","Range":f"bytes={start}-{end-1}"})
    with urlopen(req,timeout=20) as response:
        ranged=response.status==206
        if ranged:
            value=response.headers.get("Content-Range","")
            if not re.fullmatch(rf"bytes {start}-{end-1}/[0-9]+",value):
                raise ValueError("wrong LoTSS header range")
        elif response.status!=200:
            raise ValueError("unusable archive response")
        if not ranged:
            # The primary HDU contains a small metadata payload. Never read a catalogue row.
            before=response.read(start)
            if len(before)!=start or not before.startswith(b"SIMPLE  ="):
                raise ValueError("unexpected LoTSS primary structure")
        header=bytearray()
        for _ in range(0,end-start,2880):
            block=response.read(2880)
            if len(block)!=2880:raise ValueError("short LoTSS FITS header")
            header.extend(block)
            if any(block[i:i+8]==b"END     " for i in range(0,2880,80)):break
        else:raise ValueError("no END in bounded extension header")
    if not header.startswith(b"XTENSION="):raise ValueError("unexpected LoTSS table offset")
    h=fits.Header.fromstring(bytes(header).decode("ascii"),sep="")
    if h.get("XTENSION")!="BINTABLE" or h.get("EXTNAME")!=extname:
        raise ValueError("LoTSS source-table identity mismatch")
    with LOTSS_LOCAL.open("rb") as f:
        f.seek(start);same=f.read(len(header))==header
    return {"status":"OFFICIAL_TABLE_HEADER_READ","url":LOTSS_URL,"local_path":str(LOTSS_LOCAL),
            "http_status":206 if ranged else 200,"range_honored":ranged,
            "received_bytes":len(header)+(0 if ranged else start),"table_header_bytes":len(header),
            "catalogue_row_payload_bytes_read":0,"extension":extname,"table_header_sha256":hashlib.sha256(header).hexdigest(),
            "local_extension_header_byte_identical":same,"published_page_source_count":prose_rows,
            "local_FITS_NAXIS2":local_rows,"official_FITS_NAXIS2":h["NAXIS2"],
            "official_FITS_minus_prose":h["NAXIS2"]-prose_rows,"local_minus_official_FITS":local_rows-h["NAXIS2"],
            "cause_of_page_difference":None,"catalog_payload_byte_identity_checked":False}

def known_file_jobs():
 jobs=[]
 for name,(size,md5) in ALLOWLIST.items():
  path=OLD_DEST/name
  available=path.is_file() and path.stat().st_size==size and file_md5(path)==md5
  jobs.append({"id":name,"url":RECORD+name+"/content","bytes":size,"md5":md5,
               "existing_path":str(path),"status":"ALREADY_IDENTICAL" if available else "READY_TO_DOWNLOAD",
               "purpose":"relative-selection/scan templates only; not absolute inclusion probability"})
 return jobs

PLA = "https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID="
COMMANDER_SIZE = 603987840
COMMANDER_IDS = tuple(f"dx12_v3_commander_{part}_mc_00000_raw.fits" for part in ("cmb", "noise"))
COMMANDER_RAW = Path("/mnt/extdrive/workdir/raw/planck_ffp10/commander")
PREFIX_BYTES = 5760
PRIOR_FAILURES = [
 {"url":"https://www.cosmos.esa.int/web/gaia/edr3-celestial-reference-frame","observation":"earlier R98 preflight returned HTTP 404"},
 {"url":"https://cdsarc.cds.unistra.fr/ftp/J/ApJ/944/94/ReadMe","observation":"earlier R98 preflight timed out"},
 {"url":"https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/944/94?format=html&tex=true","observation":"bounded eight-second owner-host request timed out"},
 {"url":PLA+"dx12_v3_commander_noise_hm1_mc_00000_raw.fits","observation":"bounded five-second HEAD timed out; full-mission success does not validate HM1"}]


def archive_job(name):
    if name in ALLOWLIST:
        size, md5 = ALLOWLIST[name]
        return {"id":name,"url":RECORD+name+"/content","bytes":size,"md5":md5}
    if name not in COMMANDER_IDS:
        raise ValueError("unknown file ID")
    return {"id":name,"url":PLA+name,"bytes":COMMANDER_SIZE}


def check_commander_head(h):
    expected = {"XTENSION":"BINTABLE","NSIDE":2048,"ORDERING":"RING","TFIELDS":3,
                "NAXIS1":12288,"NAXIS2":49152}
    for i, col in enumerate(("INTENSITY","Q-POLARISATION","U-POLARISATION"),1):
        expected.update({f"TTYPE{i}":col, f"TFORM{i}":"1024E", f"TUNIT{i}":"K_CMB"})
    if any(h.get(k)!=v for k,v in expected.items()):
        raise ValueError("unexpected Commander T/Q/U FITS layout or units")


def archive_filename(headers):
    msg = Message()
    msg["Content-Disposition"] = headers.get("Content-Disposition","")
    return msg.get_filename()


def commander_probe(name):
    job = archive_job(name)
    req = Request(job["url"], headers={"Range":"bytes=0-5759","Accept-Encoding":"identity"})
    with urlopen(req, timeout=18) as response:
        if response.status not in (200,206) or archive_filename(response.headers)!=name:
            raise ValueError("wrong Commander product response")
        if response.status==206 and response.headers.get("Content-Range")!=f"bytes 0-5759/{COMMANDER_SIZE}":
            raise ValueError("wrong probe range")
        prefix = response.read(PREFIX_BYTES)
        if len(prefix)!=PREFIX_BYTES or not prefix.startswith(b"SIMPLE  =") or not prefix[2880:].startswith(b"XTENSION="):
            raise ValueError("short or non-FITS product header")
        ext = fits.Header.fromstring(prefix[2880:].decode("ascii"), sep="")
        check_commander_head(ext)
        result = {**job,"status":"HEADER_VERIFIED_ONLY","http_status":response.status,
                  "content_type":response.headers.get("Content-Type"),"returned_filename":name,
                  "range_honored":response.status==206,"header_bytes":len(prefix),
                  "header_sha256":hashlib.sha256(prefix).hexdigest(),
                  "nside":ext["NSIDE"],"ordering":ext["ORDERING"],
                  "fields":[ext[f"TTYPE{i}"] for i in (1,2,3)],"units":[ext[f"TUNIT{i}"] for i in (1,2,3)],
                  "full_payload_sha256":None,"commander_null_qualified":False}
    part = "cmb" if name == COMMANDER_IDS[0] else "noise"
    local = COMMANDER_RAW / f"{part}_mc" / name
    result["canonical_local_path"] = str(local)
    result["canonical_local_exists"] = local.is_file()
    if local.is_file():
        with local.open("rb") as f:
            result["local_header_matches_remote"] = f.read(PREFIX_BYTES)==prefix
    return result


def validate_payload(path, job, expected_sha=None):
    if path.stat().st_size != job["bytes"]:
        raise ValueError("file length mismatch")
    digest = sha(path)
    result = {"bytes":job["bytes"],"sha256":digest}
    if expected_sha and digest!=expected_sha:
        raise ValueError("SHA-256 mismatch")
    if job["id"] in ALLOWLIST:
        if file_md5(path)!=job["md5"]:
            raise ValueError("publisher MD5 mismatch")
        return {**result,"md5":job["md5"]}
    with fits.open(path,memmap=True) as h:
        h.verify("exception")
        if len(h)!=2 or not h[0].header.get("SIMPLE"):
            raise ValueError("unexpected Commander HDUs")
        check_commander_head(h[1].header)
        info=h[1].fileinfo()
        if info["datLoc"]+info["datSpan"]!=path.stat().st_size:
            raise ValueError("FITS logical length mismatch")
        channel_stats={}
        for col in h[1].columns.names:
            values=h[1].data[col]
            finite=0
            for start in range(0,len(values),512):
                finite+=int(np.isfinite(values[start:start+512]).sum())
            if not finite:
                raise ValueError("channel contains no finite samples")
            channel_stats[col]={"pixels":int(values.size),"finite":finite}
    return {**result,"channels":channel_stats,"external_expected_sha256_supplied":bool(expected_sha),
            "commander_null_qualified":False}


def download(job, budget, expected_sha=None):
    # Derive the URL and expected length/digest exclusively from the registered ID.
    job=archive_job(job["id"])
    if expected_sha is not None and not re.fullmatch("[0-9a-f]{64}",expected_sha):
        raise ValueError("expected SHA-256 must be 64 lowercase hex digits")
    if job["bytes"]>budget:
        raise ValueError("per-command byte budget exceeded")
    DEST.mkdir(parents=True,exist_ok=True)
    target=DEST/job["id"]
    part=target.with_name(target.name+".partial")
    receipt=target.with_name(target.name+".receipt.json")
    with target.with_name(target.name+".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if target.exists():
            bound=expected_sha
            if job["id"] in COMMANDER_IDS and not bound:
                if not receipt.exists():raise ValueError("existing Commander file needs its transfer receipt or external digest")
                saved=json.loads(receipt.read_text())
                if saved["url"]!=job["url"]:raise ValueError("existing Commander receipt mismatch")
                bound=saved["sha256"]
            return {**validate_payload(target,job,bound),"status":"EXISTING_VERIFIED","path":str(target)}
        start=part.stat().st_size if part.exists() else 0
        if start>job["bytes"]:raise ValueError("oversized partial")
        if start and job["id"] in COMMANDER_IDS and not expected_sha and receipt.exists() and start==job["bytes"]:
            saved=json.loads(receipt.read_text())
            if saved["url"]==job["url"]:expected_sha=saved["sha256"]
        if start and job["id"] in COMMANDER_IDS and not expected_sha:
            raise ValueError("Commander partial needs a trusted full-object SHA-256 to establish its identity")
        if start < job["bytes"]:
            headers={"Accept-Encoding":"identity","User-Agent":"htt-r98-scientific-intake/1"}
            if start:headers["Range"]=f"bytes={start}-"
            with urlopen(Request(job["url"],headers=headers),timeout=30) as response:
                if start:
                    if response.status!=206 or response.headers.get("Content-Range")!=f"bytes {start}-{job['bytes']-1}/{job['bytes']}":
                        raise ValueError("resume not honored exactly; partial preserved")
                elif response.status!=200:
                    raise ValueError("fresh request did not return complete representation")
                if job["id"] in COMMANDER_IDS and archive_filename(response.headers)!=job["id"]:
                    raise ValueError("wrong response filename")
                with part.open("ab" if part.exists() else "xb") as f:
                    total=start
                    while True:
                        block=response.read(min(262144,job["bytes"]-total+1))
                        if not block:break
                        total+=len(block)
                        if total>job["bytes"]:raise ValueError("response exceeds expected file size")
                        f.write(block)
                    f.flush()
                    os.fsync(f.fileno())
        result=validate_payload(part,job,expected_sha)
        record={**result,"id":job["id"],"url":job["url"],"path":str(target),
                "status":"VALIDATED_COMPLETE_PARTIAL" if start==job["bytes"] else "DOWNLOADED_AND_VALIDATED"}
        tmp=receipt.with_suffix(".tmp")
        tmp.write_text(json.dumps(record,indent=2)+"\n")
        os.replace(tmp,receipt)
        os.replace(part,target)
        return record

def contracts():
 return {
 "CF4_UPSTREAM_CALIBRATION":{
  "status":"NO_PUBLIC_DOWNLOAD_LOCATED_FOR_REQUIRED_UPSTREAM_LAW",
  "catalogue":"J/ApJ/944/94 public post-intercalibration release",
  "required":["release DOI/version/checksums","pre-intercalibration distance modulus and uncertainty per method and group","group/galaxy membership keys","absolute anchor/training-set membership","signed zero-point joint posterior or covariance with stated gauge","DirectCal cross-covariance and overlap lineage","independent heldout calibration membership"],
  "method_order":["SNIa","FP","TFR","SBFm","SBFir","SNII","DirectCal"],
  "units":{"distance_modulus":"mag","calibration_covariance":"mag^2","peculiar_velocity":"km/s"},
  "reject":["post-MCMC residual-overlap covariance labeled upstream","ad hoc ridge on unidentifiable DirectCal contrast","holdout that shares global fit calibration"]
 },
 "CF4_PV_SELECTION":{
  "status":"MODEL_AND_UPSTREAM_DATA_REQUIRED",
  "required":["targeting/acceptance/rejection denominators","method-specific completeness versus sky/distance/source properties","radial peculiar-velocity covariance operator with cosmology, smoothing, nonlinear dispersion","same source ordering/frame/window as 35970 ID vector"],
  "operator_contract":"diag plus low-rank factors or LinearOperator; never allocate 35970^2 by default",
  "marginalization":"distance/log-modulus likelihood with Jacobian; retain cross-method and overlapping-window covariance"
 },
 "PLANCK_MATCHED_NULL":{
  "status":"OBSERVED_SPLITS_ALREADY_LOCAL; MATCHED_JOINT_LAW_UNQUALIFIED",
  "full_mission_ID00000_candidates":[archive_job(n) for n in COMMANDER_IDS],
  "source":"https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps",
  "header_qualification":"Two HTTP 200 identity-encoded 5760-byte FITS prefixes verified; Range ignored; no full-product rehash or Commander joint calibration",
  "required":["component/release/beam/pixel/mask identity","matched signal/noise split IDs and repeated-noise genealogy","foreground residual and fitted-weight selection law","same operator applied to observed and simulations"],
  "not_repaired_by":"more CMB draws with modulo-reused noise or substituting SMICA null for Commander"
 },
 "GAIA_SOURCE_SYSTEMATICS":{
  "status":"FULL_CRF3_AND_QUAIA_EXIST; ASTROMETRIC_SPATIAL_MODEL_REQUIRED",
  "required":["source_id joined redshift/quality/selection metadata","pmra/pmdec covariance and correlated angular scan error model","AGN population/centroid motion model","common observer/source frame and finite-z optical response"],
  "existing_joint_patch_covariance":"48 shared patches; rank<=47, diagnostic not AGIS covariance"
 },
 "RADIO_SOURCE_SELECTION":{
  "status":"FIVE_FULL_CATALOGUES_EXIST; RMS/FOOTPRINT/SED_RESPONSE_REQUIRED",
  "required":["all survey tiles and zero-source regions in footprint","noise and completeness maps with flux/size dependence","source-vs-component association","source spectral-index distribution","cross-catalogue match and LSS mocks"],
  "available_existing_catalogue":"LoTSS DR3 v1.0 local FITS NAXIS2=13667877; release-page prose 13664379. Compare official catalog header in ACQUISITION_PREFLIGHT.json; cause of 3498 difference unresolved.",
  "download_preparation":"official DR3 page links are recorded verbatim; separate mosaic RMS/source masks from raw visibilities; resolve byte sizes before bulk transfer"
 },
 "NORMAL_FLUX_AND_NATIVE":{
  "status":"MODEL_CONSTRUCTION_REQUIRED; NO_SINGLE_MISSING_DOWNLOAD",
  "required":["consistent normal-frame rho,j,pi and multi-fluid source closure","self-consistent radiation/recombination backreaction","full mode and IC-family atlas with external comparison"],
  "local_reuse":"R49 dynamic general tilted history + BASS rank9 Thomson + R97 all-m projected transport + R98 cosmological IVPs",
  "external_comparator":"AniCLASS/AniLoS nearly-FLRW I,V,VII0,VIIh,IX; not a general-VIh nonlinear substitute"
 }}
def preflight(network=True):
 t=time.monotonic();DEST.mkdir(parents=True,exist_ok=True);out={}
 for k,url in INDEXES.items():
  try:out[k]=fetch_index(k,url) if network else {"url":url,"status":"NETWORK_NOT_REQUESTED"}
  except Exception as e:out[k]={"url":url,"status":"FETCH_BLOCKED","error":str(e)}
 jobs=known_file_jobs()
 probes={}
 for name in COMMANDER_IDS:
  try:probes[name]=commander_probe(name) if network else {"url":PLA+name,"status":"NETWORK_NOT_REQUESTED"}
  except Exception as e:probes[name]={"url":PLA+name,"status":"FETCH_BLOCKED","error":str(e)}
 try:
  lotss=lotss_catalog_probe(out["LOTSS_DR3"]) if network else {"url":LOTSS_URL,"status":"NETWORK_NOT_REQUESTED"}
 except Exception as e:lotss={"url":LOTSS_URL,"status":"FETCH_BLOCKED","error":str(e)}
 conflict=contracts()
 conflict["RADIO_SOURCE_SELECTION"]["official_source_catalogue_header"]=lotss
 conflict["PLANCK_MATCHED_NULL"]["full_mission_ID00000_header_probes"]=probes
 result={"lotss_catalogue_header_comparison":lotss,"schema":"htt.r98.acquisition_preflight/2","historical_access_failures":PRIOR_FAILURES,"commander_header_probes":probes,"commander_max_files_per_command":1,"metadata":out,"verified_file_jobs":jobs,
  "existing_data_inventory_source":"CMB_GROUPED_FULL_CACHE.json + CMB_OBSERVED_SPLITS.json + CF4_P1_RESULTS.json + RADIO_FULL_MODELS.json + GAIA_FULL_SHARED_PATCH.json",
  "missing_input_contracts":conflict,"download_budget_default_bytes":2_000_000,
  "downloaded_science_payload_bytes":0,"existing_inputs_not_redownloaded":True,
  "new_data_destination":str(DEST),"free_bytes":shutil.disk_usage(DEST).free,
  "large_radio_mosaic_payloads":"PREPARED_URL_INDEX_ONLY; declared file sizes/checksums and aggregate disk budget required before fetching",
  "messages_to_authors_sent":False,"elapsed_seconds":time.monotonic()-t}
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/"ACQUISITION_PREFLIGHT.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 (OUT/"MISSING_INPUT_CONTRACTS.json").write_text(json.dumps(conflict,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({k:v["status"] for k,v in {**out,**probes}.items()}));return result
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline",action="store_true")
    parser.add_argument("--fetch",choices=[*ALLOWLIST,*COMMANDER_IDS],help="one exact object; incoming bytes capped")
    parser.add_argument("--budget-bytes",type=int,default=2_000_000)
    parser.add_argument("--expected-sha256",help="independent full-object digest; required for pre-existing Commander partial")
    args=parser.parse_args()
    if not args.fetch:
        preflight(not args.offline)
        return
    if args.offline:parser.error("--offline and --fetch are mutually exclusive")
    job=archive_job(args.fetch)
    if args.fetch in ALLOWLIST:
        prior=OLD_DEST/args.fetch
    else:
        kind="cmb" if args.fetch==COMMANDER_IDS[0] else "noise"
        prior=COMMANDER_RAW/f"{kind}_mc"/args.fetch
    if prior.is_file():
        record=validate_payload(prior,job,args.expected_sha256)
        print(json.dumps({**record,"status":"EXISTING_LOCAL_VALIDATED","path":str(prior)}))
    else:
        print(json.dumps(download(job,args.budget_bytes,args.expected_sha256)))
if __name__=="__main__":
    main()