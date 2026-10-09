param()
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Test-Command($cmd) {
  try { Get-Command $cmd -ErrorAction Stop | Out-Null; return $true } catch { return $false }
}

if (-not (Test-Command "python")) {
  Write-Host "Python não encontrado. Instale Python 3.10+ e tente novamente."
  exit 1
}

if (-not (Test-Path ".venv")) {
  Write-Host "Criando ambiente virtual..."
  python -m venv .venv
}

$pip = Join-Path $root ".venv\Scripts\pip.exe"
$python = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "Instalando dependências..."
& $pip install -r "$root\requirements.txt"

Write-Host "Iniciando aplicação..."
$proc = Start-Process -FilePath $python -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","4111" -PassThru -WorkingDirectory $root

Start-Sleep -Seconds 3
$url = "http://127.0.0.1:4111"
Write-Host ""
Write-Host "Aplicação disponível em: $url"
Write-Host ""

try {
  Start-Process $url
} catch {
  Write-Host "Não foi possível abrir o navegador automaticamente."
}

try {
  Wait-Process -Id $proc.Id
} catch {
  Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
}
