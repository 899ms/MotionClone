"""Capture the real local UI at narrow and wide sizes."""
from pathlib import Path
from playwright.sync_api import sync_playwright
out = Path('test-results'); out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome')
    for width in [320, 768, 1024, 1440]:
        page = browser.new_page(viewport={'width':width,'height':1000})
        errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('http://127.0.0.1:4319', wait_until='networkidle')
        page.screenshot(path=str(out/f'ui-{width}.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Horizontal overflow'
        assert not errors, errors
        page.close()
    browser.close()
