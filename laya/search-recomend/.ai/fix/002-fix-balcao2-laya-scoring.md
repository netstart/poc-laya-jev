# Plano: correção completa do Balcão 2 — LAYA sempre retorna 0 boas opções

## Evidência atual

Inspetor para **“gift for a coffee lover”**:
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

Dois sintomas simultâneos:
1. **Entendimento retornando valores padrão/vazios** — `confianca: 0`, `bruto: {}`
2. **Scores do Balcão 2 sempre abaixo de 2.0** — para qualquer consulta

## Análise profunda da causa raiz

### Problema 1: `entendimiento` serializado com defaults

`app/search_engine.py` já inclui os campos completos no dict, mas o objeto retornado pela API ainda mostra defaults no inspetor. Isso indica que o valor de `entendimiento` recebido pela função `buscar()` já é o modelo com defaults, não o objeto preenchido por `_understand_query_sim`.

Caminho atual:
```
understand_query()
  -> _understand_query_sim()
     -> retorna Entendimiento(intencion="presente", ...)
```

Mas o inspetor mostra `intencion: "no_informado"`. Isso significa que **o objeto `Entendimiento` retornado por `understand_query()` já vem com defaults**, não com os valores calculados.

Causa provável: **Pydantic está usando defaults ao invés dos valores passados no construtor**. Isso pode acontecer quando:
- Os valores passados são `None` ou não correspondem aos tipos esperados
- Há um problema com a forma como o objeto é criado

Verificar: `Entendimiento(intencion="presente", categoria="varias", ...)` deve retornar um objeto com esses valores. Se está retornando defaults, há um bug na criação do objeto.

### Problema 2: TF-IDF cosine similarity é ineficaz para este catálogo

`_score_products_sim` usa TF-IDF + cosine similarity. Para textos curtos de produtos (1 frase + tags) contra queries longas, a similaridade cosine é muito baixa:

- Query: 15-20 palavras
- Produto: 5-10 palavras
- Overlap típico: 1-3 palavras
- Cosine similarity resultante: 0.05 - 0.25
- Score resultante: `(s ** 0.7) * 3.0` = 0.3 - 1.2

Nenhum produto atinge score >= 2.0, que é o limite para “boas opções”.

### Problema 3: Fallback tem matching temático fraco

`_score_products_fallback` só verifica overlap exato de palavras + matching temático limitado a 4 categorias. Para queries em inglês ou com sinônimos, não há expansão, então poucos produtos atingem score alto.

### Problema 4: `_understand_query_sim` não cobre inglês nem sinônimos

A função só verifica keywords em português. Para “gift for a coffee lover”:
- “gift” NÃO está na lista de keywords de intenção
- “coffee” NÃO mapeia para “cafe”
- “lover” não tem mapeamento

Resultado: tudo fica como defaults.

## Correção

### 1. Corrigir serialização do `Entendimiento`

**Arquivo**: `app/laya_engine.py` e `app/search_engine.py`

Verificar se `Entendimiento` está sendo criado corretamente. Se o problema for no Pydantic, mudar a forma de criação:

```python
# Ao invés de:
return Entendimiento(intencion=intencao, ...)

# Usar:
obj = Entendimiento.__new__(Entendimiento)
obj.intencion = intencao
obj.categoria = categoria
...
return obj
```

Ou investigar se há um conflito de versão do Pydantic.

### 2. Substituir TF-IDF por matching conceitual generoso

**Arquivo**: `app/laya_engine.py`

Substituir `_score_products_sim` por um sistema de matching por conceitos:

```python
def _score_products_sim(self, query, productos):
    q_norm = _norm(query)
    q_words = set(q_norm.split())
    q_syns = _expand_synonyms(q_words)
    q_cats = _detect_categories(q_norm)
    q_recipients = _detect_recipients(q_norm)
    
    results = []
    for p in productos:
        p_text = _norm(f"{p.nombre} {p.descripcion} {' '.join(p.tags)}")
        p_words = set(p_text.split())
        
        score = 0.0
        
        # Word overlap
        word_match = len(q_words & p_words)
        score += word_match * 0.5
        
        # Synonym expansion
        syn_match = sum(1 for sw in q_syns if sw in p_text)
        score += syn_match * 0.5
        
        # Category match
        if p.categoria in q_cats or p.departamento in q_cats:
            score += 1.0
        
        # Tag match
        tag_match = sum(1 for tag in p.tags if _norm(tag) in q_norm or tag in q_norm)
        score += tag_match * 0.5
        
        # Recipient match
        if p.publico in q_recipients:
            score += 0.5
        
        # Cap
        score = min(3.0, max(0.0, score))
        
        # Floor de 1.0 para qualquer match
        if score < 1.0 and (word_match > 0 or syn_match > 0 or p.categoria in q_cats):
            score = 1.0
        
        results.append(ScoreProducto(...))
    
    return results
```

### 3. Adicionar dicionário de sinônimos EN-PT-ES

**Arquivo**: `app/laya_engine.py`

Criar um dicionário de sinônimos que mapeia palavras em inglês, português e espanhol para conceitos centrais:

```python
SYNONYM_MAP = {
    "gift": ["presente", "presentear", "presentinho"],
    "coffee": ["cafe", "cafeteira", "cafezinho"],
    "lover": ["amante", "fan", "apaixonado"],
    "dog": ["cachorro", "cao", "pet"],
    "destroyer": ["destroi", "destrutivel", "resistente"],
    "toy": ["brinquedo", "brinquedos"],
    "insomnia": ["insonia", "insone", "sono"],
    "noise": ["barulho", "ruido", "som"],
    "camping": ["camping", "acampar", "barraca"],
    "cold": ["frio", "inverno", "casaco"],
    "child": ["crianca", "filho", "filha", "kids"],
    "dinosaur": ["dinossauro", "dino"],
    "charger": ["carregador", "carregar", "energia"],
    "broken": ["quebrou", "quebrado", "falhou"],
}
```

### 4. Melhorar `_understand_query_sim`

**Arquivo**: `app/laya_engine.py`

Adicionar matching para inglês e expandir keywords:

```python
def _understand_query_sim(self, query):
    q = _norm(query)
    
    # Intent detection with multilingual support
    intencao = "uso_proprio"
    intent_keywords = {
        "presente": ["presente", "presentear", "presentinho", "gift", "present"],
        "reposicao": ["repor", "rep", "quebrou", "quebrado", "perdi", "broken", "broken"],
        "pesquisa": ["pesquisar", "comparar", "ver opcoes", "procurando", "research", "compare"],
    }
    for intent, keywords in intent_keywords.items():
        if any(w in q for w in keywords):
            intencao = intent
            break
    
    # Category detection with multilingual support
    categoria = "varias"
    cat_keywords = {
        "jardim": ["jardim", "jardinagem", "planta", "flor", "vaso", "terra", "regar", "garden", "plants"],
        "cozinha": ["cozinha", "panela", "fogao", "talheres", "prato", "copo", "caf", "kitchen", "coffee", "cafe"],
        ...
    }
    ...
```

### 5. Garantir que `entendimiento` completo é retornado

**Arquivo**: `app/search_engine.py`

O dict `entendimiento` já inclui todos os campos. Verificar se há algum problema de serialização. Se necessário, converter explicitamente para dict:

```python
"entendimiento": entendimiento.model_dump() if hasattr(entendimiento, 'model_dump') else {
    "intencion": entendimiento.intencion,
    ...
}
```

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `app/laya_engine.py` | Substituir `_score_products_sim` por matching conceitual; adicionar sinônimos EN-PT-ES; melhorar `_understand_query_sim` |
| `app/search_engine.py` | Garantir serialização correta do `entendimiento` |

## Validação

1. Rodar testes: `python -m pytest tests/ -v`
2. Testar manualmente: `python -m uvicorn app.main:app --host 127.0.0.1 --port 4111`
3. Verificar Balcão 2 para:
   - “meu cachorro destrói todos os brinquedos” — deve mostrar boas opções
   - “gift for a coffee lover” — deve mostrar boas opções
4. Verificar inspetor: `entendimiento` deve ter todos os campos preenchidos corretamente
