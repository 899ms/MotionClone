"""Download the selected recording through the actual button; verify media and cache."""
import argparse
import hashlib
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument('--project', required=True)
parser.add_argument('--look', default='mono')
parser.add_argument('--format', default='landscape')
parser.add_argument('--layout', default='split')
args = parser.parse_args()
out = Path('test-results/recording-export')
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chrome')
    page = browser.new_page(viewport={'width': 1440, 'height': 1100}, accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(f'http://127.0.0.1:4319/?project={args.project}&view=compare&look={args.look}&format={args.format}&layout={args.layout}')
    expect(page.locator('#download')).to_be_visible()
    page.wait_for_function('() => document.getElementById("result-video").readyState>=2')
    page.evaluate('() => {const v=document.getElementById("result-video");v.pause();v.muted=true;v.currentTime=Math.min(10,v.duration/2);}')
    with page.expect_download(timeout=3600000) as event:
        page.locator('#download').click()
        previous = ''
        deadline = time.monotonic() + 3600
        while time.monotonic() < deadline:
            status = page.locator('#recording-export-status').inner_text()
            if status != previous:
                print(status, flush=True)
                previous = status
            assert not page.locator('#recording-export-status').evaluate('(el)=>el.classList.contains("export-error")'), status
            if 'Recording MP4 ready' in status:
                break
            page.wait_for_timeout(1000)
    download = event.value
    assert download.suggested_filename == f'motionclone-{args.look}-{args.format}-{args.layout}.mp4', download.suggested_filename
    path = out / download.suggested_filename
    download.save_as(path)
    assert path.stat().st_size > 10000
    key = download.url.split('/')[-2]
    report = json.loads((Path('data') / args.project / 'recordings' / key / 'verification.json').read_text(encoding='utf-8'))
    assert report['verified'] and report['audio'] and report['audio_bitstream_match']
    assert report['settings'] == {'look': args.look, 'format': args.format, 'layout': args.layout}
    assert hashlib.sha256(path.read_bytes()).hexdigest() == report['output_sha256']
    start = time.monotonic()
    with page.expect_download(timeout=15000) as repeated:
        page.locator('#download').click()
    assert repeated.value.failure() is None
    assert time.monotonic() - start < 15, 'A verified export should download from cache'
    expect(page.locator('#download-rebuild-only')).to_have_attribute('href', f'/media/{args.project}/output.mp4')
    assert not errors, errors
    page.locator('#finished').screenshot(path=str(out / f'{args.look}-{args.format}-ready.png'))
    print(json.dumps({'download': str(path), 'cached_repeat': True, 'browser_errors': errors, 'verification': report}), flush=True)
    browser.close()
