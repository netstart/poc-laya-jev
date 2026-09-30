#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 não encontrado. Instale Python 3.10+ e tente novamente."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Criando ambiente virtual..."
  python3 -m venv .venv
fi

echo "Instalando dependências..."
.venv/bin/pip install -r requirements.txt

echo "Iniciando aplicação..."
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 4111 &
PID=$!

sleep 3

URL="http://127.0.0.1:4111"
echo ""
echo "Aplicação disponível em: $URL"
echo ""

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL"
elif command -v open >/dev/null 2>&1; then
  open "$URL"
fi

wait $PID
