"""Real UI checks, including editing/render/download, without mocking the application."""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];out=root/'test-results'
job=json.loads((out/'live-job.json').read_text(encoding='utf-8'))
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome')
    page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:4319/?workspace=1',wait_until='networkidle')
    page.locator('#open-library').click()
    page.locator('#library-grid').get_by_role('button',name='KAI STUDIO').first.click()
    page.locator('#finished').wait_for(state='visible')
    page.locator('#result-video').evaluate('(v)=>new Promise(r=>{if(v.readyState>=2)r();else v.addEventListener("loadeddata",r,{once:true})})')
    page.locator('#result-video').evaluate('(v)=>{v.currentTime=1.5}')
    page.screenshot(path=str(out/'ui-complete.png'),full_page=True)
    page.locator('#compare-tab').click()
    assert page.locator('#source-video').is_visible()
    assert page.locator('#result-video').is_visible()
    page.locator('#result-video').evaluate('(v)=>{v.currentTime=2;v.play()}')
    page.wait_for_timeout(700)
    times=page.evaluate('[document.querySelector("#result-video").currentTime,document.querySelector("#source-video").currentTime]')
    assert abs(times[0]-times[1])<.3,times
    page.locator('#result-video').evaluate('(v)=>v.pause()')
    with page.expect_download() as d:page.locator('#download').click()
    d.value.save_as(out/'downloaded.mp4')
    with page.expect_download() as d:page.locator('#export').click()
    d.value.save_as(out/'downloaded-project.zip')
    # Editing renders the real plan without another model call.
    page.locator('#copy-fields input').first.fill('KAI MOTION')
    page.locator('#rerender').click()
    page.locator('#progress-panel').wait_for(state='visible')
    page.locator('#finished').wait_for(state='visible',timeout=120000)
    assert page.locator('#copy-fields input').first.input_value()=='KAI MOTION'
    page.locator('#new-project').click()
    assert page.locator('#url').is_visible()
    page.screenshot(path=str(out/'ui-empty.png'),full_page=True)
    # Missing input produces an actionable error through the real form/server.
    page.locator('#create').click()
    page.locator('#import-error').wait_for(state='visible')
    assert 'Paste a video link' in page.locator('#import-error').inner_text()
    page.screenshot(path=str(out/'ui-error.png'),full_page=True)
    # Public reference link, entered through the UI, then full analysis/render.
    page.locator('#url').fill('https://github.com/Tejashmakwana/astra-chatgpt-hyperframes/blob/main/reference/original.mp4')
    page.locator('#project-options > summary').click()
    page.locator('#brand').fill('KAI STUDIO')
    page.locator('#instructions').fill('Rebrand this motion-design demo for KAI STUDIO. Replace the main title and product-name text with KAI STUDIO and supporting text with a creative motion studio theme. Keep original blue backgrounds, camera motion, outlines, cursor, and animation. Keep the original soundtrack.')
    page.locator('#create').click()
    page.locator('#progress-panel').wait_for(state='visible',timeout=30000)
    project_id=page.evaluate('localStorage.getItem("frameforge-project")')
    (out/'reference-link-job.json').write_text(json.dumps({'id':project_id}),encoding='utf-8')
    page.screenshot(path=str(out/'ui-link-running.png'),full_page=True)
    assert not errors,errors
    browser.close()
    print('UI checks passed: playback, comparison sync, MP4/ZIP downloads, copy edit/render, empty/error states. Real reference link job:',project_id,flush=True)
