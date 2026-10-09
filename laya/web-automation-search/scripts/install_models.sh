#!/bin/bash
# LAYA Model Installation Script
# Baixa e configura modelos locais recomendados para Ollama

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verifica se Ollama está instalado
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        log_error "Ollama não encontrado. Instale em: https://ollama.ai"
        log_info "Linux/macOS: curl -fsSL https://ollama.ai/install.sh | sh"
        log_info "Windows: Baixe o instalador em https://ollama.ai/download"
        exit 1
    fi
    log_success "Ollama encontrado: $(ollama version)"
}

# Verifica se Ollama está rodando
check_ollama_running() {
    if ! curl -s http://localhost:11434/api/version &> /dev/null; then
        log_warn "Ollama não está rodando. Iniciando..."
        ollama serve &
        OLLAMA_PID=$!
        sleep 3
        if ! curl -s http://localhost:11434/api/version &> /dev/null; then
            log_error "Falha ao iniciar Ollama"
            exit 1
        fi
        log_success "Ollama iniciado (PID: $OLLAMA_PID)"
    else
        log_success "Ollama já está rodando"
    fi
}

# Baixa modelo se não existir
pull_model() {
    local model=$1
    log_info "Verificando modelo: $model"

    if ollama list | grep -q "^$model "; then
        log_success "Modelo $model já está instalado"
    else
        log_info "Baixando modelo: $model (pode demorar)..."
        ollama pull "$model"
        log_success "Modelo $model baixado com sucesso"
    fi
}

# Modelos recomendados
MODELS=(
    "llama3.1:8b-instruct-q4_K_M"
    "mistral:7b-instruct-q4_K_M"
    "phi3:mini-instruct-4k-q4"
    "qwen2.5:7b-instruct-q4_K_M"
)

# Função principal
main() {
    echo "=========================================="
    echo "  LAYA - Instalação de Modelos Locais"
    echo "=========================================="
    echo ""

    check_ollama
    check_ollama_running

    echo ""
    log_info "Instalando modelos recomendados..."
    echo ""

    for model in "${MODELS[@]}"; do
        pull_model "$model"
    done

    echo ""
    echo "=========================================="
    log_success "Todos os modelos instalados!"
    echo "=========================================="
    echo ""
    log_info "Modelos disponíveis:"
    ollama list
    echo ""
    log_info "Para testar: ollama run llama3.1:8b-instruct-q4_K_M"
    log_info "Para usar com LAYA: defina LAYA_MODEL_NAME=llama3.1:8b-instruct-q4_K_M no .env"
}

# Executa se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi