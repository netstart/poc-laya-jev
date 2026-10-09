# LAYA UltraFast — Agente de Automação Web Local

> **Automação web ultra-rápida, privada e sem nuvem** — usando estado estruturado do DOM em vez de screenshots pesados.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/Code%20Style-Ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/Type%20Checking-Mypy-000000.svg)](https://mypy-lang.org)

---

## 🎯 Visão Geral

O **LAYA** (Local Agent for Yielding Actions) é um agente de automação web que roda **100% localmente** no seu computador. Diferente de soluções baseadas em nuvem (como JEV/Browser-Use com visão), o LAYA:

- ✅ **Zero dependência de nuvem** — nenhum dado sai do seu computador
- ✅ **Ultra-rápido** — usa estado textual estruturado do DOM, não screenshots
- ✅ **Barato** — roda modelos locais (Ollama, vLLM, llama.cpp) sem custos de API
- ✅ **Privado** — zero telemetria, zero chamadas externas não iniciadas por você
- ✅ **Determinístico** — seed fixa, temperature baixa, decisões reprodutíveis

### Como Funciona

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   snapshot.js   │────▶│   LLM Local      │────▶│  ActionExecutor │
│  (DOM → JSON)   │     │ (Ollama/vLLM)    │     │  (Playwright)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                        │
        ▼                       ▼                        ▼
   Elementos          Decisão estruturada          Validação geométrica
   interativos        (CLICK, TYPE, etc.)           + Execução atômica
```

---

## 📋 Pré-requisitos

### Hardware Recomendado

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **CPU** | 4 cores / 2.5 GHz | 8+ cores / 3.5 GHz (AVX2/AVX-512) |
| **RAM** | 16 GB | 32+ GB |
| **GPU** (opcional) | — | NVIDIA 8GB+ VRAM (CUDA 12+) |
| **Disco** | 10 GB livres | SSD NVMe 50+ GB livres |
| **SO** | Linux/macOS/WSL2 | Linux (Ubuntu 22.04+ / Arch) |

### Software Necessário

1. **Python 3.11+** — [python.org](https://python.org)
2. **uv** (gerenciador de pacotes) — `pip install uv` ou [astral.sh/uv](https://github.com/astral-sh/uv)
3. **Ollama** (modelos locais) — [ollama.ai](https://ollama.ai)
4. **Chrome/Chromium** com CDP habilitado (porta 9222)

---

## 🚀 Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/laya-ultrafast.git
cd laya-ultrafast

# 2. Instale dependências com uv
uv sync --dev

# 3. Instale modelos locais recomendados
./scripts/install_models.sh

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env se necessário

# 5. Inicie o Chrome com CDP (em outro terminal)
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-laya

# 6. Execute seu primeiro agente!
python -m laya_ultrafast --goal "Pesquise por 'LAYA automação' na Wikipedia" --max-steps 10
```

---

## ⚙️ Configuração

Copie `.env.example` para `.env` e ajuste conforme necessário:

```bash
# Modelo (Ollama padrão)
LAYA_MODEL_PROVIDER=ollama
LAYA_MODEL_NAME=llama3.1:8b-instruct-q4_K_M
LAYA_MODEL_ENDPOINT=http://localhost:11434/v1
LAYA_MODEL_TEMPERATURE=0.1
LAYA_MODEL_MAX_TOKENS=512
LAYA_MODEL_NUM_CTX=4096
LAYA_MODEL_SEED=42              # Seed fixa para reprodutibilidade

# Navegador
LAYA_BROWSER_CDP_URL=http://localhost:9222
LAYA_BROWSER_HEADLESS=true
LAYA_BROWSER_VIEWPORT_WIDTH=1280
LAYA_BROWSER_VIEWPORT_HEIGHT=720

# Engine
LAYA_MAX_STEPS=25
LAYA_GLOBAL_TIMEOUT_S=300
LAYA_HISTORY_MAX_STEPS=10
LAYA_ENABLE_INCREMENTAL_SNAPSHOT=true
LAYA_CHECKPOINT_INTERVAL_STEPS=5

# Performance
LAYA_INFERENCE_POOL_SIZE=2
LAYA_GEOMETRY_BATCH_SIZE=50
LAYA_METRICS_ENABLED=true

# Logging
LAYA_LOG_LEVEL=INFO
LAYA_LOG_FORMAT=json
LAYA_DEBUG=false
```

### Modelos Suportados

| Modelo | Provedor | Contexto | Quantização | Uso Recomendado |
|--------|----------|----------|-------------|-----------------|
| `llama3.1:8b-instruct-q4_K_M` | Ollama | 128K | Q4_K_M | **Padrão** — equilíbrio qualidade/velocidade |
| `mistral:7b-instruct-q4_K_M` | Ollama | 32K | Q4_K_M | Rápido, bom para JSON estruturado |
| `phi3:mini-instruct-4k-q4` | Ollama | 4K | Q4 | Muito rápido, tarefas simples |
| `qwen2.5:7b-instruct-q4_K_M` | Ollama | 32K | Q4_K_M | Multilíngue forte |
| `meta-llama/Meta-Llama-3.1-8B-Instruct` | vLLM/OpenAI | 128K | Auto | Via endpoint OpenAI-compatível |

---

## 💻 Uso

### CLI Básico

```bash
# Meta simples
python -m laya_ultrafast --goal "Acesse wikipedia.org e pesquise por 'Python'"

# Com URL inicial e mais passos
python -m laya_ultrafast \
  --goal "Preencha o formulário de contato" \
  --url "https://example.com/contact" \
  --max-steps 15

# Modo debug (salva snapshots)
LAYA_DEBUG=true python -m laya_ultrafast --goal "..."

# Modelo customizado
python -m laya_ultrafast --goal "..." --model "mistral:7b-instruct-q4_K_M"
```

### Arquivo de Tarefas (Múltiplos Objetivos)

Crie `tasks.json`:

```json
[
  {
    "goal": "Pesquise por 'LAYA' na Wikipedia",
    "url": "https://wikipedia.org",
    "max_steps": 10
  },
  {
    "goal": "Acesse GitHub Trending e abra o primeiro repo",
    "url": "https://github.com/trending",
    "max_steps": 12
  }
]
```

Execute:
```bash
python -m laya_ultrafast --task-file tasks.json
```

### Python API

```python
import asyncio
from laya_ultrafast.agent import LayaAgent

async def main():
    agent = LayaAgent()
    
    result = await agent.engine.run(
        goal="Pesquise por 'automação web' no DuckDuckGo",
        max_steps=10,
        initial_url="https://duckduckgo.com"
    )
    
    print(f"Sucesso: {result.success}")
    print(f"Passos: {result.steps_taken}")
    print(f"Mensagem: {result.final_message}")

asyncio.run(main())
```

---

## 📁 Estrutura do Projeto

```
laya-ultrafast/
├── pyproject.toml              # Configuração do projeto
├── .env.example                # Variáveis de ambiente
├── README.md                   # Esta documentação
├── AGENTS.md                   # Diretrizes para agentes de código
├── laya_ultrafast/
│   ├── __init__.py
│   ├── agent.py                # Fachada principal (CLI + API)
│   ├── browser.py              # Camada CDP/Playwright
│   ├── model.py                # Clientes LLM (Ollama, OpenAI, llama.cpp)
│   ├── snapshot.js             # Extração atômica do DOM
│   ├── questions.py            # Prompts + parsing de decisões
│   ├── core/
│   │   ├── laya_engine.py      # Orquestrador principal
│   │   ├── action_executor.py  # Validação + execução de ações
│   │   ├── context_manager.py  # Sessão, histórico, checkpoints
│   │   └── exceptions.py       # Hierarquia de exceções
│   ├── utils/
│   │   ├── geometry.py         # Cálculos geométricos (bbox, viewport)
│   │   ├── dom.py              # Helpers de DOM/ElementSnapshot
│   │   ├── retry.py            # Políticas de retry + circuit breaker
│   │   └── metrics.py          # Coletor de métricas (p50/p95/p99)
│   └── config/
│       ├── settings.py         # Pydantic Settings
│       └── models.yaml         # Registry de modelos
├── tests/
│   ├── unit/                   # Testes unitários
│   ├── integration/            # Testes de integração (Chrome real)
│   └── fixtures/site/          # Site HTML local para testes offline
├── examples/
│   ├── basic_search.py         # Busca na Wikipedia
│   ├── form_filling.py         # Formulários complexos
│   ├── multi_step.py           # Fluxo multi-etapa com checkpoints
│   └── benchmark.py            # Benchmark customizado
├── benchmarks/
│   └── baseline.json           # Baseline de performance
└── scripts/
    ├── install_models.sh       # Instala modelos Ollama
    ├── run_agent.py            # Entry point CLI avançado
    └── benchmark.py            # Runner de benchmarks automatizados
```

---

## 🧪 Testes

```bash
# Todos os testes (unit + integração)
uv run pytest

# Apenas unitários com cobertura
uv run pytest tests/unit --cov=laya_ultrafast --cov-report=term-missing

# Integração (requer Chrome rodando na porta 9222)
uv run pytest tests/integration -v

# Contract tests (schemas Pydantic)
uv run pytest tests/integration/contract -v

# Com relatório HTML de cobertura
uv run pytest tests/unit --cov=laya_ultrafast --cov-report=html
```

### Testes Offline Determinísticos

Testes de integração rodam contra `tests/fixtures/site/` (HTML local) para evitar flakiness de rede externa.

---

## 📊 Benchmarks

```bash
# Executa todos os cenários (3 runs cada)
python scripts/benchmark.py --all

# Cenário específico
python scripts/benchmark.py --scenario search --runs 5

# Salva resultados comparando com baseline
python scripts/benchmark.py --all --output benchmarks/results.json
```

### Cenários de Benchmark

| Cenário | Descrição | Target p95 |
|---------|-----------|------------|
| `search` | Busca na Wikipedia (página estática) | < 800ms |
| `form_filling` | Formulário multi-campo | < 800ms |
| `navigation` | Navegação multi-página (GitHub) | < 800ms |
| `dynamic_content` | Conteúdo AJAX (DuckDuckGo) | < 800ms |
| `heavy_dom` | Página > 2000 elementos (MDN) | < 800ms |

### Baseline de Performance

Resultados esperados no hardware recomendado (ver `benchmarks/baseline.json`):

```json
{
  "search": {"p95_latency_ms": 650, "success_rate": 1.0},
  "form_filling": {"p95_latency_ms": 720, "success_rate": 0.95},
  "navigation": {"p95_latency_ms": 680, "success_rate": 1.0}
}
```

---

## 🔧 Desenvolvimento

### Quality Gates (pre-commit + CI)

```bash
# Instala hooks
uv run pre-commit install

# Roda todos os checks manualmente
uv run pre-commit run --all-files
```

**Gates obrigatórios:**
- ✅ `ruff check` + `ruff format` — lint e formatação
- ✅ `mypy --strict` — tipagem estrita (zero `Any`)
- ✅ `pytest` — testes com cobertura ≥ 85%
- ✅ `pip-audit` — zero CVEs críticos/altos
- ✅ `bandit` — zero findings de segurança alta

### Estrutura de Commits

```bash
# Commits convencionais
feat: adiciona suporte a modelo Phi-3
fix: corrige validação geométrica em click
docs: atualiza README com novos exemplos
refactor: simplifica context_manager
test: adiciona testes de contrato para OpenAI
```

---

## 🐛 Troubleshooting

### Chrome não conecta na porta 9222

```bash
# Verifique se Chrome está rodando com CDP
lsof -i :9222

# Inicie manualmente
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-laya
```

### Modelo não responde / timeout

```bash
# Verifique Ollama
curl http://localhost:11434/api/version

# Reinicie Ollama
ollama serve

# Teste modelo
ollama run llama3.1:8b-instruct-q4_K_M "Olá"
```

### Erro de memória / OOM

- Reduza `LAYA_MODEL_NUM_CTX` (ex: 2048)
- Use modelo menor (`phi3:mini`)
- Feche outras aplicações pesadas
- Considere GPU via `CUDA_VISIBLE_DEVICES=0`

### JSON inválido do modelo

O LAYA tenta recuperar automaticamente (2 re-prompts). Se persistir:
- Aumente `LAYA_MODEL_MAX_TOKENS`
- Reduza `LAYA_HISTORY_MAX_STEPS`
- Verifique se modelo suporta structured output

---

## 📖 Exemplos

Veja a pasta `examples/`:

- [`basic_search.py`](examples/basic_search.py) — Busca simples na Wikipedia
- [`form_filling.py`](examples/form_filling.py) — Formulários com múltiplos campos
- [`multi_step.py`](examples/multi_step.py) — Fluxo com checkpoints
- [`benchmark.py`](examples/benchmark.py) — Benchmark customizado

---

## ⚖️ Limitações Conhecidas

| Limitação | Status | Mitigação |
|-----------|--------|-----------|
| **Único contexto de navegação** | MVP | Nova aba detectada → `BLOCKED` |
| **iframes profundos** | Não suportado | Apenas frame principal no snapshot |
| **CAPTCHA / anti-bot** | Fora de escopo | `BLOCKED` imediato, sem bypass |
| **Upload/download de arquivos** | Não suportado | Backlog futuro |
| **Páginas com WebGL/Canvas pesado** | Limitado | Elementos não interativos ignorados |

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie branch: `git checkout -b feat/nova-funcionalidade`
3. Commit: `git commit -m "feat: descrição clara"`
4. Push: `git push origin feat/nova-funcionalidade`
5. Abra Pull Request

**Requisitos para PR:**
- Todos os quality gates passando localmente
- Cobertura de testes ≥ 85%
- Docstrings em português (Google style)
- ADR atualizado se decisão arquitetural

---

## 📄 Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

## 🙏 Agradecimentos

- [browser-use](https://github.com/browser-use/browser-use) — inspiração arquitetural
- [Ollama](https://ollama.ai) — modelos locais acessíveis
- [Playwright](https://playwright.dev) — automação de navegador robusta
- [Pydantic](https://pydantic.dev) — validação de dados

---

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/laya-ultrafast/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/laya-ultrafast/discussions)
- **Docs**: Este README + docstrings no código

---

*Feito com ❤️ para automação web local, privada e rápida.*