"""Offline security and integration tests; no provider credentials or network."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import zipfile

spec = importlib.util.spec_from_file_location('publish', Path(__file__).with_name('publish.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

def fixture():
    c = dict(run_id=101, run_number=20, attempt=2, sha='a'*40, repo_id=42, event='schedule', artifact_id=700)
    run = dict(id=101, run_number=20, run_attempt=2, path=p.WORKFLOW, event='schedule',
               repository=dict(full_name=p.REPO,id=42), head_repository=dict(full_name=p.REPO,id=42), head_branch='main', head_sha='a'*40)
    job = dict(id=800, name='deploy', run_id=101, head_sha='a'*40, run_attempt=2, status='completed', conclusion='success',
               started_at='2026-09-12T19:00:00Z', completed_at='2026-09-12T19:01:00Z')
    art = dict(id=700,name='github-pages',expired=False,size_in_bytes=100,digest='sha256:'+'b'*64,
               created_at='2026-09-12T19:00:30Z', workflow_run=dict(id=101,head_sha='a'*40,head_branch='main',repository_id=42,head_repository_id=42))
    return c,run,[job],art,copy.deepcopy(run),'a'*40

def static_files():
    files = {'index.html':b'const GC_SITE = "";', '404.html':b'404', 'content.js':b'[]',
            'sw.js':b'const BUILD = "12345678";\nconst ROUTES = ["/story/example/"];',
            'data/feed.json':json.dumps(dict(fetched='2026-09-12T19:00:10Z',items=[{'title':'Gathered'}],sources=[])).encode(),
            'sitemap.xml':b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://readtheledger.github.io/</loc></url><url><loc>https://readtheledger.github.io/story/example/</loc></url></urlset>',
            'robots.txt':b'Allow: /','about/index.html':b'About',
            'story/example/index.html':b'<link rel="canonical" href="https://readtheledger.github.io/story/example/">'}
    files.update({n:b'fixture' for n in ['sources.js','topics.js','context.js','about.js','analytics.js','media.js','production.js','manifest.webmanifest',
        'icon-180.png','icon-192.png','icon-512.png','icon-maskable-512.png','sitemap-news.xml','feed.xml']})
    return files

def archive(files, extra=None):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw,mode='w') as tar:
        for name,body in files.items():
            info=tarfile.TarInfo(name if name.startswith('/') else './'+name); info.size=len(body); tar.addfile(info,io.BytesIO(body))
        if extra: tar.addfile(extra)
    zipped=io.BytesIO()
    with zipfile.ZipFile(zipped,'w',zipfile.ZIP_DEFLATED) as z: z.writestr('artifact.tar',raw.getvalue())
    return zipped.getvalue()

class ProvenanceTests(unittest.TestCase):
    def test_success_boundary_is_completed_producer_job(self):
        f=fixture(); f[1]['status']='in_progress'
        self.assertEqual(p.validate_provenance(*f)['id'],800)

    def test_untrusted_contexts(self):
        env=dict(GITHUB_REPOSITORY=p.REPO,GITHUB_REF='refs/heads/main',GITHUB_EVENT_NAME='push',GITHUB_RUN_ID='1',GITHUB_RUN_NUMBER='1',GITHUB_RUN_ATTEMPT='1',GITHUB_SHA='a'*40,GITHUB_REPOSITORY_ID='42',PAGES_ARTIFACT_ID='2')
        for key,bad in [('GITHUB_REPOSITORY','fork/repo'),('GITHUB_REF','refs/pull/1/merge'),('GITHUB_EVENT_NAME','pull_request_target')]:
            with self.subTest(key=key), self.assertRaises(p.InvalidEvidence): p.context(dict(env,**{key:bad}))

    def test_rejects_wrong_provenance(self):
        mutations=[(1,['event'],'pull_request'),(1,['path'],'other.yml'),(1,['head_repository','full_name'],'fork/repo'),
                   (1,['repository','id'],43),(1,['head_branch'],'feature'),(1,['head_sha'],'c'*40),(1,['run_attempt'],1),
                   (2,[0,'conclusion'],'failure'),(2,[0,'status'],'in_progress'),(2,[0,'run_attempt'],1),
                   (2,[0,'run_id'],102),(2,[0,'head_sha'],'d'*40),
                   (3,['id'],701),(3,['name'],'unvalidated'),(3,['expired'],True),(3,['digest'],None),
                   (3,['size_in_bytes'],p.MAX_BYTES+1),(3,['workflow_run','id'],99),
                   (3,['workflow_run','head_repository_id'],43),(3,['created_at'],'2026-09-12T18:00:00Z')]
        for index,keys,bad in mutations:
            f=fixture(); obj=f[index]
            for key in keys[:-1]: obj=obj[key]
            obj[keys[-1]]=bad
            with self.subTest(keys=keys,bad=bad),self.assertRaises(p.InvalidEvidence): p.validate_provenance(*f)

    def test_duplicate_producer_is_rejected(self):
        f=fixture(); f[2].append(copy.deepcopy(f[2][0]))
        with self.assertRaises(p.InvalidEvidence): p.validate_provenance(*f)

    def test_newer_failed_or_pending_run_and_attempt_supersede(self):
        for status in ['queued','in_progress','completed']:
            f=fixture(); f[4].update(run_number=21,status=status,conclusion='failure')
            with self.subTest(status=status),self.assertRaises(p.Superseded): p.validate_provenance(*f)
        f=fixture(); f[4]['run_attempt']=3
        with self.assertRaises(p.Superseded): p.validate_provenance(*f)
        f=list(fixture());f[-1]='c'*40
        with self.assertRaises(p.Superseded): p.validate_provenance(*f)

class ArchiveTests(unittest.TestCase):
    def unpack(self,files=None,extra=None,digest=None):
        data=archive(static_files() if files is None else files,extra)
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'site'
            result=p.unpack(data,digest or 'sha256:'+p.sha(data),dest)
            self.assertEqual(result,{name:p.sha(body) for name,body in (static_files() if files is None else files).items()})
            for name,body in (static_files() if files is None else files).items(): self.assertEqual((dest/name).read_bytes(),body)

    def test_exact_artifact_bytes_survive(self): self.unpack()

    def test_archive_digest_is_mandatory(self):
        with self.assertRaises(p.InvalidEvidence): self.unpack(digest='sha256:'+'0'*64)

    def test_path_escape_links_and_duplicates(self):
        for name in ['../escape','/escape','C:/escape','a\\escape','INDEX.HTML','.env']:
            files=static_files();files[name]=b'bad'
            with self.subTest(name=name),self.assertRaises(p.InvalidEvidence): self.unpack(files)
        for kind in [tarfile.SYMTYPE,tarfile.LNKTYPE,tarfile.CHRTYPE]:
            info=tarfile.TarInfo('link');info.type=kind;info.linkname='../escape'
            with self.subTest(kind=kind),self.assertRaises(p.InvalidEvidence): self.unpack(extra=info)

    def test_hidden_platform_and_private_build_files(self):
        for name in ['_headers','_redirects','_worker.js','build.mjs','secret.env','config.yml']:
            files=static_files();files[name]=b'bad'
            with self.subTest(name=name),self.assertRaises(p.InvalidEvidence): self.unpack(files)

    def test_feed_worker_canonical_and_measurement_guards(self):
        cases=[('data/feed.json',None),('data/feed.json',b'{"items":[],"sources":[]}'),
               ('sw.js',b'const BUILD = "dev";'),('story/example/index.html',b'<link rel="canonical" href="https://other.example/">'),
               ('index.html',b'const GC_SITE = "enabled";'),('production.js',None),
               ('sitemap.xml',b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://readtheledger.github.io/missing/</loc></url></urlset>')]
        for name,body in cases:
            files=static_files()
            if body is None: del files[name]
            else: files[name]=body
            with self.subTest(name=name,body=body),self.assertRaises(p.InvalidEvidence): self.unpack(files)

    def test_existing_directory_and_unexpected_zip_rejected(self):
        data=archive(static_files())
        with tempfile.TemporaryDirectory() as d,self.assertRaises(p.InvalidEvidence): p.unpack(data,'sha256:'+p.sha(data),Path(d))
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:z.writestr('other.tar',b'')
        with tempfile.TemporaryDirectory() as d,self.assertRaises(p.InvalidEvidence):p.unpack(raw.getvalue(),'sha256:'+p.sha(raw.getvalue()),Path(d)/'site')

class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.site=self.root/'site'; self.receipt=self.root/'receipt.json'
        config=self.root/'.github/cloudflare';config.mkdir(parents=True)
        for name in ['wrangler.json','_headers']:(config/name).write_bytes((p.ROOT/'.github/cloudflare'/name).read_bytes())
        self.f=fixture();self.data=archive(static_files());self.f[3]['digest']='sha256:'+p.sha(self.data)
        self.env=dict(GITHUB_TOKEN='github-test-secret',CLOUDFLARE_API_TOKEN='cf-test-secret',CLOUDFLARE_ACCOUNT_ID='test-account')
        for target,value in [('ROOT',self.root),('SITE',self.site),('RECEIPT',self.receipt)]:
            obj=patch.object(p,target,value);obj.start();self.addCleanup(obj.stop)
        for obj in [patch.dict(p.os.environ,self.env,clear=True),patch.object(p,'context',return_value=self.f[0]),
                    patch.object(p,'evidence',return_value=(self.f[3],self.f[2][0])),patch('builtins.print')]:
            obj.start();self.addCleanup(obj.stop)

    def prepare(self):
        with patch.object(p,'request',return_value=self.data),patch.object(p.subprocess,'check_output',return_value='a'*40):p.prepare()

    def test_prepare_receipt_and_only_header_overlay(self):
        self.prepare();record=json.loads(self.receipt.read_text())
        self.assertEqual(set(record['files']),set(static_files())|{'_headers'})
        self.assertEqual(record['artifact_digest'],self.f[3]['digest'])
        for name,body in static_files().items():self.assertEqual((self.site/name).read_bytes(),body)

    def test_old_gathered_feed_is_rejected(self):
        files=static_files();feed=json.loads(files['data/feed.json']);feed['fetched']='2026-09-11T19:00:10Z';files['data/feed.json']=json.dumps(feed).encode()
        self.data=archive(files);self.f[3]['digest']='sha256:'+p.sha(self.data)
        with self.assertRaises(p.InvalidEvidence):self.prepare()
        self.assertFalse(self.receipt.exists())

    def test_no_deploy_on_missing_secret_tampering_or_changed_evidence(self):
        self.prepare()
        for failure in ['secret','bytes','receipt','config','newer-run']:
            with self.subTest(failure=failure),patch.object(p.subprocess,'run') as run:
                if failure=='secret':
                    with patch.dict(p.os.environ,CLOUDFLARE_API_TOKEN=''),self.assertRaises(p.InvalidEvidence):p.deploy()
                elif failure=='bytes':
                    target=self.site/'index.html';original=target.read_bytes();target.write_bytes(b'changed')
                    with self.assertRaises(p.InvalidEvidence):p.deploy()
                    target.write_bytes(original)
                elif failure=='receipt':
                    original=self.receipt.read_bytes();record=json.loads(original);record['context']['artifact_id']=701;self.receipt.write_text(json.dumps(record))
                    with self.assertRaises(p.InvalidEvidence):p.deploy()
                    self.receipt.write_bytes(original)
                elif failure=='config':
                    target=self.root/'.github/cloudflare/wrangler.json';original=target.read_bytes();config=json.loads(original);config['main']='worker.js';target.write_text(json.dumps(config))
                    with self.assertRaises(p.InvalidEvidence):p.deploy()
                    target.write_bytes(original)
                else:
                    with patch.object(p,'evidence',side_effect=p.Superseded('new run')),self.assertRaises(p.Superseded):p.deploy()
                run.assert_not_called()

    def test_provider_receipt_must_match_edition_and_tool_gets_no_github_token(self):
        self.prepare();version_id='12345678-1234-1234-1234-123456789abc'
        message='Pages run 101 attempt 2; artifact 700; gathered 2026-09-12T19:00:10Z'
        deployment=dict(success=True,result=dict(deployments=[dict(created_on='2026-09-12T19:02:00Z',versions=[dict(version_id=version_id,percentage=100)])]))
        version=dict(success=True,result=dict(id=version_id,annotations={'workers/message':message}))
        for match in [True,False]:
            version['result']['annotations']['workers/message']=message if match else 'another deploy'
            with self.subTest(match=match),patch.object(p.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run,patch.object(p,'request',side_effect=[json.dumps(deployment).encode(),json.dumps(version).encode()]):
                if match:p.deploy()
                else:
                    with self.assertRaises(p.InvalidEvidence):p.deploy()
                self.assertNotIn('GITHUB_TOKEN',run.call_args.kwargs['env'])
                self.assertEqual(run.call_args.kwargs['env']['CLOUDFLARE_API_TOKEN'],'cf-test-secret')

    def test_download_redirect_never_forwards_github_token(self):
        error=urllib.error.HTTPError('https://api.github.com/artifact',302,'Found',{'Location':'https://blob.example/artifact'},None)
        with patch.object(p.urllib.request,'build_opener') as opener:
            opener.return_value.open.side_effect=[error]
            original=p.request
            with patch.object(p,'request',return_value=b'archive') as follow:
                self.assertEqual(original('https://api.github.com/artifact','github-test-secret'),b'archive')
                follow.assert_called_once_with('https://blob.example/artifact',redirect=True)

    def test_failed_upload_does_not_claim_deployment_or_expose_output(self):
        self.prepare()
        with patch.object(p.subprocess,'run',return_value=subprocess.CompletedProcess([],1,stdout='sensitive provider output')),patch.object(p,'request') as request:
            with self.assertRaisesRegex(p.InvalidEvidence,'raw output withheld') as error:p.deploy()
            self.assertNotIn('sensitive provider output',str(error.exception))
            request.assert_not_called()

if __name__=='__main__':unittest.main()
