param([int]$Puerto = 7860)

$raiz = Split-Path $PSScriptRoot -Parent
Set-Location $raiz
$env:DIR_REGISTROS = Join-Path $raiz "registros"

$servidor = Start-Process -PassThru -NoNewWindow -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "servicio.api:app", "--host", "127.0.0.1", "--port", $Puerto
try {
    cloudflared tunnel --no-autoupdate --url "http://127.0.0.1:$Puerto"
} finally {
    Stop-Process -Id $servidor.Id
}
