"""Bounded background recording exports; the saved reconstruction stays unchanged."""
import json
import re
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException
from fastapi.responses import FileResponse

from .recording_export import RecordingOptions, cached, fingerprint, render


def install(app, data, get_job, port):
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='recording-export')
    lock = threading.RLock()
    exports = {}

    def present(value):
        return {key: value[key] for key in ('key', 'status', 'stage', 'progress', 'error', 'url', 'settings')}

    def work(project, key, options):
        item = exports[(project, key)]
        folder = data / project
        target = folder / 'recordings' / key
        def progress(stage, percent):
            with lock:
                item.update(status='running', stage=stage, progress=percent)
        try:
            report = render(folder, target, options, port, progress)
            if fingerprint(folder, options) != key:
                (target / 'verification.json').unlink(missing_ok=True)
                raise ValueError('The video or recording design changed during export. Download again to use the latest version.')
            with lock:
                item.update(status='complete', stage='Recording MP4 ready', progress=100, verification=report)
        except Exception as exc:
            target.mkdir(parents=True, exist_ok=True)
            (target / 'error.log').write_text(traceback.format_exc(), encoding='utf-8')
            with lock:
                item.update(status='error', stage='Export needs attention', error=str(exc) if isinstance(exc, (ValueError, TimeoutError)) else 'Recording export failed. Retry the download; details are saved locally.')

    @app.post('/api/jobs/{id}/recording')
    def create_recording(id: str, options: RecordingOptions):
        job = get_job(id)
        folder = data / id
        if job['status'] != 'complete' or not all((folder / name).is_file() for name in ('source.mp4', 'output.mp4')):
            raise HTTPException(409, 'Finish rebuilding this video before downloading its recording view.')
        key = fingerprint(folder, options)
        target = folder / 'recordings' / key
        with lock:
            prior = exports.get((id, key))
            if prior and prior['status'] in ('queued', 'running'):
                return present(prior)
            report = cached(target)
            if not report and any(value['status'] in ('queued', 'running') for value in exports.values()):
                raise HTTPException(409, 'Another recording view is exporting. Wait for it to finish, then download this version.')
            value = dict(key=key, status='complete' if report else 'queued', stage='Recording MP4 ready' if report else 'Preparing recording export',
                         progress=100 if report else 0, error=None, settings=options.model_dump(),
                         url=f'/api/jobs/{id}/recording/{key}/download')
            exports[(id, key)] = value
            if not report:
                pool.submit(work, id, key, options)
            return present(value)

    @app.get('/api/jobs/{id}/recording/{key}')
    def recording_status(id: str, key: str):
        get_job(id)
        if not re.fullmatch(r'[a-f0-9]{20}', key):
            raise HTTPException(404, 'Recording export not found.')
        with lock:
            value = exports.get((id, key))
            if value:
                return present(value)
        raise HTTPException(404, 'Recording export was interrupted. Download again to resume.')

    @app.get('/api/jobs/{id}/recording/{key}/download')
    def recording_download(id: str, key: str):
        get_job(id)
        if not re.fullmatch(r'[a-f0-9]{20}', key):
            raise HTTPException(404, 'Recording export not found.')
        folder = data / id / 'recordings' / key
        report = cached(folder)
        if not report:
            raise HTTPException(409, 'This recording export is not ready. Use Download MP4 to create it.')
        settings = report['settings']
        name = f'motionclone-{settings["look"]}-{settings["format"]}-{settings["layout"]}.mp4'
        return FileResponse(folder / 'recording.mp4', filename=name, media_type='video/mp4')
