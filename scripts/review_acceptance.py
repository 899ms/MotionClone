"""Exercise the incremental visual review using a real ChatGPT session."""
import sys,json,threading
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from app.ai import analyze
from app.media import contact_sheets
from app.models import Brief, Plan
from app.render import render
folder=root/'test-results/rebuild'
meta=json.loads((folder/'media.json').read_text(encoding='utf-8'))
brief=Brief.model_validate_json((folder/'brief.json').read_text(encoding='utf-8'))
previous=Plan.model_validate_json((folder/'plan.json').read_text(encoding='utf-8'))
rendered=contact_sheets(folder/'output.mp4',folder/'rendered',16)
stop=threading.Event()
def progress(stage,pct):print(pct,stage,flush=True)
plan=analyze(folder,meta,brief,sorted(folder.glob('reference-*.jpg'))+rendered,stop,progress,previous=previous,review=True)
(folder/'plan.json').write_text(plan.model_dump_json(indent=2),encoding='utf-8')
render(folder,plan,brief,stop,progress)
print('Incremental visual-review acceptance passed',flush=True)
