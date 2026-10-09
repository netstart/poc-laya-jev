@echo off
title LAYA Demo

REM Copiar .env se necessario
if not exist .env copy .env.example .env >nul

echo.
echo Iniciando LAYA...
python -m laya_ultrafast.agent --goal "Acessar https://example.com" --headless=false

echo.
echo Execucao concluida.
pause