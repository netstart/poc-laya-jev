#!/bin/bash
# LAYA Model Installation Script
# Nota: O LAYA roda com modelo heurístico embutido por padrão.
# Não é necessário instalar Ollama ou quaisquer modelos externos.
# Para usar um modelo LLM real, configure LAYA_MODEL_PROVIDER=ollama
# e instale Ollama separadamente (não obrigatório).

set -euo pipefail

# Mensagem informativa
echo "=========================================="
echo "  LAYA - Configuração de Modelo"
echo "=========================================="
echo ""
echo "O LAYA roda completamente offline com seu modelo heurístico embutido."
echo "Não é necessário instalar Ollama ou quaisquer modelos externos."
echo ""
echo "Para usar o modo heurístico:"
echo "  - O agente funcionará imediatamente após a instalação"
echo ""
echo "Se desejar usar um modelo LLM real (Ollama, OpenAI, etc.):"
echo "  1. Instale Ollama em https://ollama.ai"
echo "  2. Configure .env com LAYA_MODEL_PROVIDER=ollama"
echo "  3. Execute: ollama pull <model_name>"
echo ""
echo "Modelos disponíveis para modo heurístico: nenhum necessário"
echo ""
echo "=========================================="
echo "  Concluído - LAYA pronto para uso local"
echo "=========================================="