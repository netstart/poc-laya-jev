# ============================================================
# Script de Configuração: Graphify + OpenRouter Free Models Router
# Para Windows (PowerShell)
# ============================================================
# Como usar:
#   1) Abra o PowerShell como Administrador (opcional, mas recomendado)
#   2) Navegue até a pasta do projeto: cd C:\Users\seu-usuario\seu-projeto
#   3) Execute: .\setup-graphify-openrouter.ps1
#
# O que faz:
# - Solicita sua chave da OpenRouter (se não estiver definida)
# - Define OPENAI_API_KEY, OPENAI_BASE_URL e OPENAI_MODEL
# - Testa a conexão
# - Mostra exemplos de uso do Graphify com LLM (docs, imagens, etc.)
# ============================================================

Write-Host "Configurando Graphify para usar OpenRouter Free Models Router..." -ForegroundColor Cyan

# Pergunta pela chave da OpenRouter (se não estiver definida)
if (-not $env:OPENAI_API_KEY) {
    $key = Read-Host "Digite sua chave da OpenRouter (ex: sk-or-...)"
    if (-not $key) {
        Write-Warning "Nenhuma chave fornecida. O Graphify só funcionará em modo --code-only."
    } else {
        $env:OPENAI_API_KEY = $key
        Write-Host "Chave da OpenRouter definida para esta sessão." -ForegroundColor Green
    }
} else {
    Write-Host "OPENAI_API_KEY já definida no ambiente." -ForegroundColor Green
}

# Define a URL base da OpenRouter
$env:OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
Write-Host "OPENAI_BASE_URL = $env:OPENAI_BASE_URL" -ForegroundColor Green

# Modelo gratuito padrão (pode ser alterado)
$defaultModel = "google/gemma-7b-it:free"
$env:OPENAI_MODEL = $defaultModel
Write-Host "OPENAI_MODEL = $env:OPENAI_MODEL (gratuito)" -ForegroundColor Green

# Pergunta se quer trocar o modelo
$modelInput = Read-Host "Deseja usar outro modelo? (Enter para manter '$defaultModel', ou digite ex: meta-llama/llama-3-8b-instruct:free)"
if ($modelInput) {
    $env:OPENAI_MODEL = $modelInput
    Write-Host "OPENAI_MODEL atualizado para: $env:OPENAI_MODEL" -ForegroundColor Green
}

# Testa a conexão (opcional)
Write-Host "`nTestando conexão com OpenRouter..." -ForegroundColor Cyan
try {
    & python -c "import os, openai; client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url=os.getenv('OPENAI_BASE_URL')); models = client.models.list(); print('OK - Modelo:', models.data[0].id)"
    Write-Host "Conexão com OpenRouter confirmada!" -ForegroundColor Green
} catch {
    Write-Warning "Falha ao testar conexão. Você pode continuar com --code-only (sem chave)."
}

# Mostra instruções finais
Write-Host @"
========================================
=== Graphify + OpenRouter configurado ===
========================================

Exemplos de uso:

Modo completo (LLM para docs/imagens):
  python -m graphify .

Modo apenas código (mais rápido, sem chave):
  python -m graphify . --code-only

Consultas no grafo:
  python -m graphify query "o que é um agente Laya?"
  python -m graphify explain "context_manager"
  python -m graphify path "LayaAgent" "Browser"

As variáveis valem apenas para esta sessão do PowerShell.
Para tornar permanente, adicione ao seu perfil do PowerShell:
  $env:OPENAI_API_KEY  = "sua-chave"
  $env:OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
  $env:OPENAI_MODEL    = "google/gemma-7b-it:free"
========================================
"@ -ForegroundColor Yellow
