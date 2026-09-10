"""A short, original reference used for real OAuth + render acceptance tests."""
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parents[1];out=root/'test-results';out.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',68)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',26)
proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','960x540','-r','24','-i','pipe:0',
    '-f','lavfi','-i','sine=frequency=440:duration=4','-t','4','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(out/'reference.mp4')],stdin=subprocess.PIPE)
for i in range(96):
    t=i/24;im=Image.new('RGB',(960,540),'#14231e');d=ImageDraw.Draw(im)
    d.rounded_rectangle((70,70,890,470),radius=25,outline='#426556',width=2)
    d.ellipse((755-25*t,100,825-25*t,170),fill='#a8e8a0')
    x=120+round(35*min(t,1))
    d.text((x,195),'NOVA STUDIO',font=font,fill='#f5f8ef')
    d.text((155,300),'Good ideas. Beautifully moving.',font=small,fill='#b4c8bd')
    d.line((155,360,155+int(620*t/4),360),fill='#a8e8a0',width=4)
    proc.stdin.write(im.tobytes())
proc.stdin.close();proc.wait();assert proc.returncode==0
print(out/'reference.mp4')
