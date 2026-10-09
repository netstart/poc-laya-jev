# AGENTS — Especificações e Orientações do Projeto

Este arquivo é o ponto de entrada obrigatório para agentes de inteligência artificial, coding agents e ferramentas automatizadas que trabalhem neste repositório.

## 1. Propósito

Todas as especificações, arquitetura, regras, tarefas e orientações deste projeto estão concentradas na pasta `.ai` e são referenciadas aqui para garantir que agentes automatizados consigam localizá-las rapidamente.

## 2. Regra de Localização

- Nenhuma especificação relevante está espalhada pela raiz ou por pastas aleatórias.
- Todos os arquivos de especificação, arquitetura, regras, tarefas e orientações devem ficar dentro da pasta `.ai`.
- Este arquivo (`agents.md`) é o índice oficial e deve ser mantido atualizado.

## 3. Arquivos de Especificação

### 3.1 Especificação Principal

| Arquivo | Descrição |
|---|---|
| `.ai/spec/001-prompt-busca-que-entende.md` | Especificação completa da aplicação **Busca que Entende** — substituição do JEV pelo LAYA, arquitetura local, stack, frontend, backend, testes, scripts de execução, benchmarks, critérios de aceitação e ordem de implementação. |
| `.ai/spec/002-especificacao-interface-busca-comparativa.md` | Detalhamento do comportamento da interface de busca comparativa entre busca tradicional e busca com LAYA, incluindo regras de identificação de itens em cada coluna. |
| `.ai/spec/003-legendas-resultados-busca-comparativa.md` | Especificação das legendas explicativas por lado, significados de cores, números, badges e comportamento separado das colunas. |
| `.ai/spec/004-botao-catalogo-completo.md` | Especificação do botão de catálogo completo, incluindo catálogo fixo à esquerda por categoria, transparência para itens não selecionados e borda verde para itens selecionados após a busca. |
| `.ai/fix/002-fix-balcao2-laya-scoring.md` | Plano de correção para o Balcão 2 — LAYA retornando 0 boas opções. |

### 3.2 Como Usar

1. Leia este `agents.md` para localizar as especificações.
2. Abra os arquivos listados na seção 3.1.
3. Implemente exatamente o que está definido nas especificações.
4. Se houver conflito entre arquivos, a especificação mais recente ou mais detalhada prevalece.
5. Quando terminar, atualize este índice se novos arquivos de especificação forem adicionados.

## 4. Estrutura Esperada do Projeto

```
busca-que-entende/
├── app/
│   ├── main.py
│   ├── laya_engine.py
│   ├── search_engine.py
│   ├── ranking.py
│   ├── orcamento.py
│   ├── cache.py
│   ├── schemas.py
│   └── config.py
├── model/
│   └── README.md
├── data/
│   └── catalogo.json
├── public/
│   ├── index.html
│   ├── app.js
│   ├── busca.css
│   ├── keyword.js
│   └── fonts/
├── tests/
│   ├── test_laya.py
│   ├── test_ranking.py
│   ├── test_orcamento.py
│   ├── test_api.py
│   └── test_e2e.py
├── scripts/
│   ├── setup_model.py
│   ├── benchmark.py
│   └── verify_offline.py
├── docs/
│   └── architecture.md
├── data-runtime/
│   ├── stats.json
│   ├── cache/
│   └── logs/
├── requirements.txt
├── .gitignore
├── README.md
├── run.py
├── run.sh
└── run.ps1
```

## 5. Regra Fundamental

Esta aplicação é **100% local**. Não depende de:
- VPS
- Hostinger
- API externa de LLM
- OpenRouter
- JEV
- Docker obrigatório
- Serviço SaaS
- Chave de API

O único acesso externo permitido é o download inicial dos pesos do modelo LAYA, se necessário. Depois disso, a inferência funciona **offline**.

## 6. Comando Único

O usuário deve conseguir executar a aplicação com um único comando:

```bash
./run.sh
```

ou no Windows:

```powershell
.\run.ps1
```

## 7. Motor de Busca

- **Frontend**: HTML, CSS, JavaScript vanilla (preservar original).
- **Backend**: Python + FastAPI + Uvicorn.
- **Motor de decisão**: LAYA local (substitui JEV).
- **Busca tradicional**: `public/keyword.js` preservada.
- **Modelo**: `laya-multilingual`.

## 8. Porta Padrão

```
http://127.0.0.1:4111
```

## 9. Critérios de Aceitação

Consulte `.ai/spec/prompt-busca-que-entende.md` seção 66 para a lista completa de critérios de aceitação.

## 10. Ordem de Implementação

Consulte `.ai/spec/prompt-busca-que-entende.md` seção 80 para a ordem de implementação recomendada (Fase 1 a Fase 20).

## 11. Convenção de Nomenclatura

Todos os arquivos `.md` dentro da pasta `.ai` devem seguir a seguinte convenção de nomenclatura:

- O nome do arquivo deve começar com um **número sequencial** que identifica a ordem de criação.
- Formato: `NNN-nome-do-arquivo.md`
- Exemplos:
  - `.ai/spec/001-prompt-busca-que-entende.md`
  - `.ai/fix/002-fix-balcao2-laya-scoring.md`
  - `.ai/adr/001-usar-fastapi.md`

O número sequencial deve ser único dentro de cada subpasta da `.ai` e crescente em ordem de criação.

## 12. Como Contribuir com Novas Especificações

1. Crie o arquivo dentro de `.ai/` seguindo a convenção de nomenclatura com número sequencial.
2. Adicione uma linha neste `agents.md` na seção 3.1.
3. Mantenha o formato de tabela para legibilidade.

---

**Última atualização deste índice:** 2026-09-30
