# PROMPT PARA CODING AGENT

# BUSCA QUE ENTENDE — VERSÃO 100% LOCAL COM LAYA

## 0. OBJETIVO

Você deve construir uma aplicação local chamada:

**Busca que Entende**

A aplicação deve reproduzir funcionalmente e visualmente a aplicação original "Busca que Entende", utilizando o **LAYA** diretamente, sem o openrouter na frente, executado localmente na máquina do usuário.

A aplicação é uma demonstração de busca semântica/intencional para e-commerce.

A ideia central é:

> O usuário escreve uma frase natural como:
>
> "presente pra minha mãe que ama jardinagem até 150 reais"
>
> A aplicação deve entender a intenção, avaliar o catálogo inteiro e mostrar por que uma busca semântica/intencional encontra produtos diferentes de uma busca tradicional por palavras-chave.

---

# 1. REGRA FUNDAMENTAL: TUDO DEVE RODAR LOCALMENTE

Esta é uma exigência arquitetural obrigatória.

A aplicação NÃO deve depender de:

* OpenRouter
* JEV
* TypeSafe
* API externa de LLM
* VPS
* Hostinger
* servidor dedicado
* domínio
* HTTPS externo
* Caddy
* Docker obrigatório
* banco de dados externo
* serviço SaaS
* chave de API
* autenticação externa
* CDN
* serviço remoto de inferência

O LAYA deve executar localmente na máquina do usuário.

A única comunicação externa permitida é:

**somente durante a primeira instalação, caso seja necessário baixar os pesos do modelo.**

Depois que os pesos estiverem disponíveis localmente:

> **a inferência deve funcionar sem internet e sem nenhuma API externa.**

O programa deve detectar se os pesos já existem localmente.

---

# 2. IMPORTANTE SOBRE O LAYA

Utilize o LAYA como um modelo de decisão/classificação, e não como um LLM generativo.

O LAYA recebe:

* `state`
* `questions`

e produz decisões tipadas com probabilidades.

Os tipos relevantes são:

* `choice`
* `score`
* `noul`

Não utilize um LLM generativo para substituir o LAYA.

Não faça:

```text
usuário
 ↓
LLM generativo
 ↓
JSON
 ↓
parser
```

Faça:

```text
usuário
 ↓
Busca que Entende
 ↓
LAYA local
 ↓
decisões tipadas
 ↓
regras determinísticas
 ↓
ranking
 ↓
interface
```

O LAYA atual possui checkpoints para inglês, multilíngue e typed decisions. Para este projeto, como o catálogo e as consultas principais são em português brasileiro, utilize inicialmente:

```text
laya-multilingual
```

ou o checkpoint multilíngue equivalente suportado pela versão instalada do pacote LAYA.

Não assuma APIs que não existam.

Antes de implementar, consulte a documentação oficial/README da versão instalada do LAYA e confirme:

1. instalação;
2. carregamento do checkpoint;
3. API de `choice`;
4. API de `score`;
5. batch de perguntas;
6. seleção de dispositivo;
7. CPU;
8. GPU NVIDIA/CUDA;
9. cache local do modelo;
10. execução offline depois do download.

O código final deve funcionar com a API real do LAYA instalado.

---

# 3. PRIMEIRO: INSPECIONE OS ARQUIVOS FORNECIDOS

Existe um projeto original fornecido junto com este prompt.

Existe um ZIP contendo aproximadamente:

```text
busca/
├── data/
│   └── catalogo.json
├── orcamento.mjs
├── public/
│   ├── app.js
│   ├── busca.css
│   ├── index.html
│   ├── keyword.js
│   └── fonts/
│       ├── bricolage-grotesque-vf.woff2
│       ├── figtree-vf.woff2
│       ├── figtree-vf-italic.woff2
│       └── LICENCAS.txt
├── README.md
├── server.mjs
└── test/
    └── e2e.py
```

IMPORTANTE:

Antes de escrever código:

1. descompacte o projeto original;
2. leia todos os arquivos;
3. leia especialmente:

   * `server.mjs`
   * `public/app.js`
   * `public/index.html`
   * `public/busca.css`
   * `public/keyword.js`
   * `orcamento.mjs`
   * `data/catalogo.json`
   * `test/e2e.py`
   * `README.md`

Não reimplemente cegamente a interface.

A interface original deve ser preservada tanto quanto possível.

A camada que deve ser substituída é principalmente:

```text
JEV / gateway / OpenRouter
```

por:

```text
LAYA local
```

---

# 4. O QUE DEVE SER PRESERVADO

Preserve:

## 4.1 Catálogo

Utilize o catálogo original:

```text
120 produtos
```

Não invente outro catálogo.

Não remova produtos.

Não altere os IDs.

Não altere os textos sem necessidade.

Não altere preços.

Não altere categorias.

Não altere os públicos.

O arquivo:

```text
data/catalogo.json
```

continua sendo a fonte oficial.

---

# 5. CONCEITO DA APLICAÇÃO

A aplicação simula uma loja de departamentos dos anos 70.

Ela apresenta:

### Capa

```text
CATÁLOGO GERAL · 120 ARTIGOS

Busca que Entende
```

Uma barra de pesquisa.

Exemplo:

```text
presente pra minha mãe que ama jardinagem até 150 reais
```

Abaixo:

```text
BUSCAS DE EXEMPLO
```

Com os 8 exemplos:

```text
🌱 Mãe jardineira, até R$ 150
🏕️ Acampar com criança no frio
🐶 Cachorro destruidor
😴 Insônia
🤫 Amigo secreto, até R$ 50
🦖 Fã de dinossauro
🔌 Carregador quebrou
☕ Em inglês
```

---

# 6. O DIFERENCIAL DA APLICAÇÃO

A tela deve comparar dois mecanismos.

## BALCÃO 1

```text
Balcão 1 · Busca por palavra-chave
```

É a busca tradicional.

Ela deve utilizar:

```text
public/keyword.js
```

e continuar sendo propositalmente limitada.

Ela NÃO deve entender:

* intenção;
* contexto;
* orçamento;
* ocasião;
* destinatário;
* significado semântico profundo.

Ela deve pesquisar termos.

---

## BALCÃO 2

```text
Balcão 2 · Busca com LAYA
```

Aqui está o novo mecanismo.

O LAYA avalia os produtos do catálogo de acordo com a intenção do usuário.

---

# 7. ARQUITETURA NOVA

A arquitetura deve ser:

```text
┌───────────────────────────────────────────┐
│                  USUÁRIO                  │
│                                           │
│ "presente pra minha mãe que ama           │
│  jardinagem até 150 reais"                │
└──────────────────┬────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────┐
│             FRONTEND LOCAL                │
│                                           │
│ debounce / input / UX / ranking           │
└──────────────────┬────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────┐
│          BACKEND LOCAL                    │
│                                           │
│ Busca que Entende                         │
│                                           │
│ - orçamento determinístico               │
│ - busca keyword                           │
│ - cache                                   │
│ - montagem das perguntas                  │
│ - ranking                                 │
│ - regras de negócio                       │
└──────────────────┬────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────┐
│             LAYA LOCAL                    │
│                                           │
│ laya-multilingual                         │
│                                           │
│ choice                                    │
│ score                                     │
│ noul                                      │
└──────────────────┬────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────┐
│          DECISÕES TIPADAS                 │
│                                           │
│ probabilidades                            │
│ score                                     │
│ confidence                                │
└──────────────────┬────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────┐
│         REGRAS DETERMINÍSTICAS            │
│                                           │
│ orçamento                                │
│ ranking                                   │
│ filtros                                   │
│ níveis                                    │
│ posição                                   │
└──────────────────┬────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────┐
│                UI                         │
│                                           │
│ Cupom                                     │
│ Índice                                    │
│ Balcão 1                                  │
│ Balcão 2                                  │
│ Recibo                                    │
│ Inspetor                                  │
└───────────────────────────────────────────┘
```

Não deve existir:

```text
OpenRouter
JEV Gateway
API key
VPS
```

---

# 8. SERVIDOR LOCAL

É permitido utilizar um servidor HTTP local.

Isso NÃO significa servidor dedicado.

O servidor deve escutar somente:

```text
127.0.0.1
```

ou:

```text
localhost
```

Nunca:

```text
0.0.0.0
```

por padrão.

Porta padrão:

```text
4111
```

A aplicação deve ser acessível em:

```text
http://127.0.0.1:4111
```

---

# 9. STACK

Prioridade:

## Backend

Python 3.10+

ou versão compatível com a versão atual do LAYA.

Use:

```text
FastAPI
```

ou um servidor HTTP Python simples, caso isso reduza dependências.

Para o MVP, prefira:

```text
Python
FastAPI
Uvicorn
LAYA
```

Não introduza frameworks desnecessários.

---

# 10. FRONTEND

Preserve o frontend original.

Preferencialmente:

```text
HTML
CSS
JavaScript vanilla
```

Sem React, Vue ou Angular, a menos que seja absolutamente necessário.

Não transforme o frontend em uma aplicação SPA pesada.

A interface original já está pronta.

Reutilize:

```text
index.html
app.js
busca.css
keyword.js
fonts/
```

Faça somente as alterações necessárias para substituir o contrato do JEV pelo contrato do LAYA.

---

# 11. ESTRUTURA FINAL DO PROJETO

Crie:

```text
busca-que-entende/
│
├── app/
│   ├── main.py
│   ├── laya_engine.py
│   ├── search_engine.py
│   ├── ranking.py
│   ├── orcamento.py
│   ├── cache.py
│   ├── schemas.py
│   └── config.py
│
├── model/
│   └── README.md
│
├── data/
│   └── catalogo.json
│
├── public/
│   ├── index.html
│   ├── app.js
│   ├── busca.css
│   ├── keyword.js
│   └── fonts/
│
├── tests/
│   ├── test_laya.py
│   ├── test_ranking.py
│   ├── test_orcamento.py
│   ├── test_api.py
│   └── test_e2e.py
│
├── scripts/
│   ├── setup_model.py
│   ├── benchmark.py
│   └── verify_offline.py
│
├── requirements.txt
├── .gitignore
├── README.md
├── run.py
├── run.sh
└── run.ps1
```

---

# 12. SINGLE COMMAND

Este requisito é obrigatório.

O usuário deve conseguir executar:

### Linux/macOS

```bash
./run.sh
```

### Windows PowerShell

```powershell
.\run.ps1
```

O script deve:

1. detectar Python;
2. criar `.venv` se não existir;
3. instalar dependências se necessário;
4. verificar se o modelo LAYA está disponível;
5. baixar o modelo somente se necessário;
6. armazená-lo localmente;
7. iniciar a aplicação;
8. abrir ou informar:

```text
http://127.0.0.1:4111
```

Depois que o modelo estiver baixado, a aplicação deve funcionar offline.

Idealmente também permitir:

```bash
python run.py
```

---

# 13. NÃO USAR DOCKER POR PADRÃO

Não exija:

```text
docker compose up
```

Não exija Docker Desktop.

Não exija Kubernetes.

Não exija servidor Linux.

Não exija VM.

O usuário deve executar diretamente na própria máquina.

---

# 14. MODELO LAYA

Crie uma camada de abstração:

```python
class LayaEngine:
    def __init__(self, ...):
        ...

    def decide(self, state, questions):
        ...

    def score_products(self, query, products):
        ...

    def understand_query(self, query):
        ...
```

O restante da aplicação não deve conhecer detalhes internos do LAYA.

Assim:

```text
server
  ↓
LayaEngine
  ↓
LAYA
```

e não:

```text
server
  ↓
código espalhado do LAYA
```

---

# 15. CARREGAMENTO DO MODELO

O modelo deve ser carregado UMA VEZ durante a inicialização.

Não faça:

```python
load_model()
```

a cada busca.

Faça:

```text
processo inicia
    ↓
carrega LAYA
    ↓
modelo permanece em memória
    ↓
todas as buscas reutilizam o modelo
```

Crie uma verificação:

```text
GET /healthz
```

retornando algo como:

```json
{
  "ok": true,
  "app": "busca",
  "engine": "laya",
  "model": "laya-multilingual",
  "device": "cpu",
  "loaded": true
}
```

Se houver GPU:

```json
{
  "device": "cuda"
}
```

---

# 16. DETECÇÃO DE HARDWARE

Detecte automaticamente:

1. NVIDIA CUDA;
2. Apple Silicon, se suportado pelo runtime escolhido;
3. CPU.

Não exija GPU.

O sistema deve funcionar em:

```text
CPU
```

como fallback obrigatório.

Se GPU estiver disponível e for compatível:

```text
usar GPU
```

sem alterar o código da aplicação.

Mostre no startup:

```text
LAYA
Modelo: laya-multilingual
Device: CUDA
```

ou:

```text
LAYA
Modelo: laya-multilingual
Device: CPU
```

---

# 17. BUSCA SEMÂNTICA

A aplicação deve avaliar os 120 produtos.

Não faça pré-filtro baseado em keyword antes do LAYA.

Isso destruiria justamente o propósito da demonstração.

O fluxo deve ser:

```text
query
   ↓
LAYA
   ↓
120 produtos avaliados
```

A busca tradicional roda separadamente:

```text
query
   ↓
KeywordSearch
   ↓
resultados tradicionais
```

---

# 18. PERGUNTAS DE ENTENDIMENTO

Uma chamada de entendimento deve produzir:

## INTENÇÃO

Tipo:

```text
choice
```

Critérios:

```text
presente
uso_proprio
reposicao
pesquisa
```

Use descrições equivalentes às originais:

```text
presente:
Vai comprar para dar de presente a outra pessoa

uso_proprio:
Quer algo para si mesmo, para a própria casa ou rotina, ou para resolver um problema seu

reposicao:
Precisa repor ou substituir algo que acabou, quebrou ou se perdeu

pesquisa:
Está só pesquisando ou comparando opções, sem necessidade definida
```

---

# 19. CATEGORIA

Tipo:

```text
choice
```

Opções:

```text
casa
jardim
cozinha
eletronicos
esporte
camping
moda
beleza
pet
brinquedos
livros
papelaria
bem_estar
varias
```

Preserve os critérios da aplicação original.

---

# 20. DESTINATÁRIO

Tipo:

```text
choice
```

Opções:

```text
mae
pai
avos
parceiro
crianca
bebe
adolescente
amigo
pet
eu_mesmo
familia
nao_informado
```

---

# 21. OCASIÃO

Tipo:

```text
choice
```

Opções:

```text
aniversario
dia_das_maes
dia_dos_pais
natal
amigo_secreto
dia_dos_namorados
dia_das_criancas
viagem
nenhuma
```

---

# 22. ORÇAMENTO

Tipo:

```text
choice
```

Opções:

```text
sem_limite
barato
ate_50
ate_100
ate_150
ate_200
ate_300
ate_500
ate_1000
premium
```

Mas existe uma regra fundamental:

## O LAYA NÃO FAZ A CONTA DO ORÇAMENTO.

O valor explícito deve continuar sendo interpretado deterministicamente pelo código.

Exemplos:

```text
até 150 reais
```

→

```text
150
```

```text
no máximo R$ 80
```

→

```text
80
```

```text
entre R$ 100 e R$ 200
```

→

```text
200
```

```text
até 2 mil
```

→

```text
2000
```

```text
até 2,5 mil
```

→

```text
2500
```

```text
uns cem conto
```

→

```text
aproximadamente 100
teto operacional = 110
```

Preserve a lógica existente de `orcamento.mjs`.

Apenas converta-a para Python ou mantenha-a em JavaScript se houver motivo real.

---

# 23. AVALIAÇÃO DOS PRODUTOS

Cada produto deve receber uma pergunta:

```text
type: score
```

Instrução:

```text
Quão bem o produto pXXX atende ao pedido do cliente?
```

Critérios:

```text
0:
Irrelevante: não tem relação com o que a pessoa pediu

1:
Talvez: tem alguma relação, mas não resolve bem o pedido

2:
Boa opção: atende bem ao pedido

3:
Perfeito: exatamente o que a pessoa procura, para a pessoa e a situação certas
```

---

# 24. IMPORTANTE: BATCH

Não faça uma chamada LAYA para cada produto individualmente se a API instalada do LAYA permitir batch.

Utilize a capacidade de perguntas múltiplas do modelo.

Estrutura desejada:

```text
1 query
+
24 produtos
+
24 perguntas score
=
1 inferência
```

Depois:

```text
lote 1 = 24
lote 2 = 24
lote 3 = 24
lote 4 = 24
lote 5 = 24
```

Total:

```text
120 produtos
```

Mais uma chamada de entendimento.

Portanto:

```text
6 operações lógicas
```

Mas atenção:

Se a implementação local do LAYA conseguir processar as 125 perguntas em uma única chamada sem perda de qualidade e sem ultrapassar os limites reais de contexto/memória, faça benchmark.

Não copie cegamente o limite de 24 do JEV.

O tamanho 24 era uma decisão do projeto original relacionada ao limite do inspetor e ao comportamento do JEV.

No LAYA, determine empiricamente:

```text
12
24
32
48
60
120
```

e compare:

* latência;
* memória;
* estabilidade;
* qualidade do ranking;
* top-5;
* uso de CPU/GPU.

Escolha o melhor tamanho.

---

# 25. PARALELISMO

Se o runtime do LAYA permitir inferências concorrentes com eficiência, avalie:

```text
entendimento
+
lote 1
+
lote 2
+
lote 3
+
lote 4
+
lote 5
```

em paralelo.

Mas NÃO faça paralelismo irresponsável.

Em CPU, várias inferências simultâneas podem ser mais lentas do que batch.

Portanto, implemente um benchmark inicial e escolha:

```text
batch
```

ou:

```text
paralelo
```

baseado em medição real.

Não faça uma escolha baseada em suposição.

---

# 26. NORMALIZAÇÃO DA RESPOSTA LAYA

Crie um adaptador:

```python
normalize_laya_response(...)
```

O frontend não deve depender do formato interno específico da versão do LAYA.

Converta tudo para:

```json
{
  "score": 2.79,
  "probabilities": {
    "0": 0.00,
    "1": 0.21,
    "2": 0.00,
    "3": 0.79
  },
  "confidence": 0.91
}
```

ou equivalente.

Para `choice`:

```json
{
  "choice": "jardim",
  "probabilities": {
    "jardim": 0.98,
    "cozinha": 0.01,
    "casa": 0.01
  },
  "confidence": 0.98
}
```

---

# 27. RANKING

Preserve a lógica do projeto original.

A nota final do produto é:

```text
score
```

convertida para:

```text
0 = Irrelevante
1 = Talvez
2 = Boa opção
3 = Perfeito
```

A exibição deve utilizar:

```javascript
Math.max(0, Math.min(3, Math.round(score)))
```

ou equivalente em Python.

---

# 28. ORDENAMENTO

Primeiro:

```text
produtos dentro do orçamento
```

Depois:

```text
produtos acima do orçamento
```

Dentro de cada grupo:

```text
score descendente
```

Empate:

```text
preço menor primeiro
```

---

# 29. BALCÃO LAYA

Mostrar até 8 produtos.

Critério:

```text
score >= 1
```

Mas o contador de:

```text
boas opções
```

deve ser:

```text
score >= 2
```

Exemplo:

```text
11 boas opções
```

---

# 30. ACIMA DO ORÇAMENTO

Produtos que:

```text
score >= 1.5
```

mas ultrapassam o orçamento devem aparecer no rodapé:

```text
Também combinam, mas passam de R$ 150,00:
Produto A (R$ 199,90)
Produto B (R$ 249,90)
Produto C (R$ 299,90)
```

Máximo:

```text
3
```

---

# 31. NADA SERVE

Se nenhum produto dentro do orçamento atingir:

```text
score >= 2
```

mostrar:

```text
Nada no catálogo atende bem a este pedido.
O LAYA prefere dizer isso a empurrar qualquer coisa — abaixo, o que chega mais perto.
```

Não inventar recomendação.

Se nenhum produto atingir sequer:

```text
score >= 1
```

mostrar:

```text
Nenhum produto desta loja tem relação com o pedido.
Nenhuma nota passou de "irrelevante".
```

---

# 32. BUSCA POR PALAVRA-CHAVE

Não transforme a busca tradicional em busca semântica.

Preserve `keyword.js`.

Ela deve continuar sendo a contraparte honesta.

Deve manter:

* normalização;
* stopwords;
* sinônimos;
* stemming simples;
* IDF;
* peso por campo;
* prefixo durante digitação;
* highlight.

O objetivo é permitir comparar:

```text
BUSCA TRADICIONAL
```

versus:

```text
BUSCA COM LAYA
```

---

# 33. CACHE

Implemente cache local.

TTL:

```text
30 minutos
```

Capacidade:

```text
500 buscas
```

LRU.

Chave:

```text
texto normalizado
```

Remover:

* acentos;
* pontuação;
* espaços duplicados;
* diferenças de caixa.

Exemplo:

```text
Presente pra minha MÃE!
```

e:

```text
presente pra minha mae
```

devem resultar na mesma chave.

---

# 34. FRESH

Preserve:

```text
?fresh=1
```

Quando presente:

```text
não usar cache
```

Isso serve para benchmark.

---

# 35. API LOCAL

Implemente:

```text
GET /healthz
GET /api/catalogo
GET /api/exemplos
GET /api/stats
POST /api/buscar
```

---

# 36. POST /api/buscar

Entrada:

```json
{
  "q": "presente pra minha mãe que ama jardinagem até 150 reais",
  "fresh": false
}
```

Validações:

### menos de 2 caracteres

HTTP:

```text
400
```

Código:

```text
vazio
```

Mensagem:

```text
Digite o que você procura (pelo menos 2 letras).
```

### mais de 300 caracteres

HTTP:

```text
400
```

Código:

```text
longo
```

Mensagem:

```text
Busca longa demais: use até 300 caracteres.
```

---

# 37. RESPONSE CONTRACT

Mantenha aproximadamente:

```json
{
  "ok": true,
  "q": "...",
  "cached": false,

  "entendimento": {
    "pilulas": [],
    "orcamento_max": 150,
    "orcamento_fonte": "texto",
    "bruto": {}
  },

  "scores": {
    "p001": [2.95, 0.00, 0.01, 0.03, 0.96]
  },

  "ordem": [
    "p001",
    "p002"
  ],

  "lotes": [],

  "latency_ms": 412,

  "laya_ms": 390,

  "n_produtos": 120,

  "n_chamadas": 6,

  "n_perguntas": 125,

  "parcial": null,

  "_laya": []
}
```

Você pode alterar nomes internos se necessário, mas mantenha compatibilidade com o frontend original sempre que possível.

---

# 38. RENOMEAR O CONCEITO JEV

Na interface, substitua todas as referências:

```text
Jev
```

por:

```text
Laya
```

Exemplos:

```text
O que o Jev vê
```

vira:

```text
O que o Laya vê
```

```text
O Jev entendeu
```

vira:

```text
O Laya entendeu
```

```text
Recibo do Jev
```

vira:

```text
Recibo do Laya
```

```text
Busca com Jev
```

vira:

```text
Busca com Laya
```

Não deixe referências falsas ao JEV na interface.

---

# 39. INSPETOR

Crie um inspetor equivalente ao original.

Botão:

```text
🔍 Ver o que o Laya vê
```

Ao abrir:

```text
O que o Laya recebeu e respondeu
```

Mostrar:

### Estado

```json
{
  "pedido_do_cliente": "...",
  "contexto": "..."
}
```

### Perguntas

Mostrar:

```text
choice
score
noul
```

### Respostas

Mostrar:

```text
probabilidades
score
confidence
```

O objetivo é deixar evidente que:

> LAYA não é um gerador de texto. Ele recebe estado + perguntas tipadas e devolve decisões probabilísticas.

---

# 40. ARQUITETURA VISUAL

Mantenha o conceito visual da arquitetura.

Porém substitua:

```text
JEV
OpenRouter
Gateway
Hostinger
VPS
```

por:

```text
LAYA
Modelo local
Runtime Python
Máquina do usuário
```

Arquitetura:

```text
┌───────────────────────┐
│      Navegador        │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Backend local         │
│ localhost:4111        │
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
└───────────────────────┘
```

---

# 41. INTERFACE VISUAL

NÃO redesenhe a interface.

Use os arquivos fornecidos como referência principal.

Preserve:

* catálogo anos 70;
* papel creme;
* tipografia;
* bordas;
* sombras;
* etiquetas;
* cupom;
* recibo;
* índice;
* balcões;
* animações;
* responsive;
* celular;
* fontes;
* cores;
* proporções.

A aplicação deve parecer a mesma aplicação.

A mudança deve ser percebida principalmente na arquitetura:

```text
JEV externo
```

para:

```text
LAYA local
```

---

# 42. ESTADOS DA INTERFACE

Implemente todos:

## Estado 1

```text
Inicial
```

## Estado 2

```text
Digitando
```

## Estado 3

```text
Avaliando
```

## Estado 4

```text
Resultado
```

## Estado 5

```text
Cache
```

## Estado 6

```text
Nada serve
```

## Estado 7

```text
Resultado parcial
```

## Estado 8

```text
Erro
```

## Estado 9

```text
Mobile
```

---

# 43. DEBOUNCE

Preserve:

```text
550 ms
```

Após:

```text
3+ caracteres
```

Enter:

```text
2+ caracteres
```

Botão:

```text
Buscar
```

também:

```text
2+ caracteres
```

---

# 44. CONTROLE DE REQUESTS ANTIGAS

Use um:

```text
sequence id
```

ou:

```text
AbortController
```

ou ambos.

Se o usuário digitar:

```text
cachorro
```

e rapidamente:

```text
cachorro destruidor
```

a resposta antiga não pode substituir a nova.

---

# 45. CATÁLOGO VISUAL

Mantenha:

```text
120 quadradinhos
```

Organizados por departamento.

Estados:

```text
cinza
```

quando não avaliados.

Depois:

```text
lv0
lv1
lv2
lv3
```

Produtos relevantes:

```text
hot
```

Produtos acima do orçamento:

```text
over
```

Top 5:

```text
círculo de caneta
```

e:

```text
1
2
3
4
5
```

---

# 46. EXEMPLOS OBRIGATÓRIOS

Os oito exemplos devem continuar funcionando:

```text
presente pra minha mãe que ama jardinagem até 150 reais

acampar com criança no frio

meu cachorro destrói todos os brinquedos

tenho insônia e acordo com qualquer barulho

amigo secreto da firma até 50 reais

presente pra criança de 5 anos que ama dinossauro

o carregador do meu celular quebrou

gift for a coffee lover
```

---

# 47. RESULTADOS ESPERADOS

Não exija probabilidades exatamente iguais às do JEV.

Isso seria um erro conceitual.

O objetivo é reproduzir:

```text
comportamento
```

e não:

```text
números idênticos
```

O LAYA é outro modelo.

Portanto, valide principalmente:

1. relevância;
2. top-5;
3. separação entre relevante e irrelevante;
4. respeito ao orçamento;
5. intenção;
6. categoria;
7. destinatário;
8. ocasião;
9. comportamento da busca tradicional;
10. latência;
11. estabilidade.

---

# 48. TESTE "MÃE JARDINEIRA"

Entrada:

```text
presente pra minha mãe que ama jardinagem até 150 reais
```

Esperado:

* intenção = presente;
* categoria = jardim;
* destinatário = mãe;
* orçamento = R$150;
* produtos de jardim dominam o ranking;
* produtos acima de R$150 não devem dominar o resultado;
* busca tradicional continua encontrando resultados limitados;
* LAYA deve recuperar produtos semanticamente relacionados.

O teste não precisa exigir:

```text
p001 exatamente em primeiro
```

a menos que o benchmark real demonstre isso consistentemente.

---

# 49. TESTE "CACHORRO DESTRUIDOR"

Entrada:

```text
meu cachorro destrói todos os brinquedos
```

O sistema deve entender:

```text
pet / cachorro
```

e dar preferência a produtos descritos como:

```text
resistentes
ultrarresistentes
indestrutíveis
mordedores
para cães que destroem
```

A busca tradicional deve continuar sendo limitada.

---

# 50. TESTE "INSÔNIA"

Entrada:

```text
tenho insônia e acordo com qualquer barulho
```

O sistema deve recuperar semanticamente:

* ruído branco;
* isolamento acústico;
* sono;
* relaxamento;
* proteção contra ruído;
* produtos relacionados.

---

# 51. TESTE EM INGLÊS

Entrada:

```text
gift for a coffee lover
```

O modelo multilíngue deve ser utilizado justamente para permitir que o sistema consiga interpretar consultas em outros idiomas.

O resultado deve encontrar produtos relacionados a:

```text
coffee
café
cafeteira
moedor
prensa francesa
```

sem depender da busca tradicional em português.

---

# 52. BENCHMARK LAYA

Crie:

```text
scripts/benchmark.py
```

Ele deve medir:

```text
1 pergunta
5 perguntas
24 perguntas
50 perguntas
120 perguntas
125 perguntas
```

Medir:

```text
latência
CPU
RAM
GPU
VRAM
```

Quando possível.

Também medir:

```text
cold start
warm inference
```

Executar cada cenário pelo menos 10 vezes.

Reportar:

```text
min
p50
p90
p95
max
```

---

# 53. BENCHMARK DE QUALIDADE

Crie um pequeno conjunto de queries:

```text
mãe jardineira
cachorro destruidor
insônia
acampar com criança no frio
gift for a coffee lover
amigo secreto até 50
presente para criança que ama dinossauro
carregador quebrado
```

Para cada query, registre um gabarito de relevância.

Calcule:

```text
Precision@5
Precision@8
Recall@K
```

Se possível:

```text
NDCG@5
NDCG@10
```

Não invente que LAYA é melhor que JEV.

A comparação deve ser medida.

---

# 54. COMPARAÇÃO JEV × LAYA

Não coloque o JEV na aplicação final.

Porém crie uma documentação:

```text
docs/LAYA-VS-JEV.md
```

Explicando:

```text
JEV:
serviço remoto

LAYA:
modelo local

JEV:
OpenRouter

LAYA:
inference local

JEV:
custo por chamada

LAYA:
custo marginal praticamente local, depois do download

JEV:
latência depende de rede

LAYA:
latência depende principalmente do hardware local
```

Não invente números.

Os números devem ser os medidos na máquina.

---

# 55. MODO OFFLINE

Crie:

```text
scripts/verify_offline.py
```

Ele deve:

1. bloquear ou detectar acesso externo;
2. iniciar aplicação;
3. fazer `/healthz`;
4. fazer busca;
5. verificar que nenhuma requisição externa ocorreu.

A aplicação deve funcionar.

---

# 56. ZERO API KEY

Não deve existir:

```text
OPENROUTER_API_KEY
```

nem:

```text
JEV_MODEL
```

nem:

```text
JEV_GATEWAY_URL
```

nem:

```text
HOSTINGER_API_TOKEN
```

no projeto final.

Se encontrar qualquer uma dessas variáveis no projeto original, remova.

---

# 57. ZERO SERVIDOR EXTERNO

Não implemente:

```text
deploy/
gateway/
auth/
Caddy/
Docker Compose de produção/
VPS/
Hostinger/
```

O projeto final é local.

---

# 58. DADOS RUNTIME

Utilize:

```text
data-runtime/
```

para:

```text
stats.json
cache
logs
```

Nunca altere:

```text
data/catalogo.json
```

em runtime.

---

# 59. LOGS

Ao iniciar:

```text
============================================
 BUSCA QUE ENTENDE
============================================

Engine: LAYA
Checkpoint: laya-multilingual
Device: CPU
Catalogo: 120 produtos
Porta: 4111
Modo: LOCAL / OFFLINE
============================================
```

Quando fizer busca:

```text
[search] query="..."
[search] products=120
[search] laya_questions=125
[search] latency=XXXms
[search] cache=false
```

Não imprimir dados sensíveis porque esta aplicação não possui segredo.

---

# 60. TRATAMENTO DE ERRO

Se LAYA não carregar:

mostrar:

```text
O mecanismo de inteligência local não conseguiu iniciar.
Verifique a instalação do modelo LAYA.
```

Não mostrar stack trace no frontend.

No terminal, registrar erro técnico.

---

# 61. INSTALAÇÃO

Criar:

```text
requirements.txt
```

com apenas dependências realmente necessárias.

Não adicionar bibliotecas sem justificativa.

O `run.py` deve instalar automaticamente as dependências se necessário.

Se possível:

```text
venv
```

isolado.

Nunca instalar globalmente.

---

# 62. PRIMEIRA EXECUÇÃO

O comportamento deve ser:

```text
./run.sh
```

↓

```text
Detectando Python...
```

↓

```text
Criando ambiente virtual...
```

↓

```text
Instalando dependências...
```

↓

```text
Verificando LAYA...
```

↓

```text
Modelo não encontrado.
Baixando checkpoint...
```

↓

```text
Modelo instalado.
```

↓

```text
Iniciando aplicação...
```

↓

```text
http://127.0.0.1:4111
```

---

# 63. EXECUÇÕES SEGUINTES

Depois da primeira instalação:

```text
./run.sh
```

deve:

```text
detectar modelo
↓
carregar modelo
↓
iniciar aplicação
```

sem baixar novamente.

---

# 64. ABRIR AUTOMATICAMENTE O NAVEGADOR

Após o servidor estar saudável:

```text
GET /healthz
```

abra automaticamente:

```text
http://127.0.0.1:4111
```

No Linux:

```text
xdg-open
```

macOS:

```text
open
```

Windows:

```text
start
```

Se não for possível abrir automaticamente, apenas imprimir a URL.

---

# 65. TESTES AUTOMÁTICOS

Implemente testes para:

### orçamento

```text
até 150
até R$ 80
2k
2,5 mil
cento e cinquenta
entre 100 e 200
uns cem conto
```

### keyword

Preservar os testes originais.

### LAYA

Verificar:

```text
choice
score
confidence
probabilities
```

### ranking

Verificar:

```text
orçamento
score
desempate
```

### API

Verificar:

```text
/healthz
/catalogo
/exemplos
/stats
/buscar
```

### E2E

Utilizar Playwright.

---

# 66. CRITÉRIOS DE ACEITAÇÃO

O projeto só está terminado quando:

## A

```bash
./run.sh
```

inicia tudo.

## B

A aplicação abre:

```text
http://127.0.0.1:4111
```

## C

Não existe dependência de servidor externo para inferência.

## D

O LAYA roda na máquina.

## E

A busca tradicional funciona.

## F

A busca LAYA funciona.

## G

Os 120 produtos são avaliados.

## H

O orçamento é tratado deterministicamente.

## I

Existe cache.

## J

O inspetor mostra:

```text
state
questions
answers
probabilities
latency
```

## K

O layout é visualmente equivalente ao original.

## L

O celular funciona.

## M

A aplicação continua funcionando sem internet depois do primeiro download do modelo.

## N

Os testes automatizados passam.

---

# 67. REGRA CONTRA MOCK

Não faça:

```python
if "cachorro" in query:
    return produtos_cachorro
```

Não faça:

```python
if "jardinagem" in query:
    return jardim
```

Não faça regras específicas para os exemplos.

O LAYA deve realmente fazer a classificação.

As regras determinísticas permitidas são apenas regras de aplicação, como:

```text
orçamento
ranking
cache
limiares
ordenação
UI
```

---

# 68. REGRA CONTRA "FAKE AI"

A aplicação deve deixar tecnicamente claro que o ranking está vindo do LAYA.

No inspetor deve ser possível abrir:

```text
Pergunta:
Quão bem o produto p001 atende ao pedido?
```

e:

```text
Resposta:
score = 2.94

0 = 0.00
1 = 0.01
2 = 0.05
3 = 0.94
```

---

# 69. IMPORTANTE SOBRE O NÚMERO DE PERGUNTAS

O projeto original utiliza:

```text
5 perguntas de entendimento
+
120 perguntas de produto
=
125 perguntas
```

Preserve essa lógica conceitual.

Mas não force artificialmente:

```text
6 chamadas
```

se o LAYA conseguir fazer tudo de maneira mais eficiente.

Primeiro faça funcionar.

Depois faça benchmark.

Escolha a arquitetura baseada em dados.

---

# 70. O RECIBO

O recibo deve mostrar algo semelhante a:

```text
RECIBO DO LAYA

120 produtos avaliados em 382 ms

6 decisões locais
125 perguntas

processamento ........ 382 ms
modelo ............... LAYA
device ............... CPU

custo de inferência .. local
```

Não mostre:

```text
US$ 0,000909
```

como se existisse cobrança de API.

Isso seria conceitualmente falso.

Pode mostrar:

```text
Custo API: R$ 0
```

ou:

```text
Inferência: local
```

---

# 71. MÉTRICAS DA TOPBAR

Troque:

```text
última decisão
decisões
custo
```

por algo coerente com LAYA:

```text
última decisão
decisões
inferência
```

ou:

```text
última decisão
perguntas
tempo
```

Sugestão:

```text
última inferência 382 ms
decisões 125
modo LOCAL
```

---

# 72. IDENTIDADE DO MOTOR

O visualizador deve mostrar:

```text
⚡ LAYA
```

com subtítulo:

```text
modelo de decisão local
```

Não:

```text
JEV
```

---

# 73. DOCUMENTAÇÃO

Crie um README extremamente claro.

Deve explicar:

```text
O que é o projeto
Como instalar
Como executar
Como o LAYA funciona
Como o catálogo funciona
Como funciona a busca tradicional
Como funciona o ranking
Como funciona o orçamento
Como funciona o cache
Como mudar o modelo
Como rodar offline
Como rodar testes
Como medir performance
```

---

# 74. DOCUMENTAÇÃO DE ARQUITETURA

Criar:

```text
docs/architecture.md
```

Com:

```text
Browser
   ↓
Local HTTP
   ↓
Search Service
   ↓
LayaEngine
   ↓
LAYA
   ↓
Decision Adapter
   ↓
Ranking
   ↓
UI
```

Explique também:

```text
Probabilistic boundary
```

e:

```text
Deterministic boundary
```

### Fronteira probabilística

```text
LAYA
```

### Fronteira determinística

```text
orçamento
ranking
filtros
UI
cache
ordenação
```

Esse é um ponto arquitetural importante.

---

# 75. SEGURANÇA

Como é local:

* bind em `127.0.0.1`;
* não expor porta na rede;
* não usar CORS aberto;
* não executar código vindo do modelo;
* escapar HTML;
* não permitir path traversal;
* limitar tamanho do request;
* validar JSON;
* não permitir que o LAYA produza HTML executável.

---

# 76. PERFORMANCE

Não faça o frontend esperar o carregamento do modelo a cada busca.

O modelo deve ficar carregado.

Se a primeira inferência for muito mais lenta:

mostrar:

```text
Preparando mecanismo de busca inteligente...
```

somente durante o warm-up.

Depois:

```text
pronto
```

---

# 77. MEMÓRIA

Monitore o uso.

Não mantenha cópias desnecessárias de:

```text
catalogo
state
questions
answers
```

em múltiplos formatos.

O cache deve ter limite.

---

# 78. NÃO CRIE UMA "PLATAFORMA"

O objetivo não é reproduzir toda a infraestrutura Jev Showcase.

O objetivo é criar:

```text
UMA APLICAÇÃO LOCAL
```

com:

```text
UMA PÁGINA
UM BACKEND LOCAL
UM MODELO LAYA
UM CATÁLOGO
UM COMANDO
```

---

# 79. RESULTADO FINAL ESPERADO

Ao final, o usuário deve poder fazer:

```bash
./run.sh
```

e obter:

```text
┌─────────────────────────────────────────────┐
│ BUSCA QUE ENTENDE                           │
│                                             │
│ O que você procura?                         │
│                                             │
│ [ presente pra minha mãe que ama           │
│   jardinagem até 150 reais             ]    │
│                                             │
│       [ Buscar ]                            │
│                                             │
│ ┌──────────────┐ ┌──────────────────────┐  │
│ │ Palavra-chave│ │ Busca com LAYA       │  │
│ │              │ │                      │  │
│ │ 4 resultados │ │ 11 boas opções       │  │
│ └──────────────┘ └──────────────────────┘  │
│                                             │
│          ÍNDICE DO CATÁLOGO                │
│                                             │
│  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■                  │
│  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■                  │
│                                             │
│       CUPOM DO LAYA                         │
│                                             │
│ Intenção      Presente                      │
│ Departamento  Jardim                        │
│ Para quem     Para a mãe                    │
│ Orçamento     Até R$ 150                    │
│                                             │
│ RECIBO DO LAYA                               │
│ 120 produtos · 382 ms · 125 decisões       │
└─────────────────────────────────────────────┘
```

---

# 80. ORDEM DE IMPLEMENTAÇÃO

Não tente implementar tudo de uma vez.

Faça exatamente nesta ordem:

### FASE 1

Inspecionar projeto original.

### FASE 2

Copiar/adaptar frontend.

### FASE 3

Criar servidor local.

### FASE 4

Criar `LayaEngine`.

### FASE 5

Carregar LAYA.

### FASE 6

Testar uma pergunta `choice`.

### FASE 7

Testar uma pergunta `score`.

### FASE 8

Testar 24 produtos.

### FASE 9

Testar 120 produtos.

### FASE 10

Implementar entendimento.

### FASE 11

Implementar ranking.

### FASE 12

Implementar cache.

### FASE 13

Integrar frontend.

### FASE 14

Implementar inspetor.

### FASE 15

Implementar benchmark.

### FASE 16

Implementar E2E.

### FASE 17

Implementar `run.sh`.

### FASE 18

Implementar `run.ps1`.

### FASE 19

Testar offline.

### FASE 20

Entregar.

---

# 81. REGRA DE QUALIDADE

Não declare que está funcionando simplesmente porque:

```text
o servidor iniciou
```

Você deve provar:

```text
LAYA carregou
↓
pergunta choice funciona
↓
pergunta score funciona
↓
120 produtos são avaliados
↓
ranking funciona
↓
frontend recebe resultado
↓
cache funciona
↓
offline funciona
↓
E2E passa
```

---

# 82. SAÍDA FINAL DO CODING AGENT

Ao terminar, apresente:

```text
==========================================
 BUSCA QUE ENTENDE
==========================================

Status: OK

Engine:
LAYA

Modelo:
laya-multilingual

Execução:
LOCAL

Device:
CPU/GPU

Catálogo:
120 produtos

URL:
http://127.0.0.1:4111

Comando:
./run.sh

Testes:
X passed

Offline:
OK

Benchmark:
p50 = XXX ms
p90 = XXX ms

==========================================
```

Também informe:

1. arquivos criados;
2. arquivos reutilizados do projeto original;
3. arquivos modificados;
4. dependências;
5. modelo utilizado;
6. localização dos pesos;
7. como trocar o modelo;
8. como rodar offline;
9. resultado dos testes;
10. benchmark.

---

# 83. REGRA FINAL — NÃO PARE PARA PERGUNTAR COISAS DESNECESSÁRIAS

Se alguma decisão de implementação estiver ambígua:

1. escolha a alternativa mais simples;
2. mantenha a aplicação local;
3. preserve o comportamento original;
4. não adicione infraestrutura;
5. documente a decisão.

Somente pergunte ao usuário se houver uma decisão que realmente impeça a execução.

Caso contrário:

> **implemente.**

O resultado final deve ser uma aplicação local funcional, não apenas um protótipo ou uma arquitetura conceitual.

# FIM DO PROMPT
