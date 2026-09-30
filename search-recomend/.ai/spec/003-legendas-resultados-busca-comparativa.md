# ESPECIFICAÇÃO DE LEGENDAS PARA RESULTADOS DE BUSCA COMPARATIVA

## 1. OBJETIVO
Definir como o usuário deve entender o que vê em cada lado da interface comparativa, incluindo cores, números, badges e comportamento dos itens exclusivos ou comuns.

## 2. LAYOUT GERAL
A interface mantém a estrutura de duas colunas da `spec/002`, mas agora cada lado deve exibir sua própria legenda explicativa imediatamente abaixo do cabeçalho da coluna.

## 3. LEGENDA DO BALCÃO 1 · BUSCA TRADICIONAL
Local: coluna esquerda, logo abaixo do título da coluna.

### 3.1 Texto mínimo
"Resultados por correspondência de palavras. Nenhuma compreensão de intenção, contexto ou orçamento."

### 3.2 Regras de exibição
- **Itens encontrados apenas pela busca tradicional**: devem aparecer apenas no lado esquerdo, com identificação visual de exclusividade.
- **Itens encontrados em ambos os mecanismos**: aparecem no lado esquerdo com identificação visual de presença nos dois lados.
- **Números/badges**: indicam a ordem de relevância por frequência de termos, do maior para o menor.

## 4. LEGENDA DO BALCÃO 2 · BUSCA COM LAYA
Local: coluna direita, logo abaixo do título da coluna.

### 4.1 Texto mínimo
"Resultados por inteligência local, considerando intenção, contexto e orçamento quando possível."

### 4.2 Regras de exibição
- **Itens encontrados apenas pelo LAYA**: devem aparecer apenas no lado direito, com identificação visual de exclusividade.
- **Itens encontrados em ambos os mecanismos**: aparecem no lado direito com identificação visual de presença nos dois lados.
- **Números/badges**: indicam o ranking do LAYA entre os primeiros resultados considerados.
- **Níveis `lv0` a `lv3`**: representam faixas de score do LAYA, do mais baixo ao mais alto.

## 5. SIGNIFICADO DAS CORES
- **Borda esquerda verde**: item encontrado tanto pela busca tradicional quanto pelo LAYA.
- **Borda esquerda azul**: item encontrado apenas pela busca tradicional.
- **Borda esquerda laranja**: item encontrado apenas pelo LAYA.
- **Fundo do tile**: indica nível do LAYA conforme `lv0..lv3`, do mais claro ao mais forte.

## 6. SIGNIFICADO DOS NÚMEROS E BADGES
- **No Balcão 1**: números representam posição por relevância tradicional.
- **No Balcão 2**: números representam posição no ranking LAYA.
- A ausência de badge não significa ausência de relevância; significa que o item não está entre os primeiros posicionados exibidos.

## 7. COMPORTAMENTO SEPARADO
- O lado esquerdo mostra exclusivamente o que a busca tradicional retornar, sem itens injetados pelo LAYA.
- O lado direito mostra exclusivamente o que o LAYA retornar, sem itens injetados pela busca tradicional.
- Quando um item aparece nos dois mecanismos, ele deve ser exibido em ambos os lados com a identificação de presença dupla.

## 8. RESPONSIVIDADE
Em telas pequenas, as colunas devem empilhar verticalmente e as legendas devem acompanhar suas respectivas colunas, mantendo a legibilidade e a separação entre Balcão 1 e Balcão 2.

## 9. CRITÉRIOS DE ACEITAÇÃO DA LEGENDA
- Cada lado tem uma legenda própria, clara e sucinta.
- As cores e badges são explicadas visual ou textualmente.
- O comportamento separado dos lados é mantido em qualquer tamanho de tela.
- A legenda não interfere na usabilidade nem polui a interface.
