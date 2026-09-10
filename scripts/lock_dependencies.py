from pathlib import Path
import importlib.metadata as md
from packaging.requirements import Requirement
root=Path(__file__).resolve().parents[1]
names=set()
def visit(name):
    d=md.distribution(name);key=d.metadata['Name'].lower().replace('_','-')
    if key in names:return
    names.add(key)
    for spec in d.requires or []:
        r=Requirement(spec)
        if r.marker is None or r.marker.evaluate({'extra':''}):visit(r.name)
for line in (root/'requirements.txt').read_text(encoding='utf-8').splitlines():
    if line and not line.startswith('#'):visit(line.split('==')[0])
(root/'requirements.lock.txt').write_text('\n'.join(sorted(f'{md.distribution(n).metadata["Name"]}=={md.version(n)}' for n in names))+'\n',encoding='utf-8')
(root/'.venv/frameforge-ready').touch()
