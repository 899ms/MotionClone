"""Validate the faster correction path against the real imported reference."""
import json,sys,shutil,threading
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from app.ai import analyze
from app.media import contact_sheets,review_timestamps
from app.models import Plan,Brief
from app.render import render
source=root/'data'/json.loads((root/'test-results/reference-link-job.json').read_text(encoding='utf-8'))['id']
folder=root/'test-results/corrected-reference';folder.mkdir(exist_ok=True)
for name in ['source.mp4','preview.mp4','media.json','plan.json']:
    shutil.copy2(source/name,folder/name)
for path in source.glob('reference-*.jpg'):shutil.copy2(path,folder/path.name)
meta=json.loads((folder/'media.json').read_text(encoding='utf-8'))
job=json.loads((source/'job.json').read_text(encoding='utf-8'))
brief=Brief.model_validate(job['brief']);prior=Plan.model_validate_json((folder/'plan.json').read_text(encoding='utf-8'))
stop=threading.Event()
def progress(stage,pct):print(pct,stage,flush=True)
render(folder,prior,brief,stop,progress,preview=True)
times=review_timestamps(meta,prior)
review_source=contact_sheets(folder/'source.mp4',folder/'review-source',timestamps=times)
rendered=contact_sheets(folder/'preview.mp4',folder/'rendered',timestamps=times)
plan=analyze(folder,meta,brief,review_source+rendered,stop,progress,previous=prior,review=True)
(folder/'plan.json').write_text(plan.model_dump_json(indent=2),encoding='utf-8')
(folder/'brief.json').write_text(brief.model_dump_json(indent=2),encoding='utf-8')
render(folder,plan,brief,stop,progress)
contact_sheets(folder/'output.mp4',folder/'final',24)
print('Real-reference corrected export completed',flush=True)
