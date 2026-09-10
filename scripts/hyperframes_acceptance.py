"""Read-only acceptance against the independent rebuild."""
import io
import json
import zipfile
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

OUT=Path('test-results/hyperframes');OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser(description='Inspect a completed local independent rebuild; never starts AI.')
parser.add_argument('--project',required=True,help='ID of a completed local HyperFrames project')
args=parser.parse_args()
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome')
    page=browser.new_page(viewport={'width':1440,'height':1100})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    job=page.request.get(f'http://127.0.0.1:4319/api/jobs/{args.project}').json()
    assert job['status']=='complete' and job['brief']['mode']=='hyperframes'
    frames=job['verification']['actual_frames'];fps=float(job['verification']['fps']);length=frames/fps
    page.goto(f'http://127.0.0.1:4319/?project={args.project}',wait_until='networkidle')
    expect(page.locator('#finished')).to_be_visible()
    expect(page.locator('#verification-label')).to_contain_text('REBUILT')
    expect(page.locator('#editor-description')).to_contain_text('independent HyperFrames rebuild')
    page.locator('#export-details > summary').click()
    expect(page.locator('#finished-detail')).to_contain_text(f'{frames} frames compared')
    expect(page.locator('#hyperframes-export')).to_be_visible()
    expect(page.locator('#remotion-export')).to_be_hidden()
    expect(page.locator('#edit-panel')).to_be_hidden()
    page.locator('#compare-tab').click()
    for sec in [length*.03,length*.5,length*.97]:
        page.evaluate('''async sec => {
          await Promise.all(['source-video','result-video'].map(id => new Promise(resolve => {
            const v=document.getElementById(id);v.pause();v.muted=true;
            v.addEventListener('seeked',resolve,{once:true});v.currentTime=sec;
          })));
        }''',(int(sec*fps)+.5)/fps)
        page.wait_for_timeout(150)
        page.locator('.viewer-panel').screenshot(path=str(OUT/f'compare-{sec}.png'))
    page.evaluate("document.querySelector('#result-video').play()")
    page.wait_for_timeout(350)
    assert page.locator('#result-video').evaluate('(v)=>v.currentTime')>length*.97
    page.evaluate("document.querySelector('#result-video').pause()")
    for width in [320,1440]:
        page.set_viewport_size({'width':width,'height':1100})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(OUT/f'project-{width}.png'),full_page=True)
    response=page.request.get(f'http://127.0.0.1:4319/api/jobs/{args.project}/hyperframes')
    assert response.ok
    with zipfile.ZipFile(io.BytesIO(response.body())) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        assert manifest['frames']==frames and manifest['source_backed'] is False
        assert not any(name.endswith('.mp4') or name.startswith('ref-') for name in archive.namelist())
        assert manifest['independent_visual_layers'] is True
    assert not errors,errors
    browser.close()
print('PASS: actual HyperFrames result, first/middle/ending playback, comparison, responsive UI and project download')
