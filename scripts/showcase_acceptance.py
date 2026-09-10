"""Check the project landing page, local demo, and standalone fallback."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
OUT=Path('test-results/showcase');OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome')
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:4319/',wait_until='domcontentloaded')
    expect(page.locator('#hero-title')).to_have_text('Love the motion?Rebuild it.')
    expect(page.locator('#demo-player .live-comparison')).to_be_visible(timeout=12000)
    assert page.locator('#create-form').count()==0
    page.locator('.demo-button').click()
    page.wait_for_function("() => [...document.querySelectorAll('#demo-player video')].every(v=>!v.paused&&v.currentTime>.5)",timeout=15000)
    assert page.locator('#demo-player video').evaluate_all('(v)=>v[0].currentSrc!==v[1].currentSrc')
    page.evaluate('scrollTo(0,0)')
    page.wait_for_timeout(700)
    for width in [320,390,768,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
        page.screenshot(path=str(OUT/f'home-{width}.png'),full_page=True)
    page.locator('details').first.locator('summary').click()
    expect(page.locator('details').first.locator('p')).to_be_visible()
    page.locator('#open-workspace').click()
    expect(page.locator('#create-form')).to_be_visible()
    expect(page).to_have_url('http://127.0.0.1:4319/?workspace=1')
    # Offline/static hosting has an explicit illustrative preview, never broken players.
    page.route('**/api/library',lambda route:route.abort())
    page.goto('http://127.0.0.1:4319/',wait_until='domcontentloaded')
    expect(page.locator('.illustrative-demo')).to_be_visible()
    expect(page.locator('.sample-note')).to_contain_text('illustration')
    page.screenshot(path=str(OUT/'standalone.png'),full_page=True)
    assert not errors,errors
    browser.close()
print('PASS: landing page, real paired demo, GitHub CTA, workspace, FAQ, responsive layout and standalone fallback')
