"""Browser regression checks for recovery and SVG assets. Does not run AI."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import time

OUT=Path('test-results/final-ui');OUT.mkdir(parents=True,exist_ok=True)
job=dict(id='aaaaaaaaaaaa',name='Example motion',created=time.time(),started=time.time(),
    status='running',stage='Scenes rebuilt: 2/4',progress=35,files={},events=[],url='https://x.com/example/status/123',
    brief=dict(brand='',instructions='',accent='#6953cc',mode='hyperframes',keep_audio=True,auto_review=False,sampling='standard'))
state=dict(chatgpt=True,online=True,cancels=0)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome');page=browser.new_page(viewport={'width':1440,'height':900})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def route(r):
        path=r.request.url.split('/api/',1)[1]
        if not state['online']:r.abort();return
        if path=='status':r.fulfill(json=dict(token='fixture',chatgpt=state['chatgpt'],ffmpeg=True,hyperframes=True,active=job['id'] if job['status']=='running' else None))
        elif path in ['library','jobs']:r.fulfill(json=[job])
        elif path.endswith('/cancel'):state['cancels']+=1;r.fulfill(json={'ok':True})
        else:r.fulfill(json=job)
    page.route('**/api/**',route)
    page.goto('http://127.0.0.1:4319/?workspace=1',wait_until='networkidle')
    expect(page.locator('#source-summary')).to_contain_text(job['url'])
    expect(page.locator('#create-form')).to_be_hidden()
    expect(page.locator('#viewer-tabs')).to_be_hidden()
    expect(page.locator('#job-stage')).to_contain_text('2/4')
    page.locator('#open-library').click();expect(page.locator('#active-project')).to_be_visible()
    page.locator('#active-project').click();expect(page.locator('#progress-panel')).to_be_visible()
    page.locator('#cancel').click();expect(page.locator('#cancel')).to_be_disabled()
    page.evaluate("document.getElementById('cancel').dispatchEvent(new Event('click'))")
    assert state['cancels']==1
    job.update(status='cancelled',stage='Cancelled. Your project is saved.')
    page.evaluate('poll()');expect(page.locator('#job-error-title')).to_have_text('Rebuild cancelled')
    page.locator('#choose-video').click();expect(page.locator('#create')).to_be_enabled()
    assert 'project=' not in page.url
    state['chatgpt']=False;page.locator('#refresh-auth').click()
    expect(page.locator('#connection')).to_have_text('Sign in needed')
    expect(page.locator('#auth-help')).to_be_visible()
    state['online']=False;page.evaluate('status()');expect(page.locator('#connection-notice')).to_be_visible()
    state.update(online=True,chatgpt=True);page.evaluate('status()');expect(page.locator('#connection-notice')).to_be_hidden()
    expect(page.locator('#connection')).to_have_text('Ready')
    for width in [320,390,768,1024,1440]:
        page.set_viewport_size({'width':width,'height':900})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
        expect(page.locator('.coffee-link')).to_be_visible()
        assert page.locator('.coffee-link').get_attribute('href')=='https://buymeacoffee.com/blix'
        page.screenshot(path=str(OUT/f'checked-{width}.png'))
    assert page.locator('.icon use').count()>15
    assert page.evaluate("[...document.images].filter(i=>i.offsetParent!==null).every(i=>i.complete&&i.naturalWidth>0)")
    for name in ['empty','search','upload','processing','error','success']:
        response=page.request.get(f'http://127.0.0.1:4319/static/assets/illustration-{name}.svg')
        assert response.ok and b'<svg' in response.body()
    assert not errors,errors
    browser.close()
print('PASS: cancellation, saved progress, active navigation, source replacement, sign-in, reconnect and SVG assets')
