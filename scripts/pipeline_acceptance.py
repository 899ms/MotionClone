"""Explicit real ChatGPT end-to-end test; uses plan allowance and an original fixture."""
import json
import time
from pathlib import Path
import httpx

root=Path(__file__).resolve().parents[1]
with httpx.Client(base_url='http://127.0.0.1:4319',timeout=60) as client:
    status=client.get('/api/status').json()
    if status.get('active'):raise SystemExit('An existing job is active; no test started.')
    headers={'X-Frameforge-Token':status['token']}
    source=root/'test-results/reference.mp4'
    with source.open('rb') as video:
        response=client.post('/api/jobs',headers=headers,files={'video':('reference.mp4',video,'video/mp4')},
            data={'brand':'Motion library demo','instructions':'Rebuild this original four-second reference as editable layers. Keep the green background, moving circle, growing line and rounded border. Heading: KAI MOTION. Subtitle: Save it. Make it yours.',
                  'mode':'rebuild','keep_audio':'true','auto_review':'true','sampling':'standard'})
    response.raise_for_status();job=response.json();ident=job['id'];started=time.monotonic()
    print('PROJECT',ident,flush=True)
    client.patch(f'/api/jobs/{ident}',headers=headers,json={'name':'Motion library demo','collection':'Examples','tags':['Remotion','Typography']}).raise_for_status()
    stage=''
    while job['status'] in ('queued','running'):
        if job['stage']!=stage:
            stage=job['stage'];print(stage,flush=True)
        time.sleep(2)
        response=client.get(f'/api/jobs/{ident}');response.raise_for_status();job=response.json()
    result={'id':ident,'seconds':round(time.monotonic()-started,2),'status':job['status'],
            'error':job.get('error'),'warning':job.get('warning'),'verification':job.get('verification')}
    (root/'test-results/pipeline-acceptance.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)
    assert job['status']=='complete',job.get('error')
    assert job['verification']['renderer']=='remotion'
