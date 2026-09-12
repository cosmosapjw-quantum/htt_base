"""Git-object and filesystem collectors; all target code is inert input."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from . import PARSER_VERSION
from .db import identity, js, put_meta, get_meta, gap, reindex, counts, version_members
from .extract import CODE, extract, language, owner, role, extraction_context, state, catalog_generated


def git(location, *args, text=False, check=True):
    return subprocess.run(git_prefix(location) + list(args), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=check, text=text,
                          env=dict(os.environ,GIT_NO_LAZY_FETCH='1'))


def git_prefix(location):
    p=Path(location)
    prefix=['git','-c','core.fsmonitor=false','-c','log.showSignature=false']
    return prefix+['--git-dir',str(p)] if (p/'objects').is_dir() and (p/'HEAD').is_file() else prefix+['-C',str(p)]


class ObjectReader:
    def __init__(self, location):
        self.process = subprocess.Popen(git_prefix(location) + ['cat-file', '--batch'],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        env=dict(os.environ,GIT_NO_LAZY_FETCH='1'))

    def read(self, oid, *, limit=None, spool=False):
        p = self.process
        p.stdin.write(oid.encode() + b'\n'); p.stdin.flush()
        header = p.stdout.readline().decode().strip().split()
        if len(header) != 3 or not header[2].isdigit(): raise ValueError(f'missing Git object {oid}: {header}')
        kind, size = header[1], int(header[2])
        keep = limit is None or size <= limit
        target = tempfile.SpooledTemporaryFile(max_size=8*1024**2) if keep and spool else io.BytesIO() if keep else None
        left = size
        while left:
            block = p.stdout.read(min(left, 1024**2))
            if not block: raise EOFError(f'truncated Git object {oid}')
            if target is not None: target.write(block)
            left -= len(block)
        if p.stdout.read(1) != b'\n': raise ValueError('invalid cat-file frame')
        if target is not None: target.seek(0)
        return kind, size, target if spool else target.getvalue() if target else None

    def close(self):
        self.process.stdin.close(); self.process.stdout.close(); self.process.wait()


class Scanner:
    def __init__(self, connection, scope):
        self.c, self.scope = connection, scope
        self.text_limit = int(scope.get('text_limit_bytes', 8*1024**2))
        self.archive_limit = int(scope.get('archive_limit_bytes', 2*1024**3))
        self.archive_depth = int(scope.get('archive_depth', 4))
        prior=get_meta(self.c,'scope')
        defaults={'text_limit_bytes':8*1024**2,'archive_limit_bytes':2*1024**3,'archive_depth':4}
        if prior and any(prior.get(k,v)!=scope.get(k,v) for k,v in defaults.items()):
            raise ValueError('extraction limits changed; preserve this DB and use scan --full with a new --db path')
        self.parsed_new, self.parsed_cached = 0, 0
        self.visited_dirs = set()
        self.exclude_roots = [str(Path(p).resolve()) for p in scope.get('exclude_roots', [])]
        self.exclude_dirs = set(scope.get('metadata_only_directories', ['.git','.venv','venv','env','target','__pycache__','.cache','.pytest_cache','node_modules']))
        self.exclude_dirs.add('.remember')
        stale=self.c.execute('SELECT count(*) FROM contents WHERE parser_version<>?',(PARSER_VERSION,)).fetchone()[0]
        self._file_cache = set(r['id'] for r in self.c.execute('SELECT f.id,f.path,f.language,c.parser_version FROM files f LEFT JOIN contents c ON f.content_id=c.id')
            if (not r['parser_version'] or r['parser_version']==PARSER_VERSION)
            and not (r['path'].endswith('.pdf') and r['language']!='pdf')
            and not (stale and r['language']=='archive'))
        self._content_cache = {r['id']: (r['processing_status'], r['language']) for r in self.c.execute('SELECT id,processing_status,language FROM contents')}
        self._archive_cache = {}
        self._git_files = None
        self._common_sources = {}
        for config in scope.get('git_sources',[]):
            p=Path(config['path'])
            if p.exists():
                common=git(p,'rev-parse','--git-common-dir',text=True,check=False).stdout.strip()
                if common:self._common_sources[str((p/common).resolve())]=config.get('replica_of',config['id'])

    def source(self, sid, kind, locator, origin='', head='', history_scope='', **details):
        self.c.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,locator=excluded.locator,origin=excluded.origin,head=excluded.head,history_scope=excluded.history_scope,details=excluded.details',
            (sid, kind, str(locator), origin, head, history_scope, js(details)))

    def material(self, sid, path, data=None, *, git_blob=None, commit=None, size=None,
                 container=None, root_file=None, status_override=None, details=None):
        lang = language(path)
        f_role = role(path, lang)
        details = dict(details or {})
        if '.remember' in PurePosixPath(path.replace('!/', '/')).parts:
            if size is None and data is not None:size=len(data)
            data=None;f_role='environment_cache';status_override='agent_context_cache_metadata_only'
            details['exclusion_reason']='automatic agent context/cache; not a project source'
        elif catalog_generated(path):
            if size is None and data is not None:size=len(data)
            data=None;f_role='catalog_generated';status_override='catalog_generated_metadata_only'
            details['exclusion_reason']='catalog output; metadata retained without recursive semantic extraction'
        digest = hashlib.sha256(data).hexdigest() if data is not None else None
        version = git_blob or digest or 'metadata:' + identity(size, details.get('mtime_ns'), details.get('target'))
        fid = identity(sid, path, version, container)
        if fid in self._file_cache:
            return fid
        self.c.execute('DELETE FROM edges WHERE from_id IN (SELECT id FROM records WHERE file_id=?)',(fid,))
        self.c.execute('DELETE FROM records WHERE file_id=?',(fid,))
        result, cid = None, None
        process = status_override or ('metadata_only' if data is None else 'parsed')
        if data is not None:
            # Structured extraction depends on registry context, not only bytes.
            context = extraction_context(path)
            cid = digest + ':' + identity(lang, context)[:8]
            if cid in self._content_cache:
                cached = self.c.execute('SELECT parsed FROM contents WHERE id=? AND parser_version=?', (cid, PARSER_VERSION)).fetchone()
                if cached:
                    result = json.loads(cached[0]); self.parsed_cached += 1
            if result is None:
                result = extract(data, path)
                self.parsed_new += 1
                self.c.execute('INSERT OR REPLACE INTO contents VALUES (?,?,?,?,?,?,?)',
                    (cid,len(data),lang,result['status'],PARSER_VERSION,result['summary'],js(result)))
                self._content_cache[cid] = result['status'], lang
            process = result['status']
            details['content_sha256'] = digest
            details['limitations'] = result['limitations']
        self.c.execute('INSERT INTO files VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET content_id=excluded.content_id,language=excluded.language,processing_status=excluded.processing_status,details=excluded.details',
            (fid,sid,path,cid,git_blob,commit,f_role,lang,process,size if size is not None else len(data or b''),container,root_file,js(details)))
        self._file_cache.add(fid)
        if process in {'parse_error','decode_error','oversized_text','archive_error','archive_depth_limit','oversized_archive'}:
            gap(self.c,sid,path,'extract',process,js(details))
        if result:
            self.add_records(fid, path, result)
        return fid

    def add_records(self, fid, path, result):
        assigned_owner = owner(path)
        recs = list(result['records'])
        # Preserve explicit migration prose as a searchable lead. Direction and
        # successful porting are never inferred from word similarity or age.
        for original in list(recs):
            excerpt = original['summary'] + '\n' + str(original['details'].get('source_record_excerpt',''))
            match = re.search(r'\b(?:ported|migrated|backported)\s+(?:from|to)\b|\b(?:migration|porting)\b|이식',excerpt,re.I)
            if match:
                recs.append(dict(kind='port',local_id='port:'+original['kind']+':'+original['local_id'],
                    name=original['name'],line=original['line'],end_line=original['end_line'],
                    summary=excerpt[max(0,match.start()-300):match.end()+1800],
                    status='recorded_port_mention',recorded_status=original['recorded_status'],
                    evidence_level='source_statement_only',details={
                        'source_record_local_id':original['local_id'],
                        'direction_status':'NOT_INFERRED; consult explicit source and target in statement',
                        'port_completion':'NOT_VERIFIED','runtime_status':'NOT_EXECUTED',
                        'followup':'Compare the named source, target, API and assumptions at their declared versions; text may describe a plan or rejected migration.'} ))
        if not recs:
            recs = [dict(kind='file',local_id='file',name=PurePosixPath(path).name,line=1,end_line=None,
                         summary=result['summary'][:3000],recorded_status='',status='source_present',
                         evidence_level='static_source_only',details={'extraction':'file_metadata_and_excerpt'})]
        feature = next((r for r in recs if r['kind']=='feature' and r['local_id']=='module'),None)
        if feature:
            feature['name'] = PurePosixPath(path).name
            if feature['details'].get('entrypoint') and role(path,result['language']) not in {'test','tooling'}:
                candidate = dict(feature)
                candidate.update(kind='analysis',local_id='entrypoint',status='static_entrypoint_candidate',name=PurePosixPath(path).name)
                candidate['details'] = dict(feature['details'],command=f'python {path}',command_basis='inferred_main_guard_not_executed',scientific_usability='NOT_VERIFIED')
                recs.append(candidate)
        multiplicity=Counter((r['kind'],r['local_id']) for r in recs)
        for raw_record in recs:
            r=dict(raw_record)
            if r['recorded_status'] and r['kind']!='port':r['status']=state(r['recorded_status'])
            if multiplicity[(r['kind'],r['local_id'])]>1:
                r['local_id']=r['local_id']+'@'+str(r.get('line'))
            rid = identity(fid,r['kind'],r['local_id'])
            raw_owner = r['details'].get('owner', assigned_owner)
            own = str(raw_owner) if isinstance(raw_owner,(str,int)) else assigned_owner
            self.c.execute('INSERT OR IGNORE INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (rid,fid,r['local_id'],r['kind'],r['name'],own,result['language'],r['status'],r['recorded_status'],
                 r['evidence_level'],r['line'],r['end_line'],r['summary'],js(r['details'])))
            refs = set(result['references']) if r['kind'] in {'feature','file'} else set()
            from .extract import reference_edges
            refs.update(reference_edges(js(r['details']) + '\n' + r['summary']))
            for target in sorted(refs): self.edge(rid,'references',target,'unresolved')
            for imp in r['details'].get('imports', []): self.edge(rid,'imports',imp,'static_import_unresolved')
            for call in r['details'].get('calls', []): self.edge(rid,'calls',call,'static_call_unresolved')
            for rel in ['supersedes','superseded_by']:
                targets = r['details'].get(rel, [])
                targets = targets if isinstance(targets,list) else [targets]
                for target in targets: self.edge(rid,rel,str(target),'recorded_relation_unresolved')

    def refresh_record_views(self):
        """Rebuild derived rows from cached extraction when view semantics change.

        This does not reopen Git blobs, archives or research programs. The cached
        parser preserves all duplicate declarations even when an older row view
        accidentally used only their qualified name as a key.
        """
        if get_meta(self.c,'record_view_version')=='2':return
        self.c.execute('DELETE FROM edges');self.c.execute('DELETE FROM records')
        rows=self.c.execute('SELECT f.id,f.path,c.parsed FROM files f JOIN contents c ON f.content_id=c.id')
        for n,row in enumerate(rows):
            self.add_records(row['id'],row['path'],json.loads(row['parsed']))
            if n%10000==0:print(f'record views: {n} files',file=sys.stderr,flush=True)
        put_meta(self.c,'record_view_version','2')
        self.c.commit()

    def omit_context_caches(self):
        """Retain path/version metadata while dropping recursive agent-cache text.

        Applies to earlier catalog snapshots too. Original cache files are never
        changed; their old observations remain explicitly outside source scope.
        """
        rows=self.c.execute("SELECT id,content_id,details FROM files WHERE path LIKE '.remember/%' OR path LIKE '%/.remember/%'").fetchall()
        cache_records="SELECT r.id FROM records r JOIN files f ON r.file_id=f.id WHERE f.path LIKE '.remember/%' OR f.path LIKE '%/.remember/%'"
        self.c.execute("UPDATE edges SET target_id=NULL,resolution='excluded_context_cache' WHERE target_id IN ("+cache_records+")")
        self.c.execute('DELETE FROM search WHERE record_id IN ('+cache_records+')')
        for row in rows:
            fid=row['id'];old=json.loads(row['details'])
            self.c.execute('DELETE FROM edges WHERE from_id IN (SELECT id FROM records WHERE file_id=?)',(fid,))
            self.c.execute('DELETE FROM records WHERE file_id=?',(fid,))
            detail={k:old[k] for k in ['mtime_ns','version_kind','content_sha256'] if k in old}
            detail['exclusion_reason']='automatic agent context/cache; metadata only; not a project source'
            self.c.execute("UPDATE files SET content_id=NULL,role='environment_cache',processing_status='agent_context_cache_metadata_only',details=? WHERE id=?",(js(detail),fid))
        self.c.execute('DELETE FROM contents WHERE NOT EXISTS (SELECT 1 FROM files WHERE content_id=contents.id)')
        self.c.execute("UPDATE filesystem SET status='agent_context_cache_metadata_only' WHERE path LIKE '.remember/%' OR path LIKE '%/.remember/%'")
        return len(rows)

    def refresh_record_states(self):
        """Upgrade status classification without reopening unchanged sources."""
        if get_meta(self.c,'status_classifier_version')=='2':return 0
        changed=0;contents=set()
        for row in self.c.execute("SELECT r.id,r.status,r.recorded_status,f.content_id FROM records r JOIN files f ON r.file_id=f.id WHERE r.recorded_status<>'' AND r.kind<>'port'").fetchall():
            normalized=state(row['recorded_status'])
            if normalized!=row['status']:
                self.c.execute('UPDATE records SET status=? WHERE id=?',(normalized,row['id']))
                changed+=1
                if row['content_id']:contents.add(row['content_id'])
        for cid in contents:
            parsed=json.loads(self.c.execute('SELECT parsed FROM contents WHERE id=?',(cid,)).fetchone()[0])
            for record in parsed['records']:
                if record['recorded_status']:record['status']=state(record['recorded_status'])
            self.c.execute('UPDATE contents SET parsed=? WHERE id=?',(js(parsed),cid))
        put_meta(self.c,'status_classifier_version','2')
        return changed

    def edge(self, rid, relation, target, resolution, target_id=None, **details):
        self.c.execute('INSERT OR IGNORE INTO edges VALUES (?,?,?,?,?,?,?)',
            (identity(rid,relation,target),rid,relation,target,target_id,resolution,js(details)))

    def archive(self, sid, path, stream, parent_fid, *, root_file=None, commit=None, depth=0):
        if depth >= self.archive_depth:
            gap(self.c,sid,path,'archive','archive_depth_limit',f'depth={depth}; limit={self.archive_depth}')
            return
        root_file = root_file or parent_fid
        try:
            if path.lower().endswith('.zip'):
                archive = zipfile.ZipFile(stream)
                entries = [(x.filename,x.file_size,x.is_dir(),x) for x in archive.infolist()]
                opener = archive.open
            else:
                archive = tarfile.open(fileobj=stream,mode='r:*')
                entries = [(x.name,x.size,x.isdir(),x) for x in archive.getmembers()]
                opener = archive.extractfile
            with archive:
                duplicate_names = set()
                for name,size,is_dir,entry in entries:
                    if is_dir: continue
                    member = path + '!/' + name
                    if name in duplicate_names:
                        gap(self.c,sid,member,'archive_member','duplicate_archive_member','Duplicate name; indexed first member separately from ambiguity.')
                        continue
                    duplicate_names.add(name)
                    lang = language(name)
                    target = getattr(entry,'linkname','')
                    if target:
                        self.material(sid,member,size=size,container=parent_fid,root_file=root_file,commit=commit,
                                      status_override='archive_link_metadata',details={'target':target}); continue
                    if lang == 'archive' and size <= self.archive_limit:
                        handle = opener(entry)
                        if handle is None: continue
                        with handle, tempfile.SpooledTemporaryFile(max_size=8*1024**2) as nested:
                            import shutil
                            shutil.copyfileobj(handle,nested);nested.seek(0)
                            fid = self.material(sid,member,size=size,container=parent_fid,root_file=root_file,commit=commit,status_override='archive_members_enumerated')
                            self.archive(sid,member,nested,fid,root_file=root_file,commit=commit,depth=depth+1)
                    elif lang not in {'binary_or_unclassified','archive','csv'} and size <= self.text_limit:
                        handle = opener(entry)
                        if handle is None:
                            self.material(sid,member,size=size,container=parent_fid,root_file=root_file,commit=commit,status_override='archive_special_member')
                        else:
                            with handle: data=handle.read(self.text_limit+1)
                            self.material(sid,member,data,container=parent_fid,root_file=root_file,commit=commit,size=size)
                    else:
                        status = 'oversized_archive' if lang=='archive' else 'oversized_text' if lang not in {'binary_or_unclassified','csv'} else 'metadata_only'
                        self.material(sid,member,size=size,container=parent_fid,root_file=root_file,commit=commit,status_override=status)
        except (OSError,EOFError,ValueError,RuntimeError,zipfile.BadZipFile,tarfile.TarError) as exc:
            gap(self.c,sid,path,'archive','archive_error',repr(exc))

    def git_source(self, config):
        sid, location = config['id'], Path(config['path'])
        history = config.get('history','all')
        self.source(sid,'git',str(location),history_scope=history)
        if not location.exists():
            gap(self.c,sid,str(location),'git','missing_source','Git source path is unavailable'); return
        # -C accepts both working trees and a bare/pre-rewrite Git directory.
        refs = git(location,'for-each-ref','--format=%(refname)%00%(objectname)',text=True)
        reference_rows=[]
        for line in refs.stdout.splitlines():
            name,oid=line.split('\0',1)
            peeled=git(location,'rev-parse',oid+'^{commit}',text=True,check=False)
            if peeled.returncode==0: reference_rows.append((sid,name,peeled.stdout.strip()))
            else: gap(self.c,sid,name,'git_ref','non_commit_ref','Ref does not point to a commit')
        self.c.execute('DELETE FROM refs WHERE source_id=?',(sid,))
        self.c.executemany('INSERT INTO refs VALUES (?,?,?)',reference_rows)
        head=git(location,'rev-parse','HEAD',text=True,check=False).stdout.strip()
        origin=git(location,'remote','get-url','origin',text=True,check=False).stdout.strip()
        self.source(sid,'git',str(location),origin=origin,head=head,history_scope=history)
        if config.get('replica_of'):
            self.source(sid,'git_replica',str(location),origin=origin,head=head,history_scope='replica_ref_metadata',canonical_source=config['replica_of'])
            self.c.commit();return
        log=git(location,'log','--all','--reverse','--topo-order','--format=%H%x00%T%x00%P%x00%ct%x00%s',text=True)
        commits=[]
        for line in log.stdout.splitlines():
            fields=line.split('\0',4)
            if len(fields)!=5:
                gap(self.c,sid,'git-log','decode','invalid_commit_line',line[:200]);continue
            sha,tree,parents,stamp,subject=fields
            commits.append((sid,sha,tree,js(parents.split()),int(stamp),subject))
        if history=='heads':
            wanted={r[2] for r in reference_rows}|{head}
            commits=[x for x in commits if x[1] in wanted]
        self.c.executemany('INSERT OR IGNORE INTO commits VALUES (?,?,?,?,?,?)',commits)
        if config.get('dependency_only'):
            self.source(sid,'git_dependency_metadata',str(location),origin=origin,head=head,history_scope='commit_and_ref_metadata',
                        classification='installed_general_dependency; source internals are not project implementations')
            self.c.commit();return
        reader=ObjectReader(location)
        tree_cache={}
        visited=set()
        def tree_entries(oid):
            if oid in tree_cache:return tree_cache[oid]
            rows=self.c.execute('SELECT name,oid,kind,mode FROM trees WHERE source_id=? AND tree_sha=?',(sid,oid)).fetchall()
            if rows:
                entries=[tuple(x) for x in rows]
            else:
                kind,size,raw=reader.read(oid)
                if kind!='tree':raise ValueError(f'{oid} is not a tree')
                entries=[];at=0
                while at<len(raw):
                    sep=raw.index(b' ',at);nul=raw.index(b'\0',sep)
                    mode=raw[at:sep].decode();name=raw[sep+1:nul].decode('utf-8','surrogateescape')
                    child=raw[nul+1:nul+21].hex();at=nul+21
                    k='tree' if mode=='40000' else 'submodule' if mode=='160000' else 'symlink' if mode=='120000' else 'blob'
                    entries.append((name,child,k,mode))
                self.c.executemany('INSERT OR IGNORE INTO trees VALUES (?,?,?,?,?,?)',[(sid,oid,*e) for e in entries])
            tree_cache[oid]=entries;return entries

        def walk(oid,prefix,sha):
            if (oid,prefix) in visited:return
            visited.add((oid,prefix))
            for name,child,kind,mode in tree_entries(oid):
                path=prefix+name
                if kind=='tree':walk(child,path+'/',sha);continue
                fid=identity(sid,path,child,None)
                if fid in self._file_cache:continue
                if kind=='submodule':
                    self.material(sid,path,git_blob=child,commit=sha,status_override='submodule_reference',details={'target_commit':child});continue
                lang=language(path)
                if catalog_generated(path):
                    size=int(git(location,'cat-file','-s',child,text=True).stdout.strip())
                    self.material(sid,path,git_blob=child,commit=sha,size=size,status_override='catalog_generated_metadata_only');continue
                if lang=='archive':
                    k,size,stream=reader.read(child,limit=self.archive_limit,spool=True)
                    fid=self.material(sid,path,git_blob=child,commit=sha,size=size,status_override='archive_members_enumerated' if stream else 'oversized_archive')
                    if stream:
                        with stream:self.archive(sid,path,stream,fid,commit=sha)
                else:
                    limit=self.text_limit if lang not in {'binary_or_unclassified','csv'} else 0
                    k,size,data=reader.read(child,limit=limit)
                    status='metadata_only' if lang in {'binary_or_unclassified','csv'} else 'oversized_text' if data is None else None
                    if kind=='symlink':
                        self.material(sid,path,git_blob=child,commit=sha,size=size,status_override='git_symlink',details={'target':data.decode('utf8','replace') if data else 'not_read'})
                    else:self.material(sid,path,data,git_blob=child,commit=sha,size=size,status_override=status)
        try:
            for i,(_,sha,tree,*_) in enumerate(commits):
                try:walk(tree,'',sha)
                except (ValueError,OSError,EOFError) as exc:gap(self.c,sid,sha,'git_tree','git_object_error',repr(exc))
                if i%100==0:
                    self.c.commit(); print(f'git {sid}: {i}/{len(commits)} commits, files={len(self._file_cache)}',file=sys.stderr,flush=True)
        finally:reader.close()
        targets={r[2] for r in reference_rows}|{head}
        if sid==self.scope.get('baseline_source'):targets.add(self.scope['baseline_commit'])
        for sha in sorted(targets):self.snapshot(sid,sha)
        self.c.commit()

    def snapshot(self,sid,sha):
        if self.c.execute('SELECT 1 FROM snapshots WHERE source_id=? AND commit_sha=?',(sid,sha)).fetchone():return
        rows=version_members(self.c,sid,sha)
        self.c.executemany('INSERT OR IGNORE INTO members VALUES (?,?,?)',[(sid,sha,r) for r in rows])
        self.c.execute('INSERT OR IGNORE INTO snapshots VALUES (?,?)',(sid,sha))

    def filesystem_source(self, config):
        sid,root=config['id'],Path(config['path'])
        self.source(sid,'filesystem',str(root),history_scope='observed_overlay',description=config.get('description',''))
        self.c.execute("UPDATE filesystem SET status='not_seen_this_scan' WHERE source_id=?",(sid,))
        if not root.exists():gap(self.c,sid,str(root),'filesystem','missing_source','Root unavailable');return
        scanned=0
        if self._git_files is None:
            self._git_files={(r['source_id'],r['path'],r['git_blob']):r['id'] for r in self.c.execute('SELECT id,source_id,path,git_blob FROM files WHERE git_blob IS NOT NULL')}
        def walk(directory,relative='',repo_context=None):
            nonlocal scanned
            try: info=directory.stat()
            except OSError as exc:gap(self.c,sid,relative,'stat','read_error',repr(exc));return
            key=(info.st_dev,info.st_ino)
            if key in self.visited_dirs:return
            self.visited_dirs.add(key)
            try:entries=sorted(os.scandir(directory),key=lambda x:x.name)
            except OSError as exc:gap(self.c,sid,relative,'scandir','read_error',repr(exc));return
            if any(x.name=='.git' for x in entries):
                common=git(directory,'rev-parse','--git-common-dir',text=True,check=False).stdout.strip()
                logical=self._common_sources.get(str((directory/common).resolve())) if common else None
                if not logical:
                    origin=git(directory,'remote','get-url','origin',text=True,check=False).stdout.strip()
                    if origin.rstrip('/').removesuffix('.git')=='https://github.com/cosmosapjw-quantum/htt_base':logical='htt_base'
                if logical:
                    index={}
                    for item in git(directory,'ls-files','--stage','-z',check=False).stdout.split(b'\0'):
                        if not item:continue
                        metadata,name=item.split(b'\t',1);bits=metadata.split()
                        if bits[2]==b'0':index[name.decode('utf8','surrogateescape')]=bits[1].decode()
                    repo_context=(logical,relative,index)
            for entry in entries:
                path=relative+entry.name
                try:
                    st=entry.stat(follow_symlinks=False)
                    is_link=stat.S_ISLNK(st.st_mode);is_dir=stat.S_ISDIR(st.st_mode)
                    kind='symlink' if is_link else 'directory' if is_dir else 'file' if stat.S_ISREG(st.st_mode) else 'special'
                    target=os.readlink(entry.path) if is_link else None
                    status='observed';fid=None
                    absolute=str(Path(entry.path).absolute())
                    excluded=any(absolute==p or absolute.startswith(p+'/') for p in self.exclude_roots)
                    if is_dir and (entry.name in self.exclude_dirs or excluded):status='directory_contents_metadata_only'
                    elif is_dir:
                        walk(Path(entry.path),path+'/',repo_context)
                    elif is_link:
                        resolved=Path(entry.path).resolve()
                        status='symlink_target_present' if resolved.exists() else 'broken_symlink'
                        if status=='broken_symlink':gap(self.c,sid,path,'symlink',status,target)
                        # Follow directory links only into the explicitly declared roots.
                        allowed=any(str(resolved)==p or str(resolved).startswith(p+'/') for p in self.scope.get('follow_link_roots',[]))
                        if allowed and resolved.is_dir() and not any(str(resolved)==p or str(resolved).startswith(p+'/') for p in self.exclude_roots):walk(resolved,path+'/')
                    elif kind=='file':
                        previous=self.c.execute('SELECT file_id,bytes,mtime_ns,inode,device FROM filesystem WHERE source_id=? AND path=?',(sid,path)).fetchone()
                        alias=None
                        if repo_context:
                            logical,prefix,index=repo_context
                            local=path[len(prefix):]
                            blob=index.get(local)
                            if blob:
                                candidate=self._git_files.get((logical,local,blob))
                                if candidate:
                                    digest=hashlib.sha1(f'blob {st.st_size}\0'.encode())
                                    with open(entry.path,'rb') as raw:
                                        for block in iter(lambda:raw.read(1024**2),b''):digest.update(block)
                                    after=entry.stat(follow_symlinks=False)
                                    if (st.st_size,st.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                                        gap(self.c,sid,path,'alias_read','changed_during_scan','Raw file changed while comparing to Git blob')
                                    elif digest.hexdigest()==blob:alias=candidate
                        if alias:
                            # Raw bytes match a known Git blob; no clean filters,
                            # diff drivers or research programs are executed.
                            fid=alias
                        elif previous and previous['file_id'] in self._file_cache and tuple(previous[k] for k in ['bytes','mtime_ns','inode','device'])==(st.st_size,st.st_mtime_ns,st.st_ino,st.st_dev):
                            fid=previous['file_id']
                        else:
                            lang=language(path); detail={'mtime_ns':st.st_mtime_ns,'version_kind':'local_observation'}
                            if lang=='archive' and st.st_size<=self.archive_limit:
                                fid=self.material(sid,path,size=st.st_size,status_override='archive_members_enumerated',details=detail)
                                with open(entry.path,'rb') as stream:self.archive(sid,path,stream,fid)
                            elif lang not in {'binary_or_unclassified','csv','archive'} and st.st_size<=self.text_limit:
                                with open(entry.path,'rb') as stream:data=stream.read(self.text_limit+1)
                                fid=self.material(sid,path,data,size=st.st_size,details=detail)
                            else:
                                why='oversized_archive' if lang=='archive' else 'oversized_text' if lang not in {'binary_or_unclassified','csv'} else 'metadata_only'
                                fid=self.material(sid,path,size=st.st_size,status_override=why,details=detail)
                    self.c.execute('INSERT OR REPLACE INTO filesystem VALUES (?,?,?,?,?,?,?,?,?,?)',
                        (sid,path,kind,st.st_size,st.st_mtime_ns,st.st_dev,st.st_ino,target,status,fid))
                    scanned+=1
                    if scanned%20000==0:self.c.commit();print(f'filesystem {sid}: {scanned} entries',file=sys.stderr,flush=True)
                except (OSError,ValueError,RuntimeError) as exc:
                    gap(self.c,sid,path,'filesystem_read','read_error',repr(exc))
        walk(root)
        self.c.execute("UPDATE filesystem SET status='missing_since_previous_scan' WHERE source_id=? AND status='not_seen_this_scan'",(sid,))
        self.c.commit();print(f'filesystem {sid}: complete ({scanned})',file=sys.stderr,flush=True)

    def resolve_edges(self):
        """Bind paths at the *same observed commit*, never borrow another version."""
        file_index={}
        for row in self.c.execute('SELECT id,source_id,path,git_blob FROM files WHERE container_id IS NULL'):
            file_index.setdefault((row['source_id'],row['path']),[]).append((row['git_blob'],row['id']))
        tree_index={}
        commit_roots={(r['source_id'],r['sha']):r['tree_sha'] for r in self.c.execute('SELECT source_id,sha,tree_sha FROM commits')}
        path_cache={}
        def lookup(sid,sha,path):
            cache_key=(sid,sha,path)
            if cache_key in path_cache:return path_cache[cache_key]
            tree=commit_roots.get((sid,sha))
            if not tree:return None
            parts=PurePosixPath(path).parts
            for i,part in enumerate(parts):
                key=(sid,tree)
                if key not in tree_index:tree_index[key]={r['name']:(r['oid'],r['kind']) for r in self.c.execute('SELECT name,oid,kind FROM trees WHERE source_id=? AND tree_sha=?',key)}
                value=tree_index[key].get(part)
                if not value:path_cache[cache_key]=None;return None
                tree,kind=value
                if i<len(parts)-1 and kind!='tree':path_cache[cache_key]=None;return None
            path_cache[cache_key]=tree
            return tree
        # Curated annotations bind their own declared source version in
        # add_curation(); their file is not a Git occurrence. Do not replace
        # that explicit binding with a lookup in the annotation pseudo-source.
        rows=self.c.execute("SELECT e.id,e.target,e.relation,f.source_id,f.path,f.observed_commit,f.container_id FROM edges e JOIN records r ON e.from_id=r.id JOIN files f ON r.file_id=f.id WHERE e.relation IN ('references','imports') AND f.source_id NOT IN (SELECT id FROM sources WHERE kind='curated_navigation')").fetchall()
        for n,row in enumerate(rows):
            candidates=[row['target'],str(PurePosixPath(row['path']).parent/row['target'])]
            if row['relation']=='imports':
                module=row['target'];relative=len(module)-len(module.lstrip('.'))
                if relative:
                    parent=PurePosixPath(row['path']).parent
                    for _ in range(relative-1):parent=parent.parent
                    stem=str(parent/module.lstrip('.').replace('.','/'))
                    candidates=[stem+'.py',stem+'/__init__.py']
                else:
                    stem=module.replace('.','/')
                    candidates=[prefix+stem+suffix for prefix in ['', 'htt/','htt/src/','htt/htt/','scripts/'] for suffix in ['.py','/__init__.py']]
            if row['container_id']:
                prefix=row['path'].rsplit('!/',1)[0]+'!/'
                candidates=[prefix+row['target'],str(PurePosixPath(row['path']).parent/row['target'])]
            matches=set()
            for path in candidates:
                if row['container_id']:
                    matches.update(r[0] for r in self.c.execute('SELECT id FROM files WHERE source_id=? AND path=? AND container_id=?',(row['source_id'],path,row['container_id'])))
                elif row['observed_commit']:
                    oid=lookup(row['source_id'],row['observed_commit'],path)
                    matches.update(fid for blob,fid in file_index.get((row['source_id'],path),[]) if blob==oid)
                else:
                    match=self.c.execute('SELECT file_id FROM filesystem WHERE source_id=? AND path=? AND status=?',(row['source_id'],path,'observed')).fetchone()
                    if match and match[0]:matches.add(match[0])
            resolution=('same_version_import_candidate' if row['relation']=='imports' else 'same_version_file_present') if len(matches)==1 else 'ambiguous' if len(matches)>1 else 'unresolved_at_source_version'
            self.c.execute('UPDATE edges SET resolution=?,target_id=? WHERE id=?',(resolution,next(iter(matches)) if len(matches)==1 else None,row['id']))
            if n%50000==0:self.c.commit();print(f'references: {n}/{len(rows)}',file=sys.stderr,flush=True)
        self.c.execute("""UPDATE edges SET target_id=(
          SELECT min(target.id) FROM records source JOIN records target ON source.file_id=target.file_id
          WHERE source.id=edges.from_id AND target.kind='code' AND target.local_id=edges.target),
          resolution='same_file_symbol_candidate'
          WHERE relation='calls' AND (SELECT count(*) FROM records source JOIN records target
          ON source.file_id=target.file_id WHERE source.id=edges.from_id AND target.kind='code'
          AND target.local_id=edges.target)=1""")

    def run(self):
        started=time.time()
        put_meta(self.c,'scope',self.scope)
        put_meta(self.c,'baseline',{'source_id':self.scope.get('baseline_source'),'commit':self.scope.get('baseline_commit')})
        put_meta(self.c,'scientific_execution','NOT_EXECUTED_STATIC_INVENTORY_ONLY')
        put_meta(self.c,'parser_version',PARSER_VERSION)
        for config in self.scope.get('git_sources',[]):
            try:self.git_source(config)
            except (OSError,subprocess.CalledProcessError,ValueError) as exc:gap(self.c,config['id'],config['path'],'git_source','source_scan_error',str(exc))
        for config in self.scope.get('filesystem_sources',[]):self.filesystem_source(config)
        for mapping in self.scope.get('commit_maps',[]):
            with open(mapping) as f:
                for line in f:
                    fields=line.strip().split()
                    if len(fields)==2 and all(len(x)==40 for x in fields):
                        self.c.execute('INSERT OR REPLACE INTO commit_aliases VALUES (?,?,?)',(*fields,mapping))
        self.refresh_record_views()
        self.omit_context_caches()
        self.refresh_record_states()
        self.resolve_edges()
        reindex(self.c)
        report=counts(self.c)
        report.update(parsed_new=self.parsed_new,parsed_cached=self.parsed_cached,elapsed_seconds=round(time.time()-started,3))
        put_meta(self.c,'last_scan',report)
        self.c.commit();self.c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        return report
