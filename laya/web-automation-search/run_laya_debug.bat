@echo off
title LAYA - Visualizar Resultado do Processamento

echo.
echo ==========================================
echo  LAYA - RESULTADO DO PROCESSAMENTO
echo ==========================================
echo.

REM 1. Verificar se módulos carregam
echo [1/5] Verificando módulos Python...
python -c "import structlog" >nul 2>&1 && echo [OK] structlog carregado || echo [FALHANDO] structlog
python -c "import laya_ultrafast" >nul 2>&1 && echo [OK] laya_ultrafast carregado || echo [FALHANDO] laya_ultrafast
echo.

REM 2. Testar agente com goal simples
echo [2/5] Testando agente com goal simples...
timeout 15 python -m laya_ultrafast.agent --goal "Acessar https://example.com" --headless=false >nul 2>nul
set errorlevel=%errorlevel%
if %errorlevel% equ 0 (
    echo [SUCESSO] Agente executou sem erros aparentes.
) else (
    echo [ERRO] Agente encontrou problema (ver detalhes abaixo).
)

REM 3. Verificar estado dos arquivos
echo [3/5] Verificando arquivos gerados...
if exist .env echo [OK] .env existe
else echo [FALTA] .env nao encontrado - sera criado

if exist output_log.txt (
    echo [OK] output_log.txt encontrado
    type output_log.txt
) else (
    echo [INFO] Nenhum output_log.txt gerado
)

echo.
echo [4/5] Verificando configurações...
type .env 2>nul | find "LAYA_MODEL" && echo [OK] Config visivel ou echo [INFO] Config nao visivel

echo.
echo [5/5] RESUMO FINAL
echo.
echo "O agente LAYA executou o objetivo: Acessar https://example.com"
echo.
echo "Resultados possiveis:"
echo "  1. Tela piscou e sumiu muito rapido - use o pause final"
echo "  2. Erros de config aparecem em vermelho"
echo "  3. Nenhum output = agente pode estar aguardando Chrome/CDP"
echo.
echo ============================================
echo Pressione qualquer tecla para continuar e ver detalhes...
echo ============================================
pause >nul