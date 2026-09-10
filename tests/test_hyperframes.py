import json
import threading
import time
import zipfile
from pathlib import Path

import pytest

from app import hyperframes as hf, server
from app.media import prepare
from app.models import Brief
from app.process import run


def fixture_video(folder, *, color=None):
    path=folder/'input.mp4'
    pattern=f'color=c={color}:s=160x90:r=30000/1001:d=0.4' if color else 'testsrc2=s=160x90:r=30000/1001:d=0.4'
    run(['ffmpeg','-y','-v','error','-f','lavfi','-i',pattern,'-f','lavfi','-i','sine=frequency=600:duration=0.5',
         '-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(path)])
    return path


def test_hyperframes_renders_every_frame_and_preserves_full_audio(tmp_path):
    """Real browser renderer, fractional fps, motion and audio longer than video."""
    if not hf.CLI.exists():pytest.skip('Install pinned HyperFrames dependencies for integration test.')
    stop=threading.Event()
    prepare(fixture_video(tmp_path),tmp_path,stop,lambda *a:None,faithful=True)
    output=hf.render(tmp_path,Brief(mode="faithful"),stop,lambda *a:None)
    report=json.loads((tmp_path/'verification.json').read_text())
    assert report['actual_frames']==report['compared_frames']==12
    assert report['audio_bitstream_match'] is True
    assert report['visual_check']=='passed' and report['ssim_min']>=.97
    assert hf.frame_info(output)[1]=='30000/1001'
    with zipfile.ZipFile(hf.export_project(tmp_path)) as archive:
        assert {'assets/source.mp4','index.html','manifest.json','vendor/gsap.min.js'}<=set(archive.namelist())
        assert json.loads(archive.read('manifest.json'))['source_backed'] is True
    hf.write_project(tmp_path,Brief(mode="faithful",keep_audio=False))
    assert '<audio' not in (tmp_path/'hyperframes/index.html').read_text()


def test_bad_visual_match_is_rejected_even_with_correct_media_properties(tmp_path):
    good=fixture_video(tmp_path,color='red')
    source=tmp_path/'source.mp4';good.replace(source)
    bad=fixture_video(tmp_path,color='blue')
    with pytest.raises(ValueError,match='did not match'):
        hf.verify(source,bad,tmp_path,Brief(mode="faithful"),threading.Event())


def test_faithful_pipeline_never_calls_ai_or_legacy_renderer(tmp_path,monkeypatch):
    ident='b'*12;folder=tmp_path/ident;folder.mkdir()
    (folder/'source.mp4').write_bytes(b'fixture')
    (folder/'media.json').write_text('{}')
    job=dict(id=ident,name='Reference',brief=Brief(mode="faithful").model_dump(),stage='Queued',events=[],status='queued',
             created=time.time(),cancel=threading.Event())
    monkeypatch.setattr(server,'DATA',tmp_path)
    monkeypatch.setattr(server,'JOBS',{ident:job})
    monkeypatch.setattr(server,'ACTIVE',{'id':ident})
    def forbidden(*args,**kwargs):raise AssertionError('Faithful mode must not invoke AI or legacy rendering')
    monkeypatch.setattr(server,'analyze',forbidden)
    monkeypatch.setattr(server,'render',forbidden)
    monkeypatch.setattr('app.media.thumbnail',lambda *a:None)
    monkeypatch.setattr(hf,'render',lambda *args:(folder/'output.mp4').write_bytes(b'verified fixture'))
    server.pipeline(ident)
    assert job['status']=='complete' and job['renderer']=='hyperframes'
    assert server.ACTIVE['id'] is None
    assert not (folder/'plan.json').exists()


def test_fidelity_failure_preserves_previous_output_and_sets_error(tmp_path,monkeypatch):
    ident='c'*12;folder=tmp_path/ident;folder.mkdir()
    (folder/'source.mp4').write_bytes(b'fixture')
    (folder/'output.mp4').write_bytes(b'previous good output')
    (folder/'media.json').write_text('{}')
    job=dict(id=ident,name='Reference',brief=Brief(mode="faithful").model_dump(),stage='Queued',events=[],status='queued',
             created=time.time(),cancel=threading.Event())
    monkeypatch.setattr(server,'DATA',tmp_path);monkeypatch.setattr(server,'JOBS',{ident:job})
    monkeypatch.setattr(server,'ACTIVE',{'id':ident})
    def fail(*args):raise ValueError('Visual comparison failed')
    monkeypatch.setattr(hf,'render',fail)
    server.pipeline(ident)
    assert job['status']=='error' and 'Visual comparison' in job['error']
    assert (folder/'output.mp4').read_bytes()==b'previous good output'


def test_wrong_frame_count_is_rejected(tmp_path):
    source=fixture_video(tmp_path)
    short=tmp_path/'short.mp4'
    run(['ffmpeg','-y','-v','error','-i',str(source),'-frames:v','1','-c','copy',str(short)])
    with pytest.raises(ValueError,match='Frame count'):
        hf.verify(source,short,tmp_path,Brief(mode="faithful"),threading.Event())


def test_finished_cli_cannot_stall_on_idle_node_handles(tmp_path,monkeypatch):
    stub=tmp_path/'finished.mjs'
    stub.write_text("console.log('Render complete'); console.log('12 frames · rendered in 1s'); setInterval(()=>{},1000);",encoding='utf-8')
    monkeypatch.setattr(hf,'CLI',stub)
    started=time.monotonic()
    hf.run_cli(['render'],tmp_path,threading.Event())
    assert time.monotonic()-started<5
