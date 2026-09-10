import threading
import json
from app.media import prepare
from app.process import run


def test_variable_frame_rate_normalizes_automatically(tmp_path):
    source=tmp_path/'variable.mkv'
    run(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=s=160x90:r=20:d=1',
        '-vf',r'setpts=if(lt(N\,10)\,N/10/TB\,(1+(N-10)/20)/TB)','-fps_mode','vfr','-c:v','ffv1',str(source)])
    meta,_=prepare(source,tmp_path,threading.Event(),lambda *a:None,rebuild=True)
    assert any('Variable frame timing' in s for s in meta['normalizations'])
    frames=json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(tmp_path/'source.mp4')]))['frames']
    times=[float(x['best_effort_timestamp_time']) for x in frames]
    deltas=[b-a for a,b in zip(times,times[1:])]
    assert max(deltas)-min(deltas)<.001


def test_hdr_is_tone_mapped_for_browser_playback(tmp_path):
    source=tmp_path/'hdr.mkv'
    run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=c=gray:s=160x90:r=15:d=0.3',
        '-vf','format=yuv420p10le,setparams=color_primaries=bt2020:color_trc=smpte2084:colorspace=bt2020nc',
        '-pix_fmt','yuv420p10le','-c:v','libx265','-preset','ultrafast','-x265-params','log-level=error:colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc',
        '-color_trc','smpte2084','-color_primaries','bt2020','-colorspace','bt2020nc',str(source)])
    meta,_=prepare(source,tmp_path,threading.Event(),lambda *a:None,rebuild=True)
    assert any('HDR converted to SDR' in s for s in meta['normalizations'])
    stream=json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-of','json',str(tmp_path/'source.mp4')]))['streams'][0]
    assert stream['pix_fmt']=='yuv420p' and stream.get('color_transfer')!='smpte2084'
