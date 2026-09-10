"""Verify real synchronized preview playback without creating or changing projects."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
OUT=Path('test-results/live');OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome')
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:4319/',wait_until='domcontentloaded')
    pair=page.locator('#recent-grid .live-comparison').first
    expect(pair).to_be_visible(timeout=15000)
    pair.scroll_into_view_if_needed()
    page.wait_for_function("""() => {const v=[...document.querySelectorAll('#recent-grid .live-comparison video')];return v.length>=2 && v.slice(0,2).every(x=>!x.paused && x.currentTime>.5)}""",timeout=25000)
    sources=pair.locator('video').evaluate_all('(vs)=>vs.map(v=>v.currentSrc)')
    assert sources[0]!=sources[1] and 'source.mp4' in sources[0] and 'output.mp4' in sources[1]
    page.wait_for_timeout(2000)
    drift=pair.locator('video').evaluate_all('(vs)=>Math.abs(vs[0].currentTime-vs[1].currentTime)')
    assert drift<.25,drift
    pair.locator('.compare-toggle').click()
    assert pair.locator('video').evaluate_all('(vs)=>vs.every(v=>v.paused)')
    pair.locator('input').fill('20')
    page.wait_for_timeout(500)
    times=pair.locator('video').evaluate_all('(vs)=>vs.map(v=>v.currentTime)')
    assert all(abs(t-20)<.15 for t in times),times
    pair.locator('.compare-toggle').click()
    page.wait_for_timeout(700)
    assert pair.locator('video').evaluate_all('(vs)=>vs.every(v=>!v.paused && v.currentTime>20.3)')
    assert abs(float(pair.locator('input').input_value())-pair.locator('video').first.evaluate('(v)=>v.currentTime'))<.25
    page.screenshot(path=str(OUT/'home-1440.png'),full_page=True)
    page.locator('#open-library').click()
    expect(page.locator('#library-grid .live-comparison')).to_be_visible()
    page.wait_for_timeout(1000)
    assert page.locator('#recent-grid video').evaluate_all('(vs)=>vs.every(v=>v.paused)')
    page.screenshot(path=str(OUT/'library-1440.png'),full_page=True)
    for width in [320,390,768,1024]:
        page.set_viewport_size({'width':width,'height':900})
        pair=page.locator('#library-grid .live-comparison').first
        pair.scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
        expect(pair.locator('figcaption').nth(0)).to_have_text('Original')
        expect(pair.locator('figcaption').nth(1)).to_have_text('Rebuilt')
        page.screenshot(path=str(OUT/f'library-{width}.png'),full_page=True)
    page.emulate_media(reduced_motion='reduce')
    page.reload(wait_until='domcontentloaded')
    pair=page.locator('#recent-grid .live-comparison').first
    pair.scroll_into_view_if_needed();page.wait_for_timeout(700)
    assert pair.locator('video').evaluate_all('(vs)=>vs.every(v=>v.paused)')
    pair.locator('.compare-toggle').click()
    page.wait_for_function("() => [...document.querySelectorAll('#recent-grid video')].every(v=>!v.paused)",timeout=15000)
    # Simulate unavailable graphics acceleration; media and controls still work.
    fallback=browser.new_page(viewport={'width':1440,'height':1000})
    fallback.add_init_script("""const getContext=HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext=function(type,...args){return type==='webgl'?null:getContext.call(this,type,...args)};""")
    fallback.goto('http://127.0.0.1:4319/',wait_until='domcontentloaded')
    expect(fallback.locator('#recent-grid .live-comparison').first).to_be_visible()
    expect(fallback.locator('.studio-light')).to_have_count(0)
    fallback.wait_for_function("() => [...document.querySelectorAll('#recent-grid video')].length===2 && [...document.querySelectorAll('#recent-grid video')].every(v=>!v.paused && v.currentTime>.3)",timeout=15000)
    fallback.close()
    assert not errors,errors
    browser.close()
print(f'PASS: distinct original/rebuild, autoplay, drift {drift:.3f}s, pause, seek, navigation, mobile, reduced motion and no-WebGL fallback')
