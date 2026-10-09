@echo off
REM ============================================================
REM Script de Configuração: Graphify + OpenRouter Free Models Router
REM Para Windows (CMD / Batch)
REM ============================================================
REM Como usar:
REM   1) Abra o CMD
REM   2) Navegue até a pasta do projeto: cd /d C:\Users\seu-usuario\seu-projeto
REM   3) Execute: setup-graphify-openrouter.bat
REM
REM O que faz:
REM - Solicita sua chave da OpenRouter (se não estiver definida)
REM - Define OPENAI_API_KEY, OPENAI_BASE_URL e OPENAI_MODEL
REM - Testa a conexão
REM - Mostra exemplos de uso do Graphify com LLM
REM ============================================================

@echo off
echo Configurando Graphify para usar OpenRouter Free Models Router...

REM Verifica se a chave já está definida no ambiente
if defined OPENAI_API_KEY (
    echo OPENAI_API_KEY já definida no ambiente.
) else (
    set /p OPENAI_API_KEY="Digite sua chave da OpenRouter (ex: sk-or-...): "
    if "%OPENAI_API_KEY%"=="" (
        echo AVISO: Nenhuma chave fornecida. O Graphify só funcionará em modo --code-only.
    ) else (
        echo Chave da OpenRouter definida para esta sessão.
    )
)

REM Define a URL base da OpenRouter
set OPENAI_BASE_URL=https://openrouter.ai/api/v1
echo OPENAI_BASE_URL = %OPENAI_BASE_URL%

REM Modelo gratuito padrão
set DEFAULT_MODEL=google/gemma-7b-it:free
set OPENAI_MODEL=%DEFAULT_MODEL%
echo OPENAI_MODEL = %OPENAI_MODEL% (gratuito)

REM Pergunta se quer trocar o modelo
set /p MODEL_INPUT="Deseja usar outro modelo? (Enter para manter '%DEFAULT_MODEL%', ou digite ex: meta-llama/llama-3-8b-instruct:free): "
if not "%MODEL_INPUT%"=="" (
    set OPENAI_MODEL=%MODEL_INPUT%
    echo OPENAI_MODEL atualizado para: %OPENAI_MODEL%
)

REM Testa a conexão (opcional)
echo.
echo Testando conexão com OpenRouter...
python -c "import os, openai; client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url=os.getenv('OPENAI_BASE_URL')); models = client.models.list(); print('OK - Modelo:', models.data[0].id)" 2>nul
if errorlevel 1 (
    echo AVISO: Falha ao testar conexão. Verifique a chave e internet.
    echo Voce pode continuar usando --code-only.
) else (
    echo Conexão com OpenRouter confirmada!
)

echo.
echo ========================================
echo === Graphify + OpenRouter configurado ===
echo ========================================
echo.
echo Exemplos de uso:
echo.
echo Modo completo (LLM para docs/imagens):
echo   python -m graphify .
echo.
echo Modo apenas codigo (mais rapido, sem chave):
echo   python -m graphify . --code-only
echo.
echo Consultas no grafo:
echo   python -m graphify query "o que e um agente Laya?"
echo   python -m graphify explain "context_manager"
echo   python -m graphify path "LayaAgent" "Browser"
echo.
echo As variaveis valem apenas para esta sessao do CMD.
echo Para tornar permanente, adicione como variaveis de ambiente do usuario.
echo ========================================

pause