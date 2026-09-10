"""Live ChatGPT acceptance test for source-free reconstruction (consumes plan allowance)."""
import sys
import threading
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from app.ai import analyze
from app.media import prepare, contact_sheets
from app.models import Brief
from app.render import render
folder=root/'test-results/rebuild';folder.mkdir(exist_ok=True)
stop=threading.Event()
def progress(stage,pct):print(f'{pct}% {stage}',flush=True)
meta,sheets=prepare(root/'test-results/reference.mp4',folder,stop,progress)
brief=Brief(brand='KAI STUDIO',mode='rebuild',keep_audio=False,auto_review=False,
            instructions='Recreate the reference design and motion from editable layers. Use KAI STUDIO for the heading and Made to move. for the subtitle. Reconstruct the green background, rounded border, moving circle and growing underline. Do not use source frames.')
plan=analyze(folder,meta,brief,sheets,stop,progress)
(folder/'plan.json').write_text(plan.model_dump_json(indent=2),encoding='utf-8')
(folder/'brief.json').write_text(brief.model_dump_json(indent=2),encoding='utf-8')
render(folder,plan,brief,stop,progress)
contact_sheets(folder/'output.mp4',folder/'result',8)
assert any(t.kind=='text' and 'KAI' in t.text for t in plan.tracks)
assert len(plan.tracks)>=4
print('Live ChatGPT reconstruction complete:',folder/'output.mp4',flush=True)
