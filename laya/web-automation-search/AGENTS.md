# LAYA - Guidelines for Agents

> Este documento define as convenções e diretrizes para desenvolvedores e agentes de código trabalhando neste projeto LAYA (Local Agent for Yielding Actions).

## 🏗️ Estrutura do Código

```
/laya-ultrafast/
├── laya_ultrafast/           # Pacote principal Python
│   ├── __init__.py           # Exports principais
│   ├── agent.py              # Fachada CLI + API
│   ├── browser.py            # Playwright + CDP
│   ├── model.py              # Clientes LLM
│   ├── snapshot.js           # Extração DOM
│   ├── questions.py          # Prompts e parsing
│   ├── core/
│   │   ├── __init__.py
│   │   ├── laya_engine.py    # Orquestrador
│   │   ├── action_executor.py
│   │   ├── context_manager.py
│   │   └── exceptions.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── geometry.py
│   │   ├── dom.py
│   │   ├── retry.py
│   │   └── metrics.py
│   └── config/
│       ├── __init__.py
│       ├── settings.py
│       └── models.yaml
├── tests/                    # Testes
├── scripts/                  # Scripts utilitários
├── examples/                 # Exemplos executáveis
└── benchmarks/               # Baseline + métricas
```

## 📦 Commits e PRs

### Convencionais de Commits

```
feat:           Nova funcionalidade (ex.: novo modelo suportado)
fix:            Correção de bug (ex.: validação geométrica)
docs:           Atualização de documentação
refactor:       Reestruturação sem mudança de comportamento
test:           Adição ou melhoria de testes
chore:          Atualização de config/dependências (não afeta código)
perf:           Otimização de performance
```

### Requisitos para PR

| Item | Obrigatório |
|------|-------------|
| **Tests** | Pelo menos 1 teste unitário + cobertura ≥ 85% |
| **Docs** | Docstrings em Google style, README atualizado |
| **ADR** | Nova decisão arquitetural → novo ADR no topo de `README.md` |
| **Lint** | `ruff check` e `ruff format` verdes |
| **Type** | `mypy --strict` sem erros, zero `Any` em código de produção |
| **Benchmarks** | Se alterar `core/`, `browser.py`, `snapshot.js`, `model.py`, `questions.py`: benchmark CI passa |

### Padrão de Branches

```
main:           Código estável, tags de release
feature/*:      Novas funcionalidades (ex.: feature/laya-engine-v2)
fix/*:          Correções de bug
refactor/*:     Reestruturações
docs/*:         Atualizações de documentação
```

---

## 🧪 Testes

### Convenções

| Padrão | Descrição |
|--------|-----------|
| `test_*.py` | Arquivos de teste |
| `Test*.py` | Classes de teste |
| `test_*` | Funções começam com `test_` |
| Arrange-Act-Assert | Padrão AAA em todos testes |

### Tipos de Teste

| Tipo | Onde | Requisito |
|------|------|-----------|
| **Unitário** | `tests/unit/` | Cobertura ≥ 85%, rápido (< 2s) |
| **Contractual** | `tests/integration/contract/` | Validação de schemas Pydantic, mock de modelo |
| **Integração** | `tests/integration/` | Chrome real via Playwright, `--headed` + `--headless` |

### Estrutura de Teste

```python
def test_foo_succeeds():
    # Arrange
    agent = LayaAgent()
    
    # Act
    result = await agent.engine.run(goal="...")
    
    # Assert
    assert result.success
    assert result.steps_taken > 0
```

### Testes Offline (Fixtures)

```python
def test_parsing_deterministic():
    """Testa parsing de snapshot sem requisições de rede."""
    from laya_ultrafast.utils.dom import ElementSnapshot
    from laya_ultrafast.tests.fixtures import simple_html
    
    snapshot = extract_snapshot(simple_html)
    assert len(snapshot) > 0
    assert any(s.role == "button" for s in snapshot)
```

### Estrutura de Fixtures

```
tests/fixtures/site/
├── simple.html           # Página simples com botões/inputs
├── form.html             # Formulário completo
├── heavy.html            # Página > 2000 elementos
└── dynamic.html          # Conteúdo via AJAX (simulado)
```

---

## 🔧 Convenções de Código

### Python

| Convenção | Específicação |
|-----------|---------------|
| **Type Hints** | Obrigatório em todos os módulos públicos |
| **Docstrings** | Google style, em português |
| **Linha máxima** | 100 caracteres (ruff `--select=RUF`) |
| **Imports** | Sempre na ordem: stdlib → third-party → local |
| **Naming** | `snake_case` para funções/vars, `PascalCase` para classes, `UPPER_SNAKE` para constants |
| **Default args** | Nunca usar `Any` como default; usar `Optional[Tipo]` ou valor padrão sensato |

### Rust / JavaScript (snapshot.js)

| Convenção | Específicação |
|-----------|---------------|
| **ES2020+** | Modern JavaScript, sem transpilação necessária |
| **DOM APIs** | `getBoundingClientRect`, `getComputedStyle`, `querySelectorAll` |
| **Performance** | Execução < 50ms em páginas típicas |
| **Sanitização** | Sanitizar todos inputs antes de injetar no JS |

### YAML (models.yaml)

| Convenção | Específicação |
|-----------|---------------|
| **Chaves** | Sempre aspas duplas para strings |
| **Valores** | Asneiras quando necessário, mas números sem aspas |
| **Ordem** | Manter ordem alfabética dentro de grupos |

---

## 📋 Processo de Release

### Versionamento

```
MAJOR.MINOR.PATCH
ex: 0.1.0 → 0.2.0 → 1.0.0
```

### Checklist de Release

- [ ] Todos quality gates passando (`mypy`, `ruff`, `pytest`)
- [ ] Baseline de benchmarks atualizada (`benchmarks/baseline.json`)
- [ ] `README.md` com nova versão
- [ ] `AGENTS.md` atualizado
- [ ] `CHANGELOG.md` criado (se houver mudanças significativas)
- [ ] Tag git: `git tag v0.2.0` + `git push origin v0.2.0`
- [ ] Publicar no PyPI (opcional): `uv run build && twine upload dist/*`

---

## 🐛 Reporting Issues

### Modelo de Issue

```markdown
## Descrição
Descreva o problema de forma clara e concisa.

## Passos para reproduzir
1. Executa este comando: ...
2. Observe esse erro: ...

## Comportamento esperado
O que deveria acontecer?

## Ambiente
- SO: Ubuntu 22.04
- Python: 3.11.7
- Ollama: 0.3.5
- Modelo: llama3.1:8b-instruct-q4_K_M
- Chrome: 120.0.6099.109

## Contexto Adicional
Logs relevantes, snapshots, métricas.
```

### Etiquetas Sugeridas

| Etiqueta | Quando usar |
|----------|-------------|
| `bug` | Erro, comportamento inesperado |
| `enhancement` | Nova funcionalidade, melhoria |
| `documentation` | Docs faltando ou incorretas |
| `performance` | Métricas, latência, throughput |
| `security` | Vulnerabilidades |
| `good-first-issue` | Ideal para contribuidores novos |

---

## 📞 Comunicação

- **Slack/Discord**: `#laya-dev` (canal da comunidade)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/laya-ultrafast/discussions)
- **Email**: contato@laya-ai.dev (para assuntos sensíveis)

---

*Este documento segue as convenções de:*
- [Google's Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Conventional Commits](https://conventionalcommits.org)
- [Crafting reliable codebases with ADRs](https://adr.github.io)