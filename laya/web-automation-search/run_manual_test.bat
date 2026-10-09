@echo off
REM LAYA UltraFast - Manual Test Local

REM 1. Copy .env.example to .env if not exists
if not exist .env (
    copy .env.example .env 2>nul
    echo .env created from .env.example
)

REM 2. LAYA runs fully locally - no external services needed
echo LAYA running in local mode (heuristic model)
echo No Ollama or external LLM required

REM 3. Run LAYA agent in interactive mode (headless=false)
echo Starting LAYA local agent...
python -m laya_ultrafast.agent --goal "Acessar https://example.com e clicar em 'Mais informacao'" --headless=false

REM Keep window open for inspection
pause