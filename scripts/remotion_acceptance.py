"""Render saved motion with audio off/on and verify an independent exported project."""
import json
import shutil
import sys
import threading
import time
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.models import Brief, Plan
from app.remotion import render, export_project
from app.media import probe, thumbnail
from app.process import run

root=Path(__file__).resolve().parents[1]
folder=root/'test-results/remotion-acceptance'
plan=Plan.model_validate_json((folder/'plan.json').read_text())
brief=Brief.model_validate_json((folder/'brief.json').read_text())
report={}
for audio in (False,True):
    brief.keep_audio=audio
    started=time.monotonic()
    result=render(folder,plan,brief,threading.Event(),lambda *args:None)
    report['with_audio' if audio else 'muted']={
        'seconds':round(time.monotonic()-started,2),
        'verification':json.loads((folder/'verification.json').read_text())}
    thumbnail(result,folder/('with-audio.jpg' if audio else 'muted.jpg'))
exported=export_project(folder,plan,brief)
dest=root/'test-results/remotion-export-independent';dest.mkdir(exist_ok=True)
with zipfile.ZipFile(exported) as archive:archive.extractall(dest)
print(json.dumps(report,indent=2),flush=True)
(folder/'acceptance.json').write_text(json.dumps(report,indent=2))
print('EXPORTED',dest,flush=True)
