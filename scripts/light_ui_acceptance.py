"""Browser acceptance with isolated API fixtures; never starts real AI work."""
import copy
import json
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results/light-ui'
OUT.mkdir(parents=True, exist_ok=True)
media = OUT / 'fixture.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',
                'color=c=0x315dd6:s=320x180:d=1','-c:v','libx264',
                '-pix_fmt','yuv420p',str(media)], check=True)
brief = dict(brand='', instructions='', mode='hyperframes', accent='#b9abff',
             keep_audio=True, auto_review=False, sampling='standard')
jobs = [dict(id=f'{i:012d}', name=f'Video {i}', created=time.time()-i,
             status='complete', stage='Ready', progress=100, brief=brief.copy(),
             files={}, events=[], archived=i == 0, favorite=False, tags=[], collection='')
        for i in range(9)]
active = copy.deepcopy(jobs[1])
pending = []
submissions = []
connected = True

def api_route(route):
    path = route.request.url.split('/api/', 1)[1]
    if path == 'status':
        route.fulfill(json=dict(token='fixture', chatgpt=True, ffmpeg=True, hyperframes=connected))
    elif path == 'library':
        route.fulfill(json=jobs)
    elif path == 'jobs' and route.request.method == 'POST':
        submissions.append(route.request.post_data_buffer)
        pending.append(route)
    elif path.startswith('jobs/'):
        route.fulfill(json=active)
    else:
        route.fulfill(status=404, json={'detail':'Unknown fixture endpoint'})

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome')
    page = browser.new_page(viewport={'width':1440,'height':900})
    page.set_default_timeout(5000)
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.route('**/api/**', api_route)
    page.route('**/fixture.mp4', lambda route: route.fulfill(path=str(media), content_type='video/mp4'))
    page.goto('http://127.0.0.1:4319/?workspace=1', wait_until='networkidle')
    expect(page.get_by_label('Video link', exact=True)).to_be_visible()
    page.locator('#url').focus()
    page.keyboard.press('Tab')
    expect(page.locator('#create')).to_be_focused()
    expect(page.locator('#recent-grid .motion-card')).to_have_count(6)
    expect(page.locator('#recent-grid .card-title').first).to_have_text('Video 1')
    assert 'Video 0' not in page.locator('#recent-grid').inner_text()
    for width, height in [(320,900),(390,844),(768,900),(1024,900),(1440,900)]:
        page.set_viewport_size({'width':width,'height':height})
        for selector in ['#url', '#create']:
            box = page.locator(selector).bounding_box()
            assert box['y'] >= 0 and box['y']+box['height'] <= height, (width, selector, box)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(OUT/f'home-{width}.png'), full_page=True)

    page.locator('#video').set_input_files({'name':'reference.mp4','mimeType':'video/mp4','buffer':b'fixture'})
    expect(page.locator('#filename')).to_have_text('reference.mp4')
    page.locator('#remove-video').click()
    assert page.locator('#video').input_value() == ''
    page.locator('#dropzone').dispatch_event('drop', {
        'dataTransfer': page.evaluate_handle("""() => {
            const transfer = new DataTransfer();
            transfer.items.add(new File(['fixture'], 'dropped.mp4', {type:'video/mp4'}));
            return transfer;
        }""")
    })
    expect(page.locator('#filename')).to_have_text('dropped.mp4')
    page.locator('#url').fill('https://x.com/example/status/123')
    assert page.locator('#video').input_value() == ''

    page.locator('#url').fill('')
    page.locator('#create').click()
    expect(page.locator('#import-error')).to_be_visible()
    assert not submissions
    page.locator('#url').fill('https://x.com/example/status/123')
    page.locator('#url').press('Enter')
    page.wait_for_function("document.querySelector('#create').disabled")
    page.locator('#create-form').dispatch_event('submit')
    page.wait_for_timeout(200)
    assert len(submissions) == 1, 'Duplicate submission reached API'
    assert b'https://x.com/example/status/123' in submissions[0]
    assert b'name="mode"\r\n\r\nhyperframes' in submissions[0]
    active.update(status='running', stage='Mapping motion', progress=35)
    pending.pop().fulfill(json=active)
    expect(page.locator('#progress-panel')).to_be_visible()
    page.screenshot(path=str(OUT/'running.png'), full_page=True)

    active.update(status='error', stage='Download failed', error='This video is unavailable. Try uploading the file.')
    page.evaluate('poll()')
    expect(page.locator('#job-error')).to_contain_text('Try uploading')
    page.screenshot(path=str(OUT/'error.png'), full_page=True)
    jobs[1].update(status='error', error=active['error'])
    page.reload(wait_until='networkidle')
    expect(page.locator('#job-error')).to_contain_text('Try uploading')
    active.update(status='complete', stage='Ready', error=None, progress=100,
                  files={'output.mp4':'/fixture.mp4','source.mp4':'/fixture.mp4'})
    page.evaluate('poll()')
    expect(page.locator('#finished')).to_be_visible()
    expect(page.locator('#download')).to_have_attribute('href','/fixture.mp4')
    expect(page.locator('#hyperframes-export')).to_have_attribute('href',f"/api/jobs/{active['id']}/hyperframes")
    expect(page.locator('#remotion-export')).to_be_hidden()
    expect(page.locator('#edit-panel')).to_be_hidden()
    page.locator('#result-tab').focus()
    page.keyboard.press('End')
    expect(page.locator('#compare-tab')).to_be_focused()
    expect(page.locator('#compare-tab')).to_have_attribute('aria-selected','true')
    expect(page.locator('#source-video')).to_be_visible()
    expect(page.locator('#result-video')).to_be_visible()
    for width in [320,768,1024,1440]:
        page.set_viewport_size({'width':width,'height':900})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(OUT/'complete.png'), full_page=True)

    page.locator('#new-project').click()
    page.locator('#project-options > summary').click()
    expect(page.locator('#keep-audio')).to_be_visible()
    for selector in ['#brand','#accent','#instructions','#logo','#sampling','#auto-review','[name=mode]']:
        for control in page.locator(selector).all():
            expect(control).to_be_hidden()
    page.locator('#video').set_input_files({'name':'upload.mp4','mimeType':'video/mp4','buffer':b'fixture'})
    page.locator('#create').click()
    page.wait_for_timeout(200)
    assert len(submissions) == 2
    assert b'filename="upload.mp4"' in submissions[1] and b'hyperframes' in submissions[1]
    pending.pop().fulfill(status=422, json={'detail':'Fixture upload rejected'})
    expect(page.locator('#import-error')).to_have_text('Fixture upload rejected')
    expect(page.locator('#create')).to_be_enabled()
    page.set_viewport_size({'width':320,'height':900})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(OUT/'options-320.png'), full_page=True)

    page.locator('#new-project').click()
    page.locator('#view-all').click()
    expect(page.locator('#library-view')).to_be_visible()
    page.locator('#library-search').fill('Video 4')
    expect(page.locator('#library-grid .motion-card')).to_have_count(1)
    page.locator('#new-project').click()
    jobs.clear()
    page.evaluate('refreshLibrary()')
    expect(page.locator('#recent-empty')).to_be_visible()
    connected = False
    page.locator('#refresh-auth').click()
    expect(page.locator('#connection')).to_have_text('Setup needed')
    expect(page.locator('#auth-help')).to_be_hidden()
    page.screenshot(path=str(OUT/'disconnected-empty.png'), full_page=True)
    assert not errors, errors
    browser.close()
print('PASS: recent videos, responsive layout, link/Enter/upload/drop/remove, validation, single submission, options, progress/error/success, comparison, exports, library and disconnected state')
