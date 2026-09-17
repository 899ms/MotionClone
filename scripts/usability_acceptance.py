"""Exercise real workspace assets with isolated API responses; no AI jobs."""
import mimetypes
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results' / 'usability'
OUT.mkdir(parents=True, exist_ok=True)
baseline = '--baseline' in sys.argv
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chrome')
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    def respond(route):
        path = urlparse(route.request.url).path
        if path == '/api/status':
            route.fulfill(json={'token': 'test', 'hyperframes': True, 'ffmpeg': True, 'chatgpt': True})
        elif path in ('/api/jobs', '/api/library'):
            route.fulfill(json=[])
        else:
            relative = path.removeprefix('/static/') if path.startswith('/static/') else path.lstrip('/')
            file = ROOT / 'web' / ('index.html' if path == '/' else 'showcase.html' if path == '/showcase' else relative)
            route.fulfill(path=str(file), content_type=mimetypes.guess_type(file)[0] or 'application/octet-stream') if file.is_file() else route.fulfill(status=404)
    page.route('http://motionclone.test/**', respond)
    page.goto('http://motionclone.test/')
    expect(page.locator('#connection')).to_have_text('Ready')
    if not baseline:
        page.locator('#project-options > summary').click()
        expect(page.locator('#keep-audio')).to_be_checked()
        page.locator('#keep-audio').uncheck()
        assert page.evaluate('brief().keep_audio') is False
        page.locator('#keep-audio').check()
        page.locator('#project-options > summary').click()
        page.locator('#getting-started > summary').focus()
        page.keyboard.press('Enter')
        expect(page.get_by_role('link', name='简体中文指南')).to_be_visible()
        page.locator('#getting-started > summary').click()
        page.locator('#create').click()
        expect(page.locator('#import-error')).to_be_visible()
        page.locator('#url').fill('https://example.com/video.mp4')
        expect(page.locator('#import-error')).not_to_be_visible()
        page.locator('#open-library').click()
        expect(page.locator('#library-empty')).to_be_visible()
        page.locator('#new-project').click()
    for width in [320, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        expect(page.locator('#create')).to_be_visible()
        page.screenshot(path=str(OUT / f'{"before" if baseline else "after"}-{width}.png'), full_page=True)
    if not baseline:
        page.locator('#project-options > summary').click()
        page.locator('#getting-started > summary').click()
        for width in [320, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            expect(page.locator('#keep-audio')).to_be_visible()
            page.screenshot(path=str(OUT / f'help-{width}.png'), full_page=True)
        page.goto('http://motionclone.test/showcase')
        expect(page.get_by_role('link', name='Setup', exact=True)).to_have_attribute('href', '#get-started')
        expect(page.get_by_role('link', name='简体中文指南 ↗')).to_have_attribute('hreflang', 'zh-CN')
        for width in [320, 768, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(OUT / f'website-{width}.png'), full_page=True)
    assert not errors, errors
    browser.close()
print('PASS: workspace, audio settings, keyboard help, validation, empty library, responsive layout; mocked APIs')
