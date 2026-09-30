# Arquitetura — Busca que Entende

## Visão Geral

A aplicação é 100% local. O usuário interage com uma interface web que consome um backend local executado em `127.0.0.1:4111`. Toda inferência de inteligência acontece na máquina do usuário, sem dependência de APIs externas.

```
┌───────────────────────┐
│      Navegador        │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Backend local         │
│ localhost:4111        │
│ FastAPI + Uvicorn     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Search Engine         │
│ - orçamento           │
│ - keyword search      │
│ - cache               │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ LayaEngine            │
│ Python                │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ LAYA                  │
│ laya-multilingual     │
│ local inference       │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Probabilidades        │
│ Score / Choice        │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Ranking               │
│ - orçamento           │
│ - ordenação           │
│ - filtros             │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ UI                    │
│ Cupom                 │
│ Balcão 1              │
│ Balcão 2              │
│ Recibo                │
│ Inspetor              │
└───────────────────────┘
```

## Fronteiras

### Fronteira Probabilística

A parte da aplicação que envolve decisão probabilística:

- **LAYA**: modelo local de decisão/classificação.
- Entrada: `state` + `questions`.
- Saída: `choice`, `score`, `probabilities`, `confidence`.

Esta é a única parte que não é determinística.

### Fronteira Determinística

Tudo que vem antes e depois do LAYA é determinístico:

- **Orçamento**: extração e bucketing deterministicamente por regex.
- **Busca por palavra-chave**: TF-IDF + sinônimos + stopwords.
- **Cache**: LRU com chave normalizada.
- **Ranking**: ordenação por score, depois preço.
- **Filtros**: orçamento, limiares (`score >= 1`, `score >= 2`, etc.).
- **UI**: estados, animações, layout.

## Camadas

### Frontend

- `public/index.html`: estrutura da página.
- `public/busca.css`: estilo anos 70.
- `public/app.js`: integração com API e renderização.
- `public/keyword.js`: busca tradicional preservada.

### Backend

- `app/main.py`: FastAPI, endpoints, startup.
- `app/config.py`: configurações centralizadas.
- `app/schemas.py`: modelos Pydantic.
- `app/cache.py`: cache LRU local.
- `app/orcamento.py`: parsing determinístico de orçamento.
- `app/ranking.py`: ordenação e filtros.
- `app/search_engine.py`: orquestração das buscas.
- `app/laya_engine.py`: abstração do LAYA.

### Modelo

- LAYA executado localmente via `laya-multilingual`.
- Carregado uma única vez na inicialização.
- Reutilizado por todas as requisições.

### Dados

- `data/catalogo.json`: 120 produtos (somente leitura).
- `data-runtime/cache/`: cache em disco.
- `data-runtime/logs/`: logs da aplicação.

## Decisões

- **Sem Docker**: executado diretamente na máquina do usuário.
- **Sem API key**: inferência 100% local.
- **Single command**: `./run.sh` ou `.\run.ps1`.
- **Frontend vanilla**: sem frameworks pesados.
- **Backend Python**: FastAPI + Uvicorn.
