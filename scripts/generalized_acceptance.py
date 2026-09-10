"""Real ChatGPT + HyperFrames acceptance on fresh synthetic references. Explicit opt-in."""
import argparse
import json
import sys
import threading
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.media import prepare,reference_frames
from app.models import Brief
from app.rebuild_author import author
from app.reconstruction import render

parser=argparse.ArgumentParser();parser.add_argument('--run-ai',action='store_true');args=parser.parse_args()
if not args.run_ai:raise SystemExit('Pass --run-ai to use the connected ChatGPT plan for these two test references.')
root=Path('test-results/generalized').resolve();root.mkdir(parents=True,exist_ok=True)
results=[]
for name,w,h in [('landscape',640,360),('portrait',360,640)]:
    folder=root/name;folder.mkdir(exist_ok=True);raw=folder/'fixture.mp4'
    writer=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*'mp4v'),12,(w,h))
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',36)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    for frame in range(48):
        if name=='landscape':
            image=Image.new('RGB',(w,h),'#122038');draw=ImageDraw.Draw(image)
            draw.rounded_rectangle((40,40,600,320),radius=22,fill='#ffffff')
            draw.text((70,68),'Make it move',font=font,fill='#122038')
            draw.text((70,119),'Independent layers',font=small,fill='#546070')
            x=90+frame/47*390;draw.ellipse((x-22,225-22,x+22,225+22),fill='#44cda2')
        else:
            image=Image.new('RGB',(w,h),'#eee7de');draw=ImageDraw.Draw(image)
            draw.rounded_rectangle((30,105,330,535),radius=28,fill='#ed7c35')
            draw.text((62,152),'Launch 07',font=font,fill='#181818')
            draw.text((63,207),'Build. Review. Ship.',font=small,fill='#181818')
            draw.rounded_rectangle((63,421,297,439),radius=9,fill='#b24a1c')
            draw.rounded_rectangle((63,421,63+max(18,234*frame/47),439),radius=9,fill='#fff4cf')
        writer.write(cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR))
    writer.release();stop=threading.Event();started=time.monotonic()
    def progress(stage,pct):print(f'{name}: {pct}% {stage}',flush=True)
    meta,_=prepare(raw,folder,stop,progress,rebuild=True);sheets=reference_frames(folder,stop,progress)
    author(folder,meta,sheets,stop,progress);report=render(folder,Brief(),stop,progress)
    cache_started=time.monotonic();cached=render(folder,Brief(),stop,progress)
    assert cached['cache_hit'] and report['actual_frames']==48 and report['source_backed'] is False
    results.append(dict(name=name,total_seconds=round(time.monotonic()-started,2),cache_seconds=round(time.monotonic()-cache_started,3),
        frames=48,ssim=report['ssim_mean'],minimum=report['ssim_min'],near_perfect=report['near_perfect']))
    (root/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
