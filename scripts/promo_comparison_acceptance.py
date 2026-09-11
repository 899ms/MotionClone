"""Exercise the branded recording view against saved media; never starts AI jobs."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import argparse
import json
from urllib.request import urlopen

OUT=Path('test-results/promo');OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--project');args=parser.parse_args()
with urlopen('http://127.0.0.1:4319/api/library') as response:jobs=json.load(response)
project=args.project or next((job['id'] for job in jobs if job['status']=='complete' and all(name in job['files'] for name in ['source.mp4','output.mp4'])),None)
if not project:raise SystemExit('A completed source/rebuild pair is required. Pass --project ID.')
URL=f'http://127.0.0.1:4319/?project={project}&view=compare'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome')
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL,wait_until='domcontentloaded')
    stage=page.locator('#comparison-stage')
    expect(page.locator('#promo-brand')).to_be_visible(timeout=15000)
    for href in ['https://motionclone.lol','https://github.com/blixvip','https://x.com/waselyy','https://github.com/blixvip/MotionClone']:
        expect(stage.locator(f'a[href="{href}"]').first).to_be_visible()
    for href in ['https://github.com/blixvip','https://x.com/waselyy']:
        expect(stage.locator(f'a[href="{href}"] svg path')).to_have_attribute('d',__import__('re').compile('.{100,}'))
    shader=page.locator('#promo-shader')
    stage.scroll_into_view_if_needed()
    expect(shader).to_have_attribute('data-state','running')
    frames=int(shader.get_attribute('data-frames'))
    page.wait_for_function('(n) => +document.getElementById("promo-shader").dataset.frames > n+2',arg=frames)
    page.emulate_media(reduced_motion='reduce')
    expect(shader).to_have_attribute('data-state','static')
    page.wait_for_timeout(150)
    frames=shader.get_attribute('data-frames')
    page.wait_for_timeout(250)
    assert shader.get_attribute('data-frames')==frames,'Reduced motion must stop the shader loop'
    page.emulate_media(reduced_motion='no-preference')
    source=page.locator('#source-video');result=page.locator('#result-video')
    assert source.bounding_box()['x']<result.bounding_box()['x']
    assert source.get_attribute('src')!=result.get_attribute('src')
    page.locator('#promo-play').click()
    page.wait_for_function("() => ['source-video','result-video'].every(id=>{const v=document.getElementById(id);return !v.paused&&v.currentTime>.3})")
    page.locator('#promo-play').click()
    expect(page.locator('#promo-play')).to_have_attribute('aria-label','Play both videos')
    page.locator('#promo-speed').select_option('1.5')
    assert source.evaluate('(v)=>v.playbackRate')==result.evaluate('(v)=>v.playbackRate')==1.5
    page.locator('#promo-speed').select_option('1')
    page.locator('#promo-sound').click()
    assert source.evaluate('(v)=>v.muted') and not result.evaluate('(v)=>v.muted')
    page.locator('#promo-sound').click()
    page.locator('#promo-seek').fill('4')
    page.wait_for_function("() => ['source-video','result-video'].every(id=>Math.abs(document.getElementById(id).currentTime-4)<.1)")
    page.locator('#promo-restart').click()
    page.wait_for_function("() => document.getElementById('result-video').currentTime<2&&!document.getElementById('result-video').paused")
    page.locator('#promo-play').click()
    expect(page.locator('#promo-error')).to_be_hidden()
    page.locator('#promo-seek').fill(str(round(result.evaluate('(v)=>v.duration-.15'),2)))
    page.locator('#promo-play').click()
    page.wait_for_function("() => document.getElementById('result-video').currentTime<2&&!document.getElementById('result-video').paused")
    page.locator('#promo-play').click()
    stage.screenshot(path=str(OUT/'comparison-desktop.png'))
    page.locator('#present-comparison').click()
    expect(page.locator('body')).to_have_class(__import__('re').compile(r'recording-view'))
    expect(page.locator('#promo-controls')).to_be_hidden()
    for width,height in [(1920,1080),(1280,720),(390,844)]:
        page.set_viewport_size({'width':width,'height':height})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        for selector in ['#promo-brand','#promo-website','#promo-identities']:
            bounds=page.locator(selector).bounding_box()
            assert bounds and bounds['x']>=0 and bounds['y']>=0
            assert bounds['x']+bounds['width']<=width+1 and bounds['y']+bounds['height']<=height+1,(selector,bounds)
        for video in [source,result]:
            bounds=video.bounding_box();footer=page.locator('#promo-identities').bounding_box()
            assert bounds['height']>40 and bounds['y']+bounds['height']<=footer['y']+1,(width,bounds,footer)
        page.screenshot(path=str(OUT/f'recording-{width}.png'))
    page.keyboard.press('Escape')
    expect(page.locator('body')).not_to_have_class(__import__('re').compile(r'recording-view'))
    page.set_viewport_size({'width':390,'height':844})
    stage.screenshot(path=str(OUT/'comparison-mobile.png'))
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.locator('#result-tab').click()
    expect(page.locator('#promo-brand')).to_be_hidden()
    expect(shader).to_have_attribute('data-state','paused')
    expect(source).to_be_hidden()
    expect(result).to_be_visible()
    page.locator('#compare-tab').click()
    expect(page.locator('#promo-brand')).to_be_visible()
    page.goto(URL+'&record=1',wait_until='domcontentloaded')
    expect(page.locator('body')).to_have_class(__import__('re').compile(r'recording-view'))
    page.keyboard.press('Escape')
    expect(page.locator('#promo-controls')).to_be_visible()
    # A browser without WebGL still has complete branding and playable media.
    fallback=browser.new_page(viewport={'width':1280,'height':720})
    fallback.add_init_script("const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return /webgl/.test(type)?null:original.call(this,type,...args)}")
    fallback.goto(URL,wait_until='domcontentloaded')
    expect(fallback.locator('#promo-brand')).to_be_visible(timeout=15000)
    expect(fallback.locator('#promo-shader')).to_have_attribute('data-state','fallback')
    fallback.locator('#promo-play').click()
    fallback.wait_for_function("() => !document.getElementById('result-video').paused && document.getElementById('result-video').currentTime>.3")
    fallback.close()
    assert not errors,errors
    browser.close()
print('PASS: social logos, animated shader, reduced motion, WebGL fallback, branding, synchronized playback/seek/replay, recording view, mobile, exit, tab recovery')
