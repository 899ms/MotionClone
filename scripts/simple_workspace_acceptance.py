"""Check the everyday local workflow with saved media; never submit an AI job."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

OUT = Path('test-results/simple-workspace')
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chrome')
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:4319/')
    page.screenshot(path=str(OUT / 'entry.png'))
    expect(page.locator('#create')).to_be_visible()
    expect(page.locator('#recent-grid .motion-card').first).to_be_visible()
    expect(page.locator('#recent-grid video')).to_have_count(0)
    for width in [320, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        box = page.locator('#create').bounding_box()
        assert box['y'] + box['height'] < 800, box
        page.screenshot(path=str(OUT / f'new-{width}.png'), full_page=True)
    page.locator('#open-library').click()
    page.locator('#library-search').fill('Nexa')
    expect(page.locator('#library-grid .motion-card')).to_have_count(3)
    for width in [320, 768, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
    page.screenshot(path=str(OUT / 'library.png'), full_page=True)
    page.locator('#library-grid .card-thumbnail').first.click()
    expect(page.locator('#finished')).to_be_visible()
    assert page.locator('#download').bounding_box()['y'] < page.locator('#result-video').bounding_box()['y']
    page.locator('#compare-tab').click()
    expect(page.locator('#recording-format')).to_be_visible()
    expect(page.locator('.recording-preset').first).not_to_be_visible()
    page.locator('#recording-style-options > summary').click()
    page.locator('[data-look="signal"].recording-preset').click()
    expect(page.locator('#recording-format')).to_have_value('portrait')
    page.locator('#recording-format').select_option('landscape')
    page.locator('#recording-style-options > summary').click()
    page.wait_for_function('() => document.getElementById("result-video").readyState >= 2')
    page.locator('#promo-play').click()
    page.wait_for_function('() => document.getElementById("result-video").currentTime > .2')
    page.locator('#promo-play').click()
    for width in [320, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        page.screenshot(path=str(OUT / f'project-{width}.png'), full_page=True)
    # Check the selected format reaches the real download handler, without rendering.
    submitted = []
    def export_route(route):
        submitted.append(route.request.post_data_json)
        route.fulfill(status=503, json={'detail': 'Acceptance test: export intentionally stopped'})
    page.route('**/api/jobs/*/recording', export_route)
    page.locator('#download').click()
    expect(page.locator('#recording-export-status')).to_contain_text('intentionally stopped')
    assert submitted == [{'look': 'signal', 'format': 'landscape', 'layout': 'stack'}]
    expect(page.locator('#download')).not_to_have_attribute('aria-disabled', 'true')
    page.locator('#back-library').click()
    expect(page.locator('#library-search')).to_have_value('Nexa')
    page.locator('#library-search').fill('no-such-video-acceptance')
    expect(page.locator('#empty-title')).to_have_text('No matching videos')
    assert not errors, errors
    browser.close()
print('PASS: local entry, compact library, search/open, responsive layout, playback, styles and export handler')
