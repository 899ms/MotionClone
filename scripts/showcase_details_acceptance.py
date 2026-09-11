"""Exercise the showcase controls and support links without changing saved projects."""
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
OUT=Path('test-results/showcase-details');OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome')
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:4319/?demo=1',wait_until='domcontentloaded')
    expect(page.locator('#demo-player video')).to_have_count(2,timeout=12000)
    expect(page.locator('.header-star')).to_have_attribute('href','https://github.com/blixvip/MotionClone')
    expect(page.locator('.header-coffee')).to_have_attribute('href','https://buymeacoffee.com/blix')
    page.locator('#view-wipe').click()
    expect(page.locator('#view-wipe')).to_have_attribute('aria-pressed','true')
    page.locator('#wipe-position').fill('72')
    assert page.locator('#demo').evaluate('(e)=>e.style.getPropertyValue("--wipe")')=='72%'
    assert '72%' in page.locator('.compare-pane.rebuilt').evaluate('(e)=>getComputedStyle(e).clipPath')
    page.locator('#demo-speed').select_option('0.5')
    assert page.locator('#demo video').evaluate_all('(vs)=>vs.every(v=>v.playbackRate===.5)')
    page.screenshot(path=str(OUT/'wipe-1440.png'))
    page.locator('#demo-expand').click()
    page.wait_for_function('() => document.fullscreenElement?.id === "demo"')
    page.locator('#demo-expand').click()
    page.wait_for_function('() => !document.fullscreenElement')
    page.locator('#view-pair').click()
    page.locator('[data-layer="type"]').click()
    expect(page.locator('#layer-count')).to_have_text('2 layers visible')
    expect(page.locator('[data-plane="type"]')).to_have_class('lab-plane lab-type plane-hidden')
    page.locator('[data-layer="type"]').click()
    page.locator('#explode-layers').click()
    expect(page.locator('#explode-layers')).to_have_attribute('aria-pressed','true')
    page.wait_for_timeout(650)
    page.locator('.layer-stage').screenshot(path=str(OUT/'layers.png'))
    page.locator('#explode-layers').click()
    for width in [320,390,768,1024,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        page.evaluate('scrollTo(0,0)')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
        for selector in ['.header-star','.header-coffee']:
            expect(page.locator(selector)).to_be_visible()
            box=page.locator(selector).bounding_box();assert 0<=box['y']<250,(width,selector,box)
        page.screenshot(path=str(OUT/f'home-{width}.png'),full_page=True)
    page.emulate_media(reduced_motion='reduce')
    page.locator('#explode-layers').click()
    assert page.locator('.lab-plane').first.evaluate('(e)=>getComputedStyle(e).transitionDuration')=='0s'
    page.route('**/api/library',lambda r:r.abort())
    page.goto('http://127.0.0.1:4319/?demo=1',wait_until='domcontentloaded')
    page.locator('#view-wipe').click()
    expect(page.locator('.illustrative-demo')).to_be_visible()
    page.locator('[data-layer="shape"]').click()
    expect(page.locator('#layer-count')).to_have_text('2 layers visible')
    assert not errors,errors
    browser.close()
print('PASS: support links, wipe, speed, fullscreen, layer controls, five widths, reduced motion and standalone controls')
