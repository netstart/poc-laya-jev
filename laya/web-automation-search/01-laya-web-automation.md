# Plano de Implementação: LAYA UltraFast Web Automation Agent

## Visão Geral

Criar um agente de automação web de alta performance (nos moldes do repositório `browser-use/jev-ultrafast`), substituindo completamente a dependência externa do **JEV** (Just-in-Time Environment Vision / Cloud Vision Services) por uma arquitetura proprietária e local chamada **LAYA** (Local Agent for Yielding Actions).

**Objetivo:** Rodar automação web localmente, ultra-rápida, barata, sem depender de nuvens proprietárias, consumindo estados estruturados do DOM em vez de screenshots pesados.

**Escopo do MVP:**
- Automação em um único contexto de navegação (uma aba/janela CDP — ADR-006)
- Operações da §1: navegar, clicar, digitar, selecionar, rolar, esperar e voltar
- Modelos locais até 8B de parâmetros, quantizados (Q4_K_M)

**Não-objetivos (detalhados na §8):** visão multimodal/screenshot-based, bypass de CAPTCHA/anti-bot, automação mobile, múltiplas abas/iframes aninhados, uploads/downloads de arquivos.

**Fluxo de um ciclo do agente:**

```
snapshot.js (DOM → ElementSnapshot[])
   → questions.py (estado + goal + histórico → prompt)
   → LLM local (structured output → AgentDecision)
   → validação Pydantic + frescura da página (§4.5)
   → action_executor (validações geométricas → ação no browser)
   → verificação (URL/DOM mudou?) → próximo ciclo ou DONE/BLOCKED
```

---

## 1. Requisitos Técnicos

| Item | Especificação |
|------|---------------|
| **Linguagem** | Python 3.11+ com tipagem estrita (`mypy --strict`) |
| **Gerenciamento de deps** | `uv` (compatível com `pyproject.toml`) |
| **Automação de Navegador** | Playwright via CDP como backend único (ADR-002); conexão CDP persistente para renderização contínua e controle atômico do DOM |
| **Extração de Estado (DOM Snapshot)** | Script JS injetado (`snapshot.js`) que mapeia elementos interativos atômicos → tabela indexada com rótulos limpos, `aria-labels`, bounding boxes, seletores CSS/XPath |
| **Motor de Decisão (LAYA Core)** | LLM local leve (Ollama: Llama 3 / Mistral / Phi-3, ou endpoints compatíveis OpenAI via vLLM/Llama.cpp) — recebe estado textual estruturado, retorna operação + target_id em único ciclo |
| **Formato de Decisão** | Structured output nativo (Ollama `format` com JSON Schema / OpenAI `response_format`); fallback: parsing tolerante + validação Pydantic (§4.4) |
| **Operações Suportadas** | `CLICK`, `TYPE_TEXT`, `SELECT`, `SCROLL_UP`, `SCROLL_DOWN`, `WAIT`, `DONE`, `BLOCKED`, `NAVIGATE`, `GO_BACK` |
| **Executor Local** | Valida frescura da página, verifica visibilidade/obstrução geométrica antes de clicar, preenchimento de texto condicional, retry com backoff exponencial |
| **Concorrência** | `asyncio` nativo; pool de workers para inferência paralela (se múltiplos modelos) |
| **Observabilidade** | Logs estruturados (JSON), métricas de latência (p50/p95/p99), tracing opcional (OpenTelemetry) |

---

## 2. Estrutura de Diretórios

```
laya-ultrafast/
├── pyproject.toml              # Configuração do projeto, deps, scripts, tooling
├── .env.example                # Variáveis de ambiente (model endpoint, timeouts, etc.)
├── README.md                   # Documentação principal em PT-BR
├── AGENTS.md                   # Diretrizes para agentes de código (derivadas deste plano)
├── laya_ultrafast/
│   ├── __init__.py
│   ├── agent.py                # Loop principal assíncrono do agente
│   ├── browser.py              # Camada CDP/Playwright: conexão, geometria, execução de ações
│   ├── model.py                # Interface LLM local (OpenAI-compatible + Ollama nativo)
│   ├── snapshot.js             # Script JS injetado para extração atômica do DOM
│   ├── questions.py            # System prompts + engenharia de instruções
│   ├── core/
│   │   ├── __init__.py
│   │   ├── laya_engine.py      # Orquestrador: snapshot → decisão → execução → validação
│   │   ├── context_manager.py  # Gerenciamento de estado de sessão (histórico, cache, checkpoints)
│   │   ├── action_executor.py  # Executor robusto com validações geométricas
│   │   └── exceptions.py       # Hierarquia de exceções customizadas
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── geometry.py         # Cálculos de bounding box, sobreposição, viewport
│   │   ├── dom.py              # Helpers de parsing/normalização de DOM
│   │   ├── retry.py            # Políticas de retry/backoff
│   │   └── metrics.py          # Coletor de métricas de performance
│   └── config/
│       ├── __init__.py
│       ├── settings.py         # Pydantic Settings (validação de config)
│       └── models.yaml         # Registry de modelos suportados + parâmetros
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│       └── site/                # Site HTML local p/ testes offline e determinísticos (§9.3)
├── examples/
│   ├── basic_search.py         # Busca na Wikipedia (Google fora do escopo: anti-bot, §8)
│   ├── form_filling.py         # Preenchimento de formulários complexos
│   └── multi_step.py           # Fluxo multi-etapa com checkpoints
├── benchmarks/
│   └── baseline.json           # Baseline de performance versionada (§9.2)
└── scripts/
    ├── install_models.sh       # Download/configuração de modelos locais
    ├── run_agent.py            # Entry point CLI
    └── benchmark.py            # Runner de benchmarks automatizados
```

---

## 3. Diretrizes de Implementação

### 3.1 Princípios Arquiteturais
- **Zero Screenshots no Loop Principal:** Priorizar estado textual estruturado + atributos ARIA → economia de tokens e latência
- **Local-First por Default:** Todas configs apontam para modelos 100% locais (Ollama, vLLM, Llama.cpp) — privacidade e custo zero de API
- **Validação Geométrica Obrigatória:** Antes de qualquer `CLICK`, confirmar visibilidade, `opacity > 0`, `z-index`, ausência de sobreposição, elemento dentro do viewport
- **Imutabilidade de Estado:** Snapshots do DOM são imutáveis; cada ciclo gera novo snapshot versionado
- **Fail-Fast com Contexto:** Exceções devem carregar snapshot ID, target_id, operação tentada, timestamp
- **Determinismo:** `temperature` baixa + `seed` fixa para decisões reprodutíveis; animações CSS reduzidas via injeção; user-agent identificável (`LAYA-Bot`)

### 3.2 Qualidade de Código
- **Tipagem:** `mypy --strict` em CI; `pyright` como backup; zero `Any` em código de produção
- **Lint/Format:** `ruff` (lint + format), `pre-commit` hooks obrigatórios
- **Testes:** 
  - Unitários: ≥ 85% cobertura (`pytest-cov`)
  - Integração: Testes contra Chrome real (headless + headed) via Playwright
  - Contract: Validação de schemas de request/response do modelo (Pydantic)
- **Documentação:** Docstrings em português (Google style); type hints completos; README com exemplos executáveis

### 3.3 Performance
| Métrica | Target | Estratégia |
|---------|--------|------------|
| Latência snapshot→ação (p95) | < 800ms | DOM textual apenas, inferência local, cache de seletores |
| Throughput (ações/min) | > 40 | Pool de inferência, reuso de conexão CDP, snapshots incrementais |
| Memória (steady state) | < 500MB | Stream parsing, limpeza proativa de histórico antigo |
| Cold start | < 3s | Lazy load de modelo, conexão CDP persistente |

**Otimizações-chave:**
- Snapshots incrementais (diff do DOM) em vez de full snapshot a cada ciclo
- Cache de seletores CSS/XPath válidos por sessão
- Batch de validações geométricas via `page.evaluate()` único
- Modelo quantizado (4-bit/8-bit) + `flash_attention` quando disponível
- `asyncio.TaskGroup` para operações paralelas independentes

### 3.4 Segurança e Isolamento
- Nenhuma telemetria externa; zero chamadas de rede não iniciadas pelo usuário
- Sandbox do navegador: `--no-sandbox` apenas em CI controlado; perfil Chrome dedicado
- Sanitização de inputs antes de injetar no JS (`snapshot.js`)
- Validação de resposta do modelo contra schema Pydantic antes de executar
- **Mascaramento de dados sensíveis** em logs e checkpoints: valores digitados em campos `password` e tokens nunca são persistidos

---

## 4. Módulos Principais — Contratos e Responsabilidades

### 4.1 `laya_ultrafast/snapshot.js`
- **Entrada:** `document` + config (seletores permitidos, atributos ARIA, threshold de visibilidade)
- **Saída:** JSON array de `ElementSnapshot { id, tag, role, label, bbox, selector, attrs, is_visible, is_obstructed }`
- **Requisitos:** Execução < 50ms em páginas típicas; sem dependências externas; ES2020+

### 4.2 `laya_ultrafast/browser.py`
- `BrowserSession` — gerencia ciclo de vida CDP/Playwright
- `connect(cdp_url?) → BrowserSession`
- `snapshot() → List[ElementSnapshot]`
- `execute(action: Action) → ExecutionResult`
- `navigate(url) → NavigationResult`
- `close() → None`
- **Contrato:** Thread-safe para uso assíncrono; reconexão automática com backoff

### 4.3 `laya_ultrafast/model.py`
- `LocalModelClient` (protocol) — `complete(prompt: str, schema: Type[BaseModel]) → BaseModel`
- Implementações: `OllamaClient`, `OpenAICompatibleClient`, `LlamaCppClient`
- **Config:** `model_name`, `temperature`, `max_tokens`, `timeout`, `num_ctx`, `num_predict`
- **Resiliência:** Circuit breaker, fallback para modelo menor, retry com jitter

### 4.4 `laya_ultrafast/questions.py`
- `SYSTEM_PROMPT` — instruções base (papel, formato de resposta JSON estrito)
- `build_prompt(snapshot: List[ElementSnapshot], goal: str, history: List[Action]) → str`
- `parse_response(raw: str) → AgentDecision` (validação Pydantic)
- **Schema da decisão** (Pydantic; reutilizado como JSON Schema do structured output):
  `AgentDecision { operation: Operation, target_id: int | None, text: str | None, value: str | None, scroll_px: int | None, reason: str }`
- **Recuperação de JSON inválido:** até 2 re-prompts anexando o erro de validação; esgotadas → decisão `BLOCKED` com o motivo (fail-fast, §3.1)

### 4.5 `laya_ultrafast/core/laya_engine.py`
- Orquestra: `snapshot → build_prompt → model.complete → validate → execute → verify → loop`
- **Frescura da página (anti-TOCTOU):** antes de executar, re-snapshot barato do `target_id`; se o elemento sumiu ou mudou de bounding box → descarta ação e reinicia o ciclo com snapshot completo
- **Gestão de contexto:** histórico truncado para os últimos `LAYA_HISTORY_MAX_STEPS` passos (com sumário dos anteriores) para não estourar `num_ctx`
- **Timeout global:** aborta e emite `RunResult` parcial ao exceder `LAYA_GLOBAL_TIMEOUT_S`
- Gerencia checkpoints de sessão (serialização periódica do estado)
- Expõe `run(goal: str, max_steps: int = 25) → RunResult` (default alinhado a `LAYA_MAX_STEPS`)

### 4.6 `laya_ultrafast/core/action_executor.py`
- `execute_click(element: ElementSnapshot) → ExecutionResult`
- `execute_type(element: ElementSnapshot, text: str) → ExecutionResult`
- `execute_select(element: ElementSnapshot, value: str) → ExecutionResult`
- `execute_scroll(direction: str, amount: int) → ExecutionResult` (preferir `scrollIntoView` no `target_id` quando houver; quantitativo como fallback)
- `execute_navigate(url: str) → NavigationResult` / `execute_go_back() → ExecutionResult`
- `execute_wait(ms: int) → ExecutionResult`
- `DONE`/`BLOCKED` são decisões de término tratadas pelo orquestrador (§4.5), não por este executor
- Validações: `is_in_viewport`, `not_obstructed`, `is_enabled`, `stable_position`

### 4.7 `laya_ultrafast/core/context_manager.py`
- `SessionContext` — histórico de ações, snapshots, decisões, métricas
- `checkpoint() → bytes` / `restore(bytes) → SessionContext`
- TTL configurável para limpeza automática

---

## 5. Configuração (`.env.example`)

```bash
# Modelo Local (Ollama padrão)
LAYA_MODEL_PROVIDER=ollama
LAYA_MODEL_NAME=llama3.1:8b-instruct-q4_K_M
LAYA_MODEL_ENDPOINT=http://localhost:11434/v1
LAYA_MODEL_TEMPERATURE=0.1
LAYA_MODEL_MAX_TOKENS=512
LAYA_MODEL_NUM_CTX=4096
LAYA_MODEL_SEED=42                # Seed fixa p/ decisões reprodutíveis (§3.1)

# Navegador
LAYA_BROWSER_CDP_URL=http://localhost:9222
LAYA_BROWSER_HEADLESS=true
LAYA_BROWSER_VIEWPORT_WIDTH=1280
LAYA_BROWSER_VIEWPORT_HEIGHT=720

# Engine
LAYA_MAX_STEPS=25                 # Teto de passos por execução (default de run())
LAYA_GLOBAL_TIMEOUT_S=300         # Aborta run() e emite RunResult parcial (§4.5)
LAYA_HISTORY_MAX_STEPS=10         # Passos de histórico mantidos no prompt (§4.5)
LAYA_SNAPSHOT_INTERVAL_MS=100
LAYA_ACTION_TIMEOUT_MS=10000
LAYA_ENABLE_INCREMENTAL_SNAPSHOT=true  # Diff de DOM entre ciclos (ADR-004)
LAYA_CHECKPOINT_INTERVAL_STEPS=5
LAYA_DEBUG=false                  # Persiste snapshots/decisões p/ inspeção (§9.4)

# Performance
LAYA_INFERENCE_POOL_SIZE=2        # Workers p/ N agentes paralelos (1 modelo local)
LAYA_GEOMETRY_BATCH_SIZE=50
LAYA_METRICS_ENABLED=true

# Logging
LAYA_LOG_LEVEL=INFO
LAYA_LOG_FORMAT=json
```

---

## 6. Entregáveis (Definition of Done)

1. **Código-fonte completo** em `laya_ultrafast/` seguindo a estrutura acima
2. **Testes** passando (unit + contrato + integração) com cobertura ≥ 85%, conforme §3.2 e gates da §9.1
3. **Documentação:**
   - `README.md` em PT-BR: instalação, pré-requisitos hardware, modelos locais, execução, troubleshooting
   - `AGENTS.md` derivado deste plano, atualizado com a implementação real
   - Docstrings em todos os módulos públicos
4. **Scripts de inicialização:**
   - `scripts/install_models.sh` — baixa/configura modelos Ollama recomendados
   - `scripts/run_agent.py` — CLI com args: `--goal`, `--max-steps`, `--headless`, `--model`
5. **Benchmarks** automatizados (`scripts/benchmark.py`) com relatório de latência/throughput/memória/taxa de sucesso e comparação contra `benchmarks/baseline.json` (§9.2)
6. **CI/CD** (GitHub Actions): lint, type-check, testes, gates de segurança e benchmark de regressão (§9.1–§9.2), build, publicação de artefatos

---

## 7. Pré-requisitos de Hardware (Recomendado)

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| CPU | 4 cores / 2.5 GHz | 8+ cores / 3.5 GHz (AVX2/AVX-512) |
| RAM | 16 GB | 32+ GB |
| GPU (opcional) | — | NVIDIA 8GB+ VRAM (CUDA 12+) para aceleração `llama.cpp`/`vLLM` |
| Disco | 10 GB livres | SSD NVMe 50+ GB livres |
| SO | Linux/macOS/WSL2 | Linux (Ubuntu 22.04+ / Arch) |

---

## 8. Riscos, Limitações e Mitigações

| Item | Limitação | Estratégia |
|------|-----------|------------|
| Multi-abas/popups | MVP opera com um único contexto de navegação (ADR-006) | Novo contexto detectado → `BLOCKED` com motivo claro; extensão futura via ADR |
| iframes profundos | Snapshot cobre apenas o frame principal | Limitação documentada no README; extensão futura percorrendo frames |
| CAPTCHA / anti-bot | Fora de escopo por decisão de escopo e ética | `BLOCKED` imediato; nenhum bypass será implementado |
| Uploads/downloads | Não suportados no MVP | Backlog; fora dos targets de benchmark |
| JSON inválido do LLM | Modelos ≤ 8B erram formato com alguma frequência | Structured output nativo + retry com erro de validação (§4.4) → `BLOCKED` |
| Página muda entre decisão e ação (TOCTOU) | Risco de agir sobre elemento obsoleto | Re-snapshot de frescura antes da execução (§4.5) |
| LLM local lento em CPU | p95 da §3.3 pode não ser atingido sem GPU | Q4_K_M + `num_ctx` enxuto; hardware da §7 é pré-requisito de performance |
| Site real indisponível nos testes | Flakiness externa | CI determinístico contra `tests/fixtures/site/` (§9.3); sites reais apenas em soak/manual |

---

## 9. Garantia de Qualidade e Performance

As seções §3.2 e §3.3 definem *o que* é esperado; esta seção define *como* verificar e o que bloqueia a entrega quando o padrão não é cumprido.

### 9.1 Quality Gates (obrigatórios — falha bloqueia o merge)

| Gate | Ferramenta | Critério de aprovação |
|------|-----------|----------------------|
| Lint + formatação | `ruff check` + `ruff format --check` | zero erros |
| Tipagem | `mypy --strict` + `pyright` | zero erros, zero `Any` em código de produção |
| Testes unitários | `pytest tests/unit --cov` | todos passam; cobertura ≥ 85% (§3.2) |
| Testes de contrato | `pytest tests/integration/contract` | schemas Pydantic válidos para todos os providers de modelo |
| Testes de integração | `pytest tests/integration` (Chrome real via Playwright) | todos passam em modo headless e headed |
| Segurança de dependências | `pip-audit` | zero CVEs de severidade alta/crítica |
| Código inseguro | `bandit` | zero findings de severidade alta |

- Os gates rodam localmente via `pre-commit` e são re-executados no CI (GitHub Actions); qualquer falha bloqueia o merge.
- `skip`/`xfail` silenciosos são proibidos: testes desabilitados exigem `reason=` com issue vinculada.

### 9.2 Validação de Performance (pipeline de benchmark)

1. `scripts/benchmark.py` roda em CI dedicado a cada PR que altere `core/`, `browser.py`, `snapshot.js`, `model.py` ou `questions.py`.
2. **Baseline versionada** em `benchmarks/baseline.json`: p50/p95 de latência snapshot→ação, throughput, pico de memória e duração do `snapshot.js`.
3. **Regra de regressão:** piora > 10% em p95 ou > 15% em memória falha o CI; regressão só é aceita com justificativa em ADR + atualização da baseline no mesmo PR.
4. **Cenários mínimos do benchmark:**
   - Página estática (busca na Wikipedia) — caminho feliz;
   - DOM dinâmico (resultados via AJAX) — valida `WAIT` e snapshots incrementais (ADR-004);
   - Formulário longo multi-etapa — valida `TYPE_TEXT`/`SELECT` em massa;
   - Página pesada (> 2.000 elementos interativos) — valida o orçamento de < 50ms do `snapshot.js` (§4.1) e o teto de tokens do prompt.
5. **Gate de aceite:** todos os targets da tabela de §3.3 **e taxa de conclusão de goal ≥ 90%** por cenário devem ser atingidos antes do merge (latência sem sucesso de tarefa não conta como performance)

### 9.3 Estabilidade, Vazamento de Memória e Resiliência

- **Soak test:** ≥ 500 passos contínuos contra páginas reais; memória em steady state < 500MB e sem crescimento linear (amostragem a cada 50 passos).
- **Idempotência de checkpoint:** roundtrip `checkpoint() → restore()` preserva histórico, decisões e métricas (teste automatizado).
- **Resiliência CDP:** reinício do navegador no meio da execução → reconexão automática com backoff e retomada do último checkpoint (teste automatizado).
- **Testes offline:** integração e benchmark de CI rodam contra `tests/fixtures/site/` (HTML local, sem internet); sites reais ficam restritos a soak test e validação manual
- **Flakiness:** testes de integração rodam 3× seguidas no CI; qualquer instabilidade é corrigida como bug — nunca mascarada com retry cego

### 9.4 Observabilidade na Execução

- Cada ciclo emite log JSON com: `step`, `snapshot_id`, `target_id`, `ação`, `latência_snapshot_ms`, `latência_inferência_ms`, `latência_execução_ms`, `tokens_prompt`, `tokens_completion` (alimenta as métricas descritas na §1).
- `RunResult.metrics` agrega p50/p95/p99 ao final de cada execução; exportação via OpenTelemetry opcional.
- `LAYA_DEBUG=true` persiste snapshots e decisões em disco para inspeção pós-execução; o CI anexa esses arquivos como artefato quando um teste falha.

### 9.5 Checklist de Aceite (Definition of Quality)

- [ ] Todos os gates da §9.1 verdes em local e CI
- [ ] Benchmark da §9.2 dentro dos targets da §3.3 e sem regressão vs baseline
- [ ] Soak test e testes de resiliência da §9.3 aprovados
- [ ] Logs estruturados com métricas de latência presentes em pelo menos um exemplo executável
- [ ] Nenhuma chamada de rede além das iniciadas pelo usuário (verificado com interceptador de rede em teste E2E)
- [ ] `README.md` e docstrings refletindo exatamente a implementação entregue

---

## 10. Próximos Passos (Ordem de Execução)

1. `pyproject.toml` + `.env.example` + config de `ruff`/`mypy`/`pytest` + `pre-commit`
2. `laya_ultrafast/config/settings.py` + `models.yaml`
3. `laya_ultrafast/snapshot.js` (testado isoladamente no DevTools)
4. `laya_ultrafast/browser.py` (conexão CDP + snapshot básico)
5. `laya_ultrafast/model.py` (clientes Ollama/OpenAI-compatíveis)
6. `laya_ultrafast/questions.py` (prompts + parsing)
7. `laya_ultrafast/core/` (exceptions, geometry, retry, metrics, action_executor, context_manager, laya_engine)
8. `laya_ultrafast/agent.py` (fachada principal)
9. `tests/fixtures/site/` (site HTML local) + testes unitários, de contrato e de integração (cobertura ≥ 85%, §3.2)
10. `examples/` + `scripts/` (incl. `benchmark.py` + `benchmarks/baseline.json`, §9.2)
11. Quality gates e pipelines de CI (§9.1–§9.2)
12. `README.md` final + validação E2E + soak test (§9.3)

---

## 11. Decisões de Arquitetura Registradas (ADR Log)

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| 001 | Uso de DOM textual estruturado vs screenshots | Aceito | 2026-10-08 |
| 002 | Playwright/CDP como backend de navegador único | Aceito | 2026-10-08 |
| 003 | Ollama como provider padrão; suporte multi-provider via interface | Aceito | 2026-10-08 |
| 004 | Snapshots incrementais com diffing de DOM | Aceito | 2026-10-08 |
| 005 | Quantização 4-bit (Q4_K_M) como default para modelos ≤ 8B | Aceito | 2026-10-08 |
| 006 | MVP restrito a um único contexto de navegação (aba/janela); CAPTCHA/anti-bot, multimodal e uploads fora de escopo | Aceito | 2026-10-08 |

> **Nota:** Novas ADRs devem ser adicionadas aqui conforme decisões forem tomadas durante a implementação.