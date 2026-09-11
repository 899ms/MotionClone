import hashlib
import io
import json
import shutil

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.recording_export import RecordingOptions, cached, encoder_command
from app.hyperframes import frame_info
from app.process import run
from PIL import Image
from app import recording_routes
from app.server import app as server_app


def test_recording_options_only_accept_known_presets_and_no_audio_opt_out():
    for data in ({'look': '../../secrets'}, {'format': '4k'}, {'layout': '<script>'}, {'audio': False}):
        with pytest.raises(ValidationError):
            RecordingOptions.model_validate(data)


def test_recording_cache_rejects_changed_output(tmp_path):
    output = tmp_path / 'recording.mp4'
    output.write_bytes(b'verified-video')
    (tmp_path / 'verification.json').write_text(json.dumps({'verified': True, 'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
    assert cached(tmp_path)
    output.write_bytes(b'corrupted')
    assert cached(tmp_path) is None


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg required')
def test_encoder_preserves_audio_packets_beyond_final_video_frame(tmp_path):
    audio, output = tmp_path / 'audio.m4a', tmp_path / 'recording.mp4'
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1.024', '-c:a', 'aac', str(audio)])
    image = io.BytesIO()
    Image.new('RGB', (64, 64), '#101018').save(image, format='PNG')
    run(encoder_command(audio, output, '30'), input=image.getvalue() * 30)
    assert frame_info(output)[0] == 30
    hashes = [run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-c', 'copy', '-f', 'hash', '-']) for path in (audio, output)]
    assert hashes[0] == hashes[1]


@pytest.fixture
def routes(tmp_path, monkeypatch):
    calls = []
    class Pool:
        def __init__(self, **kwargs): pass
        def submit(self, *args): calls.append(args)
    monkeypatch.setattr(recording_routes, 'ThreadPoolExecutor', Pool)
    monkeypatch.setattr(recording_routes, 'fingerprint', lambda folder, options: ('a' if options.look == 'mono' else 'b') * 20)
    job = {'id': '123456abcdef', 'status': 'complete'}
    folder = tmp_path / job['id']; folder.mkdir()
    (folder / 'source.mp4').write_bytes(b'source')
    (folder / 'output.mp4').write_bytes(b'rebuild')
    app = FastAPI()
    recording_routes.install(app, tmp_path, lambda id: job, 4319)
    return TestClient(app), folder, job, calls


def test_duplicate_export_is_coalesced_and_other_export_cannot_queue_unbounded(routes):
    client, folder, job, calls = routes
    url = f'/api/jobs/{job["id"]}/recording'
    first = client.post(url, json={'look': 'mono'}).json()
    second = client.post(url, json={'look': 'mono'}).json()
    assert first == second and first['status'] == 'queued'
    assert len(calls) == 1
    assert client.post(url, json={'look': 'signal'}).status_code == 409
    assert client.get(first['url']).status_code == 409


def test_export_requires_both_finished_videos(routes):
    client, folder, job, calls = routes
    job['status'] = 'running'
    assert client.post(f'/api/jobs/{job["id"]}/recording', json={}).status_code == 409
    job['status'] = 'complete'; (folder / 'source.mp4').unlink()
    assert client.post(f'/api/jobs/{job["id"]}/recording', json={}).status_code == 409
    assert not calls


def test_verified_recording_can_be_downloaded_after_restart(routes):
    client, folder, job, calls = routes
    target = folder / 'recordings' / ('a' * 20); target.mkdir(parents=True)
    content = b'framed-recording'
    (target / 'recording.mp4').write_bytes(content)
    (target / 'verification.json').write_text(json.dumps({'verified': True, 'settings': {'look': 'mono', 'format': 'landscape', 'layout': 'split'}, 'output_sha256': hashlib.sha256(content).hexdigest()}))
    response = client.get(f'/api/jobs/{job["id"]}/recording/{"a" * 20}/download')
    assert response.status_code == 200 and response.content == content
    assert 'motionclone-mono-landscape-split.mp4' in response.headers['content-disposition']
    assert not calls


def test_export_uses_existing_local_token_boundary():
    client = TestClient(server_app)
    assert client.post('/api/jobs/123456abcdef/recording', json={}).status_code == 403
