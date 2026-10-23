#!/usr/bin/env python3
"""Bounded PR3 acquisition. Raw maps and transfer scratch remain on external disk."""
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from astropy.io import fits
import astropy

OUT = Path(__file__).resolve().parent
CONTRACT = OUT.parent / 'R25-PR3-FREQUENCY-ACQUIRE_INPUT.json'
INPUT = 'ae7e2f0b136ec3dddcf3b9543f9ec91446587dc50c7908b93b3f17b77e014d9f'
PACKET = '014cb70b115b051a27cf126089c1e7f270363aa236d69320c2f777f738dca00d'
AGENT = '/root/rc_014cb70b115b051a'
TASK = 'R25-PR3-FREQUENCY-ACQUIRE'
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def save(p,x): p.write_text(json.dumps(x,indent=2)+'\n')
def headers(p):
    # Curl retains all redirect/CONNECT header blocks; use final HTTP block.
    s=p.read_text(errors='replace')
    blocks=re.split(r'\r?\n\r?\n',s)
    parsed=[]
    for block in blocks:
        lines=block.splitlines()
        if lines and lines[0].startswith('HTTP/'):
            parsed.append((int(lines[0].split()[1]),dict((a.lower().strip(),b.strip()) for a,b in (l.split(':',1) for l in lines[1:] if ':' in l))))
    if not parsed: raise ValueError('No HTTP response headers')
    return parsed[-1]
def validate_range(status,h,start,total,received):
    if start:
        m=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',h.get('content-range',''))
        if status!=206 or not m: raise ValueError('Resume requires HTTP206 Content-Range; never append HTTP200')
        a,b,n=map(int,m.groups())
        if a!=start or n!=total or b!=total-1 or received>b-a+1: raise ValueError('Conflicting Content-Range')
    elif status!=200: raise ValueError('Fresh full transfer requires HTTP200')
    if 'content-length' in h and int(h['content-length'])!=total-start: raise ValueError('Conflicting Content-Length')
    if received>total-start: raise ValueError('Body exceeds expected remaining bytes')
def validate(p,spec):
    with fits.open(p,memmap=True,checksum=False) as hdus:
        hdus.verify('exception')
        tables=[x for x in hdus if isinstance(x,fits.BinTableHDU) and {'Q_STOKES','U_STOKES'}<=set(x.columns.names)]
        if len(tables)!=1: raise ValueError('Expected exactly one Q/U table')
        t=tables[0]; h=t.header
        rawheaders=[x.header.tostring(sep='\n',endcard=True,padding=False) for x in hdus]
        headerpath=TARGET/(p.name+'.headers.json'); save(headerpath,rawheaders)
        units={k:t.columns[k].unit for k in ('Q_STOKES','U_STOKES')}
        is_lfi=spec['band_GHz']<100
        assert all(x==('K_CMB' if is_lfi else 'Kcmb') for x in units.values()),units
        polkey='POLCONV' if is_lfi else 'POLCCONV'
        assert str(h[polkey]).strip()=='COSMO'
        assert str(h['COORDSYS']).strip()=='GALACTIC'
        assert str(h['ORDERING']).strip()=='NESTED'
        assert h['NSIDE']==spec['required_nside']
        npix=int(h['NAXIS2'])*int(t.columns['Q_STOKES'].format.repeat)
        assert npix==12*spec['required_nside']**2, npix
        # Validate payload extent using FITS structural sizes, not just filename.
        extent=max(x.fileinfo()['datLoc']+x.fileinfo()['datSpan'] for x in hdus)
        assert extent==p.stat().st_size,(extent,p.stat().st_size)
        raw_identity={k:(list(h[k]) if k in ('COMMENT','HISTORY') else h[k]) for k in h if any(z in k.upper() for z in ('FREQ','PROC','VERS','RELE','BAND','FILENAME','FILETYPE','COMMENT','HISTORY'))}
        # The exact official URL/filename binds release/full/variant; preserve headers for cross-check.
        assert spec['required_release'] in p.name and '_full.fits' in p.name
        if is_lfi:
            assert 'BPassCorrected' in p.name
            assert h['FREQ']==spec['band_GHz']
            assert h['EXTNAME']=='FREQ-MAP-BPCorr'
            comments='\n'.join(h.get('COMMENT',[]))
            assert f"LFI_SkyMap_{spec['band_GHz']:03d}_1024_R3.00_full.fits" in comments
            assert f"LFI_CorrMap_{spec['band_GHz']:03d}-BPassCorr_1024_R3.00_full.fits" in comments
        else:
            assert h['FILENAME']==p.name
            assert int(str(h['FREQ']).split('-')[0])==spec['band_GHz']
            assert h['EXTNAME']=='FREQ-MAP'
        if spec['band_GHz']==353: assert '353-psb' in p.name
        return {'status':'PASS','Q_U_columns':list(units),'raw_units':units,'canonical_units':'K_CMB','normalization':'spelling only; no rescaling','raw_polarization_keyword':polkey,'raw_polarization_value':h[polkey],'canonical_polarization_convention':'COSMO','NSIDE':h['NSIDE'],'ORDERING':h['ORDERING'],'COORDSYS':h['COORDSYS'],'npix':npix,'payload_extent_bytes':extent,'raw_header_path':str(headerpath),'raw_header_sha256':sha(headerpath),'raw_product_identity_headers':raw_identity,'release_full_variant_identity':'official exact URL and filename, cross-check raw headers','required_release':spec['required_release'],'required_product_variant':spec['required_product_variant']}
def current_receipt_path(filename):
    """Read latest version; legacy receipt is inherited and never overwritten."""
    directory=TARGET/'cooperative_product_receipts'/filename
    versions=sorted(x for x in directory.glob('*.json') if x.stem.isdigit())
    return versions[-1] if versions else TARGET/(filename+'.receipt.json')

def reserve_receipt_path(filename):
    """A new working version per invocation; frozen after the invocation returns.

No mutable current pointer is needed or sealed. An incomplete reserved version
fails closed on the next read rather than silently skipping missing evidence.
"""
    directory=TARGET/'cooperative_product_receipts'/filename
    directory.mkdir(parents=True,exist_ok=True)
    numbers=[int(x.stem) for x in directory.glob('*.json') if x.stem.isdigit()]
    path=directory/f'{max(numbers,default=0)+1:08d}.json'
    with path.open('x'):pass
    return path

def acquire(spec, resume_timeouts=True, candidate_directory=None, cooperative_check=None):
    start=now(); directory=Path(candidate_directory) if candidate_directory else TARGET; directory.mkdir(parents=True,exist_ok=True); p=directory/spec['filename']; part=directory/(p.name+'.part'); attempts=[]
    # Reconstruct earlier actual transport metadata, including initial V1 attempts.
    previous_path=current_receipt_path(p.name)
    previous={}
    if previous_path.exists():
        previous=json.loads(previous_path.read_text())
        attempts=previous.get('partial_or_failure_history',[])
        for old in attempts: old.setdefault('executing_source_sha256',previous.get('executing_source_sha256','UNKNOWN'))
    known={x.get('curl_metadata_path') or x.get('http_header_path','').replace('.http','.curl.json') for x in attempts}
    for cp in sorted(TARGET.glob(p.name+'.attempt-*.curl.json')):
        if str(cp) in known: continue
        base=str(cp).removesuffix('.curl.json'); hp=Path(base+'.http')
        try:
            meta=json.loads(cp.read_text()); status,h=headers(hp)
            stamp=cp.name.split('attempt-')[1].removesuffix('.curl.json')
            began=dt.datetime.strptime(stamp,'%Y%m%dT%H%M%S%f').astimezone(dt.timezone.utc)
            ended=began+dt.timedelta(seconds=float(meta['time_total']))
            attempts.append({'start_time':began.isoformat(),'end_time':ended.isoformat(),'reconstructed_from_retained_raw_files':True,'curl_metadata_path':str(cp),'http_header_path':str(hp),'stderr_path':base+'.stderr','HTTP_status':status,'available_HTTP_metadata':h,'curl_metadata':meta,'returncode':meta.get('exitcode'),'received_bytes':meta.get('size_download'),'offset':int(h['content-range'].split()[1].split('-')[0]) if 'content-range' in h else 0})
        except Exception as e:
            attempts.append({'raw_metadata_parse_error':str(e),'curl_metadata_path':str(cp)})
    for old in attempts:
        if 'start_time' not in old and 'curl_metadata' in old:
            name=Path(old.get('curl_metadata_path') or old['http_header_path'].replace('.http','.curl.json')).name
            stamp=name.split('attempt-')[1].removesuffix('.curl.json')
            began=dt.datetime.strptime(stamp,'%Y%m%dT%H%M%S%f').astimezone(dt.timezone.utc)
            old['start_time']=began.isoformat()
            old['end_time']=(began+dt.timedelta(seconds=float(old['curl_metadata']['time_total']))).isoformat()
            old['timestamp_origin']='Retained local attempt filename plus actual curl time_total'
    rp=reserve_receipt_path(p.name)
    rec={'product_receipt_path':str(rp),'filename':p.name,'band_GHz':spec['band_GHz'],'original_url':spec['url'],'start_time':min([start]+[x['start_time'] for x in attempts if 'start_time' in x]),'validation_start_time':start,'partial_or_failure_history':attempts,'upstream_sha256':None,'upstream_hash_status':'unavailable','path':str(p),'executing_source_sha256':EXECUTING_SOURCE_SHA256}
    for key in ('mirror_source_qualification','published_rehost_MD5','rehost_MD5_status','mixed_source_assembly','required_rehost_MD5','assembled_rehost_MD5'):
        if key in previous:rec[key]=previous[key]
    def persist(): save(rp,rec)
    try:
        if p.exists(): rec['cache_status']='existing exact filename; validated below'
        else:
            rec['cache_status']='no complete exact cached product located'
            expected=spec['advisor_head_content_length']
            offset=part.stat().st_size if part.exists() else 0
            if offset>expected: raise ValueError('Oversize pre-existing partial preserved')
            while offset<expected:
                if cooperative_check:cooperative_check()
                if shutil.disk_usage(TARGET).free<expected-offset+2147483648: raise OSError('Destination reserve would be violated')
                ident=dt.datetime.now().strftime('%Y%m%dT%H%M%S%f')
                base=TARGET/(p.name+'.attempt-'+ident)
                body=Path(str(base)+'.body'); hp=Path(str(base)+'.http'); err=Path(str(base)+'.stderr'); cp=Path(str(base)+'.curl.json')
                cmd=['curl','--http1.1','--location','--fail','--silent','--show-error','--connect-timeout','30','--max-time','900','--dump-header',str(hp),'--output',str(body),'--write-out','%{json}']
                if offset: cmd+=['--range',f'{offset}-']
                cmd+=[spec['url']]
                a={'start_time':now(),'executing_source_sha256':EXECUTING_SOURCE_SHA256,'offset':offset,'command':cmd,'http_header_path':str(hp),'stderr_path':str(err),'curl_metadata_path':str(cp)}
                def actual_started(identity):
                    a.update(start_time=now(),actual_process_started=identity,execution_state='ACTUALLY_STARTED');attempts.append(a)
                    rec['status']='TRANSFER_IN_PROGRESS';persist()
                print('START',p.name,'offset',offset,flush=True)
                with err.open('w') as e:
                    result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=e,text=True,timeout=910,on_process_started=actual_started)
                a.update(end_time=now(),returncode=result.returncode)
                cp.write_text(result.stdout)
                meta=json.loads(result.stdout); status,h=headers(hp)
                received=body.stat().st_size if body.exists() else 0
                a.update(HTTP_status=status,available_HTTP_metadata=h,received_bytes=received,curl_metadata=meta)
                validate_range(status,h,offset,expected,received)
                if not received: raise RuntimeError('Zero progress; stop this product and diagnose transport')
                if offset:
                    with part.open('ab') as dst,body.open('rb') as src: shutil.copyfileobj(src,dst,8*1024*1024)
                    # Retain actual raw attempt body for checkpoint evidence.
                else: shutil.copyfile(body,part)
                offset=part.stat().st_size
                a['validated_partial_bytes_after_attempt']=offset
                persist()
                if cooperative_check:cooperative_check()
                if result.returncode==28 and offset<expected:
                    a['diagnosis']='900s transfer deadline with positive progress and valid response metadata; resume exact remaining bytes'
                    if not resume_timeouts: raise TimeoutError('900s positive-progress partial preserved; scheduled batch continuation will resume')
                    print('RESUME',p.name,'offset',offset,flush=True)
                    persist(); continue
                if result.returncode: raise RuntimeError(f'curl exit {result.returncode}; valid partial retained')
                if offset!=expected: raise ValueError('Incomplete successful transfer; partial retained')
            part.rename(p)
        rec.update(local_byte_count=p.stat().st_size,local_sha256=sha(p))
        assert rec['local_byte_count']==spec['advisor_head_content_length']
        rec['actual_FITS_header_validation']=validate(p,spec)
        if rec.get('required_rehost_MD5'):
            md5=hashlib.md5()
            with p.open('rb') as source:
                for block in iter(lambda:source.read(8*1024*1024),b''):md5.update(block)
            rec['assembled_rehost_MD5']=md5.hexdigest()
            rec['rehost_MD5_status']='PASS' if md5.hexdigest()==rec['required_rehost_MD5'] else 'BYTE_IDENTITY_MISMATCH'
            assert rec['rehost_MD5_status']=='PASS','BYTE_IDENTITY_MISMATCH to Zenodo rehost checksum; no qualification'
            rec['mirror_source_qualification']['status']='FULL_PRODUCT_REHOST_MD5_AND_FITS_PASS'
        rec['status']='VALIDATED_LOCAL_PRODUCT'
        actual=[x for x in attempts if 'curl_metadata' in x]
        if actual:
            last=actual[-1]
            rec.update(final_url=last['curl_metadata']['url_effective'],HTTP_status=last['HTTP_status'],available_HTTP_metadata=last['available_HTTP_metadata'])
        else: rec.update(final_url=None,HTTP_status=None,available_HTTP_metadata={},transport_status='cache reuse; current HTTP unavailable')
    except Exception as e:
        rec.update(status='HOLD',error=f'{type(e).__name__}: {e}')
    rec['end_time']=now(); persist()
    print('END',p.name,rec['status'],rec.get('error',''),flush=True)
    return rec
if __name__=='__main__':
    raise SystemExit('Use reviewed cooperative_resume with a fresh host ACK')
