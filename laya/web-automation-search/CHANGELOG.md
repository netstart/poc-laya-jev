# Changelog

Todas as mudanças significativas do LAYA UltraFast são documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) e o versionamento segue [SemVer](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-08

### Added

- Arquitetura completa do agente LAYA (Local Agent for Yielding Actions)
- Camada de browser via Playwright/CDP com snapshot do DOM
- Clientes de modelo local: Ollama, OpenAI-compatible, llama.cpp
- Engine de orquestração com ciclo: snapshot → prompt → inferência → execução
- Executor de ações com validações geométricas (visibilidade, obstrução, estabilidade)
- Gerenciamento de contexto com checkpoints e restore
- Métricas de performance (p50/p95/p99, throughput, memória)
- Snapshot.js para extração atômica do DOM (< 50ms em páginas típicas)
- Sistema de retry com circuit breaker
- Testes unitários, de contrato e de integração
- Benchmarks automatizados com baseline versionada
- CI/CD com GitHub Actions (lint, type-check, testes, benchmarks)
- Pre-commit hooks (ruff, mypy, pytest)
- Documentação completa em PT-BR (README, AGENTS.md)
- Exemplos de uso (busca, formulário, multi-step, benchmark)
- Scripts de instalação de modelos locais e execução

### Changed

- Substitui dependência de nuvem (JEV) por arquitetura 100% local (LAYA)
- Passa de screenshots para estado textual estruturado do DOM
- Adiciona tipagem estrita (mypy --strict) em todos os módulos públicos
- Adiciona validação Pydantic em schemas de request/response do modelo
- Adiciona logging estruturado (JSON) com métricas de latência por ciclo

### Fixed

- TOCTOU race condition: validação de frescura da página antes de executar ações
- Resposta inválida do modelo: retry com re-prompt até 2 tentativas, depois BLOCKED
- Memory leak: limpeza proativa de histórico antigo no context_manager

### Security

- Zero telemetria externa
- Sanitização de inputs em snapshot.js
- Validação de resposta do modelo contra schema Pydantic antes de executar
- Mascaramento de dados sensíveis em logs e checkpoints

---

## [Unreleased]

### Planned

- Snapshots incrementais com diffing de DOM (ADR-004)
- Suporte a múltiplas abas/iframes (fora do MVP atual)
- OpenTelemetry tracing opcional
- ADR-007: Cache de seletores CSS/XPath por sessão