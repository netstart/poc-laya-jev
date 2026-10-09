# Busca que Entende

Aplicação local de busca semântica/intencional para e-commerce, usando **LAYA** como modelo de decisão local. Substitui completamente serviços externos como JEV/OpenRouter por inferência 100% local.

## Como Executar

### Setup inicial (primeira vez)

```bash
python scripts/setup.py
```

Esse comando irá:
- criar/atualizar o ambiente virtual
- instalar todas as dependências, incluindo LAYA
- baixar o modelo `laya-multilingual`
- executar um smoke test automático

### Linux / macOS

```bash
./run.sh
```

### Windows PowerShell

```powershell
.\run.ps1
```

### Python direto

```bash
python run.py
```

Depois disso, abra: **http://127.0.0.1:4111**

## O que é

O usuário digita frases naturais como:

> "presente pra minha mãe que ama jardinagem até 150 reais"

A aplicação entende a intenção, avalia os 120 produtos do catálogo e compara:

- **Balcão 1**: busca tradicional por palavra-chave (`keyword.js`).
- **Balcão 2**: busca com LAYA — entende contexto, destinatário, ocasião e orçamento.

## Stack

- **Frontend**: HTML, CSS, JavaScript vanilla.
- **Backend**: Python 3.10+, FastAPI, Uvicorn.
- **Modelo**: LAYA local (`laya-multilingual`).
- **Dados**: `data/catalogo.json` (120 produtos).

## Estrutura

```
app/             Backend Python
data/            Catálogo
public/          Frontend
tests/           Testes automatizados
scripts/         Setup, benchmark, verificação offline
docs/            Arquitetura
data-runtime/    Cache e logs
```

## Como funciona o LAYA

O LAYA é um modelo de decisão/classificação local. Ele recebe estado + perguntas tipadas e devolve probabilidades. Não é um LLM generativo.

- **Entrada**: `state` + `questions`
- **Saída**: `choice`, `score`, `confidence`, `probabilities`

## Busca Tradicional

Preservada em `public/keyword.js`. Usa normalização, stopwords, sinônimos, stemming simples, IDF e peso por campo.

## Orçamento

Tratado deterministicamente pelo código, não pelo LAYA. O backend extrai valores numéricos de texto como "até 150 reais", "2 mil", "uns cem conto".

## Cache

LRU com TTL de 30 minutos e capacidade de 500 buscas. Chave normalizada sem acentos, pontuação ou diferenças de caixa.

## Modo Offline

Depois da primeira execução (que pode baixar o modelo), a aplicação funciona sem internet.

```bash
./scripts/verify_offline.py
```

## Testes

```bash
make test
# ou
pytest tests/ -v
```

Com cobertura:

```bash
make coverage
# ou
pytest tests/ --cov=app --cov-report=term-missing
```

## Benchmark

```bash
python scripts/benchmark.py
```

## Porta

```
http://127.0.0.1:4111
```

## Segurança

- Bind apenas em `127.0.0.1`
- Sem CORS aberto
- Sem execução de código vindo do modelo
- Sem dependências externas
