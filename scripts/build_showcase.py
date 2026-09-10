"""Build a portable static project site. Never includes user videos or local data."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'site';OUT.mkdir(exist_ok=True)
shutil.copyfile(ROOT/'web/showcase.html',OUT/'index.html')
for name in ['showcase.css','showcase.js','previews.js']:
    shutil.copyfile(ROOT/'web'/name,OUT/name)
(OUT/'assets').mkdir(exist_ok=True)
for name in ['icons.svg','motionclone-icon-color.svg','buymeacoffee-yellow.png']:
    shutil.copyfile(ROOT/'web/assets'/name,OUT/'assets'/name)
(OUT/'.nojekyll').touch()
print('Static showcase built in site/ (no private media).')
