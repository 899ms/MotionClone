"""Render an exported project offline: python render_project.py [project-directory]."""
import json
import sys
import threading
from pathlib import Path
root=Path(__file__).resolve().parent
if (root.parent/'app').is_dir():sys.path.insert(0,str(root.parent))
from app.models import Brief, Plan
from app.render import render
folder=Path(sys.argv[1] if len(sys.argv)>1 else 'project').resolve()
brief=Brief.model_validate_json((folder/'brief.json').read_text(encoding='utf-8'))
if brief.mode=='hyperframes':
    from app.reconstruction import render as render_rebuilt
    render_rebuilt(folder,brief,threading.Event(),lambda stage,pct:print(f'{pct}% {stage}',flush=True))
elif brief.mode=='faithful':
    from app.hyperframes import render as render_faithful
    render_faithful(folder,brief,threading.Event(),lambda stage,pct:print(f'{pct}% {stage}',flush=True))
else:
    render(folder,Plan.model_validate_json((folder/'plan.json').read_text(encoding='utf-8')),
           brief,threading.Event(),lambda stage,pct:print(f'{pct}% {stage}',flush=True))
print(folder/'output.mp4')
