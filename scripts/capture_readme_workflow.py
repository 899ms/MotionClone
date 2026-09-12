"""Capture the README's public examples from the real local UI; never start jobs."""
import json
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'images'
FRAMES = ROOT / 'test-results' / 'readme-motion-frames'
BASE = 'http://127.0.0.1:4319'
LEO = '09a418cdd005'
PORTRAIT = '5fbdf5e42405'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome')
        context = browser.new_context(viewport={'width': 1440, 'height': 1050}, reduced_motion='reduce')
        # Screenshots must never submit reconstruction, account, or library changes.
        context.route('**/api/**', lambda route: route.continue_() if route.request.method in {'GET', 'HEAD'} else route.abort())
        page = context.new_page()

        def ready():
            page.evaluate('document.fonts.ready')

        def open_project(project=LEO, **options):
            page.goto(BASE + '/?' + urlencode({'project': project, **options}), wait_until='domcontentloaded')
            expect(page.locator('#finished')).to_be_visible()
            ready()
            page.wait_for_function('''() => [...document.querySelectorAll('#players video')]
                .filter(v => !v.hidden).every(v => v.readyState >= 2)''')

        def seek(seconds):
            page.locator('#players video').evaluate_all('(vs) => vs.forEach(v => v.pause())')
            if page.locator('#promo-seek').is_visible():
                page.locator('#promo-seek').fill(str(seconds))
            else:
                page.locator('#players video').evaluate_all('(vs, time) => vs.forEach(v => {v.currentTime=time;})', seconds)
            page.wait_for_function('''() => [...document.querySelectorAll('#players video')]
                .every(v => !v.seeking && v.readyState >= 2)''')

        page.goto(BASE + '/?workspace=1', wait_until='domcontentloaded')
        expect(page.locator('#create')).to_be_visible()
        ready()
        public_url = json.loads((ROOT / 'data' / LEO / 'job.json').read_text())['url']
        page.locator('#url').fill(public_url)
        page.locator('#create-form').screenshot(path=str(OUT / '01-add-reference.png'))

        open_project(view='result')
        page.locator('#result-video').evaluate('(v) => {v.pause(); v.currentTime=1;}')
        page.wait_for_function('() => !document.getElementById("result-video").seeking')
        page.locator('.stage-column').screenshot(path=str(OUT / '02-rebuilt-video.png'))
        page.locator('#finished').screenshot(path=str(OUT / '05-downloads.png'))

        open_project(view='compare', look='studio', format='landscape', layout='split')
        seek(1)
        page.locator('.viewer-panel').screenshot(path=str(OUT / '03-compare.png'))
        page.locator('#recording-style-options > summary').click()
        page.locator('#recording-options').screenshot(path=str(OUT / '04-style-picker.png'))

        page.set_viewport_size({'width': 1440, 'height': 810})
        open_project(view='compare', record='1', look='studio', format='landscape', layout='split')
        seek(1)
        page.locator('#comparison-stage').screenshot(path=str(OUT / 'hero-comparison.png'))
        for frame in range(48):
            seek(frame / 8)
            page.locator('#comparison-stage').screenshot(path=str(FRAMES / f'{frame:03d}.png'))

        page.set_viewport_size({'width': 720, 'height': 1280})
        open_project(PORTRAIT, view='compare', record='1', look='signal', format='portrait', layout='split')
        seek(1)
        page.locator('#comparison-stage').screenshot(path=str(OUT / 'portrait-comparison.png'))

        page.set_viewport_size({'width': 1440, 'height': 900})
        page.goto(BASE + '/?workspace=1', wait_until='domcontentloaded')
        page.locator('#open-library').click()
        page.locator('#library-search').fill('Leo - remake comparison')
        expect(page.locator('#library-grid .motion-card')).to_have_count(1)
        ready()
        page.locator('#library-view').screenshot(path=str(OUT / '06-saved-videos.png'))
        browser.close()
    print('Captured eight real UI images and 48 comparison frames. No jobs or exports submitted.')


if __name__ == '__main__':
    main()

