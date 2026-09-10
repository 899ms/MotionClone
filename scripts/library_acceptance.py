"""Real browser workflow against isolated project data; never changes existing user projects."""
import json
import os
import sys
import time
import threading
from pathlib import Path
import uvicorn
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import server
from app.models import Brief, Plan, Track

out=Path('test-results/library-acceptance').resolve();out.mkdir(parents=True,exist_ok=True)
server.DATA=out/'data';server.DATA.mkdir(exist_ok=True)
server.JOBS={};server.ACTIVE={'id':None};server.PORT=4321
server.AUTH.update(ok=True,checked=time.monotonic()+3600)
ident='b'*12;folder=server.DATA/ident;folder.mkdir(exist_ok=True)
plan=Plan(title='Orbit',tracks=[Track(id='headline',kind='text',text='Orbit')])
(folder/'plan.json').write_text(plan.model_dump_json())
(folder/'media.json').write_text(json.dumps(dict(width=320,height=180,fps=24,duration=2,audio=False)))
(folder/'temporal.json').write_text(json.dumps({'decoded_frames':48,'sample_frames':[0,12,24,47]}))
job=dict(id=ident,name='Orbit',created=time.time(),status='complete',stage='Ready',progress=100,
    brief=Brief(mode='rebuild').model_dump(),events=[],error=None,cancel=threading.Event())
server.JOBS[ident]=job;server.persist(job)
config=uvicorn.Config(server.app,host='127.0.0.1',port=4321,log_level='error')
host=uvicorn.Server(config);thread=threading.Thread(target=host.run,daemon=True);thread.start()
for _ in range(100):
    if host.started:break
    time.sleep(.05)
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome')
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:4321/?workspace=1',wait_until='networkidle')
        expect(page.locator('#url')).to_be_visible()
        expect(page.locator('#project-options')).not_to_have_attribute('open', '')
        page.locator('#open-library').click()
        expect(page.locator('#library-grid .motion-card')).to_have_count(1)
        page.locator('#library-search').fill('missing reference')
        expect(page.locator('#library-empty')).to_be_visible()
        page.screenshot(path=str(out/'empty-search.png'),full_page=True)
        page.locator('#library-search').fill('orbit')
        page.locator('#library-grid').get_by_role('button',name='Open project').click()
        expect(page.locator('#editor-view')).to_be_visible()
        page.locator('#library-details > summary').click()
        page.locator('#saved-name').fill('Orbit title')
        page.locator('#saved-collection').fill('Launches')
        page.locator('#saved-tags').fill('Type, UI')
        page.locator('#save-details').click()
        expect(page.locator('#saved-notice')).to_have_text('Details saved.')
        page.locator('#favorite').click()
        expect(page.locator('#favorite')).to_have_text('★ Favorited')
        page.locator('#duplicate').click()
        expect(page.locator('#editor-title')).to_have_text('Orbit title copy')
        expect(page.locator('#copy-fields input')).to_have_value('Orbit')
        expect(page.locator('#editor-kind')).to_have_text('SAVED VARIATION')
        page.screenshot(path=str(out/'draft-wide.png'),full_page=True)
        copy_id=page.evaluate('current.id')
        page.locator('#archive').click()
        expect(page.locator('#library-view')).to_be_visible()
        expect(page.locator('#library-grid .motion-card')).to_have_count(1)
        page.locator('#library-options > summary').click()
        page.locator('[data-filter=archived]').click()
        expect(page.locator('#library-grid .card-title')).to_have_text('Orbit title copy')
        page.locator('#library-grid .card-open').click()
        page.locator('#archive').click()
        page.locator('[data-filter=all]').click()
        expect(page.locator('#library-grid .motion-card')).to_have_count(2)
        page.locator('#collection-filter').select_option('Launches')
        expect(page.locator('#library-grid .motion-card')).to_have_count(2)
        page.locator('[data-filter=favorites]').click()
        expect(page.locator('#library-grid .motion-card')).to_have_count(1)
        page.reload(wait_until='networkidle')
        page.locator('#open-library').click()
        expect(page.locator('#library-grid .motion-card')).to_have_count(2)
        page.locator('#add-reference').click()
        expect(page.locator('#editor-title')).to_have_text('Recreate an X video.')
        expect(page.locator('[name=mode][value=rebuild]')).to_be_checked()
        expect(page.locator('#sampling')).to_have_value('standard')
        for width in [320,768,1024,1440]:
            page.set_viewport_size({'width':width,'height':1000})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(out/f'import-{width}.png'),full_page=True)
        page.locator('#project-options > summary').click()
        for selector in ['#brand','#accent','#instructions','#logo','#sampling','#keep-audio','#auto-review','[name=mode]']:
            for control in page.locator(selector).all():
                expect(control).to_be_visible()
        page.set_viewport_size({'width':320,'height':1000})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(out/'options-320.png'),full_page=True)
        page.locator('#create').click()
        expect(page.locator('#import-error')).to_contain_text('Paste a video link')
        page.locator('#open-library').click()
        page.set_viewport_size({'width':1440,'height':1000})
        for state in ['running','error','interrupted']:
            server.JOBS[copy_id].update(status=state,progress=35,stage='Mapping motion' if state=='running' else 'Needs attention',error='Example connection error' if state=='error' else None)
            page.reload(wait_until='networkidle')
            page.locator('#open-library').click()
            page.locator('#library-grid').get_by_role('button',name='Orbit title copy',exact=True).click()
            expect(page.locator('#progress-panel' if state=='running' else '#job-error')).to_be_visible()
            page.screenshot(path=str(out/f'state-{state}.png'),full_page=True)
        assert not errors,errors
        browser.close()
    print('PASS: metadata, search, favorites, collections, copy, archive/restore, reload, import widths, running/error/interrupted states; no JS errors')
finally:
    host.should_exit=True;thread.join(timeout=5)
