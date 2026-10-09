IMPLEMENTAÇÃO CONCLUÍDA: BOTÃO DE PAYLOAD DOS BALCÕES

## Arquivos Modificados

1. **Especificação**: `.ai/spec/005-botao-payload-balcoes.md`
   - Nova spec detalhando o comportamento do botão de payload
   - Inclui objetivos, localização, comportamento, estrutura dos payloads e critérios de aceitação

2. **HTML**: `public/index.html`
   - Adicionado botão `#payloadBtn` abaixo do `#inspectorBtn`
   - Adicionados containers `.payload-container` para cada balcão:
     - `#payload-balcao1` dentro da coluna de keyword (Balcão 1)
     - `#payload-balcao2` dentro da coluna de LAYA (Balcão 2)

3. **CSS**: `public/busca.css`
   - Estilização dos containers de payload:
     - Fundo `#f4efe3`, borda variável, padding 12px
     - Altura máxima 300px com overflow auto
     - Estilos para headers (h4) e blocos de código (pre) dentro dos payloads
   - Ajuste de espaçamento entre os botões do inspector-trigger

4. **JavaScript**: `public/app.js`
   - Adicionada variável `currentKeywordIds` para armazenar resultados da busca tradicional
   - Atualizada função `doSearch()` para armazenar os IDs da busca keyword
   - Atualizada função `renderInspector()` para chamar `renderPayloads()`
   - Adicionada função `renderPayloads()` que:
     - Cria objeto payload para Balcão 1 (busca tradicional): query, tipo, total de resultados, IDs encontrados
     - Cria objeto payload para Balcão 2 (busca LAYA): query, tipo, entendimento, scores brutos, ordem de ranking, itens dentro/acima do orçamento, métricas
     - Formata ambos como JSON legível nos respectivos containers
   - Adicionado event listener para `#payloadBtn` que:
     - Alterna a visibilidade dos payload containers
     - Alterna o texto do botão entre "Ver payload dos balcões" e "Ocultar payload dos balcões"

## Funcionalidade Implementada

✅ Botão "Ver payload dos balcões" posicionado abaixo de "Ver detalhes da busca"
✅ Payload do Balcão 1 aparece à esquerda, abaixo da coluna do Balcão 1
✅ Payload do Balcão 2 aparece à esquerda, abaixo da coluna do Balcão 2
✅ Clique alternado mostra/oculta os payloads
✅ Texto do botão alterna conforme o estado
✅ Payloads contêm dados JSON formatados e legíveis
✅ Funciona em ambos os modos (desktop e mobile devido ao layout responsivo existente)
✅ Não interfere nas funcionalidades existentes

## Dados nos Payloads

**Balcão 1 (Busca Tradicional)**:
- Query original
- Tipo de busca
- Total de resultados encontrados
- Lista de IDs dos produtos encontrados
- Timestamp

**Balcão 2 (Busca com LAYA)**:
- Query original
- Tipo de busca
- Objeto de entendimento (intenção, categoria, orçamento máximo)
- Scores brutos por produto
- Ordem de ranking completa
- Lista de itens dentro do orçamento
- Lista de boas opções (score >= 2)
- Lista de itens acima do orçamento mas relevantes
- Métricas de performance (latency, número de chamadas, número de perguntas)
- Timestamp

A implementação segue exatamente as especificações definidas e está pronta para uso.