# Plano: corrigir Balcão 2 — LAYA sempre retorna 0 boas opções

Evidência atual do inspetor para a consulta **“meu cachorro destrói todos os brinquedos”**:

```json
{
  "intencion": "no_informado",
  "categoria": "no_informado",
  "destinatario": "no_informado",
  "ocasion": "nenhuma",
  "orcamento_max": null,
  "orcamento_fonte": "no_detectado",
  "confianca": 0,
  "bruto": {}
}
```

Isso mostra dois sintomas simultâneos:

1. **Entendimento retornando valores padrão/vazios**
   - `confianca: 0`
   - `bruto: {}`
   - Tudo como `"no_informado"` / `null`

2. **Scores do Balcão 2 muito baixos**
   - Mesmo quando o entendimento funcionar, o fallback local gera scores ruins.

## Causa raiz confirmada

`app/search_engine.py` não retorna o objeto completo de entendimento na resposta da API:

```python
"entendimiento": {
    "pilulas": [],
    "orcamento_max": orcamento_max,
    "orcamento_fonte": entendimento.orcamento_fonte,
    "bruto": entendimento.bruto,
},
```

Faltam: `intencion`, `categoria`, `destinatario`, `ocasion`, `confianca`.

Além disso, o fallback do LAYA (`_score_products_sim` e `_score_products_fallback`) gera scores muito baixos para o catálogo misto espanhol/português, fazendo com que `score >= 2` quase nunca seja atingido.

## Correção

### 1. Retornar entendimento completo

**Arquivo**: `app/search_engine.py`

 Substituir o dicionário `entendimiento` por:

```python
"entendimiento": {
    "pilulas": [],
    "intencion": entendimiento.intencion,
    "categoria": entendimiento.categoria,
    "destinatario": entendimiento.destinatario,
    "ocasion": entendimiento.ocasion,
    "orcamento_max": orcamento_max,
    "orcamento_fonte": entendimiento.orcamento_fonte,
    "confianca": entendimiento.confianca,
    "bruto": entendimiento.bruto,
},
```

### 2. Ajustar escala do `_score_products_sim`

**Arquivo**: `app/laya_engine.py`

Trocar:
```python
score = min(3.0, max(0.0, s * 3.0))
```

Por:
```python
score = min(3.0, max(0.0, (s ** 0.7) * 3.0))
```

Garantir floor de `1.0` para `s > 0.15`.

### 3. Melhorar `_score_products_fallback`

**Arquivo**: `app/laya_engine.py`

Adicionar matching por categoria, tags e sinônimos. Dar score base `1.0` para matches temáticos e `+0.5` por palavra adicional.

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `app/search_engine.py` | Retornar campos completos do entendimento |
| `app/laya_engine.py` | Ajustar escala do TF-IDF e melhorar fallback |

## Validação

1. Rodar testes: `python -m pytest tests/ -v`
2. Testar manualmente: `python -m uvicorn app.main:app --host 127.0.0.1 --port 4111`
3. Verificar Balcão 2 para “meu cachorro destrói todos os brinquedos” — deve mostrar boas opções.
