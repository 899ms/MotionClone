import json
import threading
import time
import zipfile
import pytest
from fastapi.testclient import TestClient
from app import server
from app.models import Brief, Plan, Track


@pytest.fixture
def library(tmp_path, monkeypatch):
    monkeypatch.setattr(server, 'DATA', tmp_path)
    monkeypatch.setattr(server, 'JOBS', {})
    monkeypatch.setattr(server, 'ACTIVE', {'id': None})
    ident = 'a' * 12
    folder = tmp_path / ident
    folder.mkdir()
    plan = Plan(title='Orbit', tracks=[Track(id='title', kind='text', text='Orbit')])
    (folder / 'plan.json').write_text(plan.model_dump_json())
    (folder / 'media.json').write_text(json.dumps(dict(width=320, height=180, fps=24, duration=2, audio=False)))
    (folder / 'source.mp4').write_bytes(b'source fixture')
    (folder / 'temporal.json').write_text(json.dumps({'decoded_frames':48,'sample_frames':[0,12,24,47]}))
    server.JOBS[ident] = dict(id=ident, name='Orbit', created=time.time(), status='complete',
        stage='Ready', progress=100, brief=Brief(mode='rebuild').model_dump(), events=[], error=None,
        cancel=threading.Event())
    server.persist(server.JOBS[ident])
    return TestClient(server.app), ident, folder


HEADERS = {'X-Frameforge-Token': server.TOKEN}


def test_library_metadata_persists_and_rejects_unknown_fields(library):
    client, ident, folder = library
    r = client.patch(f'/api/jobs/{ident}', headers=HEADERS,
                     json={'name':'New orbit','favorite':True,'collection':'Launches','tags':['type','3D']})
    assert r.status_code == 200
    saved = json.loads((folder/'job.json').read_text())
    assert saved['favorite'] and saved['collection'] == 'Launches'
    updated=client.patch(f'/api/jobs/{ident}',headers=HEADERS,json={'favorite':False}).json()
    assert updated['collection']=='Launches' and updated['tags']==['type','3D']
    assert client.patch(f'/api/jobs/{ident}',headers=HEADERS,json={'status':'running'}).status_code == 422


def test_duplicate_reuses_analysis_without_changing_original(library):
    client, ident, folder = library
    r = client.post(f'/api/jobs/{ident}/duplicate', headers=HEADERS)
    assert r.status_code == 200
    copy = r.json()
    assert copy['id'] != ident and copy['status'] == 'draft'
    copied = folder.parent / copy['id']
    assert (copied/'temporal.json').read_bytes() == (folder/'temporal.json').read_bytes()
    assert (copied/'plan.json').exists() and not (copied/'output.mp4').exists()
    assert server.ACTIVE['id'] is None
    assert json.loads((folder/'job.json').read_text())['name'] == 'Orbit'


def test_remotion_export_contains_editable_source_and_no_original_video(library):
    client, ident, folder = library
    r = client.get(f'/api/jobs/{ident}/remotion')
    assert r.status_code == 200
    import io
    with zipfile.ZipFile(io.BytesIO(r.content)) as archive:
        assert {'src/Composition.jsx','src/index.jsx','public/project.json','package.json','render.mjs'} <= set(archive.namelist())
        assert 'public/source.mp4' not in archive.namelist()
        assert json.loads(archive.read('public/project.json'))['plan']['tracks'][0]['text'] == 'Orbit'


def test_original_frame_mode_is_not_mislabeled_as_remotion(library):
    client, ident, _ = library
    server.JOBS[ident]['brief']['mode'] = 'adapt'
    assert client.get(f'/api/jobs/{ident}/remotion').status_code == 409


def test_archive_is_reversible(library):
    client, ident, folder = library
    for value in (True, False):
        assert client.patch(f'/api/jobs/{ident}',headers=HEADERS,json={'archived':value}).json()['archived'] is value
    assert (folder/'source.mp4').exists()


def test_render_failure_retry_reuses_saved_plan(library,monkeypatch):
    client,ident,folder=library
    calls=[]
    class Pool:
        def submit(self,*args):calls.append(args)
    monkeypatch.setattr(server,'POOL',Pool())
    job=server.JOBS[ident]
    job.update(status='error',checkpoint='render')
    r=client.post(f'/api/jobs/{ident}/retry',headers=HEADERS,json=job['brief'])
    assert r.status_code==200
    assert calls[0]==(server.pipeline,ident,True)


def test_library_listing_omits_heavy_plans(library):
    client,ident,_=library
    response=client.get('/api/library')
    assert response.status_code==200
    job=response.json()[0]
    assert job['id']==ident and 'plan' not in job
    assert client.get(f'/api/jobs/{ident}').json()['plan']['title']=='Orbit'
