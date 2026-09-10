import numpy as np
import pytest
from app.models import Plan, Track, Keyframe
from app.render import state_at, clear_region
from app.media import validate_url


def test_keyframe_interpolation_and_clamping():
    t = Track(id='title', kind='text', start=0, end=2, text='Hello', keyframes=[
        Keyframe(t=0, x=.1, y=.2), Keyframe(t=2, x=.9, y=.6)])
    assert state_at(t, 1)['x'] == pytest.approx(.5)
    assert state_at(t, -1)['x'] == pytest.approx(.1)
    assert state_at(t, 9)['y'] == pytest.approx(.6)


def test_cleaning_does_not_change_pixels_outside_mask():
    im = np.full((100,100,3), 200, dtype=np.uint8)
    im[30:60,30:70] = 0
    result = clear_region(im.copy(), (30,30,70,60), 'gradient', '#ffffff')
    assert np.all(result == 200)
    assert np.all(im[:30] == result[:30])


@pytest.mark.parametrize('url', ['file:///etc/passwd','http://127.0.0.1/a.mp4','https://localhost/a','https://user:pass@example.com/a','https://[::1]/a'])
def test_reject_local_and_credential_urls(url):
    with pytest.raises(ValueError): validate_url(url)


def test_invalid_plan_rejected():
    with pytest.raises(ValueError): Plan.model_validate({'tracks':[{'id':'x','kind':'script'}]})
    with pytest.raises(ValueError): Track(id='x',kind='text',start=4,end=1)


def test_reconstruction_can_cover_a_full_6153_second_clip():
    track = Track(id='ending', kind='text', start=60, end=61.533,
                  keyframes=[Keyframe(t=60), Keyframe(t=61.533)])
    assert track.end == 61.533
    with pytest.raises(ValueError): Keyframe(t=121)


def test_playlist_upload_cannot_fetch_network_resources(tmp_path):
    from app.media import probe
    path=tmp_path/'input.bin'
    path.write_text('#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXTINF:10,\nhttp://127.0.0.1:9999/secret.ts\n#EXT-X-ENDLIST\n')
    with pytest.raises(ValueError,match='valid MP4'):probe(path)


def test_review_patch_preserves_unmodified_layers_and_their_order():
    from app.models import Review, apply_review
    base=Plan(tracks=[Track(id='background',kind='rect'),Track(id='title',kind='text',text='Old'),Track(id='remove-me',kind='text')])
    patch=Review(summary='Corrected title',observations=[],replace_tracks=[Track(id='title',kind='text',text='New')],
                 replace_masks=[],remove_tracks=['remove-me'],remove_masks=[])
    out=apply_review(base,patch)
    assert [x.id for x in out.tracks]==['background','title']
    assert out.tracks[0]==base.tracks[0]
    assert out.tracks[1].text=='New'
    assert base.tracks[1].text=='Old'


def test_logged_process_captures_unicode_and_errors(tmp_path):
    import sys
    from app.process import run_logged
    inp=tmp_path/'prompt.txt';inp.write_text('KAI – motion',encoding='utf-8')
    prefix=tmp_path/'run'
    run_logged([sys.executable,'-c','import sys;sys.stdout.buffer.write(sys.stdin.buffer.read())'],inp,prefix)
    assert prefix.with_suffix('.stdout.log').read_text(encoding='utf-8')=='KAI – motion'
    with pytest.raises(RuntimeError,match='test failure'):
        run_logged([sys.executable,'-c','import sys;sys.stderr.write("test failure");sys.exit(1)'],inp,prefix)


def test_visual_review_includes_cut_boundaries_at_source_frame_rate():
    from app.media import review_timestamps
    plan=Plan(tracks=[Track(id='cut',kind='text',start=0,end=1.875)])
    times=review_timestamps({'duration':4,'fps':24},plan)
    assert 1.875 in times
    assert 44/24 in times and 46/24 in times
    assert all(0<=t<4 for t in times)
