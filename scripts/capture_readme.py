"""Capture real documentation screenshots from a running local app. No AI or exports."""
import argparse
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, help='Completed project suitable for public screenshots')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / 'docs'
    base = 'http://127.0.0.1:4319'
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome')
        context = browser.new_context(viewport={'width': 1440, 'height': 640}, reduced_motion='reduce')
        page = context.new_page()
        page.goto(base + '/?workspace=1', wait_until='networkidle')
        expect(page.locator('#create')).to_be_visible()
        expect(page.locator('#connection')).not_to_have_text('Connecting…')
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(output / 'interface.png'))

        page.set_viewport_size({'width': 1440, 'height': 1200})
        query = urlencode({'project': args.project, 'view': 'compare', 'look': 'studio',
                           'format': 'landscape', 'layout': 'split'})
        page.goto(base + '/?' + query, wait_until='networkidle')
        expect(page.locator('#finished')).to_be_visible()
        page.wait_for_function('''() => ['source-video', 'result-video'].every(id =>
            document.getElementById(id).readyState >= 2)''')
        page.locator('#players video').evaluate_all('(videos) => videos.forEach(v => v.pause())')
        page.locator('#promo-seek').fill('2')
        page.wait_for_function('''() => ['source-video', 'result-video'].every(id => {
            const v = document.getElementById(id); return !v.seeking && v.readyState >= 2;
        })''')
        page.locator('.viewer-panel').screenshot(path=str(output / 'comparison.png'))
        page.locator('#recording-style-options > summary').click()
        page.locator('#recording-options').screenshot(path=str(output / 'recording-looks.png'))

        page.set_viewport_size({'width': 1440, 'height': 1000})
        page.goto(base + '/?demo=1', wait_until='networkidle')
        expect(page.locator('#hero-title')).to_be_visible()
        expect(page.locator('#demo-player video')).to_have_count(2)
        page.wait_for_function('''() => [...document.querySelectorAll('#demo-player video')]
            .every(v => v.readyState >= 2)''')
        page.locator('#demo-player video').evaluate_all('(videos) => videos.forEach(v => v.pause())')
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(output / 'showcase.png'))
        browser.close()
    print('Captured interface, comparison, recording looks, and showcase in docs/. Review before publishing.')


if __name__ == '__main__':
    main()
