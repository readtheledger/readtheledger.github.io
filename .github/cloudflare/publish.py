"""Publish a proven same-run Pages artifact, never PR code or a regathered edition."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

REPO = 'readtheledger/readtheledger.github.io'
WORKFLOW = '.github/workflows/pages.yml'
ALLOWED_EVENTS = {'push', 'schedule', 'workflow_dispatch'}
MAX_BYTES = 200 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / '_cloudflare_site'
RECEIPT = Path(os.environ.get('RUNNER_TEMP', str(ROOT / '.qa'))) / 'cloudflare-pages-provenance.json'

class InvalidEvidence(ValueError): pass
class Superseded(Exception): pass
def require(ok, message):
    if not ok: raise InvalidEvidence(message)
def stamp(value): return datetime.fromisoformat(value.replace('Z', '+00:00'))
def sha(data): return hashlib.sha256(data).hexdigest()
def context(env=os.environ):
    require(env.get('GITHUB_REPOSITORY') == REPO, 'Only the canonical repository may publish')
    require(env.get('GITHUB_REF') == 'refs/heads/main', 'Only main may publish')
    require(env.get('GITHUB_EVENT_NAME') in ALLOWED_EVENTS, 'Untrusted trigger')
    return {'run_id': int(env['GITHUB_RUN_ID']), 'run_number': int(env['GITHUB_RUN_NUMBER']),
            'attempt': int(env['GITHUB_RUN_ATTEMPT']), 'sha': env['GITHUB_SHA'],
            'repo_id': int(env['GITHUB_REPOSITORY_ID']), 'event': env['GITHUB_EVENT_NAME'],
            'artifact_id': int(env['PAGES_ARTIFACT_ID'])}

def validate_provenance(c, run, jobs, artifact, latest, main_sha):
    require(run['id'] == c['run_id'] and run['run_number'] == c['run_number'] and run['run_attempt'] == c['attempt'], 'Run/attempt mismatch')
    require(run['path'] == WORKFLOW and run['event'] == c['event'] and run['event'] in ALLOWED_EVENTS, 'Wrong producer workflow/event')
    require(run['repository']['full_name'] == REPO and run['head_repository']['full_name'] == REPO, 'Foreign or fork producer')
    require(run['repository']['id'] == c['repo_id'] == run['head_repository']['id'], 'Producer repository ID mismatch')
    require(run['head_branch'] == 'main' and run['head_sha'] == c['sha'], 'Producer branch/commit mismatch')
    # The workflow is still running this consumer; the completed producer JOB is the success boundary.
    producers = [j for j in jobs if j['name'] == 'deploy' and j['run_attempt'] == c['attempt']]
    require(len(producers) == 1 and producers[0]['run_id'] == c['run_id'] and producers[0]['head_sha'] == c['sha'] and producers[0]['status'] == 'completed' and producers[0]['conclusion'] == 'success', 'Pages job has not succeeded for this commit/run')
    producer = producers[0]
    require(artifact['id'] == c['artifact_id'] and artifact['name'] == 'github-pages' and not artifact['expired'], 'Wrong or expired artifact')
    origin = artifact['workflow_run']
    require(origin['id'] == c['run_id'] and origin['head_sha'] == c['sha'] and origin['head_branch'] == 'main', 'Artifact is from another run/commit')
    require(origin['repository_id'] == c['repo_id'] == origin['head_repository_id'], 'Artifact repository mismatch')
    require(stamp(producer['started_at']) <= stamp(artifact['created_at']) <= stamp(producer['completed_at']), 'Artifact is not from this producer attempt')
    require(bool(re.fullmatch(r'sha256:[0-9a-f]{64}', artifact.get('digest') or '')), 'Missing archive digest')
    require(0 < artifact['size_in_bytes'] <= MAX_BYTES, 'Archive size out of bounds')
    require(latest['path'] == WORKFLOW and latest['head_branch'] == 'main', 'Latest-run lookup mismatch')
    # The workflow-wide pages lock serializes all publishes. Even an older rerun is refused
    # after a newer run is issued, including a newer run that failed after uploading.
    if (latest['run_number'], latest['run_attempt']) > (c['run_number'], c['attempt']) or main_sha != c['sha']:
        raise Superseded('A newer main revision or workflow run supersedes this edition')
    return producer

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

def request(url, token=None, redirect=False):
    headers = {'Accept':'application/json', 'User-Agent':'Ledger-static-publisher'}
    if url.startswith('https://api.github.com/'):
        headers['X-GitHub-Api-Version'] = '2022-11-28'
    if token: headers['Authorization'] = 'Bearer ' + token
    opener = urllib.request.build_opener() if redirect else urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(urllib.request.Request(url, headers=headers), timeout=45) as response:
            data = response.read(MAX_BYTES + 1)
            require(len(data) <= MAX_BYTES, 'Response too large')
            return data
    except urllib.error.HTTPError as error:
        if error.code == 302 and not redirect:
            location = error.headers.get('Location', '')
            require(location.startswith('https://'), 'Unsafe artifact download redirect')
            # Never forward the GitHub bearer token to blob storage.
            return request(location, redirect=True)
        raise InvalidEvidence('Provider request failed with HTTP ' + str(error.code)) from None

def github(endpoint):
    token = os.environ.get('GITHUB_TOKEN')
    require(bool(token), 'GitHub read token is required')
    return json.loads(request('https://api.github.com/repos/' + REPO + endpoint, token))

def evidence(c):
    run = github('/actions/runs/' + str(c['run_id']))
    jobs = github('/actions/runs/' + str(c['run_id']) + '/attempts/' + str(c['attempt']) + '/jobs?per_page=100')['jobs']
    artifact = github('/actions/artifacts/' + str(c['artifact_id']))
    runs = github('/actions/workflows/pages.yml/runs?branch=main&per_page=100')['workflow_runs']
    require(bool(runs), 'No current main run')
    latest = max(runs, key=lambda r:(r['run_number'],r['run_attempt']))
    main_sha = github('/git/ref/heads/main')['object']['sha']
    producer = validate_provenance(c, run, jobs, artifact, latest, main_sha)
    return artifact, producer

def unpack(data, digest, destination):
    require('sha256:' + sha(data) == digest, 'Archive checksum mismatch')
    require(not destination.exists(), 'Refusing to overwrite an existing asset directory')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        require(len(entries) == 1 and entries[0].filename == 'artifact.tar', 'Expected only the Pages artifact.tar')
        require(entries[0].file_size <= MAX_BYTES, 'Expanded tar too large')
        raw = archive.read(entries[0])
    files = {}; seen = set(); total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:*') as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            require(not name.is_absolute() and '..' not in name.parts and '\\' not in member.name and ':' not in member.name, 'Unsafe archive path')
            require(member.isdir() or member.isfile(), 'Archive links/devices are forbidden')
            if member.isdir(): continue
            key = str(name)
            require(key != '.' and key.casefold() not in seen and 0 <= member.size <= 25 * 1024 * 1024, 'Duplicate or oversized asset')
            seen.add(key.casefold())
            require(not any(p.startswith('.') and p != '.nojekyll' for p in name.parts), 'Unexpected hidden asset')
            total += member.size
            require(total <= MAX_BYTES and len(files) < 19999, 'Asset budget exceeded')
            files[key] = archive.extractfile(member).read()
    require('_headers' not in files and '_redirects' not in files and '_worker.js' not in files, 'Untrusted platform configuration in source artifact')
    validate_static_files(files)
    destination.mkdir(parents=True)
    for name, body in files.items():
        target = destination / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(body)
    return {name: sha(body) for name, body in files.items()}

def validate_static_files(files):
    # Same application assets required by check_site.sh, plus the mandatory feed.
    # upload-pages-artifact excludes .nojekyll; Cloudflare does not use that marker.
    required = {'index.html','404.html','content.js','sources.js','topics.js','context.js','about.js',
                'analytics.js','media.js','production.js','sw.js','manifest.webmanifest','data/feed.json',
                'icon-180.png','icon-192.png','icon-512.png','icon-maskable-512.png',
                'sitemap.xml','sitemap-news.xml','feed.xml','robots.txt','about/index.html'}
    require(required <= files.keys(), 'Incomplete Pages artifact or missing gathered feed')
    require(not any(n.endswith(('.py','.mjs','.toml','.yml','.yaml','.env')) for n in files), 'Non-static/private build files in artifact')
    require(re.search(rb'^const BUILD = "[0-9a-f]{8}";', files['sw.js'], re.M), 'Unstamped service worker')
    require(re.search(rb'^const ROUTES = \[.*"/story/[^\"]+/".*\];', files['sw.js'], re.M), 'Missing offline story routes')
    require(any(n.startswith('story/') and n.endswith('/index.html') for n in files), 'Missing story pages')
    sitemap = ET.fromstring(files['sitemap.xml'])
    locations = [n.text for n in sitemap.iter() if n.tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}loc']
    require(bool(locations), 'Empty sitemap')
    origin = 'https://readtheledger.github.io/'
    for location in locations:
        require(location and location.startswith(origin) and location.endswith('/'), 'Unexpected sitemap address')
        require(location[len(origin):] + 'index.html' in files, 'Sitemap page missing from artifact')
    feed = json.loads(files['data/feed.json'])
    require(isinstance(feed.get('items'),list) and len(feed['items']) > 0 and isinstance(feed.get('sources'),list), 'Invalid gathered edition')
    stamp(feed['fetched'])
    for name, body in files.items():
        if name.startswith('story/') and name.endswith('/index.html'):
            expected = ('<link rel="canonical" href="https://readtheledger.github.io/' + name[:-10] + '">').encode()
            require(expected in body, 'Story canonical changed before migration')
    require(re.search(rb'const GC_SITE\s*=\s*[\'"][\'"]', files['index.html']), 'Collection must remain off for the test target')
    return feed

def output(name, value):
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as file: file.write(name + '=' + value + '\n')

def prepare():
    c = context(); artifact, producer = evidence(c)
    checkout = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    require(checkout == c['sha'], 'Checkout does not match producer commit')
    data = request('https://api.github.com/repos/' + REPO + '/actions/artifacts/' + str(c['artifact_id']) + '/zip', os.environ['GITHUB_TOKEN'], redirect=False)
    manifest = unpack(data, artifact['digest'], SITE)
    feed = json.loads((SITE/'data/feed.json').read_text(encoding='utf-8'))
    require(stamp(producer['started_at']) - timedelta(seconds=60) <= stamp(feed['fetched']) <= stamp(producer['completed_at']) + timedelta(seconds=60), 'Feed collection time does not belong to the producer job')
    headers = (ROOT/'.github/cloudflare/_headers').read_bytes()
    (SITE/'_headers').write_bytes(headers); manifest['_headers'] = sha(headers)
    record = {'context':c, 'artifact_digest':artifact['digest'], 'producer_job_id':producer['id'], 'feed_fetched':feed['fetched'], 'feed_items':len(feed['items']), 'files':manifest}
    RECEIPT.parent.mkdir(parents=True,exist_ok=True); RECEIPT.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    output('eligible','true')
    print(json.dumps({k:v for k,v in record.items() if k != 'files'}))

def deploy():
    c = context(); artifact, _ = evidence(c)
    record = json.loads(RECEIPT.read_text(encoding='utf-8'))
    require(record['context'] == c and record['artifact_digest'] == artifact['digest'], 'Prepared receipt does not match current evidence')
    require(not SITE.is_symlink() and not any(p.is_symlink() for p in SITE.rglob('*')), 'Prepared assets contain a link')
    actual = {p.relative_to(SITE).as_posix():sha(p.read_bytes()) for p in SITE.rglob('*') if p.is_file()}
    require(actual == record['files'], 'Prepared asset bytes changed')
    config = json.loads((ROOT/'.github/cloudflare/wrangler.json').read_text())
    require(config == {'name':'ledger-static-preview','compatibility_date':'2026-09-12','workers_dev':True,'preview_urls':False,'send_metrics':False,'assets':{'directory':'../../_cloudflare_site','not_found_handling':'404-page','html_handling':'auto-trailing-slash'}}, 'Only the free static preview configuration is allowed')
    require(bool(os.environ.get('CLOUDFLARE_API_TOKEN')) and bool(os.environ.get('CLOUDFLARE_ACCOUNT_ID')), 'Configure CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID repository secrets; never export local OAuth credentials')
    message = f"Pages run {c['run_id']} attempt {c['attempt']}; artifact {c['artifact_id']}; gathered {record['feed_fetched']}"
    # Wrangler does not need the GitHub token. Do not print its raw provider output.
    child_env = {k:v for k,v in os.environ.items() if k not in {'GITHUB_TOKEN','GH_TOKEN'}}
    result = subprocess.run(['node',str(ROOT/'.github/cloudflare/node_modules/wrangler/bin/wrangler.js'),'deploy','--config',str(ROOT/'.github/cloudflare/wrangler.json'),'--message',message], cwd=ROOT, env=child_env, capture_output=True, text=True, timeout=300)
    require(result.returncode == 0, 'Wrangler deployment failed; inspect provider status and token scope (raw output withheld)')
    # Provider receipts remain available even when an independent web reader cannot fetch the preview.
    account = os.environ['CLOUDFLARE_ACCOUNT_ID']
    endpoint = 'https://api.cloudflare.com/client/v4/accounts/' + account + '/workers/scripts/ledger-static-preview/deployments'
    data = json.loads(request(endpoint, os.environ['CLOUDFLARE_API_TOKEN']))
    require(data.get('success'), 'Deployment receipt lookup failed')
    deployments = data['result']['deployments'] if isinstance(data['result'],dict) else data['result']
    require(bool(deployments), 'No deployment receipt returned')
    latest = max(deployments,key=lambda d:d['created_on'])
    require(len(latest['versions']) == 1 and latest['versions'][0]['percentage'] == 100, 'Expected one version serving 100 percent')
    version_id = latest['versions'][0]['version_id']
    require(bool(re.fullmatch(r'[0-9a-f-]{36}', version_id)), 'Invalid provider version ID')
    version = json.loads(request(endpoint.rsplit('/',1)[0] + '/versions/' + version_id, os.environ['CLOUDFLARE_API_TOKEN']))
    require(version.get('success') and version['result']['id'] == version_id and version['result'].get('annotations',{}).get('workers/message') == message, 'Provider version does not match this edition')
    receipt = {'pages_run':c['run_id'],'artifact':c['artifact_id'],'artifact_digest':artifact['digest'],'feed_fetched':record['feed_fetched'],'deployment_created_on':latest['created_on'],'versions':latest['versions'],'public_runtime_verified':False}
    print(json.dumps(receipt))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as file:
            file.write('Cloudflare static preview published from the exact validated Pages artifact.\n\n```json\n'+json.dumps(receipt,indent=2)+'\n```\nPublic-runtime verification is separate; this receipt does not establish it.\n')

if __name__ == '__main__':
    try:
        {'prepare':prepare,'deploy':deploy}[sys.argv[1]]()
    except Superseded as error:
        output('eligible','false'); print('Skipped: ' + str(error))
    except (InvalidEvidence, urllib.error.URLError, KeyError, ValueError, TypeError, AttributeError, OSError, subprocess.SubprocessError, zipfile.BadZipFile, tarfile.TarError, ET.ParseError) as error:
        # Avoid printing provider URLs, credential-bearing requests or arbitrary API response bodies.
        print('Cloudflare publish failed: ' + (str(error) if isinstance(error,InvalidEvidence) else type(error).__name__),file=sys.stderr)
        sys.exit(1)
