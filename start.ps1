$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath $pythonPath)) {
    & python -m venv (Join-Path $projectRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required.' }
}
$depsMarker = Join-Path $projectRoot '.venv\frameforge-ready'
if (-not (Test-Path -LiteralPath $depsMarker)) {
    & $pythonPath -m pip install -r (Join-Path $projectRoot 'requirements.lock.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Could not install MotionClone dependencies.' }
    New-Item -ItemType File -Path $depsMarker -Force | Out-Null
}
$existing = $null
$rendererRoot = Join-Path $projectRoot 'hyperframes'
if (-not (Test-Path -LiteralPath (Join-Path $rendererRoot 'node_modules\hyperframes\package.json'))) {
    & npm ci --prefix $rendererRoot --no-fund --no-audit
    if ($LASTEXITCODE -ne 0) { throw 'Could not install HyperFrames. Check Node.js and your connection.' }
}
try { $existing = Invoke-RestMethod -Uri 'http://127.0.0.1:4319/api/status' -TimeoutSec 15 } catch {}
if ($null -eq $existing) {
    Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','app.server:app','--host','127.0.0.1','--port','4319' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'server.log') -RedirectStandardError (Join-Path $projectRoot 'server-error.log')
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 500
        try { $existing = Invoke-RestMethod -Uri 'http://127.0.0.1:4319/api/status' -TimeoutSec 3; break } catch {}
    }
}
if ($null -eq $existing) { throw 'MotionClone could not start. See server-error.log.' }
Start-Process 'http://127.0.0.1:4319'
