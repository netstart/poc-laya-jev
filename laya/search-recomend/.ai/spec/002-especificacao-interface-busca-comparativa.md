# ESPECIFICAÇÃO DE INTERFACE DE BUSCA COMPARATIVA

## 1. OBJETIVO
Definir o comportamento da interface de busca, focando na visualização comparativa entre a busca tradicional e a busca com LAYA.

## 2. LAYOUT
A interface deve apresentar os resultados de busca divididos em duas colunas distintas abaixo da barra de pesquisa:
- **Coluna Esquerda:** "Busca Tradicional" (baseada em `public/keyword.js`)
- **Coluna Direita:** "Busca com LAYA" (baseada na inferência local)

## 3. IDENTIFICAÇÃO E VISUALIZAÇÃO DE ITENS

Cada item encontrado deve ser identificado corretamente em cada uma das colunas.

### 3.1 Regras de Exibição
- **Item encontrado em ambas:** Deve aparecer em ambas as colunas, identificado visualmente como presente nos dois mecanismos.
- **Item encontrado APENAS pela busca tradicional:** Deve ser mostrado em destaque (ex: contorno ou badge de "Apenas busca tradicional") na coluna da esquerda.
- **Item encontrado APENAS pelo LAYA:** Deve ser mostrado em destaque (ex: contorno ou badge de "Apenas busca com LAYA") na coluna da direita.

### 3.2 Distinção Visual
Para facilitar a leitura, o item deve ter um marcador claro (ex: ícone, cor de fundo sutil ou badge) que indique se ele foi retornado por um, outro, ou ambos os mecanismos.

- Exemplo:
  - Se `p002` é encontrado por ambos: aparece em ambos os lados, com identificação de "Encontrado em ambos".
  - Se `p010` é encontrado apenas pela tradicional: aparece à esquerda, identificado como "Encontrado apenas na busca tradicional".
  - Se `p018` é encontrado apenas pelo LAYA: aparece à direita, identificado como "Encontrado apenas na busca com LAYA".

## 4. CRITÉRIOS DE ACEITAÇÃO DA UI
- A estrutura de duas colunas deve ser responsiva e manter-se funcional em dispositivos móveis (ex: empilhando ou permitindo alternância entre visualizações).
- A identificação visual deve ser intuitiva e consistente com a identidade visual anos 70 do projeto.
- O inspetor deve ser capaz de mostrar detalhes da classificação de cada item em cada mecanismo, se aplicável.
- Deve haver uma divisão bem clara entre o lado do balcão 1 e o lado do Balcão 2, deixando claro a separação e resultado dos itens encontrados por cada mecanismo de busca
